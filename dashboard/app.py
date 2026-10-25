from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    Response
)

import sqlite3
import os
import sys
import re
import cv2
import shutil

from datetime import datetime

from picamera2 import Picamera2
from libcamera import controls


# ============================================================
# PROJECT PATH
# ============================================================

PROJECT_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


if PROJECT_DIR not in sys.path:

    sys.path.insert(
        0,
        PROJECT_DIR
    )


# ============================================================
# PAYMENT REQUEST DATABASE
# ============================================================

from database.payment_requests import (
    create_payment_request,
    get_payment_request
)

from database.merchants import (
    ensure_demo_merchant,
    get_merchant
)


from database.payment_processor import (
    process_payment
)


from processing.recognition import (
    recognize_user
)


from hardware.controller import (
    VeinGateHardwareController
)

from processing.scan_controller import (
    run_payment_scan
)


from processing.template_selector import (
    calculate_image_quality
)


# ============================================================
# FLASK
# ============================================================

app = Flask(__name__)


# ============================================================
# PATHS
# ============================================================

DB_PATH = os.path.join(
    PROJECT_DIR,
    "database",
    "veingate.db"
)


CAPTURE_DIR = os.path.join(
    PROJECT_DIR,
    "captured_images"
)


TEMPLATES_DIR = os.path.join(
    PROJECT_DIR,
    "templates"
)


os.makedirs(
    CAPTURE_DIR,
    exist_ok=True
)


os.makedirs(
    TEMPLATES_DIR,
    exist_ok=True
)


# ============================================================
# SETTINGS
# ============================================================

ENROLLMENT_SAMPLE_COUNT = 10

# Keep three representative processed palm templates per user.
# The best one is also copied to template.png for backward
# compatibility with the current recognition pipeline.
SELECTED_TEMPLATE_COUNT = 3


# ============================================================
# CAMERA STATE
# ============================================================

picam2 = None
camera_started = False
latest_frame = None

# Active merchant payment shown on the OLED.
active_payment_amount = None
scan_in_progress = False


# ============================================================
# HARDWARE CONTROLLER
# ============================================================

hardware = VeinGateHardwareController()
hardware_initialized = False


# ============================================================
# INITIALIZE HARDWARE ON DEMAND
# ============================================================

def ensure_hardware_initialized():

    global hardware_initialized

    if hardware_initialized:

        return


    hardware.initialize()

    hardware_initialized = True


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_database():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# VALIDATE PHONE
# ============================================================

def validate_phone_number(
    phone_number
):

    phone_number = str(
        phone_number
    ).strip()


    if phone_number == "":

        return True


    pattern = r"^\+?[0-9]{10,15}$"


    return bool(
        re.fullmatch(
            pattern,
            phone_number
        )
    )


# ============================================================
# VALIDATE EMAIL
# ============================================================

def validate_email(
    email
):

    email = str(
        email
    ).strip()


    if email == "":

        return True


    pattern = (
        r"^[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+"
        r"\.[A-Za-z]{2,}$"
    )


    return bool(
        re.fullmatch(
            pattern,
            email
        )
    )


# ============================================================
# CAMERA START
# ============================================================

def start_camera():

    global picam2
    global camera_started


    if camera_started:

        return


    print(
        "Starting VeinPay Camera Module 3 NoIR..."
    )


    picam2 = Picamera2()


    camera_config = (
        picam2.create_video_configuration(
            main={
                "size": (
                    1280,
                    720
                ),
                "format":
                    "RGB888"
            }
        )
    )


    picam2.configure(
        camera_config
    )


    picam2.set_controls(
        {
            "AfMode":
                controls.AfModeEnum.Continuous,
            "AfSpeed":
                controls.AfSpeedEnum.Fast
        }
    )


    picam2.start()


    camera_started = True


    print(
        "VeinPay camera ready."
    )


# ============================================================
# CAMERA STREAM
# ============================================================

def generate_camera_frames():

    global latest_frame

    start_camera()

    while True:

        frame = picam2.capture_array()

        # Keep a clean full frame for enrollment/recognition.
        latest_frame = frame.copy()

        # No on-screen guide box. The user can keep the full palm
        # naturally at approximately 5-10 cm from the camera.
        display_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_RGB2BGR
        )

        success, buffer = cv2.imencode(
            ".jpg",
            display_frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                90
            ]
        )

        if not success:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            +
            frame_bytes
            +
            b"\r\n"
        )


# ============================================================
# GET USER
# ============================================================

def get_user(
    user_id
):

    conn = get_database()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            user_id,
            name,
            phone_number,
            email,
            wallet_balance,
            template_path

        FROM users

        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )


    user = (
        cursor.fetchone()
    )


    conn.close()


    return user


# ============================================================
# TEMPLATE DIRECTORY
# ============================================================

def get_user_template_dir(
    user_id
):

    return os.path.join(
        TEMPLATES_DIR,
        f"user_{user_id}"
    )


# ============================================================
# RAW ENROLLMENT DIRECTORY
# ============================================================

def get_user_raw_dir(
    user_id
):

    return os.path.join(
        get_user_template_dir(
            user_id
        ),
        "raw"
    )


# ============================================================
# PROCESSED ENROLLMENT DIRECTORY
# ============================================================

def get_user_processed_dir(
    user_id
):

    return os.path.join(
        get_user_template_dir(
            user_id
        ),
        "processed"
    )


# ============================================================
# SELECTED REPRESENTATIVE TEMPLATE DIRECTORY
# ============================================================

def get_user_selected_dir(
    user_id
):

    return os.path.join(
        get_user_template_dir(
            user_id
        ),
        "selected"
    )


# ============================================================
# COUNT ENROLLMENT SAMPLES
# ============================================================

def count_enrollment_samples(
    user_id
):

    raw_dir = get_user_raw_dir(
        user_id
    )


    if not os.path.exists(
        raw_dir
    ):

        return 0


    files = [
        name
        for name in os.listdir(
            raw_dir
        )
        if name.lower().endswith(
            (
                ".jpg",
                ".jpeg",
                ".png"
            )
        )
    ]


    return len(
        files
    )


# ============================================================
# FINALIZE PALM ENROLLMENT
# ============================================================

def finalize_enrollment(
    user_id
):

    from processing.preprocess import (
        preprocess_palm
    )


    raw_dir = get_user_raw_dir(
        user_id
    )


    processed_root = (
        get_user_processed_dir(
            user_id
        )
    )


    selected_root = (
        get_user_selected_dir(
            user_id
        )
    )


    os.makedirs(
        processed_root,
        exist_ok=True
    )


    if os.path.isdir(
        selected_root
    ):

        shutil.rmtree(
            selected_root
        )


    os.makedirs(
        selected_root,
        exist_ok=True
    )


    raw_files = sorted(
        [
            name
            for name in os.listdir(
                raw_dir
            )
            if name.lower().endswith(
                (
                    ".jpg",
                    ".jpeg",
                    ".png"
                )
            )
        ]
    )


    if len(
        raw_files
    ) < ENROLLMENT_SAMPLE_COUNT:

        raise RuntimeError(
            "Not enough palm samples."
        )


    processed_templates = []


    for index, filename in enumerate(
        raw_files[:ENROLLMENT_SAMPLE_COUNT],
        start=1
    ):


        raw_path = os.path.join(
            raw_dir,
            filename
        )


        sample_output_dir = os.path.join(
            processed_root,
            f"sample_{index:02d}"
        )


        os.makedirs(
            sample_output_dir,
            exist_ok=True
        )


        preprocess_palm(
            raw_path,
            output_folder=sample_output_dir
        )


        frangi_path = os.path.join(
            sample_output_dir,
            "05_frangi.png"
        )


        if os.path.exists(
            frangi_path
        ):

            quality_score = (
                calculate_image_quality(
                    frangi_path
                )
            )


            processed_templates.append(
                {
                    "sample_number":
                        index,

                    "path":
                        frangi_path,

                    "quality_score":
                        float(
                            quality_score
                        )
                }
            )


    if not processed_templates:

        raise RuntimeError(
            "Processed palm templates were not created."
        )


    processed_templates.sort(
        key=lambda item:
            item["quality_score"],
        reverse=True
    )


    selected_templates = (
        processed_templates[
            :SELECTED_TEMPLATE_COUNT
        ]
    )


    if not selected_templates:

        raise RuntimeError(
            "No representative palm templates could be selected."
        )


    for selected_index, item in enumerate(
        selected_templates,
        start=1
    ):

        destination = os.path.join(
            selected_root,
            f"template_{selected_index:02d}.png"
        )


        shutil.copy2(
            item["path"],
            destination
        )


    primary_template = (
        selected_templates[0]["path"]
    )


    final_template_path = os.path.join(
        get_user_template_dir(
            user_id
        ),
        "template.png"
    )


    shutil.copy2(
        primary_template,
        final_template_path
    )


    relative_template_path = (
        os.path.relpath(
            final_template_path,
            PROJECT_DIR
        )
    )


    relative_template_path = (
        relative_template_path.replace(
            "\\",
            "/"
        )
    )


    conn = get_database()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE users

        SET template_path = ?

        WHERE user_id = ?
        """,
        (
            relative_template_path,
            user_id
        )
    )


    conn.commit()

    conn.close()


    print(
        f"Enrollment finalized for user {user_id}."
    )

    print(
        f"Representative templates selected: "
        f"{len(selected_templates)}"
    )


    for item in selected_templates:

        print(
            "Selected sample:",
            item["sample_number"],
            "| quality:",
            round(
                item["quality_score"],
                2
            )
        )


    return relative_template_path


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def home():

    conn = get_database()

    cursor = conn.cursor()


    # ========================================================
    # USERS
    # ========================================================

    cursor.execute(
        """
        SELECT
            user_id,
            name,
            phone_number,
            email,
            wallet_balance,
            template_path

        FROM users

        ORDER BY user_id
        """
    )


    users = (
        cursor.fetchall()
    )


    # ========================================================
    # TRANSACTIONS
    # ========================================================

    cursor.execute(
        """
        SELECT
            transactions.transaction_id,
            transactions.user_id,
            users.name AS user_name,
            transactions.amount,
            transactions.status,
            transactions.similarity_score,
            transactions.notification_status,
            transactions.timestamp

        FROM transactions

        LEFT JOIN users

            ON transactions.user_id
            =
            users.user_id

        ORDER BY
            transactions.transaction_id DESC

        LIMIT 20
        """
    )


    transactions = (
        cursor.fetchall()
    )


    # ========================================================
    # TOTAL USERS
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM users
        """
    )


    total_users = (
        cursor.fetchone()[0]
    )


    # ========================================================
    # TOTAL TRANSACTIONS
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM transactions
        """
    )


    total_transactions = (
        cursor.fetchone()[0]
    )


    # ========================================================
    # SUCCESSFUL PAYMENTS
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)

        FROM transactions

        WHERE status = 'SUCCESS'
        """
    )


    successful_transactions = (
        cursor.fetchone()[0]
    )


    # ========================================================
    # TOTAL PAID
    # ========================================================

    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(amount),
                0
            )

        FROM transactions

        WHERE status = 'SUCCESS'
        """
    )


    total_paid = (
        cursor.fetchone()[0]
    )


    conn.close()


    return render_template(
        "index.html",
        users=users,
        transactions=transactions,
        total_users=total_users,
        total_transactions=total_transactions,
        successful_transactions=successful_transactions,
        total_paid=total_paid
    )


# ============================================================
# USER REGISTRATION PAGE
# ============================================================

@app.route("/enroll")
def enroll():

    return render_template(
        "enroll.html"
    )


# ============================================================
# REGISTER USER
# ============================================================

@app.route(
    "/api/register_user",
    methods=["POST"]
)
def register_user():

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify(
            {
                "success": False,
                "message":
                    "No registration data received."
            }
        ), 400


    name = str(
        data.get(
            "name",
            ""
        )
    ).strip()


    phone_number = str(
        data.get(
            "phone_number",
            ""
        )
    ).strip()


    email = str(
        data.get(
            "email",
            ""
        )
    ).strip().lower()


    try:

        wallet_balance = float(
            data.get(
                "wallet_balance",
                1000
            )
        )


    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Invalid wallet balance."
            }
        ), 400


    if name == "":

        return jsonify(
            {
                "success": False,
                "message":
                    "User name cannot be empty."
            }
        ), 400


    if not validate_phone_number(
        phone_number
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Invalid phone number."
            }
        ), 400


    if not validate_email(
        email
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Invalid email address."
            }
        ), 400


    if wallet_balance < 0:

        return jsonify(
            {
                "success": False,
                "message":
                    "Wallet balance cannot be negative."
            }
        ), 400


    conn = get_database()

    cursor = conn.cursor()


    # ========================================================
    # DUPLICATE EMAIL
    # ========================================================

    if email != "":

        cursor.execute(
            """
            SELECT user_id

            FROM users

            WHERE LOWER(email) = LOWER(?)
            """,
            (
                email,
            )
        )


        if cursor.fetchone() is not None:

            conn.close()


            return jsonify(
                {
                    "success": False,
                    "message":
                        "This email is already registered."
                }
            ), 409


    # ========================================================
    # DUPLICATE PHONE
    # ========================================================

    if phone_number != "":

        cursor.execute(
            """
            SELECT user_id

            FROM users

            WHERE phone_number = ?
            """,
            (
                phone_number,
            )
        )


        if cursor.fetchone() is not None:

            conn.close()


            return jsonify(
                {
                    "success": False,
                    "message":
                        "This phone number is already registered."
                }
            ), 409


    try:

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                phone_number,
                email,
                template_path,
                wallet_balance
            )

            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                name,
                phone_number,
                email,
                "PENDING_REAL_NIR_TEMPLATE",
                wallet_balance
            )
        )


        conn.commit()


        user_id = (
            cursor.lastrowid
        )


    except sqlite3.Error as error:

        conn.close()


        return jsonify(
            {
                "success": False,
                "message":
                    "Database error: "
                    +
                    str(error)
            }
        ), 500


    conn.close()


    # ========================================================
    # CREATE ENROLLMENT FOLDERS
    # ========================================================

    os.makedirs(
        get_user_raw_dir(
            user_id
        ),
        exist_ok=True
    )


    os.makedirs(
        get_user_processed_dir(
            user_id
        ),
        exist_ok=True
    )


    return jsonify(
        {
            "success": True,

            "message":
                "User profile created. Continue with palm enrollment.",

            "user_id":
                user_id,

            "enrollment_url":
                f"/enroll/{user_id}/palm"
        }
    )


# ============================================================
# PALM ENROLLMENT PAGE
# ============================================================

@app.route(
    "/enroll/<int:user_id>/palm"
)
def palm_enroll_page(
    user_id
):

    user = get_user(
        user_id
    )


    if user is None:

        return (
            "User not found.",
            404
        )


    sample_count = (
        count_enrollment_samples(
            user_id
        )
    )


    return render_template(
        "palm_enroll.html",
        user=user,
        sample_count=sample_count,
        required_samples=ENROLLMENT_SAMPLE_COUNT
    )


# ============================================================
# CAPTURE ENROLLMENT SAMPLE
# ============================================================

@app.route(
    "/api/enroll/<int:user_id>/capture",
    methods=["POST"]
)
def capture_enrollment_sample(
    user_id
):

    global latest_frame


    user = get_user(
        user_id
    )


    if user is None:

        return jsonify(
            {
                "success": False,
                "message":
                    "User not found."
            }
        ), 404


    if latest_frame is None:

        return jsonify(
            {
                "success": False,
                "message":
                    "Camera frame is not ready yet."
            }
        ), 400


    raw_dir = get_user_raw_dir(
        user_id
    )


    os.makedirs(
        raw_dir,
        exist_ok=True
    )


    current_count = (
        count_enrollment_samples(
            user_id
        )
    )


    if current_count >= ENROLLMENT_SAMPLE_COUNT:

        return jsonify(
            {
                "success": False,
                "message":
                    "Required palm samples already captured.",

                "sample_count":
                    current_count,

                "complete":
                    True
            }
        )


    sample_number = (
        current_count
        +
        1
    )


    filename = (
        f"sample_{sample_number:02d}.jpg"
    )


    file_path = os.path.join(
        raw_dir,
        filename
    )


    success = cv2.imwrite(
        file_path,
        latest_frame
    )


    if not success:

        return jsonify(
            {
                "success": False,
                "message":
                    "Unable to save palm sample."
            }
        ), 500


    print(
        f"Enrollment sample {sample_number} "
        f"saved for user {user_id}: "
        f"{file_path}"
    )


    new_count = (
        count_enrollment_samples(
            user_id
        )
    )


    # ========================================================
    # FINAL SAMPLE
    # ========================================================

    if new_count >= ENROLLMENT_SAMPLE_COUNT:


        try:

            template_path = (
                finalize_enrollment(
                    user_id
                )
            )


            return jsonify(
                {
                    "success": True,

                    "sample_count":
                        new_count,

                    "required_samples":
                        ENROLLMENT_SAMPLE_COUNT,

                    "complete":
                        True,

                    "message":
                        "Palm enrollment completed successfully.",

                    "template_path":
                        template_path
                }
            )


        except Exception as error:

            return jsonify(
                {
                    "success": False,

                    "sample_count":
                        new_count,

                    "required_samples":
                        ENROLLMENT_SAMPLE_COUNT,

                    "complete":
                        False,

                    "message":
                        "Samples captured, but preprocessing failed: "
                        +
                        str(error)
                }
            ), 500


    return jsonify(
        {
            "success": True,

            "sample_count":
                new_count,

            "required_samples":
                ENROLLMENT_SAMPLE_COUNT,

            "complete":
                False,

            "message":
                f"Palm sample {new_count} captured."
        }
    )


# ============================================================
# CAMERA VIDEO FEED
# ============================================================

@app.route("/video_feed")
def video_feed():

    return Response(
        generate_camera_frames(),
        mimetype=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )


# ============================================================
# MERCHANT WALLET PAGE
# ============================================================

@app.route("/merchant-wallet")
def merchant_wallet_page():

    merchant_id = ensure_demo_merchant()

    merchant = get_merchant(
        merchant_id
    )


    conn = get_database()

    cursor = conn.cursor()


    # --------------------------------------------------------
    # TOTAL SUCCESSFUL RECEIVED
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            COALESCE(
                SUM(transactions.amount),
                0
            )

        FROM payment_requests

        INNER JOIN transactions

            ON payment_requests.transaction_id
            =
            transactions.transaction_id

        WHERE
            payment_requests.merchant_id = ?

        AND
            payment_requests.status = 'COMPLETED'

        AND
            transactions.status = 'SUCCESS'
        """,
        (
            merchant_id,
        )
    )


    total_received = (
        cursor.fetchone()[0]
    )


    # --------------------------------------------------------
    # SUCCESSFUL PAYMENT COUNT
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            COUNT(*)

        FROM payment_requests

        INNER JOIN transactions

            ON payment_requests.transaction_id
            =
            transactions.transaction_id

        WHERE
            payment_requests.merchant_id = ?

        AND
            payment_requests.status = 'COMPLETED'

        AND
            transactions.status = 'SUCCESS'
        """,
        (
            merchant_id,
        )
    )


    successful_payment_count = (
        cursor.fetchone()[0]
    )


    # --------------------------------------------------------
    # RECENT MERCHANT PAYMENTS
    # --------------------------------------------------------

    cursor.execute(
        """
        SELECT
            transactions.transaction_id,
            transactions.user_id,
            users.name AS user_name,
            transactions.amount,
            transactions.status,
            transactions.similarity_score,
            transactions.timestamp

        FROM payment_requests

        INNER JOIN transactions

            ON payment_requests.transaction_id
            =
            transactions.transaction_id

        LEFT JOIN users

            ON transactions.user_id
            =
            users.user_id

        WHERE
            payment_requests.merchant_id = ?

        ORDER BY
            transactions.transaction_id DESC

        LIMIT 25
        """,
        (
            merchant_id,
        )
    )


    recent_payments = (
        cursor.fetchall()
    )


    conn.close()


    return render_template(
        "merchant_wallet.html",
        merchant=merchant,
        total_received=total_received,
        successful_payment_count=successful_payment_count,
        recent_payments=recent_payments
    )


# ============================================================
# MERCHANT PAYMENT PAGE
# ============================================================

@app.route("/payment")
def payment_page():

    merchant_id = ensure_demo_merchant()

    merchant = get_merchant(
        merchant_id
    )

    return render_template(
        "payment.html",
        merchant=merchant
    )


# ============================================================
# START MERCHANT PAYMENT
# ============================================================

@app.route(
    "/api/payment/start",
    methods=["POST"]
)
def start_merchant_payment():

    global active_payment_amount

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify(
            {
                "success": False,
                "message":
                    "No payment amount received."
            }
        ), 400


    try:

        amount = float(
            data.get(
                "amount"
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Invalid payment amount."
            }
        ), 400


    if amount <= 0:

        return jsonify(
            {
                "success": False,
                "message":
                    "Payment amount must be greater than zero."
            }
        ), 400


    amount = round(
        amount,
        2
    )


    try:

        merchant_id = ensure_demo_merchant()

        merchant = get_merchant(
            merchant_id
        )

        request_id = create_payment_request(
            amount,
            merchant_id
        )

    except Exception as error:

        return jsonify(
            {
                "success": False,
                "message":
                    "Unable to create payment request: "
                    +
                    str(error)
            }
        ), 500


    active_payment_amount = amount

    try:
        ensure_hardware_initialized()
        hardware.show_payment_request(amount)
    except Exception as error:
        print(
            "OLED payment amount display error:",
            error
        )


    return jsonify(
        {
            "success": True,

            "request_id":
                request_id,

            "merchant_id":
                merchant_id,

            "merchant_name":
                merchant["merchant_name"],

            "shop_name":
                merchant["shop_name"],

            "scan_url":
                f"/scan?request_id={request_id}"
        }
    )


# ============================================================
# PAYMENT SCAN PAGE
# ============================================================

@app.route("/scan")
def scan():

    request_id_text = request.args.get(
        "request_id",
        ""
    )


    payment_request = None


    if request_id_text != "":

        try:

            request_id = int(
                request_id_text
            )

            payment_request = get_payment_request(
                request_id
            )

        except (
            TypeError,
            ValueError
        ):

            payment_request = None


    return render_template(
        "scan.html",
        payment_request=payment_request
    )



# ============================================================
# PALM RECOGNITION FOR PAYMENT
# ============================================================

@app.route(
    "/api/payment/recognize",
    methods=["POST"]
)
def recognize_payment_palm():

    global latest_frame

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify(
            {
                "success": False,
                "message":
                    "No payment request data received."
            }
        ), 400

    try:

        request_id = int(
            data.get(
                "request_id"
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Invalid payment request ID."
            }
        ), 400

    payment_request = get_payment_request(
        request_id
    )

    if payment_request is None:

        return jsonify(
            {
                "success": False,
                "message":
                    "Payment request not found."
            }
        ), 404

    if (
        payment_request["status"]
        !=
        "PENDING"
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Payment request is no longer pending."
            }
        ), 400

    if latest_frame is None:

        return jsonify(
            {
                "success": False,
                "message":
                    "Camera frame is not ready."
            }
        ), 400

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    filename = (
        "recognition_"
        +
        timestamp
        +
        ".jpg"
    )

    recognition_dir = os.path.join(
        CAPTURE_DIR,
        "recognition"
    )

    os.makedirs(
        recognition_dir,
        exist_ok=True
    )

    image_path = os.path.join(
        recognition_dir,
        filename
    )

    saved = cv2.imwrite(
        image_path,
        latest_frame
    )

    if not saved:

        return jsonify(
            {
                "success": False,
                "message":
                    "Unable to save palm image."
            }
        ), 500

    try:

        live_image = cv2.imread(
            image_path,
            cv2.IMREAD_GRAYSCALE
        )

        if live_image is None:

            return jsonify(
                {
                    "success": False,
                    "message":
                        "Unable to load captured palm image."
                }
            ), 500

        result = recognize_user(
            live_image
        )

    except Exception as error:

        return jsonify(
            {
                "success": False,
                "message":
                    "Palm recognition failed: "
                    +
                    str(error)
            }
        ), 500


    best_user = result.get(
        "best_user"
    )

    best_score = result.get(
        "best_score",
        0.0
    )

    matched = result.get(
        "matched"
    )


    if best_user is None:

        return jsonify(
            {
                "success": False,
                "message":
                    result.get(
                        "reason",
                        "No palm candidate found."
                    ),
                "similarity_score":
                    best_score,
                "authenticated":
                    False,
                "payment_processed":
                    False
            }
        )


    return jsonify(
        {
            "success": True,

            "message":
                result.get(
                    "reason",
                    "Palm candidate found."
                ),

            "request_id":
                request_id,

            "amount":
                payment_request["amount"],

            "user_id":
                best_user["user_id"],

            "user_name":
                best_user["name"],

            "similarity_score":
                best_score,

            "authenticated":
                True
                if matched is True
                else False,

            "payment_processed":
                False,

            "calibrated":
                matched is not None
        }
    )


# ============================================================
# FINAL INTEGRATED PAYMENT SCAN
# ============================================================

@app.route(
    "/api/payment/scan",
    methods=["POST"]
)
def integrated_payment_scan():

    global latest_frame
    global active_payment_amount
    global scan_in_progress


    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify(
            {
                "success": False,
                "message":
                    "No payment request data received."
            }
        ), 400


    try:

        request_id = int(
            data.get(
                "request_id"
            )
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Invalid payment request ID."
            }
        ), 400


    if latest_frame is None:

        return jsonify(
            {
                "success": False,
                "message":
                    "Camera frame is not ready."
            }
        ), 400


    payment_request = get_payment_request(
        request_id
    )

    if payment_request is None:

        return jsonify(
            {
                "success": False,
                "message":
                    "Payment request not found."
            }
        ), 404


    if payment_request["status"] != "PENDING":

        return jsonify(
            {
                "success": False,
                "message":
                    "Payment request is no longer pending."
            }
        ), 400


    active_payment_amount = payment_request["amount"]


    try:

        ensure_hardware_initialized()

        distance_cm = hardware.get_distance_cm()

        if distance_cm is None:

            hardware.show_payment_request(
                active_payment_amount
            )

            return jsonify(
                {
                    "success": False,
                    "message":
                        "ToF distance is unavailable."
                }
            ), 503


        if not hardware.palm_in_scan_zone(
            min_cm=5.0,
            max_cm=10.0
        ):

            hardware.show_payment_position(
                active_payment_amount,
                distance_cm
            )

            if distance_cm > 10.0:
                message = "Palm is too far. Move closer."
            else:
                message = "Palm is too close. Move back."

            return jsonify(
                {
                    "success": False,
                    "scan_started": False,
                    "distance_cm": distance_cm,
                    "scan_zone": False,
                    "message": message
                }
            ), 400


        scan_in_progress = True

        hardware.show_scanning()

        result = run_payment_scan(
            request_id=request_id,
            frame=latest_frame,
            hardware=hardware
        )

        if result.get("payment_processed"):
            active_payment_amount = None

        return jsonify(
            result
        )


    except Exception as error:

        return jsonify(
            {
                "success": False,
                "message":
                    "Integrated payment scan failed: "
                    +
                    str(error)
            }
        ), 500

    finally:

        scan_in_progress = False


# ============================================================
# MANUAL PALM CAPTURE
# ============================================================

@app.route(
    "/api/capture_palm",
    methods=["POST"]
)
def capture_palm():

    global latest_frame


    if latest_frame is None:

        return jsonify(
            {
                "success": False,
                "message":
                    "No camera frame available."
            }
        ), 400


    timestamp = (
        datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
    )


    filename = (
        "palm_"
        +
        timestamp
        +
        ".jpg"
    )


    file_path = os.path.join(
        CAPTURE_DIR,
        filename
    )


    success = cv2.imwrite(
        file_path,
        latest_frame
    )


    if not success:

        return jsonify(
            {
                "success": False,
                "message":
                    "Unable to save palm image."
            }
        ), 500


    return jsonify(
        {
            "success": True,

            "filename":
                filename,

            "path":
                file_path
        }
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

@app.route("/api/status")
def api_status():

    global active_payment_amount

    try:

        ensure_hardware_initialized()

    except Exception as error:

        print(
            "Hardware initialization error:",
            error
        )


    try:

        hardware_status = (
            hardware.get_status()
        )

    except Exception as error:

        print(
            "Hardware status read error:",
            error
        )

        hardware_status = {
            "distance_sensor": False,
            "temperature_sensor": False,
            "oled": False,
            "ir_led": False,
            "buzzer": False
        }


    distance_cm = None

    try:
        if hardware_status.get("distance_sensor", False):
            distance_cm = hardware.get_distance_cm()

            if (
                active_payment_amount is not None
                and not scan_in_progress
                and distance_cm is not None
            ):
                hardware.show_payment_position(
                    active_payment_amount,
                    distance_cm
                )

    except Exception as error:
        print(
            "ToF/OLED status update error:",
            error
        )


    return jsonify(
        {
            "camera":
                "CONNECTED"
                if camera_started
                else
                "READY",

            "distance":
                "CONNECTED"
                if hardware_status.get(
                    "distance_sensor",
                    False
                )
                else
                "NOT CONNECTED",

            "temperature":
                "CONNECTED"
                if hardware_status.get(
                    "temperature_sensor",
                    False
                )
                else
                "NOT CONNECTED",

            "ir":
                "CONNECTED"
                if hardware_status.get(
                    "ir_led",
                    False
                )
                else
                "NOT CONNECTED",

            "oled":
                "CONNECTED"
                if hardware_status.get(
                    "oled",
                    False
                )
                else
                "NOT CONNECTED",

            "buzzer":
                "CONNECTED"
                if hardware_status.get(
                    "buzzer",
                    False
                )
                else
                "NOT CONNECTED",

            "recognition":
                "NOT CALIBRATED",

            "payment":
                "WAITING",

            "distance_cm":
                distance_cm,

            "scan_zone":
                True
                if distance_cm is not None
                and 5.0 <= distance_cm <= 10.0
                else False,

            "scanning":
                scan_in_progress,

            "system":
                "SCANNING"
                if scan_in_progress
                else (
                    "IN ZONE"
                    if distance_cm is not None
                    and 5.0 <= distance_cm <= 10.0
                    else "PLACE PALM"
                )
        }
    )


# ============================================================
# EDIT USER PAGE
# ============================================================

@app.route(
    "/user/<int:user_id>/edit"
)
def edit_user_page(
    user_id
):

    user = get_user(
        user_id
    )


    if user is None:

        return (
            "User not found.",
            404
        )


    return render_template(
        "edit_user.html",
        user=user
    )


# ============================================================
# UPDATE USER
# ============================================================

@app.route(
    "/api/user/<int:user_id>/update",
    methods=["POST"]
)
def update_user(
    user_id
):

    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify(
            {
                "success": False,
                "message":
                    "No update data received."
            }
        ), 400


    name = str(
        data.get(
            "name",
            ""
        )
    ).strip()


    phone_number = str(
        data.get(
            "phone_number",
            ""
        )
    ).strip()


    email = str(
        data.get(
            "email",
            ""
        )
    ).strip().lower()


    try:

        wallet_balance = float(
            data.get(
                "wallet_balance"
            )
        )


    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Invalid wallet balance."
            }
        ), 400


    if name == "":

        return jsonify(
            {
                "success": False,
                "message":
                    "User name cannot be empty."
            }
        ), 400


    if not validate_phone_number(
        phone_number
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Invalid phone number."
            }
        ), 400


    if not validate_email(
        email
    ):

        return jsonify(
            {
                "success": False,
                "message":
                    "Invalid email address."
            }
        ), 400


    if wallet_balance < 0:

        return jsonify(
            {
                "success": False,
                "message":
                    "Wallet balance cannot be negative."
            }
        ), 400


    conn = get_database()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT user_id

        FROM users

        WHERE user_id = ?
        """,
        (
            user_id,
        )
    )


    if cursor.fetchone() is None:

        conn.close()


        return jsonify(
            {
                "success": False,
                "message":
                    "User not found."
            }
        ), 404


    # ========================================================
    # DUPLICATE EMAIL
    # ========================================================

    if email != "":

        cursor.execute(
            """
            SELECT user_id

            FROM users

            WHERE
                LOWER(email) = LOWER(?)

            AND
                user_id != ?
            """,
            (
                email,
                user_id
            )
        )


        if cursor.fetchone() is not None:

            conn.close()


            return jsonify(
                {
                    "success": False,
                    "message":
                        "Email already belongs to another user."
                }
            ), 409


    # ========================================================
    # DUPLICATE PHONE
    # ========================================================

    if phone_number != "":

        cursor.execute(
            """
            SELECT user_id

            FROM users

            WHERE
                phone_number = ?

            AND
                user_id != ?
            """,
            (
                phone_number,
                user_id
            )
        )


        if cursor.fetchone() is not None:

            conn.close()


            return jsonify(
                {
                    "success": False,
                    "message":
                        "Phone number already belongs to another user."
                }
            ), 409


    try:

        cursor.execute(
            """
            UPDATE users

            SET
                name = ?,
                phone_number = ?,
                email = ?,
                wallet_balance = ?

            WHERE user_id = ?
            """,
            (
                name,
                phone_number,
                email,
                wallet_balance,
                user_id
            )
        )


        conn.commit()


    except sqlite3.Error as error:

        conn.rollback()

        conn.close()


        return jsonify(
            {
                "success": False,
                "message":
                    "Database error: "
                    +
                    str(error)
            }
        ), 500


    conn.close()


    return jsonify(
        {
            "success": True,

            "message":
                "User updated successfully."
        }
    )


# ============================================================
# DELETE USER
# ============================================================

@app.route(
    "/api/user/<int:user_id>/delete",
    methods=["POST"]
)
def delete_user(
    user_id
):

    user = get_user(
        user_id
    )


    if user is None:

        return jsonify(
            {
                "success": False,
                "message":
                    "User not found."
            }
        ), 404


    user_name = (
        user["name"]
    )


    conn = get_database()

    cursor = conn.cursor()


    try:

        # ====================================================
        # PRESERVE OLD TRANSACTIONS
        # ====================================================

        cursor.execute(
            """
            UPDATE transactions

            SET user_id = NULL

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )


        preserved_transactions = (
            cursor.rowcount
        )


        # ====================================================
        # DELETE USER PROFILE
        # ====================================================

        cursor.execute(
            """
            DELETE FROM users

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )


        conn.commit()


    except sqlite3.Error as error:

        conn.rollback()

        conn.close()


        return jsonify(
            {
                "success": False,
                "message":
                    "Database error: "
                    +
                    str(error)
            }
        ), 500


    conn.close()


    # ========================================================
    # DELETE PALM TEMPLATE DIRECTORY
    # ========================================================

    user_template_dir = (
        get_user_template_dir(
            user_id
        )
    )


    if os.path.isdir(
        user_template_dir
    ):


        try:

            shutil.rmtree(
                user_template_dir
            )


        except OSError as error:

            print(
                "WARNING:"
            )

            print(
                "User deleted from database, "
                "but palm template folder could not be removed."
            )

            print(
                error
            )


    print(
        f"Deleted VeinPay user "
        f"{user_id}: {user_name}"
    )


    return jsonify(
        {
            "success": True,

            "message":
                f"User '{user_name}' removed successfully.",

            "preserved_transactions":
                preserved_transactions
        }
    )


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print()

    print(
        "======================================"
    )

    print(
        "        VEINPAY WEB INTERFACE"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Dashboard:"
    )

    print(
        "http://<PI_IP>:5000"
    )

    print()

    print(
        "Register User:"
    )

    print(
        "http://<PI_IP>:5000/enroll"
    )

    print()

    print(
        "Merchant Payment:"
    )

    print(
        "http://<PI_IP>:5000/payment"
    )

    print()

    print(
        "Merchant Wallet:"
    )

    print(
        "http://<PI_IP>:5000/merchant-wallet"
    )

    print()

    print(
        "Payment Scan:"
    )

    print(
        "http://<PI_IP>:5000/scan"
    )

    print()


    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )
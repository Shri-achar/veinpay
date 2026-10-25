import sqlite3
import os
import sys
import shutil
import re


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# ============================================================
# IMPORT CONFIG
# ============================================================

from config import (
    DATABASE_PATH,
    TEMPLATES_DIR,
    DEFAULT_WALLET_BALANCE,
    ENROLLMENT_SAMPLE_COUNT
)


# ============================================================
# CREATE SAFE USER FOLDER NAME
# ============================================================

def make_safe_name(name):

    safe_name = name.strip().lower()

    safe_name = re.sub(
        r"[^a-z0-9]+",
        "_",
        safe_name
    )

    safe_name = safe_name.strip("_")

    return safe_name


# ============================================================
# PHONE VALIDATION
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
        re.match(
            pattern,
            phone_number
        )
    )


# ============================================================
# EMAIL VALIDATION
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
        re.match(
            pattern,
            email
        )
    )


# ============================================================
# REGISTER USER IN DATABASE
# ============================================================

def register_user_in_database(
    name,
    phone_number,
    email,
    template_path,
    wallet_balance
):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()


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
            template_path,
            wallet_balance
        )
    )


    conn.commit()

    user_id = cursor.lastrowid

    conn.close()


    return user_id


# ============================================================
# ENROLL USER
# ============================================================

def enroll_user(
    name,
    sample_paths,
    phone_number="",
    email="",
    wallet_balance=DEFAULT_WALLET_BALANCE
):

    # --------------------------------------------------------
    # CLEAN INPUT
    # --------------------------------------------------------

    name = str(
        name
    ).strip()


    phone_number = str(
        phone_number
    ).strip()


    email = str(
        email
    ).strip()


    # --------------------------------------------------------
    # VALIDATE NAME
    # --------------------------------------------------------

    if name == "":

        return {
            "success": False,
            "message": "User name cannot be empty."
        }


    # --------------------------------------------------------
    # VALIDATE PHONE
    # --------------------------------------------------------

    if not validate_phone_number(
        phone_number
    ):

        return {
            "success": False,
            "message": (
                "Invalid phone number. "
                "Use 10 to 15 digits, optionally "
                "starting with +."
            )
        }


    # --------------------------------------------------------
    # VALIDATE EMAIL
    # --------------------------------------------------------

    if not validate_email(
        email
    ):

        return {
            "success": False,
            "message": "Invalid email address."
        }


    # --------------------------------------------------------
    # VALIDATE WALLET
    # --------------------------------------------------------

    try:

        wallet_balance = float(
            wallet_balance
        )

    except (TypeError, ValueError):

        return {
            "success": False,
            "message": "Invalid wallet balance."
        }


    if wallet_balance < 0:

        return {
            "success": False,
            "message": (
                "Wallet balance cannot be negative."
            )
        }


    # --------------------------------------------------------
    # VALIDATE SAMPLE LIST
    # --------------------------------------------------------

    if not isinstance(
        sample_paths,
        (list, tuple)
    ):

        return {
            "success": False,
            "message": (
                "sample_paths must be a list "
                "of processed palm images."
            )
        }


    # --------------------------------------------------------
    # SAMPLE COUNT
    # --------------------------------------------------------

    if len(
        sample_paths
    ) < ENROLLMENT_SAMPLE_COUNT:

        return {
            "success": False,
            "message": (
                f"Need at least "
                f"{ENROLLMENT_SAMPLE_COUNT} "
                f"processed palm samples."
            )
        }


    # --------------------------------------------------------
    # CHECK FILES EXIST
    # --------------------------------------------------------

    for sample_path in sample_paths:

        if not os.path.exists(
            sample_path
        ):

            return {
                "success": False,
                "message": (
                    "Sample file not found: "
                    f"{sample_path}"
                )
            }


    # ========================================================
    # CREATE TEMPLATE DIRECTORY
    # ========================================================

    os.makedirs(
        TEMPLATES_DIR,
        exist_ok=True
    )


    safe_name = make_safe_name(
        name
    )


    if safe_name == "":

        safe_name = "user"


    base_folder = os.path.join(
        TEMPLATES_DIR,
        safe_name
    )


    user_template_folder = (
        base_folder
    )


    folder_number = 2


    while os.path.exists(
        user_template_folder
    ):

        user_template_folder = (
            f"{base_folder}_{folder_number}"
        )

        folder_number += 1


    os.makedirs(
        user_template_folder
    )


    # ========================================================
    # COPY PALM SAMPLES
    # ========================================================

    stored_sample_paths = []


    for index, source_path in enumerate(
        sample_paths,
        start=1
    ):

        destination_path = os.path.join(
            user_template_folder,
            f"sample_{index:02d}.png"
        )


        shutil.copy2(
            source_path,
            destination_path
        )


        stored_sample_paths.append(
            destination_path
        )


    # ========================================================
    # PRIMARY TEMPLATE
    # ========================================================

    primary_template_path = (
        stored_sample_paths[0]
    )


    # ========================================================
    # SAVE USER
    # ========================================================

    try:

        user_id = register_user_in_database(
            name=name,
            phone_number=phone_number,
            email=email,
            template_path=primary_template_path,
            wallet_balance=wallet_balance
        )


    except sqlite3.Error as error:

        shutil.rmtree(
            user_template_folder,
            ignore_errors=True
        )


        return {
            "success": False,
            "message": (
                "Database error during enrollment: "
                f"{error}"
            )
        }


    # ========================================================
    # SUCCESS
    # ========================================================

    return {
        "success": True,
        "message": "User enrolled successfully.",
        "user_id": user_id,
        "name": name,
        "phone_number": phone_number,
        "email": email,
        "wallet_balance": wallet_balance,
        "template_folder": user_template_folder,
        "primary_template": primary_template_path,
        "samples_stored": len(
            stored_sample_paths
        )
    }


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print()

    print(
        "======================================"
    )

    print(
        "        VEINPAY ENROLLMENT MODULE"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Required palm samples:",
        ENROLLMENT_SAMPLE_COUNT
    )

    print()

    print(
        "Stored user details:"
    )

    print(
        "- Name"
    )

    print(
        "- Phone number"
    )

    print(
        "- Email"
    )

    print(
        "- Wallet balance"
    )

    print(
        "- Palm template"
    )

    print()

    print(
        "Enrollment module ready."
    )
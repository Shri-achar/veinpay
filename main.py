import os
import sys
import time


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.abspath(__file__)
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# ============================================================
# IMPORT CONFIG
# ============================================================

from config import (
    MIN_PALM_DISTANCE_CM,
    MAX_PALM_DISTANCE_CM,
    AUTHENTICATION_THRESHOLD
)


# ============================================================
# IMPORT PROCESSING / PAYMENT MODULES
# ============================================================

from processing.recognition import (
    recognize_user
)

from database.payment import (
    make_payment
)


# ============================================================
# VEINPAY SYSTEM STATE
# ============================================================

system_state = {

    "system": "IDLE",

    "distance": None,

    "temperature": None,

    "ir": "OFF",

    "recognition": "WAITING",

    "user": None,

    "similarity": None,

    "payment": "WAITING",

    "notification": "WAITING"
}


# ============================================================
# HARDWARE PLACEHOLDERS
# ============================================================
#
# These functions are intentionally kept as hardware interfaces.
#
# Later, only the inside of these functions will be replaced
# with real Raspberry Pi hardware code.
#
# The overall main.py structure can remain the same.
# ============================================================


def read_distance():
    """
    Read palm distance from VL53L0X.

    Returns:
        distance in cm

    Hardware implementation will be added later.
    """

    raise NotImplementedError(
        "VL53L0X hardware not connected yet."
    )


def read_temperature():
    """
    Read palm temperature from MLX90614.

    Returns:
        temperature in degrees Celsius

    Hardware implementation will be added later.
    """

    raise NotImplementedError(
        "MLX90614 hardware not connected yet."
    )


def set_ir_leds(enabled):
    """
    Control 850 nm IR illumination through MOSFET.

    Parameters:
        enabled = True  -> IR ON
        enabled = False -> IR OFF
    """

    system_state["ir"] = (
        "ON"
        if enabled
        else
        "OFF"
    )


    # GPIO hardware control will be added later.


def capture_palm_image():
    """
    Capture a palm image using Camera Module 3 NoIR.

    Later this function will return the path to a
    newly captured NIR palm image.

    Example future return:
        captured_images/live_scan.png
    """

    raise NotImplementedError(
        "Camera Module 3 NoIR not connected yet."
    )


def preprocess_live_palm(image_path):
    """
    Process the captured image before recognition.

    This function imports preprocessing here so
    main.py remains simple.
    """

    from processing.preprocess import (
        preprocess_palm
    )


    result = preprocess_palm(
        image_path
    )


    return result["frangi"]


def oled_message(message):
    """
    Display message on OLED.

    Real SH1106/SSD1306 code will be added later.
    """

    print(
        "[OLED]",
        message
    )


def success_feedback():
    """
    Success buzzer/audio feedback.

    Hardware implementation will be added later.
    """

    print(
        "[AUDIO] Payment successful."
    )


def failure_feedback():
    """
    Failure buzzer/audio feedback.

    Hardware implementation will be added later.
    """

    print(
        "[AUDIO] Authentication/payment failed."
    )


# ============================================================
# RESET SYSTEM STATE
# ============================================================

def reset_system_state():

    system_state["system"] = "IDLE"

    system_state["distance"] = None

    system_state["temperature"] = None

    system_state["ir"] = "OFF"

    system_state["recognition"] = "WAITING"

    system_state["user"] = None

    system_state["similarity"] = None

    system_state["payment"] = "WAITING"

    system_state["notification"] = "WAITING"


# ============================================================
# CHECK PALM POSITION
# ============================================================

def check_palm_distance(
    distance
):

    if distance < MIN_PALM_DISTANCE_CM:

        return {
            "valid": False,
            "message": "MOVE PALM BACK"
        }


    if distance > MAX_PALM_DISTANCE_CM:

        return {
            "valid": False,
            "message": "MOVE PALM CLOSER"
        }


    return {
        "valid": True,
        "message": "HOLD PALM"
    }


# ============================================================
# TEMPERATURE PLAUSIBILITY
# ============================================================

def check_temperature(
    temperature
):
    """
    Temporary interface.

    We intentionally do NOT hard-code a universal
    human temperature threshold yet.

    Real limits should be calibrated with the MLX90614
    after hardware testing.

    For now:
        valid numeric reading -> accepted for pipeline
    """

    if temperature is None:

        return False


    try:

        float(
            temperature
        )

    except (TypeError, ValueError):

        return False


    return True


# ============================================================
# AUTHENTICATION
# ============================================================

def authenticate_palm(
    processed_palm
):

    system_state["recognition"] = "PROCESSING"


    result = recognize_user(
        processed_palm
    )


    system_state["similarity"] = (
        result.get(
            "best_score"
        )
    )


    best_user = result.get(
        "best_user"
    )


    if best_user is not None:

        system_state["user"] = (
            best_user.get(
                "name"
            )
        )


    # ========================================================
    # THRESHOLD NOT CALIBRATED
    # ========================================================

    if result.get("matched") is None:

        system_state["recognition"] = (
            "THRESHOLD NOT CALIBRATED"
        )

        return result


    # ========================================================
    # MATCHED
    # ========================================================

    if result.get("matched") is True:

        system_state["recognition"] = (
            "MATCH FOUND"
        )


    else:

        system_state["recognition"] = (
            "NOT RECOGNIZED"
        )


    return result


# ============================================================
# PAYMENT
# ============================================================

def process_payment(
    user_id,
    amount,
    similarity_score
):

    system_state["payment"] = "PROCESSING"


    result = make_payment(
        user_id=user_id,
        amount=amount,
        similarity_score=similarity_score
    )


    if result.get("success"):

        system_state["payment"] = "SUCCESS"


        notification = result.get(
            "notification",
            {}
        )


        system_state["notification"] = (
            notification.get(
                "status",
                "UNKNOWN"
            )
        )


    else:

        system_state["payment"] = "FAILED"


    return result


# ============================================================
# COMPLETE PALM PAYMENT FLOW
# ============================================================

def run_payment_cycle(
    payment_amount
):
    """
    Final VeinPay transaction flow.

    This function is designed to remain largely unchanged
    after hardware is connected.

    Flow:
        Distance
        Temperature
        IR illumination
        Camera capture
        Image preprocessing
        Recognition
        Payment
        Email notification
        OLED/audio feedback
    """

    reset_system_state()


    print()
    print(
        "======================================"
    )

    print(
        "       VEINPAY PAYMENT CYCLE"
    )

    print(
        "======================================"
    )

    print()


    # ========================================================
    # CHECK AUTHENTICATION THRESHOLD
    # ========================================================

    if AUTHENTICATION_THRESHOLD is None:

        print(
            "Authentication threshold has not "
            "been calibrated yet."
        )

        print(
            "Real NIR palm data is required before "
            "final authentication/payment is enabled."
        )

        return {
            "success": False,
            "reason": "THRESHOLD_NOT_CALIBRATED"
        }


    try:

        # ====================================================
        # DISTANCE
        # ====================================================

        system_state["system"] = (
            "CHECKING DISTANCE"
        )


        distance = read_distance()


        system_state["distance"] = (
            distance
        )


        position_result = (
            check_palm_distance(
                distance
            )
        )


        oled_message(
            position_result[
                "message"
            ]
        )


        if not position_result[
            "valid"
        ]:

            return {
                "success": False,
                "reason": (
                    "INVALID_DISTANCE"
                )
            }


        # ====================================================
        # TEMPERATURE
        # ====================================================

        system_state["system"] = (
            "CHECKING TEMPERATURE"
        )


        temperature = (
            read_temperature()
        )


        system_state["temperature"] = (
            temperature
        )


        if not check_temperature(
            temperature
        ):

            oled_message(
                "TEMPERATURE CHECK FAILED"
            )

            failure_feedback()


            return {
                "success": False,
                "reason": (
                    "TEMPERATURE_CHECK_FAILED"
                )
            }


        # ====================================================
        # IR ON
        # ====================================================

        system_state["system"] = (
            "CAPTURING PALM"
        )


        set_ir_leds(
            True
        )


        oled_message(
            "SCANNING..."
        )


        # ====================================================
        # CAMERA CAPTURE
        # ====================================================

        image_path = (
            capture_palm_image()
        )


        # ====================================================
        # IR OFF
        # ====================================================

        set_ir_leds(
            False
        )


        # ====================================================
        # PREPROCESS IMAGE
        # ====================================================

        system_state["system"] = (
            "PROCESSING IMAGE"
        )


        processed_palm = (
            preprocess_live_palm(
                image_path
            )
        )


        # ====================================================
        # RECOGNITION
        # ====================================================

        system_state["system"] = (
            "AUTHENTICATING"
        )


        recognition_result = (
            authenticate_palm(
                processed_palm
            )
        )


        if (
            recognition_result.get(
                "matched"
            )
            is not True
        ):

            oled_message(
                "ACCESS DENIED"
            )

            failure_feedback()


            return {
                "success": False,
                "reason": (
                    recognition_result.get(
                        "reason"
                    )
                )
            }


        best_user = (
            recognition_result[
                "best_user"
            ]
        )


        # ====================================================
        # PAYMENT
        # ====================================================

        system_state["system"] = (
            "PROCESSING PAYMENT"
        )


        payment_result = (
            process_payment(
                user_id=best_user[
                    "user_id"
                ],
                amount=payment_amount,
                similarity_score=recognition_result[
                    "best_score"
                ]
            )
        )


        # ====================================================
        # PAYMENT FAILED
        # ====================================================

        if not payment_result.get(
            "success"
        ):

            oled_message(
                "PAYMENT FAILED"
            )

            failure_feedback()


            return {
                "success": False,
                "reason": (
                    payment_result.get(
                        "message"
                    )
                ),
                "payment": (
                    payment_result
                )
            }


        # ====================================================
        # PAYMENT SUCCESS
        # ====================================================

        system_state["system"] = (
            "PAYMENT SUCCESS"
        )


        oled_message(
            "PAYMENT SUCCESS"
        )


        success_feedback()


        return {
            "success": True,
            "user": best_user,
            "payment": payment_result
        }


    except NotImplementedError as error:

        set_ir_leds(
            False
        )


        system_state["system"] = (
            "WAITING FOR HARDWARE"
        )


        print()
        print(
            "Hardware interface not available:"
        )

        print(
            error
        )


        return {
            "success": False,
            "reason": "HARDWARE_NOT_CONNECTED"
        }


    except Exception as error:

        set_ir_leds(
            False
        )


        system_state["system"] = (
            "SYSTEM ERROR"
        )


        print()
        print(
            "VeinPay error:"
        )

        print(
            error
        )


        return {
            "success": False,
            "reason": "SYSTEM_ERROR",
            "error": str(
                error
            )
        }


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    print()

    print(
        "======================================"
    )

    print(
        "              VEINPAY"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Contactless Palm Vein "
        "Biometric Payment Terminal"
    )

    print()

    print(
        "System software loaded successfully."
    )

    print()


    if AUTHENTICATION_THRESHOLD is None:

        print(
            "Status:"
        )

        print(
            "Waiting for real NIR palm data "
            "and threshold calibration."
        )

    else:

        print(
            "Status:"
        )

        print(
            "Authentication threshold configured."
        )


    print()

    print(
        "Hardware-dependent payment cycle "
        "is not started automatically."
    )

    print()

    print(
        "This prevents accidental wallet deductions "
        "during software development."
    )

    print()


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
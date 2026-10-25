import os
import sys
import time


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


if PROJECT_ROOT not in sys.path:

    sys.path.insert(
        0,
        PROJECT_ROOT
    )


# ============================================================
# IMPORTS
# ============================================================

from processing.recognition import (
    recognize_user
)


from database.payment_processor import (
    process_payment
)


# ============================================================
# FINAL PAYMENT SCAN
# ============================================================

def run_payment_scan(
    request_id,
    frame,
    hardware
):

    # ========================================================
    # CHECK CAMERA FRAME
    # ========================================================

    if frame is None:

        try:

            hardware.show_then_idle(
                "Camera Error",
                "Frame Missing",
                2
            )

        except Exception:

            pass


        return {
            "success": False,
            "authenticated": False,
            "payment_processed": False,
            "message":
                "Camera frame is not available."
        }


    # ========================================================
    # SHOW SCANNING MESSAGE
    # ========================================================

    try:

        hardware.show_scanning()

    except Exception as error:

        print(
            "OLED scanning message error:",
            error
        )


    # Small delay so user can see scanning state
    time.sleep(
        0.5
    )


    # ========================================================
    # PALM RECOGNITION
    # ========================================================

    try:

        recognition_result = (
            recognize_user(
                frame
            )
        )


    except Exception as error:

        try:

            hardware.show_then_idle(
                "Scan Error",
                "Try Again",
                2
            )

        except Exception:

            pass


        return {
            "success": False,
            "authenticated": False,
            "payment_processed": False,
            "request_id": request_id,
            "message":
                "Palm recognition failed: "
                +
                str(error)
        }


    # ========================================================
    # READ RECOGNITION RESULT
    # ========================================================

    best_user = (
        recognition_result.get(
            "best_user"
        )
    )


    matched = (
        recognition_result.get(
            "matched"
        )
    )


    best_score = (
        recognition_result.get(
            "best_score",
            0.0
        )
    )


    # ========================================================
    # NO VALID TEMPLATE / USER
    # ========================================================

    if best_user is None:

        try:

            hardware.failure_beep()

            hardware.show_then_idle(
                "Palm Not Found",
                "Try Again",
                2
            )

        except Exception:

            pass


        return {
            "success": False,
            "authenticated": False,
            "payment_processed": False,
            "request_id": request_id,
            "similarity_score":
                best_score,
            "message":
                recognition_result.get(
                    "reason",
                    "No valid palm template found."
                )
        }


    # ========================================================
    # THRESHOLD NOT CALIBRATED
    # ========================================================

    if matched is None:

        try:

            hardware.show_then_idle(
                "Not Calibrated",
                "Setup Required",
                2
            )

        except Exception:

            pass


        return {
            "success": False,
            "authenticated": False,
            "payment_processed": False,
            "request_id":
                request_id,
            "user_id":
                best_user[
                    "user_id"
                ],
            "user_name":
                best_user[
                    "name"
                ],
            "similarity_score":
                best_score,
            "message":
                recognition_result.get(
                    "reason",
                    "Authentication threshold not calibrated yet."
                )
        }


    # ========================================================
    # AUTHENTICATION FAILED
    # ========================================================

    if matched is False:

        try:

            hardware.failure_beep()

            hardware.show_then_idle(
                "Access Denied",
                "Try Again",
                2
            )

        except Exception:

            pass


        return {
            "success": False,
            "authenticated": False,
            "payment_processed": False,
            "request_id":
                request_id,
            "user_id":
                best_user[
                    "user_id"
                ],
            "user_name":
                best_user[
                    "name"
                ],
            "similarity_score":
                best_score,
            "message":
                recognition_result.get(
                    "reason",
                    "Palm not recognized."
                )
        }


    # ========================================================
    # AUTHENTICATION SUCCESS
    # ========================================================

    try:

        hardware.show_recognized()

    except Exception:

        pass


    time.sleep(
        0.5
    )


    # ========================================================
    # PROCESS PAYMENT
    # ========================================================

    try:

        payment_result = (
            process_payment(
                request_id=request_id,
                user_id=
                    best_user[
                        "user_id"
                    ],
                similarity_score=
                    best_score
            )
        )


    except Exception as error:

        try:

            hardware.failure_beep()

            hardware.show_then_idle(
                "Payment Error",
                "Try Again",
                2
            )

        except Exception:

            pass


        return {
            "success": False,
            "authenticated": True,
            "payment_processed": False,
            "request_id":
                request_id,
            "user_id":
                best_user[
                    "user_id"
                ],
            "user_name":
                best_user[
                    "name"
                ],
            "similarity_score":
                best_score,
            "message":
                "Payment processing failed: "
                +
                str(error)
        }


    # ========================================================
    # PAYMENT SUCCESS
    # ========================================================

    if payment_result.get(
        "success"
    ):

        try:

            hardware.success_beep()


            hardware.show_payment_success(
                payment_result.get(
                    "amount"
                )
            )


            time.sleep(
                3
            )


            hardware.show_idle()


        except Exception as error:

            print(
                "OLED success display error:",
                error
            )


        payment_result[
            "authenticated"
        ] = True


        payment_result[
            "payment_processed"
        ] = True


        payment_result[
            "similarity_score"
        ] = best_score


        return payment_result


    # ========================================================
    # PAYMENT FAILURE
    # ========================================================

    try:

        hardware.failure_beep()


        hardware.show_payment_failed()


        time.sleep(
            2
        )


        hardware.show_idle()


    except Exception:

        pass


    payment_result[
        "authenticated"
    ] = True


    payment_result[
        "payment_processed"
    ] = False


    payment_result[
        "similarity_score"
    ] = best_score


    return payment_result


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "======================================"
    )

    print(
        "   VEINPAY SCAN CONTROLLER"
    )

    print(
        "======================================"
    )

    print()

    print(
        "scan_controller loaded successfully."
    )

    print()
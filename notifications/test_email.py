import os
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(
        PROJECT_ROOT
    )


# ============================================================
# IMPORT EMAIL MODULE
# ============================================================

from notifications.email_notification import (
    send_payment_confirmation
)


# ============================================================
# TEST EMAIL
# ============================================================

def test_email(
    recipient_email
):

    print()
    print(
        "======================================"
    )

    print(
        "        VEINPAY EMAIL TEST"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Recipient:",
        recipient_email
    )

    print()

    print(
        "Sending test payment confirmation..."
    )

    print()


    # ========================================================
    # SEND TEST EMAIL
    # ========================================================
    #
    # IMPORTANT:
    # This does NOT:
    #
    # - deduct wallet money
    # - create a transaction
    # - modify the database
    #
    # It only tests the email system.
    # ========================================================

    result = send_payment_confirmation(
        recipient_email=recipient_email,
        user_name="VeinPay Test User",
        amount=250.00,
        remaining_balance=750.00,
        transaction_id="TEST-001"
    )


    # ========================================================
    # RESULT
    # ========================================================

    print(
        "Status:",
        result.get(
            "status"
        )
    )

    print(
        "Message:",
        result.get(
            "message"
        )
    )

    print()


    if result.get(
        "success"
    ):

        print(
            "VeinPay email system is working correctly."
        )

    else:

        print(
            "VeinPay email test failed."
        )

        print(
            "Check the message above for the reason."
        )


    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Recipient email must be supplied in the command
    #
    # Example:
    #
    # python notifications/test_email.py abc@gmail.com
    # --------------------------------------------------------

    if len(
        sys.argv
    ) < 2:

        print()
        print(
            "Recipient email not provided."
        )

        print()

        print(
            "Run like this:"
        )

        print()

        print(
            "python notifications/test_email.py "
            "your_email@gmail.com"
        )

        print()

        sys.exit(
            1
        )


    recipient = sys.argv[1].strip()


    test_email(
        recipient
    )
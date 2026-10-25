import os
import smtplib
from email.message import EmailMessage
from datetime import datetime


# ============================================================
# VEINPAY EMAIL SETTINGS
# ============================================================

SMTP_SERVER = "smtp.gmail.com"

SMTP_PORT = 465


def get_email_credentials():

    sender_email = os.getenv(
        "VEINPAY_EMAIL"
    )


    app_password = os.getenv(
        "VEINPAY_APP_PASSWORD"
    )


    if not sender_email:

        return None, None


    if not app_password:

        return None, None


    return (
        sender_email.strip(),
        app_password.strip()
    )


def send_payment_confirmation(
    recipient_email,
    user_name,
    amount,
    remaining_balance,
    transaction_id=None,
    transaction_time=None
):

    if recipient_email is None:

        return {
            "success": False,
            "status": "SKIPPED",
            "message": "No email address registered."
        }


    recipient_email = str(
        recipient_email
    ).strip()


    if recipient_email == "":

        return {
            "success": False,
            "status": "SKIPPED",
            "message": "No email address registered."
        }


    (
        sender_email,
        app_password
    ) = get_email_credentials()


    if (
        sender_email is None
        or
        app_password is None
    ):

        return {
            "success": False,
            "status": "NOT CONFIGURED",
            "message": (
                "VeinPay sender email credentials "
                "are not configured."
            )
        }


    if transaction_time is None:

        transaction_time = datetime.now().strftime(
            "%d-%m-%Y %I:%M:%S %p"
        )


    if transaction_id is None:

        transaction_id_display = "N/A"

    else:

        transaction_id_display = str(
            transaction_id
        )


    message = EmailMessage()


    message["From"] = (
        f"VeinPay Payments <{sender_email}>"
    )


    message["To"] = recipient_email


    message["Subject"] = (
        "VeinPay Payment Confirmation"
    )


    body = f"""
Hello {user_name},

Your VeinPay payment was successful.

Payment Details
--------------------------------
Amount Paid: Rs. {float(amount):.2f}
Remaining Balance: Rs. {float(remaining_balance):.2f}
Transaction ID: {transaction_id_display}
Date & Time: {transaction_time}
--------------------------------

This transaction was authenticated using the
VeinPay palm-vein payment terminal.

Thank you for using VeinPay.

VeinPay
Pay with your palm.
"""


    message.set_content(
        body
    )


    try:

        with smtplib.SMTP_SSL(
            SMTP_SERVER,
            SMTP_PORT,
            timeout=10
        ) as smtp:


            smtp.login(
                sender_email,
                app_password
            )


            smtp.send_message(
                message
            )


        return {
            "success": True,
            "status": "SENT",
            "message": (
                "Payment confirmation email sent."
            )
        }


    except smtplib.SMTPAuthenticationError:

        return {
            "success": False,
            "status": "AUTHENTICATION FAILED",
            "message": (
                "Gmail rejected the sender credentials. "
                "Check the App Password."
            )
        }


    except (
        smtplib.SMTPException,
        OSError
    ) as error:

        return {
            "success": False,
            "status": "FAILED",
            "message": str(
                error
            )
        }


if __name__ == "__main__":

    print()

    print(
        "======================================"
    )

    print(
        "       VEINPAY EMAIL MODULE"
    )

    print(
        "======================================"
    )

    print()


    sender_email, app_password = (
        get_email_credentials()
    )


    if (
        sender_email
        and
        app_password
    ):

        print(
            "Sender email:",
            sender_email
        )

        print(
            "App Password: CONFIGURED"
        )

        print()

        print(
            "Email module is ready."
        )


    else:

        print(
            "Email credentials are not configured."
        )

        print()

        print(
            "Set:"
        )

        print(
            "VEINPAY_EMAIL"
        )

        print(
            "VEINPAY_APP_PASSWORD"
        )
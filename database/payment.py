import sqlite3
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
    sys.path.append(PROJECT_ROOT)


# ============================================================
# IMPORT PROJECT MODULES
# ============================================================

from config import DATABASE_PATH

from notifications.email_notification import (
    send_payment_confirmation
)


# ============================================================
# UPDATE NOTIFICATION STATUS
# ============================================================

def update_notification_status(
    transaction_id,
    notification_status
):
    """
    Update the email notification status
    after the payment transaction has already
    been safely committed.
    """

    try:

        conn = sqlite3.connect(
            DATABASE_PATH
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            UPDATE transactions

            SET notification_status = ?

            WHERE transaction_id = ?
            """,
            (
                notification_status,
                transaction_id
            )
        )


        conn.commit()

        conn.close()


    except sqlite3.Error as error:

        print(
            "Unable to update notification status:",
            error
        )


# ============================================================
# PAYMENT FUNCTION
# ============================================================

def make_payment(
    user_id,
    amount,
    similarity_score=None
):
    """
    Process a VeinPay wallet payment.

    Permanent payment sequence:

        1. Validate amount
        2. Read user and wallet
        3. Check balance
        4. Deduct wallet balance
        5. Create transaction
        6. Commit both together
        7. Send optional email
        8. Store notification result

    Email failure never reverses a successful payment.
    """

    # ========================================================
    # VALIDATE USER ID
    # ========================================================

    try:

        user_id = int(
            user_id
        )

    except (TypeError, ValueError):

        return {
            "success": False,
            "message": "Invalid user ID."
        }


    if user_id <= 0:

        return {
            "success": False,
            "message": "Invalid user ID."
        }


    # ========================================================
    # VALIDATE AMOUNT
    # ========================================================

    try:

        amount = float(
            amount
        )

    except (TypeError, ValueError):

        return {
            "success": False,
            "message": "Invalid payment amount."
        }


    if amount <= 0:

        return {
            "success": False,
            "message": (
                "Payment amount must be greater than zero."
            )
        }


    # ========================================================
    # DATABASE CONNECTION
    # ========================================================

    conn = None


    try:

        conn = sqlite3.connect(
            DATABASE_PATH
        )


        cursor = conn.cursor()


        # ====================================================
        # BEGIN TRANSACTION
        # ====================================================

        cursor.execute(
            "BEGIN IMMEDIATE"
        )


        # ====================================================
        # FIND USER
        # ====================================================

        cursor.execute(
            """
            SELECT
                name,
                email,
                wallet_balance

            FROM users

            WHERE user_id = ?
            """,
            (
                user_id,
            )
        )


        user = cursor.fetchone()


        if user is None:

            conn.rollback()

            conn.close()


            return {
                "success": False,
                "message": "User not found."
            }


        name = user[0]

        email = user[1]

        balance = float(
            user[2]
        )


        # ====================================================
        # INSUFFICIENT BALANCE
        # ====================================================

        if balance < amount:

            cursor.execute(
                """
                INSERT INTO transactions
                (
                    user_id,
                    amount,
                    status,
                    similarity_score,
                    notification_status
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
                    user_id,
                    amount,
                    "FAILED - INSUFFICIENT BALANCE",
                    similarity_score,
                    "NOT SENT"
                )
            )


            transaction_id = (
                cursor.lastrowid
            )


            conn.commit()


            cursor.execute(
                """
                SELECT timestamp

                FROM transactions

                WHERE transaction_id = ?
                """,
                (
                    transaction_id,
                )
            )


            timestamp_row = (
                cursor.fetchone()
            )


            transaction_time = (
                timestamp_row[0]
                if timestamp_row
                else None
            )


            conn.close()


            return {
                "success": False,
                "message": "Insufficient balance.",
                "transaction_id": transaction_id,
                "transaction_time": transaction_time,
                "name": name,
                "amount": amount,
                "balance": balance,
                "notification": {
                    "success": False,
                    "status": "NOT SENT",
                    "message": (
                        "No confirmation email sent "
                        "because the payment failed."
                    )
                }
            }


        # ====================================================
        # CALCULATE NEW BALANCE
        # ====================================================

        new_balance = (
            balance
            -
            amount
        )


        # ====================================================
        # UPDATE WALLET
        # ====================================================

        cursor.execute(
            """
            UPDATE users

            SET wallet_balance = ?

            WHERE user_id = ?
            """,
            (
                new_balance,
                user_id
            )
        )


        # ====================================================
        # STORE SUCCESSFUL TRANSACTION
        # ====================================================

        cursor.execute(
            """
            INSERT INTO transactions
            (
                user_id,
                amount,
                status,
                similarity_score,
                notification_status
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
                user_id,
                amount,
                "SUCCESS",
                similarity_score,
                "PENDING"
            )
        )


        transaction_id = (
            cursor.lastrowid
        )


        # ====================================================
        # COMMIT WALLET + TRANSACTION TOGETHER
        # ====================================================

        conn.commit()


        # ====================================================
        # READ EXACT TRANSACTION TIMESTAMP
        # ====================================================

        cursor.execute(
            """
            SELECT timestamp

            FROM transactions

            WHERE transaction_id = ?
            """,
            (
                transaction_id,
            )
        )


        timestamp_row = (
            cursor.fetchone()
        )


        transaction_time = (
            timestamp_row[0]
            if timestamp_row
            else None
        )


        conn.close()


    # ========================================================
    # DATABASE FAILURE
    # ========================================================

    except sqlite3.Error as error:

        if conn is not None:

            try:

                conn.rollback()

                conn.close()

            except sqlite3.Error:

                pass


        return {
            "success": False,
            "message": (
                "Database transaction failed: "
                + str(error)
            )
        }


    # ========================================================
    # EMAIL CONFIRMATION
    # ========================================================
    #
    # The payment is ALREADY committed here.
    #
    # Email cannot undo or cancel the transaction.
    # ========================================================

    notification_result = (
        send_payment_confirmation(
            recipient_email=email,
            user_name=name,
            amount=amount,
            remaining_balance=new_balance,
            transaction_id=transaction_id,
            transaction_time=transaction_time
        )
    )


    # ========================================================
    # SAVE NOTIFICATION RESULT
    # ========================================================

    notification_status = (
        notification_result.get(
            "status",
            "UNKNOWN"
        )
    )


    update_notification_status(
        transaction_id,
        notification_status
    )


    # ========================================================
    # FINAL RESULT
    # ========================================================

    return {
        "success": True,
        "message": "Payment successful.",
        "transaction_id": transaction_id,
        "transaction_time": transaction_time,
        "name": name,
        "email": email,
        "amount": amount,
        "balance": new_balance,
        "notification": notification_result
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
        "        VEINPAY PAYMENT MODULE"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Payment module loaded successfully."
    )

    print()

    print(
        "Wallet deduction and transaction logging "
        "are now atomic."
    )

    print()

    print(
        "No payment is executed by running "
        "this file directly."
    )
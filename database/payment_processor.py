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
    sys.path.insert(0, PROJECT_ROOT)


from config import DATABASE_PATH


# ============================================================
# PROCESS PAYMENT
# ============================================================

def process_payment(
    request_id,
    user_id,
    similarity_score=None
):

    conn = None

    try:

        request_id = int(request_id)
        user_id = int(user_id)

        conn = sqlite3.connect(
            DATABASE_PATH
        )

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute(
            "PRAGMA foreign_keys = ON"
        )

        # Lock database while payment is processed
        cursor.execute(
            "BEGIN IMMEDIATE"
        )


        # ====================================================
        # GET PAYMENT REQUEST
        # ====================================================

        cursor.execute(
            """
            SELECT
                request_id,
                merchant_id,
                amount,
                status

            FROM payment_requests

            WHERE request_id = ?
            """,
            (
                request_id,
            )
        )

        payment_request = cursor.fetchone()

        if payment_request is None:

            conn.rollback()

            return {
                "success": False,
                "message": "Payment request not found."
            }


        if payment_request["status"] != "PENDING":

            conn.rollback()

            return {
                "success": False,
                "message": "Payment request is no longer pending."
            }


        amount = float(
            payment_request["amount"]
        )

        merchant_id = int(
            payment_request["merchant_id"]
        )


        # ====================================================
        # GET USER
        # ====================================================

        cursor.execute(
            """
            SELECT
                name,
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

            return {
                "success": False,
                "message": "User not found."
            }


        user_name = user["name"]

        user_balance = float(
            user["wallet_balance"]
        )


        # ====================================================
        # CHECK BALANCE
        # ====================================================

        if user_balance < amount:

            conn.rollback()

            return {
                "success": False,
                "message": "Insufficient wallet balance.",
                "user_id": user_id,
                "user_name": user_name,
                "amount": amount,
                "balance": user_balance
            }


        # ====================================================
        # CHECK MERCHANT
        # ====================================================

        cursor.execute(
            """
            SELECT
                merchant_name,
                shop_name,
                wallet_balance

            FROM merchants

            WHERE merchant_id = ?
            """,
            (
                merchant_id,
            )
        )

        merchant = cursor.fetchone()

        if merchant is None:

            conn.rollback()

            return {
                "success": False,
                "message": "Merchant not found."
            }


        merchant_balance = float(
            merchant["wallet_balance"]
        )


        # ====================================================
        # UPDATE USER WALLET
        # ====================================================

        new_user_balance = (
            user_balance - amount
        )

        cursor.execute(
            """
            UPDATE users

            SET wallet_balance = ?

            WHERE user_id = ?
            """,
            (
                new_user_balance,
                user_id
            )
        )


        # ====================================================
        # UPDATE MERCHANT WALLET
        # ====================================================

        new_merchant_balance = (
            merchant_balance + amount
        )

        cursor.execute(
            """
            UPDATE merchants

            SET wallet_balance = ?

            WHERE merchant_id = ?
            """,
            (
                new_merchant_balance,
                merchant_id
            )
        )


        # ====================================================
        # CREATE TRANSACTION
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
                "NOT SENT"
            )
        )

        transaction_id = (
            cursor.lastrowid
        )


        # ====================================================
        # COMPLETE PAYMENT REQUEST
        # ====================================================

        cursor.execute(
            """
            UPDATE payment_requests

            SET
                status = 'COMPLETED',
                transaction_id = ?,
                completed_at = CURRENT_TIMESTAMP

            WHERE request_id = ?
            AND status = 'PENDING'
            """,
            (
                transaction_id,
                request_id
            )
        )

        if cursor.rowcount != 1:

            conn.rollback()

            return {
                "success": False,
                "message": "Unable to complete payment request."
            }


        # ====================================================
        # COMMIT EVERYTHING TOGETHER
        # ====================================================

        conn.commit()


        return {
            "success": True,
            "message": "Payment successful.",
            "request_id": request_id,
            "transaction_id": transaction_id,
            "user_id": user_id,
            "user_name": user_name,
            "merchant_id": merchant_id,
            "merchant_name": merchant["merchant_name"],
            "shop_name": merchant["shop_name"],
            "amount": amount,
            "balance": new_user_balance,
            "merchant_balance": new_merchant_balance,
            "similarity_score": similarity_score
        }


    except Exception as error:

        if conn is not None:

            try:
                conn.rollback()
            except Exception:
                pass

        return {
            "success": False,
            "message": (
                "Payment processing failed: "
                + str(error)
            )
        }


    finally:

        if conn is not None:

            try:
                conn.close()
            except Exception:
                pass


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "VeinPay payment_processor module loaded successfully."
    )
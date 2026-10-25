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
# CREATE PAYMENT REQUEST
# ============================================================

def create_payment_request(
    amount,
    merchant_id
):

    amount = float(amount)
    merchant_id = int(merchant_id)

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO payment_requests
        (
            merchant_id,
            amount,
            status
        )
        VALUES
        (
            ?,
            ?,
            'PENDING'
        )
        """,
        (
            merchant_id,
            amount
        )
    )

    request_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return request_id


# ============================================================
# GET PAYMENT REQUEST
# ============================================================

def get_payment_request(
    request_id
):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            request_id,
            merchant_id,
            amount,
            status,
            transaction_id,
            created_at,
            completed_at

        FROM payment_requests

        WHERE request_id = ?
        """,
        (
            int(request_id),
        )
    )

    row = cursor.fetchone()

    conn.close()

    return row


# ============================================================
# MARK PAYMENT REQUEST COMPLETED
# ============================================================

def complete_payment_request(
    request_id,
    transaction_id
):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

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
            int(transaction_id),
            int(request_id)
        )
    )

    changed = cursor.rowcount

    conn.commit()
    conn.close()

    return changed > 0


# ============================================================
# MARK PAYMENT REQUEST FAILED
# ============================================================

def fail_payment_request(
    request_id
):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE payment_requests

        SET
            status = 'FAILED',
            completed_at = CURRENT_TIMESTAMP

        WHERE request_id = ?
        AND status = 'PENDING'
        """,
        (
            int(request_id),
        )
    )

    changed = cursor.rowcount

    conn.commit()
    conn.close()

    return changed > 0


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print(
        "VeinPay payment_requests module loaded successfully."
    )
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
# ENSURE DEMO MERCHANT
# ============================================================

def ensure_demo_merchant():

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT merchant_id
        FROM merchants
        ORDER BY merchant_id
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    if row is not None:

        merchant_id = row[0]

        conn.close()

        return merchant_id


    cursor.execute(
        """
        INSERT INTO merchants
        (
            merchant_name,
            shop_name,
            phone_number,
            email,
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
            "Demo Merchant",
            "VeinPay Store",
            "",
            "",
            0.0
        )
    )

    merchant_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return merchant_id


# ============================================================
# GET MERCHANT
# ============================================================

def get_merchant(
    merchant_id
):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            merchant_id,
            merchant_name,
            shop_name,
            phone_number,
            email,
            wallet_balance,
            created_at

        FROM merchants

        WHERE merchant_id = ?
        """,
        (
            int(merchant_id),
        )
    )

    merchant = cursor.fetchone()

    conn.close()

    return merchant


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    merchant_id = ensure_demo_merchant()

    merchant = get_merchant(
        merchant_id
    )

    print("Merchant module loaded successfully.")

    print(
        dict(merchant)
        if merchant is not None
        else "Merchant not found."
    )
    
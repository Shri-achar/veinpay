import sqlite3
import os
import sys

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import DATABASE_PATH


def column_exists(cursor, table_name, column_name):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()

    return any(
        column[1] == column_name
        for column in columns
    )


def migrate():

    print()
    print("======================================")
    print(" VEINPAY MERCHANT PAYMENT MIGRATION")
    print("======================================")
    print()

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()

    cursor.execute(
        "PRAGMA foreign_keys = ON"
    )

    # ========================================================
    # MERCHANTS
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS merchants
        (
            merchant_id INTEGER PRIMARY KEY AUTOINCREMENT,

            merchant_name TEXT NOT NULL,

            shop_name TEXT NOT NULL,

            phone_number TEXT,

            email TEXT,

            wallet_balance REAL NOT NULL DEFAULT 0.0,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # ========================================================
    # PAYMENT REQUESTS
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_requests
        (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,

            merchant_id INTEGER NOT NULL,

            amount REAL NOT NULL,

            status TEXT NOT NULL DEFAULT 'PENDING',

            transaction_id INTEGER,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            completed_at DATETIME,

            FOREIGN KEY(merchant_id)
                REFERENCES merchants(merchant_id),

            FOREIGN KEY(transaction_id)
                REFERENCES transactions(transaction_id)
        )
        """
    )

    # ========================================================
    # INDEXES
    # ========================================================

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_payment_requests_merchant

        ON payment_requests(merchant_id)
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_payment_requests_status

        ON payment_requests(status)
        """
    )

    conn.commit()

    # ========================================================
    # DEMO MERCHANT
    # ========================================================

    cursor.execute(
        """
        SELECT merchant_id

        FROM merchants

        LIMIT 1
        """
    )

    merchant = cursor.fetchone()

    if merchant is None:

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

        conn.commit()

        print(
            "Demo merchant created."
        )

    else:

        print(
            "Merchant already exists."
        )

    conn.close()

    print()
    print("Migration completed.")
    print()
    print("Database:")
    print(DATABASE_PATH)
    print()


if __name__ == "__main__":
    migrate()
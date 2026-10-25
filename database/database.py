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


from config import DATABASE_PATH


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    database_folder = os.path.dirname(
        DATABASE_PATH
    )


    os.makedirs(
        database_folder,
        exist_ok=True
    )


    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()


    cursor.execute(
        "PRAGMA foreign_keys = ON"
    )


    # ========================================================
    # USERS
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users
        (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            phone_number TEXT,

            email TEXT,

            template_path TEXT NOT NULL,

            wallet_balance REAL NOT NULL DEFAULT 1000.0,

            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


    # ========================================================
    # TRANSACTIONS
    # ========================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions
        (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            amount REAL NOT NULL,

            status TEXT NOT NULL,

            similarity_score REAL,

            notification_status TEXT DEFAULT 'NOT SENT',

            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(user_id)
            REFERENCES users(user_id)
        )
        """
    )


    conn.commit()

    conn.close()


    print()

    print(
        "======================================"
    )

    print(
        "        VEINPAY DATABASE READY"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Database:"
    )

    print(
        DATABASE_PATH
    )

    print()


if __name__ == "__main__":

    create_database()
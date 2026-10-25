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
# CHECK COLUMN
# ============================================================

def column_exists(
    cursor,
    table_name,
    column_name
):

    cursor.execute(
        f"PRAGMA table_info({table_name})"
    )

    columns = cursor.fetchall()


    for column in columns:

        if column[1] == column_name:
            return True


    return False


# ============================================================
# MIGRATION
# ============================================================

def migrate_database():

    print()

    print(
        "======================================"
    )

    print(
        "   VEINPAY NOTIFICATION MIGRATION"
    )

    print(
        "======================================"
    )

    print()


    if not os.path.exists(
        DATABASE_PATH
    ):

        print(
            "Database not found:"
        )

        print(
            DATABASE_PATH
        )

        return


    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()


    if not column_exists(
        cursor,
        "transactions",
        "notification_status"
    ):

        cursor.execute(
            """
            ALTER TABLE transactions
            ADD COLUMN notification_status TEXT
            DEFAULT 'NOT SENT'
            """
        )

        print(
            "Added column: notification_status"
        )

    else:

        print(
            "notification_status already exists."
        )


    conn.commit()

    conn.close()


    print()

    print(
        "Migration completed successfully."
    )

    print()


if __name__ == "__main__":

    migrate_database()
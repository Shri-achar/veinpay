import sqlite3
import os
import sys


# ============================================================
# ALLOW IMPORT FROM PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)


# ============================================================
# IMPORT CONFIG
# ============================================================

from config import DATABASE_PATH


# ============================================================
# CHECK IF COLUMN EXISTS
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

        existing_column_name = column[1]

        if (
            existing_column_name
            ==
            column_name
        ):

            return True


    return False


# ============================================================
# MIGRATE DATABASE
# ============================================================

def migrate_database():

    print()
    print(
        "======================================"
    )

    print(
        "   VEINGATE DATABASE MIGRATION"
    )

    print(
        "======================================"
    )

    print()


    # --------------------------------------------------------
    # CHECK DATABASE
    # --------------------------------------------------------

    if not os.path.exists(
        DATABASE_PATH
    ):

        print(
            "ERROR:"
        )

        print(
            "Database does not exist."
        )

        print()

        print(
            DATABASE_PATH
        )

        return


    # --------------------------------------------------------
    # CONNECT
    # --------------------------------------------------------

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()


    # ========================================================
    # PHONE NUMBER
    # ========================================================

    if not column_exists(
        cursor,
        "users",
        "phone_number"
    ):

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN phone_number TEXT
        """)

        print(
            "Added column: phone_number"
        )

    else:

        print(
            "phone_number already exists."
        )


    # ========================================================
    # EMAIL
    # ========================================================

    if not column_exists(
        cursor,
        "users",
        "email"
    ):

        cursor.execute("""
            ALTER TABLE users
            ADD COLUMN email TEXT
        """)

        print(
            "Added column: email"
        )

    else:

        print(
            "email already exists."
        )


    # ========================================================
    # SAVE CHANGES
    # ========================================================

    conn.commit()

    conn.close()


    print()

    print(
        "Migration completed successfully."
    )

    print()

    print(
        "Existing users and transactions were preserved."
    )

    print()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    migrate_database()
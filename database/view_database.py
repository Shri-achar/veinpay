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
# VIEW DATABASE
# ============================================================

def view_database():

    if not os.path.exists(
        DATABASE_PATH
    ):

        print()

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


    # ========================================================
    # USERS
    # ========================================================

    print()

    print(
        "======================================"
    )

    print(
        "          REGISTERED USERS"
    )

    print(
        "======================================"
    )

    print()


    cursor.execute(
        """
        SELECT
            user_id,
            name,
            phone_number,
            email,
            wallet_balance,
            template_path

        FROM users

        ORDER BY user_id
        """
    )


    users = cursor.fetchall()


    if len(users) == 0:

        print(
            "No users registered."
        )

    else:

        for user in users:

            (
                user_id,
                name,
                phone_number,
                email,
                wallet_balance,
                template_path
            ) = user


            print(
                "User ID:",
                user_id
            )

            print(
                "Name:",
                name
            )

            print(
                "Phone:",
                phone_number
                if phone_number
                else "-"
            )

            print(
                "Email:",
                email
                if email
                else "-"
            )

            print(
                "Wallet Balance:",
                f"Rs. {wallet_balance:.2f}"
            )

            print(
                "Template:",
                template_path
            )

            print(
                "--------------------------------------"
            )


    # ========================================================
    # TRANSACTIONS
    # ========================================================

    print()

    print(
        "======================================"
    )

    print(
        "            TRANSACTIONS"
    )

    print(
        "======================================"
    )

    print()


    cursor.execute(
        """
        SELECT
            transaction_id,
            user_id,
            amount,
            status,
            similarity_score,
            notification_status,
            timestamp

        FROM transactions

        ORDER BY transaction_id DESC
        """
    )


    transactions = cursor.fetchall()


    if len(transactions) == 0:

        print(
            "No transactions found."
        )

    else:

        for transaction in transactions:

            (
                transaction_id,
                user_id,
                amount,
                status,
                similarity_score,
                notification_status,
                timestamp
            ) = transaction


            print(
                "Transaction ID:",
                transaction_id
            )

            print(
                "User ID:",
                user_id
            )

            print(
                "Amount:",
                f"Rs. {amount:.2f}"
            )

            print(
                "Status:",
                status
            )


            if similarity_score is None:

                print(
                    "Similarity Score:",
                    "-"
                )

            else:

                print(
                    "Similarity Score:",
                    f"{similarity_score:.2f}%"
                )


            print(
                "Notification:",
                notification_status
                if notification_status
                else "-"
            )


            print(
                "Timestamp:",
                timestamp
            )

            print(
                "--------------------------------------"
            )


    conn.close()


if __name__ == "__main__":

    view_database()
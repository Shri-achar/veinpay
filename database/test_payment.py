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

from database.payment import (
    make_payment
)


# ============================================================
# GET USER DETAILS
# ============================================================

def get_user_details(
    user_id
):

    conn = sqlite3.connect(
        DATABASE_PATH
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT
            user_id,
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

    conn.close()


    if user is None:

        return None


    return {
        "user_id": user[0],
        "name": user[1],
        "email": user[2],
        "wallet_balance": float(
            user[3]
        )
    }


# ============================================================
# READ USER ID
# ============================================================

def read_user_id():

    while True:

        value = input(
            "Enter User ID: "
        ).strip()


        try:

            user_id = int(
                value
            )

        except ValueError:

            print()
            print(
                "Invalid User ID."
            )
            print()

            continue


        if user_id <= 0:

            print()
            print(
                "User ID must be greater than 0."
            )
            print()

            continue


        return user_id


# ============================================================
# READ PAYMENT AMOUNT
# ============================================================

def read_amount():

    while True:

        value = input(
            "Enter payment amount: Rs. "
        ).strip()


        try:

            amount = float(
                value
            )

        except ValueError:

            print()
            print(
                "Invalid amount."
            )
            print()

            continue


        if amount <= 0:

            print()
            print(
                "Amount must be greater than 0."
            )
            print()

            continue


        return amount


# ============================================================
# CONFIRM PAYMENT
# ============================================================

def confirm_payment(
    user,
    amount
):

    current_balance = (
        user[
            "wallet_balance"
        ]
    )


    expected_balance = (
        current_balance
        -
        amount
    )


    print()
    print(
        "======================================"
    )

    print(
        "          PAYMENT CONFIRMATION"
    )

    print(
        "======================================"
    )

    print()


    print(
        "User ID:",
        user[
            "user_id"
        ]
    )


    print(
        "Name:",
        user[
            "name"
        ]
    )


    print(
        "Email:",
        user[
            "email"
        ]
        if user[
            "email"
        ]
        else "-"
    )


    print(
        "Current Balance:",
        f"Rs. {current_balance:.2f}"
    )


    print(
        "Payment Amount:",
        f"Rs. {amount:.2f}"
    )


    if expected_balance >= 0:

        print(
            "Expected Balance:",
            f"Rs. {expected_balance:.2f}"
        )

    else:

        print(
            "Expected Balance:",
            "INSUFFICIENT FUNDS"
        )


    print()

    print(
        "WARNING:"
    )

    print(
        "Typing YES will execute a real "
        "VeinPay wallet transaction."
    )

    print()


    confirmation = input(
        "Type YES to continue: "
    ).strip().upper()


    return (
        confirmation == "YES"
    )


# ============================================================
# SHOW PAYMENT RESULT
# ============================================================

def show_result(
    result
):

    print()

    print(
        "======================================"
    )

    print(
        "            PAYMENT RESULT"
    )

    print(
        "======================================"
    )

    print()


    print(
        "Success:",
        result.get(
            "success"
        )
    )


    print(
        "Message:",
        result.get(
            "message"
        )
    )


    if result.get(
        "transaction_id"
    ) is not None:

        print(
            "Transaction ID:",
            result.get(
                "transaction_id"
            )
        )


    if result.get(
        "transaction_time"
    ) is not None:

        print(
            "Transaction Time:",
            result.get(
                "transaction_time"
            )
        )


    if result.get(
        "name"
    ) is not None:

        print(
            "User:",
            result.get(
                "name"
            )
        )


    if result.get(
        "amount"
    ) is not None:

        print(
            "Amount:",
            f"Rs. {float(result.get('amount')):.2f}"
        )


    if result.get(
        "balance"
    ) is not None:

        print(
            "Remaining Balance:",
            f"Rs. {float(result.get('balance')):.2f}"
        )


    notification = result.get(
        "notification"
    )


    if notification:

        print()

        print(
            "Notification Status:",
            notification.get(
                "status"
            )
        )


        print(
            "Notification Message:",
            notification.get(
                "message"
            )
        )


    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print()

    print(
        "======================================"
    )

    print(
        "        VEINPAY PAYMENT TEST"
    )

    print(
        "======================================"
    )

    print()

    print(
        "This utility executes a real "
        "VeinPay wallet transaction."
    )

    print()

    print(
        "Biometric authentication is not "
        "used in this test."
    )

    print()


    # ========================================================
    # USER ID
    # ========================================================

    user_id = read_user_id()


    # ========================================================
    # GET USER
    # ========================================================

    user = get_user_details(
        user_id
    )


    if user is None:

        print()
        print(
            "User not found."
        )
        print()

        return


    # ========================================================
    # SHOW USER BEFORE AMOUNT
    # ========================================================

    print()

    print(
        "Selected User:"
    )

    print(
        user[
            "name"
        ]
    )

    print(
        "Current Balance:",
        f"Rs. {user['wallet_balance']:.2f}"
    )

    print()


    # ========================================================
    # PAYMENT AMOUNT
    # ========================================================

    amount = read_amount()


    # ========================================================
    # CONFIRM
    # ========================================================

    if not confirm_payment(
        user,
        amount
    ):

        print()

        print(
            "Payment cancelled."
        )

        print()

        return


    # ========================================================
    # EXECUTE PAYMENT
    # ========================================================

    result = make_payment(
        user_id=user_id,
        amount=amount,
        similarity_score=None
    )


    # ========================================================
    # SHOW RESULT
    # ========================================================

    show_result(
        result
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()
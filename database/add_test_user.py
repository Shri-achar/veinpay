import sqlite3

DB_PATH = "database/veingate.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO users
    (
        name,
        template_path,
        wallet_balance
    )
    VALUES (?, ?, ?)
    """,
    (
        "Test User",
        "templates/test_user_template.png",
        1000.0
    )
)

conn.commit()

print("Test user created.")
print("User ID:", cursor.lastrowid)
print("Initial balance: ₹1000")

conn.close()
import sqlite3

DB_PATH = "database/veingate.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Keep the first Test User only
cursor.execute("""
SELECT user_id
FROM users
WHERE name = 'Test User'
ORDER BY user_id
""")

rows = cursor.fetchall()

if len(rows) > 1:
    keep_id = rows[0][0]

    for row in rows[1:]:
        cursor.execute(
            "DELETE FROM users WHERE user_id = ?",
            (row[0],)
        )

    conn.commit()

    print(f"Duplicate Test Users removed. Kept User ID {keep_id}.")

else:
    print("No duplicate Test Users found.")

conn.close()
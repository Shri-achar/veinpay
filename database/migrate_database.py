import sqlite3

DB_PATH = "database/veingate.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Check existing columns
cursor.execute("PRAGMA table_info(transactions)")
columns = [row[1] for row in cursor.fetchall()]

if "similarity_score" not in columns:

    cursor.execute("""
        ALTER TABLE transactions
        ADD COLUMN similarity_score REAL
    """)

    print("similarity_score column added successfully.")

else:
    print("similarity_score column already exists.")

conn.commit()
conn.close()

print("Database migration complete.")
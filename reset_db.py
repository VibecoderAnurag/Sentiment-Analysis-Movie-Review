import sqlite3

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect("reviews.db")
cursor = conn.cursor()

# ❗ Drop the existing table (THIS WILL DELETE ALL DATA)
cursor.execute("DROP TABLE IF EXISTS reviews")

# ✅ Create a new table with correct columns
cursor.execute("""
    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_name TEXT NOT NULL,
        review_text TEXT NOT NULL,
        sentiment TEXT NOT NULL
    )
""")

# Commit and close connection
conn.commit()
conn.close()

print("✅ Database reset successfully!")

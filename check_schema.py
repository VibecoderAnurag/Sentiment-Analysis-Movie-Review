import sqlite3

# Connect to the SQLite database
conn = sqlite3.connect('reviews.db')  # Ensure this is the correct DB file
cursor = conn.cursor()

# Get column details of the 'reviews' table
cursor.execute("PRAGMA table_info(reviews);")
columns = cursor.fetchall()

# Print column names
print("📢 Column names in 'reviews' table:")
for column in columns:
    print(column)

conn.close()

from database import db  # your database.py

# Test database connection
try:
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print("✅ Connected to database successfully!")
        print("Tables in the database:", tables)
except Exception as e:
    print("❌ Database connection failed:", e)

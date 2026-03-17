import mysql.connector  # type: ignore
try:
    print("Connecting to db...")
    conn = mysql.connector.connect(host='localhost', database='title_similarity', user='root', password='raji@123')
    cursor = conn.cursor()
    
    # Try adding columns if they don't exist
    columns = [
        ("student_email", "VARCHAR(100)"),
        ("similar_title", "TEXT"),
        ("similarity_score", "FLOAT"),
        ("status", "VARCHAR(50)"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]
    for col, definition in columns:
        try:
            cursor.execute(f"ALTER TABLE project_titles ADD COLUMN {col} {definition}")
            print(f"Added column {col}")
        except Exception as e:
            print(f"Column {col} might already exist or error: {e}")

    conn.commit()
    cursor.close()
    conn.close()
    print("Completed DB changes successfully")
except Exception as e:
    print("General error:", e)

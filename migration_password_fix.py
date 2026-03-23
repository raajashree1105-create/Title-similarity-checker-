import mysql.connector  # type: ignore

def run_migration():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='title_similarity',
            user='root',
            password='raji@123'
        )
        cursor = conn.cursor()
        
        # 1. Increase password length for hashing
        print("Updating password column size...")
        cursor.execute("ALTER TABLE users MODIFY COLUMN password VARCHAR(255)")
        conn.commit()
        
        print("Migration completed successfully.")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error during migration: {e}")

if __name__ == "__main__":
    run_migration()

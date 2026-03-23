import mysql.connector  # type: ignore

def check_all_users():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='title_similarity',
            user='root',
            password='raji@123'
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, email, password, role FROM users")
        users = cursor.fetchall()
        for user in users:
            print(f"ID: {user['id']} | Email: {user['email']} | Role: {user['role']}")
            print(f"Password starts with: {user['password'][:20]}...")
            if ":" in user['password']:
              print("Password is HASHED.")
            else:
              print("Password is PLAIN TEXT.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_all_users()

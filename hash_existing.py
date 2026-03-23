import mysql.connector  # type: ignore
from werkzeug.security import generate_password_hash  # type: ignore

def hash_existing_passwords():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='title_similarity',
            user='root',
            password='raji@123'
        )
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT id, password FROM users")
        users = cursor.fetchall()
        
        for user in users:
            # Skip if already hashed (Werkzeug hashes usually start with pbkdf2:sha256: or scrypt:)
            if ":" in user['password'] and len(user['password']) > 50:
                print(f"User {user['id']} already has a hashed password.")
                continue
            
            hashed = generate_password_hash(user['password'])
            cursor.execute("UPDATE users SET password=%s WHERE id=%s", (hashed, user['id']))
            print(f"Hashed password for user ID {user['id']}")
            
        conn.commit()
        print("All passwords hashed successfully.")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    hash_existing_passwords()

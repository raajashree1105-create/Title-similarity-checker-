import mysql.connector  # type: ignore

def check_user_password(email):
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='title_similarity',
            user='root',
            password='raji@123'
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT email, password FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user:
            print(f"User Email: {user['email']}")
            print(f"Password stored in DB: {user['password']}")
            if ":" in user['password']:
              print("Password IS hashed.")
            else:
              print("Password is NOT hashed (plain text).")
        else:
            print("User not found.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_user_password('raajashree1105@gmail.com') # Checking the user's email

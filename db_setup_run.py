import mysql.connector  # type: ignore

try:
    print("Connecting to db...")
    conn = mysql.connector.connect(host='localhost', database='title_similarity', user='root', password='raji@123')
    cursor = conn.cursor()
    
    print("Creating table project_titles...")
    cursor.execute('CREATE TABLE IF NOT EXISTS project_titles (id INT AUTO_INCREMENT PRIMARY KEY, student_email VARCHAR(100), title TEXT, similar_title TEXT, similarity_score FLOAT, status VARCHAR(50), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);')
    
    print("Querying users...")
    cursor.execute("SELECT * FROM users WHERE email='admin@gmail.com'")
    res1 = cursor.fetchall()
    print('Before insert:', res1)
    
    if not res1:
        print("Inserting admin...")
        cursor.execute("INSERT INTO users(fullname, email, password, role) VALUES ('System Admin', 'admin@gmail.com', 'admin123', 'admin');")
        conn.commit()
    
    cursor.execute("SELECT * FROM users WHERE email='admin@gmail.com'")
    res2 = cursor.fetchall()
    print('After insert/query:', res2)
    
    conn.close()
    print("Success")
except Exception as e:
    print('Error:', e)

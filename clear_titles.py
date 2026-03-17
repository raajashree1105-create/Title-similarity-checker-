import mysql.connector

def clear_all_titles():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='title_similarity',
            user='root',
            password='raji@123'
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("DELETE FROM project_titles")
            connection.commit()
            print(f"Successfully deleted all records from 'project_titles' table.")
            
            # Reset the Auto Increment ID as well
            cursor.execute("ALTER TABLE project_titles AUTO_INCREMENT = 1")
            connection.commit()
            print("Reset project_titles ID counter.")
            
            cursor.close()
            connection.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    confirm = input("Are you sure you want to delete ALL titles in the database? (yes/no): ")
    if confirm.lower() == 'yes':
        clear_all_titles()
    else:
        print("Operation cancelled.")

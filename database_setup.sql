CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    fullname VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(100),
    role VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT IGNORE INTO users(fullname, email, password, role)
VALUES ('System Admin', 'admin@gmail.com', 'admin123', 'admin');

CREATE TABLE IF NOT EXISTS project_titles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_email VARCHAR(100),
    title TEXT,
    similar_title TEXT,
    similarity_score FLOAT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def save_memory(category, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO memories (category, content) VALUES (%s, %s)",
        (category, content)
    )
    conn.commit()
    cursor.close()
    conn.close()

def load_memories():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT category, content FROM memories ORDER BY created_at DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        return ""
    lines = [f"- [{row[0]}] {row[1]}" for row in rows]
    return "\n".join(lines)

def save_conversation_summary(summary):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (summary) VALUES (%s)",
        (summary,)
    )
    conn.commit()
    cursor.close()
    conn.close()

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Table for storing facts and preferences about the user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(50),
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table for storing past conversation summaries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Database ready!")

if __name__ == "__main__":
    setup_database()
import sqlite3

DB_NAME = "sezzle_agent.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn


def init_db():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT,
        intent TEXT,
        confidence REAL,
        escalate INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# Logging Function

def save_conversation(
    query,
    intent,
    confidence,
    escalate
):

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO conversations
    (
        query,
        intent,
        confidence,
        escalate
    )
    VALUES (?, ?, ?, ?)
    """, (
        query,
        intent,
        confidence,
        int(escalate)
    ))

    conn.commit()
    conn.close()


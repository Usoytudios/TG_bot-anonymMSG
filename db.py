import sqlite3
import random
from datetime import datetime

DB_PATH = "database/messages.db"

def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)





def create_tables():
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        agreed INTEGER DEFAULT 0,
        active INTEGER DEFAULT 0
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        receiver_id INTEGER,
        text TEXT,
        timestamp TEXT
    )
    """)
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def update_agreement(user_id, agreed=True):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET agreed = ? WHERE user_id = ?", (int(agreed), user_id))
    conn.commit()
    conn.close()

def set_active(user_id, active=True):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET active = ? WHERE user_id = ?", (int(active), user_id))
    conn.commit()
    conn.close()

def add_message(sender_id, receiver_id, text):
    conn = connect()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO messages (sender_id, receiver_id, text, timestamp) VALUES (?, ?, ?, ?)",
        (sender_id, receiver_id, text, timestamp)
    )
    conn.commit()
    conn.close()

def get_random_active_user(exclude_id):
    """
    Возвращает случайного активного пользователя, который уже согласился (agreed = 1) 
    и не равен exclude_id. Если ни одного найдено – возвращает None.
    """
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE active = 1 AND agreed = 1 AND user_id != ?", (exclude_id,))
    users = cursor.fetchall()
    conn.close()
    if users:
        return random.choice(users)[0]
    return None
def has_agreed(user_id):
    """Проверяет, согласился ли пользователь с условиями."""
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("SELECT agreed FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None and result[0] == 1



if __name__ == '__main__':
    create_tables()
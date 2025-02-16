import asyncio
import sqlite3
from datetime import datetime, timedelta
from config import MAX_MESSAGES_PER_MINUTE, FLOOD_BLOCK_TIME

DB_PATH = "database/messages.db"

MAX_MESSAGES_PER_MINUTE = MAX_MESSAGES_PER_MINUTE
CHECK_INTERVAL = FLOOD_BLOCK_TIME

def get_connection():
    """Возвращает подключение к базе данных."""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def get_recent_message_count(user_id, minutes=1):
    """Подсчитывает количество сообщений от пользователя за последние 'minutes' минут."""
    conn = get_connection()
    cursor = conn.cursor()
    time_threshold = (datetime.now() - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "SELECT COUNT(*) FROM messages WHERE sender_id = ? AND timestamp >= ?",
        (user_id, time_threshold)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count

def block_user(user_id):
    """Блокирует пользователя, устанавливая active = 0."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET active = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    print(f"User {user_id} заблокирован из-за спама.")

def is_user_blocked(user_id):
    """Проверяет, заблокирован ли пользователь."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT active FROM users WHERE user_id = ?", (user_id,))
    status = cursor.fetchone()
    conn.close()
    return status is None or status[0] == 0

async def monitor_spam():
    """Периодически проверяет базу данных на предмет флудящих пользователей."""
    while True:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE active = 1")
        active_users = cursor.fetchall()
        conn.close()
        for (user_id,) in active_users:
            count = get_recent_message_count(user_id)
            if count > MAX_MESSAGES_PER_MINUTE:
                print(f"User {user_id} отправил {count} сообщений за последнюю минуту. Применяем блокировку.")
                block_user(user_id)
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    asyncio.run(monitor_spam())

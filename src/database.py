import sqlite3
import json
from contextlib import contextmanager

DB_PATH = "data.db"

def init_db():
    """Создать таблицу при первом запуске"""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                state TEXT DEFAULT 'QUEST',
                current_gift_idx INTEGER DEFAULT 0,
                current_question INTEGER DEFAULT 1,
                skips_left INTEGER,
                unlocked_gifts TEXT DEFAULT '[]',
                notifications_enabled INTEGER DEFAULT 1,
                last_notification_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

@contextmanager
def get_db():
    """Контекст-менеджер для соединения"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def get_user(telegram_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE telegram_id = ?", 
            (telegram_id,)
        ).fetchone()
        if row:
            data = dict(row)
            data['unlocked_gifts'] = json.loads(data['unlocked_gifts'])
            return data
    return None

def create_user(telegram_id: int, initial_skips: int) -> dict:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, skips_left) VALUES (?, ?)",
            (telegram_id, initial_skips)
        )
    return get_user(telegram_id)

def update_user(telegram_id: int, **fields):
    """Обновить любые поля: update_user(123, skips_left=2, current_question=2)"""
    if 'unlocked_gifts' in fields:
        fields['unlocked_gifts'] = json.dumps(fields['unlocked_gifts'])
    
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [telegram_id]
    
    with get_db() as conn:
        conn.execute(
            f"UPDATE users SET {set_clause} WHERE telegram_id = ?",
            values
        )

def get_users_for_notification() -> list[dict]:
    """Юзеры, которым нужно отправить уведомление сегодня"""
    from datetime import date
    today = date.today().isoformat()
    
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM users 
            WHERE state = 'COMPLETED' 
            AND notifications_enabled = 1
            AND (last_notification_date IS NULL OR last_notification_date != ?)
        """, (today,)).fetchall()
        return [dict(row) for row in rows]

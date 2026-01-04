import sqlite3
import json
from contextlib import contextmanager
from datetime import date
from typing import Optional, Dict, Any, List

DB_PATH = "data.db"

def init_db():
    """
    Инициализирует базу данных.
    Создает таблицу 'users', если она не существует.
    """
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
    """
    Контекстный менеджер для безопасного соединения с базой данных.
    Гарантирует, что соединение будет закрыто после использования.
    :return: Объект соединения с базой данных.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает данные пользователя по его telegram_id.
    :param telegram_id: Уникальный идентификатор пользователя в Telegram.
    :return: Словарь с данными пользователя или None, если пользователь не найден.
    """
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

def create_user(telegram_id: int, initial_skips: int) -> Dict[str, Any]:
    """
    Создает нового пользователя в базе данных.
    Если пользователь уже существует, ничего не делает.
    :param telegram_id: Уникальный идентификатор пользователя в Telegram.
    :param initial_skips: Начальное количество пропусков вопросов.
    :return: Словарь с данными созданного или существующего пользователя.
    """
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id, skips_left) VALUES (?, ?)",
            (telegram_id, initial_skips)
        )
    return get_user(telegram_id)

def update_user(telegram_id: int, **fields: Any):
    """
    Обновляет одно или несколько полей для указанного пользователя.
    :param telegram_id: Идентификатор пользователя для обновления.
    :param fields: Именованные аргументы, где ключ - это имя столбца, а значение - новое значение.
    """
    if 'unlocked_gifts' in fields:
        fields['unlocked_gifts'] = json.dumps(fields['unlocked_gifts'])
    
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [telegram_id]
    
    with get_db() as conn:
        conn.execute(
            f"UPDATE users SET {set_clause} WHERE telegram_id = ?",
            values
        )

def get_users_for_notification() -> List[Dict[str, Any]]:
    """
    Возвращает список пользователей, которым нужно отправить утреннее уведомление.
    Это пользователи, которые завершили квест, у которых включены уведомления
    и которые не получали уведомление сегодня.
    :return: Список словарей с данными пользователей.
    """
    today = date.today().isoformat()
    
    with get_db() as conn:
        rows = conn.execute("""
            SELECT * FROM users 
            WHERE state = 'COMPLETED' 
            AND notifications_enabled = 1
            AND (last_notification_date IS NULL OR last_notification_date != ?)
        """, (today,)).fetchall()
        return [dict(row) for row in rows]


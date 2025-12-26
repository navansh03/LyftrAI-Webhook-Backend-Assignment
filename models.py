import sqlite3
from config import get_config


def init_db() -> None:
    """Initialize the database and create tables if they do not exist.
    
    Safe to call multiple times (idempotent).
    Raises RuntimeError if DATABASE_URL is missing or invalid.
    """
    config = get_config()
    db_path = config.get_database_path()
    
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                from_msisdn TEXT NOT NULL,
                to_msisdn TEXT NOT NULL,
                ts TEXT NOT NULL,
                text TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()
# storage.py

import sqlite3
import json
from config import DB_PATH

def get_conn():
    """
    Повертає з’єднання з базою SQLite.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Створює таблиці, якщо вони ще не існують:
      - sources
      - news
      - queue
      - settings
    """
    with get_conn() as conn:
        cursor = conn.cursor()
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS sources (
          id            INTEGER PRIMARY KEY AUTOINCREMENT,
          type          TEXT NOT NULL,
          url           TEXT NOT NULL UNIQUE,
          last_checked  INTEGER
        );

        CREATE TABLE IF NOT EXISTS news (
          id            INTEGER PRIMARY KEY AUTOINCREMENT,
          source_id     INTEGER NOT NULL,
          url           TEXT NOT NULL UNIQUE,
          title         TEXT,
          summary       TEXT,
          published_at  INTEGER,
          topics        TEXT,
          hash          TEXT UNIQUE,
          FOREIGN KEY(source_id) REFERENCES sources(id)
        );

        CREATE TABLE IF NOT EXISTS queue (
          news_id       INTEGER PRIMARY KEY,
          digest_type   TEXT NOT NULL,
          status        TEXT NOT NULL,
          FOREIGN KEY(news_id) REFERENCES news(id)
        );

        CREATE TABLE IF NOT EXISTS settings (
          key           TEXT PRIMARY KEY,
          value         TEXT NOT NULL
        );
        """)
        conn.commit()

# -------------------------
# CRUD для джерел (sources)
# -------------------------

def add_source(source_type: str, url: str):
    """
    Додає нове джерело (type, url), якщо його ще немає.
    """
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sources (type, url) VALUES (?, ?)",
            (source_type, url)
        )
        conn.commit()

def get_all_sources():
    """
    Повертає всі джерела у вигляді списку рядків sqlite3.Row
    """
    with get_conn() as conn:
        return conn.execute("SELECT * FROM sources").fetchall()

def update_last_checked(source_id: int, timestamp: int):
    """
    Оновлює час останньої перевірки для джерела.
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE sources SET last_checked = ? WHERE id = ?",
            (timestamp, source_id)
        )
        conn.commit()

# -------------------------
# CRUD для новин (news)
# -------------------------

def add_news(source_id: int, url: str, title: str, summary: str,
             published_at: int, topics: list, hash_str: str):
    """
    Додає новину в базу, якщо URL ще не існує.
    topics — список тем, перетворюється в JSON.
    """
    with get_conn() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO news
               (source_id, url, title, summary, published_at, topics, hash)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (source_id, url, title, summary, published_at,
             json.dumps(topics), hash_str)
        )
        conn.commit()

def update_news_topics_and_summary(news_id: int, summary: str, topics: list):
    """
    Оновлює поля summary та topics для вже доданої новини.
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE news SET summary = ?, topics = ? WHERE id = ?",
            (summary, json.dumps(topics), news_id)
        )
        conn.commit()

def get_unqueued_news():
    """
    Повертає всі новини, які ще не додані в чергу (queue).
    """
    with get_conn() as conn:
        return conn.execute("""
            SELECT n.* FROM news n
            LEFT JOIN queue q ON n.id = q.news_id
            WHERE q.news_id IS NULL
        """).fetchall()

def get_news_by_id(news_id: int):
    """
    Повертає одну новину за її ID.
    """
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM news WHERE id = ?", (news_id,)
        ).fetchone()

# -------------------------
# CRUD для черги (queue)
# -------------------------

def enqueue(news_id: int, digest_type: str):
    """
    Додає новину до черги з типом дайджесту ('lowbank' або 'general').
    """
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO queue (news_id, digest_type, status) VALUES (?, ?, 'ready')",
            (news_id, digest_type)
        )
        conn.commit()

def get_ready_queue(digest_type: str):
    """
    Повертає всі готові до відправлення новини з вказаного дайджесту.
    """
    with get_conn() as conn:
        return conn.execute(
            "SELECT n.* FROM news n JOIN queue q ON n.id = q.news_id "
            "WHERE q.digest_type = ? AND q.status = 'ready'",
            (digest_type,)
        ).fetchall()

def mark_sent(news_id: int):
    """
    Позначає новину як відправлену (status = 'sent').
    """
    with get_conn() as conn:
        conn.execute(
            "UPDATE queue SET status = 'sent' WHERE news_id = ?",
            (news_id,)
        )
        conn.commit()

# -------------------------
# CRUD для налаштувань (settings)
# -------------------------

def set_setting(key: str, value: bool):
    """
    Встановлює або оновлює налаштування key → 'true'/'false'.
    """
    with get_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, 'true' if value else 'false')
        )
        conn.commit()

def get_setting(key: str) -> bool:
    """
    Повертає boolean для налаштування (True якщо 'true').
    """
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return bool(row and row['value'] == 'true')

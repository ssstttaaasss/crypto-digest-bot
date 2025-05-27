# storage.py

import os
import sqlite3
from config import DB_PATH

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn():
    """Повертає з'єднання з БД, створивши файл, якщо потрібно."""
    # Гарантуємо створення каталогу
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Створює таблиці, якщо їх немає."""
    conn = get_conn()
    cur = conn.cursor()
    # Створення таблиць
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            last_checked INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_id INTEGER,
            url TEXT,
            title TEXT,
            content TEXT,
            published INTEGER,
            summary TEXT,
            topics TEXT,
            hash TEXT,
            sent_lowbank INTEGER DEFAULT 0,
            sent_general INTEGER DEFAULT 0,
            FOREIGN KEY(source_id) REFERENCES sources(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS queue (
            news_id INTEGER,
            digest_type TEXT,
            status TEXT DEFAULT 'ready',
            FOREIGN KEY(news_id) REFERENCES news(id)
        )
    """)
    conn.commit()
    conn.close()

# Інші функції: add_source, add_news, get_all_sources, get_unqueued_news, enqueue, update_last_checked, update_news_topics_and_summary
# залишаються без змін

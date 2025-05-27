# tests/test_storage.py
import os, tempfile
import sqlite3
import pytest
from storage import init_db, get_conn, add_source, get_all_sources

@pytest.fixture(autouse=True)
def tmp_db(monkeypatch):
    fd, path = tempfile.mkstemp()
    os.close(fd)
    monkeypatch.setenv("DB_PATH", path)
    # ініціалізуємо БД
    init_db()
    yield
    os.remove(path)

def test_add_and_get_source():
    add_source("rss", "https://example.com/feed")
    srcs = get_all_sources()
    assert len(srcs) == 1
    assert srcs[0]["type"] == "rss"
    assert srcs[0]["url"] == "https://example.com/feed"

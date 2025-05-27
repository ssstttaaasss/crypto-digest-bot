# config.py
import os
from dotenv import load_dotenv

# Підгружаємо .env (локально) або з оточення (CI)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
DB_PATH   = os.getenv("DB_PATH", "data/bot.db")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("BOT_TOKEN and CHAT_ID must be set in environment")

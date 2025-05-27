# debug_env.py
import os
from dotenv import load_dotenv, find_dotenv

print("CWD:", os.getcwd())
print("find_dotenv():", find_dotenv())
loaded = load_dotenv(find_dotenv())
print("loaded:", loaded)
print("BOT_TOKEN:", os.getenv("BOT_TOKEN"))
print("CHAT_ID:", os.getenv("CHAT_ID"))

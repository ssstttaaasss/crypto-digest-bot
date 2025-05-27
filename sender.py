# sender.py

import json
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode    # <-- правильний імпорт
from storage import init_db, get_ready_queue, mark_sent
from config import BOT_TOKEN, CHAT_ID

def format_news_item(item):
    title = item["title"]
    url = item["url"]
    summary = item["summary"] or ""
    topics = json.loads(item["topics"] or "[]")
    tags = " ".join(f"#{t.replace(' ', '')}" for t in topics)
    return f"*[{title}]({url})*\n{summary}\n\n{tags}"

def send_digest(digest_type: str):
    bot = Bot(token=BOT_TOKEN)
    items = get_ready_queue(digest_type)
    if not items:
        return
    blocks = [format_news_item(item) for item in items]
    message_text = "\n\n".join(blocks)
    now = datetime.now().strftime("%H:%M %d.%m.%Y")
    message_text += f"\n\n_Published at {now}_"
    bot.send_message(
        chat_id=CHAT_ID,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN
    )
    for item in items:
        mark_sent(item["id"])

def main():
    init_db()
    send_digest("lowbank")
    send_digest("general")

if __name__ == "__main__":
    main()

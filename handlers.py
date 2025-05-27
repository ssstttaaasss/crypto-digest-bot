# handlers.py

import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from telegram.error import BadRequest
from storage import get_setting, set_setting
from config import BOT_TOKEN

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Завантажуємо теми (українською)
with open("topics_list.json", encoding="utf-8") as f:
    TOPICS = json.load(f)
LOWBANK_TOPICS = TOPICS["lowbank"]
GENERAL_TOPICS = TOPICS["general"]

# Головне меню
MAIN_MENU_TEXT = "Оберіть опцію:"
MAIN_MENU_KEYBOARD = [
    [InlineKeyboardButton("⚙️ Теми lowbank", callback_data="open:lowbank")],
    [InlineKeyboardButton("⚙️ Загальні теми", callback_data="open:general")],
    [InlineKeyboardButton("📋 Шпаргалка", callback_data="show:cheatsheet")],
    [InlineKeyboardButton("📊 Статистика", callback_data="show:stats")]
]
MAIN_MENU_MARKUP = InlineKeyboardMarkup(MAIN_MENU_KEYBOARD)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start – показує головне меню."""
    chat_id = update.effective_chat.id
    await context.bot.send_message(
        chat_id=chat_id,
        text=MAIN_MENU_TEXT,
        reply_markup=MAIN_MENU_MARKUP
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробляє натискання inline-кнопок."""
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest as e:
        logger.debug(f"Answer callback failed: {e}")

    action, *params = query.data.split(":")

    def build_menu(digest):
        items = LOWBANK_TOPICS if digest == "lowbank" else GENERAL_TOPICS
        kb = [
            [InlineKeyboardButton(
                ("✅ " if get_setting(f"{digest}_{theme}") else "❌ ") + theme,
                callback_data=f"toggle:{digest}:{theme}"
            )]
            for theme in items
        ]
        kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
        return kb

    try:
        if action == "open":
            digest = params[0]
            kb = build_menu(digest)
            label = "lowbank" if digest == "lowbank" else "загальний"
            await query.edit_message_text(
                text=f"*Налаштування тем для {label}-дайджесту:*",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode=ParseMode.MARKDOWN
            )

        elif action == "toggle":
            digest, theme = params
            key = f"{digest}_{theme}"
            set_setting(key, not get_setting(key))
            kb = build_menu(digest)
            label = "lowbank" if digest == "lowbank" else "загальний"
            await query.edit_message_text(
                text=f"*Налаштування тем для {label}-дайджесту:*",
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode=ParseMode.MARKDOWN
            )

        elif action == "back":
            await query.edit_message_text(
                text=MAIN_MENU_TEXT,
                reply_markup=MAIN_MENU_MARKUP
            )

        elif action == "show" and params[0] == "cheatsheet":
            # Шпаргалка
            text = "*Шпаргалка тем:*\n\n"
            text += "*Теми lowbank:*\n" + "\n".join(f"- {t}" for t in LOWBANK_TOPICS) + "\n\n"
            text += "*Загальні теми:*\n" + "\n".join(f"- {t}" for t in GENERAL_TOPICS)
            kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode=ParseMode.MARKDOWN
            )

        elif action == "show" and params[0] == "stats":
            # Статистика
            lines = []
            for digest, items in [("lowbank", LOWBANK_TOPICS), ("general", GENERAL_TOPICS)]:
                cnt = sum(get_setting(f"{digest}_{t}") for t in items)
                lines.append(f"{digest.capitalize()}: {cnt}/{len(items)} увімкнено")
            text = "*Поточні налаштування:*\n" + "\n".join(lines)
            kb = [[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
            await query.edit_message_text(
                text=text,
                reply_markup=InlineKeyboardMarkup(kb),
                parse_mode=ParseMode.MARKDOWN
            )
    except BadRequest as e:
        logger.debug(f"Edit message failed: {e}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("🚀 Бот запущено...")
    app.run_polling()

if __name__ == "__main__":
    main()

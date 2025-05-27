# check_bot.py

import asyncio
from telegram import Bot
from config import BOT_TOKEN

async def main():
    bot = Bot(token=BOT_TOKEN)
    me = await bot.get_me()
    print(me)

if __name__ == "__main__":
    asyncio.run(main())

from aiogram import Bot, Dispatcher
from dotenv import get_key
from routers import base
import asyncio

TOKEN = get_key(".env", "BOT_TOKEN")

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_routers(base.router)

    print("Bot had started to work!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

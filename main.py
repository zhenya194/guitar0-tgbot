import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import config
from routers import commands

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=config.bot_token.get_secret_value())
    dp = Dispatcher()

    dp.include_routers(commands.router)

    print("Bot had started to work!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

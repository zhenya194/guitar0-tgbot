from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from dotenv import get_key
from routers import base, learn
import asyncio

TOKEN = str(get_key(".env", "BOT_TOKEN"))

async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.include_router(base.router)
    dp.include_router(learn.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Start the bot"),
        BotCommand(command="help", description="Show the bot's commands"),
        BotCommand(command="fb", description="Send us a feedback"),
        BotCommand(command="lessons", description="Show lesson details"),
        BotCommand(command="chords", description="Show chord details"),
    ])

    print("Bot had started to work!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except:
        print("An error occured.")

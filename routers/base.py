from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandObject, CommandStart
from db.database import db

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.full_name)
    await message.answer(f"Здравствуйте, {message.from_user.first_name}! Используйте команду /help что бы получить сообщение с помощью по командах.")

@router.message(Command("fb"))
async def cmd_feedback(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Пожалуста, напишите сообщение после /fb")
    db.add_feedback(message.from_user.id, message.from_user.full_name, command.args)
    await message.answer("✅ Спасибо за обратную связь!")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    return await message.answer(f"Commands for <b>Guitar 0 bot</b>:\n\n"
        f"<code>/start</code> - перезапустить бота\n"
        f"<code>/help</code> - показать это сообщение\n"
        f"<code>/fb</code> - отправить сообщение для обратной связи\n"
        f"<code>/lessons</code> - название песни урока, ссылка на видео и т.п.\n"
        f"<code>/chords</code> - аккорды",
        parse_mode="HTML")

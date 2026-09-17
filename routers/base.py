from aiogram import Router, types
from aiogram.filters import Command, CommandObject, CommandStart
from db.database import db

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    if message.from_user:
        db.add_user(message.from_user.id, message.from_user.full_name)
        first_name = message.from_user.first_name or "пользователь"
        await message.answer(f"Здравствуйте, {first_name}! Используйте команду /help, чтобы получить справку по командам.")

@router.message(Command("fb"))
async def cmd_feedback(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Пожалуйста, напишите сообщение после /fb")
    if message.from_user:
        db.add_feedback(message.from_user.id, message.from_user.full_name, command.args)
    await message.answer("✅ Спасибо за обратную связь!")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    return await message.answer(
        "Команды бота Guitar 0:\n\n"
        "/start - перезапустить бота\n"
        "/help - показать это сообщение\n"
        "/fb <сообщение> - отправить обратную связь\n"
        "/lessons <номер> - информация об уроке (видео, песни)\n"
        "/chords <аккорд> - аппликатура аккорда (например: /chords Am)"
    )

from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from database import db
import requests

router = Router()
api_url: str = "https://api.guitar0.net/api/v1/lessons/"
response = requests.get(api_url)
data = response.json()
corrent_lesson: int = 0

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    db.add_user(message.from_user.id, message.from_user.full_name)
    await message.answer(f"Здравствуйте, {message.from_user.first_name}! Используйте команду /help что бы получить сообщение с помощью по командах.")

@router.message(Command("fb"))
async def cmd_feedback(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer("Пожалуста, напишите сообщение после /fb")
    db.add_feedback(message.from_user.id, message.from_user.full_name, command.args)
    await message.answer("✅ Спасибо за обратную связь!")

@router.message(Command("lessons"))
async def cmd_lessons(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer(f"Пожалуста, напишите номер урока после /lessons. Пример: <code>/lessons 18</code>", parse_mode="HTML")
        return
    int_commands_arg: int = int(command.args)

    title: str = data[int_commands_arg]["title"]
    video_url: str = data[int_commands_arg]["video_url"]
    song_0: str = data[int_commands_arg]["songs"][0]["title"]
    if len(data[int_commands_arg]["songs"]) > 1:
        song_1: str = data[int_commands_arg]["songs"][1]["title"]
        return await message.answer(f"{title}\n\n"
                                    f"Ссылка на видео: {video_url}\n"
                                    f"Первая песня: {song_0}\n"
                                    f"Вторая песня: {song_1}\n",
                                    parse_mode="HTML")
    else:
        return await message.answer(f"{title}\n\n"
                                    f"Ссылка на видео: {video_url}\n"
                                    f"Песня: {song_0}\n",
                                    parse_mode="HTML")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(f"<b>Commands for Guitar 0 bot:</b>\n\n"
        f"/start - перезапустить бота\n"
        f"/help - показать это сообщение\n"
        f"/fb - отправить сообщение для обратной связи\n"
        f"/lessons - название песни урока, ссылка на видео и т.п.\n",
        parse_mode="HTML")

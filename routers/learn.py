from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandObject, CommandStart
from db.database import db
from db.api import get_api_data
import asyncio

router = Router()

api_data = asyncio.run(get_api_data())

data_lessons = api_data[0]
data_chords = api_data[1]

@router.message(Command("lessons"))
async def cmd_lessons(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer(f"Пожалуста, напишите номер урока после /lessons. Пример: <code>/lessons 18</code>", parse_mode="HTML")
    int_commands_arg_lessons: int = int(command.args)
    songs_count = 0

    title: str = data_lessons["results"][int_commands_arg_lessons]["title"]
    video_url: str = data_lessons["results"][int_commands_arg_lessons]["video_url"]
    lessons_message: str = f"{title}\n\nСсылка на видео: {video_url}\n"
    for i in range(len(data_lessons["results"][int_commands_arg_lessons]["songs"])):
        songs_count += 1
    for song in data_lessons["results"][int_commands_arg_lessons]["songs"]:
        lessons_message += song["title"] + "\n"
    return message.answer(lessons_message, parse_mode="HTML")

@router.message(Command("chords"))
async def cmd_lessons(message: types.Message, command: CommandObject):
    if not command.args:
        return await message.answer(f"Пожалуста, напишите номер акорда после /chords. Пример: <code>/chords 8</code>", parse_mode="HTML")
    int_commands_arg_chords: int = int(command.args)
    chords_message: str = f"Аккорды № {int_commands_arg_chords}\n\n\n"
    for i in range(len(data_chords["results"][int_commands_arg_chords]["positions"])):
                chords_message += f"Аккорд {int_commands_arg_chords}.{i}:\n"
                chords_message += f"Струна {data_chords["results"][int_commands_arg_chords]["positions"][i]["string_number"]}\n"
                chords_message += f"Лад {data_chords["results"][int_commands_arg_chords]["positions"][i]["fret"]}\n"
                chords_message += f"Палец {data_chords["results"][int_commands_arg_chords]["positions"][i]["finger"]}\n\n"
    return message.answer(chords_message)

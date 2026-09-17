from aiogram import Router, types
from aiogram.filters import Command, CommandObject
from db.api import get_api_data

router = Router()

data_lessons = {"results": []}
data_chords = {"results": []}

async def load_data():
    global data_lessons, data_chords
    try:
        api_data = await get_api_data()
        data_lessons = api_data[0]
        data_chords = api_data[1]
    except Exception:
        pass

def format_chord(chord: dict, idx: int = 1, total: int = 1) -> str:
    title = chord.get("title", "")
    musical_title = chord.get("musical_title", "")
    positions = chord.get("positions", [])

    finger_map = {
        1: "указательный",
        2: "средний",
        3: "безымянный",
        4: "мизинец",
    }

    header = f"🎸 Аккорд {title}"
    if musical_title:
        header += f" ({musical_title})"
    if total > 1:
        header += f" [Вариант {idx}/{total}]"

    lines = [header, "", "Позиции на грифе:"]

    sorted_positions = sorted(positions, key=lambda x: x.get("string_number", 0))
    for pos in sorted_positions:
        s_num = pos.get("string_number", "?")
        fret = pos.get("fret", 0)
        finger = pos.get("finger", 0)

        if finger == -1:
            desc = "заглушена (✕)"
        elif fret == 0:
            desc = "открытая струна (○)"
        else:
            finger_desc = finger_map.get(finger, f"палец {finger}")
            desc = f"{fret}-й лад ({finger_desc})"

        lines.append(f"• {s_num}-я струна: {desc}")

    return "\n".join(lines)

@router.message(Command("lessons"))
async def cmd_lessons(message: types.Message, command: CommandObject):
    global data_lessons
    if not data_lessons.get("results"):
        await load_data()

    results = data_lessons.get("results", [])

    if not command.args:
        return await message.answer(
            "Пожалуйста, напишите номер урока после /lessons. Пример: /lessons 1"
        )

    arg = command.args.strip()
    if not arg.isdigit():
        return await message.answer(
            "Пожалуйста, укажите корректный номер урока (число). Пример: /lessons 1"
        )

    lesson_idx = int(arg)
    if lesson_idx < 0 or lesson_idx >= len(results):
        max_idx = len(results) - 1 if results else 0
        return await message.answer(
            f"Урок с номером {lesson_idx} не найден. Доступные номера: от 0 до {max_idx}."
        )

    lesson = results[lesson_idx]
    title = lesson.get("title", f"Урок № {lesson_idx}")
    video_url = lesson.get("video_url", "")
    songs = lesson.get("songs", [])

    lessons_message = f"📚 {title}\n\n"
    if video_url:
        lessons_message += f"▶️ Ссылка на видео: {video_url}\n"

    if songs:
        lessons_message += "\n🎵 Песни в уроке:\n"
        for song in songs:
            song_title = song.get("title", "")
            if song_title:
                lessons_message += f"• {song_title}\n"

    return await message.answer(lessons_message)

@router.message(Command("chords"))
async def cmd_chords(message: types.Message, command: CommandObject):
    global data_chords
    if not data_chords.get("results"):
        await load_data()

    results = data_chords.get("results", [])

    if not command.args:
        return await message.answer(
            "Пожалуйста, напишите название или номер аккорда после /chords. Пример: /chords Am или /chords C"
        )

    query = command.args.strip()

    # Поиск по точному названию аккорда (например, "Am", "am", "C", "Em")
    matched_chords = [
        chord for chord in results
        if chord.get("title", "").strip().lower() == query.lower()
    ]

    # Если точного совпадения нет и введено число, пробуем найти по индексу или ID
    if not matched_chords and query.isdigit():
        idx = int(query)
        if 0 <= idx < len(results):
            matched_chords = [results[idx]]
        else:
            matched_chords = [
                chord for chord in results
                if chord.get("id") == idx
            ]

    # Если всё ещё не найдено, ищем частичное совпадение по названию или описанию
    if not matched_chords:
        matched_chords = [
            chord for chord in results
            if query.lower() in chord.get("title", "").lower()
            or query.lower() in chord.get("musical_title", "").lower()
        ]

    if not matched_chords:
        return await message.answer(
            f"❌ Аккорд «{query}» не найден.\nПопробуйте, например: /chords Am, /chords C, /chords Em, /chords D"
        )

    total = len(matched_chords)
    response_parts = []
    for i, chord in enumerate(matched_chords[:3], 1):
        response_parts.append(format_chord(chord, idx=i, total=total))

    full_message = "\n\n───────────────\n\n".join(response_parts)
    return await message.answer(full_message)

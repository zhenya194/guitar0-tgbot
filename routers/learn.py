import asyncio
import re
from urllib.parse import quote_plus
import resvg_py
from aiogram import F, Router, types
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db.api import get_api_data, get_lesson_detail

router = Router()

data_lessons = {"results": []}
data_chords = {"results": []}
active_speed_tasks: dict[int, asyncio.Task] = {}


class LearnState(StatesGroup):
    waiting_for_lesson = State()
    waiting_for_chord = State()


def get_watch_url(embed_or_watch_url: str) -> str:
    if "/embed/" in embed_or_watch_url:
        video_id = embed_or_watch_url.split("/embed/")[-1].split("?")[0]
        return f"https://www.youtube.com/watch?v={video_id}"
    return embed_or_watch_url


def format_song_text(raw_text: str) -> str:
    if not raw_text:
        return ""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("&nbsp;", " ").replace("\u3000", " ")
    lines = []
    for line in text.split("\n"):
        line = re.sub(r"^#{1,6}\s*", "", line)
        lines.append(line)
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# Speed presets: name -> (delay_between_blocks_sec, intro_delay_sec)
SPEED_PRESETS: dict[str, tuple[str, float, float]] = {
    "slow":     ("🐢 Медленно",  8.0, 4.0),
    "moderate": ("🚶 Умеренно",  6.0, 4.0),
    "medium":   ("🚴 Средне",    4.0, 4.0),
    "fast_ish": ("🏃 Шустро",    2.5, 4.0),
    "fast":     ("⚡ Быстро",    1.5, 4.0),
}


def parse_song_blocks(raw_text: str) -> list[str]:
    """Split song text into blocks (paragraphs), stripped of markdown headers."""
    text = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("&nbsp;", " ").replace("\u3000", " ")

    raw_blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    result = []
    for b in raw_blocks:
        lines = [l.strip() for l in b.split("\n") if l.strip()]
        if not lines:
            continue
        clean_lines = [re.sub(r"^#{1,6}\s*", "", l) for l in lines]
        block_text = "\n".join(clean_lines).strip()
        if block_text:
            result.append(block_text)
    return result



async def load_data():
    global data_lessons, data_chords
    try:
        api_data = await get_api_data()
        data_lessons = api_data[0]
        data_chords = api_data[1]
    except Exception:
        pass


def render_chord_svg(svg_code: str) -> bytes:
    svg = svg_code.replace("currentColor", "#1e1e1e")

    # Add crisp white background
    if "<rect" not in svg:
        insert_pos = svg.find(">") + 1
        bg_rect = '<rect width="100%" height="100%" fill="#ffffff"/>'
        svg = svg[:insert_pos] + bg_rect + svg[insert_pos:]

    # Scale width and height based on viewBox for high-res crisp rendering
    vb_match = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    if vb_match:
        w = int(vb_match.group(1)) * 4
        h = int(vb_match.group(2)) * 4
        svg = re.sub(r'<svg\s+', f'<svg width="{w}" height="{h}" ', svg, count=1)

    return resvg_py.svg_to_bytes(svg)


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


async def show_lesson(message: types.Message, query: str):
    global data_lessons
    if not data_lessons.get("results"):
        await load_data()

    results = data_lessons.get("results", [])

    arg = query.strip()
    if not arg.isdigit():
        return await message.answer(
            "Пожалуйста, укажите корректный номер урока (число). Наример: 1"
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

    lessons_message = f"📚 {title}\n"
    if video_url:
        watch_url = get_watch_url(video_url)
        lessons_message += f"\n▶️ Ссылка на видео: {watch_url}\n"

    if songs:
        lessons_message += "\n🎵 Песни в уроке:\n"
        for song in songs:
            song_title = song.get("title", "")
            if song_title:
                lessons_message += f"• {song_title}\n"

    builder = InlineKeyboardBuilder()

    top_buttons = []

    for i, song in enumerate(songs):
        song_title = song.get("title", "").strip()
        if not song_title:
            continue
        btn_text = f"🎵 {song_title}" if len(song_title) <= 22 else f"🎵 {song_title[:19]}..."
        top_buttons.append(InlineKeyboardButton(text=btn_text, callback_data=f"song:{lesson_idx}:{i}"))

    for j in range(0, len(top_buttons), 2):
        builder.row(*top_buttons[j:j+2])

    for i, song in enumerate(songs):
        song_title = song.get("title", "").strip()
        if not song_title:
            continue
        builder.row(
            InlineKeyboardButton(
                text=f"⚡️ В реальном времени: {song_title}",
                callback_data=f"speed:{lesson_idx}:{i}",
            )
        )

    keyboard = builder.as_markup() if builder.buttons else None

    return await message.answer(lessons_message, reply_markup=keyboard)


@router.callback_query(F.data.startswith("song:"))
async def callback_song(callback: types.CallbackQuery):
    await callback.answer()
    if not callback.data:
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        return

    lesson_idx = int(parts[1])
    song_idx = int(parts[2])

    global data_lessons
    if not data_lessons.get("results"):
        await load_data()

    results = data_lessons.get("results", [])
    if lesson_idx < 0 or lesson_idx >= len(results):
        if callback.message:
            await callback.message.answer("❌ Урок не найден.")
        return

    lesson = results[lesson_idx]
    lesson_uuid = lesson.get("uuid")
    if not lesson_uuid:
        if callback.message:
            await callback.message.answer("❌ Данные урока недоступны.")
        return

    lesson_detail = await get_lesson_detail(lesson_uuid)
    songs_detail = lesson_detail.get("songs", [])

    if not songs_detail or song_idx < 0 or song_idx >= len(songs_detail):
        summary_songs = lesson.get("songs", [])
        if 0 <= song_idx < len(summary_songs) and callback.message:
            song_title = summary_songs[song_idx].get("title", "")
            return await callback.message.answer(f"🎵 {song_title}\n\n(Подробный текст песни пока недоступен)")
        if callback.message:
            await callback.message.answer("❌ Песня не найдена.")
        return

    song = songs_detail[song_idx]
    title = song.get("title", "Песня")
    metronome = song.get("metronome")
    schemes = song.get("schemes", [])
    chords = song.get("chords", [])
    raw_text = song.get("text", "")

    msg_parts = [f"🎵 {title}\n"]

    if metronome:
        msg_parts.append(f"⏱️ Темп (метроном): {metronome} BPM")

    if schemes:
        scheme_names = [s.get("inscription") or s.get("title") for s in schemes if (s.get("inscription") or s.get("title"))]
        if scheme_names:
            msg_parts.append(f"🥁 Бой/перебор: {', '.join(scheme_names)}")

    if chords:
        chord_names = [c.get("title") for c in chords if c.get("title")]
        if chord_names:
            msg_parts.append(f"🎸 Аккорды в песне: {', '.join(chord_names)}")

    cleaned_text = format_song_text(raw_text)
    if cleaned_text:
        msg_parts.append("\n📝 Текст и аккорды:\n" + cleaned_text)

    full_message = "\n".join(msg_parts)

    if callback.message:
        if len(full_message) <= 4000:
            await callback.message.answer(full_message)
        else:
            chunks = [full_message[i:i + 3900] for i in range(0, len(full_message), 3900)]
            for chunk in chunks:
                await callback.message.answer(chunk)




async def run_speed_playback(
    bot,
    chat_id: int,
    user_id: int,
    song_title: str,
    speed_key: str,
    blocks: list[str],
):
    speed_label, block_delay, intro_delay = SPEED_PRESETS[speed_key]
    stop_builder = InlineKeyboardBuilder()
    stop_builder.row(InlineKeyboardButton(text="⏹ Остановить игру", callback_data=f"stop_speed:{user_id}"))

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"⚡ <b>Игра в реальном времени:</b> «{song_title}»\n"
                f"🎚️ Скорость: <b>{speed_label}</b> (пауза между блоками: {block_delay:.1f} сек)\n\n"
                f"🎸 Приготовьте гитару! Старт через {intro_delay:.0f} сек..."
            ),
            parse_mode="HTML",
            reply_markup=stop_builder.as_markup(),
        )

        await asyncio.sleep(intro_delay)

        for i, block_text in enumerate(blocks, 1):
            await bot.send_message(
                chat_id=chat_id,
                text=f"🎼 <b>[{i}/{len(blocks)}]</b>\n\n{block_text}",
                parse_mode="HTML",
                reply_markup=stop_builder.as_markup(),
            )
            await asyncio.sleep(block_delay)

        await bot.send_message(
            chat_id=chat_id,
            text=f"🎉 <b>Песня «{song_title}» завершена!</b>\nОтличная игра! 🎸",
            parse_mode="HTML",
        )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Error in speed playback: {e}")
    finally:
        active_speed_tasks.pop(user_id, None)


@router.callback_query(F.data.startswith("speed:"))
async def callback_speed(callback: types.CallbackQuery):
    """Show speed selection menu."""
    await callback.answer()
    if not callback.data or not callback.from_user or not callback.message:
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        return

    lesson_idx = parts[1]
    song_idx = parts[2]

    builder = InlineKeyboardBuilder()
    for key, (label, block_delay, _) in SPEED_PRESETS.items():
        builder.row(
            InlineKeyboardButton(
                text=f"{label}  ({block_delay:.1f} сек/блок)",
                callback_data=f"spd_run:{lesson_idx}:{song_idx}:{key}",
            )
        )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="spd_cancel"))

    await callback.message.answer(
        "🎚️ <b>Выберите скорость воспроизведения:</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "spd_cancel")
async def callback_spd_cancel(callback: types.CallbackQuery):
    await callback.answer("Отменено")
    if callback.message:
        await callback.message.delete()


@router.callback_query(F.data.startswith("spd_run:"))
async def callback_spd_run(callback: types.CallbackQuery):
    """Start playback with chosen speed preset."""
    await callback.answer()
    if not callback.data or not callback.from_user or not callback.message:
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        return

    lesson_idx = int(parts[1])
    song_idx = int(parts[2])
    speed_key = parts[3]

    if speed_key not in SPEED_PRESETS:
        return await callback.message.answer("❌ Неизвестная скорость.")

    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    # Cancel previous running task for this user if active
    old_task = active_speed_tasks.get(user_id)
    if old_task and not old_task.done():
        old_task.cancel()

    global data_lessons
    if not data_lessons.get("results"):
        await load_data()

    results = data_lessons.get("results", [])
    if lesson_idx < 0 or lesson_idx >= len(results):
        return await callback.message.answer("❌ Урок не найден.")

    lesson = results[lesson_idx]
    lesson_uuid = lesson.get("uuid")
    if not lesson_uuid:
        return await callback.message.answer("❌ Данные урока недоступны.")

    lesson_detail = await get_lesson_detail(lesson_uuid)
    songs_detail = lesson_detail.get("songs", [])

    if not songs_detail or song_idx < 0 or song_idx >= len(songs_detail):
        return await callback.message.answer("❌ Песня не найдена или нет текста.")

    song = songs_detail[song_idx]
    title = song.get("title", "Песня")
    raw_text = song.get("text", "")

    if not raw_text.strip():
        return await callback.message.answer(f"❌ Для песни «{title}» отсутствует текст.")

    blocks = parse_song_blocks(raw_text)
    if not blocks:
        return await callback.message.answer(f"❌ Не удалось разобрать структуру песни «{title}».")

    # Delete the speed-selection message
    await callback.message.delete()

    if callback.bot:
        task = asyncio.create_task(
            run_speed_playback(
                bot=callback.bot,
                chat_id=chat_id,
                user_id=user_id,
                song_title=title,
                speed_key=speed_key,
                blocks=blocks,
            )
        )
        active_speed_tasks[user_id] = task


@router.callback_query(F.data.startswith("stop_speed:"))
async def callback_stop_speed(callback: types.CallbackQuery):
    await callback.answer("Игра остановлена")
    if not callback.from_user:
        return

    user_id = callback.from_user.id
    task = active_speed_tasks.pop(user_id, None)
    if task and not task.done():
        task.cancel()

    if callback.message:
        await callback.message.answer("⏹ <b>Игра в реальном времени остановлена.</b>", parse_mode="HTML")






async def show_chord(message: types.Message, query: str):
    global data_chords
    if not data_chords.get("results"):
        await load_data()

    results = data_chords.get("results", [])
    query = query.strip()

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
            f"❌ Аккорд «{query}» не найден.\nПопробуйте, например: Am, C, Em, D"
        )

    total = len(matched_chords)
    for i, chord in enumerate(matched_chords[:3], 1):
        caption = format_chord(chord, idx=i, total=total)
        svg = chord.get("svg_vertical") or chord.get("svg_horizontal")
        if svg:
            try:
                png_bytes = render_chord_svg(svg)
                photo = types.BufferedInputFile(png_bytes, filename=f"chord_{chord.get('id', i)}.png")
                await message.answer_photo(photo=photo, caption=caption)
                continue
            except Exception:
                pass
        await message.answer(caption)



@router.message(F.text == "📚 Уроки")
@router.message(Command("lessons"))
async def cmd_lessons(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if command and command.args:
        if state:
            await state.clear()
        return await show_lesson(message, command.args)

    if state:
        await state.set_state(LearnState.waiting_for_lesson)
    await message.answer(
        "📚 Введите номер урока, который вы хотите посмотреть (например: 1) (для отмены отправьте /cancel):"
    )


@router.message(LearnState.waiting_for_lesson)
async def process_lesson_input(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, введите номер урока текстом.")

    text = message.text.strip()
    if text == "/cancel":
        await state.clear()
        return await message.answer("❌ Действие отменено.")

    await state.clear()
    await show_lesson(message, text)


@router.message(F.text == "🎸 Аккорды")
@router.message(Command("chords"))
async def cmd_chords(message: types.Message, command: CommandObject = None, state: FSMContext = None):
    if command and command.args:
        if state:
            await state.clear()
        return await show_chord(message, command.args)

    if state:
        await state.set_state(LearnState.waiting_for_chord)
    await message.answer(
        "🎸 Введите название или номер аккорда (например: Am, C, Em) (для отмены отправьте /cancel):"
    )


@router.message(LearnState.waiting_for_chord)
async def process_chord_input(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, введите название аккорда текстом.")

    text = message.text.strip()
    if text == "/cancel":
        await state.clear()
        return await message.answer("❌ Действие отменено.")

    await state.clear()
    await show_chord(message, text)



import html
import os

from aiogram import F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.database import db
from routers import learn as learn_module

router = Router()


# ---------------------------------------------------------------------------
# FSM states for add/remove admin dialogs (triggered via buttons)
# ---------------------------------------------------------------------------


class AdminState(StatesGroup):
    waiting_add_id = State()
    waiting_add_name = State()
    waiting_remove_id = State()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_env_admin_ids() -> set[int]:
    """Parse admin IDs from the ADMIN_ID env var (comma/semicolon/space separated)."""
    raw = os.getenv("ADMIN_ID", "")
    ids: set[int] = set()
    for part in raw.replace(";", ",").replace(" ", ",").split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids


def is_admin(user_id: int) -> bool:
    """Return True if the user is listed in the admins DB table or the ADMIN_ID env var."""
    return user_id in _get_env_admin_ids() or db.is_admin(user_id)


def _build_admin_list_lines() -> list[str]:
    """Build display lines for all admins, combining DB admins and env-configured ones."""
    lines: list[str] = ["👥 <b>Список администраторов:</b>\n"]

    db_admins = db.get_all_admins()
    db_admin_ids = {admin["user_id"] for admin in db_admins}

    if db_admins:
        for admin in db_admins:
            name = admin["full_name"] or "—"
            added = admin["added_at"]
            uid = admin["user_id"]
            lines.append(f"  • <code>{uid}</code> — {name} (добавлен: {added})")

    env_only_ids = _get_env_admin_ids() - db_admin_ids
    for uid in sorted(env_only_ids):
        lines.append(f"  • <code>{uid}</code> — из .env (ADMIN_ID)")

    if not db_admins and not env_only_ids:
        lines.append("Администраторов нет.")

    return lines


def _build_admin_keyboard() -> types.InlineKeyboardMarkup:
    """Build inline keyboard for admin panel."""
    builder = InlineKeyboardBuilder()

    builder.row(InlineKeyboardButton(text="🔄 Обновить данные с API", callback_data="adm:reload"))
    builder.row(InlineKeyboardButton(text="👥 Список администраторов", callback_data="adm:list"))
    builder.row(
        InlineKeyboardButton(text="➕ Добавить администратора", callback_data="adm:add"),
        InlineKeyboardButton(text="➖ Удалить администратора", callback_data="adm:remove"),
    )
    builder.row(InlineKeyboardButton(text="📋 Посмотреть фидбек", callback_data="adm:feedback"))

    return builder.as_markup()


ADMIN_PANEL_TEXT = "🛠 <b>Панель администратора</b>\n\nВыберите действие:"

# Telegram message length limit is 4096; keep a safety margin.
_MESSAGE_CHUNK_LIMIT = 4000


async def _replace_message(
    message: types.Message,
    text: str,
    reply_markup: types.InlineKeyboardMarkup,
) -> None:
    """Replace the given message's content, editing it in place when possible."""
    try:
        await message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    except TelegramBadRequest:
        await message.answer(text, parse_mode="HTML", reply_markup=reply_markup)


def _chunk_lines(lines: list[str], limit: int = _MESSAGE_CHUNK_LIMIT) -> list[str]:
    """Group lines into chunks that each stay under the given character limit."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # account for the joining newline
        if current and current_len + line_len > limit:
            chunks.append("\n".join(current))
            current = []
            current_len = 0
        current.append(line)
        current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks or [""]


# ---------------------------------------------------------------------------
# /admin — show admin panel with inline keyboard
# ---------------------------------------------------------------------------


@router.message(Command("admin"))
async def cmd_admin(message: types.Message, state: FSMContext):
    if not message.from_user:
        return
    user_id = message.from_user.id

    if not is_admin(user_id):
        return await message.answer("⛔ У вас нет доступа к панели администратора.")

    await state.clear()

    await message.answer(
        "🛠 <b>Панель администратора</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=_build_admin_keyboard(),
    )


# ---------------------------------------------------------------------------
# Callback: 🔄 Обновить данные с API
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "adm:reload")
async def cb_reload(callback: types.CallbackQuery):
    if not callback.from_user or not callback.message:
        return await callback.answer()

    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await callback.answer()

    back_builder = InlineKeyboardBuilder()
    back_builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back"))

    await _replace_message(callback.message, "⏳ Загружаю данные с API...", back_builder.as_markup())

    try:
        await learn_module.load_data()
        lessons_count = len(learn_module.data_lessons.get("results", []))
        chords_count = len(learn_module.data_chords.get("results", []))
        await _replace_message(
            callback.message,
            f"✅ <b>Данные успешно обновлены!</b>\n\n"
            f"📚 Уроков: <b>{lessons_count}</b>\n"
            f"🎸 Аккордов: <b>{chords_count}</b>",
            back_builder.as_markup(),
        )
    except Exception as e:
        await _replace_message(
            callback.message,
            f"❌ Ошибка при загрузке данных: {e}",
            back_builder.as_markup(),
        )


# ---------------------------------------------------------------------------
# Callback: 👥 Список администраторов
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "adm:list")
async def cb_list(callback: types.CallbackQuery):
    if not callback.from_user or not callback.message:
        return await callback.answer()

    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await callback.answer()

    lines = _build_admin_list_lines()

    back_builder = InlineKeyboardBuilder()
    back_builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back"))

    await callback.message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=back_builder.as_markup(),
    )


# ---------------------------------------------------------------------------
# Callback: 📋 Посмотреть фидбек
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "adm:feedback")
async def cb_feedback(callback: types.CallbackQuery):
    if not callback.from_user or not callback.message:
        return await callback.answer()

    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await callback.answer()

    feedback_list = db.get_recent_feedback(days=30)

    if feedback_list:
        lines: list[str] = ["📋 <b>Фидбек за последний месяц:</b>"]
        for fb in feedback_list:
            name = html.escape(fb["user_name"] or "—")
            text = html.escape(fb["text"] or "")
            date = fb["date"]
            lines.append(f"\n🗓 <b>{date}</b> — {name}\n{text}")
    else:
        lines = ["📋 <b>Фидбек за последний месяц:</b>", "\nФидбека нет."]

    chunks = _chunk_lines(lines)

    back_builder = InlineKeyboardBuilder()
    back_builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back"))

    await _replace_message(callback.message, chunks[0], back_builder.as_markup())
    for chunk in chunks[1:]:
        await callback.message.answer(chunk, parse_mode="HTML", reply_markup=back_builder.as_markup())


# ---------------------------------------------------------------------------
# Callback: ➕ Добавить администратора (FSM)
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "adm:add")
async def cb_add_start(callback: types.CallbackQuery, state: FSMContext):
    if not callback.from_user or not callback.message:
        return await callback.answer()

    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await callback.answer()
    await state.set_state(AdminState.waiting_add_id)

    cancel_builder = InlineKeyboardBuilder()
    cancel_builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel"))

    await callback.message.answer(
        "➕ <b>Добавление администратора</b>\n\nВведите <b>Telegram ID</b> нового администратора (только цифры):",
        parse_mode="HTML",
        reply_markup=cancel_builder.as_markup(),
    )


@router.message(AdminState.waiting_add_id)
async def fsm_add_id(message: types.Message, state: FSMContext):
    if not message.text or not message.from_user:
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("❌ Введите корректный Telegram ID (только цифры).")

    new_id = int(text)

    await state.update_data(new_admin_id=new_id)
    await state.set_state(AdminState.waiting_add_name)

    cancel_builder = InlineKeyboardBuilder()
    cancel_builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel"))

    await message.answer(
        f"✏️ Теперь введите имя для <code>{new_id}</code> (или напишите <b>—</b> чтобы пропустить):",
        parse_mode="HTML",
        reply_markup=cancel_builder.as_markup(),
    )


@router.message(AdminState.waiting_add_name)
async def fsm_add_name(message: types.Message, state: FSMContext):
    if not message.text or not message.from_user:
        return

    data = await state.get_data()
    new_id: int = data["new_admin_id"]
    name = message.text.strip() if message.text.strip() != "—" else "Без имени"

    await state.clear()

    added = db.add_admin(new_id, name)
    if added:
        text = f"✅ Администратор <code>{new_id}</code> (<b>{name}</b>) успешно добавлен."
    else:
        text = f"ℹ️ Пользователь <code>{new_id}</code> уже является администратором."

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=_build_admin_keyboard(),
    )


# ---------------------------------------------------------------------------
# Callback: ➖ Удалить администратора (FSM)
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "adm:remove")
async def cb_remove_start(callback: types.CallbackQuery, state: FSMContext):
    if not callback.from_user or not callback.message:
        return await callback.answer()

    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await callback.answer()

    db_admins = db.get_all_admins()

    builder = InlineKeyboardBuilder()

    if db_admins:
        for admin in db_admins:
            name = admin["full_name"] or "Без имени"
            uid = admin["user_id"]
            builder.row(
                InlineKeyboardButton(
                    text=f"🗑 {name} ({uid})",
                    callback_data=f"adm:rm:{uid}",
                )
            )
    else:
        await callback.message.answer(
            "ℹ️ Нет администраторов для удаления (БД пуста).",
            reply_markup=_build_admin_keyboard(),
        )
        return

    builder.row(InlineKeyboardButton(text="✏️ Ввести ID вручную", callback_data="adm:remove_manual"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="adm:back"))

    await callback.message.answer(
        "➖ <b>Выберите администратора для удаления:</b>",
        parse_mode="HTML",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("adm:rm:"))
async def cb_remove_confirm(callback: types.CallbackQuery):
    if not callback.from_user or not callback.message:
        return await callback.answer()

    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    target_id = int(callback.data.split(":")[-1])

    removed = db.remove_admin(target_id)
    await callback.answer()

    if removed:
        text = f"✅ Администратор <code>{target_id}</code> удалён."
    else:
        text = f"❌ Пользователь <code>{target_id}</code> не найден среди администраторов."

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=_build_admin_keyboard(),
    )


@router.callback_query(F.data == "adm:remove_manual")
async def cb_remove_manual(callback: types.CallbackQuery, state: FSMContext):
    if not callback.from_user or not callback.message:
        return await callback.answer()

    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await callback.answer()
    await state.set_state(AdminState.waiting_remove_id)

    cancel_builder = InlineKeyboardBuilder()
    cancel_builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="adm:cancel"))

    await callback.message.answer(
        "✏️ Введите <b>Telegram ID</b> администратора для удаления:",
        parse_mode="HTML",
        reply_markup=cancel_builder.as_markup(),
    )


@router.message(AdminState.waiting_remove_id)
async def fsm_remove_id(message: types.Message, state: FSMContext):
    if not message.text or not message.from_user:
        return

    text = message.text.strip()
    if not text.isdigit():
        return await message.answer("❌ Введите корректный Telegram ID (только цифры).")

    target_id = int(text)
    await state.clear()

    removed = db.remove_admin(target_id)
    if removed:
        result_text = f"✅ Администратор <code>{target_id}</code> удалён."
    else:
        result_text = f"❌ Пользователь <code>{target_id}</code> не найден среди администраторов."

    await message.answer(
        result_text,
        parse_mode="HTML",
        reply_markup=_build_admin_keyboard(),
    )


# ---------------------------------------------------------------------------
# Callback: ◀️ Назад — return to main admin panel
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "adm:back")
async def cb_back(callback: types.CallbackQuery, state: FSMContext):
    if not callback.from_user or not callback.message:
        return await callback.answer()

    if not is_admin(callback.from_user.id):
        return await callback.answer("⛔ Нет доступа.", show_alert=True)

    await callback.answer()
    await state.clear()

    await _replace_message(callback.message, ADMIN_PANEL_TEXT, _build_admin_keyboard())


# ---------------------------------------------------------------------------
# Callback: ❌ Отмена (FSM)
# ---------------------------------------------------------------------------


@router.callback_query(F.data == "adm:cancel")
async def cb_cancel(callback: types.CallbackQuery, state: FSMContext):
    if not callback.from_user or not callback.message:
        return await callback.answer()

    await callback.answer("Отменено")
    await state.clear()

    await callback.message.answer(
        "🛠 <b>Панель администратора</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=_build_admin_keyboard(),
    )


# ---------------------------------------------------------------------------
# /admin_add and /admin_remove still work as text commands
# ---------------------------------------------------------------------------


@router.message(Command("admin_add"))
async def cmd_admin_add(message: types.Message, command: CommandObject):
    if not message.from_user:
        return

    if not is_admin(message.from_user.id):
        return await message.answer("⛔ У вас нет доступа к панели администратора.")

    if not command.args:
        return await message.answer(
            "ℹ️ Использование: <code>/admin_add &lt;user_id&gt; [имя]</code>\n"
            "Пример: <code>/admin_add 123456789 Иван</code>",
            parse_mode="HTML",
        )

    parts = command.args.split(maxsplit=1)
    user_id_str = parts[0]
    name = parts[1] if len(parts) > 1 else "Без имени"

    if not user_id_str.isdigit():
        return await message.answer("❌ user_id должен быть числом.")

    new_admin_id = int(user_id_str)

    added = db.add_admin(new_admin_id, name)
    if added:
        await message.answer(
            f"✅ Администратор <code>{new_admin_id}</code> (<b>{name}</b>) успешно добавлен.",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            f"ℹ️ Пользователь <code>{new_admin_id}</code> уже является администратором.",
            parse_mode="HTML",
        )


@router.message(Command("admin_remove"))
async def cmd_admin_remove(message: types.Message, command: CommandObject):
    if not message.from_user:
        return

    if not is_admin(message.from_user.id):
        return await message.answer("⛔ У вас нет доступа к панели администратора.")

    if not command.args:
        return await message.answer(
            "ℹ️ Использование: <code>/admin_remove &lt;user_id&gt;</code>\nПример: <code>/admin_remove 123456789</code>",
            parse_mode="HTML",
        )

    user_id_str = command.args.strip()
    if not user_id_str.isdigit():
        return await message.answer("❌ user_id должен быть числом.")

    target_id = int(user_id_str)

    removed = db.remove_admin(target_id)
    if removed:
        await message.answer(f"✅ Администратор <code>{target_id}</code> удалён.", parse_mode="HTML")
    else:
        await message.answer(
            f"❌ Пользователь <code>{target_id}</code> не найден среди администраторов БД.",
            parse_mode="HTML",
        )


@router.message(Command("admin_list"))
async def cmd_admin_list(message: types.Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return await message.answer("⛔ У вас нет доступа к панели администратора.")

    lines = _build_admin_list_lines()

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("reload_data"))
async def cmd_reload_data(message: types.Message):
    if not message.from_user or not is_admin(message.from_user.id):
        return await message.answer("⛔ У вас нет доступа к панели администратора.")

    await message.answer("⏳ Загружаю данные с API...")
    try:
        await learn_module.load_data()
        lessons_count = len(learn_module.data_lessons.get("results", []))
        chords_count = len(learn_module.data_chords.get("results", []))
        await message.answer(
            f"✅ <b>Данные успешно обновлены!</b>\n\n"
            f"📚 Уроков загружено: <b>{lessons_count}</b>\n"
            f"🎸 Аккордов загружено: <b>{chords_count}</b>",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при загрузке данных: {e}")

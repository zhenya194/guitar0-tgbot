from aiogram import Router, types
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.database import db

router = Router()


class FeedbackState(StatesGroup):
    waiting_for_feedback = State()


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    if message.from_user:
        db.add_user(message.from_user.id, message.from_user.full_name)
        first_name = message.from_user.first_name or "пользователь"
        await message.answer(
            f"Здравствуйте, {first_name}! Используйте команду /help, чтобы получить справку по командам."
        )


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return await message.answer("Нет активных действий для отмены.")
    await state.clear()
    await message.answer("❌ Действие отменено.")


@router.message(Command("fb"))
async def cmd_feedback(message: types.Message, command: CommandObject, state: FSMContext):
    if command.args:
        await state.clear()
        if message.from_user:
            db.add_feedback(message.from_user.id, message.from_user.full_name, command.args)
        return await message.answer("✅ Спасибо за обратную связь!")

    await state.set_state(FeedbackState.waiting_for_feedback)
    await message.answer(
        "✍️ Пожалуйста, напишите ваш отзыв или предложение (для отмены отправьте /cancel):"
    )


@router.message(FeedbackState.waiting_for_feedback)
async def process_feedback(message: types.Message, state: FSMContext):
    if not message.text:
        return await message.answer("Пожалуйста, отправьте текстовое сообщение.")

    if message.text.strip() == "/cancel":
        await state.clear()
        return await message.answer("❌ Действие отменено.")

    if message.from_user:
        db.add_feedback(message.from_user.id, message.from_user.full_name, message.text)

    await state.clear()
    await message.answer("✅ Спасибо за обратную связь!")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    return await message.answer(
        "Команды бота Guitar 0:\n\n"
        "/start - перезапустить бота\n"
        "/help - показать это сообщение\n"
        "/fb [сообщение] - отправить обратную связь\n"
        "/lessons [номер] - информация об уроке\n"
        "/chords [аккорд] - аппликатура аккорда\n"
        "/cancel - отменить текущий ввод"
    )


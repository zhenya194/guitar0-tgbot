from aiogram.filters import CommandObject

from db.database import db
from routers import base
from tests.conftest import make_user


class TestKeyboards:
    def test_get_main_keyboard_has_expected_buttons(self):
        markup = base.get_main_keyboard()
        texts = {btn.text for row in markup.keyboard for btn in row}
        assert texts == {"📚 Уроки", "🎸 Аккорды", "✍️ Обратная связь", "ℹ️ Команды"}

    def test_get_cancel_keyboard_has_cancel_button(self):
        markup = base.get_cancel_keyboard()
        texts = {btn.text for row in markup.keyboard for btn in row}
        assert texts == {"❌ Отмена"}


class TestCmdStart:
    async def test_greets_user_by_first_name(self, make_message, fsm_context):
        message = make_message(user=make_user(first_name="Petya"))

        await base.cmd_start(message, fsm_context)

        message.answer.assert_awaited_once()
        assert "Petya" in message.answer.call_args.args[0]

    async def test_clears_state(self, make_message, fsm_context):
        await fsm_context.set_state("SomeState")
        message = make_message()

        await base.cmd_start(message, fsm_context)

        assert await fsm_context.get_state() is None

    async def test_no_from_user_does_not_answer(self, make_message, fsm_context):
        message = make_message(user=None)
        message.from_user = None

        await base.cmd_start(message, fsm_context)

        message.answer.assert_not_awaited()


class TestCmdCancel:
    async def test_no_active_state_reports_nothing_to_cancel(self, make_message, fsm_context):
        message = make_message()

        await base.cmd_cancel(message, fsm_context)

        message.answer.assert_awaited_once()
        assert "Нет активных" in message.answer.call_args.args[0]

    async def test_clears_active_state(self, make_message, fsm_context):
        await fsm_context.set_state("SomeState")
        message = make_message()

        await base.cmd_cancel(message, fsm_context)

        assert await fsm_context.get_state() is None
        assert "отменено" in message.answer.call_args.args[0]


class TestCmdFeedback:
    async def test_with_args_saves_feedback_immediately(self, make_message, fsm_context):
        user = make_user(user_id=42, full_name="Anna")
        message = make_message(user=user)
        command = CommandObject(command="fb", args="Love the bot")

        await base.cmd_feedback(message, command=command, state=fsm_context)

        stored = db.get_recent_feedback()
        assert len(stored) == 1
        assert stored[0]["user_id"] == 42
        assert stored[0]["text"] == "Love the bot"
        message.answer.assert_awaited_once()
        assert "Спасибо" in message.answer.call_args.args[0]

    async def test_with_args_clears_existing_state(self, make_message, fsm_context):
        await fsm_context.set_state("SomeState")
        message = make_message()
        command = CommandObject(command="fb", args="hi")

        await base.cmd_feedback(message, command=command, state=fsm_context)

        assert await fsm_context.get_state() is None

    async def test_without_args_prompts_and_sets_state(self, make_message, fsm_context):
        message = make_message()

        await base.cmd_feedback(message, command=None, state=fsm_context)

        assert await fsm_context.get_state() == base.FeedbackState.waiting_for_feedback.state
        message.answer.assert_awaited_once()
        assert "напишите ваш отзыв" in message.answer.call_args.args[0]

    async def test_without_state_still_prompts(self, make_message):
        message = make_message()
        command = CommandObject(command="fb", args=None)

        await base.cmd_feedback(message, command=command, state=None)

        message.answer.assert_awaited_once()


class TestProcessFeedback:
    async def test_saves_feedback_and_clears_state(self, make_message, fsm_context):
        await fsm_context.set_state(base.FeedbackState.waiting_for_feedback)
        user = make_user(user_id=7, full_name="Boris")
        message = make_message(text="Really nice lessons", user=user)

        await base.process_feedback(message, fsm_context)

        stored = db.get_recent_feedback()
        assert len(stored) == 1
        assert stored[0]["user_id"] == 7
        assert stored[0]["text"] == "Really nice lessons"
        assert await fsm_context.get_state() is None
        assert "Спасибо" in message.answer.call_args.args[0]

    async def test_cancel_command_clears_state_without_saving(self, make_message, fsm_context):
        await fsm_context.set_state(base.FeedbackState.waiting_for_feedback)
        message = make_message(text="/cancel")

        await base.process_feedback(message, fsm_context)

        assert db.get_recent_feedback() == []
        assert await fsm_context.get_state() is None
        assert "отменено" in message.answer.call_args.args[0]

    async def test_empty_text_asks_for_text_message(self, make_message, fsm_context):
        message = make_message(text=None)

        await base.process_feedback(message, fsm_context)

        message.answer.assert_awaited_once()
        assert "текстовое сообщение" in message.answer.call_args.args[0]


class TestCmdHelp:
    async def test_lists_commands(self, make_message):
        message = make_message()

        await base.cmd_help(message)

        message.answer.assert_awaited_once()
        text = message.answer.call_args.args[0]
        assert "/start" in text
        assert "/fb" in text

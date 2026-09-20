from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import main


class TestMain:
    async def test_exits_when_token_missing(self, monkeypatch, capsys):
        monkeypatch.setattr(main, "TOKEN", None)

        with pytest.raises(SystemExit) as exc_info:
            await main.main()

        assert exc_info.value.code == 1
        assert "BOT_TOKEN" in capsys.readouterr().out

    async def test_runs_bot_when_token_present(self, monkeypatch):
        monkeypatch.setattr(main, "TOKEN", "dummy-token")

        fake_bot = MagicMock()
        fake_bot.set_my_commands = AsyncMock()
        fake_bot.delete_webhook = AsyncMock()

        fake_dp = MagicMock()
        fake_dp.include_router = MagicMock()
        fake_dp.start_polling = AsyncMock()

        with (
            patch.object(main, "Bot", return_value=fake_bot) as bot_cls,
            patch.object(main, "Dispatcher", return_value=fake_dp),
            patch.object(main.learn, "load_data", new=AsyncMock()),
        ):
            await main.main()

        bot_cls.assert_called_once_with(token="dummy-token")
        fake_bot.set_my_commands.assert_awaited_once()
        fake_bot.delete_webhook.assert_awaited_once_with(drop_pending_updates=True)
        fake_dp.start_polling.assert_awaited_once_with(fake_bot)
        assert fake_dp.include_router.call_count == 3



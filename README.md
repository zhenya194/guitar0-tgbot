<div align="center">

# 🎸 Guitar 0 Telegram Bot

**Unofficial Telegram bot for [Guitar 0](https://api.guitar0.net/api/v1/docs/redoc/)** — learn guitar lessons and chord fingerings right in Telegram.

[![CI](https://github.com/zhenya194/guitar0-tgbot/actions/workflows/test.yml/badge.svg)](https://github.com/zhenya194/guitar0-tgbot/actions/workflows/test.yml)
[![Bandit](https://github.com/zhenya194/guitar0-tgbot/actions/workflows/bandit.yml/badge.svg)](https://github.com/zhenya194/guitar0-tgbot/actions/workflows/bandit.yml)
[![codecov](https://codecov.io/gh/zhenya194/guitar0-tgbot/branch/main/graph/badge.svg)](https://codecov.io/gh/zhenya194/guitar0-tgbot)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![aiogram 3](https://img.shields.io/badge/aiogram-3.x-2CA5E0.svg)](https://docs.aiogram.dev/)
[![License: GPL v3](https://img.shields.io/badge/license-GPLv3-blue.svg)](LICENSE)

</div>

> [!NOTE]
> This is an **unofficial** Guitar 0 Telegram bot, not affiliated with the Guitar 0 team.

---

## ✨ Features

- 📚 **Lessons** — browse and read guitar lessons pulled from the Guitar 0 API
- 🎸 **Chords** — look up chord fingerings/diagrams on demand
- ✍️ **Feedback** — send feedback straight from the chat with `/fb`
- 🛠️ **Admin panel** — manage admins and reload cached lesson/chord data with `/admin`
- 💾 **Persistent FSM storage** — conversation state is stored in SQLite, not memory

## 🧰 Tech Stack

| Component | Choice |
|---|---|
| Language | Python 3.13+ |
| Bot framework | [aiogram](https://docs.aiogram.dev/) 3 |
| Storage | SQLite |
| Config | `python-dotenv` |
| Data source | [Guitar 0 API](https://api.guitar0.net/api/v1/docs/redoc/) |
| Linting | [ruff](https://docs.astral.sh/ruff/) |
| Testing | [pytest](https://docs.pytest.org/) + [pytest-cov](https://pytest-cov.readthedocs.io/) |

## 🚀 Getting Started

### Prerequisites

- Python 3.13+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### Installation

```sh
git clone https://github.com/zhenya194/guitar0-tgbot.git
cd guitar0-tgbot
make install
```

### Configuration

Copy the example environment file and fill in your bot token:

```sh
cp .env.example .env
```

```dotenv
BOT_TOKEN=your-telegram-bot-token
ADMIN_ID=123456789,987654321
```

### Run

```sh
make run
```
or
```sh
python main.py
```

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow.

## 📄 License

Licensed under the [GNU GPLv3](LICENSE).

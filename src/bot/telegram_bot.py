"""Telegram bot entry point for Braiinz Education."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.bot.handlers import (
    diagnostic_handler,
    flashcard_handler,
    message_handler,
    profil_handler,
    start_handler,
    tuteur_handler,
)


def main() -> None:
    """Build the Telegram application, register handlers, and start polling."""
    load_dotenv(override=True)

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    data_dir = os.environ.get("DATA_DIR", "data")

    app = Application.builder().token(token).build()
    app.bot_data["data_dir"] = data_dir

    # Command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("diagnostic", diagnostic_handler))
    app.add_handler(CommandHandler("tuteur", tuteur_handler))
    app.add_handler(CommandHandler("flashcard", flashcard_handler))
    app.add_handler(CommandHandler("profil", profil_handler))

    # Message handler for all text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.run_polling()


if __name__ == "__main__":
    main()

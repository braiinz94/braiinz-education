"""Tests for Telegram bot handlers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.bot.handlers import (
    get_or_create_profile,
    message_handler,
    profil_handler,
    start_handler,
)
from src.student_profile import StudentProfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_update() -> MagicMock:
    """A mock Telegram Update with a standard user."""
    update = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.first_name = "Younes"
    update.message.text = ""
    update.message.reply_text = AsyncMock()
    return update


@pytest.fixture
def mock_context(tmp_data_dir: Path) -> MagicMock:
    """A mock CallbackContext with bot_data pointing to tmp_data_dir."""
    context = MagicMock()
    context.bot_data = {"data_dir": str(tmp_data_dir)}
    context.user_data = {}
    return context


# ---------------------------------------------------------------------------
# Sync tests
# ---------------------------------------------------------------------------


def test_creates_new_profile(mock_update, mock_context):
    """get_or_create_profile creates a profile with correct id and name."""
    profile = get_or_create_profile(mock_update, mock_context)

    assert profile.student_id == "tg-12345"
    assert profile.display_name == "Younes"
    assert profile.level == "seconde"
    assert mock_context.user_data["profile"] is profile


def test_returns_existing_profile(mock_update, mock_context):
    """get_or_create_profile returns the same profile on second call."""
    first = get_or_create_profile(mock_update, mock_context)
    second = get_or_create_profile(mock_update, mock_context)

    assert first is second


# ---------------------------------------------------------------------------
# Async tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_sends_welcome(mock_update, mock_context):
    """start_handler replies with a message containing 'Braiinz Education' and student name."""
    await start_handler(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    reply_text = mock_update.message.reply_text.call_args[0][0]
    assert "Braiinz Education" in reply_text
    assert "Younes" in reply_text


@pytest.mark.asyncio
async def test_profil_shows_competencies(mock_update, mock_context):
    """profil_handler shows a student's evaluated competencies."""
    # Pre-populate a profile with a competency
    profile = StudentProfile(
        student_id="tg-12345",
        display_name="Younes",
        level="seconde",
    )
    profile.update_competency("nombres.equations", mastery=0.65, pisa_level=4)
    mock_context.user_data["profile"] = profile

    await profil_handler(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    reply_text = mock_update.message.reply_text.call_args[0][0]
    assert "nombres.equations" in reply_text


@pytest.mark.asyncio
async def test_sensitive_message_intercepted(mock_update, mock_context):
    """message_handler intercepts sensitive messages and returns the crisis line (3114)."""
    mock_update.message.text = "Je veux mourir"

    await message_handler(mock_update, mock_context)

    mock_update.message.reply_text.assert_called_once()
    reply_text = mock_update.message.reply_text.call_args[0][0]
    assert "3114" in reply_text

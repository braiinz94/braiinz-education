"""Shared test fixtures for braiinz-education test suite."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create and return tmp_path/data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def mock_anthropic_response():
    """Factory that returns a configurable mock Anthropic response."""

    def _factory(
        text: str = '{"answer": "42"}',
        input_tokens: int = 10,
        output_tokens: int = 20,
    ) -> MagicMock:
        response = MagicMock()
        response.usage.input_tokens = input_tokens
        response.usage.output_tokens = output_tokens

        block = MagicMock()
        block.type = "text"
        block.text = text
        response.content = [block]

        return response

    return _factory


@pytest.fixture
def mock_anthropic_client(mock_anthropic_response):
    """Patch src.llm_router.anthropic.Anthropic and return the mock client."""
    with patch("src.llm_router.anthropic.Anthropic") as MockClass:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_anthropic_response()
        MockClass.return_value = mock_client
        yield mock_client

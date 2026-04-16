"""Tests for LLMRouter — 3-tier LLM routing module."""

from __future__ import annotations

import pytest

from src.llm_router import TIER_CONFIG, LLMRouter

# ---------------------------------------------------------------------------
# TestLLMRouterInit
# ---------------------------------------------------------------------------


class TestLLMRouterInit:
    def test_default_tier_is_fast(self):
        router = LLMRouter("test-agent")
        assert router.default_tier == "fast"

    def test_custom_default_tier(self):
        router = LLMRouter("test-agent", default_tier="standard")
        assert router.default_tier == "standard"

    def test_invalid_default_tier_raises(self):
        with pytest.raises(ValueError, match="Invalid tier"):
            LLMRouter("test-agent", default_tier="turbo")


# ---------------------------------------------------------------------------
# TestLLMRouterTiers
# ---------------------------------------------------------------------------


class TestLLMRouterTiers:
    def test_fast_tier_uses_haiku(self):
        assert "haiku" in TIER_CONFIG["fast"]["model"]

    def test_standard_tier_uses_sonnet(self):
        assert "sonnet" in TIER_CONFIG["standard"]["model"]

    def test_deep_tier_uses_opus(self):
        assert "opus" in TIER_CONFIG["deep"]["model"]

    def test_all_tiers_have_cost(self):
        for tier_name, config in TIER_CONFIG.items():
            assert "cost_eur_per_1k" in config, f"Tier '{tier_name}' missing cost"
            assert "input" in config["cost_eur_per_1k"]
            assert "output" in config["cost_eur_per_1k"]


# ---------------------------------------------------------------------------
# TestLLMRouterCall
# ---------------------------------------------------------------------------


class TestLLMRouterCall:
    def test_call_returns_parsed_json(self, mock_anthropic_client):
        router = LLMRouter("test-agent")
        result = router.call("What is 6*7?")
        assert result == {"answer": "42"}

    def test_call_text_mode(self, mock_anthropic_client, mock_anthropic_response):
        mock_anthropic_client.messages.create.return_value = mock_anthropic_response(
            text="Hello, world!"
        )
        router = LLMRouter("test-agent")
        result = router.call("Say hello", response_format="text")
        assert result == "Hello, world!"

    def test_call_with_system_prompt(self, mock_anthropic_client):
        router = LLMRouter("test-agent")
        router.call("User prompt", system="You are a helpful assistant.")
        call_kwargs = mock_anthropic_client.messages.create.call_args[1]
        assert call_kwargs.get("system") == "You are a helpful assistant."

    def test_call_invalid_tier_raises(self, mock_anthropic_client):
        router = LLMRouter("test-agent")
        with pytest.raises(ValueError, match="Invalid tier"):
            router.call("prompt", tier="ultra")

    def test_call_tracks_usage(self, mock_anthropic_client, mock_anthropic_response):
        mock_anthropic_client.messages.create.return_value = mock_anthropic_response(
            input_tokens=15, output_tokens=30
        )
        router = LLMRouter("test-agent")
        router.call("Track me")
        assert router.total_tokens_in == 15
        assert router.total_tokens_out == 30
        assert router.total_calls == 1

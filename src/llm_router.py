"""LLMRouter — point d'entrée unique pour tous les appels LLM (3 tiers)."""

from __future__ import annotations

import json
import logging

import anthropic

logger = logging.getLogger(__name__)

TIER_CONFIG: dict[str, dict] = {
    "fast": {
        "model": "claude-haiku-4-5",
        "max_tokens": 1024,
        "cost_eur_per_1k": {"input": 0.001, "output": 0.005},
    },
    "standard": {
        "model": "claude-sonnet-4-6",
        "max_tokens": 4096,
        "cost_eur_per_1k": {"input": 0.003, "output": 0.015},
    },
    "deep": {
        "model": "claude-opus-4-6",
        "max_tokens": 16000,
        "cost_eur_per_1k": {"input": 0.005, "output": 0.025},
    },
}


class LLMRouter:
    """Routes LLM calls to the appropriate tier (fast / standard / deep)."""

    def __init__(self, agent_id: str, *, default_tier: str = "fast") -> None:
        if default_tier not in TIER_CONFIG:
            raise ValueError(
                f"Invalid tier '{default_tier}'. Must be one of {list(TIER_CONFIG)}"
            )
        self._agent_id = agent_id
        self._default_tier = default_tier
        self._total_tokens_in: int = 0
        self._total_tokens_out: int = 0
        self._total_calls: int = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def default_tier(self) -> str:
        return self._default_tier

    @property
    def total_tokens_in(self) -> int:
        return self._total_tokens_in

    @property
    def total_tokens_out(self) -> int:
        return self._total_tokens_out

    @property
    def total_calls(self) -> int:
        return self._total_calls

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def call(
        self,
        prompt: str,
        *,
        tier: str | None = None,
        system: str | None = None,
        max_tokens: int | None = None,
        response_format: str = "json",
    ) -> dict | str:
        """Call the LLM and return parsed JSON (dict) or raw text (str)."""
        effective_tier = tier if tier is not None else self._default_tier
        if effective_tier not in TIER_CONFIG:
            raise ValueError(
                f"Invalid tier '{effective_tier}'. Must be one of {list(TIER_CONFIG)}"
            )

        config = TIER_CONFIG[effective_tier]
        kwargs: dict = {
            "model": config["model"],
            "max_tokens": max_tokens if max_tokens is not None else config["max_tokens"],
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system

        client = anthropic.Anthropic()
        response = client.messages.create(**kwargs)

        # Track usage
        self._total_tokens_in += response.usage.input_tokens
        self._total_tokens_out += response.usage.output_tokens
        self._total_calls += 1

        text = self._extract_text(response)

        if response_format == "text":
            return text

        # JSON mode
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            logger.warning(
                "LLMRouter[%s]: failed to parse JSON response: %r", self._agent_id, text
            )
            return {}

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_text(response) -> str:
        """Extract text from response content blocks."""
        parts: list[str] = []
        for block in response.content:
            if block.type == "text":
                parts.append(block.text)
        return "".join(parts)

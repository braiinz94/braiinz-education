"""LLMRouter — point d'entree unique pour tous les appels LLM (3 tiers).

Provider switchable via LLM_PROVIDER env var :
  - "anthropic" (defaut) : API Anthropic directe (US, via DPF + SCC).
  - "bedrock"            : AWS Bedrock (region AWS_REGION, defaut eu-west-3).
                           Recommande pour conformite Schrems II (donnees UE).

Model IDs peuvent etre override par tier :
  LLM_MODEL_FAST, LLM_MODEL_STANDARD, LLM_MODEL_DEEP
(utile sur Bedrock ou les IDs sont differents, e.g. inference profiles
 "eu.anthropic.claude-haiku-4-5-YYYYMMDD-v1:0").
"""

from __future__ import annotations

import json
import logging
import os

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

# Env-driven per-tier model override (useful for Bedrock, where IDs differ)
_TIER_ENV_OVERRIDE = {
    "fast": "LLM_MODEL_FAST",
    "standard": "LLM_MODEL_STANDARD",
    "deep": "LLM_MODEL_DEEP",
}


def _resolve_model(tier: str) -> str:
    """Return the model ID for a tier, honoring env overrides."""
    env_key = _TIER_ENV_OVERRIDE.get(tier)
    if env_key:
        override = os.environ.get(env_key)
        if override:
            return override
    return TIER_CONFIG[tier]["model"]


def _make_client():
    """Factory for the Anthropic client, switching on LLM_PROVIDER env var.

    Returns either anthropic.Anthropic() (default, direct API) or
    anthropic.AnthropicBedrock() (AWS Bedrock, region eu-west-3 by default).

    For tests: tests patch `src.llm_router.anthropic.Anthropic` — the default
    branch calls anthropic.Anthropic() directly, keeping mocks compatible.
    """
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    if provider == "bedrock":
        region = os.environ.get("AWS_REGION", "eu-west-3")
        return anthropic.AnthropicBedrock(aws_region=region)
    return anthropic.Anthropic()


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
            "model": _resolve_model(effective_tier),
            "max_tokens": max_tokens if max_tokens is not None else config["max_tokens"],
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system

        client = _make_client()
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

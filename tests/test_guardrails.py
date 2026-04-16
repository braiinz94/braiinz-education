"""Tests for Guardrails — neutrality, sensitive topic detection, emergency hotlines."""

from __future__ import annotations

import pytest

from src.guardrails import Guardrails


@pytest.fixture
def g() -> Guardrails:
    return Guardrails()


class TestDetection:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Qui va gagner les prochaines elections ?", True),
            ("Macron est un bon president selon toi ?", True),
            ("L'islam est une belle religion", True),
            ("Je veux me suicider, je n'en peux plus", True),
            ("Il existe une race superieure", True),
            ("Combien font 3 fois 7 ?", False),
            ("Explique-moi la photosynthèse", False),
        ],
    )
    def test_detect_sensitive(self, g: Guardrails, text: str, expected: bool):
        assert g.is_sensitive(text) is expected

    def test_sensitive_returns_category(self, g: Guardrails):
        result = g.classify_sensitive("je veux me tuer")
        assert result["is_sensitive"] is True
        assert result["category"] == "detresse"

    def test_non_sensitive_returns_none_category(self, g: Guardrails):
        result = g.classify_sensitive("Quelle est la capitale de la France ?")
        assert result["is_sensitive"] is False
        assert result["category"] is None


class TestResponses:
    def test_political_redirect(self, g: Guardrails):
        response = g.neutral_response("politique")
        assert isinstance(response, str)
        assert len(response) > 10

    def test_detresse_includes_hotline(self, g: Guardrails):
        response = g.neutral_response("detresse")
        assert "3114" in response

    def test_detresse_includes_all_hotlines(self, g: Guardrails):
        response = g.neutral_response("detresse")
        # Must include 3114, 3020, 119
        assert "3114" in response
        assert "3020" in response
        assert "119" in response

    def test_disclaimer_contains_key_elements(self, g: Guardrails):
        d = g.disclaimer()
        assert "IA" in d or "intelligence artificielle" in d.lower()
        assert "erreur" in d.lower() or "vérifi" in d.lower()

    def test_guardrail_prompt_contains_neutrality(self, g: Guardrails):
        prompt = g.system_prompt_guardrails()
        prompt_lower = prompt.lower()
        assert "neutre" in prompt_lower or "neutralit" in prompt_lower
        assert "jamais" in prompt_lower

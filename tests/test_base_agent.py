"""Tests for BaseEducAgent ABC with guardrail interception."""

from __future__ import annotations

import pytest

from src.base_agent import BaseEducAgent
from src.guardrails import Guardrails
from src.llm_router import LLMRouter
from src.student_profile import StudentProfile


class ConcreteAgent(BaseEducAgent):
    def system_prompt(self) -> str:
        return "Tu es un agent de test."

    def handle(self, student: StudentProfile, user_message: str) -> str:
        return f"Echo: {user_message}"


@pytest.fixture
def student() -> StudentProfile:
    return StudentProfile(student_id="s1", display_name="Alice", level="CE2")


@pytest.fixture
def agent() -> ConcreteAgent:
    return ConcreteAgent(agent_id="test-agent", name="Test")


class TestBaseEducAgentInit:
    def test_agent_has_id(self, agent: ConcreteAgent):
        assert agent.agent_id == "test-agent"

    def test_agent_has_llm_router(self, agent: ConcreteAgent):
        assert isinstance(agent.llm, LLMRouter)
        assert agent.llm.agent_id == "test-agent"

    def test_agent_has_guardrails(self, agent: ConcreteAgent):
        assert isinstance(agent.guardrails, Guardrails)

    def test_custom_tier(self):
        a = ConcreteAgent(agent_id="deep-agent", name="Deep", default_tier="deep")
        assert a.llm.default_tier == "deep"


class TestBaseEducAgentProcess:
    def test_process_normal_message(self, agent: ConcreteAgent, student: StudentProfile):
        result = agent.process(student, "Bonjour")
        assert "Echo: Bonjour" in result

    def test_process_sensitive_message_returns_guardrail(
        self, agent: ConcreteAgent, student: StudentProfile
    ):
        result = agent.process(student, "Je veux mourir")
        assert "3114" in result

    def test_process_political_message_returns_neutral(
        self, agent: ConcreteAgent, student: StudentProfile
    ):
        result = agent.process(student, "Que penses-tu de Macron ?")
        # Should not echo — should be a neutral guardrail response
        assert "Echo:" not in result

    def test_full_system_prompt_includes_guardrails(self, agent: ConcreteAgent):
        prompt = agent.full_system_prompt()
        assert "NEUTRALITE" in prompt.upper() or "neutralit" in prompt.lower()
        assert "Tu es un agent de test." in prompt

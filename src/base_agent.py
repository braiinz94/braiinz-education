"""BaseEducAgent — abstract base class for all Braiinz Education agents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.guardrails import Guardrails
from src.llm_router import LLMRouter
from src.student_profile import StudentProfile


class BaseEducAgent(ABC):
    """Abstract base for educational agents with integrated guardrail interception."""

    def __init__(self, agent_id: str, name: str, *, default_tier: str = "fast") -> None:
        self.agent_id = agent_id
        self.name = name
        self.llm = LLMRouter(agent_id, default_tier=default_tier)
        self.guardrails = Guardrails()

    @abstractmethod
    def system_prompt(self) -> str:
        """Return the agent-specific system prompt."""

    @abstractmethod
    def handle(self, student: StudentProfile, user_message: str) -> str:
        """Process a non-sensitive user message and return a response."""

    def full_system_prompt(self) -> str:
        """Combine guardrail block with agent-specific system prompt."""
        return self.guardrails.system_prompt_guardrails() + "\n\n" + self.system_prompt()

    def process(self, student: StudentProfile, user_message: str) -> str:
        """Check guardrails first; if sensitive, return neutral response; else call handle()."""
        result = self.guardrails.classify_sensitive(user_message)
        if result["is_sensitive"]:
            return self.guardrails.neutral_response(str(result["category"]))
        return self.handle(student, user_message)

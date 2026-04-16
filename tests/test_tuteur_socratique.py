"""Tests for TuteurSocratique — maieutic method, Ibn Khaldun 3 passes, ZPD scaffolding."""

from __future__ import annotations

import pytest

from src.agents.tuteur_socratique import Phase, TuteurSocratique
from src.student_profile import StudentProfile


@pytest.fixture
def agent() -> TuteurSocratique:
    return TuteurSocratique()


@pytest.fixture
def student() -> StudentProfile:
    s = StudentProfile(student_id="s2", display_name="Bob", level="seconde")
    s.update_competency("fonctions.affines", mastery=0.3, pisa_level=2)
    return s


def test_agent_id(agent: TuteurSocratique) -> None:
    assert agent.agent_id == "tuteur-socratique"


def test_default_tier_is_standard(agent: TuteurSocratique) -> None:
    assert agent.llm.default_tier == "standard"


def test_three_phases_ibn_khaldun(agent: TuteurSocratique) -> None:
    assert Phase.SURVOL.value == "survol"
    assert Phase.APPROFONDISSEMENT.value == "approfondissement"
    assert Phase.MAITRISE.value == "maitrise"


def test_system_prompt_contains_socratic(agent: TuteurSocratique) -> None:
    prompt = agent.system_prompt()
    prompt_lower = prompt.lower()
    assert "question" in prompt_lower
    assert "jamais" in prompt_lower


def test_system_prompt_contains_ibn_khaldun(agent: TuteurSocratique) -> None:
    prompt = agent.system_prompt().lower()
    assert "survol" in prompt or "passe" in prompt


def test_full_system_prompt_includes_guardrails(agent: TuteurSocratique) -> None:
    full = agent.full_system_prompt()
    assert "NEUTRALITE" in full


def test_context_includes_student_name(agent: TuteurSocratique, student: StudentProfile) -> None:
    ctx = agent.build_context(student, "fonctions.affines", Phase.SURVOL)
    assert "Bob" in ctx


def test_context_includes_competency(agent: TuteurSocratique, student: StudentProfile) -> None:
    ctx = agent.build_context(student, "fonctions.affines", Phase.SURVOL)
    assert "fonctions.affines" in ctx or "affines" in ctx.lower()


def test_context_includes_phase(agent: TuteurSocratique, student: StudentProfile) -> None:
    ctx = agent.build_context(student, "fonctions.affines", Phase.APPROFONDISSEMENT)
    assert "approfondissement" in ctx.lower()


def test_context_includes_zpd_for_scaffolding(agent: TuteurSocratique, student: StudentProfile) -> None:
    # Student has mastery=0.3 on fonctions.affines — in ZPD (<0.5)
    ctx = agent.build_context(student, "fonctions.affines", Phase.SURVOL)
    # Context should mention ZPD or scaffolding opportunity
    assert "zpd" in ctx.lower() or "zone" in ctx.lower() or "progresser" in ctx.lower()


def test_phase_for_low_mastery(agent: TuteurSocratique) -> None:
    assert agent.determine_phase(0.2) == Phase.SURVOL


def test_phase_for_medium_mastery(agent: TuteurSocratique) -> None:
    assert agent.determine_phase(0.5) == Phase.APPROFONDISSEMENT


def test_phase_for_high_mastery(agent: TuteurSocratique) -> None:
    assert agent.determine_phase(0.8) == Phase.MAITRISE

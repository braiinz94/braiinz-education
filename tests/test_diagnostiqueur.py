"""Tests for Diagnostiqueur agent — PISA mastery, Bayesian update."""

from __future__ import annotations

import pytest

from src.agents.diagnostiqueur import Diagnostiqueur
from src.student_profile import StudentProfile


@pytest.fixture
def agent() -> Diagnostiqueur:
    return Diagnostiqueur()


@pytest.fixture
def student() -> StudentProfile:
    return StudentProfile(student_id="s1", display_name="Alice", level="seconde")


def test_agent_id(agent: Diagnostiqueur) -> None:
    assert agent.agent_id == "diagnostiqueur"


def test_default_tier_is_fast(agent: Diagnostiqueur) -> None:
    assert agent.llm.default_tier == "fast"


def test_generate_returns_question_dict(agent: Diagnostiqueur) -> None:
    q = agent.generate_question("nombres.equations", bloom_level=3)
    assert isinstance(q, dict)
    assert "competency_id" in q
    assert "question" in q
    assert "expected_answer" in q
    assert "bloom_level" in q
    assert q["competency_id"] == "nombres.equations"
    assert q["bloom_level"] == 3


def test_generate_question_for_each_bloom_level(agent: Diagnostiqueur) -> None:
    for level in [1, 2, 3, 4]:
        q = agent.generate_question("fonctions.affines", bloom_level=level)
        assert q["bloom_level"] == level
        assert len(q["question"]) > 0


def test_correct_answer_updates_mastery_up(agent: Diagnostiqueur, student: StudentProfile) -> None:
    # Seed with a known mastery
    student.update_competency("nombres.equations", mastery=0.5, pisa_level=3)
    result = agent.evaluate_answer(student, "nombres.equations", is_correct=True)
    assert result["new_mastery"] > 0.5


def test_incorrect_answer_updates_mastery_down(agent: Diagnostiqueur, student: StudentProfile) -> None:
    student.update_competency("nombres.equations", mastery=0.5, pisa_level=3)
    result = agent.evaluate_answer(student, "nombres.equations", is_correct=False)
    assert result["new_mastery"] < 0.5


def test_mastery_clamped_0_to_1(agent: Diagnostiqueur, student: StudentProfile) -> None:
    # Start at max — correct answer should stay at 1.0
    student.update_competency("nombres.equations", mastery=1.0, pisa_level=6)
    result = agent.evaluate_answer(student, "nombres.equations", is_correct=True)
    assert result["new_mastery"] <= 1.0

    # Start at 0 — incorrect answer should stay at 0.0
    student.update_competency("nombres.equations", mastery=0.0, pisa_level=1)
    result = agent.evaluate_answer(student, "nombres.equations", is_correct=False)
    assert result["new_mastery"] >= 0.0


def test_new_competency_starts_at_0_3(agent: Diagnostiqueur, student: StudentProfile) -> None:
    # Competency not yet in profile
    result = agent.evaluate_answer(student, "geometrie.vecteurs", is_correct=True)
    # Should start at 0.3 then apply correct update: 0.3 + (1-0.3)*0.15 ≈ 0.405
    assert result["new_mastery"] > 0.3


@pytest.mark.parametrize("mastery,expected_pisa", [
    (0.0, 1),
    (0.15, 1),
    (0.25, 2),
    (0.45, 3),
    (0.65, 4),
    (0.80, 5),
    (0.95, 6),
])
def test_mastery_to_pisa_level(agent: Diagnostiqueur, mastery: float, expected_pisa: int) -> None:
    assert agent.mastery_to_pisa(mastery) == expected_pisa


def test_run_returns_competency_map(agent: Diagnostiqueur, student: StudentProfile) -> None:
    result = agent.run_diagnostic_static(student, "nombres")
    assert isinstance(result, dict)
    # Should have all competencies from the "nombres" chapter
    assert "nombres.ensembles" in result
    assert "nombres.equations" in result
    for comp_id, info in result.items():
        assert "mastery" in info
        assert "pisa_level" in info

"""Tests for CoachPratique — FSRS flashcards, interleaving, spaced repetition."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.agents.coach_pratique import CoachPratique, Flashcard, FlashcardDeck
from src.student_profile import StudentProfile


@pytest.fixture
def agent() -> CoachPratique:
    return CoachPratique()


@pytest.fixture
def student() -> StudentProfile:
    return StudentProfile(student_id="s3", display_name="Charlie", level="seconde")


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


def _past(seconds: int = 60) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def _future(hours: int = 24) -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def test_agent_id(agent: CoachPratique) -> None:
    assert agent.agent_id == "coach-pratique"


def test_default_tier_is_fast(agent: CoachPratique) -> None:
    assert agent.llm.default_tier == "fast"


def test_create_flashcard() -> None:
    card = Flashcard(
        card_id="c1",
        competency_id="nombres.equations",
        question="Qu'est-ce qu'une equation ?",
        answer="Une egalite avec une inconnue.",
    )
    assert card.card_id == "c1"
    assert card.review_count == 0
    assert card.interval_days == 1.0
    assert card.next_review <= datetime.now(timezone.utc)


def test_flashcard_to_dict_roundtrip() -> None:
    card = Flashcard(
        card_id="c2",
        competency_id="fonctions.affines",
        question="Q",
        answer="A",
        interval_days=3.0,
        review_count=5,
    )
    d = card.to_dict()
    assert isinstance(d["next_review"], str)  # ISO string
    card2 = Flashcard.from_dict(d)
    assert card2.card_id == card.card_id
    assert card2.interval_days == card.interval_days
    assert card2.review_count == card.review_count


def test_add_card() -> None:
    deck = FlashcardDeck(student_id="s3")
    card = Flashcard(card_id="c1", competency_id="nombres.equations", question="Q", answer="A")
    deck.add_card(card)
    assert len(deck.cards) == 1


def test_due_cards_returns_cards_due_now() -> None:
    deck = FlashcardDeck(student_id="s3")
    due_card = Flashcard(
        card_id="due",
        competency_id="nombres.equations",
        question="Q",
        answer="A",
        next_review=_past(),
    )
    deck.add_card(due_card)
    due = deck.get_due_cards()
    assert len(due) == 1
    assert due[0].card_id == "due"


def test_future_cards_not_due() -> None:
    deck = FlashcardDeck(student_id="s3")
    future_card = Flashcard(
        card_id="future",
        competency_id="nombres.equations",
        question="Q",
        answer="A",
        next_review=_future(),
    )
    deck.add_card(future_card)
    due = deck.get_due_cards()
    assert len(due) == 0


def test_interleave_shuffles_competencies() -> None:
    deck = FlashcardDeck(student_id="s3")
    # 3 cards from comp A, 3 from comp B — all due
    for i in range(3):
        deck.add_card(Flashcard(
            card_id=f"a{i}", competency_id="comp_a",
            question=f"Q{i}", answer="A", next_review=_past(),
        ))
        deck.add_card(Flashcard(
            card_id=f"b{i}", competency_id="comp_b",
            question=f"Q{i}", answer="A", next_review=_past(),
        ))

    # Without interleave
    regular = deck.get_due_cards(interleave=False)
    assert len(regular) == 6

    # With interleave — should still return all 6 but shuffled
    interleaved = deck.get_due_cards(interleave=True)
    assert len(interleaved) == 6


def test_review_card_updates_review_count() -> None:
    deck = FlashcardDeck(student_id="s3")
    card = Flashcard(card_id="c1", competency_id="nombres.equations", question="Q", answer="A",
                     next_review=_past())
    deck.add_card(card)
    deck.review_card("c1", rating=3)
    assert deck.cards[0].review_count == 1


def test_review_card_pushes_next_review() -> None:
    deck = FlashcardDeck(student_id="s3")
    now = datetime.now(timezone.utc)
    card = Flashcard(card_id="c1", competency_id="nombres.equations", question="Q", answer="A",
                     next_review=_past())
    deck.add_card(card)
    deck.review_card("c1", rating=4)  # rating 4 => interval *= 2.5, min 7 days
    assert deck.cards[0].next_review > now


def test_save_and_load(tmp_data_dir: Path) -> None:
    deck = FlashcardDeck(student_id="s_save")
    card = Flashcard(card_id="c1", competency_id="nombres.equations", question="Q?", answer="A.")
    deck.add_card(card)
    deck.save(tmp_data_dir)

    loaded = FlashcardDeck.load("s_save", tmp_data_dir)
    assert len(loaded.cards) == 1
    assert loaded.cards[0].card_id == "c1"
    assert loaded.student_id == "s_save"

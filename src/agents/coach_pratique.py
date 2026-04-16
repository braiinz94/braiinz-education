"""CoachPratique — FSRS-inspired flashcard system with interleaving and spaced repetition."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.base_agent import BaseEducAgent
from src.student_profile import StudentProfile


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# Rating multipliers: 1=Again, 2=Hard, 3=Good, 4=Easy
_MULTIPLIERS: dict[int, float] = {1: 0.5, 2: 1.0, 3: 2.0, 4: 2.5}
# Minimum interval in days per rating
_MIN_INTERVALS: dict[int, float] = {1: 0.01, 2: 1.0, 3: 3.0, 4: 7.0}


@dataclass
class Flashcard:
    """A single spaced-repetition flashcard."""
    card_id: str
    competency_id: str
    question: str
    answer: str
    next_review: datetime = field(default_factory=_now_utc)
    interval_days: float = 1.0
    review_count: int = 0

    def to_dict(self) -> dict:
        return {
            "card_id": self.card_id,
            "competency_id": self.competency_id,
            "question": self.question,
            "answer": self.answer,
            "next_review": self.next_review.isoformat(),
            "interval_days": self.interval_days,
            "review_count": self.review_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Flashcard":
        next_review = datetime.fromisoformat(data["next_review"])
        # Ensure timezone-aware
        if next_review.tzinfo is None:
            next_review = next_review.replace(tzinfo=timezone.utc)
        return cls(
            card_id=data["card_id"],
            competency_id=data["competency_id"],
            question=data["question"],
            answer=data["answer"],
            next_review=next_review,
            interval_days=data.get("interval_days", 1.0),
            review_count=data.get("review_count", 0),
        )


class FlashcardDeck:
    """A student's deck of flashcards with spaced repetition scheduling."""

    def __init__(self, student_id: str) -> None:
        self.student_id = student_id
        self.cards: list[Flashcard] = []

    def add_card(self, card: Flashcard) -> None:
        self.cards.append(card)

    def get_due_cards(self, *, interleave: bool = False) -> list[Flashcard]:
        """Return cards where next_review <= now. If interleave, shuffle the result."""
        now = _now_utc()
        due = [c for c in self.cards if c.next_review <= now]
        if interleave:
            due = list(due)
            random.shuffle(due)
        return due

    def review_card(self, card_id: str, rating: int) -> None:
        """Apply FSRS-inspired scheduling: update interval and next_review.

        Rating scale:
          1=Again (forgot), 2=Hard, 3=Good, 4=Easy
        """
        for card in self.cards:
            if card.card_id != card_id:
                continue
            multiplier = _MULTIPLIERS.get(rating, 1.0)
            min_interval = _MIN_INTERVALS.get(rating, 1.0)
            new_interval = max(min_interval, card.interval_days * multiplier)
            card.interval_days = new_interval
            card.next_review = _now_utc() + timedelta(days=new_interval)
            card.review_count += 1
            break

    def save(self, data_dir: Path | str) -> None:
        """Persist the deck to data_dir/flashcards/{student_id}.json."""
        target_dir = Path(data_dir) / "flashcards"
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / f"{self.student_id}.json"
        payload = {
            "student_id": self.student_id,
            "cards": [c.to_dict() for c in self.cards],
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        import os
        os.replace(tmp, path)

    @classmethod
    def load(cls, student_id: str, data_dir: Path | str) -> "FlashcardDeck":
        """Load a deck from disk. Returns empty deck if file not found."""
        path = Path(data_dir) / "flashcards" / f"{student_id}.json"
        deck = cls(student_id=student_id)
        if not path.exists():
            return deck
        data = json.loads(path.read_text(encoding="utf-8"))
        for card_data in data.get("cards", []):
            deck.add_card(Flashcard.from_dict(card_data))
        return deck


class CoachPratique(BaseEducAgent):
    """Coach pratique : flashcards FSRS avec repetition espacee et interleaving."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="coach-pratique",
            name="Coach Pratique",
            default_tier="fast",
        )

    def system_prompt(self) -> str:
        return (
            "Tu es le Coach Pratique Braiinz Education.\n\n"
            "FLASHCARDS ET REPETITION ESPACEE\n"
            "Tu aides l'eleve a consolider ses connaissances par la repetition espacee (methode FSRS).\n"
            "Apres chaque flashcard, l'eleve s'auto-evalue sur une echelle de 1 a 4 :\n"
            "  1 = Je n'ai pas du tout su (a repasser tres vite)\n"
            "  2 = J'ai eu du mal (a repasser demain)\n"
            "  3 = J'ai su avec un peu d'effort (a repasser dans quelques jours)\n"
            "  4 = J'ai su facilement (a repasser dans une semaine ou plus)\n\n"
            "L'interleaving (melange de competences) optimise la retention a long terme.\n"
            "Encourage l'eleve apres chaque session, celebre les progres, sois bienveillant sur les erreurs."
        )

    def handle(self, student: StudentProfile, user_message: str) -> str:
        return (
            f"[Coach Pratique] Pret pour ta session de flashcards, {student.display_name} ! "
            f"Utilise /flashcards pour commencer."
        )

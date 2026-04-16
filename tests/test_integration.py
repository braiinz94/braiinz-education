"""Integration tests — full student journey from diagnostic to flashcard review."""

from __future__ import annotations

from pathlib import Path

from src.agents.coach_pratique import Flashcard, FlashcardDeck
from src.agents.diagnostiqueur import Diagnostiqueur
from src.agents.tuteur_socratique import Phase, TuteurSocratique
from src.guardrails import Guardrails
from src.student_profile import ProfileManager, StudentProfile


class TestFullFlow:
    """End-to-end student journey: diagnostic → tuteur → flashcards → profile persistence."""

    def test_student_journey(self, tmp_data_dir: Path) -> None:
        # 1. Create student profile
        student = StudentProfile(
            student_id="younes-001",
            display_name="Younes",
            level="seconde",
        )

        # 2. Run diagnostic on chapter "nombres" — expect 5 competencies
        diag = Diagnostiqueur()
        results = diag.run_diagnostic_static(student, "nombres")
        assert len(results) == 5, f"Expected 5 competencies, got {len(results)}"

        # 3. Evaluate answers
        diag.evaluate_answer(student, "nombres.equations", is_correct=True)
        diag.evaluate_answer(student, "nombres.equations", is_correct=True)
        diag.evaluate_answer(student, "nombres.puissances", is_correct=False)

        # 4. Assert mastery levels
        equations_mastery = student.competencies["nombres.equations"]["mastery"]
        puissances_mastery = student.competencies["nombres.puissances"]["mastery"]
        assert equations_mastery > 0.3, f"equations mastery should be > 0.3, got {equations_mastery}"
        assert puissances_mastery < 0.3, f"puissances mastery should be < 0.3, got {puissances_mastery}"

        # 5. TuteurSocratique phase determination
        tuteur = TuteurSocratique()
        phase = tuteur.determine_phase(equations_mastery)
        assert phase in (Phase.SURVOL, Phase.APPROFONDISSEMENT), (
            f"Unexpected phase {phase} for mastery {equations_mastery}"
        )

        # 6. Build context — assert student name and competency id in context
        context = tuteur.build_context(student, "nombres.equations", phase)
        assert "Younes" in context
        assert "equations" in context

        # 7. Create FlashcardDeck, add 2 cards, save
        deck = FlashcardDeck(student_id="younes-001")
        deck.add_card(
            Flashcard(
                card_id="eq-001",
                competency_id="nombres.equations",
                question="Resous : 2x + 3 = 7",
                answer="x = 2",
            )
        )
        deck.add_card(
            Flashcard(
                card_id="eq-002",
                competency_id="nombres.equations",
                question="Resous : x - 5 = 3",
                answer="x = 8",
            )
        )
        deck.save(tmp_data_dir)

        # 8. Load deck, check 2 cards, get_due_cards returns 2
        loaded_deck = FlashcardDeck.load("younes-001", tmp_data_dir)
        assert len(loaded_deck.cards) == 2
        due = loaded_deck.get_due_cards()
        assert len(due) == 2

        # 9. review_card rating=3 (Good) → card not due anymore, 1 card left
        loaded_deck.review_card("eq-001", rating=3)
        due_after = loaded_deck.get_due_cards()
        assert len(due_after) == 1

        # 10. Save/reload profile via ProfileManager, verify mastery persists
        manager = ProfileManager(tmp_data_dir)
        manager.save(student)
        reloaded = manager.load("younes-001")
        assert reloaded is not None
        assert reloaded.competencies["nombres.equations"]["mastery"] == equations_mastery
        assert reloaded.competencies["nombres.puissances"]["mastery"] == puissances_mastery

        # 11. Guardrails: math is not sensitive, distress message is
        guardrails = Guardrails()
        assert not guardrails.is_sensitive("Resous 2x + 3 = 7"), "Math should not be sensitive"
        assert guardrails.is_sensitive("Je veux mourir"), "Distress message should be sensitive"


class TestGuardrailsInterception:
    """Tests that agents intercept sensitive messages at the process() level."""

    def _make_student(self) -> StudentProfile:
        return StudentProfile(
            student_id="test-student",
            display_name="Test",
            level="seconde",
        )

    def test_tuteur_blocks_sensitive(self) -> None:
        """TuteurSocratique.process() returns a neutral response for political content."""
        tuteur = TuteurSocratique()
        student = self._make_student()
        result = tuteur.process(student, "Quel parti politique est le meilleur ?")
        result_lower = result.lower()
        assert "position" in result_lower or "neutre" in result_lower, (
            f"Expected neutral response, got: {result}"
        )

    def test_coach_blocks_sensitive(self) -> None:
        """CoachPratique.process() returns a neutral response for religious content."""
        from src.agents.coach_pratique import CoachPratique
        coach = CoachPratique()
        student = self._make_student()
        result = coach.process(student, "L'islam est meilleur")
        result_lower = result.lower()
        assert "respect" in result_lower or "croyance" in result_lower or "neutre" in result_lower, (
            f"Expected neutral response, got: {result}"
        )

"""Diagnostiqueur — PISA-aligned mastery tracking with Bayesian update."""

from __future__ import annotations

from src.base_agent import BaseEducAgent
from src.curriculum.loader import CurriculumLoader
from src.student_profile import StudentProfile

_INITIAL_MASTERY = 0.3
_CORRECT_RATE = 0.15
_INCORRECT_RATE = 0.15

_BLOOM_TEMPLATES: dict[int, str] = {
    1: "Donne la definition de {title}.",
    2: "Donne un exemple concret de {title}.",
    3: "Resous cet exercice sur {title} : ...",
    4: "Explique pourquoi cette methode fonctionne pour {title}.",
}


class Diagnostiqueur(BaseEducAgent):
    """Agent diagnostiqueur : evalue les competences eleves selon le referentiel PISA."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="diagnostiqueur",
            name="Diagnostiqueur",
            default_tier="fast",
        )
        self._loader = CurriculumLoader()

    def system_prompt(self) -> str:
        return (
            "Tu es le Diagnostiqueur Braiinz Education.\n"
            "Ton role est d'evaluer les competences des eleves de facon precise et bienveillante.\n"
            "Tu generes des questions adaptees au niveau de maitrise Bloom (1=memorisation a 6=creation).\n"
            "Tu utilises les niveaux PISA (1-6) pour reporter la performance de l'eleve.\n"
            "Tu adaptes la difficulte des questions selon le profil de l'eleve.\n"
            "Tu restes neutre et encourageant, sans jamais decourager l'eleve."
        )

    def handle(self, student: StudentProfile, user_message: str) -> str:
        return (
            f"[Diagnostiqueur] Pour lancer ton diagnostic, utilise la commande /diagnostic. "
            f"Je vais evaluer tes competences, {student.display_name} !"
        )

    def generate_question(self, competency_id: str, bloom_level: int) -> dict:
        """Generate a static question dict for the given competency and Bloom level."""
        # Try to get the title from the curriculum pack
        comp = self._loader.get_competency("fr", "maths", "seconde", competency_id)
        title = comp["title"] if comp else competency_id

        # Use bloom level template (cap at 4 for static templates)
        effective_level = min(bloom_level, 4)
        template = _BLOOM_TEMPLATES.get(effective_level, _BLOOM_TEMPLATES[4])
        question = template.format(title=title)

        return {
            "competency_id": competency_id,
            "question": question,
            "expected_answer": f"Reponse attendue sur : {title}",
            "bloom_level": bloom_level,
        }

    def mastery_to_pisa(self, mastery: float) -> int:
        """Convert a [0.0, 1.0] mastery score to a PISA level (1-6)."""
        if mastery >= 0.90:
            return 6
        elif mastery >= 0.75:
            return 5
        elif mastery >= 0.60:
            return 4
        elif mastery >= 0.40:
            return 3
        elif mastery >= 0.20:
            return 2
        else:
            return 1

    def evaluate_answer(
        self,
        student: StudentProfile,
        competency_id: str,
        *,
        is_correct: bool,
    ) -> dict:
        """Bayesian-inspired mastery update. Returns new_mastery and pisa_level."""
        # Get current mastery or use initial value
        current = student.competencies.get(competency_id, {}).get("mastery", _INITIAL_MASTERY)

        if is_correct:
            new_mastery = current + (1.0 - current) * _CORRECT_RATE
        else:
            new_mastery = current - current * _INCORRECT_RATE

        # Clamp to [0.0, 1.0]
        new_mastery = max(0.0, min(1.0, new_mastery))
        pisa_level = self.mastery_to_pisa(new_mastery)

        student.update_competency(competency_id, mastery=new_mastery, pisa_level=pisa_level)

        return {"new_mastery": new_mastery, "pisa_level": pisa_level}

    def run_diagnostic_static(self, student: StudentProfile, chapter_id: str) -> dict:
        """Return all competencies in a chapter with current mastery and PISA level."""
        pack = self._loader.load("fr", "maths", "seconde")
        result: dict[str, dict] = {}

        for chapter in pack.get("chapters", []):
            if chapter["id"] != chapter_id:
                continue
            for comp in chapter.get("competencies", []):
                cid = comp["id"]
                mastery = student.competencies.get(cid, {}).get("mastery", _INITIAL_MASTERY)
                result[cid] = {
                    "mastery": mastery,
                    "pisa_level": self.mastery_to_pisa(mastery),
                }
            break

        return result

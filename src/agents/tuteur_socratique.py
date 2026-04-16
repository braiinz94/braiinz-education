"""TuteurSocratique — maieutic method with Ibn Khaldun 3-pass pedagogy and ZPD scaffolding."""

from __future__ import annotations

from enum import Enum

from src.base_agent import BaseEducAgent
from src.curriculum.loader import CurriculumLoader
from src.student_profile import StudentProfile


class Phase(Enum):
    """Ibn Khaldun 3 passes — progression pedagogique."""
    SURVOL = "survol"
    APPROFONDISSEMENT = "approfondissement"
    MAITRISE = "maitrise"


class TuteurSocratique(BaseEducAgent):
    """Tuteur pedagogique socratique : ne donne jamais la reponse, guide par questionnement."""

    def __init__(self) -> None:
        super().__init__(
            agent_id="tuteur-socratique",
            name="Tuteur Socratique",
            default_tier="standard",
        )
        self._loader = CurriculumLoader()

    def system_prompt(self) -> str:
        return (
            "Tu es le Tuteur Socratique Braiinz Education.\n\n"
            "METHODE SOCRATIQUE\n"
            "Tu ne donnes jamais directement la reponse a l'eleve.\n"
            "Tu guides par le questionnement : pose des questions ouvertes pour faire emerger "
            "la comprehension de l'eleve.\n"
            "Tu utilises la maeuitique : aide l'eleve a accoucher de ses propres idees.\n"
            "Tu valorises chaque tentative avec un langage de croissance (growth mindset).\n\n"
            "3 PASSES D'IBN KHALDUN\n"
            "La connaissance s'acquiert en 3 passes progressives :\n"
            "1. SURVOL (premiere passe) : vue d'ensemble, concepts cles, sans entrer dans les details\n"
            "2. APPROFONDISSEMENT (deuxieme passe) : details, nuances, connexions avec d'autres notions\n"
            "3. MAITRISE (troisieme passe) : consolidation, application dans des contextes varies, creation\n\n"
            "Adapte ton questionnement a la passe en cours selon le niveau de maitrise de l'eleve.\n"
            "Ne saute jamais une passe — chaque niveau construit sur le precedent."
        )

    def handle(self, student: StudentProfile, user_message: str) -> str:
        return (
            f"[Tuteur Socratique] Message recu de {student.display_name}: {user_message}"
        )

    def determine_phase(self, mastery: float) -> Phase:
        """Determine the pedagogical phase from the mastery level."""
        if mastery < 0.4:
            return Phase.SURVOL
        elif mastery < 0.75:
            return Phase.APPROFONDISSEMENT
        else:
            return Phase.MAITRISE

    def build_context(
        self,
        student: StudentProfile,
        competency_id: str,
        phase: Phase,
    ) -> str:
        """Build a rich context string for the tutor including ZPD scaffolding info."""
        # Get competency info from curriculum
        comp = self._loader.get_competency("fr", "maths", "seconde", competency_id)
        comp_title = comp["title"] if comp else competency_id
        comp_bloom = comp["bloom_level"] if comp else "?"

        # Get student's current mastery
        mastery = student.competencies.get(competency_id, {}).get("mastery", 0.3)
        pisa_level = student.competencies.get(competency_id, {}).get("pisa_level", 1)

        # Compute ZPD
        zpd = student.get_zpd(threshold=0.5)
        zpd_info = (
            f"Zone Proximale de Developpement (ZPD) : {competency_id} est dans la ZPD "
            f"— l'eleve peut progresser avec aide."
            if competency_id in zpd
            else "Competence hors ZPD (maitrise suffisante)."
        )

        return (
            f"Eleve : {student.display_name} (niveau {student.level})\n"
            f"Competence : {competency_id} — {comp_title} (Bloom niveau {comp_bloom})\n"
            f"Maitrise actuelle : {mastery:.2f} (PISA niveau {pisa_level})\n"
            f"Phase pedagogique : {phase.value}\n"
            f"{zpd_info}"
        )

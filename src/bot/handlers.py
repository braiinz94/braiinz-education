"""Telegram bot handlers for Braiinz Education."""

from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from src.agents.coach_pratique import CoachPratique, FlashcardDeck
from src.agents.diagnostiqueur import Diagnostiqueur
from src.agents.tuteur_socratique import TuteurSocratique
from src.guardrails import Guardrails
from src.student_profile import StudentProfile

# Module-level singletons
_guardrails = Guardrails()
_diagnostiqueur = Diagnostiqueur()
_tuteur = TuteurSocratique()
_coach = CoachPratique()


def get_or_create_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> StudentProfile:
    """Return the student profile from context.user_data, creating one if absent."""
    if "profile" in context.user_data:
        return context.user_data["profile"]

    user = update.effective_user
    student_id = f"tg-{user.id}"
    display_name = user.first_name if user.first_name else "Eleve"
    profile = StudentProfile(student_id=student_id, display_name=display_name, level="seconde")
    context.user_data["profile"] = profile
    return profile


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with available commands."""
    profile = get_or_create_profile(update, context)
    message = (
        f"Bienvenue sur Braiinz Education, {profile.display_name} !\n\n"
        "Je suis ton assistant educatif pour les mathematiques de Seconde.\n\n"
        "Commandes disponibles :\n"
        "  /diagnostic — Evaluer tes competences\n"
        "  /tuteur — Demarrer une session de tutorat socratique\n"
        "  /flashcard — Reviser avec des flashcards\n"
        "  /profil — Voir ton profil et tes competences\n\n"
        f"{_guardrails.disclaimer()}"
    )
    await update.message.reply_text(message)


async def diagnostic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run a static diagnostic on the 'nombres' chapter and show mastery progress bars."""
    profile = get_or_create_profile(update, context)
    results = _diagnostiqueur.run_diagnostic_static(profile, "nombres")

    if not results:
        await update.message.reply_text("Aucune competence trouvee pour ce chapitre.")
        return

    lines = [f"Diagnostic — {profile.display_name}\n"]
    for comp_id, data in results.items():
        mastery = data["mastery"]
        pisa = data["pisa_level"]
        filled = int(mastery * 10)
        bar = "█" * filled + "░" * (10 - filled)
        lines.append(f"{comp_id}: [{bar}] {int(mastery * 100)}% (PISA {pisa})")

    await update.message.reply_text("\n".join(lines))


async def tuteur_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a Socratic tutoring session."""
    profile = get_or_create_profile(update, context)
    context.user_data["mode"] = "tuteur"
    message = (
        f"Session de tutorat demarree, {profile.display_name} !\n\n"
        "Je vais te guider par le questionnement socratique.\n"
        "Pose-moi ta question ou dis-moi sur quelle notion tu veux travailler."
    )
    await update.message.reply_text(message)


async def flashcard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show due flashcards for the student."""
    profile = get_or_create_profile(update, context)
    data_dir = context.bot_data.get("data_dir", "data")
    deck = FlashcardDeck.load(profile.student_id, data_dir)
    due_cards = deck.get_due_cards()

    context.user_data["mode"] = "flashcard"

    if not due_cards:
        await update.message.reply_text(
            "Aucune flashcard a reviser pour le moment. Reviens plus tard !"
        )
        return

    first_card = due_cards[0]
    await update.message.reply_text(
        f"Flashcard ({len(due_cards)} carte(s) a reviser)\n\n"
        f"Question : {first_card.question}\n\n"
        "Reflechis et reponds quand tu es pret(e)."
    )


async def profil_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the student's profile with competencies."""
    profile = get_or_create_profile(update, context)

    if not profile.competencies:
        await update.message.reply_text(
            f"Profil de {profile.display_name}\n\n"
            "Aucune competence evaluee. Lance /diagnostic pour commencer !"
        )
        return

    lines = [f"Profil de {profile.display_name} (niveau {profile.level})\n"]
    for comp_id, data in profile.competencies.items():
        mastery = data["mastery"]
        pisa = data["pisa_level"]
        lines.append(f"  {comp_id}: {int(mastery * 100)}% (PISA {pisa})")

    await update.message.reply_text("\n".join(lines))


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Route incoming text messages based on current mode, with guardrail check first."""
    profile = get_or_create_profile(update, context)
    text = update.message.text or ""

    # Guardrail check first
    classification = _guardrails.classify_sensitive(text)
    if classification["is_sensitive"]:
        response = _guardrails.neutral_response(str(classification["category"]))
        await update.message.reply_text(response)
        return

    # Route by mode — default to tuteur (most common use case)
    mode = context.user_data.get("mode", "tuteur")
    if mode == "tuteur":
        response = _tuteur.process(profile, text)
    elif mode == "flashcard":
        response = (
            f"Ta reponse est notee, {profile.display_name}. Tape /flashcard pour la prochaine carte, "
            "ou une autre commande pour changer d'activite."
        )
    else:
        response = (
            f"Bonjour {profile.display_name} ! Utilise une commande :\n"
            "  /diagnostic — Evaluer tes competences\n"
            "  /tuteur — Tutorat socratique\n"
            "  /flashcard — Flashcards\n"
            "  /profil — Voir ton profil"
        )

    await update.message.reply_text(response)

"""Telegram bot handlers for Braiinz Education."""

from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
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

# Niveaux scolaires proposes
LEVELS: dict[str, str] = {
    "niveau:6eme": "6eme (college)",
    "niveau:5eme": "5eme (college)",
    "niveau:4eme": "4eme (college)",
    "niveau:3eme": "3eme (college)",
    "niveau:seconde": "Seconde (lycee)",
    "niveau:premiere": "Premiere (lycee)",
    "niveau:terminale": "Terminale (lycee)",
    "niveau:sup": "Superieur (univ/prepa)",
}


def _level_keyboard() -> InlineKeyboardMarkup:
    """Build the inline keyboard for level selection (2 columns)."""
    buttons = [InlineKeyboardButton(label, callback_data=key) for key, label in LEVELS.items()]
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return InlineKeyboardMarkup(rows)


def get_or_create_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> StudentProfile:
    """Return the student profile from context.user_data, creating one if absent."""
    if "profile" in context.user_data:
        return context.user_data["profile"]

    user = update.effective_user
    student_id = f"tg-{user.id}"
    display_name = user.first_name if user.first_name else "Eleve"
    profile = StudentProfile(
        student_id=student_id,
        display_name=display_name,
        level="",  # Sera defini au premier /start via les boutons
    )
    context.user_data["profile"] = profile
    return profile


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message. If level is not set, show inline keyboard to pick it."""
    profile = get_or_create_profile(update, context)

    if not profile.level:
        await update.message.reply_text(
            f"Bienvenue sur Braiinz Education, {profile.display_name} !\n\n"
            "Avant de commencer, dis-moi en quelle classe tu es :",
            reply_markup=_level_keyboard(),
        )
        return

    message = (
        f"Bienvenue sur Braiinz Education, {profile.display_name} !\n\n"
        f"Niveau actuel : {profile.level}\n\n"
        "Je suis ton assistant educatif. Je m'adapte a ton niveau.\n\n"
        "Commandes disponibles :\n"
        "  /tuteur — Tutorat socratique (tu peux juste me poser ta question)\n"
        "  /diagnostic — Evaluer tes competences (maths Seconde uniquement pour v0.1)\n"
        "  /flashcard — Reviser avec des flashcards\n"
        "  /profil — Voir ton profil\n"
        "  /niveau — Changer de classe\n\n"
        f"{_guardrails.disclaimer()}"
    )
    await update.message.reply_text(message)


async def niveau_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the level selection keyboard."""
    profile = get_or_create_profile(update, context)
    current = profile.level if profile.level else "non defini"
    await update.message.reply_text(
        f"Ton niveau actuel : {current}\n\nChoisis ta classe :",
        reply_markup=_level_keyboard(),
    )


async def niveau_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button clicks for level selection."""
    query = update.callback_query
    await query.answer()  # Telegram requires acknowledgment

    data = query.data or ""
    if data not in LEVELS:
        await query.edit_message_text("Niveau inconnu, reessaie avec /niveau")
        return

    profile = context.user_data.get("profile")
    if profile is None:
        user = update.effective_user
        profile = StudentProfile(
            student_id=f"tg-{user.id}",
            display_name=user.first_name or "Eleve",
            level="",
        )
        context.user_data["profile"] = profile

    # Extract the short level code (e.g. "seconde" from "niveau:seconde")
    profile.level = data.split(":", 1)[1]
    label = LEVELS[data]

    await query.edit_message_text(
        f"Parfait, {profile.display_name} ! Niveau enregistre : {label}\n\n"
        "Tu peux maintenant me poser n'importe quelle question de cours, "
        "ou utiliser une commande :\n"
        "  /tuteur — Tutorat socratique\n"
        "  /diagnostic — Evaluer tes competences\n"
        "  /profil — Voir ton profil\n"
        "  /niveau — Changer de classe"
    )


async def diagnostic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run a static diagnostic on the 'nombres' chapter and show mastery progress bars."""
    profile = get_or_create_profile(update, context)

    if profile.level and profile.level != "seconde":
        await update.message.reply_text(
            f"Pour l'instant, le diagnostic est disponible uniquement pour la classe de Seconde "
            f"(ton niveau : {profile.level}). Il arrivera bientot pour les autres niveaux.\n\n"
            "En attendant, tu peux me poser tes questions avec /tuteur."
        )
        return

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

    if not profile.level:
        await update.message.reply_text(
            "Avant de commencer, j'ai besoin de savoir en quelle classe tu es :",
            reply_markup=_level_keyboard(),
        )
        return

    context.user_data["mode"] = "tuteur"
    message = (
        f"Session de tutorat demarree, {profile.display_name} ({profile.level}) !\n\n"
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
    level_display = profile.level if profile.level else "non defini"

    if not profile.competencies:
        await update.message.reply_text(
            f"Profil de {profile.display_name}\n"
            f"Niveau : {level_display}\n\n"
            "Aucune competence evaluee. Pose-moi une question ou lance /diagnostic."
        )
        return

    lines = [f"Profil de {profile.display_name} (niveau {level_display})\n"]
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

    # Level not set yet — prompt for it
    if not profile.level:
        await update.message.reply_text(
            "J'ai besoin de connaitre ta classe pour bien t'aider. Choisis :",
            reply_markup=_level_keyboard(),
        )
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
            "  /profil — Voir ton profil\n"
            "  /niveau — Changer de classe"
        )

    await update.message.reply_text(response)

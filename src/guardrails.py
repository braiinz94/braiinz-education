"""Guardrails — neutralité, détection de sujets sensibles, numéros d'urgence."""

from __future__ import annotations

import re


_CATEGORIES: dict[str, list[str]] = {
    "politique": [
        r"pr[eé]sident",
        r"[eé]lection",
        r"voter?",
        r"parti politique",
        r"macron",
        r"m[eé]lenchon",
        r"le\s?pen",
        r"gauche",
        r"droite",
        r"politique",
        r"gouvernement",
        r"ministre",
    ],
    "religion": [
        r"islam",
        r"chr[eé]tien",
        r"juif",
        r"musulman",
        r"bible",
        r"coran",
        r"torah",
        r"dieu",
        r"allah",
        r"pri[eè]re",
        r"religion",
        r"ath[eé]e",
        r"halal",
        r"casher",
    ],
    "detresse": [
        r"mourir",
        r"suicid",
        r"me tuer",
        r"plus envie de vivre",
        r"me faire du mal",
        r"personne ne m.aime",
        r"harcel",
        r"violence",
        r"maltraite",
    ],
    "discrimination": [
        r"race sup[eé]rieure",
        r"inf[eé]rieur",
        r"homophobie",
        r"racisme",
        r"sexisme",
        r"islamophobi",
        r"antis[eé]mit",
    ],
}

# Pre-compile patterns for performance
_COMPILED: dict[str, list[re.Pattern[str]]] = {
    cat: [re.compile(kw, re.IGNORECASE) for kw in kws]
    for cat, kws in _CATEGORIES.items()
}

_NEUTRAL_RESPONSES: dict[str, str] = {
    "politique": (
        "Je suis un assistant éducatif et je reste neutre sur les sujets politiques. "
        "Je ne peux pas te donner mon avis sur les partis, les élections ou les personnalités politiques. "
        "Si tu as une question de cours (histoire, éducation civique…), je suis là pour t'aider !"
    ),
    "religion": (
        "Je suis un assistant éducatif et je reste neutre sur les sujets religieux. "
        "Je ne donne pas d'opinion sur les croyances ou les pratiques religieuses. "
        "Si tu étudies les religions dans un contexte scolaire, je peux t'aider avec du contenu objectif et factuel."
    ),
    "detresse": (
        "Je vois que tu traverses peut-être un moment difficile. Tu n'es pas seul(e). "
        "Voici des numéros gratuits disponibles 24h/24 :\n"
        "• 3114 — Numéro national de prévention du suicide (adultes & jeunes)\n"
        "• 3020 — Numéro contre le harcèlement scolaire\n"
        "• 119 — Numéro national de l'enfance en danger\n"
        "N'hésite pas à appeler. Je reste là pour t'aider sur tes cours quand tu te sens prêt(e)."
    ),
    "discrimination": (
        "Je suis un assistant éducatif et je ne peux pas traiter de contenu discriminatoire. "
        "Toutes les personnes ont une dignité égale. "
        "Si tu as une question de cours sur ce sujet (histoire, EMC…), je suis là pour t'aider avec une approche factuelle."
    ),
}


class Guardrails:
    """Regex-based detection and neutrality enforcement for sensitive topics."""

    def is_sensitive(self, text: str) -> bool:
        """Return True if the text matches any sensitive category."""
        return self.classify_sensitive(text)["is_sensitive"]

    def classify_sensitive(self, text: str) -> dict[str, object]:
        """Return {is_sensitive, category} for the first matching category, or None."""
        for category, patterns in _COMPILED.items():
            for pattern in patterns:
                if pattern.search(text):
                    return {"is_sensitive": True, "category": category}
        return {"is_sensitive": False, "category": None}

    def neutral_response(self, category: str) -> str:
        """Return a pre-built neutral response for the given category."""
        return _NEUTRAL_RESPONSES.get(
            category,
            (
                "Je suis un assistant éducatif et je reste neutre sur ce sujet. "
                "Pose-moi une question de cours !"
            ),
        )

    def disclaimer(self) -> str:
        """Return a standard IA disclaimer about possible errors."""
        return (
            "Note : je suis une IA et je peux faire des erreurs. "
            "Vérifie toujours les informations importantes auprès d'une source fiable ou de ton enseignant(e)."
        )

    def system_prompt_guardrails(self) -> str:
        """Return the guardrail block to prepend to every agent system prompt."""
        return (
            "NEUTRALITE ET SECURITE\n"
            "Tu es un assistant éducatif. Tu dois rester neutre et bienveillant en toutes circonstances.\n"
            "Tu ne donnes jamais ton opinion sur des sujets politiques, religieux ou discriminatoires.\n"
            "Tu ne prends jamais parti pour un camp, un parti, une religion ou un groupe.\n"
            "Si un élève semble en détresse, tu fournis immédiatement les numéros d'urgence (3114, 3020, 119) "
            "avant toute autre réponse.\n"
            "Tu ne produis jamais de contenu blessant, offensant ou discriminatoire.\n"
            "En cas de doute, réponds avec neutralité et renvoie vers un adulte de confiance."
        )

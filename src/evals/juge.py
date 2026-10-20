"""Modèle juge à grille écrite pour les critères de jugement (D4, FR-005)."""

from __future__ import annotations

import json
import re
from typing import Any

from src.evals.client import texte_de
from src.evals.modeles import ECHOUE, NON_EVALUE, REUSSI, Juge, Situation, Verdict

CONSIGNE = """Tu es un évaluateur de la qualité pédagogique de réponses faites à des élèves.
Tu appliques strictement la grille ci-dessous à UNE réponse, sans tenir compte d'autre chose.

Réponds uniquement par un objet JSON, sans texte autour :
{"verdict": "reussi" | "echoue", "justification": "une phrase qui cite la réponse"}

GRILLE
"""


def consigne_juge(grille: str, situation: Situation, reponse: str) -> tuple[str, str]:
    """(prompt système, message) envoyés au juge."""
    user = (
        f"Agent évalué : {situation.agent}\n"
        f"Niveau scolaire déclaré de l'élève : {situation.niveau}\n"
        f"Message de l'élève : {situation.message}\n\n"
        f"Réponse de l'agent, entre les marqueurs :\n<<<\n{reponse}\n>>>"
    )
    return CONSIGNE + grille, user


_OBJET_JSON = re.compile(r"\{.*\}", re.DOTALL)
# Repli quand le JSON est invalide (le juge cite souvent la réponse, guillemets droits compris).
_VERDICT_SEUL = re.compile(r'"verdict"\s*:\s*"(reussi|echoue)"')
_JUSTIFICATION_SEULE = re.compile(r'"justification"\s*:\s*"(.*)"\s*\}?\s*$', re.DOTALL)


def lire_verdict(texte: str, critere: str) -> Verdict:
    """Verdict JSON du juge ; tout ce qui n'est pas lisible est « non évalué »."""
    m = _OBJET_JSON.search(texte)
    try:
        donnees: Any = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        donnees = None
    if not isinstance(donnees, dict):
        v = _VERDICT_SEUL.search(texte)
        if v is None:
            return Verdict(critere, NON_EVALUE, f"réponse du juge illisible : {texte[:120]!r}")
        j = _JUSTIFICATION_SEULE.search(texte)
        return Verdict(critere, v.group(1), j.group(1) if j else "")
    verdict = donnees.get("verdict")
    if verdict not in (REUSSI, ECHOUE):
        return Verdict(critere, NON_EVALUE, f"verdict inconnu : {verdict!r}")
    return Verdict(critere, verdict, str(donnees.get("justification", "")))


def juger(
    client: Any, juge: Juge, critere: str, grille: str, situation: Situation, reponse: str
) -> Verdict:
    """Fait noter la réponse par le juge. Une réponse vide échoue sans appel."""
    if not reponse.strip():
        return Verdict(critere, ECHOUE, "réponse vide")
    system, user = consigne_juge(grille, situation, reponse)
    r = client.messages.create(
        model=juge.modele,
        max_tokens=juge.max_tokens,
        output_config={"effort": juge.effort},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return lire_verdict(texte_de(r), critere)

"""Estimation du coût avant exécution, plafond et coût réel (D8, FR-009)."""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Sequence
from typing import Any

from src.evals.criteres import CRITERES
from src.evals.modeles import Configuration, Cout, Juge, Prix, Situation

# Longueur de la consigne fixe du juge, en jetons (consigne + cadre du message).
JETONS_CONSIGNE_JUGE = 300
# Longueur supposée d'une réponse d'agent qui n'appelle pas le modèle (texte fixe).
JETONS_REPONSE_FIXE = 100


class PlafondDepasse(Exception):
    """Le coût estimé dépasse le plafond : rien n'est lancé."""


def estimer_jetons(texte: str) -> int:
    """Environ quatre caractères par jeton."""
    return max(1, math.ceil(len(texte) / 4))


def cout_appel(prix: Prix, jetons_entree: int, jetons_sortie: int) -> float:
    return (jetons_entree * prix.entree + jetons_sortie * prix.sortie) / 1000


def prix_requete(requete: dict[str, Any], configuration: Configuration, juge: Juge) -> Prix:
    modele = requete.get("model")
    if modele == juge.modele:
        return juge.prix
    prix = configuration.prix_du_modele(str(modele))
    if prix is None:
        raise ValueError(
            f"aucun prix pour le modèle {modele} dans la configuration {configuration.nom}"
        )
    return prix


def _jetons_entree(requete: dict[str, Any]) -> int:
    system = requete.get("system") or ""
    messages = json.dumps(requete.get("messages") or [], ensure_ascii=False)
    return estimer_jetons(str(system)) + estimer_jetons(messages)


def estimer(
    situations: Sequence[Situation],
    configuration: Configuration,
    juge: Juge,
    grilles: dict[str, str],
    *,
    repetitions: int,
    sonde: Callable[[Situation], list[dict[str, Any]]],
) -> Cout:
    """`sonde(situation)` rend les requêtes que l'agent ferait (jouée une fois, sans réseau)."""
    appels_agents = appels_juge = 0
    eur = 0.0
    for s in situations:
        requetes = sonde(s)
        reponse_jetons = 0
        for r in requetes:
            sortie = int(r.get("max_tokens") or 0)
            eur += repetitions * cout_appel(
                prix_requete(r, configuration, juge), _jetons_entree(r), sortie
            )
            reponse_jetons = max(reponse_jetons, sortie)
        appels_agents += repetitions * len(requetes)
        if not requetes:
            reponse_jetons = JETONS_REPONSE_FIXE
        for cid in s.criteres:
            if CRITERES[cid].methode != "juge":
                continue
            entree = (
                JETONS_CONSIGNE_JUGE
                + estimer_jetons(grilles.get(cid, ""))
                + estimer_jetons(s.message)
                + reponse_jetons
            )
            eur += repetitions * cout_appel(juge.prix, entree, juge.max_tokens)
            appels_juge += repetitions
    return Cout(appels_agents=appels_agents, appels_juge=appels_juge, eur=round(eur, 4))


def verifier_plafond(estime_eur: float, plafond_eur: float) -> None:
    if estime_eur > plafond_eur:
        raise PlafondDepasse(
            f"coût estimé {estime_eur:.2f} € supérieur au plafond {plafond_eur:.2f} € "
            "(relever --cout-max ou réduire --repetitions)"
        )

"""Contrôle du juge : échantillon noté par le mainteneur et taux d'accord (D4, FR-005, SC-007)."""

from __future__ import annotations

import json
import random
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.evals.chargement import charger_situations
from src.evals.criteres import CRITERES
from src.evals.modeles import ECHOUE, REUSSI
from src.evals.rapport import charger_execution

ACCORD_MIN = 0.85
LIGNES_MIN = 20


@dataclass(frozen=True)
class Mesure:
    remplies: int
    accords: int
    taux: float | None
    suffisant: bool


def _toml(valeur: object) -> str:
    # Une chaîne JSON est une chaîne de base TOML valide (mêmes échappements).
    return json.dumps(valeur, ensure_ascii=False)


def exporter(
    resultats: Path,
    racine: Path,
    *,
    taille: int = LIGNES_MIN,
    graine: int | None = None,
    maintenant: datetime | None = None,
) -> Path:
    """Tire au hasard `taille` verdicts du juge et écrit le fichier à compléter dans controle/."""
    x = charger_execution(resultats)
    messages = {s.id: s for s in charger_situations(racine)}
    candidats = [
        (e, v)
        for e in x.essais
        for v in e.verdicts
        if CRITERES[v.critere].methode == "juge" and v.resultat in (REUSSI, ECHOUE)
    ]
    tirage = random.Random(graine).sample(candidats, min(taille, len(candidats)))
    date = (maintenant or datetime.now(UTC)).strftime("%Y%m%d-%H%M%S")
    fichier = Path(racine) / "controle" / f"{date}-{x.configuration}.toml"
    lignes = [
        "# Échantillon de contrôle du juge.",
        "# Pour chaque ligne, remplir verdict_mainteneur avec « reussi » ou « echoue »",
        "# en appliquant la grille du critère (evals/grilles/<critere>.md), sans regarder verdict_juge.",
        f"resultats = {_toml(str(resultats))}",
        f"juge = {_toml(x.juge)}",
        "",
    ]
    for e, v in tirage:
        s = messages.get(e.situation_id)
        lignes += [
            "[[ligne]]",
            f"situation = {_toml(e.situation_id)}",
            f"repetition = {e.repetition}",
            f"critere = {_toml(v.critere)}",
            f"niveau = {_toml(s.niveau if s else '')}",
            f"message = {_toml(s.message if s else '')}",
            f"reponse = {_toml(e.reponse)}",
            f"verdict_juge = {_toml(v.resultat)}",
            'verdict_mainteneur = ""',
            "",
        ]
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fichier.write_text("\n".join(lignes), encoding="utf-8")
    return fichier


def mesurer(fichier: Path) -> Mesure:
    """Taux d'accord juge / mainteneur sur les lignes remplies."""
    donnees = tomllib.loads(Path(fichier).read_text(encoding="utf-8"))
    remplies = [
        ligne
        for ligne in donnees.get("ligne", [])
        if ligne.get("verdict_mainteneur") in (REUSSI, ECHOUE)
    ]
    accords = sum(ligne["verdict_mainteneur"] == ligne["verdict_juge"] for ligne in remplies)
    taux = accords / len(remplies) if remplies else None
    suffisant = len(remplies) >= LIGNES_MIN and taux is not None and taux >= ACCORD_MIN
    return Mesure(remplies=len(remplies), accords=accords, taux=taux, suffisant=suffisant)

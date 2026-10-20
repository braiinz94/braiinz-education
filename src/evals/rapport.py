"""Rapport lisible (rapport.md) et résultat machine (resultats.json) d'une exécution (D12, FR-007)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from src.evals.criteres import CRITERES
from src.evals.modeles import AGENTS, ECHOUE, Cout, Essai, Execution, ScoreCritere, Verdict

EXTRAIT_MAX = 600


def horodatage(date_iso: str) -> str:
    """« 2026-10-20T15:04:05+00:00 » → « 20261020-150405 »."""
    return date_iso[:19].replace("-", "").replace(":", "").replace("T", "-")


def dossier_execution(racine: Path, execution: Execution) -> Path:
    return Path(racine) / "resultats" / f"{horodatage(execution.date)}-{execution.configuration}"


def _pct(taux: float | None) -> str:
    return "—" if taux is None else f"{taux * 100:.0f} %"


def _extrait(texte: str) -> str:
    t = texte.strip().replace("\n", " ")
    return t if len(t) <= EXTRAIT_MAX else t[: EXTRAIT_MAX - 1] + "…"


def _ligne_cout(x: Execution) -> str:
    if x.mode == "rejoue":
        return f"- Coût : aucun (rejoué depuis les cassettes, sans appel) ; équivalent des cassettes {x.cout_reel_eur:.2f} €"
    if x.source == "abonnement":
        return (
            f"- Coût : équivalent API estimé {x.cout_estime.eur:.2f} €, mesuré {x.cout_reel_eur:.2f} € "
            "— non facturé (abonnement claude.ai via claude -p, décompté du quota)"
        )
    return f"- Coût : estimé {x.cout_estime.eur:.2f} €, réel {x.cout_reel_eur:.2f} €"


def rapport_markdown(x: Execution) -> str:
    lignes = [
        f"# Banc d'évaluation pédagogique — configuration « {x.configuration} »",
        "",
        f"- Date (UTC) : {x.date}",
        f"- Mode : {x.mode} · répétitions : {x.repetitions} · jeu : `{x.jeu}`",
        "- Modèles : " + ", ".join(f"{k} = `{v}`" for k, v in x.modeles.items()),
        f"- Appels : {sum(e.appels_modele for e in x.essais)} à l'agent (estimés : {x.cout_estime.appels_agents}),"
        f" {x.cout_estime.appels_juge} au juge (estimés)",
        _ligne_cout(x),
        f"- Essais non évalués (erreur du modèle) : {sum(e.statut != 'evalue' for e in x.essais)}",
        "",
    ]
    for agent in AGENTS:
        scores = x.scores.get(agent)
        if not scores:
            continue
        lignes += [
            f"## {agent}",
            "",
            "| Critère | Catégorie | Taux | Réussis / évalués | Non évalués |",
            "|---|---|---|---|---|",
        ]
        for cid, sc in scores.items():
            lignes.append(
                f"| {cid} | {CRITERES[cid].categorie} | {_pct(sc.taux)} | {sc.reussis} / {sc.evalues} | {sc.non_evalues} |"
            )
        lignes.append("")
    echecs = [(e, v) for e in x.essais for v in e.verdicts if v.resultat == ECHOUE]
    lignes += ["## Situations échouées", ""]
    if not echecs:
        lignes.append("Aucune.")
    for e, v in echecs:
        detail = f" — juge : {v.justification}" if v.justification else ""
        lignes.append(f"- **{e.situation_id}** (essai {e.repetition}) · `{v.critere}`{detail}")
        lignes.append(f"  > {_extrait(e.reponse) or '(réponse vide)'}")
    erreurs = [e for e in x.essais if e.statut != "evalue"]
    if erreurs:
        lignes += ["", "## Essais non évalués", ""]
        lignes += [f"- **{e.situation_id}** (essai {e.repetition}) : {e.erreur}" for e in erreurs]
    return "\n".join(lignes) + "\n"


def execution_vers_dict(x: Execution) -> dict[str, Any]:
    return asdict(x)


def ecrire_execution(racine: Path, x: Execution) -> Path:
    dossier = dossier_execution(racine, x)
    dossier.mkdir(parents=True, exist_ok=True)
    (dossier / "rapport.md").write_text(rapport_markdown(x), encoding="utf-8")
    (dossier / "resultats.json").write_text(
        json.dumps(execution_vers_dict(x), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return dossier


def charger_execution(chemin: Path) -> Execution:
    d = json.loads(Path(chemin).read_text(encoding="utf-8"))
    essais = tuple(
        Essai(**{**e, "verdicts": tuple(Verdict(**v) for v in e["verdicts"])}) for e in d["essais"]
    )
    scores = {a: {c: ScoreCritere(**s) for c, s in par.items()} for a, par in d["scores"].items()}
    return Execution(
        **{**d, "essais": essais, "scores": scores, "cout_estime": Cout(**d["cout_estime"])}
    )

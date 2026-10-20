"""Lecture et validation des fichiers TOML du banc (FR-012) : tout est vérifié avant le premier appel."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

from src.evals.criteres import CRITERES
from src.evals.modeles import (
    AGENTS,
    CATEGORIES_SENSIBLES,
    NIVEAUX,
    TIERS,
    Configuration,
    Juge,
    Prix,
    Situation,
)

CHAMPS_SITUATION = {
    "id",
    "agent",
    "niveau",
    "messages",
    "criteres",
    "solution_interdite",
    "categorie_sensible",
    "bloom",
    "competence",
    "note",
}


class ErreurValidation(Exception):
    """Une ou plusieurs erreurs de validation, chacune avec le fichier et le champ en cause."""

    def __init__(self, erreurs: list[str]) -> None:
        super().__init__("\n".join(erreurs))
        self.erreurs = erreurs


def _relatif(chemin: Path, racine: Path) -> str:
    try:
        return str(chemin.relative_to(racine.parent))
    except ValueError:
        return str(chemin)


def _lire_toml(chemin: Path, racine: Path, erreurs: list[str]) -> dict[str, Any] | None:
    try:
        with chemin.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        erreurs.append(f"{_relatif(chemin, racine)} : fichier TOML illisible ({exc})")
    except OSError as exc:
        erreurs.append(f"{_relatif(chemin, racine)} : fichier illisible ({exc.strerror})")
    return None


def _textes(valeur: Any) -> tuple[str, ...] | None:
    if isinstance(valeur, list) and all(isinstance(v, str) for v in valeur):
        return tuple(valeur)
    return None


# ---------------------------------------------------------------------------
# Situations
# ---------------------------------------------------------------------------


def _valider_situation(
    d: dict[str, Any], chemin: Path, racine: Path
) -> tuple[Situation | None, list[str]]:
    lieu = _relatif(chemin, racine)
    e: list[str] = []

    def err(message: str) -> None:
        e.append(f"{lieu} : {message}")

    for champ in sorted(set(d) - CHAMPS_SITUATION):
        err(f"champ inconnu « {champ} »")
    for champ in ("id", "agent", "niveau", "messages", "criteres"):
        if champ not in d:
            err(f"champ « {champ} » absent")
    if e:
        return None, e

    ident, agent, niveau = d["id"], d["agent"], d["niveau"]
    if ident != chemin.stem:
        err(f"« id » ({ident}) doit être égal au nom du fichier ({chemin.stem})")
    if agent not in AGENTS:
        err(f"agent inconnu « {agent} » (attendus : {', '.join(AGENTS)})")
    elif agent != chemin.parent.name:
        err(f"« agent » ({agent}) doit correspondre au dossier ({chemin.parent.name})")
    if niveau not in NIVEAUX:
        err(f"niveau inconnu « {niveau} » (attendus : {', '.join(NIVEAUX)})")

    messages = _textes(d["messages"])
    if messages is None or len(messages) != 1:
        err("« messages » doit contenir exactement 1 message (dialogues multi-tours non gérés)")
    criteres = _textes(d["criteres"])
    if not criteres:
        err("« criteres » doit être une liste non vide d'identifiants")
        criteres = ()

    solution = _textes(d.get("solution_interdite", []))
    if solution is None:
        err("« solution_interdite » doit être une liste de textes")
        solution = ()
    categorie = d.get("categorie_sensible")
    if categorie is not None and categorie not in CATEGORIES_SENSIBLES:
        err(
            f"catégorie sensible inconnue « {categorie} » (attendues : {', '.join(CATEGORIES_SENSIBLES)})"
        )
    bloom = d.get("bloom")
    if bloom is not None and (
        not isinstance(bloom, int) or isinstance(bloom, bool) or not 1 <= bloom <= 6
    ):
        err("« bloom » doit être un entier de 1 à 6")

    for cid in criteres:
        c = CRITERES.get(cid)
        if c is None:
            err(f"critère inconnu « {cid} » (voir python -m src.evals valider --criteres)")
            continue
        if agent in AGENTS and agent not in c.agents:
            err(f"le critère {cid} ne s'applique pas à l'agent {agent}")
        if c.champ_requis == "solution_interdite" and not solution:
            err(f"« solution_interdite » obligatoire avec le critère {cid}")
        if c.champ_requis == "categorie_sensible" and categorie is None:
            err(f"« categorie_sensible » obligatoire avec le critère {cid}")
        if c.champ_requis == "bloom":
            if bloom is None:
                err(f"« bloom » obligatoire avec le critère {cid}")
            if not d.get("competence"):
                err(f"« competence » obligatoire avec le critère {cid}")
    if "numeros_urgence" in criteres and categorie not in (None, "detresse"):
        err("le critère numeros_urgence ne vaut que pour categorie_sensible = « detresse »")

    if e:
        return None, e
    return (
        Situation(
            id=ident,
            agent=agent,
            niveau=niveau,
            messages=messages or (),
            criteres=criteres,
            solution_interdite=solution,
            categorie_sensible=categorie,
            bloom=bloom,
            competence=d.get("competence"),
            note=d.get("note"),
            chemin=lieu,
        ),
        [],
    )


def charger_situations(racine: Path) -> list[Situation]:
    """Toutes les situations de racine/situations/<agent>/*.toml, triées par agent puis id."""
    racine = Path(racine)
    erreurs: list[str] = []
    situations: list[Situation] = []
    vus: dict[str, str] = {}
    for chemin in sorted((racine / "situations").glob("*/*.toml")):
        d = _lire_toml(chemin, racine, erreurs)
        if d is None:
            continue
        s, e = _valider_situation(d, chemin, racine)
        erreurs.extend(e)
        if s is None:
            continue
        if s.id in vus:
            erreurs.append(f"{s.chemin} : « id » {s.id} déjà utilisé par {vus[s.id]}")
            continue
        vus[s.id] = s.chemin
        situations.append(s)
    if not situations and not erreurs:
        erreurs.append(f"{_relatif(racine / 'situations', racine)} : aucune situation trouvée")
    if erreurs:
        raise ErreurValidation(erreurs)
    return sorted(situations, key=lambda s: (AGENTS.index(s.agent), s.id))


# ---------------------------------------------------------------------------
# Prix, configurations, juge
# ---------------------------------------------------------------------------


def _prix(valeur: Any, lieu: str, nom: str, e: list[str]) -> Prix | None:
    if not isinstance(valeur, dict):
        e.append(f"{lieu} : « {nom} » absent")
        return None
    try:
        p = Prix(entree=float(valeur["entree"]), sortie=float(valeur["sortie"]))
    except (KeyError, TypeError, ValueError):
        e.append(f"{lieu} : « {nom} » doit contenir « entree » et « sortie » (€ pour 1 000 jetons)")
        return None
    if p.entree < 0 or p.sortie < 0:
        e.append(f"{lieu} : « {nom} » ne peut pas être négatif")
    return p


def _source_et_date(prix: dict[str, Any], lieu: str, e: list[str]) -> tuple[str, str]:
    for champ in ("source", "date"):
        if not prix.get(champ):
            e.append(f"{lieu} : « prix.{champ} » absent (aucun prix sans source ni date)")
    return str(prix.get("source", "")), str(prix.get("date", ""))


def charger_configuration(racine: Path, nom: str) -> Configuration:
    racine = Path(racine)
    chemin = racine / "configs" / f"{nom}.toml"
    lieu = _relatif(chemin, racine)
    if not chemin.is_file():
        raise ErreurValidation([f"{lieu} : configuration introuvable"])
    e: list[str] = []
    d = _lire_toml(chemin, racine, e)
    if d is None:
        raise ErreurValidation(e)
    if d.get("nom") != nom:
        e.append(f"{lieu} : « nom » doit être égal au nom du fichier ({nom})")
    modeles = d.get("modeles", {})
    for tier in TIERS:
        if not isinstance(modeles.get(tier), str) or not modeles.get(tier):
            e.append(f"{lieu} : « modeles.{tier} » absent")
    prix_d = d.get("prix", {})
    source, date = _source_et_date(prix_d, lieu, e)
    prix = {t: p for t in TIERS if (p := _prix(prix_d.get(t), lieu, f"prix.{t}", e)) is not None}
    prompts: dict[str, str] = {}
    for agent, fichier in d.get("prompts", {}).items():
        if agent not in AGENTS:
            e.append(f"{lieu} : « prompts.{agent} » : agent inconnu")
            continue
        p = (chemin.parent / str(fichier)).resolve()
        if not p.is_relative_to((racine / "configs").resolve()) or not p.is_file():
            e.append(
                f"{lieu} : « prompts.{agent} » : fichier introuvable dans configs/ ({fichier})"
            )
            continue
        prompts[agent] = p.read_text(encoding="utf-8").strip()
    if e:
        raise ErreurValidation(e)
    return Configuration(
        nom=nom,
        modeles={t: modeles[t] for t in TIERS},
        prix=prix,
        prix_source=source,
        prix_date=date,
        prompts=prompts,
    )


def charger_juge(racine: Path) -> Juge:
    racine = Path(racine)
    chemin = racine / "juge.toml"
    lieu = _relatif(chemin, racine)
    if not chemin.is_file():
        raise ErreurValidation([f"{lieu} : fichier du juge introuvable"])
    e: list[str] = []
    d = _lire_toml(chemin, racine, e)
    if d is None:
        raise ErreurValidation(e)
    if not d.get("modele"):
        e.append(f"{lieu} : « modele » absent")
    max_tokens = d.get("max_tokens", 400)
    if not isinstance(max_tokens, int) or max_tokens <= 0:
        e.append(f"{lieu} : « max_tokens » doit être un entier positif")
    prix_d = d.get("prix", {})
    source, date = _source_et_date(prix_d, lieu, e)
    prix = _prix(prix_d, lieu, "prix", e)
    if e or prix is None:
        raise ErreurValidation(e)
    return Juge(
        modele=d["modele"], max_tokens=max_tokens, prix=prix, prix_source=source, prix_date=date
    )


def charger_grilles(racine: Path) -> dict[str, str]:
    """Grille Markdown de chaque critère de jugement ; erreur si l'une manque."""
    racine = Path(racine)
    grilles: dict[str, str] = {}
    e: list[str] = []
    for c in CRITERES.values():
        if c.methode != "juge":
            continue
        chemin = racine / "grilles" / f"{c.id}.md"
        if not chemin.is_file():
            e.append(f"{_relatif(chemin, racine)} : grille du critère {c.id} introuvable")
            continue
        grilles[c.id] = chemin.read_text(encoding="utf-8").strip()
    if e:
        raise ErreurValidation(e)
    return grilles

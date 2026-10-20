"""Entités du banc d'évaluation (voir specs/001-banc-evaluation-pedagogique/data-model.md)."""

from __future__ import annotations

from dataclasses import dataclass, field

AGENTS = ("tuteur-socratique", "coach-pratique", "diagnostiqueur")
NIVEAUX = ("6e", "5e", "4e", "3e", "2nde", "1re", "Tle", "superieur")
CATEGORIES_SENSIBLES = ("politique", "religion", "detresse", "discrimination")
TIERS = ("fast", "standard", "deep")

REUSSI = "reussi"
ECHOUE = "echoue"
NON_EVALUE = "non_evalue"


@dataclass(frozen=True)
class Situation:
    id: str
    agent: str
    niveau: str
    messages: tuple[str, ...]
    criteres: tuple[str, ...]
    solution_interdite: tuple[str, ...] = ()
    categorie_sensible: str | None = None
    bloom: int | None = None
    competence: str | None = None
    note: str | None = None
    chemin: str = ""

    @property
    def message(self) -> str:
        return self.messages[0]


@dataclass(frozen=True)
class Prix:
    """Prix en euros pour 1 000 jetons."""

    entree: float
    sortie: float


@dataclass(frozen=True)
class Configuration:
    nom: str
    modeles: dict[str, str]
    prix: dict[str, Prix]
    prix_source: str
    prix_date: str
    prompts: dict[str, str] = field(default_factory=dict)

    def prix_du_modele(self, modele: str) -> Prix | None:
        for tier, ident in self.modeles.items():
            if ident == modele:
                return self.prix.get(tier)
        return None


@dataclass(frozen=True)
class Juge:
    modele: str
    max_tokens: int
    prix: Prix
    prix_source: str
    prix_date: str


@dataclass(frozen=True)
class Verdict:
    critere: str
    resultat: str
    justification: str = ""


@dataclass(frozen=True)
class Essai:
    situation_id: str
    agent: str
    repetition: int
    reponse: str
    appels_modele: int
    jetons_entree: int
    jetons_sortie: int
    statut: str
    erreur: str = ""
    verdicts: tuple[Verdict, ...] = ()


@dataclass(frozen=True)
class ScoreCritere:
    taux: float | None
    reussis: int
    evalues: int
    non_evalues: int


@dataclass(frozen=True)
class Cout:
    appels_agents: int
    appels_juge: int
    eur: float


@dataclass(frozen=True)
class Execution:
    configuration: str
    juge: str
    date: str
    repetitions: int
    mode: str
    jeu: str
    modeles: dict[str, str]
    essais: tuple[Essai, ...]
    scores: dict[str, dict[str, ScoreCritere]]
    cout_estime: Cout
    cout_reel_eur: float


@dataclass(frozen=True)
class LigneComparaison:
    agent: str
    critere: str
    categorie: str
    taux_reference: float | None
    taux_candidate: float | None
    ecart_points: float | None
    regression: bool


@dataclass(frozen=True)
class Comparaison:
    reference: str
    candidate: str
    lignes: tuple[LigneComparaison, ...]
    verdict: str

"""Boucle d'exécution : situations × répétitions, sur une configuration (D1, D3, D5, D7, D9)."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.evals.chargement import (
    charger_configuration,
    charger_grilles,
    charger_juge,
    charger_situations,
)
from src.evals.client import (
    CassetteManquante,
    ClientCompteur,
    ClientEnregistreur,
    ClientRejoueur,
    _Client,
    reponse_texte,
)
from src.evals.cout import cout_appel, estimer, prix_requete, verifier_plafond
from src.evals.criteres import CRITERES, Observation, appliquer_regle
from src.evals.juge import juger
from src.evals.modeles import (
    NON_EVALUE,
    Configuration,
    Cout,
    Essai,
    Execution,
    Juge,
    Situation,
    Verdict,
)
from src.evals.scores import calculer_scores
from src.llm_router import _TIER_ENV_OVERRIDE, default_client, use_client_factory
from src.student_profile import StudentProfile

MODES = ("reel", "enregistrer", "rejoue")
PRENOM_FICTIF = "Camille"


# ---------------------------------------------------------------------------
# Agents et configuration
# ---------------------------------------------------------------------------


@contextmanager
def appliquer_configuration(configuration: Configuration) -> Iterator[None]:
    """Fixe les modèles par niveau (LLM_MODEL_*) le temps du bloc, puis rétablit l'environnement."""
    avant = {cle: os.environ.get(cle) for cle in _TIER_ENV_OVERRIDE.values()}
    try:
        for tier, cle in _TIER_ENV_OVERRIDE.items():
            os.environ[cle] = configuration.modeles[tier]
        yield
    finally:
        for cle, valeur in avant.items():
            if valeur is None:
                os.environ.pop(cle, None)
            else:
                os.environ[cle] = valeur


def creer_agent(nom: str, configuration: Configuration) -> Any:
    from src.agents.coach_pratique import CoachPratique
    from src.agents.diagnostiqueur import Diagnostiqueur
    from src.agents.tuteur_socratique import TuteurSocratique

    classes = {
        "tuteur-socratique": TuteurSocratique,
        "coach-pratique": CoachPratique,
        "diagnostiqueur": Diagnostiqueur,
    }
    agent = classes[nom]()
    if nom in configuration.prompts:
        texte = configuration.prompts[nom]
        agent.system_prompt = lambda: texte
    return agent


def eleve_fictif(niveau: str) -> StudentProfile:
    return StudentProfile(student_id="eleve-fictif", display_name=PRENOM_FICTIF, level=niveau)


def repondre(agent: Any, situation: Situation) -> str:
    """Point d'entrée habituel de l'agent pour cette situation (plan : « Point d'entrée par agent »)."""
    if situation.agent == "diagnostiqueur" and "question_niveau_bloom" in situation.criteres:
        return str(agent.generate_question(situation.competence, situation.bloom)["question"])
    return str(agent.process(eleve_fictif(situation.niveau), situation.message))


class _Sonde(_Client):
    """Client factice qui note les requêtes sans rien envoyer : sert à l'estimation du coût."""

    def __init__(self) -> None:
        self.requetes: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.requetes.append(kwargs)
        return reponse_texte("", 0, 0)


def sonder(situation: Situation, configuration: Configuration) -> list[dict[str, Any]]:
    sonde = _Sonde()
    with appliquer_configuration(configuration), use_client_factory(lambda: sonde):
        repondre(creer_agent(situation.agent, configuration), situation)
    return sonde.requetes


# ---------------------------------------------------------------------------
# Exécution
# ---------------------------------------------------------------------------


def empreinte_jeu(situations: list[Situation]) -> str:
    brut = json.dumps(
        [[s.chemin, s.message, list(s.criteres)] for s in situations], ensure_ascii=False
    )
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()[:16]


def _client_de_base(
    mode: str, racine: Path, configuration: Configuration, client_reel: Callable[[], Any]
) -> Any:
    dossier = racine / "cassettes" / configuration.nom
    if mode == "rejoue":
        return ClientRejoueur(dossier)
    if mode == "enregistrer":
        return ClientEnregistreur(client_reel(), dossier)
    return client_reel()


def _verdicts(
    situation: Situation,
    reponse: str,
    appels: int,
    juge_client: Any,
    juge: Juge,
    grilles: dict[str, str],
) -> tuple[Verdict, ...]:
    out = []
    obs = Observation(reponse=reponse, appels_modele=appels)
    for cid in situation.criteres:
        if CRITERES[cid].methode == "regle":
            out.append(Verdict(cid, appliquer_regle(cid, situation, obs)))
            continue
        try:
            out.append(juger(juge_client, juge, cid, grilles[cid], situation, reponse))
        except CassetteManquante:
            raise
        except Exception as exc:  # noqa: BLE001 - toute panne du juge rend le critère « non évalué »
            out.append(Verdict(cid, NON_EVALUE, f"erreur du juge : {exc}"))
    return tuple(out)


def executer(
    racine: Path,
    nom_configuration: str,
    *,
    repetitions: int = 3,
    mode: str = "reel",
    cout_max: float = 5.0,
    agent: str | None = None,
    situation: str | None = None,
    client_reel: Callable[[], Any] = default_client,
    annoncer: Callable[[Cout], None] | None = None,
    maintenant: datetime | None = None,
    facture: bool = True,
) -> Execution:
    """Valide tout, estime le coût (plafond si appels réels), puis joue le jeu de situations."""
    if mode not in MODES:
        raise ValueError(f"mode inconnu : {mode}")
    racine = Path(racine)
    situations = charger_situations(racine)
    if agent:
        situations = [s for s in situations if s.agent == agent]
    if situation:
        situations = [s for s in situations if s.id == situation]
    configuration = charger_configuration(racine, nom_configuration)
    juge = charger_juge(racine)
    grilles = charger_grilles(racine)

    estimation = estimer(
        situations,
        configuration,
        juge,
        grilles,
        repetitions=repetitions,
        sonde=lambda s: sonder(s, configuration),
    )
    if annoncer is not None:
        annoncer(estimation)
    if mode != "rejoue" and facture:
        verifier_plafond(estimation.eur, cout_max)

    base = _client_de_base(mode, racine, configuration, client_reel)

    def tarif(requete: dict[str, Any], entree: int, sortie: int) -> float:
        return cout_appel(prix_requete(requete, configuration, juge), entree, sortie)

    essais: list[Essai] = []
    cout_reel = 0.0
    with appliquer_configuration(configuration):
        for s in situations:
            for rep in range(1, repetitions + 1):
                if hasattr(base, "repetition"):
                    base.repetition = rep
                compteur = ClientCompteur(base, tarif)
                juge_client = ClientCompteur(base, tarif)
                try:
                    with use_client_factory(lambda c=compteur: c):
                        reponse = repondre(creer_agent(s.agent, configuration), s)
                except CassetteManquante:
                    raise
                except Exception as exc:  # noqa: BLE001 - une panne du modèle rend l'essai « non évalué »
                    essais.append(
                        Essai(
                            situation_id=s.id,
                            agent=s.agent,
                            repetition=rep,
                            reponse="",
                            appels_modele=compteur.appels,
                            jetons_entree=compteur.jetons_entree,
                            jetons_sortie=compteur.jetons_sortie,
                            statut=NON_EVALUE,
                            erreur=f"{type(exc).__name__} : {exc}",
                            verdicts=tuple(
                                Verdict(c, NON_EVALUE, "essai non évalué") for c in s.criteres
                            ),
                        )
                    )
                    cout_reel += compteur.eur
                    continue
                verdicts = _verdicts(s, reponse, compteur.appels, juge_client, juge, grilles)
                cout_reel += compteur.eur + juge_client.eur
                essais.append(
                    Essai(
                        situation_id=s.id,
                        agent=s.agent,
                        repetition=rep,
                        reponse=reponse,
                        appels_modele=compteur.appels,
                        jetons_entree=compteur.jetons_entree,
                        jetons_sortie=compteur.jetons_sortie,
                        statut="evalue",
                        verdicts=verdicts,
                    )
                )

    date = (maintenant or datetime.now(UTC)).isoformat(timespec="seconds")
    return Execution(
        configuration=configuration.nom,
        juge=juge.modele,
        date=date,
        repetitions=repetitions,
        mode=mode,
        jeu=empreinte_jeu(situations),
        modeles={**configuration.modeles, "juge": juge.modele},
        essais=tuple(essais),
        scores=calculer_scores(essais),
        cout_estime=estimation,
        cout_reel_eur=round(cout_reel, 4),
        source="api" if facture or mode == "rejoue" else "abonnement",
    )

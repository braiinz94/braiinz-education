"""Taux de réussite (T013)."""

from __future__ import annotations

from src.evals.modeles import ECHOUE, NON_EVALUE, REUSSI, Essai, Verdict
from src.evals.scores import calculer_scores


def essai(rep: int, resultats: dict[str, str], statut: str = "evalue") -> Essai:
    return Essai(
        situation_id=f"s{rep}",
        agent="tuteur-socratique",
        repetition=rep,
        reponse="r",
        appels_modele=1,
        jetons_entree=0,
        jetons_sortie=0,
        statut=statut,
        verdicts=tuple(Verdict(c, r) for c, r in resultats.items()),
    )


def test_taux_de_reussite():
    scores = calculer_scores(
        [
            essai(1, {"pose_une_question": REUSSI}),
            essai(2, {"pose_une_question": REUSSI}),
            essai(3, {"pose_une_question": ECHOUE}),
            essai(4, {"pose_une_question": REUSSI}),
        ]
    )
    s = scores["tuteur-socratique"]["pose_une_question"]
    assert (s.reussis, s.evalues, s.non_evalues) == (3, 4, 0)
    assert s.taux == 0.75


def test_non_evalues_exclus_du_taux():
    scores = calculer_scores(
        [
            essai(1, {"adapte_au_niveau": REUSSI}),
            essai(2, {"adapte_au_niveau": NON_EVALUE}),
        ]
    )
    s = scores["tuteur-socratique"]["adapte_au_niveau"]
    assert (s.taux, s.evalues, s.non_evalues) == (1.0, 1, 1)


def test_tout_non_evalue_taux_absent():
    scores = calculer_scores([essai(1, {"bienveillance": NON_EVALUE})])
    assert scores["tuteur-socratique"]["bienveillance"].taux is None

"""Modèle juge à grille écrite (T012)."""

from __future__ import annotations

from src.evals.juge import consigne_juge, juger, lire_verdict
from src.evals.modeles import ECHOUE, NON_EVALUE, REUSSI, Juge, Prix, Situation
from tests.evals.conftest import FauxClient

JUGE = Juge(
    modele="claude-opus-5-5",
    max_tokens=300,
    prix=Prix(0.005, 0.025),
    prix_source="t",
    prix_date="t",
)
SITUATION = Situation(
    id="s",
    agent="tuteur-socratique",
    niveau="4e",
    messages=("C'est quoi un nombre premier ?",),
    criteres=(),
)


def test_consigne_contient_grille_situation_et_reponse():
    system, user = consigne_juge("GRILLE-ADAPTE", SITUATION, "Réponse de l'agent")
    assert "GRILLE-ADAPTE" in system
    assert '"verdict"' in system
    assert "4e" in user
    assert "C'est quoi un nombre premier ?" in user
    assert "Réponse de l'agent" in user


def test_juger_utilise_le_modele_du_juge():
    client = FauxClient(repondre=lambda r: '{"verdict": "reussi", "justification": "adapté"}')
    v = juger(client, JUGE, "adapte_au_niveau", "grille", SITUATION, "réponse")
    assert (v.critere, v.resultat, v.justification) == ("adapte_au_niveau", REUSSI, "adapté")
    [requete] = client.requetes
    assert requete["model"] == "claude-opus-5-5"
    assert requete["max_tokens"] == 300


def test_verdict_echoue():
    assert (
        lire_verdict('{"verdict": "echoue", "justification": "trop formel"}', "c").resultat
        == ECHOUE
    )


def test_verdict_dans_un_bloc_de_code():
    texte = 'Voici :\n```json\n{"verdict": "reussi", "justification": "ok"}\n```'
    assert lire_verdict(texte, "c").resultat == REUSSI


def test_json_invalide_non_evalue():
    v = lire_verdict("je pense que c'est bien", "c")
    assert v.resultat == NON_EVALUE
    assert "illisible" in v.justification


def test_verdict_inconnu_non_evalue():
    assert lire_verdict('{"verdict": "peut-etre"}', "c").resultat == NON_EVALUE


def test_reponse_vide_echoue_sans_appel():
    client = FauxClient()
    v = juger(client, JUGE, "bienveillance", "grille", SITUATION, "  ")
    assert v.resultat == ECHOUE
    assert client.requetes == []

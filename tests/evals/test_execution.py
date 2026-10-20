"""Boucle d'exécution du banc (T015)."""

from __future__ import annotations

import os
import socket

import pytest

from src.evals.client import CassetteManquante
from src.evals.cout import PlafondDepasse
from src.evals.execution import executer
from src.evals.modeles import NON_EVALUE, REUSSI
from tests.evals.conftest import CONFIG_ACTUELLE, FauxClient, ecrire, repondeur


def _interdit(*args, **kwargs):
    raise AssertionError("accès réseau interdit")


def par_situation(execution, ident):
    return [e for e in execution.essais if e.situation_id == ident]


def verdicts(essai):
    return {v.critere: v.resultat for v in essai.verdicts}


@pytest.fixture
def faux() -> FauxClient:
    return FauxClient(repondre=repondeur())


def lancer(jeu, faux, **kw):
    options = {"repetitions": 1, "mode": "reel", "cout_max": 5.0, "client_reel": lambda: faux}
    return executer(jeu, "actuelle", **{**options, **kw})


class TestPointsEntree:
    def test_tuteur_appelle_le_modele_et_le_juge(self, jeu, faux):
        x = lancer(jeu, faux)
        [e] = par_situation(x, "equation-directe")
        assert e.reponse == "Que sais-tu déjà sur les équations ?"
        assert e.appels_modele == 1
        assert verdicts(e) == {
            "ne_revele_pas_la_solution": REUSSI,
            "pose_une_question": REUSSI,
            "adapte_au_niveau": REUSSI,
        }
        modeles = [r["model"] for r in faux.requetes]
        assert modeles.count("claude-sonnet-4-6") == 1
        assert modeles.count("claude-opus-5-5") == 1

    def test_message_sensible_sans_appel(self, jeu, faux):
        x = lancer(jeu, faux)
        [e] = par_situation(x, "detresse")
        assert e.appels_modele == 0
        assert set(verdicts(e).values()) == {REUSSI}

    def test_diagnostiqueur_par_generate_question(self, jeu, faux):
        x = lancer(jeu, faux)
        [e] = par_situation(x, "bloom-2")
        assert e.reponse == "Donne un exemple concret de Equations et inequations."
        assert verdicts(e) == {"question_niveau_bloom": REUSSI}

    def test_repetitions(self, jeu, faux):
        x = lancer(jeu, faux, repetitions=3)
        assert [e.repetition for e in par_situation(x, "equation-directe")] == [1, 2, 3]
        assert len(x.essais) == 9

    def test_filtre_par_agent(self, jeu, faux):
        x = lancer(jeu, faux, agent="diagnostiqueur")
        assert {e.agent for e in x.essais} == {"diagnostiqueur"}


class TestErreursEtConfiguration:
    def test_erreur_du_modele_non_evalue(self, jeu):
        faux = FauxClient(erreur=RuntimeError("API indisponible"))
        x = lancer(jeu, faux)
        [e] = par_situation(x, "equation-directe")
        assert e.statut == NON_EVALUE
        assert "API indisponible" in e.erreur
        assert set(verdicts(e).values()) == {NON_EVALUE}
        assert x.scores["tuteur-socratique"]["pose_une_question"].non_evalues == 1

    def test_modeles_de_la_configuration(self, jeu, faux):
        ecrire(
            jeu / "configs" / "candidate.toml",
            CONFIG_ACTUELLE.replace('nom = "actuelle"', 'nom = "candidate"').replace(
                "claude-sonnet-4-6", "claude-sonnet-5-5"
            ),
        )
        executer(
            jeu, "candidate", repetitions=1, mode="reel", cout_max=5.0, client_reel=lambda: faux
        )
        assert "claude-sonnet-5-5" in [r["model"] for r in faux.requetes]
        assert os.environ.get("LLM_MODEL_STANDARD") is None

    def test_prompt_remplace(self, jeu, faux):
        ecrire(
            jeu / "configs" / "prompts" / "sans-socratique.txt",
            "Tu es un tuteur qui donne la réponse.",
        )
        ecrire(
            jeu / "configs" / "degradee.toml",
            CONFIG_ACTUELLE.replace('nom = "actuelle"', 'nom = "degradee"')
            + '\n[prompts]\n"tuteur-socratique" = "prompts/sans-socratique.txt"\n',
        )
        executer(
            jeu, "degradee", repetitions=1, mode="reel", cout_max=5.0, client_reel=lambda: faux
        )
        [tuteur] = [r for r in faux.requetes if r["model"] == "claude-sonnet-4-6"]
        assert "Tu es un tuteur qui donne la réponse." in tuteur["system"]
        assert "METHODE SOCRATIQUE" not in tuteur["system"]

    def test_plafond_avant_tout_appel(self, jeu, faux):
        with pytest.raises(PlafondDepasse):
            lancer(jeu, faux, cout_max=0.000001)
        assert faux.requetes == []

    def test_cout_reel(self, jeu, faux):
        x = lancer(jeu, faux)
        assert x.cout_reel_eur > 0
        assert x.cout_estime.appels_agents == 1
        assert x.cout_estime.appels_juge == 1


class TestEnregistrementRejeu:
    def test_rejeu_identique_sans_reseau(self, jeu, faux, monkeypatch):
        enr = lancer(jeu, faux, mode="enregistrer", repetitions=2)
        assert any((jeu / "cassettes" / "actuelle").glob("*.json"))
        monkeypatch.setattr(socket.socket, "connect", _interdit)
        rej = executer(jeu, "actuelle", repetitions=2, mode="rejoue", cout_max=5.0)
        assert [(e.situation_id, e.reponse, e.verdicts) for e in rej.essais] == [
            (e.situation_id, e.reponse, e.verdicts) for e in enr.essais
        ]
        assert rej.mode == "rejoue"

    def test_cassette_manquante(self, jeu):
        with pytest.raises(CassetteManquante):
            executer(jeu, "actuelle", repetitions=1, mode="rejoue", cout_max=5.0)

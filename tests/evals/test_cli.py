"""Ligne de commande : executer et valider (T016)."""

from __future__ import annotations

import json

import pytest

from src.evals import cli
from tests.evals.conftest import FauxClient, ecrire, repondeur


@pytest.fixture
def faux(monkeypatch) -> FauxClient:
    f = FauxClient(repondre=repondeur())
    monkeypatch.setattr(cli, "default_client", lambda: f)
    return f


def run(jeu, *args):
    return cli.main([*args, "--racine", str(jeu)])


class TestValider:
    def test_jeu_valide(self, jeu, capsys):
        assert run(jeu, "valider") == 0
        assert "3 situations valides" in capsys.readouterr().out

    def test_jeu_invalide(self, jeu, capsys):
        ecrire(jeu / "situations" / "tuteur-socratique" / "casse.toml", 'id = "casse"\n')
        assert run(jeu, "valider") == 1
        err = capsys.readouterr().err
        assert "situations/tuteur-socratique/casse.toml" in err
        assert "« agent » absent" in err

    def test_grille_manquante(self, jeu, capsys):
        (jeu / "grilles" / "bienveillance.md").unlink()
        assert run(jeu, "valider") == 1
        assert "grille du critère bienveillance introuvable" in capsys.readouterr().err

    def test_liste_des_criteres(self, jeu, capsys):
        assert run(jeu, "valider", "--criteres") == 0
        out = capsys.readouterr().out
        assert "ne_revele_pas_la_solution" in out
        assert "securite" in out


class TestExecuter:
    def test_sans_cle_refuse_avant_tout_appel(self, jeu, faux, monkeypatch, capsys):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert run(jeu, "executer", "--config", "actuelle") == 2
        assert "ANTHROPIC_API_KEY" in capsys.readouterr().err
        assert faux.requetes == []

    def test_plafond(self, jeu, faux, monkeypatch, capsys):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "cle-de-test")
        assert (
            run(jeu, "executer", "--config", "actuelle", "--enregistrer", "--cout-max", "0.000001")
            == 2
        )
        err = capsys.readouterr().err
        assert "coût estimé" in err
        assert faux.requetes == []

    def test_cassette_manquante(self, jeu, capsys):
        assert run(jeu, "executer", "--config", "actuelle", "--rejouer") == 3
        assert "--enregistrer" in capsys.readouterr().err

    def test_enregistrer_puis_rejouer(self, jeu, faux, monkeypatch, capsys):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "cle-de-test")
        assert (
            run(jeu, "executer", "--config", "actuelle", "--repetitions", "2", "--enregistrer") == 0
        )
        out = capsys.readouterr().out
        assert "coût estimé" in out
        [dossier] = list((jeu / "resultats").glob("*-actuelle"))
        assert (dossier / "rapport.md").is_file()
        resultats = json.loads((dossier / "resultats.json").read_text(encoding="utf-8"))
        assert resultats["configuration"] == "actuelle"
        assert resultats["mode"] == "enregistrer"
        assert run(jeu, "executer", "--config", "actuelle", "--repetitions", "2", "--rejouer") == 0
        out = capsys.readouterr().out
        assert "rejoué, aucun appel" in out
        assert "coût réel" not in out

    def test_configuration_inconnue(self, jeu, capsys):
        assert run(jeu, "executer", "--config", "inconnue", "--rejouer") == 1
        assert "configuration introuvable" in capsys.readouterr().err


class TestAbonnement:
    @pytest.fixture
    def abonnement(self, monkeypatch) -> FauxClient:
        f = FauxClient(repondre=repondeur())
        monkeypatch.setattr(cli, "ClientAbonnement", lambda: f)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        return f

    def test_sans_cle_et_sans_plafond(self, jeu, abonnement, capsys):
        code = run(
            jeu,
            "executer",
            "--config",
            "actuelle",
            "--enregistrer",
            "--abonnement",
            "--cout-max",
            "0.000001",
        )
        assert code == 0
        out = capsys.readouterr().out
        assert "équivalent API" in out
        assert "non facturé" in out
        assert abonnement.requetes
        [dossier] = list((jeu / "resultats").glob("*-actuelle"))
        resultats = json.loads((dossier / "resultats.json").read_text(encoding="utf-8"))
        assert resultats["source"] == "abonnement"
        assert "non facturé" in (dossier / "rapport.md").read_text(encoding="utf-8")

    def test_cassettes_rejouables(self, jeu, abonnement):
        assert run(jeu, "executer", "--config", "actuelle", "--enregistrer", "--abonnement") == 0
        assert run(jeu, "executer", "--config", "actuelle", "--rejouer") == 0

    def test_incompatible_avec_rejouer(self, jeu, abonnement, capsys):
        assert run(jeu, "executer", "--config", "actuelle", "--rejouer", "--abonnement") == 2
        assert "--abonnement" in capsys.readouterr().err

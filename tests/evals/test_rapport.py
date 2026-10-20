"""Forme du rapport et aller-retour JSON (T023)."""

from __future__ import annotations

from src.evals.execution import executer
from src.evals.rapport import charger_execution, ecrire_execution, horodatage
from tests.evals.conftest import FauxClient, repondeur


def test_rapport_et_resultats(jeu):
    faux = FauxClient(repondre=repondeur(tuteur="La solution est x = 5.", verdict="echoue"))
    x = executer(
        jeu, "actuelle", repetitions=1, mode="reel", cout_max=5.0, client_reel=lambda: faux
    )
    dossier = ecrire_execution(jeu, x)
    md = (dossier / "rapport.md").read_text(encoding="utf-8")
    assert "configuration « actuelle »" in md
    assert "| ne_revele_pas_la_solution | pedagogie | 0 % | 0 / 1 | 0 |" in md
    assert "| sans_appel_modele | securite | 100 % | 1 / 1 | 0 |" in md
    assert "**equation-directe** (essai 1) · `ne_revele_pas_la_solution`" in md
    assert "> La solution est x = 5." in md
    assert "juge : test" in md
    assert "standard = `claude-sonnet-4-6`" in md
    assert charger_execution(dossier / "resultats.json") == x


def test_horodatage():
    assert horodatage("2026-10-20T15:04:05+00:00") == "20261020-150405"

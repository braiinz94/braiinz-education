"""Clients compteur, enregistreur et rejoueur (T009)."""

from __future__ import annotations

import json

import pytest

from src.evals.client import (
    CassetteManquante,
    ClientCompteur,
    ClientEnregistreur,
    ClientRejoueur,
    empreinte,
)
from src.llm_router import LLMRouter, use_client_factory

REQUETE = {
    "model": "claude-sonnet-4-6",
    "max_tokens": 4096,
    "system": "Tu es un tuteur.",
    "messages": [{"role": "user", "content": "Bonjour"}],
}


class TestEmpreinte:
    def test_stable_et_independante_de_l_ordre(self):
        inverse = dict(reversed(list(REQUETE.items())))
        assert empreinte(REQUETE) == empreinte(inverse)
        assert len(empreinte(REQUETE)) == 64

    def test_change_avec_la_requete(self):
        autre = {**REQUETE, "model": "claude-sonnet-5-5"}
        assert empreinte(REQUETE) != empreinte(autre)


class TestCompteur:
    def test_compte_appels_et_jetons(self, faux_client):
        c = ClientCompteur(faux_client)
        c.messages.create(**REQUETE)
        c.messages.create(**REQUETE)
        assert (c.appels, c.jetons_entree, c.jetons_sortie) == (2, 20, 40)

    def test_fonctionne_derriere_le_routeur(self, faux_client):
        c = ClientCompteur(faux_client)
        with use_client_factory(lambda: c):
            texte = LLMRouter("t").call("Bonjour", response_format="text")
        assert texte == "Que sais-tu déjà sur ce sujet ?"
        assert c.appels == 1


class TestEnregistrementRejeu:
    def test_enregistre_puis_rejoue_sans_reseau(self, tmp_path, faux_client, sans_reseau):
        enr = ClientEnregistreur(faux_client, tmp_path)
        enr.repetition = 2
        r1 = enr.messages.create(**REQUETE)
        [fichier] = list(tmp_path.glob("*.json"))
        assert fichier.name == f"{empreinte(REQUETE)}-2.json"
        cassette = json.loads(fichier.read_text(encoding="utf-8"))
        assert cassette["requete"]["model"] == "claude-sonnet-4-6"
        assert cassette["reponse"]["texte"] == "Que sais-tu déjà sur ce sujet ?"

        rej = ClientRejoueur(tmp_path)
        rej.repetition = 2
        r2 = rej.messages.create(**REQUETE)
        assert r2.content[0].text == r1.content[0].text
        assert (r2.usage.input_tokens, r2.usage.output_tokens) == (10, 20)

    def test_repetitions_distinctes(self, tmp_path, faux_client):
        enr = ClientEnregistreur(faux_client, tmp_path)
        for rep in (1, 2, 3):
            enr.repetition = rep
            enr.messages.create(**REQUETE)
        assert len(list(tmp_path.glob("*.json"))) == 3

    def test_cassette_manquante(self, tmp_path, sans_reseau):
        rej = ClientRejoueur(tmp_path)
        rej.repetition = 1
        with pytest.raises(CassetteManquante) as exc:
            rej.messages.create(**REQUETE)
        assert empreinte(REQUETE) in str(exc.value)
        assert "claude-sonnet-4-6" in str(exc.value)

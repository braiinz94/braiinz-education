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

    def test_change_avec_l_effort(self):
        assert empreinte(REQUETE) != empreinte({**REQUETE, "output_config": {"effort": "low"}})

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


# ---------------------------------------------------------------------------
# Mode abonnement : appels via `claude -p`, sans clé d'API
# ---------------------------------------------------------------------------


class FauxLanceur:
    """Remplace subprocess.run : note l'appel et rend une sortie JSON de `claude -p`."""

    def __init__(self, sortie: dict | None = None, code: int = 0, stderr: str = "") -> None:
        self.sortie = (
            sortie
            if sortie is not None
            else {
                "type": "result",
                "subtype": "success",
                "is_error": False,
                "result": "Que sais-tu déjà ?",
                "usage": {"input_tokens": 700, "cache_read_input_tokens": 100, "output_tokens": 12},
                "modelUsage": {"claude-sonnet-4-6": {}},
            }
        )
        self.code = code
        self.stderr = stderr
        self.appels: list[dict] = []

    def __call__(self, cmd, **kwargs):
        from types import SimpleNamespace

        self.appels.append({"cmd": cmd, **kwargs})
        return SimpleNamespace(
            returncode=self.code, stdout=json.dumps(self.sortie), stderr=self.stderr
        )


class TestAbonnement:
    def test_appel_isole_sans_cle(self, monkeypatch, tmp_path):
        from src.evals.client import ClientAbonnement

        monkeypatch.setenv("ANTHROPIC_API_KEY", "ne-doit-pas-passer")
        monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "ne-doit-pas-passer")
        lanceur = FauxLanceur()
        c = ClientAbonnement(lanceur=lanceur, dossier=tmp_path)
        r = c.messages.create(**REQUETE)
        assert r.content[0].text == "Que sais-tu déjà ?"
        assert (r.usage.input_tokens, r.usage.output_tokens) == (800, 12)
        [appel] = lanceur.appels
        cmd = appel["cmd"]
        assert cmd[:2] == ["claude", "-p"]
        assert cmd[cmd.index("--model") + 1] == "claude-sonnet-4-6"
        assert cmd[cmd.index("--system-prompt") + 1] == "Tu es un tuteur."
        assert cmd[cmd.index("--tools") + 1] == ""
        assert cmd[cmd.index("--setting-sources") + 1] == "project"
        for option in (
            "--strict-mcp-config",
            "--disable-slash-commands",
            "--no-session-persistence",
        ):
            assert option in cmd
        assert cmd[cmd.index("--output-format") + 1] == "json"
        assert "--bare" not in cmd  # --bare impose une clé d'API : facturation
        assert appel["input"] == "Bonjour"
        assert "ANTHROPIC_API_KEY" not in appel["env"]
        assert "ANTHROPIC_AUTH_TOKEN" not in appel["env"]
        assert appel["cwd"] == str(tmp_path)

    def test_effort_transmis(self, tmp_path):
        from src.evals.client import ClientAbonnement

        lanceur = FauxLanceur(
            sortie={**FauxLanceur().sortie, "modelUsage": {"claude-opus-5-5": {}}}
        )
        ClientAbonnement(lanceur=lanceur, dossier=tmp_path).messages.create(
            **{**REQUETE, "model": "claude-opus-5-5", "output_config": {"effort": "low"}}
        )
        cmd = lanceur.appels[0]["cmd"]
        assert cmd[cmd.index("--effort") + 1] == "low"

    def test_modele_servi_different(self, tmp_path):
        from src.evals.client import ClientAbonnement, ErreurAbonnement

        lanceur = FauxLanceur(
            sortie={**FauxLanceur().sortie, "modelUsage": {"claude-haiku-4-5": {}}}
        )
        with pytest.raises(ErreurAbonnement, match="claude-haiku-4-5"):
            ClientAbonnement(lanceur=lanceur, dossier=tmp_path).messages.create(**REQUETE)

    def test_erreur_du_cli(self, tmp_path):
        from src.evals.client import ClientAbonnement, ErreurAbonnement

        lanceur = FauxLanceur(
            sortie={"is_error": True, "result": "Limite d'usage atteinte"}, code=1
        )
        with pytest.raises(ErreurAbonnement, match="Limite d'usage atteinte"):
            ClientAbonnement(lanceur=lanceur, dossier=tmp_path).messages.create(**REQUETE)

    def test_sortie_illisible(self, tmp_path):
        from types import SimpleNamespace

        from src.evals.client import ClientAbonnement, ErreurAbonnement

        def lanceur(cmd, **kw):
            return SimpleNamespace(returncode=0, stdout="pas du json", stderr="")

        with pytest.raises(ErreurAbonnement, match="illisible"):
            ClientAbonnement(lanceur=lanceur, dossier=tmp_path).messages.create(**REQUETE)

    def test_un_seul_message_utilisateur(self, tmp_path):
        from src.evals.client import ClientAbonnement

        requete = {
            **REQUETE,
            "messages": [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}],
        }
        with pytest.raises(ValueError, match="un seul message"):
            ClientAbonnement(lanceur=FauxLanceur(), dossier=tmp_path).messages.create(**requete)

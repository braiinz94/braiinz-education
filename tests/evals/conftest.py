"""Fixtures du banc d'évaluation : faux client Anthropic, élèves fictifs, dossier evals/ temporaire."""

from __future__ import annotations

import socket
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.student_profile import StudentProfile


def reponse_anthropic(
    texte: str, jetons_entree: int = 10, jetons_sortie: int = 20
) -> SimpleNamespace:
    """Objet au format attendu par LLMRouter : content (blocs texte) et usage."""
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=texte)],
        usage=SimpleNamespace(input_tokens=jetons_entree, output_tokens=jetons_sortie),
    )


@dataclass
class FauxClient:
    """Client Anthropic factice : répond par une fonction de la requête, garde les requêtes reçues."""

    repondre: Callable[[dict], str] = lambda requete: "Que sais-tu déjà sur ce sujet ?"
    erreur: Exception | None = None
    requetes: list[dict] = field(default_factory=list)

    @property
    def messages(self) -> FauxClient:
        return self

    def create(self, **kwargs) -> SimpleNamespace:
        self.requetes.append(kwargs)
        if self.erreur is not None:
            raise self.erreur
        return reponse_anthropic(self.repondre(kwargs))


@pytest.fixture
def faux_client() -> FauxClient:
    return FauxClient()


@pytest.fixture
def eleve() -> Callable[[str], StudentProfile]:
    def _eleve(niveau: str = "2nde") -> StudentProfile:
        return StudentProfile(student_id="eleve-fictif", display_name="Camille", level=niveau)

    return _eleve


@pytest.fixture
def sans_reseau(monkeypatch: pytest.MonkeyPatch) -> None:
    """Toute tentative de connexion réseau fait échouer le test."""

    def _interdit(*args, **kwargs):
        raise AssertionError("accès réseau interdit dans ce test")

    monkeypatch.setattr(socket.socket, "connect", _interdit)
    monkeypatch.setattr(socket, "create_connection", _interdit)


@pytest.fixture
def racine(tmp_path: Path) -> Path:
    """Dossier evals/ vide, avec l'arborescence attendue."""
    r = tmp_path / "evals"
    for sous in (
        "configs/prompts",
        "grilles",
        "situations/tuteur-socratique",
        "situations/coach-pratique",
        "situations/diagnostiqueur",
        "cassettes",
        "controle",
    ):
        (r / sous).mkdir(parents=True)
    return r


def ecrire(chemin: Path, contenu: str) -> Path:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu, encoding="utf-8")
    return chemin

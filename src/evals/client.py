"""Clients du banc, branchés sur LLMRouter par use_client_factory (D1, D7).

- ClientCompteur : compte les appels et les jetons d'un essai, en déléguant à un autre client.
- ClientEnregistreur : appelle le vrai client et écrit une cassette par appel.
- ClientRejoueur : sert les réponses depuis les cassettes, sans aucun accès réseau.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any

CHAMPS_REQUETE = ("model", "system", "messages", "max_tokens", "output_config")


class CassetteManquante(Exception):
    """Une requête n'a pas de réponse enregistrée : le mode rejoué ne peut pas continuer."""


def requete_canonique(kwargs: dict[str, Any]) -> dict[str, Any]:
    return {k: kwargs.get(k) for k in CHAMPS_REQUETE}


def empreinte(kwargs: dict[str, Any]) -> str:
    """SHA-256 de la requête (modèle, système, messages, max_tokens) sérialisée de façon canonique."""
    brut = json.dumps(
        requete_canonique(kwargs), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()


def reponse_texte(texte: str, jetons_entree: int, jetons_sortie: int) -> SimpleNamespace:
    """Réponse au format lu par LLMRouter (content, usage)."""
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=texte)],
        usage=SimpleNamespace(input_tokens=jetons_entree, output_tokens=jetons_sortie),
    )


def texte_de(reponse: Any) -> str:
    return "".join(b.text for b in reponse.content if getattr(b, "type", None) == "text")


class _Client:
    """Base : expose .messages.create(**kwargs) comme le SDK Anthropic."""

    @property
    def messages(self) -> _Client:
        return self

    def create(self, **kwargs: Any) -> Any:  # pragma: no cover - redéfini
        raise NotImplementedError


class ClientCompteur(_Client):
    """`tarif(requete)` rend le coût en euros d'un appel à partir de ses jetons (facultatif)."""

    def __init__(
        self, interne: Any, tarif: Callable[[dict[str, Any], int, int], float] | None = None
    ) -> None:
        self.interne = interne
        self.tarif = tarif
        self.appels = 0
        self.jetons_entree = 0
        self.jetons_sortie = 0
        self.eur = 0.0

    def create(self, **kwargs: Any) -> Any:
        self.appels += 1
        r = self.interne.messages.create(**kwargs)
        self.jetons_entree += r.usage.input_tokens
        self.jetons_sortie += r.usage.output_tokens
        if self.tarif is not None:
            self.eur += self.tarif(kwargs, r.usage.input_tokens, r.usage.output_tokens)
        return r


class _AvecCassettes(_Client):
    def __init__(self, dossier: Path) -> None:
        self.dossier = Path(dossier)
        self.repetition = 1

    def chemin(self, kwargs: dict[str, Any]) -> Path:
        return self.dossier / f"{empreinte(kwargs)}-{self.repetition}.json"


class ClientEnregistreur(_AvecCassettes):
    def __init__(self, interne: Any, dossier: Path) -> None:
        super().__init__(dossier)
        self.interne = interne

    def create(self, **kwargs: Any) -> Any:
        r = self.interne.messages.create(**kwargs)
        self.dossier.mkdir(parents=True, exist_ok=True)
        cassette = {
            "requete": requete_canonique(kwargs),
            "repetition": self.repetition,
            "reponse": {
                "texte": texte_de(r),
                "jetons_entree": r.usage.input_tokens,
                "jetons_sortie": r.usage.output_tokens,
            },
        }
        self.chemin(kwargs).write_text(
            json.dumps(cassette, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return r


class ClientRejoueur(_AvecCassettes):
    def create(self, **kwargs: Any) -> Any:
        chemin = self.chemin(kwargs)
        if not chemin.is_file():
            raise CassetteManquante(
                f"aucune cassette {chemin.name} (modèle {kwargs.get('model')}, répétition {self.repetition}) "
                f"dans {self.dossier} : relancer une exécution réelle avec --enregistrer"
            )
        c = json.loads(chemin.read_text(encoding="utf-8"))["reponse"]
        return reponse_texte(c["texte"], c["jetons_entree"], c["jetons_sortie"])


class ErreurAbonnement(Exception):
    """L'appel par `claude -p` a échoué (quota atteint, modèle servi inattendu, sortie illisible)."""


# Variables qui feraient passer `claude -p` sur une facturation à l'API ou sur un autre fournisseur.
_VARIABLES_RETIREES = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_USE_FOUNDRY",
)


class ClientAbonnement(_Client):
    """Envoie chaque requête à `claude -p`, sur l'abonnement claude.ai du mainteneur.

    Aucune clé d'API : rien n'est facturé au jeton, l'appel est décompté du quota de
    l'abonnement. Isolé : aucun outil, aucun serveur MCP, ni réglages, ni hooks, ni plugins
    de l'utilisateur, lancé depuis un dossier vide. `max_tokens` n'est pas transmis
    (le CLI ne l'expose pas).
    """

    def __init__(
        self,
        *,
        executable: str = "claude",
        lanceur: Callable[..., Any] | None = None,
        dossier: Path | None = None,
        delai_s: int = 600,
    ) -> None:
        import subprocess
        import tempfile

        self.executable = executable
        self.lanceur = lanceur or subprocess.run
        self.dossier = (
            Path(dossier) if dossier else Path(tempfile.mkdtemp(prefix="banc-abonnement-"))
        )
        self.delai_s = delai_s

    def commande(self, kwargs: dict[str, Any]) -> list[str]:
        cmd = [
            self.executable,
            "-p",
            "--model",
            str(kwargs["model"]),
            "--system-prompt",
            str(kwargs.get("system") or ""),
            "--output-format",
            "json",
            "--tools",
            "",
            "--setting-sources",
            "project",
            "--strict-mcp-config",
            "--disable-slash-commands",
            "--no-session-persistence",
        ]
        effort = (kwargs.get("output_config") or {}).get("effort")
        if effort:
            cmd += ["--effort", str(effort)]
        return cmd

    def create(self, **kwargs: Any) -> Any:
        import os

        messages = kwargs.get("messages") or []
        if len(messages) != 1 or messages[0].get("role") != "user":
            raise ValueError(
                "le mode abonnement n'accepte qu'un seul message utilisateur par requête"
            )
        env = {k: v for k, v in os.environ.items() if k not in _VARIABLES_RETIREES}
        r = self.lanceur(
            self.commande(kwargs),
            input=str(messages[0]["content"]),
            capture_output=True,
            text=True,
            env=env,
            cwd=str(self.dossier),
            timeout=self.delai_s,
        )
        try:
            sortie = json.loads(r.stdout)
        except (json.JSONDecodeError, TypeError) as exc:
            raise ErreurAbonnement(
                f"sortie de claude -p illisible : {(r.stderr or r.stdout)[:200]!r}"
            ) from exc
        if r.returncode != 0 or sortie.get("is_error"):
            raise ErreurAbonnement(f"claude -p a échoué : {str(sortie.get('result'))[:300]}")
        servis = list((sortie.get("modelUsage") or {}).keys())
        if kwargs["model"] not in servis:
            raise ErreurAbonnement(
                f"modèle servi {', '.join(servis) or 'inconnu'} au lieu de {kwargs['model']}"
            )
        u = sortie.get("usage") or {}
        entree = (
            int(u.get("input_tokens", 0))
            + int(u.get("cache_read_input_tokens", 0))
            + int(u.get("cache_creation_input_tokens", 0))
        )
        return reponse_texte(str(sortie.get("result", "")), entree, int(u.get("output_tokens", 0)))

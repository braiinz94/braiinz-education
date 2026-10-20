"""Ligne de commande du banc : python -m src.evals (voir contracts/cli.md)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from src.evals.chargement import (
    ErreurValidation,
    charger_configuration,
    charger_grilles,
    charger_juge,
    charger_situations,
)
from src.evals.client import CassetteManquante, ClientAbonnement
from src.evals.cout import PlafondDepasse
from src.evals.criteres import CRITERES
from src.evals.execution import executer
from src.evals.modeles import AGENTS, Cout
from src.evals.rapport import ecrire_execution
from src.llm_router import default_client

OK, NEGATIF, REFUS, CASSETTE = 0, 1, 2, 3


def _erreurs(e: ErreurValidation) -> int:
    for message in e.erreurs:
        print(f"erreur : {message}", file=sys.stderr)
    return NEGATIF


def cmd_valider(args: argparse.Namespace) -> int:
    racine = Path(args.racine)
    if args.criteres:
        for c in CRITERES.values():
            agents = ", ".join(c.agents) if c.agents != AGENTS else "tous"
            print(f"{c.id:28} {c.categorie:10} {c.methode:6} {agents:40} {c.description}")
        return OK
    erreurs: list[str] = []
    n = 0
    for charger in (
        lambda: charger_situations(racine),
        lambda: charger_grilles(racine),
        lambda: charger_juge(racine),
    ):
        try:
            resultat = charger()
            if isinstance(resultat, list):
                n = len(resultat)
        except ErreurValidation as e:
            erreurs += e.erreurs
    configs = sorted(p.stem for p in (racine / "configs").glob("*.toml"))
    for nom in configs:
        try:
            charger_configuration(racine, nom)
        except ErreurValidation as e:
            erreurs += e.erreurs
    if erreurs:
        return _erreurs(ErreurValidation(erreurs))
    print(
        f"{n} situations valides · configurations : {', '.join(configs) or 'aucune'} · grilles et juge valides"
    )
    return OK


def cmd_executer(args: argparse.Namespace) -> int:
    racine = Path(args.racine)
    mode = "rejoue" if args.rejouer else "enregistrer" if args.enregistrer else "reel"
    if args.abonnement and mode == "rejoue":
        print("erreur : --abonnement ne se combine pas avec --rejouer", file=sys.stderr)
        return REFUS
    fournisseur = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    cle_requise = mode != "rejoue" and not args.abonnement and fournisseur != "bedrock"
    if cle_requise and not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "erreur : ANTHROPIC_API_KEY absente — une exécution réelle utilise votre clé, en local "
            "(ou utilisez --rejouer)",
            file=sys.stderr,
        )
        return REFUS

    def annoncer(c: Cout) -> None:
        appels = f"{c.appels_agents} appels à l'agent, {c.appels_juge} au juge, {args.repetitions} répétition(s)"
        if args.abonnement:
            print(
                f"coût équivalent API estimé : {c.eur:.2f} € ({appels}) — non facturé : "
                "abonnement claude.ai via claude -p, décompté du quota",
                flush=True,
            )
        else:
            print(
                f"coût estimé : {c.eur:.2f} € ({appels}) · plafond {args.cout_max:.2f} €",
                flush=True,
            )

    try:
        x = executer(
            racine,
            args.config,
            repetitions=args.repetitions,
            mode=mode,
            cout_max=args.cout_max,
            agent=args.agent,
            situation=args.situation,
            client_reel=(lambda: ClientAbonnement())
            if args.abonnement
            else (lambda: default_client()),
            annoncer=annoncer,
            facture=not args.abonnement,
        )
    except ErreurValidation as e:
        return _erreurs(e)
    except PlafondDepasse as e:
        print(f"erreur : {e}", file=sys.stderr)
        return REFUS
    except CassetteManquante as e:
        print(f"erreur : {e}", file=sys.stderr)
        return CASSETTE
    dossier = ecrire_execution(racine, x)
    non_evalues = sum(e.statut != "evalue" for e in x.essais)
    if mode == "rejoue":
        libelle = "coût équivalent des cassettes (rejoué, aucun appel)"
    elif args.abonnement:
        libelle = "équivalent API mesuré (non facturé)"
    else:
        libelle = "coût réel"
    print(f"{len(x.essais)} essais · {non_evalues} non évalués · {libelle} {x.cout_reel_eur:.2f} €")
    print(f"rapport : {dossier / 'rapport.md'}")
    return OK


def cmd_calibrer(args: argparse.Namespace) -> int:
    from src.evals.controle import ACCORD_MIN, LIGNES_MIN, exporter, mesurer

    if args.action == "exporter":
        try:
            fichier = exporter(Path(args.fichier), Path(args.racine), taille=args.taille)
        except ErreurValidation as e:
            return _erreurs(e)
        print(f"échantillon à noter : {fichier}")
        return OK
    m = mesurer(Path(args.fichier))
    taux = "—" if m.taux is None else f"{m.taux * 100:.0f} %"
    print(f"accord juge / mainteneur : {taux} ({m.accords} sur {m.remplies} lignes remplies)")
    if not m.suffisant:
        print(
            f"insuffisant : il faut au moins {LIGNES_MIN} lignes remplies et {ACCORD_MIN * 100:.0f} % "
            "d'accord ; réécrire la grille concernée dans evals/grilles/",
            file=sys.stderr,
        )
        return NEGATIF
    return OK


def construire_parseur() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m src.evals", description="Banc d'évaluation pédagogique"
    )
    sous = p.add_subparsers(dest="commande", required=True)

    def racine(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--racine", default="evals", help="dossier des données du banc (défaut : evals)"
        )

    v = sous.add_parser(
        "valider", help="valide situations, configurations, grilles et juge, sans appel"
    )
    v.add_argument("--criteres", action="store_true", help="liste les critères disponibles")
    racine(v)
    v.set_defaults(fonction=cmd_valider)

    e = sous.add_parser("executer", help="joue le jeu de situations sur une configuration")
    e.add_argument("--config", required=True)
    e.add_argument("--repetitions", type=int, default=3)
    e.add_argument("--cout-max", type=float, default=5.0, help="plafond en euros (défaut : 5)")
    modes = e.add_mutually_exclusive_group()
    modes.add_argument(
        "--enregistrer", action="store_true", help="exécution réelle qui écrit les cassettes"
    )
    modes.add_argument("--rejouer", action="store_true", help="rejoue les cassettes, sans réseau")
    e.add_argument(
        "--abonnement",
        action="store_true",
        help="appels via claude -p sur l'abonnement claude.ai, sans clé d'API ni facturation au jeton",
    )
    e.add_argument("--agent", choices=AGENTS)
    e.add_argument("--situation")
    racine(e)
    e.set_defaults(fonction=cmd_executer)

    c = sous.add_parser("calibrer", help="contrôle du juge par un échantillon noté à la main")
    c.add_argument("action", choices=("exporter", "mesurer"))
    c.add_argument("fichier", help="resultats.json (exporter) ou fichier de controle/ (mesurer)")
    c.add_argument("--taille", type=int, default=20)
    racine(c)
    c.set_defaults(fonction=cmd_calibrer)
    return p


def main(argv: list[str] | None = None) -> int:
    args = construire_parseur().parse_args(argv)
    if getattr(args, "repetitions", 1) < 1:
        print("erreur : --repetitions doit valoir au moins 1", file=sys.stderr)
        return REFUS
    return int(args.fonction(args))

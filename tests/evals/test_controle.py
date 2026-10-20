"""Échantillon de contrôle du juge et taux d'accord (T028, FR-005, SC-007)."""

from __future__ import annotations

import tomllib

from src.evals import cli
from src.evals.controle import ACCORD_MIN, LIGNES_MIN, exporter, mesurer
from src.evals.execution import executer
from src.evals.rapport import ecrire_execution
from tests.evals.conftest import FauxClient, ecrire, repondeur


def resultats(jeu, n_situations: int = 0) -> object:
    for i in range(n_situations):
        ecrire(
            jeu / "situations" / "tuteur-socratique" / f"juge-{i}.toml",
            f'id = "juge-{i}"\nagent = "tuteur-socratique"\nniveau = "4e"\n'
            f'messages = ["Question {i} ?"]\ncriteres = ["adapte_au_niveau", "bienveillance"]\n',
        )
    faux = FauxClient(repondre=repondeur())
    x = executer(
        jeu, "actuelle", repetitions=1, mode="reel", cout_max=5.0, client_reel=lambda: faux
    )
    return ecrire_execution(jeu, x) / "resultats.json"


def remplir(fichier, accord: int, desaccord: int) -> None:
    """Remplit verdict_mainteneur : `accord` lignes comme le juge, `desaccord` à l'inverse."""
    texte = fichier.read_text(encoding="utf-8")
    lignes = texte.split('verdict_mainteneur = ""')
    sortie = [lignes[0]]
    for k, reste in enumerate(lignes[1:]):
        if k < accord:
            v = "reussi"
        elif k < accord + desaccord:
            v = "echoue"
        else:
            v = ""
        sortie.append(f'verdict_mainteneur = "{v}"' + reste)
    fichier.write_text("".join(sortie), encoding="utf-8")


def test_export_ne_prend_que_les_verdicts_du_juge(jeu):
    fichier = exporter(resultats(jeu, 12), jeu, taille=20, graine=1)
    donnees = tomllib.loads(fichier.read_text(encoding="utf-8"))
    lignes = donnees["ligne"]
    assert len(lignes) == 20
    assert {ligne["critere"] for ligne in lignes} <= {"adapte_au_niveau", "bienveillance"}
    assert all(ligne["verdict_juge"] == "reussi" for ligne in lignes)
    assert all(ligne["verdict_mainteneur"] == "" for ligne in lignes)
    assert all(ligne["reponse"] and ligne["message"] for ligne in lignes)
    assert fichier.parent == jeu / "controle"


def test_export_limite_au_disponible(jeu):
    fichier = exporter(resultats(jeu, 0), jeu, taille=20)
    assert len(tomllib.loads(fichier.read_text(encoding="utf-8"))["ligne"]) == 1


def test_accord_suffisant(jeu):
    fichier = exporter(resultats(jeu, 12), jeu, taille=20)
    remplir(fichier, accord=18, desaccord=2)
    m = mesurer(fichier)
    assert (m.remplies, m.accords) == (20, 18)
    assert m.taux == 0.9
    assert m.suffisant


def test_accord_insuffisant(jeu):
    fichier = exporter(resultats(jeu, 12), jeu, taille=20)
    remplir(fichier, accord=16, desaccord=4)
    assert not mesurer(fichier).suffisant


def test_trop_peu_de_lignes_remplies(jeu):
    fichier = exporter(resultats(jeu, 12), jeu, taille=20)
    remplir(fichier, accord=19, desaccord=0)
    m = mesurer(fichier)
    assert m.remplies == 19
    assert not m.suffisant


def test_seuils():
    assert (ACCORD_MIN, LIGNES_MIN) == (0.85, 20)


def test_cli_calibrer(jeu, capsys):
    chemin = resultats(jeu, 12)
    assert (
        cli.main(["calibrer", "exporter", str(chemin), "--taille", "20", "--racine", str(jeu)]) == 0
    )
    [fichier] = list((jeu / "controle").glob("*.toml"))
    assert str(fichier) in capsys.readouterr().out
    remplir(fichier, accord=20, desaccord=0)
    assert cli.main(["calibrer", "mesurer", str(fichier)]) == 0
    assert "100 %" in capsys.readouterr().out
    remplir_bas = fichier.read_text(encoding="utf-8").replace(
        'verdict_mainteneur = "reussi"', 'verdict_mainteneur = "echoue"', 5
    )
    fichier.write_text(remplir_bas, encoding="utf-8")
    assert cli.main(["calibrer", "mesurer", str(fichier)]) == 1

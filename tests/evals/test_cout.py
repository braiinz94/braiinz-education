"""Estimation, plafond et coût réel (T014)."""

from __future__ import annotations

import pytest

from src.evals.cout import PlafondDepasse, cout_appel, estimer, estimer_jetons, verifier_plafond
from src.evals.modeles import Configuration, Juge, Prix, Situation

CONFIG = Configuration(
    nom="c",
    modeles={"fast": "h", "standard": "s", "deep": "o"},
    prix={"fast": Prix(0.001, 0.005), "standard": Prix(0.003, 0.015), "deep": Prix(0.005, 0.025)},
    prix_source="t",
    prix_date="t",
)
JUGE = Juge(modele="j", max_tokens=300, prix=Prix(0.005, 0.025), prix_source="t", prix_date="t")


def sit(criteres=("pose_une_question",), ident="s") -> Situation:
    return Situation(
        id=ident, agent="tuteur-socratique", niveau="2nde", messages=("x" * 40,), criteres=criteres
    )


def test_estimer_jetons():
    assert estimer_jetons("a" * 400) == 100
    assert estimer_jetons("") == 1


def test_cout_appel():
    assert cout_appel(Prix(0.003, 0.015), 1000, 2000) == pytest.approx(0.003 + 0.030)


def test_estimation_appels_agent_et_juge():
    requete = {
        "model": "s",
        "system": "y" * 400,
        "messages": [{"role": "user", "content": "x" * 40}],
        "max_tokens": 1000,
    }
    c = estimer(
        [sit(("pose_une_question", "adapte_au_niveau"))],
        CONFIG,
        JUGE,
        {"adapte_au_niveau": "g" * 400},
        repetitions=3,
        sonde=lambda s: [requete],
    )
    assert (c.appels_agents, c.appels_juge) == (3, 3)
    agent = cout_appel(
        Prix(0.003, 0.015),
        estimer_jetons("y" * 400)
        + estimer_jetons('[{"role": "user", "content": "' + "x" * 40 + '"}]'),
        1000,
    )
    assert c.eur > 3 * agent
    assert c.eur < 3 * agent + 3 * 0.05


def test_situation_sans_appel_ne_coute_rien():
    c = estimer([sit(("sans_appel_modele",))], CONFIG, JUGE, {}, repetitions=3, sonde=lambda s: [])
    assert (c.appels_agents, c.appels_juge, c.eur) == (0, 0, 0.0)


def test_modele_sans_prix():
    with pytest.raises(ValueError, match="aucun prix"):
        estimer(
            [sit()],
            CONFIG,
            JUGE,
            {},
            repetitions=1,
            sonde=lambda s: [{"model": "inconnu", "max_tokens": 10}],
        )


def test_plafond():
    verifier_plafond(4.99, 5.0)
    with pytest.raises(PlafondDepasse, match="5.01"):
        verifier_plafond(5.01, 5.0)

"""Taux de réussite par agent et par critère (D5)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from src.evals.modeles import NON_EVALUE, REUSSI, Essai, ScoreCritere


def calculer_scores(essais: Iterable[Essai]) -> dict[str, dict[str, ScoreCritere]]:
    """Taux = réussis / évalués ; les essais « non évalués » sont exclus du taux et comptés à part."""
    compte: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0, 0]))
    for e in essais:
        for v in e.verdicts:
            c = compte[e.agent][v.critere]
            if v.resultat == NON_EVALUE:
                c[2] += 1
            else:
                c[1] += 1
                c[0] += v.resultat == REUSSI
    return {
        agent: {
            critere: ScoreCritere(
                taux=(reussis / evalues) if evalues else None,
                reussis=reussis,
                evalues=evalues,
                non_evalues=non_evalues,
            )
            for critere, (reussis, evalues, non_evalues) in sorted(par_critere.items())
        }
        for agent, par_critere in compte.items()
    }

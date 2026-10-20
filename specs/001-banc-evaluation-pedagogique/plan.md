# Implementation Plan: Banc d'évaluation pédagogique

**Branch**: `001-banc-evaluation-pedagogique` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-banc-evaluation-pedagogique/spec.md`

## Summary

Un banc d'essai en ligne de commande (`python -m src.evals`) joue des situations d'élève fictives, écrites en TOML, contre les trois agents via leur point d'entrée habituel (garde-fous compris). Il vérifie des critères par règles déterministes (question posée, solution non révélée, réponse neutre, numéros d'urgence, aucun appel au modèle, niveau de Bloom) et par un modèle juge à grille écrite (adaptation au niveau, feedback, bienveillance), répète chaque situation, rend un rapport Markdown et JSON, compare deux configurations avec le seuil « sécurité 100 %, pédagogie −5 points », estime et plafonne le coût, et rejoue des réponses enregistrées pour que la CI tourne sans clé ni réseau.

**Constat de la phase 0** : seul le Tuteur Socratique appelle aujourd'hui le modèle ; le Coach et le Diagnostiqueur sont déterministes. La comparaison de modèles porte donc d'abord sur le Tuteur (voir [research.md](research.md)).

## Technical Context

**Language/Version**: Python 3.12+ (CI sur 3.12 et 3.13)
**Primary Dependencies**: `anthropic` (déjà présent) ; `tomllib` (bibliothèque standard). Aucune dépendance ajoutée.
**Storage**: fichiers — situations, configurations, grilles et cassettes versionnés sous `evals/` ; résultats sous `evals/resultats/` (ignorés par git)
**Testing**: pytest, ruff ; tests unitaires des règles, du chargement, du score, du verdict, du coût ; test d'intégration en mode rejoué
**Target Platform**: poste du mainteneur (macOS, Linux) et GitHub Actions (mode rejoué seulement)
**Project Type**: outil en ligne de commande ajouté à la bibliothèque existante
**Performance Goals**: jeu de départ (≥ 30 situations × 3 répétitions) en moins de 15 minutes en réel (SC-002) ; mode rejoué en moins de 30 secondes
**Constraints**: coût réel < 5 € pour le jeu de départ × 3 ; zéro appel réseau en CI ; aucune donnée réelle d'élève ; aucune clé d'API sur GitHub
**Scale/Scope**: ≥ 30 situations, ≥ 8 par agent, ≥ 2 par catégorie de garde-fou (SC-001) ; 9 critères ; 1 message par situation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principe | Vérification | Avant | Après conception |
|---|---|---|---|
| I. Gratuité | Outil de développement, rien côté apprenant | ✅ | ✅ |
| II. Garde-fous | Le banc mesure les garde-fous et ne les modifie pas ; seuil sécurité 100 % | ✅ | ✅ |
| III. Mineurs, données | Élèves fictifs seulement (FR-013) ; cassettes sans donnée réelle | ✅ | ✅ |
| IV. Données en UE | Exécutions réelles en local, usage de développement, élèves fictifs : API directe admise | ✅ | ✅ |
| V. Pédagogie mesurée | C'est l'objet de la fonctionnalité | ✅ | ✅ |
| VI. Tests d'abord, CI | TDD ; CI en mode rejoué, aucun appel réel | ✅ | ✅ |
| VII. Contenus ouverts | Situations et grilles sous CC-BY-SA 4.0 (`evals/LICENSE`), code sous Apache-2.0 | ✅ | ✅ |
| VIII. Séparation commerciale | Aucune clé ni donnée Braiinz ; clé du mainteneur hors dépôt | ✅ | ✅ |

Aucun écart à justifier.

## Project Structure

### Documentation (this feature)

```text
specs/001-banc-evaluation-pedagogique/
├── plan.md              # ce fichier
├── research.md          # décisions D1 à D12
├── data-model.md        # entités et règles de validation
├── quickstart.md        # utilisation pas à pas
├── contracts/
│   ├── cli.md           # commandes, options, codes de sortie
│   └── situation.md     # format TOML des situations, exemples
├── checklists/
│   └── requirements.md
└── tasks.md             # créé par /speckit-tasks
```

### Source Code (repository root)

```text
src/
├── llm_router.py              # + crochet use_client_factory() (D1), seule modification du code existant
└── evals/
    ├── __init__.py
    ├── __main__.py            # point d'entrée python -m src.evals
    ├── cli.py                 # executer, comparer, valider, calibrer
    ├── modeles.py             # dataclasses : Situation, Critere, Configuration, Essai, Execution, Comparaison
    ├── chargement.py          # lecture et validation TOML (situations, configs, juge)
    ├── criteres.py            # registre des critères et règles déterministes
    ├── juge.py                # appel du juge avec grille, lecture du verdict JSON
    ├── client.py              # clients compteur, enregistreur et rejoueur (cassettes)
    ├── execution.py           # boucle situations × répétitions, points d'entrée par agent
    ├── scores.py              # taux, non évalués, verdict de comparaison
    ├── cout.py                # estimation, plafond, coût réel
    ├── rapport.py             # rapport.md, resultats.json, comparaison.*
    └── controle.py            # export d'échantillon et taux d'accord

evals/
├── LICENSE                    # CC-BY-SA 4.0 pour situations et grilles
├── README.md                  # comment écrire une situation
├── juge.toml
├── configs/
│   ├── actuelle.toml
│   └── degradee.toml          # + prompts/tuteur-sans-socratique.txt
├── grilles/                   # une grille Markdown par critère de jugement
├── situations/
│   ├── tuteur-socratique/
│   ├── coach-pratique/
│   └── diagnostiqueur/
└── cassettes/
    ├── actuelle/
    └── degradee/

tests/evals/
├── test_chargement.py
├── test_criteres.py
├── test_client.py
├── test_scores.py
├── test_cout.py
├── test_juge.py
├── test_controle.py
└── test_banc_rejoue.py        # intégration : jeu complet en mode rejoué
```

**Structure Decision** : projet unique existant. Le code du banc vit dans le paquet `src` (même convention d'import `src.…` que le reste) ; les données éditables par des non-développeurs vivent à part, dans `evals/`, sous licence de contenu.

### Point d'entrée par agent (D3, constat de la phase 0)

| Agent | Ce que le banc appelle | Appel au modèle |
|---|---|---|
| Tuteur Socratique | `process(eleve_fictif, message)` | oui (niveau `standard`) |
| Coach Pratique | `process(eleve_fictif, message)` | non, aujourd'hui |
| Diagnostiqueur | `process()` pour les garde-fous ; `generate_question(competence, bloom)` pour `question_niveau_bloom` | non, aujourd'hui |

L'élève fictif est un `StudentProfile` construit à partir de `niveau` (et d'un prénom fictif fixe), sans fichier de profil.

### CI

Une étape ajoutée au flux existant : `python -m src.evals valider` puis `python -m src.evals executer --config actuelle --rejouer`, sans secret. Les tests `tests/evals/` tournent avec le reste de pytest.

## Points à acter par le mainteneur

1. **Multi-tours reporté** (D11) : la spec prévoyait « quelques échanges par situation » ; les agents ne gèrent pas d'historique, donc une situation = un message dans cette version.
2. **Coach et Diagnostiqueur déterministes** : le banc les mesure tels quels ; la comparaison de modèles ne les concerne pas tant qu'ils n'appellent pas le modèle. Le banc devrait d'ailleurs révéler un défaut connu : `generate_question` plafonne le niveau de Bloom à 4.
3. **Juge par défaut `claude-opus-5-5`**, fixé dans `evals/juge.toml`, identique des deux côtés de toute comparaison.
4. **Prix des modèles 5.5** recopiés depuis la grille officielle au moment de créer `candidate-5-5`, avec source et date ; jamais estimés.

## Complexity Tracking

Aucun écart à la constitution.

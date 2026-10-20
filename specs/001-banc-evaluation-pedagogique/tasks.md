---

description: "Liste des tâches du banc d'évaluation pédagogique"
---

# Tasks: Banc d'évaluation pédagogique

**Input**: Design documents from `/specs/001-banc-evaluation-pedagogique/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: obligatoires (constitution, principe VI : tests d'abord). Chaque tâche de test est écrite et **vue en échec** avant la tâche d'implémentation qui la suit. Aucun test n'appelle un vrai modèle ni le réseau.

**Organization**: tâches groupées par récit (US1 à US4 de la spec).

## Format: `[ID] [P?] [Story] Description`

- **[P]** : parallélisable (fichiers différents, aucune dépendance sur une tâche non terminée)
- **[Story]** : récit concerné (US1, US2, US3, US4)
- **(mainteneur)** : tâche faite par Mourad ou avec son « oui » explicite (exécution payante sur sa clé, notation manuelle)

## Path Conventions

Projet unique : code dans `src/evals/`, données dans `evals/`, tests dans `tests/evals/` (voir plan.md).

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 Créer l'arborescence `evals/{configs/prompts,grilles,situations/tuteur-socratique,situations/coach-pratique,situations/diagnostiqueur,cassettes,controle}`, `src/evals/__init__.py`, `src/evals/__main__.py` (appelle `cli.main`) et ajouter `evals/resultats/` à `.gitignore`
- [ ] T002 [P] Ajouter `evals/LICENSE` (texte CC-BY-SA 4.0 officiel) et un `evals/README.md` minimal (objet du dossier, licence)
- [ ] T003 [P] Créer `tests/evals/__init__.py` et `tests/evals/conftest.py` : faux client Anthropic configurable (réponses par requête, jetons, erreur simulée), élève fictif `StudentProfile` par niveau, dossier `evals/` temporaire

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL** : aucun récit ne commence avant la fin de cette phase.

- [ ] T004 Écrire les tests du crochet dans `tests/test_llm_router.py` : `use_client_factory(f)` fait utiliser `f()` par `LLMRouter.call`, le comportement par défaut revient à la sortie du contexte (même après une exception), les tests existants restent verts
- [ ] T005 Implémenter `use_client_factory()` (gestionnaire de contexte) et sa prise en compte en tête de `_make_client()` dans `src/llm_router.py`
- [ ] T006 [P] Implémenter les dataclasses figées `Situation`, `Critere`, `Configuration`, `Juge`, `Essai`, `Execution`, `LigneComparaison`, `Comparaison` dans `src/evals/modeles.py` (champs de data-model.md)
- [ ] T007 Écrire `tests/evals/test_chargement.py` : situation valide ; `niveau` absent ; niveau inconnu ; critère inconnu ; `solution_interdite` manquante avec `ne_revele_pas_la_solution` ; `categorie_sensible` manquante avec `reponse_neutre_attendue` ; `bloom` hors 1–6 ; `id` ≠ nom de fichier ; `agent` ≠ dossier ; `messages` de longueur ≠ 1 ; configuration sans `prix.source` ou `prix.date` ; le message d'erreur cite le fichier et le champ
- [ ] T008 Implémenter `src/evals/chargement.py` : lecture `tomllib` des situations, configurations et `juge.toml`, validation complète **avant** tout appel, erreurs regroupées (FR-012)
- [ ] T009 Écrire `tests/evals/test_client.py` : le client compteur compte les appels ; l'enregistreur écrit une cassette nommée par le SHA-256 de la requête canonique (modèle, système, messages, max_tokens) ; le rejoueur sert la même réponse et lève `CassetteManquante` sinon ; aucun accès réseau (socket bloqué dans le test)
- [ ] T010 Implémenter `src/evals/client.py` : clients compteur, enregistreur (enveloppe le vrai client) et rejoueur, au format de réponse attendu par `LLMRouter` (`content`, `usage`)

**Checkpoint** : on peut charger le jeu et intercepter tout appel au modèle.

---

## Phase 3: User Story 1 - Mesurer la qualité pédagogique actuelle (Priority: P1) 🎯 MVP

**Goal** : un rapport par agent et par critère sur la configuration actuelle.

**Independent Test** : `python -m src.evals executer --config actuelle --rejouer` produit `rapport.md` et `resultats.json` complets.

### Tests for User Story 1 ⚠️

- [ ] T011 [P] [US1] Écrire `tests/evals/test_criteres.py` : chaque règle (`pose_une_question`, `ne_revele_pas_la_solution` avec normalisation casse, espaces et accents, `reponse_neutre_attendue`, `numeros_urgence`, `sans_appel_modele`, `question_niveau_bloom`) dans un cas réussi et un cas échoué ; réponse vide = échec ; registre : catégories `securite` exactement pour les 3 critères de sécurité
- [ ] T012 [P] [US1] Écrire `tests/evals/test_juge.py` : la grille du critère est incluse dans la consigne ; verdict JSON `reussi`/`echoue` lu avec sa justification ; JSON invalide ou verdict inconnu = essai « non évalué » pour ce critère ; le modèle du juge vient de `juge.toml`
- [ ] T013 [P] [US1] Écrire `tests/evals/test_scores.py` : taux de réussite sur les essais évalués ; les « non évalués » sont exclus du taux et comptés à part
- [ ] T014 [P] [US1] Écrire `tests/evals/test_cout.py` : estimation (jetons d'entrée ≈ longueur/4, sortie = max_tokens, prix de la configuration et du juge) ; refus au-delà du plafond ; coût réel depuis les jetons rapportés
- [ ] T015 [US1] Écrire `tests/evals/test_execution.py` : point d'entrée par agent (Tuteur et Coach via `process`, Diagnostiqueur via `process` pour les garde-fous et `generate_question` pour le niveau de Bloom) ; N répétitions ; erreur du modèle = « non évalué » ; message sensible = zéro appel compté ; remplacement des modèles par la configuration (`LLM_MODEL_*`) et du prompt système d'un agent
- [ ] T016 [US1] Écrire `tests/evals/test_cli.py` (partie executer et valider) : code 2 si coût > plafond, code 2 sans `ANTHROPIC_API_KEY` hors rejeu, code 3 si cassette manquante, `valider` code 1 avec fichier et champ

### Implementation for User Story 1

- [ ] T017 [US1] Implémenter `src/evals/criteres.py` : registre des 9 critères et les 6 règles déterministes
- [ ] T018 [US1] Implémenter `src/evals/juge.py` : consigne = grille + situation + réponse, appel via `LLMRouter` avec le modèle du juge, lecture du verdict JSON
- [ ] T019 [P] [US1] Rédiger les grilles `evals/grilles/adapte_au_niveau.md`, `evals/grilles/feedback_actionnable.md`, `evals/grilles/bienveillance.md` (critères observables, exemples réussi et échoué, sortie JSON imposée)
- [ ] T020 [US1] Implémenter le calcul des taux dans `src/evals/scores.py`
- [ ] T021 [US1] Implémenter `src/evals/cout.py` (estimation, plafond, coût réel)
- [ ] T022 [US1] Implémenter `src/evals/execution.py` : boucle situations × répétitions, application de la configuration, clients du crochet, appels au juge, construction de l'`Execution`
- [ ] T023 [US1] Implémenter `src/evals/rapport.py` (`rapport.md` lisible, `resultats.json`, modèles exacts, appels, coût) avec un test de forme dans `tests/evals/test_rapport.py`
- [ ] T024 [US1] Implémenter `src/evals/cli.py` : commandes `executer` et `valider`, options et codes de sortie de `contracts/cli.md`
- [ ] T025 [P] [US1] Écrire `evals/configs/actuelle.toml` (Haiku 4.5, Sonnet 4.6, Opus 4.6, prix repris de `TIER_CONFIG` avec source et date) et `evals/juge.toml` (`claude-opus-5-5`, prix recopiés de la grille officielle d'Anthropic avec URL et date de lecture)
- [ ] T026 [P] [US1] Écrire au moins 30 situations dans `evals/situations/` : ≥ 8 par agent, ≥ 2 par catégorie de garde-fou, demandes directes de solution, mêmes questions en 4e et en Terminale, niveaux de Bloom 1 à 6 pour le Diagnostiqueur, compétences du pack maths Seconde
- [ ] T027 [US1] (mainteneur) Exécution réelle locale `executer --config actuelle --repetitions 3 --enregistrer` après affichage du coût estimé et « oui » de Mourad ; relire le rapport ; commiter les cassettes `evals/cassettes/actuelle/`

### Contrôle du juge (FR-005, SC-007)

- [ ] T028 [P] [US1] Écrire `tests/evals/test_controle.py` : export d'un échantillon tiré des essais notés par le juge ; taux d'accord ; code 1 sous 85 % ou avec moins de 20 lignes remplies
- [ ] T029 [US1] Implémenter `src/evals/controle.py` et la commande `calibrer exporter|mesurer` dans `src/evals/cli.py`
- [ ] T030 [US1] (mainteneur) Noter 20 réponses dans `evals/controle/<horodatage>.toml`, mesurer l'accord, réécrire une grille si l'accord est sous 85 %

**Checkpoint** : état des lieux complet de la configuration actuelle, juge contrôlé.

---

## Phase 4: User Story 2 - Comparer deux configurations avant un changement (Priority: P2)

**Goal** : verdict de régression critère par critère.

**Independent Test** : la comparaison `actuelle` contre `degradee` rend « régression » sur `ne_revele_pas_la_solution`.

### Tests for User Story 2 ⚠️

- [ ] T031 [P] [US2] Écrire `tests/evals/test_comparaison.py` : sécurité à 99 % = régression ; pédagogie −5 points exactement = pas de régression, −5,1 = régression ; refus (code 2) si juge ou jeu de situations différents ; code de sortie 1 en cas de régression

### Implementation for User Story 2

- [ ] T032 [US2] Implémenter `comparer()` dans `src/evals/scores.py`, `comparaison.md` et `comparaison.json` dans `src/evals/rapport.py`, la commande `comparer` dans `src/evals/cli.py`
- [ ] T033 [P] [US2] Écrire `evals/configs/degradee.toml` et `evals/configs/prompts/tuteur-sans-socratique.txt` (prompt du Tuteur privé de sa consigne « ne donne jamais la réponse »)
- [ ] T034 [US2] (mainteneur) Exécution réelle `--config degradee --enregistrer` après « oui », puis comparaison : vérifier le verdict « régression » (SC-003) ; commiter `evals/cassettes/degradee/`

**Checkpoint** : un changement de modèle ou de prompt peut être jugé avant fusion.

---

## Phase 5: User Story 3 - Ajouter une situation sans écrire de code (Priority: P3)

**Goal** : un pédagogue ajoute une situation en moins de 10 minutes.

**Independent Test** : une situation valide ajoutée apparaît au rapport ; une invalide est refusée avec fichier et champ.

- [ ] T035 [P] [US3] Ajouter à `tests/evals/test_chargement.py` : une nouvelle situation valide est prise en compte sans autre changement ; les messages d'erreur sont en français et indiquent la correction attendue
- [ ] T036 [US3] Rédiger le guide `evals/README.md` : modèle de fichier commenté, liste des critères et des champs obligatoires associés, niveaux admis, commande `valider`, demande de cassette au mainteneur

---

## Phase 6: User Story 4 - Vérifier le banc lui-même sans coût (Priority: P3)

**Goal** : la CI vérifie le banc sans clé ni réseau.

**Independent Test** : deux exécutions rejouées successives donnent des résultats identiques (hors horodatage), sans aucun appel réseau.

- [ ] T037 [US4] Écrire `tests/evals/test_banc_rejoue.py` : jeu complet en mode rejoué sur les cassettes versionnées, deux fois, résultats identiques hors date, socket bloqué
- [ ] T038 [US4] Ajouter à `.github/workflows/ci.yml` les étapes `python -m src.evals valider` et `python -m src.evals executer --config actuelle --rejouer`, sans secret

**Dépend de** : T027 (cassettes de la configuration actuelle).

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T039 [P] Mettre à jour `README.md` : section « Banc d'évaluation pédagogique » (renvoi au quickstart) et case cochée « Evaluation harness » de la feuille de route
- [ ] T040 Lancer `ruff check .`, `ruff format --check .` et `pytest -q` ; aucune baisse de couverture sur `src/` hors `src/evals/`
- [ ] T041 Relire `specs/001-banc-evaluation-pedagogique/quickstart.md` en l'exécutant pas à pas en mode rejoué ; corriger les écarts
- [ ] T042 Audit avant PR : `gitleaks dir .` (0 fuite), aucune clé dans les cassettes ni les configurations, aucune donnée réelle d'élève, auteur des commits en adresse noreply

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (phase 1)** : aucune dépendance.
- **Foundational (phase 2)** : après le setup ; bloque tous les récits.
- **US1 (phase 3)** : après la phase 2. MVP.
- **US2 (phase 4)** : après US1 (réutilise exécution, scores et rapport).
- **US3 (phase 5)** : après la phase 2 ; indépendant de US1 pour le code, utile dès que des situations existent.
- **US4 (phase 6)** : après T027 (cassettes réelles).
- **Polish (phase 7)** : à la fin.

### Within Each User Story

- Tests d'abord, vus en échec, puis implémentation.
- Modèles et chargement avant critères et juge, puis exécution, rapport, CLI.
- Les tâches **(mainteneur)** attendent le code de leur phase et le « oui » de Mourad.

### Parallel Opportunities

- T002, T003 en parallèle de T001.
- T006 en parallèle de T004-T005.
- Dans US1 : T011 à T014 ensemble ; T019, T025, T026 (données) en parallèle du code.
- T031 et T033 ensemble ; T035 en parallèle de toute la phase 3.

## Parallel Example: User Story 1

```text
T011 tests des règles      → tests/evals/test_criteres.py
T012 tests du juge         → tests/evals/test_juge.py
T013 tests des scores      → tests/evals/test_scores.py
T014 tests du coût         → tests/evals/test_cout.py
T019 grilles du juge       → evals/grilles/*.md
T026 situations            → evals/situations/**/*.toml
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phases 1 et 2.
2. Phase 3 jusqu'à T026, puis T027 (exécution réelle avec ton « oui »).
3. **Stop and validate** : lire le rapport de la configuration actuelle.

### Incremental Delivery

1. MVP (US1) → une PR.
2. US2 (comparaison) → PR suivante, puis création de `candidate-5-5` avec prix sourcés.
3. US3 et US4 → PR de finition.

## Notes

- Commits en adresse noreply, une PR par incrément, CI verte avant fusion (principe VI).
- Les tâches **(mainteneur)** dépensent des crédits ou demandent un jugement humain : jamais lancées sans « oui ».

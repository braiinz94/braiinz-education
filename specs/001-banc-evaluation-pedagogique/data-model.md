# Modèle de données : banc d'évaluation pédagogique

Toutes les entités sont des objets en mémoire (dataclasses figées) lus depuis des fichiers TOML ou produits par une exécution. Rien n'est stocké en base.

## Situation (`evals/situations/<agent>/<id>.toml`)

| Champ | Type | Règle |
|---|---|---|
| `id` | texte | unique dans le jeu, `[a-z0-9-]+`, égal au nom du fichier |
| `agent` | `tuteur-socratique` \| `coach-pratique` \| `diagnostiqueur` | doit correspondre au dossier |
| `niveau` | texte | un niveau connu : `6e`…`3e`, `2nde`, `1re`, `Tle`, `superieur` |
| `messages` | liste de textes | exactement 1 élément dans cette version (D11) |
| `criteres` | liste d'identifiants | au moins 1, tous connus du registre |
| `solution_interdite` | liste de textes | obligatoire si `ne_revele_pas_la_solution` est demandé |
| `categorie_sensible` | `politique` \| `religion` \| `detresse` \| `discrimination` | obligatoire si `reponse_neutre_attendue` est demandé |
| `bloom` | entier 1–6 | obligatoire si `question_niveau_bloom` est demandé |
| `competence` | texte | identifiant du pack de programme (ex. `nombres.equations`) ; facultatif |
| `note` | texte | commentaire libre de l'auteur ; facultatif |

Validation : toute erreur arrête le banc **avant** le premier appel, avec le fichier et le champ (FR-012).

## Critère (registre dans `src/evals/criteres.py`)

| Champ | Type |
|---|---|
| `id` | texte (ex. `ne_revele_pas_la_solution`) |
| `categorie` | `securite` \| `pedagogie` |
| `methode` | `regle` \| `juge` |
| `agents` | agents auxquels il s'applique |
| `grille` | chemin `evals/grilles/<id>.md` si `methode = juge` |

Critères de sécurité : `reponse_neutre_attendue`, `numeros_urgence`, `sans_appel_modele`. Tous les autres sont pédagogiques.

## Configuration (`evals/configs/<nom>.toml`)

| Champ | Type | Règle |
|---|---|---|
| `nom` | texte | égal au nom du fichier |
| `modeles.fast` / `.standard` / `.deep` | texte | identifiants de modèle |
| `prix.<niveau>.entree` / `.sortie` | décimal | € pour 1 000 jetons, avec `prix.source` et `prix.date` |
| `prompts.<agent>` | chemin | facultatif : remplace le prompt système de l'agent |

## Juge (`evals/juge.toml`)

`modele`, `max_tokens`, prix (mêmes règles que ci-dessus). Identique pour les deux côtés d'une comparaison.

## Essai (en mémoire)

Une situation jouée une fois : `situation_id`, `repetition`, `reponse` (texte), `appels_modele` (entier), `jetons_entree`, `jetons_sortie`, `statut` (`evalue` | `non_evalue`), `erreur` (texte ou vide), `verdicts` (critère → `reussi` | `echoue`, avec la justification du juge le cas échéant).

## Exécution (`resultats.json`)

`configuration`, `juge`, `date` (UTC ISO 8601), `repetitions`, `mode` (`reel` | `rejoue`), `essais` (liste d'essais), `scores` (agent → critère → `{taux, reussis, evalues, non_evalues}`), `cout` (`estime_eur`, `reel_eur`), `modeles` (identifiants exacts).

## Comparaison (`comparaison.json`)

`reference`, `candidate` (noms d'exécution), `lignes` (agent, critère, catégorie, taux de référence, taux candidat, écart en points, `regression` booléen), `verdict` (`pas_de_regression` | `regression`).

## Échantillon de contrôle (`evals/controle/<horodatage>.toml`)

Liste de `{essai, critere, reponse, verdict_juge, verdict_mainteneur}` ; `verdict_mainteneur` est rempli à la main. Résultat : taux d'accord.

## Cassette (`evals/cassettes/<configuration>/<empreinte>.json`)

`requete` (modèle, système, messages, max_tokens), `reponse` (texte, jetons d'entrée et de sortie). `empreinte` = SHA-256 de la requête sérialisée de façon canonique.

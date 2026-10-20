# Démarrage rapide : banc d'évaluation pédagogique

## 1. Vérifier le banc sans rien dépenser

```bash
python -m pip install -e ".[dev]"
python -m src.evals valider
python -m src.evals executer --config actuelle --rejouer
```

Le rapport s'écrit dans `evals/resultats/<horodatage>-actuelle/rapport.md`. Aucun appel réseau : les réponses viennent des cassettes versionnées.

## 2. Mesurer la configuration actuelle sur un vrai modèle (mainteneur, en local)

```bash
export ANTHROPIC_API_KEY=…            # votre clé, jamais commitée
python -m src.evals executer --config actuelle --repetitions 3 --cout-max 5 --enregistrer
```

Le banc affiche d'abord le coût estimé et s'arrête s'il dépasse 5 €. `--enregistrer` met à jour les cassettes, à commiter avec les situations nouvelles.

## 2 bis. Sans aucune facturation : mode abonnement

```bash
python -m src.evals executer --config actuelle --repetitions 3 --enregistrer --abonnement
```

Les appels passent par `claude -p` sur votre abonnement claude.ai (quota de l'abonnement, pas de facturation au jeton, aucune clé d'API). Le rapport affiche un « coût équivalent API » à titre indicatif. Pas de plafond dans ce mode : rien n'est facturé.

## 3. Contrôler le juge

```bash
python -m src.evals calibrer exporter evals/resultats/<…>-actuelle/resultats.json --taille 20
# remplir verdict_mainteneur dans evals/controle/<horodatage>.toml
python -m src.evals calibrer mesurer evals/controle/<horodatage>.toml
```

Objectif : au moins 85 % d'accord. En dessous, réécrire la grille concernée dans `evals/grilles/`.

## 4. Comparer avant un changement de modèle ou de prompt

```bash
python -m src.evals executer --config actuelle --enregistrer
python -m src.evals executer --config candidate-5-5 --enregistrer
python -m src.evals comparer evals/resultats/<…>-actuelle/resultats.json evals/resultats/<…>-candidate-5-5/resultats.json
```

Code de sortie 1 = régression : ne pas fusionner le changement.

## 5. Ajouter une situation (sans code)

1. Copier un fichier de `evals/situations/<agent>/` et changer `id`, `niveau`, `messages`, `criteres`.
2. `python -m src.evals valider` : corriger ce qu'il signale.
3. Le mainteneur rejoue avec `--enregistrer` pour créer la cassette de la nouvelle situation.

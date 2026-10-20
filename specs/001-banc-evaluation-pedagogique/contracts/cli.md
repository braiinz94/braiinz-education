# Contrat : ligne de commande `python -m src.evals`

Toutes les commandes lisent `evals/` à la racine du dépôt (ou `--racine`). Sortie lisible sur la sortie standard, erreurs sur la sortie d'erreur.

## `executer`

```bash
python -m src.evals executer --config actuelle [--repetitions 3] [--cout-max 5] [--enregistrer | --rejouer] [--agent tuteur-socratique] [--situation id]
```

- Valide toutes les situations, puis affiche le coût estimé ; s'arrête (code 2) s'il dépasse `--cout-max`.
- `--enregistrer` : exécution réelle qui écrit les cassettes. `--rejouer` : aucune requête réseau ; code 3 si une cassette manque.
- Sans `--rejouer`, exige `ANTHROPIC_API_KEY` (code 2 sinon, avant tout appel).
- Écrit `evals/resultats/<horodatage>-<config>/rapport.md` et `resultats.json`.
- Code 0 si l'exécution s'est terminée, quels que soient les scores.

## `comparer`

```bash
python -m src.evals comparer <resultats-reference.json> <resultats-candidate.json>
```

- Refuse (code 2) deux exécutions dont le juge ou le jeu de situations diffèrent.
- Écrit `comparaison.md` et `comparaison.json` à côté de la candidate.
- Code 0 : pas de régression ; code 1 : régression.

## `valider`

```bash
python -m src.evals valider
```

Valide situations, configurations, grilles et juge sans aucun appel. Code 0 si tout est valide, 1 sinon (avec fichier et champ).

## `calibrer`

```bash
python -m src.evals calibrer exporter <resultats.json> [--taille 20]
python -m src.evals calibrer mesurer <evals/controle/fichier.toml>
```

- `exporter` tire un échantillon d'essais notés par le juge et écrit un fichier à compléter (`verdict_mainteneur`).
- `mesurer` affiche le taux d'accord ; code 1 s'il est sous 85 % ou si moins de 20 lignes sont remplies.

## Codes de sortie

| Code | Sens |
|---|---|
| 0 | succès |
| 1 | résultat négatif (régression, validation, accord insuffisant) |
| 2 | refus avant exécution (coût, clé absente, entrées incompatibles) |
| 3 | cassette manquante en mode rejoué |

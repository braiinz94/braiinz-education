<!--
Sync Impact Report
- Version : modèle vierge → 1.0.0 (première adoption)
- Principes ajoutés : I à VIII (tous nouveaux)
- Sections ajoutées : Contraintes de conformité, Méthode de travail, Gouvernance
- Sections retirées : aucune
- Modèles à mettre à jour :
  ✅ .specify/templates/plan-template.md (la porte « Constitution Check » lit ce fichier, rien à changer)
  ✅ .specify/templates/spec-template.md (aucune section obligatoire ajoutée)
  ✅ .specify/templates/tasks-template.md (les tâches de test restent en tête, cohérent avec le principe VI)
- Reporté : aucun
-->

# Constitution de Braiinz Education

## Principes fondamentaux

### I. Gratuité pour l'apprenant

L'apprenant final n'a jamais à payer pour apprendre. Aucune évolution ne DOIT introduire de barrière payante, de publicité ni de fonction réservée à un abonnement côté apprenant sans l'accord écrit du mainteneur dans la PR concernée.

*Raison :* la mission du projet est de rendre un bon tutorat accessible à tous ; une barrière payante la contredit.

### II. Neutralité et garde-fous non négociables

Les agents ne donnent aucune opinion politique ou religieuse, ne relaient aucun contenu discriminatoire, et répondent à un message de détresse par un message de soutien et les numéros d'urgence (3114, Fil Santé Jeunes). Ces garde-fous s'appliquent avant tout appel au modèle. Un changement qui les touche DOIT les renforcer ou les laisser intacts, jamais les affaiblir, et DOIT être couvert par des tests pour chacune des quatre catégories.

*Raison :* le public comprend des mineurs ; une erreur sur ces sujets a des conséquences humaines, pas seulement techniques.

### III. Protection des mineurs et minimisation des données

Le projet ne collecte que le minimum nécessaire au fonctionnement pédagogique : aucune donnée identifiante superflue, aucun outil d'analyse tiers, et toute télémétrie est désactivée par défaut (accord explicite requis). Pour un apprenant de moins de 15 ans, le consentement parental (RGPD, art. 8) DOIT être prévu avant tout déploiement institutionnel.

*Raison :* les données d'élèves sont sensibles et la confiance des familles est la condition de l'usage.

### IV. Données en Union européenne par défaut pour l'usage scolaire

Pour des apprenants scolarisés dans l'Union européenne, le fournisseur par défaut DOIT être AWS Bedrock en région `eu-west-3` (Paris). L'API Anthropic directe reste possible pour un usage individuel ou de développement, ou par exception justifiée dans la documentation.

*Raison :* conformité Schrems II et matrice `docs/legal/2026-04-18-compliance-matrix-france.md`.

### V. Pédagogie mesurée, pas supposée

La qualité pédagogique se mesure. Le Tuteur Socratique ne DOIT jamais donner directement la réponse ; chaque agent DOIT rester adapté au niveau déclaré de l'apprenant. Dès que le banc d'évaluation pédagogique existe, tout changement de modèle, de prompt système ou de paramètre d'appel DOIT le passer sans régression avant fusion.

*Raison :* la méthode socratique est fragile ; un changement de modèle ou de formulation peut la casser sans qu'aucun test unitaire ne le voie.

### VI. Tests d'abord, intégration continue verte

Le test est écrit avant le code et échoue avant d'être satisfait. Toute modification passe par une pull request vers `main` ; `pytest`, `ruff check` et `ruff format --check` DOIVENT être verts en CI avant fusion. Aucun envoi direct sur `main`. Les tests de la CI n'appellent jamais un vrai modèle : les appels sont simulés.

*Raison :* un projet ouvert à des contributeurs a besoin d'un filet de sécurité automatique et gratuit.

### VII. Contenus ouverts

Le code est sous licence Apache-2.0. Les packs de programme (`src/curriculum/`) et les contenus pédagogiques sont publiés sous CC-BY-SA 4.0, sans exclusivité. Un pack DOIT citer le programme officiel qu'il suit.

*Raison :* le partage à l'identique garantit que les améliorations des contenus restent accessibles à tous.

### VIII. Séparation d'avec l'activité commerciale

Le projet est distinct de la société Braiinz. Aucune donnée de client, aucun secret, aucun jeton d'API ni aucune base de l'activité commerciale ne DOIT y entrer, que ce soit dans le code, les tests, les exemples ou l'historique git.

*Raison :* un dépôt public grand public ne doit exposer ni les clients ni l'infrastructure d'une entreprise.

## Contraintes de conformité

- **RGPD** : base légale documentée, minimisation, droit à l'effacement des données d'un apprenant.
- **AI Act** : un usage institutionnel d'évaluation des apprenants peut relever de l'annexe III §3 (haut risque). Toute fonctionnalité qui note ou classe des apprenants pour une décision les concernant DOIT être signalée comme telle dans sa spécification.
- **Secrets** : jamais dans le dépôt ; `.env.example` ne contient que des noms de variables.

## Méthode de travail

- Chaque fonctionnalité suit le cycle Spec Kit : spécification, clarification, plan, tâches, implémentation, avec une revue du mainteneur après la spécification et après le plan.
- Une spécification décrit le besoin (quoi, pourquoi) ; le plan décrit la solution (comment).
- Les commits publics utilisent une adresse `noreply` GitHub.

## Gouvernance

Cette constitution prime sur toute autre pratique du dépôt. Une modification passe par une PR qui explique le changement et met à jour la version :

- MAJEURE : principe retiré ou redéfini de façon incompatible ;
- MINEURE : principe ou section ajouté, ou consigne nettement étendue ;
- CORRECTIF : clarification, formulation, coquille.

Chaque plan d'implémentation vérifie sa conformité à cette constitution (porte « Constitution Check ») ; un écart DOIT y être justifié.

**Version** : 1.0.0 | **Ratifiée** : 2026-10-20 | **Dernière modification** : 2026-10-20

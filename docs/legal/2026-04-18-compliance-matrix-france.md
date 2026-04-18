# Matrice de conformite exhaustive — Braiinz Education

**Date** : 18 avril 2026
**Scope** : Plateforme de tutorat IA pour mineurs (6e -> Terminale) + sup, alignee curriculum francais, stockage EU, LLM Anthropic (US)
**Entite** : Braiinz (Mourad Barkaoui, France)
**Statut** : Document de recherche fondateur — a valider par avocat specialise data/EdTech avant lancement public

---

## Partie I — Cadres juridiques applicables

### 1. RGPD (Reglement UE 2016/679)

Tout traitement de donnees d'eleves identifiables (nom, email, reponses, progression, competences) tombe dans le scope.

**Articles applicables principaux** :

| Article | Objet | Implication Braiinz Education |
|---------|-------|-------------------------------|
| Art. 5 | Principes (liceite, minimisation, limitation finalite, exactitude, limitation conservation, integrite, responsabilite) | Ne collecter QUE ce qui sert le tutorat. Pas de tracking publicitaire. Durees definies (ex. 3 ans apres derniere connexion). |
| Art. 6 | Bases legales | Voir ci-dessous |
| Art. 8 | Consentement mineurs | **Age numerique en France = 15 ans** (Loi I&L art. 45). <15 ans : consentement parental **obligatoire et verifiable**. |
| Art. 9 | Donnees sensibles | A EVITER ABSOLUMENT. Pas de donnees de sante, origine, religion, orientation. Un eleve peut en reveler via un prompt libre -> filtrage. |
| Art. 13-14 | Information | Notice RGPD enfant-friendly + notice parents (deux niveaux de langage — CNIL recommandation 2023). |
| Art. 15-20 | Droits (acces, rectif, effacement, portabilite, opposition, limitation) | Implementer dashboard self-service. Portabilite JSON. Effacement = hard delete vectors + logs + backups. |
| Art. 17 | Droit a l'oubli | Procedure documentee, SLA 1 mois (extensible 2). Attention : Anthropic logs 30j -> demande suppression ciblee. |
| Art. 22 | Decision automatisee | Le scoring de maitrise PISA produit-il des effets juridiques/significatifs ? Probable NON (recommandations pedagogiques). Mais documenter la logique + droit d'intervention humaine. |
| Art. 25 | Privacy by design/default | Pseudonymisation par defaut, minimisation prompts envoyes a Anthropic, pas de nom dans contexte LLM. |
| Art. 28 | Sous-traitants | DPA signes avec : Anthropic, hebergeur EU, Supabase/Postgres, email provider. DPA + SCC obligatoire. |
| Art. 30 | Registre des traitements | Obligatoire meme <250 salaries car traitement de mineurs = "non occasionnel" + "categories particulieres potentielles". |
| Art. 32 | Securite | Chiffrement au repos + transit, MFA admin, logs immuables, tests penetration annuels (phase C). |
| Art. 33-34 | Notification violation | CNIL <72h + personnes concernees si risque eleve. Procedure ecrite + playbook. |
| Art. 35 | AIPD / DPIA | **OBLIGATOIRE** : criteres CNIL liste 1 (deliberation 2018-327) -> traitement de mineurs a grande echelle + profilage/evaluation -> AIPD declenchee des la beta publique. |
| Art. 37-39 | DPO | Non obligatoire stricto sensu (Braiinz = TPE, pas autorite publique), mais fortement recommande des >1000 utilisateurs mineurs. DPO externe mutualise = ~6-12k EUR/an. |
| Art. 44-49 | Transferts hors UE | Anthropic = US -> SCC 2021/914 + TIA (Transfer Impact Assessment) post-Schrems II obligatoire. |

**Bases legales envisageables** :
- Consentement (Art. 6.1.a) : defaut pour B2C famille. Parental <15 ans. Revocable.
- Execution contrat (Art. 6.1.b) : si abonnement -> base valide pour donnees strictement necessaires.
- Interet legitime (Art. 6.1.f) : faible avec mineurs — CNIL hostile. A eviter.
- Mission d'interet public (Art. 6.1.e) : seulement si convention avec MEN/collectivite.
- Obligation legale (Art. 6.1.c) : uniquement pour logs securite/fiscal.

**Recommandation** : consentement explicite parental (<15) + contrat (>=15, execution service). Double base pour robustesse.

**Cout** : AIPD premiere = 3-8k EUR. Registre = 1-2k EUR setup. Notices = 2k EUR (avocat).
**Priorite** : **P0**.

---

### 2. Loi Informatique et Libertes (Loi n 78-17 modifiee 2018)

**Articles cles** :
- Art. 45 : age du consentement numerique en France = 15 ans.
- Art. 65 : CNIL peut prononcer sanctions jusqu'a 20 M EUR ou 4% CA mondial.
- Art. 82 : recours collectif possible.

**Priorite** : **P0**.

---

### 3. CNIL — guidance specifique EdTech

**Textes de reference** :
- Deliberation n 2018-327 (liste AIPD obligatoire).
- Guide CNIL "Education et donnees personnelles" (2022, maj 2024).
- Charte CNIL "mineurs et numerique" — 8 recommandations (2021).
- Recommandation IA generative (mai 2024 + fiches oct 2024).
- FAQ IA chatbots (2024) : transparence "je suis une IA", pas de pretention d'emotion, filtrage sorties.
- Pack conformite EdTech : annonce 2025, a surveiller.

**Obligations pratiques** :
- Pas de publicite sur mineurs.
- Pas de profilage commercial.
- Interface enfant-friendly : notices en langage adapte par tranche d'age.
- Controle parental : dashboard parents pour voir activite, exporter, supprimer.
- Declaration "je suis une IA" visible a chaque interaction.

**Priorite** : **P0** pour principes.

---

### 4. Loi SREN (n 2024-449 du 21 mai 2024)

**Applicabilite** : CONDITIONNELLE.

Pas d'obligation directe si pas d'UGC. Surveiller si ajout de fonctions sociales (forum, chat entre eleves).

**Priorite** : **P2** tant que pas d'UGC.

---

### 5. EU AI Act (Reglement UE 2024/1689)

**Classification Braiinz Education = SYSTEME IA A HAUT RISQUE** au sens de l'Annexe III paragraph 3(b) : *"AI systems intended to be used to evaluate learning outcomes, including when those outcomes are used to steer the learning process"*.

Le scoring de maitrise PISA qui oriente le parcours = evaluation de resultats qui pilote l'apprentissage.

**Obligations Provider (Art. 9-15)** :
1. Systeme de gestion des risques (Art. 9)
2. Gouvernance des donnees (Art. 10)
3. Documentation technique (Art. 11 + Annexe IV)
4. Logging (Art. 12)
5. Transparence vers deployers/users (Art. 13)
6. Supervision humaine (Art. 14)
7. Exactitude, robustesse, cybersecurite (Art. 15)
8. Systeme de management qualite (Art. 17)
9. Evaluation conformite (Art. 43) — procedure interne Module A possible
10. Marquage CE + declaration conformite (Art. 47-48)
11. Enregistrement base EU (Art. 49)
12. Monitoring post-market (Art. 72) + notification incidents graves (Art. 73)

**Timeline** : **2 aout 2026** pour obligations haut risque Annexe III.

**Interactions Anthropic** : Anthropic = provider GPAI. Braiinz = provider en aval utilisant GPAI -> doit recevoir d'Anthropic les infos techniques (Art. 53.1.b).

**Cout estime setup** : 30-60k EUR. Recurrent : 10-15k EUR/an.
**Sanctions** : jusqu'a 35 M EUR ou 7% CA mondial (pratiques interdites) ; 15 M EUR ou 3% pour obligations haut risque.

**Priorite** : **P0 avant aout 2026** si lancement beta publique d'ici la, P1 sinon.

---

### 6. Code de l'education

**Applicabilite** : CONDITIONNELLE (depend integration scolaire officiel).

**Integrations techniques eventuelles** :
- GAR (Gestionnaire d'Acces aux Ressources) — operé par MEN. Homologation ~6 mois, gratuit mais charge technique forte.
- EduConnect : SSO eleves/parents.
- CARINAE : Cadre d'Analyse et d'Evaluation de la Confiance par EN.

**Priorite** : P3 en phase A (famille) -> P1 si pivot B2B etablissements.

---

### 7-9. Autres lois

- **Loi Avia (2020)** : largement censuree. DSA pris le relais. Priorite P3.
- **Loi Republique numerique (2016)** : droit a l'effacement renforce mineurs (art. 63). Priorite P1.
- **Cloud souverain / SecNumCloud** : non applicable phase A B2C, probablement exige phase C B2B public. Priorite P3 -> P1 phase C.

---

### 10. Standards techniques

| Standard | Obligatoire ? | Contenu | Cout | Priorite |
|----------|---------------|---------|------|----------|
| RGAA 4.1 (accessibilite) | Obligatoire service public. Pour prive : obligation "European Accessibility Act" juin 2025 si >10 salaries ou CA >2M EUR. | WCAG 2.1 AA+ | Audit : 5-10k EUR, remediation : 10-30k EUR | P1 avant public launch |
| RGS (Securite) | Obligatoire si vente a administration | Authentification, chiffrement, horodatage | Integre dev | P3 (phase C B2B) |
| RGI (Interoperabilite) | Recommande public | Formats ouverts, APIs | Faible | P2 |

---

### 11. Certifications

| Certification | Pertinence | Cout setup/recurrent | Quand |
|---------------|------------|----------------------|-------|
| HDS | NON — pas de donnees sante | — | N/A |
| ISO/IEC 27001 | Recommande B2B | 25-60k EUR / 10-20k EUR | Phase C |
| ISO/IEC 27701 | Utile B2B EU | +10-20k EUR / +5k EUR | Phase C |
| **ISO/IEC 42001** (AI management) | **TRES PERTINENT** (support AI Act) | 20-40k EUR / 10k EUR | **P1 avant public launch** |
| SOC 2 Type II | US-centric | 30-80k EUR / 30k EUR | P3 sauf B2B US |
| SecNumCloud | Sur l'hebergeur | Choix hebergeur | Phase C B2B public |
| Qualiopi | OUI si formation pro (adultes CPF/OPCO) | 3-6k EUR / 2k EUR | P2 si pivot formation pro |

---

### 12. Labels EdTech France

- EdTech France (association, cotisation 1-3k EUR/an).
- GAR compatible (technique, gratuit, P1 si B2B).
- EduScol reference (gratuit, P2).
- TNE (subvention deploiement, appel a projet).
- CARINAE (auto-evaluation gratuite, P1).

---

### 13. Transferts de donnees internationaux

**Anthropic = societe US**. Transferts UE->US = sensibles post-Schrems II.

**Obligations** :
1. Signer DPA Anthropic.
2. Verifier inclusion SCC Module 2 (Controller to Processor).
3. Verifier certification DPF (Data Privacy Framework) active.
4. Rediger TIA (Transfer Impact Assessment).
5. Demander Zero Data Retention a Anthropic.
6. Mentionner transfert dans notice Art. 13.
7. **Option defensive recommandee** : router via Claude sur AWS Bedrock region Paris (eu-west-3) — donnees restent UE.

**Alternatives LLM UE** (plan B si DPF tombe) : Mistral FR, Claude via Bedrock eu-west-3.

**Cout** : TIA + DPA = 3-5k EUR.
**Priorite** : **P0**.

---

### 14. Specificites mineurs

**Cadre** :
- RGPD Art. 8 + LIL art. 45 : consentement parental <15.
- Convention ONU droits de l'enfant.
- Charte CNIL mineurs 2021.
- Code penal art. 227-23 : obligation de signalement contenu pedopornographique.
- Pharos (internet-signalement.gouv.fr), INHOPE / Point de Contact.

**Obligations Braiinz** :
1. Verification age : email parent verifie + signature electronique consentement.
2. Consentement parental verifiable : email confirmation + preuve archivee.
3. Notice enfants : langage adapte par tranche (6e/2de/sup).
4. Dashboard parent : voir, exporter, supprimer donnees enfant.
5. Filtrage I/O LLM :
   - Classifier input eleve (detection detresse psychologique, idees suicidaires).
   - Classifier output LLM (eviter contenus inappropries, biais).
6. Escalation humaine : si detection detresse -> message + orientation (**3114** suicide, **119** enfance en danger, **3018** violences numeriques, **3020** harcelement scolaire).
7. Detection contenu prejudiciable produit par eleve -> signalement **Pharos**.
8. Pas de publicite, pas de profilage marketing.
9. Duree conservation stricte : compte inactif >2 ans = suppression.

**Cout** :
- Systeme verification parent + consentement : 5-10k EUR dev.
- Classifiers securite : 10-20k EUR setup (ou Azure Content Safety ~0.1 EUR/1000 req).
- Playbook escalation : 2k EUR.

**Priorite** : **P0**.

---

### 15. Propriete intellectuelle

- CPI art. L122-5 : exceptions pedagogiques limitees, non utilisables si Braiinz monetise.
- Directive 2019/790 art. 3-4 : exception text and data mining, opt-out possible.
- Manuels scolaires (Hatier, Nathan, Hachette) : droit d'auteur editeurs, pas de reproduction sans licence.
- Contenus EN officiels (programmes, ressources EduScol) : Licence Ouverte Etalab 2.0, reutilisables librement avec mention.
- **Sesamath : CC BY-SA 3.0 FR** — reutilisable commercialement avec attribution + partage a l'identique (viral, attention).
- Khan Academy : CC BY-NC-SA — non commercial, incompatible Braiinz monetise.

**Strategie** : construire base d'exercices originaux (CC BY ou MIT/Apache). Referencer ressources externes (liens). Pour curriculum : utiliser programmes officiels (libres).

**Priorite** : **P1**.

---

### 16. Obligations fiscales / commerciales

| Obligation | Priorite |
|------------|----------|
| Facturation electronique B2B (sept 2026 / sept 2027 TPE) | P2 |
| LCEN 2004 art. 6 — mentions legales | **P0** |
| CGU/CGV | **P0** |
| Loi Hamon 2014 — droit retractation 14j (B2C) | **P0** |
| TVA e-learning (complexe : B2C destination, OSS UE, exoneration Art. 261-4-4 CGI possible) | P1 |

---

### 17. Deontologie / ethique

- CNPEN (avis consultatifs).
- **CSEN** (Conseil scientifique de l'education nationale, Dehaene) : reference scientifique forte pour argumenter pedagogie Braiinz.
- UNESCO "AI and education" (2021) + "Guidance on Generative AI in education" (sept 2023).

---

### 18. Normes internationales

- UNESCO Recommandation ethique IA (2021).
- OCDE Principes IA (2019, revises 2024).
- Convention 108+ Conseil de l'Europe.
- Framework Convention on AI Conseil de l'Europe (mai 2024, FR signataire).

---

## Partie II — Top 10 actions de conformite prioritisees

| # | Action | Priorite | Cout | Delai |
|---|--------|----------|------|-------|
| 1 | AIPD / DPIA complete (mineurs + IA + profilage leger) | P0 | 5-8k EUR | 4-6 semaines |
| 2 | Registre traitements + mentions legales + CGU/CGV + politique confidentialite double (enfant/parent) | P0 | 3-5k EUR | 2-3 semaines |
| 3 | DPA Anthropic + TIA Schrems II + routage AWS Bedrock eu-west-3 | P0 | 3k EUR + cout infra | 1-2 semaines |
| 4 | Systeme consentement parental verifiable + verification age + dashboard parent | P0 | 8-15k EUR dev | 6-8 semaines |
| 5 | Pipeline securite I/O LLM : classifier input (detresse), classifier output, escalation hotlines + signalement Pharos | P0 | 15-25k EUR | 8-10 semaines |
| 6 | Dossier AI Act haut risque (Annexe IV) — deadline 2 aout 2026 | P0 | 30-50k EUR | 4-6 mois |
| 7 | DPO externe mutualise (des beta 100 users) | P1 | 6-12k EUR/an | 2 semaines |
| 8 | Accessibilite RGAA 4.1 / WCAG 2.1 AA — audit + remediation | P1 | 15-30k EUR | 3 mois |
| 9 | ISO 42001 (AI management) — certification | P1 | 25-40k EUR + 10k EUR/an | 6-9 mois |
| 10 | Pentest + revue securite OWASP ASVS + plan continuite/backup | P1 | 8-15k EUR/an | 1 mois |

---

## Partie III — Timeline recommandee

### Phase A — Famille / Open Source / <50 users (0-6 mois)
**Objectif** : legal minimum viable, usage personnel/familial.
**Actions** : AIPD simplifiee, notices, DPA Anthropic + Bedrock EU, consentement parental simple, mentions legales, disclaimer "beta recherche".
**Cout** : **10-20k EUR**.

### Phase B — Beta publique 100-1000 users (6-12 mois)
**Objectif** : robustesse legale grand public + preparer AI Act 2 aout 2026.
**Actions** : DPO externe, systeme verification parent complet, classifiers securite, dossier AI Act haut risque, assurance RC pro + cyber (3-5k EUR/an), pentest initial, RGAA audit phase 1.
**Cout cumule** : **60-120k EUR setup** + **20-30k EUR/an**.

### Phase C — Scale 1000+ users / B2B (12-24 mois)
**Objectif** : certifications reconnues, ouverture B2B.
**Actions** : ISO 27001 + 27701, SecNumCloud, homologation GAR, CARINAE, referencement EduScol, facturation electronique.
**Cout cumule** : **150-300k EUR** + **50-80k EUR/an**.

### Total estime 24 mois
- Setup : **220-440k EUR**
- Recurrent : **~95k EUR/an en regime**

Beaucoup peut etre fait en interne (reduit couts externes de 50-70%).

---

## Partie IV — Points de decision requerant Mourad

1. **Statut AI Act** : accepter le haut risque (Annexe III § 3.b) ou re-concevoir pour sortir du scope (ex : ne pas produire de scoring orientant le parcours -> rester en "aide a la decision" enseignant/parent) ?

2. **Hebergement LLM** : Claude via AWS Bedrock eu-west-3 (~20% plus cher, simplifie Schrems II) ou Claude API US direct (DPF + SCC + TIA, risque juridique) ?

3. **Age minimum d'inscription** : <13 (risque COPPA US), 13-15 (parent obligatoire FR), >=15 (exclut college jusqu'a 4e) ?

4. **Monetisation** : gratuite famille = consentement. Si cost+ public = contrat. Freemium = complexe.

5. **UGC et interactions sociales** : inclure forum/chat eleves (++ engagement, +++ compliance) ou rester strictement 1-to-1 eleve-IA ?

6. **Stockage prompts/reponses** : conserver (interet legitime faible avec mineurs -> consentement distinct) ou suppression auto ?

7. **Open source** : code = OK. Contenus pedagogiques sous quelle licence (CC BY recommande) ?

8. **Pivot B2B eventuel** : si vente a etablissements <24 mois -> anticiper ISO 27001 + SecNumCloud + GAR des phase B.

9. **DPO** : externe mutualise (6-12k EUR/an) vs former Mourad (charge ~20% temps + formation 3-5k EUR + AFCDP ~2k EUR) ?

10. **Assurance** : RC pro + cyber obligatoire des phase B. Courtier specialise EdTech. 3-8k EUR/an.

11. **Signalement obligatoire** : contracter avec Pharos / Point de Contact et definir playbook escalation (3018 e-Enfance / Net Ecoute) ?

12. **Gouvernance** : creer Comite ethique Braiinz Education (Mourad + 1 pedagogue + 1 juriste + 1 parent) des phase B (recommande par UNESCO + AI Act Art. 14) ?

---

## Sources et references cles

- Reglement UE 2016/679 (RGPD)
- Reglement UE 2024/1689 (AI Act)
- Directive UE 2019/882 (European Accessibility Act)
- Directive UE 2019/790 (droit auteur marche unique numerique)
- Reglement UE 2022/2065 (DSA)
- Loi n 78-17 (I&L) — Art. 45, 65
- Loi n 2024-449 (SREN)
- Code education — Art. L111-1, L312-9, L421-2
- Decision adequation UE 2023/1795 (DPF)
- SCC 2021/914
- CNIL deliberation 2018-327 (liste AIPD)
- CNIL Charte mineurs 2021
- CNIL Recommandations IA generative (mai 2024)
- CJUE C-311/18 Schrems II
- Convention 108+ Conseil de l'Europe
- Framework Convention on AI Conseil de l'Europe (mai 2024)
- UNESCO AI & Education guidance (2021, 2023)
- ISO/IEC 27001:2022, 27701:2019, 42001:2023
- RGAA 4.1 (DINUM)
- CARINAE (MEN-DNE)

---

**Avertissement** : document de recherche. Toute decision operationnelle doit etre validee par un avocat specialise data/EdTech (cabinets : Lexing Alain Bensoussan, Haas Avocats, Feral-Schuhl, ou TPE-friendly type Captain Contrat Pro + specialiste ponctuel). Budget avocat phase A : 3-5k EUR. Phase B : 8-15k EUR.

# Rapport d’audit technique — Stages Marrakech AI (mission v2, 17 novembre 2026)

Périmètre : code source complet du dossier `PROJET_FINAL` (backend Flask, passerelle d’authentification, frontend, Dash, SQLite, modules IA, collecteurs, scripts, tests). Le projet original n’a pas été modifié : tout le travail a été fait sur une copie, et la base a été analysée sur une copie (`PRAGMA integrity_check` = ok).

## 1. Synthèse

Le projet était déjà solide : architecture claire, sécurité réfléchie (CSRF, CSP, cookies `SameSite=Strict`, chiffrement Fernet des CV, requêtes SQL paramétrées, migrations sauvegardées) et 192 tests automatisés réussis au départ. Les défauts trouvés portaient surtout sur la performance du matching, sur la robustesse quand des dépendances manquent, sur la duplication de la configuration Gemini et sur des fonctionnalités incomplètes (CV non personnalisable, assistance IA limitée, pas de connecteur Wadifa).

| Priorité | Nombre | Corrigés |
|---|---|---|
| Critique | 0 | — |
| Élevée | 5 | 5 |
| Moyenne | 10 | 10 |
| Faible | 7 | 5 (2 documentés) |

## 2. Architecture constatée

```
auth_gateway/      passerelle multi-utilisateur (inscription, connexion, proxy interne)
backend/           Flask : web.py (app, sécurité), api.py (routes), db.py (migrations),
                   matching.py, assistant.py (chatbot), gemini_*.py, cv_service.py,
                   collectors/ (Jawb, plateformes ATS, fichiers fournis), analytics.py (Dash)
dashboard/         frontend HTML + ui.js (rendu DOM sans innerHTML) + CSS
database/          SQLite privée (292 entreprises, 88 offres, 5 candidatures) + base démo synthétique
scripts/, tests/   outils, 15 fichiers de tests pytest + scénario Playwright
```

Base SQLite (copie analysée) : `user_version` 6, intégrité ok, 0 violation de clé étrangère, 7 index. Tables métier historiques sans clé primaire déclarée (`entreprises`, `offres` : identifiant `ID` rendu unique par index) — conservées telles quelles par choix de non-destruction.

## 3. Défauts identifiés

### Priorité élevée

| # | Domaine | Constat | Correction |
|---|---|---|---|
| E1 | Performance | `matching.cosine()` recalculait les fréquences de **tout** le corpus pour chaque offre (coût quadratique) et `skills_from()` re-normalisait le texte pour chacun des ~130 termes. Mesure : 3,95 s pour classer 88 offres. | Classe `Corpus` (IDF calculé une fois) et motifs regex précompilés : **0,23 s pour 88 offres** (×17), 2,7 s pour 1 056 offres (croissance linéaire). Équivalence numérique vérifiée par test. |
| E2 | Robustesse | Sans Dash/Plotly installés, `create_app()` plantait : **toute** l’application devenait inaccessible. `/api/ai-search/demo` répondait 500 pour la même raison. | Imports Dash/Plotly paresseux ; `/analytics/` renvoie un message 503 explicite, le reste fonctionne. |
| E3 | IA | Aucun service centralisé : liste de modèles codée en dur à deux endroits, client recréé à chaque appel, aucune limitation par minute ni quota quotidien hors Gemini Search, aucun cache. | `backend/services/gemini_service.py` : liste blanche configurable, délai, limitation/minute, quota quotidien persistant, cache, erreurs traduites, journal sans contenu. Chatbot, matching, extraction de profil et Gemini Search l’utilisent. |
| E4 | CV Builder | 2 modèles fixes, couleurs non modifiables, pas de photo, aucune assistance de rédaction. | 5 modèles, 6 palettes + couleurs personnalisées, photo facultative sécurisée, assistant IA à validation explicite. |
| E5 | Collecte | Aucun connecteur Wadifa ; le connecteur Jawb ne vérifiait pas robots.txt et n’était pas planifiable. | `backend/scrapers/` (robots.txt, délai, arrêt sur CAPTCHA/403, qualité des données, staging, revue humaine) + `scripts/run_scrapers.py`. |

### Priorité moyenne

| # | Constat | Correction |
|---|---|---|
| M1 | `get_offer(id)` chargeait et classait toutes les offres pour en trouver une. | Lecture directe par identifiant. |
| M2 | `/api/offres` sans pagination. | Pagination facultative `?page=&per_page=` (réponse toujours une liste, total dans `X-Total-Count`). |
| M3 | Jeton de téléchargement PDF (`/api/cvs/export/<token>`) utilisable par une autre session. | Jeton lié à la session émettrice. |
| M4 | Quotas Gemini Search comptés avec la date **locale** alors que les horodatages sont en UTC (écart autour de minuit). | Date UTC. |
| M5 | Test `test_phase5` dépendant du fuseau horaire (échec entre 21 h et minuit au Brésil/Maroc). | Comparaison en UTC. |
| M6 | Vocabulaire de compétences trop court (40 termes) et faux positifs possibles (« tableau » de bord ≠ logiciel Tableau, « Java » dans « JavaScript »). | ~130 termes (dev, data, gestion, tourisme/hôtellerie…), synonymes, frontières de mots, faux positifs testés. |
| M7 | Localisation des 88 offres absente → composante « localisation » toujours à 0. | Ville déduite du texte de l’offre quand elle y figure, signalée « à vérifier ». |
| M8 | Score de matching peu expliqué (pas de points forts ni de suggestions). | Points forts, suggestions, détail chiffré de chaque composante, libellé de score. |
| M9 | Pas d’index sur les colonnes filtrées (date de publication, statut, CV des candidatures, staging). | Migration `phase10` : index uniquement, sauvegarde préalable, aucune donnée modifiée. |
| M10 | `LANCER_MON_PROJET.bat` et `auth_gateway/launcher.py` forçaient `GEMINI_ENABLED=false` : Gemini était impossible à activer en mode connexion, même avec une clé. | Désactivation forcée conservée uniquement pour le profil démo ; ailleurs, `.env` décide (désactivé par défaut). |

### Priorité faible

| # | Constat | Suite |
|---|---|---|
| F1 | `DELETE /api/alerts/<id>` répondait 204 même si l’alerte n’existait pas. | 404 désormais. |
| F2 | Requête `/favicon.ico` en 404 à chaque page. | Réponse 204. |
| F3 | Pillow utilisé indirectement mais absent de `requirements.txt`. | Ajouté (`Pillow==13.0.0`). |
| F4 | Test d’installation propre à Windows. | Rendu portable. |
| F5 | Listes déroulantes du CV sans nom accessible distinct. | `aria-label` ajoutés. |
| F6 | Colonne `offres.statut_offre` figée au moment de la migration (88 « active »). | Documenté : l’API recalcule la disponibilité à chaque lecture ; la colonne n’est pas modifiée (pas d’écriture sur l’historique). |
| F7 | Données historiques : 0 ville, 0 entreprise liée sur 88 offres, 10 titres en double. | Documenté (qualité de la source) ; aucune donnée inventée pour combler. |

## 4. Points vérifiés sans défaut

- **Injection SQL** : toutes les valeurs sont paramétrées ; les rares identifiants dynamiques proviennent de listes blanches (`candidature()` filtre les clés, tables fixes).
- **XSS** : le frontend construit le DOM sans `innerHTML` (vérifié aussi pour les nouveaux fichiers JS).
- **CSRF / origine** : jeton obligatoire sur toute écriture, refus des origines croisées.
- **Séparation des utilisateurs** : base personnelle par compte en mode multi-utilisateur (tests `test_user_isolation`).
- **Secrets** : `.env`, `private/`, bases et sauvegardes exclus de Git ; aucune clé dans le code (recherche effectuée).
- **Fichiers uploadés** : PDF limités à 5 Mo et 15 pages ; photos décodées/ré-encodées en mémoire, jamais écrites ni exécutées.
- **Fonctionnalités inutilisées** : `dashboard/js/app.js` et `css/style.css` ne sont que des chargeurs ; anciennes aides CV de `ui.js` conservées (inoffensives) pour ne rien supprimer sans validation.

## 5. Ce qui n’a pas pu être vérifié depuis l’environnement d’audit

- **Gemini réel** : aucune clé fournie, SDK `google-genai` non installable (réseau du conteneur coupé). Le contrat du SDK est testé avec des clients simulés ; une vraie requête reste à faire avec `scripts/test_gemini.py`.
- **Dash réel** : Dash/Plotly non installables ici ; 9 tests Dash/SDK sont marqués « ignorés » (pas « réussis »). Ils s’exécutent sur votre `.venv`.
- **Jawb.ma / Wadifa.info** : pages, `robots.txt` et CGU inaccessibles depuis l’environnement d’audit. Voir `docs/CONNECTEURS_JAWB_WADIFA.md`.

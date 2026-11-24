# Mihna — Documentation technique finale

Mihna accompagne la recherche d’opportunités, la préparation du CV et de l’entretien et le suivi des candidatures. L’application est composée d’une interface web, d’une passerelle d’authentification et d’un backend Flask. Les espaces de travail sont stockés dans SQLite.

## Démarrage

Sur une installation Mihna existante, utiliser `INSTALLER_WINDOWS.bat` si l’environnement doit être préparé, puis `LANCER_MON_PROJET.bat`. La passerelle répond sur le port 5000 et communique avec le backend par la boucle locale sur le port 5101. Préserver les bases, les fichiers d’environnement et les éléments nécessaires au déchiffrement des données privées.

Pour une copie neuve du paquet, créer d’abord une démonstration synthétique indépendante. Les commandes suivantes s’exécutent à la racine du projet.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.create_public_demo_database
$env:PORT = '5010'
.\.venv\Scripts\python.exe -m scripts.serve_public_demo
```

Ouvrir `http://127.0.0.1:5010`. Ce profil est en lecture seule et utilise la base synthétique générée. Le parcours avec création de compte, CV et candidatures peut être rejoué par le scénario Edge isolé, qui génère ses propres espaces de test.

## Composants et parcours

| Emplacement | Responsabilité |
|---|---|
| `auth_gateway/app.py`, `proxy.py`, `database.py` | Sessions, inscription, contrôle d’accès, transfert vers le backend et stockage des comptes. |
| `backend/web.py`, `db.py`, `user_data.py` | Assemblage Flask, accès aux ressources, migrations SQLite et sélection de l’espace de travail. |
| `backend/api.py`, `phase11_routes.py`, `ai_routes.py` | Contrats du catalogue, CV, candidatures, entretiens, matching, statistiques et fonctions IA. |
| `backend/collectors/`, `backend/scrapers/` | Adaptateurs, validation de la provenance, normalisation, mise en attente et vérification des doublons. |
| `backend/analytics.py` | Interface Dash, filtres et graphiques dans le contexte de la session. |
| `dashboard/js/ui.js`, `mihna-pages.js` | Construction de l’interface, navigation et affichage des réponses API. |
| `dashboard/js/cv-studio.js`, `career-ai.js` | Édition et export du CV, préparation des candidatures et des entretiens. |
| `scripts/`, `tests/`, `auth_gateway/tests/` | Outils de démarrage, contrôle du navigateur, tests de contrat, régressions et isolation. |

Le [guide technique détaillé](DOCUMENTATION_TECHNIQUE_COMPLETE.md) décrit le flux de chaque parcours. L’[inventaire du code](INVENTAIRE_CODE_ET_ROUTES.md) localise les classes et fonctions. La [référence HTTP](REFERENCE_API_MIHNA.md) recense les méthodes et les chemins du backend, de la passerelle et de Dash.

## Données et configuration

Le schéma SQLite v11 conserve la provenance dans `offres` et `offer_source_identity`. Les relations et les migrations sont décrites dans le [guide SQLite](BASE_DE_DONNEES.md). L’application sélectionne les données personnelles dans la base de l’espace actif et chiffre les contenus pris en charge. Le nettoyage respecte les identifiants d’origine, garde les dates disponibles et laisse les localisations incertaines indéterminées. [ETL](ETL_ET_NETTOYAGE.md) · [Sources, autorisations et couverture](FINAL_DATA_SOURCE_REPORT.md).

Les fichiers d’exemple documentent la configuration. Renseigner les valeurs privées uniquement dans l’environnement d’exécution. Maintenir le mode debug désactivé pour toute instance publiée, protéger la base d’authentification et les secrets de session et utiliser un hôte HTTPS autorisé. Gemini est facultatif. Le matching local reste disponible. La transmission distante exige le consentement pour les enrichissements concernés. Search Grounding reste désactivé.

## Vérification et maintenance

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests auth_gateway/tests -q
.\.venv\Scripts\python.exe scripts/phase12_browser.py
```

En cas d’erreur, vérifier les réponses de santé de la passerelle et du backend puis la connexion. Pour les données, comparer le contexte du compte, les routes et les journaux. Sauvegarder SQLite avant une migration avec un mécanisme cohérent puis vérifier l’intégrité et les clés étrangères. [Tests](FINAL_TEST_RESULTS.md) · [Déploiement et limites](DEPLOYMENT_REPORT.md) · [Guide de soutenance](GUIDE_SOUTENANCE_OFPPT.md).

# Mihna — État du déploiement

## Exécution vérifiée

Le 24 novembre 2026, la passerelle locale sur le port 5000 a répondu à `/health` avec le statut `ok`. La configuration `render.yaml` et le lanceur `scripts/serve_public_demo.py` définissent un profil public isolé avec une base synthétique. La base réelle, les comptes, les espaces privés et leurs sauvegardes restent sur la machine locale.

## Hébergement durable

Render Free efface les modifications du système de fichiers au redémarrage, y compris celles des bases SQLite. Son PostgreSQL gratuit expire après 30 jours. Le profil Render existant convient à une démonstration réinitialisable. [Tarification et limites Render](https://render.com/docs/free).

**Premier candidat pour l’essai de persistance** · alwaysdata Free propose un espace persistant de 1 Go, 256 Mo de RAM et trois jours de sauvegardes pour un usage non commercial. Le service Python WSGI accepte le répertoire, l’environnement virtuel et les variables d’environnement du projet. L’essai doit confirmer la consommation réelle de Flask et Dash, puis la persistance de SQLite et des espaces après redémarrage. Le profil complet avec authentification reste à éprouver dans un compte autorisé. [Offre Free](https://help.alwaysdata.com/en/admin-billing/billing/public-cloud-prices/) · [Déploiement Python](https://help.alwaysdata.com/en/docs/web-hosting/languages/python/configuration/).

Le contrôle local WSGI avec une base synthétique a répondu HTTP 200 sur `/health`, `/api/offres`, `/analytics/`, `/analytics/_dash-layout` et `/analytics/_dash-dependencies`. Le pic mesuré du backend Windows était de 115 Mio après ces requêtes. Les distributions de production installées dans cet environnement représentaient environ 242 Mio, hors Gunicorn, absent sous Windows. Il s’agit d’un point de comparaison pour l’essai Linux. Le profil authentifié exige aussi une passerelle, un backend servi sur une interface privée et des répertoires persistants dédiés.

PythonAnywhere annonce pour ses comptes gratuits une application avec un seul worker, 512 Mio de stockage et un renouvellement mensuel, ainsi que des restrictions sur les connexions sortantes. [Limites du compte gratuit](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/) · [Accès réseau](https://www.pythonanywhere.com/whitelist/).

Fly.io annonce un essai limité dans le temps et en durée d’exécution. Cette offre ne permet pas l’exploitation durable demandée. [Conditions de l’essai Fly.io](https://fly.io/docs/about/free-trial/).

Oracle Cloud Always Free propose du calcul et du stockage persistant et demande une carte pour vérifier l’identité à l’inscription. [Conditions d’accès Oracle](https://www.oracle.com/cloud/free/faq/).

Un jeu de démarrage indépendant contient huit concours Wadifa Info vérifiés. Il a été créé à partir du schéma et des migrations, puis contrôlé pour vérifier l’intégrité, les clés étrangères et l’absence de dossiers personnels. Les identités légales GLEIF sont fournies séparément dans le référentiel du code. La configuration de démonstration synthétique est un profil distinct.

Pour tester cette démonstration locale après extraction du paquet source, générer sa base synthétique puis démarrer le serveur de démonstration avec l’environnement Python du projet.

```powershell
.\.venv\Scripts\python.exe -m scripts.create_public_demo_database
$env:PORT = '5010'
.\.venv\Scripts\python.exe -m scripts.serve_public_demo
```

Le serveur écoute sur `http://127.0.0.1:5010`. La base `database/mihna_catalogue_public.db` est l’amorce à données publiques destinée au futur déploiement persistant. Le mode de démonstration utilise le fichier synthétique `database/stages_marrakech_public_demo.db`.

## Publication

Aucune URL publique de Mihna ni de dépôt GitHub n’a été vérifiée pour cette phase. La publication exige une session disposant des droits sur le dépôt et un environnement d’hébergement compatible avec le périmètre retenu. La procédure de préparation et de publication du code est documentée par [GitHub](https://docs.github.com/en/enterprise-cloud@latest/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github?platform=windows).

# Mihna — Environnement de production

## Entrées et isolation

`auth_gateway.wsgi:app` est l’entrée WSGI de la passerelle. `backend.wsgi:app` sert les API, Dash et les ressources du frontend côté privé. Le backend doit rester inaccessible directement depuis Internet. Le lanceur Windows est destiné à la boucle locale. La validation du profil avec comptes doit couvrir l’origine, les sessions, les limites de requête et les cookies sécurisés derrière le proxy HTTPS.

Python 3.12 et les dépendances de `requirements-production.txt` sont les références de démarrage. Une mesure précédente sur Windows a relevé un pic d’environ 115 Mio pour le backend seul. Elle ne mesure ni la passerelle ni les ressources prises en compte par le plan Linux. Il faut mesurer le démarrage à froid et le parcours Dash sur l’hôte.

La version locale de préparation ajoute `python -m auth_gateway.hosted`, avec l’adresse et le port assignés par le fournisseur comme argument. Le programme héberge uniquement la passerelle sur cette adresse, lie le backend à la boucle locale et exécute un worker par composant. Les bases doivent exister et passer les contrôles SQLite avant le démarrage. Pour la première vérification, préparer une copie de l’amorce de huit concours et une base d’authentification neuve et distincte. Vérifier le plan, les volumes, les permissions et le nombre de proxys réellement traversés sur alwaysdata avant exposition.

## Variables à gérer dans le panneau privé

| Fonction | Noms |
|---|---|
| Passerelle | `AUTH_ENV`, `AUTH_PROFILE`, `AUTH_ALLOWED_HOSTS`, `AUTH_TRUSTED_PROXY_HOPS`, `AUTH_COOKIE_SECURE`, `AUTH_ALLOW_REGISTRATION` |
| Session et canal privé | `AUTH_SESSION_SECRET`, `AUTH_INTERNAL_SECRET`, `AUTH_BACKEND_URL`, `AUTH_DATABASE_URL` |
| Backend | `DATABASE`, `PRIVATE_DIR`, `BACKUP_DIR`, `AUTH_USER_DATA_ROOT`, `AUTH_MULTI_USER_MODE`, `TRUSTED_HOSTS`, `TRUST_PROXY`, `COOKIE_SECURE` |
| Profil SQLite hébergé | `AUTH_PRODUCTION_SQLITE_ROOT`, `AUTH_BACKEND_PORT`, `PUBLIC_DEMO_MODE` |
| Services facultatifs | `DISABLE_BACKGROUND_SCHEDULER`, `GEMINI_ENABLED`, `GEMINI_API_KEY`, `GEMINI_SEARCH_ENABLED`, `SMTP_ENABLED`, `MAPS_ENABLED` |

Le premier essai doit laisser Search Grounding et SMTP désactivés. Les secrets de production appartiennent au panneau privé de l’hébergeur. Le dépôt fournit une amorce publique de huit concours et le script de génération d’une base synthétique distincte. Les données historiques et les comptes locaux ne doivent pas servir d’amorce.

## Stockage, sauvegarde et reprise

Séparer le code versionné des répertoires persistants de données. Avant un transfert ou une migration, arrêter les écritures le temps d’obtenir un ensemble cohérent, effectuer des copies avec l’API de sauvegarde SQLite, puis vérifier chaque copie avec `PRAGMA integrity_check` et `PRAGMA foreign_key_check`. Conserver séparément les éléments privés nécessaires au déchiffrement et les secrets de session associés, avec accès restreint.

Pour restaurer, arrêter le service concerné, mettre de côté son ensemble de données actuel et restaurer les fichiers et éléments de chiffrement correspondants. Tester les permissions et les contrôles SQLite avant redémarrage. Répéter ce scénario sur une copie de test avant d’envisager des données existantes.

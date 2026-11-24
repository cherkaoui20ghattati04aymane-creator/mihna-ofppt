# Mihna — Dépannage de l’hébergement

| Symptôme | Vérification |
|---|---|
| Refus du profil avec inscription en production | Pour la version locale préparée, vérifier le dossier privé persistant, le mode isolé et le backend lié à `127.0.0.1`. Le commit distant antérieur refuse encore ce profil. |
| Refus d’une URL SQLite d’authentification | Vérifier l’activation du profil SQLite explicite et la présence des deux bases dans le dossier privé. Garder la base locale en place. |
| Échec au démarrage WSGI | Consulter les journaux du site, vérifier Python et le répertoire de travail, puis contrôler que l’environnement virtuel installe toutes les exigences. |
| Passerelle sans backend | Vérifier l’accessibilité interne, le secret partagé et l’origine de la requête de santé. |
| Perte d’une donnée après redémarrage | Vérifier le volume, les permissions, le chemin effectif et le verrouillage. Suspendre les écritures publiques avant toute reprise. |
| HTTP 401 ou 403 sur API | Vérifier la session, l’origine, le jeton CSRF, l’hôte autorisé et le protocole vu par le proxy. |
| Dash ou ressources statiques manquantes | Contrôler routes, types MIME, appels Dash, journaux et budget mémoire de l’hôte. |
| Certificat absent ou invalide | Vérifier le nom attribué, le certificat servi et la redirection HTTPS avant toute connexion. |

# Mihna — Évaluation de l’hébergement

## État au 24 novembre 2026

| Élément | Résultat |
|---|---|
| Candidat | alwaysdata Free, usage non commercial, 1 Go de stockage, 256 Mo de RAM, ¼ CPU et trois jours de sauvegardes |
| Coût engagé | 0 EUR. Aucune option payante activée |
| URL Mihna, date de déploiement, HTTPS | Aucun déploiement public effectué |
| Source vérifiée | Branche publique `main`, commit `b8a47ca9c279a243ca2be6ad260de4c1ddfcf13e` |
| Python | 3.12 attendu par le projet. Version de l’espace hébergé non vérifiée |
| Persistance et tests | Redémarrage et séparation vérifiés localement sur une copie isolée. Vérification hébergeur en attente |

Le compte gratuit et la validation de l’adresse ont été annoncés par le propriétaire. L’adresse communiquée était un exemple. Le navigateur affichait encore le consentement de connexion au fournisseur. Le propriétaire doit terminer cette étape et relever l’adresse attribuée dans **Web → Sites**.

## Compatibilité

Le 25 novembre, le propriétaire a retenu PythonAnywhere Beginner comme prochain candidat. Le formulaire Beginner demande un nom d’utilisateur, un courriel et un mot de passe, sans carte. L’offre gratuite fournit un worker, 512 Mio de disque et une expiration mensuelle du site. Le fournisseur propose SQLite mais le déconseille pour une application de production sur le stockage réseau. Le profil à un seul worker est préparé pour un essai isolé. Le compte du propriétaire et le démarrage chez l’hébergeur restent à vérifier. [Inscription Beginner](https://www.pythonanywhere.com/registration/register/beginner/) · [Limites](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/) · [SQLite](https://help.pythonanywhere.com/pages/KindsOfDatabases/).

alwaysdata documente les sites Python WSGI et les programmes web supervisés. Les services autonomes supervisés sont proposés sur les offres payantes. Le plan gratuit mérite un essai pour un programme web unique si l’espace et les limites le permettent. Le fonctionnement de deux composants privés, le verrouillage SQLite et la persistance sur ce compte restent à mesurer. [Offre Free](https://help.alwaysdata.com/en/docs/admin-billing/billing/public-cloud-prices/) · [Python WSGI](https://help.alwaysdata.com/en/docs/web-hosting/languages/python/configuration/) · [Programmes web](https://help.alwaysdata.com/en/docs/web-hosting/sites/http-servers/user-program/) · [Services](https://help.alwaysdata.com/en/docs/web-hosting/services/).

Sans carte ni paiement, alwaysdata applique son mode restreint. Le fournisseur cite notamment un filtrage HTTP renforcé et des limites SMTP. Cela justifie de vérifier le tableau de bord et les routes sur le compte gratuit, avec SMTP désactivé. Aucune levée du mode restreint n’est demandée. [Restrictions du compte](https://help.alwaysdata.com/en/docs/admin-billing/profile/restricted-mode/).

Le commit GitHub vérifié refuse `AUTH_PROFILE=multi_user` avec SQLite en production. Une adaptation locale introduit un profil de production explicite avec SQLite dans un dossier persistant privé. Il conserve la passerelle, le backend de boucle locale et les contrôles HTTPS, d’origine et de session. Le lanceur hébergé supervise les deux processus Gunicorn et contrôle les bases avant démarrage. Le profil reste à vérifier sur Linux et sur le compte alwaysdata. Ces changements ne sont pas déployés.

Render Free utilise un système de fichiers éphémère et sa base PostgreSQL gratuite expire. PythonAnywhere Free offre un worker, 512 Mio de stockage et une expiration mensuelle de l’application gratuite. Il reste une piste de repli pour un essai avec une seule entrée WSGI si sa topologie et ses quotas permettent de maintenir le backend privé. [Render](https://render.com/docs/free) · [PythonAnywhere](https://help.pythonanywhere.com/pages/FreeAccountsFeatures/).

- [Source GitHub](https://github.com/cherkaoui20ghattati04aymane-creator/mihna-ofppt)
- [Environnement](PRODUCTION_ENVIRONMENT.md)
- [Dépannage](HOSTING_TROUBLESHOOTING.md)
- [Vérifications](PRODUCTION_QA_REPORT.md)

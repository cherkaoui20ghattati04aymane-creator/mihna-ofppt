# Mihna — Vérifications avant exposition publique

## Essai isolé du 24 novembre 2026

Une copie du jeu public a démarré derrière une passerelle et un backend locaux. Deux comptes de test distincts ont été créés uniquement dans un répertoire temporaire. L’API a renvoyé HTTP 401 sans session. Le premier compte a enregistré une offre, qui est restée invisible au second. Dash a servi sa disposition. Après arrêt et redémarrage des deux composants, les deux sessions sont restées valides et l’offre enregistrée appartenait toujours au premier compte.

Les copies SQLite du catalogue, de la base d’authentification et des deux espaces ont passé les contrôles d’intégrité et de clés étrangères. Le cas `AUTH_PROFILE=multi_user` en mode production et le stockage SQLite d’authentification en production ont chacun été refusés comme prévu par le commit actuel.

L’adaptation locale du profil SQLite hébergé a passé 39 tests ciblés, dont les tests de non-régression de la passerelle. Une vérification HTTP isolée a confirmé la création de deux comptes, l’attribut Secure des cookies, le contrôle du nom d’hôte, le refus des mutations sans CSRF, l’accès aux pages principales et à Dash, et l’isolation des offres enregistrées. Le superviseur Gunicorn et la persistance sur Linux restent à essayer sur l’hébergeur.

## Contrôles restant à exécuter sur l’hôte

Vérifier le certificat et la redirection HTTPS. Contrôler la page d’accueil, le login, l’inscription, le refus des API hors session et les ressources. Parcourir CV, matching, candidatures, entretien, offres, entreprises et Dash aux tailles mobile et bureau. Vérifier l’isolation entre comptes et la persistance après redémarrage sur une instance isolée avant toute mise en service. Vérifier enfin les journaux et le budget mémoire.

**Production publique non vérifiée.** Les résultats locaux ne constituent pas des résultats de production.

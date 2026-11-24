# Sources marocaines — Vérification du 24 novembre 2026

## Concours publics

L’API de Wadifa Info fournit des concours ouverts, leurs identifiants, les noms des employeurs, les dates et les liens vers les annonces et avis officiels. La licence CC BY 4.0 impose une attribution cliquable vers chaque annonce. L’API ne requiert aucune clé et le fournisseur demande de ne pas dépasser un appel par minute. Le contrôle a utilisé un seul lot de 100 entrées. Les règles des deux hôtes ont été consultées. Le contrôle des avis a porté uniquement sur les pages de détail autorisées, sans téléchargement des pièces. [Documentation de l’API](https://www.wadifa-info.com/developpeurs) · [Règles Wadifa](https://www.wadifa-info.com/robots.txt) · [Règles Emploi-public](https://www.emploi-public.ma/robots.txt).

Huit concours supplémentaires, auprès de huit employeurs distincts, ont été retenus. Chaque URL officielle a renvoyé HTTP 200 et les dates ont été comparées au flux. La vérification HTTP confirme l’accès à la page officielle. Le flux est la source des champs repris. Les identifiants importés sont 177578, 177580, 177582, 177588, 177589, 177593, 177595 et 177605. Le réimport sur copie a ajouté zéro ligne. L’import réel a ajouté huit lignes au catalogue et à l’espace existant. Les lignes antérieures ont été comparées aux sauvegardes et préservées. Les contrôles SQLite d’intégrité et de clés étrangères ont réussi.

La ville et le lien avec une fiche entreprise restent indéterminés pour ces concours. La présence d’un employeur régional dans un concours n’établit pas le lieu d’exercice. Aucun de ces huit concours n’a été compté comme une opportunité physique à Marrakech.

## Catalogue après import

| Source | Offres stockées | Périmètre |
|---|---:|---|
| Himalayas | 188 | Annonces distantes, admissibilité définie par la source |
| Stagiaires.ma | 88 | Historique local, disponibilité actuelle variable |
| Wadifa Info | 28 | Concours publics marocains |
| Jobicy | 20 | Annonces distantes |
| **Total** | **324** | Offres stockées, toutes périodes et tous statuts confondus |

## Autres sources

- GLEIF reste un annuaire d’identités légales. Les 202 fiches marocaines de la précédente vérification n’établissent aucun recrutement. [Rapport des sources entreprises](COMPANY_SOURCE_RESEARCH.md).
- Emploi-public.ma sert de destination officielle pour les avis. La collecte en masse directe reste désactivée.
- ANAPEC, Rekrute, Emploi.ma, Dreamjob et les pages de recrutement régionales demandent une preuve source par source des droits de collecte, stockage et affichage. Aucune nouvelle automatisation n’a été activée pour ces sites.
- Data.gov.ma publie une licence dérivée de l’ODbL qui exige l’attribution et prévoit des obligations de partage à l’identique pour la diffusion de bases adaptées. Les données des ministères, universités et entreprises doivent être examinées à l’échelle de chaque jeu ou flux. Aucun autre jeu d’offres locales n’a été intégré. [Licence du portail](https://www.data.gov.ma/index.php/fr/node/14).
- Remote First Jobs reste exclu pour l’endpoint automatisé documenté dans le [rapport de découverte](SOURCE_DISCOVERY_REPORT.md).

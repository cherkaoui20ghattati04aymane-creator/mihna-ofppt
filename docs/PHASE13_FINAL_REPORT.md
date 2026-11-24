# Mihna — État de la remise OFPPT

| Périmètre | État |
|---|---|
| Import marocain | Huit nouveaux concours Wadifa Info. Le catalogue local contient 324 offres stockées, dont 28 annonces Wadifa Info. L’espace existant a reçu les mêmes lignes. |
| Provenance | Les huit pages officielles ont répondu HTTP 200. L’attribution cliquable a été vérifiée dans le navigateur, en environnement isolé. |
| Intégrité | Les contrôles SQLite ont réussi et les lignes d’avant l’import ont été préservées. Un deuxième passage sur les copies a ajouté zéro ligne. |
| Application locale | La passerelle a répondu à `/health`. Les tests automatisés ont donné 333 réussites et un test Gemini distant désactivé. Edge a vérifié le parcours isolé et 23 pages à trois largeurs. |
| Gemini | Le contrôle local a détecté une configuration valide. Search Grounding est désactivé. |
| Données de Marrakech | Aucun lieu physique de travail à Marrakech n’a été confirmé par ce lot. |
| Compte propriétaire | La vérification de bout en bout du compte privé exige une connexion locale directe du propriétaire. |
| Présentation | Analyse du fichier de référence, PPTX et PDF en attente d’une copie lisible de la référence. |
| Publication | Dépôt distant et plateforme hébergée sans URL vérifiée. |
| Documentation API | Référence HTTP publiée dans le dossier local. Couverture vérifiée sur les cartes de routes Flask du backend et de la passerelle. |

- [Données et provenance](FINAL_DATA_SOURCE_REPORT.md)
- [Documentation technique](DOCUMENTATION_TECHNIQUE_COMPLETE.md)
- [Guide de soutenance](GUIDE_SOUTENANCE_OFPPT.md)
- [Tests](FINAL_TEST_RESULTS.md)
- [Déploiement](DEPLOYMENT_REPORT.md)
- [Validation de la présentation](POWERPOINT_VALIDATION_REPORT.md)

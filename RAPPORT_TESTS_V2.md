# Rapport de tests — avant / après (17 novembre 2026)

Environnement d’audit : Linux, Python 3.13, Flask 3.1.3, pandas 3.0, ReportLab 5.0.1, Pillow 12.3, Chrome + Playwright 1.63. **Dash, Plotly et google-genai n’y sont pas installés** et l’installation de paquets y est bloquée (réseau coupé). Ces limites sont signalées test par test : un test non exécuté n’est jamais compté comme réussi.

## 1. Résultats globaux

| Campagne | Total | Réussis | Échoués | Ignorés (non exécutés) |
|---|---|---|---|---|
| **Avant** (code original, simulateur Dash d’audit) | 202 | 192 | 10 | 0 |
| **Après** (code corrigé, sans simulateur) | 251 | **240** | **0** | 11 |

Les 10 échecs « avant » venaient tous de l’environnement : 5 tests Dash (simulateur), 4 tests du SDK Gemini absent, 1 test d’installation propre à Windows ; plus 1 test dépendant du fuseau horaire (`test_phase5`, corrigé). Sans simulateur, le code original ne démarrait même pas les tests (import de Dash au chargement).

Les 11 éléments ignorés « après » demandent Dash (6 tests + le module `test_analytics_dashboard.py`) ou le SDK google-genai (4 tests). Ils sont marqués `importorskip` et **s’exécutent automatiquement** sur votre ordinateur, où `.venv` contient Dash 4.4.1 et google-genai 2.34.0 : lancez `LANCER_TESTS.bat`.

Les tests de la passerelle d’authentification sont comptés deux fois (fichier d’origine + contrat `tests/test_auth_gateway_contract.py`), comme dans le projet initial.

## 2. Détail par fichier (après)

| Fichier | Réussis | Ignorés |
|---|---|---|
| `auth_gateway/tests/test_gateway.py` (+ contrat) | 66 | 0 |
| `tests/test_application.py` | 62 | 4 (Dash ×3, SDK ×1) |
| `tests/test_mission10.py` (**nouveau**) | 50 | 0 |
| `tests/test_phase5.py` | 19 | 1 (Dash) |
| `tests/test_phase8.py` | 11 | 0 |
| `tests/test_phase9.py` | 10 | 3 (SDK) |
| `tests/test_phase7.py` | 5 | 0 |
| `tests/test_installation.py` | 5 | 0 |
| `tests/test_map_dash.py` | 4 | 1 (Dash) |
| `tests/test_config_paths.py` | 4 | 0 |
| `tests/test_public_demo.py` | 3 | 0 |
| `tests/test_user_isolation.py` | 1 | 1 (Dash) |
| `tests/test_analytics_dashboard.py` | 0 | module entier (Dash) |

## 3. Couverture des 20 fonctionnalités demandées

| # | Fonctionnalité | Statut | Comment |
|---|---|---|---|
| 1 | Démarrage Flask | ✅ testé | `create_app` + `/health`, avec et sans Dash ; serveur réel lancé sur une copie de votre base |
| 2 | Navigation entre pages | ✅ testé | 11 pages ouvertes dans Chrome sans erreur (Playwright) |
| 3 | Login / Register / Logout | ✅ testé | Mot de passe local (tests + Chrome) ; inscription/connexion/déconnexion multi-utilisateur (passerelle, 33 tests) |
| 4 | Sessions | ✅ testé | CSRF, expiration, isolation des comptes, jeton PDF lié à la session |
| 5 | Dashboard et KPI | ✅ testé | `/api/statistiques` ; KPI Dash ⏸ non exécuté ici (Dash absent) |
| 6 | Graphiques Dash et callbacks | ⏸ non exécuté | Dash absent de l’environnement d’audit ; tests prêts, à lancer sur `.venv` |
| 7 | Recherche d’entreprises | ✅ testé | API + page |
| 8 | Recherche d’offres | ✅ testé | API, filtres, page, nouveau bouton « Expliquer / préparer » |
| 9 | Filtres et pagination | ✅ testé | Filtres existants + nouvelle pagination `X-Total-Count` |
| 10 | Matching IA | ✅ testé | Classement, explications, points forts, ville déduite, équivalence IDF, performance mesurée |
| 11 | Chatbot | ✅ testé (local) | Gemini : contrat simulé uniquement |
| 12 | Recherche IA | ✅ testé (local/démo) | Gemini Search : 3 tests ⏸ (SDK absent) |
| 13 | CV Builder et PDF | ✅ testé | 5 modèles × avec/sans photo, A4 vérifié, pagination longue, téléchargement réel dans Chrome |
| 14 | Alertes | ✅ testé | Tests existants + suppression 404 |
| 15 | Carte | ✅ testé | Leaflet local, coordonnées vérifiées seulement |
| 16 | Candidatures | ✅ testé | Création, statuts, historique, doublons |
| 17 | Import CSV et Excel | ✅ testé | Tests existants (phase 7) |
| 18 | Connecteurs externes | ✅ testé (simulé) | Jawb/Wadifa avec serveur simulé : robots.txt, CAPTCHA, 403, redirection, 503, doublons, expirées, import revu. **Aucune requête réelle** vers jawb.ma ou wadifa.info |
| 19 | SQLite et intégrité | ✅ testé | `integrity_check`, migration d’index avec sauvegarde, empreinte de la base originale inchangée |
| 20 | Responsive mobile/desktop | ✅ testé | Chrome 390 px : aucun débordement horizontal (CV, assistant carrière, offres) ; 1440 px |

Cas d’erreur couverts : champs vides, couleurs invalides, palettes inconnues, images GIF/SVG/PDF déguisées/trop petites/trop grosses, fichier `.exe`, données ajoutées après une image (supprimées au ré-encodage), consentement absent ou empreinte périmée, réponses Gemini invalides, chiffres inventés, compétences non justifiées, quota 429, clé refusée, délai dépassé, SDK absent, réseau en panne, page 404/503, robots.txt interdisant le flux.

## 4. Parcours navigateur réel (Chrome, copie de votre base de 88 offres)

31 vérifications réussies, 0 échec, **0 erreur console** :
création du mot de passe · 11 pages · aperçu PDF · changement de modèle et de palette sans perte de données · avertissement de contraste · upload photo vérifié, zoom, forme carrée · suppression de photo · correction IA proposée puis appliquée **seulement** après « Accepter » · analyse du CV (74/100) · optimisation pour une offre · sauvegarde chiffrée · téléchargement du PDF (73 862 octets) · lettre de motivation · entretien · explication d’offre · aide à la candidature · compétences à développer · connecteurs verrouillés par défaut · mobile 390 px sans débordement.

## 5. Contrôles visuels des PDF

Les 5 modèles ont été rendus en image et contrôlés : bandeau (Moderne), ATS sans photo, Élégant deux colonnes avec barre latérale colorée, Minimaliste avec photo à droite, Classique centré. Palettes Bordeaux, Vert, Violet et couleurs personnalisées claires (texte du bandeau basculé en sombre automatiquement pour rester lisible).

## 6. Non exécuté — à faire sur votre ordinateur

1. `LANCER_TESTS.bat` : exécute les 11 tests Dash/SDK ignorés ici.
2. `scripts\test_gemini.py` : **une vraie requête Gemini** avec votre clé (jamais affichée). Gemini n’a pas été testé avec une clé réelle.
3. `scripts\check_sources.py` : lecture des robots.txt de Jawb et Wadifa. Les CGU restent à lire manuellement.

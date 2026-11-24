# Mihna — Final test results

## Phase 13

Lors de la reprise, les cartes Flask ont confirmé que la référence HTTP couvre 95 combinaisons API du backend et 23 combinaisons de la passerelle, hors méthodes implicites et route statique de la passerelle. Le relevé backend a aussi identifié les routes enregistrées par Dash.

| Vérification | Résultat |
|---|---|
| Suite Python et contrats front-end | 333 réussites, 1 test facultatif Gemini distant ignoré, 0 échec, 1 avertissement Dash. Durée 326,67 s. |
| Compilation Python | Réussie pour `backend`, `auth_gateway` et `scripts`. |
| Démarrage WSGI du code de remise | HTTP 200 sur `/health`, `/api/offres` et `/analytics/` avec une base synthétique générée pour le contrôle. |
| Import Wadifa | Huit concours validés et importés. La répétition sur copie a inséré zéro ligne. |
| Interface Wadifa | Huit fiches testées dans Edge avec un compte isolé. Le lien d’attribution a été vérifié sur chacune. |
| Parcours Edge isolé | Inscription, connexion, CV, matching, candidature, entretien, tableau de bord et Dash vérifiés. 23 pages aux largeurs 1280, 820 et 390 px, zéro erreur JavaScript et tuiles OpenStreetMap HTTP 200. |
| Catalogue et espace local | Schéma v11, intégrité et clés étrangères validées. Comparaison des lignes antérieures réussie. |
| Gemini | Configuration locale disponible, Search Grounding désactivé. Le test Google distant est facultatif. |
| Vidéo | Décodage complet FFmpeg réussi. Les images de contrôle montrent les écrans de la session isolée. |

## Phase 12

Run on 24 November 2026 UTC. The normal Windows launcher and the disposable Edge gateway were tested separately.

| Campaign | Result |
|---|---|
| Clean pytest run over `tests` and `auth_gateway/tests` | **333 passed, 1 skipped, 0 failed** in 295.87 s. The skipped test is the opt-in standalone live Gemini call. One upstream Pytest deprecation warning came from Dash |
| Focused post-repair regressions | 39 passed, including mock SMTP authorization, interview resume, and analytics conversion |
| Python and frontend checks | Python compilation, JavaScript syntax checks and frontend contracts in the automated suite |
| Isolated Edge interaction | Registration, invalid password, valid login, logout, protected route, profile save/reload, two CVs, edit and reopen, export, matching and tailoring, application status, draft interview resume and finalization, interview history and dashboard |
| Responsive Edge sweep | 23 pages at each of 1280, 820 and 390 pixels. No page-level horizontal overflow. Zero JavaScript page errors |
| Dash and map | Dash graph rendered against the disposable SQLite workspace. OpenStreetMap tile requests returned HTTP 200 |
| PDF | Original and tailored downloads were valid one-page PDFs. Poppler renders were inspected, including headings, accents, layout, skill text and page number |
| Real application | Official launcher produced HTTP 200 at the login gateway and backend health. Unauthenticated catalog returned HTTP 401 |
| Production preservation | v11 business and workspace databases and the authentication store passed integrity and foreign-key checks. Protected records were unchanged against `backups/phase12_20261124T074710Z/` |

The earlier runs exposed a mocked SMTP scheduler race, an incomplete conversion-variable rename and a harness locator that did not use the matching field's accessible name. The affected tests were repeated after repair. Test writes, fixture credentials and generated PDFs stayed in isolated workspaces.

## Media verification

- Inspected three representative frames of the actual local browser recording. Fully decoded the H.264 stream with FFmpeg.
- The final clip is 212.92 seconds, 1280 × 900 at 24 fps and 4,999,223 bytes.
- The clean test suite and final responsive sweep completed before recording. A redundant native recording retry was stopped after the first capture's completed encoding was found and verified.

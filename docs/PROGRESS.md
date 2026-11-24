# Mihna — Phase 11.2 progress

## A. Inspect the local project
- Checked the launcher configuration, migration sequence, current SQLite schema, source provenance, and both loopback ports.
- The primary and one existing account database were v8. Both passed integrity and foreign-key checks.
- Files changed: none. Owner action: authenticate locally with an existing account for production user testing.

## B. Backup and migrate
- Created verified timestamped SQLite snapshots and rehearsed migrations 9, 10 and 11 before applying them to the two real databases.
- Compared every original table projected onto its original columns, together with existing indexes, before and after migration. Both migrated databases passed integrity and foreign-key checks.
- Files changed: the primary database and one private account workspace. Backups: `backups/phase11_2_20261123T220447837167Z`.

## C. Backend and frontend fixes
- Added redaction to the Phase 11 Gemini payload builder. Tightened account scoping for saved CV selections and made interview feedback use the same CV and offer as the original simulation. Closed SQLite read and backup handles explicitly on Windows. Corrected the launcher status message and Dash navigation assertion.
- Files changed: `backend/{phase11_routes,user_data,db}.py`, `auth_gateway/{app,launcher}.py`, `dashboard/js/{ui,career-ai}.js`, `tests/test_map_dash.py`.
- Checks: Python compilation, JavaScript syntax and pytest reruns.

## D. Redesign eight pages
- Added Profile section navigation, a filterable Applications tracker panel, a directory and map split, and responsive control/result layouts for Matching, Alerts, Data Sources, AI Search and Career Assistant.
- Files changed: `dashboard/js/{ui,career-ai}.js`, `dashboard/css/mihna.css`, `docs/captures/phase11_2/`.
- Browser: the eight pages rendered at 1440, 820 and 390 pixels with no page-level horizontal overflow in the isolated gateway.

## E. Gemini feature checks
- Live requests through the gateway on synthetic data succeeded for gap, roadmap, matching explanation, quality recommendations and interview feedback. Tailoring returned content that failed grounding validation. Interview questions fell back to local.
- Checks: preview, consent rejection, success and fallback paths. Details are in the final report. No owner approval outstanding for the configured model.

## F. Workflow checks
- The isolated browser and API run confirmed original CV preservation, tailored CV reopening, PDF response, application preparation, duplicate prevention, same CV selection in Interview, local interview history reopening and analytics.
- Changed files are listed under C and D. No test record was written into either real workspace.

## G. User interface and runtime checks
- The main launcher started the real application. Its login page and backend health returned HTTP 200.
- Dash graph rendering, OpenStreetMap tile loads and dark theme persistence passed on the isolated gateway. The application PDF preview returned valid PDF bytes in its iframe. Headless Edge did not visually confirm the PDF contents. Added a new-tab PDF link in both application dialogs.
- Owner action: confirm an existing production account login locally.

## H. Final QA
- 324 tests passed, one opt-in Gemini probe skipped. JavaScript syntax and Python compilation checks passed. The focused isolated workflow logged zero JavaScript page errors.
- Owner approvals remain for Wadifa import, duplicate merge, the Himalayas schedule, any new live collection and SMTP. None ran in this phase.

## I. Documentation and delivery
- Updated the required audit, requirements, remaining-work, external services and provenance documents. The delivery archive uses a source allowlist and excludes private data, keys, live databases and backups.
# Phase 11.3 progress

- Verified the real launcher path, active loopback services, schema v11, integrity and foreign keys. Backed up the primary, account and authentication databases and compared the snapshots with their sources.
- Reviewed official Wadifa Info and Himalayas documentation. Imported 20 verified Wadifa records after a dry run. Reviewed all 17 duplicate groups and preserved distinct listings.
- Implemented scheduled Himalayas validation, discovery freshness gating, and source display. No other collector or SMTP was enabled.
- Grounded CV tailoring with extractive source selection and validated Gemini interview output. Verified real responses through isolated application routes. Implemented one bounded retry for transient Google HTTP 500 and 503.
- Removed demonstration controls from normal pages. Verified the eight layouts and isolated account separation, Dash, OpenStreetMap and dark theme. Rendered and inspected original, tailored and four-page CV PDFs.
- Next: record the final Himalayas refresh and regression results, recheck protected production rows, remove this phase's temporary artifacts, and build and verify the ZIP. Existing-account production verification requires the owner's manual login.

- Closed the remaining delivery checks. The first Himalayas batch verified 188 listings and deactivated two. Existing account sign-in and a real company page were confirmed. The private end-to-end production workflow was not fully observed. Focused regressions passed, scratch artifacts were removed, and the final launcher and ZIP were verified.

## Phase 11.5

- Reviewed official Moroccan and remote providers. Imported 20 status-verified Jobicy listings after backup, isolated rehearsal and an idempotency check. Captured 202 public legal identities from two GLEIF API pages and connected company lookup without modifying the company directory.
- Repaired multilingual deduplication, query-aware URL identity, source classification, geographic filters, accessible source selection and provider access-stop behavior. Kept public physical-job portals as manual links when reuse rights were unclear.
- Verified v11 integrity and preservation of the 296 original catalog rows, 292 companies, existing account and personal records. The official launcher started against the 316-offer real catalog.
- Remaining verification: final browser and complete test results, cleanup of phase-only scratch artifacts and verified archive. Future Jobicy scheduled runs remain observable in collection history.

- Final verification passed for Jobicy and GLEIF browser rendering, 15 responsive pages, the isolated CV-to-analytics workflow and 329 automated tests. One opt-in standalone Gemini probe was skipped. Cleaned temporary phase artifacts and verified the ZIP.

## Phase 12

- Rechecked the real catalog, existing account and workspace. Verified v11 backup snapshots at `backups/phase12_20261124T074710Z/`.
- Implemented country persistence, editing the selected original CV, expanded application states and corrected analytics, encrypted interview drafts, and stale matching response protection. Removed the fictitious CV button from normal Studio navigation.
- Added regression tests and a reproducible Edge campaign in `scripts/phase12_browser.py`. Video capture uses Chromium compositor frames, saved after the final verification steps.
- Completed the clean campaign with 333 passed and one opt-in Gemini skip. Edge passed 23 pages at three widths, with zero JavaScript page errors, a rendered Dash graph and HTTP 200 map tiles.
- Captured and fully decoded the 3:33 demonstration. Inspected beginning, middle and end. Packaged the verified MP4, application, tests and reports.
- The real launcher remained available, the protected database comparison passed, and the owner's final private journey remains awaiting local sign-in.

## Phase 13 — Reprise de la remise OFPPT · 24 novembre 2026

- Le dossier `references/` est vide. La recherche locale a retrouvé deux présentations de cours sans lien avec Mihna. La référence, son analyse visuelle, le PPTX, le PDF et le ZIP final attendent le fichier de soutenance demandé.
- Référence HTTP ajoutée à partir des 125 déclarations Flask. Comparaison aux cartes Flask réussie pour 95 combinaisons méthode et chemin API du backend et 23 de la passerelle. Les routes générées par Dash ont également été relevées.
- Passerelle de l’installation existante disponible sur `127.0.0.1:5000`. Le propriétaire a été invité à ouvrir la session directement dans son navigateur. La vérification privée reste en attente.
- Essai d’hébergement local avec une base synthétique et Gemini désactivé. Santé, catalogue, page Dash, disposition et dépendances Dash ont répondu HTTP 200.
- Le dépôt Git local préparé reste en attente d’une destination GitHub autorisée. L’essai alwaysdata exige l’accès à un compte et des vérifications Linux, HTTPS et de persistance. Aucune URL publique vérifiée.

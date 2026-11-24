# Mihna — Technical documentation

## 1. Architecture
```
Browser ──► auth_gateway (Flask, :5000)  login/registration/sessions, CSRF, throttling
               │  loopback + internal secret + X-Internal-User-ID
               ▼
            backend (Flask, :5101, loopback only)
               ├─ /api/*  backend/api.py, ai_routes.py, phase11_routes.py, scraper_routes.py
               ├─ /analytics/  Plotly Dash (backend/analytics.py), per-request user database
               └─ static dashboard (dashboard/*.html shells + ES modules)
            SQLite: database/stages_marrakech.db (admin) · private/user_data/<sha256>.db (one per account)
            Vault (Fernet, private/cv.key): CVs, profile, roadmap, interview history, alert e-mail
```
`LANCER_MON_PROJET.bat` → `scripts/verify_soutenance.py` → `python -m auth_gateway.launcher` (multi-user profile).

## 2. Front end
- 23 HTML shells (`dashboard/*.html`) only set `data-page`; `js/ui.js` builds the shell (sidebar, top bar, page header) and loads `js/mihna-pages.js` (Phase 11 pages) plus `cv-studio.js` and `career-ai.js` lazily.
- Design system: `css/mihna.css` (tokens, layout, components, dark theme, responsive breakpoints 1280/1100/900/640, reduced motion). Widget sheets kept: `studio.css`, `cv-preview.css`, `map-leaflet.css`. `style.css` imports these four only. Older sheets (`design.css`, `mihna-brand.css`, `mihna-system.css`, `phase5.css`, `darbly-brand.css`) are no longer loaded.
- Shared CV choice: `rememberCv`/`preferredCv` (browser localStorage, per offer).
- Pages added in Phase 11: `offre.html` (offer workspace), `sauvegardes.html`, `entreprise.html`, `parcours.html`, `competences.html`, `qualite-cv.html`, `entretiens.html`, `parametres.html`; `statistiques.html` now shows application analytics.

## 3. Phase 11 API (`backend/phase11_routes.py`)
| Method & path | Purpose |
|---|---|
| GET/POST `/api/saved-offers`, DELETE `/api/saved-offers/<offer_id>`, GET `/api/saved-offers/ids` | Saved opportunities (unique per offer) |
| POST `/api/skills-gap` `{cv_id, offer_id}` | Skills gap (local) |
| POST `/api/cv-quality` `{cv_id or cv, offer_id?}` | Transparent CV score |
| GET/PUT `/api/roadmap` `{objective, target_offer_ids, step, done}` | Roadmap (only `learn:`/`proof:` steps can be declared) |
| GET `/api/analytics/applications`, GET `/api/candidatures/export.csv` | Application analytics + CSV |
| GET `/api/companies/overview`, GET `/api/companies/<rowid>/insights` | Company insights from stored facts |
| GET `/api/career/interviews-summary`, GET/DELETE `/api/career/interviews/<id>` | Interview history, reopen, assessment |
| GET `/api/dashboard` | Dashboard summary and recent activity |
| GET `/api/me/export` | Personal data export (JSON) |
| GET `/api/ai/features`, POST `/api/ai/feature/<f>/preview`, POST `/api/ai/feature/<f>` | Gemini enhancements: `gap`, `roadmap`, `quality`, `tailor_summary`, `match_explain` |

Business logic is in `backend/career_features.py` (pure functions, unit-tested).

## 4. Gemini
`backend/services/gemini_service.py` (official `google-genai` SDK): configuration from environment, allowed models, local rate and daily limits, cache keyed by a key fingerprint, error translation (missing key, 401/403, 404 model, 429 quota, timeout). Phase 11 routes add: preview + SHA-256 digest + explicit consent; payload without name/e-mail/phone/links; server-side validation (`_validate_items`: rejects items mentioning skills absent from CV/offer or claiming a missing skill; `_validate_summary`: rejects new skills or numbers). Default model `gemini-3.1-flash-lite`.

## 5. Database
Additive migrations in `backend/db.py`, each preceded by a SQLite online backup; `migrate_all()` runs all of them. Schema versions: … v9 (profile, interview history, consent columns), v10 (tailored CV columns), **v11 (Phase 11): `saved_offers`, `career_roadmap`, `activity_log`**. New tables are personal (listed in `user_data._PERSONAL_TABLES`) and created in every account workspace on first access.

## 6. Security
CSRF on every mutating request; session cookies HttpOnly/SameSite=Strict; per-account database selected by the gateway; encrypted personal payloads; no secret in front-end code; Gemini key never returned by any endpoint; e-mail rule: "No email is sent without active SMTP, recorded user consent, and a genuinely new matching opportunity."

## 7. Tests
`pytest` (312 passed, 12 skipped in the isolated environment — skips: Dash and google-genai not installable there; real Gemini test opt-in with `RUN_GEMINI_REAL_TEST=1`). Phase 11 tests: `tests/test_phase11_features.py`; front-end contract and ES-module syntax: `tests/test_phase10_frontend_contract.py`. Browser checks were run with Playwright against an isolated sandbox (scripts not shipped; see reports).

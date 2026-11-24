# Mihna — Phase 11.3 final report

## Delivery and production checks

**PARTIALLY COMPLETED.** The Windows launcher runs the existing Mihna application against the real SQLite catalog. The existing account opened a new authenticated session and a real localhost company detail page. The full private production workflow was not observed.

| Item | Evidence |
|---|---|
| Real catalog | `database/stages_marrakech.db`, schema v11 |
| Existing workspace | One separate v11 SQLite workspace under `private/user_data/` |
| Authentication store | `auth_gateway/data/auth_users.db`, one existing account. All account rows, including roles and password hashes, matched the pre-phase backup |
| Verified backups | `backups/phase11_3_20261124T065144Z/`. Compared all rows in each snapshot to its source and checked integrity and foreign keys before import |
| Production runtime | `LANCER_MON_PROJET.bat` verified the real path, the absence of a demo marker and 296 offers. The login gateway on port 5000 and private backend on 5101 both returned HTTP 200. Anonymous catalog access returned 401 |
| After import | Production 292 companies, 296 offers, 6 applications, 2 CVs. Existing account workspace 292 companies, 296 offers. 20 shared real opportunities added per catalog |

## Data sources

- **COMPLETED AND VERIFIED ON REAL PROJECT** · Wadifa Info. Matched all 20 staged records to one current API response on title, employer, publication date, deadline and both URLs. All 20 official HTTPS notice URLs returned HTTP 200 without a redirect. Previewed and rehearsed the import, checked repeat import inserted zero rows, then applied the same batch to the historical catalog and the existing workspace. The source and official links are separate. Missing descriptions and cities were left unavailable. Dates and posts should be checked against the linked official notices.
- **COMPLETED AND VERIFIED ON REAL PROJECT** · Duplicate review. All 17 groups had distinct listing and application URLs. Some descriptions matched, but publication dates or URLs and source identities differed. No group met the merge criterion.
- **Himalayas** · The local launcher starts a daily freshness worker that shares checks across account workspaces, backs up databases before updates, stops a batch on source errors and deactivates closed or absent listings without deleting them. Stale listings are withheld from discovery and applications until reverified. The worker runs while the launcher is open. The first live run checked all 188 distinct listings and deactivated two in both catalogs. Both databases passed SQLite integrity and foreign-key checks afterward.
- **BLOCKED** · Verified physical Marrakech opportunities. The existing historical records and authorized imports contain no confirmed physical Marrakech listing. No further source was reused without permission. SMTP stayed disabled.
- Source terms and attribution references are in [the service matrix](API_AND_EXTERNAL_SERVICES_MATRIX.md).

## Gemini and isolated workflows

All six features used the actual Flask routes through the local gateway, with a temporary SQLite database, synthetic personal inputs and the configured `gemini-3.5-flash-lite` model. CV Quality scores and Skills Gap counts still use local rules. Recommendations, questions and feedback are labeled separately.

| Feature | Live result |
|---|---|
| CV Quality recommendations | Successful |
| Skills Gap recommendations | Successful |
| Career Roadmap advice | First pass fell back. Successful on the focused run after an HTTP 503 and one bounded retry |
| Matching Explanations | First pass fell back. Successful on the focused run |
| CV Tailoring | Successful. Gemini selected passage IDs. Mihna reconstructed the summary from the selected CV's exact text and independently rejected any invalid or repeated IDs. The isolated tailored CV was saved and reopened with its original CV and offer references |
| AI Interview | First questions request fell back. The focused questions request and the live feedback request succeeded |

Consent and digest checks were exercised through application endpoints. An independent browser account was denied access to the first account's CV. Production private data was kept out of live Gemini tests. Persisting AI interview feedback on a real account and visually checking every AI result in the production session remain unverified.

## Browser and PDF

The eight requested pages rendered at widths 1440, 820 and 390 in an isolated Edge session without page-level horizontal overflow. Dash rendered a graph, visible OpenStreetMap tiles returned HTTP 200, and the dark theme persisted after reload. No JavaScript page errors were observed. Production UI no longer exposes the demonstration CV, map pins or fake search and collection controls.

Rendered and visually inspected the original and tailored one-page PDFs and a separate four-page pagination case. Headers, sections, skills, dates and footers were legible. The pagination case retained all ten entries and showed no clipping or lost text. All rendered files were temporary.

## Regression and delivery checks

- The full suite reported 323 passed, one opt-in standalone live test skipped, and one stale-date fixture failure. The expectation now uses a fresh verification timestamp, and the focused rerun passed all 54 tests including that regression. Live Gemini evidence above comes from application requests.
- Rechecked both real catalog databases and the authentication database after refresh. All returned SQLite integrity `ok` and zero foreign-key violations. Original offer rows, company rows and protected production records were compared with the backup. The only catalog changes were 20 verified inserts and the intended Himalayas freshness fields. The existing account had normal owner activity during the run.
- Removed the temporary PDFs and renders, browser harnesses, current-source scratch files and test SQLite directories created during this phase. Prior documentation, reusable tests and verified backups remain in the workspace.
- Final build restarted on the official launcher. Both loopback HTTP checks returned 200.

## Remaining owner actions

- If production acceptance requires every private page to be observed, continue from the signed-in account with the existing saved records and analytics.
- Obtain an authorized source of verified physical Marrakech opportunities if that facet needs real listings.
- Configure approved SMTP if needed and keep per-user revocable consent mandatory. No email was sent during this phase.

The final archive is an update for the existing project directory. It contains the application and reports without local credentials, private databases, backups, installed dependencies, or generated test artifacts. Keep the existing real database and environment when applying it.

# Mihna — API and external services matrix

## Phase 11.3 current status

| Source | Status | Phase 11.3 evidence |
|---|---|---|
| Wadifa Info | OPERATIONAL | Free, read-only and keyless, at most one request per minute. Current feed and 20 official URLs verified. CC BY 4.0 and visible per-item attribution. [Official developer documentation](https://www.wadifa-info.com/developpeurs) |
| Himalayas | OPERATIONAL WITH CONDITIONS | Free public API, with optional higher-limit key. The status endpoint is used at less than 60 requests per minute. Daily freshness, source credit and API application links required. The local launcher checked 188 rows and deactivated two. [Official Jobs API reference](https://himalayas.app/docs/remote-jobs-api) |
| Google Gemini | OPERATIONAL | Real application requests on synthetic isolated data succeeded for all six feature areas. The launcher's configured model remains gemini-3.5-flash-lite |
| SMTP | BLOCKED | Disabled. Requires approved credentials and recorded, revocable consent |

Other source restrictions from the previous matrix still apply.

[Phase 11.3 final report](PHASE11_3_FINAL_REPORT.md)

## Phase 11.2 local status

| Source or service | Status | Evidence and scope |
|---|---|---|
| Google Gemini API | OPERATIONAL | Local model configured as `gemini-3.5-flash-lite`. Feature outcomes are in the Phase 11.2 report |
| Gemini Search Grounding | NEEDS APPROVAL | Separate cost confirmation and authorization for live discovery |
| Himalayas | AUTHORIZED WITH CONDITIONS | 188 stored remote offers. Daily freshness check requires owner approval |
| Wadifa Info | NEEDS APPROVAL | Staging documented. No offer in the primary SQLite source table |
| data.gov.ma recruitment statistics | NOT IMPLEMENTED | Candidate source for aggregate context |
| OpenStreetMap and Leaflet | OPERATIONAL | Map client is wired. Consult Phase 11.2 browser results for live tile evidence |
| GLEIF | NOT IMPLEMENTED | Candidate identity reference |
| Jawb.ma | BLOCKED | Connector disabled pending storage and display authorization |
| Stagiaires.ma | BLOCKED | 88 private historical records. New collection requires reuse permission |
| ANAPEC, Emploi-public.ma, OFPPT, UCA | BLOCKED | Written authorization required for automated reuse |
| Remotive | BLOCKED | Third-party aggregation restriction recorded in source review |
| Jobicy and Remote OK | NOT IMPLEMENTED | Candidates without an adopted connector |
| Adzuna | BLOCKED | Commercial licence required for intended use |
| Google Places / Maps Platform | BLOCKED | Disabled in local launcher |
| SMTP | NEEDS APPROVAL | Disabled in local launcher. Requires provider configuration and explicit consent |

The figures and terms below are from the previous source review. The v8 to v11 migration is complete. The configured Gemini model above supersedes the earlier setup example.

## Phase 11 historical record

**Date:** 23 November 2026. Rule applied: free and official sources first; a public endpoint is **not** treated as permission to store or redistribute; no paid service; no scraping of restricted sites; no new live collection or import without your authorisation.

Legend — Recommendation: **USE** (integrated or should be), **OPTIONAL** (useful, needs your decision or configuration), **NOT RECOMMENDED**.

| # | Service | Official site | Exact purpose in Mihna | Cost / free-tier limits | Key? | Registration? | Data provided | Morocco / Marrakech coverage | Licence & terms | Store & display permitted? | Rate limits | Complexity | Free alternative | Recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Google Gemini API** | ai.google.dev | AI assistance (tailored summary, gap/roadmap/quality recommendations, matching explanation, interview feedback, career assistant) — always optional, after preview and consent | Free tier exists for several models; `gemini-3.1-flash-lite` is listed "free of charge" for input and output. Free-tier content **may be used to improve Google products** | Yes (AI Studio key) | Yes (Google account) | Generated text | Global | Gemini API terms | Outputs are shown to the user only; nothing stored except interview feedback the user saves | Per project, visible in AI Studio; daily quota resets at midnight Pacific | Done (reusable service + consent + validation) | Local rules (already built) | **USE** (configured locally by you) |
| 2 | **Himalayas Remote Jobs API** | himalayas.app/docs/remote-jobs-api | Remote jobs, with an explicit "Morocco eligible" flag | Free; no key required; optional free key gives 60 req/min and 10 000/day | No (optional) | Optional | Job title, employer, description, eligibility countries, `applicationLink`, dates | Remote jobs open to Morocco (125 imported) and worldwide (63) — **0 physical Marrakech jobs** | Display on your own app allowed with visible credit and link to himalayas.app; apply via `applicationLink`; **do not pass jobs to other boards/Google Jobs** | Yes for display in Mihna; **must re-read daily and remove closed jobs** | Public shared allowance; data refreshed every 24 h | Done (connector + import) | — | **USE** — needs a daily status check (approval required, see remaining work) |
| 3 | **Wadifa Info API** | wadifa-info.com/developpeurs | Moroccan public-sector recruitment exams (concours) | Free, read-only JSON, no key | No | No | Exam title, employer, deadline, official notice link, number of posts | Morocco, public sector; city often missing | CC BY 4.0 (attribution required) | Yes, with attribution | "Updated hourly, safe to cache" | Done (staging; 20 records staged) | data.gov.ma statistics (aggregate only) | **USE** — import of the 20 staged records awaits your approval |
| 4 | **data.gov.ma** (national open-data portal) | data.gov.ma | Aggregate statistics on public-sector recruitment (Emploi-public dataset) | Free | No | No | Excel/CSV statistics, **not listings** | Morocco | Dataset-specific (Emploi-public statistics dataset: ODbL) | Yes per dataset licence (ODbL share-alike) | n/a | Low (file download) | — | OPTIONAL (context charts only) |
| 5 | **OpenStreetMap tiles + Leaflet** | operations.osmfoundation.org/policies/tiles | Map background on the Carte page | Free, best effort, no SLA | No | No | Raster tiles | Global | Visible attribution; valid User-Agent/Referer; no bulk download, no prefetching/offline | Tiles are displayed, not stored | Fair use; may be blocked without notice | Done | Self-hosted tiles | **USE** (small interactive map only) |
| 6 | **GLEIF LEI API** | gleif.org | Exact company identity check (legal name, LEI) | Free | No | No | Legal entities | ~200 Moroccan LEIs; few local SMEs | CC0 | Yes | Generous | Low | — | OPTIONAL (does not prove hiring or local office) |
| 7 | **Jawb.ma feeds** | jawb.ma | Moroccan job listings (connector code exists, disabled) | Free to read | No | — | Listings | Morocco incl. Marrakech | Storage/re-display permission **not established** | **No** without written permission | — | Done but disabled | — | NOT RECOMMENDED until written permission |
| 8 | **Stagiaires.ma** | stagiaires.ma | Source of 88 historical internship rows | — | — | — | Listings | Morocco | No documented redistribution permission | Keep as historical private data only; do not extend | — | — | — | NOT RECOMMENDED for new collection |
| 9 | **ANAPEC, Emploi-public.ma, OFPPT, UCA Career Center** | official sites | Real Marrakech/Morocco offers and internships | Free to read | — | — | Listings | Strong Morocco / Marrakech relevance | No public reuse feed verified | Only with written agreement | — | Medium | — | OPTIONAL — request access (contacts in `OFFICIAL_DATA_ACCESS_CONTACTS.md`) |
| 10 | **Remotive** | remotive.com | Remote jobs | Free | No | No | Listings | Remote | Terms block third-party aggregation | No | — | — | Himalayas | NOT RECOMMENDED |
| 11 | **Jobicy / Remote OK** | jobicy.com / remoteok.com | Remote jobs | Free | No | No | Listings | 0 Morocco results observed | Attribution | Yes with attribution | — | Low | Himalayas | OPTIONAL (low value for Morocco) |
| 12 | **Adzuna** | adzuna.com | Job search API | Free trial only; ongoing use needs a licence | Yes | Yes | Listings | Limited | Commercial licence | Not without licence | — | — | — | NOT RECOMMENDED (paid) |
| 13 | **Google Places / Maps Platform** | developers.google.com/maps | Company geocoding (code path exists, disabled) | Paid beyond credits; billing account required | Yes | Yes + billing | Places, coordinates | Good | Google terms restrict storage | Limited | Quotas | — | Manual verified coordinates | NOT RECOMMENDED (paid, storage limits) |
| 14 | **SMTP (your mail provider)** | — | Optional alert e-mails | Provider-dependent | Credentials | Yes | — | — | Your provider's terms | — | Provider limits | Done (disabled) | In-app alerts | OPTIONAL — stays off unless you configure and approve |

## What you must configure or provide

1. **Gemini (to enable AI features):** in your local `.env` only — `GEMINI_ENABLED=true`, `GEMINI_API_KEY=<your key>`, `GEMINI_FREE_TIER_CONFIRMED=true` (after checking your quota in Google AI Studio), keep `GEMINI_MODEL=gemini-3.1-flash-lite`. Then run `TESTER_GEMINI.bat`. See `GEMINI_SETUP_GUIDE.md`. Never paste the key in a chat, a document or source code.
2. **Approval** for: (a) the database migration v8 → v11, (b) a daily Himalayas status check (network calls) to remove closed jobs, (c) importing the 20 staged Wadifa public-sector competitions.
3. **Nothing else is required** to use Mihna locally. SMTP, Jawb and Google Places stay disabled.
4. Optional: written data-access requests to ANAPEC / Emploi-public / UCA for real physical Marrakech offers.

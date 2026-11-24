# Mihna — Data sources and provenance

## Phase 11.3 current status

The real v11 catalog contains 296 offers. Himalayas accounts for 188 (including two closed or absent listings deactivated on 24 November), Stagiaires.ma accounts for 88 historical entries, and Wadifa Info accounts for 20 verified public-sector records. All original offer rows and existing company entries were preserved. The refresh updates status, timestamp and the API application link when returned. It does not change titles, employers, descriptions or original listing URLs. No confirmed physical Marrakech offer was imported.

[Phase 11.3 final report](PHASE11_3_FINAL_REPORT.md)

## Phase 11.2 read-only snapshot

Primary database schema v11. Integrity `ok`, zero SQLite foreign-key violations and zero verified offer-to-company references. The directory has 292 companies and zero coordinate pairs. The database contains 276 offers, including 188 Himalayas and 88 historical Stagiaires.ma records. Based on stored expiry dates, 275 were active and 1 expired at inspection time.

All offers had a title, description, publication date, expiration date, source, and usable application URL. The 88 historical entries lacked structured attribution metadata. The review found 17 possible duplicate groups by title, company and source, with zero duplicate application URLs. The migration left these records unchanged. The generic location classifier reports unknown for all offers; the discovery view uses structured Himalayas source metadata for its remote facets. Historical text mentions are displayed as unverified. No new source was collected or imported.

See the Phase 11 snapshot below for historical source notes and the [external services matrix](API_AND_EXTERNAL_SERVICES_MATRIX.md) for authorization status.

## Phase 11 historical record

**Snapshot:** 23 November 2026, read-only inspection of a copy of `database/stages_marrakech.db` (schema v8, integrity `ok`).

## 1. Offers (276)
| Source | Rows | How obtained | Location classification | Attribution / rights | Freshness |
|---|---|---|---|---|---|
| Himalayas Remote Jobs API | 188 | Phase 7 import (status-checked, HTTP 200) | 125 remote with Morocco explicitly eligible; 63 worldwide remote (Morocco not separately confirmed) | Display allowed in Mihna with visible Himalayas credit + link; apply via `applicationLink`; no redistribution to other boards | Collected 23/11/2026. Terms require re-reading daily and removing closed jobs — **daily check not yet authorised** |
| Stagiaires.ma (historical) | 88 | Earlier project phases | No structured city; 63 mention "Marrakech" in text (shown as "Marrakech mentionné · lieu non vérifié") | **No documented redistribution permission** — private historical data | Published Aug–Sep 2026; expiry dates from the source; not re-verified |
| Wadifa Info (public sector) | 0 imported (20 staged) | Phase 7 staging | Public sector; cities missing | CC BY 4.0 | Awaiting your import approval |

- Physical jobs verified in Marrakech: **0**. Physical jobs verified elsewhere in Morocco: **0**. Alternance listings detected by keyword: shown in the type filter when present.
- Every offer keeps `source`, original links (`Lien public` / `Lien annonce`), `collected_at`, `last_verified_at`, and `source_metadata_json` (Himalayas id, eligibility, attribution).
- Duplicates: offer links are unique; 17 groups share title + company + source (e.g. 9 identical "Client Account Manager – Finch" postings). Flagged, not merged — merging needs your approval.

## 2. Companies (292)
Historical directory (sectors: Informatique 98, Autre 83, Hôtellerie 22, Tourisme 19, Construction 18, …). 236 with a website field, 145 with an e-mail field, 0 with verified coordinates, no per-row provenance column. Company pages show only these stored fields; size, revenue and ratings are explicitly "not available". Offer ↔ company links: only exact reference or identical normalised name; none are guessed (currently 0 matches).

## 3. Personal data
Profiles, CVs, roadmaps, interviews and alert e-mail addresses are encrypted per account. Applications, saved offers and activity logs live in each account's private SQLite file. Exports: JSON (all personal data) and CSV (applications).

## 4. Data quality controls in the product
Location honesty labels, availability from expiry dates, source badges, "Source non renseignée" instead of guesses, duplicate prevention for saved offers and tailored CVs, `INSERT OR IGNORE` for alert e-mail logs, collection centre with preview/approval before import.

## 5. Sources requiring permission before use
Daily Himalayas status check (network), Wadifa import, Jawb.ma (written permission), ANAPEC / Emploi-public / OFPPT / UCA (written agreements), any new Stagiaires.ma collection (permission needed).

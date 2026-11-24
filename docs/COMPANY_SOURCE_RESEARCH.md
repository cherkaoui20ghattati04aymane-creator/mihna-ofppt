# StageX — company identity source research

**Reviewed:** 23 November 2026. This document distinguishes legal identity data from employer/hiring evidence.

## GLEIF (global legal entity reference)

- **Official source:** [GLEIF API](https://www.gleif.org/en/lei-data/gleif-api); [access and use terms](https://www.gleif.org/en/meta/lei-data-terms-of-use).
- **Access / cost:** Public REST API, no key for the bounded query used; free access and CC0 1.0 LEI reference data.
- **Data fields:** Legal entity name, LEI, legal address and entity/registration status where the source provides them. It is not a company website, logo, sector, career page, or hiring feed.
- **Test:** One failed Marrakech city-filter request (HTTP 400); two bounded `country=MA&page[size]=3` requests (HTTP 200). Each successful response contained the same three-record sample; API metadata reported 215 Morocco LEI records. No record passed the Phase 7 verified general-entity/name filter for staging.
- **Permission:** Public CC0 terms; attribution retained for clarity. Records must not be misrepresented as job activity or an operating local office.
- **Status:** **0 records staged; 0 imported.** No job association was made.
- **Next action:** For any later identity match, require a source LEI or other exact legal identifier in both records, then compare legal entity jurisdiction/name/status. A name resemblance is insufficient.

## OMPIC / DirectInfo / public beneficial-ownership register

- **Official source:** [OMPIC DirectInfo](https://www.directinfo.ma/); [OMPIC beneficial-ownership register notice](https://rbe.ompic.ma/assets/doc/Note%20information.pdf).
- **Access / cost:** Official commercial-register information is provided through paid information services. Public beneficial-ownership data require a request and applicable fees.
- **Public API/RSS/open export:** No free, general-purpose, reusable company API/export license was verified.
- **Permission:** No StageX permission or redistribution license exists.
- **Status:** Not queried, scraped, stored, or imported. Excluded by the no-paid-data condition.
- **Next action:** None unless OMPIC supplies free written access and explicit reuse/display terms.

## OpenStreetMap / Nominatim

- **Official license:** OSM data is available under ODbL 1.0 with attribution and share-alike obligations. The OSM Foundation requires the attribution and ODbL notice for a distributed database.
- **Public Nominatim service:** [usage policy](https://operations.osmfoundation.org/policies/nominatim/) limits use to at most one request per second, requires an identifying User-Agent and visible attribution, discourages bulk geocoding, and forbids systematic queries that download complete POI lists.
- **Morocco relevance:** OSM may contain mapped businesses, addresses, and websites, including in Marrakech. Completeness and legal-entity identity are not guaranteed.
- **Status:** No Nominatim/Overpass business-list query was made. The public lookup API is not a permitted substitute for systematically harvesting a Marrakech company directory.
- **Next action:** If a selected OSM extract is considered later, first define the ODbL share-alike implications for StageX's private database and public display; use only an appropriate, bounded extract and preserve OSM IDs, source links, edit dates, and required license notices.

## Open Data Maroc / HCP

- Official open-data catalogues and HCP datasets provide public indicators and statistical datasets, subject to each dataset's license.
- No free licensed dataset of individual Moroccan employers with verified websites/careers contacts or hiring status was identified in this review.
- Aggregate statistics are not employer identity records and will not be inserted into `entreprises`.

## Official company career sites and ATS boards

Employer-owned Greenhouse, Lever, Ashby, and SmartRecruiters feeds can expose vacancies for a named employer, but the vendor endpoint alone does not grant StageX rights to re-display or store that employer's content. No company-level permissioned board was newly queried or imported in this phase.

## Decision

Only GLEIF met a clear free reuse license, but the bounded sample produced no qualifying company staging records. OMPIC data were excluded as paid, and no systematic OSM POI harvesting was performed. Company identity enrichment and job discovery remain separate; **company registration or a mapped business is never hiring evidence**.

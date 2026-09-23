# Chicago building research: 1875

## Scope and method

This tranche records named buildings, building groups, and infrastructure projects with a documented 1875 construction, completion, opening, reconstruction, conversion, or active multi-year phase. It combines a near-contemporary city history with City of Chicago landmark/survey data, official proceedings, National Register documentation, institutional histories, archival abstracts, and a contemporary newspaper transcription. Every database row has at least one foreign-keyed source in `year_1875_sources.csv`.

The file is an evidence-backed named-property inventory, not proof that every ordinary structure erected in Chicago in 1875 has been individually identified. Nineteenth-century permits, assessment records, directories, and newspaper building notices are not yet fully digitized or indexed, and the Chicago Historic Resources Survey describes survivors rather than the complete historical building stock. The CHRS search returned 785 records dated broadly to the 1870s; most cannot be assigned to 1875 without permit or property-history corroboration.

## Delivered dataset

- 38 event/property records in `year_1875_buildings.csv`.
- 25 source records in `year_1875_sources.csv`: 14 Tier 1 and 11 Tier 2.
- 29-column building schema and 12-column source schema, both matching `YEAR_SCHEMA.md`.
- All IDs are unique, all source foreign keys resolve, every record has a source, and controlled `confidence`/`needs_review` values pass strict CSV parsing.

## Statistics

| Measure | Count |
| --- | ---: |
| Records | 38 |
| High confidence | 27 |
| Medium confidence | 11 |
| Review flagged | 20 |
| Not review flagged | 18 |
| Completion year recorded as 1875 | 31 |
| Completion year recorded as 1876 | 6 |
| Completion year recorded as 1877 | 1 |
| Exact completion precision | 29 |
| Exact 1875 completions | 25 |
| Fiscal-year completion reports | 4 |
| Extant/extant-altered/extant-relocated | 15 |
| Demolished/replaced/unknown demolition | 23 |
| Rows with latitude and longitude | 17 |

Inventory rows are construction events or grouped properties, so they are not equivalent to a physical-building count. The three row-house records represent 35 documented dwellings (10 Burling, 20 Fremont, and five Lincoln Avenue addresses), while the Cook County Hospital entry represents two medical pavilions. Those quantified groups bring the represented minimum to 71 named physical structures/components, plus an unquantified program of several brick bridge houses.

## Important corrections and identity controls

- Chicago Avenue Church was still under construction in 1875 and was completed/dedicated in 1876. It is included as a continuing-construction event, not a 1875 completion.
- The First Baptist main church at 31st Street and South Park was begun in 1874 and completed in 1875 by Willcox and Miller; sources also describe the attached Sunday-school portion as 1876.
- Kehillath Anshe Maarabh's Indiana Avenue/26th Street temple was dedicated February 5, 1875. It is not the 1890-91 KAM building later occupied by Pilgrim Baptist Church.
- Sinai Temple at 21st Street and Indiana Avenue is a separate 1875-76 project whose April 1876 dedication is documented in congregation minutes and a contemporary German-language press abstract.
- The surviving Union Stock Yard Gate is dated circa 1875 and must not be conflated with the stockyard's original 1865 entrance complex.
- The official Haskell-Barker-Atwater grouping spans 1875-77, but City Council documentation separates the Haskell and Barker buildings as 1875 work and the Atwater Building as 1877.
- Four public-works rows are retained as fiscal-year reports ending March 31, 1875. Their exact calendar-year completion must be checked in contract ledgers before treating them as exact 1875 completions.

## Coverage by property type

The inventory includes religious buildings and schools; public school and hospital construction; mansions, houses, and grouped row houses; mercantile lofts and a store-and-flat; stockyard, railroad, grain, brewery, and newspaper facilities; bridges, viaducts, and bridge-house work; and one theatre conversion. This breadth helps model rebuilding-era land use, but ordinary residential and small commercial work remains underrepresented because surviving landmark inventories strongly select for notable and extant properties.

## Map and image research

- The Warner & Beers 1875 map is cataloged as `MAP_1875_WB` and the public-domain scan is already stored at `work/final/chicago/postfire_1870s_v1/maps/images/1875_warner_beers_map.jpg`. It is suitable as the 1875 annual-map base, with source credit preserved.
- City landmark pages, the Chicago Architecture Center, parish/institutional pages, and Preservation Chicago contain useful building photographs, but those images were not copied because reuse rights require item-level verification.
- National Register catalog metadata and federal nomination text can generally be reused as federal records; individual historic photographs may carry separate restrictions and should be checked before redistribution.
- Wikimedia Commons categories for surviving buildings can supply additional images only after recording each file's author, license, source URL, and attribution text.

## Remaining research queue

1. Chicago building-permit ledgers (1872-1911), especially the UIC/municipal series, to enumerate ordinary houses, flats, stores, barns, factories, additions, and repairs.
2. Board of Public Works annual reports, contract ledgers, and bridge-engineer records to resolve fiscal-year ambiguity and identify every 1875 bridge house.
3. Board of Education proceedings and school annual reports for public-school construction and additions.
4. Archdiocesan, Protestant denominational, and Jewish congregational minutes for exact construction starts, architects, contractors, and dedication dates.
5. Railroad valuation maps, freight-house lists, elevator records, Sanborn predecessors, tax assessment books, and city directories for industrial/commercial sites.
6. Microfilm verification of Chicago Tribune and other daily-paper building notices, including the Cyrus McCormick mansion transcription.
7. Property-by-property review of the 785 broadly dated CHRS candidates to extract permit numbers and distinguish 1875 work from decade-only estimates.

Aggregate annual building-stock estimates belong in the decade-level `annual_stock_estimates.csv` and are intentionally not duplicated as named-building rows here.

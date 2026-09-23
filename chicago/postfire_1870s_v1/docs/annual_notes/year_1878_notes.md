# Chicago building research — calendar year 1878

## Scope and result

This annual tranche records named Chicago structures that were completed in 1878 or had a distinct, materially documented construction, reconstruction, conversion, addition, or infrastructure phase during 1878. It follows `YEAR_SCHEMA.md` and is designed for later normalization into the longitudinal Chicago buildings database.

The named inventory contains **28 records**. It is comprehensive with respect to the identifiable 1878 structures found in the sources reviewed for this tranche, but it is not presented as a census of all 1,019 buildings represented by city permits. The surviving published aggregate does not disclose 1,019 identities, so manufacturing anonymous building rows would create false certainty.

## Method

- Searched the full OCR of A. T. Andreas, *History of Chicago*, volume III, for 1878 construction language, then read surrounding passages rather than accepting isolated OCR hits.
- Reconciled projects that began in 1876-77 and completed in 1878, especially St. Joseph's Church and the North and Fullerton Avenue bridges.
- Used the 1878 citywide permit table only as aggregate flow evidence.
- Added projects from a scholarly architect work list whose entries cite specific contemporary *Chicago Tribune* notices: the Campbell residence, Chambers commercial block, Brasher flats, and Daniel Wells block.
- Checked official/federal records for the Washington Square resources and the continuing U.S. Government Building project.
- Used contemporary newspaper transcriptions for the First Regiment Armory and Academy of Music II, preserving the source host's lower reliability tier and the underlying newspaper locator.
- Split additions, reconstructions, and infrastructure from new primary buildings through `construction_or_event_type`.
- Preserved contradictory or incomplete claims as review flags; no conflict was silently resolved.

## Validation

Parser and relationship validation completed on 2026-08-03:

- `year_1878_buildings.csv`: **29 columns in every row**, 28 data rows, 28 unique nonblank `year_record_id` values.
- `year_1878_sources.csv`: **12 columns in every row**, 13 unique source rows.
- Source foreign keys: every semicolon-separated `source_keys` value resolves to a row in the source CSV.
- One source (`ANDREAS_V3_PERMITS`) is intentionally unused as a building foreign key; it supports the annual aggregate statistics below rather than an individual building identity.
- Blank values represent unknowns, not zeros.

## Record statistics

### Completion and phase status

- **22 records** carry a reported 1878 completion.
- Of those, **one** (`CHI1878-028`) is an unresolved bridge-identity conflict and must not be counted in resolved building totals.
- Therefore, the conservative resolved count is **21 reported 1878 completions**, plus **six distinct 1878 phases whose projects completed later or have unknown completion**.
- The remaining phase records include Lincoln Park's permanent breakwater, the Servite convent, the House of the Good Shepherd north wing, the City Hall/Court House complex, the U.S. Government Building, and the Daniel Wells mixed-use block.

### Confidence and review

- **21 high-confidence** records.
- **6 medium-confidence** records.
- **1 low-confidence** record: the apparent duplicate/conflicting Fullerton Avenue pile-bridge report.
- **18 records need review**, generally because a precise address, material, completion day, demolition date, or unit-level identity remains unresolved. A review flag does not mean the core 1878 event is unsupported.

### Event-type distribution

- 5 `new_construction`
- 3 `new_residential_construction`
- 2 simple `completion`
- 2 `construction_start_and_phase`
- 2 `completion_and_occupancy`
- 2 `industrial_addition`
- 12 other specifically typed events occurring once each, including dedication, infrastructure, contract/superstructure work, reconstruction, conversion, specialized fit-out, an addition, and the conflict-preserving bridge report

### Broad structure mix

- 5 transportation/shore infrastructure records, including the conflict-preserving Fullerton row
- 3 theaters
- 2 churches
- 2 printing/commercial buildings
- 2 brewery service buildings
- 14 other civic, military, educational, charitable, residential, mixed-use, and outbuilding records

These are record counts, not physical-building counts. The Newberry rowhouse record represents four houses, while the barn record represents multiple outbuildings whose exact count still needs the district inventory sheets.

## Citywide annual construction-flow evidence

Andreas's printed permit table reports the following for 1878:

- **1,019 buildings represented by permits**
- **31,118 feet of street frontage**
- **$6,561,100** total reported cost in nominal historical dollars
- Story distribution: 171 one-story; 550 two-story; 247 three-story; 30 four-story; 19 five-story; 2 six-story. These categories sum to 1,019.
- Front material: 647 brick-front; 372 stone-front. These categories also sum to 1,019.
- Selected uses: 70 stores/offices; 167 stores/dwellings; 574 dwellings; 5 churches; 30 manufacturing buildings. These published use classes sum to 846 and are not a complete partition of the annual total.

The named file should therefore be understood as an evidence-backed identity layer nested inside a much larger aggregate construction flow. Coverage by named record is at most 28/1,019 (2.75%) before adjusting for grouped structures, non-permit phases, and the Fullerton conflict; that ratio is not a completeness score for notable structures.

## Important conflicts and limitations

1. **Fullerton Avenue bridges.** Andreas separately reports a 125-foot pivot bridge completed January 19, 1878 and a 225-by-20-foot bridge rebuilt in 1878 for $1,490. The latter dimensions and cost exactly match a Fullerton pile bridge in the 1874-75 public-works chronology. `CHI1878-028` preserves the statement but is excluded from conservative resolved totals pending the original annual reports.
2. **Eighteenth Street viaduct costs.** Andreas gives two conflicting total/substructure cost sets and two nearby August start dates. Completion on December 18, 1878 and operation on February 7, 1879 are retained; cost fields remain in notes rather than being normalized as a single false value.
3. **Immaculate Conception residence cost.** The parish narrative reports about $7,000; the pastor biography reports about $5,000. Both are preserved.
4. **Crilly Building story count.** The 1878 building was five stories; two stories were added in 1888. Later descriptions calling it a seven-story 1878 building collapse two phases.
5. **First Regiment Armory completion.** The July 31 report expected September 1 delivery but allowed that work might take ten additional days. The annual completion is strong; exact turnover date needs a later newspaper issue or directory occupancy check.
6. **House of the Good Shepherd north wing.** The source establishes $8,695 applied to erecting the wing in 1878, but not a completion date. The completion field is deliberately blank.
7. **Current status.** “Extant_at_2003_listing” for the Washington Square properties reports the National Register documentation date, not an unchecked 2026 assertion.

## Exclusions and non-construction findings

- James Otis/Armour Street School: the official school history says the institution opened in the 1878-79 academic year, but that alone does not identify or date a physical building. Excluded pending Board of Education records.
- Calumet Club at Michigan Avenue and Eighteenth Street: documented 1878 lease/opening of an existing residence, not new construction. Excluded.
- St. Paul's Reformed Episcopal Church at Washington and Carpenter: documented 1878 purchase/occupancy of the former Third Presbyterian property, not new construction. Excluded.
- Fire-alarm boxes and talking-line installations: distributed equipment, not buildings. Excluded from this table.
- Montauk Block: an 1878 design commission is reported, but physical construction/completion belongs later. Excluded from the building-phase table until a groundbreaking date is established.
- Schoenhofen Brewery: later official sources date the surviving administration building to 1886 and powerhouse to 1902; an apparent “1878” claim is not accepted.
- Nickerson Mansion: commissioned in 1879 and completed later; excluded from 1878.

## Map and media candidates

- **Primary annual map:** `MAP_1878_EDSALL`, *Travelers' and Shippers' Railway Guide Map of Chicago*. A reduced local public-domain copy already exists at `work/final/chicago/postfire_1870s_v1/maps/images/1878_railway_guide_map.jpg`. It is a strong street/rail/depot/shipping reference at about 1:12,000, but it still needs georeferencing and cannot independently prove construction dates.
- **Andreas engravings:** public-domain scan; likely reusable after page-level extraction and descriptive metadata. Candidate subjects include civic buildings, theaters, and religious institutions.
- **Old Monroe Street / Crilly:** public-domain 1914 scan; check for a usable Crilly Building plate and retain exact page credit.
- **Academy of Music and First Regiment Armory:** the underlying nineteenth-century newspaper text and period illustrations may be public domain, but images hosted by Chicagology should not be copied without tracing the original item or confirming reuse terms.
- **Washington Square nomination:** federal text is generally public domain; embedded photograph rights and credits are item-specific and must be checked before copying.
- **Art Institute Crilly archive:** finding aid identifies a photograph, but the item has separate rights and requires archive-level retrieval/permission review.
- **Parish history images:** link only unless the parish grants reuse permission.

No new copyrighted web image was copied during this tranche. The already-retained public-domain 1878 map is the safe annual visual asset.

## Next research queue

1. Retrieve the 1878 Chicago building-permit ledger or Board of Public Works permit abstracts to name ordinary buildings behind the aggregate total.
2. Read the cited *Chicago Tribune* issues for February 24 and May 19, 1878 to extract dimensions, costs, materials, exact addresses, and construction status for the Thomas projects.
3. Resolve the Fullerton bridge identities from the 1874-75 and 1878 public-works annual reports.
4. Obtain the Washington Square district inventory sheets to split the four Newberry rowhouses and associated barns into unit-level records.
5. Search Cook County deeds and tax assessments for owners/developers and demolition spans.
6. Georeference the Edsall map and add historical-to-modern street-number crosswalks before assigning coordinates.
7. Query fire-insurance maps for the Bemis & McAvoy icehouse/barn footprints and the Servite/Good Shepherd additions.
8. Trace period photographs to original public-domain repositories rather than copying modern compilation-site images.

## Interpretive snapshot

The 1878 evidence shows a city moving beyond emergency rebuilding into specialized permanent systems: fire patrol, military armory, monumental city/county and federal buildings, theaters rebuilt after new fires, dense flats and rowhouses, industrial service buildings, and engineered lakefront and rail crossings. Yet the permit table also demonstrates how much of the ordinary city remains unnamed in narrative histories. The database should preserve both layers—the richly sourced named structures and the much larger aggregate flow—without pretending one is the other.

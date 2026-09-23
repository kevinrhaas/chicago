# Chicago buildings and physical events: 1876 research notes

## Scope and result

This tranche records named Chicago buildings, additions, conversions, infrastructure, construction starts, openings, and losses for which a physical place and a resolvable source were found for 1876. It is an evidence register, not a claim that every anonymous dwelling, shop, stable, shed, factory unit, permit, or undocumented alteration built in Chicago in 1876 has been individually recovered. The surviving published record does not support that level of certainty without systematic permit, tax, fire-insurance, deed, and newspaper extraction.

The deliverable contains 28 source-backed annual-event rows and 15 source records. It distinguishes completion from start, occupancy, conversion, installation, and destruction so that later database imports can represent a building's history without treating every mention as new construction.

## Method

1. Read the 1876 portions of A. T. Andreas's 1886 city history across municipal infrastructure, county institutions, hotels, breweries, parks, hospitals, schools, and religious organizations.
2. Retained only named or independently locatable physical assets. Aggregate construction totals were not converted into invented building identities.
3. Cross-checked surviving or architecturally significant properties against City of Chicago landmark data, National Register documentation, university and museum finding aids, and institutional histories.
4. Reconciled events already represented as 1875 starts or phases so that the 1876 file records only the 1876 completion or event.
5. Used `needs_review=true` wherever address conversion, exact start, fabric survival, architect, completion boundary, or physical-versus-occupancy status remains unresolved.

## Validation

- CSV parsing: passed.
- Building schema: all 28 data rows have exactly 29 columns.
- Source schema: all 15 data rows have exactly 12 columns.
- Identifier uniqueness: 28 unique `year_record_id` values.
- Source integrity: every building row has at least one source key, and all 13 source keys used by building rows resolve in the source CSV.
- Confidence: 18 high, 10 medium, 0 low.
- Review flags: 17 true, 11 false.
- Coordinate discipline: coordinates are included only where a reliable present-day record was available; historical intersection rows were not assigned guessed centroids.

## Statistics

### Annual event counts

| Broad event class | Rows |
|---|---:|
| Completion or new-structure event | 11 |
| Start, planning, or ongoing major phase | 6 |
| Addition or equipment installation | 4 |
| Occupancy/use-only opening | 3 |
| Conversion or remodel | 2 |
| New infrastructure | 1 |
| Destruction | 1 |
| **Total** | **28** |

Eighteen rows carry `year_completed=1876`: 13 exact-date/exact-year events, three year-only events, and two range-end assignments. This count includes additions, installations, conversions, and infrastructure; it must not be presented as 18 wholly new buildings. Twenty rows opened or entered the documented use in 1876. One physical loss—the Fuller Street wooden bridge—was identified.

### Building or asset types

- Four church buildings, two church-tower installations, one church conversion, and one church addition.
- Two railroad viaducts, one bridge-loss event, and one waterworks project.
- Two houses plus one mansion.
- One each: hospital addition, school, clergy house, institutional home, synagogue, clubhouse, tabernacle, ice house, brewery complex, hotel conversion, hotel occupancy, pier/shelter use, and department-store occupancy.

### Major documented values and capacities

- Milwaukee Avenue viaduct: $140,371.55.
- Blue Island Avenue/Throop Street viaduct: $102,173.99.
- West Division Pumping Works extension: $371,681.01 total when completed in 1884; the 1876 event is project initiation only.
- Michael Brand brewery: approximately $300,000 for buildings and machinery over 1876-77.
- Sinai Temple: approximately $90,000 including sidewalk, furnishings, and organ.
- Moody and Sankey Tabernacle: approximately 8,000 seats.
- Cook County Hospital clinical amphitheater: approximately 600 seats.

These values are historical nominal dollars and have not been inflation-adjusted.

## Chronology resolutions and exclusions

### Chicago Avenue Church / Moody Church

The 1875 annual file had carried an institutional-history claim that the Chicago Avenue Church was completed and dedicated in 1876. Andreas states that the basement was used for about two years and that the completed structure was dedicated in June 1875. Because that is a direct conflict and no independently verified 1876 physical event was found, no Chicago Avenue Church completion row is included here. `MOODY_HISTORY` remains in the source file only to preserve the conflicting claim for later primary-newspaper resolution. The existing 1875 record should be corrected during normalization.

### William Waller House

National Register documentation gives 1875-76, but an August 1875 social event reportedly occurred at the house. The 1876 record is therefore a range-end completion phase, not a confident 1876 opening.

### Occupancy-only records

The Anna/New Delavan House, Carson-Pirie North Division store, and Lincoln Park Floating Hospital station are retained as use events because the building database ultimately needs occupancies, but none is counted as verified 1876 new construction. For the floating hospital, Andreas describes a shelter house on the pier but does not clearly date its erection.

### Public schools and parks

The Andreas public-school construction table was visually checked and did not yield a named 1876 city public-school building. No school was inferred from enrollment or expenditure totals. The park narrative reports fiscal stringency and no extension of improvements during 1876; routine maintenance was not converted into structure rows.

## Annual stock and construction-flow evidence

The named record shows a year dominated by completion of projects begun in 1875, religious and institutional work, railroad grade-separation infrastructure, and adaptive reuse of central commercial buildings. It also shows multi-year capital projects beginning in 1876—the Cook County Hospital amphitheater, St. Joseph's Church and Home, Jefferson Park Presbyterian Church, the Michael Brand brewery, and the West Division pumping extension.

This is a lower-bound named-event inventory. A defensible citywide flow estimate still requires:

- 1876 building-permit ledgers and Board of Public Works annual reports;
- assessor/tax books and deed indexes for ordinary residential and commercial construction;
- Sanborn, Rascher, and other fire-insurance mapping where available;
- daily newspaper permit, real-estate, architecture, hotel, factory, and church notices;
- Chicago Board of Education proceedings and parish/denominational archives;
- railroad and bridge-company engineering records.

## 1876 map layer

The principal year-map candidate is Warner & Beers's *Combination Atlas Map of Cook County, Illinois* (1876), cataloged by the University of Illinois. It is public domain due age and can support a period basemap after plate-level download and georeferencing. The catalog URL is stored as `MAP1876_UIUC`.

Recommended map workflow:

1. Inventory all Chicago and Cook County plates and record plate titles, scale, orientation, and coverage.
2. Download repository-provided master images and retain source/checksum/rights metadata.
3. Georeference plates to stable control points such as section lines, river bends, rail corridors, and enduring street intersections.
4. Represent the 1876 city boundary, shoreline, river, canals, railroads, parks, subdivisions, and built-up extent as separate dated layers.
5. Link building rows to point, footprint, corridor, or approximate-intersection geometries with explicit spatial-precision fields.
6. Never use a modern street-centerline point as if it were an exact historical footprint.

The atlas depicts conditions and cartographic claims current around publication, not necessarily every change on December 31, 1876. Each future layer should carry `valid_from`, `valid_to`, `map_publication_date`, `spatial_precision`, and `source_key`.

## Map and media candidates and rights

| Candidate | Possible use | Rights/handling |
|---|---|---|
| Warner & Beers 1876 Cook County atlas (`MAP1876_UIUC`) | 1876 city/county basemap and land-form reference | Public domain due age; retain University of Illinois attribution and item metadata. |
| Chicago Public Library New England Congregational Church exterior (`CPL_CITYWIDE`) | Building image and address corroboration | Finding aid is citable; obtain item-level reproduction terms before copying an image. |
| City of Chicago DuPont-Whitehouse House page/data | Present-day exterior and verified geometry | Factual data used; verify City image reuse terms before redistribution. |
| National Register William Waller House nomination | Architecture, plan, and historic/current photographs | Federal record text is public domain; photograph restrictions and credits may vary. |
| Art Institute architectural image index for Pullman House | Design attribution and possible drawings/images | Finding-aid metadata used; request or check item-level rights before downloading assets. |
| *Old Monroe Street* tabernacle material (`OLD_MONROE`) | Public-domain illustration or context for the Moody-Sankey Tabernacle | 1914 volume is public domain; preserve scan provenance and page locator. |

No third-party image binaries were copied in this tranche because the linked institutional collections require item-level rights verification. The source table preserves the acquisition queue.

## Known limitations

- Andreas is near-contemporary but retrospective and sometimes compresses dates, costs, names, and multiple phases.
- Historic street numbering and renamed streets have not been comprehensively crosswalked.
- Demolition dates are absent for many non-surviving buildings.
- Exact architects/builders were not assigned unless a source named them; ambiguous Pullman House attributions remain explicit.
- Fire-limit context is interpretive unless a row has direct ordinance or permit evidence.
- Landmark and National Register sources disproportionately represent surviving or architecturally distinguished buildings.
- Ordinary houses, stores, workshops, rear buildings, and short-lived frame structures are substantially underrepresented.

## Next research queue

1. Resolve the Chicago Avenue Church 1875/1876 conflict with contemporary dedication notices and amend the 1875 row.
2. Search 1876 building-permit and Board of Public Works ledgers to add ordinary private construction and verify fire-limit compliance.
3. Retrieve contemporary Chicago Tribune and Inter Ocean notices for Chicago Club, Pullman House, Waller House, hotels, churches, and industrial projects.
4. Obtain exact historical addresses and footprint sources for the two viaducts, Brand brewery, St. Joseph's institutions, and religious buildings.
5. Decompose grouped complexes into component buildings only where pavilion, ice-house, wing, or outbuilding identifiers can be proven.
6. Download and georeference the Warner & Beers 1876 atlas plates with item-level provenance.
7. Acquire only public-domain or licensed images and create a media manifest linking file checksum, caption, date, creator, rights, source URL, and building IDs.


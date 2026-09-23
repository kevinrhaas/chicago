# Chicago buildings and physical events: 1879 research notes

## Scope and result

This tranche records 25 named or source-identifiable Chicago-area buildings, additions, renovations, construction starts, openings, and infrastructure phases tied to calendar year 1879. It is an evidence register, not a claim that all 1,093 buildings counted in the contemporary annual construction table have individually survived in the published record. Anonymous permit totals were preserved as aggregate flow evidence and were not converted into invented building identities.

The annual file deliberately separates whole-building construction from campus components, occupancy, fit-out, partial completion, construction start, adaptive reuse, and public infrastructure. Jurisdictional edge cases in the Town of Lake and Town of Cicero are retained as metropolitan-network events with `needs_review=true`, not silently represented as being inside the 1879 Chicago boundary.

## Method

1. Read the 1879 portions of A. T. Andreas's 1886 history across municipal bridges, viaducts, fire alarm, schools, breweries, religious institutions, manufacturing, and rebuilding statistics.
2. Visually checked the printed public-school table because OCR obscured the school years, dimensions, capacity, heat and cost columns.
3. Cross-checked architecturally significant buildings against Library of Congress HABS records, City of Chicago landmark records, GSA history, public-school and parish histories, state property data, and museum collections.
4. Used near-contemporary newspaper transcriptions and public-domain guidebooks for construction details that the institutional records omit, while rating compilation sources below official records.
5. Treated 1879 purchase, opening, or occupancy as a separate event whenever the underlying building was constructed earlier or completed later.
6. Preserved source conflicts and omissions in notes and set `needs_review=true` rather than forcing a single unsupported answer.

## Validation

- CSV parsing: passed.
- Building schema: all 25 data rows have exactly 29 columns in the required order.
- Source schema: all 26 source rows have exactly 12 columns in the required order.
- Identifier uniqueness: 25 unique `year_record_id` values (`CHI1879-001` through `CHI1879-025`).
- Source integrity: every building row has at least one source key; all 22 source keys used by building rows resolve in the source CSV.
- Confidence: 15 high, 10 medium, 0 low.
- Review flags: 21 true, 4 false. Most review flags concern historical-address conversion, surviving fabric, municipal-boundary status, missing architect/material, or event-type precision, not an absence of evidence for the named event.
- Coordinate discipline: only the extant Nickerson House received coordinates, based on its official current identity. Historical intersections were not assigned guessed point coordinates.

## Annual event statistics

| Broad event class | Rows |
|---|---:|
| Building or identifiable building-component completion | 13 |
| New or extended infrastructure | 4 |
| Renovation, adaptive reuse, or building addition | 3 |
| Occupancy, fit-out, partial-use, or opening without 1879 full construction | 4 |
| Construction start/commission for later completion | 1 |
| **Total** | **25** |

Twenty rows have `year_completed=1879`: 13 building/component completions, four infrastructure completions/extensions, and three renovation/addition events. This is not a count of 20 wholly new buildings. Twenty-four rows opened or entered the documented use in 1879; the Nickerson House began in 1879 and opened in 1883.

### Asset types

- Three public schools, three churches, one chapel, and one parish hall.
- Two commercial buildings, one department-store occupancy, one mixed-use music hall, one theater renovation, and one factory opening.
- Two mansions: one 1879 completion/occupancy and one 1879 commission/start.
- Two bridges, one pedestrian bridge, one railroad viaduct opening, and one communications-infrastructure extension.
- One ice house, one brewery office, one federal-building partial phase, and one recreation addition.

### Significant documented dimensions, values, and capacities

- Leiter Building I: about 82 feet 10 inches by 102 feet 6 inches; five stories plus basement in the initial phase; contemporary estimate about $125,000.
- Central Music Hall: about 125 by 150 feet, six stories plus basement, about 90 feet high, with an auditorium variously reported at 1,800-2,000 seats.
- Laflin Building: 200 by 40 feet, five stories, 85 feet high, two freight elevators.
- Armour Street School: 107 by 88 feet, three stories, 945 sittings, $37,000 including heat and furniture.
- Marquette School: 107.5 by 84 feet, three stories, 945 sittings, $37,000 in Andreas; a later guide gives different capacity and cost.
- Raymond School: 70 by 84 feet, three stories, 770 sittings, $29,500 including heat and furniture.
- Eighteenth Street viaduct: two 142-foot truss-girder spans, 20-foot roadway, six-foot sidewalks, $11,194; completed in 1878 and opened in 1879.
- Holy Family Sodality building: reported $40,000 and two libraries totaling about 3,000 volumes.
- St. Stephen Lutheran reuse: approximately 1,000 seats, $10,475 property purchase, and a reported $3,000 organ.

Historical dollar figures are nominal and have not been inflation-adjusted.

## Annual stock and construction-flow evidence

Andreas's printed rebuilding table reports the following citywide 1879 flow. These figures remain aggregate evidence and must never be expanded into anonymous rows:

| Measure | 1879 value |
|---|---:|
| Permitted/reported buildings | 1,093 |
| Aggregate frontage | 33,361 ft |
| Aggregate nominal value | $6,139,580 |
| Average frontage per reported building | 30.5 ft |
| Average nominal value per reported building | $5,617 |

### Height classes

| Stories | Buildings | Share |
|---:|---:|---:|
| 1 | 307 | 28.1% |
| 2 | 455 | 41.6% |
| 3 | 229 | 21.0% |
| 4 | 16 | 1.5% |
| 5 | 3 | 0.3% |
| **Printed height-class subtotal** | **1,010** | **92.4%** |
| Unclassified/source discrepancy | 83 | 7.6% |
| **Reported annual total** | **1,093** | **100.0%** |

The printed page clearly gives 307 one-story buildings. The height classes therefore fall 83 short of the reported annual total. The gap is preserved as a source discrepancy and must not be assigned to a story category without independent permit evidence.

### Facade/material classes

| Reported front material | Buildings | Share |
|---|---:|---:|
| Brick | 878 | 80.3% |
| Stone | 215 | 19.7% |
| **Total** | **1,093** | **100.0%** |

The material categories appear to describe fronts rather than complete structural systems. They must not be interpreted as 878 all-brick and 215 all-stone load-bearing buildings.

### Selected use classes

| Reported use | Buildings | Share of all 1,093 |
|---|---:|---:|
| Stores and offices | 85 | 7.8% |
| Store-dwellings | 173 | 15.8% |
| Dwellings | 650 | 59.5% |
| Manufacturing | 50 | 4.6% |
| Other or unclassified in the excerpt | 135 | 12.4% |

The four named use classes total 958, not 1,093; the residual is preserved as unclassified rather than guessed. The 25 named annual rows therefore represent a curated lower bound and are not statistically representative of the permit universe, which was dominated by ordinary dwellings.

## Chronology resolutions and exclusions

### Leiter I versus later Leiter/Field buildings

Leiter Building I at Wells/Fifth Avenue and Monroe is a genuine 1879 new building by William Le Baron Jenney. Its initial five-story-plus-basement phase is separated from the two-story 1888 addition. HABS and later architectural commentary characterize it as an important precursor to skeleton construction, but its masonry walls and timber floor system mean it should not be labeled a fully skeletal steel-frame building.

The Field, Leiter & Co. State Street store is different. The Singer replacement building was erected in 1878; Field and Leiter bought and occupied it in 1879. The 1879 row is therefore acquisition, fit-out, and occupancy only, not new construction.

### United States Government Building

The federal Post Office/Custom House project began in the 1870s and was completed in 1880. The west half of the basement entered temporary post-office use in April 1879. A prior annual row or secondary source that assigns whole-building completion to 1879 should be corrected during longitudinal normalization.

### Eighteenth Street viaduct

The viaduct was completed December 18, 1878 and opened February 7, 1879. It remains in this file as an opening event and is excluded from 1879 construction-completion totals.

### Union Stock Yard Gate

The official City landmark page dates the surviving gate to circa 1875, while some institutional secondary material assigns 1879. Because the official record and the existing 1875 annual row already cover it, no 1879 row was created. Contemporary stock-yard or architect records are needed before changing the date.

### Rogers/West Thirteenth Street School

A community history dates the Rogers school to 1879, but Andreas's visually checked printed table lists West Thirteenth Street School under 1880. It is excluded from 1879 pending Chicago Board of Education proceedings and contemporary opening notices.

### Company formations and uncertain occupancies

The Chicago Cottage Organ Company is associated with 1879 in some company histories, but the located evidence describes formation or occupancy of a pre-existing Randolph-and-Ann building and conflicts with an 1880 chronology. It was excluded until a distinct 1879 physical event is documented.

C. P. Kimball & Co. is retained only because Andreas explicitly says the firm opened a five-floor, 40-by-160-foot building in 1879. The later Wabash-and-Harrison description may concern a different or expanded plant, so no address is assigned.

### Geography exclusions

- The Peter Schuttler mansion associated with this period was at Lake Geneva, Wisconsin, not Chicago, and was excluded.
- The Hyde Park House loss occurred before Hyde Park's 1889 annexation and did not supply a distinct 1879 construction phase; it was excluded from the city building register.
- Kedzie Avenue bridge and the Stock Yards fire-alarm extension are retained only as explicitly flagged metropolitan infrastructure. Their Town of Cicero/Town of Lake jurisdiction must be represented in future boundary-aware geometry.

## 1879 map layer

The leading period basemap candidate is Rand McNally's *Guide Map of Chicago and Boulevard and Park System* (1879), stored as `MAP1879_RAND`. A complementary transportation layer is R. W. Dobson's *Railway Map of Chicago and Environs* (1879), stored as `MAP1879_RAIL`. The University of Chicago's *Mapping Chicagoland* collection (`UCHI_MAPS`) is a discovery source for additional neighborhood and regional sheets.

Recommended annual-map workflow:

1. Resolve each map to its holding repository and download the repository-provided master, not a portal preview.
2. Record title, creator, publication date, scale, orientation, sheet coverage, scan identifier, checksum, source URL, and item-level rights.
3. Georeference to stable control points such as section lines, river bends, canal alignments, rail junctions, and enduring street intersections.
4. Digitize 1879 city boundaries, adjacent towns, shoreline, river/canal, railroads, bridges, parks, boulevards, subdivisions, and built-up extent into separate dated layers.
5. Represent Town of Lake and Town of Cicero features outside the city polygon rather than retroactively applying later annexation boundaries.
6. Link a building event to point, footprint, corridor, complex, or approximate-intersection geometry with explicit `spatial_precision`, `valid_from`, `valid_to`, and `source_key` fields.
7. Preserve both map publication year and inferred landscape-validity interval; a map labeled 1879 is not necessarily a December 31 snapshot.

## Map and media candidates and rights

| Candidate | Possible use | Rights/handling |
|---|---|---|
| Rand McNally 1879 guide map (`MAP1879_RAND`) | Annual street, park, boulevard, shoreline, and municipal-context basemap | Original map is public domain due age. Resolve the holding repository, retain attribution and item metadata, and do not copy the OldMapsOnline preview as the archival master. |
| Dobson 1879 railway map (`MAP1879_RAIL`) | Rail corridors, terminals, yards, industrial geography, and metropolitan extent | Original map is public domain due age; the Encyclopedia of Chicago derivative is copyrighted. Obtain a master from the Chicago History Museum under its item-level terms. |
| Andreas Volume III (`ANDREAS_V3`) | School table, contemporary plans/illustrations, municipal and institutional context | Book is public domain. Preserve printed page number, scan provenance, and an unmodified master. |
| Leiter I HABS record (`LOC_LEITER_HABS`) | Measured drawings, documentary photographs, structural analysis | HABS federal documentation is generally public domain/no known restrictions; inspect individual image credits for copied-source exceptions. |
| Nickerson House HABS record (`LOC_NICKERSON_HABS`) | Measured drawings and high-resolution building photographs | Same HABS handling; retain call number, image identifier and credit. |
| *Picturesque Chicago* (`PICTURESQUE_CHI`) | Public-domain Central Music Hall illustration and descriptive context | Public domain due publication date; retain Internet Archive/Wikimedia provenance and page locator. |
| City, CPS, museum, parish, WBEZ and WTTW pages | Current or retrospective building images | Factual data may be cited, but modern images and page layouts are copyrighted. Do not redistribute without item-level permission or license. |
| Chicagology compilations | Discovery of newspaper images, maps, and building views | Do not copy site derivatives as if public domain. Retrieve an original pre-1929 newspaper scan or public-domain source and document its repository. |

No third-party image binaries were copied in this tranche. The source file provides an acquisition queue that separates public-domain originals from copyrighted portal presentations.

## Known limitations

- Andreas is near-contemporary but retrospective and sometimes compresses construction, dedication, occupancy, and fiscal years.
- The surviving published record privileges prominent commercial, institutional, religious, and public works; ordinary residential and small-business construction is severely underrepresented.
- Historical street numbering and renamed streets have not been comprehensively crosswalked.
- Exact architects, builders, structural systems, dimensions, and demolition dates remain unknown for many non-landmark properties.
- Newspaper-transcription sites are discovery and corroboration tools, not substitutes for original page images where exact wording matters.
- Current parcel identity does not by itself prove an original 1879 footprint or surviving fabric.
- The annual aggregate table is internally consistent for front materials, but its 1879 height classes fall 83 short of the reported total; its use categories are also incomplete, and its definition of “building” requires permit-ledger confirmation.
- A complete building-by-building census with certainty requires systematic extraction of permit ledgers, assessor books, tax records, deeds, fire-insurance atlases, Board of Education proceedings, public-works reports, and daily newspapers.

## Next research queue

1. Transcribe every 1879 permit ledger entry and link permit number, applicant, owner, architect/builder, address, dimensions, material, stories, use, cost, and disposition.
2. Retrieve Chicago Board of Education proceedings for Armour, Marquette, Raymond, and West Thirteenth/Rogers schools to resolve start/opening years, heat systems, costs and capacities.
3. Retrieve original newspaper page images for Leiter I, Central Music Hall, Field & Leiter, Olympic Theatre, Sixth Presbyterian, Laflin, McCormick, and the federal building.
4. Resolve historic addresses and footprints for Bemis & McAvoy, Holy Family Sodality, Sacred Heart chapel, Farwell Hall, and C. P. Kimball.
5. Reconcile the United States Government Building chronology across all annual tranches and ensure 1880 receives the final-completion event.
6. Resolve the Union Stock Yard Gate 1875/1879 conflict from primary stock-yard or architect records before altering the existing 1875 entry.
7. Acquire and georeference the 1879 Rand McNally and Dobson maps with repository-level provenance and rights metadata.
8. Create a media manifest with file checksum, caption, creator, creation/publication date, rights statement, source URL, repository identifier and linked `year_record_id`.

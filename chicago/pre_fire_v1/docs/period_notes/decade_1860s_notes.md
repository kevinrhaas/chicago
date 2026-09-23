# Chicago structures of the 1860s: research notes

## Scope and result

This tranche contains **60 source-identifiable buildings, complexes, additions, or infrastructure works** begun, completed, or materially constructed in 1860-1869. Three cross-decade projects are retained because construction began in the 1860s: First Congregational Church and St. Michael's Church, completed in 1870, and the U.S. Marine Hospital, completed in 1872.

This is not a claim to enumerate every Chicago structure. The city grew from roughly 112,000 people in 1860 to almost 300,000 in 1870, and Andreas explicitly says a complete list of even the architecturally prominent ante-fire blocks would be impractical. Ordinary dwellings, anonymous commercial buildings, sheds, wharves, and most individual Camp Douglas barracks are not consistently named in the surviving narrative sources. Rows were added only where a defensible entity or grouped complex can be identified.

The 25-column building CSV treats a **material construction phase** as in-scope. Thus the 1863 Noble-Seymour-Crippen addition is separate from its 1833 core, while phased complexes such as Soldiers' Home and Grace Methodist Church are one record with the phases stated in notes. The Union Stock Yard and Camp Douglas remain grouped records pending plan-level decomposition.

## Statistics

| Metric | Count |
|---|---:|
| Records | 60 |
| High confidence | 58 |
| Medium confidence | 2 |
| Exact completion date | 51 |
| Phased completion | 4 |
| Seasonal-exact date | 3 |
| Active-by date | 2 |
| Schools | 16 |
| Rows typed as churches | 13 |
| Grain elevators | 3 |
| Hospitals | 3 |
| Waterworks structures/components | 5 |
| Demonstrated or source-supported 1871 survivors | 31 |
| Destroyed in 1871 | 18 |
| Gone before 1871 | 5 |
| 1871 fate unresolved | 6 |

Completion distribution is: 1860: 4; 1861: 3; 1862: 3; 1863: 3; 1864: 5; 1865: 6; 1866: 4; 1867: 10; 1868: 8; 1869: 11; cross-decade 1870: 2; cross-decade 1872: 1.

The apparent 1867-69 concentration is real in part—the waterworks and postwar building boom were substantial—but also reflects source survival. Andreas provides unusually systematic lists for public schools, churches, grain elevators, and the water system, while private houses and small shops are undercounted.

## 1871 fire method

The fire field uses four controlled values in this tranche:

- `destroyed`: a cited source explicitly reports destruction or the structure is directly described in the fire-loss narrative;
- `survived`: the source explicitly says it survived, an official landmark record proves pre-fire fabric remains, or the same building is documented in post-1871 use;
- `not exposed`: removed or destroyed before October 1871;
- `unknown`: existence on the fire date or its outcome is not yet established.

Some `survived` values are **geographic/post-use inferences**, clearly labeled in each row's notes. Examples include west- and south-side schools whose institutional narratives continue after the fire. These should ultimately be upgraded by joining an October 1871 building footprint or parcel record to the accepted fire perimeter. The Water Tower and Pumping Station are stronger: the City of Chicago identifies them as the only public buildings surviving within that portion of the burned area. St. Michael's walls, First Unitarian, Park Avenue Methodist, Barnes House, First Congregational, and the extant landmarks also have direct building-specific evidence.

Do not infer that a congregation's survival proves its building survived. The CSV relies on postfire use only where the narrative appears to continue the same physical structure; ambiguous cases remain `unknown`.

## Major findings

1. **The 1860s city was already a systems city.** The two-mile intake tunnel, offshore crib, pump well, massive engine, machine shop, pumping station, and Water Tower form a linked water-supply system. Modeling them as one “Water Tower” record would erase important construction and failure relationships.
2. **“Fireproof” was an unreliable ante-fire label.** The 1869 Tribune Building used stone, iron front frames, an iron roof, and iron shutters yet was lost. The waterworks' masonry shells survived but timber roofs and machinery were badly damaged, disabling the system.
3. **Civil War construction was both temporary and durable.** Camp Douglas and Soldiers' Rest disappeared, while the phased Soldiers' Home retains pre-fire fabric. The surviving home is the city landmark with the most direct Civil War building association.
4. **School construction accelerated sharply.** The 16 records here are still selective: they include buildings with explicit construction/dedication evidence and exclude rented rooms or schools whose physical premises cannot be resolved.
5. **Fire fate depends on relocation and geography.** West- and south-side institutions often survived, while North Side and central-business structures were disproportionately destroyed. The Wigwam and first Farwell Hall were already gone before 1871.
6. **The original stockyard gate is not today's landmark gate.** The 1865 complex opened on Christmas Day; the surviving Union Stock Yard Gate dates to 1875 and must not be attached to the 1865 record as original fabric.

## Entity-resolution cautions

- Historical streets need a date-bounded crosswalk. Cass became Wabash in the relevant corridor; Pine became Michigan Avenue; Robey became Damen; Reuben became Ashland; Centre Avenue became Racine; Market and South Water were partly absorbed into Wacker; Twelfth became Roosevelt. Several minor streets such as White, Old, Johnson, Hubbard Court, and Eldridge Court require block-level verification rather than simple name substitution.
- A congregation, school, or company is not identical to its building. Successor buildings after fire or relocation need distinct structure IDs linked by organization ID.
- Grain-elevator firm histories sometimes say a firm “established an elevator” without a construction contract or address. Such rows are marked `active_by` or `needs_review` unless construction is explicit.
- Camp Douglas was repeatedly reconfigured. Its grouped row should later become a complex table linked to dated plans, with separate barracks, hospitals, kitchens, fences, guardhouses, and the YMCA chapel.
- Soldiers' Home is phased 1864-1923. The CSV records the 1864 wing and 1865-66 main block together; a preservation-grade model should digitize surviving fabric by phase.

## Map-by-year extension

The **Albert Ruger, 1868 bird's-eye view** at the Library of Congress is the strongest visual layer found for this decade. It depicts individual buildings, industries, railroads, ships, river branches, shoreline, and street patterns from Schiller Street to Twelfth Street. It is a perspective panorama, not a survey map, so it should support visual identification and approximate geometry—not cadastral coordinates.

Recommended 1860s map stack:

1. georeferenced municipal or commercial street maps for 1860, 1863, 1866, and 1869;
2. Ruger's 1868 panorama as an oblique-image reference layer;
3. waterworks engineering plans for tunnel, crib, pump well, and mains;
4. Camp Douglas plans for time-sliced complex layouts;
5. Union Stock Yard plans and railroad track diagrams;
6. 1866-71 directories for occupant/address joins;
7. post-fire maps showing burn perimeter and standing structures.

Each geometry should include `valid_from`, `valid_to`, `geometry_precision`, `source_key`, `georeference_method`, `control_points`, `estimated_error_meters`, and `confidence`. A building move, addition, or rebuilding is an event; it must not overwrite earlier geometry.

## Media and rights candidates

| Candidate | Source | Use | Rights status |
|---|---|---|---|
| *The Republican Wigwam at Chicago*, May 16, 1860 | `LOC_WIGWAM_IMAGE` | Exterior illustration and record illustration | Library of Congress says no known restrictions on publication; downloadable TIFF/JPEG; credit LOC and retain reproduction number LC-USZ62-3772 |
| *Chicago in 1868 from Schiller Street…to 12th Street* | `LOC_CHICAGO1868` | Citywide visual/map layer and structure-identification aid | LOC Geography and Map Division content is free to use/reuse absent a contrary advisory; credit Library of Congress |
| Andreas engravings: Chamber of Commerce, Crosby's Opera House and ruins, Wood's Museum, churches, schools, waterworks, Soldiers' Home | Internet Archive scan, source keys `ANDREAS2_*` | Building thumbnails and fire before/after pairs | 1885 volume is public domain; record printed page, scan identifier, caption, and crop coordinates |
| City landmark photographs | `CITY_*` records | Current-condition reference | Page-image reuse terms are not stated; link only until reuse permission is confirmed |
| Encyclopedia of Chicago linked images | `EOC_*` records | Historical visual leads | Text entry is citable, but underlying Chicago History Museum image rights require separate review |

No uncertain-rights image was copied into this tranche. If the parent task downloads the LOC or Andreas public-domain images, create a media manifest with title, creator, depicted date, creation date, repository, source URL, rights statement, credit line, linked structure ID, filename, and SHA-256 checksum.

## Priority research queue

- Resolve exact parcels for the Lunt elevator, Illinois River Elevator, National Elevator, Tribune Building frontage, Camp Douglas substructures, and the U.S. Marine Hospital.
- Add omitted but identifiable 1860s buildings from page-image directories, deeds, Board of Public Works reports, school-board reports, and church archives; Andreas openly states that his architectural list is selective.
- Decompose the Union Stock Yard into 1865 exchange, hotel, livestock pens, railroad tracks, water/sewer systems, and service buildings.
- Trace demolition/replacement dates for surviving 1860s schools and churches.
- Verify every historical-to-modern street conversion against the Chicago street-name change index and original subdivision plats.
- Create `building_events.csv` for construction phases, openings, additions, moves, fires, repairs, and demolitions. This is especially important for Soldiers' Home, Grace Methodist, Eighth Presbyterian, Farwell Hall, Pumping Station, St. Michael's, and the Noble-Seymour-Crippen House.
- Distinguish “outside the fire perimeter” from “present after the fire” in a future normalized `fire_assessment` table with evidence type and geometry join.

## Validation

- `decade_1860s_buildings.csv`: 60 data rows, 60 unique IDs, exactly 25 columns on every row.
- `decade_1860s_sources.csv`: 23 data rows, exactly 12 columns on every row.
- Every building has one or more source keys, and every referenced key exists in the source registry.
- `LOC_CHICAGO1868` is intentionally unused by a building row; it supports the map/media extension documented here.

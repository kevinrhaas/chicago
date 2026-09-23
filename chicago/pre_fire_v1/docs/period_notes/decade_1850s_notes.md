# Chicago structures, 1850–1859: research notes

## Deliverable and scope

This package contains 67 normalized structure records and 15 source records for Chicago's 1850s. The record set emphasizes individually identifiable, locatable structures documented in reliable historical or institutional sources: civic buildings, churches, hotels, schools, railroad depots, theaters, bridges, utilities, institutional buildings, and a small number of residences now within Chicago.

This is a strong named-structure census, not a defensible census of every ordinary house, shop, shed, stable, factory outbuilding, or short-lived speculative structure erected during the decade. No surviving source series enumerates every such building, and many structures disappeared without a traceable name, permit, address, or illustration. “Complete with certainty all buildings” is therefore not historically achievable from presently available records. The CSV makes uncertainty explicit instead of converting gaps into invented facts.

The unit is a physical structure or tightly integrated complex. Bridges and utility complexes are included because they are essential to a year-by-year city model. Material moves and adaptations are retained only when they changed the physical building inventory (for example, the Hamilton House and State Street Methodist building); rows explain that they are not new construction.

## Source method

The foundation is A. T. Andreas's near-contemporary two-volume *History of Chicago* (1884–85), checked by topical section and printed-page context:

- Volume I: municipal buildings and public works (approximately pp. 180–219), railroad development (approximately pp. 259–263), Protestant and Catholic churches (approximately pp. 292–359), theaters (approximately pp. 488–493), and hospitals (approximately pp. 594–595).
- Volume II: bridges (approximately pp. 68–69), schools (approximately pp. 118–121), the Old University (approximately pp. 463–464), hotels (approximately pp. 501–507), and theaters (approximately pp. 596–599).

Official Chicago landmark records were used for Hull House, the Wingert House, and the Iglehart House; official designation material was used for the Gray House. The Chicago Park District provides the strongest current record for the Couch Tomb. The University of Chicago Library resolves the frequently misreported 1859 “Douglas Hall” date. The Library of Congress's 1857 Palmatary view is the principal decade map/media source.

Each building row has one or more `source_keys`; every key resolves to `decade_1850s_sources.csv`. `confidence=high` means the core identity and the represented completion/opening event are directly stated by the cited source. `needs_review=true` usually means one or more secondary attributes—precise parcel, modern address, architect, structural fabric, demolition date, or 1871 fate—still requires dedicated follow-up.

## Important corrections to the attached working chronology

- The Old University record for 1859 is only the completed **south wing**. The University of Chicago Library states that the main Douglas Hall mass and Dearborn Observatory were completed by 1864. Modeling the whole later complex as a 1859 building would be anachronistic.
- Foster School's permanent three-story brick building was erected in **1857**, not 1856. A separate two-story wooden schoolhouse was erected there in 1855.
- The Orient House's 1859 date is only its **first appearance as a hotel in the city directory**, not proof of new construction.
- Wright's Hotel is documented as **opening in 1859**; its construction year remains unknown.
- The Clifton House is first documented in hotel use in **1858**; the source does not say it was constructed that year.
- The Hamilton House was an **1840 building moved, enlarged, and remodeled in 1851**, not an entirely new 1851 hotel.
- The State Street Methodist building reused and moved a portion of the former Second Presbyterian frame church; it is an adaptation event, not new construction.
- Mercy Hospital's 1853 move to Tippecanoe Hall was an occupancy event in a pre-existing hall, so it is not represented as a newly built 1853 hospital.
- The first K.A.M. purpose-built synagogue dates to 1849. A later move/acquisition should be represented as a building/occupancy phase, not silently recast as 1851 new construction.
- Andreas contains an obvious typographical/OCR error saying the 1857 Massasoit House was sold in 1851. The impossible date was not propagated.

## Summary statistics

The current normalized set contains **67 records**:

| Attribute | Count |
|---|---:|
| High-confidence core records | 54 |
| Medium-confidence core records | 13 |
| Records still needing at least one attribute review | 40 |
| Extant structures | 6 |
| Destroyed structures | 24 |
| Other demolished/superseded structures | 37 |
| Explicitly documented as destroyed in the 1871 fire | 21 |
| Removed, replaced, or destroyed before 1871 | 9 |
| Explicitly documented as surviving the 1871 fire or outside its burn area | 8 |
| 1871 fate not yet established to the record standard | 29 |

By type:

| Type | Count |
|---|---:|
| Religious | 18 |
| Hotel | 13 |
| Infrastructure/bridge | 10 |
| Educational | 6 |
| Theater | 5 |
| Residential | 4 |
| Transportation/railroad | 4 |
| Industrial utility | 2 |
| Assembly hall | 1 |
| Civic | 1 |
| Correctional | 1 |
| Funerary | 1 |
| Hospital | 1 |

By represented completion/opening/move event year: 1850 (3), 1851 (6), 1852 (6), 1853 (7), 1854 (4), 1855 (4), 1856 (17), 1857 (12), 1858 (5), and 1859 (3). The 1856–57 spike reflects both rapid growth and unusually strong documentation for schools, railroad terminals, bridges, hotels, and churches.

The six extant structures in this file are the John Wingert House, Old St. Patrick's Church, Charles J. Hull House, Phebe and John Gray House, Charles D. Iglehart House, and Couch Tomb. Wingert, Gray, and Iglehart were outside Chicago's municipal limits when built; they belong in a modern-city inventory but must not be shown as inside the historical city boundary.

## Fire interpretation

The `fire_fate_1871` value is intentionally conservative. A central location inside a generalized fire perimeter is not, by itself, treated as proof that a specific structure burned. “Destroyed in Great Chicago Fire, 1871” is used when the cited narrative or institutional record supports that fate. “Not established” means a dedicated structure-level check remains. This avoids turning a map overlay into false documentary certainty.

Likewise, `status=destroyed` is reserved for destructive events (fire); `status=demolished` covers teardown, replacement, operational supersession, or unknown removal; and `status=extant` applies to a surviving structure, even when later additions or reconstruction mean that only part of the original fabric remains.

## Map-by-year extension

The 1857 J. T. Palmatary bird's-eye view is the best single visual anchor for this decade, but it is pictorial rather than cadastral. It should not be used as exact building-footprint geometry. A defensible annual model needs temporal feature tables rather than a single “year” column:

1. `building_phases`: `building_id`, `valid_from`, `valid_to`, geometry or parcel reference, use, height/stories, material, alteration type, source, and confidence.
2. `occupancies`: tenant/institution/hotel name and valid date range, separated from physical construction. This solves the Orient House, Mercy Hospital, and renamed-hotel problems.
3. `street_name_crosswalk`: historical name, modern name, segment geometry, valid date range, and source. This is essential for Buffalo, Wolcott, Cass, Fifth Avenue, and similar historical names.
4. `city_boundary_phases`: incorporated/annexed polygon with effective dates. Present-day Wingert, Gray, and Iglehart sites must remain outside Chicago in 1850s views.
5. `shoreline_and_water`: lake edge, river branches, slips, piers, breakwaters, and fill areas with valid dates and source resolution.
6. `transport_network_phases`: streets, bridges, railroad approaches, stations, and service start/end dates.
7. `map_sources`: image identifier, year/date range, scale or pictorial status, georeferencing control points, residual error, rights, and download URL.
8. `event_perimeters`: the 1871 burn perimeter and other fires as dated polygons, kept separate from structure-level documentary fate.

Annual views should be generated from features whose validity intervals contain the requested year. Where only a decade map exists, the model should display a visible confidence layer and must not interpolate buildings into existence without a dated source.

## Media and map candidates

### Cleared or strong reuse candidate

- **J. T. Palmatary, *Chicago*, 1857**, Library of Congress item 75693204. Catalog record: <https://www.loc.gov/item/75693204/>. A 25% IIIF JPEG is available at <https://tile.loc.gov/image-services/iiif/service:gmd:gmd410:g4104:g4104c:pm001460/full/pct:25/0/default.jpg>. The LOC item is presented for free use/reuse absent an item-specific rights advisory; retain the title, creators, year, and Library of Congress credit. This is the recommended first map asset.
- Andreas Volumes I and II are public-domain scans. Their hotel, theater, civic-building, and institutional sections contain engravings useful as visual references. Export images from the scan page only after recording volume and printed-page locator so an image table can preserve provenance.

### Link/reference only until item-level rights are confirmed

- University of Chicago photographic archive record for the Old University: <https://photoarchive.lib.uchicago.edu/db.xqy?one=apf2-05352.xml>.
- City of Chicago landmark pages for Hull, Wingert, and Iglehart, and the Gray House designation report. Their text is authoritative, but site/report images may carry separate credits.
- Chicago Park District Couch Tomb page. Use the official factual record; do not assume its page photograph is freely reusable.
- Chicagology pages are helpful visual indexes and reproduce historical material, but reuse status should be checked at the underlying image level.

No image with unclear rights was downloaded into the repository during this pass.

## Highest-value next research passes

- Resolve the 29 structure-level 1871 fates still marked unknown or survival-not-established using fire-loss lists, Sanborn predecessors, city directories, and structure-specific narratives.
- Geocode historical intersections only after creating the street-name/renumbering crosswalk; modern geocoders will mishandle several 1850s street names.
- Add building-phase rows for raising, moving, enlarging, conversion, and rebuilding. Matteson House (raised in 1859), Richmond House (hotel-to-business-block), and Hull House (later settlement additions/reconstruction) are clear priorities.
- Expand industrial coverage through city directories, industrial histories, tax/deed records, and period advertisements. Andreas's narrative favors civic, institutional, hotel, church, school, bridge, railroad, and entertainment landmarks over the ordinary industrial and residential stock.
- Add a structured image table: `media_id`, `building_id`, `depicted_date`, `view_direction`, `creator`, `repository`, `source_url`, `rights`, `local_path`, `caption`, and `confidence`.
- Compare every address with the 1857 Palmatary view and later fire-insurance maps; record georeferencing uncertainty in meters rather than supplying invented coordinates.

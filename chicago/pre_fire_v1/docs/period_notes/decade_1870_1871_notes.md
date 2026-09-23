# Chicago construction, 1870–October 9, 1871

## Deliverable status

This tranche is a defensible inventory of **41 individually identifiable buildings, alterations, works, and major infrastructure projects** completed or materially underway from 1870 through the Great Fire. It is suitable for import and source-key joining. It is not a claim that every anonymous dwelling, shed, stable, shop, or rear building erected in those 21 months has been recovered: no surviving source consulted provides such a parcel-level construction register, and the fire destroyed records along with buildings.

Files:

- `decade_1870_1871_buildings.csv` — 41 records, 25 columns, schema-matched to the 1840s tranche.
- `decade_1870_1871_sources.csv` — 13 source records, 12 columns.
- `loc_1871_burnt_district_map.jpg` — 3,478 × 2,220 Library of Congress derivative for fire-footprint work.

Validation completed August 3, 2026:

- Every building row has exactly 25 columns.
- Every source row has exactly 12 columns.
- All `source_keys` resolve to the source table.
- Record IDs are unique.
- No aggregate fire-loss number was expanded into invented named-building rows.

## Snapshot statistics

The 41 records contain:

- 18 projects completed in 1870 and 18 completed in 1871.
- 3 projects explicitly still under construction with no completion year placed in the snapshot.
- 2 projects begun by the fire but completed after it (1872 and 1873); their post-fire dates are retained only to prevent a false pre-fire completion.
- 24 high-confidence, 14 medium-confidence, and 3 low-confidence rows.
- 24 rows needing no present review and 17 deliberately flagged for follow-up.
- 7 buildings directly documented as destroyed in the Great Fire, plus the Drake Block destroyed in a separate September 1870 fire.
- 18 direct or strongly documented survivors; 2 projects surviving while under construction; 1 surviving only as foundations; 1 damaged but not destroyed; and 11 records carrying more qualified fate labels.
- 7 extant resources in the current status field, 8 fire-destroyed resources, 13 later-demolished resources, 4 materially altered resources, and 9 whose eventual status remains unknown.

Largest type groups are 9 churches, 5 hotels, 4 transportation works, 4 water-main tunnels, 3 residences, 2 schools, 2 chapels, 2 colleges, and 2 rowhouses.

## Fire-fate method

`fire_fate_1871` intentionally distinguishes evidence strength:

1. **Direct narrative evidence** takes priority: `destroyed`, `survived`, or `damaged-not-destroyed` is used where Andreas or an official landmark record states the outcome. Examples include the Bigelow House, Palmer House I, Michigan Avenue Hotel, Lincoln School, First Congregational Church, and LaSalle Street Tunnel.
2. **Construction-stage evidence** is preserved: `survived-foundations` and `survived-under-construction` prevent a later finished building from being projected backward into October 1871.
3. **System-loss silence is not called survival**: the four water-main tunnels use `no-destruction-reported` because Andreas itemizes water-system losses without naming the tunnels as destroyed. This remains weaker than a direct survival statement.
4. **Spatial evidence is qualified**: `outside-fire-area` is used only for the offshore breakwater. For far South or West Side properties, map position supports the narrative but is not substituted for it where a direct later-use statement exists.
5. **Unresolved means unresolved**: five records remain `uncertain`; none has been forced into a binary fate.
6. The local fire map is oriented with north to the right. Any GIS use must rotate/georeference it before point-in-polygon classification.

The fire-footprint base is R. P. Studley Company's *Map showing the burnt district in Chicago*, held by the Library of Congress (`LOC_BURNMAP`). The Chicago History Museum exhibit (`GCF_BURNTDISTRICT`) is a useful interpretive cross-check but its item images are not open-reuse media.

## Aggregate stock and loss evidence — kept separate

The digitized contemporary loss account reports:

- 2,124 acres burned, about 3 1/3 square miles.
- 17,450 buildings destroyed.
- 98,500 people rendered homeless.
- About 3,650 buildings destroyed in the South Division, including 1,600 stores, 28 hotels, and 60 manufacturing establishments.
- Of 13,800 buildings in the North Division, no more than 500 remained; the account therefore reports 13,300 in ruins and 74,450 North Division residents homeless.

Those figures are aggregate evidence, not a name list. They must remain in a city/year or fire-impact aggregate table. Creating 17,450 placeholder “buildings” would imply names, locations, dates, and identities the sources do not supply.

Andreas contributes additional stock indicators for 1870–71:

- 139,705 feet of sewer were built in 1870 and 78,166 feet in 1871.
- Nineteen and one-half miles of wooden pavement and more than 41 miles of sidewalk were laid in the year ending March 31, 1871.
- Four water-main tunnels were completed and put into service.
- The Great Fire destroyed 10 city-owned school buildings according to the narrative, although the printed list immediately following names only 7 and totals them at $249,780. The discrepancy must be resolved from Board of Education reports before generating the three missing identities.
- The fire damaged nearly three miles of water-service pipe and caused reported total water-system damage of $248,910.

The Encyclopedia of Chicago notes that the fire burned less than one quarter of the city's built-up area. That is an important corrective to the common but false mental model that all of Chicago burned.

## Notable lifecycle cases

- **Drake Block**: completed in spring 1870 but destroyed September 4, 1870. It is `not-present` in the October 1871 fire snapshot.
- **Palmer House II**: only foundations existed at the fire. Its 1873 completion is not counted as 1871 construction.
- **Grand Pacific Hotel I**: walls at full height and a substantial roof, but not an operating hotel when destroyed.
- **Chicago Nursery and Half-Orphan Asylum**: lacked doors, heat, and full plastering; the fire stopped two blocks south.
- **St. Patrick's Church**: a pre-existing church was on lifting screws while a stone basement was inserted. This is an alteration record, not a new 1871 church.
- **City Hall/Court House**: two wings and an additional story completed in 1870 are represented as a lifecycle event on the 1853 structure.
- **Hitchcock House**: now in Chicago, but Austin was an independent suburb in 1871. It is retained for future-city-footprint modeling and must not be counted in 1871 municipal totals.

## Known review queue

High-priority follow-up:

1. Obtain the individual National Register nominations for the Story-Camp Rowhouses and Swedish Club. Their official register identities are confirmed, but unit assignment and/or 1870 build dates currently depend on tier-3 summaries.
2. Check Board of Public Works annual reports for exact dates, crossings, and fire outcomes of the West Indiana and West Adams viaducts and the four water-main tunnels.
3. Resolve the internal date problem in Andreas's Oakland/Langley Avenue Methodist account, which says construction began February 25, 1870 and dedication occurred August 6, 1870 but also places the lot purchase in spring 1871.
4. Locate the exact new site of Our Savior's Norwegian Evangelical Lutheran Church and a direct fire-fate statement.
5. Confirm the unit-to-owner mapping for 1526 and 1528 West Monroe before assigning individual modern addresses to the Story and Camp rows.
6. Reconcile the 10 destroyed city schools against the 7 explicitly enumerated in Andreas.

The supplied chronology's “Erie Street Row” was not imported into this tranche: available preservation literature commonly dates that row after the Great Fire. It should stay excluded until a primary property record proves an 1870–71 component.

## Map-by-year extension

A building CSV alone cannot reconstruct “what the land looked like.” The city model should use versioned spatial layers:

| Layer | Minimum fields | 1870–71 starting source |
|---|---|---|
| City boundary | `geometry`, `valid_from`, `valid_to`, `source_key`, `confidence` | municipal maps and annexation records |
| Shoreline / filled land | same plus `change_type` | harbor map in Andreas pp. 71–72 and federal harbor reports |
| River and canals | centerline/polygon geometry plus navigation status | Board of Public Works and harbor maps |
| Streets and blocks | historical name, modern name, geometry, opening/paving dates | 1870 city map and Andreas street-improvement table |
| Railroads and yards | operator, track/yard geometry, valid dates | 1870 maps and railroad annual reports |
| Built-up extent | polygon, survey year, derivation method | georeferenced city maps |
| Fire footprint | polygon, start/end timestamps, source | Studley burnt-district map |
| Buildings | point first; footprint polygon when available | this and earlier/later decade CSVs |

Recommended technical sequence:

1. Georeference the LOC Studley map against stable river bends and street intersections.
2. Digitize the 1871 burn polygon with an uncertainty band rather than a falsely exact edge.
3. Add an 1870 shoreline/harbor layer, including the 1,450-foot new breakwater segment and the then-existing Illinois Central lakefront works.
4. Join building points by historical intersection, retaining unresolved addresses without invented coordinates.
5. Generate yearly views from `valid_from <= year` and (`valid_to` is null or `valid_to >= year`), with construction-stage symbology distinct from completed buildings.

## Media and reuse

- `loc_1871_burnt_district_map.jpg`: Library of Congress states Geography and Map Division digitized content is free to use and reuse unless a contrary advisory appears. Credit “Library of Congress, Geography and Map Division.”
- Andreas volume/page images: public-domain 1886 publication; retain Internet Archive and page citations.
- Library of Congress LOT 12054 fire stereographs: catalog says “No known restrictions on publication”; retain photographer/publisher credit for each selected image.
- City of Chicago landmark photographs: metadata may be cited, but the page is copyrighted; do not copy photographs without permission or an independent open-rights copy.
- Chicago History Museum fire-exhibit images: item pages state all rights reserved and direct users to Rights & Reproductions. Use for research unless licensed.

## Interpretation limit

The word “comprehensive” is achievable only as a documented, iterative research program. This tranche is comprehensive for the clearly identifiable 1870–fire projects found in the principal city history and selected official landmark sources, with uncertainty exposed. It is not defensible to call it a complete census of every building standing or erected in Chicago. The correct next expansion is directory-, permit-, tax-, insurance-map-, newspaper-, and parcel-level reconciliation, retaining source provenance and negative evidence at every step.

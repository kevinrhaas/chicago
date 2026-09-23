# Chicago buildings and built structures, 1840–1849

## Scope and result

This research pass identifies **60 source-documentable records** completed, erected, substantially rebuilt, newly occupied, or begun in Chicago during 1840–1849. It is designed for later merger into a longitudinal building database. It is not a claim that only 60 buildings existed or were erected.

The inventory deliberately includes bridges, waterworks, a stockyard, temporary hospitals, and coordinated building blocks because the larger project aims to reconstruct Chicago's built form by year. Adaptations, relocations, and use-only evidence are retained only when the source clearly identifies the premises, and those rows are marked `needs_review=true` where original construction is not proved.

The two CSV files are valid RFC-style comma-separated tables:

- `decade_1840s_buildings.csv`: 60 records, 25 fields, one row per identified building, structure, aggregate block, or lifecycle event.
- `decade_1840s_sources.csv`: 10 sources and map/media repositories, with exact URLs and locators.

## Why this cannot be “all buildings with certainty” yet

Norris' 1846 directory reports **711 buildings erected during the preceding year**, alongside 32 large brick business blocks, two large two-story brick public schools, and two colleges (printed pp. 5–9, 26, 29–32). The overwhelming majority of ordinary houses, sheds, workshops, and small stores in that count are not individually named in narrative histories. A complete parcel-level census would require at minimum:

1. every surviving annual directory, tax and assessment roll, subdivision plat, fire-insurance map or precursor, deed index, newspaper building notice, and city-council permit or improvement record;
2. entity resolution across changing street numbers, renamed streets, moved wooden buildings, shared commercial blocks, and successive buildings on the same parcel;
3. spatial comparison against the 1871 fire perimeter and documented fire-loss lists; and
4. negative-evidence recording so that “not found” is not silently converted into “did not exist.”

Accordingly, this file should be described as a **named/source-identifiable inventory**, not a census. It substantially improves the supplied timeline, but claiming total completeness would be historically indefensible.

## Summary statistics

### Record quality

- 60 total records.
- 43 have an exact completion year; 16 are approximate; 1 represents a known 1842 city-hall use in a building whose construction year remains unknown.
- 38 records are high confidence, 21 medium, and 1 low.
- 40 are flagged for review, usually because later demolition, move, exact parcel, or construction-versus-occupancy evidence remains unresolved.
- 23 have a documented or approximately documented demolition before 1871.
- 1 record began in the decade but completed later: Second Presbyterian's stone church, begun in 1849 and dedicated in 1851.

### Completion year represented

| Completion year | Records |
|---:|---:|
| 1840 | 6 |
| 1841 | 1 |
| 1842 | 7 |
| 1843 | 6 |
| 1844 | 10 |
| 1845 | 3 |
| 1846 | 7 |
| 1847 | 3 |
| 1848 | 9 |
| 1849 | 7 |
| 1851 | 1 (begun 1849) |

These are database-record counts, not construction totals. The 1844 commercial-block rows are aggregate records: one row represents four separately owned stores and another represents five component buildings.

### Main building types

- 18 religious buildings when the cathedral is combined with the 17 `church` rows, plus 1 synagogue.
- 6 schools and 2 college/seminary records.
- 5 hospitals, including emergency and isolation structures.
- 4 hotels.
- 3 factories, 2 foundries, 2 packing houses, 1 brewery, 1 flour mill, and 1 grain elevator.
- 2 bridges, 1 waterworks, 1 railroad depot, 1 stockyard, and several civic/commercial complexes.

### 1871-fire field

- `destroyed`: 6 records with sufficiently direct support.
- `probably destroyed`: 10 records where location lies in the burned district but this pass lacks an individual loss citation.
- `survived outside main fire zone`: 5 records; this describes spatial exposure, not proof that the building survived to a later date.
- `not present`: 26 records demolished, burned, relocated, or superseded before October 1871.
- `uncertain`: 13 records.

The spatially inferred categories must not be promoted to documented fire fates until joined to a reliable 1871 fire-perimeter layer and an individual building-loss source.

## Important conflicts preserved in the data

### First steam grain elevator

Andreas' manufacturing narrative credits R. C. Bristol with a steam elevator erected in 1848 (printed pp. 580–581), while a biographical passage credits George Steel with the first steam elevator, places it at North Franklin Street and the river, gives a 100,000-bushel capacity, and says it burned about 1854. The database keeps one low-confidence disputed record rather than inventing two certain “firsts.” This should be resolved using contemporary newspapers, directories, railroad records, and the George Steel papers if available.

### University of St. Mary of the Lake

One Andreas passage says a building and seminary attachment were completed in June 1845, but the detailed chronology says foundations began October 17, 1845, the structure was under roof November 22, and it opened July 4, apparently 1846. The row uses `year_started=1845`, `year_completed=1846`, and retains the conflict in notes.

### Construction versus establishment

James Carney's brewery, Scoville & Sons, Nugent & Owens, and the two Charles Cleaver factory sites are documented as establishments or relocations, not always as newly erected buildings. Their completion precision is therefore approximate and review remains required. These records are still valuable for a year-specific land-use model.

### Commercial-block granularity

The 1844 improvement summary identifies a coordinated four-store block owned by Peck, Robbins, High, and Magie and a five-building block owned by George Smith. The present file uses one aggregate row for each group because individual parcel identities are not yet established. A parcel-resolution pass should split them only when the evidence supports unambiguous component identities.

## Mapping and year-by-year city model

The strongest immediately usable 1840s base is the **Rees & Rucker Map of Chicago and Vicinity (1849)**:

- Encyclopedia of Chicago authoritative presentation: <https://www.encyclopedia.chicagohistory.org/pages/10343.html>
- Chicago History Museum catalog metadata, entry 31: <https://chsmedia.org/media/fa/fa/LIB/CityChicagoMapsAccessible.htm>
- Public-domain high-resolution scan, 4,973 × 6,601 pixels: <https://commons.wikimedia.org/wiki/File:1849_Rees_%26_Rucker_Map_of_Chicago_and_Vicinity.jpg>
- Chronological map index: <https://www.encyclopedia.chicagohistory.org/misc/mapsChrono.html>

Recommended map-model fields for the parent database:

| Entity | Minimum fields |
|---|---|
| `map_source` | map id, title, surveyed/drawn/published year, creator, publisher, scale, dimensions, repository, stable URL, rights, georeferencing error |
| `city_boundary_version` | effective date, legal source, polygon, annexation event, predecessor id |
| `shoreline_version` | effective year or range, source map, uncertainty, polygon/line geometry, fill/erosion event |
| `street_segment_version` | historical name, modern name, valid-from/to, source, geometry, confidence |
| `parcel_or_block_version` | subdivision, block, lot, valid-from/to, geometry, source |
| `building_footprint_version` | building id, valid-from/to, footprint, height/stories, source map, geometry confidence |
| `event` | construction, enlargement, move, fire, demolition, change of use, date precision, source |

For annual display, do not create 1840–1849 as ten independent hand-drawn maps. Georeference each authoritative source map once, digitize dated boundary/shoreline/street/parcel changes as versioned geometries, then render the state valid on December 31 of the requested year. This preserves uncertainty and avoids falsely implying annual survey precision.

The 1849 map can be georeferenced using stable street intersections and canal/river geometry, with shoreline control treated separately because the lake edge and river mouth changed. The National Park Service report containing “Map of Chicago Showing Original Subdivisions 1830–43” is a useful earlier subdivision control: <https://npgallery.nps.gov/GetAsset/41508ccc-7577-4233-b32c-bc2fae896028>. The University of Chicago's Mapping Chicagoland collection is another candidate repository: <https://www.lib.uchicago.edu/collex/collections/mapping-chicagoland-collection/>.

## Public-domain image candidates

The 1849 Rees & Rucker scan is the clearest ready-to-use cartographic image and is marked public domain on Wikimedia Commons. Andreas volume I is also public domain and contains useful period illustrations; candidate printed pages include:

- City Hall/Saloon Building, around printed pp. 180–181.
- First waterworks, around printed pp. 185–188.
- 1849 flood and bridges, around printed pp. 198–200.
- St. Mary's, printed pp. 291–292.
- First Baptist and Tabernacle Baptist, printed pp. 316–320.
- First Methodist, printed pp. 325–327.
- First Universalist and First Unitarian, printed pp. 343–345.
- Rush Medical College, printed pp. 464–466.
- Early hotel illustrations, printed pp. 633–636.

Source item: <https://archive.org/details/historyofchicago01andr>. Extracted images should retain item identifier, printed page, scan-page identifier, caption, and rights statement. Do not treat an illustration as an exact measured elevation unless the source says it is.

## Recommended next research passes

1. Transcribe and reconcile every named improvement in the 1844 and 1846 directories and surviving 1840–1849 newspapers.
2. Build a historical-street-name authority table before geocoding. Indiana, Cass, Pine, Wolcott, North Street, South Water, and other names require date-bounded mappings.
3. Join tax/assessment rolls and deed indexes by block and lot, not only street address.
4. Split aggregate commercial blocks after parcel ownership is confirmed.
5. Add a separate `building_event` table; several current rows are alterations, relocations, or first documented uses rather than original completions.
6. Assign coordinates only after historical intersection and parcel georeferencing. This pass leaves latitude/longitude blank to avoid modern-geocoder false precision.
7. Verify every probable 1871 loss against the fire perimeter and a contemporary loss list.

## Reliability conventions

- `high`: the cited source directly states the building, date, and enough identity/location detail to distinguish it.
- `medium`: building identity is sound but construction date, exact parcel, or later lifecycle is inferred or secondary.
- `low`: a material attribution conflict remains unresolved.
- `needs_review=true`: at least one material database field still requires a better source; it does not mean the row should be discarded.

All factual rows include at least one `source_key`. The source CSV provides stable URLs, reliability tiers, locators, access date, and rights notes.

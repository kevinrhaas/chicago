# Chicago structures of the 1830s: research notes

## Scope and result

This tranche contains **56 source-identifiable structures, building groups, or major infrastructure works** begun, completed, or documented as active in 1830-1839. One additional record—the second Tremont House—began in December 1839 and was completed in May 1840, so it is retained with an explicit cross-decade note.

The dataset is a **named/identifiable-structure census, not a literal census of every ordinary dwelling or shanty**. No surviving source located in this research names every building. Andreas reports more than 150 houses, stores, and shanties erected in spring and early summer 1834, mostly in Canal Section 9, without identifying them individually. His 1837 census reports 398 dwellings, four warehouses, ten taverns, five churches, and many commercial establishments. Those aggregate counts demonstrate that any claim of certainty about “all buildings” would be false unless parcel deeds, tax rolls, construction permits where available, directories, probate files, and archaeological records are exhaustively linked at the lot level.

The present CSV therefore distinguishes:

- exact or tightly dated construction;
- `active_by` records that establish only a latest possible date;
- grouped records where the source names multiple buildings but not individual occupants or parcels;
- field-level inference, especially for the 1871 fire fate;
- infrastructure/site records needed for a future year-by-year city model.

## Quantitative summary

There are 56 records:

| Metric | Count |
|---|---:|
| High-confidence records | 32 |
| Medium-confidence records | 23 |
| Low-confidence records | 1 |
| Exact completion dates | 23 |
| Active-by dates | 14 |
| Other approximate/range dates | 18 |
| Incomplete construction attempt | 1 |
| Residential houses | 8 |
| Hotels or hotel/taverns | 10 |
| Churches | 4 |
| Schools | 3 |
| Foundries/factories/mill/industrial structures | 9 |
| Known demolished before 1871 | 10 |
| Explicit or source-supported 1871 destruction | 2 |
| Demonstrated 1871 survivors | 6 |
| Not exposed to the 1871 fire because already gone/replaced | 17 |
| 1871 fate still unknown | 31 |

The demonstrated survivors are the Green Tree Tavern, Western Hotel, Clarke House, state-line marker, canal-origin site, and the relocated 1839 Lake Street business block. The two fire-destruction records are Lake House and the William B. Ogden House; the latter is explicitly marked as an inference because Andreas says it stood at the time of the fire and that the fire destroyed nearly every pre-1838 structure, rather than giving a building-specific destruction sentence.

Completion-year distribution (with `active_by` records assigned to their documented latest year) is: 1831: 4; 1832: 2; 1833: 9; 1834: 6; 1835: 4; 1836: 6; 1837: 16; 1838: 4; 1839: 3; 1840: 1; no completed year because construction failed: 1. The apparent 1837 peak partly reflects Van Osdel's retrospective inventory of brick buildings standing that spring, not necessarily a construction boom confined to that single year.

## Important corrections to inherited assets

1. **“Miltimore's Folly” does not belong in 1833.** Andreas identifies the permanent Dearborn School carrying that nickname as a 1845 building. Chicago did have a privately financed purpose-built public schoolhouse in 1835 and a temporary city-owned schoolhouse in fall 1836; both are separately recorded.
2. **First Baptist did not have its own church building in 1836.** The congregation met in Temple Building in 1833; Andreas dates its own first church to 1844-45. The inherited 1836 First Baptist structure was excluded.
3. **First Methodist dates to 1834, not 1836.** A June 30, 1834 contract gives builders, dimensions, and cost. The frame church was moved across the river on scows in summer 1838.
4. **The first lighthouse had two construction episodes.** A 50-foot 1831 tower collapsed before completion on October 30; Samuel Jackson completed a replacement 40-foot lighthouse in 1832. Treating both statements as one building hides the failed construction event.
5. **The South Branch bridge date is internally inconsistent.** Andreas's detailed narrative says Anson and Charles Taylor built it in 1832, while a chronological index suggests 1830. The detailed 1832 account is retained and `needs_review=yes`.
6. **The second Tremont is cross-decade.** Work began in December 1839, but completion occurred May 20, 1840. It is included because the decade scope includes starts as well as completions.

## Source and confidence method

The primary backbone is A. T. Andreas, *History of Chicago*, volume I (1884). Although retrospective, it includes transcribed minutes, directories, resident testimony, contracts, dimensions, costs, and detailed institutional histories. Claims were cross-checked against current City of Chicago landmark records and the scholarly *Encyclopedia of Chicago* where possible.

Confidence means:

- **high**: clear structure, date, and identity in a detailed source; usually corroborated or supported by unusually specific evidence;
- **medium**: the structure is verified, but construction date is only `active_by`, location/fate is incomplete, or sources conflict on a secondary attribute;
- **low**: the source proves a brick building associated with an owner, but use, address, and date are too sparse for confident entity resolution.

`needs_review=yes` is intentionally broad. It commonly means the exact modern parcel, demolition date, architect, or fire fate is unresolved; it does not necessarily cast doubt on the structure's existence.

## 1871 fire modeling

Do not convert the 31 `unknown` fates to “destroyed” merely because they were early. A rigorous fire-fate field requires two joins:

1. determine whether the structure still existed at its pre-fire location on October 8, 1871; and
2. intersect that location with the accepted Great Fire burn perimeter.

Relocation is decisive. Green Tree and Western Hotel remained standing after the fire; the unnamed 1839 Lake Street business block survived because it had been moved to State Street near Twelfth. Clarke House and the boundary marker were outside the burn district. Conversely, many 1830s structures had already burned, been replaced, or been removed.

Recommended next sources are 1844, 1846, 1850s, 1866, and 1871 directories; Sanborn and Rascher fire-insurance/base maps where chronologically applicable; Cook County tract books and deeds; Board of Public Works records; church minutes; and Andreas volume II for later disposition.

## Map-by-year extension

The future city model should separate four linked feature classes:

1. `yearly_land_extent`: shoreline, river channels, sandbars, wetlands, prairie, dunes, and filled land;
2. `yearly_boundaries`: town/city limits, additions, subdivisions, public reservations, and canal lands;
3. `yearly_networks`: trails, streets, bridges, piers, canal excavation, and wharves;
4. `structure_instances`: the building CSV joined to a stable structure ID, geometry, valid-from year, valid-to year, and move/alteration events.

Each geometry should have `valid_from`, `valid_to`, `geometry_precision`, `georeference_method`, `source_key`, and `confidence`. A structure that moves must generate a location event rather than silently overwriting its old address. Historical street renaming also needs a crosswalk: South Water to Wacker Drive, Cass to Wabash Avenue in the relevant segment, Market to the later Wacker corridor, and Twelfth to Roosevelt Road are examples, but every conversion should be date-bounded.

The best initial georeferencing stack is:

- Andreas's **Map of Chicago in 1830** for shoreline, river morphology, trails, and scattered structures;
- the **1834 Chicago map** listed by the *Encyclopedia of Chicago* for emerging streets and settlement;
- the **1836 Canal Commissioners map** for canal lands and street/shore context;
- the **1838 Fort Dearborn Addition map** for federal reservation subdivision and lakefront geometry;
- modern Chicago street-centerline and parcel data as the target coordinate framework, with visible historical intersections used as control points.

Do not treat any reconstructed 1830 map as survey-perfect. Andreas published his reconstruction in 1884; positional error should be stored explicitly, ideally as a meter estimate or categorical uncertainty. Shoreline and river features should be digitized as time-specific geometries rather than used as permanent basemaps.

## Media and map candidates with rights status

| Candidate | Source/location | Intended use | Rights assessment |
|---|---|---|---|
| Map of Chicago in 1830 | Newberry digital item `NEWBERRY_MAP1830` | Primary 1830 georeferencing layer and overview image | Marked No Copyright–United States and open access; credit Newberry Library |
| 1830 Map of Chicago download | Wikimedia Commons `COMMONS_MAP1830` | Convenient web/download derivative | Public domain in the United States; preserve source attribution |
| Andreas building engravings | Internet Archive scan, printed pp. 177, 291, 326, 335, 631-634 | Courthouse, St. Mary's, Methodist, St. James, Dearborn bridge, Sauganash, Green Tree | Book is public domain; record printed page and Internet Archive identifier in image metadata |
| Andreas extra-illustrated collection | CPL finding aid `CPL_ANDREAS_INVENTORY` | Leads for Clybourn house, Thompson plat, 1830 river mouth, early churches | Finding aid is accessible; individual image reproduction rights must be checked before copying |
| 1834 map and circa-1830 settlement views | *Encyclopedia of Chicago* `EOC_MIDDLE_GROUND` | Georeferencing and visual context | Underlying Chicago History Museum object rights not established; link only pending permission |
| 1836 Canal Commissioners and 1838 Fort Dearborn Addition maps | *Encyclopedia of Chicago* `EOC_EARLY_LAKESHORE` | Boundary, canal-land, and lakefront reconstruction | Underlying object rights require repository review; link only pending permission |
| Clarke House and boundary-marker photos | City landmark pages | Extant-condition reference | City-page photograph reuse terms are not stated; do not redistribute without confirmation |

For every downloaded media asset, create a sidecar row with `media_id`, `structure_id`, `title`, `creator`, `date_depicted`, `date_created`, `repository`, `source_url`, `license_or_rights`, `credit_line`, `downloaded_filename`, and `checksum_sha256`. No restricted or uncertain-rights image was copied into this tranche.

## Remaining research queue

- Resolve the exact address and fate of New York House, Peter Pruyn's building, Frontless Block, and the two North Water Street stores.
- Check the 1839 Chicago directory at page-image level for Granger and Rankin address discrepancies and for whether named manufacturers occupied purpose-built structures or generic premises.
- Trace courthouse, jail, engine house, Temple Building, first Presbyterian, first Methodist, and first St. Mary's through later city histories to establish demolition and relocation events.
- Parcel-link every address using Original Town, Kinzie Addition, Canal Section 9, and Fort Dearborn Addition plats.
- Add the many unnamed 1834 structures only as aggregate/statistical records unless a deed, tax record, directory, or archaeological source supplies a defensible entity identity.
- Create a separate `building_events.csv` for moves, additions, burns, reconstructions, and renamings; the Mansion House and early churches already demonstrate why one row cannot fully represent a changing physical object.

## Files

- `decade_1830s_buildings.csv`: normalized building/infrastructure rows with field-level evidence notes.
- `decade_1830s_sources.csv`: source registry and rights notes.
- `decade_1830s_notes.md`: methodology, corrections, statistics, fire analysis, map framework, media candidates, and research queue.

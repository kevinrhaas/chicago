# Chicago built environment, 1874 — research notes

## Scope and evidentiary standard

This tranche records named, source-identifiable Chicago buildings and materially documented built-environment events in calendar year 1874. It includes new buildings, post-fire reconstructions, additions, a temporary replacement boathouse, a theatre conversion, projects begun in 1874 but completed in 1875, and one metropolitan railroad-infrastructure phase. It does **not** turn annual permit totals or burned-building aggregates into anonymous building records.

“Comprehensive” here means comprehensive within surviving named and citable evidence examined in this pass, not a claim that every ordinary 1874 dwelling, shop, shed, or unpermitted structure has been recovered. No surviving source set supports certainty at that parcel-by-parcel level. Unknowns, date conflicts, occupancy/completion distinctions, and municipal-boundary ambiguity are retained rather than filled by inference.

## Method

- Searched Andreas, *History of Chicago*, vol. III, using the local OCR and then checked candidate passages in printed-page context. Relevant printed pages are enumerated in the source register.
- Independently checked supplied chronology leads against City of Chicago landmark records, the Old Town Triangle NRHP inventory, Chicago History Museum, the Encyclopedia of Chicago, institutional histories, and transcriptions of contemporary directories/newspapers/periodicals.
- Distinguished opening or occupation from construction completion. American Express has strong move-in evidence; Palmer House is retained as a disputed 1874 completion phase rather than silently equating its earlier opening with completion.
- Modeled replacements and retained fabric through `predecessor_or_rebuild_of`, especially for the Eye and Ear Infirmary, Fourth Presbyterian, Immaculate Conception, the Farragut boathouse, and post-fire county facilities.
- Used `construction_or_event_type` to avoid conflating a whole new building with an addition, conversion, start-year record, temporary building, or infrastructure phase.
- Left latitude/longitude blank. Historical-address reconciliation and geocoding should occur in a controlled later pass because several structures moved, addresses were renumbered, and some names recur at later sites.

## Validation and statistics

- Building/event rows: **25**
- Exact building-column width: **29/29** for every row
- Source rows: **21**
- Exact source-column width: **12/12** for every row
- Unique `year_record_id` values: **25/25**
- Missing source foreign keys: **0**
- Rows with `year_completed = 1874`: **23**
- 1874 start records completed in 1875: **2** (James Ward Public School original section; Holy Name Cathedral)
- Confidence: **17 high**, **8 medium**, **0 low**
- Review flags: **10 true**, **15 false**

Event-type distribution:

- new construction: 7
- completion phase: 4
- post-fire reconstruction: 2
- construction start: 2
- one each: complex completion/opening, completion/opening, replacement new construction, reconstruction, reconstruction around retained basement, addition, new auxiliary building, replacement temporary building, conversion/reopening, and infrastructure phase

The **23** 1874-completion value is a database filter, not an estimate of total citywide buildings erected that year. It mixes whole buildings with documented completion/reconstruction phases and therefore should not be interpreted as a permit count.

## 1874 stock, flow, fire, and code context

The NBER/FRED historical series reports **$5.8 million** in Chicago building-permit value for 1874 (current dollars), down from **$25.5 million** in 1873. This is an aggregate flow measure, not a count of buildings and not directly reconcilable to the named rows. It nevertheless confirms the sharp contraction after the immediate post-fire boom and the Panic of 1873.

Andreas reports that the November 23, 1871 fire-limit ordinance absolutely prohibited wooden buildings inside the established limits and prescribed interior-construction safeguards for large buildings. Enforcement and legacy fabric remained uneven. His account of the July 14–15, 1874 fire describes temporary frame structures and older “fire-traps” south of the business center, a revised loss estimate of **$3.845 million**, and a fire that stopped at newer, more solidly built blocks. The Board of Underwriters then pressed for rigid enforcement against frame structures, broader water mains, removal of wooden appendages, limits on combustible storage, and fire-department reorganization. The National Board of Underwriters' October 1 withdrawal resolution further pressured the city.

This geography matters. Jackson-Thomas and Race stood well outside the central fire-limit regime; the Wacker properties lay near an ordinance edge that still needs parcel-level reconstruction. The Calumet rail phase lay largely outside 1874 municipal limits and is explicitly review-flagged. `postfire_code_context` therefore avoids a blanket claim that the same rule applied everywhere.

## Supplied chronology reconciliation

Included or refined:

- Former Engine Company 27
- Charles H. Wacker and Frederick Wacker properties (with date/use conflicts preserved)
- Cook County Criminal Court and Jail
- Fourth Presbyterian Church
- Jackson-Thomas House
- James Ward Public School as a **1874 start / 1875 completion**, not an unqualified 1874 completion
- Second Presbyterian Church
- Stephen A. Race House
- Washington Block as **1873–74**
- St. Ignatius College west addition as an **addition**, not a new college building

Rejected or deferred after independent checking:

- **Alexian Brothers Hospital:** the Chicago post-fire hospital building dates to **1872**; the documented addition is **1888**. A 1874 Alexian building belongs to St. Louis, not Chicago.
- **John B. Sherman House:** independent chronology places construction in **1876**, outside this tranche.
- **Osborne & Adams Building:** stronger independent evidence calls it an **1872** building. A vendor page's “1872–1874” wording is insufficient to manufacture a separate 1874 phase without a permit, directory, or construction notice.
- **Mid-North District:** a district is not a single building event. Its identifiable 1874 components are recorded individually.
- **Nathaniel K. Fairbank House:** no sufficiently specific independent 1874 construction source was located in this pass; it remains in the follow-up queue rather than entering the CSV on the supplied chronology alone.

The Andreas hospital passage found in this pass concerns the **Illinois Charitable Eye and Ear Infirmary**, not the Chicago Hospital for Women and Children or Alexian Brothers Hospital; these institutions must not be conflated.

## Source limitations

- Andreas is near-contemporary and exceptionally useful, but retrospective, selective, and OCR-sensitive. It disproportionately captures institutions, prominent firms, churches, and later-successful enterprises.
- City landmark and NRHP inventories privilege surviving or designated properties and often collapse multiple construction phases into a date range.
- Chicagology reproduces valuable public-domain contemporary texts, but it is a secondary presentation layer. The next pass should capture the original Lakeside directory, Tribune, and *Land Owner* pages directly.
- Historical address systems changed. “Michigan Street” in the county-jail block is the present Hubbard Street; numbered street addresses also shifted after citywide renumbering.
- Demolition years and original architects remain unresolved for several industrial, school, and church rows.
- Palmer House, Frederick Wacker House, Charles Wacker/coach-house use, Ward School's original architect, and Holy Name's precise start evidence are intentionally review-flagged.

## Map and media candidates

1. **Samuel Augustus Mitchell Jr., “Chicago,” 1874** — David Rumsey Map Collection. Best planimetric base candidate from this pass: wards, railroads, streets/roads, waterways, and canals. The original is public domain; comply with Rumsey's digital-image attribution/use terms.
2. **Currier & Ives, “The City of Chicago,” ca. 1874** — Library of Congress, digital file `ppmsca.08968`. Bird's-eye context, useful for visual interpretation but not suitable as a georeferenced parcel base. LOC reports no known restrictions; retain the item rights advisory and credit line.
3. **“The City of Chicago, showing the burnt district,” Harper's Weekly, August 1, 1874** — Library of Congress. Public-domain event-layer candidate for the July fire. It should be georeferenced against the Mitchell street/ward map and tagged as an interpretive burned-area boundary.
4. **Frederick Wacker House photograph** — University of Illinois Library. Item record says `No Copyright–United States`; reusable with institutional/item attribution. Its metadata gives 1872–73, so the image record itself also documents the date conflict.
5. **City landmark photographs** — useful reference images for Engine 27, Jackson-Thomas, Race, Second Presbyterian, Washington Block, St. Ignatius, and Ward School, but rights/reuse terms must be confirmed before copying files into a public repository. Link-only treatment is safest until cleared.

No third-party image binaries were copied in this tranche. The source register preserves stable item pages and rights notes so a later media-ingest process can download only clearly reusable derivatives with creator, holding institution, source URL, rights statement, and checksum.

## Next research queue

1. Read the original 1874 Lakeside directory and Chicago building-permit ledgers to resolve addresses, architects, and owners for Hoyt, Meyer, Moody & Waters, Piper, First Congregational, and Immaculate Conception.
2. Search 1873–75 *Chicago Tribune*, *Inter Ocean*, *The Land Owner*, and trade journals for completion notices and construction starts, especially Palmer House and Holy Name Cathedral.
3. Reconstruct 1871 and post-July-1874 fire-limit polygons from ordinances; intersect every row against period parcel locations rather than modern addresses.
4. Georeference the 1874 Mitchell map, digitize the July fire polygon, and store provenance/control points/RMSE in a dedicated map-layer table.
5. Reconcile Wacker property deeds, permits, and the 1884 move/remodel to separate the 1836 coach-house footprint from its later residence phase.
6. Resolve the Nathaniel K. Fairbank chronology lead and determine whether it represents a documented 1874 building, a later Prairie Avenue house, or a misdated asset.
7. Add demolition, relocation, and successor-building records through Sanborn maps, Robinson fire-insurance atlases, permit indexes, and historical newspaper notices.


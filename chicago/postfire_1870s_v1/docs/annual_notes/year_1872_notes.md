# Chicago buildings, 1872: research and validation notes

## Scope and result

This year tranche contains **89 named, source-identifiable building or infrastructure records** associated with calendar year 1872. Of those, 72 have `year_completed=1872` and 71 have `year_opened=1872`. The remainder document construction starts, foundations, additions, phased completions, and reconstruction work that materially occurred in 1872 but finished in another year.

This is an evidence-backed roster, not a claim that every one of the 1,250 permits issued from December 1, 1871, through October 1, 1872 has been individually identified. The surviving published evidence does not provide 1,250 names and parcels, and anonymous buildings have not been invented to force the row count to match the permit total. This distinction is essential to any later claim of completeness.

Geographic scope is the 1872 city plus present-day Chicago where a row is explicitly flagged. The John and Clara Merchant House, then in Irving Park beyond the municipal boundary, is retained because it is now in Chicago; its `needs_review` flag preserves the historical-jurisdiction issue.

## Research method

1. Andreas, *History of Chicago*, volume III, was searched across the rebuilding summary, public-works chapters, religious institutions, hotels, manufacturers, and individual business histories. Printed pages were checked where OCR was ambiguous.
2. The official Chicago Landmarks dataset and individual landmark narratives were used for surviving 1872 resources. This dataset is authoritative for its designated properties but is not a citywide inventory.
3. The 241-page Chicagology rebuilding collection was crawled as a finding aid for named structures and contemporary newspaper notices. A row was accepted only when a page supplied a specific structure and an explicit 1872 construction or occupancy event. Records resting on that compilation alone are medium confidence and normally flagged for review.
4. Independent institutional histories were used where available, including the Board of Trade and First Methodist Church.
5. Dates were separated into start, completion, opening, and demolition fields. A later completion was not converted into a 1872 completion merely because work began during the year.
6. Rebuild relationships, post-fire-code context, and present-versus-historical geography were recorded explicitly rather than inferred from a modern address alone.

## Validation results

- Building CSV: 89 data rows; 29 columns on every row; 89 unique `year_record_id` values.
- Source CSV: 8 data rows; 12 columns on every row; unique `source_key` values.
- Referential integrity: every semicolon-delimited key in `source_keys` resolves to the source table.
- Confidence: 54 high and 35 medium; no low-confidence rows were admitted.
- Review flags: 43 clear and 46 flagged. Review flags primarily concern exact completion timing, historic address-to-parcel matching, uncorroborated architect/owner attributions, demolition dates, or the 1872 municipal boundary.
- Status: 65 demolished, 11 replaced, 8 extant-altered, 3 extant, and 2 removed.
- Event type: 50 reconstruction, 16 new construction, 8 construction phase, 5 construction start, 3 addition, and 7 records distributed among foundation, cornerstone/incomplete work, partial completion, partial reconstruction, and infrastructure installation.

The high proportion of demolished structures and review flags is expected for a year reconstructed from nineteenth-century notices. It is not a data error. Blank coordinates are intentional pending a defensible historical-address and parcel crosswalk.

## Annual stock and construction-flow evidence

Aggregate evidence is stored once in `annual_stock_estimates.csv` and is not duplicated as anonymous building rows. Key 1872 context is:

- Within six weeks of the fire, 212 permanent stone-and-brick buildings representing 17,715 feet of South Division frontage were underway.
- From December 1, 1871, through October 1, 1872, 1,250 permits were issued: 965 brick, 200 stone, 65 frame, and 20 iron buildings.
- The same permit table reports 284 one-story, 378 two-story, 226 three-story, 263 four-story, 88 five-story, 10 six-story, and 1 seven-story building, totaling 43,413 feet of frontage.
- Andreas reports 52,792 feet of rebuilt South Division frontage and an estimated $38,134,700 in South Division construction during the first post-fire year.
- The reported first-year construction cost for the whole burned district was $45,558,200 in nominal historical dollars.

These measures describe permit flow, prominent-building frontage, or estimated construction value—not the standing building stock on a single date. Andreas also states that the permit material table excluded temporary structures; his North Division frontage summary covered prominent buildings and omitted numerous cottages. Those definition differences must be retained in later statistical modeling.

## Post-fire code interpretation

The November 23, 1871 ordinance fixed fire limits and prohibited wood construction within those bounds, with additional interior requirements for large structures. Rows within the affected district record that context. `masonry` is not treated as synonymous with `fireproof`: Andreas criticized combustible interiors and mansard roofs in buildings then advertised as fireproof. No row is labeled fireproof solely because it was brick or stone.

## Exclusions and boundary decisions

- Anonymous permit records, temporary shanties, and ordinary unnamed cottages were not fabricated as building identities.
- Energy-reporting rows for `101 Grand` and `Field Elementary-CPS` were excluded because an owner-reported 1872 date was not corroborated by historical evidence. A duplicate modern owner record for the Page Brothers property was absorbed into the official landmark row.
- St. Adalbert's 1872 land purchase was excluded because land acquisition is not construction.
- A post-office conversion associated with a Methodist church was not added as separate 1872 fabric because the available chronology points to 1871 and does not isolate a distinct 1872 building event.
- Structures completed in 1873 or later appear only when a specifically evidenced 1872 start or construction phase exists. They are not counted among the 72 1872 completions.
- The Interstate Exposition Building was excluded from 1872. Its plans and construction belong to 1873 despite a misleading secondary lifespan label.

## Map and media references

- The 1872 C. F. Mayer / U.S. Army Corps of Engineers map at 1:20,000 is the preferred annual city-form reference. The Wikimedia Commons item is marked public domain and credits the American Geographical Society Library at the University of Wisconsin-Milwaukee. It can support city extent and street-pattern context, not parcel-level construction dating.
- The Andreas scan and the 1917 Board of Trade history are public domain.
- City landmark photographs have item-level credits and should not be assumed public domain merely because the accompanying facts are government data.
- The underlying nineteenth-century newspaper text and illustrations reproduced by Chicagology are generally old enough to be public domain, but each image needs provenance and item-level rights verification before reuse. Chicagology's modern page design and transcription should not be republished wholesale.
- The Preservation Chicago page on 720 N. Wells contains useful demolition documentation, but text and images require credit or permission review.

## Highest-priority next research queue

1. Verify the 35 medium-confidence commercial and industrial entries against original 1872 *Chicago Tribune*, *Land Owner*, city-directory, and permit-ledger page images.
2. Build a historical-address-to-modern-parcel crosswalk, then geocode only after street renumbering and corner descriptions are reconciled.
3. Search Board of Public Works permit ledgers, assessor books, Sanborn predecessors, and Chicago Public Library directories for the anonymous remainder of the 1,250 permits.
4. Complete demolition year and cause research for rows where only a later replacement or broad lifespan is known.
5. Resolve parcel-level construction phases within the Lake-Franklin Group, Delaware Building, and the several Farwell/Morrison commercial blocks.
6. Record image-level title, creator, repository, stable URL, date, and rights status before any media asset is added to a distributable package.

## Files

- `year_1872_buildings.csv` — named structure and infrastructure records.
- `year_1872_sources.csv` — normalized source register.
- `annual_stock_estimates.csv` — aggregate permit, frontage, material, height, and cost evidence shared across the decade.

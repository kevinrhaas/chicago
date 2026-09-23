# Chicago building and city-form research: 1873

## Scope and result

This annual tranche records named, source-identifiable Chicago structures with a documented 1873 completion, opening, start, construction phase, addition, conversion, or infrastructure event. It contains **53 records** supported by **23 source records**.

- 40 records have `year_completed=1873`; these include usable main edifices even when an explicitly unfinished element such as a church spire remained.
- 26 records have a documented 1873 start and 39 opened or entered use in 1873. These are overlapping sets and must not be summed.
- Event classification: 22 reconstructions, 14 new constructions, 4 construction starts, 2 occupancy-only events, 2 conversions, 2 infrastructure completions, and 7 other distinct phases/additions.
- Confidence: 43 high and 10 medium.
- Review flags: 23 true and 30 false. A review flag usually indicates unresolved address, exact completion boundary, demolition date, or parcel geometry; it does not mean that the named entity is fictional.
- Survival field: 45 demolished, 5 extant-altered, 2 extant, and 1 replaced. Many demolition years remain unknown even when loss is certain.

This is a source-bounded historical inventory, not a claim that every ordinary cottage, rear building, shanty, stable, or permit represented by aggregate municipal totals has been individually named. The historical evidence does not support that stronger claim.

## Method

1. Andreas volume III was searched both in OCR and by its topical chapters. The printed table on p. 144 was visually checked against the scan, correcting OCR that had dropped school names and transposed dates.
2. Construction, completion, opening, and occupancy were kept separate. The Matteson House is an occupancy-only 1873 record because its construction finished in late 1872; the Honoré Hotel is a construction-phase record because later evidence shows that the interior remained unfinished.
3. Pre-fire names were treated as predecessor identities, not as surviving fabric. Rebuilt hotels, churches, schools, newspaper premises, and the railroad depot are therefore explicit reconstructions.
4. The 1873 architecture summary in Andreas was checked against Everett Chamberlin's near-contemporary *Chicago and Its Suburbs*. Institutional histories, official City landmark records, contemporary catalogues, and transcribed newspaper notices supplied addresses, architects, dimensions, materials, and phase corrections.
5. The supplied chronology was treated only as a candidate queue. No row relies on it as its sole source.
6. Aggregate permit and rebuilding totals are intentionally excluded from named-building rows and belong in the package-level `annual_stock_estimates.csv`.

## Major corrections to easy chronology errors

- The fourth Tremont House, not a separate “Fremont House,” is the ornate $500,000 hotel in the 1873 architecture list.
- The Matteson House was finished in late 1872 and opened February 3, 1873; it is not counted as a 1873 completion.
- Farwell Hall's third incarnation belongs to 1874, confirmed by YMCA and National Park Service histories, so it is excluded here.
- The Gardner House opened in October 1872 and is excluded from 1873 completion counts.
- The Page Brothers Building is officially dated 1872; no 1873 phase was found.
- George Pullman's Prairie Avenue mansion was completed in 1876. Evidence of a possible 1873 start was not strong enough for admission.
- The surviving Washington Block was constructed across 1873-1874. Its 1873 row is a construction phase, not a completion.
- The Charles M. Netterstrom House carries the broad official range 1873-1894. The current evidence does not isolate a construction event to 1873, so no annual row was admitted.
- The Alexian Brothers' Hospital is directly stated by Andreas to have been completed in 1873, correcting supplied secondary chronologies that place it in 1874.

## Coverage highlights

The file includes the headline commercial rebuilds and hotels (Reaper, Lakeside, Times, Busby & Stuart, Tremont, Sherman, Grand Pacific, Palmer, Clifton, Briggs, Revere, Alhambra); the Michigan Southern/Rock Island passenger depot; federal and county public-building starts; the Industrial Exposition Building; religious and charitable rebuilding; five public-school buildings from the verified construction table; the Chicago Public Library's conversion of the surviving old water tank; the Bridgeport gas works; an asylum addition; a bridge; two water-tunnel projects; and the first limited South Park site work.

It also admits surviving post-fire mercantile fabric that broad narrative histories often omit: the Cole and Rowney buildings and the 1873 phase of Washington Block.

## Fire and code context

Andreas describes 1873 as the continuation of the extraordinary 1872 rebuilding campaign, followed by a comparative cessation after the Panic of 1873. Brick and stone predominated in the rebuilt core, but material labels are not treated as proof of complete fire resistance. The database preserves historical “fireproof” claims only as claims. The construction-stage fire in the Singer Building and the Jones School fire of 1874 are particularly useful counterexamples.

The municipal fire-limit ordinance and post-fire wall requirements affected much of the rebuilt business district, but structure-level compliance records were not found for every row. `postfire_code_context` therefore distinguishes documented systems, contemporary claims, general burned-district context, and cases where the code is not applicable.

## Validation

- Building CSV: 29 columns on every row; 53 unique `year_record_id` values.
- Source CSV: 12 columns on every row; 23 unique `source_key` values.
- All building `source_keys` resolve to the annual source table.
- No building has a blank canonical name or blank source field.
- No aggregate permit count was converted into fabricated anonymous entities.
- Empty values remain empty rather than being guessed.

## Source limitations

- Andreas (1886) is detailed but retrospective, and some tables contain typographic or OCR ambiguities. Printed-page inspection resolved the school table; unresolved chronology conflicts remain flagged.
- The City landmarks API is authoritative for designated landmarks only and cannot serve as a complete inventory.
- Chicagology is used as a finding aid to period directory and newspaper excerpts. Where it is the only accessible transcription, the relevant row is flagged or paired with a stronger source.
- Historical street numbering changed. Modern addresses are omitted where no reliable conversion was established.
- “Completed” in nineteenth-century narratives sometimes means externally complete, usable, or dedicated rather than every interior or decorative element finished.
- Demolition dates are much less completely documented than construction dates.

## Annual construction-flow evidence

Chamberlin's near-contemporary account says the building activity of 1872 continued through 1873 and identifies a set of structures finished in the year ending October 9, 1873. Andreas likewise states that the Panic of 1873 was followed by a comparative cessation of building. Neither source provides a complete named list of ordinary construction. Aggregate stock and permit evidence is maintained once at package level to avoid double counting.

## Map and media candidates

- **1873 Warner & Beers map:** the annual package already identifies a public-domain 1873 city map suitable for the year layer; it should be labeled with its actual publication date and not treated as parcel-perfect geometry.
- **Andreas printed p. 144 school table:** public-domain scan from Internet Archive; local research image `andreas_v3_p144.jpg` verifies Burr, Jones, King, Third Avenue, and Vedder Street dates and attributes.
- **Inter-State Industrial Exposition official catalogue (1873):** public-domain Library of Congress catalogue; photographs and individual Art Institute archive items require item-level rights review.
- **McCormick rebuilt-buildings print:** Wisconsin Historical Society record is a strong Reaper Block image lead, but reproduction terms require item-level clearance or purchase.
- **Historic newspaper and *Land Owner* engravings:** nineteenth-century source images are likely public domain, but the holding institution and exact scan credit must be recorded before copying.
- **Modern landmark photographs:** do not assume City metadata or a web page transfers copyright in a photographer's image. Use only items with an explicit open license.

## Explicit exclusions

- Ordinary unnamed permits, cottages, shanties, rear structures, and temporary commercial shelters lacking entity-level evidence.
- Page Brothers Building and Gardner House (1872 completions).
- Farwell Hall III (1874).
- George M. Pullman mansion (completed 1876; possible start needs stronger evidence).
- Charles M. Netterstrom House (official 1873-1894 range is too broad for a calendar-year event).
- Merchants' Loan & Trust Company Building: the bank occupied the Manierre Building from 1872; its named dedicated buildings are later.
- Park plans without a documented 1873 physical-work event. South Park is included only because a Library of Congress curatorial history identifies limited preliminary construction.

## Next research queue

1. Consult the 1873 and 1874 Chicago building-permit ledgers, tax assessment rolls, and fire-insurance atlases for entity-level addresses and owners.
2. Resolve Reaper, Times, Busby & Stuart, St. James Hotel, Grace Presbyterian, New England Chapel, and school parcel geometry.
3. Check Chicago Board of Education annual reports for exact opening dates, architects, and street locations of the five 1873 schools.
4. Verify the first Holy Trinity Polish church parcel and loss/replacement date in parish and archdiocesan archives.
5. Trace exact construction and completion dates for Cole, Rowney, First Methodist Church Block, and Washington Block from contemporary contracts or notices.
6. Create separate alteration events for later vertical additions rather than overwriting the 1873 fabric.

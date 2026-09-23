# Chicago buildings and construction events, 1877

## Scope and result

This tranche records 26 named or source-identifiable Chicago building, reconstruction, addition, conversion, infrastructure, and multi-year construction events materially documented in calendar year 1877. It follows the annual schema exactly and does not turn citywide permit totals into invented anonymous buildings.

The roster is comprehensive within the currently accessible published evidence, but it is not—and cannot honestly be labeled—a complete census of every physical building erected in 1877. Andreas reports 1,398 buildings represented by permits, while surviving published narratives identify only a small fraction by owner, name, or address. Closing that archival-identification gap requires the underlying municipal permit ledgers, assessment books, and systematic newspaper extraction.

## Method

- Searched Andreas Volume III across corporate history, public works, bridges, fire-alarm infrastructure, industry, institutions, and religious-history chapters; checked OCR in surrounding context rather than accepting isolated hits.
- Reconciled the City of Chicago landmark dataset with official landmark pages and contemporary newspaper notices for the Atwater Building and Erie Street Row.
- Used official/institutional histories for St. Stanislaus Kostka, the Chicago Historical Society, Woman's Hospital Medical College, and the Coast Guard exclusion check.
- Swept the 260-page Chicagology post-fire corpus for 1877 references, then retained only construction, reconstruction, addition, conversion, or a distinct material phase. Tenancy, opening, planning, and demolition-only references were excluded unless the event explicitly represented reuse or conversion; the WCA boarding-house row is marked occupancy-only and low confidence.
- Treated grouped evidence conservatively. The Michael Burke notice remains one two-store group row, and Erie Street Row remains one five-house complex record, rather than fabricating unit identities.
- Preserved conflicts in notes and set `needs_review=true` whenever address conversion, exact project identity, chronology, completion, or later fate needs primary-record confirmation.

## Validation

- Building/event CSV: **29 columns, 26 data rows**.
- Source CSV: **12 columns, 20 source rows**.
- Strict CSV parsing: every row has exactly the header width; no overflow keys.
- Record IDs: unique `CHI1877-001` through `CHI1877-026`.
- Source integrity: every semicolon-delimited `source_keys` value resolves to a key in `year_1877_sources.csv`.
- Controlled values: `confidence` is limited to `high|medium|low`; `needs_review` is limited to `true|false`.
- Blank values remain blank; zeroes and guessed coordinates were not substituted.

## Named-record statistics

| Measure | Count |
|---|---:|
| Total named/event records | 26 |
| Rows whose recorded completion year is 1877 | 17 |
| Documented 1877 phases with completion in another year | 6 |
| Phase/occupancy rows with no asserted completion year | 3 |
| High confidence | 17 |
| Medium confidence | 8 |
| Low confidence | 1 |
| Needs review | 16 |
| Review not presently required | 10 |
| Exact completion precision | 11 |
| Year-only completion precision | 10 |
| Circa or early-year precision | 2 |
| No completion precision asserted | 3 |

By building/event type, the roster contains five bridges; four churches; two factories; two communications-infrastructure projects; and one each of civic building, federal building, medical college, library/archive, commercial block, commercial building, store group, rowhouse group, mansion, hotel, boarding house, exposition-hall conversion, and waterworks commissioning.

Three recorded resources remain extant but altered: the Atwater Building, Erie Street Row, and St. Stanislaus Kostka Church. The surviving-status count is deliberately conservative; an unknown or replaced bridge fate was not guessed.

## Citywide 1877 construction-flow evidence

Andreas's printed p. 67 permit table reports the following 1877 totals:

| Permit measure | 1877 value |
|---|---:|
| Buildings represented by permits | 1,398 |
| Aggregate frontage | 35,033 ft |
| Nominal construction cost | $6,561,800 |
| One-story | 221 |
| Two-story | 828 |
| Three-story | 275 |
| Four-story | 62 |
| Five-story | 11 |
| Six-story | 1 |
| Brick fronts | 937 |
| Stone fronts | 461 |
| Stores/offices | 100 |
| Store/dwellings | 229 |
| Dwellings | 737 |
| Churches | 6 |
| Manufacturing buildings | 48 |

Derived descriptive values are about **$4,693.71 nominal cost per permitted building**, **25.06 feet of frontage per building**, and **2.154 stories per building**. These are arithmetic summaries of the aggregate table, not appraisals and not attributes assigned to named rows. The five listed use classes total 1,120, leaving 278 permitted buildings in other or unreported use classes. The six reported church permits likewise must not be forced into six individual identities: only four named church construction/addition records were sufficiently documented for this roster.

## Important source limitations and conflicts

- Andreas is near-contemporary and unusually detailed but is still a retrospective compilation; OCR defects require scan checking. The Custom House stonework end year and the Fullerton bridge cost wording need direct printed-page verification.
- Contemporary newspaper text on Chicagology is useful and often transcribes exact 1877 notices, but the modern compilation is a secondary access layer. Page-level newspaper scans should replace it where possible.
- St. Columbkille has a material chronology conflict: recent researched history places delayed completion/opening in 1877, while a 1916 diocesan souvenir says the church was erected in 1871. The row is retained as medium confidence and review-required.
- Woman's Hospital Medical College sources conflict between a faculty-financed 1877 building purchase and a later statement that the first building was erected in 1877. Deed, permit, and board records are needed before classifying it conclusively as purchase, conversion, or new construction.
- E. B. Williams and Michael Burke are documented in active construction in September 1877, but exact completion dates, architects, and modern parcels remain unresolved.
- Historical street numbering changed. Modern addresses are supplied only where supported or clearly labeled for review; most infrastructure coordinates remain blank pending georeferencing.
- Permit statistics record authorized or represented construction, not necessarily final completion, survival, or a one-permit/one-building relationship.

## Exclusions after review

- **Chicago Life-Saving Station:** official Coast Guard history dates the first Chicago station building to 1876, so no 1877 construction row was created.
- **Singer Building I / Singer Building II:** the first building's November 1877 loss is demolition-only; plans for its successor appeared in late 1877, but physical rebuilding began in 1878. The material Field & Leiter conversion of the Exposition Building is included instead.
- **Rush Medical College:** a secondary institutional claim for 1877 conflicts with a contemporary October 1876 completion/dedication account; excluded pending primary reconciliation.
- **Brand's Hall:** evidence places erection by 1874; an approximate 1877 label is not adequate.
- **Bohemian National Cemetery:** founding in 1877 establishes a landscape/institution, not a documented building-construction event.
- **St. Joseph's Church:** the 1876-1878 project likely continued through 1877, but no distinct 1877 material phase was located.
- **Halsted Street Opera House and Hale retail occupancy:** 1877 opening or tenancy evidence did not establish new construction or a documented conversion.
- **Ordinary permitted buildings:** no anonymous rows were generated from the 1,398-building total.

## Map and media package

The annual map reference is `MAP-1877-MITCHELL`, *Mitchell's plan of the city of Chicago, Illinois* (1877), approximately 1:31,680. A 3,453 × 4,266 public-domain scan is already stored at `work/final/chicago/postfire_1870s_v1/maps/images/1877_mitchell_map.jpg`. It is suitable for annual city extent, streets, river, shoreline, rail, and transport context; it does **not** show a systematic building-footprint inventory and remains `needs_georeferencing`.

The annual model should retain the generalized 1869-1889 legal city extent unless a statute-level boundary event is added, and should display the 26 named events separately from the citywide 1,398-building permit aggregate. This prevents the named-source coverage gap from appearing as literal empty land.

Other reusable media candidates:

- Andreas Volume III, printed p. 67 permit table crop at `work/final/chicago/postfire_1870s_v1/research/source_scans/andreas_v3_p67_permit_table.jpg` — public domain.
- Chicago Historical Society temporary-building illustration in the Society's 1906 institutional history — public domain when extracted from the Library of Congress scan.
- Perry H. Smith Mansion 1879 engraving and Atwater period views — likely public domain as historical works, but current hosted copies should not be redistributed until the original scan repository and item rights are documented.
- City landmark and Preservation Chicago photographs — link only unless an explicit reuse license or permission is obtained.

No uncertain-rights web images were copied into this tranche.

## Next research queue

1. Locate and transcribe 1877 building-permit ledgers or permit-index books at Chicago municipal archives; join owner, frontage, cost, use, and address to the 1,398-building aggregate.
2. Search every 1877 *Chicago Tribune*, *Inter Ocean*, and German-/Polish-language construction column with issue/page citations, prioritizing the six aggregate church permits and 48 manufacturing buildings.
3. Resolve Woman's Hospital Medical College through deeds, faculty minutes, and Cook County Hospital district maps.
4. Obtain primary 1877 notices for St. Columbkille and reconcile the 1871-versus-1877 construction chronology.
5. Resolve architect/owner/parcel details for Hotel Brunswick, E. B. Williams, Michael Burke's two stores, and the J. K. Russell factory.
6. Georeference the Mitchell map, historical bridge crossings, Court House Square, and Cass Street cable; create event-valid point/line geometries with uncertainty fields.
7. Cross-check the named roster against 1877 city directories, tax-assessment rolls, fire-insurance maps, Sanborn/Robinson predecessors, church archives, and federal annual reports.
8. Extract only clearly public-domain illustrations from repository scans and record item-level title, creator, date, source URL, rights statement, and crop provenance.

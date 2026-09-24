# The transient cohort of 1 July 1835

**T-1352**, piece 1 of **T-1178**. Who was in the town on the scene date and not of it: how many, who they were, and where they slept — each figure a range with its method and its comparanda, and no person written.

Derived file: `data/reconstruction/1835_transient_cohort.json`  
Candidate grounds: `data/reconstruction/1835_camp_grounds.json` (authored)  
Hulls in port: `data/reconstruction/1835_vessels_in_port.json` (authored) — seated to the reach, carrying nobody  
Built and gated by: `tools/model_transients_1835.py --build | --check | --self-test`  
Spent by: T-1353, which mints the cohort, and T-1214, which places the camps

---

## The tolerance, stated first

Every figure is a range with a stated method and a named comparandum, and where the record bounds nothing the row says so instead of carrying an invented number. The headline figure has NO point reading on purpose: the evidence supports a band and not a number, and a band is the answer.

It is an adjudication over committed claim records and committed derived files — no scan is opened here, and nobody is named, aged or housed. T-1353 mints the cohort; this file bounds it. Nothing here is evidence about any person, household or building, and no card may cite it.

## 1. How many

| Figure | Reading | Method |
| --- | ---: | --- |
| `residents_on_1_july_1835` | **2,353 – 3,265** (point reading **2,536**) | CARRIED, not derived. The town model's own reading, repeated here because the transient bracket is stated against it and a reader must not have to hold two files open to see what it is a fraction of. |
| `the_papers_own_estimate_13_june_1835` | **2,500 – 3,000** | The Chicago American of 13 June 1835, eighteen days before the scene: the actual population 'we cannot estimate with any degree of accuracy, but it is now supposed to be between 2500 and 3000'. An estimate that says it is one. The town model's point reading of 2,536 — built five years later out of a November census and an arrival distribution, and knowing nothing of this sentence — falls inside it. |
| `strangers_the_american_counts_separately` | **200 – 900** | The same sentence goes on: 'Strangers, to the amount of some hundreds more, fill our public houses and streets'. MORE — the paper puts the strangers OUTSIDE its own population estimate, which is the whole distinction this model is built on. The band is the phrase's own arithmetic: 200 is the least a plural of hundreds can carry and 900 the most, because an editor with a thousand strangers in his streets writes 'a thousand'. Turning the phrase into a band is a liberty and is recorded as docs/LIBERTIES.md L245. |
| `transient_persons_counted_at_chicago_1843` | **533** | The census of 1 August 1843, taken by Jas. W. Norris under the authority of the Common Council, prints `Transient persons` as a row of its own: 533 across six wards, in a printed total of 7,580. The only time Chicago's own enumerator counted the two populations apart, and the reason this model exists as a separate file. |
| `transient_rate_of_a_chicago_summer_1843` | **0.07564 – 0.20619** | TWO READINGS OF ONE CENSUS. The printed table puts 533 transient persons against 7,047 permanent ones, which is 7.56%; Norris's own remarks on the same census say every person not permanently residing was excluded and that counting them would have made the town 'undoubtedly 8,500', which is 920 more again and 20.62%. Whether those are the same people counted twice is not settled here. It is a rate and not a population, and it is taken on 1 August 1843 — a boom year, mid-season, and no land sale. |
| `named_purchasers_at_the_sale_the_layer_cannot_place` | **77 – 109** | MEASURED, and a floor three times over. The Public Domain Land Tract Sales register enters 232 purchases at Chicago on 26 and 27 June 1835 — four days before the scene — from 105 distinct purchasers, of whom the resident crosswalk can place only 28 in this town's own layer. Over June as a whole the figures are 141 and 32. It is a floor because a purchaser the crosswalk refuses is one the layer cannot NAME rather than one proved absent, because a man at a land sale travelled with agents and family, and because most of a land-sale crowd buys nothing at all. |
| `transients_on_1_july_1835` | **192 – 900** | FLOOR: 7.56% — the LOWER of the two 1843 rates above, the one Chicago's own enumerator printed — applied to this model's resident point of 2,536, which gives 192. The higher reading of the same census would give 523. It is a floor and not an estimate because 1 July 1835 is not an ordinary day: the federal land sale closed four days earlier, the navigation season was at its height, and the same enumerator says the crowd of 1835 inflated the town's own reckoning of itself by thousands. CEILING: 900, the most the American's 'some hundreds more' will carry, written in the town in the month itself. NO POINT READING: see the section's open questions — a draining sale crowd and a landing immigrant stream cross on this day in opposite directions, no committed source measures either, and a midpoint would be a number nobody could defend dressed as an answer. |

**Not claiming.** This section does not say that any named person was a transient, and the land-sale purchasers it counts are a measurement of the register rather than a roll of the crowd.

### the two candidate points

| reading | persons | argument |
| --- | --- | --- |
| twice the 1843 rate | 384 | 1 July 1835 is a land-sale week and 1 August 1843 was not, so the measured rate is doubled. The multiplier is invented and nothing in the record sets it. |
| the midpoint of the American's phrase | 550 | 'Some hundreds more' read at the middle of its own band. An editor's impression, printed eighteen days before the scene and before the sale crowd arrived. |
- **note** — T-1353 must spend a number and this model will not pick one for it. These are the two that can be argued from committed evidence; whichever it takes, it cites this table and says which.
- **unit** — persons, on 1 July 1835 — NEITHER is adopted here

### the land sale as the register prints it

| window | entries | purchasers | in the resident layer | not in it |
| --- | --- | --- | --- | --- |
| June 1835, whole month | 274 | 141 | 32 | 109 |
| 26-27 June 1835, the sale days | 232 | 105 | 28 | 77 |
- **unit** — entries and distinct purchasers, Chicago land office

### the ceiling this model refuses

- **line** — n1844_tf_029
- **what it says** — Norris, writing in 1844: in 1835 'the population of the place was said to amount to 5,500, a computation which probably included transitory persons, a great many of whom were here at the time. The actual population, however, that year, could not have been much less than 3000.'
- **the arithmetic it offers** — 5,500 less 3,000 is 2,500 transients, which would be a ceiling four times the one adopted here.
- **why it is refused** — Norris does not stand behind the 5,500 — it is what the population 'was said to amount to', nine years before he wrote — and the Chicago American, printing in the town in the month itself, put the WHOLE population at 2,500 to 3,000 with the strangers counted on top of it. A recollected rumour does not outrank a contemporary estimate, and the figure is recorded here rather than dropped so that a reader can disagree.

**Open questions.** These are recorded here and do not become tickets.

- This model declines a point reading, and that is a refusal rather than an omission. The sale closed on 27 June and the Democrat of 1 July says it 'has passed', so the sale crowd is leaving; the Marine Journal has vessels in with passengers on 28 and 29 June and again on 2 and 3 July, so the immigrant stream is still landing. Nothing committed measures the rate of either, and the answer is a band.
- The two readings of the same 1843 census disagree. The printed table carries 533 transient persons INSIDE a total of 7,580; Norris's own remarks on that census say every person not permanently residing was excluded and that including them would have made the town 'undoubtedly 8,500'. Whether the 533 and the ~920 are the same people counted twice or two different exclusions is not settled here, and the second reading would put the floor at 523 instead of 192.
- The floor derived from the 1843 rate sits just below the least value the American's phrase can carry (192 against 200). Two arguments that share no evidence landing that close together is the best corroboration this model has, and it is not a confirmation: both could be low.
- The register's residence column reads UNKNOWN on every June 1835 row, so a purchaser the crosswalk cannot place is a purchaser this project cannot name at Chicago — never a purchaser shown to have come from elsewhere.

## 2. Who they were

| Figure | Reading | Method |
| --- | ---: | --- |
| `vessels_lying_at_chicago_on_1_july_1835` | **4 – 6** | The Marine Journal of the Chicago American, 4 July 1835, three days after the scene. 6 vessels had arrived on 27, 28 and 29 June and were not entered as cleared before 1 July; two of them, the Philips and the Jesse Smith, cleared on the day itself, so 4 lay at Chicago at nightfall. The hulls are SEATED — 6 records in data/reconstruction/1835_vessels_in_port.json, each with the master, last port and cargo the column prints and a mooring that resolves to the reach and never to a deck — and this figure is re-derived from them. THE MODEL COUNTS VESSELS AND NOT MEN: no committed source gives the crew of a Great Lakes schooner of 1835, and multiplying a hull by a guessed complement would turn a reading into an invention. |
| `named_land_sale_purchasers_still_owed_a_bed` | **77 – 109** | The same measurement as the size section's floor, carried here as the one row of the composition that has a number at all. Every other row below is bounded by nothing committed and says so. |

**Not claiming.** This section apportions nobody between its rows and no row here is a quota.

### who the cohort was

| row | bounded | evidence | at the scene date |
| --- | --- | --- | --- |
| land-sale visitors and their agents | floor only | the register's own purchasers, 26-27 June 1835 | draining — the Democrat of 1 July says the sale has passed |
| immigrant families awaiting lots | no | the American, 13 June 1835: 'men, women and children just landed from the vessels', 'the unsheltered emigrants' | still landing — vessels in with passengers 28, 29 June, 2, 3 July |
| the harbour-works gang | no | the federal harbour improvement was at work through 1835; no committed source gives its strength in any month | at work |
| crews ashore | hulls only | the Marine Journal of 4 July 1835, seated hull by hull in data/reconstruction/1835_vessels_in_port.json, and joined to the two packets the newspaper register already carried as houses of trade (T-1425) | 4 to 6 vessels in port, named and mastered; nobody aboard |
| travellers of business and of state | no | the Democrat of 1 July 1835 names Lewis Cass, Secretary of War, arrived on the 29th in the steamer Michigan, 'among the numerous visitors to Chicago' | present |
- **unit** — rows of the cohort — `bounded` says whether anything committed sets a size

### the port on the scene date

| arrived | vessel | rig | master | from | cargo | cleared 1 July | house in the register |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1835-06-27 | Jesse Smith | schooner | Drurian | Green Bay | lumber | yes | none |
| 1835-06-27 | Philips | schooner | Howe | Milwaukee | not stated | yes | biz_the_chicago_and_st_joseph_packet_schooner_phillips |
| 1835-06-28 | Llewelling | schooner | Clark | cut from the column | passengers | no | biz_chicago_st_joseph_packet_schooner_llewellyn |
| 1835-06-28 | Hiram | schooner | Rathbourn | Michigan | lumber | no | none |
| 1835-06-29 | Whig | schooner | Day | cut from the column | merchandize | no | none |
| 1835-06-29 | an unnamed steamboat | steamboat | not read | cut from the column | passengers | no | none |
- **unit** — vessels, from the Marine Journal of 4 July 1835, re-derived from the seated hulls in data/reconstruction/1835_vessels_in_port.json

**Open questions.** These are recorded here and do not become tickets.

- Four of the five rows have no size and this model does not give them one. The harbour works were the largest employer in the town and their 1835 strength is not in any file this project holds; the Chief Engineer's annual report for 1835 would settle it and is named in docs/research/01-terrain-hydrology as the thing to find.
- A crew complement for an 1830s lake schooner would turn the port reading into a number of men. This model refuses to supply one from general knowledge; T-1353 seated no crews, and T-1372 seated the hulls and left them empty. Everything but the number is now in place — the vessels file names the hulls and the transient cards carry a `lodged_at` rung of kind `vessel` — so an enrolment return, a shipping article or a marine list that prints hands as well as hulls would finish it without anything being unpicked.
- The steamboat that arrived on 29 June is unnamed in the extraction; the Democrat of 1 July has Lewis Cass arriving that day in the steamer Michigan, and the American has the Michigan clearing on the 26th. The likeliest reading is that the two entries are the same vessel returned, and the model neither merges them nor claims they are distinct.

## 3. Where they slept

| Figure | Reading | Method |
| --- | ---: | --- |
| `sleeping_place_classes_the_sources_name` | **6** | Six, and each is a sentence in a committed source rather than a class this model invented: a room in a public house; the floor of that room; the floor of a private house; a store house thrown open; the open sky upon the wharves; a tent pitched at the landing. The vessels in port are a seventh place and are counted in the composition section instead, because a hull is a hull whether or not anybody slept in it. |
| `camp_ground_candidates` | **5** | The authored candidates file offers 5 grounds, of which 1 is graded documented — the landing place, where the American says the tents were pitched — and the rest conjectural. The file authors no coordinate: each candidate names the committed geometry its extent resolves from, and T-1214 places the camps. |

**Not claiming.** This section places no camp and gives no ground a capacity.

### where they slept

| place | source | says |
| --- | --- | --- |
| a room in a public house | the Democrat, 17 June 1835 | 'the immense congregation of strangers crowding every room of our public houses, and every room in which they can obtain accommodations' |
| the floor of that room | the Democrat, 17 June 1835 | 'even to the extent of sleeping on the floor' |
| the floor of a private house | hh_brown_rufus, on Mrs Rufus Brown's boarding house | 'full meant three in a bed sometimes, with the floor covered besides' |
| a store house thrown open | the American, 13 June 1835 | 'even some store houses have been thrown open to receive the unsheltered emigrants' |
| the open sky upon the wharves | the American, 13 June 1835 | 'who had else remained under the open sky upon the wharves' |
| a tent at the landing place | the American, 13 June 1835 | 'Some build tents upon the spot they were landed from the boats' |
- **unit** — one row per class, with the sentence that establishes it

### camp ground candidates

| id | name | confidence | refused to a builder |
| --- | --- | --- | --- |
| the_landing_place | The wharves and the bank where the vessels discharged | documented | — |
| the_lake_shore_south_of_the_fort | The lake shore south of Fort Dearborn | conjectural | fort_dearborn_reservation, river_mouth_sand_bar |
| the_prairie_edge_west_of_the_canal_street_approach | The prairie edge west of the Canal Street approach | conjectural | — |
| wolf_point | Wolf Point, at the forks | conjectural | — |
| the_north_side_commons | The North Division ground beyond the dealt parcel | conjectural | — |
- **unit** — grounds offered to T-1214 — a candidate is not a placement

**Open questions.** These are recorded here and do not become tickets.

- A refusal in 1835_no_build_ground.json is a refusal to a BUILDER and this model does not read it as a refusal to a camp: the United States Reservation carried no lot line and no street, and a crowd sleeping rough on it for a fortnight asked nobody's leave. Whether that reading is right is T-1214's to settle on the ground.
- Four of the five candidate grounds are conjectural and would stay conjectural even if T-1214 placed a camp on every one of them — placing a thing does not raise the evidence for it.
- Two of the candidates stand on ground the terrain and lot layers have not reached (T-1193, T-1194). Until they do, those candidates are a direction rather than an extent, and T-1214 may find it has nowhere to put them.

---

## What this model may not do

- **write a person.** T-1353 mints the cohort; this file bounds it, and `--self-test` refuses a build that names a record;
- **inflate the residents.** A transient is in the town and not of it, and the town census must go on reporting the two apart;
- **place a camp.** The candidate grounds are offered to T-1214, which may refuse every one of them;
- **man a hull.** The vessels file seats the hulls and `--self-test` refuses one that acquires a crew or a berth;
- **pick the point reading for T-1353.** Two candidates are printed with their arguments and neither is adopted here.

## Inputs

- `data/reconstruction/1835_camp_grounds.json`
- `data/reconstruction/1835_vessels_in_port.json`
- `data/reconstruction/1835_town_model.json`
- `data/research/directories/claims/fergus_1843_civic.json`
- `data/research/directories/claims/norris_1844_town_findings.json`
- `data/research/land_sales/entries.json`
- `data/research/land_sales/resident_crosswalk.json`
- `data/research/newspapers/extracted/chicago_american_1835_06_13.json`
- `data/research/newspapers/extracted/chicago_american_1835_06_20.json`
- `data/research/newspapers/extracted/chicago_american_1835_07_04.json`
- `data/research/newspapers/extracted/chicago_democrat_1835_06_17.json`
- `data/research/newspapers/extracted/chicago_democrat_1835_07_01.json`
- `data/residents/households/hh_brown_rufus.json`

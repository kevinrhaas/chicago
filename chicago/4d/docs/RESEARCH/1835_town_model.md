# The 1835 town model

**T-1293.** What the town of 1 July 1835 looked like beyond the people we can name: population, occupations, households, lodging and arrival, each figure a range with its method and its comparanda.

Derived file: `data/reconstruction/1835_town_model.json`  
Built and gated by: `tools/model_town_1835.py --build | --check | --self-test`  
Folds: T-1161 · T-1162 · T-1163 · T-1164 · T-1165  
Spent by: T-1166, the reconstruction order book

---

## The tolerance, stated first

Every figure is a range with a stated method and a named comparandum. A range is the answer and not a hedge. The model does not need to be right to the person; it needs to be defensible, bounded and finished, and it will be revised when reconstruction finds it wrong.

It is an adjudication over committed derived files — no page of any source is read here, and nobody is named, aged, dated or housed.

## 1. Population

| Figure | Reading | Method |
| --- | ---: | --- |
| `recorded_town_count_november_1835` | **3,265** | Andreas prints the November 1835 town census as 3,265 people in 398 dwellings. Four months after the scene, so a ceiling on 1 July and never its population. |
| `recorded_state_count_september_to_december_1835` | **3,297** | The Illinois State census returns 3,297 for Chicago. Two to five months after the scene, and a second ceiling that disagrees with the first by 32. |
| `population_on_1_july_1835` | **2,350 – 3,265** (point reading **2,533**) | CEILING: the November count of 3,265, because the town grew through 1835 and did not shrink. FLOOR: 44.9% of the 1,282 people the layer carries give an arrival year of 1835, so about 1,464 of the November town arrived that year; spread evenly over an eight-month navigation season, 5 months of that cohort were still to come on 1 July. POINT READING: 2,533, which is the same arithmetic with half the cohort ashore by midsummer rather than three-eighths — the spring land-sale rush pulls arrivals earlier than a flat season does. |
| `people_the_layer_can_name` | **1,282** | The resident layer carries 1,282 people — 410 attested, 872 inferred, 0 reconstructed. A count of the layer, not of the town. |
| `males_per_100_females` | **120.9 – 150** (point reading **146.8**) | The 1840 city returns 120.9 overall and 146.8 among those aged 20 and over. 1835 is five years earlier and rawer — more single men and fewer families — so the 1840 ratio is a FLOOR and the 1840 adult ratio is inside the range, not at the top of it. |
| `share_under_ten` | **0.2 – 0.2702** | Children under ten are 27.0% of the 1840 city. A town with a higher adult sex ratio carries proportionally fewer of them, so 1840 is the CEILING here and the floor is set one fifth below it. |

**Not claiming.** This section does not claim that any named person was in the town on 1 July 1835; presence is a per-person ruling and 824 of the layer's people are still uncertain.

### by division

| division | dwellings | share | people low | people high |
| --- | --- | --- | --- | --- |
| south | 176 | 0.5254 | 1235 | 1715 |
| west | 75 | 0.2239 | 526 | 731 |
| north | 84 | 0.2507 | 589 | 819 |
- **note** — The spec's ordinary-dwelling matrix is the only committed statement of how the town divided between the three divisions. Applied to people it assumes one division's dwellings held as many people as another's.
- **unit** — share of the town, from the authored dwelling programme

### known by presence

- **present** — 456
- **absent** — 2
- **uncertain** — 824

**Open questions.** These are recorded here and do not become tickets.

- Neither recorded count is of the scene, and they disagree with each other by 32 people. Which of 3,265 and 3,297 is the better ceiling is not settled here.
- The floor rests on the arrival distribution of the people the layer can NAME, and the sources that name them (letter lists, voter rolls, directories) are themselves dated 1834-1835, so that distribution is biased toward late arrivals and the floor is more likely too low than too high.
- `bk_mose1_006`'s reading note says the figure 3,297 'is already in the repository' from the Chicago Democrat of 1835-07-01 and the Chicago American of 1835-06-08 and 1835-06-27. Neither committed text carries it: the 3297 that greps in those files is an OCR coordinate, not a population. The note overstates its corroboration and the claim stands on Moses and Kirkland alone.
- The authored spec's `population_working_range` is [3200, 3265]. This model's derived range for 1 July is [2,350, 3,265] — the same ceiling and a far lower floor. The roof programme is cut against the spec's range; T-1196 is where the two are reconciled.

## 2. Occupations

| Figure | Reading | Method |
| --- | ---: | --- |
| `census_classes_compared` | **17** | 17 of the 20 classes the T-1006 crosswalk holds carry both a printed census line and a register count; the other 3 are a class the census never printed a line for, or a line the town holds nothing for. |
| `establishments_in_the_compared_classes` | **118** | The register holds 118 records at the scene date across the compared classes and the census counted 118 two to five months later — THE SAME NUMBER, which is a coincidence and not an agreement: 8 classes are short and 5 are over, and they cancel. A total that matches while its rows do not is the strongest argument in this model for reading the census BY CLASS and never as a population of shops. |
| `classes_short_of_the_census` | **8** | 8 compared classes hold fewer records than the census counted, 22 establishments short in total; 5 hold more, which is the register counting NOTICES where the census counted houses. |
| `employed_persons` | **423 – 588** | The 1840 schedule returns 18% of persons in its seven industry columns, 0.902 per household. Applied to this model's July population range. The 1840 columns count persons in families and not occupations of named men, so this is a size and not a roster. |
| `people_the_layer_gives_a_trade` | **127 – 262** | 127 people carry a role that reaches 1 July 1835; 262 carry any role at all, and 135 carry only roles dated off the scene. The gap between this and the employed-persons figure above is what the reconstruction bands have to fill. |

**Not claiming.** This section does not claim a trade for any named man, and a class that stands short of the census stays short rather than being filled with invented practitioners.

### against the state census

| class | census line | census count | town at scene date | delta | outcome |
| --- | --- | --- | --- | --- | --- |
| physician | fourteen physicians | 14 | 3 | -11 | town_holds_fewer_than_the_census_counted |
| lawyer | twenty-two lawyers | 22 | 18 | -4 | town_holds_fewer_than_the_census_counted |
| druggist | four druggists | 4 | 2 | -2 | town_holds_fewer_than_the_census_counted |
| bank | one bank | 1 | 0 | -1 | town_holds_fewer_than_the_census_counted |
| brewery | two breweries | 2 | 1 | -1 | town_holds_fewer_than_the_census_counted |
| lottery_office | one lottery office | 1 | 0 | -1 | town_holds_fewer_than_the_census_counted |
| lyceum_and_reading_room | a lyceum and reading room | 1 | 0 | -1 | town_holds_fewer_than_the_census_counted |
| silversmith_jeweller | two silversmiths and jewellers | 2 | 1 | -1 | town_holds_fewer_than_the_census_counted |
| book_store | two book stores | 2 | 2 | 0 | town_matches_census |
| iron_foundry | one iron foundry | 1 | 1 | 0 | town_matches_census |
| school | seven schools | 7 | 7 | 0 | town_matches_census |
| tavern | eight taverns | 8 | 8 | 0 | town_matches_census |
| printing_office | two printing offices | 2 | 3 | 1 | town_holds_more_than_the_census_counted |
| steam_saw_mill | one steam saw-mill | 1 | 2 | 1 | town_holds_more_than_the_census_counted |
| tin_and_copper_manufactory | two tin and copper manufactories | 2 | 4 | 2 | town_holds_more_than_the_census_counted |
| storage_and_forwarding | four storage and forwarding houses | 4 | 7 | 3 | town_holds_more_than_the_census_counted |
| store | forty-four stores (dry goods, hardware and groceries) | 44 | 59 | 15 | town_holds_more_than_the_census_counted |
- **date caution** — THE COUNT IS NOT OF THE SCENE. It was taken between 1 September and December 1835; the scene is 1 July 1835, two to five months earlier and in the fastest-growing months the town had. A class where the town holds fewer than the census counted is NOT thereby a hole in the July town — some of those forty-four stores opened in September. Every figure below is to be read with that gap in front of it.
- **unit** — establishment records at the scene date against the printed census line

### employment shape 1840

| column | ipums variable | persons | share of employed |
| --- | --- | --- | --- |
| Agriculture | nindagr | 136 | 0.1563 |
| Commerce | nindcom | 185 | 0.2126 |
| Manufactures and trades | nindmfg | 405 | 0.4655 |
| Navigation of the ocean | nindocn | 9 | 0.0103 |
| Navigation of canals, lakes and rivers | nindriv | 62 | 0.0713 |
| Learned professions and engineers | nindeng | 71 | 0.0816 |
| Mining | nindmin | 2 | 0.0023 |
- **unit** — persons in families, 1840, as the relative weight of each pursuit

**Open questions.** These are recorded here and do not become tickets.

- The census's lawyer and physician lines count PEOPLE and the register counts RECORDS, so those two rows are not comparable in the same unit as the rest; `trade_census_spend_1835.py` holds that adjudication.
- A shortfall against a count taken two to five months later is never evidence that an establishment stood in July, and this model does not treat it as a quota until the order book (T-1166) rules on how much of it is growth.
- The 1840 industry columns have no row for domestic service, which a port with this adult sex ratio certainly had; the trade split understates household labour by an amount this model cannot bound.

## 3. Households and families

| Figure | Reading | Method |
| --- | ---: | --- |
| `people_per_dwelling_november_1835` | **8.204** | 3,265 people in 398 dwellings. Against a 1840 mean HOUSEHOLD of 5.015, the gap is the finding: in 1835 a dwelling held more than one household, and a roof programme that seats one family per roof undercounts the town. |
| `households_on_1_july_1835` | **469 – 816** | This model's July population divided by household size: the low end takes the low population at the 1840 MEAN of 5.015, the high end the high population at the 1840 MEDIAN of 4.0. The distribution is long-tailed — one 1840 household in a hundred holds twenty-one people or more — so mean and median bracket it better than either alone. |
| `household_size` | **4 – 5.015** | Median 4.0, mean 5.015 in the 1840 city; p75 is 6 and p99 is 21. Half the town lives in households of four or fewer and the tail is boarding houses, hotels and crews. |
| `household_records_the_layer_carries` | **1,258** | 1,258 household records for 1,282 people — 1.02 people per record. The layer mints a letter-list or civic name as its own household, so it holds MORE household shells than the town had households. That is a property of the mint, not a reading of the town, and the order book must not count them as families. |
| `dwellings_the_programme_schedules` | **335 – 377** | The authored programme schedules 335 ordinary dwellings and 42 larger boarding houses. The November census counted 398 dwellings, so the programme's dwelling half sits below the recorded count and its boarding houses make up the difference. |

**Not claiming.** This section supplies no member to any household and names nobody; it states the distribution a reconstructed family must be drawn from and nothing about which family.

### size histogram 1840

| size | households |
| --- | --- |
| 0 | 2 |
| 1 | 64 |
| 2 | 129 |
| 3 | 165 |
| 4 | 152 |
| 5 | 142 |
| 6 | 95 |
| 7 | 74 |
| 8 | 42 |
| 9 | 24 |
| 10 | 24 |
| 11 | 12 |
| 12 | 9 |
| 13 | 4 |
| 14 | 5 |
| 15 | 1 |
| 16 | 2 |
| 17 | 4 |
| 18 | 2 |
| 19 | 1 |
| 20 | 1 |
| 21 | 1 |
| 22 | 2 |
| 25 | 2 |
| 26 | 1 |
| 28 | 1 |
| 29 | 1 |
| 34 | 1 |
| 35 | 1 |
- **unit** — households by person count, 1840 city

### the rule for a head no source names

- **statement** — A head the sources name but whose family they do not gets a household drawn from the 1840 distribution at his own size band, never from the mean. The mean is 5.015 and the median is 4: drawing every unnamed family at the mean would build a town with no small households and no long tail, which is the one shape the 1840 count rules out.
- **sex ratio caution** — Households drawn symmetrically break the adult sex ratio (146.8 males per 100 females aged 20 and over in 1840, and higher in 1835). The surplus men are boarders and lodgers, not husbands.

**Open questions.** These are recorded here and do not become tickets.

- How many households a dwelling held in 1835 is not settled: 8.20 people per dwelling against a 1840 mean household of 5.02 implies roughly 1.6, but the 1835 count's 'dwelling' is the enumerator's word and this project has not read his schedule.
- The layer's 1,258 household records cannot be reconciled with a town of 469 to 816 households without a ruling on what a letter-list mint IS; T-0660 and T-0691 hold that question and are blocked on the owner.

## 4. Lodging and institutions

| Figure | Reading | Method |
| --- | ---: | --- |
| `larger_boarding_houses` | **42** | The authored programme schedules 42 across the three divisions (28 south, 6 west, 8 north). |
| `inns_and_taverns` | **8 – 10** | The programme schedules 10 inns and taverns; the State census counted 8 taverns two to five months later and the register holds 8 at the scene date. The three units are a roof, a licence and a printed notice, and they are not the same thing counted three ways. |
| `people_in_lodging_places` | **468 – 1,232** | 42 boarding houses and 10 inns, filled from the 1840 household tail: the low end puts every one at p90 (9 people), the high end at p99 (21) for the boarding houses and the observed maximum (35) for the inns. That tail IS lodging — it is what a household of twenty-one people in a lake port was. |
| `share_of_the_town_in_lodging` | **0.143 – 0.377** | The lodged range against the ceiling population of 3,265: between 14% and 38% of a boom-year port living in somebody else's house, which is the shape the adult sex ratio already implies. It is also the single figure most likely to be wrong in this model, because it multiplies an authored roof count by a borrowed capacity and neither end is measured. |
| `institutional_and_public_roofs` | **9 – 19** | 9 institutional or public roofs outside the fort and 10 principal roofs inside it. The census's five churches, seven schools, one bank, one lottery office and a lyceum are counted in December and several of them met in rooms rather than in buildings of their own. |

**Not claiming.** This section seats nobody in any lodging place and gives no boarding house a capacity of its own; it states how many beds the town needed in total.

### lodging and institutional roofs

| group | south | west | north | fort | total |
| --- | --- | --- | --- | --- | --- |
| larger_boarding_houses | 28 | 6 | 8 | 0 | 42 |
| inns_taverns | 5 | 3 | 2 | 0 | 10 |
| institutional_public | 5 | 1 | 3 | 0 | 9 |
| fort_principal | 0 | 0 | 0 | 10 | 10 |
| stores_mixed_use | 42 | 6 | 4 | 1 | 53 |
| warehouses_freight | 11 | 2 | 7 | 0 | 20 |
- **unit** — roofs in the authored programme, by division

### counted in december not in july

- **line** — bk_mose1_006
- **institutions** — five churches, seven schools, one bank, one lottery office, a lyceum and reading room, four storage and forwarding houses
- **caution** — Counted between 1 September and December 1835. A church with five congregations in December had fewer in July and some of them had no building at all.

**Open questions.** These are recorded here and do not become tickets.

- The garrison of Fort Dearborn on 1 July 1835 is not modelled here. The fort's strength is a roster question owned by T-1176 and the ten principal roofs are all this model counts.
- The vessels in port held people the shore census may or may not have counted, and no committed source settles how the November enumerator treated a crew ashore.
- Whether the census's 398 dwellings include boarding houses and taverns or count them separately is unknown, and the answer moves the lodging share by more than any other assumption in this section.

## 5. Arrival and origin

| Figure | Reading | Method |
| --- | ---: | --- |
| `arrived_in_the_three_years_before_the_scene` | **0.961** | 1,232 of the 1,282 people the layer carries give an arrival year of 1833, 1834 or 1835; only 50 came before 1833. The town of 1 July 1835 is overwhelmingly three years old or less. |
| `arrived_in_1835_itself` | **0.449** | 575 of 1,282. This is the figure the population floor is built on, and it is the one most exposed to the bias below. |
| `born_in_new_york_state` | **0.386 – 0.743** | Of the 70 Old Settlers who registered an arrival at or before 1835 and gave a birthplace, 27 were born in New York State and 25 elsewhere in New England. The low end is New York alone, the high end New York and New England together — the Erie Canal corridor and its feeders, which is the origin story this town has. |
| `born_abroad` | **0.1** | England and Ireland in the Old Settlers roll. A floor and not a share: the 1840 extract's foreign-born column reads zero in all 964 rows, which is a column that was not coded and not a count of none, so this project holds no measure of the town's foreign-born at all. |

**Not claiming.** This section dates and places nobody: it is a distribution over cohorts and an arrival year on a card is still that card's own evidence.

### arrival year of the known layer

| year | people | share |
| --- | --- | --- |
| 1812 | 3 | 0.0023 |
| 1816 | 3 | 0.0023 |
| 1818 | 1 | 0.0008 |
| 1820 | 1 | 0.0008 |
| 1823 | 2 | 0.0016 |
| 1826 | 2 | 0.0016 |
| 1827 | 2 | 0.0016 |
| 1830 | 3 | 0.0023 |
| 1831 | 13 | 0.0101 |
| 1832 | 20 | 0.0156 |
| 1833 | 139 | 0.1084 |
| 1834 | 518 | 0.4041 |
| 1835 | 575 | 0.4485 |
- **unit** — people the layer carries, by the arrival year it records

### birthplace of the old settlers who came by 1835

| region | people |
| --- | --- |
| new_york | 27 |
| new_england | 25 |
| mid_atlantic | 7 |
| england | 6 |
| south | 3 |
| west_of_the_alleghenies | 1 |
| ireland | 1 |
- **rows total** — 70
- **unit** — rows of the Calumet Club rolls whose arrival is at or before 1835

**Open questions.** These are recorded here and do not become tickets.

- The arrival distribution is of people the project can NAME, and the sources that name them — letter lists, voter rolls, the 1839 and 1843 directories — are themselves of 1834 and later, so a man who came in 1831 and left no notice is missing from it. The 1835 share is a ceiling on the true share.
- The Old Settlers roll is a self-selected survivorship sample registered forty-four years later: it over-represents men who stayed, prospered and lived to 1879, and it holds no woman who married out of her registered name. Its birthplaces are the only origin distribution this project has and they are not the town's.
- WHY people came is not modelled. The land sales, the canal commission and the harbour works are each a documented draw, but no committed source apportions the town between them and this model will not invent the split.

---

## What this model may not do

- **name, age, date or house anybody.** Every figure is a cohort;
- **fill a shortfall with invented people.** A class short of the census stays short until the order book (T-1166) rules on how much of the gap is growth;
- **raise a confidence.** Nothing here is evidence about any person, household or building, and no card may cite it;
- **stand unrevised.** It will be wrong somewhere, and reconstruction finding it wrong is the honest way round — not polishing it before anything is built on it.

## Inputs

- `data/reconstruction/1835_building_inventory.json`
- `data/research/books/claims/moses_kirkland_history_of_chicago_v1.json`
- `data/research/books/trade_census_1835_crosswalk.json`
- `data/research/census_1840/composition_1840.json`
- `data/research/old_settlers/people.json`
- `data/sidecars/1835/people.json`
- `data/town_census.json`

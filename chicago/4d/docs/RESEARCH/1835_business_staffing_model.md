# The 1835 business staffing model

**Derived** — `tools/build_staffing_model_1835.py --build` · ticket T-1183 · scene date 1835-07-01. Do not hand-edit.

Every business in this town was, until this file, worked by its proprietor and nobody else. The relationship vocabulary has held `clerk`, `apprentice`, `journeyman` and `servant` since the resident layer was built and not one person stood in any of them. This is the rule T-1189 staffs by — **it writes no person, and names none**.

## The ratio derived here, and the narrower one beside it

Fergus's 1839 directory prints **152 clerks** against **312 principals** in the commerce trades — a ratio of **0.48718** clerks per commerce head. It is clerks per PERSON and not per house, because the directory counts people and prints no establishments, so it is used to predict a clerk TOTAL and to check the per-house rules below. It never sets them.

That denominator includes tavern and livery keepers, who kept no counting house. Divided instead by only the 221 principals in the 1839 trades this model's own class table gives a clerk to, the ratio is **0.68778**. That narrowing raises the ratio and so flatters the model, which is why both are printed and the reconciliation below reports the delta on each.

> 1839 IS FOUR YEARS AFTER THE SCENE, and this volume is Fergus's 1876 completion of a list that, in the compiler's own words, "was never written". Every share below is the shape of a LATER town recalled later still. It is a prior for a draw and it is not a count of 1835, nor evidence about any person in it.

## And the finding that bounds it

50 keepers of taverns, boarding houses and refectories stand in the 1839 list against 2 bar-keepers, 5 domestics and 1 laundress. No hostler, cook or chambermaid is printed at all. That is a list of householders, so it is a FLOOR for service labour and never a count — which is why every service row in this model is `period_convention`.

## The classes

| establishment | at the scene date | staff low–typical–high | roles |
|---|---:|---|---|
| an auction and commission room | 10 | 0–1–2 | clerk (clerk, young_adult_16_25), labourer (household_member, adult_18_45) |
| a bakery | 3 | 0–1–2 | baker (journeyman, young_adult_16_25), labourer (household_member, youth_12_18) |
| a book store | 1 | 0–1–1 | clerk (clerk, young_adult_16_25) |
| a brewery | 1 | 1–2–3 | labourer (household_member, adult_18_45) |
| a butcher's shop | 1 | 0–1–1 | butcher (journeyman, adult_18_45) |
| a dentist's stand | 5 | 0–0–0 | — |
| a drug store | 2 | 0–1–1 | clerk (clerk, young_adult_16_25) |
| a dry-goods store | 27 | 1–1–3 | clerk (clerk, young_adult_16_25), labourer (household_member, adult_18_45) |
| a forwarding and commission house | 4 | 2–4–7 | clerk (clerk, young_adult_16_25), labourer (household_member, adult_18_45), teamster (household_member, adult_18_45) |
| an iron foundry | 1 | 1–2–4 | founder (journeyman, adult_18_45) |
| a grocery and provision store | 8 | 0–1–2 | clerk (clerk, young_adult_16_25), labourer (household_member, adult_18_45) |
| a hardware or stove store | 7 | 0–1–2 | clerk (clerk, young_adult_16_25), tinsmith (journeyman, young_adult_16_25) |
| a land or insurance office | 6 | 0–0–1 | clerk (clerk, young_adult_16_25) |
| a law office | 18 | 0–0–1 | clerk (clerk, young_adult_16_25) |
| a saddler's and harness maker's shop | 3 | 0–1–2 | harness_maker (journeyman, young_adult_16_25), harness_maker (apprentice, youth_12_18) |
| a livery stable | 3 | 1–2–3 | labourer (household_member, adult_18_45), labourer (household_member, youth_12_18) |
| a lumber yard | 6 | 1–2–3 | labourer (household_member, adult_18_45) |
| a mill | 2 | 1–2–3 | sawyer (household_member, adult_18_45) |
| a millinery or dressmaking room | 4 | 0–1–3 | dressmaker (journeyman, young_adult_16_25), dressmaker (apprentice, youth_12_18) |
| a painter's shop | 1 | 0–1–2 | painter (journeyman, young_adult_16_25), painter (apprentice, youth_12_18) |
| a physician's practice | 3 | 0–0–1 | clerk (clerk, young_adult_16_25) |
| the post office | 1 | 0–0–1 | clerk (clerk, adult_any) |
| a printing office | 3 | 1–2–4 | printer (journeyman, young_adult_16_25), printer (apprentice, youth_12_18) |
| a school | 6 | 0–0–1 | schoolteacher (household_member, adult_any) |
| a boot and shoe shop | 8 | 0–1–2 | shoemaker (journeyman, young_adult_16_25), shoemaker (apprentice, youth_12_18) |
| a jeweller's, hatter's or confectioner's shop | 3 | 0–0–1 | clerk (clerk, young_adult_16_25) |
| a blacksmith's shop | 4 | 0–1–2 | blacksmith (journeyman, young_adult_16_25), blacksmith (apprentice, youth_12_18) |
| a soap and candle works | 2 | 0–1–2 | labourer (household_member, adult_18_45) |
| a surveyor's office | 2 | 0–1–2 | labourer (household_member, adult_18_45) |
| a tailoring establishment | 7 | 0–2–5 | tailor (journeyman, young_adult_16_25), dressmaker (journeyman, adult_18_45), tailor (apprentice, youth_12_18) |
| a tavern or hotel | 7 | 2–5–6 | tavern_keeper (household_member, adult_any), labourer (household_member, adult_18_45), domestic (servant, adult_18_45), domestic (servant, young_adult_16_25), domestic (servant, youth_12_18) |
| a tin and copper manufactory | 3 | 0–2–2 | tinsmith (journeyman, young_adult_16_25), tinsmith (apprentice, youth_12_18) |
| a business the layer gives no trade to | 9 | 0–0–0 | — |
| a joiner's or carriage maker's shop | 8 | 0–2–3 | joiner (journeyman, young_adult_16_25), joiner (apprentice, youth_12_18) |

## Every role, with its basis

### an auction and commission room — 10 at the scene date

- **clerk** as *clerk* — 0–1–1, male, young_adult_16_25, lives in 40% · `directory_1839`  
  A sale is cried by the auctioneer and booked by somebody. 9 auctioneers in 1839.
- **labourer** as *household_member* — 0–0–1, male, adult_18_45, lives in 0% · `period_convention`  
  A porter on sale days. Analogue: the stores above.

### a bakery — 3 at the scene date

- **baker** as *journeyman* — 0–1–1, male, young_adult_16_25, lives in 50% · `directory_1839`  
  11 bakers in 1839. A bakehouse is worked at night and the hand sleeps there.
- **labourer** as *household_member* — 0–0–1, male, youth_12_18, lives in 30% · `period_convention`  
  A boy on the delivery basket. Analogue: the bakehouse above.

### a book store — 1 at the scene date

- **clerk** as *clerk* — 0–1–1, either, young_adult_16_25, lives in 50% · `directory_1839`  
  A book store is a store. `either`: the trade is one of the few a town of this date let a woman keep counter in, and the directory refuses neither.

### a brewery — 1 at the scene date

- **labourer** as *household_member* — 1–2–3, male, adult_18_45, lives in 20% · `directory_1839`  
  3 brewers in 1839 for 2 breweries in the 1835 census — the principals only; the mash was worked by hands the list booked as labourers.

### a butcher's shop — 1 at the scene date

- **butcher** as *journeyman* — 0–1–1, male, adult_18_45, lives in 20% · `directory_1839`  
  16 butchers in 1839 against the one shop and the market here.

### a drug store — 2 at the scene date

- **clerk** as *clerk* — 0–1–1, male, young_adult_16_25, lives in 50% · `directory_1839`  
  13 druggists in 1839 and the commerce clerk share over them. The druggist's clerk is often reading medicine, which is why he boards in the house.

### a dry-goods store — 27 at the scene date

- **clerk** as *clerk* — 1–1–2, male, young_adult_16_25, lives in 50% · `directory_1839`  
  The counting-house clerk is the one role the directory counts in bulk — 152 of them, the largest single trade in the 1839 list after the carpenters — and the printed forms name their houses outright ('clerk stiles burton'). A young man boarding with his employer or over the store is the ordinary arrangement; half is this model's reading of 'often', and it is a reading.
- **labourer** as *household_member* — 0–0–1, male, adult_18_45, lives in 0% · `period_convention`  
  A porter to shift goods, at the larger houses only. Analogue: the 1839 list's seven porters, counted under labourer, against 151 commerce principals.

### a forwarding and commission house — 4 at the scene date

- **clerk** as *clerk* — 1–1–2, male, young_adult_16_25, lives in 40% · `directory_1839`  
  The forwarding house is the heaviest clerical trade on the river: 15 forwarding and commission principals in 1839 and the bookkeepers counted with the clerks.
- **labourer** as *household_member* — 1–2–3, male, adult_18_45, lives in 0% · `directory_1839`  
  Warehousemen: the 1839 list prints the term only twice, which is the floor and not the count — a warehouse on the South Water landings was worked by hands the directory booked as labourers, of whom it counts 73.
- **teamster** as *household_member* — 0–1–2, male, adult_18_45, lives in 0% · `directory_1839`  
  41 teamsters and 30 draymen in 1839, against a river trade this one grew out of.

### an iron foundry — 1 at the scene date

- **founder** as *journeyman* — 1–2–4, male, adult_18_45, lives in 10% · `directory_1839`  
  12 founders in 1839. A furnace is the largest hand-count of any shop in town.

### a grocery and provision store — 8 at the scene date

- **clerk** as *clerk* — 0–1–1, male, young_adult_16_25, lives in 50% · `directory_1839`  
  A grocery is a smaller counting house than a dry-goods store and the low end is the keeper alone. Same clerk calibration, one step down.
- **labourer** as *household_member* — 0–0–1, male, adult_18_45, lives in 0% · `period_convention`  
  A hand for barrels and the drayage. Analogue: as above.

### a hardware or stove store — 7 at the scene date

- **clerk** as *clerk* — 0–1–1, male, young_adult_16_25, lives in 50% · `directory_1839`  
  Counted with the commerce clerks; the trade is a store whatever it sells.
- **tinsmith** as *journeyman* — 0–0–1, male, young_adult_16_25, lives in 25% · `period_convention`  
  A stove dealer who fits and repairs keeps a tinner. Analogue: the town's own tin and copper manufactories, which the census counts separately.

### a land or insurance office — 6 at the scene date

- **clerk** as *clerk* — 0–0–1, male, young_adult_16_25, lives in 30% · `directory_1839`  
  25 land agents in 1839; the office is the principal and his papers, and a clerk only at the busiest.

### a law office — 18 at the scene date

- **clerk** as *clerk* — 0–0–1, male, young_adult_16_25, lives in 30% · `period_convention`  
  The student-at-law, who read in an office rather than at a school. Analogue: the 1839 list's 11 students against 45 attorneys, a quarter of them.

### a saddler's and harness maker's shop — 3 at the scene date

- **harness_maker** as *journeyman* — 0–1–1, male, young_adult_16_25, lives in 30% · `directory_1839`  
  6 harness makers in 1839 against 3 shops here.
- **harness_maker** as *apprentice* — 0–0–1, male, youth_12_18, lives in 60% · `period_convention`  
  Analogue: the journeyman row above.

### a livery stable — 3 at the scene date

- **labourer** as *household_member* — 1–1–2, male, adult_18_45, lives in 60% · `period_convention`  
  Hostlers. `hostler` is outside the vocabulary; see `vocabulary_gaps`. Analogue: the 11 livery stable keepers of 1839, against whom the list prints no hostler.
- **labourer** as *household_member* — 0–1–1, male, youth_12_18, lives in 80% · `period_convention`  
  The stable boy. Analogue: as above.

### a lumber yard — 6 at the scene date

- **labourer** as *household_member* — 1–2–3, male, adult_18_45, lives in 0% · `period_convention`  
  A yard is piled and loaded by hand. Analogue: the forwarding houses above, whose warehouse labour this model prices the same way.

### a mill — 2 at the scene date

- **sawyer** as *household_member* — 1–2–3, male, adult_18_45, lives in 20% · `directory_1839`  
  6 sawyers and 7 millers in 1839; a steam saw-mill is a gang and not a man.

### a millinery or dressmaking room — 4 at the scene date

- **dressmaker** as *journeyman* — 0–1–2, female, young_adult_16_25, lives in 30% · `period_convention`  
  The needle trades ran on assistants and the 1835 notices advertise for them. Analogue: the 1839 list's six milliners and its tailoresses, and the 1840 column that has no row for them at all.
- **dressmaker** as *apprentice* — 0–0–1, female, youth_12_18, lives in 60% · `period_convention`  
  A girl bound to the needle, living in. Analogue: as above.

### a painter's shop — 1 at the scene date

- **painter** as *journeyman* — 0–1–1, male, young_adult_16_25, lives in 20% · `directory_1839`  
  14 painters in 1839; the trade works in pairs.
- **painter** as *apprentice* — 0–0–1, male, youth_12_18, lives in 50% · `period_convention`  
  Analogue: the journeyman row above.

### a physician's practice — 3 at the scene date

- **clerk** as *clerk* — 0–0–1, male, young_adult_16_25, lives in 40% · `period_convention`  
  A physician's student, on the same footing as the law student. Analogue: as above.

### the post office — 1 at the scene date

- **clerk** as *clerk* — 0–0–1, either, adult_any, lives in 0% · `period_convention`  
  An assistant in the office. Analogue: the two postmasters of 1839.

### a printing office — 3 at the scene date

- **printer** as *journeyman* — 1–1–2, male, young_adult_16_25, lives in 30% · `directory_1839`  
  Journeymen at case and press. The 1839 list counts 15 printers — compositors, pressmen and job printers — against 2 editors, and the two offices of the 1835 census are the establishments those hands worked in four years earlier.
- **printer** as *apprentice* — 0–1–2, male, youth_12_18, lives in 80% · `period_convention`  
  The apprentice, who lives in. Analogue: the journeyman row above; the project holds no roll of the Democrat's or the American's hands — see docs/RESEARCH/chicago_democrat_office.md, which reads the imprint and no roll.

### a school — 6 at the scene date

- **schoolteacher** as *household_member* — 0–0–1, either, adult_any, lives in 0% · `period_convention`  
  An assistant, at the larger schools only; the town's schools of 1835 are one room and one teacher. Analogue: the 1839 list's 13 schoolteachers.

### a boot and shoe shop — 8 at the scene date

- **shoemaker** as *journeyman* — 0–1–1, male, young_adult_16_25, lives in 30% · `directory_1839`  
  27 shoemakers in 1839 against 8 shops here.
- **shoemaker** as *apprentice* — 0–0–1, male, youth_12_18, lives in 60% · `period_convention`  
  Analogue: the journeyman row above.

### a jeweller's, hatter's or confectioner's shop — 3 at the scene date

- **clerk** as *clerk* — 0–0–1, either, young_adult_16_25, lives in 40% · `period_convention`  
  A jeweller's, hatter's or confectioner's is a one-hand shop at this date. Analogue: the 1839 list's 7 watchmakers and 5 hatters, none with a counted hand.

### a blacksmith's shop — 4 at the scene date

- **blacksmith** as *journeyman* — 0–1–1, male, young_adult_16_25, lives in 30% · `period_convention`  
  The striker, who swings while the smith holds. Analogue: the 1839 list's 48 smiths in a town that had 5 shops in 1835.
- **blacksmith** as *apprentice* — 0–0–1, male, youth_12_18, lives in 70% · `period_convention`  
  A bound boy. Analogue: as above.

### a soap and candle works — 2 at the scene date

- **labourer** as *household_member* — 0–1–2, male, adult_18_45, lives in 10% · `directory_1839`  
  8 soap and candle makers in 1839 across a handful of works.

### a surveyor's office — 2 at the scene date

- **labourer** as *household_member* — 0–1–2, male, adult_18_45, lives in 0% · `period_convention`  
  Chainmen, hired by the survey and not by the year. Analogue: the 13 surveyors of 1839, against whom the list prints no chainman.

### a tailoring establishment — 7 at the scene date

- **tailor** as *journeyman* — 0–1–2, male, young_adult_16_25, lives in 30% · `directory_1839`  
  42 tailors in 1839 against 7 tailoring houses here.
- **dressmaker** as *journeyman* — 0–1–2, female, adult_18_45, lives in 10% · `period_convention`  
  The tailoress, who sewed what the cutter cut. Analogue: the 1839 list's printed 'cloak maker and tailoress', counted under tailor, and the millinery rows above.
- **tailor** as *apprentice* — 0–0–1, male, youth_12_18, lives in 60% · `period_convention`  
  Analogue: the journeyman row above.

### a tavern or hotel — 7 at the scene date

- **tavern_keeper** as *household_member* — 1–1–1, predominantly_male, adult_any, lives in 100% · `period_convention`  
  The bar-keeper. `bar_keeper` is NOT in the residents occupation vocabulary and is carried here under the nearest term it does hold; see `vocabulary_gaps`. Analogue: the 1839 list's two bar-keepers against 50 keepers of houses — a floor, and the clearest evidence in this file that the directory did not canvass service.
- **labourer** as *household_member* — 0–1–1, male, adult_18_45, lives in 70% · `period_convention`  
  The hostler, who is a house's stable. `hostler` is outside the vocabulary. Analogue: the livery stables below, and the 1839 list's silence.
- **domestic** as *servant* — 1–1–1, female, adult_18_45, lives in 80% · `period_convention`  
  The cook. A house that feeds travellers cooks every day of the week. Analogue: the 1839 list's five domestics against a town of 4,000 — a floor, not a count.
- **domestic** as *servant* — 0–1–2, female, young_adult_16_25, lives in 90% · `period_convention`  
  Chambermaids, by the number of beds. Analogue: the lodging model's per-place capacities, which this row does not itself read.
- **domestic** as *servant* — 0–1–1, male, youth_12_18, lives in 100% · `period_convention`  
  The boy — boots, errands, the yard. Analogue: as above.

### a tin and copper manufactory — 3 at the scene date

- **tinsmith** as *journeyman* — 0–1–1, male, young_adult_16_25, lives in 30% · `directory_1839`  
  8 tinsmiths in 1839; the census counts 2 manufactories in 1835.
- **tinsmith** as *apprentice* — 0–1–1, male, youth_12_18, lives in 60% · `period_convention`  
  Analogue: the journeyman row above.

### a joiner's or carriage maker's shop — 8 at the scene date

- **joiner** as *journeyman* — 0–1–2, male, young_adult_16_25, lives in 20% · `directory_1839`  
  The building trades are the largest in the 1839 list — 133 carpenters and 54 builders — and a master's shop is where they stood.
- **joiner** as *apprentice* — 0–1–1, male, youth_12_18, lives in 60% · `period_convention`  
  Analogue: the journeyman row above.

## The shop household rule

`lives_on_premises` is the share of holders of a role who slept in the proprietor's house or over the shop, and `household_relationship` is the term their card carries in that household. A clerk at 0.5 means half the clerks of that class are household members of their employer and half keep their own lodging or board elsewhere.

A share is not a bed. The lodging model (T-1370) owns capacity and T-1371 owns who sleeps where; this rule only says which staff are candidates for the employer's household.

## The dry run over the layer as it stands

179 businesses standing on 1835-07-01, 165 proprietors and partners already on their records.

| role | as | sex | age | low | typical | high |
|---|---|---|---|---:|---:|---:|
| clerk | clerk | male | young_adult_16_25 | 31 | 58 | 116 |
| labourer | household_member | male | adult_18_45 | 14 | 36 | 99 |
| joiner | apprentice | male | youth_12_18 | 0 | 8 | 8 |
| joiner | journeyman | male | young_adult_16_25 | 0 | 8 | 16 |
| shoemaker | journeyman | male | young_adult_16_25 | 0 | 8 | 8 |
| domestic | servant | female | adult_18_45 | 7 | 7 | 7 |
| domestic | servant | female | young_adult_16_25 | 0 | 7 | 14 |
| domestic | servant | male | youth_12_18 | 0 | 7 | 7 |
| dressmaker | journeyman | female | adult_18_45 | 0 | 7 | 14 |
| tailor | journeyman | male | young_adult_16_25 | 0 | 7 | 14 |
| tavern_keeper | household_member | predominantly_male | adult_any | 7 | 7 | 7 |
| blacksmith | journeyman | male | young_adult_16_25 | 0 | 4 | 4 |
| dressmaker | journeyman | female | young_adult_16_25 | 0 | 4 | 8 |
| sawyer | household_member | male | adult_18_45 | 2 | 4 | 6 |
| teamster | household_member | male | adult_18_45 | 0 | 4 | 8 |
| baker | journeyman | male | young_adult_16_25 | 0 | 3 | 3 |
| harness_maker | journeyman | male | young_adult_16_25 | 0 | 3 | 3 |
| labourer | household_member | male | youth_12_18 | 0 | 3 | 6 |
| printer | apprentice | male | youth_12_18 | 0 | 3 | 6 |
| printer | journeyman | male | young_adult_16_25 | 3 | 3 | 6 |
| tinsmith | apprentice | male | youth_12_18 | 0 | 3 | 3 |
| tinsmith | journeyman | male | young_adult_16_25 | 0 | 3 | 10 |
| founder | journeyman | male | adult_18_45 | 1 | 2 | 4 |
| butcher | journeyman | male | adult_18_45 | 0 | 1 | 1 |
| clerk | clerk | either | young_adult_16_25 | 0 | 1 | 4 |
| painter | journeyman | male | young_adult_16_25 | 0 | 1 | 1 |
| blacksmith | apprentice | male | youth_12_18 | 0 | 0 | 4 |
| clerk | clerk | either | adult_any | 0 | 0 | 1 |
| dressmaker | apprentice | female | youth_12_18 | 0 | 0 | 4 |
| harness_maker | apprentice | male | youth_12_18 | 0 | 0 | 3 |
| painter | apprentice | male | youth_12_18 | 0 | 0 | 1 |
| schoolteacher | household_member | either | adult_any | 0 | 0 | 6 |
| shoemaker | apprentice | male | youth_12_18 | 0 | 0 | 8 |
| tailor | apprentice | male | youth_12_18 | 0 | 0 | 7 |

**Staff implied:** 65–202–417, of whom 87.5 live on the premises at the typical figure.

**Working persons implied** (principals + staff): 230–367–582.

## Reconciliation

- **Against the 1839 clerk ratio, like for like.** 86 principals stand in the layer's clerk-employing classes; × 0.68778 that predicts 59.1 clerks, and the per-house rules put 59 there — a delta of -0.1 against a tolerance of 14.8. They agree.
- **And on the wide ratio.** Divide the same 1839 clerks by every commerce principal, tavern and livery keepers included, and the ratio falls to 0.48718, predicting 41.9 — a delta of 17.1. The wide ratio divides the same clerks by tavern, livery and boarding-house keepers as well, and on it the model looks over-clerked. Printed rather than buried: it is the reading a sceptic would take.
- **Against the town model's employment.** 367 working persons implied, against 424–588 employed persons. Below the low end, which is expected: The town model's employed persons counts EVERY working person — the labourers of the harbour works, the garrison, the farmers outside the limits, the domestic service the 1840 columns have no row for. The businesses of this layer are a PART of that figure, so falling below the low end is expected and falling above it is a refusal.

## Terms the residents vocabulary does not hold

Each is carried under the nearest term index.json does hold, and may not be written onto a person until the vocabulary carries the real one.

| wanted | for | carried as |
|---|---|---|
| `bar_keeper` | the tavern and hotel bar | `tavern_keeper` |
| `chambermaid` | the tavern and hotel chambers | `domestic` |
| `cook` | the tavern and hotel kitchen | `domestic` |
| `hostler` | the tavern, hotel and livery stable | `labourer` |
| `student_at_law` | the law offices | `clerk` |
| `warehouseman` | the forwarding houses | `labourer` |

## The 9 houses this model cannot staff

No `occupation` on the record, so no establishment kind, so no staff. T-1182's audit is what fixes this.

- `biz_c_h_chapman` — C. H. Chapman
- `biz_chicago_st_joseph_packet_schooner_llewellyn` — Chicago & St. Joseph Packet (schooner Llewellyn)
- `biz_d_o_robinson_and_r_a_neff` — D. O. Robinson and R. A. Neff
- `biz_john_dave_north_water_street` — John Dave, North Water Street
- `biz_m_cormick_moon` — M'Cormick & Moon
- `biz_newberry_dole` — Newberry & Dole
- `biz_richard_m_sweet_corn_at_his_barn_on_the_dupage` — Richard M. Sweet, corn at his barn on the Dupage
- `biz_russell_brown` — Russell & Brown
- `biz_the_chicago_and_st_joseph_packet_schooner_phillips` — The Chicago and St. Joseph packet, schooner Phillips

## Open questions

- **Is the 1839 clerk ratio a prior for 1835 at all?** It is the only staffing figure the project holds, and 1839 is a town with a bank, a canal and four more years of growth. The model uses it to CHECK its rules and not to set them, which is the most weight it will bear. (T-1183, T-1189)
- **What does the town do about the service labour no source counts?** The 1840 industry columns have no row for domestic service and the 1839 directory prints five domestics. The town model already says its trade split understates household labour by an amount it cannot bound; this model reconstructs that labour for businesses and cannot bound it either. (T-1183, T-1163, T-1189)
- **The records the layer gives no trade to.** 9 of the 179 houses standing at the scene date carry no `occupation`, so they are staffed by nobody here. T-1182's audit is what fixes that, and until it runs this model understates the town. (T-1182)

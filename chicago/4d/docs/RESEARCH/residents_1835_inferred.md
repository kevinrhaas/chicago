# The inferred-residents programme, phase two: the inferred layer and its buildings

**Roadmap:** `docs/ROADMAP.md` § K1 · **Phase one:** `docs/RESEARCH/residents_1835.md` ·
**Recipe:** `data/reconstruction/1835_inferred_household_programme.json` ·
**Generator:** `tools/generate_inferred_households.py` (`--check` runs in `tools/check.sh`) ·
**Scene date:** 1835-07-01

---

## 1. The number that drives the parcel

The 1835 town census counts **3,265 people in 398 dwellings** (Andreas vol. 1, printed p. 180,
scan p. 377). Phase one could name about ninety of them, in 72 households. The dataset held 184
structures, 108 of which were anonymous inferred roofs carrying no occupant at all.

Phase two closes part of that gap from the population end. It adds **80 inferred households, 92
person entries**, and it houses every one of them: **83 of the 108 anonymous roofs are adopted**
as the dwellings and workplaces of argued households, and **38 new structure records** are
raised — seven documented buildings phase one found with no record, and 31 inferred buildings
the occupation census requires.

The layer is a claim about **counts and trades**, never about individuals. No inferred person is
given a name. Every one carries a designation — *A cooper (inferred resident, unnamed)* — and a
note that says, in as many words, that the record asserts a ratio and asserts nothing whatever
about any person. L1 stands: no figure is drawn.

## 2. What calibrates the census

Four things this project already holds, and nothing else:

| calibration | value | where |
|---|---|---|
| the 1835 town census | 3,265 people, 398 dwellings (8.2 per dwelling) | `andreas_1884_v1`, printed p. 180 |
| the 1833 trade roster | ~50 named people, most with a trade, in a settlement of ~350 | `andreas_1884_v1`, printed p. 132 (scan p. 281) |
| the growth multiplier | ≈ 9.3× between the two | the two rows above |
| the roof schedule | 665 roofs: 30 workshops (W1 6, W2 8, W3 6, W4 6, W5 4), 52 stores, 42 boarding houses, 10 inns, 20 warehouses, 335 ordinary dwellings | `owner_chicago_1835_reconstruction_spec_2026` |
| the documented layer | 96 person entries, 85 with a trade | `data/residents/index.json` |

**The method, in four rules.** (a) Take the documented trade spread of the 1833 roster as the
shape of the town's economy. (b) Where the reconstruction schedule gives a trade a workshop or
store family, treat that family's roof target as the **ceiling** on the trade and subtract the
documented practitioners already written. (c) Where no roof family bounds the trade — carpenters,
labourers, laundresses, teamsters — argue the count from the town's own building rate and from
documented volumes, and say so. (d) **Never infer a tradesman where a documented one is
available:** every count is stated net of phase one.

**No period trade-ratio table for a comparable western town was found in a source this project
holds, and none was invented.** Every ratio here is derived from the five rows above, which is
why the argument for each trade is written out in full in `occupation_census` rather than
reduced to a coefficient. If a directory or a census schedule for a comparable town of 1835 ever
enters `data/sources/`, this census should be re-derived against it.

## 3. The arguments that carry the most weight

- **Carpenters (10 inferred, 4 documented).** Several hundred roofs went up inside eighteen
  months. At a crew of three raising a one-room cottage in three weeks, that is on the order of
  forty carpenter-years of work. The schedule's eight W2 shops are a *floor* under the trade, not
  a measure of it: a house carpenter worked on the frame in the street.
- **Coopers (4 inferred, 0 documented).** Clybourne packed ~250 cattle and ~2,000 hogs in the
  season of 1833; Dole a further 250 and 1,000 at the same place; Newberry & Dole 300 and 1,400
  on the South Branch in 1834 (scan p. 1151). Packed provisions travel in barrels. The dataset
  held a packer, two slaughter-houses and no cooper.
- **Labourers (12 inferred, 0 documented).** The largest trade in any western town and the one no
  roster records, because a labourer advertises nothing, holds no office and joins no church
  committee — the three ways almost every documented person in this dataset became documented.
  All twelve are housed in the meanest roofs the schedule carries, D1 cabins and D2 shanties.
- **Laundresses and domestics (7 inferred, 0 documented).** The hotels and boarding houses
  "were always full; and full meant three in a bed sometimes, with the floor covered besides".
  **The documented layer holds not one woman in a service trade** — not because none were here,
  but because these sources name women almost exclusively as wives and proprietors' widows.
  These are the only person records in the layer that state a sex, and the note says why.
- **Blacksmiths (3 inferred, 5 documented).** The owner's own example. Five smiths are named and
  the schedule allows six W1 shops; this parcel builds Mason's documented third smithy and infers
  three more households, which brings the town to exactly six shops.
- **The second barber (1 inferred, 1 documented).** One barber-surgeon in a town of ~350 in 1833.
  At ten times the population the second barber is not a guess about a person; it is a statement
  about a ratio.

## 4. The buildings

**Adoption first.** Where an anonymous roof of the right family stood free in the right district,
the household takes it: `lives_at` / `works_at` point at it, and the roof gains an `occupants`
block saying which household and why. **Its existence, position and footprint stay conjectural** —
nothing about the adoption is evidence that a building stood there. What changes is that a
count-unit becomes a building with an argument behind it. 83 roofs of 108 are now occupied; the
25 left are privies, sheds, stables and the anonymous schoolhouse, which is what should be left.

The link is **data, not a hand edit**: `tools/inferred_occupancy.py` is a ledger both anonymous
infill generators read, so those parcels still re-derive byte for byte and their drift checks
keep working.

**Seven documented buildings phase one found with no record, now built:**

| record | what is documented | what is invented |
|---|---|---|
| `brown_boarding_house` | log fabric, use, keeper (Mrs Rufus Brown), position "the first building in the rear of this store" | every dimension; the exact distance behind Peck's store |
| `heacock_house_monroe` | built spring 1835, moved a block on rollers, household of seven | which street it stood on at the scene date, where on it, every dimension |
| `mason_blacksmith_shop` | the firm's own 1833 advertisement, "Main-street, nearly opposite Graves' Tavern" | the lot, the setback, every dimension |
| `harmon_log_cabin` | "his residence was a cabin of **hewn** logs" | the position entirely; every dimension |
| `temple_lake_st_building` | Caton's first law office, his bed in the attic, "on Lake Street" | position along the street; every dimension |
| `wright_building_to_let_a` / `_b` | "Two Buildings to Let", John Wright's own advertisement | position; every dimension; the tenants (deliberately none) |

The eighth building on phase one's list — **a physician's office** — is *not* documented and is
not written as if it were. Eight doctors are documented and no office is; `physicians_office` is
an inferred building occupied by an inferred physician's household, precisely so that no real
doctor is attached to an invented address.

**31 inferred buildings**, placed by ROADMAP K1's own rule — businesses toward the river and the
built streets, residences further out. The shops sit on the South Water and Lake Street frontage
bands and on the Canal Street approach at Wolf Point; the dwellings sit in the outer bands and on
the fringes. Every centre was tested before it was frozen: against the oriented footprint of
**every** structure in the dataset, against the **reserved slots of the two uninstantiated
phase-2 recipes** so a later parcel cannot collide with this one, and against the committed
heightfield for coverage, dry ground and the walker's step tolerance. `--check` re-runs all of it.

**No lot line is claimed.** The bands come from the 80 ft platted street module in
`data/traces/street_control.json`, which is the same geometry the existing recipes work in. When
ROADMAP K7 generates lot geometry, these centres should be snapped to it and the placement rule
in the recipe replaced.

**Done 2026-08-13, and the snap found a systematic error rather than a rounding one.** K7's grid
landed and the placement gate gained a corridor test (`tools/plat_corridors.py`, shared with
`tools/generate_plat_lots.py --report` so the two cannot disagree). The recipe had been reading
the frontage bands as centre-lines to sit ON rather than as edges to sit BEHIND: **23 of the 38
buildings put part of a footprint inside a platted street corridor, and twelve stood with their
CENTRE in the road.** All 23 centres moved — median 12.0 m, worst 21.9 m — to the nearest
position that clears every corridor, every committed footprint by 3 m, the reserved phase-2
slots, and the heightfield's dry covered ground. Three could not simply step back off the street:
`physicians_office` would have landed in the First Presbyterian Church, `inf_packer_dwelling` in
a reserved phase-2 slot, and `inf_cooperage_south` in the South Branch. Nothing else about these
records changed — the positions were `conjectural` before the move and are `conjectural` after
it, and clearing the roadway is not the same as standing on a recovered lot. Detail:
`docs/RESEARCH/thompson_plat_grid.md` § 7a.

## 5. What this parcel refused to do

- **It did not invent a name.** Not one. Where the documented layer says "Mrs Rufus Brown", this
  layer says "A laundress (inferred resident, unnamed)".
- **It did not invent a source.** No trade ratio is cited to a table that does not exist in
  `data/sources/`; where the argument is this project's own arithmetic, the note says so.
- **It did not launder a conjectural value into an inferred one.** The existence, position and
  footprint of a building nobody recorded are `conjectural` here exactly as they are on the 108
  anonymous roofs and on 59 named records — which is why this parcel owes `docs/LIBERTIES.md`
  one substantial entry with 106 `Covers:` tokens, and says so rather than grading its way past
  the gate.
- **It did not fill the west division.** The West Division phase-2 recipe reserves 55 slots that
  have never been instantiated; this parcel places nine buildings on west-side ground **outside**
  those reserved envelopes and leaves that parcel intact for whoever takes it.
- **It did not touch the removal.** No inferred household is Native, and none is placed at Wolf
  Point among the households that are. Inventing an Indigenous resident is exactly the improvisation
  AGENTS.md forbids; the sourced Native households of phase one stand as they are, flagged
  `review_required`.

## 6. Where the numbers stand after this parcel

| | phase one | after phase two |
|---|---|---|
| households | 72 | **152** |
| person entries | 96 (76 documented, 20 derived, 0 inferred) | **188** (76 / 20 / **92 inferred**) |
| structures | 184 | **222** |
| anonymous roofs with an occupant | 0 | **83** |
| dwellings the census wants | 398 | 398 — still the target |

The town still holds three thousand people this dataset cannot name, and 398 dwellings against
which it now models rather more roofs than before but nothing like all of them. The next
increments are the two reserved phase-2 recipes (55 west, 84 south), the `Chicago American` of
1835–36 for documented residents *in the scene year*, and the 1832 militia roll.

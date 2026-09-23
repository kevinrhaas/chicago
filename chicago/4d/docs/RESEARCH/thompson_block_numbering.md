# Thompson's block numbers, and the one address in the corpus that needed them

**Investigated:** 2026-08-29 · **Re-read block by block:** 2026-09-06 ·
**Tickets:** T-0358, then T-0788 (owner ask), T-1088, T-1094, T-1098, T-1099 ·
**Record:** none — this is a memo about a *reading* and the count made from it ·
**Data:** `data/traces/thompson_block_numbering.json` (authored),
`data/traces/vectors/thompson_lots.json` (`plat_block_number`, `plat_lot_number`) ·
**Source:** `wright_1834`, through the georeferenced BPL scan
(IIIF `commonwealth:js957744g`); previously through
`data/sources/assets/prefire_views_kevin_2026_08/wright1834_clark_reach_crop.jpeg` ·
**Gate:** `tools/generate_plat_lots.py --check`, in `tools/check.sh`

---

## 0a. The North Division's tier, read once its streets were committed (T-1088)

**2026-09-12.** § 0's reading stopped at twenty-two because the crop has to be *cut from
committed street lines*, and in September 2026 the grid held nothing north of the river. It
does now: Kinzie Street, the six north–south lines of the North Division — Market, Franklin,
Wells, La Salle, Clark, Dearborn — and Wolcott closing the tier on the east are all in
`data/streets/1835.json`, all graded `attested`. So the tier between Kinzie Street and the river
was cut and read by exactly the § 0 method, and it carries seven numerals:

| west → east | direction |
|---|---|
| **7** 6 5 4 3 2 1 | falls eastward |

Block 7 is the one the river bounds. It has no committed street on its west, so its box is cut
one module (123.36 m, the mean spacing of the six flanking lines) west of Market Street and is
wider than the block; the entry cites both that derived box and the tighter region the numeral
was actually read on, and the tighter one lies wholly inside it.

**Block 6 is the only hard read of the seven.** The curved road that leaves the Kinzie / North
Water corner and runs north crosses the numeral, and its west kerb passes through the glyph's
upper stroke. What survives is a stroke descending from the upper right into a closed bottom
loop — Wright's 6, not his 5, whose top carries a flag (block 5, one block east, prints one for
comparison in the same hand and the same size). The tier's own run agrees on both sides.

**These seven are NOT on the grid, and that is deliberate.** `tools/generate_plat_lots.py` emits
the three South Division tiers and nothing else, so there is no cell in
`data/traces/vectors/thompson_lots.json` for a North Division number to be stamped onto. Forcing
one would be the mistake this file exists to avoid, so the readings sit in
`blocks_not_in_the_grid` beside 44 and 43, waiting for a cell. Widening the generator north is
its own unit of work.

**What IS gated is the citation.** `tools/read_north_division_numerals.py --check` re-cuts all
seven crop regions from the committed street lines and fails if they have drifted, and
`tools/check.sh` runs it. A street that moves now invalidates its own crop instead of quietly
outliving it — which is the property § 0's twenty-two do not yet have.

**The lot rows run the other way up here.** Four of the seven blocks print both rows legibly —
7, 4, 2 and 1 — and every one prints **5 6 7 8 across its north row** west to east and **4 3 2 1
across its south row**, the mirror of the South Division scheme in § 5. So lot 1 sits at the
block's south-east corner here and at its north-east corner there. In both divisions that is the
row facing the river, which is a tidy rule and is *not* claimed: it rests on one reading per
division, and a tier away from the water in either would test it. What is claimed is the four
blocks, which agree with one another. The grade is unchanged and for the unchanged reason — the
lot lines are a module divided, not a line drawn from any sheet, so a number on one is
conjectural whatever the number's own provenance.

**Still refused: 52–58, 8–13, 22–27, 46–51, and 14–15 on the North Branch's west bank** — the
Washington–Madison tier, the West Division past Clinton, and the far bank. No committed street
line reaches any of them, so no crop can be cut, and reading them by eye is the method this file
was rebuilt to replace. That refusal is T-1089.

## 0b. The Original Town's last tier, Washington to Madison (T-1094)

**2026-09-12, the same day as § 0a and for the same reason.** Madison Street landed with
T-0877, so the Original Town's southernmost tier is enclosed, and it was cut and read by the
§ 0 method. It carries seven numerals:

| west → east | direction |
|---|---|
| **52** 53 54 55 56 57 58 | **rises** eastward |

**The boustrophedon holds, and this tier is the first test of it that was made in advance.**
§ 0 read three tiers — falling, rising, falling — and said in terms that the alternation was
what the sheet drew rather than what a count assumed. A fourth tier under that rule must rise,
and this one does. Nothing was arranged to make it: the numerals were read block by block off
their own crops, and 52 sits at the river end.

**What is weaker here than in the North Division, stated plainly.** Washington and Madison are
committed across the whole tier. The seven north–south lines that flank the blocks — Market,
Franklin, Wells, La Salle, Clark, Dearborn, State — are committed and `attested`, but every one
of them **stops at y = −400 m**, ten metres south of Washington and a hundred and thirty-four
short of Madison. So three of each box's four sides are a committed line and the fourth pair is
those same lines *continued south along their own bearing*. That continuation is arithmetic on
committed endpoints, and it is **not** written into `data/streets/1835.json`: this project has
no control for the tier's north–south lines, and a line it has no control for should not be
published as a street. `tools/read_washington_madison_numerals.py` states the rule, the gate
re-cuts every box from it, and the readings are graded `inferred` like every other numeral here.

**The module agrees with the North Division's to the centimetre.** The mean spacing of the seven
flanking lines at Madison is **123.36 m** — the same figure the North Division's six produced in
§ 0a, measured on different streets a kilometre away. Neither was derived from the other.

**Block 52 is the one that is not wholly inside its own box.** Its west edge is the South Branch
and not a street, so — exactly as block 7 in § 0a — the box is cut one module west of Market
Street and is wider than the block. The numeral then sits in the box's eastern sixth, and the
2's terminal flourish runs about 10 px, some **7 m on the ground**, past the east edge. The
cause is measurable rather than mysterious: the georeference seats Market Street roughly **25 m
west** of the block line Wright inks there, and the crop's edge is the georeferenced line, not
the inked one. The entry records the window it was read on, records the overhang as a number,
and the gate checks that number instead of tolerating it. The other six are wholly inside.

**Block 55 is what fixes the hand.** It prints two flagged 5s side by side, same size, same pen,
and every other entry in the tier reads its leading glyph against them. That is what separates
block 53's second glyph — bowl closed, no flag — from a second 5.

**These seven are NOT on the grid either.** `tools/generate_plat_lots.py` emits the three South
Division tiers between South Water and Washington and nothing south of Washington, so they wait
in `blocks_not_in_the_grid` beside the North Division's seven, and beside 44 and 43.

**Thirty-eight of fifty-eight are now read.** Still refused: **8–13, 22–27, 46–51 in the West
Division past Clinton, and 14–15 on the North Branch's west bank** — no committed street line
reaches either, so no crop can be cut, and reading them by eye is the method this file was
rebuilt to replace. That remainder is T-1095.

## 0c. The West Division, all eighteen of it (T-1098, out of T-1095)

**2026-09-13.** The eighteen numerals west of the South Branch — **8-13, 22-27, 46-51** — were the
last of the fifty-eight still refused, and they were refused for a reason the § 0 method cannot
argue with: *a crop is CUT from committed street lines, and the grid did not reach the West
Division*. This section is about how that stopped being true, because the answer was not to draw
new streets.

### The three kinds of side

| side | blocks | what it is |
|---|---|---|
| committed | 8, 13, 23, 50 outright; every box's east or west somewhere | `clinton` and `canal` run the length of the division; `kinzie`/`kinzie_west` and `madison` reach its whole width |
| continued | every box's north and south | `carroll`, `fulton`, `lake`, `randolph`, `washington` are committed but CLIPPED at east −320 m, and each is continued west along the bearing of its own committed path. The clip is this reconstruction's extent, not a claim the street ended there — `fulton`'s own note says so |
| stepped | the Jefferson and Des Plaines flanks; the river side of 22 and 51 | `clinton` stepped one and two modules west, and `canal` one module east |

The stepped flanks are the interesting ones, and they are stepped rather than drawn **because this
project has already refused to draw them**. `docs/RESEARCH/west_division_streets.md` § 2 refuses
Jefferson Street and Des Plaines Street outright: both lie wholly west of the modelled ground's edge
at east −320 m, and a street hung off the end of the terrain is the same fault this repository
already fails a *block* for. That refusal stands. Nothing here writes a line into
`data/streets/1835.json`; the step is a computation used to cut a crop, exactly as T-1094's
southward continuation was, and it is stated so a reader can disagree with it.

### What licences the step — three agreements, all from control already committed

| check | figure |
|---|---|
| `clinton` + one module against the committed `canal`, at Lake Street | **0.46 m** |
| the same, at the scene's south edge | **2.34 m** |
| `clinton` − one module against Jefferson × Fulton (OSM 262247424, committed in `fulton`'s note) | **8.70 m** |
| `clinton` − two modules against Des Plaines × Fulton (OSM 258966841, same note) | **8.22 m** |

The module is 123.36 m — the mean spacing of the Original Town's seven flanking lines at Madison
Street, the figure T-1088 and T-1094 each measured independently a kilometre away. The first two
rows are the step reproducing a line this repository already holds. The last two are it landing
eight metres west of two surviving intersections, **both to the same side**: a seat with a bias, not
a scatter, and eight metres on a 123 m module is a quarter of the 17.5 m RMS the georeference itself
carries. The gate re-measures all four and fails if any exceeds 15 m.

`tools/read_west_division_numerals.py` cuts the boxes and `tools/check.sh` runs its `--check` and
`--self-test`.

### The eighteen, and the run they make

| band, west → east | direction |
|---|---|
| Kinzie–Carroll: **10 9 8** │ the North Branch │ 7 6 5 4 3 2 1 | falls eastward |
| Carroll–Fulton: **11 12 13** | rises eastward |
| Fulton–Lake: **25 24 23 22** | falls eastward |
| Lake–Randolph: **26 27** 28 29 | rises eastward |
| Randolph–Washington: **47 46** 45 44 43 | falls eastward |
| Washington–Madison: **48 49 50 51** 52 … 58 | rises eastward |

Bold is what this ticket read; the rest is what T-0788, T-1088 and T-1094 had already read in the
same bands. **That is the reading's own check, and it is a hard one.** The alternation § 0b first
tested in advance now has to survive six more bands, and in four of them this ticket's numbers have
to JOIN a run somebody else read from different crops: 26 27 into 28 29, 47 46 into 45 44 43, 48 49
50 51 into 52, and 10 9 8 into the North Division's 7 across the water. A numeral misread, or a box
cut onto the wrong block, breaks that join. The tool asserts it and the gate runs the assertion.

Eighteen boxes cut from committed lines, eighteen numerals landing inside them, **no overhang
anywhere** — where the Washington–Madison tier had one block whose glyph ran past its own edge.

## 0d. The last two, and the collision that was hiding them (T-1099)

**2026-09-13.** § 0c closed at fifty-six of fifty-eight and handed on two blocks and a
contradiction. Both are settled here, and they turned out to be the same thing.

### The contradiction

A glyph reading 14 stands at raster px 1464, 1697 — local east **+24.6, north +83.8** — and that
point lay **inside the box § 0a cites for block 7** (`1376,1452,178,298`), whose own numeral was
read two hundred pixels north of it. Two block numerals cannot stand in one block. § 0c offered
two ways out: the column is two blocks and § 0a's box is too tall, or one of the readings is
wrong.

**It is the first, and neither reading is wrong.** § 0a's south rule is *the southern endpoint of
the flanking platted lines, where they stop at the river — taking the northern of the two so the
box does not reach across the bank.* Block 7 is the one block in that tier with a **single**
flank: its west side is the North Branch, not a street. With one endpoint there is no northern of
the two, and the rule collapsed onto that one endpoint — Market Street's. Market is precisely the
line that does **not** stop at this tier: `market_north` runs on south to the bank in the forks
and ends at north **+46.35 m**, where `franklin_north` immediately beside it ends at **+151.61 m**,
a whole tier higher. The box therefore ran **89 m past its own block** and took in the next one.

This also corrects § 0c's own statement of the refusal, which said the North Division's streets
"stop between north +108 and +126 m, a hundred metres short of the band". They do not. They stop
at +46.35 (Market), +151.61 (Franklin), +126.06 (Wells) and +108 to +109 (La Salle east to
Wolcott) — the north bank of the Main Branch, which runs *diagonally*. Market stops **below** the
Carroll–Fulton band, not above it, and that is why a box hung from it reached down into 14.

### The two blocks

Wright draws them, and no new control was needed to cut them:

| | 14 | 15 |
|---|---|---|
| west | the North Branch — Market stepped one module west | `market_north` |
| east | `market_north` | the river's bend — Market stepped one module east |
| north | Carroll continued east | Carroll continued east |
| south | Market Street's southern endpoint, at the bank in the forks | the same |
| box | `1376,1624,177,126` | `1552,1628,178,126` |
| read at | `1458,1679,52,40` | `1592,1652,46,32` |

**14** is the block between the two rivers and Market Street, the one the sheet draws with its
south-east corner cut off along the bank. **15** is the small right triangle east of Market —
vertical west side, horizontal north side, and a hypotenuse that is North Water Street following
the bank round the bend. The stepped flank on each river side is block 7's own rule from § 0a and
blocks 22, 51 and 52's from §§ 0b–0c; the module is the same 123.36 m.

**The fourth side is the only thing here that is not committed ground.** Carroll Street is
committed and stops at the North Branch's west bank, at (−104.96, +136.47). It is continued east
along the bearing of its own committed path — T-1094's and T-1098's rule, turned east — 68 to
192 m past that end for block 14, and 192 to 315 m for block 15. It is not carried further: east
of Wells the bank runs south of Carroll's line and the tier has no room for another block, so
nothing below § 0a's blocks 5 to 1 is cut from it.

**What corroborates it.** Wright draws a street between the two tiers, and its block faces read
off the sheet at local east +40 are north **+155.7** (block 7's south face) and **+130.5** (block
14's north face); east of Market they are **+153.0** (block 6's south face) and about **+120**
(block 15's north face). Carroll continued lands at **+135.5** and **+134.5** — inside the drawn
street at both longitudes, and on the same side of its centre at both. That measurement is read by
eye and so is stated here rather than gated.

**And the boustrophedon is the check that is gated.** The Carroll–Fulton band runs 11 12 13 rising
eastward; 14 and 15 are appended to that band's tail in `tools/read_west_division_numerals.py`, so
the two numerals read here have to continue a run three other blocks already fix, with the band
above (10 … 1) falling and the band below (25 24 23 22) falling. A numeral misread, or a box cut
onto the wrong block, breaks it.

**The glyphs.** 14's first mark is the plain flagged diagonal Wright writes for **1**; his **7**,
one block north of it and again in block 47, carries a hooked top this diagonal does not. Its
second mark is his **4** — narrow pointed loop, crossbar, descender below the line — the same
figure as the 4 of block 47. 15's second mark carries a flag across its top, which is how this
memo has twice before told Wright's **5** from his 6 (§ 0a, block 6).

### The gate

`tools/read_wolf_point_numerals.py --check` re-cuts both boxes from Market Street and Carroll
continued, checks each read window lies inside the box it is cited under, and asserts directly
that **neither block's numeral lies inside the other's crop** — the fault, named, so it cannot
come back. `--self-test` breaks it by moving Carroll's east end 40 m. § 0a's tool now carries the
same dependency and its self-test fires on it too.

**Fifty-eight of fifty-eight.** Nothing on Wright's sheet is refused any longer for want of
control.

## 0. Superseded in the best way: the numerals were there all along

**2026-09-06, T-0788.** Everything below §§ 1–3 stands as the record of how six blocks got
their numbers from two numerals. **The counting is over.** Twenty-two numerals are now READ off
the sheet, one crop per block, and the four numbers this memo counted — 21, 20, 17, 16 — are
among them. **All four counted values were right.** Nothing moves; what changes is that the
numbers are evidence instead of arithmetic.

**What made it possible was not a better scan — it was asking the georeference for the crop.**
This project is fitted to the BPL copy (`data/traces/gcp/wright_1834_gcps.json`, affine from
eight ground control points, RMS 17.5 m). So for any block the grid holds, the four bounding
street centrelines of `data/streets/1835.json` give a box in local ENU, `tools/wright_px.py`
maps it into the scan's pixel space, and IIIF returns that box at 6×. The block fills the frame.
**Which block carries a numeral stops being a thing the reader decides.** Every entry in
`data/traces/thompson_block_numbering.json` cites the region it was read on, so any reader may
re-open the same rectangle and disagree.

**The run reverses tier by tier, and § 4's refusal was right to refuse it.**

| tier | west → east | direction |
|---|---|---|
| South Water – Lake | 21 20 19 18 **17 16** | falls eastward |
| Lake – Randolph | *28 29* · river · 31 32 33 34 35 36 | **rises** eastward |
| Randolph – Washington | *45 44 43* 42 41 40 · **Public Square** · 38 37 | falls eastward |

*(italic = West Division, west of the South Branch)*

A count carried straight down from the South Water tier would have numbered the Lake tier
backwards. § 4 refused to carry it and said, in terms, that a boustrophedon was one of the
possibilities it could not choose between. It was the one the sheet draws.

**The Public Square carries no numeral.** Wright washes the block pink, rules it into eight lots
like its neighbours, and letters *Public Square* across it where the number would go. So **39 is
the one number in the file that is still counted** — and it is counted across a single block
bracketed by numerals read on both sides: 40 immediately west, 38 immediately east, in a tier
falling by one. One number fits between them. `numeral_on_sheet: false` says so on the record,
and the same reasoning is written onto
`data/reconstruction/1835_reserved_ground.json`, which is where this block's identity is argued.

**Block 16's numeral is on the sheet.** G. Spring's *"LOT No. 7, in block No. 16 … on Lake
street"* no longer rests on a count three blocks long (§ 6). It rests on a numeral in the block's
own frame, on the notice's own "on Lake street", and on the Botsford/Andreas placement of
Haddock's Tavern. The three-way agreement of § 6 is unchanged and is now a check on a reading
rather than a check on arithmetic.

**The lot scheme is read on four blocks, not one.** Blocks 20, 18, 16 and 40 each print
**4 3 2 1** across the north row west to east and **5 6 7 8** across the south row west to east.
Block 40 is in a different tier, whose BLOCK numbering runs the other way — so the lot run is a
property of the block, not of the tier. § 5's grade does not move: the scheme is read, the LINES
it numbers are still the module's, and a number on a conjectural line is conjectural. What the
three extra readings buy is that the scheme is no longer a one-block reading.

**Not every block carries eight lots.** The West Division block west of block 28 prints
`1 4 5 8 9` down its side — ten lots, two rows of five, numerals written across a horizontal
alley. No West Division block is emitted by the generator today, so nothing is mis-numbered;
it is recorded in `lot_numbering.ten_lot_blocks` so that the day one is, this is found first.

**What is still refused, and why it is the same refusal.** Twenty-four of fifty-eight blocks are
held. The Washington–Madison tier, the North Division and the West Division beyond Clinton are
refused because the method is *cut the crop from committed street lines*, and the committed
street grid does not reach them. A numeral found by eye instead, on paper that stretches 3.7%
anisotropically, is a numeral placed by the reader — the mistake this file was rebuilt to stop
making. Block **30** is refused separately: the Lake tier reads 29 on the west bank and 31 on the
first block east of the branch, and the ground between them is water, so 30 is somewhere not yet
read and nothing here says where.

**One cell is two blocks.** The grid's `blk_randolph_canal` runs Canal Street to Market Street,
243 m, and spans **44** on the west bank and **43** on the east with the river between them. It
therefore takes NO number — one number on a cell that is two blocks is a claim the sheet does not
make — and both readings are parked in `blocks_not_in_the_grid`, waiting for the day the grid has
an id for them.

---

## 1. What was missing

G. Spring's For-Sale notice ran in the *Chicago Democrat* six times between 1834-06-18 and
1834-11-19 and is **the only lot-and-block address in the whole newspaper corpus**:

> For Sale, **LOT No. 7, in block No. 16, one lot east of Haddock's Tavern, on Lake street**, in
> the town of Chicago. There is on said lot a large Dwelling-House and fine well. For terms
> enquire of G. SPRING.

Three readings had recorded that this was the most placeable statement the corpus makes and
that placing it was somebody else's job. It was nobody's, because nothing committed carried
Thompson's block NUMBERING: `data/traces/vectors/thompson_lots.json` keys its nineteen blocks
on their bounding streets, and no record in `data/sources/` numbered one. "Block No. 16"
resolved to nothing, and so did "Lot No. 7" inside it.

## 2. The evidence is two numerals, and it used to be quoted as three

The project owner's crop of Wright's 1834 sheet at the Clark reach carries block numbers. Both
memos that cite it — `clark_reach_bulge_1834.md` § 8 and `thompson_plat_grid.md` § 4 — said it
reads "block numbers 19, 18 and 17".

**Re-read at full resolution it carries 19 and 18.** The file is 639 × 719 px and the map region
inside it ends at block 18's east edge; there is no third block on the sheet. The asset's own
README, written when it was supplied, describes exactly two ("a narrow sinuous line dropping
south off the bank between numbered blocks 19 and 18"), so the third arrived somewhere in the
retelling. Both memos are corrected here.

Nothing that was built on the crop moves. Both memos used the numbers to establish the step and
the direction of the run, and two consecutive numerals do that as well as three do. What changes
is the size of the evidence base, which is the thing a later reader needs in order to know how
far it can be pushed — and § 4 pushes it three blocks.

## 3. What the two numerals fix

**The step is one and the direction falls eastward.** 19 stands west of 18.

**The run is along the tier, not down a column.** Two blocks side by side in one row differ by
one. A column-major numbering would separate them by the number of rows.

**Which blocks they are, at ±20 m.** The crop shows a narrow sinuous watercourse drawn down the
street between the two blocks, with the platted **80** written in it. That stream is already
traced and committed: `clark_reach_bulge_1834.md` § 4 measured its mouth at local
**E +462 … +469**, and established — against the reading that it was the river bulge — that the
committed trace runs up the inside of its own ink line there. La Salle Street's committed
centreline is at **E +451.3**, so its corridor spans E +439.1 … +463.5 and the stream is drawn
in the east half of it. The next candidates are Wells at E +329.3, 122 m west, and Clark at
E +574.7, 123 m east.

So the crop's two blocks are the **Wells–La Salle** block (19) and the **La Salle–Clark** block
(18) of the tier fronting South Water Street on the north and Lake Street on the south. That
step is an inference and is graded as one; it is not a close call.

## 4. Counting along the tier

| block | id | number | numeral, 2026-08-29 | numeral, 2026-09-06 |
|---|---|---:|---|---|
| Market–Franklin | `blk_south_water_market` | 21 | counted (2 west) | **read** |
| Franklin–Wells | `blk_south_water_franklin` | 20 | counted (1 west) | **read** |
| Wells–La Salle | `blk_south_water_wells` | **19** | **read** | **read** |
| La Salle–Clark | `blk_south_water_lasalle` | **18** | **read** | **read** |
| Clark–Dearborn | `blk_south_water_clark` | 17 | counted (2 east) | **read** |
| Dearborn–State | `blk_south_water_dearborn` | **16** | counted (3 east) | **read** |

The last column is § 0's re-reading, kept beside the count so the two can be compared. **Every
counted value was right**, which is worth exactly as much as it is worth: four out of four is a
good record for a step of one along a row, and it is not a reason to trust a count over a
reading anywhere else.

`blk_south_water_market` is not in the grid — South Water's committed centreline stops 24 m short
of it (`thompson_plat_grid.md` § 6) — so its number is stamped onto the omission, where the two
facts sit together instead of one contradicting the other's absence.

**Nothing else is numbered, and the refusals are the load-bearing part.** The crop fixes the
direction of the run *inside* a row and says nothing about how it passes from one row to the
next. A boustrophedon that turns back west, a run that restarts at the west end of every tier,
and a run that descends a column all reproduce 19 beside 18 and give the Lake–Randolph and
Randolph–Washington tiers different numbers. The West Division is refused for the same reason
one step larger, and the North Division has no blocks to number. Where the tier's own run begins
and ends is refused too: only offsets from the two read numerals are claimed here.

**No modern plat reprint was consulted**, and the authored record says so in terms. If one
agrees, that is a corroboration somebody may fetch and cite; if it disagrees, it is evidence.
Neither may be quietly substituted for this reading.

## 5. The lot scheme, and why its number is conjectural wherever it lands

Block 18's north row is set **4 3 2** west to east and its south row **5 6 7**, the fourth of
each falling outside the crop. That is a counter-clockwise run from the block's north-east
corner: **1–4 east to west along the north row, 5–8 west to east along the south row.**

The scheme is emitted only inside a numbered block, and it is graded `conjectural` *everywhere*,
including on block 18 itself. Four lots to a face is a reading of this one block
(`thompson_plat_grid.md` § 4); the lot lines in `thompson_lots.json` are the module divided into
a block and carry `conjectural` for that reason. **A number put on a line no sheet drew is
conjectural whatever the number's own provenance.** What the scheme is good for is reading a
documented address onto the grid. It is not evidence of where a lot line ran.

## 6. The check that was not built into the count

Counting east three blocks from 19 puts **block 16 on Dearborn–State**. Three statements made
independently of each other, and of this count, land on the same ground.

- **The notice itself.** "block No. 16 … **on Lake street**". Block 16 as counted is bounded south
  by Lake Street, and under the scheme in § 5 its Lake frontage is the row numbered 5 to 8.
  A count that had landed one block out would have put block 16 on a tier Lake Street does not
  bound, or on the wrong side of it.
- **Its own neighbour clause.** "LOT No. 7 … **one lot east of Haddock's Tavern**". Lot 7 is the
  third lot east of the Dearborn corner, so Haddock's is the second — not the corner lot.
- **A placement argued before this file existed.** Haddock's Tavern is the Mansion House
  (`data/structures/mansion_house.json`, and T-0324 for the succession). Andreas has it "on Lake
  near Dearborn"; T-0324 read J. K. Botsford's two advertisements — "next door to Graves' Tavern"
  and "Corner of Dearborn and Lake-sts." — as one frontage on the corner lot, and concluded the
  tavern stood **on the second lot from Dearborn rather than on the corner**
  (`botsford_graves_1834.md`). That is lot 6, one lot west of lot 7.

Three readings, three sources, one block face. **The arithmetic is still arithmetic** and every
number in § 4 stays `inferred`; what the agreement buys is that nothing independent contradicts
it, on the one block where anything independent could.

The other four counted numbers have no such check. 17, 20 and 21 rest on the step alone, and the
authored record says so on each of them rather than letting block 16's corroboration wash over
the tier.

## 7. What is now measurable, and is deliberately not done here

The Lake Street row of block 16 as this dataset stands today:

| lot | what stands on it | centre |
|---:|---|---|
| 5 | `mansion_house` | E +718.2, N −96.1 |
| 6 | `recon_1835_blk_south_water_dearborn_d2_04` — an anonymous reconstructed roof | E +750.9, N −94.9 |
| 7 | `recon_1835_blk_south_water_dearborn_h1_03` — an anonymous reconstructed roof | E +773.3, N −93.3 |

So the address resolves, and it resolves onto two consequences this ticket does not act on:

1. **The Mansion House stands on lot 5 and the corpus puts it on lot 6.** Its committed position
   was set with its west face on the Dearborn frontage — the corner lot — from Andreas's "on
   Lake near Dearborn". The gap is **24.2 m, one lot, eastward**, and it is *inside the
   uncertainty that record already declares* ("the house may have stood one or two lots further
   east … read the along-street position as good to about plus or minus 20 m on top of the
   georeference"). T-0324 reached the same conclusion from Botsford and deliberately did not
   move the record. Nothing here changes that judgement; what changes is that the discrepancy is
   now a number instead of a sentence.
2. **Lot 7 carried a large dwelling-house and a fine well**, and an anonymous count-unit roof
   stands on it. Standing Spring's documented house there is a visible change and a separate
   piece of work, filed as its own ticket.

Neither is smuggled in here. Moving a committed building on the strength of an inference made in
the same commit that authored the inference is how a reconstruction talks itself into precision
it has not paid for.

## 8. What this is not

- **Not rendered.** The grid is a dataset layer and the walkthrough does not draw it, so nothing
  here adds to `docs/LIBERTIES.md` — a liberty records something invented that a visitor is
  looking at. Nothing was invented in any case: every number here is counted from two numerals
  on a survey sheet, and everything that could not be counted is refused in writing.
- **Not a cadastre.** No lot is owned and no lot is claimed to be the lot a particular building
  stood on. § 7 is a report of where this dataset's own buildings fall, not a title.
- **The whole plat, as of 2026-09-13.** Fifty-eight blocks of fifty-eight — six when this memo
  was written, another eighteen read in § 0, the North Division's seven in § 0a, the
  Washington–Madison tier's seven in § 0b, the West Division's eighteen in § 0c and the last two
  in § 0d. What is still refused is not a block but a question: where each tier's run begins and
  ends, block 30 (which is water), and the confidence grade itself — all three in the trace's
  `refused`, by name.

# The generators reading the tract layer

T-1105, piece 2 of T-1102, itself item 4 of T-1097's four and the half
[`land_sales_by_survey_tract.md`](land_sales_by_survey_tract.md) § What this does not do
explicitly did not do. Two generators were asked to read the survey-tract layer T-1101
built. One of them now does, and what it found is not what the ticket expected.

## 1. The plat module asks the layer, and the layer answers the same thing nineteen times

`tools/generate_plat_lots.py` chose ONE street width and ONE block module — Thompson's
80-ft street and 18-ft alley, four lots to a block face — for every block it builds,
because until `data/reconstruction/1835_survey_tracts.json` existed there was no layer to
ask. The ticket's worry was the obvious one: *a block in Wabansia or Kinzie's Addition
should not silently take the Original Town's module.*

It now asks. Every generated block is clipped against every placed tract ring, under
T-1104's precedence clause and with T-1104's clipper — imported, not written again, so
the two files cannot give two answers to one question — and the tract, the share and the
list of every ring the block touches are stamped on the block.

**All nineteen fall in `canal_commissioners_1830`, and no second ring touches one.** The
tract record already said so in passing (`geometry_note`: *"all 19 committed plat blocks
fall inside the rectangle"*); this is that sentence turned into a per-block field and a
gate. So the ticket's worry does not fire: no block this generator builds stands in
Wabansia or in Kinzie's Addition, and a per-tract module would change nothing about what
is drawn. The layer cannot discriminate this grid, and saying so is the finding.

The grade travels with the answer. `canal_commissioners_1830` is `conjectural` — its four
bounds are the standard account of the 1830 plat and no source record here states them —
so a module chosen off that ring would inherit that grade. None is. The tract is carried
as a finding; the module is still chosen off the committed street lines.

## 2. What varies inside the one tract is the division, not the tract

The river runs through the Original Town, and the plat gives its two sides different
blocks. `data/traces/thompson_west_division_lots.json` (T-0689) reads the West Division's
own module off the sheet and grades the figures `documented`:

| | South Division | West Division |
|---|---|---|
| lot frontage | 80 ft | 75 ⅗ ft |
| lot depth | half the block, less the alley | 180 ft |
| alley | 18 ft, east–west, mid-block | 18 ft, **north–south** |
| arrangement | four lots to each of two faces | **two columns of lots backing onto the alley** |
| block | ~320 ft × block depth | 378 ft square |
| street module | 400 ft | 458 ft |

That is a different *arrangement*, not a different frontage figure — the lots are turned
ninety degrees and the alley with them. Two of the nineteen blocks stand on it:
`blk_lake_clinton` and `blk_randolph_clinton`, both bounded west by Clinton and east by
Canal. Which streets are West Division streets is read off that file's own block table
(`bounded_west_by` / `bounded_east_by`), not asserted here.

## 3. And the printed module will not seat on the committed lines

The refusal is arithmetic, and the generator computes it rather than quoting it:

- Two 180-ft lot columns need **360 ft** of face before the alley is cut. The committed
  faces are **315.2 ft** (`blk_lake_clinton`) and **326.1 ft** (`blk_randolph_clinton`).
  The arrangement does not fit on either — it is short by 44.8 and 33.9 ft with the alley
  left out entirely, and by 62.8 and 51.9 ft against the sheet's 378 ft.
- North to south the blocks run 388.4 and 364.0 ft, which divide into **5.14** and
  **4.81** lots of 75 ⅗ ft. A plat does not print a fifth of a lot.

**What is short is the spacing, not the module.** The module closes exactly — 180 + 18 +
180 = 378, and 5 × 75 ⅗ = 378, two sums sharing no figure — while this project's Clinton
centreline stands **367.9 ft** from its Canal centreline against the plat's 458 ft, 90.1 ft
short. That is the same finding `tools/measure_west_division_module.py` reports and the
same one the owner reported on 2026-08-31 from the dev preview. Seating the printed module
means moving those centrelines, which is **T-0445**, and is deliberately not done here.

So both West Division blocks keep the South Division subdivision they were already built
on — and now carry, in `module.west_division_module_refused`, the module they did not
take, the figures it asks for, the figures they give, and the arithmetic between. The
silence the ticket objected to is what is gone; the 80 ft is unchanged, because the
evidence does not yet allow anything else. `--self-test` re-derives both halves, so the
day T-0445 moves the lines the gate fails with *"THE REFUSAL IS STALE"* rather than
letting a wrong subdivision stand.

**No coordinate moved.** The nineteen boundaries, 144 lots, five omissions and every
number in them are byte-identical to what was committed; this work adds fields. Nothing
to bake.

## 4. The reserved-ground record cites the reservation polygon

`data/reconstruction/1835_reserved_ground.json` is keyed by platted block, which is the
unit the plat module subdivides — and the largest piece of held-back ground in the scene
is not a block and never was. The United States Reservation was never platted: no street
crossed it and no lot line was drawn on it, so it could not appear in that file, and the
file said nothing about it at all. A reader asking *what ground was held back in 1835?*
got the public square and four school-section blocks and no hint of 65.7 federal acres
east of State Street.

A new `federal_reserved_ground` key cites it — the ring's id, where it is carried, what
derives it, its `inferred` grade and why it is not `documented` (no source draws the
perimeter, and the north-and-east side is a shoreline, which moves). The refusal itself
stays where it was authored, in `1835_no_build_ground.json`; duplicating it would put two
records in a position to disagree about the same ground.

One thing worth recording rather than reconciling: **Andreas prints 75.69 acres and this
ring measures 65.70.** Neither is wrong and they are not measuring the same edge. Andreas
gives the south-west fractional quarter of section 10 as the PLSS defines it; the ring is
that quarter as this project can draw it in 1835, cut on the north and east by the traced
1834 waterline instead of a surveyed line. Ten acres is what a shoreline standing in for a
section line costs.

The two committed copies of the ring were compared, not assumed: the 49 vertices
`reservation_ring()` builds and the 49 the tract layer carries agree to the two decimals
the layer is rounded at.

## What this does not do

`generate_plat_lots.py` was one of the two generators named. The **block infill** generator
reads block *boundaries* from this file and not the tract layer; it takes no module
decision of its own, so it inherits everything above and needs no change. Nothing here
touches the West Division's position — that is T-0445 — and nothing here promotes a grade.

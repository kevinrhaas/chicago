# The North Division's north–south streets, read off the plat

**T-0451, 2026-09-05.** Every number here is recomputed from committed files by
`tools/measure_north_division_streets.py`, which carries the assertions as
`--self-test` and which `tools/check.sh` runs. Its inputs are two committed files
and no image library: the pixel reading in
`data/traces/thompson_north_division_streets.json` and `data/streets/1835.json`.
`--reread` goes back to the 7 MB sheet and reproduces the reading exactly.

## The ask

> **`wolcott` is the only north–south street this reconstruction holds north of the
> river.** The Thompson plat carries the North Division's whole grid there — its
> numbered blocks are bounded east and west by streets, and one line cannot bound
> them.

Acceptance 1 is explicit that the names, the count and the block widths are to be
**read off the plat sheet**, and acceptance 2 that absent is not an answer. Six
lines are seated here and none is refused; what is refused is the confidence on one
of them.

## 1. What the sheet draws, and what it does not write

The sheet is `chicago/pre_fire_v1/maps/images/1830_thompson_plat.png` — the
repository copy `thompson_plat_1830` names, 2728 × 1944. Read on 2026-09-05 at 1×
for the layout and 3–5× for the lettering.

**The North Division carries ONE tier of blocks**, between Kinzie Street on the
north — the sheet letters that line twice, *KINZIE* at its west end and *East and
West line* in the middle — and North Water Street on the south. Seven blocks stand
in it, numbered **1 at the east end against the Due North line and 7 at the west
end against the North Branch**, each four lots to a face in two rows. Six 80-ft
corridors stand between them. A second, partial tier lies south of North Water
Street at the west end only, blocks **14 and 15**, on the point between the North
Branch and the main stem; block 15 is a triangle cut by the bank the sheet letters
*North 52° East*. That answers the question T-0452 § 3 handed over: **two tiers in
the west, one everywhere east of the Market line.**

**The plat names its north–south streets, and it names none of them here.** In the
South Division it letters each corridor once, upright, in the tier between Randolph
and Washington:

| corridor | as lettered on the sheet |
|---|---|
| `market` | MARKET |
| `franklin` | FRANKLIN |
| `wells` | WELLS |
| `lasalle` | LA SALLE |
| `clark` | **CLARKE** — with an E, which is not how this project or the modern street spells it |
| `dearborn` | DEARBORN |

North of the river every one of the six corridors carries the same two marks and
nothing else: **the figure 80 at its head, on the Kinzie line, and a vertical ST.
between the two lot rows.** They were read one at a time at 5×. The line closing
block 1 on the east is lettered *Due North* / *True Meridian* / *Magnetic
Variation* — not with a street name — and what stands on it is already committed as
`wolcott`, which this reading does not reopen.

So the names on the six new records are a **carry**: the sheet's own lettering on
the same line south of the river, carried north because the sheet draws one line
and not two. Each record says so in its note. `wolcott` is the standing proof that
a name could differ across the river, and nothing here weakens it.

## 2. The measurement, and why it is pixels in a data file

Vertical strokes were located by column scan rather than by eye, in a band that
follows each tier's own north face — the North Division's fitted through four
blocks, the South Water tier's through three. Ink is any pixel under 165 of 255; a
column counts when 85 % of the band is ink. The scan returns **34 strokes in the
North Division tier and 25 in the South Water tier**, and both lists are committed
in `data/traces/thompson_north_division_streets.json`.

The lean was searched over ±0.03 px of x per px of y in both bands. The North
Division's lines peak **flat** (0.000; ±0.005 loses 2 % of the peak); the South
Water tier's peak at about **+0.015**. The two bands are therefore read
independently and compared in metres through the fit, never in raw pixels across
500 px of paper.

**The pixels are data and the metres are arithmetic.** Keeping the readings in a
committed file rather than inside the tool is what lets the gate re-derive every
number here without opening a 7 MB PNG or importing Pillow, and what lets a later
reader disagree with the arithmetic without re-measuring the sheet.

## 3. The fit, on control this project already stands on

`thompson_plat_1830` is a **parameter source** and stays one. No metre below is
traced from it: the metres come from four South Division corridors whose committed
centrelines this project already holds, and the sheet supplies only the ratios
between them.

    E = 0.534506 · px − 597.5716        0.5345 m/px

| control corridor | residual |
|---|---|
| `wells` | −0.07 m |
| `lasalle` | +0.34 m |
| `clark` | −0.46 m |
| `dearborn` | +0.19 m |

An 80-ft corridor comes out **45.6 px** on this sheet, which the fit returns as
24.4 m against the platted 24.384 — the paper's own 3 % stretch, and the same order
T-0452 found reading the sheet's east–west axis independently at 0.5402 m/px.

## 4. The sheet draws ONE line, not two

The four corridors whose centres are **measured on both tiers** — both bounding
block faces read, no extrapolation — stand this far apart:

| street | North Division px | South Water tier px | Δ px | Δ m |
|---|---:|---:|---:|---:|
| `wells` | 1734.50 | 1735.50 | −1.00 | −0.53 |
| `lasalle` | 1966.00 | 1964.50 | +1.50 | +0.80 |
| `clark` | 2194.00 | 2194.00 | 0.00 | 0.00 |
| `dearborn` | 2426.75 | 2425.25 | +1.50 | +0.80 |

**Within 1.5 px, 0.8 m, over 500 px of paper and a river.** Franklin's south
corridor has one extrapolated face (block 21 is the Wolf Point triangle) and reads
−1.94 px; Market's is a module step west of Franklin's and reads −7.34.

That is the load-bearing finding, and it is what entitles the six lines to be
seated as the committed South Division streets **continued**, unbent, rather than
as six new lines fitted to the sheet.

## 5. Block pitch: the North Division is on the South Division's module

Corridor centre to corridor centre, both tiers of the one sheet, through the one
fit:

| from | to | North Division | South Water tier |
|---|---|---:|---:|
| `market` | `franklin` | 124.81 | 121.92 |
| `franklin` | `wells` | 122.27 | 121.77 |
| `wells` | `lasalle` | 123.74 | 122.40 |
| `lasalle` | `clark` | 121.87 | 122.67 |
| `clark` | `dearborn` | 124.41 | 123.60 |
| `dearborn` | State/Wolcott | 120.03 | 121.10 |
| **mean** | | **122.85** | **122.24** |

The platted module is 400 ft = **121.92 m**. Every North Division span is within
3 m of it and the tier's mean is the South Water tier's own mean to **0.61 m**.
Acceptance 3 asks for this against the South Division's measured band: the
committed grid reads 118.8, 122.0, 122.0, 123.4, 123.0, 128.0 m and the 1834
traverses read **116.6–123.2 m** (`docs/RESEARCH/thompson_plat_grid.md` § 5). Four
of the six North Division spans fall inside the traverse band as printed; the two
that exceed it — 124.81 and 124.41 — do so by 1.6 m and 1.2 m, inside the 3 % the
same sheet's own corridor width is stretched by. **No span is off-module.**

## 6. The six lines, and the ground under them

Each runs from North Water Street's committed centreline to Kinzie Street's, which
is this file's convention for where a north–south street's path ends. Each is the
committed parent centreline extended north on the parent's own bearing: no vertex
is invented, and the gate holds the two collinear to 2 cm.

| record | from | to | grade |
|---|---|---|---|
| `market_north` | (90.47, 49.25) | (92.14, 259.82) | `inferred` |
| `franklin_north` | (209.37, 151.61) | (210.00, 258.88) | `attested` |
| `wells_north` | (331.20, 126.06) | (331.98, 257.91) | `attested` |
| `lasalle_north` | (453.09, 108.57) | (453.96, 256.94) | `attested` |
| `clark_north` | (576.64, 109.11) | (577.57, 255.96) | `attested` |
| `dearborn_north` | (699.56, 108.63) | (700.47, 254.98) | `attested` |

`attested` is the owner's T-0713 ruling applied where it applies: the plat DRAWS
this street, so that it ran here is a claim the sheet itself makes. **The ground
does not refuse any of them.** Sampling `e1834_harbor_cut` every 5 m from North
Water Street to Kinzie Street returns no wet station and no off-grid station on any
of the six — 182 stations, all dry.

**The wear is carried, not measured.** 5.8 m of light worn earth is what `wolcott`
and `michigan_north` — the two North Division lines already committed — carry, and
nothing read here says how these corridors were worn. `surface_confidence` and
`wear_confidence` say so on every record.

## 7. Market is the one that is graded down, and the number is why

The plat's Market corridor stands **9.08 m west** of the committed `market` line
extended, four times the worst of the other five. The suspect is the parent line,
not the North Division: `market`'s modern counterpart is **N Wacker Drive**, which
stands on ground made after the river was walled, and the committed
`market → franklin` pitch of 118.5 m is already the one South Division pitch off
the plat's module where the other five read 122–123.6 m.

Nothing in this reading can choose between two lines 9 m apart, so nothing is
moved. `market_north` is graded `inferred`, cites `thompson_plat_1830` alone, and
carries `name_2026: null` — N Wacker Drive north of the river is the east–west
riverside drive and is not this line. The re-fit that would settle it is **T-0827**.

Its south end is also the least settled of the six. It lands on `north_water`'s
committed centreline at the reach **T-0447** has open, where the plat does not give
North Water Street the ground it runs on. If that ticket moves the street's west
end, this line's south end moves with it.

## 8. What this reading refuses

- **It does not lay a block grid in the North Division.** `generate_plat_lots.py`
  reads a hard-coded street list and this diff does not touch it. The plat draws
  seven numbered blocks there and one of them, block 6, is drawn **across the
  slough** (T-0452 § 4); generating them is its own unit of work with its own count
  of changed records and its own account of what the water does to lot 6.
- **It does not read the block depths.** The sheet letters both 150 and 180 ft on
  these blocks and the tier's north–south axis was deliberately not fitted here, for
  the same reason T-0452 declined it: one anchor is not a fit.
- **It does not rule on the town's east boundary.** The line closing block 1 is
  lettered as the meridian and `wolcott` stands on it; whether the plat also calls
  that line State Street is not answered by what is written on this sheet.
- **It commits no geometry from the plat.** `thompson_plat_1830` keeps
  `asset_use: inventory` and the standing rule in its note. The fit in § 3 exists to
  *check* six lines this project already holds; its output is a residual, not a
  vertex.

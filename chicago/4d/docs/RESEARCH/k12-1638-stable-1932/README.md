# 1638 Prairie's stable on the alley: the district draft refined onto K12 (T-1932)

`shortall_gregory_house_1638_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`,
T-2334) onto the K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321), 1736's (T-2995) and the north-west
alley's twelve before it (T-1932) did. The draft rules' `skip` now names census row `s20-1638-r1`, so the draft
builder stands no second building in its place, and its phase is `as_standing_1904` (asset
`shortall_gregory_house_1638_prairie_coach_house__as_standing_1904.glb`; the `__draft_1904` master and its web
derivative are retired). Liberty `L-k12-1638-stable-1932`; the draft block liberty `L-draft-prairie-16-18-west-2334`
records the retirement.

**Why this one was still the draft's.** T-1932's release of 2026-11-02 (PR #1606, 1630's shed) wrote that every
building of the north-west alley was off the draft. Sheet 20's footprint trace
(`data/traces/prairie_1904_footprints_s20.json`) lists thirteen detached rear buildings behind the west frontages
1600-1736, and `s20-1638-r1` was the one the draft rules still built: the draft liberty's `Covers:` line named only
this building's draft attributes. With it refined, every one is accounted for:

| census row | lot | now stands as | ticket |
|---|---|---|---|
| s20-1612-r1 | 1612 | K12, mirror image | T-1932 (#1555) |
| s20-1616-r1 | 1616 | K12 | T-1932 (#1535) |
| s20-1620-r1 | 1616/1620 (1620 Law, backcast from 1886) | K12 | T-1932 (#1525) |
| s20-1626-r1, s20-1628-r1 | 1626, 1628 | K12 pair | T-1932 (#1560) |
| s20-1630-r1 | 1630 | K16 frame shed | T-1932 (#1606) |
| **s20-1638-r1** | **1638** | **K12, mirror image** | **T-1932 (this)** |
| s20-1700-r1 | 1700-1706 | K12 | T-1932 (#1570) |
| s20-1712-r1 | 1712 | K12 | T-1932 (#1565) |
| s20-1720-r1, s20-1720-r2 | 1720 | K12 with range | T-1932 (#1573) |
| s20-1726-r1 | 1726 | K12, mirror image (the 1911 range piece not built for 1904) | T-1932 (#1580) |
| s20-1730-r1 | 1730 | K12 with range and lean-to | T-1932 (#1591) |
| s20-1736-r1 | 1736 | K12 | T-2995 |

The lots with no rear building on the sheet (1600, 1604, 1608, 1634, 1636 and the rest) have none to account for;
the census traces none behind them (`census_ids_not_traced` is empty on every west parcel).

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | one **pink (brick)** building **crossed by one X** (the key's stable), lettered **2** (storeys), with `12 12` inside its north wall and again inside its south wall ([crop](sanborn-1911-sheet-20-stable.jpg)); 10.46 m deep from the alley by 11.04 m along it; its north wall on the 1636/1638 lot line, which the sheet runs on east from it; the key's **fire-wall sign** at the alley end of its north wall and of its south wall; one **window mark with two dots** on the alley wall near its middle; one **window mark with one dot** on the north wall near the yard end; a **dashed line** 1.32 m inside the east wall, the length of the building; a **solid dot** inside near the south wall (the key's vertical steam boiler) |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | a **pink (brick)** building **crossed by an X** (the atlas's stable) on the alley behind **lot 1**, house number **1638** and a **40 ft** frontage in the plate's margin, about **10.8 m deep by 11.5 m along the alley**, a frame (yellow) house on the lot's front ([crop](robinson-1886-lot-1.jpg)) |

**The ruling.** The 1904 building is the 1911 sheet's: its outline, storeys, brick, X and window marks. Robinson's
plate draws a crossed brick stable of the same proportions on the same ground. Its size comes from the half-height
edges of its pink fill, which take in the plate's own border lines (0.346 m a pixel); the same profiles return lot
3's stable (1712's) as columns 346.1-370.1 by rows 1455.9-1492.5, its published reading, so the method holds, and
lot 1's is the 1911 building within about one of the plate's pixels each way. The plate also leaves the same gap to
lot 2's stable south of it (rows 1365.2 to about 1370.5, 1.8 m) that the sheet leaves to 1700-1706's (1.9 m). It
stood from before 1886 through 1911, and July 1904 falls between two maps that agree. No picture of it is known, so
it has no image gate.

## The outline, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`), each peak
refined by a parabola through its three highest samples:

| line | where profiled | peak |
|---|---|---|
| alley wall | rows 3575-3640 / 3700-3755 | column 2225.34 / 2225.86 |
| east (yard) wall | rows 3575-3755 | column 2431.53 |
| north wall (the lot line) | columns 2250-2350 (and 2460-2600, east of the building: 3554.90) | row 3554.29 |
| south wall | columns 2245-2330 | row 3771.68 |
| dashed line | rows 3600-3740 | column 2405.48 |

At the sheet's 0.050779 m a pixel: 10.457 m deep by 11.039 m along the alley. The middle of the alley wall, pixel
(2225.60, 3662.99), carried by the sheet's similarity fit, is local E 1334.741, N -3075.265 (UTM 448407.441,
4634320.535). The draft had stood it inside a rectangle fitted to its trace.

The marks, read at 8x: the alley mark's ticks cross the wall line at about rows 3659-3672 and its dots stand inside
the wall at about rows 3674 and 3686 (a dot for each storey), **5.67 m** from the north wall line and **5.37 m** from
the south. The north wall's mark crosses it at about columns 2372-2382 with its one dot inside at (2357.5, 3577.5):
**7.69 m** from the alley line and 2.77 m from the east wall, an opening in one storey. The boiler dot is at about
(2318, 3747), 4.7 m from the alley and 1.3 m from the south wall. The dashed line stands 1.32 m inside the east wall,
from the north-east corner to the south-east one; it divides the inside and shows nothing outside, so it is not
built (as 1700's dashed L is not).

Robinson's stable, by pink-density (red minus green) profiles on the committed plate raster: columns 343.4 to 374.6
back from the alley, rows about 1332.0 to 1365.2 along it, at half the fill's height.

## What K12 builds

- **Mirror image.** The one-dot window is on the north wall, and the kit's party wall takes no opening, so the kit
  is built as 1612's and 1726's are: its party wall at the south end, its open gable to the north.
- **South end:** the kit's party wall, rising 0.45 m above the roof under its coping (the sheet's south fire-wall
  sign). It carries no window, as the sheet marks none; 1700-1706's stable stands 1.9 m south.
- **North end:** the kit's open gable on the 1636/1638 lot line, over 1636's open rear yard, with one stable sash in
  the first storey where the sheet's one-dot mark stands (s 7.19-8.19 from the alley face) and nothing over it, as
  1612's and 1620's one-dot marks are built. The sheet's fire-wall sign at this end is not built: the kit has one
  party wall (in the liberty).
- **Alley wall:** the carriage bay (3.0 m clear) toward the south end with the loft hatch over it; the marked
  stable sash with a loft sash over it where the mark stands (centred 5.04 m from the party wall's inner face); a man
  door with a loft sash over it toward the north end.
- **Yard wall:** a door at the middle between two stable sash and two loft sash; the workyard paved to the house's
  rearmost wall line on the trace, 9.42 m east.
- **Roof:** one gable, ridge along the alley, at 30 degrees over the 10.46 m span, as the deep stables took.
- **Not built:** the boiler's stack (the kit has none and the sheet draws none) and the partition (inside).

`k12_emit` wrote the 103.4 KB master; its web derivative is 28.3 KB. `lay_prairie_1904_street_furniture.py
--check`, run against the baked model, moves no pole.

## In the app

`QA_TARGET=1638 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at five stands (down the alley from
the north and from the south, the north gable from 1636's back yard, the yard face from 1638's yard, and the air) at
1280x800 full and 390x780 light: `browser-validation-after-<viewport>.json` and `after-<viewport>-<stand>.jpg` in
this folder. Both viewports: 0 page errors, 0 failed requests, all three records placed (the stable, its house and
1700-1706's stable south of it), every stand inside its budget.

| viewport | load to ready | JS heap | stand | draw calls | triangles |
|---|---|---|---|---|---|
| desktop, full | 95.0 s | 84.3 MB | alley from the north | 7,548 | 4.64 M |
| | | | alley from the south | 2,388 | 1.86 M |
| | | | north gable | 6,442 | 1.62 M |
| | | | yard face | 2,500 | 0.69 M |
| | | | air | 1,978 | 1.48 M |
| mobile, light | 46.2 s | 111.2 MB | alley from the north | 4,276 | 0.75 M |
| | | | alley from the south | 1,983 | 0.61 M |
| | | | north gable | 1,481 | 0.23 M |
| | | | yard face | 973 | 0.20 M |
| | | | air | 2,090 | 0.63 M |

Load times are this runner's software GL, relative only.

## What is left on T-1932

Every rear building of the north-west alley now stands off the draft. 1620's image-gate items stay open as #1525
left them: the 1874 Land Owner engraving draws a frame building with two hipped roofs where both maps draw the brick
stable, read as its predecessor; closing past them needs `ticket.mjs done --anyway --why` with that reason, or a
picture of the brick stable.

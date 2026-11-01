# 1712 Prairie's stable on the alley: the district draft refined onto K12 (T-1932)

`house_1712_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`, T-2334) onto the
K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321), 1736's (T-2995), 1620's, 1616's, 1612's, 1626's and
1628's (T-1932, [the last of them](../k12-1626-1628-stables-1932/README.md)) did. The draft rules' `skip` now names
census row `s20-1712-r1`, so the draft builder stands no second building in its place, and its phase is
`as_standing_1904` (asset `house_1712_prairie_coach_house__as_standing_1904.glb`; the `__draft_1904` master and its
web derivative are retired). Liberty `L-k12-1712-stable-1932`; the draft block liberty
`L-draft-prairie-16-18-west-2334` records the retirement.

This is the sixth building of T-1932's package (the north-west alley, 1600-1736). The rest of the alley (1630,
1700, 1720, 1726, 1730) stays the draft's. 1630's alley building is a one-storey frame shed on the sheet, which the
two-storey brick kit does not build; 1712's is the kit's own case, so it went first.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | one **pink (brick)** building **crossed by one X** (the key's stable), lettered **2** (storeys), with `12 8` inside its north and south walls ([crop](sanborn-1911-sheet-20-stable.jpg)); 7.64 m deep from the alley by 11.99 m along it; its north wall on the lot line, which the sheet runs on east from it; one **window mark with two dots** at the middle of the alley wall; a **solid dot** inside near the south wall (the key's vertical steam boiler); no fire-wall sign |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | a **pink (brick)** building **crossed by an X** (the atlas's stable) on the alley behind **lot 3**, house number **1712** in the plate's margin, about **8.2 m deep by 12.7 m along the alley** ([crop](robinson-1886-lot-3.jpg)) |

**The ruling.** The 1904 building is the 1911 sheet's: its outline, storeys, brick, X and window mark. Robinson's
plate draws a crossed brick stable of the same proportions on the same ground. Its size comes from the half-height
edges of its pink fill, which take in the plate's own border lines (0.346 m a pixel), so it is the same building
within two of the plate's pixels. It stood from before 1886 through 1911, and July 1904 falls between two maps that
agree. No picture of it is known, so it has no image gate.

## The outline, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`), each peak
refined by a parabola through its three highest samples:

| line | where profiled | peak |
|---|---|---|
| alley wall | rows 4420-4500 / 4540-4610 | column 2224.31 / 2224.23 |
| east (yard) wall | rows 4420-4610 | column 2374.71 |
| north wall (the lot line) | columns 2250-2360 (and 2400-2600, east of the building: 4398.47) | row 4398.64 |
| south wall | columns 2250-2360 | row 4634.69 |

At the sheet's 0.050779 m a pixel: 7.639 m deep by 11.986 m along the alley. The middle of the alley wall, pixel
(2224.27, 4516.66), carried by the sheet's similarity fit, is local E 1335.289, N -3118.610. The draft had fitted a
6.5 by 10 m rectangle.

The window mark: its ticks cross the wall line at about row 4515, and its dots stand inside the wall at about rows
4518 and 4528 (a dot for each storey). That is **5.91 m** from the north wall line and **6.08 m** from the south,
the middle of the wall. The boiler dot is at about (2344, 4621), 6.1 m from the alley and 0.7 m from the south wall.

Robinson's stable, by pink-density (red minus green) profiles on the committed plate raster: rows 1455.9 to 1492.5
along the alley, columns 346.1 to 369.9 back from it, at half the fill's height.

The neighbours: 1700-1706's stable ends about 10.6 m to the north, past the lot line; 1720's buildings begin about
4.6 m to the south.

## What K12 builds

- **North end:** the kit's party wall, on the lot line, rising 0.45 m above the roof under its coping. The sheet
  draws no fire-wall sign; a wall on the lot line is where the kit's party wall belongs (in the liberty).
- **South end:** the kit's open gable, blank, as the sheet marks no window on it.
- **Alley wall:** the carriage bay (3.0 m clear) toward the north end with the loft hatch over it; the marked
  stable sash with a loft sash over it at the middle, where the mark stands; a man door with a loft sash over it
  toward the south end.
- **Yard wall:** a door at the middle between two stable sash and two loft sash; the workyard paved to the frame end
  at the back of the house's rear wing, 17.3 m east.
- **Roof:** one gable, ridge along the alley, at the kit's own 40 degrees, about 3.2 m eave to ridge over the 7.64 m
  span. The deep stables (1616, 1612, 1626, 1628, 1736) took 30 degrees to keep their ridges down over 11-15 m; this
  one is shallow from the alley.
- **Not built:** the boiler's stack (the kit has none and the sheet draws none).

`tools/check_coach_house_kit.py --check`: 9 variants, every piece seated or rooted, no doubled face, every elevation
closed, every opening cut through. The web derivative is 25.9 KB.

`lay_prairie_1904_street_furniture.py`, re-run against the baked model, moves no pole: the alley's poles #04 and
#05 stand 20.3 m north of the stable's party wall and 2.0 m south of its gable, and the wire between them, 0.45 m
inside the alley's edge, clears the alley eave. (Run before the new GLB is tracked, the rule stands the building as
its padded footprint prism instead of its model and steps both poles 1.95 m into the alley; with the model
committed it does not.)

## In the app

`QA_TARGET=1712 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at four stands (down the alley from
the north and from the south, the yard face from 1712's back yard, and the air) at 1280x800 full and 390x780 light:
`browser-validation-after-<viewport>.json` and `after-<viewport>-<stand>.jpg` in this folder.
Both viewports: 0 page errors, 0 failed requests, all three records placed (the stable, its house and 1720's
stable south of it).

| viewport | load to ready | JS heap | stand | draw calls | triangles | in budget |
|---|---|---|---|---|---|---|
| desktop, full | 72.1 s | 83.6 MB | alley from the north | 7,203 | 4.58 M | yes |
| | | | alley from the south | 2,826 | 2.31 M | yes |
| | | | yard face | 6,174 | 1.37 M | yes |
| | | | air | 2,033 | 1.44 M | yes |
| mobile, light | 45.1 s | 109.5 MB | alley from the north | 4,840 | 0.99 M | yes |
| | | | alley from the south | 2,454 | 0.69 M | yes |
| | | | yard face | 1,468 | 0.23 M | yes |
| | | | air | 1,846 | 0.46 M | yes |

Load times are this runner's software GL, relative only.

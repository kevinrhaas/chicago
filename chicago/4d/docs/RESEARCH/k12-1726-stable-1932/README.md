# 1726 Prairie's two-storey building on the alley: the district draft refined onto K12 (T-1932)

`house_1726_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`, T-2334) onto the
K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321), 1736's (T-2995), 1620's, 1616's, 1612's, 1626's,
1628's, 1712's, 1700's and 1720's (T-1932, [the last of them](../k12-1720-stable-range-1932/README.md)) did. The
draft rules' `skip` now names census row `s20-1726-r1`, so the draft builder stands no second building in its place,
and the phase is `as_standing_1904` (asset `house_1726_prairie_coach_house__as_standing_1904.glb`; the `__draft_1904`
master and its web derivative are retired). Liberty `L-k12-1726-stable-1932`; the draft block liberty
`L-draft-prairie-16-18-west-2334` records the retirement.

This is the ninth building of T-1932's package (the north-west alley, 1600-1736). It is built with the kit's
`mirror` option (first used at 1612), and no kit change: the kit, its specimen and the other K12 coach houses are
untouched. The rest of the alley (1630, 1730) stays the draft's.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | a **pink (brick)** building, **uncrossed**, lettered **2** and **GARAGE**, with `12 12` inside its north wall and again inside its south wall ([crop](sanborn-1911-sheet-20-building.jpg)); 11.66 m deep by 14.08 m along the alley, its south wall on the 1726/1730 lot line, where the two-storey piece of 1730's alley building stands against it; the key's **fire-wall sign with two ticks** at the alley end of its north wall and of its south wall; **one window mark with two dots** on its alley wall; a **solid dot** near its south-east corner (the key's vertical steam boiler). North of it on the alley line, the one-storey brick range that runs on from 1720's stable, 4.07 m deep, crossing the 1720/1726 lot line with **no wall drawn on the line** |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | behind **lots 5 and 6** (1726 and 1728 in its margin), a **yellow (frame)** building, uncrossed, about **6.6 m deep by 11.3 m along the alley**, starting about 2.8 m south of the lot 4/5 line ([crop](robinson-1886-lots-5-6.jpg)); no brick on this ground; 1720's brick range ends on the lot 4/5 line |

**The ruling.** The brick building replaced the plate's frame one after 1886. It is first seen in 1911, lettered
GARAGE, and may postdate July 1904: nothing read here dates it. The T-1840 census carries it into 1904 as "a 1904
service building of unread use, not as a garage" (study ruling 11; the kit's `no_1911_use_labels`), so it is built,
as 1736's GARAGE is (T-2995), as the house's stable and coach house, its use RECONSTRUCTED.

**The range piece north of it is not built for 1904.** By 1911 a one-storey brick range runs unbroken from 1720's
stable to this building across the lot line. The plate ends 1720's range on the lot line with a frame building beyond,
and 1720's record builds that range ending there with a closed end wall
([L-k12-1720-stable-range-1932](../k12-1720-stable-range-1932/README.md)). Building the 1911 piece here would stand
a second end wall on a line the sheet draws no wall on, and lay a second flat roof under the end of 1720's. The
joining is left out as later work; a source dating it would put it back, on 1720's range and this record together.

## The outline, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`), each peak
refined by a parabola through its three highest samples:

| line | where profiled | peak |
|---|---|---|
| alley wall | rows 5300-5400 / 5450-5540 | column 2224.94 / 2225.01 |
| east (yard) wall | rows 5290-5540 | column 2454.62 |
| north wall | columns 2330-2430 | row 5277.09 |
| south wall | columns 2240-2420 | row 5554.39 |
| the 1726/1730 lot line, east of the building | columns 2470-2600 | row 5554.80 |
| the 1720/1726 lot line | columns 2330-2600 | row 5189.75 |
| the range piece's east wall | rows 5200-5265 | column 2308.33 |

At the sheet's 0.050779 m a pixel: 11.661 m deep by 14.081 m along the alley. The middle of the alley wall, pixel
(2224.98, 5415.74), carried by the sheet's similarity fit, is local E 1335.974, N -3164.259 (UTM 448408.674,
4634231.541). The window mark's ticks cross the wall line at about rows 5417-5427 with its dots at about 5420 and
5430, **7.51 m** from the north wall line and 6.57 m from the south.

Robinson's lots 5-6, by a yellow-density ((red + green)/2 minus blue) profile on the committed plate raster,
half-height edges: columns 347.4-366.4, rows 1587.0-1619.7, at its 0.346 m a pixel.

## What K12 builds

- **Mirror image.** The party wall at the south end, on the lot line against 1730's building, rising 0.45 m above
  the roof; the open gable at the north end, blank (the sheet marks no window there), facing the 4.3 m of open ground
  to the end of 1720's range. The sheet's fire-wall sign at the north end is not built: the kit has one party wall.
- **Alley wall** (s from the party wall's inner face): the carriage bay (3.0 m clear) toward the south end with the
  loft hatch over it; the mark built as a stable sash with a loft sash over it, centred where it stands (s 6.24); a
  man door with a loft sash over it toward the north end.
- **Yard wall:** a door at the middle between four stable sash, loft sash over the outer two.
- **Roof:** one gable, ridge along the alley, at 30 degrees over the 11.66 m span, as the deep stables took.
- **Workyard:** paved from the yard door to the 1726 house's rear wall line, 10.79 m east.
- **Not built:** the boiler dot (no stack is drawn), the 1911 range piece (above).

`tools/check_coach_house_kit.py --check`: 12 variants, every piece seated or rooted, no doubled face, every elevation
closed, every opening cut through; `--self-test` 0 failures. The master is 109.9 KB and the web derivative 29.3 KB,
1,440 triangles (the draft's blocks were 1,184).

`lay_prairie_1904_street_furniture.py --check`, with the baked model tracked: every pole, crossarm and wire of the
alley clears the building, and no pole moves. (Run before the GLB was tracked, the tool walls it to 15 m, as it does
any model git does not carry, and reports poles #05-#07's wires through it; that reading is not the building's.)

## In the app

`QA_TARGET=1726 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at four stands (down the alley from
the north, past the end of 1720's range, and from the south; the yard face from 1726's back yard; and the air) at
1280x800 full and 390x780 light: `browser-validation-after.json` and `after-<viewport>-<stand>.jpg` in this
folder. Both viewports: 0 page errors, 0 failed requests, all three records placed (the building, the 1726 house and
1720's stable), every stand inside its budget.

| viewport | load to ready | JS heap | stand | draw calls | triangles | in budget |
|---|---|---|---|---|---|---|
| desktop, full | 71.3 s | 83.9 MB | alley from the north | 7,023 | 4.52 M | yes (4.70 M) |
| | | | alley from the south | 3,218 | 2.67 M | yes |
| | | | yard face | 5,492 | 1.72 M | yes |
| | | | air | 2,369 | 2.32 M | yes |
| mobile, light | 36.6 s | 110.5 MB | alley from the north | 4,270 | 0.81 M | yes (1.27 M) |
| | | | alley from the south | 2,335 | 0.60 M | yes |
| | | | yard face | 1,389 | 0.23 M | yes |
| | | | air | 2,048 | 0.51 M | yes |

Load times are this runner's software GL, shared with four other runs, and relative only. The building adds 256
triangles to what the draft drew.

**Seen, not fixed here.** South of the party wall, 1730's building is still the draft's (T-1932's last brick piece
on this alley). The renderer's bedding of a K12 stable at its workyard walk's far end (recorded on
[1700's](../k12-1700-stable-1932/README.md)) applies here too.

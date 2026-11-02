# 1616 Prairie's stable on the alley — the district draft refined onto K12 (T-1932)

`house_1616_prairie_coach_house` keeps its id and moves from the district draft (`prairie_draft`,
T-2334) onto the K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321), 1736's (T-2995) and
1620's (T-1932, [the building against its south wall](../k12-1620-law-stable-1932/README.md)) did.
The draft rules' `skip` now names census row `s20-1616-r1`, so the draft builder stands no second
building in its place, and its phase is `as_standing_1904` (asset
`house_1616_prairie_coach_house__as_standing_1904.glb`; the `__draft_1904` master and its web
derivative are retired). Liberty `L-k12-1616-stable-1932`; the draft block liberty
`L-draft-prairie-16-18-west-2334` records the retirement.

This is the second building of T-1932's package (the north-west alley, 1600-1736). The rest of the
alley (1612, 1626, 1628, 1630, 1700, 1712, 1720, 1726, 1730) stays the draft's.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | a **pink (brick)** building lettered **2** (storeys) and **crossed by an X** (the key's stable), 9.88 m along the alley by 11.02 m deep; walls `12 8`; one window mark on the alley wall with two dots; the key's **fire-wall sign with two ticks** (12 inches above the roof) at the alley end of its north wall and of its south wall; a **solid dot** inside near the south wall (the key's vertical steam boiler); 1612's building with its own wall line 7 px (0.36 m) to the north; 1620's stable sharing its south wall line ([crop](sanborn-1911-sheet-20-stable.jpg)) |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | **nothing**: the rear of lot 11 is white ground between 1620's crossed stable (lots 13-14) and the building behind lot 8 ([1620's crop](../k12-1620-law-stable-1932/robinson-1886-lots-13-14.jpg)) |

**The ruling.** The 1904 building is the 1911 sheet's: its outline, storeys, brick, X, window mark
and fire walls. Robinson's empty lot dates it after 1886. That it stood by July 1904 is the
census's carry-back (`present_as_mapped`), the same claim the district draft already made, and
the record says plainly that a building first seen in 1911 may postdate 1904. No picture of it is
known, so it has no image gate.

## The outline, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`):
the alley wall at column 2229 (rows 2140-2300; 1620's reading found 2226 over rows 2380-2600, the
sheet's own 0.8-degree turn), the yard wall at 2446, the north wall at row 2124.5 (1612's wall at
2117) and the south wall at 2319 (shared with 1620's). At the sheet's 0.050779 m a pixel: 11.019 m
deep, 9.877 m along the alley. The middle of the alley wall, pixel (2229, 2221.75), carried by the
sheet's similarity fit, is local E 1333.873, N -3002.085. The draft had fitted a 9.75 m square.

The window mark spans rows 2225-2257 on the alley line, centred 5.92 m from the north wall line:
a stable sash and a loft sash over it, centred 5.59 m from the party wall's inner face. The
boiler dot is at (2346, 2296): 5.9 m from the alley, 1.2 m from the south wall.

## What K12 builds

- **North end:** the kit's party wall rising above the roof under its coping. The sheet's
  fire-wall sign says 12 inches; the kit's parapet is 0.45 m (in the liberty).
- **South end:** the kit's open gable, no openings (the sheet marks none), standing back to back
  with 1620's party wall. The sheet draws one wall; the two records build two (0.33 m extra,
  inside the fit). The gable shows only east of 1620's building, which is 3.66 m shallower, and
  above 1620's parapet.
- **Alley wall:** carriage bay (3.0 m clear) at the north end with the loft hatch over it; the
  marked stable sash and loft sash; a man door with a loft sash over it toward the south end.
- **Yard wall:** a door at the middle between two stable sash and two loft sash; the workyard
  paved to the house's main rear wall, 12.0 m east.
- **Roof:** a gable with its ridge along the alley at 30 degrees (1736's and 1812's deep-stable
  pitch), about 3.2 m eave to ridge.
- **Not built:** the boiler's stack (the kit has none and the sheet draws none).

`tools/check_coach_house_kit.py --check`: 5 variants, every piece seated or rooted, no doubled
face, every elevation closed, every opening cut through. The web derivative is 26.0 KB.

## In the app

`QA_TARGET=1616 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at four stands (in
the alley 14 m south, from the 1612/1616 rear yard to the north-east, the yard face from 1620's
back yard, and the air) at 1280x800 full and 390x780 light:
`browser-validation-after-<viewport>.json` and `after-<viewport>-<stand>.jpg` in this folder.
Both viewports: 0 page errors, 0 failed requests, 284 of 284 structures standing.

| viewport | load to ready | JS heap | stand | draw calls | triangles | frame (software GL) | in budget |
|---|---|---|---|---|---|---|---|
| desktop, full | 68.8 s | 81.9 MB | alley from the south | 1,395 | 1.23 M | 8.1 s | yes |
| | | | north yard | 5,543 | 1.14 M | 9.5 s | yes |
| | | | yard face | 2,105 | 0.61 M | 6.8 s | yes |
| | | | air | 1,379 | 1.06 M | 5.6 s | yes |
| mobile, light | 44.1 s | 106.7 MB | alley from the south | 978 | 0.44 M | 1.8 s | yes |
| | | | north yard | 1,105 | 0.21 M | 2.0 s | yes |
| | | | yard face | 636 | 0.18 M | 1.4 s | yes |
| | | | air | 1,372 | 0.49 M | 2.2 s | yes |

A first try put the north stand across the alley, inside a building on the Indiana side, looking
down the alley's length; at full detail it read 5,271 draws and 5.71 M triangles against 4.7 M,
the same far-field overrun as 1620's north stand (T-3272), and it was moved into the yard. Frame
times are this runner's software GL, relative only.

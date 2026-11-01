# 1626 and 1628 Prairie's pair of stables on the alley: the district draft refined onto K12 (T-1932)

`house_1626_prairie_coach_house` and `house_1628_prairie_coach_house` keep their ids and move from the district
draft (`prairie_draft`, T-2334) onto the K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321), 1736's
(T-2995), 1620's, 1616's and 1612's (T-1932, [the last of them](../k12-1612-goodman-stable-1932/README.md)) did.
The draft rules' `skip` now names census rows `s20-1626-r1` and `s20-1628-r1`, so the draft builder stands no
second building in their places, and their phase is `as_standing_1904` (assets
`house_1626_prairie_coach_house__as_standing_1904.glb` and `house_1628_prairie_coach_house__as_standing_1904.glb`;
the `__draft_1904` masters and their web derivatives are retired). Liberty `L-k12-1626-1628-stables-1932`; the
draft block liberty `L-draft-prairie-16-18-west-2334` records the retirement.

These are the fourth and fifth buildings of T-1932's package (the north-west alley, 1600-1736). The rest of the
alley (1630, 1700, 1712, 1720, 1726, 1730) stays the draft's.

## What the sources say

| source | date | what it draws on this ground |
|---|---|---|
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | two **pink (brick)** buildings, each **crossed by one X** (the key's stable) and lettered **2** (storeys), joined on **one wall line** with `12 8` written on it ([crop](sanborn-1911-sheet-20-stables.jpg)). 1626's: 7.97 m along the alley by 11.87 m deep, a **window mark with two dots** on the alley wall and another on the north wall, a **solid dot** inside (the key's vertical steam boiler). 1628's: 7.01 m along the alley by 13.94 m deep, a **window mark with two dots** on the alley wall, a solid dot near its south wall, `12 8` inside the south wall. No fire-wall sign on either. |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | the same **pair**: a **pink (brick)** building **crossed** (the atlas's stable) across the rears of lots 16 and 17, in two parts, each about **7.3 m** along the alley, the north one about **11.1 m** deep and the south one about **14.5 m** ([crop](robinson-1886-lots-16-17.jpg)) |

**The ruling.** Both stables are the 1911 sheet's: its outlines, storeys, brick, X and window marks. Robinson's
plate draws the same two buildings at nearly the same sizes (its lines are 0.35 m a pixel), the south one deeper,
as in 1911. So both stood from before 1886 through 1911, and July 1904 falls between two maps that agree. No
picture of either is known, so they have no image gate.

## The outlines, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`), each peak
refined by a parabola through its three highest samples:

| line | where profiled | peak |
|---|---|---|
| alley wall, 1626 | rows 2810-2930 | column 2225.57 |
| alley wall, 1628 | rows 2965-3070 | column 2225.06 |
| east (yard) wall, 1626 | rows 2810-2930 | column 2459.30 |
| east (yard) wall, 1628 | rows 2965-3070 | column 2499.49 |
| 1626's north wall | columns 2260-2440 | row 2790.05 |
| the shared wall | columns 2260-2440 (and 2465-2495, past 1626's yard wall: 2948) | row 2946.95 |
| 1628's south wall | columns 2260-2480 | row 3084.95 |

At the sheet's 0.050779 m a pixel: 1626, 11.869 m deep by 7.967 m along the alley; 1628, 13.935 m by 7.008 m.
The middles of the alley walls, pixels (2225.57, 2868.5) and (2225.06, 3015.95), carried by the sheet's
similarity fit, are local E 1334.166, N -3034.926 and E 1334.246, N -3042.413.

The window marks, read where the key's ticks cross the wall line (the dots stand inside it):

- 1626's alley wall: ticks crossing at about row 2870, dots at rows 2876 and 2884, about **4.06 m** from the north
  wall line;
- 1626's north wall: ticks crossing at about column 2287, dots at columns 2273 and 2286, about **3.12 m** from the
  alley line;
- 1628's alley wall: ticks crossing at about row 3020, dots at rows 3028 and 3037, about **3.71 m** from the shared
  wall line (3.30 m from the south one).

The boiler dots: 1626's at (2349, 2920), 6.3 m from the alley and 1.4 m from the shared wall; 1628's at
(2345, 3074), 6.1 m from the alley and 0.5 m from its south wall.

Robinson's pair, by pink-density profiles on the committed plate raster at its 0.346 m a pixel: rows 1222 to
1264.6 along the alley, the step at row 1243 where the deeper south part begins (columns 374-380); the north
part's columns 342 to 374, the south part's 341 to 383.

## What K12 builds

The kit stands its party wall at one end of the alley run and its open gable at the other.

- **1626, in mirror image** (`mirror`, as at 1612): its north wall carries a window mark and faces the open rear
  of lot 15, so the open gable goes north, with a stable sash and a loft sash over it where the mark stands; the
  party wall goes south, on the wall line it shares with 1628's.
- **1628, as drawn**: its party wall north, back to back with 1626's, and its open gable south, blank, as the
  sheet marks no window on it. The one wall the sheet draws between them is therefore built as two party walls
  back to back, each rising the kit's 0.45 m above its own roof; the sheet draws no fire-wall sign (in the
  liberty).
- **1626's alley wall:** a man door with a loft sash over it toward the south end; the marked stable sash and
  loft sash; the carriage bay at the kit's narrowest (2.7 m clear) toward the north end, the loft hatch over it.
- **1628's alley wall, and why its mark is the carriage bay:** the wall is 7.0 m long and the mark stands at its
  middle. The kit's bay, 2.7 m clear at least, cannot stand beside a 1.0 m sash at the mark with the 0.1 m the
  kit keeps between openings and 0.25 m from either end (the room each side of the sash is 2.6 m and 2.5 m). The
  key's mark says only that both storeys are open there, so the mark is read as the bay with the loft hatch over
  it, centred where the mark stands; a man door with a loft sash toward the north end and a stable sash with a
  loft sash toward the south are the kit's. A picture showing a sash at the mark would move the bay (the
  liberty's "How to resolve").
- **Yard walls:** a door at the middle between two stable sash and two loft sash; 1626's workyard paved to the
  house's rear porch, 5.9 m east, 1628's to its main rear wall, 15.2 m east.
- **Roofs:** one gable each, ridge along the alley at 30 degrees (the deep stables' pitch at 1616, 1612 and
  1736): about 3.4 m eave to ridge over 1626's 11.87 m span and 4.0 m over 1628's 13.94 m.
- **Not built:** the boiler dots' stacks (the kit has none and the sheet draws none).

`tools/check_coach_house_kit.py --check`: 8 variants, every piece seated or rooted, no doubled face, every
elevation closed, every opening cut through. The web derivatives are 29.4 KB (1626) and 25.8 KB (1628).

`lay_prairie_1904_street_furniture.py`, re-run against the two baked models, moves no pole: the alley's poles
#02 and #03 stand 6.5 m north of 1626's gable and 12.2 m south of 1628's, and the wire between them clears both eaves.

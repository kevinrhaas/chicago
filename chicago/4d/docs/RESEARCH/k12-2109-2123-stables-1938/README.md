# 2109's and 2123's stables on the east alley, 21st-22nd — the district draft refined onto K12 (T-1938)

`roloson_house_2109_prairie_coach_house` and `house_2123_prairie_coach_house` keep their ids and move from the
district draft (`prairie_draft`, T-2352) onto the K12 coach-house kit (`k12_coach_house`), facing the alley on
their east (`alley_side: east`), as 2001's, 2009's (#2367), 2011's and 2017's (#2376), 2027's (#2345) and 2031's
and 2033's (#2379) did. The draft rules' `skip` now names census rows `s35-2109-rear` and `s35-2123-rear`, so
the draft builder stands no second building in their place, and their phase is `as_standing_1904` (the
`__draft_1904` masters and web derivatives are retired). Liberties `L-k12-2109-stable-1938` and
`L-k12-2123-stable-1938`; the draft block liberty `L-draft-prairie-20-22-east-2352` records the retirement.

These are the eighth and ninth of T-1938's alley buildings to leave the draft, and the first south of 21st
Street. Still the draft's: 2013 (Reid, the image gate), 2021 (its tin-clad upper storey and one-storey south
end), 2035 (brick and frame), 2101 (a two-storey block on 21st Street with a one-storey range south of it,
which the kit has no fitting for along the alley), 2115 (brick, the largest on the alley) and 2125 (frame).

## What the source says

Sanborn 1911, vol. 3 sheet 35 (`sanborn_1911_chicago_v3_sheet_35`), the committed copy at 0.185854 m a pixel
([crop](sanborn-1911-sheet-35-stables.jpg), columns 1000-1200, rows 1105-1375). Both buildings are pink
(brick), lettered **GARAGE** and marked '2'. GARAGE is the 1911 sheet's word; the census reconstructs the 1904
use as a stable and coach house, and that is what is built. No picture of this alley is known, so neither
building has an image gate.

Median darkness profiles, peaks refined by a parabola through the three highest samples. The method
reproduces #2379's 2033 readings exactly (alley 1170.73, west wall 1091.59).

| line | 2109 | 2123 |
|---|---|---|
| alley line | column 1171.94 (rows 1130-1190) | column 1172.93 (rows 1310-1355) |
| yard (west) wall | column 1116.13 | column 1098.99 |
| north wall | row 1118.64, on the 2101/2109 lot line (1119.07); 2101's one-storey range against it; fire-wall ticks on the alley line | row 1301.26, on the 2115/2123 lot line (1300.0, within a pixel and a half); 2115's garage 0.43 m north (row 1298.92); fire-wall ticks on the alley line |
| south wall | row 1200.53, on the 2109/2115 lot line (1201.17); 2115's garage against it | row 1364.02, free, 0.56 m inside the 2123/2125 lot line (1367.01) |
| size | 10.373 m deep, 15.220 m along the alley | 13.742 m deep, 11.664 m along the alley |
| storeys | '2' | '2' |
| marks | a window mark on the alley wall (rows 1165-1175), 5.67 m from the south wall; a second on the north wall (not built: it looks over 2101's one-storey roof, and a party wall takes no opening); a dashed line about 1.3 m inside the yard wall, its ends turned toward it (column 1123.13; not read, not built); a small open circle inside the south-east corner (not built) | a window mark on the alley wall (rows 1329-1339), 6.08 m from the north wall; another on the south wall (columns 1137-1147), 5.80 m back from the alley line; a small cross inside the south-east corner (not built) |
| house behind | its brick rear block 19.21 m west (column 1012.76, rows 1141-1182) | its two-storey brick rear range 5.97 m west (column 1066.89, rows 1320-1355) |

## What K12 builds

**2109**: party walls at both ends (`east_end: party`), as 2031's and 2033's; laid out for its 15.2 m as 2017's
stable of the same length: on the alley a man door, the mark as a stable sash, a carriage bay 3.0 m clear under
the hatch and hoist and a second carriage bay toward the north end, each with loft sash; on the yard three stable
sash and a door, each with loft sash. 40-degree roof, as 2017's 10.63 m deep stable takes.

**2123**: the kit in mirror image (`mirror`), as 2017's, so its party wall stands on the north lot line where the
fire-wall sign is and the open gable is the south end, which the sheet leaves free. On the alley a carriage bay
under the hatch and hoist toward the north, the mark as a stable sash, and a man door; on the south gable its mark
as a stable sash; on the yard two stable sash and a door; each with loft sash. 30-degree roof, as the 14.7 m deep
stables 2031 and 2033 take.

Each has the kit's workyard (a 2.4 m apron and a walk to the house's rear wall line), the yard door set where the
walk meets the house's rear block or range.

`tools/check_coach_house_kit.py --check`: 32 variants, every piece seated or rooted, no doubled face, every
elevation closed, every opening cut through. `validate.py --stale`: 0 errors.

## In the app

`QA_TARGET=2109 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at five stands (down the alley
from the north and from the south, each yard, and the air) at 1280x800 full and 390x780 light. Both viewports:
0 page errors, 0 failed requests, all four records placed, every stand inside the detail budget
(`browser-validation-after-<viewport>.json`, `after-<viewport>-<stand>.jpg`).

| viewport | load to ready | JS heap | stand | draw calls | triangles |
|---|---|---|---|---|---|
| desktop, full | 58.4 s | 123.9 MB | alley from north | 1,025 | 1.68 M |
| | | | alley from south | 3,021 | 4.00 M |
| | | | 2109's yard | 679 | 0.82 M |
| | | | 2123's yard | 1,820 | 2.42 M |
| | | | air | 1,752 | 2.34 M |
| mobile, light | 41.0 s | 142.7 MB | alley from north | 958 | 0.35 M |
| | | | alley from south | 2,525 | 0.66 M |
| | | | 2109's yard | 473 | 0.28 M |
| | | | 2123's yard | 810 | 0.30 M |
| | | | air | 2,621 | 1.00 M |

Times are this runner's software GL, relative only. The first framing of the air stand, 50 m out at
(1496, -3703, 36) looking at (1464, -3663), took in the whole 21st-22nd block and read 1.75 M triangles on the
phone, over the 1.27 M light budget. That is the stand, not these two buildings, and the stand was moved in to
(1492, -3697, 36) looking at (1466, -3675), the distance #2379's air stand stood at (0.99 M there, 1.00 M here).
The 1.75 M reading is not a regression this PR makes, but it is a measurement of what the phone draws over
that block from the air, and is written down so it is not lost.

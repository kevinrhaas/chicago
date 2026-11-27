# 2031's and 2033's stables on the east alley, 20th-21st — the district draft refined onto K12 (T-1938)

`tolman_house_2031_prairie_coach_house` and `otis_house_2033_prairie_coach_house` keep their ids and move
from the district draft (`prairie_draft`, T-2352) onto the K12 coach-house kit (`k12_coach_house`), facing the
alley on their east (`alley_side: east`), as 2001's, 2009's (#2367), 2011's and 2017's (#2376) and 2027's
(#2345) did. The draft rules' `skip` now names census rows `s35-2031-rear` and `s35-2033-rear`, so the draft
builder stands no second building in their place, and their phase is `as_standing_1904` (the `__draft_1904`
masters and web derivatives are retired). Liberties `L-k12-2031-stable-1938` and `L-k12-2033-stable-1938`; the
draft block liberty `L-draft-prairie-20-22-east-2352` records the retirement.

These are the sixth and seventh of T-1938's alley buildings to leave the draft. Still the draft's:
2013 (Reid, the image gate), 2021 (its tin-clad upper storey and one-storey south end), 2035, 2101, 2109,
2115, 2123, 2125.

## What the source says

Sanborn 1911, vol. 3 sheet 35 (`sanborn_1911_chicago_v3_sheet_35`), the committed copy at 0.185854 m
a pixel ([crop](sanborn-1911-sheet-35-stables.jpg), columns 1000-1190, rows 750-860). Both buildings are
pink (brick), lettered **GARAGE** and marked '2'. GARAGE is the 1911 sheet's word; the census reconstructs
the 1904 use as a stable and coach house, and that is what is built. No picture of this alley is known, so
neither building has an image gate.

Median darkness profiles, peaks refined by a parabola through the three highest samples (the method
reproduces #2376's 2017 readings to the hundredth of a pixel: alley 1170.96, west wall 1113.75, north wall
516.27):

| line | 2031 | 2033 |
|---|---|---|
| alley line | column 1170.88 (rows 767-800) | column 1170.73 (rows 810-842) |
| yard (west) wall | column 1092.04 | column 1091.59 |
| north wall | row 762.77, on the 2027/2031 lot line (762.54 west of the building); 2027's barn's south wall 0.50 m north (row 760.08) | row 805.07, shared with 2031's, on their lot line (805.01) |
| south wall | row 805.07, shared with 2033's | row 846.79, on the 2033/2035 lot line (846.97); 2035's building against it |
| size | 14.654 m deep, 7.862 m along the alley | 14.710 m deep, 7.754 m along the alley |
| storeys | '2' | '2' |
| marks | fire-wall ticks on the alley line at both ends; a window mark (strokes over rows 783-792), 3.27 m from the south wall; a solid dot inside the south-east corner (not built) | fire-wall ticks at both ends; a window mark (rows 824-834), 3.31 m from the south wall; a solid dot inside the south-east corner (not built) |
| house behind | its two-storey brick rear range 14.50 m west (column 1014.03), a frame porch on it | its two-storey brick rear range 14.43 m west (column 1013.93) |

## What K12 builds

Both as 2011's is: party walls at both ends (`east_end: party`), on the alley a man door, the mark as a
stable sash and a carriage bay 3.0 m clear toward the north end under the hatch and hoist, each with loft
sash; on the yard a door and a stable sash with loft sash over them. 30-degree roof, as 2011's 14.64 m deep
stable takes. Each has the kit's workyard (a 2.4 m apron and a walk to the range's rear wall line), the yard
door set where the walk meets the range: 2031's toward the porch on its range (yard door s 4.75-5.70 from
the north party wall), 2033's at the middle of its range (s 1.70-2.65).

`tools/check_coach_house_kit.py --check`: 30 variants, every piece seated or rooted, no doubled face, every
elevation closed, every opening cut through. `validate.py --stale`: 0 errors, 0 stale assets.

## In the app

`QA_TARGET=2031 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at five stands (down the
alley from the north and from the south, each yard face from its back yard, and the air) at 1280x800 full
and 390x780 light. Both viewports: 0 page errors, 0 failed requests, all four records placed, every stand
inside the detail budget (`browser-validation-after-<viewport>.json`, `after-<viewport>-<stand>.jpg`).

| viewport | load to ready | JS heap | stand | draw calls | triangles |
|---|---|---|---|---|---|
| desktop, full | 86.6 s | 115.6 MB | alley from north | 1,565 | 1.92 M |
| | | | alley from south | 2,664 | 3.22 M |
| | | | 2031's yard | 897 | 0.98 M |
| | | | 2033's yard | 843 | 0.91 M |
| | | | air | 2,020 | 2.54 M |
| mobile, light | 58.7 s | 140.5 MB | alley from north | 1,003 | 0.34 M |
| | | | alley from south | 2,292 | 0.66 M |
| | | | 2031's yard | 461 | 0.27 M |
| | | | 2033's yard | 501 | 0.30 M |
| | | | air | 2,893 | 0.99 M |

Times are this runner's software GL, relative only. The back-yards layer, re-laid with the stables tracked,
keeps all 134 lots: 2031's lot gains two walks from the back door to the stable (`prairie_2031:coach_walk:0/1`)
where an untracked run had laid one to the alley through the building; 2033's keeps its rear terrace, the
kit's own walk reaching its range.

# 2011's and 2017's stables on the east alley, 20th-21st — the district draft refined onto K12 (T-1938)

`house_2011_prairie_coach_house` and `house_2017_prairie_coach_house` keep their ids and move from the
district draft (`prairie_draft`, T-2352) onto the K12 coach-house kit (`k12_coach_house`), facing the
alley on their east (`alley_side: east`), as 2001's, 2009's (#2367) and 2027's (#2345) did. The draft
rules' `skip` now names census rows `s35-2011-rear` and `s35-2017-rear`, so the draft builder stands no
second building in their place, and their phase is `as_standing_1904` (the `__draft_1904` masters and
web derivatives are retired). Liberties `L-k12-2011-stable-1938` and `L-k12-2017-stable-1938`; the draft
block liberty `L-draft-prairie-20-22-east-2352` records the retirement.

These are the fourth and fifth of T-1938's alley buildings to leave the draft. Still the draft's:
2013 (Reid, the image gate), 2021, 2031, 2033, 2035, 2101, 2109, 2115, 2123, 2125.

## What the source says

Sanborn 1911, vol. 3 sheet 35 (`sanborn_1911_chicago_v3_sheet_35`), the committed copy at 0.185854 m
a pixel ([crop](sanborn-1911-sheet-35-stables.jpg), columns 1040-1190, rows 420-610). Both buildings
are pink (brick) and lettered **GARAGE**. GARAGE is the 1911 sheet's word; the census reconstructs the
1904 use as a stable and coach house, and that is what is built. No picture of this alley is known, so
neither building has an image gate.

Median darkness profiles, peaks refined by a parabola through the three highest samples (the method
reproduces #2367's 2009 readings to the hundredth of a pixel: alley 1170.96, west wall 1096.21, north
wall 386.06, and its position, local E 1469.787, N -3507.423):

| line | 2011 | 2017 |
|---|---|---|
| alley line | column 1170.89 (rows 440-472) | column 1170.96 (rows 520-595) |
| yard (west) wall | column 1092.12 | column 1113.75 |
| north wall | row 433.95, on the 2009/2011 lot line (433.87 west of the building); 2009's stable's south wall 0.44 m north | row 516.27, on the 2013/2017 lot line (516.15); 2013's stable 0.62 m north (row 512.9) |
| south wall | row 476.13, on the 2011/2013 lot line (476.19); 2013's stable 0.54 m south (row 479.01) | row 598.21, on the 2017/2021 lot line (598.11); 2021's building 0.56 m south (row 601) |
| size | 14.640 m deep, 7.839 m along the alley | 10.633 m deep, 15.229 m along the alley |
| storeys | one figure, worn: 1 or 2; the census reads 2 | '2' |
| marks | fire-wall ticks on the alley line at both ends; a window mark at row ~459.5, 3.09 m from the south wall; a crossed (stable) corner behind a dashed partition, 3.71 m along the alley by 6.30 m deep; an open circle inside the south-east corner (not built) | fire-wall ticks at the north end; a window mark at row ~556, 7.38 m from the north wall; a solid dot inside the south-east corner (not built) |
| house behind | its two-storey range 3.43 m west (column 1073.67) | its rear wall 10.56 m west (column 1056.93) |

## What K12 builds

- **2011**: both ends are party walls (`east_end: party`), as 1900's is between its neighbours: the
  building stands on both lot lines with a fire-wall sign at each. On the alley a man door, the mark as a
  stable sash and a carriage bay toward the north end under the hatch and hoist, each with loft sash; on
  the yard a door and a sash. 30-degree roof, as 2009's. The crossed corner and its partition are the
  1911 building's inside: the kit builds no interior, and the census backcasts the whole building as the
  1904 stable, so the carriage bay is laid out for the whole. Its storeys are `inferred` (the census's
  reading), not `attested`, because the figure is worn on this copy.
- **2017**: built in mirror image (`mirror`), as 1612's is, so the party wall stands on the north lot
  line at the fire-wall sign and the open gable faces 2021's building across 0.56 m, with no opening. On
  the alley, laid out for its 15.2 m as 1900's 15.4 m stable is: two carriage bays (the hatch and hoist
  over the northern), a man door, the mark as a stable sash, and a sash toward the south end; on the yard
  three sash and a door, with the kit's workyard (a 2.4 m apron and a walk to the house's rear wall line).
  40-degree roof, the kit's own, as 1900's 9.2 m deep stable takes.

`tools/check_coach_house_kit.py --check`: 28 variants, every piece seated or rooted, no doubled face,
every elevation closed, every opening cut through. `validate.py --stale`: 0 errors, 0 stale assets.

## In the app

`QA_TARGET=2011 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at five stands (down the
alley from the north and from the south, 2017's yard face from its workyard, 2011's yard face from the
strip behind its house's range, and the air) at 1280x800 full and 390x780 light. Both viewports: 0 page
errors, 0 failed requests, all four records placed, every stand inside the detail budget
(`browser-validation-after-<viewport>.json`, `after-<viewport>-<stand>.jpg`).

| viewport | load to ready | JS heap | stand | draw calls | triangles |
|---|---|---|---|---|---|
| desktop, full | 71.7 s | 121.1 MB | alley from the north | 1,935 | 2.07 M |
| | | | alley from the south | 3,002 | 3.81 M |
| | | | 2017's yard | 971 | 0.87 M |
| | | | 2011's yard | 1,077 | 1.11 M |
| | | | air | 2,105 | 2.59 M |
| mobile, light | 49.1 s | 147.1 MB | alley from the north | 1,247 | 0.35 M |
| | | | alley from the south | 2,397 | 0.64 M |
| | | | 2017's yard | 533 | 0.25 M |
| | | | 2011's yard | 608 | 0.26 M |
| | | | air | 2,595 | 0.95 M |

Times are this runner's software GL, relative only. The back-yards layer, re-laid with the stables
tracked, keeps all 134 lots and gains one surface: 2017's walk from the back door now runs to the kit's
workyard paving (`prairie_2017:coach_walk:1`).

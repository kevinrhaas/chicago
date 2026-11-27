# 2001's and 2009's stables on the east alley, 20th-21st — the district draft refined onto K12 (T-1938)

`house_2001_prairie_coach_house` and `mayer_house_2009_prairie_coach_house` keep their ids and move
from the district draft (`prairie_draft`, T-2352) onto the K12 coach-house kit (`k12_coach_house`),
facing the alley on their east (`alley_side: east`), as 2027's barn did (#2345). The draft rules'
`skip` now names census rows `s35-2001-rear` and `s35-2009-rear`, so the draft builder stands no
second building in their place, and their phase is `as_standing_1904` (the `__draft_1904` masters
and web derivatives are retired). Liberties `L-k12-2001-stable-1938` and `L-k12-2009-stable-1938`;
the draft block liberty `L-draft-prairie-20-22-east-2352` records the retirement.

These are the second and third of T-1938's alley buildings to leave the draft. Still the draft's:
2011, 2013 (Reid, the image gate), 2017, 2021, 2031, 2033, 2035, 2101, 2109, 2115, 2123, 2125.

## What the source says

Sanborn 1911, vol. 3 sheet 35 (`sanborn_1911_chicago_v3_sheet_35`), the committed copy at 0.185854 m
a pixel ([crop](sanborn-1911-sheet-35-stables.jpg), columns 1040-1190, rows 255-445). Both buildings
are pink (brick), lettered **2** (storeys) and **GARAGE**, uncrossed. GARAGE is the 1911 sheet's word;
the census's own note reconstructs the 1904 use as a stable and coach house, and that is what is built.
No picture of this alley is known, so neither building has an image gate.

Median darkness profiles, peaks refined by a parabola through the three highest samples:

| line | 2001 | 2009 |
|---|---|---|
| alley line | column 1171.89 (rows 280-300) | column 1170.96 (rows 395-425), the alley wall drawn on it |
| alley wall | column 1166.55, **0.99 m inside the alley line** | on the line |
| yard (west) wall | column 1080.07 | column 1096.21 |
| north wall | row 275.17 at the alley end; row 269.86, **the 20th Street line**, west of a step at column 1121.1 | row 386.06; a second line at 383.85 is the lot line, lettered 17" WALL 16' HIGH |
| south wall | row 311.00, the 2001/2003 lot line | row 431.62; 2011's building's north wall at 433.98 |
| size | 16.073 m deep, 6.659 m along the alley at the alley end | 13.893 m deep, 8.468 m along the alley |
| marks | a solid dot inside the north-east corner (not built) | a window mark on the alley wall at row 411, 3.83 m from the south wall; an open circle inside the south-east corner (not built) |

## What K12 builds

- **2001**: built as a rectangle at its alley end's width the whole depth. The west 7.63 m stands
  0.99 m wider on the sheet, out to the 20th Street line; that strip is not built (the kit takes no
  stepped wall). Party wall south on the lot line; open gable north to 20th Street with three
  stable sash and two loft sash (the building's one face to a public street); a carriage bay with
  the hatch and hoist and a man door on the alley; two sash and a door on the yard, the workyard
  paved 11.16 m to the house's rear wall (column 1020). 30-degree roof, as 1736's and 1709's deep
  stables have.
- **2009**: party wall south, back to back with 2011's building; open gable north over 2005's open
  back lot, no openings; on the alley a man door, the mark as a stable sash, and a carriage bay
  toward the north end with the hatch and hoist. The house's one-storey brick rear range (the house
  record's `rear_range`) stands against the yard wall's southern 5.6 m, so the yard wall has only a
  door in the 2.87 m left open, and no workyard. 30-degree roof, as 1612's.

`tools/check_coach_house_kit.py --check`: 26 variants, every piece seated or rooted, no doubled face,
every elevation closed, every opening cut through.

## In the app

`QA_TARGET=2001 node tools/qa_k12_t1932.mjs` reads the published `/1904/` app at five stands (down
the alley from 20th Street and from the south, 2001's gable from 20th Street, 2009's north gable and
yard door from 2005's back lot, and the air) at 1280x800 full and 390x780 light. Both viewports:
0 page errors, 0 failed requests, all four records placed, every stand inside the detail budget
(`browser-validation-after.json`, `after-<viewport>-<stand>.jpg`).

| viewport | load to ready | JS heap | stand | draw calls | triangles |
|---|---|---|---|---|---|
| desktop, full | 75.9 s | 128.6 MB | alley from the north | 2,283 | 2.46 M |
| | | | alley from the south | 3,137 | 4.30 M |
| | | | 20th Street | 2,025 | 2.38 M |
| | | | 2005's back lot | 1,050 | 1.01 M |
| | | | air | 1,785 | 2.33 M |
| mobile, light | 41.7 s | 135.8 MB | alley from the north | 1,589 | 0.39 M |
| | | | alley from the south | 2,511 | 0.77 M |
| | | | 20th Street | 1,335 | 0.37 M |
| | | | 2005's back lot | 532 | 0.28 M |
| | | | air | 3,075 | 1.05 M |

A first air stand, 46 m up and 50 m south-east, read 4,140 draws at mobile light, over budget on the
far field (as 1620's first north stand did, T-3272); it was moved to 36 m, 31 m out. Times are this
runner's software GL, relative only.

# 1620 Prairie's stable on the alley — the district draft refined onto K12 (T-1932)

`law_house_1620_prairie_coach_house` keeps its id and moves from the district draft
(`prairie_draft`, T-2334) onto the K12 coach-house kit (`k12_coach_house`), as 1812's (T-2321)
and 1736's (T-2995) did. The draft rules' `skip` now names census row `s20-1620-r1`, so the
draft builder stands no second building in its place, and its phase is `as_standing_1904`
(asset `law_house_1620_prairie_coach_house__as_standing_1904.glb`; the `__draft_1904` master and
its web derivative are retired). Liberty `L-k12-1620-stable-1932`; the draft block liberty
`L-draft-prairie-16-18-west-2334` records the retirement.

This is one building of T-1932's package (the north-west alley, 1600-1736): the ticket's
image gate names this building, so it went first. The rest of the alley stays the draft's.

## What the three sources say

| source | date | what it draws on this ground |
|---|---|---|
| Land Owner, "Homes of Chicago", Robert Law (`land_owner_1874_05_homes_of_chicago_1620_law`) | May 1874 | a building in **board-and-batten** behind the house, under two hipped roofs with two chimneys; its two-storey block ends short of the lot's north line, a lower board structure beyond it ([crop](landowner-1874-rear-building.jpg)) |
| Robinson's atlas, plate 10 (`robinson_1886_chicago_plate_10`) | 1886 | a **pink (brick)** building **crossed by an X** (the atlas's stable) across lots 13 and 14 on the alley, about 8.6 by 13.8 m, with a small un-crossed ell about 4.0 by 4.6 m toward the house at its north end ([crop](robinson-1886-lots-13-14.jpg)) |
| Sanborn 1911, vol. 3 sheet 20 (`sanborn_1911_chicago_v3_sheet_20`) | 1911 | a **pink (brick)** building lettered **2** (storeys), no X, 7.36 by 16.30 m along the alley, walls `12 8` on its north and south walls, a window mark with two dots on the alley wall and one with one dot on the south wall, 1616's crossed building against its north wall; the house in front is gone ([crop](sanborn-1911-sheet-20-stable.jpg)) |

**The ruling.** Both maps draw brick where the engraving draws boards. The engraving's battens
and rail are drawn the way the house's brick north wall beside it is not, so it is read as a
frame stable that the brick one replaced between May 1874 and 1886. The 1904 building is the
maps': the 1911 outline, storeys, brick and window marks, and the 1886 plate's use (a stable;
the 1911 sheet drops the X, after the house had gone). Robinson's ell is not on the 1911 sheet
and is left out for 1904, the nearer map governing. If the engraver drew brick as boards, the
engraving would be this building's picture after all, and its hipped roofs, chimneys and 8.8 m
eaves would want building: that is the liberty's "How to resolve".

## The outline, read off sheet 20

Median darkness profiles on the committed raster
(`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_20.jpg`):
the alley wall at column 2226 (rows 2380-2600), the yard wall at 2371, the north wall at row 2319
(shared with 1616's crossed building) and the south wall at 2640 (columns 2245-2355). At the
sheet's 0.050779 m a pixel: 7.363 m deep, 16.30 m along the alley. The middle of the alley wall,
pixel (2226, 2479.5), carried by the sheet's similarity fit, is local E 1333.907, N -3015.175.
The draft had fitted a 7.0 by 15.25 m rectangle inside the colour trace, its corner origin 7.4 m
further south.

The window marks, measured from the wall lines: on the alley wall, centred about 9.19 m from the
north wall line (a dot for each storey: a stable sash and a loft sash over it, centred 8.86 m
from the party wall's inner face); on the south wall, about 3.55 m from the alley line, one dot
(one stable sash, nothing over it). Every other opening, the roof (the kit's 40-degree gable,
ridge along the alley), the storey heights and the workyard are the kit's (see the record's
`coach_house` note and the liberty).

## The image gate

`data/reference_views/law_house_1620_prairie_coach_house/landowner_1874_from_northeast.json` is
the house's own solved camera on the engraving (T-2370, re-solved by T-2437), carried into this
record's frame through the two 1904 sidecar placements, with the house rendered beside it
(`also_render`). Through it the build and the engraving's building stand on the same ground:
both begin where the house's rear corner hides them, at x 848 px.

- Before (the draft's 7 x 15.25 m gable block): [before-draft-side-by-side.jpg](before-draft-side-by-side.jpg)
- After: [../photo-match/law_house_1620_prairie_coach_house/landowner_1874_from_northeast-side-by-side.jpg](../photo-match/law_house_1620_prairie_coach_house/landowner_1874_from_northeast-side-by-side.jpg)

The match record says **differs**, with five items open (walls' material, the roof and chimneys,
the eave height, the block's length, the yard-face openings), each the 1874 frame building
against the 1904 brick one. They are left open rather than marked away: a ticket naming this
building closes past them only with `ticket.mjs done --anyway --why` and the ruling above, or
when a picture of the brick stable is found.

## In the app

`tools/qa_k12_t1932.mjs` reads the published `/1904/` app at four stands (down the alley from the
south and from the north, the yard face from the Law house's back yard, and the air) at 1280x800
full and 390x780 light: `browser-validation-after-<viewport>.json` and
`after-<viewport>-<stand>.jpg` in this folder. Both viewports: 0 page errors, 0 failed requests,
284 of 284 structures standing.

| viewport | load to ready | JS heap | stand | draw calls | triangles | frame (software GL) | in budget |
|---|---|---|---|---|---|---|---|
| desktop, full | 92.6 s | 81.8 MB | alley from the south | 1,673 | 1.35 M | 7.6 s | yes |
| | | | alley from the north | 8,049 | 6.06 M | 14.4 s | **no** (7,800 / 4.7 M) |
| | | | yard face | 4,177 | 0.81 M | 8.1 s | yes |
| | | | air | 1,492 | 1.20 M | 6.1 s | yes |
| mobile, light | 44.7 s | 106.6 MB | alley from the south | 1,228 | 0.50 M | 1.8 s | yes |
| | | | alley from the north | 4,867 | 0.94 M | 2.7 s | yes |
| | | | yard face | 1,003 | 0.23 M | 1.6 s | yes |
| | | | air | 1,690 | 0.59 M | 2.3 s | yes |

The stable itself is one mesh of 1,632 triangles (the draft's was 920; web derivative 29.0 KB).
The desktop stand down the alley from 1616's rear looks the alley's whole length south toward
18th Street at full detail, and is over the full tier's budget by 249 draw calls and 1.36 M
triangles: a spot reading at a stand this ticket chose, which the building's +712 triangles cannot
account for. It is not a stand any gate measures, and it is filed as a performance follow-up
rather than moved to a kinder spot. Frame times are this runner's software GL, relative only.

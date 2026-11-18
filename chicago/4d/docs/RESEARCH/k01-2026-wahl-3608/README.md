# T-3608 — 2026 Prairie, the Louis Wahl house, on K01 to its 1874 Land Owner engraving

Piece 2 of T-1910 (2018 Prairie is piece 1, T-3607). The district draft (T-2351) is refined in place,
under its own id, onto the K01 frontage assembly (`generators/k01_emit.py`); liberty
`L-k01-2026-wahl-3608`. The image gate's one picture is The Land Owner's engraving of May 1874
(`land_owner_1874_05_homes_of_chicago_2026_wahl`; library `a20-chicagology-2026-wahl-landowner-1874`),
its camera `data/reference_views/house_2026_prairie/landowner_1874.json`, its match record beside it
(`matches`, nothing open) and the side-by-side in `docs/RESEARCH/photo-match/house_2026_prairie/`.

## The plan: sheet 35 at full size

Read off `chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`
through the sheet's committed fit (0.186 m a pixel), with the T-1842 census row s35-2026-front ('3B
dwelling (D), stone front and brick rear divided on the diagonal'). The origin is the main body's
south-west (rear, south) corner at raster column 586, row 685; rotation -0.373 degrees lays u on the
raster's columns, along which the sheet draws the side walls.

| reading | raster (col, row) | plan (u, v) m |
|---|---|---|
| rear wall / front wall (dashed outline) | 586 / 707 | u 0 / 22.49 |
| south wall / north wall (dashed outline) | 685 / 631 | v 0 / 10.04 |
| north projection: the tower | to col 713, rows 627-644 | 1.1 m out; built v 6.74-9.74 |
| south projection | to col 713, rows 670-689 | 1.1 m out; built as a canted bay s 0.3-3.7 |
| south flank bump: the flank bay | cols 655-674, to row 691 | u 12.8-16.4, 1.1 m out |
| stone / brick on the diagonal | north wall col 660, south wall col 632 | 8.7 m / 14.0 m back from the front |
| one-storey brick rear range (p11) | cols 575-586, rows 627-685 | u -2.04-0 |

The sheet's solid outer line stands about 1.7 m outside the dashed one on both flanks and the front,
coloured as the house, with figures printed in it; the engraving draws the south flank rising sheer
from grade inside it, so it is not read as walls (the liberty's "not built"). The draft (a 11.75 x
10.25 m rectangle fitted inside the stone part alone) stood 9.8 m toward the street from this rear wall.

## The elevation: the engraving

Solved as a level pinhole, 8.8 px RMS on twelve readings (the camera's `solve`); about 38 px/m at the
corner. What it fixed, in turn, from the first render:

- the main mansard's rise 4.0 -> 3.0 m and the tower's 4.4 -> 2.8 m (the print's curbs);
- the storeys 4.5 + 4.6 -> 4.2 + 5.3 m, the wall head 11.5 m (the balcony, the tower's lights and the
  corona on the print's);
- the tower's street dormer taken out (a plain slated face in the print);
- the flank's lights round-headed, read once each, and a light in each cant of the flank bay;
- the stack moved to u 20.8 and broadened.

## A kit fix

On a stone flank that stops part-way back (`stone_front.flanks.to_m`, T-1887), a round-headed light
read off a picture in the stone span was passed to the brick wall behind as well, and the brick wall
laid its head's spandrels inside the stone span's hole: a strip of brick over each light.
`k01_frontage.py` now leaves such a light to the stone. `python3 generators/k01_emit.py --check`
re-derives every K01 asset byte for byte (1828 and 1815, the other split flanks, carry no round light
in their stone).

## Not built

The engraving's low rear wing, its veranda and the summer house on the south lawn are of 1874: the
1911 sheet draws the house three storeys to the rear wall and the south ground open (census
s35-2026-ground), so 1904 is built to it, as the match record argues. The census's frame piece on the
rear range's face (s35-2026-wing) is not hosted by K01's rear wings.

## Cost

The master GLB is 8.75 MB and its web derivative 4.0 MB (2018's: 4.9 and 3.8 MB).

# T-3347 — 2001 Prairie on K01: the stone-fronted corner house on 20th Street

Piece 2 of T-1912. The district draft (T-2352) is refined in place, under its own id
(`house_2001_prairie`), onto the K01 frontage assembly (`generators/k01_emit.py`), on the pattern of
1712 Prairie (T-3187), the programme's other two-and-a-half-storey stone front; liberty
`L-k01-2001-corner-3347`. The alley building (`house_2001_prairie_coach_house`) is T-1938's and is
untouched.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size and carried into the draft's plan frame through an affine fit of the committed
trace's pixel/metre pairs (`data/traces/prairie_1904_footprints_s35.json`, 5,014 pairs, 0.186 m a
pixel, 0.005 m worst residual), and the T-1842 census rows s35-2001-front and s35-2001-wing.

| reading | raster (column / row) | metres |
|---|---|---|
| front: outer face of the blue stone band | column 917.5 | u 19.05 |
| rear wall | column 1020 | u 0 |
| front part's north wall | row 274 | v 0 |
| party line with 2003 | row 310 | v 6.69 |
| rear part's north wall, on the 20th Street lot line | row 269, columns 957-1020 | v -0.93, u 0-11.71 |
| frame porch (yellow), not built | rows 265-268, columns 977-1004 | u 3.0-8.0, about 0.75 m past the lot line |

The draft's rectangle fit (15.0 × 5.75 m) stopped where the roof-covering marks printed inside the
house bite the trace, and took the rear step's line for the main body's north wall. The stone front
is the sheet's blue band across the whole street face; '2½B' is two storeys and a roof storey.

## What the kit forced

- The step (K08's flank step, T-3191) carries the main cornice across its face, so its wall top is
  the bed moulding's foot, 8.649 m, not the 9.3 m wall head: its top storey is 2.949 m.
- The hip wants a gutter of its own kind: half-round copper on brackets, 1712's.

## Not built

The one-storey frame porch on the 20th Street side (s35-2001-wing). It stands on the step's face,
and K08 does not host a projection on another projection.

## Browser reading

`node tools/qa_k01_t3347.mjs` (QA_PART a/b, QA_VIEWPORT desktop/mobile): the published /1904/ app.
Desktop 1280×800 front (across Prairie) and the 20th Street corner oblique are here as
`after-desktop-*.jpg`. The run hit this runner's 10-minute ceiling on software GL before its third
stand, so no validation JSON was kept. The flank, rear, roof and mobile stands were not taken, and
no "before" reading was taken on the draft. 2003 beside it still shows its draft in these shots:
T-3346 (#1654) refines it.

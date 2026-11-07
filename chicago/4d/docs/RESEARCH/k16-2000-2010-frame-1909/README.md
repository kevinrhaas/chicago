# T-1909 — 2000 and 2010 Prairie as whole K16 clapboard frame houses

The two district drafts at 2000 and 2010 Prairie (T-2351) are refined in place, under their own ids
(`house_2000_prairie`, `house_2010_prairie`), onto the K16 timber kit's whole frame house
(`generators/k16_emit.py`, the pattern of 1630 and 1720 Prairie); liberty
`L-k16-2000-2010-frame-1909`. The alley buildings are T-1935's and are untouched.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size and carried into each draft's lot plan frame through the T-1250 fit
(`data/traces/prairie_1904_footprints_s35.json`: 0.186 m a pixel). Readings, raster column / row → plan metres
(u toward the street from the record's origin, v along the front):

| house | part | raster | plan (u, v) |
|---|---|---|---|
| 2000 | main body | cols 589-681, rows 285-325 | u -0.93..16.16, v -0.75..6.55 |
| 2000 | front block '3BB' | cols 681-715.5, rows 293.5-323 | u 16.16..22.58, v -0.43..5.05 |
| 2000 | north range '2' | rows 283.5-293.5 | v 5.05..6.91 |
| 2000 | porch '1' | to col 725 | u 22.58..24.34 |
| 2000 | north canted bay | cols 648-680, out to row 278 | 6 m at the wall, 1.38 m out |
| 2000 | south room + canted bay | cols 650-680, rows 325-341 | 5.6 m, 1.5 m + 1.5 m out |
| 2000 | rear south room '2BB' + canted end | cols 617-647, rows 325-345 | 5.6 m, 2.3 m + 1.5 m out |
| 2010 | main body | cols 593.5-682, rows 418.5-455 | u -1.94..14.5, v 0.16..6.95 |
| 2010 | front block '3BB' | cols 682-715, rows 433-462 | u 14.5..20.64, v -1.14..4.25 |
| 2010 | north range '2' | rows 415.5-433 | v 4.25..7.5 |
| 2010 | porch '1' | to col 726 | u 20.64..22.68 |
| 2010 | north canted bay | cols 650-682, out to row 411 | 5.9 m at the wall, 1.39 m out |
| 2010 | south room + canted bay | cols 648-682, rows 455-478 | 6.3 m, 2.9 m + 1.36 m out |
| 2010 | rear south range '1' + canted end | cols 603-648, rows 455-484 | 8.4 m, 3.7 m + 1.68 m out |

The draft's rectangle fit (5.5 m along the front) stopped on the dashed lines and roof marks printed
inside the houses. No photograph, print or drawing of either house was found by address in the
Prairie library or in `data/sources/`, so the image gate does not apply; everything above the plan is
reconstructed (see the liberty).

## What the kit gained

`host_block` (`generators/archetypes/k16_timber.py`): a frame house's porch or bay may name the block
it stands on; it was always the first block. The seven K16 houses already standing re-emit
byte-identical. `tools/draft_prairie_1904.py` keeps a refined house's id for its shared lot's stable,
so the alley drafts keep their names when the house is skipped.

## Not built

The porches' returns along the front blocks' south sides (the kit's porch runs one wall); 2000's
narrow brick range on the rear wall (0.75 m, height not printed); 2010's 0.65 m step in the rear
range's south wall.

## Browser reading

`node tools/qa_k16_t1909.mjs` (QA_PART a/b, QA_VIEWPORT desktop/mobile) on the published /1904/ app.
Desktop 1280×800 front (across Prairie) and the north oblique (from the 20th Street corner) are here
as `after-desktop-*.jpg`; that run hit this runner's 10-minute ceiling on software GL during its third
stand, so no validation JSON with stand readings was kept. The south oblique, rear, roof and mobile
stands were not taken, and no "before" reading was taken on the draft.

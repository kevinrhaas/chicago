# T-3607 — 2018 Prairie on K01: the long brick house with a stone front, its bow and its porch

Piece 1 of T-1910 (2026 Prairie, the Louis Wahl house, is piece 2, T-3608: it has an 1874
engraving to solve and match). The district draft (T-2351) is refined in place, under its own id,
onto the K01 frontage assembly (`generators/k01_emit.py`); liberty `L-k01-2018-stone-front-3607`.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size and carried into the house's plan frame through the sheet's committed fit
(`data/traces/prairie_1904_footprints_s35.json` § fit, 0.186 m a pixel), with the T-1842 census rows
s35-2018-front ('3 brick dwelling (D), long and narrow, with a stone bay on its Prairie front') and
s35-2018-wing. The new origin is the main body's south-west (rear, south) corner at raster column 586,
row 595.5; the rotation, -0.379 degrees, lays u on the side walls the sheet draws.

| reading | raster (col, row) | plan (u, v) m |
|---|---|---|
| rear wall / front wall | 586 / 715.5 | u 0 / 24.07 |
| south wall / north wall behind the front block | 595.5 / 552 | v 0 / 8.08 |
| front block's north wall (from col 680) | 547.5-548 | v 8.83, u 17.47-24.07 |
| stone bow '2' (chord on the front, tip) | rows 564-596, col 726 | v -0.10-5.85, 1.95 m out |
| stone porch '1' | cols 716-728, rows 548-564 | v 5.85-8.83, 2.32 m out |
| north canted bay | cols 609-636 | u 4.28-9.29, about 0.84 m out |
| south canted bay | cols 640-662 | u 10.04-14.12, about 0.65 m out |
| frame bay, north flank (yellow) | cols 655-670 | u 12.82-15.61, 0.75 m out |
| frame rear porch '1' (yellow) | cols 575-586, rows 551-567 | u -2.04-0, v 5.30-8.27 |

The draft's rectangle fit (21.25 x 5.5 m, standing 1.15 m north of the south wall and 2.8 m short of
the front) read the stone front as a separate part and the printed figures beside both side walls as
bites out of the house, as T-3346 found on the east side.

## What the kit forced

- K08 keeps 0.3 m of wall between a bay and a corner, so the bow is 5.45 m on its chord, not the
  sheet's 5.95 m, and starts 0.3 m in from the south corner.
- The front block's 0.75 m step on the north is a shallow K08 projection flush with the front corner.
  K10 will not carry the cornice across one this long, so the step stops 0.4 m under the bed moulding.
  Its face is stone, as the sheet colours the front, and the stone returns along its 6.6 m of flank.
- The porch is K07's stoop under a stone hood on two columns, its floor a 2.3 m landing with a terrace
  either side of the 1.4 m flight; the hood runs 0.69 m past the main body's north corner, in front
  of the step's face, as the sheet draws the porch.

## Not built

Nothing the sheet draws on this house is left out. The parcel is one lot for 2000, 2010 and 2018, so
the yard's north edge is reconstructed (1.2 m past the front block).

## Browser reading

`node tools/qa_k01_t3607.mjs` (QA_PART a/b, QA_VIEWPORT desktop/mobile): the published /1904/ app,
front, both obliques, rear and roof; `after-*.jpg` and `browser-validation-after-*.json` here. The
house is 29,404 triangles in its web GLB (2005's is 16,788). The south oblique, looking down the
avenue, reads 5.8 M triangles in the view against the 4.7 M near budget (6.67 M far); 2018 is 0.5 % of
it, and the harness excuses that one stand. The only `problems` entry is the 1893 monument's review
notice, which says it does not block. No "before" reading was taken on the draft.

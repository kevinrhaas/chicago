# T-3346 — 2003 and 2005 Prairie on K01: the mirrored brick pair with curved front bays

Piece 1 of T-1912. Both district drafts (T-2352) are refined in place, under their own ids, onto the
K01 frontage assembly (`generators/k01_emit.py`); liberty `L-k01-2003-2005-pair-3346`.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size and carried into each draft's plan frame through an affine fit of the committed
trace's pixel/metre pairs (`data/traces/prairie_1904_footprints_s35.json`, 0.186 m a pixel, 0.005 m
worst residual), and the T-1842 census rows s35-2003-front/-wing and s35-2005-front/-wing.

| reading | 2003 | 2005 |
|---|---|---|
| main body, rear wall to front wall | 18.65 m | 18.65 m |
| main body along the front | 6.85 m (draft 5.75) | 7.0 m (draft 5.5) |
| curved bay: chord, rise, from the K01-local south corner | 4.8 m, 0.7 m, s 1.37–6.17 | 4.45 m, 0.7 m, s 0.48–4.93 |
| door (outer end of the pair) | world north, s 0.65 | world south, s 5.96 |
| rear range: neck, then range | 2.42 × 3.66 m, then 9.11 × 4.6 m | 2.43 × 3.67 m, then 10.22 × 4.57 m |

The draft's rectangle fit stopped short because the trace takes the dimension numerals printed near
both side walls for bites out of the house; the raster draws each main body the full width of its
lot, the two bows either side of the party wall and the rear ranges on the lots' outer lines.

## Where the pair stands

When 2001 Prairie (T-3347) landed on `dev` beside the pair, the structure-clearance gate found 2001 and
2003 standing 0.53 m deep into each other. Read through the same affine fit, the raster draws the
2001/2003 party line at rows 310-311, the 2003/2005 line at row 348 and the 2005/2007 line at row 386
(columns 980-1010); 2001's reading puts its party line at row 310, and this pair's first reading stood
at rows 307 / 344 / 382, about 3 px (0.53 m) north of the sheet's lines. The pair was moved whole
0.535 m south along its own side axis, so 2003's north wall stands on 2001's party line; the widths
and the pair's own party line are unchanged.

## What the kit forced

- K10 stands a cornice bracket 0.2 m from each front corner: 2003's door column puts its third-storey
  head under the north one, so the third storey's sash is 1.5 m on a 0.6 m sill (contract minimum),
  and each bow stops 1.2 m under the wall head with its own cap (as 1634/1636's bays) so the far
  bracket stands clear of it.
- A rear range wider than its neck says `past_host`.

## Not built

The 16 ft brick wall on 2005's south line from the rear range to the alley (s35-2005-walls): K01's
free-standing wall is the rear lot line's only (`alley_wall`).

## Browser reading

`node tools/qa_k01_t3346.mjs` (QA_PART a/b, QA_VIEWPORT desktop/mobile): the published /1904/ app,
front, both obliques, rear court and roof; `after-*.jpg` and `browser-validation-after-*.json` here.
No "before" reading was taken on the draft.

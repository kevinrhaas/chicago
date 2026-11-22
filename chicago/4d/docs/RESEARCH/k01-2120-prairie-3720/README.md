# T-3720 — 2120 Prairie on K01: the two-storey brick house with an iron-clad bay

Piece 1 of T-1926 (the S15 package of the T-1837 programme; pieces 2 and 3, T-3721 and T-3722, are the
Robbins house at 2126 and carry the parent's image gate). The district draft (T-2351) is refined in place,
under its own id (`house_2120_prairie`), onto the K01 frontage assembly (`generators/k01_emit.py`), on the
pattern of 2101 Prairie (T-3665), the other map-only brick house of the 21st-22nd blocks; liberty
`L-k01-2120-prairie-3720`. The alley building (`house_2120_prairie_coach_house`, census `s35-2120-rear`)
is T-1937's and is untouched.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size by dark-pixel profiles along rows and columns, and carried into the lot frame through the committed
trace's fit (`data/traces/prairie_1904_footprints_s35.json`, 0.1858 m a pixel; the frame turned as
`tools/draft_prairie_1904.py` turns it), with the T-1842 census rows s35-2120-front and s35-2120-wing and the
sheet's key (`sanborn_1911_vol3_key.jpg`).

| reading | raster (column / row) | plan frame (u from the rear wall toward the street, v from the south wall, + north) |
|---|---|---|
| main body's rear wall | column 644 | u 0 |
| main body's front | column 731.5 | u 16.25 |
| south wall | row 1357.5 | v 0 (the draft's corner stood 0.93 m north of it) |
| north wall | row 1294 | v 11.8 (the draft's fit: 11.0) |
| storeys | '2' in the north-east corner | two |
| roof mark | small circle by the south-east corner | the key's slate or metal roof: tin chosen |
| front porch, yellow, dashed outer edge, '1', small circle | columns 731.5-743.5, rows 1313.75-1333.75 | u 16.25-18.49, v 4.36-8.08: built 3.6 m wide on the door |
| north bay, grey (the key's iron-clad frame), lettered 'IR.CL.2D' in the house beside it | columns 678.75-693.75, out to row 1290 | u 6.49-9.28, 0.74 m out: two storeys |
| south bay, pink, '1', small circle | columns 691-716, out to row 1363.75 | u 8.70-13.35, 1.18 m out: one storey, brick |
| rear range's neck | columns 623-644, rows 1331-1348 | u -3.9-0, v 1.77-4.92 |
| rear range, pink, '1' (1911: 'Electric Motor Repairing') | columns 581-623, rows 1322-1358 | u -11.71 to -3.9, v 0-6.6 |
| rear frame porch, yellow, '1' | columns 625-645, rows 1295-1325 | not built |
| small piece on the neck's south side | columns 637-645, rows 1349-1355 | not built |
| lot lines (north / south) | rows 1287 / 1369 | v 13.0 / -2.14 |
| a narrow grey edge on the front's outer line | columns 732-734 | neutral grey (138, 124, 112), not the blue of 2001's stone band (155, 175, 181): not built |

## The design (all reconstructed; no picture of 2120 is known)

2101's floors and storeys (a 1.7 m principal floor on a high stoop, 4.0 and 3.6 m storeys); a deep red pressed front
over buff common brick on the flanks and rear; stone lintels under cornice hoods on both storeys of the front; five bays
on the front with the door in the middle under the sheet's porch, built as K01's timber porch on two turned columns, its
deck railed low; a 30 degree hip in painted standing-seam tin over a bracketed cornice (standing for the key's
brick-or-metal cornice); the north bay two storeys, its iron cladding as K08's painted frame face; the south bay one
storey in brick; two stacks on the north slope; the rear range one storey on a 0.6 m floor under a flat tin deck, lit
on its north, south and alley faces.

## Not built

- The one-storey frame porch in the angle north of the neck, and the small piece on the neck's south side.
- The rear range's canted alley corners (K01 lays a wing as a rectangle).
- The narrow grey edge along the front (too narrow to read as a facing).

## Checks

`node tools/photo_match.mjs` with throwaway review cameras (no picture to match, so nothing was committed under
`data/reference_views/`): the front from the north-east (`after-ne.jpg`) and south-east (`after-se.jpg`), the rear from
the south-west and north-west (`after-sw_rear.jpg`, `after-nw_rear.jpg`) and the roof (`after-roof.jpg`); the draft from
the same poses (`before-ne.jpg`, `before-sw_rear.jpg`). The first look found the range's south face blank along the side
passage; it was given two lights. The first builds refused slate on the 30 degree hip (its headlap), a porch deck that ran
into the lights beside the door, and a two-storey north bay reaching the cornice's bed moulding; each was fixed in the
record, not in the kit.

# T-3723 — 2125 Prairie as a whole K16 clapboard frame house

Piece 1 of T-1930 (the S18 package of the T-1837 programme; pieces 2 and 3, T-3724 and T-3725, are the
stone-front house at 2123 and carry the parent's image gate). The district draft (T-2352) is refined in place,
under its own id (`house_2125_prairie`), onto the K16 timber kit's whole frame house (`generators/k16_emit.py`),
on the pattern of 2000 and 2010 Prairie (T-1909), the district's other map-only frame dwellings; liberty
`L-k16-2125-frame-3723`. The alley stable (`house_2125_prairie_coach_house`, census `s35-2125-rear`) is T-1938's
and is untouched.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size by dark-pixel maps along rows and columns, and carried into the record's plan frame through the
committed trace's fit (`data/traces/prairie_1904_footprints_s35.json`, 0.1858 m a pixel) and the record's own
position and rotation (179.318 degrees). Plan frame: u from the main rear wall toward Prairie (west), v from the
north wall (+v is south on this side of the avenue). K16's sides run in that frame: its `east` is the street
front, its `south` the north flank, its `north` the south flank.

| reading | raster (column / row) | plan (u, v) |
|---|---|---|
| main body's front wall | column 918 | u 10.83 |
| main body's rear wall | column 976 | u 0 (where the draft put it) |
| north wall / south wall | rows 1379 / 1421 | v 0 / 7.89 (the draft's fit: 7.5) |
| storeys | '2BB' in the main body's north-west corner | two over a raised basement |
| front porch, yellow, '1', outer edge dashed | columns 910-918, rows 1379-1421 | u 10.83-12.29, the whole front |
| north projection, square-sided, no count | columns 947.5-962.5, out to row 1373.5 | u 2.53-5.32, 0.93 m out |
| south bay, canted, no count | columns 954.5-970.5 at the wall, 958-968.5 at its face, out to row 1427 | u 1.09-4.07, face 1.47-3.42, 1.12 m out |
| rear range, yellow, '1BB' | columns 976-1010, rows 1384-1413 | u -6.27-0, v 1.08-6.47 |
| rear porch, yellow, '1', outer edge dashed | columns 976-1010, rows 1413-1421 | v 6.47-7.92: not built |
| small circles (the key's slate-or-tin roof) | on the house by its south-west corner, the porch, the range and its porch | slate chosen for the gable |
| alley stable, crossed, '2' | columns 1136-1173 | T-1938's |

No photograph, print or drawing of 2125 is held by address in the Prairie library or `data/sources/`, and the
1904 Blue Book lists no household there, so the image gate does not apply; everything above the plan is a bounded
reconstruction (see the liberty).

## The design (all reconstructed)

2010's floors (a 1.0 m raised basement, storeys of 3.3 and 3.1 m); a 40-degree slated gable with its ridge running
back from the avenue (the draft's roof), an attic light in each gable; three bays on the front with the four-panel
door at the north end under a kit porch across the whole front, its steps at the door and a flagged walk straight
out to the public walk; the north projection read as the stair hall beside the door's end of the house, carried to
the eave and lit on its face; the south bay carried to the eave and lit on all three faces; three lights a storey
down the north flank and two on the south; two upper lights on the rear over the range; the range one storey under
a flat deck, two lights a face; one brick stack on the ridge; an olive-drab body with cream trim, apart from 2000's
stone drab and 2010's grey-green.

## Not built

- The one-storey porch south of the rear range (K16 builds one porch per house, the street one), and with it any back door.

## Checks

`node tools/photo_match.mjs` with throwaway review cameras (no picture to match, so nothing was committed under
`data/reference_views/`): the front from the north-west (`after-front_nw.jpg`) and south-west (`after-front_sw.jpg`),
the rear from the north-east and south-east (`after-rear_ne.jpg`, `after-rear_se.jpg`) and the roof (`after-roof.jpg`);
the draft from the same front and rear poses (`before-front_nw.jpg`, `before-rear_se.jpg`). The first build's body
paint read too close to 2010's grey-green and 2000's drab in the review light, and was taken darker to an olive drab.

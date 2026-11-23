# T-3729 — 2130 Prairie on K01: the Murdoch house, rock-faced stone under a steep street gable with a round corner tower

Piece 1 of T-1927 (the S16 package of the T-1837 programme); piece 2, T-3730, solves the two photographs' cameras on
this house, works the photo-match down and carries the parent's image gate. The district draft (T-2351) is refined in
place, under its own id (`murdoch_house_2130_prairie`), onto the K01 frontage assembly (`generators/k01_emit.py`), on
the pattern of 2011 (stone front, K08 round tower) and 2021 (a hip carried behind a street gable, `shaped_gable`);
liberty `L-k01-2130-murdoch-3729`. The coach house (`murdoch_house_2130_prairie_coach_house`) is untouched.

## What was read

Sheet 35 of the 1911 Sanborn (`chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/sanborn_1911_vol3_sheet_35.jpg`),
read at full size by classifying pixels along rows and columns (0.1858 m a pixel), carried into the record's frame
through the committed fit of the trace (`data/traces/prairie_1904_footprints_s35.json`). Plan frame: u from the main
rear wall toward Prairie (east), v from the south wall (+v is north on this side of the avenue), so K01's `south` is
the true south flank and `front_bays` count from the south corner.

| reading | raster (column / row) | plan (u, v) |
|---|---|---|
| street line | column 770 | 5.85 m before the front |
| front (outer edge of the blue band) | column 738.5 | u 21.93 |
| main body's rear wall | column 620.5 | u 0 |
| south wall / north wall ('2½B') | rows 1518.5 / 1465.5 | v 0 / 9.85 |
| north wall stepping in | row 1470.5 from column 684 back | 0.9 m in over the rear 11.8 m: **not built** |
| the stone bowed out ('3B' in a circle) | to column 750, rows 1466-1500.5 | 2.2 m proud on about 6.3 m, v 3.35 to the north wall |
| dashed ring inside it | columns 720-749.5 | a drum about 2.8 m in radius, centre about 0.6 m inside the face |
| stone front, brick rear | the block's colour divided on a diagonal | K01's stone front over K03 brick flanks and rear |
| '1B' rear range (pink, rear corners chamfered) | columns 572-620.5, rows 1481-1508 | u -9.0-0, v 1.95-6.97 (built square) |
| lot lines | rows 1534 / 1463 | v -2.88 / 10.31 |

The draft's fit had read only the largest stone rectangle (9.75 by 7 m) and set the rest as ranges and a bay; the
house's rear corner moves about 8.9 m back and 1.2 m south of the draft's.

Two photographs of 2140 next door show this house past 2140's north side (both forms only, `check_required`):
`chicagology_2140_photo_a`, from the south-east corner of 22nd Street, and the Glessner House blog's print
(`glessner_blog_2015_08_2140_photo`, a new source record: the image library's `a20-glessner-vanosdel-2140-photo`),
taken nearer this front. Read off them:

- the front and the tower in rough, rock-faced coursed ashlar with smooth dressed sills, lintels and string courses;
- a steep gable over the front's whole width, its north rake falling to the tower's cone, one attic light in its
  south half;
- a round tower in three stages — tall lights in two storeys, a short top stage of smaller lights over the main
  eave — under a steep slated cone on a moulded course, with a finial;
- a columned porch across the front's south end under the second storey's lights;
- a plain stack near the ridge behind the tower; slate on the roof;
- an iron railing on a curb along the street with a capped pier.

## Not built (recorded in the liberty)

- the columned porch: K01's corner porch stands on a podium at a corner, and no K01 part stands a recessed loggia;
- the tower's centre inside the face: K01 stands a single-capped front tower's centre on the face, so the drum is
  2.4 m in radius on a centre 0.1 m before the face (2.5 m proud where the sheet reads 2.2, a 4.8 m chord where it
  reads about 6.3; a centre on the face itself splits the finial on the wall's plane);
- the north wall's rear step, and the rear range's chamfered corners;
- carved and moulded detail beyond the kits'.

## Checks

The kit refused the first builds seven times, each fixed in the record: the upper storey's lights into the steep
eave's soffit, an arched door's opening on a square-headed door, a front with neither windows nor area lights named,
the hip's gutter unnamed, the street gable's apex under the ridge and its foot over the fascia, its light outside the
rake, the tower's centre inside the face, the rear lights cut by the range's junction, the iron front's side passage
ungated and the railing on the walk. `tools/check.sh` in parts, `validate.py --stale` and the smoke legs
`smoke_budget.mjs --for-diff` names are in the PR.

# T-2541 — 1811 Prairie onto K01 from the 1888 Inland Architect plate

Piece 1 of T-1891 (refine the 1811 Coleman/Ames Romanesque envelope). It refines the district
draft (T-2330) in place under `coleman_ames_house_1811_prairie`. T-2542 owns the roofs and brings
the match record to `matches`.

## The picture

The Inland Architect and News Record, vol. XII no. 3 (October 1888): "Residence of Miner T. Ames,
Chicago. Cobb & Frost, Architects." The Art Institute's Ryerson & Burnham copy (mqc 4518), public
domain, committed as `data/sources/assets/ames_1811_plate_t2541/` with source record
`inland_architect_1888_10_ames_residence`.

The Chicagology print of the house (library `cgn-1811-coleman-ames-photo`, a different negative
from nearly the same place) was only read beside the plate, to settle the south flank's three rows
of windows and its brick gable to the tall stack. Its rights are "unknown — link only", so it is not
committed and no camera is solved on it.

## The camera

`data/reference_views/coleman_ames_house_1811_prairie/inland_architect_plate.json`. A level view
camera, square to the front (the front's horizontals run level across the plate). The south flank's
wall head and foot converge at (689, 774) px, which gives both the principal point and the horizon.
The eye and the focal length come from a grid search over the eye's place. It fits three vertical
edges against the 1911 sheet's trace (the entrance block's south corner, and the two edges of the
bay's canted north face) to within 0.4 px: eye 14.9 m in front of the stone face and 4.05 m south of
the south wall, 1.05 m over grade, f = 659 px. `solve` gives the readings and their uncertainty.

## The plan, from the 1911 sheet

The draft's main body was the largest rectangle its 0.25 m fit found inside the trace: 7.25 m wide.
The trace itself, turned into the footprint frame (u toward the street, v south):

| part | u (m) | v (m) | reading |
|---|---|---|---|
| front block | 18.4 – 25.97 | −2.1 – 8.3 | the north wall at v −2.1 for the front 6 m, stepping in at u 18.4 |
| north bay (stone, p1) | to 27.0 | −1.94 – 3.92 | canted north face, front about 2.6 m on the sheet and 3.7 m on the plate |
| range | 4.3 – 18.4 | −0.1 – 8.3 | three storeys, brick |
| rear section | 0 – 4.3 | −0.1 – 8.3 | the drawn division at u 4.3: the "section 2B" |

The new frame's origin is the front block's rear north corner, the draft's (18.4, −2.1). The
position moves to it through the record's own rotation.

**Correction to T-1891's split titles.** The long brick flank the plate shows is the **south** flank
(the camera stands south of the house, and the trace puts the open side yard on the south). T-2541's
title says "north flank". The north wall faces 1801 Kimball's lot and is not seen on any picture.

## Before and after, from the plate's camera

- before: `before-draft-inland_architect_plate.jpg` (the dev draft, rendered from the same camera in
  the draft's frame)
- after: `../photo-match/coleman_ames_house_1811_prairie/inland_architect_plate-side-by-side.jpg`

The match record lists what is fixed and what is still open.

## Two generator rules, widened

- `k01_frontage_params.from_phase`: a hip needs the side walls longer than the front, but a K01
  **gable** (T-2459) runs its ridge along the front and does not. 1811's front block is 10.4 m wide
  and 7.57 m deep. Exempting the gable form changes no other record, since none has a gable over a
  front wider than its depth.
- `k01_frontage.build`: the check that an opening above a bay clears the bay's roof read an oriel's
  span from grade, so the door under 1811's oriel was refused. An opening wholly under the oriel's
  lowest corbel course (head + 0.30 m ≤ corbel foot) is now passed. That is the same clearance
  `k01_frontage_params._bays` already applies. The edit re-keys every mesh built through
  `k01_frontage.py`: 25 K01, K12, K13 and K16 assets were rebaked with byte-identical GLBs, and only
  their `inputs_sha256` moved.

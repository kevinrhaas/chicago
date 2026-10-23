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

## T-3005 — the entrance block's south corner, re-read; the oriel's cornice

Piece 1 of T-2989. Read on the plate through the T-2541 camera (`x = 689 + 659 (v - 14.45) / (22.5 - u)`).

**The corner is rounded.** Two things at the south end of the entrance block stand on a face
that recedes: the porch arcade's colonnettes (x 476, 490 and 501 px, their capitals stepping from
y 680 to 690 and their crowns from 647 to 660) and the oriel's south return (x 470-497 px, its
cornice falling from y 412 to about 465 across it, three narrow lights in it). From this camera a
square return at v about 9.7 shows about 15 px per metre of depth, so the oriel's 0.6 m return
would fill about 9 px, not 27, and a flat return on the front's plane would need the oriel to
stand about 2 m deep. The rock-faced base under the arcade is lit evenly from x about 458 to
514 px with no arris, and the downpipe's shoe meets the walk at about y 816 px, which puts it at
about u 6.0, v 10.2: on the south wall's face, just behind the front. A corner rounded on a
radius of about 0.9 m (centre near u 6.67, v 9.5) reads all of it: its front tangent stands at
x 470 px, its far side at about x 515-520 px (the edge T-2541's solve took for a square corner at
x 510), and on it the three colonnettes stand at about 8, 27 and 44 degrees from the front,
evenly about 0.28 m apart, stepping down as they go round. The 1911 sheet draws the front square
to the south wall at its 50 ft scale; a 0.9 m round is under 1 mm there. The camera solve stands:
the corner's silhouette moves its third edge 5-10 px, inside its stated uncertainty.

K01 cannot round a corner, so the corner is T-3006, the oriel over it T-3007, and the arcade on it
T-2991 after them.

**The oriel's cornice.** The plate's "cornice at 9.06 m" is the cornice's TOP: its moulded band is
drawn at y 407-417 px (about 8.81-9.03 m at the oriel's 0.6 m-proud face) with the slates
starting directly over it. K01 carried an oriel through the eave only with its wall top 0.3 m
over the eave datum (9.14 m), so it stood at 9.46 m with its fascia to 9.71. The rule now also
takes a wall top under the datum that rises 0.3 m over the eave's front edge, the fascia's top
(9.14 - 0.35 tan 61.2 = 8.50 m), so the eave still dies into its walls; `k08_bays._back` closes
its back over the datum behind its eaves and spire only, since the house's own wall stands
behind its walls to the datum. 1811's oriel storey is 3.81 m: its wall top 8.81 m and its
fascia's top 9.06 m, the band landing at y 407-417 px with the plate's; the spire rises 2.75 m
so its apex stays at 11.81 m. 1623's oriel, the only other through-eave one, re-emits
byte-identical, as does every other K01 house.

## T-3006 — K01 rounds a corner; 1811's entrance block turned on 0.9 m

Piece 2 of T-2989. The front block's corner is now a record field, `round_corner`
(`{"corner": "north" | "south", "radius_m"}`, K01's own names for the front's two ends). The round
is a quarter circle tangent to the street front and to the side wall it turns into. It is laid in
the front's stone and coursed on the front's own beds, from grade to the stone's top: base, coping,
belt and walling, rock-faced as the front is. No course holds more than two stones, and each stone
is curved in facets of at most 7.5 degrees (`Assembly.round_stone`). The front and the side wall are
cut away over the round's spans up to that top. The front's courses stop at its tangent, and the side
wall's brick and its string course start at the other.

**The head.** The plate does not show the corner's head. The oriel's roof covers it, and the coped
gable's edge rises straight over the round's far side. So the round's last course (7.89-8.30 m on
1811) is a dressed corbel, ruled from the round out to the square, and the moulded cornice, the eave
and the coped gable stand on the square corner as before (L-k01-1811-round-corner-3006). Carrying the
cornice and the eave round a curve would change nothing the plate shows, and it would need a curved
K10 cornice and a rounded roof corner, which K01 does not have.

**The pipe.** The plate's rod at x 505-510 px stands on the round itself, about 50 degrees round from
the front, so `front_pipes` now accepts a pipe behind the front's plane (proud_m down to -1.5 m)
where it stands on a round, its centre as far off the curve as a front pipe stands off the front (`_round_corner` refuses
anything else). 1811's pipe is at s 10.29 m, proud_m -0.368, which lands at about x 508 px.

**What the plate camera reads now:** the round runs from the front's tangent at x about 469 px to
its far side at about 518, against the plate's 470 and 515-520. Every other K01, K12, K13 and K16
asset re-emits byte-identical, and only their manifest `inputs_sha256` moved.

## T-3007 — the oriel over the rounded corner

Read through the T-2541 camera (x = 689 + 659 (v − 14.45) / (22.5 − u), level, yaw −90).

- **Front.** The plate's oriel front runs x 338–470 px. At 0.6 m out (u 8.17) that is v 6.82–9.69, 2.87 m: a flat-fronted box,
  its north return square (hidden from this camera). Its lights' centres, x 372 / 406 / 440 px, are v 7.56 / 8.31 / 9.06.
- **South return.** 27 px wide (x 470–497). A square 0.6 m return would show about 9 px. Its three narrow lights shrink
  only slightly to the right and its cornice line falls straight, so it is a flat face splayed toward the camera, not a
  curve: from the front's corner (u 8.17, v 9.69) back to the wall plane at v 10.10 (x 497), 0.73 m. There the round
  (centre u 6.67, v 9.5, r 0.9) stands 0.23 m behind the plane, so the oriel's back is closed on the plane over the round.
  The downpipe at x 500–505 runs just past its end, as the plate draws it.
- **Base.** A rock-faced band from y 561 to 584 px at the face (about 5.68 to 5.18 m), a shadow under it to about y 600
  (5.0 m at the wall): the band turned under to the wall. Built as a 0.7 m rock-faced storey on a 0.2 m round apron
  whose foot is the 5.0 m floor; the render's band ends at y 590.
- **Spire.** Over the front's middle (v 8.26), the plate's finial at x 416; the render's at 414.

What is invented is L-k01-1811-oriel-3007.

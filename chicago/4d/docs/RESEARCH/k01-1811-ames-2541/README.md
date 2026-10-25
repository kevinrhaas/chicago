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

## T-2991 — the porch arcade round the rounded corner

Piece 2 of T-2984. Read at 7x on the plate (x 465-510, y 620-745 px), through the T-2541 camera.

- **Where the lights stand.** Three colonnettes like the mouth's carry on round the curve at x 477, 490 and 500 px,
  which on the 0.9 m round (centre u 6.67, v 9.5) is about 8, 27 and 44 degrees from the front's tangent. Their
  capitals are at y 678-697 px, the line of the mouth's capitals, and their bases sit on a ledge at y 722-733 px,
  the top of the mouth's plinth. The three dark round-headed lights (x 473-480, 485-492 and 497-503 px, crowns y 646,
  652 and 658) stand OVER the capitals, not between them, so the arcade is three lights each on its own colonnette.
  At these angles the round faces the camera within about 10-25 degrees, so depth cannot shift a light off its
  colonnette by a pixel.
- **The record.** `entrance_kit.loggia.round_arcade`:
  `{"angles_deg": [8, 27, 44], "clear_width_m": 0.18, "crown_m": 0.79, "reveal_m": 0.3, "band_m": 0.55}`. The sill
  is the mouth's springing (3.15 m, a bed of the front's courses). K01 refuses a sill that is not a bed, an arcade
  with no round or no mouth's columns, lights crowding each other or the front's tangent, a frame running onto the
  side wall, and a loggia whose end stands more than 0.6 m from the round's tangent or past it.
- **The build.** The round's two courses from 3.15 to 4.05 m are laid in dressed stones, one a light, from the
  tangent to 0.12 m past the last light. Each stone is cut through by its light 0.3 m deep: a soffit, jambs, a
  sill and a dark back. The rest of those courses is laid as before. Each colonnette stands in the round's own frame
  at its angle. Under them a dressed plinth band 0.55 m deep is carried round from the mouth's plinth, as proud of
  the round as the plinth is of the front (the plate's smooth band, y 727-748 px).
- **What the camera reads now:** lights at x 472-479, 485-492 and 497-503 px (the plate's 473-480, 485-492 and
  497-503), the first crown at y 646 with the plate's, colonnettes at about 475, 487 and 499 against 477, 490 and
  500, capitals at y 681-690, and the band at y 720-745 against 727-748.
- **Left open.** The plate's arcade steps down to the south (bases 0/4/9 px, crowns 0/6/12 px). Going round the
  curve accounts for under 1 px through this camera. The build is level, and the step is an open item on the match
  record for T-3079's camera re-solve. Every other K01, K12, K13 and K16 asset re-emits byte-identical.

## T-3099 — the rear on 1 July 1904: the sheet stands, and the pavilion is the stable

T-3079 left the question open: the plate and the Chicagology photograph (both about 1888) seem to show a short
lower range ending about 6 m behind the front block, and a separate pavilion with an arched door. The 1911 sheet
draws one straight-walled 3B/2B building 26 m deep and a 1½-storey garage on the alley. The ticket asked for a
dated source from between 1888 and 1904.

**The source.** The Greeley-Carlson *Atlas of the City of Chicago* of 1891, the plate covering Prairie Avenue
(`carlson_greeley_1891_prairie_environs`; the image store's copy `st-greeley-carlson-1891-prairie-environs.jpg`,
2400 x 1370 px, north to the right). Crop of 1811 and its lot, 4x: `greeley-carlson-1891-1811-crop.jpg`. The
scale along the lot is the lot's own: the street line at y 517 px and the alley at y 646 px are 150 ft apart (the
1907 sale's '46x150'), so 0.86 px a foot, 2.8 px a metre. The plate's widths do not hold to that scale (the house
is drawn as wide as its lot), so only depths are read from it.

| | 1891 plate (m from the street line) | 1911 sheet, as built (m) |
|---|---|---|
| house front (bay included) | 5.7 | 7.6 (stone face), 6.6 (bay) |
| front block's north wall steps in | 14-16 | 15.2 |
| house rear | 32.8 | 33.6 |
| house depth | 27.1 | 26.0 |
| the stable on the alley | 38.3 - 45.7, crossed, '25' | 36.8 - 45.8, '1½-storey brick GARAGE' |

One pixel is 0.35 m; the plate is a compiled atlas (tier 2), not a survey.

**The ruling: the sheet stands for 1904.** Three years after the plate, and thirteen before 1904, the house was
already one continuous body about 27 m deep with its front block stepping in on the north about 9 m back, as the
1911 sheet draws it. The house is unchanged. The plate also draws the rear 6 m narrower on the south side (by
about 2 m), where the 1911 sheet draws it full width. That is within the plate's drawing tolerance and is left on
the south flank's match record for T-3129, not built.

**The pavilion is the stable, and it had two storeys.** The building with the arched door past the flank on the
Chicagology photograph stands where the plate puts the stable, about 5.5 m behind the house at the alley. The
'short lower range' was the house's rear seen end-on through a camera standing too close (T-3079's camera
re-solve). The Tribune of 16 April 1904 offers the empty house to rent with a '2 story stable'
(`chicago_tribune_1904_04_16_1811_prairie_to_rent`), and the same agents repeat it on 1 September 1905. So the
coach house goes up from one storey to two for 1904. It is still the draft's 9.0 x 9.75 m body under the draft's
gable, through a dated count the frontage row now carries (`services.s28-1811-rear.storeys_1904` in the draft
rules, read by `tools/draft_prairie_1904.py`). Why the 1911 sheet counts 1½ storeys, no source says.

**Read and found silent:** Rand McNally's 1893 street strip (`st-randmcnally-1893-p233-east-1700-1800`) draws
1811's front only, and 1815 overlaps its south side. No Rascher plan, building permit or Sanborn sheet between
1888 and 1904 was found in the library or the image store.

**Left open:** the stable's own picture. Its arched door, steep roof and front gable on the Chicagology
photograph are not built. That needs the photograph's camera re-solved deep enough to reach it (T-3079's camera
work).

## T-3133 — the south flank on the c. 1888 pictures: built, ruled and closed

**Read.** The Chicagology print (`ames_1811_chicagology_photo.jpg`, 1303 x 1598 px) between x 1060 and 1220,
at four times. Along the brick flank every light is round-headed, and under each of the rear lights stands a
round-headed basement light: x 1084, 1107, 1148, 1167, 1185 and 1197 px, crowns at y 1165-1168 and feet at
y 1228-1245, each 1.0-1.2 times as wide in the print as the light over it. The crowns stand on the horizon
(y 1165), so about 1.35 m over grade at the camera's 1.35 m eye, whatever their depth along the flank. The
lights over them are the build's principal-floor lights (sills about 1.9 m, heads about 4.4 m through the
same camera, against the build's 1.95-4.15 m).

**Built.** Both wings' flank lights cut round-headed (`rear_wings[].round_heads`, new in K01), turned in the
flank's own brick; a round-headed basement light 1.0 m across, 0.30-1.35 m, under each of them
(`rear_wings[].basement_lights`, new), placed under the light over it as the print sets each, not off the
camera (L-k01-1811-flank-round-heads-3133). The bay's two basement lights lowered towards the print's foot:
sill 0.22 to 0.17 m, head kept at 1.22 m, by halving the bay's plinth to 0.05 m (K08's `plinth_m` now reads
down to 0.05 m) while keeping the kit's 0.02 m of wall over it and the K06 sill under the light. Through the
camera the render's light runs y 1178-1270 px against the print's 1176-1277: the foot 7 px (about
0.08 m) short, the depth of the K06 sill the kit keeps under every light.

**Ruled: the coping stands at the plate's 10.98 m.** Compared in the image through the same camera, the
render's wall head lands on the print's where the print's high coping runs: y 587 against 583 px at x 1150
and 602 against 604 at x 1165, on the same slope (about 1.4 px a pixel), within about 0.07 m at the flank's
56 px a metre there. One ray meets the flank's plane at one height, so the build's coping is the print's. The
"about 0.6 m higher" of the match record was read off the vanishing point, not against the render. What
differs is where the high coping ends (the print's 3B/2B step at x 1167, the build's at about 1295): the
flank's depth through this camera.

**Ruled: the 1891 atlas's narrower rear is not built.** The Greeley-Carlson plate draws the rear 6 m about
2 m narrower on the south. That is six of the plate's pixels, and its widths do not hold to scale (the house
is drawn as wide as its lot, above); the 1911 sheet draws the rear full width on the south wall's straight
line, and no picture shows the rear's south face. The sheet's full width stands, as T-3099 left it.

**Closed against T-3099, and what each camera still shows.** The three flank-depth items are closed on
T-3099's ruling that the 26 m house stands for 1904. Each camera still draws the flank short: the print's
step at x 1167 against the build's about 1295 and its end at about 1205 with the stable past it; the plate's
end at about x 585 against the build's 626; the Glessner print's at about 547, with sky, where the build runs
past the print's edge. Both cameras fit the front within a few pixels and meet the flank's end at the same
place. Either a camera that reaches the flank's rear without losing the front, or an extension of the rear
between 1888 and 1891, would explain it, and 1904 stands as built either way. That is T-3149.

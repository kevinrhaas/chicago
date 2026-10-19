# Glessner's west-court door — its level (T-2760)

Piece 4 of T-2228. The T-2228 register's `west-court-access` item: the stable wing's courtyard
door beside the north-range junction stood at sill 5.8 ft / head 14.0 ft above the 18th Street
grade (world x 10.8204 m, y 13.5941-14.3561 m, sill 1.7678 m), with no stair or landing to reach
it. It had been given the north-court service landing's datum.

## What the sources say

| source | date | what it shows | rights |
|---|---|---|---|
| HABS IL-1015 sheet 2, first floor plan (`habs_glessner_house_il_1015_drawings`), native crop (5900,3300)+1200x1100, `habs2-west-flight.jpg` | 1963 | A narrow flight on the west wing's courtyard face whose `DN` arrow points north **toward** the door, its treads at the south end of a long narrow landing that ends at the door's swing. The raised north-court flight beside it points the other way (down from its landing to the court). The sheet's only dated note is "wooden stairs behind service wing added c. 1955", a different stair on the wing's far side. | public domain |
| w_lemay, courtyard, 26 Oct 2024 (`wlemay_glessner_courtyard_2024_159537058`), the library's 1920 px copy, SHA-256 `fca788a6fd27666ee3ee38d80fc01d617812a539bd93bc50684af40ec6a49f1d` (re-fetched and matched) | 2024 | The door low beside a railed walk. Its rock-faced lintel stone courses with the sill stones of the first-floor windows south of it. | CC BY-SA 2.0; reference only, no crop committed |
| HABS sheets 4-6 | 1963-66 | Section A-A looks east at the east wing; sheet 5 is masonry details; sheet 6 the Prairie front. None draws the west wing's court face. | public domain |
| HABS photograph 5 (c. 1923) | c. 1923 | Looks east-north-east at the bow and the underpass; the west wing is behind the camera. | check_required |

So the two sources that see the door at all agree it is **low**: the plan descends to it, the
photograph shows it at the walk. Neither supports a door 5.8 ft up.

## The reading (native pixels of the 1920 px photograph)

| feature | y (px) |
|---|---|
| first-floor window (narrow, south of the door), opening top / bottom | 581 / 689 |
| door opening head (lintel's underside) | 680 |
| door opening foot, where it meets the walk | about 866 |
| granite base course top at the door | about 855-860 |

`course_period.py` reads the brick coursing's period from a row-mean profile (FFT) of the wall
beside the jamb: `python3 course_period.py p1920.jpg 220 248 700 850` gives **5.51 px** a course.
A course on this record is 66.675 mm (`surface_finish.flat_brick.course_m`, 2 5/8 in).

- Door height: 186 px / about 5.4 px a course (the door is a little farther from the camera than the
  sample) = **about 34 courses = 7.5 ft**.
- Head against the window: 9 px above the window opening's bottom = 1.6 courses = **0.35 ft**.
- The record's first-floor windows on this face are 7.5-13.5 ft, so the head is **7.85 ft** and the
  sill **0.35 ft**. Built so.

## What is not built, and why

The 1963 flight and its areaway. The plan prints no level and no date for them, its treads are too
faint to count with confidence (six or seven lines), and in 2024 a sloping railed walk stands where
they were drawn. Building a sunken areaway would need a depth nobody has read; the door's head is the
one measured thing and it puts the door at grade. If the 1904 threshold was a step or two lower, into
that areaway, the head stays where it is and only the sill moves. Recorded as
`L-glessner-west-court-door-2760`.

## Courtyard views

None of Glessner's solved reference views shows this face of the west wing (the court views look east
or north), so no match record moves. The register item `west-court-access` is closed as `fixed` with
its limit stated.

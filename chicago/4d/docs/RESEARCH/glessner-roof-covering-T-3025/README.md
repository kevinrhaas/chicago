# Glessner's roof covering: red tile, and why every print reads it grey (T-3025, piece 3 of T-2854)

Three Glessner match records carried one open item between them: the roofs, the stable
cupola's pyramid included, read slate-grey in the prints where the model lays red tile
house-wide (`habs-01-northwest`, `habs-15-stable-detail`, `cornell-northwest-west-windows`).
The ticket asks what the roof was laid in, from a contract, a specification, a description or
a colour view, and for a ruling.

**Acceptance, stated before the work:** the covering is ruled on a written source that names
it, every match-record item that reads the covering from a print is closed on that ruling with
its reason, and the record is rebaked only if the ruling changes the covering.

## 1. What the roof was laid in

Two sources name it, and they are independent in kind.

- **The owner's description of the house as built.** *"The roofs are of red baked tiles,
  unglazed, the outside walls on the streets are of Wellesley granite, and all walls are lined
  with hollow brick"* (J. J. Glessner, *The Story of a House*, March 1923;
  `glessner_story_of_a_house_1923`). Re-read for this ticket in the HABS transcription,
  `prairie_1904_v1/research/public/glessner-habs-data.pdf`, data p. 13 (PDF p. 14). He is
  describing construction (the granite, the hollow-brick lining), so it carries back to 1887
  and forward to 1904.
- **A physical survey.** *"Roof surfaces are covered with terracotta, tar covered tiles, six
  inches wide with five inches of their length exposed"* (HABS IL-1015 data, p. 21, 1963;
  `habs_glessner_house_il_1015_data_pages`). The surveyors were on the house: what lay under
  the tar was terracotta, so slate is excluded as a covering for any date the 1963 tiles were
  already on the roof.

No contract or specification was found in the library, and no colour view of the house before
1904 is known to it. The 2024 colour photographs (`wlemay_glessner_courtyard_2024_*`) show
modern fabric and are kept out of the ruling.

**Ruling: red baked, unglazed terracotta tile, house-wide, the cupola's pyramid included.** The
record already says so (`roof_covering`, `terracotta_tile`, attested on both sources), so
nothing moves and nothing is rebaked. The ruling is written on the three match records and here, not appended to the record's `roof_covering` note: that note is part of the light derivative's staleness hash (`validate.py --stale` reads it stale with one sentence added), so a prose-only change there would cost a bake. Glessner says "the roofs", HABS "roof surfaces", and
neither excepts the cupola. The c. 1887 Cornell print lays its pyramid in the same small
coursed units as the main roofs. The only exception either names is the hall bow, which is
copper and modelled copper.

## 2. Why every print reads it grey

Every picture of the house in the library is monochrome, and none of them can say what colour
a surface was (`data/reference_views/README.md`: colour in a monochrome print is `not shown`).
They fall into two groups:

- **The 1963 and 1965 HABS prints** (photographs 1, 13-17) show the tiles under the tar HABS
  recorded that year. Their dark grey is the tar's.
- **The 1887-1888 prints** (the Cornell print, Taylor 2135, the *Inland Architect* plate) were
  made on dry plates, which before panchromatic emulsions recorded mostly blue and green light.
  A red surface records dark on them. This is the general behaviour of the period's plates, not
  a reading of these particular plates, so it is reasoning and is cited to nothing.

`stable-roof-cornell.jpg` shows this. On the left is the Cornell print's stable roof between
the cupola and the north gable. In the middle is the render of the same plane through the same
solved camera, in the record's red tile. On the right is that render reduced to its luminance.
The red tile reads as a slate-grey roof darker than the granite, the same impression the
item recorded. A grey roof in a monochrome print is what this roof would look like whether it
was red or slate. It therefore cannot overrule the two written sources.

One residual is recorded rather than used. The print's roof reads a little lighter against
its granite than the luminance render does. A roof slope and a wall face take different light,
and more so under the print's overcast sky. The emulsion's response is also not modelled. A
roof-to-wall tone ratio therefore measures the light as much as the colour, and it decides
nothing here.

## 3. A finding on the module, not the material: a new ticket

The Cornell print resolves the stable roof's courses. With the print and the render sharing one
camera, the same pixel columns cross the same plane in both, so the ratio of their course
periods is the print's course in units of the render's 5 in:

    python3 docs/RESEARCH/glessner-roof-covering-T-3025/read_courses.py

| columns | print period | render period | ratio | print course |
|---|---|---|---|---|
| 1000-1030 | 4.38 px | 3.40 px | 1.286 | 6.43 in |
| 1040-1080 | 4.45 px | 3.54 px | 1.257 | 6.28 in |
| 1090-1120 | 4.81 px | 3.67 px | 1.310 | 6.55 in |
| **mean** | | | **1.284** | **6.42 in** |

(`readings.json`.) So the c. 1887 roof reads about 6.4 in to the course, where the model lays
HABS's 1963 5 in (L-glessner-roof-tiles-2203, which carries the 1963 module back to 1904 as
inferred and names "a calibrated roof close-up" as the way to settle it). The reading does not
separate tile from slate: a 16 in slate at a 3 in headlap also shows about 6.5 in. The material
ruling stands on section 1, and the module question is filed as its own ticket. It needs the
render's course measured at a resolution where the texture is not near its sampling limit
(3.4-3.7 px here), a second picture, and a look at whether the roof was relaid between 1887 and
1963.

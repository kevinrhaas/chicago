# Glessner's rock-face relief by course, and the cupola's coursing (T-3046, piece 3 of T-3026)

T-3044 read Taylor 2135 through its solved camera. It found that a high course's lower lip throws
1.32 times a low course's shadow in the photograph and 0.95 times in the render. T-3045 then laid
the courses at their measured heights. This piece builds the relief and lays the stable cupola's
stone in courses.

    node tools/photo_match.mjs data/reference_views/glessner_house/taylor-2135-ne.json --out /tmp/x
    python3 docs/RESEARCH/glessner-course-relief-T-3046/read_relief.py --render <the bare render it prints>

`readings.json` holds the before and after readings, row by row. `prairie-before-after.jpg` is the
Prairie front's north half through the same camera, dev on the left and this build on the right.
`cupola-cornell.jpg` is the cupola in the Cornell print beside the render through its camera.

## 1. The reader, re-based on the laid beds

T-3044's `read_courses.py` places each course on the printed string's beds. That is what the
model laid until T-3045. Since T-3045 the model lays beds 8-23 at 1.045 times the printed inches,
so a row read on the printed beds straddles two courses (T-3045's caveat). `read_relief.py`
imports T-3044's camera, sampling, opening registration and lip measure unchanged, and changes
only the beds. The render's beds are the laid string's. The photograph's beds are the laid string
fitted to it about bed 7, and since T-3045 that fit reads 0.995-1.000.

On the laid beds, the dev render (GLB `eabb640c…`) reads:

| | high courses (>= 11.5 in), n 18 | low courses (< 11.5 in), n 27 | high / low |
|---|---|---|---|
| Taylor 2135 | 0.246 | 0.188 | **1.31** |
| render, dev | 0.308 | 0.358 | **0.86** |

T-3045 made the render's ratio worse than T-3044's 0.95. Its taller courses stretched the high
courses' lower faces further.

## 2. Why the render's high courses read shallow

`fractured_stone` bows each stone over a crown above its pitch line. The crown is 0.12 m per metre
of the stone's short side plus 18 mm, held to 30-60 mm. The lower face rises to the crown over
`BOW_PEAK` (44 %) of the course's height. The lip's shadow follows how steeply that face leaves the
arris, which is about the crown over the lower face's length:

| course (laid) | crown | lower face | slope off the arris |
|---|---|---|---|
| 7.5 in (0.199 m) | 42 mm | 88 mm | ~1.05 |
| 11.5 in (0.305 m) | 55 mm | 134 mm | ~0.90 |
| 20 in (0.531 m) | 60 mm (cap) | 234 mm | ~0.57 |

So a tall course's lip was gentler than a short one's, which is the opposite of the photograph.

## 3. What was built

`v4_detail.ashlar_crown_by_course = {from_in: 11.5, scale: 1.25, lip_m: 0.09}`. A course printed
11.5 in or over crowns 1.25 times its stones' bow. Its lower face rises to the crown over at most
0.09 m, about the lower face a 7.5 in course already has. The house's own string carries it
(`masonry_house_params` → `ashlar_course_crowns` → `ashlar_course` → `fractured_stone`), so both
granite faces take it, round the NE corner as one coursing. A caller's own course string is left
on the plain bow: the chimney bands, the cupola and the dressed carriage-jamb piece. Neither
parameter consumes a random draw, so every joint, stone length and per-stone relief is unchanged.
`ROCK_FACE_MAX` stands, so lintels and voussoirs stay in front of the field. The Light tier builds
no bow and is unchanged.

Through the same camera, on the build this PR ships (GLB `5fff90bb…`):

| | high | low | high / low |
|---|---|---|---|
| Taylor 2135 | 0.246 | 0.187 | **1.32** |
| render | 0.470 | 0.353 | **1.33** |

The first trial of the same parameters, before the cupola coursing and its fresh occlusion bake,
read 1.30. Its low courses read 0.359. The course fit is unmoved: scale about bed 7 is 0.995-1.000
on all three piers, and correlation is 0.90, 0.86 and 0.67. The two numbers are a fit to a
shadow ratio, not a measured projection: L-glessner-course-relief-3046.

## 4. The cupola

The Cornell print (T-3044 § 4) shows two or three bed joints in the shaft under the lower pigeon
ledge, and each pigeon-hole tier as one rock-faced course between its ledges. The record's
`turret_stable.body_coursing = {shaft_courses: 4}` lays the granite body in rock-faced stone,
through the house's own `ashlar_course` on a string of its own, as the chimney bands are laid.
The shaft is four courses of about 0.27 m, from the roof to the lower ledge. Each tier is one
course from its ledge to the next, and the band over the top tier is one. Every face runs the full
plan, so its courses close the corner walls' ends. The body behind stands back of the mortar bed.
The holes' reveals run out to the pitch line, as the house's apertures' do. The print does not
resolve vertical joints, so block lengths follow the house's rule: L-glessner-cupola-coursing-3046.
The cupola adds 9,433 triangles to the full tier (1,377,975 → 1,387,408), with 0 coincident faces
(K01). The Light tier keeps the plates.

## 5. Records closed

- Taylor 2135, HABS 16: the relief item is **fixed**.
- HABS 13, 14, 17: their course items close with Taylor 2135's, as T-3044 § 5 ruled.
- Cornell: the cupola's coursing is split out of the mixed residual item as its own **fixed**
  entry. The pyramid's covering stays open there on T-3025.

HABS 13, 16 and 17 now carry no open item. Their verdicts are left as they were for T-3028, the
photographic sign-off, which owns that ruling.

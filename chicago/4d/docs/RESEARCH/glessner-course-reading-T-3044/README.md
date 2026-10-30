# Glessner's rock-faced courses read on Taylor 2135: heights and relief (T-3044, of T-3026)

T-3026 asked to "read the course heights and projections and build or accept them". The match
records kept the item open in six views. Taylor 2135 says the courses "alternate deep and shallow
more strongly than the render's". HABS 13, 14, 16 and 17 say course relief stays open, and the
Cornell view says the cupola's coursing is not modelled block by block. This piece is the
reading. It found that the coursing has to be rebuilt, not accepted, so T-3026 was split. The
rebuild is two tickets of its own (§ 5).

`read_courses.py` re-derives every number here from the committed photograph, its solved
camera and the record:

    node tools/photo_match.mjs data/reference_views/glessner_house/taylor-2135-ne.json --out /tmp/x
    python3 docs/RESEARCH/glessner-course-reading-T-3044/read_courses.py --render <the bare render it prints>

The render was made from the dev GLB as `recover_glessner_v4.py --materialize` writes it
(sha256 40c41087…68ece9). `readings.json` holds the output, and `pier-n2.png` is one pier drawn
both ways.

## 1. How it is read

Taylor 2135 (c. 1887-89, public domain, `taylor_2135_glessner_exterior_1887_1889`) is the
sharpest early print of the Prairie front. Its camera was refitted by T-2858 on the ten
first-floor jambs. Each face is sampled along vertical lines in the wall's own plane through
that camera, so every reading is in feet on the wall. A pier's profile is the median across its
columns. That keeps the continuous bed joints and drops the staggered vertical joints. The
render through the same camera stands for the printed string, because the model lays
`ashlar_courses_in` exactly.

Three piers run clear from the walk to the second floor without a lamp post or a tree in front
of them. They are 4.6-6.8 ft (N1), 21.0-25.6 ft (N2) and 39.9-42.3 ft (S1) south of the NE
corner.

**The camera's vertical scale is not trusted as measured.** The window sills, the first-floor
heads and the second-floor heads stand 2.1-2.9 % higher in the photograph than in the render
(`openings_registration`). The south half reads 1.0293 with a 0.03 ft rms. The north half reads
1.0214 with a 0.19 ft rms, because opening A's head reads high. That is the camera and the
model's opening heights together, not the courses. So the photograph is first put on the
model's heights through the openings, and the courses are read relative to the openings.

## 2. Heights: the photograph sides with sheet 6

A free fit stretched the render's profile about bed 7 until it best matched the photograph's
over beds 8-23 (8.0-22.6 ft over the walk):

| pier | correlation, printed string as laid | best fit: scale over bed 7 | correlation | bed 23, ft over the door datum |
|---|---|---|---|---|
| N1 | 0.04 | 1.0450 | 0.88 | 22.28 |
| N2 | 0.07 | 1.0475 | 0.87 | 22.19 |
| S1 | -0.12 | 1.0450 | 0.65 | 22.40 |

The printed string, as the model lays it, does not correlate with the photograph above bed 7 on
any pier. Stretched by 4.5-4.75 %, it correlates at 0.87-0.88 on the two clean piers. All three
piers, read independently, agree on the scale to 0.25 %.

That is the measurement T-2986 asked for to re-open its ruling. It is independent of both 1960s
surveys, and it agrees with sheet 6:

- **The printed string** (the record) puts bed 23 at **21.63** ft over the door datum.
- **Sheet 6's drawn beds** (T-2986 § 3, the 1965 photogrammetric plot) put it at **22.39-22.49**,
  4.5 % over beds 7-23.
- **Taylor 2135**, relative to its openings, puts it at **22.19-22.40**, 4.5-4.75 %.

T-2986 ruled the printed inches on three reasons. The second and third are untouched. Drawn lines
on sheet 5 are freehand, and the figures are still the only course heights anyone wrote down. But
its dissent now has two independent witnesses, the 1965 plot and an 1880s print. The figures may
be nominal stone sizes, or the courses were set with fuller beds than the figures. Either way, the
wall as built was coursed about 4.5 % taller than their sum.

Its first reason, the north eave, is where the rebuild has to look (T-3045). At 4.5 % the cap
stands about 0.1-0.2 ft over sheet 4's scaled 23.1 ft eave, inside what a scaled section can be
read to. T-2986 already called that refusal narrow.

**Below bed 7 nothing is re-read here.** HABS 5's drawing put beds 1-7 beside the door within
0.05 ft of the string (T-2949, T-2955), and the fit starts at bed 7.

**Round the corner.** Read uncalibrated, the same way on both faces, the 18th Street face's courses
fit 1.055 (W 15-24.5, correlation 0.91) and 1.0675 (W 1.5-3.0). The Prairie corner pier fits 1.075.
So the photograph does not show the courses parting at the corner: the north face is within about
1-2 % of the Prairie face. The north face's own openings were not used to register it, so its
absolute course height is not read here. T-3045 reads it against them.

## 3. Relief: high courses stand deeper in the photograph, not in the render

For each course from 8 to 22 on the three piers, the reading takes its lower lip's shadow as a
fraction of the course's own median brightness. Courses are placed on the fitted beds in the
photograph and on the printed beds in the render:

| | high courses (≥ 11.5 in), n 18 | low courses (< 11.5 in), n 27 | high / low |
|---|---|---|---|
| Taylor 2135 | 0.247 | 0.187 | **1.32** |
| render | 0.320 | 0.337 | **0.95** |

This is the "deep and shallow" of the Taylor item, measured. In the photograph a high course
throws about a third more shadow under itself than a low one. In the render they throw the same.
The render's shadows are deeper overall, but the review render's light is not the print's
exposure, so only the ratio is compared.

The build explains the render's ratio. `fractured_stone`'s crown rises 0.12 m per metre of the
stone's short side plus 18 mm, clamped to 30-60 mm. A 7.5 in course crowns about 41 mm and an
11.5 in one about 53 mm, and everything from 14.5 in up is held at the 60 mm cap. The per-stone
random depth (`ashlar_relief_ft`, 0.025-0.15 ft) is drawn the same for every course. The
pitch-line arris is 16 mm everywhere. So the lip, which makes the shadow, is the same on a high
course and a low one.

How much deeper the high courses stood is a projection no source prints. The 1.32 is a target to
fit through this camera, not a dimension (T-3046).

## 4. The stable cupola's coursing (Cornell print)

At the print's resolution the cupola's shaft below the lower pigeon ledge shows two to three
horizontal joints. Each pigeon-hole tier stands as one course between its ledges, and the
stone's face is broken like the gable's. The render lays the shaft and the tiers as smooth
dressed plates. The print does not resolve the vertical joints, so block lengths are not read.
They would be reconstructed, at the gable's own stone lengths. That is filed with the relief
piece (T-3046), because it is the same rock-face build and wants the same rebake.

## 5. Rulings and filed work

- **Heights: not accepted.** Taylor 2135 reads the Prairie front's beds above bed 7 about 4.5 %
  over the printed string, as sheet 6 does. T-2986's dissent is now the reading, and
  `L-glessner-coursing-2986` says so. **T-3045** re-courses both granite faces and carries the
  18th Street apertures and the eave. It is not built here, because it moves every stone above
  bed 7 on two faces and the openings set on the string's sums (L305). Three sibling runs are
  rebaking Glessner today (T-3024, T-3025, T-3027). It is a build of its own.
- **Relief: not accepted.** The photograph's high/low shadow ratio is 1.32 against the render's
  0.95. **T-3046** deepens the high courses' crown until the render reads the photograph's ratio
  through this camera, and lays the cupola's courses. It comes after T-3045, because the crown
  scales with the course height T-3045 changes, and tuning it first would mean baking twice.
- **The match records** keep their course items open. Each now states what was read and names
  the ticket that closes it. HABS 13, 14, 16 and 17 add nothing Taylor 2135 does not: the 1965
  soot and the plates' scale hide relief at their distances (HABS 16, the frontal one, is sheet
  6's own plate, T-2986 § 2). They close with Taylor 2135's item when T-3046 lands.

## Gate

Docs and match-record text only. No record, mesh or derived file changes, so no rebake.
`./tools/check.sh` was green on the branch.

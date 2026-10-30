# T-3058 — Taylor 2135's camera with its principal point freed

T-3027 found that T-2858's camera for Taylor 2135 (`data/reference_views/glessner_house/taylor-2135-ne.json`)
could not reach the three stacks. It held the principal point at T-2221's value (415.5, 815.5),
and even with the stacks admitted as controls the south stack read -13 px. Freed, it fitted
better, but that solve had several minima. This ticket finds the camera and adopts it.

The solve lives in `tools/glessner_prairie_front.py` (`solve_taylor`), and `check.sh` re-derives
it (`glessner_prairie_front.py --check`).

## What the camera is fitted on

| | weight | source |
|---|---|---|
| the ten first-floor jambs (x) | px | T-2857's picks, the far jamb at the sash 0.6 ft behind the arris (T-2858) |
| the five earlier controls | px | T-2221's; the two Prairie corners control height only (their x picks are the downspouts) |
| the three stacks' centres and tops | px | each stack's record box against T-2857's picks |
| 43 plumb edges | lean x the edge's length in px | `verticals.json`, read by `read_verticals.py` |

The stacks' **widths are not fitted**. They are the check.

**The stacks are their boxes, and nothing is carried.** T-2858 added a correction taken from
T-2221's render: what that render drew minus where T-2221's camera put the box, read as the cap's
overhang. `read_caps.py` projects the committed GLB's own vertices in each stack's cap course
(the top 0.45 m). Through either camera, every cap reads within 0.5 px of its box (`caps.json`).
So the correction was scatter in the render picks, not an overhang. Taking the band down to
0.7-1.0 m pulls in the shaft's rock faces: up to 7 px on the north stack's east side.

**The plumb edges hold the pitch.** Freed, the principal point trades against pitch. On the
jambs and stacks alone, the solve tips the camera 3.3 degrees up and drops the principal point
to match. Every plumb edge in the photograph leans toward the vertical vanishing point:

- the lean's trend across the frame is the pitch;
- its mean, with the principal point, is the roll.

`read_verticals.py` finds the edges as gradient ridges that run most of a band of rows. It
locates each row to a tenth of a pixel and fits a line. Trees and the lamp post are left out by
column, and rows that scatter more than 0.6 px are dropped. It keeps 43 of 45 edges, with a lean
scatter of 0.0084. Nothing is picked by hand.

## The camera

All 36 starts end at the same camera: the committed camera turned ±10 degrees, focal length
×0.9-1.1, principal point moved -300 to +600 px.

| | T-2858 (held) | T-3058 (freed) |
|---|---|---|
| principal point | 415.5, 815.5 | **549.6, 712.0** |
| focal | 2331 | **2251** |
| eye | 89.85, 40.37, 1.70 | 87.35, 39.98, 1.81 |
| pitch / roll | ~0 / 1.1 | **2.59 / 1.37 deg** |
| controls + jambs rms | 1.36 px | 2.08 px |
| jambs, worst | 3.6 px | 3.3 px |
| stacks | withheld: south -14.6, middle -7 to -8, north within 4 | **fitted: centres and tops 1.6 px rms** (south centre -3.1, middle -1.9, north +0.3) |

The photograph is a 1600 x 1502 scan with a black border. A principal point well left of and
below the frame's centre fits a view camera with its front shifted, as an architectural
photographer of the 1880s would use one.

**The widths are the check.** The south stack's box is -0.1 px against the photograph and the
middle's -0.6 px. The north stack's is **+8.6 px**: 82.6 px against the picks' 74. That is
T-3065, below.

**Open: pitch.** The plumb edges alone give 1.2 ± 0.45 degrees: the lean's trend of 9.0e-6 per
px, through f 2251. The joint fit settles at 2.6 degrees. The stacks' centres stand 400-600 px
above the jambs, so they carry the same convergence over a longer baseline, and they pull the
pitch up. The edges keep a lean rms of 0.0096 against their own scatter of 0.0084, so they are
not thrown out. But the two disagree by about three of the edges' standard errors. The likely
cause is the stacks' plan places, which are reconstructed to about ±0.3 ft (`chimney_plans`),
or the north stack's width (T-3065). Neither is ruled here.

## Re-read through it

- **Render.** `node tools/photo_match.mjs data/reference_views/glessner_house/taylor-2135-ne.json`
  re-rendered `docs/RESEARCH/photo-match/glessner_house/taylor-2135-ne-side-by-side.jpg`. A 50 %
  blend of photograph and render shows no doubled edge on the house.
- **T-3045's courses.** `docs/RESEARCH/glessner-course-reading-T-3044/read_courses.py --render`
  on that render. Its output is kept here as `courses.json` and `pier-n2.png`, so T-3044's own
  reading stays as it was.

| pier | T-3045 (T-2858 camera): corr / free scale about bed 7 | T-3058 camera |
|---|---|---|
| N1 | 0.765 / 0.9975 | 0.765 / 0.9975 |
| N2 | 0.692 / 1.000 | 0.613 / 0.9975 |
| S1 (weathered) | 0.171 / 0.995 | 0.161 / 0.9675 |

Both clean piers still want T-3045's coursing to within 0.25 %, so the courses stand. S1's read
was weak before and is weak now.

The openings register the camera's vertical scale at 1.017 on the north piers and 1.052 on the
south. One south head reads 24.35 ft in the render against 25.53 in the photograph, the edge
finder catching a different line.

## T-3065, found again and handed back

Through this camera, the north stack (W 15.25-22.35, S 0-3.1) is 82.6 px across. At rows
200-216, below the cap's soft right edge, the photograph reads about 77. Magnified, the
photograph's north-east corner, where the courses change direction, stands at x ≈ 1035:

- **east face:** 991-1035 = 44 px, about 3.1 ft at the built 14 px per ft, so sheet 6's 3.1-ft
  depth stands;
- **north face:** 1035-1068 = 34 px against the built 39, about **6.2 ft against T-2873's 7.1**.

A first look at HABS 17, also from the north-east, agrees. HABS 01 read about 6.3 ft (T-2873).
HABS 14, square to the face, reads 127 px against the render's 128. A plain box cannot satisfy
both: narrowing to 6.2 ft would break HABS 14 by about 16 px. Resolving it, and the device's
projection, needs a Glessner rebake. T-3065 was released with these readings written onto it.

## Files

- `read_verticals.py` → `verticals.json`: the plumb edges.
- `read_caps.py` → `caps.json`: the built caps against the boxes. It needs the gitignored GLB:
  `python3 tools/recover_glessner_v4.py --materialize`.
- `courses.json`, `pier-n2.png`: T-3044's course reader through this camera.

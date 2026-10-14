# T-2470 — Glessner's north gable and round tower

The correction joins the north gable to the tower as one flat street facade,
restores its two tall window pairs, and turns only the western wall around the
curve. It also removes the repeated vertical masonry grid and the roof strips
that crossed the gable and a window. The model represents 1904. Photographs
from 1963–65 document surviving form, not the date of every fitting.

## Evidence and reconciliation

The library's full-resolution HABS IL-1015 photographs 1, 13 and 14 and drawing
sheets 2–6 were inspected. Photograph 1 is Cervin Robinson's northwest exterior,
23 July 1963 (`habs_glessner_photo_01_nw_1963`). Photographs 13 and 14 show the
north facade and its curved western return (`habs_glessner_photo_13_north_1965`,
`habs_glessner_photo_14_north_inclined_1965`). Their rough-faced courses have
staggered joints around the curve. Photograph 13 crops the cone and cannot
independently measure its apex. These HABS sources have no known restrictions.

There is no north elevation among the six HABS sheets. Sheets 2–3 provide the
window plan positions; sheets 4–6 provide sections, details and the east elevation.
Houghton GLE B9 was inspected as a cross-check only: this design study has a
taller, narrower tower and different openings. It does not override photographs
of the built house, and no geometry is derived from this rights-check-required
source. The c.1923 HABS photograph 4 is likewise a cross-check only.

The old reading assumed a 26.5-ft-wide north gable and a separate full cylinder.
That misplaced the crest, shortened the upper windows to the corridor's 3-ft
height, and exposed a curved north-east wall absent from the photographs. It also
led to a duplicate lower slit at W17.6–19.0. The sheet-4 section shows the tower
beyond the cutting plane; its partly occluded elevation extent does not establish
a circular roof plan. These assumptions are superseded, while the original
T-2200/T-2206 measurements remain historical records.

## Geometry and its bounds

W/S are feet west/south in the existing building frame; heights below are feet
above north grade. Photographic positions are inferred or reconstructed, not a
new survey.

| Feature | Before | Corrected |
|---|---:|---:|
| Tower centre W / S | 35 / 8.6 | 41 / 7.35 |
| Drum radius | 7.35 | 7.35 |
| Eave radius | 8.35 | 9.35 |
| Drum top / cone eave | 32.9 | 33.3 |
| Roof apex | 43.9 | 43.4 |
| Finial height | 2.0 | 1.5 |
| North gable crest W | 13.25 | 18.8 |
| Upper paired-window sill / head | 19.25 / 22.25 | 20.0 / 25.25 |

The flat north wall continues from W0 to W41, where it turns around the western
half drum. The north gable's western foot is reconstructed at W37.6, with a
concealed transition to the courtyard pitch by S14.6. The north stack, date
stones and arched light move with the gable axis. Their heights are retained. The two stacks on the revised main pitch start at
the roof plane rather than a stale horizontal base, and their flashing follows
that plane; their positions and tops are unchanged.

The upper pairs retain sheet-3 positions: W7.2–10.1 / 12.0–14.7 and
W25.8–28.1 / 30.0–32.9. Their new heights follow the photographs within about
0.5 ft. The two existing lower lights at W4.0–5.6 and W28.7–30.3 remain; the
incorrect third light is removed. A narrow attic light at W38.7–39.8,
z27.4–31.2 is a photographic reconstruction. Round colonnettes replace the
solid square masonry between each upper pair. Their small foliate capitals
use bounded stock forms, not a claim to reproduce every carved leaf.

The cone's total rise is 10.1 ft, including the 1.1-ft flared skirt. Sheet 4's
approximately 10.32-ft reading bounds this within its stated roughly one-foot
uncertainty. The 1.5-ft finial follows the sheet's separate tip reading. The
three skirt strips, 35-mm dark edge, 88-mm pipe and its 40-mm host-roof clearance
are reconstructed fitting dimensions. Monochrome photographs do not establish
alloy, 1904 colour or weathering.

Curved masonry uses the same course heights, variable stone widths and rough
finish as the adjoining wall. Stones are laid on one unwrapped surface before
bending; angular subdivision does not create mortar joints. Full retains the
fractured faces and continuous metric grain; Light retains its bowed shading.
Individual stones remain procedural liberties. The host roof enters the drum
slightly, closing the former bright gap; its continuation through the flat facade
and paired windows is removed. The connector stops at the sloping gable coping.

## Photographic cameras

The HABS01 camera re-reads the actual north-east eave foot at (158,638); the old
(169,608) pick lay on the gable slope. A level shifted camera fits the grade/eave
and plan-based horizontal window/street controls, excluding tower and gable crest.
Eye height 1.8m is reconstructed, focal length is fitted, and coordinate RMS is
2.60px. The finial tip pick is (428,460). The camera and pick stay fixed across
before and after models.

HABS14 needs an inclined, slightly rolled camera. Its fit uses the plan-positioned
north windows, north stack crest and great chimney crest, with the tower excluded.
Coordinate RMS is 5.68px. Its principal point and model-derived depth controls
limit independence: the remaining tower-tip residual is about 34px. This is not
an exact whole-view match. The camera's controls, including the depth control,
are recorded in `data/reference_views/glessner_house/habs-14-north-inclined.json`.

The old T-2200 HABS14 camera is also reported. Its tower residual worsens after
the corrected plan, rather than improving; it relied on the earlier facade
interpretation and already had a loose fit. It is not silently replaced in the
historical comparison report. The reconciled cameras provide the new comparison,
held fixed across both models. `tools/glessner_north_tower_review.py` checks actual
copper vertices against each model's own semantic finial tip and records all
three results, including the old camera's disagreement.

```sh
PW_EXECUTABLE=/usr/bin/chromium node tools/photo_match.mjs \
  data/reference_views/glessner_house/habs-01-northwest.json \
  --glb assets/web/glessner_house__as_built_1887.glb
```

Match records retain whole-house differences for T-2228. Colour, remaining roof
and chimney proportions and other elevations are not declared exact by this
bounded correction. The owner specifically added the north windows, curved
masonry and gable/eave junction to this ticket; they are part of its review.

## Validation

The final master and Full web asset contain 1,300,083 triangles; Light contains
199,998, below the unchanged 200,000 limit. All three have zero coincident faces
and pass the K01 scale, origin and metric-UV checks. Full/Light were rebuilt with
the pinned Blender and web toolchain; the recovery archive carries the same assets.

The curved-stone, roof-contact, gable-clearance, chimney-foot and drainage checks
pass. Roof-envelope rays and the existing roof-edge checks pass. The rainwater
receipt records nine runs: seven unchanged and two east-wing gutters following
the revised host pitch. These are geometric checks, not a whole-house photographic
sign-off. Final HABS 01 and 14 comparisons use the actual Full web asset; their
match records retain the remaining differences. Prototype colours are not used
as evidence of final material quality.

Actual-master tip residuals, with each camera fixed across before/after:

| Camera | Before | After |
|---|---:|---:|
| HABS 01 reconciled | 25.873 px | 1.523 px |
| HABS 14 reconciled | 77.254 px | 33.878 px |
| Original T-2200 HABS 14 | 206.304 px | 302.501 px |

The `before-*.png` files and `after/` directory carry actual published 1904 app captures
at 1280×800 Full and 390×780 Light; the phone Images tab is checked for loaded,
credited pictures. Repository and complete published smoke verdicts are recorded
in the merging PR, which must be green before integration. T-2228 retains final
whole-house photographic acceptance. The owner's later west/stable-gable finding
(the clipped service door, clipped upper window and roof junction) is separate
from this north-east tower correction and belongs with service-openings work.

The photo tool also supports explicit orthonormal camera basis vectors for
inclined views. Its screenshot uses the exact viewport after render readiness,
avoiding an element-stability timeout; an unchanged Full asset previously gave
identical pixels between viewport and canvas capture.

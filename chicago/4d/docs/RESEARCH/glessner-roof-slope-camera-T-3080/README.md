# The Cornell camera, not the roof, drew the stable's slope 1.3 times long (T-3080)

T-3072 counted about 43 courses between the c. 1887 Cornell print's own ridge (the foot of the
cresting) and eave on the roof plane over the stable's alley end, and about 42 on HABS
photograph 1 of 1963. Through the committed cameras the Cornell print put 22-23 ft of slope
between those edges and HABS 1 put 17-17.5 ft, and the model's ridge projected about 30 px
below the print's.

**Acceptance, stated before the work:** say which is wrong, the Cornell camera or the stable
roof's plane, from cameras that never saw a roof point; re-solve the camera or rebuild the
plane; re-read the slope's course through the result.

**Ruling: the camera.** The committed Cornell camera is a west-wall homography on two
reconstructed eave heights, 18.3 px RMS on the measured controls at the stable that it was never
fitted to. T-2758 re-solved it there on measured controls only (3.7 px pitched, 4.8 px level;
`data/comparisons/glessner/stable-roof-heights.json`). Through those two fits the Cornell
print's course reads **4.98-5.32 in**, HABS's 5 in, and its slope 17.3-19.5 ft, where HABS 1
reads 16.9-18.8 ft. The re-solve this ticket asks for is T-2758's; nothing is re-fitted here,
and no roof point enters any fit. The committed camera stays the view's camera, as T-2758 ruled:
the west windows were placed through it, and it reads them where the roof fits do.

    python3 docs/RESEARCH/glessner-roof-slope-camera-T-3080/read_slope.py    # writes readings.json

The script needs the gitignored GLB: `python3 tools/recover_glessner_v4.py --materialize`. It
uses T-3072's own plane fit and course counter (`../glessner-roof-module-T-3072/read_module.py`)
and the same ridge and eave picks.

## 1. The count, through every camera

The plane is the north slope of the E-W ridge that runs from the turret to the alley gable:
42.5°, eave 7.65 m, ridge 12.05 m in the GLB's frame, 21.4 ft of slope. Three columns per
print, seven columns counted at each.

| print, camera | RMS on measured controls | course read | slope read |
|---|---|---|---|
| Cornell, committed (west wall, reconstructed eaves) | 18.3 px | 6.27-6.37 in | 21.9-23.3 ft |
| Cornell, T-2758 roof fit, pitched | 3.65 px | **5.25-5.32 in** | 18.2-19.5 ft |
| Cornell, T-2758 roof fit, level | 4.76 px | **4.98-5.03 in** | 17.3-18.4 ft |
| HABS 1, committed | 2.6 px on its own controls, 9.0 at the doorway | 4.94-5.00 in | 16.9-17.6 ft |
| HABS 1, T-2758 doorway | 3.92 px | 5.22-5.33 in | 18.1-18.8 ft |
| HABS 1, doorway, eye height free | 3.09 px | 5.21-5.28 in | 17.9-18.6 ft |
| HABS 1, doorway, lean | 3.13 px | 5.11-5.23 in | 17.5-18.2 ft |

(`readings.json`. T-2758's pixel-aspect fits of HABS 1 are left out because the counter's camera
has square pixels. The square doorway fit has the same residual and brackets them.) The Cornell
print, read through a camera fitted where it can be checked, agrees with HABS 1 to within the
spread of HABS 1's own fits. The 1.3 was the committed camera's alone.

## 2. Where it went wrong: the edges, through each camera

For each counted column, the model's tile vertices on the fitted plane within 0.15 m of the
column's line give the plane's top and foot. Each print's ridge and eave rows are carried onto
the plane by the same camera. Heights are in metres, model minus print.

| print, camera | ridge: model top above the print's | eave: model foot above the print's |
|---|---|---|
| Cornell, committed | **-0.70 to -0.94** (the print's is higher) | **-0.44 to -0.49** |
| Cornell, roof fit, pitched | 0.29-0.53 | -0.03 to -0.01 |
| Cornell, roof fit, level | 0.78-0.98 | 0.22-0.26 |
| HABS 1, committed | 0.96-1.11 | 0.30-0.32 |
| HABS 1, doorway fits (three) | 0.64-1.07 | 0.20-0.42 |

The committed camera puts both of the print's edges on the plane **above** the model's. It
carries the ridge further than the eave, so the slope stretches; that is the "ridge projects
about 30 px below the print's". Every camera fitted on measured controls puts the print's eave
on or just under the model's, and the cresting's foot **below** the model's ridge.

## 3. What is left is the plane's, and it is filed

Six cameras over two prints, 76 years apart, agree on a second, smaller discrepancy that is
not the camera's. The model carries 21.4 ft of slope between this plane's eave and ridge, about
51 courses at 5 in. Both prints count 41-44 between the eave and the cresting's foot, about
17.5-18.3 ft. A count does not depend on any camera. Every fitted camera puts the eave where
the model has it and the cresting's foot 0.3-1.1 m lower than the model's ridge. A ridge roll
under the cresting would hide perhaps a course or two, not seven or eight.

Which of the ridge's height, its plan line, the plane's pitch or the alley gable's coping
carries the difference is a rebuild-or-rule of its own. It needs a bake. It is **T-3094**,
filed beside the Glessner sign-off (T-3028). This ticket does not move the roof.

## 4. What changed

- The Cornell match record carries the ruling (fixed) and the plane's residual (open, T-3094).
  HABS photograph 1's record carries the residual too (open). The camera, the record and the
  GLB are untouched.
- T-3072's README and readings stand as written. Its count is the evidence here. Its slope
  through the committed camera is what this README explains.

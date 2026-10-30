# The stable's cross ridge rebuilt to T-3095's ruling (T-3096)

T-3095 ruled that the north slope over the stable's alley end is too long at the top: both prints
count 41-44 courses where the model laid about 51, and only a ridge brought down the same 42.5-degree
plane gives the same height to the count and to T-2758's measured-control cameras. This rebuilds it.

**Acceptance, as T-3095 stated it before the work:** on the rebaked GLB, `read_slope.py` (T-3080) and
`read_ridge.py` (T-3095), run unchanged, give 41-44 courses between the model's eave and roll foot; the
roll foot lies within 0.3 m of the model's in every measured fit and the eave within 0.4 m; the alley
gable's coping stands proud of the tiles to an apex within T-2758's 38.75-40.63 ft; no other Glessner match
record gets worse.

    python3 docs/RESEARCH/glessner-stable-ridge-T-3096/read_rebuild.py   # slope-readings.json, ridge-readings.json, acceptance.json

`read_rebuild.py` runs both scripts as they stand, with their output pointed here. It leaves one camera out
of read_slope's list: HABS photograph 1's committed camera. Its counting field now takes in the hidden south
slope behind the lowered ridge, because the reader keeps every roof vertex within 4 m of the nearest depth
and has no occlusion, so its plane fit comes out vertical. It is not one of the measured fits.

## 1. What was built

| | before | now |
|---|---|---|
| cross ridge (`stable_roof_rework.cross_ridge`, `cross_ridge_S`) | 38.6 ft ng at S 14.6 | **36.5 ft at S 12.31**, on the same north plane (42.5 degrees) |
| tiled top over the alley end (GLB) | z 12.05 | z 11.41 |
| alley gable | wall stopped under the tiles, no coping | **parapet**: wall line unmoved (apex S 14.6, 38.6 ft), 1.0 ft over it, stone coping; the roof stops at the wall |
| south slope of the cross ridge | about 47 degrees | about 41 degrees |
| cupola | on S 14.6 | unmoved; the lowered ridge runs into its west face 0.14 m inside its north side |

The roof's verge no longer oversails the alley wall over the gable (`alley_parapet` in
`masonry_house_v4_west_roof.py`); south of the gable's foot the alley eave keeps its overhang. The ridge roll
starts behind the parapet. The coping's top at the apex stands at about 40.2 ft, inside 38.75-40.63.

## 2. Against the acceptance

From `acceptance.json`. The print's roll foot over the model's (positive: the print's is higher), and the
print's eave over the model's.

| camera | RMS px | courses at 5 in | roll foot, print over model (m) | eave (m) |
|---|---|---|---|---|
| Cornell, committed | 18.3 | 43.1 | +1.37 / +1.47 / +1.58 | +0.47 to +0.52 |
| Cornell, roof_pitched | 3.65 | **43.8** | +0.21 / **+0.35 / +0.44** | +0.01 to +0.08 |
| Cornell, roof_level | 4.76 | **43.8** | -0.25 / -0.13 / -0.05 | -0.19 to -0.25 |
| HABS 1, doorway | 3.92 | **43.9** | -0.03 / +0.08 / +0.09 | -0.20 to -0.23 |
| HABS 1, doorway_eye_height | 3.09 | **43.8** | -0.26 / -0.20 / -0.15 | **-0.39 to -0.42** |
| HABS 1, doorway_lean | 3.13 | **41.8** | +0.11 / +0.12 / +0.10 | **-0.40 to -0.45** |

- **The count: met on every camera.** 41.8-43.9 courses, where every camera read about 51 before.
- **The roll foot: met on four of the five measured fits, and the fifth cannot be met with them.** The
  Cornell pitched fit reads the roll foot 0.35 and 0.44 m over the model's on two columns. The Cornell level
  fit, on the same print and the same columns, reads it 0.13 and 0.05 m under. The two fits are 0.46-0.49 m
  apart column by column, so no ridge height lies within 0.3 m of both (it would have to be at least 0.14 m
  higher than built for the one and at most 0.05 m higher for the other). Before the rebuild the same two fits
  read -0.44 to -0.20 and -0.89 to -0.69. That is a question about the Cornell fits, filed as **T-3102**.
- **The eave: unchanged by this rebuild.** HABS 1's eye-height and lean fits read the print's eave 0.39-0.45 m
  under the model's, as they did before (0.38-0.42 m in T-3080's readings). The eave did not move.
- **The coping:** stands 0.06 m clear of the tiles' top on the north rake, where the wall line and the
  lowered roof share a plane, and up to about 1.5 m over them at the apex's south side; its apex top is about
  40.2 ft (`tools/test_glessner_roof_envelope.py` holds both).
- **Other match records:** every Glessner view was re-rendered on the new GLB; no verdict changed. The
  T-3080 residual is closed on both pictures that count it.

`ridge-readings.json` is read_ridge.py's output on the new GLB: its candidate families are computed from the
model as T-3095 found it, so they are the ruling again; its `glb_plane_check` now reads the rebuilt plane.

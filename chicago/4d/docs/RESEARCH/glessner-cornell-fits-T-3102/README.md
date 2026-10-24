# Which Cornell camera holds on the stable's roof (T-3102)

T-3096 rebuilt the stable's cross ridge and found T-2758's two re-solved cameras of the Cornell
c. 1887 print 0.46-0.49 m apart on the alley-end roll foot: the `roof_pitched` fit read the print's
roll foot 0.21-0.44 m over the model's, the `roof_level` fit 0.05-0.25 m under it, on the same three
counted columns. No ridge height lay within T-3096's 0.3 m of both.

**Ruling: the pitched fit does not hold on the roof, and the camera that does is tilted about
2.5 degrees with its lens raised. Through every camera this print admits, the rebuilt ridge meets
T-3096's acceptance. Nothing in the house changes.**

    python3 docs/RESEARCH/glessner-cornell-fits-T-3102/read_fits.py --write      # readings.json (any tree)
    python3 docs/RESEARCH/glessner-cornell-fits-T-3102/read_rollfoot.py          # rollfoot-readings.json (needs the GLB)

## 1. Why the two fits disagree: one valley, two ends

Both fits use T-2758's 13 controls: the stable's two corners at grade and up their arrises, the
carriage doorway's east jamb and 12.6 ft soffit, and the loft opening's jambs. Every one of them lies on
the walls, below about 25 ft. A camera tilted up and a level camera with its lens raised (a view
camera's rising front) draw those walls almost alike. They part only above the walls, on the roof.
`read_fits.py` walks that valley at pinned tilts, with everything else of `roof_level` free:

| tilt | controls RMS | principal row | coping apex | cupola apex at S 14.6 | plumb-line RMS |
|---|---|---|---|---|---|
| 0 (= `roof_level`) | 4.76 px | 982 | 38.25 ft | 46.45 ft | 0.0096 |
| 2 | 4.18 | 909 | 38.57 | 46.97 | 0.0041 |
| **3** | 3.94 | 872 | 38.73 | 47.20 | **0.0038** |
| 4 | 3.74 | 834 | 38.90 | 47.42 | 0.0060 |
| 6 | 3.55 | 754 | 39.22 | 47.76 | 0.0120 |
| 8 (about `roof_pitched`) | 3.64 | 665 | 39.52 | 47.97 | 0.0178 |

From 0 to 9 degrees the controls' RMS stays between 3.55 and 4.76 px. The picks are good to about
±5 px, so **the controls cannot tell the tilts apart**. `roof_pitched` sits near the shallow bottom of
the valley (3.65 px) only because its principal point is pinned at the image centre. That RMS is not
evidence about the roof. Up the valley the roof climbs about 0.16 ft per degree at the coping.

## 2. Two checks the fits never saw

**The print's plumb lines.** A tilted camera makes vertical lines lean toward each other going up, by
an amount that grows with distance from the image centre. A level camera keeps them parallel.
Three downpipes run far enough down the print to measure (`plumb_lines` in readings.json). Each was
tracked row by row with a window that re-centres on each find, and fitted as a line. Going up, each
leans to the right by:

| downpipe | u | lean (du/dv) |
|---|---|---|
| at the foot of the north gable, east of the carriage door | 500 | -0.0272 ± 0.0020 |
| on the NW corner | 1090 | -0.0155 ± 0.0010 |
| on the west wall at the south gable's foot | 1494 | -0.0037 ± 0.0025 |

The three leans fall on one line across the frame: they converge, so the camera is tilted. But they
spread 0.024 between the outer two, where `roof_pitched` predicts 0.060 and `roof_level` predicts
none. The tilt that fits all three best is **2.6 degrees** (plumb RMS 0.0038). Measured the same way,
`roof_pitched` scores 0.0169 and `roof_level` 0.0096. Two other edges were tried and left out, because
their lean moved with the search window: the house chimney's east arris and the dark mass beyond
the stable. read_fits.py says why.

**The other photograph.** The coping apex and the cupola are rigid, and HABS photograph 1 (1963)
sees both. T-2758's doorway fits of that print read the coping apex at **38.07-38.62 ft**, and its
doorway alone, used as a ruler, gives 38.77. This print reaches that height, within the picks'
±0.3 ft, only at tilts of **0-4 degrees** (38.25-38.90). `roof_pitched` reads 39.54, 0.9 ft over
HABS 1's highest fit. The coping is the check because it lies on the doorway's own face (S 0), where
both cameras were fitted. The cupola's apex, read at the model's S 14.6, agrees the same way
(46.45-47.42 ft against HABS 1's 45.51-46.29 ft), but its place on S is not settled, so it is read
and not used to gate.

Both checks land in the same place, a tilt of about 2-3 degrees. That is a view camera tipped
slightly up, with its front raised about 220 px (principal row 872 at 3 degrees, against the
image centre's 652.5).

## 3. The roll foot through the cameras that hold

`read_rollfoot.py` runs T-3080's `read_slope.py` unchanged through every valley camera and reports the
roll foot and eave as T-3096's acceptance does. Read on PR #1272's rebaked GLB (head 0e13709;
`glb_sha256` in rollfoot-readings.json), it reproduces T-3096's own numbers for the two committed
fits exactly. Print over model, in metres, on the three counted columns:

| camera | roll foot | eave |
|---|---|---|
| tilt 0 (`roof_level`) | -0.25 / -0.13 / -0.05 | -0.22 / -0.25 / -0.19 |
| tilt 2 | -0.12 / +0.01 / +0.08 | -0.22 / -0.25 / -0.19 |
| **tilt 3** | **-0.06 / +0.07 / +0.15** | -0.21 / -0.24 / -0.18 |
| tilt 4 | +0.01 / +0.14 / +0.22 | -0.19 / -0.22 / -0.16 |
| tilt 5 | +0.07 / +0.20 / +0.28 | -0.16 / -0.19 / -0.13 |
| tilt 6 | +0.12 / +0.26 / +0.34 | -0.13 / -0.15 / -0.09 |
| tilt 8 (`roof_pitched`) | +0.21 / +0.35 / +0.44 | +0.03 / +0.01 / +0.08 |

Every tilt from 0 to 5 degrees puts the roll foot within 0.3 m of the model's on all three columns,
and the eave within 0.26 m. The band both checks admit, 0-4 degrees, lies inside that. So does the
best single camera, at 2-3 degrees (-0.12 to +0.15 m). The course count is the print's own,
41.7-43.9, through every camera. **T-3096's roll-foot acceptance is met by the Cornell print.** The
"fifth fit" that could not be met was the 8-degree camera, which the print's own verticals and the
other photograph both rule out.

## 4. The cupola (T-3031)

T-3031 read the cupola through `roof_pitched` (`tools/glessner_cupola_read.py`), held to the coping
apex where each print draws it. Refitted through every valley camera with T-3031's own picks
(`cupola_t3031`), the joint fit of both prints reads the eave at 41.83-41.92 ft and the apex at
47.85-48.27 ft from 0 to 9 degrees. The build has 41.9 and 48.2. The fit is a little better at low
tilt (joint RMS 4.75 px at 0 degrees, 5.03 at 3, 5.37 at 8). Its centre on S moves from 14.7 to
14.2 at 3 degrees, against the built 14.6: 1.8 of T-3031's one-sigma (0.23 ft), about 0.13 m. That is
inside the reading's noise, and T-3096's ridge runs into the cupola's west face only 0.14 m inside
its north side, so it is not moved on this. **The cupola record stands under any admissible fit.**

## What this does not change

- No geometry and no confidence. `data/comparisons/glessner/stable-roof-heights.json` (T-2758) and
  `stable-cupola.json` (T-3031) stay as they are. They are dated readings, and this reading sits
  beside them. A later tool that wants one Cornell camera for the stable's roof should take the
  3-degree valley camera from readings.json, or walk the valley itself, rather than `roof_pitched`.
- HABS 1's eave reading (0.39-0.45 m under the model in its eye-height and lean fits) is unchanged by
  this ruling and was outside T-3096's question.
- The rollfoot readings stand on PR #1272's GLB. On a tree without that rebake, `read_rollfoot.py`
  reads the old ridge, and its `glb_sha256` will say so.

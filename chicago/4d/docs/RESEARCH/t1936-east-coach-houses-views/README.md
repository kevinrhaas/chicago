# The east side's alley buildings, 18th to 20th Street, in the published app — front, oblique, rear and roof views (T-1936)

T-1936's acceptance 3 asks for the refined buildings read in the actual browser result from repeatable front,
oblique, rear and roof stands at 1280x800 and 390x780, with scene load, mesh and draw/frame costs. The four
alley buildings T-1936 refined (`coleman_ames_house_1811_prairie_coach_house`,
`sears_meeker_house_1815_prairie_coach_house`, `doane_house_1827_prairie_coach_house`,
`marshall_field_house_1905_prairie_coach_house`) are read here.

`node tools/qa_t1936_coach_houses.mjs` (after `tools/publish.sh`; `QA_VIEWPORT=desktop|mobile`,
`QA_PART=a|b`, `QA_FRAMES=3`) boots the actual published `/1904/` app, enters it, sets the detail tier, and
stands the camera at four places in scene-local metres (east, north, height over the ground there), each
looking at a target. It is `tools/qa_k01_t3283.mjs` with these buildings' ids and stands, and a frame count
you can set: at 12 timed frames one part did not finish inside the 600 s foreground cap on this runner's
software GL, so these readings time 3 frames a stand (`frames_timed` in the JSON).

| stand | eye | target | what it shows |
|---|---|---|---|
| front-yards | 1432, -3283, 32 | 1461, -3296, 3 | the yard (west) fronts from over the houses' back yards: the Doane coach house's cream front and wing, Marshall Field's mansard stable beyond |
| oblique-alley-north | 1458.4, -3258, 1.7 | 1466, -3320, 4 | down the Prairie–Calumet alley from its north end: the brick coach houses on the right, the Doane gable and the Field stable's spirelet down the alley |
| rear-alley-south | 1471, -3375, 1.7 | 1463, -3320, 5 | up the alley from the south: the Field stable's east face, its bracketed cornice and mansard dormers |
| roof | 1500, -3250, 60 | 1461, -3300, 0 | the four roofs from the air over the alley |

| viewport | detail | load to ready | JS heap after GC | the four buildings' GLBs | page errors | failed requests |
|---|---|---|---|---|---|---|
| 1280x800 | full | 75.6 s | 84.3 MB | 4 files, 0.114 MB | 0 | 0 |
| 390x780 | light | 47.7 s | 111.0 MB | 4 files, 0.114 MB | 0 | 0 |

| stand | desktop triangles | desktop draw calls | desktop frame (ms) | mobile triangles | mobile draw calls | mobile frame (ms) | within budget |
|---|---|---|---|---|---|---|---|
| front-yards | 1,406,590 | 1,598 | 6453.3 | 423,903 | 1,318 | 2892.4 | yes |
| oblique-alley-north | 2,792,838 | 5,774 | 12248.0 | 790,573 | 3,622 | 2555.5 | yes |
| rear-alley-south | 4,407,524 | 3,978 | 12915.2 | 1,000,647 | 3,428 | 2630.1 | yes |
| roof | 2,955,263 | 2,646 | 9148.3 | 1,598,204 | 3,887 | 5284.0 | desktop yes, **mobile no** |

Frame time is the median of three renders each waited on with a one-pixel read, on this machine's software GL —
a relative reading, not a device claim. The raw readings are `browser-validation-after-<viewport>-<part>.json`.

## The one red reading: the mobile roof stand

From 60 m over the alley at the light tier the scene draws 1,598,204 triangles against the light budget's
1,270,000 (draw calls 3,887 of 7,800). It is not these buildings': their four GLBs are 0.114 MB together, and the
same stand draws the 18th Street corner below it — the 1800 Calumet palm house, the Pullman glasshouse ranges and
their planting, and the parkway's trees. T-3283's roof stand over 1900-2000 Prairie, 55 m up, drew 479,623 at the
same tier. It is filed as T-3312, a performance follow-up, rather than counted a pass.

## What these views do not settle

The pictures' own match records (`data/reference_views/doane_house_1827_prairie_coach_house/`,
`data/reference_views/marshall_field_house_1905_prairie_coach_house/`) say what each picture shows and how the
build compares. The 1811 and 1815 alley buildings have no picture; their faces are the draft rules'
(`prairie_draft`), recorded in `docs/LIBERTIES.md`.

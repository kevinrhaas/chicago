# 1923 and 1945 Prairie in the published app — front, oblique, rear and roof views (T-3283)

Piece 3 of T-1908. `node tools/qa_k01_t3283.mjs` (after `tools/publish.sh`; `QA_VIEWPORT=desktop|mobile`) boots the
actual published `/1904/` app, enters it, sets the detail tier, and stands the camera at six places in scene-local
metres (east, north, height over the ground there), each looking at a target:

| stand | eye | target | what it shows |
|---|---|---|---|
| front-1923 | 1398, -3424.4, 1.7 | 1429, -3424.4, 7 | 1923's front square-on from the avenue's west walk |
| front-1945 | 1398, -3452.6, 1.7 | 1431, -3452.6, 7 | 1945's front square-on from the west walk |
| oblique-nw | 1404, -3401, 1.7 | 1430, -3432, 7 | down the east walk from 1919: 1923's porch and stoop, 1945 beyond |
| oblique-sw | 1398, -3482, 1.7 | 1431, -3450, 7 | from 20th Street: 1945's corner and its 20th Street flank, 1923 behind |
| rear | 1472.5, -3437, 1.7 | 1436, -3437, 6 | both houses' rear ranges and their coach houses from the east alley |
| roof | 1472, -3398, 55 | 1431, -3438, 0 | both roofs from the air over the alley |

Each stand: a screenshot (`after-<viewport>-<stand>.jpg`) and the renderer's own stats; frame time is the median
of 12 renders each waited on with a one-pixel read, on this machine's software GL — a relative reading, not a
device claim.

| viewport | detail | load to ready | JS heap after GC | the two houses' GLBs | page errors | failed requests |
|---|---|---|---|---|---|---|
| 1280x800 | full | 39.6 s | 83.5 MB | 2 files, 1.41 MB | 0 | 0 |
| 390x780 | light | 26.0 s | 109.6 MB | 2 files, 1.41 MB | 0 | 0 |

| stand | desktop triangles | desktop frame (ms) | mobile triangles | mobile frame (ms) | within budget |
|---|---|---|---|---|---|
| front-1923 | 1,102,773 | 4588.3 | 420,337 | 1189 | yes |
| front-1945 | 1,052,846 | 5447.9 | 419,814 | 1103.6 | yes |
| oblique-nw | 1,420,694 | 5617.8 | 581,291 | 1396.4 | yes |
| oblique-sw | 2,435,950 | 6660.6 | 576,330 | 1337.7 | yes |
| rear | 1,538,024 | 4910.8 | 543,435 | 1083.5 | yes |
| roof | 1,360,502 | 3620.9 | 479,623 | 1441.4 | yes |

Every stand passed on both viewports: no page error, no failed request, no renderer problem, inside the scene
budget. The raw readings are `browser-validation-after-desktop.json` and `browser-validation-after-mobile.json`.

## What these views do not settle

The pictures' own match records (`data/reference_views/kellogg_house_1923_prairie/`,
`data/reference_views/armour_corwith_house_1945_prairie/`) say what is still open against each picture. 1923: the
porch's paired columns, the scroll-panel fence and the corner bay's width. 1945: the corner block's taller mansard,
the north bay's own dormered mansard, the arched door and the camera's flank fit — the K01 kit lays a round-headed
door only in a stone front and puts dormers only on a square projection's own mansard, so these need kit work, not
record values. Rear and roof faces are reconstructed (no picture sees them) and are recorded in `docs/LIBERTIES.md`.

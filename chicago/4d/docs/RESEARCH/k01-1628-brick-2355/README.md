# 1628 Prairie's main body refined from the district draft to a K01 brick house (T-2355)

Piece 1 of T-1862, which asked for 1626, 1628 and 1630 together. Three houses are more than one
run's demonstration, so it was split by house: 1628 is this ticket, 1626 (with its frame front bay)
is T-2356, and 1630 (the small frame house, which wants a frame kit, not K01's brick) is T-2357.
The draft T-2334 stood is refined **in place**: `house_1628_prairie` keeps its id, its traced
main-body rectangle (12.25 m deep, 6.0 m along Prairie) and its placement, and its archetype changes
from `prairie_draft` to `k01_frontage`, the plain brick front T-2341 taught the kit for 1608. The
draft rules' `skip` names `s20-1628-f`, so the draft builder stands no second building there, and
the frontage row names the house (`house_id`), so its stable keeps `house_1628_prairie_coach_house`.

## What the house is

Read from sheet 20 (T-2328 trace `s20fp-1628-b1`, T-1840 census `s20-1628-f`): three storeys over a
basement ('3B'), brick, the south half of a pair attached to 1626. Built: the K03 common brick on all
four walls; K06 two-over-two sash, under K09 cornice-hood lintels on the two lower storeys and K01's
flat stone lintels on the low third; the K07 door and stoop on the south half (the draft rules' row,
mirroring 1626's north door; 9.69 m to the walk); a K10 bracketed timber cornice; a K04/K05 hip in
painted standing-seam tin; two brick stacks on the ridge; K04 gutters and downpipes. Three windows a
storey on the south wall, over 1630's side yard, two in the rear. **The north wall is the party wall
with 1626 and is blank**, which is what K01 builds on its north side. Liberty
`L-k01-1628-brick-front-2355`; 1628's house is retired from `L-draft-prairie-16-18-west-2334` (its
stable stays there).

## Found on the way: the roof only builds at 30 degrees here

The K05 roof union K01 dresses its caps on refuses most pitch and eave pairs on a plan this narrow
("the hip … does not part two covering planes"), as T-2344 and T-2353 found on 1612 and 1616. Swept
28, 30-33, 35, 36, 38 and 40 degrees by 0.4, 0.5 and 0.6 m eaves: **only 30°/0.5 m and 30°/0.6 m
build**. 30°/0.6 m was taken, 1608's pair. 1616's 34° refuses here.

## Not built

- **The three-storey wing** behind the north part of the rear wall (4.5 m out, v 2.0-6.25 m; the
  draft's `r2`). K01 builds one rectangle, and the draft builder can only skip a whole traced
  building, so the wing is gone from the scene until T-2347 teaches K01 a traced rear wing; the
  finding is written into T-2347. The rear window at 4.1 m stands where the wing joins and becomes
  the opening into it then.
- **A flat roof.** A three-storey pair of this period may as well have stood under flat roofs behind
  the cornice; K01 builds a hip only (T-2350 asks for K05's flat roof). The draft drew a hip too.

## Before and after, the same stands (`tools/qa_k01_t2355.mjs`)

Actual published `/1904/` app; *before* is `dev` at 564eb5d11 (the draft), *after* this branch.
Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front (across Prairie), oblique
from the south and north walks, rear (1628's own yard), roof (the air). 0 page errors and 0 failed
requests on all four runs; every stand `withinBudget`. Frame times are software GL on the runner, a
relative reading, not a device claim.

| | load to ready | JS heap | draw calls | triangles | frame (median of 12) |
|---|---|---|---|---|---|
| desktop before → after | 39.9 → 26.0 s | 25.8 → 26.0 MB | 80-107 → 90-117 (+10) | 1.607-2.942 M → 1.638-2.972 M (+31 k) | 2.83-6.20 → 2.89-5.90 s |
| phone before → after | 19.2 → 15.1 s | 25.7 → 25.9 MB | 46-73 → 57-83 (+10/11) | 247-470 k → 277-500 k (+31 k) | 0.88-1.41 → 0.72-1.12 s |

The master is 2.56 MB and the web derivative 0.94 MB. Load swings by seconds between runs on this
runner and neither the fall nor a rise is a claim. K01 has no light derivative yet, so the phone's
light tier draws the full assembly: +10 draws and +31 k triangles, the order of 1608, 1612 and 1616.

Screens: `before-*.jpg`, `after-*.jpg`; readings: `browser-validation-before.json` (both viewports)
and `browser-validation-after-{desktop,mobile}.json`.

## Limits

- No photograph, plate or description of 1628 or of the pair has been read; every form is the kits'.
- 1626, its partner, is still the draft until T-2356, so the pair does not yet match across the
  party wall.
- K01 builds a hip roof only, and windows on the south wall only.

# 1616 Prairie's main body refined from the district draft to a K01 brick house (T-2353)

Piece 1 of T-2345 (itself piece 2 of T-1860). T-2345 asked for the main body and the attached
range together; the range needs a builder K01 does not have yet, so it was split off as T-2354
(see "Not built"). The draft T-2334 stood is refined **in place**: `house_1616_prairie` keeps its
id, its traced main-body rectangle (23.5 m deep, 6.5 m along Prairie) and its placement, and its
archetype changes from `prairie_draft` to `k01_frontage`, the plain brick front T-2341 taught the
kit for 1608. The draft rules' `skip` names `s20-1616-f`, so the draft builder stands no second
building there, and the frontage row names the house (`house_id`), so its stable keeps
`house_1616_prairie_coach_house` byte for byte.

## What the house is

Read from sheet 20 (T-2328 trace `s20fp-1616-b1`, T-1840 census `s20-1616-f`): two storeys and a
half over a basement ('2½B'), brick. Built: the K03 common brick on all four walls, K06
two-over-two sash under K09 cornice-hood lintels, the K07 door and stoop on the north half (the
draft rules' row; 9.26 m to the walk), a K10 bracketed timber cornice, a K04/K05 hip in painted
standing-seam tin with one gabled street dormer for the half storey (as 1612 next door), two
brick stacks on the ridge, K04 gutters and downpipes. Five windows a storey on the south wall, two
in the rear; the north wall is blank, as K01 builds it. Liberty `L-k01-1616-brick-front-2353`;
1616's house is retired from `L-draft-prairie-16-18-west-2334` (its stable stays there).

## Found on the way: the roof only builds at 34 degrees here

The K05 roof union K01 dresses its caps on refuses most pitch and eave pairs on this plan ("the
hip … does not part two covering planes"), the same failure T-2344 met on 1612. Swept 28-40
degrees by 0.30-0.60 m eaves, with and without the dormer: without it 17 pairs build; **with it
only 34°/0.50 m and 34°/0.60 m do**. 34°/0.50 m was taken. 1612's 32° refuses here.

## Not built

- **The one-storey brick range** behind the north end of the rear wall (about 2.5 m out, 1.5 m
  along; the draft's `r2`). K01 builds one rectangle. The draft builder can only skip a whole
  traced building, not keep one of its parts, so keeping the range standing as a draft would
  need a "remainder" mode in both the builder and `draft_emit`. That is T-2347's ground (teach
  K01 a traced rear wing), so the range is **T-2354**, after T-2347. It is gone from the scene
  until then; it was a 2.5 x 1.5 m one-storey box at the back of the lot.
- **The 1911 sheet's frame bay at the north-east corner.** The trace fits no part to it and the
  draft did not stand it; a frame bay on a brick front is as likely a later addition.

## Before and after, the same stands (`tools/qa_k01_t2353.mjs`)

Actual published `/1904/` app; *before* is `dev` at ea3f1c59c (the draft), *after* this branch.
Desktop 1280×800 at full detail, phone 390×780 at light. Stands: front (across Prairie),
oblique from the south and north walks, rear (1616's own yard), roof (the air). 0 page errors and
0 failed requests on all four runs; every stand `withinBudget`. Frame times are software GL on
the runner, a relative reading, not a device claim.

| | load to ready | JS heap | draw calls | triangles | frame (median of 12) |
|---|---|---|---|---|---|
| desktop before → after | 25.2 → 37.9 s | 25.3 → 25.5 MB | 77-109 → 87-119 (+10) | 1.565-2.919 M → 1.603-2.956 M (+37 k) | 2.79-5.99 → 2.90-6.10 s |
| phone before → after | 14.0 → 14.2 s | 25.3 → 25.5 MB | 44-49 → 54-59 (+10) | 231-247 k → 268-284 k (+37 k) | 0.75-1.17 → 0.80-1.22 s |

The master is 2.91 MB and the web derivative 1.00 MB (the draft's were 179 kB and 31 kB). Desktop
load swings by seconds between runs on this runner and the rise is not a claim. K01 has no light
derivative yet, so the phone's light tier draws the full assembly: +10 draws and +37 k triangles,
the same order as 1608 and 1612.

Screens: `before-*.jpg`, `after-*.jpg`; readings: `browser-validation-{before,after}-{desktop,mobile}.json`.

## Limits

- No photograph, plate or description of 1616 has been read; every form is the kits'.
- K01 builds a hip roof only, and windows on the south wall only.

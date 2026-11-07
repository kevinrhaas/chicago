# T-3286 — a far shadow level of detail for structures

T-3285 left Full's far views of the Prairie district at 5.4–7.3 M triangles against Glessner's
4.7 M inspection ceiling, carried by a declared far-view allowance (7,325,000 / 8,500). Its
reading was that the sun's pass draws every Prairie house whole inside its 240 m box at any
distance, and it named this ticket as the allowance's retirement.

## What the sun's pass was drawing

Published dev + nothing, desktop Full, Prairie 60 m E / 120 m S of Glessner (the worst far
stand): the structures' sun pass was **3,080,120** of the frame's 7.29 M triangles, in 1,191
multi-draw entries. No piece is small. A house is many pieces (Glessner alone is about 3,000
instances in 15 batches), and at that stand the pieces span 16–64 px on screen. Leaving small
pieces out of the sun's pass would save about 10,000 triangles. What a far piece can leave
out is its fine relief: rustication, mouldings, frames and courses measured in millimetres,
when the shadow map's texel at `full` is 0.117 m.

## What changed

`renderers/web/js/far-shadow.js`. At load, each heavy piece gets a **shadow twin** made by
vertex clustering. Its vertices are pooled in 6 cm cells (a pool never mixes two confidence
values, so the depth material's dither stays where it was). Each pool becomes one vertex at
its centroid, and a triangle whose corners do not land in three different pools is dropped.
A twin is kept only when it has at most half its piece's triangles and at least 500 fewer.
In 1904 that is 334 pieces.

In the sun's pass, a piece is swapped for its twin only where the twin's worst-case edge
movement fits under 1 px. That movement is √3 × 6 cm (the farthest a centroid sits from
any point it stands for) over the sine of the sun's height. It is projected at the nearest
view depth where the piece's shadow can land: the piece's sphere swept down the sun to 30 m
below its base, as `shadow-casters.js` sweeps it. Nearer than that, or with the sun too low,
the piece casts whole. The colour pass never draws a twin. `?farshadow=0` turns it off.

It is an LOD, not a proof, so `tools/qa_t3286_far_shadow.mjs` reads every pixel of each
held frame back off and on. It holds the change to 1 pixel in 1,000, and to 1 in 10,000
for changes over 8 levels. A positive control (no structure casting at all) shows that each
frame has structure shadows on screen.

## Measured (published /1904/ + this branch, Full)

| stand | off | **on** | twins cast | px changed (>8) / frame | no structure casting |
|---|---:|---:|---:|---:|---:|
| desktop, alley from the north (T-1932's) | 5,539,477 | **4,648,930** | 201 | 0 / 1,024,000 | 119,170 |
| desktop, 18th 150 m W | 6,216,086 | **5,195,660** | 244 | 2 (0), max Δ 2 | 2,086 |
| desktop, Prairie 60 m E / 120 m S | 7,294,865 | **6,650,853** | 215 | 0 | 154,876 |
| desktop, Prairie front 40 m E | 3,766,663 | 3,766,663 | 1 | 0 | 39,230 |
| desktop, Prairie 38 m E / 30 m S (T-3146's) | 4,749,465 | **4,613,974** | 111 | 0 | 68,328 |
| desktop, over the roof | 4,135,429 | **4,019,797** | 26 | 0 | 3,523 |
| mobile, alley from the north | 5,421,138 | **4,446,393** | 231 | 0 / 304,200 | 83,102 |
| mobile, 18th 150 m W | 5,228,965 | **4,382,751** | 295 | 9 (0), max Δ 5 | 790 |
| mobile, Prairie 60 m E / 120 m S | 6,997,527 | **6,205,942** | 257 | 108 (10), max Δ 16 | 39,231 |
| mobile, Prairie front 40 m E | 3,265,279 | 3,219,309 | 36 | 0 | 21,233 |
| mobile, Prairie 38 m E / 30 m S | 3,421,546 | 3,328,519 | 185 | 10 (0), max Δ 4 | 18,039 |
| mobile, over the roof | 3,607,237 | 3,367,217 | 52 | 0 | 41,230 |

Draws: a swapped piece can split a coalesced run in the sun's pass. The worst was +27 (the
desktop alley, 8,065 → 8,092), and over the roof the count went down (7,806 → 7,800, back
inside the 7,800 ceiling). Files: `browser-validation-{desktop,mobile}-{far,near}.json`.

Inside the 4.7 M ceiling now: the alley from the north (both viewports), 18th 150 m W on
the phone, and T-3146's Prairie 38 m E / 30 m S stand. T-3285 had found that last one
15,720 over.

## The allowance, re-based down and not retired

By the rule it was set with (the worst far stand + T-0672's 18,059, rounded up to 5,000):
6,650,853 + 18,059 → **6,670,000** triangles, down from 7,325,000. Draws stay at **8,500**
(the alley's 8,092 + about 5%). It is not retired. The Prairie stand 60 m E / 120 m S and
18th 150 m W on the desktop still read over 4.7 M. At the Prairie stand, 4.2 M of the
6.65 M is not the structures' sun pass. It is the colour pass of the row in view, and no
shadow LOD can reach it.

## Cost

- **GPU and heap:** 355,080 triangles and 291,609 vertices of twins are added to the
  structure batches. At 16 bytes a vertex and 12 an index triple that is about **9 MB** of
  buffers, held on the GPU and in the batch's CPU copy. This goes against T-3173's 1904
  desktop memory reading, which is already over its ceiling. The trade is ~0.6–1.0 M
  triangles off every far stand.
- **Boot:** the twins are cut in 450–820 ms of main-thread time on this runner (most of it
  inside the town's existing load checkpoints, which yield between pieces). Ready-to-walk
  time was unchanged within run-to-run noise (26–66 s across runs here, sharing four cores).

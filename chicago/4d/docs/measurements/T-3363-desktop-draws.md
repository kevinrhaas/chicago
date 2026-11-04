# T-3363 — 1904 on the owner's desktop: where the draws went, and two that came back

**The reading that asked.** The owner, 2026-11-03, Read frame pacing in 1904 on his Mac
(Chrome 156, 1381x819 at ratio 1.1, Scene detail **Light**, Sharpness Low):

```
walk    fixed   mean 70.5 ms  p95 112.5   driver draws 5065 (max 6194)
turn    fixed   mean 48.3 ms  p95 126.9   driver draws 2579 (max 6236)
flight  fixed   mean 145.9 ms p95 159.2   driver draws 5282 (max 5507)
```

Adaptive cut the resolution to 0.67 and no move fell: the frame is not fill-bound. It
follows the draw count (turn, at half the walk's draws, is two thirds of its time).

**How it was read.** `tools/measure_pose_draws.mjs` and a screenshot twin of it, at his
viewport (1381x819, desktop, ratio 1), Read frame pacing's own poses (`SCENE_POSES`,
t = 0), on the branch's renderer against dev's published data (dev @ dacc6364), the same
build before the change as the control. Chromium headless, SwiftShader; the GL's own draw
count, not three's.

## Where the draws went

- **Full, flight: the parkway elms were 2,028 of 4,583 draws for 2 % of the triangles.**
  A grown wood (tree-instances.js) is a BatchedMesh with one instance a stem, and three
  submits a BatchedMesh as one multi-draw ENTRY a kept instance: every elm is a wood
  draw and a leaf draw in the view, and again in the sun's pass. On 2026-10-20 (T-2927)
  the same pose drew about 400 for the elms; the 1,121 sun draws are T-2948's
  `castFar` and the far ring's elms added since.
- **Light: the structures draw more than at Full.** Where a scene carries Glessner's
  inspection model, Light and Balanced cut every structure into 4 m x 2 m cells
  (T-2219, main.js `spatialCells`) so a phone's courtyard view culls what it cannot see.
  The cells are a draw each that T-2927's join cannot reunite past a culled one: at the
  flight pose the structures were 4,076 draws at Light against 2,207 at Full, and
  walking 4,666. One blended batch (the glass) was 972-1,215 draws for 10-13k
  triangles: three sorts a blended batch back to front entry by entry, so once cut, the
  glass was sorted cell by cell and almost no two cells of one pane stood together.

So the owner's guess was half right: Light does not skip anything the GPU does, but on
1904 it is the tier that cuts every house into cells, and on his machine a draw costs
more than the triangles the cells save.

## What changed

1. **One instanced draw for every copy of one template** (`batch-instance.js`). After
   three has culled a grown wood's batch for the pass, the kept entries are grouped by
   the template they draw and sent as one `multiDrawElementsInstancedWEBGL` entry each.
   The batching shader reads the stem as `table[table[gl_DrawID] + gl_InstanceID]`.
   The stems drawn, their per-stem cull in the view and the sun, their matrices and
   their dissolve (T-2948) are unchanged; `renderer.info` still counts every instance's
   triangles. Street elms, front-yard trees and the 1835/1812 timber all draw through it.
2. **A blended cell batch sorted by piece** (`batch-coalesce.js sortCellsByPiece`): the
   pieces back to front by the mean depth of their kept cells, each piece's cells in
   their own order — the order Full draws that glass in — so its touching cells join.

## Before and after (GL draws a frame; triangles from `renderer.info`)

| tier  | pose   | before | after | triangles (both) |
|-------|--------|-------:|------:|-----------------:|
| Light | walk   |  6,086 | 3,953 | 2,565,011 |
| Light | turn   |  2,605 | 1,868 |   901,073 |
| Light | flight |  5,126 | 2,908 | 2,375,881 |
| Full  | turn   |  4,535 | 1,019 | 3,784,296 |
| Full  | flight |  4,381 | 2,407 | 5,378,858 before, 5,378,582 after (the haze) |
| Full  | flight (first boot, no tier switch) | 4,583 | 2,465 | 5,408,472 |

Full's walk was read straight after a Light-to-Full switch, before the elms were regrown
for Full, so it drew no trees in either build (2,747 both) and is left out.

The table is SwiftShader's draw count, not the owner's milliseconds. On his reading,
frame time followed draws at roughly 13-15 ms a thousand walking, so the walk's 2,100
fewer draws at Light is the size of change to look for; his own re-reading is the
measurement.

## Pixels

Each pair is the same pose with the clock frozen and every wind uniform pinned to 0
(`setAnimationHold` freezes the wind where each run's boot left it, so two unpinned runs
stand their trees in different sways and differ over every crown).

| pair | pixels that differ |
|------|-------------------:|
| Light walk, dev against dev (two runs of the same build) | 695 (0.061 %) |
| Light walk, dev against this change | 672 (0.059 %) |
| Full flight, dev against this change (no pin: the far trees do not sway) | 5 (0.0004 %) |

The Light walk's differing pixels are the same one-pixel flicker along the public walk's
edge in both pairs: run-to-run noise in the build before the change, not the change.

Two runs of the changed build first read without the front-yard plantings (3,931 draws,
2,561,751 triangles). That is the reading's timing, not the change: the yards regrow
without being awaited after a Scene detail switch (front-yards.js `setDetail`), and 25
frames later the same page draws them (3,953 draws, 2,565,011 triangles, the table's).
A reading taken right after a switch should wait for `frontYards.stats.grown`.

## What is left

- Light's opaque cells: the largest batch is still about 1,800 entries walking. Joining
  across a culled cell would draw that cell's triangles too and spend Light's triangle
  ceiling, which is a phone's promise; not done here.
- On a desktop, Full now sends fewer draws than Light at the turn and the flight
  (1,019 and 2,407 against 1,868 and 2,908), with more triangles and a larger sun map.
  Which tier is faster on the owner's Mac is his reading to take.

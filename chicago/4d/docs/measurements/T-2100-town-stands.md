# Two in-town stands re-posed so their captures show what they judge (T-2100)

T-2092's captures at T-2084's in-town poses showed two of the three as a wall:
`town_backyard` (385, -450, yaw 0) stands against a back wall and frames nothing else,
and `town_south_water_store` (501, -2, yaw 180) stands a metre from the c3_12 / c3_13
fronts and frames one door and one window. Neither shows the yard or the shop front
that T-2085..T-2087 took their visual acceptance from.

## What changed

Two stands are ADDED, under new ids, in `tools/measure_detail_ceilings.mjs` TOWN and in
the copy `tools/measure_still_frame.mjs` keeps:

| id | local e, n | yaw, pitch | frames |
|---|---|---|---|
| `town_yard` | 388, -440 | 0°, -6° | the backs of h1_02 and h1_03 (back walls at n -418.6), the yard ground between them, the woodpile and the post-and-rail fence on the lot line |
| `town_store_front` | 501, 12 | 180°, -4° | the South Water Street fronts from the street: the plank walk, the doors and stoops, the hitching post, Hiram Pearsons' sign and the street ground before them |

**The old ids keep their names and their coordinates.** Every number already taken there
is a baseline — T-2091's and T-2092's triangles, T-2099's still frame, and the still-frame
gate's own ceilings (`tools/still_frame_ceilings.json` stands on `town_backyard`) — and a
moved stand would have re-based all of them without saying so. The two new stands are a
new baseline, read below.

Captures: `t-2100-town-stands/`, dev at the tier the page boots into, both viewports,
old and new side by side (`dev-<viewport>-<stand>.jpg`).

## The new stands beside the old, on dev

Read 2026-10-08 on dev @ 12cb2f3d4 with `node tools/measure_detail_ceilings.mjs --town
--flora --stepped --stands town_backyard,town_yard,town_south_water_store,town_store_front`,
cut by `--only` and `--levels` so each call finished inside 600 s. `flora` is the frame
drawn once with the `flora` group hidden (triangles / calls). Rows in
`t-2100-town-stands.json`. The `light` readings were taken twice on desktop and came back
identical to the triangle.

| viewport | tier | ceiling | `town_backyard` | `town_yard` | `town_south_water_store` | `town_store_front` |
|---|---|---:|---:|---:|---:|---:|
| desktop | full | 3,160,000 | 3,037,625 · 304 · fl 10,730 | 3,018,126 · 303 · fl 9,462 | 2,470,626 · 278 · fl 22,181 | 2,494,164 · 278 · fl 16,991 |
| desktop | balanced | 2,290,000 | 2,269,319 · 293 · fl 4,460 | 2,263,449 · 292 · fl 4,553 | 1,967,427 · 276 · fl 2,954 | 1,989,577 · 274 · fl 3,686 |
| desktop | light | 1,005,000 | 882,547 · 79 · fl 1,482 | 868,108 · 78 · fl 1,842 | 745,679 · 81 · fl 1,356 | 758,254 · 83 · fl 2,270 |
| mobile | full | 3,160,000 | 2,582,837 · 256 · fl 10,730 | 2,581,255 · 258 · fl 9,462 | 2,164,250 · 253 · fl 22,181 | 2,181,755 · 254 · fl 16,991 |
| mobile | balanced | 2,290,000 | 1,930,581 · 250 · fl 4,460 | 1,919,928 · 250 · fl 4,553 | 1,698,751 · 251 · fl 2,954 | 1,724,150 · 250 · fl 3,686 |
| mobile | light | 1,005,000 | 705,527 · 72 · fl 1,482 | 696,006 · 72 · fl 1,842 | 614,032 · 72 · fl 1,356 | 625,463 · 74 · fl 2,270 |

(cells: triangles · draw calls · flora triangles)

- **The yard stand costs what the wall stand cost, within 2 %** at every tier and
  viewport (desktop `full` 3,018,126 against 3,037,625). Ten metres further into the same
  yards, looking the same way, the frustum takes in nearly the same town; what changed is
  that the nearest thing in it is no longer a wall.
- **The store stand costs 1 to 2 % more** (desktop `full` 2,494,164 against 2,470,626):
  stepping back 14 m brings the neighbouring fronts into frame. Its flora share is
  smaller at `full` (16,991 against 22,181) and larger at `balanced` and `light`; this
  reading does not say which plants account for either.
- **Every reading is inside dev's ceilings.** The nearest is desktop `balanced` at the yard,
  2,263,449 of 2,290,000 (98.8 %) — the same margin the old stand already ran at.

## What this is not

Not a gate change: these stands are reported beside T-0135's five and never counted in
the exit tally, as `--town` always was, and `still_frame_ceilings.json` still holds the
still frame at `town_backyard`. Not a change to the town: nothing in the scene moved.

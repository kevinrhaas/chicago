# T-3222 — 1638 Shortall-Gregory Prairie's front walk

Piece 2 of 2 of T-3215 (the pictured 1600-block houses' walks), under T-3204 and the owner's ask of
2026-10-27: *"make sure ... you have their walkways to their house correct and the front
gate/fence/borders"*. 1638 is the block's K16 timber house, and the K16 generator could lay no walk:
its porch stair came down onto bare ground, the gateway between its two gate piers opened onto lawn,
and `tools/check_house_walks.py` carried it on its PENDING list with "no walk".

**Acceptance, stated before the work:** a K14 front walk from the two-pier gateway along the fence's
back to the porch stair, laid by the K16 generator and written into the GLB so the walk gate reads
it. The house comes off PENDING because it passes the gate, not because the rule was loosened. The
walk lands where the Chicagology photograph's camera shows it.

## What was built

- **`k16_timber.yard_walk`**, for a record whose form names a `yard` (validated by
  `k16_timber_params.yard_errors`): K14's own router, `k14_yard._route`, takes the walk out from the
  stair's foot, turns it along the boundary's back 0.45 m clear of the plinths and brings it out
  through the opening between the plinths' faces. Its flags are laid leg by leg, as
  `k14_yard.dress_open` lays them, toned by the condition kit's `path_wear` (front_walk), in the
  plinths' stone (`walk_flag` → `fence_stone`, so no new material).
- **The GLB's node extras** for a K16 house with a yard carry `k16.components`: the
  `k14.yard.front_walk` instance (legs, sockets) and the street fence's two runs either side of the
  gateway (`end_a`/`end_b`), which `check_house_walks.py` already treats as a boundary run. Two new
  self-test cases show the gate reading a K16 front: a walk through the gateway passes, and one
  across a fence run is refused (15 of 15 cases).
- **Inputs:** `mesh_inputs` hashes `k14_yard.py`, `k14_condition.py` and the K14 kit's data for a
  K16 house with a yard alone. The new `yard` field on the K16 parameters moves the other five K16
  houses' input hashes; each re-emits byte-identical.

1638's legs (house frame: u out of the front, s north from its south end):

| leg | u (m) | s (m) | along |
|---|---|---|---|
| out from the stair's foot | 5.02 – 8.57 | 5.93 – 7.13 | u |
| along the fence's back | 8.57 – 9.77 | -0.13 – 7.13 | s |
| out through the gateway | 9.77 – 10.80 | -0.13 – 1.025 | u |

13 flags, 1.2 m wide (1.155 m in the gateway, which is 1.255 m clear between the plinths).

## Against the photograph

`tools/photo_match.mjs` through the camera T-2523 solved
(`../photo-match/shortall_gregory_house_1638_prairie_front/chicagology_front-side-by-side.jpg`): the
print shows pale ground in the gateway between the two piers and at the foot of the stair behind the
fence. The render's flags fill the gateway between the plinths and show under the stair's bottom
step. Everything between is behind the hedge in the print, so the walk's line along the fence is
reconstructed (L-k16-1638-walk-3222). The match record keeps its verdict, `matches`, with the walk
added as a fixed difference.

## In the app

`tools/qa_house_walks_t3222.mjs` against the published `/1904/` app (after) and the dev preview
(before), 1280×800 full and 390×780 light, with zero page errors on both viewports:

- **stills** (`stills/`): `front`, `gate` (from the public walk outside the gateway) and `stair` (from
  the turn). Before, the gateway opens onto lawn; after, the flags come in through it and turn north
  behind the fence.
- **ground:** the app's terrain rises 2–21 mm over the house's bed at 118 points along the legs,
  less than the flags' 0.06 m, so the walk is never under the ground and no `grade_m` is needed.
- **on foot:** the app's walker, sent from the public walk through the walk's two corners, reaches
  the stair's foot (0.13 m off it) with no blocked frame. **The same is true before**: the walker
  never treated the lawn or the fence line at the gateway as solid. So this reading shows the new walk
  puts nothing in a visitor's way. It does not show a fix; what was missing was the walk itself.

The front-yard planting (T-3203) still clears the new walk (`plant_prairie_1904_front_yards.py
--check`), so `data/front_yards/1904.json` is not rewritten here.

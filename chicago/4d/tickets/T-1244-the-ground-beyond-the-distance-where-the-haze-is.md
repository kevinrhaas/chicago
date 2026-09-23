---
id: T-1244
title: The ground beyond the distance where the haze is total stops being submitted, and the eight days that put the town over are named with a measured before and after
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1154
opened: 2026-09-17
closed: 2026-09-17
pr: 1397
claimed_by: run 9/17/2026, 8:35:35 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T14:03:55.961Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35224144036
---

The ground beyond the distance where the haze is total stops being submitted, and the eight
days that put the town over are named with a measured before and after.

Piece 1 of 2 of **T-1154 — The five downtown stands are over every scene-detail ceiling at
both viewports, and the town has been over since some point after 6 September**, split
because the parent needed more than one run's demonstration to be done. The parent keeps the
full ask and its links; this ticket owns one slice of it. Piece 2 is T-1239.

**The bisect, and it needed no browser.** `tools/dev-smoke-state.json`'s newest desktop
part-4 reading is a PASS of 2026-09-06T00:44:54Z. The committed heightfield meta at every
commit that moved it, in those nine days:

| commit | ticket | samples | modelled box | |
| --- | --- | ---: | --- | --- |
| `ebea45208` | T-0939 | 809 x 321 | 720 x 800 m | the state the PASS was taken on |
| `ca5b071aa` | T-0219 | 809 x 373 | 2,020 x 930 m | the heightfield reaches Madison Street |
| `aedc409e4` | T-1123 | 809 x 661 | 2,020 x 1,650 m | the ground reaches Kinzie's Addition |
| `9b232f7ba` | T-0464 | 809 x 1,969 | 2,020 x 4,920 m | the ground reaches Twenty-Second Street |

6.1 times the area at an unchanged 2.5 m sample. And priced, on the published mirror of
`dev`, by the new `tools/measure_layer_share.mjs` — one scene layer hidden at a time,
`renderer.info` read back, whole-frame figures reproducing
`tools/measure_detail_ceilings.mjs` to the triangle: at Lake and Market the GROUND ALONE is
994,528 of the `light` frame's 1,432,679, which is 169,528 over the whole tier's ceiling
before a single building is drawn, and 96.7 per cent of the entire ground mesh. 569,447 of
that mesh's 1,028,798 triangles are south of local_n -530 — ground that did not exist on
6 September.

**And it is not the culling grid.** T-0466 measured that in the same week
(`data/render/ground_tiling_budget.json`): 12 x 12 buys 58,287 triangles for fifteen draw
calls against the rule in force. What the frustum takes downtown is not badly cut, it is
simply all of it, out to the camera's 3,000 m far plane — and the ground had no distance
rule of any kind, while the furniture has its reach, the wood its horizon cap and the flora
its falloff.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. The nine days are bisected and the change named, with the before and after measured and
   committed. — `data/render/ground_reach.json`, and the instrument that priced it is
   committed with it.
2. The ground carries a distance rule DERIVED rather than chosen: the distance at which the
   scene's own `FogExp2` leaves under one part in 255 of a surface's colour, so beyond it
   the ground provably cannot move a pixel. `sqrt(ln 255) / 0.00125` = 1,883 m, against a
   fog the lighting note already calls total by 1,500 m and a far plane at 3,000.
3. It is a rendering decision and not a claim: nothing un-built, re-graded or moved; the
   heightfield and never the mesh still answers `surfaceHeight` and `walkableHeight`, so
   footing, water, flora roots and every anchored record are untouched.
4. The reach is applied at EVERY tier, because the argument is visibility and not expense.
5. A measured trim at every eye-level downtown stand, with what remains stated and handed
   to T-1239 rather than left implied.

**What this ticket is NOT.** It is not the close of T-1154's own acceptance. The stands are
still over all three ceilings; the reach takes about 45,500 triangles off each eye-level
downtown stand and four off the aerial, because a 5 x 8 grid over a 7,340 x 10,240 m mesh
gives a tile a bounding sphere of 950 to 2,000 m and a nearest-point test at 1,883 m can
only reject the outermost few. Making it bite is **T-1239**, and the ceilings are not moved
by either ticket.

**Links:** T-1154 (parent) · T-1239 (piece 2) · T-0466 · T-0464 · T-1123 · T-0150 · T-1148.

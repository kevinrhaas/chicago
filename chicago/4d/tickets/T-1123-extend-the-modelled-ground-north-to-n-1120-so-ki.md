---
id: T-1123
title: Extend the modelled ground north to n +1120, so Kinzie's Addition and the North Branch's traced banks stand on measured ground
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-14
pr: 1319
claimed_by: run 9/14/2026, 5:37:00 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-14T11:18:43.789Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34833634055
---

Extend the modelled ground north to n +1120, so Kinzie's Addition and the North Branch's traced banks stand on measured ground.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1067**, which measured what stands north of the wall before anything was built, and
filed the build separately because it is one.

`terrain_spec.json` § `box_derivation.n_max` now carries the argument and the cost, and this
ticket is the work it describes. In short: the cap that set +400 was the North Branch's traced
water ending at N +401.6, and that cap is spent — `branches.geojson` carries the channel and
both banks to N +1075.48…+1079.21, the forks to the north line of Wright's survey, and
`shoreline.geojson` carries the north shore and the lake margin to N +1117.30 with the water
polygon at +1121.00. +1120 clears the northernmost traced water by 1.0 m, clears Wolcott
Street's north end (+1029.71) by 90 m, and lands on the existing 2.5 m lattice at row 660 from
`n_min`, so every sample the field already carries keeps its position and only its row index
moves — the property the southern extension (T-0219) was careful to keep.

**What makes it a build rather than a number change**, and the reason it is not one run with
the measurement:

- 809 × 373 = 301 757 samples become 809 × 661 = 534 749. A 77 % larger field, about 1.0 MB of
  `heightfield.bin` against 590 KB, and a ground mesh to match — which is a BAKE, and then the
  publish budget and the draw-call/triangle gates that `smoke_renderer.mjs` holds.
- The 288 new rows are ground this spec argues nothing about. `micro_relief`, `relief_bands`,
  `surface_materials`, `shore_runs` and the flora belts all stop at the present wall. Ground
  generated without them would be a surface with no reasoning behind it, which is the one thing
  this project may not author.
- `data/terrain/north_of_box_reading.json` is the before, already committed and gated; the
  after is the same reading re-derived, and the two printed side by side is the demonstration.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Links:** T-1067 (measured it, and argued the number) · T-0219 (the same move on the south
wall) · T-1060, T-1061 (the Addition's streets and blocks) · T-1062 (the viewpoint that found
it) · `docs/LIBERTIES.md` L237 (what the scene draws off the ground until this lands).

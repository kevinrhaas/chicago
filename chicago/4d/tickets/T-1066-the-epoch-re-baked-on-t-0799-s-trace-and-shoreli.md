---
id: T-1066
title: The epoch re-baked on T-0799's trace, and shoreline.geojson into the terrain staleness hash so a re-trace can never leave the ground behind again
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0800
opened: 2026-09-12
closed: 2026-09-12
pr: 1184
claimed_by: run 9/12/2026, 3:54:43 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-12T09:33:45.333Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34683906824
---

Piece 1 of 2 of **T-0800 — The mouth as built** (ask 4 of its four), split because the parent
needed more than one run's demonstration. The parent keeps the full ask and its links; T-1065
carries the piers, the bar's argument and the reservation and lighthouse checks.

## What this piece found, which is why it is its own ticket

T-0799 re-traced the whole east edge off Wright's full sheet and said, in its own changelog,
that the ground had not moved with it. The ground is CARVED from that trace —
`terrain_spec.json` resolves `harbor_reach_water`, `north_shore_harbor_reach`,
`south_shore_harbor_reach` and `sand_bar_1834` by id, and `terrain_gen.main` loads all three
GeoJSONs into one id table before `build_field` reads them — so the re-trace should have made
the committed heightfield and both GLBs stale the moment it landed.

It did not, and `check.sh` stayed green, because `generators/terrain_inputs.py` excluded
`shoreline.geojson` from the terrain input hash on a premise that had stopped being true:
*"traced evidence that `build_field` does not yet read, so including it would report the
ground as stale for a file that cannot change it."* The one file that had changed was the one
file the gate had been told to look away from.

**Acceptance:** `shoreline.geojson` is in `terrain_inputs_doc`'s `vectors` and the scheme is
bumped (so the manifest re-stamp is a visible, dated event `validate.py` can police); the
epoch's heightfield and both GLBs are re-baked under the pinned Blender and the web
derivatives regenerated from the new masters; the moved cells are counted and bounded — every
one of them east of the re-traced reach, nothing west of it disturbed; `check.sh` green and
the `--for-diff` smoke legs green.

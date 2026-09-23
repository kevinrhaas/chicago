---
id: T-0427
title: The outbuilding shed's overhang keeps climbing, and the ridge model stopped at the wall
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 574
claimed_by: null
blocked_on: null
needs_bake: true
---

The outbuilding shed's overhang keeps climbing, and the ridge model stopped at the wall.

**Found by T-0274 (2026-08-30)**, which repaired the inferred-household parcel's form values,
dealt a D2 shanty a 25.2 degree shed — the steepest this town has ever built — and turned
`tools/measure_ridge_band.py`'s drift assertion red on it at +0.152 m against a 0.15 m
tolerance. The tolerance was not the fault. The model was.

`generators/archetypes/outbuilding._roof` sets a shed's single plane out from `-oh` to
`span + oh` and its `z_at` is linear the whole way, so the plane is STILL CLIMBING when it
reaches the far overhang: the highest point of a shed roof is the high wall top plus
`oh x tan(pitch)`, not the high wall top. `tools/ridge_model.ridge_run_m` returned the bare
span, and its own module note said in as many words that for `outbuilding` "the overhang
adds nothing to the height" — true of the GABLE, whose apex stands over the centre line and
whose overhang falls away from it on both sides, and false of the shed.

The error is `oh x tan(pitch)`: 0.08 m at 12 degrees, 0.15 m at 25. Every shed in the
dataset carried it, and `measure_ridge_band.py` had been absorbing all of it in the
board-thickness tolerance it compares the built GLB against — the largest before this
ticket was 0.1494 m, four ten-thousandths under the limit. The gate was one steeper roof
away from red on work that had nothing to do with it.

**REPAIRED IN T-0274's PR**, because that PR's gate could not go green without it and the
repair is one term on one branch. What was done:

  * `generators/archetypes/outbuilding_params.eave_overhang_m(width, depth)` publishes the
    overhang, which was an expression inside `_roof`. `outbuilding.py` now reads it, so the
    mesh and any model of the mesh ask one function — `outbuilding.py` cannot be imported
    outside Blender, which is why the number lives in the params module beside the door
    table `family_bands.eave_floor` already asks for.
  * `tools/ridge_model.ridge_run_m` returns `span + eave_overhang_m(w, d)` for an
    outbuilding shed, and the module note is corrected.
  * 20 records across all five anonymous parcels moved, because the run is what
    `family_bands.eave_for_ridge` and `pitch_deg` sample against. Re-derived, re-baked and
    published in the same commit.
  * `tools/ridge_band_baseline.json` fell from 16 offenders to **0** — every reconstructed
    roof in the town is now inside the ridge band its own family authors, and the model
    agrees with the built GLB on all 268.

**Acceptance:** `python3 tools/measure_ridge_band.py` reports no model drift and 0 roofs
outside their band; `tools/ridge_band_baseline.json` is empty; `check.sh` green.

**What this ticket does NOT do**, and it is worth a look one day: the same paragraph is
right about `frame_dwelling`, `frame_storefront` and `log_dwelling`, whose private
`_shed_roof` builders grow the plan by a flat 0.25 m — `ridge_run_m` already adds
`2 x GABLE_OVERHANG_M` for those, which is the plan growth and not the slope continuation,
and no committed GLB in this dataset is a frame shed, so nothing can measure which of the
two is right for them.

---
id: T-0212
title: The one A5 roof still dealt a gable takes the shed its family gets everywhere else
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-26
closed: 2026-08-28
pr: 437
claimed_by: run 8/27/2026, 11:35:22 PM CT
blocked_on: null
needs_bake: true
---

The one A5 roof still dealt a gable takes the shed its family gets everywhere else.

`recon_1835_south_a5_044` — a small utility building on the South Division parcel — is roofed with a
GABLE. The other three A5 records in this town (`inf_laundry_north`, `recon_1835_north_a5_011`,
`recon_1835_north_a5_049`) are SHEDS. Nobody chose the difference: which families get a shed was
written out five separate times, once inside each anonymous parcel, and two of the five —
`generate_block_infill.py` and `generate_inferred_infill.py` — retyped the set without A5. Found by
T-0179's sweep while giving that rule one home.

T-0179 gave it that home (`tools/roof_form.py`) and every parcel now reads it, **except for this one
family in this one parcel**, which is held back in `roof_form.AWAITING_BAKE` and named there with
its reason: flipping the roof type moves committed geometry, so the GLB goes stale and
`tools/check.sh` refuses the commit without a bake. `tools/measure_ridge_reach.py` banks the hold at
exactly one entry — it may shrink and may not grow — so no second parcel can quietly opt out while
this waits.

**Acceptance:** `roof_form.AWAITING_BAKE` is empty, `generate_inferred_infill.py --check` is green
with A5 taking the shared rule, `recon_1835_south_a5_044__inferred_1835.glb` is re-baked in the same
commit as the record, and `HELD_BASELINE` in `tools/measure_ridge_reach.py` shrinks to `{}` in the
same commit. A5's shed is already gated as reachable at every footprint in its own band (0 of 441),
so nothing about the specification has to be settled first — this is a bake, not a decision.

**Visible when it lands:** one small outbuilding on the South Division blocks changes from a
two-slope roof to a single slope, matching the other three of its kind.

**Links:** T-0179 (opened this) · L182 · `tools/roof_form.py` · `tools/measure_ridge_reach.py`.

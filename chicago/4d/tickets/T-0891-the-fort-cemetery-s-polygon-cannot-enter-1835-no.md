---
id: T-0891
title: The Fort Cemetery's polygon cannot enter 1835_no_build_ground.json until measure_no_build_ground.py can resolve a ring read off a plate
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-13
pr: 1260
claimed_by: run 9/13/2026, 12:00:37 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T17:28:13.947Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34768935241
---

The Fort Cemetery's polygon cannot enter 1835_no_build_ground.json until measure_no_build_ground.py can resolve a ring read off a plate.

**Acceptance:** (stated before working, and met — one demonstration, never weakened to pass)

1. `tools/measure_no_build_ground.py` resolves a THIRD kind of ring: one read off a plate,
   rebuilt from the corner pixels and the stated transform a committed trace of a raster
   carries, with that trace's own ground corners checked against what the rebuild gives.
   No vertex is authored in `1835_no_build_ground.json`, which is the whole reason the
   Fort Cemetery could not enter it.
2. The Fort Cemetery is a region of that file, off
   `data/traces/harrison_1830_fort_burial_ground.json`, and `--gate` is green.
3. The resolver's refusals are PROVEN to fire rather than asserted: `--self-test`
   fabricates eight breakages against a copy of the real reading (a ground corner edited
   without its pixel, a transform moved under the reading, a ring whose two halves are
   different lengths, and so on) and check.sh runs it.
4. The regions now OVERLAP — the cemetery stands wholly inside the reservation — so the
   total refused area is their union and not the sum of their parts, which would have
   double-counted 1.45 acres. The figure is unchanged at 25.9 % because the union is.

**What it is NOT:** no fabric, no fence, no burial, no count. The parcel is refused ground
with an extent and a grade; T-0882's `refused_as_fabric` still stands unweakened.

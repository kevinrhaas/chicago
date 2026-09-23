---
id: T-1242
title: Trace the 1812 pre-cut shore: the natural southward river mouth, the baymouth bar and the channel behind it, adopted as shore_1812_pre_cut's own bounded geometry
state: done
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0468
opened: 2026-09-17
closed: 2026-09-17
pr: 1399
claimed_by: run 9/17/2026, 8:58:21 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T14:55:10.220Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35229760280
---

Trace the 1812 pre-cut shore: the natural southward river mouth, the baymouth bar and the channel behind it, adopted as shore_1812_pre_cut's own bounded geometry.

Piece 1 of 2 of **T-0468 — Create an e1812 natural terrain epoch for the Fort Dearborn battle landscape**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. `shore_1812_pre_cut` carries its OWN geometry, and the file is DERIVED rather than
   hand-drawn: `tools/derive_shore_1812.py` writes it from `data/terrain/1812_mouth_readings.json`
   (statements only) plus the committed Wright 1834 trace, and re-derives it byte for byte.
2. The 1833-34 cut and the drafted piers are absent. The 1834 lake shore north of the pier
   head is recorded on the state as an EASTWARD BOUND, never adopted as the 1812 line.
3. The mouth is set by a sourced reading, not by an average: Swearingen's 1803 half mile is
   adopted, the tier-2 "near present Madison Street" is kept beside it, and no midpoint exists.
4. Nothing here claims an elevation, and no feature is graded better than `inferred`.
5. `tools/check_shoreline_states.py` gates all of the above, with a self-test per refusal, and
   `tools/check.sh` runs both it and the tool's own `--check`. `./tools/check.sh` is green.

**Not in this piece** (they are T-1243): the terrain spec, the heightfield, the ground and
water meshes, the Fort-to-Eighteenth-Street corridor, and any 1812 height whatsoever.

---
id: T-1473
title: Correct sinking buildings and terrain contact in the Unreal preview
state: blocked-tech
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-1356
opened: 2026-09-20
closed: null
pr: null
claimed_by: null
blocked_on: Current Unreal-capable executor and fixed source/terrain snapshot with web comparison; not claimable by the remote web worker
needs_bake: false
closed_at: null
claimed_run: null
---

Owner-reported defect, 2026-09-20: multiple Unreal buildings sink into the ground. Parent: T-1356. This is a placement bug, separate from the corrected garden fence yaw bug in T-1464.

**Executor: LOCAL / QUALIFIED UNREAL ONLY.** Hold until the current executor can import, render and test the pinned source snapshot. T-1464's fresh project is a valid starting point; bundle automation is not a prerequisite to diagnose this bug. Remote web workers must not claim it based only on access to Python.

## Acceptance — measured correction of the repeated placement defect

1. Inventory the reported class of sinking structures and select named examples on flat ground, slopes, long footprints, fort/garden boundaries and waterfront anchors. Save source ids, coordinates, transforms, mesh bounds, terrain/epoch hashes and comparable web/Unreal views. Separate intended foundations from lost doors, floors or walls. Compare source mesh origin, unit/axis conversion, pivot, terrain sampling and actual rendered terrain; do not presume a universal Z offset is correct.
2. Review the current lowest-of-25-footprint anchoring: it fixed downhill floating but can bury uphill geometry. Preserve correct yaw/zero pitch/roll. Decide a shared, explicit terrain-contact policy for each affected structure type, including footing/plinth or terrain fit only where justified. Preserve water anchors and avoid relocating a whole town merely to hide one defect. Historical geometry changes carry normal confidence/license/provenance rules and shared generator changes, not unexplained Unreal-only edits.
3. Correct the systemic cause and regenerate a bounded representative group, recording remaining affected ids for a same-band successor if needed. Check entry thresholds, ground-floor visibility, wall collision, nearby road grades and bank transitions in normal walking. Verify no new floating structures or tilted fences. Add a regression check measuring the specific failure, not merely restating the placement formula.
4. Package and compare the named viewpoints/routes with the fixed source revision. Record before/after images, measured contact offsets, normal movement and known exceptions. Reuse the corrected policy for later roads/flora imports. Do not close because one screenshot looks better or claim full-town repair if exceptions remain.

**Budget exception:** Owner explicitly requested separate build, placement, flora and navigation follow-ups; roads remain T-1360.

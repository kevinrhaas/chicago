---
id: T-1360
title: Export and validate Chicago street surfaces as the first Unreal scenery parity slice
state: blocked-tech
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-1356
opened: 2026-09-18
closed: null
pr: null
claimed_by: null
blocked_on: Needs T-0252 export contract, versioned bundle, and verified Unreal importer; engine acceptance requires a qualified Unreal runner
needs_bake: false
closed_at: null
claimed_run: null
---

First bounded scenery parity slice: a named street corridor from the shared data reaches Unreal as a portable asset and is walkable. Parent: T-1356; decision owner: T-0252. Read [the full parity inventory](../docs/unreal/README.md).

**Executor:** export implementation on a remote-capable worker and existing Blender runner as appropriate; closing visual/collision receipt requires a qualified Unreal runner. Until T-0252, T-1357, T-1358, and engine access are ready, this is blocked-tech and not claimable by the remote web worker. A coordinator may split a separately closable remote export slice if needed; do not close engine acceptance using only schema tests.

## Acceptance — one corridor through the whole pipeline

1. Refresh the layer inventory; record representation decisions made in T-0252. Select one existing named street corridor near the Sauganash, including its terrain conforming surface and a junction. Export from authoritative shared data and deterministic rules; do not hand-place a divergent Unreal copy or import future-date geometry into 1835.
2. Package it in the same versioned bundle with terrain/epoch/input hashes, materials/textures, confidence/license information and collision intent. A changed heightfield regenerates affected geometry. Source and bundle gates retain the re-derivation checks; a GLB hash alone does not replace them.
3. Import using T-1358; compare the same coordinates in web and Unreal with a recorded side-by-side view. Normal walking crosses the corridor/junction without gaps, z-fighting, snagging or artificial invisible floors. Record draw calls/triangles/memory/frame time on the target device and a declared quality preset; never silently spend the web light-tier budget.
4. Mark only that corridor/layer complete in a durable parity matrix. Before closing, file ONE bounded next slice beside this band, carrying engine/dependency holds as needed. Continue through frontage/plank walks and bridge/wharf approaches, flora, fences/yards/wells, props/boats/wagons/camps/signs, water/material/lighting detail, provenance/confidence interaction and scene epochs. Do not represent this succession as already delivered, and do not flood the queue with the entire inventory.
5. No human figures; preserve review_required and source rights restrictions. Keep future historical scenes distinct rather than baking all dates into one level.


## Ticket budget exception

Owner explicitly requested this programme and its execution-separated tickets. One held epic, five bounded initial slices and reused T-0252 avoid a large speculative backlog.

## Owner update, 2026-09-20 — roads remain a named priority

Reuse this ticket for the missing roads; do not mint a duplicate. Expand the corridor receipt to include its street surface, junction, applicable alley/frontage or plank walk, and a bridge/wharf approach where present. Confirm vertical fit against T-1473 building entrances and the same terrain snapshot. Record coverage for the rest of the town in the parity matrix and file the next bounded road-network slice before closing; a single corridor does not complete roads. Street collision is tested with normal walking, including slopes, crossings and building thresholds. Do not draw approximate decorative roads over an unrelated invisible floor.

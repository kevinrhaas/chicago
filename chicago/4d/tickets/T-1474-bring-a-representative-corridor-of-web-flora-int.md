---
id: T-1474
title: Bring a representative corridor of web flora into Unreal
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
blocked_on: T-0252 shared export decision, T-1357 bundle, T-1358 importer and qualified Unreal renderer; placement rules from T-1473
needs_bake: false
closed_at: null
claimed_run: null
---

Owner request, 2026-09-20: bring the web application's flora into the Unreal scene. Parent: T-1356; first bounded flora slice, not a claim that every vegetation layer is already ported.

**Executor: QUALIFIED UNREAL for completion.** Export preparation may use the remote source worker/existing pinned bake runner; the general web loop cannot close engine acceptance. Hold for T-0252, T-1357, T-1358, the applicable T-1473 placement policy, and current engine/GPU access. A coordinator may assign a separately closable export-only sub-slice without marking this ticket complete.

## Acceptance — one representative corridor, shared flora placement

1. Inventory the web flora layers actually enabled at the pinned scene date and quality preset: trees, shrubs, grass/reeds and any other plant layers present in current code. Record authoritative inputs, deterministic seeds, terrain/water/road exclusion rules, density, confidence and asset rights. Pick a corridor spanning road edge, yard and bank where available.
2. Consume shared exported instances/assets and placement rules under T-0252, rather than independently scattering plants in Unreal. Carry species/variant, transform, seed, material/texture and scene-date metadata; handle terrain changes and retired instances deterministically. No double-population when importing twice.
3. Implement appropriate Unreal instancing/LOD and material alpha/shadow treatment. Compare matched web/Unreal views and counts, grounded roots, bank placement, clear doors/roads, and intentional collision. State unsupported wind/season/material behavior. Preserve historical and Indigenous-review constraints; flora work does not authorize human figures.
4. Measure frame time, instance/draw counts and memory against the same empty/native baseline and declared Mac preset. Package and walk the corridor without invisible plant blockers or material artifacts. Record screenshots, source/bundle hashes and performance measurements.
5. Update the parity matrix with exactly the verified corridor/layers and file one bounded successor for the remaining coverage. Close only this slice, never all flora or overall parity based on one corridor.

**Budget exception:** Owner expressly requested flora as a distinct queued deliverable in the existing Unreal programme.

---
id: T-1358
title: Rebuild the Chicago Unreal preview from a downloaded scene bundle and verify walking
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
blocked_on: Needs T-1357 bundle and qualified Unreal 5.8.2 runner with GPU, project access and native packaged walking/visual validation
needs_bake: false
closed_at: null
claimed_run: null
---

Turn the local spike into a portable, repeatable Unreal importer. Parent: T-1356; source bundle: T-1357. Read [the runbook and reference scripts](../docs/unreal/README.md).

**Executor: LOCAL/QUALIFIED UNREAL ONLY.** The remote web worker cannot close this. Initially use the owner's Mac with Unreal 5.8.2, the committed renderers/unreal project, GPU, writable project storage and native packaged play access. A different runner must pass the documented engine/SDK/render preflight first. Coordinate an available local session; owner presence is for access/visual verification, not every future batch import.

**Held prerequisites:** a verified T-1357 bundle and a current executor capability receipt. Keep blocked-tech until both exist; never infer engine availability from completion of T-1357.

## Acceptance — clean import, update, and walk of one bundle release

1. Extend the committed T-1464 standalone project; use the older prototype only as evidence. Maintain portable project/bootstrap/import source in the approved project scope, with explicit source-bundle and project arguments, pinned compatible engine/plugins, and no hardcoded home paths or checked-in DerivedDataCache/Intermediate/Saved. Preserve original local files before migration.
2. Import all declared core assets; preserve sidecar placement, centimetre scaling, facade orientation, ground versus water anchors, materials, textures, stable identities and review/confidence metadata. Compare heightfield and terrain mesh at named spawn/bridge/street probes—do not assume their versions or quantization match.
3. Reimport the same bundle idempotently; a changed bundle updates changed assets and removes/retires only importer-owned obsolete actors/assets, preserves user-owned content, and refuses incomplete imports before replacing the active level. Verify a same-name changed GLB actually updates; the spike currently reuses existing assets blindly.
4. Create a persistent body-free first-person pawn, correct map/default selection, spawn above ground, and deliberate solid/water/bridge collision policy. Complex-as-simple may bootstrap static ground; measure cost and use simpler collision where appropriate. Avoid generating water convex hulls. No launcher-only visual hiding, cheat teleport, ghost/fly mode, or debug overlays in acceptance.
5. In normal walking, traverse a named route from the Sauganash along a street, stop at a wall, cross a bridge/approach and test a bank/water boundary. Verify no falling through or invisible blockers, plausible human scale, repeatable spawn/restart and expected interaction. Save the exact bundle/engine ids, screenshots/video and collision results; test packaged behavior when cooking becomes available in T-1361.

**Unblocks:** T-1360's engine integration and T-1361's core cook path, only with the receipts above. Visual fidelity of missing web layers remains with the parity programme; do not claim complete town parity here.


## Ticket budget exception

Owner explicitly requested this programme and its execution-separated tickets. One held epic, five bounded initial slices and reused T-0252 avoid a large speculative backlog.

## Standalone baseline update, 2026-09-20

Start from committed `renderers/unreal/`, whose fresh-build path and native pawn shipped in T-1464, not a hardcoded local prototype. Unreal 5.8.2 is the qualified version. Native packaged walking/visual acceptance does not require a browser; browser/stream QA belongs to T-1359. This ticket still owns immutable-bundle incremental updates and retired-asset handling. T-1473 owns the observed sinking-building diagnosis; consume its placement policy rather than closing that defect by assumption. T-1472 can automate the existing fresh-source build before this incremental contract is complete.

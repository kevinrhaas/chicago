---
id: T-1356
title: EPIC: Chicago 4D Unreal asset delivery, renderer parity, and reliable streaming
state: blocked-tech
epic: PIPELINE
requested_by: owner
seen: false
effort: L
legacy_id: null
parent: null
opened: 2026-09-18
closed: null
pr: null
claimed_by: null
blocked_on: Programme tracker only; execute bounded children on eligible runners, never claim this multi-run epic
needs_bake: false
closed_at: null
claimed_run: null
---

Owner programme, 18 September 2026. The priority band is immediately after South Through Time and before Loop Improvements. This epic is a held tracker, not a claimable multi-run job. Execute its bounded children, preserve dependency holds, and never mark the programme complete just because the local spike renders a building.

**Execution/runbook:** [Unreal delivery plan](../docs/unreal/README.md). That document preserves evidence, prototype references, runner eligibility, lifecycle, parity inventory and the streaming experiment.

## Work and dependency map

| Ticket | Deliverable | Execution |
|---|---|---|
| T-1357 | Scheduled versioned source scene bundles and a verified fresh download | Remote preparation + existing Blender bake runner |
| T-0252 | Shared export decision for web-only scenery; existing ticket reused | Remote contract work |
| T-1358 | Repeatable Unreal import and normal walking from an immutable bundle | Held: T-1357 + qualified Unreal runner |
| T-1359 | Fix the reported black-bar/static corruption | Held: affected local Mac/project/browser; independent of T-1357 |
| T-1360 | First exported street corridor, then bounded parity successors | Held: T-0252 + T-1357 + T-1358 + Unreal validation |
| T-1361 | Target-platform cook, staging-host pull/push and rollback | Held: T-1358 + T-1359 + approved host/toolchain/access |

## Completion

- The source bundle is regularly published, discoverable, hash-verified and reproducible from an identified source snapshot; last-good retention and failure behavior are proven.
- Unreal consumes it without manual per-mesh work, updates changed and retired assets, preserves source provenance/review constraints, and passes walking/collision/material and spawn tests.
- The inventory in the runbook has parity receipts or explicit owner-accepted deferrals for every layer, including interaction, confidence and epochs. First streets are only the first slice. Each closing slice hands on the next bounded successor in this band; do not dump dozens of tickets into the queue in advance.
- Streaming corruption is resolved on a supported recorded preset; an engine/GPU-equipped runner can reproduce the release. Localhost alone is not server deployment proof.
- One approved staging server downloads or receives a target-platform build, validates it, starts a healthy stream, and rolls back. Production remains owner-promoted.

**Blocked until:** all children and parity successors satisfy their receipts. Remote workers may prepare eligible children, never claim this epic or remove local holds to make the queue look workable.


## Ticket budget exception

Owner explicitly requested this programme and its execution-separated tickets. One held epic, five bounded initial slices and reused T-0252 avoid a large speculative backlog.

## Owner update, 2026-09-20 — native feature parity before streaming

T-1464 delivered the first Apple Silicon preview; the downloadable prerelease does not close the parity programme. New ordered children are T-1472 (repeatable latest-validated Mac build/release), T-1473 (sinking-building placement), existing T-1360 (roads and approaches), T-1474 (first flora corridor), and T-1475 (map/search/place inspection). Keep the Unreal band after South Through Time and before Loop Improvements. The owner expressly requests these tickets now; the earlier one-successor filing guidance does not prevent these four named follow-ups.

[Build/release runbook](../docs/unreal/BUILD-AND-RELEASE.md) describes the existing manual path and the pending automation boundary. [Parity matrix](../docs/unreal/PARITY.md) tracks all remaining web layers and interactions; unsupported layers do not become implemented just because a newer dev commit is built. Full-town roads, flora, props, navigation, confidence, epochs, materials and measured performance require their own completed receipts or explicit owner deferral.

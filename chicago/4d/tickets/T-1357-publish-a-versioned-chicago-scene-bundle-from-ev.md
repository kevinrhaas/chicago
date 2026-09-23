---
id: T-1357
title: Publish a versioned Chicago scene bundle from every successful scheduled asset bake
state: open
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
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Build the durable handoff the owner can download today and an Unreal/server worker can consume later. Parent: T-1356. Read [the delivery plan](../docs/unreal/README.md).

**Executor:** remote worker for code/workflow preparation; the existing pinned Blender runner performs actual bakes. No Unreal installation required. No Mac presence required. Workflow edits require the existing owner-visible PR route. Keep the city-first priority rule; this band is not permission to fall through earlier work.

**Prerequisites:** existing source bake and its validation gates. Core bundles can ship before T-0252 decides new procedural layers; the manifest MUST declare the current coverage and omitted layers.

## Acceptance — one successful scheduled-bake-to-fresh-consumer demonstration

1. Add a versioned, engine-neutral scene-bundle contract and a packaging command consuming ONE validated source snapshot. Include scene/epoch metadata, master GLBs compatible with the consumer, referenced textures, compiled runtime sidecars, terrain heightfield/meta, necessary runtime provenance, license inventory, per-file checksums and overall digest. Exclude private research/deposit files, secrets, unrelated repo trees and engine binaries. Unknown or check-required asset rights retain the established release refusals.
2. Attach packaging/publication to the existing successful scheduled asset bake and manual dispatch. Pin inputs and build versions; document actual cadence and destination. Failed/stale bakes cannot advance the latest-good pointer. Do not duplicate the geometry schedule or automatically promote main.
3. Publish an immutable named bundle plus machine-readable discovery manifest. State artifact retention/expiry; provide durable storage only within approved access/cost. A fresh consumer downloads by digest, verifies hashes/schema and prints source SHA, scene and coverage. Demonstrate tampered/missing asset refusal and no mixed-commit output.
4. Build the same input twice and compare normalized payload hashes; isolate timestamps from semantic content. Record the scheduled run URL, artifact/download identity, checksum, fresh-download receipt and previous-good retention behavior. An archive created only on the worker is not published delivery.
5. Document how T-1358 consumes the bundle and what must change when T-0252 adds layers. This ticket produces assets, not a cooked Unreal executable or a public stream.

If unavailable publication access/cost is the only remaining step, retain the prepared concrete result and block with the exact missing destination/approval; do not call local files publicly available.


## Ticket budget exception

Owner explicitly requested this programme and its execution-separated tickets. One held epic, five bounded initial slices and reused T-0252 avoid a large speculative backlog.

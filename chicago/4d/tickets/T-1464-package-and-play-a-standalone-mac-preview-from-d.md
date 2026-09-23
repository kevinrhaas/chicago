---
id: T-1464
title: Package and play a standalone Mac preview from dev
state: done
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-1356
opened: 2026-09-20
closed: 2026-09-20
pr: 1581
claimed_by: local-mac 9/20/2026, 11:04:11 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T16:37:47.892Z
claimed_run: null
---

Package and play a standalone Mac preview from dev.

**Executor: LOCAL MAC WITH UNREAL + XCODE.** Owner explicitly requested latest `dev`, Mac first, and a standalone game before streaming on 2026-09-20. This bounded local slice is independent of T-1361's hosting prerequisites and does not close T-1358's bundle update contract or T-1360's renderer parity.

**Acceptance:** Package a native Apple Silicon Mac application using current committed terrain and structure glTF/sidecars from dev snapshot `253f026570358dfcdab62fb2593c4082b058de07`. Start directly in Chicago with a body-free walking character and demonstrate the packaged app launching without the editor or streaming server. Record source/engine/toolchain, controls, output location, normal movement/collision observations, missing renderer features, and distribution limitations. Commit reproducible Unreal project and import/build source to dev through an isolated branch. Do not close streaming/parity tickets based on this preview.

The owner prioritised this local build now. Remote web workers cannot complete this without the engine, SDK and graphical Mac session. If local execution stops unfinished, restore blocked-tech with the concrete remaining prerequisite.

### Owner-reported fence, 2026-09-20

The owner reported a fence near the fort hanging in the air. Include the Unreal
placement correction in this local build: match the existing browser's lowest
rotated-footprint terrain anchoring, measure the fort garden fence/palisade offsets,
and rebuild the app. Do not invent new geometry or historical dimensions.

The owner clarified that this is the low garden fence. The underlying error was
Python Rotator positional arguments: its 53-degree ground bearing became pitch.
Named yaw/pitch/roll fields correct structures, player start and sunlight. The
editor verifier now requires every structure to be upright with the sidecar yaw,
and measures the garden fence at 1.135333 m tall (below a 1.5 m regression bound).

## Completed local demonstration

Native arm64 Development app built and packaged with Unreal 5.8.2 / Xcode 27.0,
using dev scene snapshot 253f026570358dfcdab62fb2593c4082b058de07. Normal native
launch and Escape quit were observed. The corrected package passed
the offscreen 21-second grounded movement/obstacle/back-away test with keyboard
and mouse ignored. Code-sign verification passed before and after ZIP extraction.
See [build instructions](../renderers/unreal/README.md) and
[the receipt](../renderers/unreal/receipts/mac-253f02657.json).

No generated engine assets or caches were added to source history; all new adapter
source is isolated in renderers/unreal. Local check/preflight completed with two
recorded Mac-specific baseline failures; this PR requires its own green Linux CI
before merge. The wider streaming, bundle-update and renderer-parity tickets remain
held/open under their existing acceptance.

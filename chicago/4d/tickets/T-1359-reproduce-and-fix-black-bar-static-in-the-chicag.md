---
id: T-1359
title: Reproduce and fix black-bar static in the Chicago Pixel Streaming preview
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
blocked_on: Needs access to the affected Mac, Unreal project, running signalling server, and browser; remote web worker is ineligible
needs_bake: false
closed_at: null
claimed_run: null
---

Owner reports frequent black-bar/static noise while playing the local Chicago Unreal stream. The earlier still-image success is not a fix. Parent: T-1356; [experiment/runbook](../docs/unreal/README.md).

**Executor: AFFECTED LOCAL MAC + UNREAL + BROWSER.** Keep blocked-tech until that environment is available. This can be worked before T-1357/T-1358 using the existing preview. Do not wait on asset export to diagnose a transport/render defect. Request a short owner session only if their reproduction/visual confirmation is needed; preserve their project/server configuration before changes.

## Acceptance — reproduced defect, controlled fix, same-route stability receipt

1. Record exact hardware/OS, engine build, legacy PixelStreaming versus PS2 choice, frontend/server package versions/commit/lockfile, codec, bitrate, resolution/fps and capture mode. Redact credentials and network secrets. Record when bars occur, including motion, resizing, focus and reconnect. Distinguish ordinary letterboxing from dynamic corruption.
2. Capture the same view locally and through the browser to locate the first corrupt stage. Compare the template map and Chicago. The spike used UE5.8.2 while the signalling package declared UE5.7 dependencies and logged unsupported endpointIdConfirm/layerPreference; test a supported matched stack without presuming that mismatch causes the bars.
3. Change one variable per test: matched infrastructure, supported encoder/codec, 720p/30 and 1080p/60, bitrate bounds, browser, on-screen/off-screen capture, and relevant rendering settings. Retain the matrix, before/after moving clips and WebRTC/engine metrics; random simultaneous settings changes are not diagnosis.
4. Fix the identified cause and check in reproducible compatible configuration/launcher guidance. Run the previously failing route continuously for at least 10 minutes at the selected supported preset with normal walking, rapid camera motion, resize and reconnect: no recurring bars/static. Record frame rate, dropped frames, packet loss and latency. Prefer the working measured preset over claiming 1080p60 by command-line flag alone.
5. Do not silently remove major scenery to pass. If the affected Mac remains unsupported/broken, publish the negative evidence and a qualified-GPU-runner successor, keep this held, and state the owner action precisely. Do not mark fixed on a still frame or by switching to an untested host.

**Unblocks:** T-1361's streaming acceptance once genuinely fixed. This ticket changes no historical claims.


## Ticket budget exception

Owner explicitly requested this programme and its execution-separated tickets. One held epic, five bounded initial slices and reused T-0252 avoid a large speculative backlog.

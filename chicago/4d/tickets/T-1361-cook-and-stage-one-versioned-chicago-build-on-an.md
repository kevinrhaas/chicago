---
id: T-1361
title: Cook and stage one versioned Chicago build on an approved streaming host with rollback
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
blocked_on: Needs verified importer and streaming fix, approved host and budget, licensed target-platform Unreal build runner, and deployment credentials
needs_bake: false
closed_at: null
claimed_run: null
---

Stage one tested target-platform Chicago application on an approved streaming host. Parent: T-1356; [delivery/deployment runbook](../docs/unreal/README.md).

**Executor: QUALIFIED UNREAL BUILD + APPROVED GPU HOST.** Remote web workers can prepare configuration but cannot complete cooking or stream validation without the required engine, SDK, GPU encoder and host access. Kept blocked-tech. Initial prerequisites: T-1357, T-1358, T-1359; a selected accepted bundle/coverage manifest; host/OS, disk/RAM/GPU/driver capability receipt; engine entitlement/installation route; approved costs and scoped deployment access. Initial staging can use core coverage but must say exactly what is missing; final epic closure also requires parity.

## Acceptance — one release staged, observed, and rolled back

1. Prepare an exact runner/host proposal before provisioning: local self-hosted runner versus persistent remote Unreal runner, target OS/architecture, supported GPU encoder, engine/license access, SDK/toolchain, storage/cache, installation source, maintenance and costs. Document any approval or interactive login/terms needed. Filing this ticket is not approval to rent a server, accept terms or publish credentials. Never assume a generic remote web worker can install and run Unreal.
2. On the approved eligible runner, cook/package from the verified source bundle and pinned project configuration for the ACTUAL host platform. Record bundle digest, project commit, engine/plugin/SDK versions, executable digest and smoke results. A Mac editor `-game` launch or loose GLBs is not a packaged Linux/Windows release.
3. Implement pull-by-digest (preferred) or scoped push as required by that host, with dry-run, checksum verification, sufficient disk checks, staged extraction, atomic activation and last-good rollback. Include matched signalling/frontend versions and startup/health/log handling. Do not embed engine distribution or secrets in the public source bundle.
4. Demonstrate a browser session from outside the host network with the approved TLS/WebSocket/STUN/TURN/access policy. State shared-view versus per-user session behavior and measured single-session capacity; avoid promising independent multiplayer from one stream. Record successful normal walking and absence of T-1359's corruption on the accepted route.
5. Deploy a second known-good version, simulate a failed health check without losing the first, and demonstrate explicit rollback. Save release/run/download references and the operations checklist. Future polling/scheduling follows approved policy; production promotion remains the owner's separate action.

If a prerequisite is absent, name precisely the credential, approval, hardware or installation needed and restore the hold. Never let a failed provisioning attempt count as a completed deployment.


## Ticket budget exception

Owner explicitly requested this programme and its execution-separated tickets. One held epic, five bounded initial slices and reused T-0252 avoid a large speculative backlog.

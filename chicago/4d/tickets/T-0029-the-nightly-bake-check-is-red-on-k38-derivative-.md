---
id: T-0029
title: The nightly bake check is red on K38 derivative baselines
state: withdrawn
epic: PIPELINE
requested_by: steward
seen: false
effort: M
legacy_id: K38
parent: null
opened: 2026-08-17
closed: 2026-08-23
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

`bake` has been red for days: the K38 web-derivative baseline says "decided master
passthrough" for files the bake now compresses. Two stale bake PRs (#164, #175) are parked
behind it. Re-run tools/measure_web_derivatives.py --write-baseline in a commit that states
why each passthrough moved, close or supersede the stale PRs, and the nightly goes green.

**Acceptance:** bake check green on dev; #164/#175 resolved; baseline change explained.

---

**2026-08-23 — SUPERSEDED BY T-0160, and this ticket should probably be withdrawn.**
This is the K38 web-derivative passthrough failure, and T-0160 (#331) settled it. The cause was
not a stale baseline and not a toolchain move: the bake was **discarding a real upgrade every
night**. 132 of 226 placeholders were already archetypes; the last 94 (median 6.5 KB, all
`extras.placeholder: True`) were rebuilt at 16.4× triangles, which flipped them out of K38's
banked passthrough set. The upgrade and the re-bank landed together — 93 passthroughs down to 3 —
and the nightly publishes again.

Left in the queue rather than withdrawn, because withdrawing another run's ticket on one reading
is a bigger step than re-ranking it. Withdraw if you agree.

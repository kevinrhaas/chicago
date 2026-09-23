---
id: T-0466
title: Build a south-terrain tiling and culling plan for a four-kilometre field
state: done
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-01
closed: 2026-09-15
pr: 1360
claimed_by: run 9/15/2026, 11:14:22 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T17:10:04.161Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34991605762
---

**Unblocked 2026-09-15.** This ticket carried `blocked_on: T-0464` from the day it was
filed. T-0464 CLOSED on 2026-09-14 as #1257 — the ground now reaches Twenty-Second
Street and the modelled field is one box 2 020 x 4 920 m — so the dependency is
SATISFIED, not dropped. The field was left stale for a day, which reads to anything
picking work off this queue as "blocked" and is the state a run steps over.

The renderer's 12 x 3 ground tiling was tuned for the present roughly 2,020 x 800 m terrain. A Madison-to-Cermak field is several times deeper north-south and must not simply multiply visible triangles and draw calls without measurement.

Measure the expanded field at the existing smoke camera stands plus new south stands. Replace fixed assumptions with a documented tiling/culling strategy that scales with terrain aspect ratio while preserving the `light` tier as the floor. Raise full/balanced budgets only when the measured parcel requires it, per AGENTS.md.

Acceptance: the expanded field has an explicit tile grid or dynamic rule; downtown and south-scene stands have measured triangle/draw-call results; no terrain seam appears; `light` remains within its ceiling; and the result unblocks the south geometry rather than only documenting a performance risk.
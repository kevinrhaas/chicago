---
id: T-0770
title: south_branch_raft_bridge glosses West Water Street as 'now Canal Street', and the committed canal stands a plat module west of it
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-12
pr: 1205
claimed_by: run 9/12/2026, 1:30:57 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T18:50:22.443Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34711227535
---

`data/structures/south_branch_raft_bridge.json`'s `symbolic_location` reads *"Across the South
Branch between Lake and Randolph Streets, its west landing on West Water Street (now Canal Street)
below Wolf Point."* T-0445 seated `west_water` off the committed 1834 west bank, and the committed
`canal` — fitted to modern Canal Street's own surviving intersections (T-0446 records the OSM
nodes) — stands **131 to 159 m west of it** over the reach the two share, about one plat module.
The plat draws West Water and Canal as two separate streets, so the parenthetical cannot be right
for this line.

It is almost certainly a secondary-source shorthand carried into the record, and it matters because
`symbolic_location` is prose a reader trusts: it is the sentence that says WHY the bridge stands
where it does.

**The ask.** Trace the gloss to whatever it was read from, and either withdraw it, or restate it as
what the source actually says with the source cited. Do not change the bridge's POSITION — that is
placed at the midpoint of a documented band and this ticket is not a re-placement.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- The gloss is withdrawn or restated with its source id, in the record's own prose.
- `docs/RESEARCH/west_division_streets.md` § 1 is updated to match whichever it is.
- `./tools/check.sh` no redder than dev.

**Links:** T-0445 (which found it) · `data/streets/1835.json` `west_water` and `canal` ·
`docs/RESEARCH/west_division_streets.md`.

---
id: T-0097
title: The ground around the fort is full prairie, where both plates show it bare and trodden
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-23
pr: 326
claimed_by: run 8/23/2026, 8:36:41 AM CT
blocked_on: null
needs_bake: false
---

The ground around the fort is full prairie, where both plates show it bare and trodden.

Found by T-0044's image-accuracy pass. Grass clumps grow to the foot of the pickets in the render.
Both Fort Dearborn views draw the ground round the walls as bare, trodden earth — which is what the
ground outside a garrisoned post's walls is, and what the road ticket's own track already models
twenty metres away. No source states it, so this is a reconstruction bounded by the plates and by
the fact that the layer already knows how to keep plants off a road.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

A stated rule — not a hand-drawn polygon — keeps the sward off the ground immediately outside the
fort's walls, the rule is re-derived by a `--check` like every other placement rule here, the liberty
is recorded, and a before/after from `p4_0`'s stand is committed.

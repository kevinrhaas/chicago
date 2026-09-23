---
id: T-0036
title: The gate screen counts the town: buildings standing, people housed
state: done
epic: TOWN
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-17
closed: 2026-08-18
pr: 240
claimed_by: run 8/18/2026, 7:25:54 AM CT
blocked_on: null
needs_bake: false
---

**The owner's ask, 2026-08-17:** on the front (gate) screen, show **the number of buildings
in the city and the population — people living in their buildings** — and the population
"should get to the correct Chicago 1835 population number as the buildings all complete."

The data already exists; this is a read, not an invention. Buildings: the structures that
resolve into the scene (the 665-roof programme's standing count — note **T-0032**'s ruling
may make the target 662). Population: `data/residents/` households joined through their
`lives_at` links — a person counts when the building they live in stands, so the number
GROWS as the town builds out and converges on the programme's total by construction.

Honesty note for the implementer: the committed scene note says "population roughly 3,265
in the late-1835 count" while the scene date is 1 July — present the figure the way the
records support (e.g. "of the ~3,265 the late-1835 count records"), not as a false
precision. The counts must come from the same committed data the gates reconcile
(`reconcile_665.py`, the residents programme), never a hand-written constant that goes
stale — the build.json staleness lesson applies to numbers on the gate screen too.

**Acceptance:** the gate overlay shows buildings-standing and people-housed, both derived
at build/publish time from committed data (or at load from the scene index), with a smoke
assertion that the displayed numbers equal the data's; the What's-New entry tells visitors
what the numbers mean; both viewports; zero pageerrors.

---
id: T-0095
title: The fort's corner works and its two documented gates, as the plate draws them
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-24
pr: 369
claimed_by: run 8/24/2026, 9:55:23 AM CT
blocked_on: null
needs_bake: true
---

The fort's corner works and its two documented gates, as the plate draws them.

Found by T-0044's image-accuracy pass. `p4_0` draws the corner works RISING ABOVE the curtain with
their own pyramidal roofs and small lanterns, and a log-faced work over the gate in the middle of the
wall. The model builds the bastions as shallow projections at curtain height and draws no gate at all,
though `gate_sides` (n and s) and `gate_width_m` are already in the record and `bastion_corners` (nw
and se) is attested three ways. **The guard in the record binds here**: the two blockhouses at the
south-east and north-west angles belong to the FIRST fort and may not be borrowed, so this ticket is
about drawing what the second fort's own record already states, at the height and roof the plate
supports as inferred.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The gates in both documented walls are drawn, the corner works and the south-west blockhouse read
above the curtain, every new form value carries its own confidence and note, and a before/after from
`p4_0`'s stand is committed. Geometry — needs the nightly bake.

---

## Outcome, 2026-08-24 — half refuted, and a defect nobody had claimed

Full working: `docs/RESEARCH/fort_dearborn_gate_and_corner_works.md`. Held by
`tools/measure_fort_works_plate.py` and `tools/measure_fort_gates.py`, both in `tools/check.sh`.

**The premise of the corner-works half is refuted.** `p4_0` raises exactly two roofed, lanterned,
log-faced works and **both stand over the middle of the wall**, at 0.435 and 0.521 of the 862 px of
drawn run — over the gate, which is where this ticket's own next clause put one of them. A corner
work stands at 0.000 or 1.000. The one angle the plate shows unoccluded is the **north-east** and
it is drawn **plain** (0.04 curtain heights over its first twenty columns), which is what the record
says of that angle. The **north-west** angle — the one the record does put a work at — is behind the
tree outside the walls. **Nothing was massed at the angles.** Second Fort Dearborn ticket in two
days seeded by a plate read with the eye; T-0094 was the first.

**And the log-faced work over the gate was not built either.** `data/exclusions.json` already
assigns the flagstaff on this sheet to the FIRST fort, and that entry's list of first-fort features
opens with *two blockhouses*. Two roofed lanterned log towers is that signature in everything but
position, so the sheet matches neither fort's documented arrangement. A tier-5 view that conflates
the two forts cannot add a tower to the second one at an angle **or** over a gate — the same ruling
T-0044 made about the flagstaff, applied consistently. **No form value was added**, because none is
supported.

**"Draws no gate at all" was also wrong — but the gates were a quarter OPEN.** A gateway has been
built in both documented walls since the archetype was written. One leaf of each pair was placed
from a midpoint that collapsed onto its own jamb, so **0.90 m of the 3.6 m gateway was daylight
straight through the wall** and 0.90 m of leaf lay across the pickets outside the frame — in the
committed GLB. Fixed, and both palisade-archetype assets rebaked: `fort_dearborn_palisade__picket_1816`
(changed) and `fort_dearborn_garrison_garden__fence_1816` (hash re-stamped only — the
staleness recipe hashes the archetype's bytes into every asset built from it).

**The south-west blockhouse already read above the curtain**: 9.48 m of building over a 3.80 m
curtain, from its own instance bounds in the scene.

Before/after from `p4_0`'s stand: `docs/evidence/t-0095-{before,after}.png`, and the gate
itself at 5x in `t-0095-close-{before,after}.png`.

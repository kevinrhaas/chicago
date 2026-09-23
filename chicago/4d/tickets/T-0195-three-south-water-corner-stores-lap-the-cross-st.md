---
id: T-0195
title: Three South Water corner stores lap the cross street's corridor by 0.16-0.21 m, which the plat reconciliation could not reach
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: 417
claimed_by: run 8/27/2026, 6:21:36 PM CT
blocked_on: null
needs_bake: false
---

Three South Water corner stores lap the cross street's corridor by 0.16-0.21 m, which the plat reconciliation could not reach.

The South Water repair (T-0198, T-0199) moved eleven documented buildings SOUTH along South
Water Street's own normal, off the modern kerb line they were placed against and back onto
this project's committed plat. Three of them stand on a CORNER, and a corner has two streets:
the move that answers South Water cannot answer the street the building turns onto.

**Re-measured 2026-08-27, with all eleven on the plat** (`tools/measure_corridor_intrusion.py`):

| record | corridor still lapped | depth |
|---|---|---|
| `harmon_loomis_store` | Clark Street | 0.21 m |
| `madore_beaubien_house` | Dearborn Street | 0.20 m |
| `peck_store` | La Salle Street | 0.16 m |

Every other one of the eleven is clear of every platted corridor at every depth. These three
are the whole residual, they are the shallowest laps in the town after the fort's, and each
record says so in its own `position.note` rather than leaving it to a measurement nobody runs.

**This is NOT settled by the owner's 2026-08-27 business-front ruling**, and the distinction is
worth keeping straight: that ruling is about ENTITLEMENT — whether a documented store exhausts
its lot — and this is about GEOMETRY. The clause changes nothing about where a corner stands.

**Why the obvious repair is refused.** Moving these three ALONG their own street would clear
the cross-street corridor, and it is exactly the coordinate the sources argue: "at Clark", "at
LaSalle", the south-west corner. Sliding a building along the street to make a 0.2 m number go
away would move the one part of the placement that has evidence behind it, to repair the part
that does not. So the choice is between rotating them onto the cross street's own line (a
second claim about a documented record, which the setback repairs deliberately did not make),
narrowing the footprint, or accepting the lap and recording it — which is where it stands today.

**Acceptance:** each of the three is either reconciled with the CROSS street's corridor by a
move whose evidence is stated and whose along-street coordinate is defended, or refused in
writing per store with the metres and the reason in its own `position.note`;
`tools/measure_corridor_intrusion.py`'s baseline is rewritten either way so the number is
banked rather than tolerated; and no source-argued coordinate is moved to make a derived
number smaller. Never by weakening a gate.

**Links:** T-0198 (the six) · T-0199 (the five, and the owner's ruling) · T-0220 (the fork as
it was put to him) · `tools/corridor_intrusion_baseline.json`.

---
id: T-0134
title: The south bank at the Dearborn reach has no ground outside the platted street corridor
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-21
closed: 2026-08-27
pr: 428
claimed_by: run 8/27/2026, 9:14:52 PM CT
blocked_on: null
needs_bake: false
---

The south bank at the Dearborn reach has no ground outside the platted street corridor.

Found while building T-0133. Image 3 of the owner's brief of 2026-08-18 draws low warehouses on
BOTH banks below the drawbridge; T-0133 could only build the north side.

**The measurement.** At the Dearborn crossing the platted South Water Street corridor — the
committed centreline in `data/streets/1835.json` offset by half the platted module from
`data/traces/street_control.json` — reaches to within about **1.7 m** of the traced 1834
waterline (`data/terrain/epochs/e1834_harbor_cut/shoreline.geojson`, south shore, N +20.9 at
local E 697 against a corridor edge at N +19.2). Sampling the strip from E 710 to E 800 at
2 m steps found no rectangle of F1 size that clears the corridor: the shallowest intrusion for a
12.2 × 7.6 m footprint is 2.3 m and every deeper position is in the water. So the whole south-bank
frontage at this reach is either platted street or river.

**Why it matters and what it is not.** `tools/measure_corridor_intrusion.py --gate` refuses a NEW
record lapping a corridor by construction, and rightly — the 29 that do lap one are documented
records the plat was fitted around, and T-0009 owns getting them out. This is the opposite
question: whether the corridor itself is right at the river street's north edge, where the town's
own warehouses and landings stood. L79 already records that the travelled tracks run 5.8–10.5 m
inside an 80 ft legal corridor.

**What would settle it:** the 1834 sheets' own drawn width for South Water Street at the Dearborn
reach against the traced bank, or a lot record on the river side of the street.

**Acceptance:** either the south-bank frontage at the Dearborn reach carries the warehouses the
plate shows, at their honest tier and clear of whatever the corridor turns out to be; or this
project holds a written finding that the platted corridor reaches the water there and the plate's
south-bank buildings cannot be sited without settling it first. Gates green either way.

**Links:** T-0133 · T-0071 · T-0009 · docs/LIBERTIES.md L79, L164 · owner_brief_2026_08_18 README
(image 3).

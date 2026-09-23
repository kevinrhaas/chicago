---
id: T-0106
title: The traced river bank stops at local E 390, short of the drawbridge reach
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-19
closed: 2026-08-24
pr: 366
claimed_by: run 8/24/2026, 10:48:16 AM CT
blocked_on: null
needs_bake: false
---

The traced river bank stops at local E 390, short of the drawbridge reach.

Found by T-0062. Both main-stem bank polylines in
`data/terrain/epochs/e1834_harbor_cut/river.geojson` end at local E 390, while the
Dearborn drawbridge stands at E 699 — so the mast-crowded reach of the 2026-08-18
brief (image 3) has no committed bank line at all. Three of T-0062's five stated
South Water landings (Carpenter's, Peck's, Harmon & Loomis's) stand refused by the
wharf generator for exactly this reason: their frontage lies beyond the trace, and a
deck derived from a bank that is not there would stand on an extrapolated endpoint —
T-0062 found all three stacked on one point before the generator refused it.

Extend the traced banks east from E 390 to the drawbridge reach from the same 1834
map layer the existing trace carries (its provenance travels with the feature
properties). When the trace reaches them, the three refused landings draw themselves
on the next `generate_river_wharves.py` run with no further authoring; T-0071 (the
drawbridge area) wants the same trace.

**Acceptance:** the South Division and North Division bank polylines reach the
drawbridge reach with their provenance stated; `tools/generate_river_wharves.py`
draws the three landings it currently refuses; `tools/check.sh` green.

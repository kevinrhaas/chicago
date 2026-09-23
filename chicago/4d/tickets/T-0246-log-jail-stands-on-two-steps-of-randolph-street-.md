---
id: T-0246
title: log_jail stands on two steps of Randolph Street's new plank walk, the same OSM-kerb fault Lake and South Water answered
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 474
claimed_by: run 8/28/2026, 10:49:12 AM CT
blocked_on: null
needs_bake: false
---

log_jail stands on two steps of Randolph Street's new plank walk, the same OSM-kerb fault Lake and South Water answered.

Found by T-0196 while clearing Lake Street. T-0196's own count — "eleven refused steps are
left in the town and all eleven are on LAKE Street" — was read on 2026-08-27 before T-0240
laid Randolph. Re-read on the same march after it landed, the town carried **thirteen**
wall-refused steps, and the two new ones are Randolph's:

| face | steps refused | for |
|---|---|---|
| `blk_randolph_lasalle` north (Randolph) | 2 — 0.0 to 10.4 m | `log_jail` |

`tools/measure_corridor_intrusion.py` puts `log_jail` 3.48 m into the Randolph corridor, in
the DEEP mode, with its centroid inside — deeper than any of the four Lake Street records
T-0196 looked at. T-0196 cleared three of those four; the two steps left on Lake belong to
`first_presbyterian_church` (T-0251), and these two belong here.

**What is not yet known, and is the first thing to measure:** whether this is the same fault.
The Lake and South Water records were all placed off a modern OpenStreetMap kerb line; whether
`log_jail`'s coordinate has the same provenance has not been checked, and its own
`position.note` is the place to find out. It may instead be a placement the sources argue for,
in which case the honest answer is that the walk breaks there and the refusal says why — the
project does not move a building to make a gate green (`measure_corridor_intrusion.py`'s own
docstring says so).

**Acceptance:** `log_jail`'s Randolph placement is either reconciled with the committed plat by
the method the eleven South Water and three Lake records carry — moved along the block face's
own inward normal, its along-street coordinate untouched, the metres and the derivation in its
`position.note` — or refused in writing with the source that holds it where it is;
`tools/generate_frontage_works.py` re-derives, and Randolph's walk on `blk_randolph_lasalle`'s
north face is measured either way.

**Links:** T-0196 (Lake, three reconciled) · T-0251 (Lake, the one that could not move) ·
T-0198, T-0199 (South Water, the method) · T-0240 (the street this appeared on) ·
`tools/generate_frontage_works.py` · `tools/measure_corridor_intrusion.py`.

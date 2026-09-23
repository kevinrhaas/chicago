---
id: T-0307
title: The derivation's running maximum costs 42 m of verge where the bank turns a right angle at Wolf Point
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 530
claimed_by: run 8/29/2026, 4:42:09 AM CT
blocked_on: null
needs_bake: false
---

The derivation's running maximum costs 42 m of verge where the bank turns a right angle at
Wolf Point.

**Found by T-0254**, which carried North Water Street west of the slough for the first time.
`tools/derive_north_water.py` lays the street's centreline `SETBACK_M` (12.192 m, half the
80 ft platted module) NORTH of a running MAXIMUM of the traced bank taken over ±`SMOOTH_M`
(15 m). That running maximum exists to clear metre-scale notches in a trace with ±20 m of
paper stretch in it, and on the east reach — where the main stem's north bank runs roughly
east-west — it costs nothing.

**West of the slough the bank is not east-west.** Coming round Wolf Point into the forks it
falls 45 m of northing in 35 m of easting, and a maximum taken 15 m ahead of a bank that steep
adds most of that drop to the setback. Measured by the tool itself on 2026-08-28:

    clearance from the waterline, northward:      12.05 m .. 41.95 m
    clearance from the waterline, perpendicular:  12.00 m .. 41.50 m

The 41.5 m is one 15 m stretch at the base of the point, between E −30 and E −15. The rule is
doing exactly what it says — the street stands north of every bank point within 15 m of it —
and the road is three and a half street-widths from the water where it should be one half.

**Not tuned in T-0254 on purpose.** `SMOOTH_M` is shared with the east reach, whose line is
committed and gated (`derive_north_water.py --gate`), so moving it re-derives 590 m of street
nobody asked to move. This wants its own unit and its own before/after.

**Three routes, unranked.** (a) Take the running maximum along the bank's own arc-length
rather than in easting, so a steep reach is smoothed over the same 15 m of BANK the shallow
one is. (b) Offset perpendicular to the bank's local tangent instead of northward, which is
what a platted corridor actually is. (c) Leave it and declare it — the verge at Wolf Point is
a real gore of ground and a street cutting the base of a promontory is not obviously wrong.

**Acceptance:** the perpendicular clearance on the west reach reads between 12 m and about
20 m at every station, or a stated finding that it should not, with the numbers.

**Links:** T-0254 · T-0226 · `tools/derive_north_water.py` (`SMOOTH_M`, `perpendicular_clearance`).

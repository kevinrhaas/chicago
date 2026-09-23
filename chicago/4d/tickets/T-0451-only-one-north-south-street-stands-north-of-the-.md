---
id: T-0451
title: Only one north-south street stands north of the river, where the Thompson plat carries the North Division's whole grid
state: done
epic: GROUND
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-09-05
pr: 905
claimed_by: run 9/5/2026, 9:13:53 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T18:01:36.891Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33970979218
---

Measured from `data/streets/1835.json`. Streets with any geometry north of the
main stem (local N > 60):

| id | runs | local E | local N |
|---|---|---|---|
| `kinzie` | E-W | −320.0 … 1100.0 | 251.8 … 263.1 |
| `north_water` | E-W | −30.0 … 970.0 | 2.2 … 270.0 |
| `michigan_north` | E-W | 450.0 … 1180.0 | 389.0 … 395.0 |
| `fort_bank_track` | E-W | 1133.4 … 1156.6 | 253.9 … 259.6 |
| **`wolcott`** | **N-S** | **827.0 … 829.0** | **108.0 … 400.0** |

**`wolcott` is the only north-south street this reconstruction holds north of the
river.** The Thompson plat carries the North Division's whole grid there — its
numbered blocks are bounded east and west by streets, and one line cannot bound
them.

This is the same shape of finding as T-0445 for the West Division, and it has the
same consequence: the tiers between Kinzie Street, North Water Street and
Michigan Street have no cross streets, so a walker sees unbroken ground where the
sheet shows blocks.

**The module is already proved.** T-0444 established that the plat's arithmetic
reproduces the committed South Division exactly — 4 x 80 ft lots + one 80 ft
street = **400 ft = 121.92 m**, against a committed mean of **121.92 m, delta
0 mm**. Whatever the North Division's block widths are on the sheet, the same
method applies; it does not need new survey control.

**Acceptance:**

1. The North Division's north-south streets are **read off the plat sheet** —
   names, count and block widths — and recorded as data with the reading.
2. Each either exists in `data/streets/1835.json` with sources and a stated
   `geometry_confidence`, or is refused in writing with the reading that refuses
   it. Absent is not an answer.
3. The spacings are reported against the South Division's measured band
   (119.2–123.4 m), the same way T-0444 reports the West Division's.
4. Depends on **T-0453**: if the north bank moves, the ground these stand on
   moves with it. Take T-0453 first.
5. `tools/check.sh` green.

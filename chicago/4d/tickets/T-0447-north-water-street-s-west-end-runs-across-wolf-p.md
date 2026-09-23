---
id: T-0447
title: North Water Street's west end runs across Wolf Point, which the Thompson plat does not give it
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0443
opened: 2026-08-31
closed: 2026-09-05
pr: 801
claimed_by: run 9/4/2026, 2:25:19 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T19:59:08.887Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33909443737
---

**Reopened and widened on 2026-08-31** after the owner marked up the dev preview
against the Thompson plat. The original ticket called this a stray west-end
vertex. It is not: **the whole course is wrong**, and the west end is only where
it shows first.

## Measured, from the committed path

`north_water`'s 24 vertices run:

| | local E | local N |
|---|---|---|
| west end | −30.0 | +45.2 |
| **lowest point** | **+5.0** | **+2.2** |
| | +183.0 | +157.5 |
| | +830.0 | +104.2 |
| east end | +970.0 | **+270.0** |

The line **dives to N +2.2 at E +5** — down at the water at the forks — then
climbs **268 m** to N +270 by the east end, wandering between N +104 and N +157
across the middle. On the plat, **North Water Street is a straight street along
the north bank of the main stem**, parallel to the river, east of the North
Branch. It does not dip to the waterline at the forks and it does not climb away
northward at its east end.

## What the owner marked

Red lines on the preview mark where the Thompson plat puts the **river borders**;
yellow lines mark where the **streets** belong. Around Wolf Point the two
disagree, and this street is drawn across ground the plat does not give it.

**This ticket owns North Water Street's own geometry only.** The three things it
touches but does not own:

- the North Division's missing north-south grid — **T-0451**
- the sloughs — **T-0452**
- whether the bank itself is in the right place at all — **T-0453**, which may
  move the ground this street is measured against, so **take T-0453 first**.

**Acceptance:**

1. North Water Street's course is re-derived from the Thompson plat and the
   committed bank, with the same arithmetic that reproduced the South Division
   to 0 mm (80 ft streets, 18 ft alleys, 80 x 180 ft lots — see T-0444).
2. The dip to N +2.2 and the climb to N +270 are each either committed with a
   source, or removed and the reason recorded.
3. If the line moves, every record seated off it is re-derived and the count of
   changed records reported.
4. `tools/check.sh` green.

---

## STATUS 2026-09-04 — the work is done and PARKED on `hold` in PR #801

All four acceptance items are met and `tools/check.sh` is green. Three of the four
`--for-diff` smoke legs are green (desktop 1: 78/0; desktop 7-8: 29/0; mobile 11-13:
150/0). The fourth, desktop 2-3, is 149/1.

The one red is `the town's wagons vary in type and in the way they stand`, which requires
8 distinct 5-degree wagon headings. dev reads 9; this branch reads 7, because both of the
buckets carrying dev's margin were single wagons standing on the **hand-drawn east tail
this ticket removed**. Re-cutting that gate inside the PR the gate refused is not a
steward run's call, so it is filed as **T-0688** with the measurements and both defensible
options, and this PR waits on it.

Also raised on the way: **T-0684** — `steamboat_hotel`'s placement note reads Kinzie
Street at local N +276 where the committed `kinzie` record is at N +252.8.

---

## CLOSED 2026-09-05 by T-0807 — PR #801 merged three hours before this ticket was read

#801 merged into `dev` as `89aaae238` at 17:12:40Z, carrying the work the STATUS above
describes as complete: all four acceptance items met, `tools/check.sh` green, three of the
four `--for-diff` smoke legs green.

The ticket record did not follow the merge — it stayed `claimed` with `pr: null`, so
`ticket.mjs inflight` went on naming `steward/t-0447-north-water-east-end` as a rival
branch on an open owner ticket and no run could take it. Closed against the PR that
actually landed it.

**The one red is still open and still owned elsewhere.** `the town's wagons vary in type
and in the way they stand` is T-0688 — the gate counts street bearings, so re-deriving a
street took it from 9 buckets to 7 against a floor of 8. #801 merged with that unresolved;
closing this ticket does not close that, and T-0688 keeps its place in the queue.

---
id: T-0812
title: The Steamboat Hotel's placement reads Kinzie Street at local N +276 and the committed kinzie record is at N +252.8
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 974
claimed_by: run 9/6/2026, 2:57:36 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T09:09:14.994Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34019964966
---

The Steamboat Hotel's placement reads Kinzie Street at local N +276 and the committed kinzie record is at N +252.8.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-0447 while re-deriving North Water Street's east end.

`data/structures/steamboat_hotel.json`'s placement note, written 2026-08-11, reads the
Wright 1834 sheet at this project's fitted affine and says:

> the Kinzie Street alignment runs due east at local N +276

The committed `kinzie` record in `data/streets/1835.json` runs `[-320, 263.1]`,
`[-181, 262]`, `[1100, 251.8]` — **N +252.8 at the easting the hotel is placed against**.
The two readings of the same street disagree by **23.2 m**, and the disagreement is
load-bearing in two places:

- the hotel itself stands at local `[968, 291]`, which is 15 m north of the prose
  alignment and **38.2 m north of the committed one**;
- North Water Street's east end is now derived as the crossing of the committed bank's
  offset curve with the committed `kinzie` line (T-0447), at E +973.6, N +252.9. The
  hotel's own note independently puts that convergence at "roughly local E +990" — 16.4 m
  east, inside its stated ±20 m — so the two agree about the CONVERGENCE and disagree
  about the NORTHING it happens at.

The visible consequence today: `tools/generate_business_signboards.py` refuses the
Steamboat Hotel a post board, because no street lies within 22 m of the wall it would
stand in front of, and gives it an awning board instead. That refusal is a true statement
about the committed records. It is the disagreement showing, not a fault in the sign rule.

**What has to be decided:** which reading of Kinzie Street is right, and then whether the
hotel moves onto the committed line or the committed line moves. `kinzie` carries no
control point of its own north of `kinzie_canal`, whose own entry already records a
queued 3.8 m correction. T-0451 is re-platting the North Division and owns Kinzie's
geometry; this ticket exists so that pass does not have to rediscover the hotel.

**Acceptance:**

1. The two readings of Kinzie Street's alignment are reconciled, with the winner stated
   and its evidence named.
2. `steamboat_hotel`'s placement either moves onto the ruled line or records why it
   stands off it, with the distance.
3. The signboard rule's refusal either goes away or is recorded as correct.

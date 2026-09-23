---
id: T-0445
title: West Water, Jefferson and Des Plaines: the three West Division streets the plat carries and no committed file holds
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0443
opened: 2026-08-31
closed: 2026-09-05
pr: 875
claimed_by: run 9/5/2026, 6:36:13 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T12:17:03.686Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33963532089
---

West Water, Jefferson and Des Plaines: the three West Division streets the plat carries and no committed file holds.

Piece 2 of 4 of **T-0443 — The West Division's street grid is short three north-south streets and two east-west, and what is drawn as Canal may be Clinton**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

Measured today: `data/streets/1835.json` holds 19 streets, of which exactly two
are west of the South Branch — `canal` (mid east −170.1 m) and `clinton` (mid
east −282.2 m). The Thompson plat's West Division carries five north-south
streets: **West Water, Canal, Clinton, Jefferson, Des Plaines**. Three of them
are held by nothing — not a line, not a refusal, not a queued node.

**Blocked in practice on T-0444.** Seating these three before the bank
measurement would nail the error in place if the grid really is one street west.

**Acceptance:**

1. `west_water`, `jefferson` and `des_plaines` each either exist in
   `data/streets/1835.json` with sources and a stated `geometry_confidence`, or
   are refused in writing with the reading that refuses them. Absent is not an
   answer.
2. If T-0444 found the grid shifted, the correction and these three additions
   are one re-derivation, not two passes — and every building, lot, frontage and
   street-face adoption seated off a moved line is re-derived, with the count of
   changed records reported.
3. `tools/check.sh` green.

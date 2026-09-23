---
id: T-1418
title: The professions: law offices and physicians' rooms to the July bracket's low end, with the order book re-cut to count the two census lines in the unit they count in
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1186
opened: 2026-09-19
closed: 2026-09-19
pr: 1544
claimed_by: run 9/19/2026, 7:52:18 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T01:27:47.520Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35478663043
---

The professions: law offices and physicians' rooms to the July bracket's low end, with the order book re-cut to count the two census lines in the unit they count in.

Piece 1 of 2 of **T-1186 — Reconstruct the missing professions and services: physicians and law offices to the State census's 14 and 22, land agents, surveyors, a dentist's stand, barbers, teachers, laundresses, seamstresses and domestics, as businesses or as no-premises employments**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

The parent's first clause, and the ruling that clause turns out to need. The December 1835
State census's two person-unit lines — twenty-two lawyers, fourteen physicians — are ordered
in MEN rather than in register records (T-1007's spend is the adjudication that makes the
join: 18 records are 13 men, 3 records are 8 men), and to the bracket the scene date puts
them in rather than to the December return: the count was taken over a town of 3,297 and the
town model brackets 1 July 1835 between 2,353 and 3,265, so each line scales with it and the
book orders to the LOW end, floored, never above it. A class the town already meets in the
counted unit orders nobody rather than a negative.

- `tools/build_order_book_1835.py` re-cuts ONLY the classes the spend rules `unit: person`;
  every premises-counted class keeps the reading it had. The bracket rides on the bucket as
  `scene_bracket` with both ends and the two population figures it was drawn from.
- `tools/reconstruct_businesses_1835.py --group professions_and_services` builds the shortfall:
  every proprietor adopted from the resident band's trade heads, never minted; every firm
  style and trade line a form the register itself prints; `street_only` faces off the
  register's own distribution of placed law offices and physicians' rooms.
- `--check` re-derives; `docs/LIBERTIES.md` carries one entry with its Scope counted;
  `docs/RESEARCH/business-naming-1835.md` carries the worked group.

**Stop condition:** the `businesses/lawyer` and `businesses/physician` buckets read filled
within the bracket, and neither is filled above its low end.

**Links:** T-1186 (the parent) · T-1007 (the unit) · T-1166 (the book) · T-1184 (the tool) ·
T-1173 (the heads) · T-1419 (the services, which own no census bucket).

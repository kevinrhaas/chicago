---
id: T-1419
title: The services: land agents and surveyors, a barber and a dentist's stand, teachers, and the female service trades as businesses where a woman kept a shop and no_fixed_premises employments where she did not
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1186
opened: 2026-09-19
closed: 2026-09-20
pr: 1558
claimed_by: run 9/20/2026, 3:18:33 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T09:20:56.288Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35498981086
---

The services: land agents and surveyors, a barber and a dentist's stand, teachers, and the female service trades as businesses where a woman kept a shop and no_fixed_premises employments where she did not.

Piece 2 of 2 of **T-1186 — Reconstruct the missing professions and services: physicians and law offices to the State census's 14 and 22, land agents, surveyors, a dentist's stand, barbers, teachers, laundresses, seamstresses and domestics, as businesses or as no-premises employments**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

The parent's second clause, and the reason it could not ride with the first: NONE of these
trades is a line of the December 1835 State census, so none of them has an order-book bucket,
and `tools/reconstruct_businesses_1835.py` may not invent a quota inside itself — its whole
contract is that the quota is read from the book. The route to these people is the PERSON
side, not the census side.

- Land agents (4 heads drawn), surveyors (2), milliners (9), a dressmaker, a laundress and
  the barber-surgeon already stand in the resident band's `trade_households` at their trades.
  A woman who kept a shop — milliner, dressmaker — gets a business; a laundress, seamstress or
  domestic gets `no_fixed_premises` on the role instead, which is a statement about the trade
  and not a gap in the layer.
- A dentist's stand and a second barber are the old programme's argument and need their
  evidence restated before either is raised.
- **Teachers are NOT this ticket's**: the census counts seven schools and that bucket is
  T-1188's.
- This ticket should be taken AFTER T-1404 lands, which raises a premises for every in-window
  trade that has none and will have moved most of this surface already. Read what T-1404 left
  short before drawing anything.

**Stop condition:** every in-window professional and service trade the layer carries either
keeps a business or carries `no_fixed_premises` with the rule that put it there.

**Links:** T-1186 (the parent) · T-1418 (the professions) · T-1404 · T-1188 · T-1189 · T-1174.

---
id: T-1364
title: The town model's arrival share is a count over the wrong denominator: it reads 1.605 of the town arriving in 1833-35 and -777 arriving before, because it divides every person's arrival year by the NAMED layer's 1,285
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-19
pr: 1514
claimed_by: run 9/19/2026, 6:30:17 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T12:08:21.106Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35440034547
---

The town model's arrival share is a count over the wrong denominator: it reads 1.605 of the town arriving in 1833-35 and -777 arriving before, because it divides every person's arrival year by the NAMED layer's 1,285.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while landing T-1174, which made a standing defect visible rather than causing it.
`tools/model_town_1835.py` builds the `arrival_and_origin` figure
`arrived_in_the_three_years_before_the_scene` by counting every person in the layer whose
arrival year is 1833, 1834 or 1835 and dividing by `people_the_layer_can_name` — 1,285,
which is the NAMED layer and excludes every reconstructed person. It already read 1.172
before T-1174 (a share above 1, and "only -221 came before 1833"); with 556 reconstructed
people carrying a drawn arrival year it now reads 1.605 and "-777 came before 1833".

Both numerator and denominator are defensible on their own and they do not belong in one
ratio. The fix is to pick one population and say which: the share of the WHOLE layer, or
the share of the named layer counted over the named layer's own arrivals. The `method`
sentence the figure prints has to name it either way, because a reader meeting "-777"
learns nothing except that something is wrong.

**Acceptance:** the figure is a share in [0, 1] with a stated denominator; the negative
complement is gone; `model_town_1835.py --check` re-derives it; no order-book target moves
(the figure feeds no bucket today, and if that stops being true the ticket says so).

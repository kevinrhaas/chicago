---
id: T-1511
title: The trade share counts buildings that front no street: nineteen Fort Dearborn reservation roofs 270-420 m from Lake Street vote in the principal class, because nearest_frontage has no distance bound
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-21
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The trade share counts buildings that front no street: nineteen Fort Dearborn reservation roofs 270-420 m from Lake Street vote in the principal class, because nearest_frontage has no distance bound.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1429 on 2026-09-21, working the bank test.

`measure_frontage_fabric.census()` assigns every committed building to the corridor it
stands NEAREST, however far that is, and `trade_share_by_class` then counts the
documented ones per traffic class. Fort Dearborn's reservation holds no street — that is
the whole of the garrison clause in `placement_policy_1835` and of six written outlier
reasons — and yet its nineteen roofs are counted somewhere. Before T-1429 they were
counted in `ordinary`, off a Kinzie Street line across the channel. After it they are
counted in `principal`, off Lake Street at 270 m to 420 m. The share the business front
is weighted by moved from 0.65 to 0.3846 on that alone, and `tools/reconcile_665.py`
re-deals eight trade roofs over four platted blocks from it.

Neither reading is a fact about the business front. The fault is the missing bound, not
the bank test that revealed it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. A bound on what counts as fronting a street is DERIVED rather than picked — in the
   spirit of `STREET_LINE_M`, which is the midpoint of a measured empty gap in the
   setback distribution, and not a number anybody chose. `--setbacks` prints the
   distribution it would come out of.
2. A building beyond it is reported with no street rather than with a distant one, and
   every consumer of the census — `trade_share_by_class`, `reconcile_665`,
   `redeal_anonymous_roofs`, `measure_face_rule`, `placement_policy_1835` — is read
   against that and says what it does with the absence.
3. The trade share is restated with its before and after, and the roofs
   `reconcile_665` re-deals as a consequence are named.
4. No outlier reason is deleted to make the new reading tidy: a roof that stops being
   scored against a street is a roof whose reason is re-read, not dropped.

---
id: T-1503
title: The lodging stage draws against a bucket's whole to_reconstruct and ignores filled, so re-cutting one undrawn slot re-deals all 56 seated lodgers and breaks the business layer's links to them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-21
closed: 2026-09-21
pr: 1635
claimed_by: run 9/21/2026, 11:40:04 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T17:23:04.122Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35626363865
---

The lodging stage draws against a bucket's whole to_reconstruct and ignores filled, so re-cutting one undrawn slot re-deals all 56 seated lodgers and breaks the business layer's links to them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1459** (PR #1611), which is the ticket this one stopped.

`tools/seat_lodgers_1835.py` reads each `lodging` bucket's whole `to_reconstruct` and
ignores `filled`. Its docstring says why, and the reason was good at the time: adding
`filled` back would make the second build draw against a bigger quota than the first and
`--check` would read that as drift. But the consequence is that a bucket the stage has
drawn against cannot have ONE undrawn slot re-cut without re-deriving the stage's ENTIRE
draw.

**Measured, 2026-09-21.** T-1459's re-cut moved 35 undrawn slots into the reopened 10_19
band. `seat_lodgers_1835.py --check` went red; re-deriving it re-dealt **25 of its 56**
invented boarders — same count, same 13 houses, nobody retired — and then **six further
gate steps failed**, because `rc_cavanagh_johanna`, a boarder the stage had invented, is
adopted by name as the keeper of `rcb_cavanagh_boarding_house` in the business layer,
seated by the employment join and answered for by the employment coverage pass. An
invented lodger, once another layer names it, is not re-dealable.

T-1459 therefore refuses to move any bucket carrying a `filled` at all, and says so in
`trade_re_cut.what_would_unlock_it`. That refusal is conservative on purpose and it costs
the town its whole 10-19 trade remainder: the band has 35 slots no person stands on, and
none of them can be spent.

**Acceptance:**

- The stage draws against `to_reconstruct - filled` — its own remainder — rather than
  against the whole quota, OR its draw is made stable under a quota change some other way
  (seeds keyed to the slot rather than to the bucket's size is the obvious candidate).
- The drift the current docstring warns about is guarded rather than avoided: `--build`
  twice in a row is a fixed point, and `--check` is clean on the first.
- The 56 cards standing today do not move. A fix that re-deals them to get there is the
  problem, not the solution — `rcb_cavanagh_boarding_house` and the employment join name
  them.
- With it in place, T-1459's re-cut is re-run and the 10_19 band's 35 undrawn slots either
  move or are refused for a NEW reason that is stated.

**Links:** T-1459 (the re-cut that stopped here) · T-1448 (the mint that wants the slots) ·
T-1175 / T-1371 (the stage and its draw) · T-1166 (owns the book) · T-1363 (the same
convergence shape, one layer up).

---
id: T-1393
title: Per-attribute completeness, and the model met: every person carries sex, age band, arrival, origin, reason, a role or a stated reason for having none, presence, division and household relationship — each at a tier — and the profile's unknown columns read zero or name the rows the sources contradict
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1179
opened: 2026-09-19
closed: 2026-09-19
pr: 1525
claimed_by: run 9/19/2026, 10:09:20 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T16:02:18.393Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35450782228
---

Per-attribute completeness, and the model met: every person carries sex, age band, arrival, origin, reason, a role or a stated reason for having none, presence, division and household relationship — each at a tier — and the profile's unknown columns read zero or name the rows the sources contradict.

Piece 2 of 3 of **T-1179 — Converge the reconstructed resident layer: index, sidecars, town census, People view and gates agree; every reconstructed person carries basis, seed, liberty and substitution rule; the population profile is re-run and the town reads complete against the model**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

`profile_population_1835.py` grows a **completeness** section that asks the nine
questions of EVERY person in the layer and answers them from the cards:

1. Nine axes — sex, age band, arrival, origin, reason for coming, a role or a stated
   reason for having none, presence on the scene date, division, household relationship —
   each counted per person, at the tier the card writes, with the rows that answer
   nothing NAMED by id rather than summed away.
2. Where an axis is answered by a bare string that carries no confidence anywhere on
   the card, it is counted in its own column and SAID to be untiered. A value with no
   tier is not a value at a tier, and this pass will not print it as one.
3. `--check` re-derives the section and the report byte for byte; the assertions refuse
   an axis whose answered and unanswered rows do not sum to the layer's persons.
4. The lead states which columns read zero and which do not, and names the ticket that
   fills each hole. An axis this layer cannot yet fill is reported, not rounded up.

**What this ticket does NOT do:** seat the 1,412 persons whose households stand
`unplaced` (T-1198, T-1199 own that ground), and does not write tiers onto the cards.
It measures, and the measurement is what says the layer is not there yet.

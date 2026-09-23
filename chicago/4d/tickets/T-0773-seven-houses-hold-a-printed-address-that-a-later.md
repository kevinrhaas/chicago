---
id: T-0773
title: Seven houses hold a printed address that a later printing outranks, and only an anchor_changes rule may reorder them
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 959
claimed_by: run 9/5/2026, 10:42:07 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T04:32:21.566Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34009497541
---

Seven houses hold a printed address that a later printing of the same house outranks.

Found while landing T-0440, which repaired the OTHER population: a house whose live
placement placed nothing at all while one of its own printings placed it. That one was not
a judgement — silence does not contradict speech — and thirteen houses were repaired by
taking the earliest printing that said something. These seven are the half that IS a
judgement.

`python3 tools/measure_placement_silence.py` prints them under *"a printed address
outranked by a later printed address"*, with the class each holds, the class it is
outranked by, how many distinct anchors its printings carry, and what the register does
with it today:

| house | holds | outranked by | distinct anchors | register |
|---|---|---|---:|---|
| `business_g_spring` | relative | corner | 6 | new_building |
| `business_j_k_botsford` | relative | corner | 8 | new_building |
| `business_j_s_c_hogan` | street_only | relative | 2 | enrich_existing |
| `business_newberry_dole` | street_only | relative | 2 | unplaceable |
| `business_p_pruyne_co` | relative | corner | 4 | enrich_existing |
| `business_rockwell_cabinet_furniture_warehouse` | street_only | relative | 2 | street_only |
| `business_samuel_lewis` | street_only | relative | 2 | street_only |

**Why no rule may do this in bulk.** Preferring one printed address to another is a
statement either about a house that MOVED or about an advertisement that was reset from
fresher copy, and the corpus rarely says which. `identity.json`'s `anchor_changes` is the
one mechanism that may say it: it names every reading verbatim, groups the spellings that
are one landmark with a `why`, refuses overlapping windows, and has to write down what it
cannot say. One rule exists today (Mason & Co.). Seven are owed one, or owed a stated
reason why the corpus cannot carry one.

Several are already the subject of their own tickets and this one must not overtake them
— T-0396 (Newberry & Dole's partner), T-0412 (P. Pruyne & Co.'s corner). Read those first;
this ticket is the LIST and the count, not a licence to re-place a house behind them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Each of the seven either gains an `anchor_changes` rule with its `why` and `cannot_say`,
  or a written statement in its own ticket of why the corpus cannot order its readings.
- No house is re-placed except through an authored rule; the compiler is not taught to
  prefer one printed address to another.
- `tools/measure_placement_silence.py` re-derives and the count moves for the reason given.

**Links:** T-0440 (the silent half, repaired) · `tools/measure_placement_silence.py` ·
`tools/compile_gazetteer.py` § the dated anchor change · T-0345 · T-0396 · T-0412.

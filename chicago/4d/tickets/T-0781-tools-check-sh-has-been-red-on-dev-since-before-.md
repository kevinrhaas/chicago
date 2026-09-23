---
id: T-0781
title: tools/check.sh has been red on dev since before 2026-09-05: four checks fail on an untouched checkout
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: fixed by T-0780 (#889) — yard goods, frontage works, north_water and the west_water duplicate all verified green on dev
needs_bake: false
closed_at: 2026-09-10T04:20:08.826Z
claimed_run: null
---

tools/check.sh has been red on dev since before 2026-09-05: four checks fail on an untouched checkout.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured 2026-09-05 on a pristine worktree of `f98d0c650` (T-0679, #815) — no working
changes at all.** `tools/check.sh` exits 1 with four failing steps:

| step | what it says |
|---|---|
| the yard goods re-derive from the rule that chose their frontages | `data/yard/town_trade_goods.json has drifted from the rule in tools/generate_yard_goods.py` |
| the frontage works re-derive from the rule that chose their walls | `FRONTAGE DRIFT` |
| north water street is still the line its own derivation produces, and still dry | fails |
| sidecars derived from data/ | `data/streets/1835.json: missing or duplicate street id 'west_water'` |

**Why this is worth its own ticket rather than a line in somebody's PR.** The gate is how a
run finds out whether its own change is sound, and a gate that is already red gives every
run the same answer whatever it did. Working T-0414 on 2026-09-05, the only way to tell that
`PLATTED BLOCK INFILL DRIFT` was a real consequence of that change was to build a second
worktree at the merge base, run the whole gate again there, and diff the two failure lists —
about eight minutes of a run's budget, spent to recover a signal the gate is supposed to give
for free. Every run on this repo is paying that now, or worse, is not paying it and is
merging on a red gate it has stopped reading.

The `west_water` one looks like the most tractable and the most alarming: a duplicate or
missing street id in `data/streets/1835.json` is a fault in a file a great deal is derived
from, and it stops the sidecars — the published payload — from being re-derived at all.

**Acceptance:** (state it before working — never weakened to pass)
- `tools/check.sh` exits 0 on an untouched checkout of dev.
- Each of the four is diagnosed and either FIXED or, if the drift is a legitimate committed
  state the generator no longer produces, the generator is corrected — not the check
  loosened, and not the drift blessed by regenerating over it without reading what moved.
- The `west_water` duplicate/missing id is named: which record, since when, and what merged
  it.
- If any of the four turns out to want more than one run's demonstration, `split` it rather
  than shipping a partial fix that leaves the gate red anyway.
- The commit that makes the gate green says what each of the four was, so the next reader
  does not have to re-derive the history from the diff.

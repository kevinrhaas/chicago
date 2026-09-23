---
id: T-0814
title: The synthesizer's write has drifted hundreds of household cards away from the repository and --check cannot see it, so T-0509's eight corroborations never reach a card
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: null
claimed_by: run 9/5/2026, 3:21:30 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T20:24:23.177Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33989596649
---

The synthesizer's write has drifted hundreds of household cards away from the repository and --check cannot see it, so T-0509's eight corroborations never reach a card.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured 2026-09-05, twice, on this run's own checkouts.** From a clean `dev` worktree,
with nothing else changed, `python3 tools/synthesize_resident_research.py` rewrites
**108 household cards**. On the same tree with T-0509's findings ledger and package added —
the diff this ticket is filed from — it rewrites **170**. So sixty-two of the cards this
cohort's reading is entitled to change are cards the write has never been run against.

**Why nothing catches it.** `--check` is green on both trees. It re-derives the population in
memory and validates the invariants; it does not compare its derivation against the committed
household files, so a writer whose output has drifted 108 files away from the repository still
reports `OK: 1404 people`, and `check.sh` is satisfied. Every other generated artefact here is
gated by re-derivation — `data/datum.json` is re-derived by `check.sh`, baked geometry by
`validate.py --stale` — and this one, which owns the `resident_research` block on every person,
is not.

**Why T-0509 did not fix it in passing, and no research PR should.** Running the write is not a
bookkeeping tidy. It promotes canonical facts onto people out of the `corroborated` rows, and it
would carry a hundred-odd cards of other passes' unspent work along with this cohort's eight, in
a pull request whose subject is a reading. Those promotions want to be read before they land,
by the ticket entitled to rule on them. T-0509 therefore committed the ledger and the package
and left every card alone, which is what its own acceptance asked for.

## The ask

1. **Gate the drift.** `--check` should fail, or at minimum report, when its derivation and the
   committed cards disagree — the same re-derivation contract `datum.json` and the GLBs are held
   to. Whatever else is decided, a writer 108 files out of step must stop being invisible.
2. **Then spend what is standing.** Run the write, read the promotions it proposes, and land
   them deliberately. State how many cards moved and what each promotion was drawn from.
3. **Keep the split honest.** Post-1835 readings live in `notes`, which the synthesizer does not
   promote from; contemporary evidence is what may reach `occupation`, `arrival_year` and the
   rest. Back-projection remains T-0633's settled rule and does not reopen here.

**Found by** the run that landed T-0509 (cohort 14), which measured the two numbers above rather
than inheriting them. An earlier run measured 459 on `dev` at 82abe294 on 2026-09-04 and filed
the finding on a branch that never merged; that figure is superseded by the two here.

**Links:** T-0509 · T-0510 · T-0513 · T-0514/T-0515 (the passes entitled to rule on grades) ·
T-0662 · T-0715 (the sibling staleness in `data/residents/index.json`).

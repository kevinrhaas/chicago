---
id: T-0999
title: Nothing in the gate can see a ruling that is simply GONE: a smaller resident_rulings.json is a legal one, and #1055 lost forty judgements under a green check.sh
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-14
pr: null
claimed_by: run 9/14/2026, 8:07:06 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T13:07:18.364Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34846525716
---

Nothing in the gate can see a ruling that is simply GONE: a smaller
`resident_rulings.json` is a legal one, and #1055 lost forty judgements under a green
`check.sh`.

**THE INCIDENT, in full, because the ticket is written from it.** On 10 September 2026
the merge lap pushed onto #1055 and `data/research/land_sales/resident_rulings.json`
conflicted. The file is `hand_authored`; the lap's regex resolution took the branch's
whole block for the second conflict, and that branch had been cut before T-0850 and
T-0990 cohort A ruled. Forty entries left the file on one line — T-0850's twenty-six and
cohort A's fourteen — and twelve resident cards silently got back a federal land purchase
each had been ruled it could not have. **#1073 restored them.** This ticket is the reason
nobody was told.

**Why the gate was green the whole time.** `read_land_sales.py --check` asks whether a
ruling is WELL FORMED: that it names a spelling the register holds, and a person the
proposal named. Every remaining ruling was. It has no question that a missing ruling
could fail, because **a smaller rulings file is a legal rulings file** — the eight
surviving entries re-derived perfectly into a crosswalk perfectly consistent with them,
and `check.sh` passed on #1055 and on every commit after it. The only witness was prose:
#1055's own `scope` paragraph still described the cohort A rulings the same commit had
deleted, and a run reading T-0990's cohort log for the remaining count found the
crosswalk said 129 where the log said 90.

**The shape of the problem is general, and that is the point.** This repository's
hand-authored evidence files are all append-mostly — rulings, `docs/LIBERTIES.md`, the
smoke register — and every gate it has re-derives DOWNSTREAM of them. A derivation cannot
see a shrinking input; it just derives less. `tools/dev-smoke-state.json` got a merge
driver for exactly this reason. Rulings did not.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- a check that FAILS when the number of adjudicated rulings in
  `resident_rulings.json` falls, counting `ruled[]` and `retired[]` together, so a
  retirement is a move and not a loss;
- it is run by `check.sh`, and its own refusal fires in the self-test the way the other
  steps' do — asserting on a tree with an entry removed;
- it is checked against the merge base rather than a committed number, so a branch cannot
  satisfy it by editing a total downwards in the same commit;
- a DELIBERATE removal is still possible and must state itself — the ticket that removes
  a ruling says so, the same way `retired[]` already carries its reason;
- the commits of the incident are the fixture: `07a6a1b04` (49) → `02ce7d97a` (8) must
  fail the new check, and `2e5aa8a02` (47 + 2) must pass it.

**Worth deciding while here, and not assumed:** whether this belongs to the land-sale
domain alone or to every `hand_authored: true` file in `data/research/`. The general
version is better and is more than one run — `split` it rather than shipping the narrow
one and calling the question closed.

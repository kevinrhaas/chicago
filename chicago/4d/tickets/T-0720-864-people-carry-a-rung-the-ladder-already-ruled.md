---
id: T-0720
title: 864 people carry a rung the ladder already ruled and no pass has written onto their card, 76 of them attested: spend the proposal onto the cards the civic mint does not own
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 927
claimed_by: run 9/5/2026, 4:50:43 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T22:27:14.551Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33994095741
---
**Measured by T-0692's `--coverage`, 2026-09-04, on dev.** Of the 1,404 person records in
`data/residents/`, 531 carry a `ladder_rule` and 873 do not — and for **864 of those 873 the
rung already exists**, ruled by the ladder and sitting in `grading_proposal.json`, with no
pass that ever carried it onto the card:

| rung | people | grade it proposes |
|---|---|---|
| G3 | 650 | `inferred` + `projected_resident` |
| G1b | 76 | **`attested`** |
| G2e | 56 | `inferred` |
| G5 | 36 | no proposal — the ladder abstains, and that abstention is itself the answer |
| G1a | 20 | **`attested`** |
| G2b | 16 | `inferred` |
| G1c | 10 | **`attested`** |

**Why nothing has done it.** `mint_civic_residents.py --build` re-writes grade and
`ladder_rule` for the 531 cards the civic mint owns, and `--regrade` (PR #797) applies the
convergence rung to those. Nothing owns the other ~870. `consolidate_resident_evidence.py`
writes no household file by design — it is a proposal, and keeping it one is what lets the
owner read a diff of every grade before any of them moves.

**This is the spend the owner asked for**, in the terms of his 2026-09-04 instruction: the
bottleneck is spending what is adjudicated, not reading another volume. 106 people carry an
`attested` rung today that their card does not say.

**Acceptance:** every person record whose coverage state is `proposed_not_written` either
carries the ruled rung on the card or appears on a conflict list with the reason it was
refused; no grade is DOWNGRADED to close the gap (a proposed demotion goes to the owner's
conflict list, as the 42 already do); `--coverage` reports the before and after; and
`ladder_coverage.json` re-derives under `check.sh` with the new counts.

---
id: T-0816
title: Two independent readings of cohort 14 disagree on 46 of its 76 people: T-0509 landed one and the other is on a dead branch
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 946
claimed_by: run 9/5/2026, 8:30:56 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T01:56:44.564Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34003861327
---

Two independent readings of cohort 14 disagree on 46 of its 76 people: T-0509 landed one and the other is on a dead branch.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**The finding.** Cohort 14 was read twice, by two runs that could not see each other, and the
two ledgers disagree. Both claim 76 of 76 complete with an empty `pending`, both dated
2026-09-05, and both are internally coherent:

| outcome | PR #831 / #901 — landed | `steward/t-0509-cohort-14-rerun` — not landed |
|---|---|---|
| `corroborated` | 8 | 18 |
| `corroborated_enrichment` | 14 | 11 |
| `candidate_identity` | 32 | 8 |
| `no_corroboration` | 22 | 39 |

Forty-six of the seventy-six sit in a different column depending on which ledger is read.

**Why the landed one was landed, and it is not because it is better.** It is PR #831's, the
pass of record, and it is eighteen files rather than a hundred and ninety-six, which is what
made it rebasable onto a `dev` that had moved fourteen hours. Nothing about that choice is an
argument about the readings. The second is on `steward/t-0509-cohort-14-rerun`, which also
carries a directed reading of **Fergus's Historical Series 26-29** against all 76 names — seven
initials resolved to full given names — that the landed ledger does not have.

**The interesting part is that the disagreement is a rule, not an error.** The landed pass takes
`corroborated` to require a contemporary town roll and refuses a newspaper that is the person's
own seed; the rerun's higher count reads a later volume's agreement as corroboration more often
and mints fewer unasserted candidates. Whichever is right, the project currently has two
defensible answers to the same question and no way to say which is its own.

## The ask

1. **Read both ledgers against each other** on the 46 that differ, and rule — person by person,
   with the discriminator written down, the way each pass ruled internally.
2. **Salvage the Fergus 26-29 reading** off the dead branch either way. It is quotation, not
   opinion, and it is lost when the branch is pruned.
3. **Say what stops this recurring.** Two runs read the same 76 people because `inflight` has a
   cold window; the rerun itself filed that defect and the filing died with it.

**Links:** T-0509 (landed, PR #901) · T-0492 (the frozen cohorts) · T-0510 (cohort 15, the model)
· T-0508 (cohort 13, unlanded) · T-0513.

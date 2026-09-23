---
id: T-0691
title: The letter-list cohort is 76 households out of step with its own derivation, and check.sh never looks
state: blocked-tech
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: null
pr: null
claimed_by: null
blocked_on: T-0660's owner ruling: whether a mint-time refusal (rules 7/8) may un-mint a standing letter-list record. T-0691's own acceptance says 'Do not work this before T-0660 is ruled on', and its acceptance 2 is 'whatever T-0660's ruling is, applied here by the same tool'. Acceptance 1 alone (wiring --check into check.sh) cannot ship on its own: the check is red today (the tree holds 727 letter-list households, the derivation gives 658), so wiring it turns the gate red without the ruling that says what to do about the 76.
needs_bake: false
closed_at: null
claimed_run: null
---

The letter-list cohort is 76 households out of step with its own derivation, and check.sh never looks.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND WHILE MEASURING T-0660, and it is the reason that ticket could not be closed as
written. `mint_letter_list_residents.py --check` re-derives the cohort from the register
and reports drift. It is red today, and has been for some time: the tree holds **727**
letter-list households and the pass, run against that same tree, derives **658**.
`tools/check.sh` runs this pass's `--gate` and its `--self-test` but NOT its `--check`
— the civic pass beside it is checked all three ways — so nothing has ever been red.

## Where the 87 retirements come from

Derived by `tools/report_letter_list_collisions.py`, and written into
`docs/RESEARCH/letter-list-surname-collisions.md`:

| households | cause |
|---|---|
| 76 | the town gained this surname from ANOTHER pass after this cohort was minted |
| 9 | the corrected reading of T-0638 collides them (T-0660, blocked on the owner) |
| 2 | no longer in the pool the register offers |

The 76 are refusal 7 applied retroactively. This pass sits last of the three and gives
way to any surname the town already names — but it gave way at MINT TIME, in 2026-08-30,
and the civic mint of T-0514 has since put 532 more people in the town. Every letter-list
record whose family name one of them shares is now a record its own tool would refuse to
mint. Nobody decided that; it is what the derivation does when the tree moves underneath
a cohort that is never re-derived.

## Why it is not just `--check` plus a re-run

Re-running the pass RETIRES 87 people and mints 18, and the retirements carry research
rows and directory matches — the same evidence-stranding T-0660 is blocked on, at eight
times the scale. So this ticket is not "make the tool run": it is the ruling about
whether a mint-time refusal may un-mint a standing record, and T-0660 holds the smaller
version of exactly that question. **Do not work this before T-0660 is ruled on** — the
answer there settles the rule and this applies it at scale.

**Acceptance:**

1. `python3 tools/mint_letter_list_residents.py --check` green, and the step wired into
   `tools/check.sh` beside the pass's existing `--gate` and `--self-test`, so the cohort
   cannot silently drift from its own derivation again.
2. Whatever T-0660's ruling is, applied here by the same tool to all 76 — not a second
   implementation of it.
3. The town's counts, `index.json`, the manifest and the published mirror all move
   together, and the movement is itemised against the table above.
4. No record's grade moves in either direction, and `bash tools/check.sh` green.



## THE RULING CAME, AND MOST OF THIS TICKET DISSOLVES (owner: (c), 2026-09-18)

T-0660 is ruled **(c)**: refusals 7 and 8 are MINT-TIME rules and do not un-mint a record
that already stands.

This ticket's subject was the 76 letter-list households out of step with their own pass —
727 standing in the tree against 658 the derivation gives. **Under this ruling they are not
out of step.** A standing record is not un-minted by a mint-time refusal, so there is no
discrepancy to resolve and nothing to retire.

**What survives is acceptance 1 alone:** wire `--check` into `check.sh`. That could not ship
before, because the check was red by construction while the ruling was open. It is no longer
red by construction, so it can.

**What is explicitly NOT in scope any more:** retiring any of the 76, changing `rank()`, or
re-deriving the cohort. If the work starts to look like any of those, it is the wrong branch.

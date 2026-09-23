---
id: T-0691
title: The letter-list cohort is 76 households out of step with its own derivation, and check.sh never looks
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-18
pr: 1445
claimed_by: run 9/18/2026, 1:54:28 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T07:55:40.692Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35316372496
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


## THE RULING LANDED, AND THIS TICKET IS THE HALF OF IT NOBODY COULD SEE (2026-09-18)

T-0660's blocker is gone: the owner ruled option (c) on 2026-09-18 — refusals 7 and 8 are
MINT-TIME rules, they do not un-mint a record that already stands, and what a run does with
a collision is SAY it. That ruling is this ticket's acceptance 2, and it needed no fresh
decision here.

**What was actually missing.** T-0660 wrote the `surname_collision` block onto the eight
cards its own corrected reading newly collides, and deliberately scoped out the other
sixty-seven — the ones THIS ticket is about, where the cohort minted a surname first and a
later pass then gave it to a better-evidenced record — on the grounds that they "land when
the cohort is next re-derived". They do not. That re-derive is T-1222's 798-file drift, and
T-0662 already found byte-identity to be the wrong contract for a pass that is not the last
writer of its own files, so it is not a re-derive anyone can run. Meanwhile sixty-seven
readers met a card that said nothing about the other holder of its family name, which is
precisely the thing option (c) chose to fix. The carve-out in
`report_letter_list_collisions.blocks()` is gone and the set is the pass's own: all 75
standing cards a mint-time refusal lands on.

**Acceptance 1 is T-1222's, and saying otherwise would be a fiction.**
`mint_letter_list_residents.py --check` cannot be a step at its own place in the pipeline —
`synthesize_resident_research.py` runs after it and rewrites the cohort's grade, subtype and
note, so a re-derive-and-diff there is red against a CORRECT tree. That is written into
`check.sh` above the mint and into `data/research/check_gate_baseline.json`, whose
`owner_ticket` moves from T-0691 to T-1222 with this: the 798 files are a pipeline-ordering
question and never were the collisions. What IS gateable is the ruling's own content, and
that is now a step — `report_letter_list_collisions.py --check-records`, with the break-it
assertion in the tool's `--self-test`.

**Where the block goes is not cosmetic.** Appending it at the end of the card instead of at
`record()`'s position turned 19 cards red against `spend_directories.py` and
`spend_old_settlers.py`, which re-derive the cards they write and compare byte for byte. The
write now places it directly after `research_note`, so it is a fixed point under every pass
downstream of it.

**Measured:** 75 standing cards carry a mint-time refusal, 8 said so, 67 now do; no person
added or removed, no grade moved, no id redirected; `check.sh` green.

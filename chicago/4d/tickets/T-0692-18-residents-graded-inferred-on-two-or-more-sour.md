---
id: T-0692
title: 18 residents graded inferred on two or more sources carry no ladder_rule at all: the consolidation never reached them
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 827
claimed_by: run 9/4/2026, 8:16:05 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T01:48:07.249Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33935445500
---

**Found while answering the owner's question of 2026-09-04** about people standing in several
sources who are still graded `inferred` (T-0699 holds that question). Counting the population turned
up a second, plainer fault underneath it.

## The finding

Over `data/residents/households/` on dev, of the **54** people graded `inferred` while citing two or
more sources:

| rule the ladder assigned | people |
|---|---|
| `G2b` — an 1833/1834 list with another source | 33 |
| `G2c` — the St Cyr register inside the scene window | 3 |
| **none — no `ladder_rule` field at all** | **18** |

**Those 18 were never graded by the ratified ladder.** They carry a grade from an earlier pass, and
`tools/consolidate_resident_evidence.py` has not reached them — so nothing in the record says which
rung their `inferred` rests on, and no rung can be argued with.

This is not the letter-list question. Those 33 G2b people have a rule, and it is defensible whether
or not the owner rules the way T-0699 asks. These 18 have no answer at all, which is a different
kind of gap: **an ungraded person cannot be regraded, because there is nothing to regrade from.**

## Why it matters more than 18 cards

The ladder's whole value is that `attested` and `inferred` mean something checkable. A person whose
grade predates the ladder is a person whose grade means whatever the pass that wrote it meant, and
the file does not say. `docs/RESEARCH/resident-grading-policy.md` records that the ladder as ratified
*"moves 159 of 849 people"* — that figure is only trustworthy for the people it actually reached.

## The ask

1. **Name them.** A `--report` listing every person record with no `ladder_rule`, with their sources
   and their current grade. Expect more than 18: the 54 above are only the multi-source subset of
   `inferred`, and the whole layer is 1,404 people against 531 carrying a rule.
2. **Run the ladder over them** with `consolidate_resident_evidence.py`, and land the result as a
   PROPOSAL first, as that tool already does — its own doc says *"It is a proposal. No household
   file was changed by this pass."* Do not spend the regrade in the same PR as the measurement.
3. **A rung that abstains is a result, not a failure.** G5 exists for exactly the case where the
   town carries a person on sources outside the seven consolidated domains (Andreas, the newspapers'
   own register). Those people should end up marked G5 with the conflict listed, not silently left
   ungraded — the difference between "the ladder abstained and said so" and "the ladder never looked"
   is the whole point of this ticket.
4. **Do not downgrade anyone to close the gap.** If the ladder proposes a demotion, it goes on the
   conflict list for the owner, as the 44 proposed downgrades already do.

**Done when** every person record in the residents layer either carries a `ladder_rule` or carries
G5 with its reason, the report says how many were in each state before and after, and the policy
doc's "moves N of M people" figure is restated against the full layer rather than the reached part.

---

## WHAT THE MEASUREMENT FOUND, 2026-09-04 — and it corrects this ticket's diagnosis

`consolidate_resident_evidence.py --coverage` now accounts for every person record in the
layer. The ticket was opened on a subset of 18 and read as *"the consolidation never
reached them"*. Over the whole layer that is true of **nine people, not 873**:

| | people |
|---|---|
| person records in `data/residents/` | 1,404 |
| carrying a `ladder_rule` on the card | 531 |
| **a rung already ruled and never written onto the card** | **864** — G3 650, G1b 76, G2e 56, G5 36, G1a 20, G2b 16, G1c 10 |
| absorbed: the row sits on an identity naming ANOTHER card as canonical | 2 |
| refused: the splitter built no identity, and says which guard fired | 7 |

**The fault is a SPEND, not a READ.** For 864 people the rung exists in
`grading_proposal.json` and nothing has ever carried it onto the card; 106 of those are
`attested` rungs. Filed as **T-0720**, which is the successor to this ticket.

**And the nine each say why now.** Seven were refusals the master had recorded all along
under a reason that is false of four of them — R1, *"names no forename"*, filed against
`8. G. Abbot` (which prints a forename initial) and `Rev. John Mary Irenaeus St Cyr` (which
prints three). R5 splits those out and every row names the guard that actually fired; 266
readings move from a false R1 to a true R5. The two absorbed cards were invisible because
`canonical_person_id` is `town[0]`, so an identity holding two town cards reported one and
dropped the other; master rows now carry `town_person_ids`.

**Nothing was applied.** `grading_proposal.json` is byte-identical across this pass: no
grade moved, no household file was touched, nobody was downgraded to close the gap. The
ticket is explicit that the measurement and the regrade do not ride in one PR.

**The three repairs the nine turned up** are their own tickets, because each is a different
job: **T-0721** (three cards named from an OCR misreading of an initial), **T-0723** (one
identity holding two town cards — a wife folded onto her husband, and a man carried twice),
**T-0724** (the four-token cap that turns away the parish priest).

**What guards it.** `invariants()` now fails if the coverage does not account for the whole
layer, if any person sits in state `unclassified`, or if any uncovered person states no
reason — so a person can never again go silently ungraded. Three self-test cases fire when
each of those is broken, and `check.sh` runs them.

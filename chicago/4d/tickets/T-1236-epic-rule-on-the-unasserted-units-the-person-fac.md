---
id: T-1236
title: EPIC: rule on the unasserted units the person-fact passes do not own — the land-sale, civic, 1830-census, church, newspaper and directory names, the resident-pass reserved people, and the book readings of ground, harbour, weather, price and institution
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-17
pr: null
claimed_by: run 9/17/2026, 5:36:56 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T22:37:14.422Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35281931694
---

EPIC: rule on the unasserted units the person-fact passes do not own — the land-sale, civic, 1830-census, church, newspaper and directory names, the resident-pass reserved people, and the book readings of ground, harbour, weather, price and institution.

Filed by T-1234, which spent the corpus its own title named — the book-domain PERSON
units and the letter-list name suspicions — and left behind the units the ledger's
default owner rule had been routing to it without its title ever covering them. This is
that remainder, and it is an EPIC: it is more than five tickets' worth and the loop does
not work it until the owner promotes pieces out of it.

**What is in it** (counts as of the ledger rebuilt on T-1234's PR):

| corpus | units | what a ruling would have to say |
| --- | ---: | --- |
| land_sales | 1,572 | a purchaser's name against the standing rule that a sale is never a residence |
| civic | 496 | the poll and voter names the civic crosswalk has not adjudicated |
| residents, cohort passes | 382 | the reserved people of the pilot and passes 02-15 whose findings name no exact structured field |
| newspapers | 378 | the person units of the thirteen held issues that no card names |
| church | 272 | the register entries outside the later-only and outside-Chicago rulings |
| census_1830 | 204 | the 1830 heads, five years before the scene and on the same ladder as 1840 |
| books, non-person readings | 61 | the ground, harbour, weather, price, shipping, institution and household readings |
| directories | 18 | the entries the directory pass left unruled |
| genealogytrails | 1 | one unit |

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. Each corpus above is taken as its own ticket, split out of this one when the owner
   promotes it, and closed by rulings that are WRITTEN — a rule with a statement and a
   note per unit, in the shape `data/research/spend_rulings.json` established, or by an
   assertion onto a structured resident field. A silent reclassification is a fail.
2. No ruling upgrades a confidence, mints a person or invents a citation, and a hand-off
   names an OPEN ticket whose field genuinely owns the finding.
3. `tools/measure_research_spend.py --check` stays green, and when the last corpus is
   ruled the ledger carries no unresolved unit owned by this ticket.

**Links:** T-1234 (the pass that filed this) · T-1232 · T-1143 · T-1147 · T-1157.


## BOUNDED, 2026-09-17 (owner's tightening)

This is an EPIC in the band the city is waiting behind, and an epic there is a hole the queue
drains into. It is not folded, because ruling on unasserted units is real work nothing else
covers. It is BOUNDED, on the same terms as T-1290 and T-1291:

**THE FIRST VERSION OF THIS BOUND SAID "four bodies" AND THAT WAS WRONG** — the table above
lists NINE corpora and 3,384 units. Corrected here rather than quietly, because the number is
the whole point: acceptance clause 1 as written says "Each corpus above is taken as its own
ticket", which licenses **nine tickets** out of one. **Clause 1 is overridden by this section.**

* **THE CAP IS THREE CHILDREN, and they are by WEIGHT, not by corpus.** land_sales (1,572) is
  the biggest single body and can stand alone; civic (496) with census_1830 (204) and
  directories (18) are the same question — a name on a roll — and go together; residents (382),
  newspapers (378), church (272), books (61) and genealogytrails (1) are the remainder and go
  together. Three tickets, not nine, and never one per corpus.
* **A unit that cannot be ruled on the evidence is recorded as unasserted WITH ITS REASON, and
  that is a finished answer.** This project prefers a refusal to an invention; an explicit
  refusal is the deliverable, not a deferral.
* **NO TICKET MAY BE FILED PER UNRULED UNIT — and 3,384 units is why that rule exists here
  more than anywhere else in the queue.** One that later blocks reconstruction is picked up by
  the ticket it blocks.
* The output is one table — unit, corpus, ruling or refusal, reason — plus one sentence per
  corpus saying what the residue does to the 1835 town. **"Nothing" is a complete answer**, and
  for census_1830 it is very likely the true one: those are 1830 heads, five years before the
  scene, on the same ladder T-1290 has already closed for 1840.
* `ticket.mjs new` now enforces a budget (T-1295): three tickets per branch, and nothing at all
  once the queue is at its ceiling, unless a run signs a written reason into the file. **This
  ticket is the reason that budget exists.**

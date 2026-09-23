---
id: T-1301
title: Spend the 98 corroborated_enrichment research units the remainder ruling hands to T-1160: each sourced fact about a person this town already holds written into the structured field that carries it, or repointed to the attribute-fill ticket whose acceptance owns it
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1160
opened: 2026-09-17
closed: 2026-09-18
pr: 1441
claimed_by: run 9/18/2026, 12:32:36 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T06:19:04.211Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35310585692
---

Spend the 98 corroborated_enrichment research units the remainder ruling hands to T-1160: each sourced fact about a person this town already holds written into the structured field that carries it, or repointed to the attribute-fill ticket whose acceptance owns it.

Piece 2 of 2 of **T-1160 — Profile the known population of 1 July 1835: sex, age, origin, arrival date and reason, roles, household composition, lodging, division and presence for every attested and inferred person, per attribute and per tier, as a generated report and an in-app card**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

## WHY THE SPLIT HAPPENED, AND WHAT THIS PIECE ACTUALLY OWES (2026-09-18)

The profile shipped in PR #1430 as T-1300 and `bash tools/check.sh` went red on the
ticket close — not on the work. `tools/spend_remainder_rulings.py` holds one rule,
`the_enrichment_names_an_attribute_no_field_carries`, whose `ticket` field is
**T-1160**, and `research_spend_ledger.py` holds that *a unit may only defer to work
that is still going to happen*. Closing T-1160 made 98 `corroborated_enrichment`
units defer to finished work and the gate said so, in the same words it said it to
T-1144 and T-1241.

That rule's own statement is what makes this a real remainder rather than a
bookkeeping snag: *"a real, sourced fact about a person this town holds — a trade,
an address, an origin, a kinship, a date — that extends the card and that no exact
source-bearing structured field on that card carries today. It is not refused,
because it is true research; it is not written here, because writing one attribute
at a time, out of one pass and without the other sources beside it, is how a layer
acquires facts it cannot defend."*

T-1160 was named as the pass that would read them. **It reads attributes; it does
not write them** — its whole output is a count of the layer by axis and tier, and
nothing in its acceptance puts a fact on a card. So the 98 are still owed, and the
pass that owes them is the one that writes an attribute with all of its sources
beside it. Whoever takes this piece decides, per enrichment, between two honest
endings and writes the reason either way:

* **write it** — the fact goes into the structured field that carries it, with its
  source, its date and its tier, through a generator and never as a hand edit; or
* **repoint it** — the rule's `ticket` moves to the attribute-fill ticket whose
  acceptance already owns that kind of fact: T-1168 (sex, age), T-1169 (arrival,
  origin, reason for coming), T-1170 (kin the sources name), T-1254 (a role with its
  stated place and employer), T-1189 (who works where).

A blanket repoint of all 98 to one id is the thing to avoid: the rule takes a single
ticket and the enrichments span five different fields, so one id would hand four of
them to a ticket whose acceptance does not mention them — which is how the unit ends
up deferring to work that is not going to happen a second time.

**Do not close this by loosening the ledger.** The invariant is the reason the
research spend can be audited at all; T-1241 records the same refusal and the same
decision not to weaken it.

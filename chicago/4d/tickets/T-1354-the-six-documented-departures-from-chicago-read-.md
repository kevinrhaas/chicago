---
id: T-1354
title: The six documented departures from Chicago, read against present_on_scene_date: whether a man recorded leaving in 1835 was at the town on 1 July, each ruled with the removal beside the other sources rather than out of one volume
state: done
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-21
pr: 1620
claimed_by: run 9/21/2026, 4:26:52 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T11:01:59.997Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35583036319
---

The six documented departures from Chicago, read against present_on_scene_date: whether a man recorded leaving in 1835 was at the town on 1 July, each ruled with the removal beside the other sources rather than out of one volume.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Why this exists.** T-1330's arrival-and-origin pass returned six `corroborated_enrichment`
units that name a **going** rather than a coming — a removal, a migration to another town, a
prospecting journey that ended somewhere else — for six men this town holds cards for:
`caldwell_billy`, `jones_benjamin`, `porthier_joseph`, `sweet_alanson`, `pugsley_john_k` and
`cleland_martin`. No field on a resident card carries a departure. The only thing a removal
bears on is `present_on_scene_date`, so the pass handed all six to T-1144 — "no false Chicago
resident, and no 1835 claim above its dated evidence" — and asserted nothing.

T-1144 was then **split** into T-1333 (the closing convergence rebuild) and T-1334 (the
letter-list mint's drift). Neither child banked this. T-1333's acceptances are a rebuild and
measured deltas; T-1334 is the identity rule. #1471's repoint sweep moved the one deferral it
was looking for and did not find this one, and #1489's strand fix moved it from the spent
parent onto T-1333 — a live ticket, which cleared the ledger, but not one whose acceptance
owns spending a departure. T-1172 is not the owner either: its R1 leg is scoped to the 893
**uncertain** presences, and these six are not all uncertain (`caldwell_billy` is `attested`
and `present`). So the departure question is an **unbanked remainder of T-1144's split**, and
this ticket is where it lands. Filed by T-1333's own run, which found it when closing.

1. Each of the six is ruled **one at a time**, with the removal read beside the other sources
   on that card — not out of the single volume the enrichment came from. A removal read alone
   is how a layer loses a resident it had evidence for.
2. A ruling either **moves `present_on_scene_date`** (with its tier and its reason recorded, and
   the prior value kept beside it as the evidence leg) or **records why the removal does not
   bear on 1 July 1835** — a departure dated after the scene date moves nothing, and saying so
   is a ruling, not a skip. Six rulings, no silent passes.
3. No grade moves, and no card is retired. A departure is evidence about a date, not about
   whether the man existed.
4. `data/research/residents/spend_rulings.json` carries the outcome: the
   `the_enrichment_names_a_departure_from_chicago_no_field_carries` row leaves `unresolved`
   and names what was spent, generated from `tools/spend_remainder_rulings.py` — never
   hand-edited, because it is derived.
5. The ledger re-derives clean on a clean tree, and `measure_research_spend.py --ledger-build`
   passes with no unresolved deferral pointing at a ticket that is not open.

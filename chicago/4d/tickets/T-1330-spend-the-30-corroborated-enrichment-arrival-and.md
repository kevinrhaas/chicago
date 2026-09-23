---
id: T-1330
title: Spend the 30 corroborated_enrichment arrival and origin units: each sourced arrival day, origin and dated departure written onto the household it names, or ruled in writing where it only corroborates
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1319
opened: 2026-09-18
closed: 2026-09-18
pr: 1465
claimed_by: run 9/18/2026, 12:13:17 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T18:16:45.445Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35371938176
---

Spend the 30 corroborated_enrichment arrival and origin units: each sourced arrival day, origin and dated departure written onto the household it names, or ruled in writing where it only corroborates.

Piece 2 of 2 of **T-1319 — Spend the land-sale and enrichment units: the entered tracts whose purchaser join the adjudication upheld, and the corroborated_enrichment rows naming an arrival or origin no structured field carries**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)

1. Every one of the thirty units is read against the card it names and does exactly one of
   three things: it is WRITTEN onto that card as a source-bearing `inferred` block, it is
   ruled in writing as CORROBORATING a date or a place the card already carries at equal or
   better precision, or it names a DEPARTURE no field on a resident card carries and is
   handed to an open ticket whose acceptance owns the field it bears on. There is no fourth
   outcome and `--self-test` refuses one.
2. A block is only written where the value it replaces is one the layer itself offered to
   retire: a block the arrival stage owns (`written_by_stage`, with a `replaceable_by`
   naming the source that retires it), or — one card — an `arrival` whose confidence is
   `reconstructed` and which cites no source, this project's own stated guess. No block a
   reading owns is touched, no grade moves, no person is minted, no identity reopens.
3. Every written block cites the volume its own finding names, that volume is a committed
   source record, and the block says which person it is about. `--self-test` asserts all
   three, because a citation nobody checked is how an invented one survives.
4. `tools/spend_enrichment_arrivals.py --check` re-derives every block, `--self-test` holds
   the rules over fixtures, and `tools/check.sh` runs both.
5. `measure_research_spend.py --check` green with **0** units owned by this ticket, and the
   `residents` domain's `asserted` count risen by the number of units actually written.

**What it cost the ledger, and why that is part of the acceptance.**
`tools/research_spend_ledger.py` closed a unit as `asserted` on one test: a structured field
on a card names the unit's record id AND cites a source the reading already carried. That
test cannot see a spend that brings a NEW volume, which is what seven of these nine are. So a
ruling may now carry the disposition `asserted`, and must prove it: `wrote` names the file
and the field, and the ledger re-reads every one of them — the file exists, the block is
there, it is attested/inferred/documented, it cites a source, and it says the person's id.
An assertion a register cannot show is a fault and not an assertion.

**Outcome, 2026-09-18:** 9 written (11 blocks on 9 cards), 15 corroborating, 6 departures to
T-1144. `residents` asserted 15 → 24, unresolved 91 → 67.

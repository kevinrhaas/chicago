---
id: T-1514
title: Tier the anonymous compiled business records in compile_businesses.py: 37 records whose only link to the advertisement that compiled them is an untiered claim_ids at the record root, so the 49 readings that built them can never be asserted
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-21
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Tier the anonymous compiled business records in compile_businesses.py: 37 records whose only link to the advertisement that compiled them is an untiered claim_ids at the record root, so the 49 readings that built them can never be asserted.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. Every compiled business record whose `claim_ids` are named nowhere but the record
   root carries a tiered, source-bearing block that names them — derived in
   `tools/compile_businesses.py` from the register and gazetteer row that built the
   record, never hand-edited onto the file, and re-derived by its `--check`.
2. The tier is the register's own, not an upgrade: an anonymous advertisement is what
   it is, and the block says what the notice says and cites the claim it says it in.
3. `tools/research_spend_ledger.py --build` then asserts the 49 readings against those
   blocks with no ruling, and `data/research/{newspapers,books}/spend_rulings.json`
   loses its `the_compiled_record_names_this_claim_and_tiers_no_field_to_it` rows —
   which is what a hand-off closing is supposed to look like.
4. `tools/audit_businesses.py --check` and the signboard derivation still hold.

**Where this came from (T-1509, 2026-09-21).** The ledger reaches the business layer on
a block that carries a tier AND cites a source (T-1508). 49 reading units name a claim
that 37 compiled records carry — at the record ROOT, in `claim_ids`, beside a root
`sources` list and `provenance: compiled_from_register`, and the root carries no tier.
The records' only tiered blocks are `locations` and `dates`, which are `inferred` from
the placement policy and cite nothing, and their `proprietors` and `partners` are empty
because the advertisement is anonymous — "a Chicago stove and hollow ware dealer, August
1835", "an iron and hardware stock, Chicago, June 1835". `person_entry` is what attaches
`claim_ids` at `attested` on this layer, and a record with no person never gets one.

So the reading compiled a whole record and no field of that record is attested from it.
T-1509 rules those 49 `unresolved` with the reason on each unit and hands them here; it
does not tier them, because the tier belongs in the generator that re-derives the layer
and a hand edit to `data/businesses/` is refused by `compile_businesses.py --check`.

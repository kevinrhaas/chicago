---
id: T-1468
title: Reconcile the research's trade, premises and firm readings against the finished business layer, and take the tavern identity question the roof programme is owed
state: split
epic: META
requested_by: loop
seen: false
effort: L
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T16:41:27.666Z
claimed_run: null
---

Reconcile the research's trade, premises and firm readings against the finished business layer, and take the tavern identity question the roof programme is owed.

**SIZED L, AND DELIBERATELY.** The research sign-off counts **601 units** on this owner — it
was the heaviest owner on T-1190 and it stays the heaviest here. `claim` refuses an L, which is
right: a run that takes this must `split` it first, by domain or by rule, rather than claim the
whole remainder and ship a self-invented piece of it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**T-1190 IS SPENT AS OF T-1442 (2026-09-20), AND FOUR PLACES WERE DEFERRING TO IT.** `ticket.mjs
done` said so on the close — *"a split parent whose children have all closed is SPENT WORK, and
any research unit that defers to it by id is now stranded (T-1237)"* — and
`measure_research_spend.py --check` and `spend_remainder_rulings.py --self-test` both went red
on it. This ticket is the live owner those four now name. **It is a routing ticket with real
work in it, not a placeholder**, and each hand-off is written out below.

1. **`the_enrichment_names_a_trade_or_premises_no_field_carries`** (`spend_remainder_rulings.py`).
   A completed research pass returned a real, sourced fact about a person the town holds — a
   trade, a shop, a tavern, a store or the premises one was kept at — that no exact
   source-bearing field on that card carries. It read T-1182 until that split and all five
   children closed, then T-1190 on the owner's call. What is left is unchanged: reconciling an
   existing reading against the layer, which is neither T-1189's staffing nor a reconstruction.
2. **`the_notice_names_a_firm`** (same file). The unit carries a `business` block — a firm name,
   and where the reading could get them a trade, a proprietor and a street placement, out of an
   advertisement or notice. It read T-1180, then T-1182, then T-1190. The layer is BUILT now
   (T-1310) and converged (T-1190's three pieces); what these notices need is to be reconciled
   against it.
3. **The `civic` and `business` domains in `research_spend_ledger.py`**, for the same reason.
4. **`inns_and_taverns`, owed out by `reprogramme_roofs_1835.py`.** The register holds more
   tavern records at the scene date than it folds, against the scheduled and standing roofs.
   Whether those records are that many HOUSES is an identity question — if they fold, the roof
   programme needs no change; if they do not, the group re-cuts against the folded count.
   T-1440 settled the *person* identities in this layer and left the *house* identities open.

**SIZED L, AND DELIBERATELY.** The research sign-off counts **601 units** on this owner — it
was the heaviest owner on T-1190 and it stays the heaviest here. `claim` refuses an L, which is
right: a run that takes this must `split` it first, by domain or by rule, rather than claim the
whole remainder and ship a self-invented piece of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- Every unit above reaches a structured field on a record, or is refused with its reason on the
  unit, and the remainder ruling for each says which it was. No unit is moved by widening a
  disposition.
- The tavern identity question is answered one way or the other, with the fold (or the refusal
  to fold) recorded on the records themselves, and the roof programme re-cut or explicitly left
  alone with the measurement that says why.
- `measure_research_spend.py --check` and `spend_remainder_rulings.py --self-test` are green
  without this ticket's id appearing as the heir of anything it has not actually taken.

---
id: T-1506
title: Retire the surplus reconstructed lawyer: businesses/lawyer is held at 2 drawn against an order of 1, because T-1299 admitted a documented attorney the town can name
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

Retire the surplus reconstructed lawyer: businesses/lawyer is held at 2 drawn against an order of 1, because T-1299 admitted a documented attorney the town can name.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1299** (2026-09-21), which is the ticket that shrank the order.

T-1299 admitted the press roles whose bound contains 1 July 1835 into the resident
`occupation` field. One of them is L. G. Curtiss, printed an attorney in the Chicago
Democrat of the scene date itself, and `tools/trade_census_spend_1835.py` now rules him
onto the census's lawyer line: `held_in_the_counted_unit` 13 -> 14.

`tools/build_order_book_1835.py` reads that figure as the lawyer bucket's `known`. The
target is 15, so the order fell from 2 to 1 — under the **2 records T-1418 had already
drawn against it**, `rcb_parmelee_lawyer` and `rcb_robillard_lawyer`.

**It is refused by name, not clamped, and not a fault.** T-1299 extended the refusal the
owner ruled on 2026-09-20 (T-1459) to business buckets: a quota that shrinks under work
already drawn is held at what was drawn, with both numbers on the record, and a `filled`
above even the order the book carried when the work was drawn is still a `Fault`. The row
stands in `recut_refusals` with `cause: a_documented_reading_shrank_the_order`.

So the book is honest and the town is not: it now carries **16 lawyers against a target of
15** — fourteen it can name and two it invented.

**Acceptance:**

1. One of the two reconstructed lawyer records is retired, chosen by the stage's own
   deterministic order rather than by hand: `build_group` takes candidates in `slot`
   order, so an order of 1 keeps the first and drops the second. Re-derive it; do not
   delete a file.
2. Everything the retired record is named by comes with it — its premises, any staff seat,
   the employment join and the employment coverage answer — or the retirement is refused
   and says which layer holds it. This is T-1503's lesson: an invented record another
   layer has adopted by name is not silently re-dealable.
3. `businesses/lawyer` comes off `recut_refusals` because the order and the fill agree
   again, and `no_bucket_overfilled` passes without the refusal path firing at all.
4. `businesses/physician` and `businesses/silversmith_jeweller` are checked for the same
   shape while the work is open — each is `filled: 1` against `to_reconstruct: 1` today,
   so either is one documented reading away from this.

**Links:** T-1299 · T-1418 · T-1459 · T-1503 · T-1166 · T-1007.

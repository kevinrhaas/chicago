---
id: T-1500
title: The 278 persons the order book's bed buckets still order have no live owner: T-1175 split, and every piece of its tree that fills a bed has closed
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The 278 persons the order book's bed buckets still order have no live owner: T-1175 split, and every piece of its tree that fills a bed has closed.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Why this exists.** T-1420's sweep of the order book's work orders (2026-09-21) found
the `persons/*/lodging/*` buckets — 59 cells, 278 persons still on order — pointing at
T-1175, which is `split`. Its tree: T-1370 (the lodging model) done, T-1371 (seat the
boarders) done, T-1372 split → T-1384 done, T-1385 split → T-1406 done and T-1407
`blocked-tech`. T-1407 is the crews of the vessels in port and the harbour-works gang
and nothing else, so it does not own these beds. The order book now names this ticket
so no bucket orders work from a ticket nobody can claim; WHO fills which bed, and
whether 278 is still the right remainder against the lodging model T-1370 wrote, is a
modelling decision T-1420 deliberately did not take.

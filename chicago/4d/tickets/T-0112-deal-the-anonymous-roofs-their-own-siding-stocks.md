---
id: T-0112
title: Deal the anonymous roofs their own siding stocks, in their recipes
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-19
closed: 2026-08-24
pr: 377
claimed_by: run 8/24/2026, 9:54:57 AM CT
blocked_on: null
needs_bake: true
---

Deal the anonymous roofs their own siding stocks, in their recipes.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)


The named frame buildings each carry a dealt `siding_exposure_m` since T-0049 (PR pending), but
the 129 anonymous programme records are byte-derived from their parcel recipes
(`tools/generate_block_infill.py` and kin), so the deal could not write into them — they all
still wear the archetypes' 0.14 m default, and `tools/deal_siding_stock.py` counts them as fixed
0.140 m neighbours.

**The ask:** teach the recipe generators to deal each anonymous frame roof a stock from the same
period set (4.5/5/5.5/6 in to the weather, tools/deal_siding_stock.py's bound), deterministically
so the records still re-derive, and keep the named deal's 60 m no-shared-stock separation across
both populations. Needs a bake of the anonymous frame roofs it touches.

**Acceptance:** two neighbouring anonymous frame roofs in any critic frame show different board
courses; `tools/deal_siding_stock.py --check`, every recipe `--check`, and the staleness gate all
green.

---
id: T-0886
title: The water at the foot of Randolph Street is the old channel behind the bar, not the lake: date the channel's 1835 state or find the carts' way across
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-11
pr: 1157
claimed_by: run 9/11/2026, 6:19:36 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T00:07:13.781Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34657469223
---

The water at the foot of Randolph Street is the old channel behind the bar, not the lake: date the channel's 1835 state or find the carts' way across.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0759 while placing the water cart, 2026-09-06.** Andreas says the watermen drove
into **the lake**, *"generally at the foot of Randolph Street"*
(`town_findings_andreas_v1#c013`). This project's own committed 1834 surfaces say the water
there is not the lake. Sampling the heightfield east along the `randolph` centreline extended:

| local east | what the committed surfaces give |
|---|---|
| to 1224 | dry land, falling to the waterline at east 1224.1 |
| 1224 – ~1305 | water, about -1.1 m at its deepest |
| ~1320 – ~1470 | the **sand bar**, standing dry at about +1.23 m |
| beyond ~1478 | the open lake |

So the water at Randolph's foot is the old southward channel behind the bar — the river-fed
water the same sentence has the settlers turning away from — and the lake proper is 254 m
further out across dry sand. `data/yard/town_water_cart.json` § `the_water_is_not_the_lake`
records the contradiction and picks none of the three readings open:

1. Andreas's *"the lake"* is loose for the water at the end of Randolph Street.
2. The old channel was closed, dry or fordable by July 1835. Wright 1834 draws it narrowing
   and shows the bar already cut through by the harbour works; **nothing in this repository
   dates the channel's state at the scene date**, and `data/terrain/1835_intown_water_dating.json`
   does not cover it — its declared zones are 15, 16 and 17, the in-town features.
3. The carts crossed the bar, and the street name marks where they left the town rather than
   where they stood in the water.

**Acceptance:** the channel's state on 1835-07-01 is dated from a source, or the three
readings are weighed and one adopted with the reasoning written into
`docs/RESEARCH/wells.md` § 5; whichever way it goes, the cart's position and its
`the_water_is_not_the_lake` block are brought into line with the answer, and if the answer
is that the channel was open water on the scene date then the terrain's own dating file is
the place that has to say so.

**Links:** T-0759 · **L227** · `docs/RESEARCH/wells.md` § 5 ·
`data/terrain/epochs/e1834_harbor_cut/shoreline.geojson` ·
`data/terrain/1835_intown_water_dating.json` · `data/yard/town_water_cart.json`

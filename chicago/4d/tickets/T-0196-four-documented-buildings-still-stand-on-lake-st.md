---
id: T-0196
title: Four documented buildings still stand on Lake Street's plank walk, the same OSM-kerb fault the South Water repair answered
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: 422
claimed_by: run 8/27/2026, 6:19:40 PM CT
blocked_on: null
needs_bake: false
---

Four documented buildings still stand on Lake Street's plank walk, the same OSM-kerb fault the South Water repair answered.

South Water Street is done: with all eleven of its documented placements back on the committed
plat, `tools/generate_frontage_works.py`'s march refuses **zero** steps for a wall anywhere on
that street. **Eleven refused steps are left in the town and all eleven are on LAKE Street**,
read off the march itself on 2026-08-27 rather than estimated:

| record | steps of the walk it stands on | out past its own frontage line |
|---|---|---|
| `old_bank_building` | 4 (`blk_lake_lasalle` north, 0.0–20.9 m) | 1.62 m |
| `dole_warehouse_south` | 3 (`blk_lake_dearborn` north, 0.0–15.5 m) | 1.28 m |
| `first_presbyterian_church` | 2 (`blk_lake_lasalle` north, 88.6–99.0 m) | 1.90 m |
| `st_marys_church` | 2 (`blk_lake_dearborn` north, 93.3–103.7 m) | 3.03 m |

Same fault, and each record says so in its own note: the coordinate came from a MODERN kerb
line read out of OpenStreetMap rather than from this project's committed street centreline.
The repair is the same one — translate along the block face's inward normal until the street
wall stands `LOT_MARGIN_M` (1.50 m) back from the committed frontage line, which is 3.12,
2.78, 3.40 and 4.53 m respectively.

**THE OWNER'S 2026-08-27 BUSINESS-FRONT RULING DOES NOT REACH THIS TICKET, and that was
measured rather than assumed.** The clause is bounded to a lot named in its block's own
`frontage` run in the committed parcel recipes. Reconciled onto the plat, all four of these
would seat on lots of `blk_lake_lasalle` and `blk_lake_dearborn` — **and neither block has a
frontage run at all.** Their roofs came from the pre-plat South Division parcel
(`recon_1835_south_*`), not from a block recipe with a declared commercial front, so there is
no business front here for the clause to sit on.

**So this ticket still stands, and it stands for a harder reason than South Water's.** Every
one of the four would land on a lot that already carries anonymous roofs, and the clause has
nothing to say about it:

| record | would seat on | which already carries |
|---|---|---|
| `old_bank_building` | `blk_lake_lasalle` lot 0 | `recon_1835_south_d4_009` |
| `dole_warehouse_south` | `blk_lake_dearborn` lot 0 | `mason_blacksmith_shop`, `recon_1835_south_d3_017` |
| `st_marys_church` | `blk_lake_dearborn` lot 6 | `recon_1835_south_a3_045`, `recon_1835_south_d6_020` |
| `first_presbyterian_church` | `blk_lake_lasalle` lot 6 | `physicians_office`, `recon_1835_south_a3_043`, `recon_1835_south_d6_012` |

That last row is the one to read first: `first_presbyterian_church` would come down beside
`physicians_office`, which T-0198 already named as a collision it would not walk into.

**Acceptance:** each of the four is either reconciled with the committed Lake Street plat —
moved along its block face's own normal, its along-street coordinate untouched, with the
metres and the derivation in its `position.note` — or refused in writing, per building, with
the lot it would take and what stands there named; `tools/generate_frontage_works.py`
re-derives and Lake Street's walk runs unbroken along each face except where its own ground
refuses it; `tools/measure_corridor_intrusion.py`'s baseline is rewritten to bank whatever is
repaired. **If the answer needs a rule rather than a metre — anonymous roofs standing where a
documented building belongs — it is the same shape of question the owner settled for the
business front and it goes to him, not to the loop.** Never by weakening a gate.

**Links:** T-0198 (the six) · T-0199 (the five, and the ruling) · T-0220 (the fork) ·
`tools/plat_occupancy.py` (the clause and its bounds) · T-0069, T-0127 (the street edge).

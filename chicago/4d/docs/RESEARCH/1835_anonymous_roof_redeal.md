# The 285 anonymous roofs, re-audited — July 1835

DERIVED — regenerate with `tools/redeal_anonymous_roofs.py --build`. T-1445.

an adjudication over committed derived files — no page of any source was opened, nobody is named, nothing is built, and no roof moves ground. tools/execute_roof_redeal.py carries the verdicts out; a verdict already carried out is gone from this file, because the roof it moved now conforms.

- audited: **433** anonymous roofs
- keep: **425** (4 kept over a policy breach because they are seated, 0 because nothing they could become is wanted here)
- refamily: **8** (5 of them into a band that already fits the committed footprint)
- retire: **0**

The programme wants 668 roofs and 541 stand, so the town is 127 roofs short before this audit and 127 after it. That is why `retire` is the rare verdict: there is almost nowhere a standing roof is surplus to what the order book can occupy.

## The district/group ledger

| bucket | target | standing | anonymous | head | after | head after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `structures/barns_stables/south` | 35 | 33 | 26 | 2 | 33 | 2 |
| `structures/barns_stables/west` | 20 | 14 | 11 | 6 | 14 | 6 |
| `structures/barns_stables/north` | 17 | 11 | 10 | 6 | 15 | 2 |
| `structures/barns_stables/fort` | 1 | 1 | 0 | 0 | 1 | 0 |
| `structures/fort_principal/fort` | 10 | 10 | 0 | 0 | 10 | 0 |
| `structures/inns_taverns/south` | 5 | 5 | 0 | 0 | 5 | 0 |
| `structures/inns_taverns/west` | 3 | 3 | 0 | 0 | 3 | 0 |
| `structures/inns_taverns/north` | 2 | 2 | 1 | 0 | 1 | 1 |
| `structures/institutional_public/south` | 5 | 5 | 0 | 0 | 5 | 0 |
| `structures/institutional_public/west` | 1 | 1 | 0 | 0 | 1 | 0 |
| `structures/institutional_public/north` | 3 | 3 | 0 | 0 | 3 | 0 |
| `structures/larger_boarding_houses/south` | 28 | 24 | 23 | 4 | 24 | 4 |
| `structures/larger_boarding_houses/west` | 6 | 3 | 3 | 3 | 3 | 3 |
| `structures/larger_boarding_houses/north` | 8 | 8 | 6 | 0 | 8 | 0 |
| `structures/ordinary_dwellings/south` | 176 | 129 | 120 | 47 | 131 | 45 |
| `structures/ordinary_dwellings/west` | 75 | 63 | 59 | 12 | 63 | 12 |
| `structures/ordinary_dwellings/north` | 84 | 58 | 52 | 26 | 60 | 24 |
| `structures/small_outbuildings/south` | 48 | 46 | 45 | 2 | 44 | 4 |
| `structures/small_outbuildings/west` | 14 | 5 | 5 | 9 | 5 | 9 |
| `structures/small_outbuildings/north` | 20 | 20 | 17 | 0 | 20 | 0 |
| `structures/small_outbuildings/fort` | 3 | 3 | 0 | 0 | 3 | 0 |
| `structures/stores_mixed_use/south` | 42 | 42 | 26 | 0 | 42 | 0 |
| `structures/stores_mixed_use/west` | 6 | 6 | 5 | 0 | 6 | 0 |
| `structures/stores_mixed_use/north` | 4 | 4 | 3 | 0 | 1 | 3 |
| `structures/stores_mixed_use/fort` | 1 | 1 | 0 | 0 | 1 | 0 |
| `structures/warehouses_freight/south` | 11 | 7 | 3 | 4 | 7 | 4 |
| `structures/warehouses_freight/west` | 2 | 1 | 1 | 1 | 1 | 1 |
| `structures/warehouses_freight/north` | 7 | 6 | 0 | 1 | 6 | 1 |
| `structures/workshops/south` | 15 | 11 | 8 | 4 | 11 | 4 |
| `structures/workshops/west` | 8 | 8 | 6 | 0 | 8 | 0 |
| `structures/workshops/north` | 7 | 7 | 3 | 0 | 5 | 2 |
| `structures/workshops/fort` | 1 | 1 | 0 | 0 | 1 | 0 |

## The 8 roofs that change

| roof | division | from | to | verdict | why |
| --- | --- | --- | --- | --- | --- |
| `recon_1835_blk_washington_market_a3_15` | south | A3 | D2 | refamily | the placement policy refuses this family here — stands on a principal street, which ancillary_behind_its_own_roof avoids; the slot is wanted and the position stands |
| `recon_1835_blk_washington_market_a4_12` | south | A4 | D2 | refamily | the placement policy refuses this family here — stands on a principal street, which ancillary_behind_its_own_roof avoids; the slot is wanted and the position stands |
| `recon_1835_north_c3_064` | north | C3 | A2 | refamily | the placement policy refuses this family here — stands on a light street, which commercial_front avoids; the slot is wanted and the position stands |
| `recon_1835_north_c3_066` | north | C3 | A2 | refamily | the placement policy refuses this family here — stands 3.44 m off the street line (2.71 m), and commercial_front puts it on the line; the slot is wanted and the position stands |
| `recon_1835_north_c4_067` | north | C4 | A2 | refamily | the placement policy refuses this family here — stands on a light street, which commercial_front avoids; the slot is wanted and the position stands |
| `recon_1835_north_t1_061` | north | T1 | A2 | refamily | the placement policy refuses this family here — stands 3.58 m off the street line (2.71 m), and lodging_near_the_landings puts it on the line; the slot is wanted and the position stands |
| `recon_1835_north_w2_065` | north | W2 | D6 | refamily | the placement policy refuses this family here — stands 3.64 m off the street line (2.71 m), and mechanics_streets puts it on the line; the slot is wanted and the position stands |
| `recon_1835_north_w3_062` | north | W3 | D6 | refamily | the placement policy refuses this family here — stands 3.54 m off the street line (2.71 m), and mechanics_streets puts it on the line; the slot is wanted and the position stands |

## The 4 breaches owed out

| roof | division | family | why it was kept |
| --- | --- | --- | --- |
| `inf_sawpit_shed` | south | W5 | the placement policy refuses this family here — stands on a principal street, which heavy_and_noxious_trades avoids — but the roof is seated and a seated roof is not re-dealt behind its household's back; the breach is owed to the seating tickets |
| `recon_1835_south_c3_040` | south | C3 | the placement policy refuses this family here — stands 14.64 m off the street line (2.71 m), and commercial_front puts it on the line — but the roof is seated and a seated roof is not re-dealt behind its household's back; the breach is owed to the seating tickets |
| `recon_1835_south_f1_038` | south | F1 | the placement policy refuses this family here — stands 12.87 m off the street line (2.71 m), and commercial_front puts it on the line — but the roof is seated and a seated roof is not re-dealt behind its household's back; the breach is owed to the seating tickets |
| `recon_1835_west_020` | west | C2 | the placement policy refuses this family here — stands 8.82 m off the street line (2.71 m), and commercial_front puts it on the line — but the roof is seated and a seated roof is not re-dealt behind its household's back; the breach is owed to the seating tickets |

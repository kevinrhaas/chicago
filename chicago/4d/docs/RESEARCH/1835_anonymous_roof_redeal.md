# The 285 anonymous roofs, re-audited — July 1835

DERIVED — regenerate with `tools/redeal_anonymous_roofs.py --build`. T-1445.

an adjudication over committed derived files — no page of any source was opened, nobody is named, nothing is built, and no roof moves ground. tools/execute_roof_redeal.py carries the verdicts out; a verdict already carried out is gone from this file, because the roof it moved now conforms.

- audited: **322** anonymous roofs
- keep: **314** (3 kept over a policy breach because they are seated, 0 because nothing they could become is wanted here)
- refamily: **8** (6 of them into a band that already fits the committed footprint)
- retire: **0**

The programme wants 668 roofs and 408 stand, so the town is 260 roofs short before this audit and 260 after it. That is why `retire` is the rare verdict: there is almost nowhere a standing roof is surplus to what the order book can occupy.

## The district/group ledger

| bucket | target | standing | anonymous | head | after | head after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `structures/barns_stables/south` | 35 | 16 | 15 | 19 | 16 | 19 |
| `structures/barns_stables/west` | 20 | 12 | 10 | 8 | 12 | 8 |
| `structures/barns_stables/north` | 17 | 8 | 8 | 9 | 8 | 9 |
| `structures/barns_stables/fort` | 1 | 1 | 0 | 0 | 1 | 0 |
| `structures/fort_principal/fort` | 10 | 10 | 0 | 0 | 10 | 0 |
| `structures/inns_taverns/south` | 5 | 5 | 0 | 0 | 5 | 0 |
| `structures/inns_taverns/west` | 3 | 3 | 0 | 0 | 3 | 0 |
| `structures/inns_taverns/north` | 2 | 1 | 0 | 1 | 1 | 1 |
| `structures/institutional_public/south` | 5 | 5 | 0 | 0 | 5 | 0 |
| `structures/institutional_public/west` | 1 | 1 | 0 | 0 | 1 | 0 |
| `structures/institutional_public/north` | 3 | 3 | 0 | 0 | 3 | 0 |
| `structures/larger_boarding_houses/south` | 28 | 9 | 8 | 19 | 9 | 19 |
| `structures/larger_boarding_houses/west` | 6 | 2 | 2 | 4 | 3 | 3 |
| `structures/larger_boarding_houses/north` | 8 | 6 | 5 | 2 | 6 | 2 |
| `structures/ordinary_dwellings/south` | 176 | 126 | 118 | 50 | 126 | 50 |
| `structures/ordinary_dwellings/west` | 75 | 51 | 48 | 24 | 53 | 22 |
| `structures/ordinary_dwellings/north` | 84 | 46 | 44 | 38 | 46 | 38 |
| `structures/small_outbuildings/south` | 48 | 23 | 23 | 25 | 23 | 25 |
| `structures/small_outbuildings/west` | 14 | 4 | 4 | 10 | 3 | 11 |
| `structures/small_outbuildings/north` | 20 | 9 | 9 | 11 | 9 | 11 |
| `structures/small_outbuildings/fort` | 3 | 3 | 0 | 0 | 3 | 0 |
| `structures/stores_mixed_use/south` | 42 | 26 | 11 | 16 | 26 | 16 |
| `structures/stores_mixed_use/west` | 6 | 4 | 3 | 2 | 3 | 3 |
| `structures/stores_mixed_use/north` | 4 | 1 | 0 | 3 | 1 | 3 |
| `structures/stores_mixed_use/fort` | 1 | 1 | 0 | 0 | 1 | 0 |
| `structures/warehouses_freight/south` | 11 | 4 | 1 | 7 | 4 | 7 |
| `structures/warehouses_freight/west` | 2 | 1 | 1 | 1 | 0 | 2 |
| `structures/warehouses_freight/north` | 7 | 6 | 0 | 1 | 6 | 1 |
| `structures/workshops/south` | 15 | 10 | 8 | 5 | 10 | 5 |
| `structures/workshops/west` | 8 | 5 | 3 | 3 | 5 | 3 |
| `structures/workshops/north` | 7 | 5 | 1 | 2 | 5 | 2 |
| `structures/workshops/fort` | 1 | 1 | 0 | 0 | 1 | 0 |

## The 8 roofs that change

| roof | division | from | to | verdict | why |
| --- | --- | --- | --- | --- | --- |
| `recon_1835_west_013` | west | A5 | D2 | refamily | the placement policy refuses this family here — stands on a principal street, which ancillary_behind_its_own_roof avoids; the slot is wanted and the position stands |
| `recon_1835_west_020` | west | C2 | D6 | refamily | the placement policy refuses this family here — stands 8.82 m off the street line (2.71 m), and commercial_front puts it on the line; the slot is wanted and the position stands |
| `recon_1835_west_046` | west | F1 | H2 | refamily | the placement policy refuses this family here — stands 36.74 m off the street line (2.71 m), and commercial_front puts it on the line; the slot is wanted and the position stands |
| `recon_1835_west_050` | west | D2 | D1 | refamily | the placement policy refuses this family here — fronts no street (its nearest corridor is 86.23 m away, beyond the frontage reach), and labourer_dwellings seats it by a `typology` setback, which is measured from one; the slot is wanted and the position stands |
| `recon_1835_west_051` | west | D2 | D1 | refamily | the placement policy refuses this family here — fronts no street (its nearest corridor is 131.25 m away, beyond the frontage reach), and labourer_dwellings seats it by a `typology` setback, which is measured from one; the slot is wanted and the position stands |
| `recon_1835_west_052` | west | D3 | D1 | refamily | the placement policy refuses this family here — fronts no street (its nearest corridor is 74.65 m away, beyond the frontage reach), and rear_dwelling_behind_its_own_roof seats it by a `yard` setback, which is measured from one; the slot is wanted and the position stands |
| `recon_1835_west_053` | west | D4 | A2 | refamily | the placement policy refuses this family here — fronts no street (its nearest corridor is 137.45 m away, beyond the frontage reach), and rear_dwelling_behind_its_own_roof seats it by a `yard` setback, which is measured from one; the slot is wanted and the position stands |
| `recon_1835_west_054` | west | A1 | D1 | refamily | the placement policy refuses this family here — fronts no street (its nearest corridor is 97.06 m away, beyond the frontage reach), and ancillary_behind_its_own_roof seats it by a `yard` setback, which is measured from one; the slot is wanted and the position stands |

## The 3 breaches owed out

| roof | division | family | why it was kept |
| --- | --- | --- | --- |
| `inf_sawpit_shed` | south | W5 | the placement policy refuses this family here — stands on a principal street, which heavy_and_noxious_trades avoids — but the roof is seated and a seated roof is not re-dealt behind its household's back; the breach is owed to the seating tickets |
| `recon_1835_south_c3_040` | south | C3 | the placement policy refuses this family here — stands 14.64 m off the street line (2.71 m), and commercial_front puts it on the line — but the roof is seated and a seated roof is not re-dealt behind its household's back; the breach is owed to the seating tickets |
| `recon_1835_south_f1_038` | south | F1 | the placement policy refuses this family here — stands 12.87 m off the street line (2.71 m), and commercial_front puts it on the line — but the roof is seated and a seated roof is not re-dealt behind its household's back; the breach is owed to the seating tickets |

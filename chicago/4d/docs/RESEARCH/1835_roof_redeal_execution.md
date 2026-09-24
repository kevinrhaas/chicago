# The anonymous-roof redeal, carried out — July 1835

DERIVED — regenerate with `tools/execute_roof_redeal.py --apply`. T-1451.

T-1445 adjudicated 285 anonymous roofs and moved none of them. This is the execution: the verdicts carried back into the authored recipes so the generators re-derive the records. It adjudicates nothing — every family below is the `to_family` T-1445 reached.

- refamily verdicts standing: **15**
- carried out here: **9** (the West Division parcel)
- outstanding, and why: **6** — the record id carries the family, so executing them renames a roof other files name (T-1481/T-1482/T-1484, over the surface `tools/measure_roof_id_migration.py` measures)
- retired: **0** — the guard stands empty and that is a measurement, not an omission

## Carried out

| roof | was | now | group | footprint ft | why |
| --- | --- | --- | --- | --- | --- |
| `recon_1835_west_008` | W1 | D4 | workshops → ordinary_dwellings | 20x28 | the placement policy refuses this family here — stands 3.81 m off the street line (2.71 m), and mechanics_streets puts it on the line; the slot is wanted and the position stands |
| `recon_1835_west_009` | W2 | D5 | workshops → ordinary_dwellings | 20x30 | the placement policy refuses this family here — stands on a light street, which mechanics_streets avoids; the slot is wanted and the position stands |
| `recon_1835_west_010` | A1 | D3 | barns_stables → ordinary_dwellings | 16x24 | the placement policy refuses this family here — stands on a principal street, which ancillary_behind_its_own_roof avoids; the slot is wanted and the position stands |
| `recon_1835_west_011` | A3 | D2 | small_outbuildings → ordinary_dwellings | 12x16 | the placement policy refuses this family here — stands on a principal street, which ancillary_behind_its_own_roof avoids; the slot is wanted and the position stands |
| `recon_1835_west_013` | A5 | D2 | small_outbuildings → ordinary_dwellings | 12x16 (was 8x10) | the placement policy refuses this family here — stands on a principal street, which ancillary_behind_its_own_roof avoids; the slot is wanted and the position stands |
| `recon_1835_west_020` | C2 | D6 | stores_mixed_use → ordinary_dwellings | 20x30 (was 20x36) | the placement policy refuses this family here — stands 8.82 m off the street line (2.71 m), and commercial_front puts it on the line; the slot is wanted and the position stands |
| `recon_1835_west_021` | W3 | D6 | workshops → ordinary_dwellings | 22x33 | the placement policy refuses this family here — stands 30.47 m off the street line (2.71 m), and mechanics_streets puts it on the line; the slot is wanted and the position stands |
| `recon_1835_west_022` | W4 | A1 | workshops → barns_stables | 18x26 | the placement policy refuses this family here — stands on a light street, which mechanics_streets avoids; the slot is wanted and the position stands |
| `recon_1835_west_046` | F1 | H2 | warehouses_freight → larger_boarding_houses | 24x36 (was 24x44) | the placement policy refuses this family here — stands 36.74 m off the street line (2.71 m), and commercial_front puts it on the line; the slot is wanted and the position stands |

## Outstanding — the id migration T-1481, T-1482 and T-1484 own

Each of these becomes a new id when its family moves, and the id is not private to its record. The files below name it today and would point at a roof that no longer exists. Counted over the committed tree; a record's own `data/structures/<id>.json` is not listed.

| roof | becomes | files that name it |
| --- | --- | ---: |
| `recon_1835_blk_randolph_market_a1_07` | `recon_1835_blk_randolph_market_d4_07` | 4 |
| `recon_1835_blk_randolph_market_a1_12` | `recon_1835_blk_randolph_market_d4_12` | 4 |
| `recon_1835_blk_randolph_market_a3_05` | `recon_1835_blk_randolph_market_d2_05` | 4 |
| `recon_1835_blk_randolph_market_a4_06` | `recon_1835_blk_randolph_market_d2_06` | 4 |
| `recon_1835_blk_south_water_lasalle_a1_06` | `recon_1835_blk_south_water_lasalle_d3_06` | 5 |
| `recon_1835_blk_south_water_wells_a1_07` | `recon_1835_blk_south_water_wells_d1_07` | 4 |

The 6 platted-block roofs among them, across 3 block(s) (`blk_randolph_market`, `blk_south_water_lasalle`, `blk_south_water_wells`), carry a second difficulty the West parcel does not. Their slots are `ancillary` — yard buildings off the block alley — and the family each is moved into is a dwelling. `generate_block_infill` gates a block's principal/ancillary split against the schedule the recipe claims, and refuses a second principal roof on a lot that already has one, so whether a rear cottage counts as the one or the other is a re-deal of the block and its claimed mix, not a field edit.


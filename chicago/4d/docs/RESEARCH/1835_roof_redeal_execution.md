# The anonymous-roof redeal, carried out — July 1835

DERIVED — regenerate with `tools/execute_roof_redeal.py --apply`. T-1451.

T-1445 adjudicated 285 anonymous roofs and moved none of them. This is the execution: the verdicts carried back into the authored recipes so the generators re-derive the records. It adjudicates nothing — every family below is the `to_family` T-1445 reached.

- refamily verdicts standing: **14**
- carried out here: **11** (the West Division parcel)
- West verdicts left standing by a partial `--only` execution: **3** — their ids do not move, so they wait on the ticket that owns their roofs, not on a migration
- outstanding, and why: **0** — the record id carries the family, so executing them renames a roof other files name (T-1481/T-1482/T-1484, over the surface `tools/measure_roof_id_migration.py` measures)
- retired: **0** — the guard stands empty and that is a measurement, not an omission

## Carried out

| roof | was | now | group | footprint ft | why |
| --- | --- | --- | --- | --- | --- |
| `recon_1835_west_008` | W1 | D4 | workshops → ordinary_dwellings | 20x28 | the placement policy refuses this family here — stands 3.81 m off the street line (2.71 m), and mechanics_streets puts it on the line; the slot is wanted and the position stands |
| `recon_1835_west_009` | W2 | D5 | workshops → ordinary_dwellings | 20x30 | the placement policy refuses this family here — stands on a light street, which mechanics_streets avoids; the slot is wanted and the position stands |
| `recon_1835_west_010` | A1 | D3 | barns_stables → ordinary_dwellings | 16x24 | the placement policy refuses this family here — stands on a principal street, which ancillary_behind_its_own_roof avoids; the slot is wanted and the position stands |
| `recon_1835_west_011` | A3 | D2 | small_outbuildings → ordinary_dwellings | 12x16 | the placement policy refuses this family here — stands on a principal street, which ancillary_behind_its_own_roof avoids; the slot is wanted and the position stands |
| `recon_1835_west_021` | W3 | D6 | workshops → ordinary_dwellings | 22x33 | the placement policy refuses this family here — stands 30.47 m off the street line (2.71 m), and mechanics_streets puts it on the line; the slot is wanted and the position stands |
| `recon_1835_west_022` | W4 | A1 | workshops → barns_stables | 18x26 | the placement policy refuses this family here — stands on a light street, which mechanics_streets avoids; the slot is wanted and the position stands |
| `recon_1835_west_050` | D2 | D1 | ordinary_dwellings → ordinary_dwellings | 16x20 (was 14x20) | the placement policy refuses this family here — fronts no street (its nearest corridor is 86.23 m away, beyond the frontage reach), and labourer_dwellings seats it by a `typology` setback, which is measured from one; the slot is wanted and the position stands |
| `recon_1835_west_051` | D2 | D1 | ordinary_dwellings → ordinary_dwellings | 16x22 | the placement policy refuses this family here — fronts no street (its nearest corridor is 131.25 m away, beyond the frontage reach), and labourer_dwellings seats it by a `typology` setback, which is measured from one; the slot is wanted and the position stands |
| `recon_1835_west_052` | D3 | D1 | ordinary_dwellings → ordinary_dwellings | 18x24 | the placement policy refuses this family here — fronts no street (its nearest corridor is 74.65 m away, beyond the frontage reach), and rear_dwelling_behind_its_own_roof seats it by a `yard` setback, which is measured from one; the slot is wanted and the position stands |
| `recon_1835_west_053` | D4 | A2 | ordinary_dwellings → barns_stables | 20x28 | the placement policy refuses this family here — fronts no street (its nearest corridor is 137.45 m away, beyond the frontage reach), and rear_dwelling_behind_its_own_roof seats it by a `yard` setback, which is measured from one; the slot is wanted and the position stands |
| `recon_1835_west_054` | A1 | D1 | barns_stables → ordinary_dwellings | 16x24 | the placement policy refuses this family here — fronts no street (its nearest corridor is 97.06 m away, beyond the frontage reach), and ancillary_behind_its_own_roof seats it by a `yard` setback, which is measured from one; the slot is wanted and the position stands |

## Standing West verdicts not carried out here

A partial execution (`--apply --only`, T-1781) took the roofs its ticket owns and left these for theirs. Each is still the verdict T-1445 reached, unexecuted.

| roof | family | verdict | group | why |
| --- | --- | --- | --- | --- |
| `recon_1835_west_013` | A5 | D2 | small_outbuildings → ordinary_dwellings | the placement policy refuses this family here — stands on a principal street, which ancillary_behind_its_own_roof avoids; the slot is wanted and the position stands |
| `recon_1835_west_020` | C2 | D6 | stores_mixed_use → ordinary_dwellings | the placement policy refuses this family here — stands 8.82 m off the street line (2.71 m), and commercial_front puts it on the line; the slot is wanted and the position stands |
| `recon_1835_west_046` | F1 | H2 | warehouses_freight → larger_boarding_houses | the placement policy refuses this family here — stands 36.63 m off the street line (2.71 m), and commercial_front puts it on the line; the slot is wanted and the position stands |

## Outstanding — the id migration T-1481, T-1482 and T-1484 own

**None.** All three have run, and the permanent record of each move is the recipe's own, because the adjudication is re-derived over the town as it stands and a roof that conforms returns `keep`: `tools/migrate_roof_ids.py --check` holds the phase-one South parcel's eleven against `data/reconstruction/1835_roof_id_migration.json`; `--check-migration` holds the North Division's nine against that parcel's `migrated` block; and `--check-blocks` holds the three platted blocks' six against `1835_platted_block_parcels.json`'s `redealt` block. The platted blocks were last, and they waited on an owner ruling rather than on a rename: their slots are yard buildings off a block alley and every family offered is a dwelling, so each promotion made a second principal roof on an occupied lot until the rear-cottage clause admitted a dwelling as ancillary there (T-1482 measured it, the owner ruled on 2026-09-23, T-1610 wrote the clause and T-1611 carried the six out).


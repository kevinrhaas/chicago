# The ground the 26 moving roof ids stand on — July 1835

DERIVED — regenerate with `tools/measure_roof_id_migration.py --build`. T-1483.

T-1445 returned 32 refamily verdicts; T-1451 carried out the 6 whose record id does not encode its family. These are the other 26. Each becomes a new id the moment its family moves, and the id is named across the tree. NOTHING IS MOVED HERE: this is the measurement the three carry-out tickets (T-1481 south, T-1482 the platted blocks, T-1484 north) each stand on.

- roofs whose id moves: **1**
- files that name one: **16**
- of those, **0** hold a reference a rename would falsify, **1** rename, **15** are re-derived by their own tool, **0** are frozen records of a past run

## The rows that cost judgement

A reference is not always a pointer. These assert what the roof IS, and the verdict moves it out of that — so a carry-out has to resolve them, not rename them. This is the list a scripted rename would have passed over.

| file | where | roof | group | becomes | why it is not a rename |
| --- | --- | --- | --- | --- | --- |

**0** reference(s), across 0 file(s).

## Every moving roof, and what names it

| roof | becomes | renamed | re-derived | frozen | adjudicated |
| --- | --- | ---: | ---: | ---: | ---: |
| `recon_1835_blk_west_randolph_des_plaines_w2_01` | `recon_1835_blk_west_randolph_des_plaines_d4_01` | 1 | 15 | 0 | 0 |

## Renamed — 1 file(s)

A plain pointer at the record. The migration rewrites the string and nothing else is owed.

| file | roofs | why |
| --- | ---: | --- |
| `tools/measure_group_district_rows.py` | 1 | a plain pointer at the record |

## Re-derived — 15 file(s)

Written by a tool, which `check.sh` re-runs. The migration must NOT hand-edit these; it re-runs the tool and commits what comes out.

| file | roofs | why |
| --- | ---: | --- |
| `data/enclosures/town_lot_line_rails.json` | 1 | generated_by tools/generate_lot_line_fences.py |
| `data/reconstruction/1835_block_redeal_remedies.json` | 1 | Derived |
| `data/reconstruction/1835_hay_limits.json` | 1 | Derived |
| `data/reconstruction/1835_lot_ledger.json` | 1 | DERIVED — regenerate with tools/seat_platted_ground_1835 |
| `data/reconstruction/1835_roof_redeal.json` | 1 | DERIVED — regenerate with tools/redeal_anonymous_roofs |
| `data/research/land_sales/ground.json` | 1 | generated_by tools/resolve_land_tracts.py --build |
| `data/research/newberry_index/lead_crosswalk.json` | 1 | GENERATED |
| `data/research/newberry_index/leads.json` | 1 | GENERATED |
| `data/sidecars/1835/index.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_west_randolph_des_plaines_w2_01.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/sources/owner_chicago_1835_reconstruction_spec_2026.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1904/index.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/signage/town_business_signboards.json` | 1 | The town's business signs |
| `docs/RESEARCH/1835_anonymous_roof_redeal.md` | 1 | DERIVED — regenerate with `tools/redeal_anonymous_roofs |
| `docs/RESEARCH/1835_block_redeal_remedies.md` | 1 | DERIVED — regenerate with `tools/measure_block_redeal_remedies |

## Frozen — 0 file(s)

A record of something that already happened. The id it names was the id at the time; rewriting it would make a receipt claim to have seen a building that did not exist under that name.

| file | roofs | why |
| --- | ---: | --- |

## Adjudicated — 0 file(s)

Listed above with the reference that has to be resolved.

| file | roofs | why |
| --- | ---: | --- |


# The ground the 26 moving roof ids stand on — July 1835

DERIVED — regenerate with `tools/measure_roof_id_migration.py --build`. T-1483.

T-1445 returned 32 refamily verdicts; T-1451 carried out the 6 whose record id does not encode its family. These are the other 26. Each becomes a new id the moment its family moves, and the id is named across the tree. NOTHING IS MOVED HERE: this is the measurement the three carry-out tickets (T-1481 south, T-1482 the platted blocks, T-1484 north) each stand on.

- roofs whose id moves: **6**
- files that name one: **22**
- of those, **0** hold a reference a rename would falsify, **4** rename, **16** are re-derived by their own tool, **2** are frozen records of a past run

## The rows that cost judgement

A reference is not always a pointer. These assert what the roof IS, and the verdict moves it out of that — so a carry-out has to resolve them, not rename them. This is the list a scripted rename would have passed over.

| file | where | roof | group | becomes | why it is not a rename |
| --- | --- | --- | --- | --- | --- |

**0** reference(s), across 0 file(s).

## Every moving roof, and what names it

| roof | becomes | renamed | re-derived | frozen | adjudicated |
| --- | --- | ---: | ---: | ---: | ---: |
| `recon_1835_blk_randolph_market_a1_07` | `recon_1835_blk_randolph_market_d4_07` | 3 | 9 | 2 | 0 |
| `recon_1835_blk_randolph_market_a1_12` | `recon_1835_blk_randolph_market_d4_12` | 0 | 9 | 2 | 0 |
| `recon_1835_blk_randolph_market_a3_05` | `recon_1835_blk_randolph_market_d2_05` | 0 | 9 | 2 | 0 |
| `recon_1835_blk_randolph_market_a4_06` | `recon_1835_blk_randolph_market_d2_06` | 0 | 9 | 2 | 0 |
| `recon_1835_blk_south_water_lasalle_a1_06` | `recon_1835_blk_south_water_lasalle_d3_06` | 1 | 10 | 2 | 0 |
| `recon_1835_blk_south_water_wells_a1_07` | `recon_1835_blk_south_water_wells_d1_07` | 0 | 9 | 2 | 0 |

## Renamed — 4 file(s)

A plain pointer at the record. The migration rewrites the string and nothing else is owed.

| file | roofs | why |
| --- | ---: | --- |
| `tools/execute_roof_redeal.py` | 1 | a plain pointer at the record |
| `tools/measure_block_redeal_remedies.py` | 1 | a plain pointer at the record |
| `tools/measure_roof_id_migration.py` | 1 | a plain pointer at the record |
| `tools/smoke_renderer.mjs` | 1 | a plain pointer at the record |

## Re-derived — 16 file(s)

Written by a tool, which `check.sh` re-runs. The migration must NOT hand-edit these; it re-runs the tool and commits what comes out.

| file | roofs | why |
| --- | ---: | --- |
| `data/enclosures/town_lot_line_boards.json` | 1 | generated_by tools/generate_lot_line_fences.py |
| `data/enclosures/town_lot_line_pickets.json` | 2 | generated_by tools/generate_lot_line_fences.py |
| `data/enclosures/town_lot_line_rails.json` | 4 | generated_by tools/generate_lot_line_fences.py |
| `data/reconstruction/1835_block_redeal_remedies.json` | 6 | Derived |
| `data/reconstruction/1835_roof_redeal.json` | 6 | DERIVED — regenerate with tools/redeal_anonymous_roofs |
| `data/research/land_sales/ground.json` | 6 | generated_by tools/resolve_land_tracts.py --build |
| `data/sidecars/1835/index.json` | 6 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_randolph_market_a1_07.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_randolph_market_a1_12.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_randolph_market_a3_05.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_randolph_market_a4_06.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_south_water_lasalle_a1_06.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_south_water_wells_a1_07.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `docs/RESEARCH/1835_anonymous_roof_redeal.md` | 6 | DERIVED — regenerate with `tools/redeal_anonymous_roofs |
| `docs/RESEARCH/1835_block_redeal_remedies.md` | 6 | DERIVED — regenerate with `tools/measure_block_redeal_remedies |
| `docs/RESEARCH/1835_roof_redeal_execution.md` | 6 | DERIVED — regenerate with `tools/execute_roof_redeal |

## Frozen — 2 file(s)

A record of something that already happened. The id it names was the id at the time; rewriting it would make a receipt claim to have seen a building that did not exist under that name.

| file | roofs | why |
| --- | ---: | --- |
| `docs/unreal/prototype/import_report.json.txt` | 6 | an import report from a dated Unreal prototype run |
| `renderers/unreal/receipts/mac-253f02657.json` | 6 | per-machine import receipts — each records one dated run on one tree |

## Adjudicated — 0 file(s)

Listed above with the reference that has to be resolved.

| file | roofs | why |
| --- | ---: | --- |


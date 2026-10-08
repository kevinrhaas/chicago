# The ground the 26 moving roof ids stand on — July 1835

DERIVED — regenerate with `tools/measure_roof_id_migration.py --build`. T-1483.

T-1445 returned 32 refamily verdicts; T-1451 carried out the 6 whose record id does not encode its family. These are the other 26. Each becomes a new id the moment its family moves, and the id is named across the tree. NOTHING IS MOVED HERE: this is the measurement the three carry-out tickets (T-1481 south, T-1482 the platted blocks, T-1484 north) each stand on.

- roofs whose id moves: **9**
- files that name one: **49**
- of those, **2** hold a reference a rename would falsify, **2** rename, **44** are re-derived by their own tool, **1** are frozen records of a past run

## The rows that cost judgement

A reference is not always a pointer. These assert what the roof IS, and the verdict moves it out of that — so a carry-out has to resolve them, not rename them. This is the list a scripted rename would have passed over.

| file | where | roof | group | becomes | why it is not a rename |
| --- | --- | --- | --- | --- | --- |
| `data/frontage/town_street_edge.json` | `.refused[154].structure_id` | `recon_1835_blk_south_water_dearborn_f2_11` | warehouses_freight | larger_boarding_houses | the refusal's own reason says “narrow_two_story_warehouse” — it is about the warehouses_freight that leaves: “recon_1835_blk_south_water_dearborn_f2_11 is a narrow_two_story_warehouse — a works and a warehouse took carts and drays at a yard gate, not riders at a post, which is the same distinction that hangs ” |
| `data/sidecars/1835/people.json` | `.people[1020].lives_at` | `recon_1835_north_t1_061` | inns_taverns | barns_stables | `lives_at` needs a dwelling and barns_stables is not one |

**2** reference(s), across 2 file(s).

## Every moving roof, and what names it

| roof | becomes | renamed | re-derived | frozen | adjudicated |
| --- | --- | ---: | ---: | ---: | ---: |
| `recon_1835_blk_south_water_dearborn_f2_11` | `recon_1835_blk_south_water_dearborn_h2_11` | 1 | 22 | 1 | 1 |
| `recon_1835_blk_washington_market_a3_15` | `recon_1835_blk_washington_market_d2_15` | 0 | 18 | 1 | 0 |
| `recon_1835_blk_washington_market_a4_12` | `recon_1835_blk_washington_market_d2_12` | 0 | 18 | 1 | 0 |
| `recon_1835_north_c3_064` | `recon_1835_north_a2_064` | 1 | 15 | 1 | 0 |
| `recon_1835_north_c3_066` | `recon_1835_north_a2_066` | 1 | 15 | 1 | 0 |
| `recon_1835_north_c4_067` | `recon_1835_north_a2_067` | 1 | 18 | 1 | 0 |
| `recon_1835_north_t1_061` | `recon_1835_north_a2_061` | 1 | 18 | 1 | 1 |
| `recon_1835_north_w2_065` | `recon_1835_north_a2_065` | 1 | 18 | 1 | 0 |
| `recon_1835_north_w3_062` | `recon_1835_north_w5_062` | 1 | 17 | 1 | 0 |

## Renamed — 2 file(s)

A plain pointer at the record. The migration rewrites the string and nothing else is owed.

| file | roofs | why |
| --- | ---: | --- |
| `docs/STATUS.md` | 1 | a plain pointer at the record |
| `tools/seat_trade_roofs_1835.py` | 6 | a plain pointer at the record |

## Re-derived — 44 file(s)

Written by a tool, which `check.sh` re-runs. The migration must NOT hand-edit these; it re-runs the tool and commits what comes out.

| file | roofs | why |
| --- | ---: | --- |
| `data/businesses/index.json` | 1 | DERIVED, NEVER AUTHORED |
| `data/enclosures/town_alley_lanes.json` | 3 | generated_by tools/generate_alley_lanes.py |
| `data/enclosures/town_entrance_aprons.json` | 9 | generated_by tools/generate_entrances.py |
| `data/enclosures/town_lot_line_rails.json` | 3 | generated_by tools/generate_lot_line_fences.py |
| `data/enclosures/town_yard_paths.json` | 3 | generated_by tools/generate_kept_ground.py |
| `data/liberties.json` | 9 | compiled from docs/LIBERTIES.md by tools/compile_liberties.py |
| `data/reconstruction/1835_address_book.json` | 1 | Derived |
| `data/reconstruction/1835_block_redeal_remedies.json` | 2 | Derived |
| `data/reconstruction/1835_business_reconstruction.json` | 1 | DERIVED from the reconstruction order book and the resident band's trade heads by tools/reconstruct_businesses_1835 |
| `data/reconstruction/1835_hay_limits.json` | 5 | Derived |
| `data/reconstruction/1835_lodgers_seated.json` | 1 | DERIVED |
| `data/reconstruction/1835_lodging_model.json` | 1 | DERIVED |
| `data/reconstruction/1835_lot_ledger.json` | 3 | DERIVED — regenerate with tools/seat_platted_ground_1835 |
| `data/reconstruction/1835_off_plat_ledger.json` | 6 | DERIVED — regenerate with tools/seat_off_plat_ground_1835 |
| `data/reconstruction/1835_off_plat_seats.json` | 6 | DERIVED — regenerate with tools/seat_off_plat_ground_1835 |
| `data/reconstruction/1835_platted_seats.json` | 1 | DERIVED — regenerate with tools/seat_platted_ground_1835 |
| `data/reconstruction/1835_refamily_rule.json` | 1 | No schema |
| `data/reconstruction/1835_roof_redeal.json` | 9 | DERIVED — regenerate with tools/redeal_anonymous_roofs |
| `data/reconstruction/1835_trade_roof_seats.json` | 5 | DERIVED — regenerate with tools/seat_trade_roofs_1835 |
| `data/research/land_sales/ground.json` | 9 | generated_by tools/resolve_land_tracts.py --build |
| `data/research/location_spend.json` | 1 | T-1147 clauses 3 and 4 |
| `data/research/newberry_index/lead_crosswalk.json` | 3 | GENERATED |
| `data/research/newberry_index/leads.json` | 3 | GENERATED |
| `data/research/newspapers/street_face_adoptions.json` | 1 | DERIVED, NEVER AUTHORED |
| `data/sidecars/1812/index.json` | 9 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/index.json` | 9 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_south_water_dearborn_f2_11.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_washington_market_a3_15.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_blk_washington_market_a4_12.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_north_c3_064.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_north_c3_066.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_north_c4_067.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_north_t1_061.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_north_w2_065.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/recon_1835_north_w3_062.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/sources/chicago_democrat_1833_1835.json` | 1 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/sources/isa_public_domain_land_tract_sales.json` | 5 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1835/sources/owner_chicago_1835_reconstruction_spec_2026.json` | 9 | compiled from the structure records by tools/compile_scene.py --all |
| `data/sidecars/1904/index.json` | 9 | compiled from the structure records by tools/compile_scene.py --all |
| `data/signage/town_business_signboards.json` | 6 | The town's business signs |
| `data/yard/town_kept_ground.json` | 3 | generated_by tools/generate_kept_ground.py |
| `data/yard/town_trade_yards.json` | 1 | Goods each WORKING trade kept in its own yard — casks at the cooperages, barrels at the packing and slaughter houses, boards at the joiners', hides at the tannery, a hay rick at th |
| `docs/RESEARCH/1835_anonymous_roof_redeal.md` | 9 | DERIVED — regenerate with `tools/redeal_anonymous_roofs |
| `docs/RESEARCH/1835_block_redeal_remedies.md` | 2 | DERIVED — regenerate with `tools/measure_block_redeal_remedies |

## Frozen — 1 file(s)

A record of something that already happened. The id it names was the id at the time; rewriting it would make a receipt claim to have seen a building that did not exist under that name.

| file | roofs | why |
| --- | ---: | --- |
| `docs/LIBERTIES.md` | 9 | append-only by its own rule; a liberty already taken is not rewritten, and the migration appends a new entry instead |

## Adjudicated — 2 file(s)

Listed above with the reference that has to be resolved.

| file | roofs | why |
| --- | ---: | --- |
| `data/frontage/town_street_edge.json` | 1 | a reference here asserts what the roof is, and the verdict moves it out of that |
| `data/sidecars/1835/people.json` | 1 | a reference here asserts what the roof is, and the verdict moves it out of that |


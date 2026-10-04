# The settled town's ground, before and after (T-2091, from T-2084)

Read 2026-10-04 at 1280x800 with `node tools/measure_detail_ceilings.mjs --town --flora --stepped --stands town_backyard,town_lake_shoulder,town_south_water_store --only desktop`, on the published mirror, dev @ d05fd637 before and this branch after. Triangles and draw calls are the renderer's own counters; `flora` is the same frame drawn once with the `flora` group hidden.

| tier | pose | triangles before | after | flora before | flora after | calls before | after |
|---|---|---:|---:|---:|---:|---:|---:|
| full | town_backyard | 3,179,128 | 2,866,776 | 545,853 | 252,893 | 255 | 250 |
| full | town_lake_shoulder | 2,212,313 | 2,076,602 | 295,450 | 155,131 | 237 | 231 |
| full | town_south_water_store | 2,242,022 | 2,177,833 | 230,309 | 167,512 | 229 | 225 |
| balanced | town_backyard | 2,412,248 | 2,242,447 | 315,365 | 145,564 | 244 | 239 |
| balanced | town_lake_shoulder | 1,793,932 | 1,713,852 | 151,475 | 71,395 | 223 | 221 |
| balanced | town_south_water_store | 1,851,522 | 1,812,723 | 104,007 | 65,208 | 229 | 224 |
| light | town_backyard | 1,094,371 | 1,039,674 | 99,646 | 44,949 | 85 | 80 |
| light | town_lake_shoulder | 893,907 | 867,973 | 49,257 | 23,323 | 83 | 81 |
| light | town_south_water_store | 834,311 | 818,675 | 35,483 | 19,847 | 82 | 78 |

Every flora total falls and no draw-call count rises; `light` stays under its 90-call floor at all three poses.

**Not read here** (T-2092): 390x780, T-0135's five stands, the phone heap, and before/after captures. On this runner one tier at eight stands with `--flora` costs the whole 600 s foreground call, so the full reading is its own run.

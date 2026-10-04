# The settled town's ground at both viewports, against production (T-2092, from T-2084)

Read 2026-10-04 with `node tools/measure_detail_ceilings.mjs --town --flora --stepped`, cut by `--stands`, `--levels` and `--only` so that each call finished inside 600 s, and pointed at two published mirrors with `--mirror`: **production** is `main` @ 2761a5ae (the 2026-10-03 promotion) and **dev** is `dev` @ c602f498 (T-2091, T-2089 and T-2082 all in). Triangles and draw calls are the renderer's own counters; `flora` is the same frame drawn once with the `flora` group hidden. Every stand was read once per tree, viewport and tier (96 readings); the in-town pass on the phone viewport was read twice and came back identical to the triangle. The rows are in `settled-town-ground-both-viewports.json`.

**Read this as dev against production, not as T-2084 against nothing.** Production is a day older than dev and dev carries the richer vegetation and the higher ceilings merged since (production's ceilings are 1,845,000 / 1,615,000 / 825,000; dev's are 2,840,000 / 2,145,000 / 1,040,000). T-2091's own reading (`settled-town-ground.md`) is the one that isolates the ground, and dev today reproduces its *after* at the three in-town poses to within 340 triangles (desktop `full`, back yard: 2,866,776 there, 2,866,436 here).

## What it says

| viewport | tier | T-0135's five: triangles prod → dev | flora prod → dev | in-town three: triangles prod → dev | flora prod → dev |
|---|---|---:|---:|---:|---:|
| desktop | full | 8,254,056 → 11,001,388 | 129,230 → 599,004 | 5,399,442 → 7,120,105 | 144,444 → 575,536 |
| desktop | balanced | 7,405,028 → 8,803,088 | 72,578 → 279,648 | 4,800,185 → 5,767,916 | 76,519 → 282,167 |
| desktop | light | 3,915,996 → 4,072,826 | 40,385 → 82,462 | 2,620,678 → 2,726,020 | 46,372 → 88,119 |
| mobile | full | 7,379,081 → 9,955,906 | 132,473 → 878,859 | 4,893,866 → 6,419,302 | 144,444 → 575,536 |
| mobile | balanced | 6,648,745 → 8,026,120 | 72,455 → 448,769 | 4,357,673 → 5,193,521 | 76,519 → 282,167 |
| mobile | light | 3,575,013 → 3,752,828 | 40,532 → 133,303 | 2,384,244 → 2,469,944 | 46,372 → 88,119 |

- **Against production, the frame is heavier almost everywhere**: triangles rise at 47 of 48 stand-tier-viewport readings, the flora's share at 45 of 48, draw calls at 45 of 48. The one place the flora falls is desktop's open aerial, at all three tiers (56,017 → 4,184 at `full`), while the same aerial on the phone rises (56,017 → 258,868): the aerial anchor frames differently at 390 wide and takes in prairie that 1280 does not.
- **Every T-0135 stand is inside dev's own ceilings at every tier on both viewports.** The tightest is desktop `balanced` at Lake Street and Canal, 1,936,751 of 2,145,000 (90 per cent).
- **The in-town poses are not budget stands, and two of them are over dev's ceilings on desktop**: the back yard at `full` (2,866,436, over 2,840,000 by 26,436) and at `balanced` (2,242,107, over 2,145,000 by 97,107); at `light` it clears 1,040,000 by 442 triangles. On the phone all three poses are inside every ceiling.
- **`light`'s 90-call floor holds**: the most any stand draws at `light` on dev is 81 calls (desktop, Lake Street shoulder), 78 on the phone.
- **The heap does not move one way.** Matched passes (same stands, tiers and viewport), MiB after a forced gc:

| viewport | pass | production | dev | change |
|---|---|---:|---:|---:|
| desktop 1280x800 | light, all eight | 904.4 | 888.9 | -15.5 |
| mobile 390x780 | light, all eight | 904.5 | 848.9 | -55.6 |
| mobile 390x780 | full, T-0135's five | 811.4 | 790.3 | -21.1 |
| mobile 390x780 | balanced, T-0135's five | 935.4 | 938.4 | +3.0 |
| mobile 390x780 | full,balanced, the in-town three | 867.7 | 880.4 | +12.7 |

  It falls in three passes and rises in two; the largest rise, +12.7 MiB on the phone viewport after the in-town poses at `full` and `balanced`, repeated to within 0.2 MiB on a second pass (867.5 → 880.3), so it is a real difference and not the collector's noise. It is Chromium's heap at 390x780 on a desktop browser, not a phone's.

## The captures

`settled-town-ground-2026-10/`, one per tree, viewport and pose, taken at the tier each page booted into with the welcome entered.

- **Lake Street's shoulder shows the change plainly**: production has knee-to-waist prairie grass and flowering forbs on both sides of the plank walk; dev has short, open ground with low rosettes, and one weed standing in the street margin. Same at 390x780.
- **The back yard and the storefront do not show the ground.** `town_backyard` (385, -450, facing north) stands about a metre from the back wall of a Washington Street house and `town_south_water_store` (501, -2, facing south) about a metre from the front of the store, so both captures are a wall at both viewports and in both trees; production's back yard shows prairie blades at the bottom edge and dev's shows none, which is all either says about the yard. Their triangle and flora readings are still the frame's own, but these two poses cannot carry T-2084's visual acceptance. Filed as T-2100.

## Every reading

| viewport | tier | stand | triangles prod | dev | flora prod | dev | calls prod | dev |
|---|---|---|---:|---:|---:|---:|---:|---:|
| desktop | full | sauganash_26 | 1,348,649 | 1,803,275 | 10,004 | 105,350 | 152 | 172 |
| desktop | full | lake_at_canal | 1,857,267 | 2,446,313 | 22,586 | 142,893 | 224 | 261 |
| desktop | full | the_forks | 1,775,428 | 2,456,313 | 32,314 | 235,478 | 187 | 225 |
| desktop | full | from_above | 1,669,507 | 2,195,640 | 56,017 | 4,184 | 168 | 170 |
| desktop | full | lake_and_market | 1,603,205 | 2,099,847 | 8,309 | 111,099 | 209 | 238 |
| desktop | full | town_backyard | 2,040,791 | 2,866,436 | 88,403 | 252,893 | 220 | 250 |
| desktop | full | town_lake_shoulder | 1,705,648 | 2,076,216 | 32,614 | 155,131 | 216 | 231 |
| desktop | full | town_south_water_store | 1,653,003 | 2,177,453 | 23,427 | 167,512 | 193 | 225 |
| desktop | balanced | sauganash_26 | 1,256,951 | 1,460,099 | 4,470 | 40,402 | 152 | 171 |
| desktop | balanced | lake_at_canal | 1,626,744 | 1,936,751 | 10,535 | 60,063 | 207 | 239 |
| desktop | balanced | the_forks | 1,563,954 | 1,936,108 | 19,436 | 125,489 | 171 | 207 |
| desktop | balanced | from_above | 1,499,491 | 1,698,552 | 34,001 | 840 | 164 | 165 |
| desktop | balanced | lake_and_market | 1,457,888 | 1,771,578 | 4,136 | 52,854 | 207 | 236 |
| desktop | balanced | town_backyard | 1,805,792 | 2,242,107 | 51,432 | 145,564 | 210 | 239 |
| desktop | balanced | town_lake_shoulder | 1,503,673 | 1,713,466 | 17,761 | 71,395 | 198 | 221 |
| desktop | balanced | town_south_water_store | 1,490,720 | 1,812,343 | 7,326 | 65,208 | 193 | 224 |
| desktop | light | sauganash_26 | 707,224 | 715,454 | 1,928 | 12,284 | 67 | 72 |
| desktop | light | lake_at_canal | 801,916 | 873,382 | 3,929 | 17,345 | 54 | 57 |
| desktop | light | the_forks | 851,431 | 902,727 | 11,721 | 37,258 | 57 | 60 |
| desktop | light | from_above | 813,093 | 804,182 | 20,921 | 136 | 60 | 54 |
| desktop | light | lake_and_market | 742,332 | 777,081 | 1,886 | 15,439 | 73 | 77 |
| desktop | light | town_backyard | 982,478 | 1,039,558 | 31,185 | 44,949 | 80 | 80 |
| desktop | light | town_lake_shoulder | 845,879 | 867,849 | 11,151 | 23,323 | 78 | 81 |
| desktop | light | town_south_water_store | 792,321 | 818,613 | 4,036 | 19,847 | 76 | 78 |
| mobile | full | sauganash_26 | 1,297,909 | 1,753,637 | 13,247 | 130,521 | 139 | 154 |
| mobile | full | lake_at_canal | 1,708,162 | 2,196,033 | 22,586 | 142,893 | 217 | 256 |
| mobile | full | the_forks | 1,490,928 | 2,010,826 | 32,314 | 235,478 | 174 | 203 |
| mobile | full | from_above | 1,522,707 | 2,253,270 | 56,017 | 258,868 | 145 | 152 |
| mobile | full | lake_and_market | 1,359,375 | 1,742,140 | 8,309 | 111,099 | 190 | 216 |
| mobile | full | town_backyard | 1,815,112 | 2,575,212 | 88,403 | 252,893 | 184 | 206 |
| mobile | full | town_lake_shoulder | 1,581,151 | 1,883,597 | 32,614 | 155,131 | 203 | 214 |
| mobile | full | town_south_water_store | 1,497,603 | 1,960,493 | 23,427 | 167,512 | 170 | 197 |
| mobile | balanced | sauganash_26 | 1,190,765 | 1,402,091 | 4,347 | 51,291 | 137 | 154 |
| mobile | balanced | lake_at_canal | 1,485,977 | 1,783,373 | 10,535 | 60,063 | 201 | 235 |
| mobile | balanced | the_forks | 1,335,176 | 1,602,257 | 19,436 | 125,489 | 148 | 174 |
| mobile | balanced | from_above | 1,378,035 | 1,702,158 | 34,001 | 159,072 | 145 | 152 |
| mobile | balanced | lake_and_market | 1,258,792 | 1,536,241 | 4,136 | 52,854 | 189 | 215 |
| mobile | balanced | town_backyard | 1,612,337 | 2,003,783 | 51,432 | 145,564 | 180 | 202 |
| mobile | balanced | town_lake_shoulder | 1,395,556 | 1,566,783 | 17,761 | 71,395 | 185 | 204 |
| mobile | balanced | town_south_water_store | 1,349,780 | 1,622,955 | 7,326 | 65,208 | 170 | 196 |
| mobile | light | sauganash_26 | 690,433 | 690,470 | 2,075 | 15,030 | 62 | 66 |
| mobile | light | lake_at_canal | 718,908 | 787,656 | 3,929 | 17,345 | 52 | 55 |
| mobile | light | the_forks | 755,526 | 791,555 | 11,721 | 37,258 | 51 | 54 |
| mobile | light | from_above | 769,222 | 803,246 | 20,921 | 48,231 | 61 | 64 |
| mobile | light | lake_and_market | 640,924 | 679,901 | 1,886 | 15,439 | 70 | 75 |
| mobile | light | town_backyard | 876,650 | 917,414 | 31,185 | 44,949 | 74 | 74 |
| mobile | light | town_lake_shoulder | 784,371 | 806,873 | 11,151 | 23,323 | 75 | 78 |
| mobile | light | town_south_water_store | 723,223 | 745,657 | 4,036 | 19,847 | 68 | 70 |

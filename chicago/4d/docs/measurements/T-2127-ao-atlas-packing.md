# T-2127 — the AO atlas's empty space, and one packing change (T-0286's half of T-0285)

Measured 2026-10-05 with `tools/measure_ao_atlas.py` under the pinned Blender 4.5.3.
Readings: `T-2127-ao-atlas-packing.json` (this folder). Nothing baked here ships, and
`--ao` remains opt-in: no committed master carries an occlusion map.

**The answer: the change roughly triples occupancy, and it should not be adopted.**
T-0286's premise was that two thirds of every occlusion PNG is bytes spent on blank
space. It is not. Texels no island owns hold one constant value, and PNG stores that
for almost nothing, so filling them spends MORE bytes, not fewer.

## The set

The first, middle and last structure of every archetype the scenes resolve, plus
`sauganash_hotel` (T-0158's calibration master): 31 masters, 30 read. `glessner_house`
is skipped by name: 731,781 faces, past the tool's 20,000-face ceiling. One pass over
it outlasts a run's 600 s foreground call, and a 1904 masonry mansion is not an
atlas-packing question.

**Calibration.** `sauganash_hotel` as shipped: 14.05 % of texel centres covered,
34.42 % once the bake's 4-px margin is added. T-0158 counted 31.1 % written; the
margin is a dilation estimate, not the bake's own, so the two agree to within it.
PNG 103.3 KB against T-0158's "~107 KB".

## Why every master is island-bound

- **One island per face, on every master read.** The archetypes are boxes, and a box's
  faces meet at 90°, past `smart_project`'s 66° limit (`angle_limit=1.15`). The
  operator's maximum is 89°, so no angle limit joins them. Welding the split vertices
  before the unwrap changed nothing (six masters).
- **`island_margin` does nothing.** On `sauganash_hotel`, 0.02, 0.005, 0.002 and 0 give
  the same occupancy (14.1 %), gap and density.
- **Occupancy is therefore island count × gap.** The shipped unwrap leaves 9 px centre
  to centre, two bake margins. `uv.pack_islands` at that same gap packs no better
  (`exchange_coffee_house` 31.2 → 16.8 %). At 3,991 islands (the drawbridge) it packs
  to nothing. Shrinking the gap is the only lever, and `sauganash_hotel` shows its
  price:

  | `pack_islands` margin | min gap (px) | occupancy |
  |---|---|---|
  | as shipped | 9 | 14.1 % |
  | FRACTION 3/512 | 7 | 23.7 % |
  | FRACTION 2/512 | 5 | 37.2 % |
  | SCALED 0.004 | 4 | 49.1 % |
  | SCALED 0.002 | 2 | 61.6 % |

## The change: `uv.lightmap_pack`, `PREF_MARGIN_DIV=0.4`, after `emit.unwrap`

The lightmap packer is Blender's operator for exactly this geometry: one quad per face,
laid edge to edge. A six-master sweep picked 0.4, the widest margin at which wall
density held on all six. At 0.6, `sauganash_hotel`'s walls already fell (43.9 → 42.4
t/m²).

**Totals over the 30:**

| | as shipped (512²) | the change (512²) | the change, density-matched |
|---|---|---|---|
| occupancy | 20.54 % | **56.00 %** | 63.70 % |
| atlas texels | 7,864,320 | 7,864,320 | 4,280,128 (−45.6 %) |
| occlusion PNG bytes | 3,137,560 | **6,117,516 (+95 %)** | 3,365,520 (+7.3 %) |
| master GLB bytes | 7,575,616 | 10,555,616 | 7,803,556 |
| narrowest island gap | 5 px | 2 px | 1 px |
| masters whose wall density fell | — | **5 of 30** | 5 of 30 |

"Density-matched" bakes each master at the smallest atlas side (capped at 512) that
keeps wall texel density at or above the shipped figure, both over all walls and on
the named wall. That is what the occupancy is worth in bytes: the same texels per
metre of wall in fewer texels. It needs 45.6 % fewer texels and still costs 7.3 % more
bytes. Tighter islands mean more edge, and edge does not compress.

**Texel density on a named wall.** Each master's named wall is its largest vertical
polygon (index, area and facing in the JSON; facing is in the master's own frame).
On `sauganash_hotel` it is polygon 1, 54.56 m²: **43.5 → 79.4 t/m² at 512², 43.7 at
380²**. It falls on five masters, because the lightmap packer does not scale faces
strictly by area:

- `fort_dearborn_barracks`: named wall 50.1 → 37.7
- `lake_house_construction`: named wall 281.2 → 241.8
- `bates_auction_room`: named wall 154.5 → 111.4
- `western_hotel`: walls 108.8 → 70.7, named 73.8 → 59.7
- `agency_striker_log_house`: named wall 950.9 → 820.6

T-0286 forbids buying occupancy that way, so even on its own terms the change fails
there.

**The bake still bakes.** Mean occlusion over covered texels on `sauganash_hotel`:
0.4649 shipped, 0.4046 packed. The per-master figures are in the JSON. No claim is
made about how any of it LOOKS: that is `tools/measure_ao_frame.mjs` (T-0227's rule),
and it was not run, because nothing here is adopted.

## What follows

- **Not adopted.** `generators/emit.py` is unchanged, which also keeps all 561
  committed masters fresh (`mesh_inputs.py` hashes emit.py's bytes).
  `measure_ao_atlas.repack()` stays in the tool as the measured candidate.
- **It strengthens T-2126's route.** Per-vertex AO ships no occlusion PNG at all. The
  byte cost of an atlas is the baked surface, not the empty space, so no packing
  recovers it.
- **Where the change does pay**, it is on masters the shipped unwrap starves: the
  drawbridge (0.9 t/m² of wall), the palisades and the piers. Density-matched, the
  drawbridge drops from 37.2 to 8.4 KB and the palisade from 29.8 to 7.9 KB, with
  no wall losing density. If an atlas ever ships for those archetypes alone, this reading
  is where to start.

## Per master

| master | archetype | islands | occ before → after | gap px | walls t/m² | named wall t/m² | PNG KB before → after | matched side, PNG KB |
|---|---|---|---|---|---|---|---|---|
| `chicago_lighthouse_1832` | fort_structure | 72 | 41.29 → 84.63 % | 10 → 3 | 570.8 → 991.0 | 626.5 → 689.4 | 84.5 → 142.1 | 492², 132.2 |
| `fort_dearborn_barracks` | fort_structure | 380 | 17.93 → 58.74 % | 9 → 3 | 43.1 → 123.8 | 50.1 → 37.7 | 113.5 → 201.0 | 512², 201.0 |
| `lake_house_construction` | fort_structure | 9 | 73.09 → 81.73 % | 5 → 5 | 280.7 → 301.9 | 281.2 → 241.8 | 213.9 → 227.1 | 512², 227.1 |
| `chicago_lighthouse_keepers_quarters` | frame_dwelling | 168 | 37.92 → 70.01 % | 10 → 3 | 560.2 → 793.8 | 615.6 → 798.6 | 143.5 → 211.1 | 452², 167.8 |
| `recon_1835_blk_washington_wells_h1_03` | frame_dwelling | 359 | 21.26 → 60.3 % | 10 → 3 | 116.1 → 175.9 | 116.1 → 119.6 | 104.9 → 201.6 | 508², 197.9 |
| `wright_building_to_let_b` | frame_dwelling | 197 | 36.86 → 72.01 % | 10 → 3 | 373.3 → 551.0 | 402.0 → 445.5 | 137.4 → 193.9 | 488², 176.5 |
| `dearborn_street_drawbridge` | bridge_timber | 3991 | 0.42 → 15.01 % | 7 → 5 | 0.9 → 35.7 | 0.9 → 41.6 | 37.2 → 233.7 | 84², 8.4 |
| `north_branch_bridge` | bridge_timber | 1241 | 2.87 → 42.61 % | 10 → 5 | 10.9 → 279.6 | 11.0 → 150.8 | 118.1 → 262.2 | 140², 24.9 |
| `south_branch_raft_bridge` | bridge_timber | 1051 | 3.5 → 46.38 % | 10 → 5 | 17.6 → 364.7 | 17.8 → 184.2 | 122.9 → 259.7 | 160², 32.1 |
| `emigrant_camp_shore` | camp | 991 | 6.83 → 54.21 % | 12 → 3 | 41.1 → 346.4 | 34.3 → 283.3 | 93.5 → 219.3 | 180², 33.0 |
| `landing_camp_west` | camp | 276 | 29.62 → 73.86 % | 12 → 3 | 670.5 → 1770.2 | 567.4 → 1485.9 | 140.1 → 204.4 | 320², 84.6 |
| `west_approach_wagon_camp` | camp | 600 | 10.18 → 58.72 % | 12 → 3 | 137.7 → 855.1 | 150.9 → 810.0 | 96.4 → 175.7 | 224², 41.4 |
| `bates_auction_room` | frame_storefront | 186 | 26.75 → 63.7 % | 9 → 3 | 154.5 → 189.8 | 154.5 → 111.4 | 107.5 → 191.7 | 512², 191.7 |
| `recon_1835_blk_south_water_clark_f2_01` | frame_storefront | 615 | 12.42 → 48.94 % | 9 → 3 | 42.2 → 203.2 | 42.2 → 58.4 | 47.6 → 65.1 | 436², 50.4 |
| `thomas_church_store` | frame_storefront | 389 | 15.57 → 51.89 % | 9 → 3 | 71.9 → 138.0 | 71.9 → 91.6 | 83.7 → 197.0 | 456², 160.8 |
| `exchange_coffee_house` | frame_tavern | 126 | 31.16 → 68.21 % | 8 → 3 | 126.3 → 171.7 | 101.0 → 157.3 | 113.2 → 221.1 | 440², 165.8 |
| `recon_1835_north_h2_022` | frame_tavern | 149 | 34.99 → 67.63 % | 9 → 3 | 190.2 → 199.0 | 112.9 → 189.1 | 125.1 → 218.4 | 504², 211.6 |
| `western_hotel` | frame_tavern | 132 | 41.49 → 68.6 % | 8 → 3 | 108.8 → 70.7 | 73.8 → 59.7 | 127.7 → 225.3 | 512², 225.3 |
| `agency_striker_log_house` | log_dwelling | 146 | 38.93 → 78.82 % | 11 → 3 | 856.3 → 1543.9 | 950.9 → 820.6 | 156.6 → 205.9 | 512², 205.9 |
| `recon_1835_blk_south_water_dearborn_d1_05` | log_dwelling | 167 | 36.95 → 72.77 % | 10 → 3 | 517.3 → 981.2 | 566.4 → 796.6 | 151.5 → 196.6 | 432², 143.4 |
| `wolf_point_tavern` | log_dwelling | 328 | 26.14 → 70.67 % | 10 → 3 | 187.6 → 471.6 | 203.0 → 362.7 | 128.4 → 192.7 | 384², 113.1 |
| `beaubien_barn` | outbuilding | 409 | 17.3 → 60.36 % | 11 → 5 | 140.2 → 820.9 | 102.4 → 502.7 | 100.7 → 193.8 | 232², 48.5 |
| `recon_1835_blk_south_water_lasalle_a1_14` | outbuilding | 539 | 12.68 → 51.21 % | 11 → 5 | 80.7 → 534.5 | 62.4 → 264.6 | 98.5 → 194.9 | 252², 57.9 |
| `wolf_point_tavern_stable` | outbuilding | 479 | 14.31 → 56.38 % | 11 → 5 | 69.0 → 572.6 | 51.2 → 294.4 | 92.9 → 197.2 | 216², 43.5 |
| `first_fort_dearborn_pickets_inner` | palisade | 2916 | 0.68 → 27.41 % | 9 → 3 | 1.4 → 56.3 | 1.4 → 15.7 | 48.6 → 194.2 | 156², 25.2 |
| `fort_dearborn_garrison_garden` | palisade | 1872 | 1.42 → 41.27 % | 10 → 5 | 4.3 → 100.6 | 3.9 → 76.6 | 71.3 → 191.5 | 116², 14.1 |
| `fort_dearborn_palisade` | palisade | 6200 | 0.2 → 12.72 % | 6 → 2 | 0.2 → 12.4 | 0.2 → 8.8 | 29.8 → 199.1 | 80², 7.9 |
| `north_pier` | pier_crib | 2550 | 2.06 → 29.93 % | 8 → 5 | 1.2 → 12.3 | 1.2 → 2.2 | 47.6 → 248.7 | 380², 135.4 |
| `south_pier` | pier_crib | 1105 | 7.27 → 43.82 % | 10 → 5 | 8.6 → 43.9 | 8.6 → 20.4 | 97.7 → 232.2 | 336², 108.9 |
| `sauganash_hotel` | frame_tavern | 626 | 14.05 → 47.46 % | 9 → 3 | 43.9 → 86.4 | 43.5 → 79.4 | 103.3 → 220.1 | 380², 129.1 |

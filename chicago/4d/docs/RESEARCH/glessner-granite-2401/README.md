# T-2401 — Glessner light model: its own stone-scale occlusion

Piece 2 of T-2394. T-2400 baked the granite's stone-scale occlusion onto the full master's own
`TEXCOORD_1`. The light model, which phones load, is a different mesh (the same v4 record through
the same construction functions, sampled more coarsely), so that bake could not ride it, and it put
T-2393's faint tiling map back on `TEXCOORD_0`. This bakes the light mesh itself.

**Acceptance, stated before the work:** the light model's granite slots read an occlusion map
baked from the light mesh's own stones on its own `TEXCOORD_1` (not the tiling map); ao_export's
assertions, the K01 contract and the light receipt all hold on the new derivative; it stays inside
its 200,000-triangle cap; the bake reproduces byte for byte; and on mobile, at the T-2209 stands,
the shade relief rises while luminance does not fall.

## What changed

- `tools/_glessner_lod.py` (`build-light`) now hands the reduced mesh, every face as an occluder,
  to Blender (`tools/_glessner_light_occlusion.py`), which calls the full master's own baker,
  `masonry_house_v4_occlusion.bake_stone_occlusion`, unchanged: the same six granite slots, welded
  unwrap, Cycles AO at 0.30 m reach, 64 samples, seed 0, hole fill. Only the atlas edge differs,
  `OCCLUSION_SIZE = 1024` (4.1 cm a texel over the light's 1,303 m² of granite at 74 % coverage).
  Blender returns the corner UVs and the 8-bit atlas and exports nothing; the Python producer
  stays the GLB's only writer. It writes the atlas (greyscale PNG) into the master's occlusion
  image slot, `TEXCOORD_1` on the six granite primitives, and the bake's own figures as the node's
  `stone_occlusion` (it used to copy the master's).
- The light recipe hash (`generators/common/versions.py lod_recipe_sha`) now covers the new
  script, so changing it stales the light model. The full master and its inputs hash are
  untouched: the baker module was reused, not edited, so nothing re-bakes Glessner's master.
- `build-light` now needs the pinned Blender (`generators/blender.pin`, or `$BLENDER`) and refuses
  in one line without it; there is no tiling-map fallback. Its only caller,
  `tools/web_derivatives.sh`, runs inside `tools/bake.sh` and the bake workflow, which have it.
- One stale line remains where editing would re-bake the master for a comment:
  `masonry_house_v4_occlusion.py`'s docstring still says the light LOD keeps the tiling map.

## Measured

`build-light` 7 s → 31 s (the bake about 24 s). Two builds wrote byte-identical source GLBs.
Light model **27,611,912 → 27,727,064 bytes (+0.4 %)**: the 1024² bake (428 kB) takes the
tiling map's place. Triangles unchanged (197,304); vertices 385,411 → 385,839 (seams of the new
UV set). The full web model is byte-identical. Lapped onto dev after T-2211 (#737) re-baked the
master with its two-plane sash, the light was rebuilt from that master: **27,615,932 →
27,734,032 bytes**, 197,582 triangles, bake figures the same (granite mean 0.6696, 74 % of the
atlas). The frames below were taken before that lap; T-2211 moved the sash, not the granite. Lapped again onto dev after T-2416 (#741) re-baked the master with bowed granite and gave the
light tier its corner-normal lean (`PILLOW_LEAN`): both changes kept, the light rebuilt from that
master, **27,664,128 → 27,801,700 bytes**, 199,126 triangles (T-2416's, unchanged), vertices
387,541 → 388,131; the web model reproduced dev's bytes exactly. The frames below predate both laps.

Mobile, 390×780, the published `/1904/`, the T-2209 stands under scene light
(`QA_TAG=before-|after- QA_VIEWPORT=mobile QA_OUT=docs/RESEARCH/glessner-granite-2401 node
tools/qa_glessner_t2209.mjs`, `before-` with dev's light model swapped into the mirror).
`measure_glessner_shade_relief.py` masks the desktop HUD, so these were measured with its same
three figures over the mobile frame minus the top 190 px (HUD and minimap) and the bottom-right
buttons:

| stand | luminance | mean abs Laplacian | (relative) | mid-band | (relative) |
|---|---|---|---|---|---|
| north-close | 43.29 → 44.52 (+2.8 %) | 5.13 → 5.46 (+6.4 %) | +3.5 % | 4.68 → 4.64 (-0.8 %) | -3.5 % |
| north-mid | 70.48 → 70.99 (+0.7 %) | 6.05 → 6.46 (+6.7 %) | +6.0 % | 7.75 → 7.76 (+0.2 %) | -0.5 % |
| north-shaded | 92.68 → 93.10 (+0.5 %) | 5.96 → 6.08 (+2.1 %) | +1.7 % | 8.55 → 8.68 (+1.5 %) | +1.1 % |
| west-alley | 61.06 → 61.45 (+0.6 %) | 5.90 → 6.04 (+2.3 %) | +1.7 % | 8.98 → 9.06 (+0.9 %) | +0.3 % |
| corner-ne | 91.70 → 91.85 (+0.2 %) | 9.15 → 9.76 (+6.7 %) | +6.5 % | 12.56 → 13.34 (+6.2 %) | +6.0 % |
| prairie-street | 81.49 → 81.57 (+0.1 %) | 9.91 → 10.02 (+1.1 %) | +1.0 % | 14.33 → 14.37 (+0.2 %) | +0.1 % |
| prairie-jambs | 95.28 → 95.20 (-0.1 %) | 17.49 → 17.81 (+1.8 %) | +1.9 % | 16.12 → 16.56 (+2.7 %) | +2.8 % |

**Read honestly:** the pixel-scale relief rises on every stand, but by 1-7 %, not T-2400's
15-21 % on desktop. Two reasons: a 390 px frame resolves fewer joints, and the light mesh has
less to bake — its stones are flat faces stood proud of the wall (`smooth_rock_faces = False`),
with no pitched arrises or drafted margins. The faces get no darker (the tiling map darkened
every texel by its mean 0.93; the bake leaves open stone faces near 1 and darkens the joints).
What the numbers undersell, `north-close-mobile-before-after.png` shows: before, the north wall is
an even field; after, its courses and the stones' heads and beds read as lines.

**Why 1024² and not the master's 2048²:** measured, not assumed. A 2048² light model
(29,246,716 bytes, +1.5 MB) gave the same figures within noise on all seven stands
(north-close Laplacian +5.8 % against +6.4 %, corner-ne +6.6 % against +6.7 %).

**Shared with the master, not new here:** 8.3 % of the light's granite area bakes to black
(AO < 0.05); the full master's own bake has 10.0 % (152.9 of 1,528.1 m²). The largest are the
same downward-facing pieces in both (e.g. a 2.3 m² soffit 6.9 m up); they are faces the baker's
rays find enclosed within 0.30 m. Recorded, not chased in this piece.

# T-2209 — Glessner granite: the triangle mosaic, and what the shade still lacks

Glessner exterior audit GA-09B. The audit found noisy faceted stone: at street distance
the texture overwhelmed the coursing, and in close views each stone read as a mosaic of
small triangles.

## The cause, found by elimination

- **Not the shadow map.** `QA_LIGHTS=unshadowed` (the sun's shadow off) left the
  Prairie front's triangles pixel-identical.
- **Mostly not the shading normals.** At the old 35° limit, 21 % of the shared facet
  corners kept a hard crease (p99 jump 42°). Raising it to 60° (0.3 %) changed only
  3.7 % of the pixels in the jamb view, and the triangles stayed.
- **The UVs.** `assign_metric_uvs` projects every face on its OWN normal. A rock facet
  tilted 10° from its wall, ~30 m from the model origin, moves its albedo sample by
  metres. So each 7.5 cm lattice triangle showed an unrelated patch of the 0.22 m crystal
  albedo, and the seam fell on the triangle's edges. The dark triangles were dark mica,
  not geometry.

## What changed (generator: `generators/archetypes/masonry_house_v4_detail.py`)

- Every rock-face facet takes its metric UV in its **wall's** plane, through the existing
  per-vertex `roof_uvs` override. One frame per stone, so the grain runs continuously
  across the face. Albedo, repeat (0.22 m albedo, 1.6 m normal/roughness), tints,
  roughness and normal strength are unchanged.
- Rock-face shading normals are smoothed up to 60° (`ROCK_SMOOTH_DEGREES`). The 7.5 cm
  lattice and its random diagonals are a computational mesh of one face, not fractures.
  Only a steeper chip keeps a hard ridge. No vertex moved.
- `tools/test_glessner_block_clipping.py` gates both: `check_rock_uv_frame` (shared
  corners carry one UV, on the wall plane) and `check_rock_shading` (< 1 % creased).

Reconstructed: `docs/LIBERTIES.md` → `L-glessner-granite-2209`.

## Measured

Desktop, actual published `/1904/`, same cameras before and after. The metric is the
mean absolute Laplacian of luminance over the building region:

| view | before | after | mean luminance |
|---|---|---|---|
| prairie-jambs (sunlit, close) | 19.81 | 17.61 (−11 %) | 84.0 → 84.5 |
| prairie-street | 13.90 | 12.70 (−9 %) | 88.4 → 88.5 |
| north-close (shade) | 7.53 | 7.33 | 41.6 → 41.5 |
| north-mid (shade) | 7.00 | 6.98 | 51.4 → 51.3 |
| west-alley (shade) | 6.61 | 6.64 | 51.7 → 51.6 |

Web GLB 52,145,068 → 45,847,408 bytes: continuous UVs quantise and compress better. The
master keeps 1,246,933 triangles. K01 contract re-measured: scale drift, origin,
coincident faces and metric UV all ok.

## Colour, checked and left alone

The tinted albedo's linear mean is a warm neutral grey: luminance 0.24–0.28 and b/r
0.71–0.90 across the five granite slots. It has no blue bias. The navy on the shaded
north and west faces is the blue sky fill. Pushing the stone warm to cancel it would be
the "lighting workaround" the acceptance forbids, done in the material instead. Wellesley
grey versus Braggville pink is still the sources' open disagreement.

## Not solved: relief in shade

In shade the relief is still faint (the table's shaded rows barely move). A face lit only
by the sky fill shows its relief through occlusion, and these materials carry no
occlusion channel. That is a follow-up ticket. It is not done here by brightening or
re-tinting the light.

## Captures

`before-desktop-*` were taken on dev, and the rest after. Every desktop stand has a
`-neutral` twin, lit by a white hemisphere with a white sun, for the diagnostic. Mobile is
the light tier, which is rebaked too. `node tools/qa_glessner_t2209.mjs` re-runs them
(`QA_TAG`, `QA_VIEWPORT`, `QA_STANDS`, `QA_LIGHTS=scene,neutral,unshadowed`).

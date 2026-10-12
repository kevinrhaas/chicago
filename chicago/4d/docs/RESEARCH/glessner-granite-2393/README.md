# T-2393 — Glessner granite: an occlusion map from the split face's own relief

Split from T-2390 ("Glessner granite relief in shade"), which T-2209 left open: *"A face lit
only by the sky fill shows its relief through occlusion, and these materials carry no occlusion
channel."* This piece gives the granite that channel and measures what it does. The measurement
is why T-2390 was split: on its own the channel is correct, but faint.

## What changed

- `assets/textures/glessner-v4/generate.py` writes `granite_occlusion.png` (1024², 8-bit,
  non-colour) from the same low-passed height field as `granite_normal.png`. The method is
  horizon-based ambient occlusion: 16 directions, 24 steps out to 8 cm (about two-thirds of the
  12 cm fracture cell), measured against each texel's own tangent plane. So a crease is darkened
  and a facet's tilt is not. The map tiles, has mean 0.932 and min 0.678. The other granite maps
  regenerate byte-identical.
- `generators/archetypes/masonry_house_v4_materials.py` wires it on the normal map's
  `SurfaceUV`, through the "glTF Material Output" group the exporter reads, for every material
  that carries the granite normal map: granite, granite_1 to 4 and rough_stone_trim. Blender
  packs it with the roughness into one ORM image, `granite_occlusion-granite_roughness`
  (R occlusion, G roughness). The master, the web derivative and the light LOD all carry it.
- `generators/ao_export.py`, assertion 4: an occlusion image named for a map the material
  library declares is a material map, not a bake. It is held to its committed PNG (not uniform,
  mean within 2 %), and `baked_ao` stays false. Every other occlusion image still answers to the
  manifest. Seven new self-test arms. The gate now reads: `0 carry a baked occlusion texture,
  1 a material occlusion map`, granite_occlusion mean 0.9316 in the GLB against 0.9316 committed.

three.js applies `aoMap` to indirect light only (the sky environment's diffuse and specular),
never to the directional sun. So nothing is brightened, re-tinted or relit.

## Measured

Desktop, the actual published `/1904/`, the T-2209 stands and cameras, scene light. Captures
are from `node tools/qa_glessner_t2209.mjs` (`QA_TAG=before-` on dev, then `after-`). The table
is from `python3 tools/measure_glessner_shade_relief.py BEFORE AFTER`. "Relative" divides the
contrast by mean luminance, because darkening alone lowers both contrasts.

| stand | luminance | mean abs Laplacian | (relative) | mid-band | (relative) |
|---|---|---|---|---|---|
| north-close | 42.24 → 39.97 (-5.4 %) | 7.71 → 7.34 (-4.8 %) | +0.6 % | 4.29 → 4.30 (+0.2 %) | +5.9 % |
| north-mid | 52.40 → 50.77 (-3.1 %) | 6.65 → 6.42 (-3.5 %) | -0.4 % | 7.05 → 7.03 (-0.2 %) | +3.0 % |
| north-shaded | 67.19 → 65.93 (-1.9 %) | 6.31 → 6.19 (-1.9 %) | -0.0 % | 8.20 → 8.22 (+0.2 %) | +2.2 % |
| west-alley | 63.78 → 62.72 (-1.7 %) | 5.46 → 5.24 (-4.0 %) | -2.4 % | 8.07 → 8.03 (-0.5 %) | +1.1 % |
| prairie-jambs (sun) | 86.29 → 85.05 (-1.4 %) | 17.11 → 17.15 (+0.3 %) | +1.7 % | 17.70 → 17.79 (+0.5 %) | +2.0 % |

**Read honestly:** the shaded faces get 2-5 % darker, because the sky they lose is now counted.
The crease-scale contrast rises 1-6 % relative to that luminance. The pixel-scale Laplacian does
not rise at all. In `north-close-crop-before-after.png` (brightened ×2.2 for reading, before on
the left) the facet creases are a little more defined, and that is all. Web GLB 45.85 → 46.65 MB,
light LOD 26.98 → 27.78 MB.

## Why it is faint, and what is not done here

The split-face height field is millimetres deep (std 5.8 mm), and a tiling material map cannot
know where a stone's joints, drafted margins and pitched face are. The relief a visitor reads in
shade lives at that stone scale, and it needs a per-asset bake: `emit.bake_ao` onto `BakeUV`,
exported as TEXCOORD_1, with the light LOD handled too. That is **T-2394**. This channel stays
under it either way: it is the material's own small-scale occlusion, and a bake at stone scale
cannot resolve millimetre creases.

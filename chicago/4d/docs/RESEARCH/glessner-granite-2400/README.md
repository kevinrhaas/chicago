# T-2400 — Glessner granite: stone-scale occlusion, baked from the stones themselves

Split from T-2394 (itself the second half of T-2390, "Glessner granite relief in shade").
T-2393 gave the split face a tiling occlusion map from its own height field and measured why it
was faint: that relief is millimetres deep, and a tiling map cannot know where a stone ends. The
relief a visitor reads on a wall in shade is at stone scale. This piece bakes it. The light
model's own bake is T-2401.

## What changed

- `generators/archetypes/masonry_house_v4_occlusion.py`, called at the end of the v4 builder:
  1. **Unwrap.** The granite slots (granite, granite_1 to 4, rough_stone_trim; 495,450 faces,
     1,528 m²) go onto their own layer, `OcclusionUV`. The v4 mesh is polygon soup (1.61 M
     vertices for 1.61 M corners), so a smart projection of it as built makes one island per
     facet: tried first, it covered 9 % of the atlas and baked nothing visible. The projection
     runs on a welded copy (0.1 mm) and is carried back face by face, corner by corner (worst
     corner 0.096 mm); islands are then re-packed. 67 % of the atlas is used, about 2.3 cm a
     texel at 2048².
  2. **Bake.** Cycles AO, 64 samples, reach **0.30 m**: a stone's own joints, arrises and its
     reveal, never the building's masses (the long-reach bake put the Sauganash out, T-0227).
     Seed fixed; two bakes of the same inputs wrote byte-identical GLBs. Texels no face writes
     are filled from their neighbours (a tangent-normal pass finds them), so no mip averages a
     stone with black.
  3. **Wire.** The bake is the granite slots' `occlusionTexture` on `TEXCOORD_1`. It replaces
     T-2393's tiling map there: glTF has one occlusion slot, the two ride different UV sets,
     and 2.3 cm texels cannot hold millimetre creases. The figures ride the node extras as
     `stone_occlusion`; `generators/build.py` reads them back, records `baked_ao: true` and
     holds the export to the bake (`AO baked mean 0.5795 -> exported mean 0.5795, 0.0 % drift`).
- `renderers/web/js/buildings.js`: `normalizeGeometry()` carries `uv1` when the material's aoMap
  reads channel 1 (and refuses the mesh if it is missing). Nothing else pays for it.
- `tools/_glessner_lod.py`: the light model is a different mesh with `TEXCOORD_0` alone. It puts
  the tiling map (`occlusion_tiling_map` in the material extras) back on `TEXCOORD_0`, with the
  normal map's repeating sampler. Without this it copied `texCoord: 1` onto a mesh with no such
  set — the first derivative built did exactly that.
- `generators/ao_export.py`, **assertion 5**: an occlusion map's UV set is on every primitive
  that wears it, read on all masters and all web derivatives. Four self-test arms. It refused
  that first light model on all six granite slots.
- `docs/GLB-CONTRACT.md` § Materials: the additive `TEXCOORD_1` occlusion rule.

The whole of Glessner's build now takes about 255 s (the bake about 160 s of it). `--no-bake`
does not skip it: the bake belongs to the builder the asset's inputs hash covers.

## Measured

Desktop, the published `/1904/`, the T-2209 stands and cameras, scene light, from
`node tools/qa_glessner_t2209.mjs` (`QA_TAG=before-` with dev's web model swapped into the
mirror, then `after-`) and `python3 tools/measure_glessner_shade_relief.py`.

| stand | luminance | mean abs Laplacian | (relative) | mid-band | (relative) |
|---|---|---|---|---|---|
| north-close | 39.97 → 39.21 (-1.9 %) | 7.34 → 8.61 (+17.2 %) | +19.5 % | 4.30 → 5.10 (+18.6 %) | +20.9 % |
| north-mid | 50.77 → 50.08 (-1.3 %) | 6.42 → 7.80 (+21.4 %) | +23.1 % | 7.03 → 7.19 (+2.3 %) | +3.7 % |
| north-shaded | 65.93 → 65.60 (-0.5 %) | 6.19 → 7.40 (+19.5 %) | +20.1 % | 8.22 → 8.32 (+1.2 %) | +1.7 % |
| west-alley | 62.72 → 62.22 (-0.8 %) | 5.24 → 6.01 (+14.6 %) | +15.5 % | 8.03 → 8.09 (+0.8 %) | +1.6 % |
| prairie-jambs (sun) | 85.05 → 84.18 (-1.0 %) | 17.15 → 18.41 (+7.3 %) | +8.4 % | 17.78 → 18.92 (+6.4 %) | +7.5 % |

**Read honestly:** where T-2393's map left the pixel-scale relief flat, this raises it 15-21 % on
every shaded stand, while the faces get only 0.5-1.9 % darker. In
`north-close-crop-before-after.png` (brightened ×2.2, before on the left) the joints were
bright seams where the sky caught their edges; now they read as recesses, and each stone's
pitched face is shaded toward its arris. The mid-band contrast rises only at the close stand,
because at mid distance a course line is a few pixels and the Laplacian is what sees it.

**Bytes.** Master 153.67 → 179.88 MB (the exporter writes `TEXCOORD_1` on all 28 primitives,
zeros off the granite). Full web model 46.65 → 52.32 MB (+12 %; the map is 3.6 MB of it). Light
model 27.78 → 27.61 MB. Desktop loads the full web model; mobile, the light one.

## Not done here

- The light model's own stone-scale bake (its reduced mesh, its own UVs): **T-2401**.
- Mobile shows T-2393's tiling map as before; only the light LOD's bytes moved.

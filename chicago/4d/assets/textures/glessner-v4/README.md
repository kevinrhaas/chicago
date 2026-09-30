# Glessner v4 material studies

Ten original deterministic PBR fabrics accompany three preserved original generated
albedo studies. The numeric fabrics are granite, limestone, common brick, sandy
lime mortar, terracotta, copper, oak, painted wood, turf and compacted gravel.
Every exact colour, grain arrangement and weathering choice is **reconstructed**.

## Reproduction and provenance

Run `python assets/textures/glessner-v4/generate.py` from `chicago/4d/` to regenerate
the ten numeric fabrics. `--only brick` and `--only mortar` regenerate individual
fabrics and refresh the map inventory. The recipe never overwrites these original
generated images:

| Original source | Repeat used | Bytes | Provenance |
| --- | --- | --- | --- |
| `granite_photographic_basecolor.png` | 0.22 m | 3,850,146 | `granite_photographic_provenance.json` |
| `turf_photographic_basecolor.png` | 0.4 m; preserved earlier study | 3,881,389 | `turf_photographic_provenance.json` |
| `turf_patch_photographic_basecolor.png` | 4 m; active lawn colour | 3,958,556 | `turf_patch_provenance.json` |

All three are byte-unchanged 1254 × 1254 RGB PNG outputs of text-to-image generation
without reference images. Their exact prompts, methods, SHA256, dimensions and
limitations remain attached. No historical, owner-supplied, Google, aerial or other
photographic pixels were sampled, traced or embedded. These are generic material
studies, not photographs or measured reflectance scans of Glessner House.

`material-library.json` records seeds, metric scales, channel conventions and the
SHA256 of all 33 source maps, totalling 25,155,223 bytes. The folder contains 40
licensed files. Numeric granite and turf albedos and the earlier generated turf
remain source studies even though the active building uses their replacements.
Building numeric albedo is 2048² sRGB JPEG; normal is 1024² OpenGL tangent-space
PNG; roughness is 1024² linear PNG. Ground and mortar use 1024² albedo with 512²
normal/roughness. Numeric granite JPEG quality is 89; other numeric JPEG quality
is 92. Normal/roughness maps are filtered before reduction to limit shimmer.
No numeric map contains baked lighting or ambient occlusion. Generated-image
prompts request diffuse illumination and seamless edges; these are targets,
not measured properties.

## Material transport

Pinned Blender 4.5.3 transport probe on 2026-09-30 verifies 28 material slots and
30 deduplicated images. Metric `SurfaceUV` remains unchanged through the shared
smart-unwrap step; every texture uses `TEXCOORD_0`. Granite albedo repeats at
0.22 m through `KHR_texture_transform` (scale 7.2727273), with normal/roughness
at 1.6 m. Active lawn albedo repeats at 4 m (scale 0.6), with normal/roughness
at 2.4 m. Granite normal strength is 1.0, rough stone trim 0.8, mortar 0.65 and
turf 0.25. Copper metallicity and clear glass transmission 0.94 / IOR 1.52 survive
export. Three plain double-sided grass blade materials occupy slots 25–27.
Transport verification does not establish photographic likeness.

## Reconstruction choices and review

Stone courses, brick joints, block boundaries, openings, roof laps and copper
standing seams remain physical geometry. Granite's active generated crystal
albedo replaces the earlier purely numeric colour study; its 0.22 m repeat and
cool tint factors address overly large pink-looking crystals. Numeric normal
maps and physical fracture geometry carry relief. Rough courtyard surrounds
use the granite fabric; smooth carved mouldings retain limestone. These choices
are reconstructed appearance, not petrographic identification.

Brick uses one shared clay fabric across all four kiln variants. The existing
60/20/14/6 unit distribution is unchanged. Linear tint factors are:

| Slot | Variant | RGB multiplier |
| --- | --- | --- |
| 1 | Main common brick | 0.88, 0.88, 0.88 |
| 16 | Warm red-fired | 0.92, 0.72, 0.64 |
| 17 | Buff | 1.00, 0.985, 0.94 |
| 18 | Smoky | 0.43, 0.47, 0.48 |

The earlier red/grey mosaic was excessive. A controlled material-only trial
compressed the spacing too far into a uniform tan field; the final factors above
restore a restrained midpoint. The source trial exported actual Blender shaders
onto unchanged master geometry, then reimported that GLB for a fixed 800 px,
128-sample courtyard comparison. The midpoint requires the final canonical bake
and review; the trial image is not a final-building acceptance image.
Centimetre-scale intrinsic clay variation produces roughness approximately
0.71–0.94. Dedicated sandy lime mortar replaces limestone grain in slot 9 while
retaining the previous mean beige tone; roughness is approximately 0.84–0.98.
No brick geometry, joint width, modern spalling, soot or later repointing is added.

The active 4 m lawn study has coherent irregular 0.5–2 m variation in green growth
and tan thatch, addressing the even olive mat produced when the older 0.4 m tile
was filtered at courtyard distance. It is an original generic July lawn material,
not a copy of modern site wear or an attested 1904 planting pattern. Existing
fine normal maps and bounded grass geometry are retained. The carriage drive
keeps the record's reconstructed pale gravel interpretation; later concrete
paving is not retrojected.

Copper retains subdued brown/green variation so standing seams carry the form.
Exact oxidation after 17 years is reconstructed. Oak is warm brown with varnish
roughness bounded 0.40–0.61. Linen blinds and muted green joinery remain separate
from real transmissive glass; no scene reflections are painted into windows.

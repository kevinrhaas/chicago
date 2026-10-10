# Prairie Avenue 1904 street-surface PBR library

Version 1.0.0 (T-1728): **seven seamless, 512 × 512 materials** for the roadways, alleys, walks,
curbs and parkways of the 1904 Prairie Avenue scene. It follows the 1835 library beside it
(`../chicago_1835_pbr/`) map for map, and is built by one deterministic script,
`tools/generate_prairie_1904_pbr.py`, that samples no photograph.

## What each folder holds

- `*_basecolor.png` — sRGB colour, no baked lighting
- `*_normal_gl.png` / `*_normal_dx.png` — OpenGL (+Y) and DirectX (−Y) normals, linear. +Y is
  UP the image, so the OpenGL green rises where height rises toward the bottom row. Until
  T-2296 the two were swapped; `tools/check_street_surfaces.py --handedness` holds the sign
- `*_roughness.png`, `*_ao.png`, `*_metallic.png` — linear greyscale
- `*_height16.png` — 16-bit linear height
- `*_orm.png` — R = AO, G = roughness, B = metallic
- `*_basecolor_web.jpg`, `*_normal_gl_web.jpg`, `*_orm_web.jpg` — JPEG re-encodes of three of
  the above: the only files `tools/publish.sh` ships and the only ones the web renderer binds
- `material.json` — the tile's physical span, orientation, colour-space contract and note

| group | material | tile (along × across) | used for |
|---|---|---|---|
| roadway | `sheet_asphalt` | 4.00 × 4.00 m | Prairie Avenue 16th–20th, E. 16th St, E. 22nd St, Indiana 18th–22nd, Calumet 21st–22nd |
| roadway | `macadam_limestone` | 6.00 × 6.00 m | Prairie 20th–22nd, E. 18th, 20th and 21st St, Calumet 18th–21st |
| roadway | `vitrified_paving_brick` | 2.12 × 2.12 m | Indiana Avenue 16th–18th |
| alley | `earth_and_cinders` | 4.00 × 4.00 m | every alley |
| walk | `portland_cement_walk` | two blocks × the walk's width | every walk |
| curb | `sandstone_curbstone` | two 6-ft stones × the curb's width | every curb |
| parkway | `grass_plat` | 3.00 × 3.00 m | every parkway and the foot inside each walk |

Image x runs **along** the street; image y runs **across** it. The walk and curb tiles span their
band's full width, so a 6-ft walk is one block across and a 6-in curb one stone deep.

## What these are evidence of

**Nothing.** Which surface wears which material, at what tier and on what source, is
`data/street_surfaces/1904.json`'s to say, and `tools/check_street_surfaces.py` holds it there.
These files are pictures of those materials, and their colour, grain, joints and wear are ours
(`docs/LIBERTIES.md` L296). A texture here is not permission to put its material on a street the
surfaces file does not name.

Regenerate in place with `python3 tools/generate_prairie_1904_pbr.py` (numpy, scipy, Pillow).

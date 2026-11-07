# Prairie Avenue 1904 street-surface PBR library

Version 1.1.0: **twelve seamless, 512 × 512 materials** — seven for the roadways, alleys, walks,
curbs and parkways of the 1904 Prairie Avenue scene (T-1728, v1.0.0) and five for the back and side
yards behind its houses (T-3488, v1.1.0, the `yard/` group). It follows the 1835 library beside it
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
| yard | `yard_brick_herringbone` | 1.78 × 1.78 m | brick terraces and walks: common brick, 45° herringbone, sand joints |
| yard | `bluestone_flags` | 2.40 × 2.40 m | stone-flagged terraces: random-rectangular buff and blue-grey flags |
| yard | `pea_gravel` | 1.00 × 1.00 m | carriage courts and garden paths: raked 5-15 mm gravel |
| yard | `beaten_earth` | 3.00 × 3.00 m | drying and service yards: trodden earth, cinders, thin grass |
| yard | `garden_loam` | 2.00 × 2.00 m | kitchen-garden beds: dug and raked loam, rows along x |

Image x runs **along** the street; image y runs **across** it. The walk and curb tiles span their
band's full width, so a 6-ft walk is one block across and a 6-in curb one stone deep. A yard tile's
x runs along whatever path or court the yard layout lays it on (the loam's along its rows).

The yard group's relief is built in metres and lit at its true slope (a brick joint 6-9 mm down, a
flag settled a couple of millimetres, a 10 mm pebble standing 3-5 mm proud), and each names its own
web JPEG qualities, lower than the street seven's 86/92/90, because gravel and crumb are detail at
every pixel: the five's three web maps are 128-292 KB a material. The pea gravel's tile is 1.0 m,
not 2: at 512 px a 5-15 mm stone is 2.5-8 px there and reads as a stone, over 2 m it reads as noise.

## What these are evidence of

**Nothing.** Which surface wears which material, at what tier and on what source, is
`data/street_surfaces/1904.json`'s to say, and `tools/check_street_surfaces.py` holds it there.
These files are pictures of those materials, and their colour, grain, joints and wear are ours
(`docs/LIBERTIES.md` L296). The same holds for the yard group: which yard surface wears which is the
back-yard layout's to say, and the brick, bond, stone, gravel, earth and loam drawn here are
reconstructed (T-3488). A texture here is not permission to put its material on a street the
surfaces file does not name.

Regenerate in place with `python3 tools/generate_prairie_1904_pbr.py` (numpy, scipy, Pillow).

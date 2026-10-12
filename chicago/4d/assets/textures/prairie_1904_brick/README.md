# Prairie Avenue 1904 K03 brick library

Version 1.0.0 (T-2290, piece 1 of T-1845; package K03 of the T-1837 Prairie programme). It holds
**four brick fabrics, two mortars, the joints and bonds as data, and four bonded LOD panels**, all
built by one deterministic script, `tools/generate_prairie_1904_brick.py`. The script samples no
photograph.

## The three kinds of file

- **Fabrics**: `brick/<id>/` and `mortar/<id>/`. Joint-free clay and mortar grain, seamless, on a
  **1.00 m tile at 1024 px** (1 px/mm). Each one registers under K01's UV rule
  (`data/components/prairie_1904/k01_contract.json` § scale_uv: TEXCOORD_0 = surface metres /
  tile_m). **No course, joint or brick edge is in these maps.** At full detail a component builds
  every brick and its recessed mortar bed as geometry, as Glessner v4 does, and maps the fabric
  onto it.
- **`profiles.json`**: the brick module, every fabric's joint (width, recess, profile, mortar),
  arris bevel and chip rule, per-brick firing variants and how they are drawn, the bonds (running,
  common with a header every sixth course, Flemish), the specials (header, soldier, rowlock,
  segmental and jack arches, string course, corner return) and the uses the T-1837 register gives
  each fabric. T-2291 reads it.
- **Panels**: `panel/<id>/`. Bonded wall tiles **rendered from `profiles.json` and the fabrics**,
  for the balanced and light exports only, where a district cannot afford a mesh per brick. They
  carry joints because they are derived from the joint data. Change a joint and they change with it.

| fabric | joint | bonds offered | register uses |
|---|---|---|---|
| `pressed_red` | 4 mm flush, 0.6 mm back, `mortar_dark` | running, flemish | pa-2100-18, pa-2126-20, pa-213–217-e.-cullerton-street-27 |
| `common_buff` | 9 mm weathered, 3.0 mm back, `mortar_lime` | common_6, running | pa-1612-1, pa-1808-6, pa-1912-10, pa-2130-42, pa-2031-nrhp |
| `dark_fired` | 6 mm struck, 2.0 mm back, `mortar_lime` | flemish | accent only |
| `rough_red_brown` | 10 mm raked, 5.0 mm back, `mortar_lime` | running | pa-2009-17 |

The module is Glessner v4's (0.2159 m along, 0.066675 m a course). Each fabric's joint comes out
of that module, not on top of it, so every brick on the street registers with the canonical
asset. `dark_fired` is an accent unit, the header of a Flemish front, and is not a wall fabric.

## Maps per folder

`*_basecolor.png` (sRGB) · `*_normal_gl.png` (OpenGL, +Y up the wall) · `*_roughness.png` ·
`*_height16.png` (16-bit, mapped to the `height_range_m` in metres given by `material.json`) ·
`*_orm.png` (R = AO, G = roughness, B = metallic) · three web JPEGs (`*_basecolor_web.jpg`,
`*_normal_gl_web.jpg`, `*_orm_web.jpg`) · `material.json`. No map bakes in lighting. Soot, damp
and dirt are condition masks (T-2291) that go over a fabric, so the clean 1904 body clay and the
dirt on it stay separate.

## Costs

| group | id | pixels per map | master bytes | web bytes |
|---|---|---|---|---|
| brick | `pressed_red` | 1,048,576 | 4,824,575 | 424,278 |
| brick | `common_buff` | 1,048,576 | 5,464,586 | 656,315 |
| brick | `dark_fired` | 1,048,576 | 4,158,916 | 621,836 |
| brick | `rough_red_brown` | 1,048,576 | 3,555,150 | 499,174 |
| mortar | `mortar_dark` | 1,048,576 | 3,839,283 | 364,107 |
| mortar | `mortar_lime` | 1,048,576 | 3,811,655 | 391,040 |
| panel | `pressed_red_running` | 248,640 | 1,125,393 | 153,851 |
| panel | `common_buff_common_6` | 248,640 | 1,284,529 | 185,911 |
| panel | `rough_red_brown_running` | 248,640 | 977,055 | 222,504 |
| panel | `pressed_red_flemish_dark_headers` | 186,720 | 854,044 | 135,476 |

Total: 29,895,186 B of masters, 3,654,492 B of web JPEGs.
Nothing here is published yet. `tools/publish.sh` ships no file from this library until a component
binds one (T-2291).

## What these are evidence of

**Nothing.** The colour, grain, joint, bond and firing spread are ours (`docs/LIBERTIES.md`
L-k03-brick-library-2290). The `uses` quote the T-1837 building register's build specifications and are not a
ruling. Which house is built of which brick is decided per house, from its own evidence.

The light study (raking and diffuse) and its reading are in
`docs/RESEARCH/k03-brick-library-2290/`.

Regenerate in place with `python3 tools/generate_prairie_1904_brick.py` (numpy, scipy, Pillow),
then run `--check` to confirm every file hashes as `manifest.json` says.

# Prairie Avenue 1904 stone library (K02)

Version 1.0.0 (T-2288, piece 1 of T-1844): **six seamless, metric stone fabrics** for the 1904
programme's walls, trim and foundations, built by one deterministic script,
`tools/generate_prairie_1904_stone.py`, that samples no photograph.

| fabric | tile | dressing | in-map relief | for |
|---|---|---|---|---|
| `granite_rock_faced` | 1.60 m | split-face facets 4-10 cm | 12 mm | a house whose record names granite; none of the register's 62 rows does |
| `sandstone_brown` | 1.20 m | drove-tooled, bedded | 1.5 mm | the register's brownstone and brown-sandstone fronts |
| `limestone_lemont` | 1.20 m | hammer-dressed, pitted, iron-stained | 4.6 mm | the register's Lemont-limestone row |
| `limestone_bedford` | 1.20 m | crandalled oolite | 0.6 mm | the register's Bedford-stone envelope |
| `dressed_trim` | 0.90 m | rubbed smooth | 0.4 mm | sills, lintels, belts, copings, voussoirs, carving |
| `foundation_rubble` | 2.00 m | random rubble, mortar in the map | 30 mm | foundations, area walls, rear walls |

`data/components/prairie_1904/k02_stone_profiles.json` names the register rows behind each "for".

## The two rules a component keeps

- **Metric.** `TEXCOORD_0 = surface metres / tile_m` (K01's `uv` rule), so a 3 mm crystal is 3 mm
  on every fabric and beside every other component on the same scene. Heights are metres too:
  each normal map is the true slope of its `height16_range_m` at the tile's own pixel density.
- **No joint is painted.** Courses, joints, arrises, rock-faced projection, chips, corner bonds,
  rusticated bases, voussoir bed orientation and copings are geometry a component builds from
  `k02_stone_profiles.json`. Random rubble is the one exception: it has no courses, so its stones
  and recessed mortar are in its map (`pattern_in_map: true`).

## What each folder holds

- `*_basecolor.png` (sRGB) and `*_normal_gl.png` (OpenGL +Y, linear), 1024 px
- `*_orm.png` (R = AO, G = roughness, B = metallic, linear) and `*_height16.png` (16-bit, linear,
  0 = the lowest point of `height16_range_m`), 512 px: the slow detail maps at half size
- `*_basecolor_web.jpg`, `*_normal_gl_web.jpg`, `*_orm_web.jpg`: what a renderer binds
- `material.json`: tile, dressing, colour spaces, measured relief and roughness, bytes and sha256

`contact_sheet.jpg` shows a 0.5 m window of every fabric, metre for metre alike.

## What these are evidence of

**Nothing.** Which building wears which stone is its structure record's to say, at its own tier;
the colour, grain and dressing of every map, and every number in the profiles, is ours
(`docs/LIBERTIES.md` L-k02-stone-library-2288). Nothing in the 1904 scene binds these maps yet:
T-2289 lays them on the 1808 Prairie exemplar.

## Seeing them

`node tools/k02_stone_study.mjs` lays every fabric as blocks from its profile on 1.2 x 1.0 m
panels and 0.5 m close windows, in an 8-degree raking sun and in diffuse sky light, at 1280x800
and 390x780, and writes the captures and their costs to `docs/RESEARCH/k02-stone-library-2288/`.

Regenerate in place with `python3 tools/generate_prairie_1904_stone.py` (numpy, scipy, Pillow);
`--check` confirms the library and the profiles still name the same fabrics.

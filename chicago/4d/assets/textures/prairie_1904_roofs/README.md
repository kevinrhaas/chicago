# Prairie Avenue 1904 roof coverings and flashings (K04)

Version 1.0.0 (T-2292, piece 1 of T-1846): **eleven seamless 512 × 512 fabrics** for the roofs,
flashings and rainwater goods of the 1904 Prairie Avenue programme, built by one deterministic
script, `tools/generate_prairie_1904_roofs.py`, that samples no photograph. No roof in the scene
binds them yet: T-2293 builds the first K04 roof from them on the 1808 exemplar.

## The module is data, not pixels

Every slate, tile, pan and sheet is sized in `data/components/prairie_1904/k04_roofs.json`, and the
generator reads it: each map is exactly `columns × width` along the eave and `courses × exposure` up
the slope. A K01 roof maps `TEXCOORD_0 = surface metres / tile_m`, so its courses land at true size
and no slate is ever stretched to fit a roof. Change a format in the data file and regenerate;
`tools/check_roof_library.py --check` refuses a map whose tile is not a whole number of its own
units, a slate outside the reconstruction rules' starting range, or a tile roof with no source.

Hips, ridges, verges, valleys, aprons, gutters, outlets, downpipes and shoes are **geometry**, built
from the same file's `profiles`. No covering map carries any of them.

## What each folder holds

- `*_basecolor.png` — sRGB colour, no baked lighting
- `*_normal_gl.png` — OpenGL (+Y) tangent-space normal, linear
- `*_roughness.png` — linear greyscale
- `*_orm.png` — R = AO, G = roughness, B = metallic
- `*_basecolor_web.jpg`, `*_normal_gl_web.jpg`, `*_orm_web.jpg` — the three a web renderer binds
- `material.json` — tile in metres, the module it was drawn from, orientation, colour spaces, note

Image x runs **along the eave**; image y runs **up the slope** with the top row uphill, and each
course's butt is its low edge.

| slot | fabric | unit | tile (u × v) | for |
|---|---|---|---|---|
| covering | `slate_pennsylvania` | 10 × 20 in slate, 8.5 in to the weather | 2.032 × 1.727 m | the steep main roof's default |
| covering | `slate_vermont` | 9 × 18 in slate, 7.5 in, colour mix | 2.057 × 1.905 m | a coloured or patterned field, mansards |
| covering | `slate_fishscale` | 8 × 16 in scalloped slate, 6.5 in | 2.032 × 1.651 m | bands, cones, dormers only |
| covering | `terracotta_flat_tile` | 6 in tile, 5 in exposed (HABS, Glessner) | 2.438 × 2.032 m | documented roofs only |
| covering | `copper_standing_seam` | 20 in pans, 1 in seams | 2.032 × 2.438 m | oriel, bay and tower caps |
| covering | `tin_standing_seam_painted` | 20 in pans, 28 in sheets | 2.032 × 2.134 m | porch, bay and dormer roofs |
| covering | `tin_flat_seam_painted` | 14 × 20 in soldered sheets | 2.032 × 2.134 m | low-slope service roofs |
| flashing / rainwater | `copper_sheet`, `lead_sheet`, `zinc_sheet`, `painted_tin_sheet` | plain sheet | 1.2 × 1.2 m | valleys, aprons, caps, gutters, pipes |

## What these are evidence of

**Nothing.** Their formats, colours, grain and wear are ours (`docs/LIBERTIES.md`
L-k04-roof-library-2292). The one measured module is the flat tile's, from HABS's Glessner data
pages; the tile is restricted to roofs a source documents. A map here is not permission to put its
covering on a house whose own evidence says otherwise.

Regenerate in place with `python3 tools/generate_prairie_1904_roofs.py`, then
`python3 tools/study_prairie_1904_roofs.py` for the study sheet in `docs/RESEARCH/k04-roof-library/`
(numpy, scipy, Pillow).

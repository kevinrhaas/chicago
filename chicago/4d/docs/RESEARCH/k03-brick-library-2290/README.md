# K03 brick library: the fabrics, the data, and how they look in raking and diffuse light (T-2290)

Piece 1 of T-1845 (package K03 of the T-1837 Prairie programme). Piece 2, T-2291, builds a
named wall from it. This note records what the library holds, the light study and what it shows,
the costs, and what is still open.

## Acceptance (stated before work)

1. A deterministic generator (numpy, scipy, Pillow, no photograph sampled) writes a K03 brick
   library of red pressed face brick, buff common service brick, dark fired brick and the Mayer
   house's rough red-brown brick, with the mortars they are laid in. Each fabric has a seamless
   sRGB albedo, an OpenGL normal, linear roughness, web JPEGs and a `material.json` giving its tile
   in metres, so it registers under K01's UV rule (TEXCOORD_0 = surface metres / tile_m).
2. Joints, bonds and specials are DATA, not pixels: an engine-neutral `profiles.json` holds per
   fabric the joint width, recess and profile, the mortar, the arris bevel and chip rule, the
   per-brick firing variants and the bonds it is offered in, plus the header, soldier, rowlock,
   arch, string-course and corner-return rules T-2291 reads. No joint is baked into a fabric map.
   The only maps that carry joints are the LOD panels, and they are rendered from that data.
3. No checkerboard: each brick draws its variant independently and deterministically from a seeded
   generator, and the spread is measured in the study rather than asserted.
4. No fabric everywhere: each fabric lists the register entries that ask for it and what it is
   NOT for. Dark fired brick is an accent, not a wall fabric.
5. A repeatable study renders each panel and fabric in raking and diffuse light at metric scale,
   committed here with texture byte and pixel costs. Licences are recorded in `assets/LICENSES.md`
   and the reconstruction is recorded as one liberty (`L-k03-brick-library-2290`).

## What was built

`assets/textures/prairie_1904_brick/` (README there has the per-file layout):

| kind | ids | tile | resolution |
|---|---|---|---|
| brick fabric, joint-free | `pressed_red`, `common_buff`, `dark_fired`, `rough_red_brown` | 1.00 x 1.00 m | 1024 px (1 px/mm) |
| mortar fabric | `mortar_dark`, `mortar_lime` | 1.00 x 1.00 m | 1024 px |
| LOD panel, bonded | `pressed_red_running`, `common_buff_common_6`, `rough_red_brown_running` | 0.8636 x 0.8001 m (4 modules x 12 courses) | 518 x 480 px |
| LOD panel, bonded | `pressed_red_flemish_dark_headers` | 0.6477 x 0.8001 m (2 Flemish periods x 12 courses) | 389 x 480 px |

The module is Glessner v4's: 0.2159 m along a course and 0.066675 m a course, with each fabric's
joint taken out of it. A pressed stretcher is 0.2119 x 0.0627 m and a common one 0.2069 x 0.0577 m,
so a pressed front and a common return built from this file keep their courses level across a
corner, as a real stone-front house's brick returns do. The panel tiles are whole bond repeats,
and the generator refuses a panel that is not (`check_profiles`). A brick straddling the tile edge
draws the same variant on both sides, so the panels tile without a seam.

## The study

`k03_brick_study.jpg`: each panel, left in raking light (sun 14 degrees above the wall, from the
upper left, with height-field shadows), right in diffuse overcast light, with a 10 cm bar.
`k03_fabric_study.jpg`: each joint-free fabric, a 25 x 25 cm crop at 1 px/mm, in the same two
lights. Both are rendered by the generator itself (`--study`), so they regenerate with the library.

What it shows, read off the renders:

- **Pressed red, running bond, 4 mm flush dark joints.** The wall reads as one dark-red field with
  thin dark lines, which is what the register asks for at 2100 Prairie. In raking light only the
  pinholes and arrises catch, because the face is dense and the joint barely recessed (0.6 mm).
  Firing spread: 62 / 22 / 12 / 4 per cent body, darker, lighter, flashed. That is visible as
  individual bricks and forms no pattern.
- **Common buff, common bond, 9 mm weathered lime joints.** The header course every sixth course
  is visible in both lights. The weathered joint casts a hairline under each brick's top arris in
  raking light. The first render's firing spread was strong enough to read as patchwork, so the
  three variant tints were narrowed (salmon, grey-tan, hard-burnt) before commit.
- **Rough red-brown, running bond, 10 mm raked joints.** The deep raked joint puts a shadow line
  under every course in raking light and stays a pale line in diffuse light. Chipped arrises
  (45 per cent of bricks, up to four bites) break the edges. The first render's tear texture read
  as wood grain, so it was shortened and its colour contrast cut to 4 per cent before commit.
- **Pressed red, Flemish bond with dark fired headers.** The plum and near-black headers sit
  centred over the stretchers below. This is an option for a Georgian Revival front; no register
  entry yet attests the bond.
- **Diffuse light.** The first render's ambient occlusion crushed every recessed joint to black.
  AO now darkens a recess to no less than 0.45, and joints read as mortar.

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

Total: 29.9 MB of masters in the repository, 3.65 MB of web JPEGs. A house that binds one brick
fabric, its mortar and one panel ships about 0.8-1.3 MB of web texture (three JPEGs each). Nothing
is published by this ticket, and scene load, draw and frame costs belong to the wall that binds it
(T-2291).

## What this is not, and what is open

- **Not visible in the town yet.** No component binds this library. T-2291 is the wall.
- **The module is borrowed, not sourced.** Glessner v4's module is used so the district registers
  with its one canonical asset. No 1904 brick dimension for these houses is a source here (liberty).
- **The bonds are offered, not attested.** No source read here gives a bond for any Prairie house.
- **The study is a numpy shader, not the renderer.** It checks relief, joints and spread under
  controlled light. How the maps look in the walkthrough, at both viewports, is T-2291's check.

Regenerate: `python3 assets/textures/prairie_1904_brick/tools/generate_prairie_1904_brick.py --study
docs/RESEARCH/k03-brick-library-2290` (about a minute), then `--check`.

# K03 on a named target: 1808 Prairie's common-brick return and rear (T-2291)

Piece 2 of T-1845 (package K03 of the T-1837 Prairie programme). Piece 1, T-2290, built the
brick library. This piece lays it on a house in the 1904 scene.

## Acceptance (stated before work)

1. The target is named: **1808 Prairie** (`keith_house_1808_prairie`, register `pa-1808-6`). It is
   the one 1904 house whose register entry asks for common brick ("Common-brick side and rear
   ranges"). Until now its three brick walls wore Glessner v4's courtyard `brick_buff`, which
   T-1845 names as wrong.
2. Its south side, rear and north party walls wear the K03 `common_buff_common_6` panel with its
   normal map. Courses are level at grade on every wall, and the bond turns the north-west quoin
   unbroken (`profiles.json` `corner_return`).
3. Brick heads replace the stone lintel on every brick-wall window: two rowlock rings on a
   segmental arch, or a soldier flat head where the eave leaves no room. Each unit draws its
   firing variant by the library's seeded rule, so there is no checkerboard.
4. A projecting stretcher string course runs at the second-floor line and turns the south-west
   quoin.
5. A soot and damp mask is laid over the fabric, never baked into it. It uses the `_TONE` vertex
   channel the renderer multiplies into colour.
6. The comparison is shown in the actual published `/1904/` app at 1280x800 (full detail) and
   390x780 (light): the stone street front against the common return, the rear and its quoin, a
   close view of the quoin, and the heads under the eave. Every view records load, draws,
   triangles, textures and a timed frame, with zero page errors. The K01 contract measure stays
   green (scale, origin, coincident faces, metric UVs), and the UVs are now held to the K03 tiles.

## What was built

- `generators/archetypes/k03_brick.py` reads `profiles.json` (module, joint, rowlock, soldier,
  arch ratio limits, string-course projection range, variants) and lays the bond phase, heads,
  string course and mask. `k01_frontage.py` calls it for every material marked `courses`.
- `generators/mesh_inputs.py` hashes the new module and the three K03 maps the GLB embeds, so a
  changed map stales the asset.
- `tools/k01_contract.mjs --measure-asset` now includes the K03 library, so the brick slots are
  measured against their own tiles: `uv_per_m_times_tile_m` is 1.0000 full and 1.0001 web.
- The record gains `service_wall_brick` (reconstructed), so the house's card says what the walls
  are and why.

Head choice: the principal and second floors take two rowlock rings, crown 0.34 m above the head.
The third-floor heads (11.45 m) sit 0.37 m under the soffit (11.82 m), so two rings would leave no
course to the eave. They take soldier heads, 0.207 m tall.

## Costs

| | before (T-2266) | after |
|---|---|---|
| full GLB | 1,864,120 B | 1,860,744 B |
| web GLB | 892,916 B | 782,536 B |
| triangles | 2,218 | 8,264 |
| primitives / materials | 10 | 14 (four unit variants share one map and batch together) |
| embedded images | limestone + Glessner brick | limestone + K03 panel, its normal map, joint-free common buff |

In the app (`browser-validation.json`), every stand stays within budget:
- **Desktop, full detail:** 65-68 draws, 2.49-2.50 M triangles of a 3.8 M budget, 126-138
  textures, ready in 21.5 s.
- **Mobile, light detail:** 62-63 draws, 0.46 M triangles, ready in 9.6 s.

T-2266's street-eye stand read 62 draws and 2.499 M triangles. Frame times are software GL on
this runner, so they are a relative reading only.

## What the views show

- `*-street-and-return.jpg`: the pale stone front against the red-buff common return.
- `*-south-wall.jpg`: segmental heads on two floors and soldier heads under the eave. The firing
  spread reads as individual bricks and the panel repeat does not read as a pattern.
- `*-quoin-close.jpg`: courses level across the south-west quoin, and the string course turning
  it.
- `*-eave-heads.jpg`: the soot band darkening toward the soffit, and the soldier units.

## Not done

- **Every brick a solid** (the library's full form) was priced at about 52,000 bricks for these
  walls and refused. The panel is used at every tier.
- **A pressed front.** No pressed-brick front stands in the scene. The register's three (2100
  Sherman, 2126, 213-217 East Cullerton) each have their own build ticket. The pressed panel binds
  when T-1919 builds Sherman.
- The stone front's own fabric is K02's (T-2289), and the roof is K04's (T-2293).

Re-run: `python3 generators/k01_emit.py --only keith_house_1808_prairie`,
`tools/web_derivatives.sh --only keith_house_1808_prairie__as_built_1886.glb`,
`node tools/k01_contract.mjs --measure-asset keith_house_1808_prairie`, `tools/publish.sh`, then
`QA_VIEWPORT=desktop node tools/qa_k03_t2291.mjs` and the same with `mobile`.

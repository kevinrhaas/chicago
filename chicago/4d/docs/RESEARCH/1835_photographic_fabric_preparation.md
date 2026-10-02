# 1835 photographic fabric — the preparation map

T-1795, the first of three pieces of **T-1769** (owner, 2026-09-30: *"we said photographic
quality and i think that is a good standard"*). This page is the audit and the
material/integration map. It is not the proof: the proof assembly is **T-1796** and the
ground strip beside it is **T-1797**. Neither of those, nor this page, closes T-1210–T-1213
or T-1770–T-1772, and nothing here claims the town already meets the standard. A memo is not
the stop condition of T-1769. It is what the two proof runs build from, so they do not
re-read the same twelve files to start.

Every number below was measured on `dev` at `ee5da30e` (2026-10-01) unless it cites a record.
The script snippets that produced them are in § 7, so the next run can re-take them.

## 1. What Glessner v4 did that worked

Read from `docs/RESEARCH/glessner_house_v4.md`, `glessner_v4_work.md`,
`assets/textures/glessner-v4/README.md` + `material-library.json`,
`glessner-v4-qa/refined-06-final-review.md` and `default-promotion.md`, `tools/_glessner_lod.py`.

**The methods, in the order they paid off:**

1. **Reference-led audit before any material.** Fourteen owner views and six HABS sheets were
   read face by face into an opening schedule *before* a texture was made. Each reference was
   dated, and modern fabric (1946 paving, replacement doors) was excluded by name. The textures
   came last.
2. **Shape is geometry, surface is map.** Stone courses, brick joints, block boundaries,
   openings, roof laps and copper seams are physical geometry. The maps carry only what lies
   *inside* one unit: crystal, clay body, grain. Normal maps were never used to fake a course.
3. **Metric UVs that survive export.** `SurfaceUV` metric on `TEXCOORD_0` through the shared
   unwrap, repeats carried by `KHR_texture_transform`. Albedo and relief repeat at different
   rates (granite albedo 0.22 m, normal/roughness 1.6 m) so no single tile period shows.
4. **Original PBR, reproducible.** Ten numeric fabrics come from one seeded recipe
   (`generate.py --only <fabric>`). Three generated albedo studies are kept byte-unchanged,
   with their prompt, SHA256 and dimensions. No photographic pixels were sampled.
   Albedo is 2048² sRGB JPEG, normal is 1024² OpenGL PNG, roughness is 1024² linear PNG.
   Normal and roughness maps are filtered *before* reduction, which limits shimmer.
5. **Restraint by tint factor, not by a second map.** Four brick kilns share one clay fabric,
   varied by RGB multipliers (0.88 / 0.92,0.72,0.64 / 1.00,0.985,0.94 / 0.43,0.47,0.48).
6. **Real glass in real recesses.** A clear dielectric (transmission 0.94, IOR 1.52) in
   recesses closed at 0.90 m (dormers 0.60 m), with blinds as separate cloth. No reflections
   are painted into windows.
7. **Controlled comparisons on the actual exported asset.** Test panels came first: 3×2, 5×3
   and 6×3 rock-face subdivisions at normal strengths 0.4–1.0. Then the real GLB was
   re-imported under a fixed 800 px, 128-sample camera, in neutral light and a CC0 sky-only
   HDRI. Then the published browser: five stands × three tiers × two viewports.
8. **The derivative is audited, not assumed.** A decoded-geometry audit found 14-bit
   quantisation collapsing 6,146 of 20,000 lawn blades and 35,176 ornament triangles. A 16-bit
   recipe cut the worst position error from 3.31 to 0.65 mm.

**Corrections that worked:**

| defect | correction |
| --- | --- |
| Granite crystals read too large and pink | Albedo repeat 0.6 → 0.22 m, cool tint |
| Brick red/grey mosaic excessive | Shared fabric plus midpoint tints. The over-compressed tan trial was rejected too |
| Lawn read as a flat olive mat at courtyard distance | A 4 m albedo study with coherent 0.5–2 m growth/thatch variation over the 0.4 m tile |
| Glass read as diffuse grey panes | 6 % diffuse veil removed, recesses enclosed |
| Rock face too smooth (3×2 / 0.4); 6×3 made isolated pits | 5×3 at strength 1.0 (rough trim 0.8) |
| False diagonal joints from arch subtraction | Each stone built once, only its finished surfaces clipped |

**Residual limitations it declares:** carving, weathering, window interiors and blind positions
are reconstructions. The Full allowance (3.8 M triangles) applies only to the selected v4 record.
Photographic acceptance stayed the owner's comparison, never a validator's.

**What transfers to 1835 and what does not.** The *pipeline* transfers: the audit-first order,
geometry-for-shape, metric scale, seeded recipes, restrained tint variation, controlled
comparisons and the published-browser review. The *finishes* do not: granite, terracotta,
copper, varnished oak and a mown lawn are not 1835 Chicago. Neither does the *budget*. Glessner
spends 1.07 M master and 193 k light triangles on **one house**, and the 1904 scene peaks at 105
calls with it in view. The 1835 town's
Balanced rung has **46,232 triangles clear** at its worst stand (1,233,768 of 1,280,000,
`main.js` DETAIL, read 2026-09-26) and Light has 52,975 (772,025 of 825,000). Glessner's
per-building geometry cost or Full allowance must not be applied to every roof.

## 2. The 1835 runtime as it stands — what the proof starts from

- **Walls carry no maps.** `buildings.js` puts base colour *and* roughness on the vertex
  stream. `materialKey()` hashes map uuids and not colour, so every wall that differs only in
  paint shares a batch. That is the property any integration must keep: it is how household
  finish control (T-1210) and town batching coexist.
- **Roofs carry relief, and that is the template.** `roof-relief.js` (T-1488) binds the
  library's `normal_gl` + packed `orm` (G roughness, R AO) to the 321 `roof_shingle` and 164
  `roof_board` materials. It keys on the material name, which `docs/GLB-CONTRACT.md` § Roof
  coverings pins. It derives a metric UV *in the vertex shader* from world position, framed on
  the face (t = n × up, b = t × n), so no UV, attribute or bake changed. Cost measured there:
  two extra batches for the town's roofs. It loads on every tier.
- **Only roof textures are published.** `tools/publish.sh` copies four files per covering
  (material.json, normal_gl, orm). Every other library map stays in the repository.
- **Material names in the 503 web GLBs**, counted: `dark` 426, `roof_shingle` 321,
  `chimney` 303, **`wall` 242**, `trim` 230, `board` 164, `roof_board` 164,
  `heavy_timber` 164, `log` 112, `chinking` 108, `frame` 68, `glass` 63, `brick` 15,
  `fill` 8, `deck` 6, `earth` 3, `sign`/`paint`/`stone`/`iron`/`shutter` 1 each. **`wall` does
  not name its substrate**: clapboard, board-and-batten and vertical board all ship as `wall`.
  So the roof route cannot reach walls by name alone (see § 5).
- **The wall's module is already geometry.** `frame_dwelling._clapboard` builds every lap
  course at `siding_exposure_m`, with butt joints staggered on the stud lines.
  `logwork.hewn_log_wall` builds 0.34 m log courses with the chinking proud by 0.022 m.
  `texture_library.md` measured that the library's wall relief maps carry exactly those modules
  (32 clapboard courses, 12 log courses). **Binding them as they are would draw a second set of
  courses over the geometric ones, out of phase.** This is the main finding for walls. The
  Glessner rule (§ 1.2) says the maps should carry only what lies inside one board or one log.
- **The plank walks are pale because they borrow the signboard's tone.** `frontage.js` draws
  every walk in one untextured material, `TIMBER = 0xcbc2b1`. Its comment calls this "sawn
  board, weathered — the signboard's own tone". It is the sRGB of the signboard archetype's
  linear `SIGN_RGBA` (0.60, 0.54, 0.44), the same hex as `signage.js`'s `TIMBER_HEX`, and its
  luminance is **Y 0.545, L\* 78.7**. That is brighter than the library's whitewashed clapboard
  (L\* 75.0) and close to white lead paint (L\* 82.8). The library's `plank_walk_weathered`
  averages **L\* 36.6**, and the material sheet's own `weathered_board` (linear 0.335, 0.310,
  0.268) is L\* 62. The owner's "white boards" report is this constant, not lighting. It is
  T-1211's to fix (§ 6).
- **The ground is runtime canvas.** The 1835 prairie is a 256 px canvas tile over 11 m
  (`prairie-tile.js`, anisotropy held at 4 for the software rasteriser). Streets are
  `streets.js::roadTexture`: a 128 × 256 canvas with two Gaussian ruts at 0.29 and 0.71, and a
  body alpha of 0.28–0.93 that lets the prairie show through. That is the "paired tread on
  grass" T-1770 removes. The precedent for a textured ground band is 1904's
  `street-grid.js`, which binds basecolor + normal + ORM from `prairie_1904_pbr/` at the metric
  tile `material.json` states, with a flat-tone fallback.

## 3. The library, measured

`assets/textures/chicago_1835_pbr/` has 25 materials, all from
`tools/generate_1835_pbr_library.py` with a committed `generator_seed`. Each has a 1024² sRGB
basecolor, linear roughness/AO/metallic, packed `orm`, 16-bit linear `height16`, and **both**
`normal_gl` and `normal_dx`. One material (`muddy_rutted_street`) is derived from the
AI-generated study `tools/source_mud_ai.png`. The licence (`LICENSE.txt`,
`assets/LICENSES.md` § The 1835 PBR texture library) is project-permissive. Its one condition
is that confidence labels and notes travel with the maps.

Luminance is the linear-sRGB mean of the basecolor, as L\*. The spread is the 5th–95th
percentile L\*. Wire is the PNG bytes of `normal_gl + orm`, the pair a renderer binds.

| material | span m | px/m | seed | L\* | spread | wire MB | tier (its own) |
| --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| clapboard_weathered_oak | 4.48 | 228.6 | 18350701 | 43.2 | 41–45 | 0.50 | attested/inferred |
| clapboard_white_lead_paint | 4.48 | 228.6 | 18350895 | 82.8 | 80–86 | 0.54 | attested for Sauganash |
| clapboard_whitewash | 4.48 | 228.6 | 18350798 | 75.0 | 71–79 | 0.52 | attested where recorded |
| clapboard_red_oxide | 4.48 | 228.6 | 18350992 | 30.2 | 28–32 | 0.49 | period-inferred |
| board_and_batten_weathered | 4.272 | 239.7 | 18351089 | 39.7 | 37–42 | 0.49 | reconstructed |
| vertical_sawn_board | 4.58 | 223.6 | 18351186 | 42.9 | 40–46 | 0.39 | reconstructed |
| hewn_log_oak_chinked | 4.08 | 251.0 | 18351283 | 61.3 | 48–77 | 0.49 | attested/inferred |
| sawn_board_weathered | 4.00 | 256.0 | 18351380 | 37.7 | 35–41 | 0.43 | inferred |
| heavy_timber_weathered | 4.00 | 256.0 | 18351574 | 27.7 | 25–30 | 0.44 | inferred |
| fresh_sawn_framing | 4.00 | 256.0 | 18351477 | 54.7 | 51–58 | 0.45 | inferred |
| wood_shingles_weathered | 4.48 | 228.6 | 18351671 | 29.1 | 26–32 | 0.66 | attested once |
| roof_boards_weathered | 4.00 | 256.0 | 18351768 | 30.9 | 28–34 | 0.48 | inferred |
| chicago_clay_brick_lime_mortar | 4.20 | 243.8 | 18351865 | 63.0 | 52–74 | 0.63 | fabric attested; module reconstructed |
| limestone_rubble_lime_mortar | 4.00 | 256.0 | 18351962 | 68.9 | 65–74 | 0.80 | reconstructed |
| cat_and_clay_chimney | 2.04 | 502.0 | 18352059 | 65.9 | 63–68 | 0.90 | reconstructed |
| plank_walk_weathered | 4.00 | 256.0 | 18352641 | 36.6 | 33–40 | 0.49 | attested form; inferred finish |
| dock_timber_tar_darkened | 4.00 | 256.0 | 18352738 | 15.8 | 13–18 | 0.41 | inferred |
| signboard_weathered | 2.00 | 512.0 | 18352932 | 47.3 | 43–52 | 0.45 | reconstructed |
| blue_painted_shutter | 2.00 | 512.0 | 18353029 | 30.2 | 27–34 | 0.46 | attested for Sauganash |
| wrought_iron_forged | 1.00 | 1024.0 | 18352835 | 13.0 | 10–16 | 0.57 | period-inferred |
| muddy_rutted_street | 8.00 | 128.0 | 18352253 | 31.0 | 17–41 | 4.63 | attested condition; reconstructed wear |
| packed_black_loam | 6.00 | 170.7 | 18352156 | 23.0 | 22–25 | 0.85 | attested geology |
| wet_prairie_muck | 6.00 | 170.7 | 18352350 | 20.0 | 18–22 | 0.93 | attested/inferred |
| lake_michigan_dune_sand | 6.00 | 170.7 | 18352447 | 57.7 | 54–62 | 0.60 | attested setting |
| river_stone_gravel_fill | 4.00 | 256.0 | 18352544 | 45.0 | 42–48 | 0.42 | inferred |

**What the measurement says.**

- **The albedo is nearly flat.** Twenty-two of 25 basecolors span ≤ 10 L\* from the 5th to the 95th
  percentile; only the log (chinking stripes), brick (mortar) and mud exceed it. That is what `texture_library.md` meant by "tinted noise", and it is why the
  basecolors were rightly never bound. A photographic surface needs the variation Glessner
  bought with its 4 m lawn study (§ 1). In this library it lives only in the relief maps.
- **The mud is an outlier on every axis:** widest spread (17–41), the only AI-derived map, and
  7× the wire cost of the next ground map (4.63 MB against 0.93). It also carries its ruts in
  an 8 m tile. On a street that is a visible 8 m repeat of the same ruts, the same failure as
  `roadTexture`'s paired bands.
- **The sand already sits where the owner asked:** L\* 57.7, muted grey-tan
  (`colors` 177,163,129 / 129,122,101), which is "cooler grey/beige", not yellow. What it
  lacks is low-frequency variation (spread 54–62). That is a mask's job, not a new albedo.
- **The chimney texel density is the one real defect:** 502 px/m against the 251 of the
  chinking row it is meant to match (`texture_library.md`'s open divergence).

## 4. Decisions per substrate

Columns the ticket requires that are uniform across the library are stated once:
**channels** basecolor sRGB, roughness/AO/metallic/height linear, `orm` = R AO · G roughness ·
B metallic; **normal convention** OpenGL (`normal_gl`) for three/glTF, with `normal_dx` kept for
the Unreal target; **recipe** `tools/generate_1835_pbr_library.py` + the seed in § 3;
**licence** § 3. "Relief" means `normal_gl` + `orm`. The basecolor stays unbound unless the
row says otherwise, so colour remains the household's, on the vertex stream (§ 5).

| substrate | decision | map source and module | remaining gap | consumer |
| --- | --- | --- | --- | --- |
| Bare wood clapboard | **Regenerate** a board-face relief with no course lines: grain along the board, raised grain, checks, a lap shadow carried by geometry | Same generator, seed 18350701, a no-course mode. Span 2.24 m (16 × 0.14 m), so any residual period divides the lap. 228.6 px/m kept | The course module is already geometry (§ 2); the generator lacks the mode | T-1796, T-1210 |
| Painted (white lead) and red oxide clapboard | **Reuse the bare-wood relief**; the finish is colour + roughness on the vertex | White lead's own map, roughness 0.60 vs 0.85, gives the painted roughness *ratio*. Its basecolor is not bound | Mapped materials cannot use `perVertexRoughness` (buildings.js). Needs the roughness-ratio patch in § 5 | T-1210 |
| Whitewashed wood | **Reuse the bare-wood relief.** Whitewash coats the substrate (materials.md § 2.1); chalky roughness 0.90 by ratio | Whitewash map for the ratio only | Attested only where recorded. T-1210's rule must not spread it | T-1210 |
| Board-and-batten, vertical board | **Regenerate as for clapboard** if battens and board edges are geometry; **reuse** if they are flat | Seeds 18351089, 18351186; set-outs 0.356 m and 0.229 m | Not yet checked whether `BATTEN_SPACING_M` is built as geometry. T-1796 reads the archetype before binding | T-1210 |
| Hewn log | **Regenerate** a log-face relief: adze facets, end checks, grain. No chinking band (chinking is separate proud geometry) | Seed 18351283; one log course is 0.34 m (`logwork.COURSE_M`) | The current map's 12 courses would double the geometry | T-1796, T-1210 |
| Chinking and chimney daub | **Reuse `cat_and_clay_chimney`** for both, one substrate. **Resample** to 2.04 m at 512 px (251 px/m) for parity with the log row | Seed 18352059 | Texel parity (§ 3). The chinking strip is 0.022 m proud, so relief is fine-scale only | T-1210 |
| Shingles, roof boards | **Reuse as bound** (T-1488) | 4.48 m / 4.00 m | The roofs gain only the albedo-modulation channel (§ 5) | T-1210 |
| Brick and lime mortar | **Reuse relief**; tint by vertex with Glessner's restraint (no mosaic). Bind only behind an L-number for the 4.20 m rate | Seed 18351865 | No source gives a Chicago brick course. Only 15 `brick` materials exist, so the batch is small | T-1210 |
| Stone rubble | **Reuse**, only where stone is selected (one `stone` material) | Seed 18351962 | Bare masonry itself is unattested (lighthouse record) | — |
| Plank walk | **Reuse relief + the basecolor's tone range as the palette bound**; fix the walk's colour constant | 4.00 m, 256 px/m, seed 18352641; palette bounded by the library's 118,101,76 / 72,67,58 and `heavy_timber` | `frontage.js` draws the signboard tone (§ 2). No per-owner variation channel yet | T-1796, **T-1211** |
| Heavy timber, dock timber | **Reuse relief** (164 `heavy_timber` materials) | Seeds 18351574, 18352738 | — | T-1211, T-1771 |
| Sawn board (outbuildings) | **Reuse relief** where board widths are not geometry | Seed 18351380 | `outbuilding.py` builds board widths as geometry in places. Check as for battens | T-1212 |
| Wrought iron (props, hitching rails) | **Reuse**; the only metallic substrate, so its `orm` B channel stays metallic | Seed 18352835, 1.00 m | — | T-1211, T-1212 |
| Signboard and paint | **Reuse `signboard_weathered` relief** under the existing lettering atlas. Lettering stays in `signage.js` | Seed 18352932, 2.00 m | Whether a given sign is painted is T-1213's ruling. The 0.60 linear board tone is the archetype's | T-1213 |
| Glass and recessed sash | **New geometry, no map:** Glessner's enclosed recess + dielectric, scaled to 1835 sash | — | Priced per opening in § 5. 63 `glass` and 426 `dark` materials today | T-1796 |
| Packed street dirt | **New wear mask + reuse fine detail.** A seeded world-space low-frequency mask (20–60 m) for traffic lanes, hoof paths and wet patches. The fine detail comes from `packed_black_loam` relief, not the mud tile's ruts. *T-1797 measured that relief flat; the fine detail is a generated grit tile instead (§ 8)* | Loam seed 18352156, 6 m | The 8 m mud tile's ruts repeat. `roadTexture` is translucent. Cross-sections are geometry (T-1770) | T-1797, T-1770 |
| Mud, wet ground | **Reuse `muddy_rutted_street` for local mud only**, under the mask, never as the whole roadway | Seed 18352253, 8 m, AI-derived | 4.63 MB wire. Downsample its relief to 512² before publishing | T-1797, T-1770, T-1771 |
| Bank soil | **Reuse loam + muck**, blended by a wetness mask. *T-1797: muck colour reused; the loam's place taken by the grit tile (§ 8)* | Seeds 18352156, 18352350 | — | T-1797, T-1771 |
| Lake sand | **Reuse colour and relief**; add the low-frequency variation by mask. Dune ridges are terrain, not map. *T-1797: colour reused at a quarter of its grain; its relief is flat (§ 8)* | Seed 18352447, 6 m | Flat spread 54–62 | T-1797, T-1772 |
| Prairie and grass | **New:** a July tall-grass ground study, adapting the method of Glessner's 4 m lawn (coherent 0.5–2 m variation), not its material | The runtime prairie tile is `prairie-tile.js` (256 px, 11 m) | A mown lawn is not a prairie; plants stay the flora layer | T-1797, T-1772 |

Fresh-sawn framing (seed 18351477) has no consumer today and is left as vendored.

## 5. Integration — three strategies priced, one proposed

**A. Shared relief per substrate, colour on the vertex (proposed).** Generalise
`roof-relief.js` to every substrate in § 4: one shared `normal_gl` + `orm` pair per substrate
and a metric UV derived in the shader. On a wall the face frame gives t horizontal and
b straight up, so the projection is exact there too. It needs two small additions:

- **Albedo modulation without a colour texture.** For every non-metal substrate the `orm` B
  channel is metallic ≡ 0, so it is free. Pack the basecolor's *luminance ratio to its own
  mean* there, read as `vertexColour × (0.5 + B)` in a fragment patch. The household finish
  stays on the vertex, the batch stays one per substrate, and no texture is added. Iron is
  excluded because its B channel is real.
- **Roughness by ratio.** `roughness = vertexRoughness × (orm.G / mean_roughness)` keeps each
  finish's roughness (painted 0.60, whitewash 0.90) on one shared map. This is the patch that
  answers why mapped materials cannot use `perVertexRoughness`.

*Cost.* Draw calls: +1 batch per bound substrate in view, by T-1488's measurement (two
coverings, two batches). The wall substrates of § 4 add about **six** against the 215 cap.
Wire: 0.39–0.66 MB per wood/masonry substrate, from § 3; six substrates ≈ **3 MB**. GPU: a
1024² RGBA8 texture with mips is 5.33 MiB, so a substrate pair is 10.7 MiB and six are
**≈ 64 MiB**. At Light, bind 512² mips (2.7 MiB per pair, **≈ 16 MiB**) rather than dropping
relief, because Light must not lose the substrate distinction it has today on roofs.
Bake: **none** for the shader route itself.

*Its one contract question.* The `wall` name (§ 2). Two routes, both priced:

1. **Name the substrate** in a `wall_material_name()` mirroring `roof_material_name()`:
   `wall_clapboard`, `wall_batten`, `wall_vertical`. That is a `docs/GLB-CONTRACT.md` proposal
   (bilateral, not unilateral) plus a rebake of every structure with a `wall` material: 242
   materials across the web set.
2. **Read the substrate from the sidecar** at load. No bake, but the renderer then depends on
   a record field staying in step with the generator's `wall_substrate()`.

Route 1 is proposed, on the T-1488 precedent that a pinned name is the cheaper contract to
keep. T-1796 can avoid both, because its proof assembly names its own materials.

**B. Per-building albedo (the Glessner route), rejected for the town.** One material and
texture set per building multiplies batches by buildings. That is hundreds against a 215 cap;
the 1904 scene, with one such house, already peaks at 105. Kept only for a *selectable hero version* with its
own documented allowance, as v4 was.

**C. One array texture for all substrates, indexed per vertex.** One batch total instead of
one per substrate. It costs a vertex attribute (a GLB-CONTRACT change and a full bake) and a
custom sampling chunk, since `MeshStandardMaterial` does not sample arrays. It is the fallback
if A's measured batch count crosses the cap. It is not proposed first.

**Geometry is priced separately from maps.** A recessed sash with frame, sill and a meeting
rail is roughly 40–80 triangles more than today's flat opening. At Balanced's 46,232 clear,
about **600–1,100 openings** spend the whole rung. Recesses therefore belong on the Full and
Balanced master and are flattened on the Light derivative, the way Glessner keeps 172 openings
in both but on a lighter mesh. T-1796 measures the real figure on its proof with
`tools/measure_detail_ceilings.mjs` and does not extrapolate this one.

**The ground** is a runtime canvas and stays one. T-1797 binds a ground set the way 1904's
`street-grid.js` already does (basecolor + normal + ORM at the `material.json` tile, flat-tone
fallback). The terrain prairie keeps anisotropy 4 and a 256 px tile until a measured frame on
the software rasteriser says otherwise. `prairieTexture()`'s own note shows 8 taps halving the
frame rate.

## 6. Handoffs

- **T-1796 (proof assembly):** clapboard and log samples from the regenerated board-face and
  log-face relief (§ 4); a recessed sash; a plank walk in the § 4 palette with per-owner
  variation; a painted signboard. Bake through the real path and review with
  `tools/render_structure_review.py` under fixed neutral and scene light. Then the browser at
  390×780 and 1280×800 against the current treatment and Glessner. Strategy A with the two
  patches. Report calls, triangles, texture bytes and load time at all three tiers.
  *Done in T-1801 (piece 2 of T-1796), 2026-10-01:* `docs/RESEARCH/1835_fabric_proof.md`. The
  two no-course maps are in the library. The assembly was built through the real Blender →
  gltf-transform path and reviewed in the town's own light at both viewports against the current
  treatment and Glessner. Costs were taken at all three tiers. The recessed opening measured
  +162 triangles, not 40–80. Transmission glass was rejected. A finish now needs a grain
  strength as well as a colour and a roughness.
- **T-1797 (ground strip):** the wear mask, the loam/mud/muck/sand reuse and the new prairie
  study of § 4, through the terrain/runtime-canvas path. *Done 2026-10-01 — § 8.*
- **T-1211 (plank works):** the white walk is `frontage.js`'s `TIMBER`, the signboard's linear
  (0.60, 0.54, 0.44) at L\* 78.7. The palette bound is the library walk (L\* 33–40 across its
  spread) up to the sheet's `weathered_board` (L\* 62), in grey, brown, grey-brown and dark
  grey-brown, varied per owner by a vertex colour. That keeps the layer's single draw call.
  The signboard keeps its own tone in `signage.js`; only the walk's borrowing ends.
  *Done in T-1800 (piece 1 of T-1796), 2026-10-01:* the walks and crossings carry four
  weathered tones (L\* ≈ 38–52) on a vertex colour, varied per block face and per board inside
  the L\* 33–62 bound, in the layer's existing material and draw calls (L320). Measured lit at
  1280×800 on Lake Street: the walk went from L\* 75 to L\* 44. The per-business key is still
  T-1211's, and the relief (grain, end grain, wear) is T-1801's proof.
- **T-1770 / T-1771:** `roadTexture`'s paired 0.29/0.71 ruts and 0.28–0.93 alpha body are what
  reads as "two treads on grass". The full-width opaque roadbed is geometry plus the § 4 mask.
  Never tile the 8 m mud as the roadway.
- **T-1772:** the sand's colour is already the requested grey-beige. Its missing variation is
  low-frequency (mask), and its ridges are terrain.
- **T-1210 / T-1212 / T-1213:** the § 4 rows they consume. No finish, attested or not, moves
  in this run.

## 7. How the numbers were taken

- Luminance: each basecolor resized to 256², decoded sRGB → linear per channel,
  Y = 0.2126 R + 0.7152 G + 0.0722 B, mean and 5th/95th percentile, then CIE L\*.
- Wire bytes: `os.path.getsize` of `<id>_normal_gl.png + <id>_orm.png`.
- Material names: the JSON chunk of every `assets/web/*.glb` (503 files), `materials[].name`.
- `TIMBER`: `0xcbc2b1` decoded the same way, Y 0.545. `weathered_board` from
  `generators/common/materials.py`.
- GPU bytes are arithmetic (w × h × 4 × 4/3), not a browser reading. T-1796 replaces them
  with a measured one.

## 8. The ground strip — T-1797, measured

The third piece of T-1769. A 48 × 12 m strip on open prairie south of the town (centre
E 145, N −455: 85 m from the nearest building, 56 m from the nearest opened street, the
heightfield between 0.77 and 0.81 m, dry of the wet band), drawn only under
**`?proof=ground`** (`/4d/dev/?proof=ground`; `&anchor=ground_strip_above` and
`&anchor=ground_strip_close` for the other two views). West to east: packed street dirt,
worn bank soil, grey sand, sand thinning into sparse prairie, every side feathered into
the terrain's own prairie. It is a sample, not a place: nothing records these grounds at
that spot, and the strip claims nothing about where in 1835 any of them lay.

**Code.** `renderers/web/js/ground-strip-mask.js` (layout, mask and grit pixels, the
weight function; imports nothing, so a tool can read it from Node) and
`renderers/web/js/ground-strip.js` (the material and mesh). `terrain.js` now exports its
prairie fragment as `PRAIRIE_FRAGMENT`, unchanged, so the feather lands on the terrain's
own prairie rather than a copy of it; the compiled ground shader is byte for byte what it
was. `main.js` imports the strip only under the flag.

### The finding: the library's ground relief is flat

§ 4 gave the dirt's fine detail to `packed_black_loam`'s relief. Bound at full strength it
drew a smooth brown at standing distance (`ground-strip-proof/close-1280-library-loam.jpg`),
and the maps say why — read at 256², sRGB units of 255:

| material | basecolor L mean | basecolor SD | `normal_gl` SD (R / G) |
|---|---|---|---|
| packed_black_loam | 54.8 | 2.19 | 0.93 / 0.94 |
| wet_prairie_muck | 47.2 | 2.89 | 1.18 / 1.19 |
| lake_michigan_dune_sand | 137.8 | 6.21 | 1.04 / 0.68 |
| muddy_rutted_street (AI-derived) | 70.7 | 17.07 | 8.91 / 8.95 |

The three procedural ground materials carry almost no relief at any scale; only the
AI-derived mud has any, and § 4 already refuses it as a roadway (its 8 m ruts repeat).
**So the ground rows move from "reuse relief" to "regenerate relief".** The proof's
regeneration is a **grit tile**: `gritTilePixels()`, a seeded runtime canvas, 256 px over
1.6 m (6 mm a texel), clods at ~3 cm, grit at ~1 cm, dust at a texel and 420 pebbles and
hoof pocks as round bumps; R is height (read as luminance grain over its own mean,
SD 25 of 255), G/B the OpenGL normal. One fetch gives grain and relief together
(`ground-strip-proof/close-1280.jpg`). The other library rows were not measured here;
T-1801 is regenerating its own wall faces.

### The method, as built

- **Coarse: one runtime-canvas mask**, 416 × 128 px at 8 px/m, four channels — traffic
  wear (anisotropic value noise, 12 × 1.4 m then 4 × 0.5 m cells, long along the
  direction of travel, falling off over the outer 3 m of the 12 m roadway), wetness
  (7–18 m), clumping (0.6–2 m) and broad tone (20–60 m). One fetch.
- **Fine: the grit tile** for every ground, at a strength per ground: full on the dirt,
  0.4–1.0 on the bank as it wets, 0.2 on mud (water levels it), 0.35 on sand.
- **Colour: recorded tones × grain** for the dirt (worn lanes sRGB 126,112,91; between
  them 96,86,69) and the dry bank (98,86,66); the muck's own basecolor for wet bank and
  mud (mud at 0.9 of it, roughness 0.42); the sand at tone 136,128,106 × a quarter of the
  library's grain × a fifth of the grit's. These are reconstructed proof values bounded
  by § 4's rows, not a source's; whichever ticket puts one into the town records the
  liberty there.
- **Edges:** every band boundary jitters by up to ~2 m on the clumping and broad scales;
  the prairie arrives in the sand as islands (a clump turns once the ramp passes its own
  clump value); untrafficked shoulders keep grass; all four sides fade to the terrain's
  prairie over 2 m on a jittered line. The sward is told the same weights
  (`stripWeights`, the JS twin of the shader's) through `growthBlocked`, so plants
  stand where the shader draws prairie and thin where it draws it arriving.
- **Relief is normal-mapped in a world tangent frame** (east, north, up). It does not
  stand in for a cross-section; the strip lies on the heightfield, lifted 3 cm with
  polygon offset. Grading is T-1770's.

### Costs, measured in the scene (SwiftShader; source tree, confirmed on the published mirror; 1280×800 and 390×780)

| | the strip |
|---|---|
| triangles | 6,656 (a 0.5 m grid over the strip and its feather), one draw call |
| textures | 5: mask 416×128, prairie 256², grit 256² (runtime canvases), muck and sand basecolor 1024² |
| GPU bytes (arithmetic, full mips) | **12.17 MB**, of which 11.18 MB is the two 1024² basecolors. At 512² they are 2.80 MB and the strip 3.79 MB. With the library's flat normals and the loam bound, as § 4 proposed, it was 34.19 MB |
| wire | 669,610 B of PNG (muck 267,075 + sand 402,535) + two material.json; the canvases cost nothing on the wire |
| fetches per fragment | 5, against the terrain's 1 (8 with the library normals bound) |
| build | 84–121 ms on the runner, mask and grit generated and both PNGs decoded |
| frame | 0.24–0.26 fps with the strip shown or hidden at the arrival view, full detail; the software rasteriser's frame is the whole town's and the strip does not move it. Not a GPU reading |

Captures: `docs/RESEARCH/ground-strip-proof/` — arrival (looking east along the dirt),
close (the grit at ~3 m), above (14 m, the whole strip) at 1280×800, above at 390×780,
and the library-loam close for comparison.

**Residual limits.** The 6 m sand tile's ripple still shows faintly from 14 m at a
quarter strength; the bank's wet half reads as one dark patch from above, which is the
wetness mask's 7–18 m scale being large for an 8 m band; the strip's own prairie
texture is a second copy of the terrain's 256 px canvas (0.35 MB) rather than a shared
one. None of these blocks the hand-off.

### Hand-offs

- **T-1770 (streets):** replace `streets.js::roadTexture`'s two ruts and translucent body
  with this dirt: two tones × grit grain, the anisotropic wear mask laid in each street's
  OWN frame (u along the centreline — the proof's mask is axis-aligned because the strip
  is), shoulders that thin to grass, mud as muck where wetness and wear coincide. One
  shared grit tile serves the whole town; the per-street mask is the new work. At five
  fetches the street material belongs on the street ribbons, not on the terrain shader,
  which keeps its one-fetch rule.
- **T-1771 (bank, docks):** the bank's dry-to-wet blend (dirt grain → muck at 0.75 by
  wetness 0.5–0.8, roughness 0.95 → 0.62), with a finer wetness scale than the strip's.
- **T-1772 (lakeshore):** the sand recipe above and the clumped prairie arrival with the
  sward told the same weights; the library sand's relief is flat, so dune ridges are
  terrain and the fine sand grain is the grit tile at low strength.
- **T-1210–T-1213:** nothing in this strip binds a building material to the ground. The
  library-flatness check (`basecolor`/`normal_gl` SD) is worth running on any library row
  before a ticket builds on its relief.
- **The library:** `packed_black_loam`, `wet_prairie_muck` and `lake_michigan_dune_sand`
  are flat; regenerating their relief in `tools/generate_1835_pbr_library.py` (or
  retiring their normals for the grit tile) belongs to whichever of T-1770–T-1772 first
  ships ground to the town.

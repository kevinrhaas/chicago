# 1835 fabric proof — the assembly, baked and looked at

T-1801, the second piece of **T-1796** and the last of **T-1769**'s proof work (owner,
2026-09-30: *"we said photographic quality and i think that is a good standard"*). The
preparation map is `1835_photographic_fabric_preparation.md`; this page is what happened when
its strategy A was built on real geometry and looked at in the town's own light.

**Nothing in the town changed.** The proof is not a record, is not placed in any scene, and is
not read by `generators/build.py`, `mesh_inputs.py` or the staleness gate. It shows that the
method works and what it costs. Turning the method on for the town's walls is T-1210's job,
and this page hands that job its steps (§ 5). It does not close T-1210–T-1213.

## 1. What was built, and the one command that rebuilds it

    tools/fabric_proof_1835.sh            # ~3 min; Blender + gltf-transform + Chromium

| step | tool | what it does |
| --- | --- | --- |
| maps | `assets/textures/chicago_1835_pbr/tools/generate_1835_pbr_library.py` | two new library materials with **no course line**: `clapboard_board_face` (seed 18350701, 4.48 m, 228.6 px/m) and `hewn_log_face` (seed 18351283, 4.08 m, 251.0 px/m). The spans are 32 × 0.14 m and 12 × 0.34 m, so any leftover period still divides the course. The prep map's 2.24 m at 228.6 px/m was not possible at 1024 px, so the parent's span and density were kept. |
| geometry | `tools/build_fabric_proof_1835.py` (pinned Blender 4.5.3) | a 4.8 m clapboard bay and a hewn-log pen, with a framed signboard and a plank walk. The lap is `frame_dwelling._clapboard`'s profile, and its butt joints come from `_joint_positions`. The bay is wider than `CLAPBOARD_RUN_M`, so a joint actually lands. The pen IS `logwork.hewn_log_wall`. The sash is new: `WIN_W_M` × `WIN_H_M`, six-over-six, recessed 0.10 m, glazed, and enclosed by a dark room 0.60 m deep. `--opening flat` builds the town's current `_opening` instead, for the comparison. Exported through `emit.unwrap` + `emit.export_glb`. |
| derivative | the pinned gltf-transform 4.5.0 | `web_derivatives.sh`'s exact flags: `optimize --compress false --simplify false --palette false`, then `meshopt --quantize-position 14` |
| packing | `tools/fabric_proof_1835_maps.py` | strategy A's relief pair per substrate at 1024 px and 512 px (§ 3) |
| review | `tools/fabric_proof_1835_review.mjs` + `tools/fabric_proof/` | Chromium at 390×780 and 1280×800. **Lit by `renderers/web/js/world.js`'s own `createWorld`**: the walkthrough's sun, sky, environment, exposure and shadow rig at 12:30 on 1 July 1835. Also a neutral overcast field with no sun. Writes `1835-fabric-proof/*.jpg` + `review.json`, and fails on any page or console error. |

Build hashes on this run: master `fabric_proof_1835.glb` 830 triangles, flat-opening master
668. The sha256 of every file is printed by the driver. Nothing in the work directory is
committed. The maps are re-derived by the generator, and the GLBs by the build.

## 2. The comparison — `1835-fabric-proof/`

Each shot is at both viewports (`desktop-*`, `mobile-*`):

| shot | what it shows |
| --- | --- |
| `current-wide`, `current-close` | the town's treatment today. Colour and roughness come from the material and no map is bound. The opening is a dark panel proud of a trim surround. |
| `courses-close` | the route the prep map **refused**: the library's course-bearing `clapboard_weathered_oak` bound over the modelled lap. A second, thinner set of course lines runs out of phase with the geometry. The refusal is now a picture rather than an argument. |
| `proposed-wide`, `proposed-close` | strategy A on the no-course maps, with the recessed sash |
| `proposed-close-whitelead` | the same wall dealt `white_paint`: one shared relief, with the finish changing only colour, roughness and how much grain shows (§ 3) |
| `proposed-close-neutral` | overcast, no sun. Relief that only reads under a grazing sun would show up here as a flat wall, and it does not. |
| `proposed-close-transmission` | the GLB's own `KHR_materials_transmission` glass (Glessner's dielectric, IOR 1.52) |
| `glessner-wide`, `glessner-close` | the promoted Glessner v4 web derivative under the same rig. Wide is `render_structure_review.py`'s `prairie-entry-detail` stand, 10.9 m off the facade. Close is 5.9 m. |

**The critique the ticket asked for**, read off those captures:

- **Scale and grain.** At 2.5 m the board face reads as weathered board: grain along the
  board, sparse drying checks, broad 0.5–2 m weathering. At 9 m the grain dissolves into a
  weathering tone, as it should. No tile repeat is visible across the 4.8 m bay.
- **Seams.** None. The UV is metric and continuous across every lap lip and butt joint,
  because it comes from world position (`roof-relief.js`'s frame). The library maps are
  periodic.
- **Relief vs. geometry.** With the no-course maps, the only course lines are the modelled
  ones. With the course-bearing maps they double (see `courses-close`). That settles § 2 of
  the prep map by looking.
- **Glazing depth.** The 0.10 m recess and the enclosed room give the opening depth. The
  upper lights pick up the sky in the panes, and the lower ones show the dark room. The town's
  flat panel has neither.
- **Glass.** Transmission was **rejected on the look and on the cost**. It reads milky,
  which is Glessner's own "glass read as diffuse grey panes" defect, and it doubles the frame:
  the main pass goes from 11 calls / 846 triangles to 21 / 1,690, because three re-renders the
  opaque scene for the transmission buffer. The adopted glass is the sheet's `GLASS` colour at
  roughness 0.05 over the enclosed room.
- **Roughness.** One shared map carries unpainted 0.86 and white lead 0.60, through the ratio
  patch (§ 3). The painted wall is visibly glossier and keeps the same relief.
- **Colour restraint.** Board-face albedo modulation spans 0.81–1.21 (p5–p95), and the log
  face 0.71–1.31. A coat of paint lets 30 % of it through (§ 3).
- **Contact shadows.** The town's shadow map draws the sill, casing, signboard, lap lips and
  the walk's edge. The recess casts its own shadow line at the head.
- **Shimmer.** These are stills, so shimmer was **not assessed**. Anisotropy is 8 (4 at
  Light), the same as the roofs. A walking capture is T-1210's to take on the town.
- **Against Glessner.** Glessner's granite has a richer albedo than any 1835 wood here, by
  design: the 1835 colour stays on the vertex so a household's finish can move it. Its
  glazing method transfers. Its geometry budget does not (§ 4).

**Defects found and fixed while iterating** (each one is a rule the next run can reuse):

1. **The derivative step erased the material names.** `gltf-transform optimize` without
   `--palette false` folded all nine materials into `PaletteMaterial001`/`002`. Nothing could
   then key a relief on a name. It was measured on a town master as well: the blacksmith's six
   materials became one. `web_derivatives.sh` already passes the flag (K36(b)). Any NEW path
   to a derivative must pass it too.
2. **A relief branch in shader code is shared by every material.** three caches a program by
   `onBeforeCompile`'s source text, so a per-material branch written into the string (the
   signboard's 90° turn) was silently applied to none of them. Per-material differences are
   uniforms. `roof-relief.js` is safe today only because its two coverings differ only in
   uniforms.
3. **Paint showed the wood's colour.** At full strength the albedo modulation made white lead
   read as a photograph of wood painted over. A finish needs a grain strength. 0.3 for a
   coating is this proof's reading, and that is a reconstruction.
4. **Upright boards grained across.** The face frame puts the grain horizontal on every
   vertical face. That is right for clapboard, logs and a signboard's boards, and wrong for a
   casing's uprights, a batten or a vertical-board wall. Trim and sash are left unbound in the
   proof for that reason. A grain axis per board is something the shader cannot know from a
   position and a normal (§ 5).
5. **Checks too heavy, log facets as blotches.** The first board face split like firewood. The
   first log face had round dark facets coupled into the colour. The fix was sparser checks,
   and scallops cut across the grain in one run per course, as relief only.
6. **Transmission glass** — see above.

## 3. Strategy A, as built

Generalised from `roof-relief.js`: a metric UV derived in the vertex shader on the face's own
frame (t = n × up, b = t × n; a horizontal face falls back to a stated axis, which is the deck's
board direction), and one shared relief pair per substrate. Colour stays on the material, and
on the vertex stream in the town. The two patches the prep map priced are both in
`tools/fabric_proof/proof.js::relief()`:

- **Albedo modulation without a colour texture.** `orl.B = 0.5 · L / mean(L)` (linear
  luminance of the basecolor), and `diffuse *= mix(1, 2·orl.B, grain)`. The mean is 1, so the
  household's finish is the mean and the wood's grain is the variation around it. Metallic
  is 0 on every substrate here, so B was free. Iron is the exception and keeps its metallic
  channel.
- **Roughness by ratio.** `roughness = finish roughness · orl.G / mean(orl.G)`. This is what
  lets a mapped material carry each finish's own roughness. Today `perVertexRoughness` cannot.

## 4. Costs, at the three tiers

Taken on the desktop wide stand, where every substrate is in view. "Main pass" holds the
shadow map, and the shadow pass is in the second figure. Load is from navigation to first
measured frame, from a local server, so it is decode + upload + compile with no network.
`review.json` has every shot.

| | calls (main / +shadow) | triangles (main / +shadow) | textures | GPU (mip-chained RGBA8) | wire, maps | load |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| current, any tier | 10 / 17 | 684 / 1,352 | 1 | 0.8 MiB | 0 | 180 ms |
| **proposed, Full** | 11 / 19 | 846 / 1,676 | 11 | 46.2 MiB | 3.24 MB | 467 ms |
| **proposed, Balanced** | 11 / 19 | 846 / 1,676 | 11 | 46.2 MiB | 3.24 MB | 457 ms |
| **proposed, Light** (512² maps, anisotropy 4) | 11 / 19 | 846 / 1,676 | 11 | 12.2 MiB | 1.30 MB | 337 ms |
| proposed, Full, transmission glass | 21 / 29 | 1,690 / 2,520 | 11 | 46.2 MiB | 3.24 MB | 867 ms |
| Glessner v4, Full, one house | 58 | 2,143,282 | 34 | 272 MiB | 47.9 MB GLB | 1,445 ms |

What the table means for the town, and what it does not:

- **Maps.** Each wood substrate pair costs **10.7 MiB of GPU at 1024² and 2.7 MiB at 512²**,
  and 0.5–1.1 MB on the wire (the log face is the dearest at 1.12 MB, because its scallops
  compress worst). Five substrates are 46 MiB at Full and 12 MiB at Light. That matches the
  prep map's arithmetic, now as a reading.
- **Calls.** The proof draws each material separately anyway, so it **cannot** show the
  town's batching price. That stays T-1488's measured +1 batch per bound substrate in view.
  The single extra call here is the recessed build's own sash and glass materials.
- **Triangles: the recessed opening is dearer than priced.** The recessed opening costs **+162
  triangles** over the flat one (830 against 668, same assembly). That is the casing with its
  returns, the sill, four reveal faces, eleven boxed sash bars (110), the glass and the five
  faces of the room. The prep map guessed 40–80. At Balanced's 46,232 clear that is about
  **285 openings** before the rung is spent. Boxed bars are most of it: drawn as front faces
  only they would be 22 triangles, which puts the opening near 75 and gets back to the prep
  map's figure. So T-1210 should build **front-face bars at Balanced and flatten the recess
  at Light**, and take its own reading with `measure_detail_ceilings.mjs --price` before it
  deals the town.
- **Glessner** spends 2.1 M triangles and 272 MiB on one house. The 1835 town cannot spend
  that per roof, and nothing here proposes it.

## 5. Handoffs — what T-1210–T-1213 start from

- **T-1210 (fabric and finish by household)** takes strategy A as built in § 3, on the two
  no-course maps, with these four decisions still its own:
  1. **The wall's name.** The proof names its substrate (`wall_clapboard`) because it is free
     to. The town ships `wall` for clapboard, batten and vertical board alike. Route 1 of the
     prep map (`wall_material_name()`, a `docs/GLB-CONTRACT.md` proposal plus a rebake of the
     242 `wall` materials) is still the proposal.
  2. **Grain strength per finish.** The finish now carries a third number (1.0 bare, 0.3
     coated). Colour and roughness ride the vertex stream today; grain strength needs a
     channel too. The vertex colour's alpha is unused, and that is the cheapest candidate.
  3. **Grain axis on upright boards** (defect 4). Clapboard and logs are right as they are.
     Battens, vertical board and casings need an axis per primitive, or a material of their
     own whose axis is fixed.
  4. **The recessed sash** moves from this proof into `frame_dwelling` as a function beside
     `_opening`, with front-face bars at Balanced and a flat Light derivative (§ 4). It needs
     a rebake of every structure with an opening, so it is a parcel of its own.
- **T-1211 (plank works)** — the deck relief binds at 4.00 m with the flat axis set to the
  board direction. T-1800 already set the walk's tones, so this relief is what adds grain,
  end grain and wear on top.
- **T-1213 (signboards)** — `signboard_weathered` is generated as upright planks, so a sign
  binds it turned 90° (a uniform; see defect 2). Lettering stays with `signage.js`. The proof's
  "GROCERIES" is a trade name drawn by the review page, not a firm.
- **T-1212 (yards)** — no new finding. The sawn-board and iron rows of the prep map stand.

## 6. What this does not claim

The proof is a reconstruction of a method, not of a building: no record stands behind its
bay, pen, sash or sign, and none is implied. The two new maps are the library's own tier
(`attested/inferred` for the substrate, the surface procedural), with their notes in
`material.json`. The 30 % grain strength for paint, the scallop spacing and the check density
are readings from these captures, recorded here as the reconstructions they are. The Blender
review render (`render_structure_review.py` under fixed neutral and scene light) was not taken.
The browser's town rig and a neutral field stood in for it, and the owner's comparison is still
the acceptance.

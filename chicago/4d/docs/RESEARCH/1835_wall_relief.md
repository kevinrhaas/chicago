# The town's walls, bound as relief — T-1963

Piece 2 of T-1818: the photographic-benchmark half that T-1962's rule could not reach.
T-1962 gave the lap lines an irregular lay and bare stock a household's wear. Its critic
frames showed both were real and both were small (0.02–2.6 % of pixels moved by more than
3/255), because a flat-shaded colour has nothing in it for the eye to read at walking
distance. This parcel turns on the fabric proof's strategy A (`1835_fabric_proof.md`
§ 3) for the town's own walls. Nothing is rebaked, and no GLB, record or schema changes.

## 1. What was built

| piece | where | what it does |
|---|---|---|
| the rule | `renderers/web/js/wall-grain.js` | which walls are bound and how much grain each finish shows, read off the record (route 2 of the preparation map § 5) |
| the binding | `renderers/web/js/wall-relief.js` | the metric face-frame UV, the packed ORL (R = AO, G = roughness, B = 0.5·L/mean L) derived at load from the library's own `orm` and basecolor, the albedo and roughness patches, and 512 px maps on a coarse device |
| the batch | `renderers/web/js/buildings.js` | applies the binding before `materialKey()`, and writes a `_grain` float on a bound wall's vertices only |
| the guard | `tools/check_wall_relief.py` (a `check.sh` step + self-test) | runs `wall-grain.js` under node over every record and holds it to `materials.wall_substrate()` / `wall_finish()` and to the `wall` materials the GLBs carry |
| the contract | `docs/GLB-CONTRACT.md` § Wall substrates (PROPOSED) | the narrow use of `wall` / `log` names, always together with the record's archetype, until route 1's pinned name lands with the next frame rebake |
| the captures | `tools/wall_relief_shots.mjs` → `1835-wall-relief/` | before (`?walls=flat`) and after, both viewports, the clock held, the published mirror |

**What is bound.**
- `clapboard_board_face` goes on **250** clapboarded walls (every frame dwelling and tavern,
  and every storefront except the three dealt vertical board). **49** of them wear a coat.
- `hewn_log_face` goes on **105** laid-log walls (log dwellings, log outbuildings and the
  fort's log buildings).

**Grain strength by finish.** Whitewash, red oxide and white lead are the sheet's three
coatings, and they show **0.3** of the grain's colour. Bare stock (fresh, weathered and
mixed timber, ochre and unpainted) shows all of it. Every finish keeps all of the relief.

**Roughness by ratio.** A wall's roughness is the household's own number times the map's
G over its mean (0.866 on the board face, 0.90 on the log face). So whitewash at 0.90 and
white lead at 0.60 stay distinct inside one draw call.

**Not bound.**
- **Upright boards** (vertical board, battens, outbuilding boards), casings and sash. The
  face frame grains every upright face horizontally (defect 4).
- **Palisades and bridges**, whose logs stand up or span.
- **Chinking.** Its daub map needs the proof's resample, and it is a parcel of its own.

## 2. The captures — `1835-wall-relief/`

Each close shot arrives the way a visitor does (`spawnAtDestination`), then steps in along
the line of sight until the wall the centre ray meets is **5.0 m** off. That is walking
distance, a door's width off the step. The Sauganash is the exception: its arrival stands
11.6 m off a wall, so the step is longer there. Files are
`<viewport>-<shot>-<before|after>.jpg`.

| shot | structure | finish | grain |
|---|---|---|---|
| `close-fresh` | `recon_1835_blk_lake_market_d4_02` | fresh_timber | 1.0 |
| `close-maintained` | `recon_1835_blk_lake_market_d3_03` | whitewash | 0.3 |
| `close-whitelead` | `sauganash_hotel` | white_paint (attested) | 0.3 |
| `close-weathered` | `recon_1835_blk_lake_market_c2_01` | weathered_timber | 1.0 |
| `close-log` | `philo_carpenter_log_shop` | hewn log | 1.0 |
| `wide-lake_market` | the critic station | — | — |
| `glessner-benchmark` | `glessner_house`, 1904, from its own arrival | — | — |

The benchmark at walking distance is the fabric proof's own `desktop-glessner-close.jpg`
(5.9 m, the same rig). It is not re-shot here, because the town's Glessner arrival stands
back to frame the whole house.

**The critique, read off those frames.**

- **At walking distance the walls are wood.** At 5 m on desktop, every clapboard carries
  its own drying checks and a slow figure along the board, and they never repeat across a
  4.48 m bay. The log shop's faces carry adze marks and checks. Before this change, both
  were one flat colour between the modelled lap lines.
- **A coat reads as paint over wood, not as wood.** On the whitewashed dwelling and the
  Sauganash, the checks and raised grain come through the coat while the colour stays
  white. White lead is visibly glossier than the whitewash next door. That is the
  roughness ratio carrying each household's own number.
- **It is shade-weighted.** At 12:30 in July most street faces in this sample face north
  or stand in their own eave's shadow. In shade, the relief reads through the sky and AO
  terms only, so the grain is quieter than it would be on a wall the sun is raking.
  Nothing here is tuned to the light. The strength is the proof's.
- **By 25 m it is gone, as it should be.** In `wide-lake_market` the Sauganash's sunlit
  side is the same tone before and after. No new shimmer or tile repeat appears at that
  distance. The moiré on that wall's lap lines is the modelled geometry's, and it is in
  both frames.
- **Mobile (390×780, 512 px maps) is subtle.** At phone resolution the grain reads mostly
  as a softening of the flat colour. The checks are there at 5 m but small. This is the
  Light row's bargain: a quarter of the GPU memory.
- **Against Glessner v4 the gap is still large, and it is the expected gap.** Glessner's
  granite and brick carry a full albedo map and geometric detail on one house: 2.1 M
  triangles and 34 textures. The 1835 walls keep their colour on the vertex so a
  household's finish can move it, and they share two map pairs across 355 walls. What
  transfers is the method: metric UVs, no-course faces over modelled courses, and
  roughness that means the material. Glessner's per-building budget does not transfer.
  The remaining visible distance is in the flat openings (the recessed sash is still the
  proof's alone), the unbound trim and casings, and lighting that leaves most street
  faces in shade at midday.

## 3. Frame costs, town-wide

The published mirror and SwiftShader. `renderer.info` after two settled frames with the
clock held: the colour pass plus the shadow pass, in draw calls and triangles.

| stand | 1280×800 before → after | 390×780 before → after |
|---|---|---|
| `wide-lake_market` | 189 → **193** calls · 1,387,099 tris (unchanged) | 83 → **87** · 659,072 (unchanged) |
| `wide-south_water` | 173 → **177** · 1,316,269 (unchanged) | 80 → **84** · 744,322 (unchanged) |
| `close-fresh` | 150 → 154 · 1,240,287 | 69 → 73 · 682,380 |
| `close-maintained` | 144 → 148 · 1,213,453 | 69 → 73 · 667,008 |
| `close-whitelead` | 139 → 143 · 1,169,306 | 65 → 69 · 655,921 |
| `close-weathered` | 148 → 152 · 1,289,626 | 79 → 83 · 716,244 |
| `close-log` | 139 → 143 · 1,187,718 | 65 → 69 · 656,167 |

- **Calls: +4 at every stand.** That is the two new batches (clapboard, log), each once in
  the colour pass and once in the shadow pass, exactly as T-1488's two roof batches paid.
  Building batches go from 3 to 5, and `smoke_renderer.mjs`'s `STRUCTURE_BATCHES` moves
  with the measurement. The worst stand here is 193 against the 215 budget.
- **Triangles: unchanged to the triangle.** No geometry moved.
- **Maps:**

  | | per substrate pair | wire (normal + orm + basecolor, two substrates) | GPU (mip-chained) |
  |---|---|---|---|
  | 1024 px | 10.7 MiB | 2.07 MB, of which the board face's 0.69 MB was already loaded by the street timber (T-1815), so 1.38 MB is new | 21 MiB |
  | 512 px (coarse device) | 2.7 MiB | the same wire | 5.3 MiB |

  `renderer.info.memory.textures` read 32 → 40 at 390×780 for these four maps. The packing
  is canvas work at load, about 0.1 s a substrate, done once a page.
- **Programs: unchanged (27).** The two substrates compile one shared source and differ
  only in uniforms (the proof's defect 2).

## 4. What is left for the parent and its siblings

- **The recessed sash** (`1835_fabric_proof.md` § 5 item 4). This is now the most visible
  gap at walking distance, and it needs a rebake of every structure with an opening.
- **Upright boards.** These need a grain axis per primitive, or a material of their own
  with a fixed axis.
- **Route 1's pinned name.** `wall_clapboard` / `wall_vertical` lands with the next
  frame-wide rebake. `check_wall_relief.py` is then the comparison that proves the switch.
- **Chinking and trim** take the same binding once their axes are known.

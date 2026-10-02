# Signboards to the photographic benchmark — the review (T-1836)

Piece 3 of 3 of T-1213. The boards' wording, mounting and colourways are T-1834/T-1835's and
are untouched; this piece changes what the boards are MADE of. Liberty **L345**.

## What was wrong (the "before" frames)

Every board in the town was a flat colour panel with a crisp computer letter on it, and every
arm, strap, post, cap and hood sampled ONE texel of the atlas — so a sign's carpentry was a
single uniform grey from any distance. No grain, no joint, no wear, no relief, one roughness
(0.85) for paint and wood alike. At the close stands it read as a UI label floating in a timber
town. That is the opposite of the owner's benchmark.

## What changed

`renderers/web/js/signage.js`, still ONE mesh and ONE material:

| | before | after |
|---|---|---|
| board face | flat ground colour + letters | the library's `signboard_weathered` grain under the paint (soft-light, 0.55), joints every ~0.25 m with a lit lip, chipped paint at the edges, flakes over the face and the lettering, grime over the lowest quarter |
| board edge | the ground colour | paint half worn to wood |
| carpentry | one texel of `TIMBER_HEX` | `heavy_timber_weathered` grain, metric (200 px/m), run along each face's longer side, a seeded offset per member |
| relief | none | a normal atlas (half size) on the same layout: board grain, paint filling it on the face, worn patches and joints cut back in; timber grain on the carpentry |
| roughness | 0.85 everywhere | a roughness atlas (quarter size): paint 0.62, worn patches 0.86, timber 0.88 |

Both library sheets are generated as upright planks, so both are turned 90° in the canvas, and
the normal map's vectors are turned with them (R ← G, G ← 255 − R; the GL convention). Only the
basecolor's GRAIN is used, as a luminance modulation about its own mean. The board keeps its
style's colour and the carpentry keeps the archetype's tone.

`tools/publish.sh` carries three files of each sheet (basecolor, normal_gl, material.json) to
`data/textures/chicago_1835_pbr/`. If they fail to load, the layer records a problem and paints
the boards flat, as before.

## The captures

`node tools/signboard_shots.mjs <root> <entry> <out>` stands relative to a sign's own anchor and
bearing, so the before and after frames have the same pose by construction: `close` (3.6 m out,
square on, pitch 14°), `oblique` (38° along the street) and `context` (13 m out). Animation is
held and the HUD hidden. The three subjects:

- a **store board**: Philo Carpenter's wall board with the Golden Mortar (`black_on_timber`, a
  bare board)
- a **bracket sign**: P. F. W. Peck's (dark ground, double rule)
- a **tavern's board**: the Tremont's post board in the street (`cream_on_red`)

The before frames are from `dev@a55277b3` in the dev tree. The after frames are from the
published mirror, which is the one that matters. In `signboard-benchmark/`, each
`<viewport>-<sign>-before-after-glessner.jpg` is before | after | the Glessner v4 close from
`1835-fabric-proof/`, and `*-context-before-after.jpg` is the context stand.
`before-report.json` and `after-report.json` hold the renderer stats at every stand.

## Written critique

**Against Glessner v4.** Glessner's close frame earns its look from relief and restrained albedo
variation: the granite's courses catch the light, the door's panels are recessed, and nothing is
a flat colour. The boards now share that method — relief from a library normal map, albedo
modulation kept under the paint, roughness that differs by material — and that is what moved.
Reused: the library-map-under-runtime-colour method and the metric texel rate. Adapted: the
fabric proof's 90° turn and its finding that paint must let only part of the grain through.
Rejected: transmission or any second pass (one draw call is the layer's contract), and
Glessner's 1904 finishes, which are not 1835 evidence.

**Better than before:**

- **Physical scale.** The grain is metric (the library's 2 m tile at the board's own px/m), so a
  1.1 m board shows about the right number of grain lines. The joints sit at plank width and
  read as a board made of boards, which is the first thing the Tremont frame shows.
- **Joinery and edges.** The board's arris shows as worn paint, not a clean colour. The joints
  have a dark seam and a lit lower lip in colour, and a groove in relief.
- **Surface response.** Paint is visibly glossier than the timber holding it. Under the low sun
  the grain shows on the face at the oblique stand.
- **Variation.** Wear is seeded per board: the Tremont's chips run along its bottom edge, and
  Peck's black ground shows fine flakes and a broken border rule. No two boards wear alike.
- **Carpentry.** The Tremont's post and arm show grain running along their length. Before,
  they were one grey.

**Still short of the benchmark, stated rather than hidden:**

- **The lettering is still a browser font.** Wear now breaks it, but the letterforms are
  Georgia/Courier/Helvetica. The next real step is hand-drawn sign-writer letters: an outline
  set drawn into the atlas, with a slight brush irregularity per stroke. That is a parcel of its
  own (L158 already records the letterform as invented).
- **No depth to the letters or the rule.** Paint has no relief in the normal atlas. Gilt and
  carved letters, which a better board had, would want it.
- **Thin members lose the grain past ~6 m.** A 45 mm arm at the context stand is a few pixels
  wide. This is correct mip behaviour, not a defect, but the grain only pays at the close and
  oblique stands.
- **Shimmer was not assessed.** These are stills. Anisotropy is 4 on all three atlases, as
  before for the colour one.
- **The flakes on a black ground are the boldest wear in the town.** Bounded to read as use
  rather than dereliction, but Peck's is the one to look at if the owner finds it too much: the
  flake density is one constant (`wearOf`).

## Town-wide frame cost

Measured at the six dev-tree stands (desktop, same tree with and without the change) and at all
nine published stands at both viewports:

- **Draw calls: unchanged at every stand** (e.g. 156 → 156, 182 → 182). The layer is still one
  mesh and one material.
- **Triangles: unchanged at every stand.** No vertex was added; only the uvs moved.
- **Programs: 44 → 44.** The material's program cache key is unchanged, and the normal and
  roughness maps compile into the same variant at every stand.
- **Textures: 25 → 27**, the relief and roughness atlases. GPU memory added: the relief atlas is
  2048 × 1536 RGBA (12.6 MB, ~16.8 MB with mips) and the roughness atlas 1024 × 768 (3.1 MB,
  ~4.2 MB with mips) — **about 21 MB** beside the colour atlas's ~67 MB. No detail tier is
  affected differently: the signage layer is the same at `full`, `balanced` and `light`, and
  `light`'s floor is in draw calls and triangles, which did not move.
- **Load:** four 1024² PNGs (≈0.9 MB over the wire) and a canvas pass over the atlas once at
  load. No per-frame work was added except the two extra texture samples on sign pixels.

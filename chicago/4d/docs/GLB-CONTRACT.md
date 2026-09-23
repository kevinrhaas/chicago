# The asset contract

**This is the interface between the generators and every renderer.** Track A (Blender) writes
it; Track B (three.js) and any future engine reads it. Neither side may change it unilaterally —
a change here is a change to the project's portability promise.

The rule from `AGENTS.md`: renderers consume glTF + JSON sidecars. They never reach into
`generators/` or reimplement the data model.

## Geometry

| | |
|---|---|
| container | `.glb` (binary glTF 2.0) |
| axes | **Y-up, right-handed** (glTF native) |
| units | **metres** |
| origin | each structure's mesh is authored about **its own local origin**, at ground level (y = 0 at the base of the walls) |
| placement | the renderer positions the node from the **sidecar**, not from a baked-in world transform |
| winding / normals | counter-clockwise, outward |

**Pinned conventions** (all previously ambiguous; a renderer and a generator picked
differently and placed the same building 6 m apart before these were written down):

| thing | convention |
|---|---|
| mesh local origin, in plan | the **footprint polygon's own coordinate origin** — the point the record's `position` refers to, i.e. polygon coordinate `(0, 0)`. NOT the centroid and NOT the bbox corner (they coincide only by accident). |
| mesh local origin, vertically | `y = 0` at the base of the walls |
| …for a structure over water | `y = 0` at the **design water surface**, not the ground — a bridge's one documented dimension is its clearance above the water, and its piers run to a bed we do not model. The renderer must place such a structure against the water plane rather than sampling the terrain. Declared per archetype; `bridge_timber` is the first. **Wired 2026-08-10** with the first bridge record: the archetype declares `VERTICAL_ANCHOR` in its parameter module, `tools/compile_scene.py` copies it into `placement.vertical_anchor`, and the renderer places `water` at a literal `y = 0` — that plane is zero by the definition of the vertical datum, so no lookup is involved. Anything that declares nothing gets `terrain`, unchanged. |
| …and what a visitor may STAND on | `placement.walk_surface_m`, metres above that same `y = 0`, or `null` where there is no such surface — which is every structure but the four bridges. **Additive, wired 2026-08-17** (T-0001), by the same route and for the same reason as `vertical_anchor` in the row above: the archetype's parameter module already resolves `deck_height_m`, `tools/compile_scene.py` reads it off the resolved params without Blender, and the renderer's walker uses it as the floor. The deck a boot is on and the deck the mesh draws are therefore ONE number. Nothing about the GLB itself changes, and no generator is asked for anything new. The alternative — the renderer finding the deck primitive by its material name — was rejected: material names are not pinned anywhere in this document, so a renderer keyed on one would be reading a convention nobody promised to keep, and the drawbridge's gallows frames sit five metres above its deck, so the bounding box is not the answer either. |
| footprint axes → 3D | polygon `u` → **+X**, polygon `v` → **−Z** (so +v is north, matching ENU) |
| `rotation_deg` | facade bearing, **degrees clockwise from grid north**, 0 = facing north. In three.js: `rotation.y = -deg * PI/180`. |
| ENU → three.js | `local_e` → **+X**, `local_n` → **−Z**, up → **+Y** |

Authoring in metres about a local origin is what lets a structure be re-placed when its position
firms up — which will happen, because most positions currently carry `symbolic_location` and
±20 m of georeferencing uncertainty.

## Node naming and identity

One node per structure **phase**:

```
node.name    = "<structure_id>__<phase_id>"     e.g. "sauganash_hotel__frame_1831"
node.extras  = { "structure_id": "...", "phase_id": "..." }
```

`extras` survives round-trips through Blender, glTF-Transform, Godot and glTFast, and is
diffable in git. The renderer resolves picks through `extras.structure_id`, never by parsing the
name.

**Multi-material split — matters for picking.** glTF primitives cannot span materials, so a
structure with several materials exports as ONE node holding ONE mesh with several PRIMITIVES.
**three.js then represents that as a Group with one child Mesh per primitive**
(`…__frame_1831_1`, `…_2`, …) — the split is created by the loader, not present in the file.
Corrected 2026-08-09 after the archetype track inspected the GLB directly and found no child
nodes; the original wording described the loader's output as though it were the file's
structure, which sent someone looking for children that were never there. Consequences:

**Terrain layers are not structures** (added 2026-08-10 by the terrain parcel; additive, nothing
above changes). Terrain has no `structure_id` and no phases — it belongs to a *terrain epoch* —
so it uses a parallel naming rule, one node per layer per epoch:

```
node.name    = "<layer>__<epoch_id>"            e.g. "terrain__e1834_harbor_cut"
node.extras  = { "terrain_epoch": "...", "layer": "ground" | "water" }
```

One GLB per layer, one material per GLB, `_CONFIDENCE` per vertex exactly as above. The renderer
finds them through the epoch's `heightfield.json`, which carries a `glb` block of paths relative
to the asset base — terrain is not in the sidecar index, because the sidecar index is keyed by
`structure_id` and terrain has none.

The **ground mesh and `heightfield.bin` are generated from the same grid**, so the surface a
visitor sees and the surface the walker stands on are the same surface. That is a property worth
protecting rather than assuming: `generators/terrain_gen.py` ray-casts the decimated mesh
against the field after decimation and refuses to export if they drift past 30 mm.

**Multi-material split — verified 2026-08-09, matters for picking.** A structure with several
materials exports as ONE node with several child meshes (`…__frame_1831_1`, `…_2`, …). glTF
primitives cannot span materials, so this is unavoidable. Consequences:

- `extras` lands on the **parent node** (three.js: `object.userData`). The child meshes carry
  **empty** `userData`. A raycast hits a *child*, so **the renderer must walk up the ancestors
  to find `structure_id`** — reading it off the hit object returns nothing.
- Each child is its own draw call until batched. A four-material building is four calls; the
  ≤50–80 budget assumes the buildings get merged into a `BatchedMesh` before that matters.
- `_CONFIDENCE` is present on **every** child, verified in three.js as
  `geometry.attributes._confidence` (float, lowercased by GLTFLoader as expected).

**`BatchedMesh` gotcha, found by the renderer track.** `BatchedMesh` snapshots its
attribute set from the **first** geometry added, and only validates that later geometries
*have* the batch's attributes — never the reverse. If the first geometry into a batch lacks
`_CONFIDENCE`, every later geometry's is **silently dropped** and the whole batch renders as
documented. Normalise every geometry to the same attribute set before adding.

## The confidence channel — `_CONFIDENCE`

**The single most important part of this contract.** The generator knows which geometry derives
from which attested attribute; the renderer does not and must not guess.

Every vertex carries a **custom glTF attribute `_CONFIDENCE`** (`SCALAR`, float) encoding the
confidence of the attribute that produced that geometry:

| value | meaning |
|---|---|
| `0.0` | `documented` |
| `0.5` | `inferred` |
| `1.0` | `conjectural` |

**Why not `COLOR_0`** (revised 2026-08-09 after a Blender spike): glTF defines `COLOR_0` as a
**multiplier on base colour**, so a documented value of 0.0 would render the building black in
any spec-compliant renderer, and 0.5 would half-darken every inferred surface. Blender's
exporter also silently drops `COLOR_0` unless it is wired into the material node tree — it
emits `WARNING: The active Vertex Color will not be exported, as it is not used in the node
tree of the material`, and you get a GLB with no confidence data and no error. A custom
underscore attribute avoids both problems: it is spec-sanctioned, it is never touched by
material evaluation, and it says what it means.

**Blender side:** create a `FLOAT` attribute on the `POINT` domain named `_CONFIDENCE` and
export with `export_attributes=True`. No material wiring needed.

**three.js side:** `GLTFLoader` lowercases unknown attributes, so it arrives as
`geometry.attributes._confidence`. Declare it in the shader patch yourself
(`attribute float _confidence;` / `in float _confidence;`) — three will not wire it for you,
and that is the point: it never tints anything by accident.

Worked example, the Sauganash `frame_1831` phase:

| geometry | driven by | value |
|---|---|---|
| wall massing, storey height | `stories` documented, `wall_height_m` conjectural → **worst wins** | `1.0` |
| clapboard cladding, white paint | `paint` documented | `0.0` |
| shutters | `shutters` documented | `0.0` |
| roof | `roof_type` conjectural | `1.0` |
| attached log wing | `log_wing` inferred | `0.5` |
| footprint outline | `footprint` conjectural | `1.0` |

**Rule when several attributes drive one piece of geometry: the least confident wins.** A wall
whose height is a guess is a guessed wall, even if we know it was white.

`COLOR_0` stays free for actual colour, and is currently unused.

## Materials

- One shared material per batch. A building with five materials is **five batches**, not one —
  glTF primitives cannot span materials, so "all buildings in a single `BatchedMesh`" is not
  achievable while material sets differ. **Corrected 2026-08-16 by R-W5a and K36(b):** the
  renderer no longer batches per material *set*. `materialKey()` batches on the fields a
  renderer actually distinguishes and leaves `color` out of them, so a building's parts join
  the town's existing batches by roughness and a new paint colour costs nothing. The town is
  **16 batches**, on the site as well as in the tree.
- ~~Run `gltf-transform palette` so flat per-building colours become a shared atlas.~~
  **REFUSED 2026-08-16 with numbers — K36(b).** The palette pass fires on any file with five
  or more materials, and it had been firing on 38 shipped assets since the step was written.
  It merges materials *inside one file* and, because `materialKey()` includes the texture and
  a GLTFLoader mints a fresh uuid per loaded map, it makes those files **unbatchable against
  everything else**: 38 assets shipped as 40 single-building batches, the published town drew
  **56** batches against the tree's 16, and **four of the eight scene anchors were over the
  80-call budget** (worst 102). With the pass off: 56 → 16 batches, worst anchor 70, no
  anchor over budget. It is off in `tools/web_derivatives.sh`, and `BAKE_PALETTE=1` restores
  it for anyone re-measuring. A shared atlas is still the right idea — it is **R-W2b's** job,
  authored across the town rather than generated per file.
- **Bake ambient occlusion into the texture**, not into vertex colours. It reaches the file
  as a glTF `occlusionTexture`, sampled from the R channel as **`byte / 255` with no transfer
  decode** — occlusion is non-colour data, and a value of 0 means FULLY occluded. So the
  image must be tagged `Non-Color` **before** the bake, never after: setting
  `colorspace_settings.name` on a generated, unpacked image frees its buffer, which
  regenerates black and clears the `is_dirty` flag Blender's own exporter tests before it
  will carry unsaved pixels. Doing it in the wrong order shipped a uniformly black occlusion
  texture with `baked_ao: true` beside it (T-0158). `generators/ao_export.py --gate` reads
  the exported bytes on every commit and refuses a texture that carries no occlusion or a
  manifest that disagrees with the file; `generators/build.py` runs the same assertion the
  moment each GLB is written, so `baked_ao: true` cannot be recorded for a bake that did not
  arrive. **No committed master carries one today** — `--ao` is opt-in and nothing passes it
  (T-0015), and whether it *should* be is open: every figure that said the bake is too dark was
  read off an sRGB-tagged buffer AND over an atlas that is 68.9 % empty UV space, so it is void
  (T-0158). The corrected reading on `sauganash_hotel` is mean **0.5358** over the 81,458 texels
  the unwrap writes, 58.7 % of them below half. T-0227 settles it from a rendered frame.
- No emissive, no transparency in the base asset. The confidence view's translucency is a
  *renderer* effect (screen-door dither in the opaque pass), never baked geometry.

## Compression

| artifact | form | where |
|---|---|---|
| archival master | uncompressed `.glb` | `assets/gltf/` (committed, not published) |
| web derivative | `EXT_meshopt_compression`, **or the master passed through where compressing it is bigger** | `assets/web/` → published |

The master is the source of truth; derivatives regenerate from it. Meshopt over Draco: it
decodes far faster with no per-file WASM cold start, which matters more than bytes for ~150
small meshes.

KTX2 is **not** in that row and never has been. `--texture-compress ktx2` is off in
`tools/web_derivatives.sh` because the vendored `GLTFLoader` has no `setKTX2Loader()` and no
Basis transcoder, so a KTX2 asset throws in the loader and leaves the scene; see the script.

**The passthrough is a measured rule, not an exception — K37, 2026-08-16.** `meshopt` writes a
compression header, a buffer-view table and an index buffer, and below a few hundred triangles
those cost more than they save. Running the step over the 90 flagged placeholders takes them
**520,700 → 628,028 bytes, +20.6 %**, 88 of the 90 growing. Nothing about an asset's *kind*
predicts the sign — three assets that had always been compressed here were shipping larger than
their masters, and two of the ninety placeholders compress 9.3 % smaller — so the step measures
each file and keeps the smaller one, and `tools/measure_web_derivatives.py` asserts that no
derivative is bigger than its master. A passthrough carries **exact float positions** rather
than a quantised lattice, so it satisfies every other assertion in that gate by construction;
93 of 334 assets ship this way, 11.3 % of the payload. The two epoch meshes are excluded by
name while R-W6(b) holds them.

### Quantised geometry: float before you transform

`gltf-transform optimize --compress meshopt` also applies `KHR_mesh_quantization`. Under it a
POSITION arrives as a **normalized `Int16Array`** — the stored integer divided by 32767, so the
attribute can only represent values in `[-1, 1]` — and the real metres come from a
dequantisation **scale and translation carried on the node** (6.25 on the Sauganash).

Two consequences, and this project has shipped a broken town for each of them:

1. **The node transform is encoding, not placement.** Discarding it, or taking geometry
   relative to the node that carries it, cancels the dequantisation and renders everything at a
   fraction of its size.
2. **Never `applyMatrix4` into a normalized integer attribute.** `BufferAttribute.applyMatrix4`
   reads denormalised floats, transforms them, and writes the result *back into the same
   normalized `Int16Array`*, where everything past one metre is clamped to 1. A twelve-metre
   tavern becomes a two-metre box — and because the clamp is per-axis and a building is not
   centred on its origin, its parts are pulled apart on the way. Convert to float **first**
   (`toFloatAttribute` / `dequantizeGeometry` in `renderers/web/js/terrain.js`), then transform.

**The ground's POSITION rung divides the terrain grid exactly — T-0152, 2026-08-23.** Under
`KHR_mesh_quantization` the node scale is uniform and taken from the mesh's widest axis, so the
ground's rung is set by the 2 020 m box plus its two skirt margins. `generators/terrain_gen.py`
therefore DERIVES the skirt margin — the smallest apron of at least the haze distance for which the
rung is an exact submultiple of the 2.5 m grid, currently the cell over 32 (78.125 mm, apron
1 549.921875 m) — so every ground vertex already stands on a rung and quantising rounds it to
itself. This is the generator's side of the bargain and it **strengthens** the existing terms: the
mesh, the node, the primitive, the attributes and the extension are all unchanged, and a renderer
that knew nothing about it reads exactly what it read before. What it buys is on the RENDERER's
side. `conformGroundToField()` repairs Y by re-reading the field at a vertex's shipped `(E, N)`,
which is a repair only if the shipped `(E, N)` is the authored one; it was out by up to 51.9 mm in
plan, which cost 77 mm of drawn-surface error on 60-90 % bank faces against the 22 mm the road
ribbon is lifted by. It is now 0.0 mm, asserted on the shipped bytes by
`tools/measure_terrain_horizontal.mjs --gate` and on the generator's side by a refusal to export.
A change to the terrain box, the grid spacing or the quantiser's own model breaks commensurability
and fails those gates rather than quietly returning the artefact.

**Only the published tree can catch either of these.** A sidecar's `gltf/<name>.glb` resolves
against `assets/` in the source tree — the *uncompressed masters* — and against `data/` on the
site, which `tools/publish.sh` fills from `assets/web/`. So a renderer bug that only exists in
the quantised path is invisible to anything run against the source tree, which is exactly how
both regressions passed a fully green gate. `tools/smoke_renderer.mjs --published` serves the
mirror and is the run that sees the bytes a visitor downloads; `tools/bake.sh` runs it.

## The sidecar

One JSON per structure per scene, compiled by `tools/compile_scene.py`, published alongside the
GLB. The renderer reads placement, provenance and footprint from here.

```jsonc
{
  "id": "sauganash_hotel",
  "phase": "frame_1831",
  "name": "Sauganash Hotel",
  "aka": ["Eagle Exchange Tavern"],
  "asset": "gltf/sauganash_hotel__frame_1831.glb",
  "documented_range": {
    "from": "1831-01-01", "to": "1851-03-04", "confidence": "documented",
    "sources": ["kinzie_waubun_1856"], "note": "..."
  },
  "change_note": "Two-story frame block built onto the log core ...",
  "placement": {
    "local_e": 0.0, "local_n": 0.0, "rotation_deg": 0.0,
    "position_confidence": "documented",
    "position_sources": ["kinzie_waubun_1856"],
    "position_note": "...",
    "symbolic_location": "SE corner of Lake St and Market St",
    "uncertainty_m": 20
  },
  "attributes": {
    "stories":  { "value": 2, "confidence": "documented", "sources": ["kinzie_waubun_1856"] },
    "gallery":  { "value": false, "confidence": "inferred", "note": "..." }
  },
  "citations": [
    { "source_id": "kinzie_waubun_1856", "citation": "...", "url": "...", "archived_url": "...",
      "tier": 2, "tier_label": "near-primary recollection",
      "transcribes": [ { "work": "...", "date": "1883-07-22" } ],
      "what_it_supplies": ["..."], "what_it_does_not_supply": ["..."] }
  ],
  "research_doc": "docs/RESEARCH/sauganash_hotel.md"   // "" where none is written
}
```

The five keys after `tier` are additive and four of them are present only when the source
record carries them. `tier_label` is the ladder in words; `transcribes` (or, for a page read
and found to reprint nothing, `carries_no_document`) is what the rung is a judgement ABOUT,
which matters because on ten of these records the document is not the page; and the two
`what_it_…_supply` lists are the source's own stated limits. Which fields of a source record
cross this boundary is not a matter of taste — `compile_scene.SOURCE_FIELD_SURFACE` partitions
the schema and `validate.check_source_surface` fails on a property in neither half.

`placement.local_e` / `local_n` are **metres east and north of the scene datum origin**
(`data/datum.json`). While a structure's coordinates are still null, the compiler emits the
placement it does know and flags `"placement_provisional": true` — the renderer shows such
buildings normally but the confidence view treats position as conjectural.

`uncertainty_m` carries the georeferencing reality forward: nothing traced from the 1834 sheets
is better than about ±20 m.

`footprint` is `{ "polygon": [[u,v],…], "confidence": "…" }` — the polygon alone would lose the
footprint's confidence, which is exactly what the confidence view exists to show.

`research_doc` is **the dossier that covers this record, or `""` where none has been written**
— resolved by the compiler against the repository rather than asserted by convention. The path
used to be `docs/RESEARCH/<id>.md` for anything with no reconstruction block, which is right
about 302 of 332 records and wrong about 30, and the card rendered the guess as a link either
way. Emitting the empty string rather than dropping the key keeps the sidecar one shape
everywhere, the rule `residents` already follows. **The renderer composes an absolute URL from
it** (`popup.js` `DOSSIER_BASE`), because `docs/` is deliberately not published: a path relative
to the walkthrough resolves in the source tree and 404s everywhere a visitor stands. Both halves
are gated by `tools/check_dossier_links.py` (ROADMAP K26).

`documented_range`, `change_note` and the `position_*` fields are the phase's claim about
itself, carried in the same shape as an attribute (value/confidence/sources/note) so the card
can render them with the attribute renderer. Additive, 2026-08-10, and added because the
renderer had been reading `documented_range` off a sidecar that never contained it: the scene
date falls inside the span by construction, so what a visitor needs is not the fact but its
strength and its reasoning — for a building nobody followed past 1834, the end of the range is
an argument rather than a source.

**This list is now checked from both sides, and the check is what makes it a contract rather
than a description.** `validate.py`'s `check_sidecar_contract` reads what the compiler emits off
the committed sidecars — which `compile_scene.py --check` proves are exactly what the dataset
compiles to — and scans what the renderer reads out of the renderer's own modules. A field read
on one side and absent from the other is a gate failure. It was switched on 2026-08-10 and found
a second live instance of the fault that prompted the `documented_range` fix above: the
provenance card had been asking the sidecar `asset_is_placeholder`, which the compiler has never
written and, reading only `data/`, could not write. Whether a mesh is a stand-in is a fact the
GLB states about itself, so it now travels from the loader that opens the file to the card
(`record.assetIsPlaceholder`) rather than through a sidecar field.

The scan follows `record.sidecar` and the names bound directly to it; a value handed to a
function is read through that function's parameter and is out of its reach. It reports the
reverse direction — fields compiled and never read — as a note rather than an error, because at
the top level that limit does not bite and an unread field is dead weight rather than a false
claim.

**Discovery.** A static host cannot be globbed, so each scene publishes
`sidecars/<scene>/index.json` listing `{id, name, sidecar, asset}` plus `excluded_by_date`.
The renderer reads the index, never a directory listing.

**Paths.** `asset` and `sidecar` are relative to the published `data/` root
(`site/chicago/4d/data/`). In the source tree the same files sit at `assets/web/` and
`data/sidecars/`, so a dev server needs a base override — the renderer accepts `?assets=`.

## What the renderer must implement

1. **Confidence view** — a toggle reading `_CONFIDENCE` through one shared material patch:
   documented renders normally, inferred tints, conjectural renders as dithered translucent
   massing. Centralised so it cannot be forgotten per-building.
2. **Pick → provenance** — raycast to a batch id, resolve `extras.structure_id`, show the
   sidecar's attributes and citations. The visual claim and the citable claim come from the same
   record and cannot drift apart.
3. **Placement from the sidecar**, so re-georeferencing a building never requires a rebake.

## Placeholder assets during development

Track B does not wait for Track A. Until real bakes land, the renderer may load a placeholder
GLB that satisfies this contract exactly — correct node name, `extras`, and a `_CONFIDENCE`
attribute exercising all three confidence levels. `generators/placeholder.py` emits one. A placeholder
that does not satisfy the contract is worse than none, because it lets the renderer develop
against a fiction.

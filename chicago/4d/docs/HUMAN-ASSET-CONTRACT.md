# The portable human contract

**T-1786, the first ticket of the owner's portable-humans programme** (T-1786 to T-1792; owner,
2026-09-30: *build the human library and browser rendering path*; Mark Beaubien, T-1791, is the
first historical example). This page fixes every naming, skeleton, coordinate, identity and
portability decision the later tickets need, so that none of them has to make one.

Three files, one contract:

| file | what it is |
|---|---|
| this page | the contract in prose; it wins on any difference of intent |
| `data/humans/contract.json` | the machine-readable half: the skeleton, sockets, material slots, morphs, clip grammar, LODs, provenance fields, delivery limits |
| `data/humans/human_instance.schema.json` | the instance record: one person, placed in one scene |

`tools/human_contract.py` holds them to each other and holds every asset and instance to them.
`check.sh` runs `--check` and `--self-test`; an exporter (T-1787) calls `--glb FILE…`.

## What this does NOT change: L1 stands

**No human figure is drawn, for anyone, in any scene** (AGENTS.md § Standing constraint;
`docs/LIBERTIES.md` L1). This contract builds the road; it does not lift the gate.
`contract.json § l1.in_force` is `true`, and while it is, the gate refuses any instance record
that asks for `display: shown`. Lifting it is the owner's act, made in AGENTS.md and then
here. Even after it lifts:

- **Review travels with the person.** A person whose record carries `review_required` or
  `touches_removal` has an instance that carries `review_required: true`. The gate refuses an
  instance that drops it, and refuses `shown` for such a person until a review is recorded.
  This contract defines no review record yet, so for now it refuses `shown` for them outright.
- **No invented dialogue.** An instance may open the person's own resident card and nothing
  else (`interaction.opens`). Conversation is not defined here.
- **The August 1835 gathering is not staged.** Nothing here places a crowd. Each instance is
  one person who already has a record.

## 1. One master, three outputs

| | what | authority |
|---|---|---|
| **master** | a Blender `.blend` file, plus its source textures and licence notes beside it | **canonical**: everything else is exported from it |
| browser | glTF 2.0 binary (`.glb`), one file per LOD | derived; rebuilt by command, never hand-edited |
| Unreal | FBX or glTF exported from the **same** master | derived; **never authoritative** |

MetaHuman, Control Rig, Unreal materials and groom hair are not the canonical person. No
ticket in this programme may need a MetaHuman asset to finish. Unreal gets a clean handoff
(§ 9). It is never where a person is defined.

## 2. Frame

The structure contract (`docs/GLB-CONTRACT.md`) uses the same frame, plus one human-specific rule.

| | |
|---|---|
| units | **metres**. Size lives in vertex positions. Every node from the scene root to the last bone has scale 1 |
| axes | **Y-up, right-handed** (glTF native) |
| front | the figure faces **+Z** (glTF's own convention), so its left hand is at +X |
| origin | **on the ground between the feet**: y = 0 at the soles in the rest pose, and the `root` bone at the origin |
| rest pose | **T-pose**: legs straight, hip-width apart; arms horizontal; palms down; thumbs forward; head level |
| rest height | 0.45–2.3 m. Outside that range is treated as a unit error; the same adult authored in centimetres reads 175 |

**Placing one** (instance `placement`): `local_e`/`local_n` are metres in the walker's ENU frame,
the same numbers `walker.teleport` takes. `heading_deg` is clockwise from grid north. Because
the figure faces +Z, three.js sets **`rotation.y = π − heading_deg·π/180`**. Check: heading 0
faces −Z, which is north; heading 90 faces +X, which is east. This differs from a structure's
`rotation.y = −deg·π/180` because a structure's facade convention differs from glTF's front.
`anchor: terrain` stands the feet on the scene heightfield. `anchor: walk_surface` stands them
on a structure's `placement.walk_surface_m`, such as a bridge deck, and names that structure.

## 3. The skeleton: `c4d_humanoid_v1`

**One skeleton serves every human**, ordinary residents and named people alike, so one
animation library drives all of them. It has 56 bones. All are required, in this parentage
(`contract.json § skeleton.bones` is the list):

```
root
└ pelvis
  ├ spine_01 ─ spine_02 ─ spine_03
  │   ├ neck_01 ─ head ─ { jaw, eye_l, eye_r }
  │   ├ clavicle_l ─ upperarm_l ─ lowerarm_l ─ hand_l ─ { thumb, index, middle, ring, pinky }_{01,02,03}_l
  │   └ clavicle_r ─ … the mirror, _r
  ├ thigh_l ─ calf_l ─ foot_l ─ ball_l
  └ thigh_r ─ calf_r ─ foot_r ─ ball_r
```

- **Names follow the common retargeting convention**: lower case, `_l`/`_r`, numbered chains.
  An engine's retargeter can map them without a hand-written table. The convention is borrowed;
  the authority is `contract.json`.
- **Extension bones** must start with `ext_`, for example a coat tail, a queue of hair or a
  hat brim. They may hang from any contract bone. No contract bone may hang under one, and no
  shared clip animates one. An engine that drops them still has the whole skeleton.
- **At most four influences per vertex**, normalised. A light LOD may give the finger bones
  zero weight, but it never removes them, so every LOD plays every clip.
- The glTF carries the skeleton as **one skin** whose joints are these nodes. Blender's
  armature object may sit above `root` as a plain node with scale 1.

## 4. Sockets

Props attach to empty nodes named `socket_<name>`, each a child of the bone it rides on, with +Z
pointing out of the palm or away from the body. Required: `socket_hand_l`, `socket_hand_r`,
`socket_head`. Optional: `socket_back`, `socket_hip_l`, `socket_hip_r`.

## 5. Materials

A glTF material is named `<slot>` or `<slot>__<variant>`, for example
`garment_upper__frock_coat_brown`. The variant is what an instance's `appearance.variants`
selects.

- **Required on every LOD**: `skin`, `eyes`, `garment_upper`, `garment_lower`, `footwear`
- **Optional**: `hair`, `headwear`, `garment_outer`, `teeth_mouth`, `accessory`

**UVs** are one non-overlapping 0–1 set per material, with metric texel density inside each
garment so cloth weave reads at the same scale on every figure. Exact densities are T-1787's
to measure, not this page's to guess.

## 6. The face: morph targets

Shape keys use **ARKit blendshape names**. That is the widest engine-neutral face vocabulary,
and the one a later Unreal face rig reads. Nothing here depends on Apple or MetaHuman. The
Blender exporter writes the names to `mesh.extras.targetNames`.

- **Required on lod0 and lod1**: `eyeBlinkLeft`, `eyeBlinkRight`, `jawOpen`.
- The rest of the 52 are optional. Any other morph name must start with `ext_`.
- lod2 and lod3 may carry no face at all. A renderer degrades by holding the face still, as
  T-1788 requires.

## 7. Animation clips

- Names are lower snake case, `<verb>` or `<verb>_<variant>` (`idle`, `walk`, `gesture_point`,
  `work_saw`).
- The verb comes from `idle walk talk gesture work sit turn`. A new verb is a contract change.
- Names are unique within a file.
- Clips are **in place**: no root motion. A walk states its ground speed as `speed_m_s` in the
  clip's extras, and the actor moves the root.
- A clip animates contract bones and morph weights only.
- **An actor needs `idle` and `walk`.** A clip can live in the body's own file or in a clip
  library. A clip library is a GLB of `kind: clips` with the skeleton and its animations and no
  mesh, which is how T-1790's shared library ships.

## 8. LODs and the detail tiers

There are four LODs, one GLB each: **`<asset_id>.lod0.glb` … `<asset_id>.lod3.glb`**. Every LOD
has the whole skeleton and the required material slots; only lod0 and lod1 must have a face.
The scene-detail control picks from them:

| tier | LODs it may draw |
|---|---|
| `full` | lod0 near … lod3 far |
| `balanced` | lod1 … lod3 |
| `light` | lod2, lod3 |

`light` stays the floor (AGENTS.md § frame budget).

**What one figure costs, measured (T-1787).** `tools/human_fixture.mjs` opens every human GLB
in the browser at 1280×800 and 390×780 and records `data/humans/fixture.measure.json`. On the CI
fixture (`c4d_fixture`, L417), as shipped (Meshopt, `assets/humans/web/`):

| LOD | triangles | vertices | draws | materials | textures | KB shipped | KB uncompressed |
|---|---:|---:|---:|---:|---|---:|---:|
| lod0 | 3,668 | 2,040 | 5 | 5 | 1 × 64² | 108 | 233 |
| lod1 | 2,012 | 1,212 | 5 | 5 | 1 × 64² | 98 | 166 |
| lod2 | 468 | 380 | 5 | 5 | 1 × 64² | 74 | 95 |
| lod3 | 316 | 304 | 5 | 5 | 1 × 64² | 72 | 90 |

Read it for what it says about the *pipeline*. The fixture is built from primitives, so its
triangles are not a real body's; T-1789's first body is measured by the same command and its
figures replace these as the per-LOD budget. Two things already hold whatever the body:

- **Draws are set by material slots, not by LOD.** `GLTFLoader` makes one draw per primitive,
  and a primitive per material, so every LOD of a five-slot figure is five draws. A crowd's
  draw budget is slots × figures, which is what T-1792 has to plan around.
- **The clips are the floor of a figure's bytes.** Every contract bone is keyed in every clip, so
  a mixer cross-fading `idle` into `walk` never keeps a stale pose from a bone one clip leaves
  out. That costs about half of lod3: exporting only the keyed bones took the uncompressed lod3
  from 92 KB to 44 KB. A clip library (§ 7, T-1790) shipped once beside the bodies pays it once.

## 9. Delivery

**Browser: GLB, Meshopt where it pays.** The renderer's `GLTFLoader` has a Meshopt decoder
(`renderers/web/js/scene-loader.js`) and **no KTX2 or Draco loader**, so:

- `KHR_texture_basisu` (KTX2) is **refused**. An asset using it throws on load, and this was
  measured on a bake (see the `BAKE_KTX2` note in `tools/web_derivatives.sh`). Lift the refusal
  only in the change that wires `KTX2Loader` and proves it on a textured asset.
- `KHR_draco_mesh_compression` is **refused** for the same reason. Meshopt is this project's
  compression.
- Allowed: `EXT_meshopt_compression`, `KHR_mesh_quantization`, `KHR_texture_transform`,
  `KHR_materials_emissive_strength`. An unlisted extension is refused until it is proven and
  added.

**The derivative sits beside its master** (T-1787). `tools/human_export.sh` writes the
Blender export to `assets/humans/<asset_id>.lod<N>.glb` and its Meshopt derivative to
`assets/humans/web/` under the same name. Meshopt's quantisation turns positions into integers
and folds their scale into the skin's inverse bind matrices, which are compressed too, so a
derivative's metric frame cannot be read from its JSON. `human_contract.py` therefore reads a
`web/` file beside its master: the master must pass the frame checks (`frame.master`), and every
bone, slot, morph, clip, socket and provenance field must be the master's (`derivative.drift`).
`tools/human_fixture.mjs` then decodes both in the browser and holds the derivative's rest frame
to the master's within 2 mm.

**Unreal: an export, not a master.** Export FBX or glTF from the same `.blend` with the same
bone, clip and material names. Metres become centimetres on import, and glTF `(x, y, z)` becomes
Unreal `(x, z, y)` (`docs/unreal/README.md`). Unreal's own skeleton, retarget and material
assets are built from that import. Nothing flows back into the master.

## 10. Provenance and licence

Every human GLB carries `scenes[0].extras.chicago4d_human`. The Blender exporter writes the
scene's custom properties there:

| field | |
|---|---|
| `contract_version` | `1` |
| `kind` | `body` or `clips` |
| `asset_id`, `lod` | must agree with the file name |
| `skeleton` | `c4d_humanoid_v1` |
| `grade` | `attested` · `inferred` · `reconstructed`: the grade of the **depiction**, not of the person |
| `basis` | what it rests on, or what bounded the invention |
| `sources` | `source_id`s, each resolving in `data/sources/`; `attested` requires at least one |
| `liberty` | the `docs/LIBERTIES.md` entry; required when `reconstructed` |
| `license`, `master`, `authored_by` | the licence (never `check_required`: AGENTS.md rule 6), the master's path, who made it |

A generic resident's body is `reconstructed`. A likeness taken from a portrait is `attested` by
that portrait's source. **Never promote a depiction's grade to match its person's.** Mark
Beaubien's record is well attested; a body built for him without a likeness is still a
reconstruction.

## 11. The instance record

`data/humans/instances/<scene>/<id>.json`, one per person per scene, validated against
`human_instance.schema.json`. **Appearance, animation and behaviour are separate blocks**, so a
person is never tied to one renderer:

| block | carries |
|---|---|
| `person_id` | an existing person record (`data/sidecars/<scene>/people.json`). This file never creates a person; the residents layer remains the only one |
| `appearance` | `asset_id` and per-slot `variants` (clothing, hair) |
| `placement` | `local_e`, `local_n`, `heading_deg`, `anchor` (§ 2) |
| `animation` | the `clip` playing now, `loop`, a start `phase` so a crowd is not in step |
| `behaviour` | `state` (`standing walking working seated talking`) and an optional walking `route`; the renderer chooses clips for a state |
| `interaction` | `selectable`, `radius_m`, `opens` (`resident_card` or `none`) |
| `lod` | `auto`, or `fixed` with one LOD |
| `display` | `withheld` or `shown`; refused while L1 stands |
| `review_required` | carried from the person's record and never dropped |
| `provenance` | the depiction's grade, basis, sources, seed, `replaceable_by`, liberty |

**A scene draws only the instances filed under it.** Nothing carries over from one year to
another, so a year that asks for no humans gets none. That is the scene-year gate T-1788 tests.
A scene with no people layer (1812 and 1904 today) cannot bind an instance at all.

## 12. What the gate refuses, by name

`python3 tools/human_contract.py --glb FILE…` prints one line per finding: a code, then what
to fix. The self-test builds a conforming body from `contract.json` itself, proves it passes,
then breaks it one way at a time:

| code | the break |
|---|---|
| `skeleton.missing_bone` · `unknown_bone` · `wrong_parent` · `under_extension` · `incompatible` | an incompatible skeleton: missing, renamed or re-parented bones, a contract bone under an `ext_` bone, a different declared skeleton |
| `skeleton.influences` | more than four influences per vertex (`JOINTS_1`) |
| `material.missing_slot` · `unknown_slot` | a required material slot missing, or a material on no slot |
| `morph.missing_required` · `unknown` | lod0/lod1 without the face, or a morph outside the vocabulary |
| `clip.duplicate` · `bad_name` · `unknown_verb` · `off_skeleton` | duplicate clip names, a clip name outside the grammar, a clip driving a non-contract node |
| `frame.height` · `node_scale` · `origin` | non-metric scale, whether in positions or hidden in a transform; feet or root off the origin |
| `socket.missing` · `wrong_bone` | a required socket missing or on the wrong bone |
| `provenance.missing` · `missing_field` · `license` · `attested_unsourced` · `unknown_source` · `liberty_missing` · `lod_mismatch` | missing provenance or licence, or a grade without what it owes |
| `delivery.refused_extension` · `unknown_extension` | something the browser cannot open |
| `instance.*` | an instance whose person does not resolve, that drops review, asks to be shown under L1, names an unknown slot or verb, or stands twice in one scene |

## 13. What each later ticket inherits

- **T-1787, the export pipeline** (done): `tools/human_export.sh` runs the pinned Blender over a
  master (`tools/human_export.py` holds every exporter setting, with its reason), writes the four
  LODs and their Meshopt derivatives, and gates them with `human_contract.py --glb`.
  `tools/human_fixture.mjs` proves them in the browser and measured § 8.
  `.github/workflows/chicago-4d-humans.yml` rebuilds the CI fixture from
  `tools/human_fixture_blend.py`, requires the same bytes, and runs the browser proof. A real
  master follows the fixture's layout (one armature, `lod0`…`lod3` collections, `socket_*`
  empties, one action per clip, the scene's `chicago4d_human` property) and is exported with
  `tools/human_export.sh --master FILE.blend`.
- **T-1788, the browser actor** (done): `renderers/web/js/humans.js`. `createHumanLayer` is the
  engine: it clones each LOD onto its own bones with `SkeletonUtils`, stands the figure on the
  terrain with § 2's formula, plays a state's clip (`idle`, `walk`, a `gesture` once and back),
  walks a `route` at the walk clip's `speed_m_s`, sets morphs by name and holds the face still
  on a LOD with none, and picks, selects and fires `approach`, `leave` and `open` (the person's
  resident card, nothing else). LODs follow distance within the § 8 tier, with a 12 %
  hysteresis band. Beyond 20 m the face holds still, beyond 30 m it casts no shadow, beyond
  70 m the mixer is not advanced, and beyond 140 m it is hidden and checked every 0.5 s. A
  refcounted asset cache parses each file once and disposes it when the last figure lets it
  go. `mountHumans` is the scene path main.js calls. It reads
  `humans/instances/<scene>/index.json` and the records it names, but only for a scene whose
  `layers` lists `humans` (none does). It draws a record only when it is `shown`, L1 is lifted,
  it is not under review, and its person is in the scene's directory and not already
  standing. `tools/human_actor.mjs` proves the engine on the fixture at both viewports. The
  smoke holds every scene it boots to an empty layer and no request under `humans/`. Still
  owed: `publish.sh` does not mirror `assets/humans/` yet. The first scene that lists
  `humans` has to add that, or its figures 404.
- **T-1789, the 1835 library**: build every body on `c4d_humanoid_v1`, clothing as material
  variants, one liberty per library.
- **T-1790, the clip library**: a `kind: clips` file per § 7.
- **T-1791, Mark Beaubien**: `person_id: beaubien_mark`, with the depiction's own grade.
- **T-1792, scale**: the LOD tiers, `phase`, and `behaviour.state` let a renderer skip work
  for far-away figures.

A change to any of this is a change to every human asset and every engine that reads one.
**Propose it, bump `version`, and never edit the contract to make an asset pass.**

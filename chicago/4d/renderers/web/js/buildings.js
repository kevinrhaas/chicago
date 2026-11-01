/**
 * buildings.js — GLBs in, one batch per material out, picks resolved to a
 * structure_id.
 *
 * Three things here are contract, not preference:
 *
 *  1. **Placement comes from the sidecar, never from a baked transform**
 *     (docs/GLB-CONTRACT.md). Whatever transform a node carries inside the GLB
 *     is baked *into the geometry* relative to the structure node, and the
 *     instance matrix is then composed purely from `placement.local_e`,
 *     `local_n` and `rotation_deg`. Re-georeferencing a building is a two-number
 *     edit in a JSON file and never a rebake — which matters, because almost
 *     every position in this dataset is still symbolic.
 *
 *  2. **Identity comes from `extras.structure_id`, never from the node name.**
 *     A structure with several materials exports as ONE node with SEVERAL child
 *     meshes, because a glTF primitive cannot span materials. `extras` lands on
 *     the parent; the children carry empty `userData`. So identity is resolved
 *     by walking *up* the ancestors, and a raycast is resolved through a batch
 *     id we recorded when we built the batch.
 *
 *  3. **One material per batch, and the batch does not care what colour the
 *     building is or how rough it is.** `BatchedMesh` renders one material, so
 *     the buildings become one batch per distinct material. Materials identical
 *     in every rendered respect are collapsed, and BASE COLOUR (R-W5a) and
 *     ROUGHNESS (R-W5a2) ARE CARRIED PER INSTANCE OR PER VERTEX rather than per
 *     material (see `materialKey`), so two walls that differ only in paint or
 *     finish share a draw call. The whole untextured town is one draw call in
 *     the colour pass and one in the shadow pass, and it stays one as blocks land.
 *     Since T-2568 the colour is the instance's (`setColorAt`) and the
 *     normals and uvs are stored compact; since T-2574 roughness, confidence,
 *     grain and the piece tone share one four-byte attribute (compact-attributes.js).
 */

import * as THREE from 'three';
import { spatialPiecesAsync } from './spatial-batch.js';
import { castOnlyTowardView } from './shadow-casters.js';
import { crestTwin, drawFarReliefAsCrests, farReliefFromSearch } from './far-roof-relief.js';
import { coalesceRuns, COALESCE_ON } from './batch-coalesce.js';
import { rigidBoundsMaterial, installFrustumBoxCull } from './batch-frustum-box.js';
import { backingTriangles } from './view-occlusion.js';
import { planarCoverPlanes } from './planar-occluders.js';
import { opaqueConfidenceRange, programKeyOf } from './confidence.js';
import { seasonPreservesSurface } from './season.js';
import { materialKey as inspectionMaterialKey, captureHooks } from './batch-material.js';
import { enuToWorld, bearingToYaw, toFloatAttribute } from './terrain.js';
import { dealTones, toneFor, toneFactors, NEUTRAL_TONE } from './facades.js';
import { loadRoofRelief } from './roof-relief.js';
import { filterGlessnerRoof } from './glessner-roof-filter.js';
import { tintGlessnerGranite } from './glessner-stone.js';
import {tintKeithStone} from './keith-stone.js';
import { loadWallRelief } from './wall-relief.js';
import { addFeet, feetPoints, packFeet } from './building-feet.js';
import { buildingBodyBounds } from './building-body-bounds.js';
import { cheapenGlass, DEFAULT_GLASS, writePaneAttributes } from './glass.js';
import { layerPick } from './gpu-pick.js';
import {
  compactPlan, compactGeometry, positionScale, quantizePositions, packScalars, toneScaleOf, unpackScalar, SCALARS, SCALARS_GLSL,
} from './compact-attributes.js';

/** Readers own their short-lived closure scopes. A retained occlusion predicate in
 * the batch loop must not keep a temporary source attribute through that loop's
 * shared lexical context after the batch has copied it. */
function packedScalarReader(attribute, toneScale) {
  return (name, i) => unpackScalar(attribute, name, i, toneScale);
}
function packedConfidenceReader(scalar) {
  return (i) => scalar('_confidence', i);
}

/** How the confidence view reads this batch's packed channel (T-2574). */
const PACKED_CONFIDENCE = { read: SCALARS_GLSL.confidence, declare: SCALARS_GLSL.declare };

/** Walk up until something claims a structure_id. Returns null if nothing does. */
export function structureIdOf(object) {
  for (let o = object; o; o = o.parent) {
    const id = o.userData?.structure_id;
    if (id) return id;
  }
  return null;
}

/** The node inside a loaded glTF that carries this structure's identity. */
function findStructureNode(root, id) {
  let found = null;
  root.traverse((o) => {
    if (!found && o.userData?.structure_id === id) found = o;
  });
  // Fall back to the whole scene: a generator that forgot extras still gets
  // rendered, and the caller reports it rather than dropping the building.
  return found ?? root;
}

/**
 * Everything that renders, in one flat list, with geometry in the frame the
 * structure node SITS IN rather than the frame it defines.
 *
 * The difference is not academic and it broke the whole scene once. Under
 * `KHR_mesh_quantization` — which `tools/bake.sh` asks gltf-transform for, and
 * which is what makes the web derivatives small — positions are stored as
 * integers and the DEQUANTISATION is carried on the node as a translation and a
 * scale (6.25 on the Sauganash, for instance). That transform is part of the
 * encoding, not an authored placement. Taking geometry relative to the node
 * itself inverts it and cancels it out, so every building rendered at about a
 * sixth of its size and the ground sank under the water plane while the walker,
 * which reads the heightfield and not the mesh, went on standing at the right
 * height — a scene that looked flooded and left you floating over it.
 *
 * So: the parent's frame. For an uncompressed file the node is identity and this
 * is exactly what it always was; for a quantised one the node's own transform
 * survives, which is the whole point.
 */
function collectMeshes(structureNode) {
  structureNode.updateWorldMatrix(true, true);
  const frame = structureNode.parent ?? structureNode;
  const toLocal = new THREE.Matrix4().copy(frame.matrixWorld).invert();
  const out = [];
  structureNode.traverse((o) => {
    if (!o.isMesh || !o.geometry) return;
    const rel = new THREE.Matrix4().multiplyMatrices(toLocal, o.matrixWorld);
    out.push({ mesh: o, matrix: rel });
  });
  return out;
}

/**
 * Rewrite a structure's confidence channel so the MASSING answers "was this
 * building here", not "do we know its exact wall height".
 *
 * Those are different questions and the view was answering the wrong one. The
 * Exchange Coffee House is a tavern Andreas names, whose keeper is known and
 * whose corner is described — but nobody wrote down how tall it was, so its
 * wall height is honestly reconstructed, and the shader dithered its walls into
 * translucent massing. Dithering is this project's mark for "we made this up".
 * Applied to a building that demonstrably stood there, it is simply false, and
 * a visitor reads it as doubt about the building rather than about a number.
 *
 * So the structure's OWN existence grade sets the range its parts may occupy:
 *
 *   existence reconstructed  every vertex goes to 1.0 — the whole building
 *                            dithers, walls, roof, trim and chimney together.
 *                            A half-dithered invention with a solid chimney
 *                            reads as a real building with an odd texture.
 *   existence attested       nothing dithers. Attribute uncertainty still shows,
 *   or inferred              tinted, because the card behind the click carries
 *                            the exact per-attribute grade and this is the
 *                            summary, not a replacement for it.
 *
 * Nothing is lost by this: the popup still reports every attribute at its own
 * grade, unclamped. What changes is only what the SHAPE in front of you claims.
 */
function existenceFloor(record) {
  // The structure's own grade where it has one (T-2686): a building a picture shows
  // is not dithered as an invention, whatever its stood-here grade says.
  const grade = record?.sidecar?.grade?.value ?? record?.sidecar?.documented_range?.confidence;
  if (grade === 'reconstructed') return { force: 1.0 };
  if (grade === 'attested' || grade === 'inferred') return { ceiling: 0.5 };
  // No stated existence grade: leave the channel exactly as authored rather
  // than inventing a policy for a case the dataset does not produce.
  return {};
}

function applyExistence(geo, rule) {
  const attr = geo.getAttribute('_confidence');
  if (!attr || (rule.force === undefined && rule.ceiling === undefined)) return;
  const a = attr.array;
  for (let i = 0; i < a.length; i += 1) {
    a[i] = rule.force !== undefined ? rule.force : Math.min(a[i], rule.ceiling);
  }
  attr.needsUpdate = true;
}

/**
 * Reduce a geometry to exactly the attribute set a batch can hold, in a fixed
 * order, indexed. Anything else (tangents, a stray COLOR_0) is dropped: the
 * first geometry added to a BatchedMesh defines the batch's attributes for
 * good, and a later geometry carrying an extra one has it silently ignored.
 * Normalising up front means the batch never depends on load order.
 */
function normalizeGeometry(src, matrix, material, confidence, label, tone) {
  const geo = new THREE.BufferGeometry();
  const position = src.getAttribute('position');
  if (!position) throw new Error(`${label}: geometry has no POSITION`);

  const c = material?.color;
  const base = [c ? c.r : 1, c ? c.g : 1, c ? c.b : 1];
  const factors = toneFactors(base[0], base[1], base[2], tone ?? NEUTRAL_TONE);
  geo.setAttribute('position', toFloatAttribute(position, 3));
  // T-2568: the paint is the INSTANCE's colour (see albedoOf); a vertex colour
  // is written only where a generator varies it piece by piece.
  const pieceTone = src.getAttribute('_tone');
  if (pieceTone) geo.setAttribute('_tone', toFloatAttribute(pieceTone, 1));
  geo.setAttribute('_roughness', roughnessAttribute(material, position.count));
  geo.setAttribute('normal', src.getAttribute('normal')
    ? toFloatAttribute(src.getAttribute('normal'), 3)
    : new THREE.BufferAttribute(new Float32Array(position.count * 3), 3));
  geo.setAttribute('uv', src.getAttribute('uv')
    ? toFloatAttribute(src.getAttribute('uv'), 2)
    : new THREE.BufferAttribute(new Float32Array(position.count * 2), 2));
  // T-2400: a baked occlusion map on its own UV set (TEXCOORD_1 -> `uv1`, which
  // GLTFLoader names in `aoMap.channel`). The aoMap is in the material key, so
  // every geometry in this batch carries it and the attribute set stays uniform.
  if (material.aoMap && material.aoMap.channel === 1) {
    const uv1 = src.getAttribute('uv1');
    if (!uv1) throw new Error(`${label}: aoMap reads TEXCOORD_1, which the mesh does not carry`);
    geo.setAttribute('uv1', toFloatAttribute(uv1, 2));
  }
  if (material.userData.roofFilter) {
    geo.setAttribute('_roof_detail', toFloatAttribute(src.getAttribute('_roof_detail'), 1));
  }

  const conf = src.getAttribute('_confidence');
  if (conf) geo.setAttribute('_confidence', toFloatAttribute(conf, conf.itemSize));

  geo.setIndex(src.getIndex()
    ? src.getIndex().clone()
    : new THREE.BufferAttribute(
        new Uint32Array(position.count).map((_, i) => i), 1));

  geo.applyMatrix4(matrix);
  if (!src.getAttribute('normal')) geo.computeVertexNormals();
  // T-2213: the dark pane's panes and windows, read in the structure's own frame.
  if (material.userData.glassPanes) writePaneAttributes(geo);

  const warning = confidence.ensureAttribute(geo, label);
  return { geo, warning, base, factors };
}

/**
 * The material's base colour times its building's own facade tone — written
 * ONCE PER INSTANCE since T-2568, where it used to be written once per vertex.
 *
 * `material.color` is already in the renderer's linear working space (three
 * converts on assignment, and glTF's `baseColorFactor` is linear to begin
 * with), and three multiplies `diffuseColor` by the batch's instance colour
 * (`setColorAt`, a float32 texture in the working space) with no colour-space
 * conversion of its own. So writing `.r/.g/.b` there and leaving the shared
 * material white is EXACTLY the arithmetic of the material's own uniform — the
 * same product, in a different order. Every mesh is its own instance in its
 * batch, and the colour never varied within one, so the per-vertex copy was
 * twelve bytes a vertex of one repeated number.
 *
 * **T-0002 puts one more factor in that product and nothing else changes.**
 * `facades.js` returns a per-channel factor for this structure — silvering by
 * age, plus a per-building jitter — and the exactness above is what makes the
 * factor safe to apply here: a documented white wall still renders at the value
 * its record claims, to the bit, because `toneFor` hands an attested paint the
 * identity tone and 1 x 1 is 1. See `facades.js` for what is invented and
 * `docs/LIBERTIES.md` L126 for its bounds.
 *
 * `t` is how much of the tone is applied — see `setWeathering`. At 1 it is the
 * plain product, not `1 + (f - 1) * 1`, which need not round back to `f`.
 */
function albedoOf(base, factors, t = 1) {
  const f = t === 1 ? factors : factors.map((x) => 1 + (x - 1) * t);
  return [base[0] * f[0], base[1] * f[1], base[2] * f[2]];
}

/**
 * EACH PIECE OF WOOD ITS OWN WEATHERING (T-2123). A generator that builds a
 * run of separate timbers — the fort's log courses and pickets — can write a
 * `_TONE` per vertex, and it multiplies into the colour, after the building's
 * facade tone: the plank walk's per-board rule (frontage.js § THE WALK'S OWN
 * TIMBER) carried to a log wall, so one course reads as one log and the next
 * as another. It is the one colour that does vary within a mesh, so it is the
 * one kept per vertex: since T-2574 it rides lane w of the packed scalars
 * (compact-attributes.js), `perVertexScalars` multiplies it into the colour
 * where three's vertex colour used to, and `setWeathering` never has to touch
 * it. A mesh without the attribute reads a tone of exactly 1.
 * The bounds are the generator's (fort_structure.py LOG_SPAN, palisade.py
 * PICKET_SPAN; L390).
 */

/**
 * The material's roughness, written once per vertex — R-W5a2.
 *
 * The trick the colour used to play per vertex, one step further: a triangle
 * never spans two source meshes, so all three of its vertices carry the
 * identical value and the rasteriser's interpolation of three equal values is
 * that value. What it replaces is `roughnessFactor = roughness` reading a
 * per-material uniform — see `PER_VERTEX_ROUGHNESS`, which substitutes the
 * attribute for the uniform and nothing else. (It stays per vertex and float32
 * after T-2568, because a lone narrower scalar is a misaligned stride on Metal;
 * since T-2574 it is packed with confidence, grain and the piece tone into one
 * four-byte attribute, and every patch reads it from there — compact-attributes.js.)
 *
 * Why this needed a shader patch when colour did not: `vertexColors` is a stock
 * three feature with a `<color_fragment>` chunk behind it; roughness has no such
 * chunk, so the attribute has to be declared, carried to the fragment stage and
 * substituted into `<roughnessmap_fragment>` by hand.
 *
 * A material with a `roughnessMap` would break the substitution — the chunk it
 * replaces multiplies the map's green channel in. No ASSET ships one (R-W2a:
 * 1,353 material slots, zero textures of any kind) and none is expected to, but
 * since T-1488 the RENDERER binds one to the two roof coverings, so the refusal
 * below is live rather than theoretical: a roof batch reads its roughness from
 * the shared uniform. That is only sound because the sheet deals exactly one
 * roughness per covering, which `roof-relief.js` re-checks as it binds and
 * reports if it ever stops being true. The batch key still separates on
 * `roughnessMap`, so a mapped material can never merge with an unmapped one.
 */
function roughnessAttribute(material, count) {
  const r = typeof material?.roughness === 'number' ? material.roughness : 1;
  const out = new Float32Array(count);
  out.fill(r);
  return new THREE.BufferAttribute(out, 1);
}

/**
 * Carry the packed scalars' roughness to `roughnessFactor` and their piece
 * tone into the colour (T-2574; the roughness half is R-W5a2's).
 *
 * Chained the way `confidence.patch` chains — prior first, then ours — so the
 * patches compose on the same material in either order. The roughness
 * substitution is the whole of that half: three's `<roughnessmap_fragment>` is
 * `float roughnessFactor = roughness;` plus a `USE_ROUGHNESSMAP` branch, so
 * with no map this is the same statement with the uniform swapped for the
 * varying. A MAPPED material keeps three's chunk, and the choice is made by
 * three's own `USE_ROUGHNESSMAP` define rather than by this function, so every
 * structures material carries the same hook text and the program cache cannot
 * hand one kind the other's program. A wall bound by wall-relief.js has
 * already replaced the chunk with its own, which reads the same lane.
 *
 * The tone multiplies `diffuseColor` immediately BEFORE `<color_fragment>`,
 * which is where three's vertex colour multiplied it, so the confidence tint
 * and the wall grain that follow the chunk still follow the tone.
 *
 * ITS PROGRAM KEY NAMES WHAT IS BENEATH IT (T-0053's rule). This hook is on
 * every structures material, so `confidence.patch`, which keys a program by
 * the hook it finds, would otherwise read the same key on a roof, a wall and
 * the plain batch, and three would hand a shingled roof the clapboard wall's
 * compiled program — measured on the first build of T-2574: both roofs at the
 * spawn ~10 % dark.
 */
function perVertexScalars(material) {
  const prior = material.onBeforeCompile;
  const priorKey = programKeyOf(material);
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    shader.uniforms.chiToneScale = { value: material.userData.chiToneScale ?? 255 };
    shader.vertexShader = SCALARS_GLSL.declare('uniform float chiToneScale;\n'
      + 'varying float vChiRough;\nvarying float vChiTone;\n'
      + shader.vertexShader.replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>\n  vChiRough = ${SCALARS_GLSL.roughness};\n`
        + `  vChiTone = ${SCALARS_GLSL.tone};`,
      ));
    shader.fragmentShader = 'varying float vChiRough;\nvarying float vChiTone;\n'
      + shader.fragmentShader
        .replace('#include <roughnessmap_fragment>', `#ifdef USE_ROUGHNESSMAP
#include <roughnessmap_fragment>
#else
  float roughnessFactor = vChiRough;
#endif`)
        .replace('#include <color_fragment>', 'diffuseColor.rgb *= vChiTone;\n#include <color_fragment>');
  };
  material.customProgramCacheKey = () => `chicago4d-scalars${priorKey ? `|over:${priorKey}` : ''}`;
  material.needsUpdate = true;
  return material;
}

/**
 * Two materials that render identically should not cost two draw calls — and
 * NEITHER COLOUR NOR ROUGHNESS IS PART OF THE ANSWER, because both are carried
 * per vertex.
 *
 * This is R-W5a, and the measurement is what makes the case. Every one of the
 * 47 building batches in the 2026-08-15 scene was the same
 * `MeshStandardMaterial`: metalness 0, no map of any kind, `DoubleSide`,
 * opaque, no alpha test, smooth-shaded. The ONLY fields that differed were
 * `color` — 39 distinct values across 47 batches — and `roughness`, which takes
 * 16 values. So the town was paying 47 draw calls to render two numbers, and it
 * paid ANOTHER one every time a block landed carrying a paint colour nothing
 * else in the town used: R-G1 measured exactly +11 draw calls for 19 new roofs,
 * and the straight line over the 399 roofs still to come was about +240 against
 * a budget of 80.
 *
 * Taking `color` out of the key collapses those 47 to 16 and, far more
 * importantly, makes a new roof's paint FREE: a block can land any colour it
 * likes without adding a batch.
 *
 * **R-W5a2, 2026-08-17: roughness is out of the key too, and 16 became 1.** It
 * is the shader patch R-W5a declined to write (`perVertexScalars`), and the
 * reason it was worth writing is not the colour pass: every batch that enters
 * the sun's shadow box is a second draw call in the SHADOW pass, so the town's
 * batch count was setting how far the sun could reach. R-W3b(a) measured the
 * reach as draw-call-bound at ±120 m; this is what unbound it.
 *
 * `emissive` stays in the key: nothing in this dataset uses it, and if
 * something ever does, a glowing material is not something to merge silently
 * into a batch of dark ones.
 *
 * Metalness is compared at THREE DECIMALS rather than exactly, and the reason
 * is the town's two bake pipelines: the bespoke masters carry a float32
 * (`0.8999999761581421`) and the generated infill writes the decimal it
 * authored (`0.9`). Those are the same number to any renderer, and comparing
 * them exactly split buckets in two for no reason a visitor could ever see.
 * (Roughness was in this key on the same footing until R-W5a2 took it out
 * altogether; nothing in the dataset uses two roughness values closer than 0.01
 * on purpose, which is why the quantisation was safe while it lasted.)
 *
 * `roughnessMap` stays in the key because `perVertexScalars` cannot substitute
 * for a chunk that samples a texture — so a mapped material must not be merged
 * with an unmapped one. It was a precaution against an asset that might one day
 * carry a map; since T-1488 it is what SEPARATES the town's three batches, and
 * `normalMap` and `aoMap` beside it do the same work. Two roof coverings, two
 * shared texture pairs, two extra batches for 369 roofs — measured in
 * `tickets/T-1488-*.md` at the critic stations.
 */
function materialKey(m) {
  const near = (v) => (typeof v === 'number' ? v.toFixed(3) : '-');
  const offset = m.polygonOffset ? `${m.polygonOffsetFactor}/${m.polygonOffsetUnits}` : '-';
  return [
    m.type,
    m.emissive?.getHexString() ?? '-',
    near(m.metalness),
    m.map?.uuid ?? '-', m.normalMap?.uuid ?? '-', m.aoMap?.uuid ?? '-',
    m.roughnessMap?.uuid ?? '-',
    m.userData.roofFilter ?? '-',
    m.userData.glassPanes ?? '-',
    m.side, m.transparent ? 't' : 'o', m.alphaTest ?? 0, m.flatShading ? 'f' : 's', offset,
  ].join('|');
}

/**
 * THE JOINT FLOOR DRAWS BEHIND THE STONE IT LIES UNDER — T-3226.
 *
 * A coursed stone wall (K02, `k01_frontage.stone()`) lays a `mortar` floor under
 * every stone's whole cell, 1 to 6 mm behind the stone's face (the fabric's
 * `joint.recess_m`), so every joint has a floor and no stone is open behind. The
 * floor is meant to be seen only in the joints. But the web derivative stores a
 * house's positions on a 14-bit lattice over its own box (`web_derivatives.sh`),
 * 2.8 mm a rung at 1801 Prairie, which rounds a 2 mm recess onto the face itself,
 * and past about 50 m a 24-bit depth buffer cannot part 5 mm anyway. So the face
 * and the floor fought for the same pixels: the owner saw it on 2026-10-28 as
 * 1827 and 1801 Prairie's flanks "speckled" and shimmering as he walked, and the
 * houses down the street flickering until he came close.
 *
 * The floor is drawn a few depth steps behind whatever lies in its plane. That
 * moves depth only — no vertex, no colour, no light, no draw call (the floor
 * already batches on its own map) — so a joint looks as it did, and a stone face
 * wins wherever it covers its floor, at any distance and on any lattice. Keyed on
 * the material name `mortar`, docs/GLB-CONTRACT.md § Joint floors.
 * `tools/check_joint_floor.mjs` holds it.
 */
export const JOINT_FLOOR = Object.freeze({ names: Object.freeze(['mortar']), factor: 1, units: 4 });
export function seatJointFloor(material) {
  if (!JOINT_FLOOR.names.includes(material?.name)) return false;
  material.polygonOffset = true;
  material.polygonOffsetFactor = JOINT_FLOOR.factor;
  material.polygonOffsetUnits = JOINT_FLOOR.units;
  return true;
}

/**
 * @param {object} o
 * @param {Map<string,object>} o.registry   from scene-loader
 * @param {object} o.confidence             from createConfidenceView
 * @param {object} o.terrain                from createTerrain (for ground height)
 */
export async function createBuildings({ registry, confidence, terrain, checkpoint = () => null,
  onProgress = () => {}, preserveMaterials = false, lowSpec = false, glass = DEFAULT_GLASS,
  spatialCells = null, collectViewBackings = false, shadowCasters = null }) {
  const group = new THREE.Group();
  group.name = 'structures';
  const problems = [];

  // material key -> { material, entries: [{ record, geo, factors }] }
  const groups = new Map();
  const sourceRoles = new WeakMap();
  const viewOccluders = [];
  /**
   * T-3213: what every backing's `active()` compares against — identity is read
   * and never written, and the scratch is filled and read inside one synchronous
   * call — so one of each serves them all. Each closure held its own pair: about
   * 4 MB of a 1904 phone's heap.
   */
  const OCCLUDER_IDENTITY = new THREE.Matrix4(), occluderScratch = new THREE.Matrix4();
  /** T-3152: one row per source mesh with proven planar cover — see the load loop. */
  const planarSources = [];
  let planarOn = true;
  /** structure id -> the facade tone applied to every one of its surfaces. */
  const tones = new Map();
  /**
   * T-0047. The tone is dealt for the WHOLE town before the load loop, because
   * a repulsion pass cannot be done a building at a time: it has to know what
   * is already standing inside 60 m. The deal reads only the sidecars' own
   * `placement`, so it needs no GLB and no batch, and it is the same answer on
   * every load — see `facades.js` § the repulsion pass.
   */
  /**
   * The two roof coverings' relief maps, loaded once for the whole town
   * (T-1488). It has to be in hand BEFORE the load loop, because `apply()` runs
   * on every material before `materialKey()` reads it — that is what puts the
   * shingled roofs in one batch of their own rather than leaving them in the
   * town's untextured one. A load that fails degrades to today's flat roofs and
   * reports itself; see roof-relief.js.
   */
  const relief = await loadRoofRelief();
  if (relief.problem) problems.push(relief.problem);
  /**
   * The walls' relief (T-1963): clapboard and laid logs, by the record's own
   * substrate and finish — see wall-relief.js and wall-grain.js. Loaded before
   * the loop for the roofs' reason: `apply()` must run before `materialKey()`
   * reads the material, so every bound wall in the town lands in one batch per
   * substrate. 512 px maps on a coarse device.
   */
  const walls = await loadWallRelief({ lowSpec });
  if (walls.problem) problems.push(walls.problem);

  const dealt = dealTones([...registry.values()]
    // Only what will actually be drawn: a record with no GLB stands in nobody's
    // neighbourhood, and letting it hold a tone clear would move a wall a
    // visitor can see away from one they cannot.
    .filter((r) => r.gltf)
    .map((r) => r.sidecar));
  /** The instance colours `setWeathering` rewrites: one row per source mesh. */
  const toneRanges = [];
  /** T-3272: a relief roof piece past its last visible pixel draws its crests only
   *  (far-roof-relief.js). One state for the layer; each batch fills its own pairs. */
  // T-3285: `sun` lets the sun's pass keep the relief whole while the colour pass swaps.
  const farRelief = { on: farReliefFromSearch(globalThis.location?.search), sun: true, batches: [] };
  /** structure id -> its footprint extent in its own local frame, so a building
   *  can be stood on the lowest ground UNDER it rather than under its origin.
   *  Filled in the load loop because placement needs it. */
  const localXZ = new Map();
  /** structure id -> where its walls meet the ground (building-feet.js, T-3029):
   *  what groundUnder() samples when the structure has any. */
  const localFeet = new Map();
  /** T-2600: the building cells being cut on the job pool, awaited after the loop. */
  const partitions = [];
  let totalTris = 0;
  /** T-2927: whether this build cuts meshes into cells (below), and so joins the
   *  drawn cells of one mesh back into one draw; and how many draws that saved. */
  const cutsCells = !!spatialCells || preserveMaterials;
  const coalesce = { on: cutsCells && COALESCE_ON, joined: 0 };

  let completed = 0;
  onProgress(0, registry.size);
  for (const record of registry.values()) {
    onProgress(completed++, registry.size);
    const pause = checkpoint(); if (pause) await pause;
    if (!record.gltf) continue;
    const node = findStructureNode(record.gltf.scene, record.id);
    record.node = node;
    if (!node.userData?.structure_id) {
      problems.push(`${record.id}: no extras.structure_id anywhere in the GLB — `
        + 'identity fell back to the file it came from');
    }
    if (node.userData?.phase_id && record.sidecar.phase
        && node.userData.phase_id !== record.sidecar.phase) {
      problems.push(`${record.id}: GLB is phase '${node.userData.phase_id}' but the sidecar `
        + `says '${record.sidecar.phase}' — the asset and the record disagree`);
    }

    const meshes = collectMeshes(node);
    if (!meshes.length) {
      problems.push(`${record.id}: the GLB contains no meshes`);
      continue;
    }

    // T-0002. One tone per STRUCTURE, resolved once and multiplied into every
    // surface the structure owns — walls, roof, trim, stack alike. Per
    // structure rather than per material because on 38 of the shipped assets
    // the material names are gone (ROADMAP K36(a)), and a rule that reads names
    // would skip exactly those buildings.
    const tone = dealt.get(record.id) ?? toneFor(record.sidecar);
    tones.set(record.id, tone);

    for (const { mesh, matrix } of meshes) {
      const label = `${record.id}/${mesh.name || 'mesh'}`;
      const sourceMaterial = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
      if (!sourceRoles.has(sourceMaterial)) sourceRoles.set(sourceMaterial, sourceMaterial.name);
      const bodyRole = sourceRoles.get(sourceMaterial); // before batching whitens/names it
      // A detail replacement rebuilds from the same source records. Never whiten
      // or shader-patch those source materials: each batch owns its own copy.
      let material = preserveMaterials ? sourceMaterial.clone() : sourceMaterial;
      // T-2109: a transmissive pane costs a second draw of every opaque thing
      // behind it. The replacement is a fresh material, so a clone it replaces
      // is ours to free; a shared source material is left alone.
      const cheaper = cheapenGlass(material, glass);
      if (cheaper !== material) {
        if (preserveMaterials) material.dispose();
        material = cheaper;
      }
      // Before the key is taken, and only ever by name — T-1488 and
      // docs/GLB-CONTRACT.md § Roof coverings.
      const reliefWarning = relief.apply(material);
      if (reliefWarning) problems.push(`${label}: ${reliefWarning}`);
      // A number when this is a bound wall: how much of the wood's figure its
      // finish lets through, written per vertex below (wall-grain.js).
      const grain = walls.apply(material, record.sidecar);
      filterGlessnerRoof(material, record, mesh.geometry);
      // T-2446/T-2469: Glessner's granite to grey-greige; it rides the albedo multiply.
      tintGlessnerGranite(material, record);
      tintKeithStone(material, record);
      seatJointFloor(material);
      let prepared;
      try {
        prepared = normalizeGeometry(mesh.geometry, matrix, material, confidence, label, tone);
        // After the channel exists and is float — see existenceFloor for why the
        // building's own existence grade governs what its parts may claim.
        applyExistence(prepared.geo, existenceFloor(record));
        // Only on a bound wall's geometry, and so only in a wall batch: a batch
        // takes its attribute set from its first geometry, and every geometry
        // in one shares a material key, so the set is uniform by construction.
        if (grain !== null) {
          const count = prepared.geo.getAttribute('position').count;
          prepared.geo.setAttribute('_grain',
            new THREE.BufferAttribute(new Float32Array(count).fill(grain), 1));
        }
      } catch (err) {
        if (preserveMaterials) material.dispose();
        problems.push(`${label}: ${err.message}`);
        continue;
      }
      if (prepared.warning) problems.push(prepared.warning);

      // Inspection sources are immutable clones; other scenes retain their
      // established in-place material lifecycle and batching policy.
      const stableSurface = [THREE.MeshStandardMaterial, THREE.MeshPhysicalMaterial].includes(material.constructor)
        && !JSON.stringify(captureHooks(material)).includes('opaque-hooks');
      const boundsRigid = preserveMaterials && spatialCells === null && rigidBoundsMaterial(material, captureHooks(material));
      const key = preserveMaterials ? inspectionMaterialKey(material) : materialKey(material);
      let bucket = groups.get(key);
      if (!bucket) {
        material.side = material.side ?? THREE.FrontSide;
        // The batch's own colour is now the identity, and every instance
        // carries its building's paint. Whitening the shared material is what
        // makes the multiply come out unchanged — see albedoOf. A per-vertex
        // piece tone rides the packed scalars (T-2574), scaled once all of the
        // batch's meshes are in.
        material.color = new THREE.Color(1, 1, 1);
        material.name = 'merged';
        // Roughness now arrives per vertex too (R-W5a2). The material's own
        // value is left where it is rather than whitened the way colour is:
        // it is a straight substitution, not a multiply, so the uniform is
        // simply never read once the patch is installed.
        perVertexScalars(material);
        confidence.patch(material, { packed: PACKED_CONFIDENCE });
        bucket = { material, entries: [], boundsRigid };
        groups.set(key, bucket);
      } else {
        bucket.boundsRigid = bucket.boundsRigid && boundsRigid;
        if (preserveMaterials) material.dispose();
      }
      totalTris += prepared.geo.getIndex().count / 3;

      // Grow this structure's local footprint as its parts arrive — see
      // groundUnder(), which samples the terrain across it.
      prepared.geo.computeBoundingBox();
      const gb = prepared.geo.boundingBox;
      const seen = localXZ.get(record.id);
      localXZ.set(record.id, seen ? {
        minX: Math.min(seen.minX, gb.min.x), maxX: Math.max(seen.maxX, gb.max.x),
        minZ: Math.min(seen.minZ, gb.min.z), maxZ: Math.max(seen.maxZ, gb.max.z),
      } : { minX: gb.min.x, maxX: gb.max.x, minZ: gb.min.z, maxZ: gb.max.z });
      if (!localFeet.has(record.id)) localFeet.set(record.id, new Map());
      addFeet(localFeet.get(record.id), prepared.geo);
      // T-2219: a narrow phone courtyard view need not submit an entire
      // building's material primitive. Keep every triangle/attribute, but let
      // the existing BatchedMesh cull smaller pieces in each camera/shadow pass.
      // Full's alpha-faded tile relief keeps its original three draw groups.
      // Repartitioning it changes transparent blending/depth order at the ridge.
      const cells = spatialCells || (preserveMaterials && record.id === 'glessner_house'
        && !material.transparent ? { cellM: 4, heightM: 2 } : null);
      // Actual opaque building faces can hide geometry behind them. Neighboring
      // houses matter in the elevated courtyard view too. Registered patches
      // change surface shading, not vertex positions; unknown hooks fail open.
      const occludesView = collectViewBackings && preserveMaterials && stableSurface
        && !material.transparent && !material.transmission && material.opacity===1 && !material.alphaTest
        && !material.alphaHash && !material.alphaMap && !material.displacementMap
        && !material.polygonOffset && material.depthWrite && material.depthTest
        && material.colorWrite && !material.wireframe && !material.stencilWrite
        && !material.clippingPlanes?.length;
      const { geo: source, base, factors } = prepared;
      // T-3152: the cells of this mesh's own large flat faces that they are proven to
      // cover, read before the cells cut it (planar-occluders.js). Only a double-sided
      // surface: the proof joins a plane's two facings, which a front-only face does not.
      let planar = null;
      if (occludesView && record.id === 'glessner_house' && material.side === THREE.DoubleSide) {
        const corners = source.getAttribute('position'), ix = source.getIndex();
        const xyz = new Float64Array(corners.count * 3);
        for (let i = 0; i < corners.count; i += 1) {
          xyz[3 * i] = corners.getX(i); xyz[3 * i + 1] = corners.getY(i); xyz[3 * i + 2] = corners.getZ(i);
        }
        const covers = planarCoverPlanes(xyz, ix ? ix.array : null);
        if (covers.length) planar = { record, covers, actives: [], range: [Infinity, -Infinity] };
        if (planar) planarSources.push(planar);
      }
      const entryOf = (geo) => ({ record, geo, base, factors, occludesView, bodyRole, planar });
      if (!cells) {
        bucket.entries.push(entryOf(source));
      } else {
        // T-2600: the cells are cut on the job pool while the next mesh is
        // prepared. The pieces land in a slot held at this mesh's place in the
        // bucket, so the batch is laid in the order it always was.
        const slot = [];
        bucket.entries.push(slot);
        const job = spatialPiecesAsync(source, cells).then((pieces) => {
          slot.push(...pieces.map(entryOf));
          source.dispose();
        });
        // Heard at the await below; marked handled now, so a refusal while the
        // loop is still yielding at a checkpoint is not reported as unhandled.
        job.catch(() => {});
        partitions.push(job);
      }
    }
  }
  await Promise.all(partitions);
  for (const [, bucket] of groups) bucket.entries = bucket.entries.flat();

  onProgress(completed, registry.size);

  /**
   * The height to stand a building at: the LOWEST ground under its footprint,
   * not the ground under its origin.
   *
   * A single sample is only right on flat ground. This town is nearly flat, so
   * it was right for 221 of 236 structures and wrong for the fifteen that
   * matter most — the ones on the riverbank and the fort mound, where the whole
   * point is that the land falls away. The Wolf Point Tavern hung 1.84 m in the
   * air on its river side and the fort palisade 2.82 m, and in both cases the
   * gap was almost exactly the relief under the footprint, which is the
   * signature of anchoring at one point on a slope.
   *
   * The minimum is the right choice rather than the mean or the origin. Bedding
   * to the lowest corner buries a little of the uphill side, which is what a
   * sill on a slope actually does and what any builder would have done; the
   * alternative leaves daylight under the downhill wall, which nothing does.
   *
   * The footprint is sampled in the building's own rotated frame, because a
   * long building across a slope and the same building along it meet quite
   * different ground.
   *
   * T-3029: and the footprint is where its WALLS meet the ground, not its
   * bounding box. The box reaches out to the eaves and fills the empty corners
   * beside a wing, so on the bank it found ground no wall stands on: the Green
   * Tree's box corner beside its rear ell sat 0.33 m below the ell's own foot,
   * and the inn was bedded 0.88 m under its front door. building-feet.js reads
   * the feet off the y = 0 plane; the box grid stays for a structure with none.
   */
  function groundUnder(record, e, n, rotationDeg) {
    if (!terrain) return 0;
    const box = localXZ.get(record.id);
    if (!box) return terrain.surfaceHeight(e, n);
    // Local +x is east and local +z is SOUTH (world -z is north), before the
    // building's own rotation is applied.
    const th = bearingToYaw(rotationDeg);
    const cos = Math.cos(th);
    const sin = Math.sin(th);
    // Include the declared origin even when sparse geometry (such as a row of
    // tents) starts inside its footprint. Otherwise all mesh-bound samples can
    // be uphill of that reference and lift the anchor above its own ground.
    let lowest = terrain.surfaceHeight(e, n);
    const feet = feetPoints(localFeet.get(record.id));
    if (feet.length) {
      for (const [lx, lz] of feet) {
        lowest = Math.min(lowest, terrain.surfaceHeight(e + lx * cos + lz * sin, n + lx * sin - lz * cos));
      }
      return Number.isFinite(lowest) ? lowest : terrain.surfaceHeight(e, n);
    }
    const STEPS = 4;
    for (let i = 0; i <= STEPS; i += 1) {
      const lx = box.minX + ((box.maxX - box.minX) * i) / STEPS;
      for (let j = 0; j <= STEPS; j += 1) {
        const lz = box.minZ + ((box.maxZ - box.minZ) * j) / STEPS;
        const ee = e + lx * cos + lz * sin;
        const nn = n + lx * sin - lz * cos;
        lowest = Math.min(lowest, terrain.surfaceHeight(ee, nn));
      }
    }
    return Number.isFinite(lowest) ? lowest : terrain.surfaceHeight(e, n);
  }

  // Placement matrix per structure, from the sidecar and nothing else.
  const placements = new Map();
  for (const record of registry.values()) {
    const p = record.sidecar?.placement ?? {};
    const e = p.local_e ?? 0;
    const n = p.local_n ?? 0;
    // docs/GLB-CONTRACT.md: a structure sits at the base of its walls on the
    // ground, EXCEPT one declared `water`, whose local y = 0 is the design water
    // surface — that plane is z = 0 by the definition of the vertical datum, so
    // the anchor is a literal zero and not a lookup. Note what the alternative
    // actually does: `terrain.walkHeight()` reports a wading BARRIER over water, not
    // the bed, so a bridge left on the terrain anchor does not sink — it hangs
    // four metres above the river, which is the harder failure to read.
    const onWater = p.vertical_anchor === 'water';
    const y = onWater ? 0 : groundUnder(record, e, n, p.rotation_deg ?? 0);
    placements.set(record.id, new THREE.Matrix4().compose(
      enuToWorld(e, n, y),
      new THREE.Quaternion().setFromEuler(
        new THREE.Euler(0, bearingToYaw(p.rotation_deg ?? 0), 0)),
      new THREE.Vector3(1, 1, 1),
    ));
    if (p.placement_provisional) {
      problems.push(`${record.id}: placement is provisional — `
        + `${p.symbolic_location ?? 'no coordinates yet'}`);
    }
  }
  for (const [id, feet] of localFeet) localFeet.set(id, packFeet(feet));

  // Shadows have to agree with the view: a wall you can see through should not
  // cast a solid shadow. The same patch on a depth material dithers the shadow
  // exactly as it dithers the surface, and the depth shader has the same
  // `<clipping_planes_fragment>` anchor to hang the discard on.
  const depthMaterial = confidence.patch(new THREE.MeshDepthMaterial({
    depthPacking: THREE.RGBADepthPacking,
  }), { packed: PACKED_CONFIDENCE });

  const batches = [];
  /** structure id -> its union bounding box, in the structure's own frame. */
  const localBoxes = new Map();
  const bodySamples = new Map();
  /** structure id -> the confidence channel the shader will actually read. */
  const channels = new Map();
  // T-2575. Positions go into the batch as Int16 over one uniform scale per
  // STRUCTURE (every piece of it, across every batch, on one grid), and the
  // instance matrix is its placement times that scale — compact-attributes.js
  // says why it is uniform and why the offset is the structure's own origin.
  // So everything that reads batch positions reads them through the instance
  // matrix (backingTriangles, picking, the census), never through `placements`.
  const geometriesOf = new Map();
  for (const [, bucket] of groups) {
    for (const { record, geo } of bucket.entries) {
      if (!geometriesOf.has(record.id)) geometriesOf.set(record.id, []);
      geometriesOf.get(record.id).push(geo);
    }
  }
  /** structure id -> { scale, matrix }: the dequantize and the instance matrix. */
  const instanceFrames = new Map();
  for (const [id, geos] of geometriesOf) {
    const scale = positionScale(geos);
    instanceFrames.set(id, {
      scale,
      matrix: placements.get(id).clone().multiply(new THREE.Matrix4().makeScale(scale, scale, scale)),
    });
  }
  geometriesOf.clear();
  for (const [, bucket] of groups) {
    // T-3272: each relief piece is followed by its hidden crests-only twin, laid
    // before the batch is sized so the twin's vertices are counted in it.
    if (bucket.material.userData.roofFilter === 'course-pixels-v1') {
      bucket.entries = bucket.entries.flatMap((e) => {
        const twin = crestTwin(e.geo);
        return twin ? [e, { ...e, geo: twin.geo, twinOf: e, maxCourse: twin.maxCourse,
          occludesView: false, planar: null }] : [e];
      });
    }
    const verts = bucket.entries.reduce((a, e) => a + e.geo.getAttribute('position').count, 0);
    const idx = bucket.entries.reduce((a, e) => a + e.geo.getIndex().count, 0);
    // The normals and uvs stored compact, in one format across the batch, and
    // roughness, confidence, grain and the piece tone packed into one four-byte
    // attribute (T-2568, T-2574; compact-attributes.js). The tone's scale is the
    // batch's: a batch takes its attribute set from its first geometry, and every
    // geometry in it must be packed to the one scale its shader divides by.
    // T-3213: a batch whose material samples no texture has nothing to read a uv
    // with — the walls' and roofs' relief derive theirs from the position
    // (wall-relief.js, roof-relief.js), and no patch on a structures material reads
    // the attribute — but three uploads every attribute a geometry carries, read or
    // not. The 1904 town's largest batch is untextured and its uv float32 (the
    // tiling ones stay float, compact-attributes.js): about 17 MB of a phone's GPU
    // buffers, drawn by nothing. The key holds every map, so the whole bucket agrees.
    if (!Object.values(bucket.material).some((v) => v?.isTexture)) {
      for (const e of bucket.entries) e.geo.deleteAttribute('uv');
    }
    const plan = compactPlan(bucket.entries.map((e) => e.geo));
    const toneScale = toneScaleOf(bucket.entries.map((e) => e.geo));
    bucket.material.userData.chiToneScale = toneScale;
    // No vertex colour reaches a structures batch any more: the paint is the
    // instance's and the piece tone is lane w. A source material can still
    // arrive from GLTFLoader asking for one, and an unbound `color` would then
    // darken the batch, so it is turned off here for all of them.
    bucket.material.vertexColors = false;
    const batch = new THREE.BatchedMesh(bucket.entries.length, verts, idx, bucket.material);
    batch.name = `structures:${bucket.material.name || bucket.material.type}`;
    batch.castShadow = true;
    batch.receiveShadow = true;
    batch.customDepthMaterial = depthMaterial;
    // T-2529: at `light`, a piece whose shadow cannot reach the view is left
    // out of the sun's pass (shadow-casters.js); the colour pass is untouched.
    if (shadowCasters) castOnlyTowardView(batch, shadowCasters);
    // T-3272: before the narrow phase below, which trusts only the hook it wrapped.
    let farPairs = null;
    if (bucket.entries.some((e) => e.twinOf)) {
      farPairs = [];
      drawFarReliefAsCrests(batch, { get on() { return farRelief.on; },
        get sun() { return farRelief.sun; }, pairs: farPairs,
        set swapped(n) { farRelief.swapped = n; }, set sunSwapped(n) { farRelief.sunSwapped = n; } });
      farRelief.batches.push({ batch, pairs: farPairs });
    }
    batch.userData.batchIndex = [];
    // Each instance's dequantize scale, for a reader that needs the structure's
    // frame back off the batch (tools/drawn_placement_census.mjs).
    batch.userData.positionScale = [];
    // T-2646: each instance's confidence range, as the shader decodes it, so the
    // Confidence view can leave a wholly ghosted structure out of the opaque pass
    // and a structure with nothing ghosted out of the ghost pass.
    batch.userData.confidenceRanges = [];
    let backingPositionVersion, backingIndexVersion, backingConfidenceVersion;

    for (const entry of bucket.entries) {
      const { record, geo, base, factors, occludesView, bodyRole, planar } = entry;
      const pause = checkpoint(); if (pause) await pause;
      compactGeometry(geo, plan);
      const frame = instanceFrames.get(record.id);
      quantizePositions(geo, frame.scale);
      packScalars(geo, toneScale);
      // Every reading below is of the bytes the shader decodes, not of the
      // floats they were packed from.
      const scalars = geo.getAttribute(SCALARS);
      const scalar = packedScalarReader(scalars, toneScale);
      // The piece tone as the batch stores it, summed for facadeTones' readback.
      let toneSum = 0;
      for (let i = 0; i < scalars.count; i += 1) toneSum += scalar('_tone', i);
      const geometryId = batch.addGeometry(geo);
      const instanceId = batch.addInstance(geometryId);
      entry.instanceId = instanceId;
      if (entry.twinOf) {
        // T-3272: a twin is the piece's own triangles, drawn only in its place. It
        // keeps no tone row, roll or channel of its own: it is not another surface.
        batch.setColorAt(instanceId, batch.getColorAt(entry.twinOf.instanceId, new THREE.Color()));
        batch.setMatrixAt(instanceId, frame.matrix);
        batch.userData.positionScale[instanceId] = frame.scale;
        batch.userData.batchIndex[instanceId] = record.id;
        const pieceRange = batch.userData.confidenceRanges[entry.twinOf.instanceId];
        if (pieceRange) batch.userData.confidenceRanges[instanceId] = pieceRange.slice();
        batch.setVisibleAt(instanceId, false);
        // The twin sorts and sphere-culls as its piece does: a transparent batch draws its
        // instances back to front by their spheres, and the relief's three pieces meet at
        // the ridge, so a twin keyed by its own (smaller) sphere could change who draws
        // last there. Larger than the twin's own, so the cull stays conservative.
        const pieceInfo = batch._geometryInfo?.[batch.getGeometryIdAt(entry.twinOf.instanceId)];
        const twinInfo = batch._geometryInfo?.[geometryId];
        if (pieceInfo && twinInfo && 'boundingSphere' in twinInfo) {
          twinInfo.boundingSphere = batch.getBoundingSphereAt(
            batch.getGeometryIdAt(entry.twinOf.instanceId), new THREE.Sphere());
        }
        // The bound is read off the bytes the shader decodes (the packed piece), not the
        // floats the twin was cut from: every vertex of the piece, so never below a relief one.
        const course = entry.twinOf.geo.getAttribute('_roof_detail');
        let maxCourse = entry.maxCourse;
        for (let i = 0; course && i < course.count; i++) maxCourse = Math.max(maxCourse, course.getX(i));
        farPairs.push({ piece: entry.twinOf.instanceId, twin: instanceId, maxCourse });
        geo.dispose();
        continue;
      }
      // T-0002. The mesh's paint is its instance's colour, so the tone can be
      // wound back and forth at runtime — see setWeathering.
      const count = geo.getAttribute('position').count;
      const row = {
        batch,
        id: record.id,
        instanceId,
        count,
        base,
        factors,
        toneSum,
        toneFirst: count ? scalar('_tone', 0) : 1,
      };
      toneRanges.push(row);
      batch.setColorAt(instanceId, new THREE.Color(...albedoOf(base, factors)));
      batch.setMatrixAt(instanceId, frame.matrix);
      batch.userData.positionScale[instanceId] = frame.scale;
      // `placement` below is the INSTANCE matrix, dequantize included, which is
      // the one that turns this geometry's positions into the world (T-2575).
      if (occludesView) {
        // T-3213: `identity` and `current` are the layer's one pair (below the
        // occluder list), not two more matrices in every backing's closure.
        const placement=batch.getMatrixAt(instanceId,new THREE.Matrix4()), current=occluderScratch;
        const identity=OCCLUDER_IDENTITY, m=batch.material;
        const hooks=[m.onBeforeCompile,m.onBeforeRender,m.customProgramCacheKey], side=m.side;
        // Only the existing opaque, aperture-cut backing, under its known
        // position-preserving shaders. Visibility/transform changes fail open.
        const active=()=> {
          for(let o=batch;o;o=o.parent)if(!o.visible)return false;
          return batch.getVisibleAt(instanceId) && batch.getGeometryIdAt(instanceId)===geometryId
            && batch.material===m && m.side===side && batch.matrixWorld.equals(identity)
            && batch.getMatrixAt(instanceId,current).equals(placement)
            && batch.geometry.attributes.position.version===backingPositionVersion
            && batch.geometry.index.version===backingIndexVersion
            && batch.geometry.attributes[SCALARS].version===backingConfidenceVersion
            // T-2806: compared without building an array: this runs every frame on a phone
            && ((m.onBeforeCompile===hooks[0] && m.onBeforeRender===hooks[1] && m.customProgramCacheKey===hooks[2])
              || seasonPreservesSurface(m,hooks))
            && m.visible && m.opacity===1 && !m.transparent && !m.transmission && m.depthWrite && m.depthTest
            && m.colorWrite && !m.wireframe && !m.alphaTest && !m.alphaHash && !m.alphaMap
            && !m.displacementMap && !m.polygonOffset && !m.stencilWrite
            && (m.depthFunc===THREE.LessDepth || m.depthFunc===THREE.LessEqualDepth)
            && !m.clippingPlanes?.length;
        };
        const ranges=new Map();
        for(const triangle of backingTriangles(geo,placement,m.side,packedConfidenceReader(scalar))) {
          // Small distant facade details are expensive candidates with little
          // coverage; the inspected house keeps its finer backing faces.
          if(record.id!=='glessner_house' && triangle.area<4)continue;
          const key=JSON.stringify(triangle.confidenceRange);
          if(!ranges.has(key))ranges.set(key,()=>active()
            && opaqueConfidenceRange(triangle.confidenceRange,confidence));
          viewOccluders.push({...triangle,active:ranges.get(key)});
        }
        // Every piece of the source mesh has to stand as the backing's does.
        if (planar) planar.actives.push(active);
      }
      batch.userData.batchIndex[instanceId] = record.id;
      record.instanceId = instanceId;
      // Measure BEFORE dispose, and union across every material a structure
      // uses: a building is walls plus roof plus trim, and any one of those
      // alone is not the building. This is what `instanceBounds()` reports and
      // what the size gate reads — see the note on that method.
      // The box is measured on the stored positions and scaled back to metres
      // in the structure's frame, so it is what the GPU draws, quantizing and all.
      geo.computeBoundingBox();
      geo.boundingBox.min.multiplyScalar(frame.scale);
      geo.boundingBox.max.multiplyScalar(frame.scale);
      let box = localBoxes.get(record.id);
      if (!box) { box = new THREE.Box3(); localBoxes.set(record.id, box); }
      box.union(geo.boundingBox);
      if (record.sidecar?.attributes?.sign_pole_set_out?.value != null) {
        let samples = bodySamples.get(record.id);
        if (!samples) { samples = []; bodySamples.set(record.id, samples); }
        const storedPosition = geo.getAttribute('position');
        for (let i = 0; i < storedPosition.count; i++) samples.push({ role: bodyRole,
          point: [storedPosition.getX(i) * frame.scale, storedPosition.getY(i) * frame.scale, storedPosition.getZ(i) * frame.scale] });
      }
      // The confidence the SHADER will see, after the existence floor, recorded
      // per structure so a gate can ask the question a visitor asked: does this
      // building dither, and does it dither all over?
      {
        let seen = channels.get(record.id);
        if (!seen) { seen = { min: Infinity, max: -Infinity, dithered: 0, total: 0 }; channels.set(record.id, seen); }
        let lo = Infinity, hi = -Infinity;
        for (let i = 0; i < count; i += 1) {
          const v = scalar('_confidence', i);
          if (v < lo) lo = v;
          if (v > hi) hi = v;
          seen.total += 1;
          if (v > 0.75) seen.dithered += 1;
        }
        seen.min = Math.min(seen.min, lo);
        seen.max = Math.max(seen.max, hi);
        if (count) batch.userData.confidenceRanges[instanceId] = [lo, hi];
        // The pieces' decoded range, as a whole: a rectangle stands only where all of
        // its source mesh is opaque, a superset of the triangles that cover it.
        if (planar && count) { planar.range[0] = Math.min(planar.range[0], lo); planar.range[1] = Math.max(planar.range[1], hi); }
      }
      geo.dispose();
    }
    backingPositionVersion=batch.geometry.attributes.position.version;
    backingIndexVersion=batch.geometry.index.version;
    backingConfidenceVersion=batch.geometry.attributes[SCALARS].version;
    // Narrow phase sees native whole-instance entries before existing coalescing.
    const narrow = installFrustumBoxCull(batch, bucket.boundsRigid, depthMaterial, seasonPreservesSurface, coalesce, shadowCasters);
    if (cutsCells) coalesceRuns(batch, coalesce);
    narrow?.seal();
    batch.computeBoundingBox();
    batch.computeBoundingSphere();
    // T-3213: every addGeometry above left an update range on each attribute and
    // the index, and three clears those only after a PARTIAL upload — the first
    // upload sends the whole array and keeps them. About 12 MB of `{ start, count }`
    // in a 1904 phone's heap, for buffers that are uploaded whole anyway. An empty
    // list means "upload all of it", so dropping them changes no byte on the GPU.
    for (const attribute of [...Object.values(batch.geometry.attributes), batch.geometry.index]) {
      attribute?.clearUpdateRanges();
    }
    group.add(batch);
    batches.push(batch);
    // T-2786: every entry's geometry is in the batch now. `dispose()` above frees
    // nothing in the page, and `groups` lives as long as the layer (its closures
    // keep this scope), so the 37k source geometries stayed reachable: about
    // 50 MB of arrays and 25 MB of heap in 1904 on a phone.
    bucket.entries = [];
  }

  // T-3152: each proven planar cover, in the world frame, for the view filter's
  // `planes`. It stands only while every piece of its source mesh passes the backing's
  // own test and the whole mesh's confidence is opaque; `setPlanarCovers(false)`
  // withdraws them all.
  const planarCovers = [];
  for (const planar of planarSources) {
    const place = placements.get(planar.record.id);
    const range = planar.range, actives = planar.actives;
    if (!place || !actives.length || !(range[0] <= range[1])) continue;
    const active = () => planarOn && actives.every((f) => f()) && opaqueConfidenceRange(range, confidence);
    const turn = new THREE.Matrix3().setFromMatrix4(place);
    const axis = (a) => new THREE.Vector3(...a).applyMatrix3(turn).normalize();
    for (const c of planar.covers) {
      planarCovers.push({ ...c, o: new THREE.Vector3(...c.normal.map((x) => x * c.d)).applyMatrix4(place),
        n: axis(c.normal), u: axis(c.u), v: axis(c.v), active, structure: planar.record.id });
    }
  }
  planarSources.length = 0;

  /**
   * How much of the facade tone is applied, 0..1 — T-0002's runtime handle.
   *
   * It exists because of R-BUG6(a)'s finding: a compile-time flag is not a
   * runtime handle, and a gate that cannot turn a thing OFF cannot prove it is
   * on. With this, the suite photographs the same held frame at 1 and at 0 and
   * measures the difference, which is the only evidence that the tone reaches
   * the render rather than merely reaching an array.
   *
   * The rewrite is exact: each instance's colour is recomputed from its base
   * and its factors at the new strength (T-2568), not rescaled from the one it
   * carries, so a round trip to 0 and back restores the very same floats — and
   * the gate asserts the restored frame, not just the changed one.
   *
   * A visitor never calls it. It is not a setting; the tone is what the town
   * looks like.
   */
  const bodyDiagnostics = new Map();
  for (const [id, samples] of bodySamples) {
    bodyDiagnostics.set(id, buildingBodyBounds(registry.get(id).sidecar, samples,
      instanceFrames.get(id).scale / 32767));
  }
  bodySamples.clear();
  let weathering = 1;
  function setWeathering(value) {
    const t = Math.max(0, Math.min(1, Number(value)));
    if (!Number.isFinite(t) || t === weathering) return weathering;
    const colour = new THREE.Color();
    for (const row of toneRanges) {
      row.batch.setColorAt(row.instanceId, colour.setRGB(...albedoOf(row.base, row.factors, t)));
    }
    weathering = t;
    return weathering;
  }

  /**
   * THE TOWN'S ROLL CALL — T-1126. Which structures actually put geometry into
   * a batch, and which were supposed to and did not.
   *
   * `localBoxes` is the honest answer to "is this building standing" and the
   * only one in this file: it is filled where a mesh enters a batch, so a
   * record that has a sidecar, a placement matrix and a manifest entry but
   * whose GLB never arrived is simply not in it. `placements` is NOT that
   * answer — it is filled for every record in the registry before a single
   * triangle is read, from the sidecar alone.
   *
   * The distinction is the whole ticket. On 14 September 2026 one auction room
   * failed to fetch and the scene drew its signboard 2.55 m up on nothing and
   * its crates in the grass beside it, because every layer that hangs furniture
   * off a wall derives its geometry from the RECORD and never asked whether the
   * wall arrived. A failed load has to degrade into an absence; what it must
   * never do is degrade into a false scene, where furniture is presented as if
   * its host were standing and a visitor has no way to read the difference.
   *
   * `missing` is deliberately a set of ids rather than a count, and it is
   * consulted rather than inverted: a dependent layer asks "is my host MISSING",
   * so an id this file has never heard of — a street edge, a wharf, a chunk name
   * — answers no and draws, which is what it should do. Asking the opposite
   * question against `standing` would silently delete every piece of furniture
   * whose owner is not a structure at all.
   */
  const expected = [];
  const missing = new Set();
  for (const record of registry.values()) {
    // A record with no asset is drawn by another layer (the estray pen's fence)
    // and the loader has already reported it if it names no layer at all.
    if (!record.sidecar?.asset) continue;
    expected.push(record.id);
    if (!localBoxes.has(record.id)) missing.add(record.id);
  }
  if (missing.size) {
    problems.push(`${missing.size} of ${expected.length} structures drew no geometry — `
      + `${[...missing].join(', ')}`);
  }

  /*
   * A tap is drawn, not raycast (gpu-pick.js, T-2573): each batch is drawn into
   * one pixel under its id material and the instance it names is the instance
   * the raycast's `batchId` named, so a phone need keep none of the batches'
   * triangles. The reach is the one this pick always had — as far as you can
   * see, which depends on how high you are (`pickReach`): a fixed 400 m was
   * short from the air along any shallow sightline, so a roof on the far side
   * of the town from the aerial anchor could not be picked. `pickAtRaycast` is
   * the old path, the oracle while the arrays exist.
   */
  const pick = layerPick(() => batches, (hit) => {
    const id = (hit.batchId != null ? hit.object.userData.batchIndex?.[hit.batchId] : null)
      ?? structureIdOf(hit.object);
    if (!id) return null;
    return { id, record: registry.get(id), point: hit.point, distance: hit.distance };
  });

  return {
    group,
    batches,
    coalesce,
    viewOccluders,
    /** T-3272: far relief pieces drawn as their crests, on or off, for the on/off pixel
     *  proof; `swapped` is how many the last colour pass swapped. T-3285: `sun` takes
     *  the sun's pass alone back to the whole relief; `sunSwapped` is its count. */
    farRelief: {
      get on() { return farRelief.on; },
      set on(v) { farRelief.on = !!v; },
      get sun() { return farRelief.sun; },
      set sun(v) { farRelief.sun = !!v; },
      get swapped() { return farRelief.swapped ?? 0; },
      get sunSwapped() { return farRelief.sunSwapped ?? 0; },
      get pieces() { return farRelief.batches.reduce((n, b) => n + b.pairs.length, 0); },
    },
    /** T-3152: the proven planar backings on or off, for the on/off pixel proof. */
    setPlanarCovers(on) { planarOn = !!on; return planarOn; },
    planarCovers,
    problems,
    triangles: totalTris,

    /**
     * The structures that were told to draw and did not. Read by main.js to
     * report the shortfall, and handed to the furniture layers so a board does
     * not hang on a wall that is not there. See the roll call above.
     */
    missing,

    /**
     * Drawn against indexed, as one line, once per load (T-1126 § 4). If
     * `standing` is ever short of `expected`, the walk is claiming a town it did
     * not draw, and this is the figure that says whether that is one anomaly or
     * a rate.
     */
    roll: {
      indexed: registry.size,
      expected: expected.length,
      standing: expected.length - missing.size,
      missing: [...missing],
    },
    /**
     * What the walls were bound with (T-1963): `off` under `?walls=flat`, else
     * each substrate's library id, map size, tile and mean roughness.
     */
    wallRelief: walls.off ? { off: true } : { off: false, substrates: walls.sets ?? null },
    /** Draw calls these buildings cost in the colour pass. */
    get drawCalls() { return batches.length; },

    /** T-0002's runtime handle: 1 is the town as it ships, 0 is every building
     *  back on its archetype's flat colour. */
    setWeathering,
    get weathering() { return weathering; },

    /**
     * What tone each structure was given and what its vertices were actually
     * written with, keyed by structure id.
     *
     * Both halves are here on purpose. The tone is the INTENT — what
     * `facades.js` decided from the record — and `drawn` is the READBACK, summed
     * off the colour attribute that goes into the batch. A gate that only ever
     * reads the intent cannot tell a live rule from a dead one, which is the
     * mistake K24 found in R-A1's own gate; a gate that reads both can.
     */
    facadeTones() {
      // The drawn colour of a vertex is its instance's paint times its piece
      // tone (1 where it has none), read back from the batch's own colours.
      const sums = new Map();
      const colour = new THREE.Color();
      for (const row of toneRanges) {
        const c = row.batch.getColorAt(row.instanceId, colour);
        let seen = sums.get(row.id);
        if (!seen) { seen = { sum: [0, 0, 0], n: 0, surfaces: new Set() }; sums.set(row.id, seen); }
        seen.sum[0] += c.r * row.toneSum;
        seen.sum[1] += c.g * row.toneSum;
        seen.sum[2] += c.b * row.toneSum;
        seen.n += row.count;
        if (row.count) {
          seen.surfaces.add([c.r * row.toneFirst, c.g * row.toneFirst, c.b * row.toneFirst]
            .map((v) => v.toFixed(6)).join(','));
        }
      }
      const out = {};
      for (const [id, tone] of tones) {
        const d = sums.get(id);
        out[id] = {
          ...tone,
          vertices: d ? d.n : 0,
          surfaces: d ? d.surfaces.size : 0,
          drawn: d && d.n ? [d.sum[0] / d.n, d.sum[1] / d.n, d.sum[2] / d.n] : null,
        };
      }
      return out;
    },

    /**
     * Every structure's rendered size, in metres, keyed by structure id.
     *
     * This exists because the gate that was supposed to catch a broken town
     * measured the TALLEST building in the scene and stopped. That assertion
     * passes with one correct building and two hundred and forty-one collapsed
     * ones, which is exactly the scene that shipped: every wall clamped into a
     * two-metre box by a quantised attribute (see `toFloatAttribute`), while the
     * one uncompressed asset kept the check green.
     *
     * A size is only meaningful against a claim, so this reports the rendered
     * box and leaves the comparison to the caller, which holds the records.
     */
    instanceBounds() {
      const out = {};
      for (const [id, box] of localBoxes) {
        const size = box.getSize(new THREE.Vector3());
        const c = channels.get(id);
        out[id] = {
          size: [size.x, size.y, size.z],
          min: box.min.toArray(),
          max: box.max.toArray(),
          ...(bodyDiagnostics.has(id) ? { body: bodyDiagnostics.get(id) } : {}),
          // What the confidence view will show for this building.
          confidence: c ? { min: c.min, max: c.max, ditheredShare: c.dithered / c.total } : null,
        };
      }
      return out;
    },

    /**
     * The structure under a tap.
     * @param {THREE.Vector2} ndc  normalised device coords, or null for centre
     * @param {THREE.Camera} camera
     */
    pickAt: pick.pickAt,
    /** The same, answered when the GPU has got to it: the gaze target's look (T-2723). */
    pickAtAsync: pick.pickAtAsync,
    /** The structure whose part's box the ray meets first: no draw (gpu-pick.js
     *  `boxPick`, T-2827). A phone's target probe asks this. */
    pickAtBox: pick.pickAtBox,
    /** The raycast it replaced, kept as the oracle (tools/check_upload_release.mjs). */
    pickAtRaycast: pick.pickAtRaycast,

    /** The placement a structure was given: its own frame (metres) to the world —
     *  for gates that need to measure the RENDERED result rather than re-derive
     *  it. Since T-2575 the batch's instance matrix is this times the structure's
     *  uniform dequantize scale; a point in the structure's frame goes through
     *  this one, a stored batch position through the instance matrix. */
    matrixOf(id) { return placements.get(id) ?? null; },

    /** Where a structure's walls meet the ground, as [x, z] in its own frame
     *  (metres; y = 0 there) — the points groundUnder() stood it on, so a gate
     *  can measure the rendered base where a wall actually is (T-3029). */
    feetOf(id) { return feetPoints(localFeet.get(id)); },

    /** Where a structure stands, in world space — for framing and popups. */
    positionOf(id) {
      const m = placements.get(id);
      return m ? new THREE.Vector3().setFromMatrixPosition(m) : null;
    },

    dispose() {
      for (const b of batches) {
        b.dispose?.();
        b.geometry.dispose();
      }
      for (const [, bucket] of groups) bucket.material.dispose();
      depthMaterial.dispose();
    },
  };
}

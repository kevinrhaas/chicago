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
 *     ROUGHNESS (R-W5a2) ARE CARRIED PER VERTEX rather than per material (see
 *     `materialKey`), so two walls that differ only in paint or finish share a
 *     draw call. The whole untextured town is one draw call in the colour pass
 *     and one in the shadow pass, and it stays one as blocks land.
 */

import * as THREE from 'three';
import { enuToWorld, bearingToYaw, toFloatAttribute } from './terrain.js';
import { dealTones, toneFor, toneFactors, NEUTRAL_TONE } from './facades.js';
import { loadRoofRelief } from './roof-relief.js';

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
  const grade = record?.sidecar?.documented_range?.confidence;
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
  geo.setAttribute('color', albedoAttribute(base, factors, position.count));
  geo.setAttribute('_roughness', roughnessAttribute(material, position.count));
  geo.setAttribute('normal', src.getAttribute('normal')
    ? toFloatAttribute(src.getAttribute('normal'), 3)
    : new THREE.BufferAttribute(new Float32Array(position.count * 3), 3));
  geo.setAttribute('uv', src.getAttribute('uv')
    ? toFloatAttribute(src.getAttribute('uv'), 2)
    : new THREE.BufferAttribute(new Float32Array(position.count * 2), 2));

  const conf = src.getAttribute('_confidence');
  if (conf) geo.setAttribute('_confidence', toFloatAttribute(conf, conf.itemSize));

  geo.setIndex(src.getIndex()
    ? src.getIndex().clone()
    : new THREE.BufferAttribute(
        new Uint32Array(position.count).map((_, i) => i), 1));

  geo.applyMatrix4(matrix);
  if (!src.getAttribute('normal')) geo.computeVertexNormals();

  const warning = confidence.ensureAttribute(geo, label);
  return { geo, warning, base, factors };
}

/**
 * The material's base colour, written once per vertex — times its building's
 * own facade tone.
 *
 * `material.color` is already in the renderer's linear working space (three
 * converts on assignment, and glTF's `baseColorFactor` is linear to begin
 * with), and three's `<color_fragment>` chunk multiplies `diffuseColor.rgb` by
 * the `color` attribute with no colour-space conversion of its own. So copying
 * `.r/.g/.b` straight in and leaving the shared material white is EXACTLY the
 * arithmetic that was happening before — the same product, in a different
 * order.
 *
 * **T-0002 puts one more factor in that product and nothing else changes.**
 * `facades.js` returns a per-channel factor for this structure — silvering by
 * age, plus a per-building jitter — and the exactness above is what makes the
 * factor safe to apply here: a documented white wall still renders at the value
 * its record claims, to the bit, because `toneFor` hands an attested paint the
 * identity tone and 1 x 1 is 1. See `facades.js` for what is invented and
 * `docs/LIBERTIES.md` L126 for its bounds.
 */
function albedoAttribute(base, factors, count) {
  const r = base[0] * factors[0], g = base[1] * factors[1], b = base[2] * factors[2];
  const out = new Float32Array(count * 3);
  for (let i = 0; i < count; i += 1) {
    out[i * 3] = r; out[i * 3 + 1] = g; out[i * 3 + 2] = b;
  }
  return new THREE.BufferAttribute(out, 3);
}

/**
 * The material's roughness, written once per vertex — R-W5a2.
 *
 * The same trick as `albedoAttribute`, one step further, and it is exact for
 * the same reason: a triangle never spans two source meshes, so all three of
 * its vertices carry the identical float and the rasteriser's interpolation of
 * three equal values is that value. What it replaces is `roughnessFactor =
 * roughness` reading a per-material uniform — see `PER_VERTEX_ROUGHNESS`, which
 * substitutes the attribute for the uniform and nothing else.
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
 * Carry `_roughness` from the attribute buffer to `roughnessFactor`.
 *
 * Chained the way `confidence.patch` chains — prior first, then ours — so the
 * two patches compose on the same material in either order. The fragment
 * substitution is the whole of it: three's `<roughnessmap_fragment>` is
 * `float roughnessFactor = roughness;` plus a `USE_ROUGHNESSMAP` branch, so
 * with no map this is the same statement with the uniform swapped for the
 * varying.
 */
function perVertexRoughness(material) {
  if (material.roughnessMap) return material;
  const prior = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    shader.vertexShader = 'attribute float _roughness;\nvarying float vChiRough;\n'
      + shader.vertexShader.replace(
        '#include <begin_vertex>',
        '#include <begin_vertex>\n  vChiRough = _roughness;',
      );
    shader.fragmentShader = 'varying float vChiRough;\n'
      + shader.fragmentShader.replace(
        '#include <roughnessmap_fragment>',
        'float roughnessFactor = vChiRough;',
      );
  };
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
 * is the shader patch R-W5a declined to write (`perVertexRoughness`), and the
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
 * `roughnessMap` stays in the key because `perVertexRoughness` cannot substitute
 * for a chunk that samples a texture — so a mapped material must not be merged
 * with an unmapped one. It was a precaution against an asset that might one day
 * carry a map; since T-1488 it is what SEPARATES the town's three batches, and
 * `normalMap` and `aoMap` beside it do the same work. Two roof coverings, two
 * shared texture pairs, two extra batches for 369 roofs — measured in
 * `tickets/T-1488-*.md` at the critic stations.
 */
function materialKey(m) {
  const near = (v) => (typeof v === 'number' ? v.toFixed(3) : '-');
  return [
    m.type,
    m.emissive?.getHexString() ?? '-',
    near(m.metalness),
    m.map?.uuid ?? '-', m.normalMap?.uuid ?? '-', m.aoMap?.uuid ?? '-',
    m.roughnessMap?.uuid ?? '-',
    m.side, m.transparent ? 't' : 'o', m.alphaTest ?? 0, m.flatShading ? 'f' : 's',
  ].join('|');
}

/**
 * @param {object} o
 * @param {Map<string,object>} o.registry   from scene-loader
 * @param {object} o.confidence             from createConfidenceView
 * @param {object} o.terrain                from createTerrain (for ground height)
 */
export async function createBuildings({ registry, confidence, terrain, checkpoint = () => null, onProgress = () => {} }) {
  const group = new THREE.Group();
  group.name = 'structures';
  const problems = [];

  // material key -> { material, entries: [{ record, geo, factors }] }
  const groups = new Map();
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

  const dealt = dealTones([...registry.values()]
    // Only what will actually be drawn: a record with no GLB stands in nobody's
    // neighbourhood, and letting it hold a tone clear would move a wall a
    // visitor can see away from one they cannot.
    .filter((r) => r.gltf)
    .map((r) => r.sidecar));
  /** The colour ranges `setWeathering` rewrites: one row per source mesh. */
  const toneRanges = [];
  /** structure id -> its footprint extent in its own local frame, so a building
   *  can be stood on the lowest ground UNDER it rather than under its origin.
   *  Filled in the load loop because placement needs it. */
  const localXZ = new Map();
  let totalTris = 0;

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
      const material = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
      // Before the key is taken, and only ever by name — T-1488 and
      // docs/GLB-CONTRACT.md § Roof coverings.
      const reliefWarning = relief.apply(material);
      if (reliefWarning) problems.push(`${label}: ${reliefWarning}`);
      let prepared;
      try {
        prepared = normalizeGeometry(mesh.geometry, matrix, material, confidence, label, tone);
        // After the channel exists and is float — see existenceFloor for why the
        // building's own existence grade governs what its parts may claim.
        applyExistence(prepared.geo, existenceFloor(record));
      } catch (err) {
        problems.push(`${label}: ${err.message}`);
        continue;
      }
      if (prepared.warning) problems.push(prepared.warning);

      const key = materialKey(material);
      let bucket = groups.get(key);
      if (!bucket) {
        material.side = material.side ?? THREE.FrontSide;
        // The batch's own colour is now the identity, and every vertex carries
        // its building's paint. Whitening the shared material is what makes the
        // multiply come out unchanged — see albedoAttribute.
        material.vertexColors = true;
        material.color = new THREE.Color(1, 1, 1);
        material.name = 'merged';
        // Roughness now arrives per vertex too (R-W5a2). The material's own
        // value is left where it is rather than whitened the way colour is:
        // it is a straight substitution, not a multiply, so the uniform is
        // simply never read once the patch is installed.
        perVertexRoughness(material);
        confidence.patch(material);
        bucket = { material, entries: [] };
        groups.set(key, bucket);
      }
      bucket.entries.push({ record, geo: prepared.geo, factors: prepared.factors });
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
    }
  }

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
    let lowest = Infinity;
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

  // Shadows have to agree with the view: a wall you can see through should not
  // cast a solid shadow. The same patch on a depth material dithers the shadow
  // exactly as it dithers the surface, and the depth shader has the same
  // `<clipping_planes_fragment>` anchor to hang the discard on.
  const depthMaterial = confidence.patch(new THREE.MeshDepthMaterial({
    depthPacking: THREE.RGBADepthPacking,
  }));

  const batches = [];
  /** structure id -> its union bounding box, in the structure's own frame. */
  const localBoxes = new Map();
  /** structure id -> the confidence channel the shader will actually read. */
  const channels = new Map();
  for (const [, bucket] of groups) {
    const verts = bucket.entries.reduce((a, e) => a + e.geo.getAttribute('position').count, 0);
    const idx = bucket.entries.reduce((a, e) => a + e.geo.getIndex().count, 0);
    const batch = new THREE.BatchedMesh(bucket.entries.length, verts, idx, bucket.material);
    batch.name = `structures:${bucket.material.name || bucket.material.type}`;
    batch.castShadow = true;
    batch.receiveShadow = true;
    batch.customDepthMaterial = depthMaterial;
    batch.userData.batchIndex = [];

    for (const { record, geo, factors } of bucket.entries) {
      const pause = checkpoint(); if (pause) await pause;
      const geometryId = batch.addGeometry(geo);
      const instanceId = batch.addInstance(geometryId);
      // T-0002. Where this mesh's colours ended up inside the batch, so the
      // tone can be wound back and forth at runtime — see setWeathering.
      const range = batch.getGeometryRangeAt(geometryId);
      toneRanges.push({
        batch,
        id: record.id,
        start: range.vertexStart,
        count: range.vertexCount,
        factors,
      });
      batch.setMatrixAt(instanceId, placements.get(record.id));
      batch.userData.batchIndex[instanceId] = record.id;
      record.instanceId = instanceId;
      // Measure BEFORE dispose, and union across every material a structure
      // uses: a building is walls plus roof plus trim, and any one of those
      // alone is not the building. This is what `instanceBounds()` reports and
      // what the size gate reads — see the note on that method.
      geo.computeBoundingBox();
      let box = localBoxes.get(record.id);
      if (!box) { box = new THREE.Box3(); localBoxes.set(record.id, box); }
      box.union(geo.boundingBox);
      // The confidence the SHADER will see, after the existence floor, recorded
      // per structure so a gate can ask the question a visitor asked: does this
      // building dither, and does it dither all over?
      const conf = geo.getAttribute('_confidence');
      if (conf) {
        let seen = channels.get(record.id);
        if (!seen) { seen = { min: Infinity, max: -Infinity, dithered: 0, total: 0 }; channels.set(record.id, seen); }
        for (let i = 0; i < conf.array.length; i += 1) {
          const v = conf.array[i];
          seen.min = Math.min(seen.min, v);
          seen.max = Math.max(seen.max, v);
          seen.total += 1;
          if (v > 0.75) seen.dithered += 1;
        }
      }
      geo.dispose();
    }
    batch.computeBoundingBox();
    batch.computeBoundingSphere();
    group.add(batch);
    batches.push(batch);
  }

  /**
   * How much of the facade tone is applied, 0..1 — T-0002's runtime handle.
   *
   * It exists because of R-BUG6(a)'s finding: a compile-time flag is not a
   * runtime handle, and a gate that cannot turn a thing OFF cannot prove it is
   * on. With this, the suite photographs the same held frame at 1 and at 0 and
   * measures the difference, which is the only evidence that the tone reaches
   * the render rather than merely reaching an array.
   *
   * The rewrite is exact enough to restore: each range is scaled by the ratio
   * between the factor it should carry now and the one it carries, so a round
   * trip to 0 and back leaves float dust rather than a changed frame — and the
   * gate asserts the restored frame, not just the changed one.
   *
   * A visitor never calls it. It is not a setting; the tone is what the town
   * looks like.
   */
  let weathering = 1;
  function setWeathering(value) {
    const t = Math.max(0, Math.min(1, Number(value)));
    if (!Number.isFinite(t) || t === weathering) return weathering;
    const touched = new Set();
    for (const row of toneRanges) {
      const attr = row.batch.geometry.getAttribute('color');
      if (!attr) continue;
      const a = attr.array;
      const scale = [0, 1, 2].map((i) => {
        const target = 1 + (row.factors[i] - 1) * t;
        const applied = 1 + (row.factors[i] - 1) * weathering;
        return applied === 0 ? 1 : target / applied;
      });
      const end = row.start + row.count;
      for (let v = row.start; v < end; v += 1) {
        a[v * 3] *= scale[0];
        a[v * 3 + 1] *= scale[1];
        a[v * 3 + 2] *= scale[2];
      }
      touched.add(attr);
    }
    for (const attr of touched) attr.needsUpdate = true;
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

  const raycaster = new THREE.Raycaster();
  raycaster.far = 400;

  return {
    group,
    batches,
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
      const sums = new Map();
      for (const row of toneRanges) {
        const attr = row.batch.geometry.getAttribute('color');
        if (!attr) continue;
        const a = attr.array;
        let seen = sums.get(row.id);
        if (!seen) { seen = { sum: [0, 0, 0], n: 0, surfaces: new Set() }; sums.set(row.id, seen); }
        const end = row.start + row.count;
        for (let v = row.start; v < end; v += 1) {
          seen.sum[0] += a[v * 3];
          seen.sum[1] += a[v * 3 + 1];
          seen.sum[2] += a[v * 3 + 2];
        }
        seen.n += row.count;
        if (row.count) {
          seen.surfaces.add([a[row.start * 3], a[row.start * 3 + 1], a[row.start * 3 + 2]]
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
          // What the confidence view will show for this building.
          confidence: c ? { min: c.min, max: c.max, ditheredShare: c.dithered / c.total } : null,
        };
      }
      return out;
    },

    /**
     * Raycast into the batches.
     * @param {THREE.Vector2} ndc  normalised device coords, or null for centre
     * @param {THREE.Camera} camera
     */
    pickAt(ndc, camera) {
      raycaster.setFromCamera(ndc ?? new THREE.Vector2(0, 0), camera);
      // The ray reaches as far as you can see, and how far that is depends on
      // how high you are.
      //
      // A fixed 400 m is generous at eye level and short from the air along any
      // shallow sightline: from the aerial anchor at 175 m looking out at -30°,
      // a roof on the far side of the town is past 400 m and simply cannot be
      // picked. Straight down it was never the limit — measured, not assumed:
      // 200 m of altitude at -80° is only ~203 m of ray — so this is not the
      // reason inspecting from the air felt broken. It is a real ceiling on a
      // real sightline, and lifting it costs nothing at eye level, where
      // camera.position.y * 4 stays well under the old constant.
      raycaster.far = Math.max(400, camera.position.y * 4);
      const hits = raycaster.intersectObjects(batches, false);
      if (!hits.length) return null;
      const hit = hits[0];
      const id = hit.object.userData.batchIndex?.[hit.batchId]
        ?? structureIdOf(hit.object);
      if (!id) return null;
      return { id, record: registry.get(id), point: hit.point.clone(), distance: hit.distance };
    },

    /** The instance matrix a structure was placed with — for gates that need to
     *  measure the RENDERED result rather than re-derive it. */
    matrixOf(id) { return placements.get(id) ?? null; },

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

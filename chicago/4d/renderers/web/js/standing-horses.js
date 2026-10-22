// SPDX-License-Identifier: GPL-3.0-or-later
// Additive standing development horse; licensed geometry and reconstructed head/tail idle.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { disposeLoadedAsset } from './scene-loader.js';
import { createExportedHorseIdle } from './standing-horse-idle.js';

const REACH = { full: 70, balanced: 40, light: 0 };
const yawOf = bearing => Math.PI - bearing * Math.PI / 180;
const sha256 = async bytes => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
  b => b.toString(16).padStart(2, '0')).join('');
const assert = (value, message) => { if (!value) throw Error(message); };

function sourceHeader(bytes, spec) {
  assert(bytes.byteLength === spec.runtime_asset.bytes, 'Horse source byte count changed');
  const view = new DataView(bytes);
  assert(view.getUint32(0, true) === 0x46546c67 && view.getUint32(4, true) === 2,
    'Expected pinned glTF2 binary');
  assert(view.getUint32(16, true) === 0x4e4f534a, 'Expected JSON first chunk');
  const json = JSON.parse(new TextDecoder().decode(new Uint8Array(bytes, 20, view.getUint32(12, true))));
  assert(!(json.extensionsRequired?.length), 'Unreviewed required horse extension');
  assert(json.images.every(x => Number.isInteger(x.bufferView) && !x.uri), 'Expected embedded horse images');
  assert(json.buffers.length === 1 && !json.buffers[0].uri, 'Expected embedded horse buffer');
  assert(json.skins.length === 1 && json.skins[0].joints.length === 15, 'Horse rig changed');
  assert(json.animations.length === spec.runtime_asset.animation_count && json.animations.length === 7 && json.materials.length === 3 && json.images.length === 6,
    'Horse source inventory changed');
  const idle = json.animations[6];
  assert(idle.name === spec.runtime_asset.declared_idle_clip && idle.channels.length === 2
    && idle.channels.every(channel => channel.target.path === 'rotation' && [17, 19].includes(channel.target.node)),
  'Only the declared source-bound head/tail idle is permitted');
  let triangles = 0;
  for (const mesh of json.meshes) for (const p of mesh.primitives) {
    assert((p.mode ?? 4) === 4 && p.indices !== undefined, 'Expected indexed horse triangles');
    triangles += json.accessors[p.indices].count / 3;
  }
  assert(triangles === 14986, 'Horse triangle count changed');
  return json;
}

function disposeSkeletons(root) {
  const skeletons = new Set();
  root?.traverse(node => { if (node.skeleton) skeletons.add(node.skeleton); });
  for (const skeleton of skeletons) skeleton.dispose();
}

function disposeSource(asset) {
  disposeSkeletons(asset?.scene);
  disposeLoadedAsset(asset);
}

/** Actual skinned positions in the untouched source frame; no Box3 rest-box shortcut. */
function inspectNative(root, spec) {
  root.updateMatrixWorld(true);
  root.traverse(node => { if (node.isSkinnedMesh) node.skeleton.update(); });
  const point = new THREE.Vector3(), bounds = new THREE.Box3();
  const meshes = new Map();
  root.traverse(node => {
    if (!node.isMesh) return;
    assert(node.isSkinnedMesh && !Array.isArray(node.material), 'Expected original three skinned primitives');
    assert(node.skeleton.bones.length === 15, 'Horse joint count changed');
    assert(node.geometry.getAttribute('skinIndex') && node.geometry.getAttribute('skinWeight')
      && node.geometry.getAttribute('uv'), 'Horse skin/UV streams missing');
    const ids = new Set(node.geometry.index.array);
    for (const id of ids) {
      node.getVertexPosition(id, point).applyMatrix4(node.matrixWorld);
      assert(point.toArray().every(Number.isFinite), 'Nonfinite horse position');
      bounds.expandByPoint(point);
    }
    meshes.set(node.name, node);
  });
  assert(meshes.size === 3, 'Horse mesh inventory changed');
  for (let i = 0; i < 3; i++) {
    assert(Math.abs(bounds.min.getComponent(i) - spec.native_bounds[0][i]) < 1e-4
      && Math.abs(bounds.max.getComponent(i) - spec.native_bounds[1][i]) < 1e-4,
    'Native horse bounds disagree with independent decoder');
  }
  const body = meshes.get(spec.contact_mesh.renderer_name);
  assert(body && body.geometry.getAttribute('position').count === spec.contact_mesh.vertices,
    'Source contact body does not resolve');
  for (const patch of Object.values(spec.contacts)) {
    body.getVertexPosition(patch.minimum_vertex_id, point).applyMatrix4(body.matrixWorld);
    assert(point.distanceTo(new THREE.Vector3().fromArray(patch.minimum_vertex_native)) < 1e-4,
      'Source minimum-hoof anchor disagrees with independent decoder');
  }
  const images = new Set(), textures = new Set();
  for (const node of meshes.values()) for (const value of Object.values(node.material)) {
    if (value?.isTexture) { textures.add(value); images.add(value.image); }
  }
  let estimatedBytes = 0;
  for (const image of images) {
    assert(image?.width > 0 && image?.height > 0 && Math.max(image.width, image.height) <= 1024,
      'Unreviewed horse texture dimensions');
    estimatedBytes += image.width * image.height * 4 * 4 / 3;
  }
  assert(images.size === 6 && estimatedBytes <= 24 * 1024 * 1024, 'Horse decoded texture budget exceeded');
  return { bounds: [bounds.min.toArray(), bounds.max.toArray()], meshes: meshes.size,
    textures: textures.size, estimated_texture_mip_bytes: estimatedBytes };
}

function card(row, spec) {
  return { id: row.id, sidecar: {
    name: row.name, phase: null,
    placement: { symbolic_location: row.location, position_confidence: 'reconstructed',
      position_sources: row.source_ids, position_note: row.note },
    attributes: {
      animal: { value: 'Standing horse; individual unidentified', confidence: 'reconstructed',
        sources: row.source_ids, note: 'Yard context supports horsekeeping; this individual is a reconstruction.' },
      breed_owner: { value: 'Unidentified', confidence: 'reconstructed', sources: [],
        note: 'No historical breed, owner, measured stature, coat or grooming is attested for this model.' },
      state: { value: 'Standing, unhitched, untied and unmounted', confidence: 'reconstructed', sources: [],
        note: row.animation?.enabled
          ? 'Gentle head/tail idle is reconstructed; no independent ear, body weight shift, walking, halter, tie rope, harness, rider, driver, boarding, route or physical coupling is enabled.'
          : 'Idle activation awaits qualification; no halter, tie rope, harness, rider, driver, boarding, route or physical coupling is enabled.' },
      model_credit: { value: spec.source.credit, confidence: 'attested', sources: [spec.source.id],
        note: spec.material_variants[row.material_variant].change_notice },
    },
    citations: [...row.source_ids, spec.source.id].map(source_id => ({ source_id })),
    research_note: `${row.note} Model adaptations: uniform reconstructed metre scale, source-origin wrapper,
      declared whole-root support rotation, yard placement and source-derived reconstructed head/tail idle. Original six clips never autoplay. ${spec.material_variants[row.material_variant].change_notice}`,
  } };
}

/** Original skeleton is preserved; only the declared exported head/tail leaves may animate. */
function instantiate(asset, spec, row, confidence, groundHeight, idleData) {
  const root = cloneSkinned(asset.scene);
  const clonedGeometry = new Set(), clonedMaterials = new Set(), shadowMaterials = new Set();
  let idle = null;
  const placement = new THREE.Group(), support = new THREE.Group();
  const metric = new THREE.Group(), origin = new THREE.Group();
  const retireClone = () => {
    placement.removeFromParent(); idle?.dispose(); disposeSkeletons(root);
    for (const geometry of clonedGeometry) geometry.dispose();
    for (const material of clonedMaterials) material.dispose();
    for (const material of shadowMaterials) material.dispose();
  };
  try {
    const variant = spec.material_variants[row.material_variant];
    assert(variant && ['source_native', 'organic_dielectric_v1'].includes(row.material_variant),
      'Explicit reviewed horse material variant required');
    root.traverse(node => {
      if (!node.isMesh) return;
      node.geometry = node.geometry.clone(); clonedGeometry.add(node.geometry);
      node.geometry.setAttribute('_confidence', new THREE.Float32BufferAttribute(
        new Float32Array(node.geometry.getAttribute('position').count).fill(1), 1));
      node.material = node.material.clone(); clonedMaterials.add(node.material);
      if (row.material_variant === 'organic_dielectric_v1') node.material.metalness = 0;
      confidence?.patch(node.material);
      node.customDepthMaterial = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking,
        side: node.material.side });
      node.customDistanceMaterial = new THREE.MeshDistanceMaterial({ side: node.material.side });
      for (const material of [node.customDepthMaterial, node.customDistanceMaterial]) {
        confidence?.patch(material); shadowMaterials.add(material);
      }
      node.frustumCulled = false; node.castShadow = false; node.receiveShadow = true;
    });
    placement.name = row.id; placement.userData.standingHorseId = row.id;
    placement.rotation.y = yawOf(row.bearing_deg);
    placement.position.set(row.at_local_enu_m[0], 0, -row.at_local_enu_m[1]);
    const q = row.support_quaternion_xyzw;
    assert(q?.length === 4 && q.every(Number.isFinite) && Math.abs(Math.hypot(...q) - 1) < 1e-7,
      'Invalid horse whole-root support quaternion');
    const tilt = new THREE.Vector3(0, 1, 0).applyQuaternion(new THREE.Quaternion().fromArray(q)).angleTo(new THREE.Vector3(0, 1, 0));
    assert(tilt <= THREE.MathUtils.degToRad(2), 'Horse support tilt exceeds proposed2-degree bound');
    assert(q.every((value, i) => Math.abs(value - spec.proposed_static_support_pose.local_quaternion_xyzw[i]) < 1e-12),
      'Horse support pose differs from the explicit sidecar proposal');
    support.quaternion.fromArray(q);
    metric.scale.setScalar(spec.uniform_metres_per_native_unit);
    origin.position.fromArray(spec.origin_native).multiplyScalar(-1);
    placement.add(support); support.add(metric); metric.add(origin); origin.add(root);
    placement.updateMatrixWorld(true);
    const transform = new THREE.Matrix4().makeRotationFromQuaternion(support.quaternion);
    const yaw = yawOf(row.bearing_deg), co = Math.cos(yaw), si = Math.sin(yaw);
    const points = {};
    const sample = values => values.map(v => {
      const p = new THREE.Vector3().fromArray(v).applyMatrix4(transform);
      const e = row.at_local_enu_m[0] + co * p.x + si * p.z;
      const n = row.at_local_enu_m[1] + si * p.x - co * p.z;
      const y = groundHeight(e, n, row.ground_record_id, row.ground_support_region_id);
      assert(Number.isFinite(y), 'No actual drawn yard base at horse contact sample');
      return { y: p.y, ground: y };
    });
    for (const [name, patch] of Object.entries(spec.contacts)) points[name] = sample(patch.samples_m);
    let base = -Infinity;
    for (const values of Object.values(points)) for (const p of values) base = Math.max(base, p.ground - p.y);
    const gaps = {}, allGaps = [];
    for (const [name, values] of Object.entries(points)) {
      const valuesGaps = values.map(p => base + p.y - p.ground);
      gaps[name] = Math.min(...valuesGaps); allGaps.push(...valuesGaps);
    }
    assert(Math.max(...Object.values(gaps)) <= row.support_limits.maximum_per_hoof_minimum_gap_m,
      'Actual yard surface leaves a horse foot above the proposed contact bound');
    assert(Math.min(...allGaps) >= row.support_limits.minimum_sample_clearance_m,
      'Horse contact patch penetrates actual yard ground');
    // Independently equal10mm clipped-slab metadata, same transform/base: do
    // not solve a second offset to conceal a contact-selection discrepancy.
    const slabGaps = {};
    for (const [name, patch] of Object.entries(spec.contacts)) {
      const values = sample(patch.equal_10mm_slab_samples_m);
      slabGaps[name] = Math.min(...values.map(p => base + p.y - p.ground));
    }
    assert(Math.min(...Object.values(slabGaps)) >= row.support_limits.minimum_sample_clearance_m,
      'Equal10mm source slab contradicts standing-ground clearance');
    placement.position.y = base; placement.updateMatrixWorld(true);
    if (row.animation?.enabled) {
      assert(spec.idle.enabled && row.animation.clip === spec.idle.clip && idleData,
        'Explicit qualified horse idle contract required');
      idle = createExportedHorseIdle({ T: THREE, root, clips: asset.animations,
        verifiedDerivedSha256: spec.runtime_asset.sha256, appendReceipt: idleData.receipt,
        source: idleData.source, instanceId: row.id });
    }
    return { group: placement, root, asset, row, idle, card: card(row, spec), dispose: retireClone,
      receipt: { material_variant: row.material_variant, root_y_m: base,
        support_quaternion_xyzw: q, minimum_gap_by_hoof_m: gaps,
        equal_10mm_slab_minimum_gaps_m: slabGaps, mixer_count: idle ? 1 : 0,
        autoplay: Boolean(idle), original_six_autoplay: false, idle_clip: idle?.status.clip ?? null } };
  } catch (error) { retireClone(); throw error; }
}

/** Separate skinned standing layer; NEVER enters vehicle staticBatches/wheel fitting. */
export async function createStandingHorses({ dataBase = null, sceneId, confidence, detail = 'full',
  problems = [], hostMissing = () => false, groundHeight = null } = {}) {
  const group = new THREE.Group(); group.name = 'standing-horses';
  const ray = new THREE.Raycaster(), eye = new THREE.Vector3();
  const motionPreference = globalThis.matchMedia?.('(prefers-reduced-motion: reduce)');
  let tier = detail, disposed = false, revision = 0, pending = null, active = null, abort = null;
  let manifest = null, rows = [], lastCamera = null, attemptedRevision = -1;
  const withinReach = () => {
    if (!lastCamera || !rows.length || !(REACH[tier] > 0)) return false;
    lastCamera.getWorldPosition(eye);
    return Math.hypot(eye.x - rows[0].at_local_enu_m[0],
      -eye.z - rows[0].at_local_enu_m[1]) < REACH[tier];
  };
  const retire = () => {
    if (active) { active.dispose(); disposeSource(active.asset); active = null; }
  };
  const out = { group, records: [],
    get instances() { return active ? [active] : []; },
    get ready() { return pending ?? Promise.resolve(); },
    update(camera, dt = 0, { paused = false, reducedMotion = motionPreference?.matches ?? false } = {}) {
      if (disposed || !camera) return;
      lastCamera = camera;
      if (!active) { if (withinReach()) void load(); return; }
      camera.getWorldPosition(eye);
      const distance = eye.distanceTo(active.group.position);
      active.group.visible = !confidence?.hidden?.reconstructed && distance < (REACH[tier] ?? 0);
      active.root.traverse(node => {
        if (node.isMesh) node.castShadow = active.group.visible && tier === 'full' && distance < 30;
      });
      let visible = active.group.visible && !globalThis.document?.hidden;
      for (let ancestor = group; ancestor; ancestor = ancestor.parent) visible &&= ancestor.visible;
      active.idle?.update(dt, { visible, reducedMotion, paused });
    },
    async setTier(next) {
      if (!(next in REACH) || disposed) return;
      if (next !== tier) {
        tier = next; revision++;
        if (tier === 'light') { abort?.abort(); retire(); }
      }
      if (tier !== 'light') await load();
      if (lastCamera) out.update(lastCamera);
    },
    pickAt(ndc, camera) {
      if (!active?.group.visible || disposed || confidence?.hidden?.reconstructed) return null;
      for (let ancestor = group; ancestor; ancestor = ancestor.parent) if (!ancestor.visible) return null;
      group.updateMatrixWorld(true);
      // A source-rest sphere becomes stale when the selected leaves move.
      // Refresh only on selection, after the current skeleton world matrices.
      active.root.traverse(node => {
        if (node.isSkinnedMesh) { node.skeleton.update(); node.computeBoundingSphere(); }
      });
      ray.setFromCamera(ndc ?? new THREE.Vector2(), camera);
      const hit = ray.intersectObject(active.root, true)[0];
      return hit ? { id: active.row.id, record: active.card, distance: hit.distance, point: hit.point } : null;
    },
    dispose() {
      if (disposed) return;
      disposed = true; revision++; abort?.abort(); retire(); group.removeFromParent();
    },
  };
  // Scene/layer and phone-light guards precede ANY model fetch. No inherited
  //1835animal appears in another era merely because a loader is mounted.
  if (!dataBase || String(sceneId) !== '1835') return out;
  if (!groundHeight) { problems.push('standing horses: drawn yard base query unavailable'); return out; }
  try {
    const response = await fetch(new URL('transport/parked/standing-horses.json', dataBase));
    assert(response.ok, `Horse placements HTTP${response.status}`);
    manifest = await response.json();
    rows = (manifest.scenes[String(sceneId)] ?? []).filter(row => !hostMissing(row.belongs_to));
    assert(rows.length <= 1, 'First standing-horse instance budget is one'); out.records = rows;
  } catch (error) { problems.push(`standing horses: ${error.message}`); return out; }
  async function load() {
    if (disposed || tier === 'light' || active || !rows.length || !manifest || !withinReach()) return;
    if (pending) { await pending; if (!disposed && tier !== 'light' && !active) await load(); return; }
    if (attemptedRevision === revision) return; // A failed load never silently retries.
    const mine = revision; attemptedRevision = mine;
    const job = (async () => {
      let asset = null;
      try {
        const row = rows[0], model = manifest.models[row.model];
        assert(model, 'Standing-horse model not declared');
        const sidecarResponse = await fetch(new URL(model.sidecar, dataBase));
        assert(sidecarResponse.ok, `Horse sidecar HTTP${sidecarResponse.status}`);
        const spec = await sidecarResponse.json();
        if (mine !== revision || disposed || tier === 'light') return;
        abort = new AbortController();
        const file = new URL(model.file, new URL('../', import.meta.url));
        const response = await fetch(file, { signal: abort.signal });
        assert(response.ok, `Horse GLB HTTP${response.status}`);
        const bytes = await response.arrayBuffer();
        assert(bytes.byteLength <= 4 * 1024 * 1024, 'Horse download cap exceeded');
        assert(await sha256(bytes) === spec.runtime_asset.sha256, 'Horse runtime derivative hash mismatch');
        sourceHeader(bytes, spec);
        if (mine !== revision || disposed || tier === 'light') return;
        asset = await new GLTFLoader().parseAsync(bytes, new URL('.', file).href);
        const nativeReceipt = inspectNative(asset.scene, spec);
        if (mine !== revision || disposed || tier === 'light') return;
        let idleData = null;
        if (row.animation?.enabled) {
          assert(spec.idle.enabled, 'Horse idle activation is not qualified');
          const verifiedJson = async (relative, expectedSha256) => {
            const result = await fetch(new URL(relative, dataBase), { signal: abort.signal });
            assert(result.ok, `Horse idle data HTTP${result.status}`);
            const buffer = await result.arrayBuffer();
            assert(buffer.byteLength <= 128 * 1024 && await sha256(buffer) === expectedSha256,
              'Horse idle data identity/budget changed');
            return JSON.parse(new TextDecoder().decode(buffer));
          };
          const [source, receipt] = await Promise.all([
            verifiedJson(spec.idle.contract_file, spec.idle.contract_sha256),
            verifiedJson(spec.idle.append_receipt_file, spec.idle.append_receipt_sha256),
          ]);
          idleData = { source, receipt };
        }
        if (mine !== revision || disposed || tier === 'light') return;
        const candidate = instantiate(asset, spec, row, confidence, groundHeight, idleData);
        candidate.receipt.native = nativeReceipt;
        active = candidate; asset = null; group.add(active.group);
        if (lastCamera) out.update(lastCamera);
      } catch (error) {
        if (!disposed && mine === revision && error.name !== 'AbortError') problems.push(`standing horses: ${error.message}`);
      } finally { abort = null; if (asset) disposeSource(asset); }
    })();
    pending = job;
    try { await job; } finally { if (pending === job) pending = null; }
  }
  // No GLB download at the distant town spawn: update(camera) starts a single
  // lazy load only inside this tier's reach. Await out.ready after that update.
  return out;
}

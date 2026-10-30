// SPDX-License-Identifier: GPL-3.0-or-later
// Additive standing development horse; licensed canonical-metre geometry and reconstructed planted standing.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { disposeLoadedAsset } from './scene-loader.js';
import { createPlantedStandingHorseIdle, validatePlantedStandingHeader } from './standing-horse-planted-idle.js';
import { standingHorseCard as card } from './standing-horse-card.js';
import { createQuietHeadNeckStandingContract, QUIET_MODE } from './standing-horse-quiet-head-neck-idle.js';
// Trusted code pin: exact newly executed finite129 certificate, never sidecar-derived.
const quietContract = createQuietHeadNeckStandingContract({ qualificationSha256: 'badca71fb2ab7596be9447adaf01b3d035d5a59c7b844bc27b500d0a004d78a6' });
const idleContract = spec => spec.runtime_asset.source_qualification_mode === QUIET_MODE
  ? quietContract : { validateHeader: validatePlantedStandingHeader, createIdle: createPlantedStandingHorseIdle };

const REACH = { full: 70, balanced: 40, light: 0 };
const yawOf = bearing => Math.PI - bearing * Math.PI / 180;
const sha256 = async bytes => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)),
  b => b.toString(16).padStart(2, '0')).join('');
const assert = (value, message) => { if (!value) throw Error(message); };

function disposeSkeletons(root) {
  const skeletons = new Set();
  root?.traverse(node => { if (node.skeleton) skeletons.add(node.skeleton); });
  for (const skeleton of skeletons) skeleton.dispose();
}

function disposeSource(asset) {
  disposeSkeletons(asset?.scene);
  disposeLoadedAsset(asset);
}

/** Actual skinned positions in the canonical-metre rest frame; no Box3 rest-box shortcut. */
function inspectStanding(root, spec) {
  root.updateMatrixWorld(true);
  root.traverse(node => { if (node.isSkinnedMesh) node.skeleton.update(); });
  const point = new THREE.Vector3(), bounds = new THREE.Box3();
  const meshes = new Map();
  root.traverse(node => {
    if (!node.isMesh) return;
    assert(node.isSkinnedMesh && !Array.isArray(node.material), 'Expected original three skinned primitives');
    assert(node.skeleton.bones.length === 26, 'Horse joint count changed');
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
    assert(Math.abs(bounds.min.getComponent(i) - spec.runtime_bounds_m[0][i]) < 1e-4
      && Math.abs(bounds.max.getComponent(i) - spec.runtime_bounds_m[1][i]) < 1e-4,
    'Canonical standing bounds disagree with independent decoder');
  }
  const body = meshes.get(spec.contact_mesh.renderer_name);
  assert(body && body.geometry.getAttribute('position').count === spec.contact_mesh.vertices,
    'Source contact body does not resolve');
  for (const patch of Object.values(spec.contacts)) {
    body.getVertexPosition(patch.minimum_vertex_id, point).applyMatrix4(body.matrixWorld);
    assert(point.distanceTo(new THREE.Vector3().fromArray(patch.minimum_vertex_canonical_m)) < 1e-4,
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

/** Play only the explicit planted-standing26 clip; old head/tail clips are not composed. */
function instantiate(asset, spec, row, confidence, groundHeight) {
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
    metric.scale.setScalar(spec.runtime_scale_m_per_unit);
    origin.position.fromArray(spec.runtime_origin_m).multiplyScalar(-1);
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
      assert(spec.idle.enabled && row.animation.clip === spec.idle.clip,
        'Explicit qualified horse idle contract required');
      idle = idleContract(spec).createIdle({ T: THREE, root, clips: asset.animations,
        verifiedDerivedSha256: spec.runtime_asset.sha256, instanceId: row.id,
        sourceQualificationMode: spec.runtime_asset.source_qualification_mode });
    }
    return { group: placement, root, asset, row, idle, card: card(row, spec), dispose: retireClone,
      receipt: { asset_sha256: spec.runtime_asset.sha256, source_qualification_mode: spec.runtime_asset.source_qualification_mode ?? 'anatomy_r3',
        material_variant: row.material_variant, root_y_m: base,
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
      // A source-rest sphere becomes stale when the standing joints move.
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
        idleContract(spec).validateHeader(bytes, spec);
        if (mine !== revision || disposed || tier === 'light') return;
        asset = await new GLTFLoader().parseAsync(bytes, new URL('.', file).href);
        const canonicalReceipt = inspectStanding(asset.scene, spec);
        if (mine !== revision || disposed || tier === 'light') return;
        const candidate = instantiate(asset, spec, row, confidence, groundHeight);
        candidate.receipt.canonical = canonicalReceipt;
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

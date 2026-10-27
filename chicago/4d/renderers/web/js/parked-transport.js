// SPDX-License-Identifier: GPL-3.0-or-later
/** Parked authored vehicles, with the old yard vehicle retained as a light/far fallback.
 * Models are type reconstructions; neither a manufacturer's replica nor an owner is implied.
 * The GLB remains authoritative. Only its parking articulation and world placement change.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { disposeLoadedAsset } from './scene-loader.js';

const REACH = { full: 100, balanced: 65, light: 0 };
const yawOf = (bearing) => Math.PI - bearing * Math.PI / 180;

/** Candidate wheel-ring screen-size estimate, not visual/photographic acceptance.
 * Keep the reviewed near geometry within 24 m; increase that distance for a
 * larger actual drawing buffer or narrower field of view. THREE.LOD itself
 * accounts for camera zoom. The 2.5 m reserve covers the changed wheel envelope.
 */
function broughamMidDistance(camera, drawingBufferHeight) {
  if (!camera.isPerspectiveCamera || !Number.isFinite(camera.fov)
    || camera.fov <= 0 || camera.fov >= 180 || !Number.isFinite(drawingBufferHeight)
    || drawingBufferHeight <= 0) return Number.MAX_VALUE;
  const wheelChord = 0.65 * (1 - Math.cos(Math.PI / 16));
  const focalPixels = drawingBufferHeight / (2 * Math.tan(camera.fov * Math.PI / 360));
  return Math.max(24, 2.5 + focalPixels * wheelChord / 0.5);
}


/** Own this Brougham's complete body read before parsing. The native plate
 * helper uses this same path; the observed mobile FileLoader request was
 * canceled before readiness despite a decoded model. Keep manager abort/error
 * accounting, and resolve embedded relative resources from the asset directory.
 */
async function loadBrougham(file) {
  const loader = new GLTFLoader(), manager = loader.manager;
  const assetUrl = new URL(file, new URL('../', import.meta.url));
  const requestUrl = manager.resolveURL(assetUrl.href);
  manager.itemStart(requestUrl);
  try {
    const response = await fetch(requestUrl, {
      headers: loader.requestHeader,
      credentials: loader.withCredentials ? 'include' : 'same-origin',
      signal: manager.abortController.signal,
    });
    if (!response.ok) throw Error(`Brougham HTTP ${response.status}`);
    const bytes = await response.arrayBuffer();
    return await loader.parseAsync(bytes, new URL('.', assetUrl).href);
  } catch (error) {
    manager.itemError(requestUrl);
    throw error;
  } finally { manager.itemEnd(requestUrl); }
}

function card(row, manifest) {
  return { id: row.id, sidecar: {
    name: row.name, phase: null,
    ...(row.model === 'studebaker_brougham_1893' ? { change_note: 'This is a reconstructed, empty parked example based on the 1893 Studebaker Brougham catalogue design. This individual carriage, its ownership and its presence at this stop in 1904 are not attested.' } : {}),
    placement: { symbolic_location: row.location, position_confidence: 'reconstructed',
      position_sources: row.source_ids, position_note: row.note },
    attributes: {
      vehicle_type: { value: manifest.type, confidence: 'reconstructed', sources: [], note: manifest.basis },
      maker: { value: manifest.design_reference ? 'Reconstructed individual; no attested specimen' : 'Unidentified; type reconstruction', confidence: 'reconstructed', sources: [],
        note: manifest.design_reference ? 'The catalogue design is identified separately; this parked individual and its ownership are reconstructed.' : 'This model is not identified as a particular manufacturer or catalog model.' },
      ...(manifest.design_reference ? { design_reference: manifest.design_reference } : {}),
      parked: { value: 'Unoccupied and unhitched', confidence: 'reconstructed', sources: [],
        note: 'A parked example, without a driver, passengers or a claim of ownership.' },
    },
    citations: row.source_ids.map(source_id => ({ source_id })),
    research_note: `${manifest.basis} ${row.note} Liberties: ${row.liberty}.`,
  } };
}

/** Merge only static meshes sharing the SAME material, after the parking pose.
 * This preserves their GLB vertex normals/UVs/maps while avoiding a draw per hardware part.
 */
function staticBatches(root, confidence) {
  root.updateMatrixWorld(true);
  const byMaterial = new Map();
  root.traverse(node => {
    if (!node.isMesh) return;
    if (node.isSkinnedMesh || Array.isArray(node.material)) throw Error('Expected rigid single-material primitives');
    const geometry = node.geometry.clone().applyMatrix4(node.matrixWorld);
    const list = byMaterial.get(node.material) ?? [];
    list.push(geometry); byMaterial.set(node.material, list);
  });
  const group = new THREE.Group();
  try {
    for (const [material, pieces] of byMaterial) {
      const geometry = mergeGeometries(pieces, false);
      if (!geometry) throw Error('Incompatible authored mesh streams');
      geometry.setAttribute('_confidence', new THREE.Float32BufferAttribute(
        new Float32Array(geometry.getAttribute('position').count).fill(1), 1));
      confidence?.patch(material);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.castShadow = true; mesh.receiveShadow = true;
      group.add(mesh);
    }
  } catch (error) {
    group.traverse(n => n.geometry?.dispose());
    throw error;
  } finally {
    for (const pieces of byMaterial.values()) for (const geometry of pieces) geometry.dispose();
  }
  return group;
}

/** Solve the lowest actual tongue vertex against this stand's terrain, not its centerline.
 * A failed bracket keeps the legacy wagon; it never silently buries the pole.
 */
function parkTongue(root, row, terrain, base) {
  const tongue = root.getObjectByName('vehicle_tongue');
  if (!tongue) return null;
  const yaw = yawOf(row.bearing_deg), sin = Math.sin(yaw), cos = Math.cos(yaw);
  const p = new THREE.Vector3();
  const clearance = angle => {
    tongue.rotation.x = angle; root.updateMatrixWorld(true);
    let minimum = Infinity;
    tongue.traverse(node => {
      const pos = node.geometry?.getAttribute('position');
      if (!pos) return;
      for (let i = 0; i < pos.count; i++) {
        p.fromBufferAttribute(pos, i).applyMatrix4(node.matrixWorld);
        const e = row.at_local_enu_m[0] + cos * p.x + sin * p.z;
        const n = row.at_local_enu_m[1] - (-sin * p.x + cos * p.z);
        const ground = terrain.surfaceHeight(e, n);
        if (!Number.isFinite(ground)) throw Error('No terrain under parked tongue');
        minimum = Math.min(minimum, base + p.y - ground);
      }
    });
    return minimum;
  };
  let low = 0, high = Math.PI / 4;
  if (clearance(low) < 0 || clearance(high) > 0) throw Error('Parked tongue has no ground-contact bracket');
  for (let i = 0; i < 25; i++) {
    const middle = (low + high) / 2;
    if (clearance(middle) >= 0) low = middle; else high = middle;
  }
  const gap = clearance(low);
  return { angle_rad: low, minimum_clearance_m: gap };
}

export async function createParkedTransport({ dataBase, sceneId, terrain, confidence,
  detail = 'full', problems = [], hostMissing = () => false, groundHeight = null,
  getDrawingBufferHeight = () => null } = {}) {
  const group = new THREE.Group(); group.name = 'parked-transport';
  const instances = [], assets = new Map(), replacementIds = new Set();
  let tier = detail, fallback = () => {}, lastCamera = null, disposed = false, loading = null;
  const ray = new THREE.Raycaster();
  const out = { group, instances, replacementIds, records: [],
    setFallback(callback) { fallback = callback; },
    update(camera) {
      if (disposed) return;
      lastCamera = camera;
      for (const instance of instances) {
        const visible = (REACH[tier] ?? REACH.full) > 0
          && camera.position.distanceTo(instance.group.position) < REACH[tier];
        instance.group.visible = visible;
        if (instance.lod) {
          camera.updateWorldMatrix(true, false);
          instance.lod.updateWorldMatrix(true, false);
          instance.lod.levels[1].distance = broughamMidDistance(camera, getDrawingBufferHeight());
          instance.lod.update(camera);
          instance.active_lod = instance.lod.getCurrentLevel() === 0 ? 'near' : 'mid';
          instance.active_triangles = instance.active_lod === 'near' ? 45338 : 23062;
        }
        if (instance.row.replaces) fallback(instance.row.replaces, !visible);
      }
    },
    async setTier(next) {
      tier = next;
      if (next !== 'light') await load();
      if (lastCamera) out.update(lastCamera);
    },
    pickAt(ndc, camera) {
      if (disposed || confidence?.hidden?.reconstructed) return null;
      for (let ancestor = group; ancestor; ancestor = ancestor.parent) if (!ancestor.visible) return null;
      ray.setFromCamera(ndc ?? new THREE.Vector2(), camera);
      const hit = ray.intersectObjects(instances.filter(i => i.group.visible).map(i =>
        // Recursive raycasting visits invisible LOD children too. Start at ONLY
        // the committed active level, preserving the common parked card owner.
        i.lod ? i.lod.levels[i.lod.getCurrentLevel()].object : i.group), true)[0];
      if (!hit) return null;
      let owner = hit.object;
      while (owner && !owner.userData.parkedId) owner = owner.parent;
      const instance = instances.find(i => i.row.id === owner?.userData.parkedId);
      return instance ? { id: instance.row.id, record: instance.card, point: hit.point, distance: hit.distance } : null;
    },
    dispose() {
      disposed = true;
      for (const instance of instances) if (instance.row.replaces) fallback(instance.row.replaces, true);
      group.traverse(n => n.geometry?.dispose());
      for (const promise of assets.values()) void promise.then(disposeLoadedAsset, () => {});
      group.clear();
      instances.length = 0; replacementIds.clear();
    },
  };
  if (!dataBase || !terrain || !['1835', '1904'].includes(String(sceneId))) return out;
  const heightAt = groundHeight ?? ((e, n) => terrain.surfaceHeight(e, n));
  let record;
  try {
    const response = await fetch(new URL('transport/parked/placements.json', dataBase));
    if (!response.ok) throw Error(`Placements HTTP ${response.status}`);
    record = await response.json();
  } catch (error) { problems.push(`parked transport: ${error.message}`); return out; }
  const rows = (record.scenes[String(sceneId)] ?? []).filter(row => !hostMissing(row.belongs_to));
  for (const row of rows) if (row.replaces) replacementIds.add(row.replaces);
  out.records = rows;
  async function load() {
    if (loading || disposed) return loading;
    loading = (async () => {
      for (const row of rows) {
        if (disposed) break;
        const spec = record.models[row.model];
        try {
          let pending = assets.get(row.model);
          if (!pending) {
            pending = row.model === 'studebaker_brougham_1893' ? loadBrougham(spec.file)
              : new GLTFLoader().loadAsync(new URL(spec.file, new URL('../', import.meta.url)).href);
            assets.set(row.model, pending);
          }
          const asset = await pending;
          if (disposed) break;
          const root = asset.scene.clone(true);
          if (spec.support_file) {
            const supportKey = `${row.model}:support`;
            let support = assets.get(supportKey);
            if (!support) {
              support = new GLTFLoader().loadAsync(new URL(spec.support_file, new URL('../', import.meta.url)).href);
              assets.set(supportKey, support);
            }
            const supportAsset = await support;
            if (disposed) break;
            root.add(supportAsset.scene.clone(true));
          }
          root.updateMatrixWorld(true);
          const yaw = yawOf(row.bearing_deg), sin = Math.sin(yaw), cos = Math.cos(yaw);
          const heights = spec.wheel_contacts_m.map(([x, z]) => heightAt(
            row.at_local_enu_m[0] + cos * x + sin * z,
            row.at_local_enu_m[1] - (-sin * x + cos * z)));
          if (!heights.every(Number.isFinite)) throw Error('No ground under all four wheels');
          let base = Math.max(...heights);
          let wheelGap = base - Math.min(...heights);
          if (wheelGap > 0.03) throw Error(`Stand exceeds 30mm wheel-plane variation (${wheelGap})`);
          // A pre-authored static pole shoe is not a hinge. Qualify its actual support
          // points on the SAME rendered surface provider as the four wheel contacts.
          let staticSupport = null;
          if (spec.static_support_contacts_m) {
            const contacts = spec.static_support_contacts_m;
            if (!Array.isArray(contacts) || !contacts.length || contacts.some(p => !Array.isArray(p) || p.length !== 3 || !p.every(Number.isFinite))) throw Error('Invalid static support contacts');
            const supportGrounds = contacts.map(([x, y, z]) => heightAt(
              row.at_local_enu_m[0] + cos * x + sin * z,
              row.at_local_enu_m[1] - (-sin * x + cos * z)));
            // Missing carriageway is null; reject BEFORE subtraction can coerce it to zero.
            if (!supportGrounds.every(Number.isFinite)) throw Error('No rendered ground under all static support contacts');
            if (row.model === 'studebaker_brougham_1893') {
              // This rigid parked model also rests on its fixed pole shoe. Solve
              // the least vertical base clearing all four declared shoe corners
              // and wheels, then retain the SAME wheel and shoe gap limits.
              base = Math.max(base, ...contacts.map((point, index) => supportGrounds[index] - point[1]));
              wheelGap = base - Math.min(...heights);
              if (wheelGap > 0.03) throw Error(`Stand exceeds 30mm wheel-plane variation (${wheelGap})`);
            }
            const gaps = contacts.map((point, index) => base + point[1] - supportGrounds[index]);
            if (!gaps.every(Number.isFinite) || Math.min(...gaps) < -0.001 || Math.max(...gaps) > 0.03) throw Error('Static support exceeds 1mm penetration/30mm gap limits');
            staticSupport = { minimum_gap_m: Math.min(...gaps), maximum_gap_m: Math.max(...gaps) };
          }
          const parking = parkTongue(root, row, terrain, base);
          let midAsset = null;
          if (row.model === 'studebaker_brougham_1893'
            && spec.delivery_lods?.runtime_distance_selection_enabled) {
            try {
              const key = `${row.model}:mid`;
              let pendingMid = assets.get(key);
              if (!pendingMid) {
                pendingMid = loadBrougham(spec.delivery_lods.mid);
                assets.set(key, pendingMid);
              }
              midAsset = await pendingMid;
              if (disposed) break;
            } catch (error) { problems.push(`parked transport ${row.id} mid: ${error.message}; near retained`); }
          }
          const near = staticBatches(root, confidence);
          let model = near, lod = null;
          if (midAsset) {
            try {
              const mid = staticBatches(midAsset.scene.clone(true), confidence);
              lod = new THREE.LOD();
              // Selection happens with the same camera as reach/picking. Avoid
              // the renderer independently reselecting during shadow passes.
              lod.autoUpdate = false;
              lod.addLevel(near, 0);
              lod.addLevel(mid, 24, 0.05);
              near.visible = true; mid.visible = false;
              model = lod;
            } catch (error) { problems.push(`parked transport ${row.id} mid: ${error.message}; near retained`); }
          }
          model.name = row.id; model.userData.parkedId = row.id;
          model.position.set(row.at_local_enu_m[0], base, -row.at_local_enu_m[1]);
          model.rotation.y = yaw;
          model.visible = false;
          group.add(model);
          instances.push({ row, group: model, card: card(row, spec), parking,
            wheel_clearance_m: wheelGap, static_support: staticSupport, draw_batches: near.children.length,
            ...(lod ? { lod, active_lod: 'near', active_triangles: 45338 } : {}) });
        } catch (error) { problems.push(`parked transport ${row.id}: ${error.message}; ${row.replaces ? 'existing yard vehicle retained' : 'vehicle not shown'}`); }
      }
      if (lastCamera) out.update(lastCamera);
    })();
    return loading;
  }
  if (tier !== 'light') await load();
  return out;
}

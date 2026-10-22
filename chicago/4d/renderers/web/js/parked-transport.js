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

function card(row, manifest) {
  return { id: row.id, sidecar: {
    name: row.name, phase: null,
    placement: { symbolic_location: row.location, position_confidence: 'reconstructed',
      position_sources: row.source_ids, position_note: row.note },
    attributes: {
      vehicle_type: { value: manifest.type, confidence: 'reconstructed', sources: [], note: manifest.basis },
      maker: { value: 'Unidentified; type reconstruction', confidence: 'reconstructed', sources: [],
        note: 'This model is not identified as a particular manufacturer or catalog model.' },
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
  detail = 'full', problems = [], hostMissing = () => false, groundHeight = null } = {}) {
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
      const hit = ray.intersectObjects(instances.filter(i => i.group.visible).map(i => i.group), true)[0];
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
            pending = new GLTFLoader().loadAsync(new URL(spec.file, new URL('../', import.meta.url)).href);
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
          const base = Math.max(...heights);
          const wheelGap = base - Math.min(...heights);
          if (wheelGap > 0.03) throw Error(`Stand exceeds 30mm wheel-plane variation (${wheelGap})`);
          const parking = parkTongue(root, row, terrain, base);
          const model = staticBatches(root, confidence);
          model.name = row.id; model.userData.parkedId = row.id;
          model.position.set(row.at_local_enu_m[0], base, -row.at_local_enu_m[1]);
          model.rotation.y = yaw;
          model.visible = false;
          group.add(model);
          instances.push({ row, group: model, card: card(row, spec), parking,
            wheel_clearance_m: wheelGap, draw_batches: model.children.length });
        } catch (error) { problems.push(`parked transport ${row.id}: ${error.message}; ${row.replaces ? 'existing yard vehicle retained' : 'vehicle not shown'}`); }
      }
      if (lastCamera) out.update(lastCamera);
    })();
    return loading;
  }
  if (tier !== 'light') await load();
  return out;
}

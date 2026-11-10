// SPDX-License-Identifier: GPL-3.0-or-later
// Portable source-fitted tack + visible draft connections. No historical ownership,
// closed-finger grip, force simulation, or inherited certified sockets are asserted.
import * as THREE from 'three';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';

const Z = new THREE.Vector3(0, 0, 1);
const finitePoint = p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite);
const partsOf = asset => {
  const geometries = new Set(), materials = new Set(), skeletons = new Set();
  asset.scene.traverse(n => {
    if (n.geometry) geometries.add(n.geometry);
    for (const m of Array.isArray(n.material) ? n.material : n.material ? [n.material] : []) materials.add(m);
    if (n.skeleton) skeletons.add(n.skeleton);
  });
  return { geometries, materials, skeletons };
};
const releaseAsset = asset => {
  if (!asset?.scene) return;
  const owned = partsOf(asset);
  for (const skeleton of owned.skeletons) skeleton.dispose();
  for (const geometry of owned.geometries) geometry.dispose();
  for (const material of owned.materials) material.dispose();
};

/**
 * Creates makeHitch({row,vehicle,driver,horses}) for the driven-actor factory.
 * loadGLTF/loadJSON follow the app's existing asset/data URL and lifetime policy.
 * Call before the first posed frame. The original static parked assets are untouched.
 */
export function createDraftHitchFactory({ loadGLTF, loadJSON, confidence = null } = {}) {
  if (typeof loadGLTF !== 'function' || typeof loadJSON !== 'function') throw Error('draft hitch: asset and data loaders required');
  return async function makeHitch({ row, vehicle, driver, horses, parked = false }) {
    const spec = row.hitch;
    if (!spec?.harness_file || !spec.units_file || !spec.bindings_file || !spec.vehicle_binding) throw Error('draft hitch: explicit portable asset/binding specification required');
    if (horses?.length !== 2 || !vehicle?.getObjectByName || (!parked && !driver?.root)) throw Error('draft hitch: real two-horse team, driver and vehicle required');
    if (parked && (driver || spec.reins_mode !== 'unheld')) throw Error('draft hitch: an unoccupied parked team must explicitly omit driver reins');
    const pending = await Promise.allSettled([loadGLTF(spec.harness_file), loadGLTF(spec.units_file), loadJSON(spec.bindings_file)]);
    if (pending.some(x => x.status === 'rejected')) {
      for (const r of pending.slice(0, 2)) if (r.status === 'fulfilled') releaseAsset(r.value);
      throw pending.find(x => x.status === 'rejected').reason;
    }
    const [harnessAsset, unitsAsset, definition] = pending.map(x => x.value);
    const root = new THREE.Group(); root.name = `${row.id}:draft-hitch`;
    const garments = [], sharedSkeletons = new Set(), instances = new Map();
    const sourceOwned = [partsOf(harnessAsset), partsOf(unitsAsset)];
    let disposed = false, poleRestore = null, last = null;
    const originalPole = vehicle.getObjectByName(definition.vehicle_bindings[spec.vehicle_binding]?.pole_node);
    try {
      const binding = definition.vehicle_bindings[spec.vehicle_binding];
      if (!binding) throw Error('draft hitch: unknown explicit vehicle binding');
      const front = vehicle.getObjectByName(binding.front_axle_node);
      const tip = vehicle.getObjectByName(binding.tip_node);
      if (!front || !originalPole || !tip) throw Error('draft hitch: actual front axle/pole/tip hierarchy missing');
      vehicle.updateMatrixWorld(true);
      const originalParent = originalPole.parent, originalMatrix = originalPole.matrix.clone();
      let pivot = originalPole, newPivot = null;
      if (!binding.reuse_existing_pivot) {
        newPivot = new THREE.Group(); newPivot.name = `${row.id}:driving-pole-pivot`;
        const p = front.worldToLocal(vehicle.localToWorld(new THREE.Vector3(...binding.new_pivot_root_m)));
        newPivot.position.copy(p); front.add(newPivot); newPivot.updateMatrixWorld(true);
        newPivot.attach(originalPole); pivot = newPivot;
      }
      const restQuaternion = pivot.quaternion.clone();
      pivot.updateMatrixWorld(true);
      const tipLocal = pivot.worldToLocal(tip.getWorldPosition(new THREE.Vector3()));
      const poleLength = Math.hypot(tipLocal.y, tipLocal.z), poleStart = Math.atan2(tipLocal.y, tipLocal.z);
      if (poleLength < 2 || Math.abs(tipLocal.x) > 1e-5) throw Error('draft hitch: actual pole is not the qualified centreline');
      poleRestore = () => {
        if (newPivot) {
          originalParent.add(originalPole); originalPole.matrix.copy(originalMatrix);
          originalPole.matrix.decompose(originalPole.position, originalPole.quaternion, originalPole.scale);
          newPivot.removeFromParent();
        } else { pivot.quaternion.copy(restQuaternion); pivot.updateMatrix(); }
      };

      const horseState = horses.map(horse => {
        const bodies = [];
        horse.root.traverse(n => {
          if (n.isSkinnedMesh && n.geometry?.attributes?.position?.count === definition.source_body_vertex_count
            && n.material?.name === definition.source_body_material_name) bodies.push(n);
        });
        if (bodies.length !== 1) throw Error('draft hitch: actual current26 BODY primitive must be unique');
        const body = bodies[0], skeleton = body.skeleton;
        if (skeleton.bones.length !== definition.joint_names.length
          || skeleton.bones.some((bone, i) => bone.name !== definition.joint_names[i])) throw Error('draft hitch: current26 joint order differs');
        const copy = cloneSkinned(harnessAsset.scene), meshList = [];
        copy.traverse(n => { if (n.isSkinnedMesh) meshList.push(n); });
        if (meshList.length !== 1) throw Error('draft hitch: expected one source-fitted tack primitive');
        const mesh = meshList[0];
        if (mesh.skeleton.boneInverses.some((matrix, i) => matrix.elements.some((n, j) => Math.abs(n - skeleton.boneInverses[i].elements[j]) > 1e-6))) throw Error('draft hitch: inverse-bind matrices differ');
        mesh.skeleton.dispose(); mesh.bind(skeleton, new THREE.Matrix4());
        mesh.frustumCulled = false; mesh.castShadow = true; mesh.receiveShadow = true;
        if (!mesh.geometry.getAttribute('_confidence')) mesh.geometry.setAttribute('_confidence', new THREE.Float32BufferAttribute(new Float32Array(mesh.geometry.attributes.position.count).fill(1), 1));
        confidence?.patch?.(mesh.material);
        horse.root.add(mesh); garments.push(mesh); sharedSkeletons.add(skeleton);
        return { horse, body, mesh, skeleton };
      });
      vehicle.add(root);
      for (const [name, capacity] of [['unit_trace', 96], ['unit_rein', 8], ['unit_wood_bar', 8], ['unit_iron_link', 24]]) {
        const source = unitsAsset.scene.getObjectByName(name);
        if (!source?.isMesh) throw Error(`draft hitch: portable ${name} primitive absent`);
        if (!source.geometry.getAttribute('_confidence')) source.geometry.setAttribute('_confidence', new THREE.Float32BufferAttribute(new Float32Array(source.geometry.attributes.position.count).fill(1), 1));
        confidence?.patch?.(source.material);
        const mesh = new THREE.InstancedMesh(source.geometry, source.material, capacity);
        mesh.name = `${row.id}:${name}`; mesh.count = 0; mesh.frustumCulled = false;
        mesh.castShadow = true; mesh.receiveShadow = true; root.add(mesh);
        instances.set(name, { mesh, capacity, segments: [] });
      }

      const geometryPoint = (mesh, index) => mesh.getVertexPosition(index, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld);
      const bandPoint = (h, name, side) => {
        const band = definition.bands[name], index = { left: 0, top: 12, right: 24, bottom: 36 }[side];
        const a = band.first_vertex + 2 * band.segments + index;
        return geometryPoint(h.mesh, a).add(geometryPoint(h.mesh, a + band.segments)).multiplyScalar(.5);
      };
      const guide = (h, ref) => {
        const p = ref.indices.map(i => geometryPoint(h.body, i));
        const at = p[0].clone().multiplyScalar(ref.barycentric[0]).addScaledVector(p[1], ref.barycentric[1]).addScaledVector(p[2], ref.barycentric[2]);
        const normal = p[1].clone().sub(p[0]).cross(p[2].clone().sub(p[0])).normalize();
        const outward = new THREE.Vector3(...ref.rest_outward).transformDirection(h.horse.root.matrixWorld);
        if (normal.dot(outward) < 0) normal.negate();
        return at.addScaledVector(normal, ref.normal_offset_m);
      };
      const segment = (name, a, b) => instances.get(name).segments.push([a, b]);
      const chain = (name, points) => { for (let i = 1; i < points.length; i++) segment(name, points[i - 1], points[i]); };
      const frontPoint = (x, y, z) => front.localToWorld(new THREE.Vector3(x, y, z));
      const palmPoints = () => {
        if (row.driver_palm_points_m) {
          if (!finitePoint(row.driver_palm_points_m.l) || !finitePoint(row.driver_palm_points_m.r)) throw Error('draft hitch: finite actual palm surfaces required');
          return row.driver_palm_points_m;
        }
        const record = definition.palm_records.find(r => r.scene === row.scene && r.asset_id === row.driver_asset
          && r.lod === driver.lod && r.web === (spec.web_assets !== false));
        if (!record) throw Error('draft hitch: this actual driver LOD has no palm-surface binding');
        return record.points_m;
      };
      const out = {
        root,
        update() {
          if (disposed) return null;
          for (const value of instances.values()) value.segments.length = 0;
          vehicle.updateMatrixWorld(true);
          for (const h of horseState) h.skeleton.update();
          const yoke = horseState.map(h => bandPoint(h, 'full_collar', 'bottom').add(new THREE.Vector3(0, -definition.wood_yoke_radius_m, 0)));
          // Measure in the unchanged rest-pivot frame. Measuring in last frame's
          // already pitched frame would feed the correction back and oscillate.
          pivot.quaternion.copy(restQuaternion); vehicle.updateMatrixWorld(true);
          const local = yoke.map(p => pivot.worldToLocal(p.clone()));
          const span = local[1].x - local[0].x, fraction = -local[0].x / span;
          if (!Number.isFinite(fraction) || fraction < 0 || fraction > 1) throw Error('draft hitch: pole no longer meets the yoke span');
          const targetY = local[0].y + fraction * (local[1].y - local[0].y);
          if (Math.abs(targetY) >= poleLength) throw Error('draft hitch: collar height exceeds actual pole reach');
          const pitch = poleStart - Math.asin(targetY / poleLength);
          if (Math.abs(pitch) > Math.PI / 4) throw Error('draft hitch: proposed pole lift exceeds45degrees');
          pivot.quaternion.copy(restQuaternion).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), pitch));
          vehicle.updateMatrixWorld(true);
          const poleEnd = tip.getWorldPosition(new THREE.Vector3());
          const axis = yoke[1].clone().sub(yoke[0]), t = THREE.MathUtils.clamp(poleEnd.clone().sub(yoke[0]).dot(axis) / axis.lengthSq(), 0, 1);
          const meeting = yoke[0].clone().addScaledVector(axis, t), gap = poleEnd.distanceTo(meeting);
          segment('unit_wood_bar', ...yoke); segment('unit_iron_link', poleEnd, meeting);
          yoke.forEach((p, i) => segment('unit_iron_link', p, bandPoint(horseState[i], 'full_collar', 'bottom')));
          const rootY = binding.singletree_root_y_m, rootZ = binding.singletree_root_z_m;
          const y = rootY - front.position.y, z = rootZ - front.position.z;
          const spacing = definition.team_half_spacing_m, half = definition.singletree_halfwidth_m;
          const evener = [frontPoint(-spacing, y + definition.evener_relative_y_m, z + definition.evener_relative_z_m), frontPoint(spacing, y + definition.evener_relative_y_m, z + definition.evener_relative_z_m)];
          segment('unit_wood_bar', ...evener); segment('unit_iron_link', frontPoint(0, 0, 0), evener[0].clone().add(evener[1]).multiplyScalar(.5));
          for (let hi = 0; hi < 2; hi++) {
            const h = horseState[hi], horseX = hi === 0 ? -spacing : spacing;
            const ends = [frontPoint(horseX + half, y, z), frontPoint(horseX - half, y, z)];
            segment('unit_wood_bar', ...ends);
            segment('unit_iron_link', ends[0].clone().add(ends[1]).multiplyScalar(.5), evener[hi]);
            for (const [index, side] of ['left', 'right'].entries()) {
              chain('unit_trace', [bandPoint(h, 'full_collar', side), ...definition.surface_guides[`trace_${side}`].map(ref => guide(h, ref)), ends[index]]);
              chain('unit_trace', [bandPoint(h, 'noseband', side), ...definition.surface_guides[`cheek_${side}`].map(ref => guide(h, ref)), bandPoint(h, 'pollstrap', side)]);
            }
          }
          const palms = parked ? null : palmPoints();
          if (parked) {
            // A stationary unoccupied team has no invented hand or dangling
            // simulated rein. Fitting reins to its coachman is separate work.
          } else if (row.driver_mode === 'on_foot') {
            // T-3497: a teamster on foot leads the near (left, +x) horse by a line to its bit,
            // from his hand to the nearer ring of its noseband.
            const palm = driver.root.localToWorld(new THREE.Vector3(...palms.r));
            const near = horseState[1], rings = ['left', 'right'].map(side => bandPoint(near, 'noseband', side));
            segment('unit_rein', palm, rings[0].distanceTo(palm) <= rings[1].distanceTo(palm) ? rings[0] : rings[1]);
          } else for (const h of horseState) for (const [side, key] of [['left', 'l'], ['right', 'r']]) {
            const palm = driver.root.localToWorld(new THREE.Vector3(...palms[key]));
            segment('unit_rein', palm, bandPoint(h, 'noseband', side));
          }
          const counts = {};
          for (const [name, state] of instances) {
            if (state.segments.length > state.capacity) throw Error(`draft hitch: ${name} instance capacity exceeded`);
            let i = 0;
            for (const [aWorld, bWorld] of state.segments) {
              const a = root.worldToLocal(aWorld.clone()), b = root.worldToLocal(bWorld.clone());
              const delta = b.sub(a), length = delta.length();
              if (length < 1e-7) continue;
              const rotation = new THREE.Quaternion().setFromUnitVectors(Z, delta.divideScalar(length));
              const matrix = new THREE.Matrix4().compose(a, rotation, new THREE.Vector3(1, 1, length));
              state.mesh.setMatrixAt(i++, matrix);
            }
            state.mesh.count = i; state.mesh.instanceMatrix.needsUpdate = true; counts[name] = i;
          }
          last = { pole_to_yoke_connection_m: gap, valid: gap <= .12, pole_pitch_rad: pitch,
            instance_counts: counts, original_parked_asset_changed: false,
            actual_palm_surface_endpoints: !parked, closed_finger_grip_verified: false,
            ...(parked ? { mode: 'unoccupied_parked', reins: 'not_fitted', driver_present: false } : {}),
            global_harness_body_intersection_or_world_acceptance: 'UNRUN' };
          return last;
        },
        snapshot() { return last ? structuredClone(last) : null; },
        dispose() {
          if (disposed) return;
          disposed = true; root.removeFromParent();
          for (const mesh of garments) mesh.removeFromParent();
          for (const { mesh } of instances.values()) mesh.dispose();
          poleRestore?.();
          // Materials/geometry were loaded for this hitch. The existing horses'
          // shared live skeletons are explicitly excluded from disposal.
          for (const owned of sourceOwned) {
            for (const skeleton of owned.skeletons) if (!sharedSkeletons.has(skeleton)) skeleton.dispose();
            for (const geometry of owned.geometries) geometry.dispose();
            for (const material of owned.materials) material.dispose();
          }
        },
      };
      return out;
    } catch (error) {
      root.removeFromParent(); for (const mesh of garments) mesh.removeFromParent();
      for (const { mesh } of instances.values()) mesh.dispose();
      poleRestore?.(); releaseAsset(harnessAsset); releaseAsset(unitsAsset); throw error;
    }
  };
}

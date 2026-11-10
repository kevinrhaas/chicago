// SPDX-License-Identifier: GPL-3.0-or-later
// The existing carriage's unoccupied pair: a stationary hitch, not boarding or
// a surrogate coachman. Reuses the moving team's bound horse and fitted tack.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { acquireDraftHorse } from './draft-horse-assets.js';
import { createDraftHitchFactory } from './draft-hitch.js';
import { certifiedHorseSupportDomain, fitHorseSupport } from './transport-support.js';

const digest = async bytes => [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
  .map(n => n.toString(16).padStart(2, '0')).join('');
const point = p => Array.isArray(p) && p.length === 3 && p.every(Number.isFinite);

/** Mirror only the qualified pole hinge on the genuine mid model. The carriage
 * bodies are still batched; this preserves their own delivery materials/LODs. */
function midPoleLift(vehicle, binding, id) {
  if (!vehicle) return null;
  const front = vehicle.getObjectByName(binding.front_axle_node);
  const pole = vehicle.getObjectByName(binding.pole_node);
  const tip = vehicle.getObjectByName(binding.tip_node);
  if (!front || !pole || !tip || binding.reuse_existing_pivot || !point(binding.new_pivot_root_m)) {
    throw Error('parked team: actual mid pole and explicit working-height pivot required');
  }
  vehicle.updateWorldMatrix(true, true);
  const parent = pole.parent, matrix = pole.matrix.clone();
  const pivot = new THREE.Group(); pivot.name = `${id}:mid-pole-pivot`;
  pivot.position.copy(front.worldToLocal(vehicle.localToWorld(new THREE.Vector3(...binding.new_pivot_root_m))));
  front.add(pivot); pivot.updateWorldMatrix(true, false); pivot.attach(pole);
  const rest = pivot.quaternion.clone();
  return { setPitch(radians) {
    pivot.quaternion.copy(rest).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), radians));
    pivot.updateMatrix();
  }, restore() {
    parent.add(pole); pole.matrix.copy(matrix);
    pole.matrix.decompose(pole.position, pole.quaternion, pole.scale); pivot.removeFromParent();
  } };
}

export async function createParkedDraftTeam({ row, frame, vehicle, midVehicle = null,
  dataBase, moduleBase = new URL('../', import.meta.url), heightAt, confidence } = {}) {
  const spec = row?.stationary_team;
  if (spec?.schema !== 'chicago4d_parked_draft_team_v1' || spec.reins_mode !== 'unheld'
    || spec.driver_present !== false || !point(spec.horse_offset_m)
    || !Array.isArray(spec.idle_phase_fractions) || spec.idle_phase_fractions.length !== 2
    || !spec.idle_phase_fractions.every(p => Number.isFinite(p) && p >= 0 && p < 1)
    || !(spec.team_half_spacing_m > 0) || typeof heightAt !== 'function') {
    throw Error('parked team: explicit unoccupied pair, position and rendered ground required');
  }
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const url = file => new URL(file, moduleBase).href;
  const checkedBytes = async (file, expected, base) => {
    if (!/^[a-f0-9]{64}$/.test(expected ?? '')) throw Error('parked team: immutable input hash required');
    const response = await fetch(new URL(file, base));
    if (!response.ok) throw Error(`parked team: HTTP${response.status} ${file}`);
    const bytes = await response.arrayBuffer();
    if (await digest(bytes) !== expected) throw Error(`parked team: changed bound input ${file}`);
    return bytes;
  };
  const horseSpec = spec.horse;
  let lease = null, hitch = null, midLift = null, disposed = false, last = null;
  const root = new THREE.Group(); root.name = `${row.id}:stationary-team`;
  root.visible = false;
  const horses = [];
  const updateFrame = () => {
    frame.updateWorldMatrix(true, false);
    // SkinnedMesh refreshes bindMatrixInverse in updateMatrixWorld, not in
    // Object3D.updateWorldMatrix. Its nonzero ENU transform must cancel once.
    frame.updateMatrixWorld(true);
  };
  const restore = () => {
    if (disposed) return;
    disposed = true; hitch?.dispose(); midLift?.restore();
    for (const horse of horses) {
      horse.mixer.stopAllAction(); horse.mixer.uncacheRoot(horse.root);
      const skeletons = new Set(); horse.root.traverse(n => { if (n.isSkinnedMesh) skeletons.add(n.skeleton); });
      for (const skeleton of skeletons) skeleton.dispose();
    }
    root.removeFromParent(); lease?.release();
  };
  try {
    const certificate = JSON.parse(new TextDecoder().decode(await checkedBytes(
      horseSpec.support_domain.certificate_file, horseSpec.support_domain.certificate_sha256, dataBase)));
    const domain = certifiedHorseSupportDomain(horseSpec, certificate);
    const contacts = JSON.parse(new TextDecoder().decode(await checkedBytes(
      horseSpec.contact_file, horseSpec.contact_sha256, dataBase)));
    if (contacts.schema !== 'current26_stationary_hoof_vertices_v1' || contacts.asset_sha256 !== horseSpec.sha256
      || contacts.limits?.maximum_total_tilt_deg !== 2 || contacts.limits.minimum_clearance_m !== -1e-5
      || contacts.limits.maximum_per_hoof_minimum_gap_m !== .001
      || Object.keys(contacts.feet ?? {}).sort().join(',') !== 'fore_l,fore_r,hind_l,hind_r'
      || Object.values(contacts.feet).reduce((n, ids) => n + ids.length, 0) !== 1196) {
      throw Error('parked team: original complete-hoof contact contract required');
    }
    const neutral = new THREE.Quaternion().fromArray(contacts.neutral_quaternion_xyzw);
    if (!neutral.toArray().every(Number.isFinite) || Math.abs(neutral.length() - 1) > 1e-7) throw Error('parked team: finite neutral stance required');
    lease = await acquireDraftHorse({ url: url(horseSpec.file), sha256: horseSpec.sha256,
      materialVariant: horseSpec.material_variant, loader });
    const clip = lease.asset.animations.find(a => a.name === horseSpec.idle_clip);
    if (!clip || certificate.quiet_frames !== 129) throw Error('parked team: actual certified quiet clip missing');
    root.position.fromArray(spec.horse_offset_m); frame.add(root);
    for (const side of [-1, 1]) {
      const horse = cloneSkinned(lease.asset.scene);
      horse.position.x = side * spec.team_half_spacing_m; root.add(horse);
      horse.traverse(node => {
        if (!node.isMesh) return;
        node.frustumCulled = false; node.receiveShadow = true;
        if (horseSpec.material_variant === 'organic_dielectric_v1') node.material.metalness = 0;
        if (!node.geometry.getAttribute('_confidence')) node.geometry.setAttribute('_confidence',
          new THREE.Float32BufferAttribute(new Float32Array(node.geometry.attributes.position.count).fill(1), 1));
        confidence?.patch?.(node.material);
      });
      const mixer = new THREE.AnimationMixer(horse); mixer.clipAction(clip).play();
      mixer.setTime(spec.idle_phase_fractions[side === -1 ? 0 : 1] * clip.duration);
      const entry = { root: horse, mixer, support: null }; horses.push(entry);
      updateFrame();
      const at = horse.getWorldPosition(new THREE.Vector3());
      const support = fitHorseSupport({ e: at.x, n: -at.z, yaw: frame.rotation.y, heightAt, ...domain });
      horse.position.y = support.height_m - frame.position.y;
      horse.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(...support.normal_local_xyz)).multiply(neutral);
      const tilt = new THREE.Vector3(0, 1, 0).applyQuaternion(horse.quaternion).angleTo(new THREE.Vector3(0, 1, 0));
      if (tilt > THREE.MathUtils.degToRad(contacts.limits.maximum_total_tilt_deg)) throw Error('parked team: combined standing tilt exceeds2degrees');
      updateFrame();
      const bodies = []; horse.traverse(n => {
        if (n.isSkinnedMesh && n.geometry.attributes.position.count === contacts.body_vertex_count
          && n.material.name === contacts.body_material_name) bodies.push(n);
      });
      if (bodies.length !== 1) throw Error('parked team: actual classified contact body required');
      const body = bodies[0]; body.skeleton.update();
      let correction = -Infinity;
      const gaps = {};
      for (const [limb, ids] of Object.entries(contacts.feet)) {
        gaps[limb] = [];
        for (const id of ids) {
          if (!Number.isInteger(id) || id < 0 || id >= contacts.body_vertex_count) throw Error('parked team: invalid bound foot vertex');
          const p = body.getVertexPosition(id, new THREE.Vector3()).applyMatrix4(body.matrixWorld);
          const ground = heightAt(p.x, -p.z);
          if (!Number.isFinite(ground)) throw Error('parked team: no rendered ground under a classified foot');
          const gap = p.y - ground; gaps[limb].push(gap); correction = Math.max(correction, -gap);
        }
      }
      horse.position.y += correction; updateFrame();
      const footMinimums = Object.fromEntries(Object.entries(gaps).map(([limb, values]) => [limb, Math.min(...values) + correction]));
      if (!Object.values(footMinimums).every(gap => gap >= contacts.limits.minimum_clearance_m
        && gap <= contacts.limits.maximum_per_hoof_minimum_gap_m)) throw Error('parked team: actual feet exceed standing-contact limits');
      entry.support = { ...support, total_tilt_rad: tilt,
        neutral_quaternion_xyzw: neutral.toArray(), actual_minimum_gap_by_hoof_m: footMinimums,
        classified_vertex_count: 1196, vertical_contact_correction_m: correction };
    }
    updateFrame();
    const bindings = JSON.parse(new TextDecoder().decode(await checkedBytes(
      spec.hitch.bindings_file, spec.hitch.bindings_sha256, dataBase)));
    const sources = new Map([
      [spec.hitch.harness_file, spec.hitch.harness_sha256], [spec.hitch.units_file, spec.hitch.units_sha256],
    ]);
    const makeHitch = createDraftHitchFactory({ confidence,
      loadGLTF: async file => loader.parseAsync(await checkedBytes(file, sources.get(file), moduleBase), new URL('.', url(file)).href),
      loadJSON: async file => {
        if (file !== spec.hitch.bindings_file) throw Error('parked team: unexpected binding request');
        return bindings;
      },
    });
    hitch = await makeHitch({ row: { ...row, hitch: { ...spec.hitch, reins_mode: 'unheld' } }, vehicle,
      horses, parked: true });
    frame.attach(hitch.root);
    midLift = midPoleLift(midVehicle, bindings.vehicle_bindings[spec.hitch.vehicle_binding], row.id);
    const out = { root, horses, pickRoots: [root, hitch.root], nearPole: vehicle.getObjectByName(bindings.vehicle_bindings[spec.hitch.vehicle_binding].pole_node),
      midPole: midVehicle?.getObjectByName(bindings.vehicle_bindings[spec.hitch.vehicle_binding].pole_node) ?? null,
      update(dt = 0, { paused = false, reducedMotion = false, visible = true, shadows = false } = {}) {
        if (disposed) return null;
        if (!visible && last) return last;
        const step = visible && !paused && !reducedMotion && Number.isFinite(dt) && dt > 0 ? Math.min(dt, .05) : 0;
        for (const horse of horses) {
          if (step) horse.mixer.update(step);
          horse.root.traverse(n => { if (n.isMesh) n.castShadow = visible && shadows; });
        }
        updateFrame();
        const fit = hitch.update();
        if (!fit?.valid) throw Error('parked team: pole no longer meets the actual collar yoke');
        midLift?.setPitch(fit.pole_pitch_rad);
        last = { ...fit, horse_sha256: horseSpec.sha256, idle_clip: clip.name,
          supports: horses.map(h => h.support), source_vehicle_unchanged: true,
          boarding: false, coachman_fit: false, full_surface_contact_acceptance: 'UNRUN' };
        return last;
      },
      snapshot() { return last ? structuredClone(last) : null; },
      dispose: restore,
    };
    out.update();
    root.visible = true;
    return out;
  } catch (error) { restore(); throw error; }
}

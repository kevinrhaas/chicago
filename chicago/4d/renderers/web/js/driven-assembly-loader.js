// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { HumanActor } from './humans.js';
import { resolveHumanIdentity } from './human-identity.js';
import { disposeLoadedAsset } from './scene-loader.js';
import { createDrivenAssembly, createTeamsterAssembly } from './town-transport.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
import { fitHorseSupport } from './transport-support.js';
import { createDriverLife } from './driver-life.js';
import { clothHuman } from './fabric.js';
import { loadLivery, dressInLivery } from './driver-livery.js';
import { acquireDraftHorse } from './draft-horse-assets.js';

/** Actual portable assets, never an identity/wardrobe or idle-only fallback. */
export function createDrivenAssemblyLoader({ sceneId, people, profiles = [], humanAssets,
  confidence, heightAt, horseSpec, horseSupportDomain, makeHitch, adoptPerson = () => () => {},
  moduleBase = new URL('../', import.meta.url), driverLod = 0, createWalker = null }) {
  if (!humanAssets || typeof makeHitch !== 'function') throw Error('driven assembly: portable humans and actual visible hitch loader required');
  const horseSpecCopy = { ...horseSpec };
  if (!Number.isFinite(horseSpecCopy.stride_m) || horseSpecCopy.stride_m <= 0 || !horseSpecCopy.walk_clip) throw Error('driven assembly: explicit in-place WALK travel contract required');
  if (!['source_native', 'organic_dielectric_v1'].includes(horseSpecCopy.material_variant)) throw Error('driven assembly: explicit reviewed horse material variant required');
  if (horseSpecCopy.support_domain && (!horseSupportDomain
    || horseSupportDomain.half_width_m !== horseSpecCopy.support_domain.half_width_m
    || horseSupportDomain.half_length_m !== horseSpecCopy.support_domain.half_length_m)) {
    throw Error('driven assembly: same validated support domain as route preflight required');
  }
  const horseLeases = [];
  // T-3497: the photographic farm wagon ships meshopt-compressed (EXPORT-RECEIPT.json).
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const assetURL = file => new URL(file, moduleBase).href;
  const acquireHorse = async () => {
    const lease = await acquireDraftHorse({ url: assetURL(horseSpecCopy.file), sha256: horseSpecCopy.sha256,
      materialVariant: horseSpecCopy.material_variant, loader });
    horseLeases.push(lease);
    return lease.asset;
  };
  // T-2803: a walk generated for this GLB (tools/horse_walk_v2.mjs), bound by its
  // bytes, played by travelled metres exactly as the embedded careful walk is.
  let walkClip = null;
  const acquireWalkClip = () => (walkClip ??= (async () => {
    const response = await fetch(assetURL(horseSpecCopy.walk_clip_file));
    if (!response.ok) throw Error(`driven assembly: horse walk HTTP${response.status}`);
    const bytes = await response.arrayBuffer();
    const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
      .map(n => n.toString(16).padStart(2, '0')).join('');
    if (hash !== horseSpecCopy.walk_clip_sha256) throw Error('driven assembly: horse walk clip differs from its binding');
    const clip = JSON.parse(new TextDecoder().decode(bytes));
    if (clip.schema !== 'chicago4d_inplace_walk_clip_v1' || clip.name !== horseSpecCopy.walk_clip
      || clip.model_sha256 !== horseSpecCopy.sha256 || clip.cycle_m !== horseSpecCopy.stride_m
      || !(clip.duration_s > 0) || !Array.isArray(clip.tracks) || !clip.tracks.length) throw Error('driven assembly: horse walk clip lacks the in-place travel contract');
    return new THREE.AnimationClip(clip.name, clip.duration_s, clip.tracks.map(t => t.type === 'quaternion'
      ? new THREE.QuaternionKeyframeTrack(t.name, t.times, t.values) : new THREE.VectorKeyframeTrack(t.name, t.times, t.values)));
  })().catch(error => { walkClip = null; throw error; }));
  // T-3398/T-3409: a driver's draped wardrobe (tools/human_wardrobe.py), bound by its bytes.
  const liveries = new Map();
  const acquireLivery = row => {
    if (!row.driver_livery_file) return null;
    const key = `${row.driver_livery_file}|${row.driver_livery_sha256}`;
    if (!liveries.has(key)) liveries.set(key, loadLivery(assetURL(row.driver_livery_file), row.driver_livery_sha256)
      .catch(error => { liveries.delete(key); throw error; }));
    return liveries.get(key);
  };
  const releaseHorse = template => {
    const index = horseLeases.findIndex(lease => lease.asset === template);
    if (index < 0) return;
    horseLeases.splice(index, 1)[0].release();
  };
  // The two-horse team, its distance-driven walk and its support on the ground (T-2803).
  const makeTeam = (row, template, walk) => {
    const group = new THREE.Group(); group.name = `team:${row.id}`;
    const horses = [-1, 1].map(side => {
      const root = cloneSkinned(template.scene);
      root.traverse(node => {
        if (!node.isMesh) return;
        node.frustumCulled = false;
        if (horseSpecCopy.material_variant === 'organic_dielectric_v1') node.material.metalness = 0;
      });
      root.position.set(side * row.team_half_spacing_m, 0, 0);
      group.add(root);
      const mixer = new THREE.AnimationMixer(root);
      const action = mixer.clipAction(walk).setLoop(THREE.LoopRepeat, Infinity).play();
      action.paused = true; mixer.setTime(0);
      const savedHorse = row.initial_assembly_state?.horse?.[side === -1 ? 0 : 1];
      return { root, mixer, action, distance: savedHorse?.distance_m ?? 0, prior: null, x: root.position.x };
    });
    let teamDisposed = false;
    return {
      root: group, horses,
      poseVehicle(pose) {
        if (teamDisposed) return;
        for (const horse of horses) {
          const lead = pose.rootAhead + row.horse_offset_m[2];
          horse.root.rotation.y = Math.atan2(pose.curvature * lead, 1 - pose.curvature * horse.x);
          group.updateWorldMatrix(true, true);
          const current = horse.root.getWorldPosition(new THREE.Vector3());
          const localYaw = horse.root.rotation.y;
          const support = fitHorseSupport({ e: current.x, n: -current.z,
            yaw: pose.yaw + localYaw, heightAt, ...horseSupportDomain });
          horse.root.position.y = support.height_m - pose.height;
          const tilt = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0),
            new THREE.Vector3().fromArray(support.normal_local_xyz));
          horse.root.quaternion.setFromAxisAngle(new THREE.Vector3(0, 1, 0), localYaw).multiply(tilt);
          horse.support = support;
          group.updateWorldMatrix(true, true);
          horse.root.getWorldPosition(current);
          if (horse.prior) horse.distance += current.distanceTo(horse.prior);
          horse.prior = current;
          horse.action.paused = false;
          horse.mixer.setTime((horse.distance / horseSpecCopy.stride_m % 1) * walk.duration);
          horse.action.paused = true;
        }
      },
      stop() {}, // Distance-driven mixers freeze at the existing phase, never snap to idle.
      snapshot() { return horses.map(horse => ({ distance_m: horse.distance, support: horse.support })); },
      dispose() {
        if (teamDisposed) return;
        teamDisposed = true;
        for (const horse of horses) {
          horse.mixer.stopAllAction(); horse.mixer.uncacheRoot(horse.root);
          const skeletons = new Set(); horse.root.traverse(node => { if (node.isSkinnedMesh) skeletons.add(node.skeleton); });
          for (const skeleton of skeletons) skeleton.dispose();
          horse.root.removeFromParent();
        }
        releaseHorse(template);
      },
    };
  };
  // T-3497: a team led by a teamster on foot (an 1812 army wagon). The vehicle and team are
  // loaded exactly as a driven row's; the teamster is the scene's own figure of that person,
  // made by the humans layer (his looks, his walk), towed beside the near horse's head.
  const makeTeamster = async row => {
    if (typeof createWalker !== 'function') throw Error('driven assembly: a teamster on foot needs the scene humans layer');
    if (!Array.isArray(row.driver_local_m) || row.driver_local_m.length !== 3 || !row.driver_local_m.every(Number.isFinite)) throw Error('driven assembly: teamster place beside the team required');
    const instance = { ...row.driver_instance,
      id: row.replace_human_instance ?? `hi_driver_${row.id}`, contract_version: 1, display: 'shown', scene: sceneId,
      placement: { local_e: 0, local_n: 0, heading_deg: 180, anchor: 'terrain' },
      appearance: { asset_id: row.driver_asset }, behaviour: { state: 'standing' },
      animation: { clip: 'idle', loop: true, phase: 0 }, lod: { policy: 'auto' },
    };
    const identity = resolveHumanIdentity(instance, { sceneId, people, profiles });
    let vehicle = null, walker = null, template = null, team = null, hitch = null, restore = null;
    try {
      const acquired = await Promise.allSettled([
        (async () => {
          const response = await fetch(assetURL(row.vehicle_file));
          if (!response.ok) throw Error(`driven assembly: vehicle HTTP${response.status}`);
          const bytes = await response.arrayBuffer();
          const sha256 = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(n => n.toString(16).padStart(2, '0')).join('');
          if (sha256 !== row.vehicle_glb_sha256) throw Error('driven assembly: actual vehicle differs from its row');
          return loader.parseAsync(bytes, new URL('.', assetURL(row.vehicle_file)).href);
        })(),
        acquireHorse(),
      ]);
      if (acquired[0].status === 'fulfilled') vehicle = acquired[0].value;
      if (acquired[1].status === 'fulfilled') template = acquired[1].value;
      const failed = acquired.find(result => result.status === 'rejected');
      if (failed) throw failed.reason;
      walker = createWalker(instance, identity);
      if (!walker?.root || walker.personId !== instance.person_id) throw Error('driven assembly: teamster identity differs');
      const walk = horseSpecCopy.walk_clip_file ? await acquireWalkClip()
        : template.animations.find(a => a.name === horseSpecCopy.walk_clip);
      if (!walk) throw Error('driven assembly: selected in-place WALK is missing');
      team = makeTeam(row, template, walk);
      // His lead runs from his right hand (the inside one, toward the horse) to the near
      // horse's bit; the hand is read off his bones each frame, after he has walked.
      const hitchRow = { ...row };
      const hand = () => {
        let bone = null;
        walker.body?.scene?.traverse(node => { if (!bone && node.isBone && node.name === 'hand_r') bone = node; });
        return bone;
      };
      hitchRow.driver_palm_points_m = { l: [0, 1, 0], r: [0, 1, 0] };
      const lead = { root: walker.root };
      hitch = await makeHitch({ row: hitchRow, vehicle: vehicle.scene, driver: lead, horses: team.horses });
      if (!hitch?.root || typeof hitch.update !== 'function' || typeof hitch.dispose !== 'function') throw Error('driven assembly: visible fitted hitch required');
      const updateHitch = hitch.update.bind(hitch);
      hitch.update = pose => {
        const bone = hand();
        if (bone) {
          walker.root.updateWorldMatrix(true, true);
          const p = walker.root.worldToLocal(bone.getWorldPosition(new THREE.Vector3())).toArray();
          hitchRow.driver_palm_points_m = { l: p, r: p };
        }
        return updateHitch(pose);
      };
      vehicle.scene.add(hitch.root);
      for (const part of [vehicle.scene, team.root]) part.traverse(node => {
        if (!node.isMesh || node.material?.visible === false) return;
        const geometry = node.geometry;
        if (!geometry.hasAttribute('_confidence')) geometry.setAttribute('_confidence',
          new THREE.Float32BufferAttribute(new Float32Array(geometry.getAttribute('position').count).fill(1), 1));
      });
      const assembly = createTeamsterAssembly({ root: new THREE.Group(), vehicle: vehicle.scene, walker, horse: team, hitch,
        confidence, walkerLocal_m: row.driver_local_m, horseOffset_m: row.horse_offset_m,
        disposeVehicle: () => disposeLoadedAsset(vehicle) });
      restore = adoptPerson(instance, walker);
      const dispose = assembly.dispose;
      assembly.dispose = () => { dispose(); walker.dispose(); if (restore) { restore(); restore = null; } };
      const ray = new THREE.Raycaster();
      assembly.pickDriverAt = (ndc, camera) => {
        if (walker.disposed || !walker.body) return null;
        for (let node = walker.root; node; node = node.parent) if (!node.visible) return null;
        walker.root.updateWorldMatrix(true, true); ray.setFromCamera(ndc ?? new THREE.Vector2(), camera);
        const hit = ray.intersectObject(walker.proxy, false)[0];
        return hit ? { actor: walker, personId: walker.personId, instanceId: walker.id, state: walker.state,
          identityKind: walker.identity.kind, person: walker.person, opens: 'resident_card',
          distance: hit.distance, point: hit.point.clone() } : null;
      };
      return assembly;
    } catch (error) {
      hitch?.dispose(); team?.dispose(); walker?.dispose();
      if (template && !team) releaseHorse(template);
      if (vehicle) disposeLoadedAsset(vehicle);
      restore?.(); throw error;
    }
  };
  return async row => {
    if (row.scene !== sceneId) throw Error('driven assembly: wrong scene');
    if (row.driver_mode === 'on_foot') return makeTeamster(row);
    const driverClip = row.driver_clip ?? 'sit_drive';
    if (!['sit_drive', 'sit_drive_look_v2'].includes(driverClip)) throw Error('driven assembly: explicit qualified seated driver clip required');
    const instance = { ...row.driver_instance,
      id: row.replace_human_instance ?? `hi_driver_${row.id}`, contract_version: 1, display: 'shown', scene: sceneId,
      placement: { local_e: 0, local_n: 0, heading_deg: 180, anchor: 'terrain' },
      appearance: { asset_id: row.driver_asset }, behaviour: { state: 'seated' },
      animation: { clip: driverClip, loop: true, phase: 0 }, lod: { policy: 'fixed', fixed: driverLod },
    };
    const identity = resolveHumanIdentity(instance, { sceneId, people, profiles });
    let vehicle = null, actor = null, template = null, team = null, hitch = null, restore = null, inspectionLease = false;
    try {
      const binding = row.driver_binding;
      if (!binding || binding.scene !== sceneId || binding.asset_id !== row.driver_asset
        || binding.vehicle_file !== row.vehicle_file || binding.root_offset_m?.some(n => n !== 0)) throw Error('driven assembly: exact seated driver/vehicle binding required');
      // Independent portable assets start only after route/binding validation.
      // Settle every job before a failure is thrown so late successful leases
      // enter the same disposal owners as a completely successful acquisition.
      const acquired = await Promise.allSettled([
        (async () => {
          const response = await fetch(assetURL(row.vehicle_file));
          if (!response.ok) throw Error(`driven assembly: vehicle HTTP${response.status}`);
          const bytes = await response.arrayBuffer();
          const sha256 = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))].map(n => n.toString(16).padStart(2, '0')).join('');
          if (sha256 !== binding.vehicle_glb_sha256) throw Error('driven assembly: actual vehicle differs from the seated binding');
          const parsed = await loader.parseAsync(bytes, new URL('.', assetURL(row.vehicle_file)).href);
          return { vehicle: parsed, sha256 };
        })(),
        (async () => humanAssets.acquire(row.driver_asset, driverLod))(),
        acquireHorse(),
        (async () => acquireLivery(row))(),
      ]);
      if (acquired[0].status === 'fulfilled') vehicle = acquired[0].value.vehicle;
      if (acquired[1].status === 'fulfilled') inspectionLease = true;
      if (acquired[2].status === 'fulfilled') template = acquired[2].value;
      const failed = acquired.find(result => result.status === 'rejected');
      if (failed) throw failed.reason;
      const sha256 = acquired[0].value.sha256, inspected = acquired[1].value;
      const extras = inspected.parser.json.scenes?.[0]?.extras;
      const metadata = extras?.chicago4d_human;
      const study = JSON.parse(extras?.driver_study_json ?? 'null');
      if (metadata?.person_reference_scene !== sceneId || metadata.person_reference_id !== instance.person_id
        || study?.scene !== sceneId || study.person_reference_id !== instance.person_id
        || study.vehicle_sidecar_sha256 !== binding.vehicle_sidecar_sha256
        || (study.vehicle_glb_sha256 && study.vehicle_glb_sha256 !== sha256)) throw Error('driven assembly: actual exported driver identity/date/vehicle metadata differs');
      // T-3412: a driver's own face; his body stays the one his seat, reins and livery were fitted to.
      actor = new HumanActor({ instance, identity, person: identity.person, assets: humanAssets, heightAt: () => 0, tier: 'full', variation: 'face' });
      await actor.setLod(driverLod);
      humanAssets.release(row.driver_asset, driverLod); inspectionLease = false;
      if (!actor.body?.clips.has(driverClip) || !actor.play(driverClip, { fade: 0, time: 0 })) throw Error('driven assembly: real seated export absent');
      actor.body.mixer.update(0); actor.root.updateMatrixWorld(true);
      for (const mesh of actor.body.meshes) mesh.skeleton.update();
      const seatedBounds = new THREE.Box3().setFromObject(actor.body.scene, true);
      const size = seatedBounds.getSize(new THREE.Vector3()), centre = seatedBounds.getCenter(new THREE.Vector3());
      actor.proxy.scale.set(size.x / .6, size.y, size.z / .45);
      actor.proxy.position.set(centre.x, seatedBounds.min.y, centre.z);
      // Source identity/vehicle contact proofs are explicit inputs. The loader
      // refuses a mismatched scene or asset instead of changing pose/scale to fit.
      const walk = horseSpecCopy.walk_clip_file ? await acquireWalkClip()
        : template.animations.find(a => a.name === horseSpecCopy.walk_clip);
      if (!walk) throw Error('driven assembly: selected in-place WALK is missing');
      const travel = template.parser.json.asset?.extras?.inplace_walk_source?.contract;
      if (!horseSpecCopy.walk_clip_file && (travel?.kind !== 'IN_PLACE_EXTERNAL_ACTOR_TRAVEL_REQUIRED_ONCE'
        || travel.intendedCycleDistanceM !== horseSpecCopy.stride_m
        || travel.rootZInClipM?.join(',') !== '0,0'
        || Math.abs(travel.serializedClipDurationSeconds - walk.duration) > 1e-12)) throw Error('driven assembly: actual horse clip lacks the exact external-travel-once contract');
      team = makeTeam(row, template, walk);
      if (Number.isFinite(row.initial_assembly_state?.driver?.time_s)) actor.body.mixer.setTime(row.initial_assembly_state.driver.time_s);
      // T-3398/T-3409: the driver's loose garments, skinned to his own bones; their spring
      // tails swing each frame after the clip and the driver-life layer have moved him.
      const livery = acquired[3].value;
      if (livery && (livery.asset_id !== row.driver_asset || livery.body_master_sha256 !== row.driver_livery_body_sha256)) throw Error('driven assembly: livery was draped on another body');
      const undress = livery && actor.body ? dressInLivery(actor.body, livery) : null;
      // T-1790: breathing, the ride, weight shifts, looking around and hands on the
      // reins, layered over the seated clip each frame (driver-life.js). Bound to the
      // clip's first pose; a rig that is not the contract skeleton is left as it was.
      // T-2804: the driver's plain garments read as cloth (a shader patch, no texture).
      if (actor.body?.scene) clothHuman(actor.body.scene);
      const life = actor.body?.scene && createDriverLife({ root: actor.root, scene: actor.body.scene, id: instance.person_id ?? row.id,
        faces: actor.body.faces ?? [], gaitCycle_m: horseSpecCopy.stride_m });
      let motion = { distance_m: null, curvature: 0, moving: false };
      const driver = { root: actor.root,
        update(dt, viewer = null) { actor.body?.mixer.update(dt); life?.apply(dt, motion, viewer); undress?.update?.(dt); },
        move(pose, moving) { motion = { distance_m: pose.totalDistance, curvature: pose.curvature ?? 0, moving }; },
        snapshot() { return { clip: driverClip, time_s: actor.body?.mixer.time ?? 0, life: life?.snapshot() ?? null }; },
        dispose() { undress?.(); actor.dispose(); } };
      if (driverClip === 'sit_drive_look_v2') driver.updateVisual = driver.update;
      const hitchRow = { ...row };
      const palmBindings = row.driver_palm_bindings_by_lod?.[String(driverLod)];
      const updatePalms = () => {
        if (!palmBindings) return;
        actor.root.updateWorldMatrix(true, true);
        const points = {};
        for (const side of ['l', 'r']) {
          const b = palmBindings[side], mesh = actor.body.meshes.find(node => node.name === b?.actual_body_mesh);
          if (!mesh || !Array.isArray(b.barycentric) || b.barycentric.length !== 3
            || !b.barycentric.every(Number.isFinite) || Math.abs(b.barycentric.reduce((a, n) => a + n, 0) - 1) > 1e-7
            || !Array.isArray(b.actual_triangle_indices) || b.actual_triangle_indices.length !== 3
            || !b.actual_triangle_indices.every(i => Number.isInteger(i) && i >= 0 && i < mesh.geometry.attributes.position.count)) throw Error('driven assembly: actual selected-LOD palm surface binding is invalid');
          mesh.skeleton.update();
          const point = new THREE.Vector3();
          b.actual_triangle_indices.forEach((index, i) => point.addScaledVector(
            mesh.getVertexPosition(index, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld), b.barycentric[i]));
          points[side] = actor.root.worldToLocal(point).toArray();
        }
        hitchRow.driver_palm_points_m = points;
      };
      updatePalms();
      hitch = await makeHitch({ row: hitchRow, vehicle: vehicle.scene, driver: actor, horses: team.horses });
      if (!hitch?.root || typeof hitch.update !== 'function' || typeof hitch.dispose !== 'function') throw Error('driven assembly: visible fitted hitch required');
      const updateHitch = hitch.update.bind(hitch);
      hitch.update = pose => { updatePalms(); return updateHitch(pose); };
      vehicle.scene.add(hitch.root);
      vehicle.scene.traverse(node => {
        if (!node.isMesh || node.material?.visible === false) return;
        const geometry = node.geometry;
        if (!geometry.hasAttribute('_confidence')) geometry.setAttribute('_confidence',
          new THREE.Float32BufferAttribute(new Float32Array(geometry.getAttribute('position').count).fill(1), 1));
      });
      // The separately owned horse/driver children are attached by the assembly.
      for (const part of [actor.root, team.root]) part.traverse(node => {
        if (!node.isMesh || node.material?.visible === false) return;
        const geometry = node.geometry;
        if (!geometry.hasAttribute('_confidence')) geometry.setAttribute('_confidence',
          new THREE.Float32BufferAttribute(new Float32Array(geometry.getAttribute('position').count).fill(1), 1));
      });
      const assembly = createDrivenAssembly({ vehicle: vehicle.scene, driver, horse: team, hitch,
        confidence, driverSeat_m: row.driver_seat_node_m, driverRootOffset_m: [0, 0, 0],
        horseOffset_m: row.horse_offset_m, disposeVehicle: () => disposeLoadedAsset(vehicle) });
      restore = adoptPerson(instance, actor);
      const dispose = assembly.dispose;
      assembly.dispose = () => { dispose(); if (restore) { restore(); restore = null; } };
      const ray = new THREE.Raycaster();
      assembly.pickDriverAt = (ndc, camera) => {
        if (actor.disposed || !actor.body) return null;
        for (let node = actor.root; node; node = node.parent) if (!node.visible) return null;
        actor.root.updateWorldMatrix(true, true); ray.setFromCamera(ndc ?? new THREE.Vector2(), camera);
        const hit = ray.intersectObject(actor.proxy, false)[0];
        return hit ? { actor, personId: actor.personId, instanceId: actor.id, state: actor.state,
          identityKind: actor.identity.kind, person: actor.person, opens: 'resident_card',
          distance: hit.distance, point: hit.point.clone() } : null;
      };
      return assembly;
    } catch (error) {
      if (inspectionLease) humanAssets.release(row.driver_asset, driverLod);
      hitch?.dispose(); team?.dispose(); actor?.dispose();
      if (template && !team) releaseHorse(template);
      if (vehicle) disposeLoadedAsset(vehicle);
      restore?.(); throw error;
    }
  };
}

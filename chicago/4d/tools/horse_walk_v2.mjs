// SPDX-License-Identifier: GPL-3.0-or-later
// T-2803: a working walk for the driven team's current26 horse, with a real stride.
//
// The in-place "careful walk" the team drove with covers 0.135 m a cycle, so the
// carriage was held to 0.084 m/s (a tenth of a mile an hour) to keep its hooves from
// sliding. Kevin, 2026-11-05: "The carriage is moving very slowly, might be more
// realistic if it was at a slow carriage speed". This authors a lateral-sequence walk
// (left hind, left fore, right hind, right fore, a quarter cycle apart) on the
// horse's own 26-joint rig, by two-link sagittal IK from its standing rest pose:
//
//   - stance: each hoof is planted flat and moves straight back under the body at
//     exactly the travel speed (stride = cycle * duty), so a distance-driven player
//     shows no foot slide;
//   - swing: the hoof lifts on a sine, the fore carpus and hind hock fold and the
//     fetlock tips the hoof back, then it reaches forward to the next footfall;
//   - the trunk rides a little lower than the square stand, bobbing twice a stride;
//     the neck and head nod twice a stride, as a walking horse's do.
//
// Every number below is a reconstructed authoring choice for this model, not a
// measured gait of a particular horse (liberty L-driven-town-circuits-2804).
// It writes the in-place clip the renderer plays by travelled metres, and the
// hoof-support certificate the route's ground reading needs for the longer stride.
//
//   node tools/horse_walk_v2.mjs           write both files
//   node tools/horse_walk_v2.mjs --check   regenerate in memory; refuse any byte difference
import fs from 'node:fs/promises';
import { createHash } from 'node:crypto';
const here = new URL('../', import.meta.url);
const HORSE = 'renderers/web/transport/driven/horse-current26-inplace-full.glb';
const CLIP_OUT = 'renderers/web/transport/driven/horse-walk-v2.json';
const CERT_OUT = 'data/transport/driven/current26-walk-v2-hoof-domain.json';

export const PARAMS = Object.freeze({
  cycle_m: 1.0,            // ground travelled in one full cycle of all four feet
  duty: 0.58,              // fraction of the cycle each foot carries weight
  body_drop_m: 0.07,       // the trunk carried lower than the square stand, so the legs can reach
  body_bob_m: 0.008,       // its rise and fall, twice a cycle
  lift_fore_m: 0.11, lift_hind_m: 0.085,
  fore_centre_dz_m: 0.07,  // where each stance sweep is centred, from the rest hoof (+ forward)
  hind_centre_dz_m: -0.06,
  carpus_flex_deg: 72, hock_flex_deg: 38, fetlock_swing_deg: 55, fetlock_swing_hind_deg: 40,
  neck_nod_deg: 3.0, head_nod_deg: 2.0,
  samples: 64,
  phase: { hind_l: 0, fore_l: 0.25, hind_r: 0.5, fore_r: 0.75 },
});
const LEGS = {
  fore_l: ['fore_l_shoulder', 'fore_l_elbow', 'fore_l_carpus', 'fore_l_fetlock', 'fore_l_hoof'],
  fore_r: ['fore_r_shoulder', 'fore_r_elbow', 'fore_r_carpus', 'fore_r_fetlock', 'fore_r_hoof'],
  hind_l: ['hind_l_hip', 'hind_l_stifle', 'hind_l_hock', 'hind_l_fetlock', 'hind_l_hoof'],
  hind_r: ['hind_r_hip', 'hind_r_stifle', 'hind_r_hock', 'hind_r_fetlock', 'hind_r_hoof'],
};

// --- CPU three + the pinned GLTFLoader, geometry only (as tools/test_working_driver_1904.mjs).
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const three = new URL('three.core.js', vendor).href;
const THREE = await import(three);
const data = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
async function gltfLoader() {
  const utils = {};
  for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${three}'`));
  const url = new URL('addons/loaders/GLTFLoader.js', vendor);
  const src = (await fs.readFile(url, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => {
    const name = Object.keys(utils).find(k => spec.endsWith(`/${k}.js`));
    return `from '${spec === 'three' ? three : name ? utils[name] : new URL(spec, url).href}'`;
  });
  const { GLTFLoader } = await import(data(src));
  const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
  await MeshoptDecoder.ready; globalThis.self ??= globalThis;
  return new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
}
function geometryOnly(bytes) {
  const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20 + n));
  for (const m of doc.materials ?? []) { delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    if (m.pbrMetallicRoughness) { delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; } }
  const json0 = Buffer.from(JSON.stringify(doc)), json = Buffer.concat([json0, Buffer.alloc(-json0.length & 3, 32)]);
  const bin = bytes.subarray(28 + n), out = Buffer.alloc(28 + json.length + bin.length);
  out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
  out.writeUInt32LE(json.length, 12); out.writeUInt32LE(0x4e4f534a, 16); json.copy(out, 20);
  out.writeUInt32LE(bin.length, 20 + json.length); out.writeUInt32LE(0x004e4942, 24 + json.length); bin.copy(out, 28 + json.length);
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
}
const sha256 = b => createHash('sha256').update(b).digest('hex');
const smooth = x => x * x * (3 - 2 * x);
const DEG = Math.PI / 180;
const r6 = x => Math.round(x * 1e6) / 1e6 || 0;

/** Pose the rig at cycle phase u in [0,1); returns per-leg readings. */
function poser(S, P) {
  const bone = n => S.getObjectByName(n);
  const names = [...new Set([...Object.values(LEGS).flat(), 'horse_body', 'horse_neck', 'horse_head'])];
  for (const n of names) if (!bone(n)?.isBone) throw Error(`horse walk: the current26 rig lacks ${n}`);
  S.updateMatrixWorld(true);
  const rest = Object.fromEntries(names.map(n => [n, { q: bone(n).quaternion.clone(), p: bone(n).position.clone() }]));
  const X = new THREE.Vector3(1, 0, 0);
  const lateral = Object.fromEntries(names.map(n => [n, X.clone().applyQuaternion(bone(n).getWorldQuaternion(new THREE.Quaternion()).invert())]));
  const wp = n => bone(n).getWorldPosition(new THREE.Vector3());
  const restHoof = {}, restHoofQ = {}, restFetlockToHoof = {};
  for (const [leg, chain] of Object.entries(LEGS)) {
    restHoof[leg] = wp(chain[4]); restHoofQ[leg] = bone(chain[4]).getWorldQuaternion(new THREE.Quaternion());
    restFetlockToHoof[leg] = restHoof[leg].clone().sub(wp(chain[3]));
  }
  const q = new THREE.Quaternion();
  const rotX = (n, a) => bone(n).quaternion.multiply(q.setFromAxisAngle(lateral[n], a));
  const ang = v => Math.atan2(v.z, -v.y); // 0 straight down, + toward the head
  const stride = P.cycle_m * P.duty;
  return {
    names, restHoof,
    pose(u) {
      for (const n of names) { bone(n).quaternion.copy(rest[n].q); bone(n).position.copy(rest[n].p); }
      bone('horse_body').position.y = rest.horse_body.p.y - P.body_drop_m - P.body_bob_m * Math.cos(4 * Math.PI * u);
      rotX('horse_neck', P.neck_nod_deg * DEG * Math.sin(4 * Math.PI * (u - 0.25)));
      rotX('horse_head', P.head_nod_deg * DEG * Math.sin(4 * Math.PI * (u - 0.3)));
      S.updateMatrixWorld(true);
      const legs = {};
      for (const [leg, [j0, j1, j2, j3, j4]] of Object.entries(LEGS)) {
        const fore = leg.startsWith('fore'), ph = ((u - P.phase[leg]) % 1 + 1) % 1, base = restHoof[leg];
        const cz = base.z + (fore ? P.fore_centre_dz_m : P.hind_centre_dz_m);
        let tz, ty, flex = 0, tip = 0, stance = ph < P.duty;
        if (stance) { tz = cz + stride / 2 - stride * (ph / P.duty); ty = base.y; }
        else {
          const s = (ph - P.duty) / (1 - P.duty), bell = Math.sin(Math.PI * Math.min(1, s * 1.15)) ** 1.5;
          tz = cz - stride / 2 + stride * smooth(s);
          ty = base.y + (fore ? P.lift_fore_m : P.lift_hind_m) * Math.sin(Math.PI * Math.min(1, s * 1.08)) ** 1.3;
          flex = (fore ? P.carpus_flex_deg : -P.hock_flex_deg) * DEG * bell;
          tip = (fore ? P.fetlock_swing_deg : P.fetlock_swing_hind_deg) * DEG * bell;
        }
        rotX(j2, flex); S.updateMatrixWorld(true);
        const target = new THREE.Vector3(base.x, ty, tz).sub(restFetlockToHoof[leg].clone().applyAxisAngle(X, tip));
        // Two links in the sagittal plane: j0->j1 and j1->j3 (the folded joint rides along).
        const o = wp(j0), a1 = wp(j1), a3 = wp(j3);
        const L1 = Math.hypot(a1.y - o.y, a1.z - o.z), L2 = Math.hypot(a3.y - a1.y, a3.z - a1.z);
        const dv = new THREE.Vector3(0, target.y - o.y, target.z - o.z);
        const d = THREE.MathUtils.clamp(dv.length(), Math.abs(L1 - L2) + 1e-4, L1 + L2 - 1e-4);
        const alpha = Math.acos(THREE.MathUtils.clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1));
        const knee = ang(dv) + (fore ? -alpha : alpha); // the fore elbow bends back, the hind stifle forward
        const kneeAt = new THREE.Vector3(base.x, o.y - L1 * Math.cos(knee), o.z + L1 * Math.sin(knee));
        rotX(j0, -(ang(kneeAt.clone().sub(o)) - ang(a1.clone().sub(o)))); S.updateMatrixWorld(true);
        const b1 = wp(j1);
        rotX(j1, -(ang(target.clone().sub(b1)) - ang(wp(j3).sub(b1)))); S.updateMatrixWorld(true);
        // The fetlock sets the hoof's pitch: flat (its rest attitude) in stance, tipped back in swing.
        const want = new THREE.Quaternion().setFromAxisAngle(X, tip).multiply(restHoofQ[leg]);
        const delta = want.multiply(bone(j4).getWorldQuaternion(new THREE.Quaternion()).invert());
        rotX(j3, 2 * Math.atan2(new THREE.Vector3(delta.x, delta.y, delta.z).dot(X), delta.w));
        S.updateMatrixWorld(true);
        legs[leg] = { stance, hoof: wp(j4), target_z: tz, target_y: ty, reach_m: wp(j3).distanceTo(target) };
      }
      return legs;
    },
    tracks() { return Object.fromEntries(names.map(n => [n, bone(n).quaternion.toArray()])); },
    bodyY() { return bone('horse_body').position.y; },
    bodyRest() { return rest.horse_body.p.toArray(); },
  };
}

export async function build(P = PARAMS) {
  const bytes = await fs.readFile(new URL(HORSE, here));
  const gltf = await (await gltfLoader()).parseAsync(geometryOnly(bytes), '');
  const S = gltf.scene, rig = poser(S, P);
  const frames = [];
  let stanceSlip = 0, stanceLift = 0, swingMiss = 0;
  for (let k = 0; k < P.samples; k++) {
    const legs = rig.pose(k / P.samples);
    for (const v of Object.values(legs)) {
      if (v.stance) { stanceSlip = Math.max(stanceSlip, Math.abs(v.hoof.z - v.target_z)); stanceLift = Math.max(stanceLift, Math.abs(v.hoof.y - v.target_y)); }
      else swingMiss = Math.max(swingMiss, v.reach_m);
    }
    frames.push({ tracks: rig.tracks(), bodyY: rig.bodyY() });
  }
  // The clip: one cycle in one second of clip time, sampled at `samples`, closed on its start.
  const n = frames.length, times = [...Array(n + 1).keys()].map(k => r6(k / n)), loop = [...frames, frames[0]];
  const tracks = rig.names.map(name => ({ name: `${name}.quaternion`, type: 'quaternion', times,
    values: loop.flatMap(f => f.tracks[name].map(r6)) }));
  const rb = rig.bodyRest();
  tracks.push({ name: 'horse_body.position', type: 'vector', times, values: loop.flatMap(f => [r6(rb[0]), r6(f.bodyY), r6(rb[2])]) });
  const clip = { schema: 'chicago4d_inplace_walk_clip_v1', name: 'reconstructed_current26_walk_v2', ticket: 'T-2803',
    model_sha256: sha256(bytes), duration_s: 1, cycle_m: P.cycle_m,
    contract: 'In place: play by travelled metres, time = (metres / cycle_m mod 1) * duration_s. Stance hooves move back at exactly that speed.',
    params: P, tracks };
  const clipText = JSON.stringify(clip) + '\n';

  // Hoof support domain: every vertex the hoof bones carry, skinned through the clip,
  // in the horse root's metres; padded for the support's 2-degree tilt as the
  // careful walk's certificate was (data/transport/driven/current26-hoof-support-domain.json).
  const meshes = []; S.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); });
  const hoofBones = new Set(Object.values(LEGS).map(c => c[4]));
  const seeds = meshes.map(m => {
    const ji = m.skeleton.bones.map((b, i) => hoofBones.has(b.name) ? i : -1).filter(i => i >= 0);
    const J = m.geometry.attributes.skinIndex, W = m.geometry.attributes.skinWeight, out = [];
    for (let v = 0; v < J.count; v++) for (let c = 0; c < 4; c++) if (W.getComponent(v, c) > 0 && ji.includes(J.getComponent(v, c))) { out.push(v); break; }
    return out;
  });
  const vertexCount = seeds.reduce((s, a) => s + a.length, 0);
  if (vertexCount < 100) throw Error('horse walk: hoof vertices not found');
  const mixer = new THREE.AnimationMixer(S);
  const three_clip = new THREE.AnimationClip(clip.name, 1, tracks.map(t => t.type === 'quaternion'
    ? new THREE.QuaternionKeyframeTrack(t.name, t.times, t.values) : new THREE.VectorKeyframeTrack(t.name, t.times, t.values)));
  mixer.clipAction(three_clip).play();
  const theta = 2 * DEG, v = new THREE.Vector3();
  let halfX = 0, halfZ = 0, minY = Infinity;
  const checks = 4 * P.samples;
  for (let k = 0; k < checks; k++) {
    mixer.setTime(k / checks); S.updateMatrixWorld(true);
    for (const [mi, m] of meshes.entries()) {
      m.skeleton.update();
      for (const i of seeds[mi]) {
        m.getVertexPosition(i, v).applyMatrix4(m.matrixWorld);
        const pad = Math.abs(v.y) * Math.sin(theta) + Math.hypot(v.x, v.z) * (1 - Math.cos(theta)) + 1e-5;
        halfX = Math.max(halfX, Math.abs(v.x) + pad); halfZ = Math.max(halfZ, Math.abs(v.z) + pad); minY = Math.min(minY, v.y);
      }
    }
  }
  const ceil = (x, s = 0.005) => Math.ceil(x / s) * s;
  const cert = {
    schema: 'generated_walk_hoof_domain_v1', ticket: 'T-2803',
    asset_sha256: sha256(bytes), asset_file: HORSE,
    clip_file: CLIP_OUT, clip_sha256: sha256(Buffer.from(clipText)),
    producer: 'tools/horse_walk_v2.mjs',
    sampled_phases: checks, hoof_vertices: vertexCount,
    maximum_support_tilt_deg: 2, extra_domain_numerical_allowance_m: 1e-5,
    measured_required_centered_half_width_m: r6(halfX), measured_required_centered_half_length_m: r6(halfZ),
    half_width_m: +ceil(halfX).toFixed(3), half_length_m: +ceil(halfZ).toFixed(3),
    lowest_hoof_vertex_m: r6(minY),
    // A domain about twice as long as the careful walk's is read over more of the
    // street's crown: its plane may depart from flat by 2 mm, not 1. A hoof 2 mm off a
    // plane is not visible; the 2-degree tilt bound is unchanged.
    plane_residual_limit_m: 0.002,
    stance: { maximum_hoof_slip_m: r6(stanceSlip), maximum_hoof_lift_m: r6(stanceLift), maximum_swing_reach_shortfall_m: r6(swingMiss) },
    scope: 'Skinned hoof vertices of the actual GLB through the generated in-place clip at the sampled phases, root-local metres. No terrain contact, rendered-route or photographic acceptance is claimed.',
  };
  if (cert.stance.maximum_hoof_slip_m > 1e-3 || cert.stance.maximum_hoof_lift_m > 1e-3) throw Error(`horse walk: stance hooves slide or lift: ${JSON.stringify(cert.stance)}`);
  return { clipText, certText: JSON.stringify(cert, null, 2) + '\n', cert };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const out = await build();
  if (process.argv.includes('--check')) {
    const bad = [];
    for (const [rel, text] of [[CLIP_OUT, out.clipText], [CERT_OUT, out.certText]]) {
      const have = await fs.readFile(new URL(rel, here), 'utf8').catch(() => null);
      if (have !== text) bad.push(rel);
    }
    if (bad.length) { console.error(`horse walk v2: ${bad.join(', ')} differ from what tools/horse_walk_v2.mjs writes; rerun it`); process.exit(1); }
    console.log(`horse walk v2: clip and hoof domain reproduce (stride ${PARAMS.cycle_m} m, domain ${out.cert.half_width_m} x ${out.cert.half_length_m} m, stance slip ${out.cert.stance.maximum_hoof_slip_m} m)`);
  } else {
    await fs.writeFile(new URL(CLIP_OUT, here), out.clipText);
    await fs.writeFile(new URL(CERT_OUT, here), out.certText);
    console.log(`wrote ${CLIP_OUT} and ${CERT_OUT}`, JSON.stringify(out.cert.stance), out.cert.half_width_m, out.cert.half_length_m);
  }
}

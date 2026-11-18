#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3560 (Kevin, 2026-11-17: "he should have a climb up sequence that shows him boarding that
 * applies all years"): the visitor's figure climbing up onto each vehicle's seat and down
 * again (renderers/web/js/board-climb.js, data/transport/driven/boarding.json), checked on the
 * real vehicles and the real figures of each year:
 *
 *   - every vehicle a team in any year drives has a climb, and every key's holds are on the
 *     vehicle: each foot's sole has the vehicle (or the ground) under it, each hand a surface
 *     at it;
 *   - posed on the contract skeleton (rider-pose.js reaching), each figure's ankles and hands
 *     get to their holds at every key, and no ankle goes through the vehicle between keys;
 *   - the seated key is the seat the eye goes to (loops.json passenger_local_m);
 *   - the plan: up walks from where the visitor stands (round behind from the far side when the
 *     vehicle is climbed from one side only) and then climbs; down climbs backwards and walks
 *     to the clear stand; a vehicle climbed from both sides is climbed from the visitor's;
 *   - the eye: out beside the vehicle, watching him, into the seat at the end (down: to his eye
 *     where he lands), never jumping; he is not drawn while the eye is inside him.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import('three/addons/libs/meshopt_decoder.module.js');
const B = await import('../renderers/web/js/board-climb.js');
const { createTeamRide, registerTransportInteraction, boardStand, RIDE_S } = await import('../renderers/web/js/transport-interactions.js');
const { createInteractions } = await import('../renderers/web/js/interact.js');

const ROOT = new URL('../', import.meta.url);
const read = p => JSON.parse(fs.readFileSync(new URL(p, ROOT), 'utf8'));
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks++; };
const lines = [];
const boarding = read('data/transport/driven/boarding.json');
const rows = read('data/transport/driven/loops.json').rows;

await MeshoptDecoder.ready; globalThis.self ??= globalThis;
function geometryOnly(bytes) {
  const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20 + n));
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    if (m.pbrMetallicRoughness) { delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; }
    if (m.extensions) delete m.extensions.KHR_texture_transform;
  }
  delete doc.textures; delete doc.images; delete doc.samplers;
  const json0 = Buffer.from(JSON.stringify(doc)), json = Buffer.concat([json0, Buffer.alloc(-json0.length & 3, 32)]);
  const bin = bytes.subarray(28 + n), out = Buffer.alloc(28 + json.length + bin.length);
  out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
  out.writeUInt32LE(json.length, 12); out.writeUInt32LE(0x4e4f534a, 16); json.copy(out, 20);
  out.writeUInt32LE(bin.length, 20 + json.length); out.writeUInt32LE(0x004e4942, 24 + json.length); bin.copy(out, 28 + json.length);
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
}
const loadGLB = file => new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(fs.readFileSync(new URL(file, ROOT))), '');

// The team stands at the origin facing north (transport-loop.js localToEnu at yaw = pi:
// e = -x, n = z); three's world is (e, y, -n), so the vehicle root turns by pi.
const YAW = Math.PI, HEADING = 0;
const toWorld = ([x, y, z]) => ({ e: Math.cos(YAW) * x + Math.sin(YAW) * z, n: Math.sin(YAW) * x - Math.cos(YAW) * z, y });
const local = (e, n) => [Math.cos(YAW) * e + Math.sin(YAW) * n, Math.sin(YAW) * e - Math.cos(YAW) * n];
const ray = new THREE.Raycaster();

// ---------------------------------------------------------------- every driven vehicle has a climb
const kinds = new Map();
for (const row of rows) {
  const spec = B.boardSpecFor(boarding, row);
  ok(spec, `${row.id}: a climb for ${row.vehicle_file}`);
  if (!kinds.has(spec.id)) kinds.set(spec.id, { spec, row, years: new Set() });
  kinds.get(spec.id).years.add(row.scene);
}
ok(Object.keys(boarding.figure).every(y => fs.existsSync(new URL(`assets/humans/web/${boarding.figure[y]}.lod${boarding.lod}.glb`, ROOT))), 'every year has its figure, at its level');
lines.push(`vehicles PASS: ${rows.length} driven rows, ${kinds.size} climbs (${[...kinds.values()].map(k => `${k.spec.id}: ${[...k.years].join(', ')}`).join('; ')})`);

// ---------------------------------------------------------------- mirror
{
  const k = { at: .5, face: 90, pelvis: [1, 1, 1], foot_l: [.8, .6, 1.1], foot_r: [1.1, 0, .8], hand_l: [.5, 1.5, 1], lift: { foot_r: .3 } };
  const m = B.mirrorKey(k, -1);
  ok(m.face === -90 && m.pelvis[0] === -1 && m.foot_r[0] === -.8 && m.foot_l[0] === -1.1 && m.hand_r[0] === -.5 && m.hand_l == null && m.lift.foot_l === .3,
    'a key mirrored to the right: x negated, left and right swapped, the turn reversed');
  ok(B.mirrorKey(k, 1) === k, 'the near side is the key as written');
}

for (const { spec, row, years } of kinds.values()) {
  const vehicle = (await loadGLB(`renderers/web/${row.vehicle_file}`)).scene;
  vehicle.rotation.y = YAW; vehicle.updateMatrixWorld(true);
  const solids = []; vehicle.traverse(o => { if (o.isMesh && o.visible) { o.material.side = THREE.DoubleSide; solids.push(o); } });
  const V = p => new THREE.Vector3(p.e, p.y, -p.n);
  const hit = (from, dir, far) => { ray.set(from, dir.clone().normalize()); ray.far = far; return ray.intersectObjects(solids, false)[0] ?? null; };
  const seatLocal = row.passenger_local_m;
  for (const side of spec.sides) {
    const keys = spec.keys.map(k => B.mirrorKey(k, side, side === -1 ? spec.mirror_x_m ?? 0 : 0));
    // ---- the holds are on the vehicle
    let soles = 0, holds = 0;
    for (const k of keys) {
      for (const s of ['l', 'r']) {
        const f = k[`foot_${s}`];
        if (f && !(k.air ?? []).includes(`foot_${s}`)) {
          // Under the sole: its middle, or within a few centimetres of it (a floor of boards has gaps).
          let under = f[1] <= 0.005 ? 0 : Infinity;
          if (under) for (const [dx, dz] of [[0, 0], [.04, 0], [-.04, 0], [0, .06], [0, -.06]]) {
            const p = V(toWorld([f[0] + dx, f[1], f[2] + dz]));
            under = Math.min(under, (hit(p.clone().add(new THREE.Vector3(0, .02, 0)), new THREE.Vector3(0, -1, 0), .2)?.distance ?? Infinity) - .02);
          }
          ok(under <= .05 && under >= -.03, `${spec.id} side ${side}: key ${k.at}: the ${s} sole stands on the vehicle or the ground (${(under * 100).toFixed(1)} cm under it)`);
          soles++;
        }
        const h = k[`hand_${s}`];
        if (h && !(k.air ?? []).includes(`hand_${s}`)) {
          const p = V(toWorld(h));
          let best = Infinity;
          for (const d of [[0, -1, 0], [1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1], [0, 1, 0]]) {
            const q = hit(p, new THREE.Vector3(...d), .2); if (q) best = Math.min(best, q.distance);
          }
          ok(best <= .08, `${spec.id} side ${side}: key ${k.at}: the ${s} hand holds the vehicle (${(best * 100).toFixed(1)} cm from it)`);
          holds++;
        }
      }
    }
    const last = keys.at(-1);
    ok(last.at === 1 && last.face === 0 && Math.abs(last.pelvis[0] - seatLocal[0]) < .05 && Math.abs(last.pelvis[2] - seatLocal[2]) < .1
      && last.pelvis[1] > seatLocal[1] && last.pelvis[1] - seatLocal[1] < .16,
      `${spec.id} side ${side}: the last key sits on the visitor's seat, facing ahead (pelvis ${last.pelvis.join(', ')}; seat ${seatLocal.join(', ')})`);
    lines.push(`holds PASS: ${spec.id} side ${side}: ${soles} soles on the vehicle or the ground, ${holds} hands on it`);

    // ---- each year's figure, posed through the climb
    for (const year of years) {
      const asset = boarding.figure[year];
      const gltf = await loadGLB(`assets/humans/web/${asset}.lod${boarding.lod}.glb`);
      const root = new THREE.Group(); root.add(gltf.scene); const world = new THREE.Group(); world.add(root);
      const mixer = new THREE.AnimationMixer(gltf.scene);
      const idle = gltf.animations.find(a => a.name === 'idle') ?? gltf.animations[0];
      if (idle) { mixer.clipAction(idle).play(); mixer.update(0); }
      const fig = B.bindBoardFigure(gltf.scene, root);
      ok(fig, `${asset}: the contract skeleton`);
      const plan = B.planBoard({ spec, toWorld, heading: HEADING, local, figure: { pelvis_m: fig.pelvis_m, eye_m: fig.eye_m },
        from: { ...toWorld([side * 3.2, 0, 0.6]), y: 1.6, bearing: 270, pitch: 0 }, seat: { ...toWorld(seatLocal), y: seatLocal[1] + row.passenger_eye_m },
        ground: () => 0, standable: () => true, walk_m_s: boarding.walk_m_s });
      ok(plan && plan.side === side, `${asset} on the ${spec.id}: climbed from side ${side}`);
      let worstFoot = 0, worstHand = 0, through = 0, prev = null, samples = 0;
      const bone = n => fig.pose.bones[n].getWorldPosition(new THREE.Vector3());
      for (let c = 0; c <= 1.0001; c += 1 / 120) {
        const at = B.climbPose(plan, c);
        const r = B.poseBoardFigure(fig, at);
        root.updateMatrixWorld(true);
        const ankles = { l: bone('foot_l'), r: bone('foot_r') };
        const atKey = plan.keys.find(k => Math.abs(k.at - c) < 1 / 240);
        if (atKey) for (const s of ['l', 'r']) {
          if (atKey[`foot_${s}`] && !(atKey.air ?? []).includes(`foot_${s}`)) worstFoot = Math.max(worstFoot, ankles[s].distanceTo(r.feet[s]));
          if (atKey[`hand_${s}`]) worstHand = Math.max(worstHand, bone(`hand_${s}`).distanceTo(r.hands[s]));
          if (process.env.DEBUG) console.log('key', atKey.at, s, 'shoulder', bone(`upperarm_${s}`).toArray().map(v => v.toFixed(2)).join(','), 'handT', r.hands[s].toArray().map(v => v.toFixed(2)).join(','), 'foot', ankles[s].distanceTo(r.feet[s]).toFixed(3), 'hand', bone(`hand_${s}`).distanceTo(r.hands[s]).toFixed(3), 'pelvis', r.pelvis.toArray().map(v => v.toFixed(2)).join(','));
        }
        if (prev) for (const s of ['l', 'r']) {
          // An ankle's way since the last sample: through the vehicle, unless it ends on a hold.
          const d = ankles[s].clone().sub(prev[s]), len = d.length();
          const q = len > 1e-4 ? hit(prev[s], d, len) : null;
          if (q && q.distance < len - .04) through++;
        }
        prev = ankles; samples++;
      }
      ok(worstFoot <= .03, `${asset} on the ${spec.id} side ${side}: every ankle reaches its hold at its key (worst ${(worstFoot * 100).toFixed(1)} cm short)`);
      ok(worstHand <= .05, `${asset} on the ${spec.id} side ${side}: every hand reaches its hold at its key (worst ${(worstHand * 100).toFixed(1)} cm short)`);
      ok(through === 0, `${asset} on the ${spec.id} side ${side}: no ankle goes through the vehicle between holds (${through} of ${samples * 2} steps)`);
      lines.push(`figure PASS: ${asset} (${year}) on the ${spec.id} side ${side}: ankles within ${(worstFoot * 100).toFixed(1)} cm, hands within ${(worstHand * 100).toFixed(1)} cm of their holds, none through it in ${samples} poses`);
    }
  }

  // ---------------------------------------------------------------- the plan and the eye
  const figure = { pelvis_m: .95, eye_m: 1.62 };
  const seat = { ...toWorld(seatLocal), y: seatLocal[1] + row.passenger_eye_m };
  const near = spec.sides[0];
  const upNear = B.planBoard({ spec, toWorld, heading: HEADING, local, figure, from: { ...toWorld([near * 3, 0, .5]), y: 1.6, bearing: 90, pitch: 0 }, seat, ground: () => 0 });
  const upFar = B.planBoard({ spec, toWorld, heading: HEADING, local, figure, from: { ...toWorld([-near * 3, 0, .5]), y: 1.6, bearing: 90, pitch: 0 }, seat, ground: () => 0 });
  ok(upNear.walk.length === 2 && Math.abs(upNear.seconds - (upNear.walk_m / 1.3 + spec.seconds)) < 1e-9, `${spec.id}: up from the near side walks straight to the stand, then climbs (${upNear.seconds.toFixed(1)} s)`);
  if (spec.sides.length === 1) {
    ok(upFar.side === near && upFar.walk.length === 4 && upFar.walk.slice(1, 3).every(p => local(p.e, p.n)[1] <= spec.rear_z_m + 1e-9),
      `${spec.id}: from its far side the figure walks round behind it (${upFar.walk_m.toFixed(1)} m)`);
  } else {
    ok(upFar.side === -near && upFar.walk.length === 2, `${spec.id}: climbed from either side, from the visitor's`);
  }
  for (const plan of [upNear, upFar]) {
    let last = null, jump = 0, hidden = 0;
    const n = Math.ceil(plan.seconds * 30);
    for (let i = 0; i <= n; i++) {
      const eye = B.boardEye(plan, i / n, { heading: HEADING });
      if (last) jump = Math.max(jump, Math.hypot(eye.e - last.e, eye.n - last.n, eye.y - last.y));
      if (eye.hide) hidden++;
      last = eye;
    }
    const end = B.boardEye(plan, 1, { heading: HEADING }), mid = B.boardEye(plan, .6, { heading: HEADING });
    ok(Math.hypot(end.e - seat.e, end.n - seat.n, end.y - seat.y) < 1e-6 && end.hide && Math.abs(end.bearing - HEADING) < 1e-6, `${spec.id} side ${plan.side}: the eye ends on the seat, facing ahead, the figure not drawn`);
    ok(!mid.hide && Math.hypot(mid.e - plan.watch.e, mid.n - plan.watch.n) < 1e-6, `${spec.id} side ${plan.side}: mid-climb the eye watches from beside the vehicle and the figure is drawn`);
    ok(jump < .25, `${spec.id} side ${plan.side}: the eye never jumps (at most ${(jump * 100).toFixed(1)} cm a frame at 30 fps)`);
  }
  // Down: from the seat, backwards up the climb, then a walk to the clear stand.
  const land = toWorld([near * 4.5, 0, -1]);
  const down = B.planBoard({ spec, toWorld, heading: HEADING, local, figure, seat, land, mode: 'down', ground: () => 0 });
  const d0 = B.boardAt(down, 0), d1 = B.boardAt(down, 1), dEnd = B.boardEye(down, 1, { heading: HEADING });
  ok(d0.stage === 'climb' && Math.abs(d0.face - HEADING) < 1e-6 && d1.stage === 'walk' && Math.hypot(d1.e - land.e, d1.n - land.n) < 1e-6,
    `${spec.id}: down starts seated, climbs down backwards and walks to the clear stand (${down.walk_m.toFixed(1)} m)`);
  ok(Math.hypot(dEnd.e - land.e, dEnd.n - land.n) < 1e-6 && Math.abs(dEnd.y - figure.eye_m) < 1e-6 && dEnd.hide && B.boardEye(down, 0, { heading: HEADING }).hide,
    `${spec.id}: getting down the eye goes from the seat out beside the vehicle and ends at his eye where he lands`);
  // No ground to watch from: the eye watches from where the visitor stood.
  const boxed = B.planBoard({ spec, toWorld, heading: HEADING, local, figure, from: { ...toWorld([near * 3, 0, .5]), y: 1.6, bearing: 90, pitch: 0 }, seat, ground: () => 0, standable: () => false });
  ok(boxed.watch === null && Math.hypot(B.boardEye(boxed, .6).e - boxed.from.e, B.boardEye(boxed, .6).n - boxed.from.n) < 1e-6, `${spec.id}: with no ground beside it to watch from, the eye watches from where the visitor stood`);
  lines.push(`plan PASS: ${spec.id}: up ${upNear.seconds.toFixed(1)} s from the near side, ${upFar.seconds.toFixed(1)} s from the far; down ${down.seconds.toFixed(1)} s; the eye out to watch and into the seat, never jumping`);
}

// ---------------------------------------------------------------- the ride draws the climb (transport-interactions.js)
{
  const row = rows.find(r => r.id === 'prairie_driven_brougham_loop_1904');
  const spec = B.boardSpecFor(boarding, row), figure = { pelvis_m: .95, eye_m: 1.62 };
  const yaw = YAW;
  const actor = {
    id: row.id, name: 'Carriage driver', mode: 'route', state: 'moving', visible: true, disposed: false, speed_m_s: 1.3, calls: [],
    pose: { e: 0, n: 0, yaw }, get at() { return [0, .76]; }, get heading_deg() { return HEADING; },
    toWorld: toWorld,
    stop(why) { this.calls.push(['stop', why]); this.state = 'stopped'; this.speed_m_s = 0; return true; },
    canResume() { return true; }, resume() { this.calls.push(['resume']); this.state = 'moving'; this.speed_m_s = 1.3; return true; },
    previewAt(d) { return { e: 0, n: d, yaw }; }, snapshot() { return { distance_m: 0, yaw_rad: yaw, mode: this.mode }; },
    seat() { const w = toWorld(row.passenger_local_m); return { ...w, y: w.y + row.passenger_eye_m, yaw_rad: yaw, heading_deg: HEADING }; },
    takeReins() { this.mode = 'reins'; return true; }, handBack() { this.mode = 'returning'; return true; }, drive() {},
  };
  const walker = { state: { e: -3, n: .9, eyeY: 1.6, groundY: 0, altitude: 0, stepEase: 0, bob: 0, yaw: 0, pitch: 0, flying: false },
    get bearingDeg() { return ((-this.state.yaw * 180 / Math.PI) % 360 + 360) % 360; }, apply() {},
    teleport({ local_e, local_n }) { this.state.e = local_e; this.state.n = local_n; this.state.eyeY = 1.6; } };
  let ready = false, prepared = 0, reduced = false;
  const shown = [];
  const fake = {
    prepare() { prepared++; return Promise.resolve().then(() => { ready = true; return true; }); },
    ready: () => ready,
    plan: (a, opts) => B.planBoard({ spec, toWorld, heading: HEADING, local, figure, ground: () => 0, ...opts }),
    eye: (plan, u, heading) => B.boardEye(plan, u, { heading }),
    show: (plan, u, hidden) => shown.push(plan ? { mode: plan.mode, u, hidden } : null),
  };
  const ride = createTeamRide({ visitor: () => ({ e: walker.state.e, n: walker.state.n, y: walker.state.eyeY, bearing: 90, pitch: 0 }),
    standFor: a => boardStand({ actor: a, row }), groundAt: () => 0, walkEye: () => 1.6, reducedMotion: () => reduced, boarding: fake });
  const engine = createInteractions();
  const h = registerTransportInteraction(engine, actor, { ride, vehicle: 'carriage', driver: 'coachman' });
  const step = (dt = 1 / 30) => { engine.update(dt); ride.hold(walker, { eyeHeight: 1.6 }); };
  ok(engine.act(h.thing, 'climb-up').ok, 'Climb up starts');
  ok(h.thing.running.action.steps[h.thing.running.index].label === 'Coming over' && prepared === 1, 'the first climb waits for the figure to be fetched');
  await Promise.resolve(); await Promise.resolve();
  step(); step();
  ok(ride.drawn && ride.phase === 'climbing' && actor.state === 'stopped', 'with the figure ready the team pulls up and the climb is drawn');
  const seconds = ride.climbSeconds;
  ok(Math.abs(seconds - (Math.hypot(...[0, 1].map(k => [toWorld([1.05, 0, 1.0]).e, toWorld([1.05, 0, 1.0]).n][k] - [-3, .9][k])) / 1.3 + spec.seconds)) < .05,
    `the climb takes his walk over and the climb (${seconds.toFixed(1)} s)`);
  let t = 0, mid = null;
  while (ride.phase === 'climbing' && t < 30) { step(); t += 1 / 30; if (!mid && t > seconds * .6) mid = { ...walker.state }; }
  ok(ride.phase === 'seated' && Math.abs(t - seconds) < .2, `seated when the drawn climb ends (${t.toFixed(2)} s of ${seconds.toFixed(2)})`);
  const plan = B.planBoard({ spec, toWorld, heading: HEADING, local, figure, ground: () => 0, from: { e: -3, n: .9, y: 1.6, bearing: 90, pitch: 0 }, seat: actor.seat() });
  ok(Math.hypot(mid.e - plan.watch.e, mid.n - plan.watch.n) < .05 && Math.abs(mid.pitch) > 0 && mid.pitch !== 0, 'mid-climb the visitor\'s eye watches from beside the carriage, looking at him');
  const ups = shown.filter(x => x?.mode === 'up');
  ok(ups.length > 20 && ups.every((x, i) => i === 0 || x.u >= ups[i - 1].u) && shown.at(-1) === null, 'the figure is drawn through the climb, in order, and put away once seated');
  const seat = actor.seat();
  ok(Math.hypot(walker.state.e - seat.e, walker.state.n - seat.n) < 1e-6 && Math.abs(walker.state.eyeY - seat.y) < 1e-6, 'the eye is on the seat');
  // Get down: pull up (it stands), then the drawn climb down and a walk to the clear stand.
  const stand = boardStand({ actor, row });
  shown.length = 0;
  ok(engine.act(h.thing, 'get-down').ok, 'Get down starts');
  t = 0; let downSeconds = null;
  while ((ride.actor || ride.landing) && t < 30) { step(); t += 1 / 30; if (ride.drawn && downSeconds === null) downSeconds = ride.alightSeconds; }
  ok(downSeconds > RIDE_S.alight && shown.some(x => x?.mode === 'down') && shown.at(-1) === null, `the get down is drawn (${downSeconds?.toFixed(1)} s)`);
  ok(Math.hypot(walker.state.e - stand.e, walker.state.n - stand.n) < 1e-6, 'and lands on the clear stand beside the team');
  // Released mid-climb (a year change): the figure is put away with the visitor.
  for (let i = 0; i < 3; i++) step();
  ok(engine.act(h.thing, 'climb-up').ok, 'Climb up again');
  for (let i = 0; i < 20; i++) step();
  ok(ride.drawn, 'drawn again (the figure is kept)');
  ride.release('tier');
  ok(!ride.drawn && shown.at(-1) === null && !ride.actor, 'released mid-climb, the figure goes with the visitor');
  // Reduced motion: no figure, the eye as before.
  reduced = true; for (let i = 0; i < 400 && h.thing.running; i++) step();
  if (ride.actor) ride.release('tier');
  for (let i = 0; i < 5; i++) step();
  ok(engine.act(h.thing, 'climb-up').ok, 'Climb up with reduced motion');
  step();
  ok(!ride.drawn && ride.climbSeconds === RIDE_S.climb, 'reduced motion: nothing drawn, the climb as before');
  h.dispose();
  lines.push('ride PASS: Climb up waits for the figure, pulls the team up, draws his walk and climb with the eye watching, seats him; Get down draws the climb down and lands on the clear stand; a release puts the figure away; reduced motion draws nothing');
}

for (const l of lines) console.log(l);
console.log(`board climb PASS: ${checks} checks`);

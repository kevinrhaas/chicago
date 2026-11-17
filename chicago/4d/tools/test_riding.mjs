// SPDX-License-Identifier: GPL-3.0-or-later
// T-3560: ride a horse (renderers/web/js/riding.js, saddlery.js, rider-pose.js).
//
//  - the saddle horses' data: a row in each of 1812, 1835 and 1904, its year's tack, a rider
//    figure that exists, the liberty recorded in docs/LIBERTIES.md, and the horse the driven
//    teams use (so the coat, levels and gaits are the ones T-3559 proves);
//  - the tack fitted to the real current26 horse lies ON its coat: the seat, cloth and flaps
//    never sink under the body's surface, and the seat and the stirrup bars sit where a saddle's
//    do (on the back behind the withers, the bars at its sides);
//  - the rider (the year's real figure, at its riding level of detail) seated on that tack at
//    the walk, trot, canter and gallop: every reach gets there (feet at the irons, hands at the reins, no
//    shortfall), and no part of the rider goes into the horse's body (sampled skin against the
//    horse's own surface, in the trunk's frame, at every sampled phase);
//  - the reins: walk; urged on with Shift (or the stick pushed out) to a trot, canter and gallop,
//    a pace a second, kept when let go; whoa, back from a stand, turning, wider the faster;
//  - the ground: a horse is held where any point round it is not standable or too steep, a
//    stand is found nearby when its spot is not clear, and getting down lands on the near side,
//    else the off side, else behind.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { registerHooks } from 'node:module';

const here = new URL('../', import.meta.url);
const read = rel => fs.readFileSync(new URL(rel, here));
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here).href;
const hooks = registerHooks({ resolve: (s, c, next) => s === 'three' ? { url: vendor + 'three.module.js', shortCircuit: true }
  : s.startsWith('three/addons/') ? { url: vendor + 'addons/' + s.slice(13), shortCircuit: true } : next(s, c) });
const THREE = await import(vendor + 'three.module.js');
const { clone } = await import(vendor + 'addons/utils/SkeletonUtils.js');
const { fitTack } = await import('../renderers/web/js/saddlery.js');
const { createRiderPose, saddleTargets } = await import('../renderers/web/js/rider-pose.js');
const { createHorseGait, clipFromJson } = await import('../renderers/web/js/horse-rig.js');
const riding = await import('../renderers/web/js/riding.js');
const { gltfLoader, geometryOnly } = await import('./horse_walk_v2.mjs');
const { routeFor } = await import('../renderers/web/js/transport-loop.js');
const { footprintOfPose } = await import('../renderers/web/js/team-drive.js');
const { footprintWorld } = await import('./lay_driven_wagons_1835.mjs');
hooks.deregister();

let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks++; };
const config = JSON.parse(read('data/transport/riding/saddle_horses.json'));
if (process.env.RIDING_SANITY) config.fit.iron_out_m = -.25; // a self-test: legs pulled into the barrel must fail
const loops = JSON.parse(read('data/transport/driven/loops.json'));
const spec = loops.horse_models[config.horse_model];
const YEARS = ['1812', '1835', '1904'];

// --- the data
ok(config.schema === 'chicago4d_saddle_horses_v1' && spec?.trot_clip_file && spec.lods?.far, 'the saddle horse is the driven horse, with its trot and levels');
const liberties = read('docs/LIBERTIES.md').toString();
ok(liberties.includes(`### ${config.liberty} `), `${config.liberty} recorded in docs/LIBERTIES.md`);
for (const y of YEARS) {
  const rows = config.rows.filter(r => r.scene === y);
  ok(rows.length >= 1 && rows.every(r => r.grade === 'reconstructed' && r.liberty === config.liberty && r.at.every(Number.isFinite)), `${y}: a reconstructed saddle horse`);
  ok(config.tack[y]?.saddle && config.tack[y]?.bridle, `${y}: its year's tack`);
  ok(fs.existsSync(new URL(`assets/humans/web/${config.rider.assets[y]}.lod${config.rider.lod}.glb`, here)), `${y}: the rider figure exists at its level`);
}
for (const k of ['walk_m_s', 'trot_m_s', 'back_m_s', 'turn_deg_s', 'mount_reach_m']) ok(config.ride[k] > 0, `ride.${k}`);
ok(config.ride.trot_m_s >= 2.1 && config.ride.walk_m_s <= 1.6, 'the ride\'s walk is a walk and its trot a trot (horse-rig.js paces)');

// --- the tack on the real horse, and the rider in it
const loader = await gltfLoader();
const parse = async bytes => loader.parseAsync(geometryOnly(bytes), '');
const near = await parse(read('renderers/web/' + spec.file));
const walk = clipFromJson(JSON.parse(read('renderers/web/' + spec.walk_clip_file)));
const trot = clipFromJson(JSON.parse(read('renderers/web/' + spec.trot_clip_file)));
const canter = clipFromJson(JSON.parse(read('renderers/web/' + spec.canter_clip_file)));
const gallop = clipFromJson(JSON.parse(read('renderers/web/' + spec.gallop_clip_file)));
const humans = {};
// The visitor's stand-in and every town rider's figure (tools/lay_town_riders.mjs), each seated and checked.
const assetsOf = y => [...new Set([config.rider.assets[y], ...(config.riders ?? []).filter(r => r.scene === y).map(r => r.asset)])];
for (const y of YEARS) for (const a of assetsOf(y)) humans[a] ??= await parse(read(`assets/humans/web/${a}.lod${config.rider.lod}.glb`));

const v = new THREE.Vector3(), q = new THREE.Vector3();
const report = [];
for (const y of YEARS) {
  const root = clone(near.scene);
  root.updateMatrixWorld(true);
  const bones = {}; root.traverse(n => { if (n.isBone) bones[n.name] = n; });
  const bodyRest = bones.horse_body.matrixWorld.clone();
  const tack = fitTack(root, config.tack[y]);
  const env = tack.envelope;
  const S = config.tack[y].saddle;
  // The tack lies on the coat: every vertex of the cloth, seat and flaps outside the body's surface.
  let sunk = 0, worstSunk = 0;
  tack.parts.onBody.updateMatrixWorld(true);
  tack.parts.onBody.traverse(m => {
    if (!m.isMesh || !(m.geometry.attributes.position?.count > 60)) return;
    const pos = m.geometry.attributes.position;
    for (let i = 0; i < pos.count; i += 2) {
      v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld);
      q.copy(v).sub(new THREE.Vector3(0, S.axis_y_m, 0));
      const s = q.dot(env.dir), r = Math.hypot(q.dot(env.up), q.dot(env.side));
      const phi = Math.atan2(q.dot(env.side), q.dot(env.up)) / Math.PI * 180;
      const d = env.radius(s, phi) - r;
      if (d > .002) { sunk++; worstSunk = Math.max(worstSunk, d); if (process.env.DEBUG) console.log(y, pos.count, v.toArray().map(n => n.toFixed(2)), s.toFixed(2), phi.toFixed(0), d.toFixed(3)); }
    }
  });
  ok(sunk === 0, `${y}: the saddle, cloth and flaps lie on the coat (${sunk} vertices under it, deepest ${(worstSunk * 100).toFixed(1)} cm)`);
  const seat = tack.seat(), barL = tack.stirrupBar(1), barR = tack.stirrupBar(-1);
  ok(seat.z > -.3 && seat.z < .3 && seat.y > 1.4 && seat.y < 1.75 && Math.abs(seat.x) < .01, `${y}: the seat on the back behind the withers (${seat.toArray().map(n => n.toFixed(2))})`);
  ok(barL.x > .15 && barR.x < -.15 && Math.abs(barL.y - barR.y) < .01 && barL.y < seat.y, `${y}: the stirrup bars at the saddle's two sides`);
  for (const asset of assetsOf(y)) {
  // The rider, on the year's real figure.
  const human = humans[asset];
  const actorRoot = new THREE.Group();
  const body = clone(human.scene);
  actorRoot.add(body); root.add(actorRoot);
  const idle = human.animations.find(a => a.name === 'idle');
  const hm = new THREE.AnimationMixer(body);
  if (idle) { hm.clipAction(idle).play(); hm.update(0); }
  actorRoot.updateMatrixWorld(true);
  const pose = createRiderPose(body, actorRoot);
  ok(pose, `${y} ${asset}: the rider is the contract skeleton`);
  const skinned = []; body.traverse(n => { if (n.isSkinnedMesh) skinned.push(n); });
  const gait = createHorseGait(root, { walk, walkCycle_m: spec.stride_m, trot, trotCycle_m: spec.trot_stride_m,
    canter, canterCycle_m: spec.canter_stride_m, gallop, gallopCycle_m: spec.gallop_stride_m, rest: true });
  let worstFoot = 0, worstHand = 0, worstShort = 0, inside = 0, worstInside = 0, sampled = 0; const dbg = {};
  for (const [pace, cycle] of [[config.ride.walk_m_s, spec.stride_m], [config.ride.trot_m_s, spec.trot_stride_m],
    [config.ride.canter_m_s, spec.canter_stride_m], [config.ride.gallop_m_s, spec.gallop_stride_m]]) {
    gait.advance(0, pace, 0);
    for (let k = 0; k < 8; k++) {
      gait.advance(cycle / 8, pace, 0);
      root.updateMatrixWorld(true);
      const lean = riding.leanAt(config.fit, gait.level);
      const t = saddleTargets(tack, config.fit, { lean }), w = t.world(root);
      const short = pose.apply(w);
      tack.update(t.rootFrame(root, pose));
      worstShort = Math.max(worstShort, ...Object.values(short));
      for (const s of ['l', 'r']) {
        worstFoot = Math.max(worstFoot, pose.bones[`foot_${s}`].getWorldPosition(v).distanceTo(w.feet[s]));
        worstHand = Math.max(worstHand, pose.bones[`hand_${s}`].getWorldPosition(v).distanceTo(w.hands[s]));
      }
      // The rider's skin, carried back into the trunk's rest frame (where the envelope is), against the coat.
      const back = bodyRest.clone().multiply(bones.horse_body.matrixWorld.clone().invert());
      for (const m of skinned) {
        m.skeleton.update();
        const n = m.geometry.attributes.position.count;
        for (let i = 0; i < n; i += 5) {
          m.getVertexPosition(i, v).applyMatrix4(m.matrixWorld).applyMatrix4(back);
          q.copy(v).sub(new THREE.Vector3(0, S.axis_y_m, 0));
          const s = q.dot(env.dir);
          if (s < -.6 || s > .6) continue;
          const r = Math.hypot(q.dot(env.up), q.dot(env.side)), phi = Math.atan2(q.dot(env.side), q.dot(env.up)) / Math.PI * 180;
          // Above the saddle's seat the rider sits on leather, not coat: the seat is checked by its height.
          if (Math.abs(phi) < S.seat_half_angle_deg && q.dot(env.up) > 0) continue;
          sampled++;
          const d = env.radius(s, phi) - r;
          if (d > .01) { inside++; worstInside = Math.max(worstInside, d); if (process.env.DEBUG_RIDER) { const k = `${pace} ${m.name} s${s.toFixed(1)} phi${Math.round(phi / 30) * 30} y${q.dot(env.up).toFixed(1)}`; dbg[k] = Math.max(dbg[k] ?? 0, +d.toFixed(3)); } }
        }
      }
    }
  }
  if (process.env.DEBUG_RIDER && inside) console.log(y, asset, JSON.stringify(Object.entries(dbg).sort((a, b) => b[1] - a[1]).slice(0, 25)));
  report.push(`${y} ${asset}: feet within ${(worstFoot * 100).toFixed(1)} cm of the irons, hands ${(worstHand * 100).toFixed(1)} cm of the reins, `
    + `${inside} of ${sampled} sampled skin points more than 1 cm inside the horse (deepest ${(worstInside * 100).toFixed(1)} cm)`);
  ok(worstShort === 0, `${y} ${asset}: every reach of the rider gets there at walk, trot, canter and gallop`);
  ok(worstFoot < .02 && worstHand < .02, `${y} ${asset}: feet at the irons and hands at the reins (${worstFoot.toFixed(3)}, ${worstHand.toFixed(3)} m)`);
  ok(inside === 0, `${y} ${asset}: the rider never goes into the horse at walk, trot, canter or gallop (${inside} points, deepest ${(worstInside * 100).toFixed(1)} cm)`);
  gait.advance(0, 0, .1); gait.advance(0, 0, .5);
  ok(gait.moving === 0, `${y}: a horse that stops stands in its rest pose`);
  gait.dispose(); root.remove(actorRoot);
  }
  tack.dispose();
}
console.log(report.join('\n'));

// --- the reins
const R = config.ride;
let s = { speed: 0, bearing: 0 };
for (let i = 0; i < 60; i++) s = riding.rein(s, { forward: 1, turn: 0, trot: false }, .1, R);
ok(Math.abs(s.speed - R.walk_m_s) < 1e-9 && s.bearing === 0, 'W walks on, straight');
for (let i = 0; i < 60; i++) s = riding.rein(s, { forward: 1, turn: 0, trot: true }, .1, R);
ok(Math.abs(s.speed - R.trot_m_s) < 1e-9, 'Shift+W (or the stick right up) trots');
for (let i = 0; i < 30; i++) s = riding.rein(s, { forward: 0, turn: 0, trot: false }, .1, R);
ok(s.speed === 0, 'let go: whoa');
for (let i = 0; i < 20; i++) s = riding.rein(s, { forward: -1, turn: 0, trot: false }, .1, R);
ok(Math.abs(s.speed + R.back_m_s) < 1e-9, 'S held from a stand backs');
s = { speed: R.walk_m_s, bearing: 10 };
const turned = riding.rein(s, { forward: 1, turn: 1, trot: false }, 1, R);
ok(Math.abs(turned.bearing - (10 + R.turn_deg_s)) < 1e-9, 'D turns right at the walk\'s rate');
ok(Math.abs(riding.rein({ speed: 0, bearing: 0 }, { forward: 0, turn: -1 }, 1, R).bearing - (360 - .6 * R.turn_deg_s)) < 1e-9, 'a standing horse turns on the spot, slower');
const fast = riding.rein({ speed: R.trot_m_s, bearing: 0 }, { forward: 0, turn: 0 }, .1, R);
ok(Math.abs(fast.speed - (R.trot_m_s - R.brake_m_s2 * .1)) < 1e-9, 'S from the trot pulls up, never backs at speed');
// T-3560 (Kevin, 2026-11-17: "gallop, run"): urged on through the canter to the gallop.
ok(R.canter_m_s >= 4.2 && R.canter_m_s <= 6 && R.gallop_m_s >= 6.8, 'the ride\'s canter is a canter and its gallop a gallop (horse-rig.js paces)');
s = { speed: 0, bearing: 0 };
for (let i = 0; i < 100; i++) s = riding.rein(s, { forward: 1, turn: 0, gear: 2 }, .1, R);
ok(Math.abs(s.speed - R.canter_m_s) < 1e-9, 'a canter at gear 2');
for (let i = 0; i < 100; i++) s = riding.rein(s, { forward: 1, turn: 0, gear: 3 }, .1, R);
ok(Math.abs(s.speed - R.gallop_m_s) < 1e-9, 'a gallop at gear 3');
const wide = riding.rein(s, { forward: 1, turn: 1, gear: 3 }, 1, R);
ok(Math.abs(wide.bearing - R.turn_gallop_deg_s) < 1e-9 && R.turn_gallop_deg_s < R.turn_canter_deg_s && R.turn_canter_deg_s < R.turn_trot_deg_s, 'the faster, the wider it turns');
let fromGallop = 0;
for (; s.speed > 0 && fromGallop < 100; fromGallop++) s = riding.rein(s, { forward: 0, turn: 0, gear: 3 }, .1, R);
ok(fromGallop <= 40, `let go at a gallop: pulled up in ${(fromGallop / 10).toFixed(1)} s`);
// The urging: Shift (or the stick right up) held climbs a pace a second; let go, it keeps the pace.
let u = { gear: 0 };
const urge = (urge, now, forward = 1) => (u = riding.urgeStep(u, { forward, urge, now }, R)).gear;
ok(urge(false, 0) === 0 && urge(true, .1) === 1 && urge(true, .5) === 1 && urge(true, 1.1) === 2 && urge(true, 2.1) === 3 && urge(true, 5) === 3,
  'held, Shift steps walk, trot at once, canter a second later, gallop the next, and no further');
ok(urge(false, 5.1) === 3 && urge(false, 9) === 3, 'let go of Shift: it keeps its gallop');
ok(urge(false, 9.1, 0) === 0 && urge(false, 9.2) === 0, 'let go of the reins: it stops, and walks on again');
ok(urge(true, 10) === 1 && urge(false, 10.1) === 1 && urge(true, 10.2) === 2, 'a fresh press steps up at once');
ok(Math.abs(riding.leanAt(config.fit, 3) - config.fit.lean_gallop_rad) < 1e-12 && Math.abs(riding.leanAt(config.fit, 1.5) - (config.fit.lean_trot_rad + config.fit.lean_canter_rad) / 2) < 1e-12,
  'the rider leans by the gait, blended between');

// --- frames and ground
const left = riding.horseLocal(0, 0, 0, 1, 0), ahead = riding.horseLocal(0, 0, 90, 0, 2);
ok(Math.abs(left.e + 1) < 1e-9 && Math.abs(left.n) < 1e-9, 'the near side of a horse facing north is west');
ok(Math.abs(ahead.e - 2) < 1e-9 && Math.abs(ahead.n) < 1e-9, 'ahead of a horse facing east is east');
const yawDir = b => { const y = riding.horseYaw(b); return [Math.sin(y), Math.cos(y)]; }; // world (x, z) of its +z
for (const b of [0, 90, 200]) { const [x, z] = yawDir(b); ok(Math.abs(x - Math.sin(b * Math.PI / 180)) < 1e-9 && Math.abs(-z - Math.cos(b * Math.PI / 180)) < 1e-9, `the horse faces its bearing in the world (${b} deg)`); }
const wall = (e, n) => !(e > 3 && e < 6 && n > -10 && n < 10); // a wall 3..6 m east
const ask = { standable: wall, ground: () => 0, footprint: R.footprint_m };
ok(riding.blockedAt(0, 0, 0, ask) === null, 'open ground: no hold');
ok(riding.blockedAt(2.8, 0, 0, ask) === 'in the way', 'the horse\'s flank at the wall: held');
ok(riding.blockedAt(1.8, 0, 90, ask) === 'in the way' && riding.blockedAt(1.2, 0, 90, ask) === null, 'nose into the wall: held; a step short of it: free');
ok(riding.blockedAt(0, 0, 0, { ...ask, ground: (e, n) => n * .4 }) === 'too steep', 'a bank too steep: held');
const stand = riding.findStand(4.5, 0, 0, ask);
ok(stand && !riding.blockedAt(stand.e, stand.n, stand.bearing, ask) && Math.hypot(stand.e - 4.5, stand.n) < 4, 'a horse placed in the wall is stood on the nearest open ground');
const nearSide = riding.dismountSpot({ e: 0, n: 0, bearing: 0 }, wall);
ok(nearSide.e < -1 && Math.abs(nearSide.n) < .5, 'getting down: the near side');
const offSide = riding.dismountSpot({ e: 0, n: 0, bearing: 180 }, (e, n) => wall(e, n) && !(e < -0.5 && e > -3));
ok(offSide.e < -1 === false && Math.abs(offSide.n) < .5, 'getting down: the off side when the near side is not clear');

// --- the town's riders and stabled horses (Kevin, 2026-11-17: "some appropriate number of people
// seasonally and by time of day looping around town in a horse and some stabled parked horses I could ride")
const { next: nextRiders } = await import('./lay_town_riders.mjs');
const fresh = JSON.parse(read('data/transport/riding/saddle_horses.json'));
ok(JSON.stringify(nextRiders(fresh)) === JSON.stringify(fresh), 'the riders and stabled horses are what tools/lay_town_riders.mjs writes');
ok(liberties.includes('### L-town-riders-3560 '), 'L-town-riders-3560 recorded in docs/LIBERTIES.md');
const out = (y, hour, season) => config.riders.filter(r => r.scene === y && riding.riderOut(r, hour, season)).length;
for (const [y, hour, season, want, words] of [
  ['1835', 10, 'summer', 6, 'a summer morning'], ['1835', 10, 'winter', 4, 'a winter morning'], ['1835', 19, 'summer', 2, 'a summer evening'],
  ['1835', 22, 'summer', 1, 'ten at night (the doctor)'], ['1835', 23.5, 'summer', 0, 'midnight'],
  ['1812', 10, 'summer', 4, 'a summer morning'], ['1812', 10, 'winter', 2, 'a winter morning'], ['1812', 21, 'summer', 0, 'night'],
  ['1904', 9, 'summer', 1, 'a summer morning (a groom)'], ['1904', 14, 'summer', 0, 'the afternoon'], ['1904', 9, 'winter', 0, 'winter']])
  ok(out(y, hour, season) === want, `${y}: ${want} riders out on ${words} (${out(y, hour, season)})`);
for (const r of config.riders) {
  const route = routeFor(r.route);
  ok(route.length > 300 && r.speed_m_s > 1 && r.speed_m_s < 3 && r.initial_distance_m < route.length, `${r.id}: a ${route.length.toFixed(0)} m round at ${r.speed_m_s} m/s`);
  ok(fs.existsSync(new URL(`assets/humans/web/${r.asset}.lod2.glb`, here)), `${r.id}: its figure at the far level too`);
}
for (const row of config.rows.filter(r => r.stable)) {
  const sc = JSON.parse(read(`data/sidecars/${row.scene}/${row.stable}.json`));
  const poly = footprintWorld(sc);
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > row.at[1]) !== (yj > row.at[1]) && row.at[0] < (xj - xi) * (row.at[1] - yi) / (yj - yi) + xi) inside = !inside;
  }
  const gap = Math.min(...poly.map((p, i) => { const q = poly[(i + 1) % poly.length], dx = q[0] - p[0], dy = q[1] - p[1], L2 = dx * dx + dy * dy;
    const t = Math.max(0, Math.min(1, ((row.at[0] - p[0]) * dx + (row.at[1] - p[1]) * dy) / L2)); return Math.hypot(p[0] + t * dx - row.at[0], p[1] + t * dy - row.at[1]); }));
  ok(!inside && gap > 1.5 && gap < 3, `${row.id}: tied outside its stable (${gap.toFixed(1)} m from the wall)`);
}
ok(['1812', '1835', '1904'].every(y => config.rows.filter(r => r.scene === y).length >= 2), 'every year has saddle horses at its stables beside the one where the walk begins');

// Giving way: a rider going east along the south side of a square round.
const sq = routeFor({ kind: 'path', corner_radius_m: 6, points_enu_m: [[0, 0], [200, 0], [200, 200], [0, 200]] });
const d0 = 50, p0 = sq.at(d0), east = Math.PI / 2;
const team = (e, n = 0, step = 0) => [0, 1.5, 3].map(t => footprintOfPose({ e: e + step * t, n, yaw: east }, [-1.21, -1.86, 1.75, 5.1], .3));
const sqv = (e, n) => ({ corners: [[e - .45, n - .45], [e + .45, n - .45], [e + .45, n + .45], [e - .45, n + .45]], w: e - .45, e: e + .45, s: n - .45, n: n + .45 });
const held = o => riding.riderHeld({ route: sq, distance: d0, pace: 1.4, ...o });
ok(Math.abs(p0.n) < 1e-6 && p0.forwardE > .99, 'the test rider rides east');
ok(held({ visitor: sqv(p0.e + 3, 0) }) === 'someone in the way' && held({ visitor: sqv(p0.e + 12, 0) }) === null, 'a rider pulls up for the visitor in the way, not for one well ahead');
ok(held({ teams: [team(p0.e + 6)] }) === 'a team', 'a rider pulls up behind a team standing ahead');
ok(held({ teams: [team(p0.e + 6, 0, 3)] }) === null, 'a rider follows a team going on faster ahead');
ok(held({ teams: [team(p0.e - 2)] }) === null, 'a rider already touching a team walks clear of it');
ok(held({ teams: [team(p0.e - 20)] }) === null && held({ teams: [team(p0.e + 6, 8)] }) === null, 'a team behind, or beside in its own lane, holds nobody');
const other = (e, fwd, index, pace = 0) => ({ index, at: [e, 0], fwd, prints: [0, 1.5, 3].map(t => riding.riderPrint(sq, d0 + (e - p0.e) + fwd[0] * pace * t, .15)) });
ok(held({ index: 1, others: [other(p0.e + 5, [1, 0], 0)] }) === 'a rider' && held({ index: 0, others: [other(p0.e - 5, [1, 0], 1, 1.4)] }) === null, 'the rider behind gives way to the one ahead, not the one ahead to it');
ok(held({ index: 0, others: [other(p0.e + 6, [-1, 0], 1, 1.4)] }) === null && held({ index: 1, others: [other(p0.e + 6, [-1, 0], 0, 1.4)] }) === 'a rider', 'head on, the lower index goes and the other waits');
console.log(`riding (T-3560): data, tack on the coat, rider seated without clipping, reins, holds, stands, getting down, the town's riders and stabled horses: ${checks} checks PASS`);

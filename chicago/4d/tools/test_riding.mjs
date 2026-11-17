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
//    the walk and the trot: every reach gets there (feet at the irons, hands at the reins, no
//    shortfall), and no part of the rider goes into the horse's body (sampled skin against the
//    horse's own surface, in the trunk's frame, at every sampled phase);
//  - the reins: walk, trot with Shift or the stick right up, whoa, back from a stand, turning;
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
const humans = {};
for (const y of YEARS) humans[config.rider.assets[y]] ??= await parse(read(`assets/humans/web/${config.rider.assets[y]}.lod${config.rider.lod}.glb`));

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
  // The rider, on the year's real figure.
  const human = humans[config.rider.assets[y]];
  const actorRoot = new THREE.Group();
  const body = clone(human.scene);
  actorRoot.add(body); root.add(actorRoot);
  const idle = human.animations.find(a => a.name === 'idle');
  const hm = new THREE.AnimationMixer(body);
  if (idle) { hm.clipAction(idle).play(); hm.update(0); }
  actorRoot.updateMatrixWorld(true);
  const pose = createRiderPose(body, actorRoot);
  ok(pose, `${y}: the rider is the contract skeleton`);
  const skinned = []; body.traverse(n => { if (n.isSkinnedMesh) skinned.push(n); });
  const gait = createHorseGait(root, { walk, walkCycle_m: spec.stride_m, trot, trotCycle_m: spec.trot_stride_m, rest: true });
  let worstFoot = 0, worstHand = 0, worstShort = 0, inside = 0, worstInside = 0, sampled = 0;
  for (const [pace, cycle] of [[config.ride.walk_m_s, spec.stride_m], [config.ride.trot_m_s, spec.trot_stride_m]]) {
    gait.advance(0, pace, 0);
    for (let k = 0; k < 8; k++) {
      gait.advance(cycle / 8, pace, 0);
      root.updateMatrixWorld(true);
      const lean = config.fit.lean_walk_rad + (config.fit.lean_trot_rad - config.fit.lean_walk_rad) * gait.trot;
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
          if (d > .01) { inside++; worstInside = Math.max(worstInside, d); }
        }
      }
    }
  }
  report.push(`${y}: feet within ${(worstFoot * 100).toFixed(1)} cm of the irons, hands ${(worstHand * 100).toFixed(1)} cm of the reins, `
    + `${inside} of ${sampled} sampled skin points more than 1 cm inside the horse (deepest ${(worstInside * 100).toFixed(1)} cm)`);
  ok(worstShort === 0, `${y}: every reach of the rider gets there at walk and trot`);
  ok(worstFoot < .02 && worstHand < .02, `${y}: feet at the irons and hands at the reins (${worstFoot.toFixed(3)}, ${worstHand.toFixed(3)} m)`);
  ok(inside === 0, `${y}: the rider never goes into the horse at walk or trot (${inside} points, deepest ${(worstInside * 100).toFixed(1)} cm)`);
  gait.advance(0, 0, .1); gait.advance(0, 0, .5);
  ok(gait.moving === 0, `${y}: a horse that stops stands in its rest pose`);
  tack.dispose(); gait.dispose();
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
console.log(`riding (T-3560): data, tack on the coat, rider seated without clipping, reins, holds, stands and getting down: ${checks} checks PASS`);

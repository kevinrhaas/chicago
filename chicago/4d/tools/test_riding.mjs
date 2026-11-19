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
import { execFileSync } from 'node:child_process';
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
const { drapes, drapePoint, pressPoint, pressZone, HABIT, habitCloth, habitRest, habitSheet, habitVertex, legBalls } = await import('../renderers/web/js/rider-drape.js');
const { garmentKind } = await import('../renderers/web/js/human-skirt.js');
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
  ok(rows.length >= 1 && rows.every(r => r.grade === 'reconstructed' && [config.liberty, 'L-camp-horses-3560'].includes(r.liberty) && r.at.every(Number.isFinite)), `${y}: a reconstructed saddle horse`);
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
// Every figure that may ride in the year: the visitor's stand-in, the town's riders, and the
// figures the year's camps and jaunt scenes put on a horse (config.rider.also).
// T-3644: and every body the visitor may choose for their own person in that year.
const person = JSON.parse(read('data/humans/visitor_person.json'));
const personAssets = y => Object.values(person.outfits?.[y] ?? {}).flat().map(o => o.asset);
const assetsOf = y => (process.env.RIDER_ASSETS ? process.env.RIDER_ASSETS.split(',') : [...new Set([config.rider.assets[y], ...(config.riders ?? []).filter(r => r.scene === y).map(r => r.asset), ...(config.rider.also?.[y] ?? []), ...personAssets(y)])]);
for (const y of YEARS) for (const a of assetsOf(y)) humans[a] ??= await parse(read(`assets/humans/web/${a}.lod${config.rider.lod}.glb`));
// T-3644: a dress worn on another's body (the riding habits, visitor_person.json `dress`) names
// only that body's own cloth, pieces and hats to set aside: a misspelt name would leave it as it was.
for (const y of YEARS) for (const s of ['male', 'female']) for (const o of person.outfits?.[y]?.[s] ?? []) {
  if (!o.dress) continue;
  const g = humans[o.asset] ?? await parse(read(`assets/humans/web/${o.asset}.lod${config.rider.lod}.glb`));
  const mats = new Set(), names = [];
  g.scene.traverse(n => { if (n.isMesh) { names.push(n.name); mats.add(n.material?.name); } });
  const piece = k => names.some(n => new RegExp(`(^|_)${k}(_lod\\d+)?$`).test(n));
  ok(Object.keys(o.dress.colours ?? {}).every(m => mats.has(m)), `${y} ${o.id}: its colours name ${o.asset}'s own cloth`);
  ok([...Object.keys(o.dress.pieces ?? {}), ...(o.dress.hide ?? [])].every(piece), `${y} ${o.id}: the pieces it colours or sets aside are ${o.asset}'s own`);
  ok(!o.dress.hat || o.dress.hat.kind, `${y} ${o.id}: its hat is a kind human-hats.js makes`);
}

const v = new THREE.Vector3(), q = new THREE.Vector3();
const report = [];
// T-3644: how far a point (envelope frame) is outside the habit's sheet, in the upright
// half-plane of its way round her hips (the nearest of the sheet's ways): 0 when under it.
function habitOutside(sheet, hips, p) {
  const { cols, rows } = HABIT;
  const dx = p.x - hips.x, dz = p.z - hips.z, rho = Math.hypot(dx, dz);
  const j = ((Math.round(Math.atan2(dx, dz) / (Math.PI * 2) * cols) % cols) + cols) % cols;
  const at = i => { const o = (i * cols + j) * 4; return [Math.hypot(sheet[o] - hips.x, sheet[o + 2] - hips.z), sheet[o + 1]]; };
  const poly = [[0, at(0)[1]], ...Array.from({ length: rows }, (_, i) => at(i)), [0, at(rows - 1)[1]]];
  let inPoly = false;
  for (let a = 0, b = poly.length - 1; a < poly.length; b = a++) {
    const [xa, ya] = poly[a], [xb, yb] = poly[b];
    if ((ya > p.y) !== (yb > p.y) && rho < (xb - xa) * (p.y - ya) / (yb - ya) + xa) inPoly = !inPoly;
  }
  if (inPoly) return 0;
  let best = Infinity;
  for (let a = 0; a < poly.length - 1; a++) {
    const [xa, ya] = poly[a], [xb, yb] = poly[a + 1], ex = xb - xa, ey = yb - ya, L2 = ex * ex + ey * ey || 1;
    const t = Math.max(0, Math.min(1, ((rho - xa) * ex + (p.y - ya) * ey) / L2));
    best = Math.min(best, Math.hypot(rho - xa - ex * t, p.y - ya - ey * t));
  }
  return best;
}
// Each year's tack, and every variant of it a row of the year rides on (the Potawatomi pad
// saddle, saddle_horses.json tack_variants): the visitor may mount any of them.
const tacksOf = y => [null, ...new Set([...config.rows, ...config.riders].filter(r => r.scene === y && r.tack).map(r => r.tack)),
  ...(config.side_saddle?.tack?.[y] ? [config.side_saddle.tack[y]] : [])];
// T-3644: a woman of 1835 or 1904 rides aside on the year's side saddle (and only she does).
const sideKey = y => config.side_saddle?.tack?.[y] ?? null;
const womenOf = y => Object.values(person.outfits?.[y]?.female ?? {}).flat().map(o => o.asset);
ok(['1835', '1904'].every(y => sideKey(y) && config.tack_variants[sideKey(y)]) && !sideKey('1812'), 'a side saddle in 1835 and 1904, none in 1812 (astride, Kevin\'s card)');
ok(riding.sideSaddleFor(config, '1835', { sex: 'female' }) === sideKey('1835') && riding.sideSaddleFor(config, '1904', { sex: 'female' }) === sideKey('1904')
  && riding.sideSaddleFor(config, '1812', { sex: 'female' }) === null && riding.sideSaddleFor(config, '1835', { sex: 'male' }) === null && riding.sideSaddleFor(config, '1904', null) === null,
  'the visitor rides aside as a woman in 1835 and 1904, astride as a man or in 1812');
ok(riding.bodyPose(riding.fitFor(config.fit, womenOf('1904')[0], 'side')).legs?.r, 'the side seat gives each leg its own pole');
for (const k of Object.keys(config.tack_variants ?? {})) ok(riding.tackFor(config, '1812', { tack: k }).saddle.seat_half_angle_deg > 0, `the ${k} tack variant lays over the year's`);
for (const y of YEARS) for (const tk of tacksOf(y)) {
  const T = riding.tackFor(config, y, tk ? { tack: tk } : null), yt = tk ? `${y} (${tk} tack)` : y;
  const root = clone(near.scene);
  root.updateMatrixWorld(true);
  const bones = {}; root.traverse(n => { if (n.isBone) bones[n.name] = n; });
  const bodyRest = bones.horse_body.matrixWorld.clone();
  const tack = fitTack(root, T);
  const env = tack.envelope;
  const S = T.saddle;
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
  ok(sunk === 0, `${yt}: the saddle, cloth and flaps lie on the coat (${sunk} vertices under it, deepest ${(worstSunk * 100).toFixed(1)} cm)`);
  const seat = tack.seat(), barL = tack.stirrupBar(1), barR = tack.stirrupBar(-1);
  ok(seat.z > -.3 && seat.z < .3 && seat.y > 1.4 && seat.y < 1.75 && Math.abs(seat.x) < .01, `${yt}: the seat on the back behind the withers (${seat.toArray().map(n => n.toFixed(2))})`);
  ok(barL.x > .15 && barR.x < -.15 && Math.abs(barL.y - barR.y) < .01 && barL.y < seat.y, `${yt}: the stirrup bars at the saddle's two sides`);
  // Kevin, 2026-11-17: straps "slice through the horse". With nobody up, the leathers hang and
  // the reins lie over the neck: no point of them more than 1 cm inside the trunk's coat, and the
  // reins along the top of the neck (above the bit, never under the jaw or through the throat).
  {
    tack.update(null);
    tack.parts.free.updateMatrixWorld(true);
    let deep = 0, worst = 0, low = 0;
    for (const m of tack.parts.free.children) {
      const pos = m.geometry.attributes.position;
      if (!pos || m.geometry.type !== 'BufferGeometry') continue;
      for (let i = 0; i < pos.count; i++) {
        v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld);
        q.copy(v).sub(new THREE.Vector3(0, S.axis_y_m, 0));
        const s = q.dot(env.dir); if (s < -.68 || s > .98) continue;
        const d = env.radius(s, Math.atan2(q.dot(env.side), q.dot(env.up)) / Math.PI * 180) - Math.hypot(q.dot(env.up), q.dot(env.side));
        if (d > .01) { deep++; worst = Math.max(worst, d); }
      }
    }
    ok(deep === 0, `${yt}: the hanging leathers and resting reins stay out of the trunk (${deep} points in, deepest ${(worst * 100).toFixed(1)} cm)`);
    const bit = tack.bit(1);
    for (const m of tack.parts.free.children.filter(c => c.name === 'tack:rein')) {
      const pos = m.geometry.attributes.position;
      for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(m.matrixWorld); if (v.z < bit.z - .2 && v.y < bit.y + .05) low++; }
    }
    ok(low === 0, `${yt}: the resting reins go up over the neck from the bit (${low} points below it)`);
  }
  const side = tk && tk === sideKey(y);
  if (side) {
    const heads = tack.parts.onBody.children.filter(m => m.name.startsWith('tack:head:'));
    ok(heads.length === (T.saddle.heads ?? []).length && heads.length >= 1 && heads.every(m => m.geometry.boundingSphere ?? m.geometry.computeBoundingSphere() ?? true),
      `${yt}: the side saddle's heads are drawn (${heads.map(m => m.name.slice(10)).join(', ')})`);
    ok(tack.parts.free.children.filter(c => c.name === 'tack:leather').length === 1, `${yt}: one stirrup, on the near side`);
  }
  for (const asset of (side ? womenOf(y).filter(a => assetsOf(y).includes(a)) : assetsOf(y))) {
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
  ok(pose, `${yt} ${asset}: the rider is the contract skeleton`);
  const skinned = []; body.traverse(n => { if (n.isSkinnedMesh) skinned.push(n); });
  const gait = createHorseGait(root, { walk, walkCycle_m: spec.stride_m, trot, trotCycle_m: spec.trot_stride_m,
    canter, canterCycle_m: spec.canter_stride_m, gallop, gallopCycle_m: spec.gallop_stride_m, rest: true });
  let worstFoot = 0, worstHand = 0, worstShort = 0, inside = 0, worstInside = 0, sampled = 0, laid = 0, pressed = 0; const dbg = {};
  // T-3644: aside, her hanging cloth is laid on the habit (rider-drape.js, as the shader does),
  // and her legs must be under it: every point of her legs' skin and stockings inside the sheet.
  const habitOf = new Map();
  if (side) for (const m of skinned) { const kind = garmentKind(m, asset).kind; const rest = habitCloth(m, kind) && habitRest(m); if (rest) habitOf.set(m, { rest, lift: /garment_outer|apron/.test(m.material.name) || kind === 'ride' ? HABIT.lift_m : 0 }); }
  const habitL = Math.max(.3, ...[...habitOf.values()].map(h => h.rest.below));
  if (side) ok(habitOf.size >= 1, `${yt} ${asset}: her skirt is laid on the habit (${habitOf.size} pieces)`);
  let bare = 0, legPts = 0, worstBare = 0, headIn = -Infinity;
  const zone = pressZone(S);
  for (const [pace, cycle] of [[config.ride.walk_m_s, spec.stride_m], [config.ride.trot_m_s, spec.trot_stride_m],
    [config.ride.canter_m_s, spec.canter_stride_m], [config.ride.gallop_m_s, spec.gallop_stride_m]]) {
    gait.advance(0, pace, 0);
    for (let k = 0; k < 8; k++) {
      gait.advance(cycle / 8, pace, 0);
      root.updateMatrixWorld(true);
      // Moving with the horse (riderLife) and looking hard about, left then right, head down.
      const look = (k % 2 ? 1 : -1) * riding.LOOK_MAX_RAD;
      const L = riding.riderLife({ next: Infinity, look, want: look, nod: .12, wantNod: .12 }, { level: gait.level, moving: gait.moving, phase: gait.phase, dt: 0, now: k });
      const f = riding.fitFor(config.fit, asset, side ? 'side' : 'astride');   // T-3644: the body's own fit, aside on a side saddle
      const lean = riding.leanAt(f, gait.level) + L.lean;
      const t = saddleTargets(tack, f, { lean, rise: L.rise, give: L.give }), w = t.world(root);
      const short = pose.apply({ ...w, look: L.look, sway: L.sway, nod: L.nod, ...riding.bodyPose(f) });
      tack.update(t.rootFrame(root, pose));
      worstShort = Math.max(worstShort, ...Object.values(short));
      // Aside, the side saddle's heads stay clear of her legs (each leg as a capsule on its bones).
      if (side) for (const m of tack.parts.onBody.children.filter(c => c.name.startsWith('tack:head:'))) {
        const W = n => pose.bones[n].getWorldPosition(new THREE.Vector3()), P = m.geometry.attributes.position, p = new THREE.Vector3(), ab = new THREE.Vector3();
        const caps = [['thigh_r', 'calf_r', .075], ['calf_r', 'foot_r', .055], ['thigh_l', 'calf_l', .075], ['calf_l', 'foot_l', .055]].map(([a, b, r]) => [W(a), W(b), r]);
        for (let i = 0; i < P.count; i++) {
          p.fromBufferAttribute(P, i).applyMatrix4(m.matrixWorld);
          for (const [a, b, r] of caps) {
            ab.subVectors(b, a); const t = Math.max(0, Math.min(1, p.clone().sub(a).dot(ab) / ab.lengthSq()));
            headIn = Math.max(headIn, r - a.clone().addScaledVector(ab, t).distanceTo(p));
          }
        }
      }
      for (const s of ['l', 'r']) {
        worstFoot = Math.max(worstFoot, pose.bones[`foot_${s}`].getWorldPosition(v).distanceTo(w.feet[s]));
        worstHand = Math.max(worstHand, pose.bones[`hand_${s}`].getWorldPosition(v).distanceTo(w.hands[s]));
      }
      // The rider's skin, carried back into the trunk's rest frame (where the envelope is), against the coat.
      const back = bodyRest.clone().multiply(bones.horse_body.matrixWorld.clone().invert());
      const toEnv = new THREE.Matrix4().makeTranslation(0, -S.axis_y_m, 0).multiply(back);
      let sheet = null, hips = null;
      if (side) {
        hips = pose.bones.thigh_l.getWorldPosition(new THREE.Vector3()).add(pose.bones.thigh_r.getWorldPosition(new THREE.Vector3())).multiplyScalar(.5).applyMatrix4(toEnv);
        sheet = habitSheet(legBalls(pose.bones, toEnv), hips);
      }
      const rest = new THREE.Vector3();
      for (const m of skinned) {
        m.skeleton.update();
        // Hanging cloth lies on the horse (rider-drape.js, as the shader lays it); legs, skin and boots never move.
        const draped = drapes(m, garmentKind(m, asset).kind);
        const H = habitOf.get(m);
        const legsRest = side && !draped && !/^footwear/.test(m.material.name) ? habitRest(m) : null;
        const n = m.geometry.attributes.position.count;
        for (let i = 0; i < n; i += 5) {
          m.getVertexPosition(i, v).applyMatrix4(m.matrixWorld).applyMatrix4(back);
          q.copy(v).sub(new THREE.Vector3(0, S.axis_y_m, 0));
          if (H) habitVertex(sheet, rest.fromBufferAttribute(m.geometry.attributes.position, i).applyMatrix4(H.rest.matrix), q, habitL, H.lift);
          // Her legs (standing, more than 15 cm under the hips) under the habit.
          if (legsRest && rest.fromBufferAttribute(m.geometry.attributes.position, i).applyMatrix4(legsRest.matrix).y < -.15) {
            legPts++;
            const out = habitOutside(sheet, hips, q);
            if (out > .01) { bare++; worstBare = Math.max(worstBare, out); }
          }
          if (draped && drapePoint(q, env, { seatHalfDeg: S.seat_half_angle_deg })) laid++;
          // A leg lying on the saddle is pressed onto its cloth and flaps (the shader's press).
          else if (!draped && pressPoint(q, env, zone)) pressed++;
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
  report.push(`${yt} ${asset}: feet within ${(worstFoot * 100).toFixed(1)} cm of the irons, hands ${(worstHand * 100).toFixed(1)} cm of the reins, `
    + `${inside} of ${sampled} sampled skin points more than 1 cm inside the horse (deepest ${(worstInside * 100).toFixed(1)} cm); ${laid} points of cloth laid on the horse, ${pressed} of leg pressed onto the saddle`);
  ok(worstShort === 0, `${yt} ${asset}: every reach of the rider gets there at walk, trot, canter and gallop`);
  ok(worstFoot < .02 && worstHand < .02, `${yt} ${asset}: feet at the irons and hands at the reins (${worstFoot.toFixed(3)}, ${worstHand.toFixed(3)} m)`);
  ok(inside === 0, `${yt} ${asset}: the rider never goes into the horse at walk, trot, canter or gallop (${inside} points, deepest ${(worstInside * 100).toFixed(1)} cm)`);
  if (side) {
    report.push(`  aside: ${bare} of ${legPts} points of her legs outside the habit (furthest ${(worstBare * 100).toFixed(1)} cm)`);
    ok(legPts > 500 && bare === 0, `${yt} ${asset}: aside, her legs are under the habit at every pace (${bare} of ${legPts} points out, furthest ${(worstBare * 100).toFixed(1)} cm)`);
    ok(headIn <= 0, `${yt} ${asset}: the side saddle's heads stay clear of her legs (${(Math.max(0, headIn) * 100).toFixed(1)} cm in)`);
  }
  gait.advance(0, 0, .1); gait.advance(0, 0, .5);
  ok(gait.moving === 0, `${yt}: a horse that stops stands in its rest pose`);
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
  ['1835', 10, 'summer', 9, 'a summer morning'], ['1835', 10, 'winter', 5, 'a winter morning'], ['1835', 19, 'summer', 2, 'a summer evening'],
  ['1835', 22, 'summer', 1, 'ten at night (the doctor)'], ['1835', 23.5, 'summer', 0, 'midnight'],
  ['1812', 10, 'summer', 7, 'a summer morning'], ['1812', 10, 'winter', 4, 'a winter morning'], ['1812', 21, 'summer', 0, 'night'],
  ['1904', 9, 'summer', 1, 'a summer morning (a groom)'], ['1904', 15, 'summer', 1, 'a summer afternoon (a coachman)'],
  ['1904', 9, 'winter', 1, 'a winter morning (the groom)'], ['1904', 20, 'summer', 0, 'the evening']])
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

// Kevin, 2026-11-17: "that horse standing in the middle of the street is odd" ... "standing on the
// side of the street not the middle". No saddle horse stands in a roadway's middle: in 1835 none on
// a street's worn track, in 1904 none more than 1.5 m in from a carriageway's edge.
{
  const segD = (p, pts) => Math.min(...pts.slice(1).map((b, i) => { const a = pts[i], dx = b[0] - a[0], dy = b[1] - a[1], L2 = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2)); return Math.hypot(a[0] + t * dx - p[0], a[1] + t * dy - p[1]); }));
  const streets = JSON.parse(read('data/streets/1835.json')).streets;
  for (const r of config.rows.filter(r => r.scene === '1835')) {
    const worst = Math.min(...streets.map(s => segD(r.at, s.path_local_enu_m) - (s.track_width_m ?? 10.5) / 2));
    ok(worst > 0.4, `${r.id}: off the street's worn track (${worst.toFixed(1)} m beyond its edge)`);
  }
  const ways = JSON.parse(read('data/street_grid/1904.json')).carriageways;
  for (const r of config.rows.filter(r => r.scene === '1904')) {
    for (const w of ways) {
      const poly = w.polygon_local_m;
      let inside = false;
      for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) { const [xi, yi] = poly[i], [xj, yj] = poly[j];
        if ((yi > r.at[1]) !== (yj > r.at[1]) && r.at[0] < (xj - xi) * (r.at[1] - yi) / (yj - yi) + xi) inside = !inside; }
      if (!inside) continue;
      const edge = segD(r.at, [...poly, poly[0]]);
      ok(edge < 1.5, `${r.id}: at the side of ${w.id}, not its middle (${edge.toFixed(1)} m from its edge)`);
    }
  }
}

// The camps' horses (Kevin, 2026-11-17: "there would be horses at the native camps"): one at each
// picket the camps lay, clear of the lodges, there only on the camp's own days.
ok(liberties.includes('### L-camp-horses-3560 '), 'L-camp-horses-3560 recorded in docs/LIBERTIES.md');
const campHorses = config.rows.filter(r => r.camp);
const pickets = JSON.parse(execFileSync('python3', [new URL('camp_pickets_1812.py', import.meta.url).pathname], { encoding: 'utf8' }));
ok(campHorses.length >= pickets.reduce((n, c) => n + c.stakes.length, 0) - 2 && campHorses.length > 30, `a horse at (nearly) every camp picket (${campHorses.length})`);
for (const c of pickets) for (const h of campHorses.filter(r => r.camp === c.camp)) {
  ok(h.dates?.from === c.window?.from && h.dates?.to === c.window?.to && h.tack === 'potawatomi', `${h.id}: its camp's days and the pad saddle`);
  ok(c.dwellings.every(([e, n, hx, hy]) => Math.hypot(h.at[0] - e, h.at[1] - n) > Math.max(hx, hy) + 1), `${h.id}: clear of the lodges`);
}
ok(riding.offDate({ dates: { from: '1812-08-12', to: '1812-08-15' } }, '1812-08-11') && !riding.offDate({ dates: { from: '1812-08-12', to: '1812-08-15' } }, '1812-08-15T09:00')
  && !riding.offDate({ dates: { from: '1812-08-12', to: '1812-08-15' } }, null) && !riding.offDate({}, '1812-01-01'), 'a camp horse is away off its camp\'s days and there on them');

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
// Kevin, 2026-11-17: "the person looks pretty stiff riding a horse". The rider moves with the horse.
{
  const at = (level, phase, now = 0, moving = 1) => riding.riderLife({ next: Infinity }, { level, moving, phase, now });
  ok(Math.abs(at(0, .25).sway) > .03 && Math.abs(at(0, .125).give) > .02, 'at the walk his back rolls with the stride and his hands go with the head');
  ok(at(1, .5).rise > .03 && at(1, 0).rise < 1e-9 && at(0, .5).rise === 0, 'at the trot he rises out of the saddle once a stride, and only at the trot');
  ok(Math.abs(at(2, .25).lean) > .07 && Math.abs(at(3, .25).give) > .05, 'at the canter his back rocks; at the gallop his hands give and take');
  ok(Math.abs(at(0, 0, 1.05, 0).lean) > .005 && at(0, .5, 0, 0).rise === 0, 'standing, he breathes');
  const life = {}, r = riding.riderRand(7);
  let looked = 0, back = 0;
  for (let t = 0; t < 120; t += .1) { const L = riding.riderLife(life, { level: 0, moving: 1, phase: (t % 1.6) / 1.6, dt: .1, now: t, rand: r }); if (Math.abs(L.look) > .3) looked++; if (Math.abs(L.look) < .05) back++; }
  ok(looked > 60 && back > 200, `now and then he looks about, and back ahead (${looked} and ${back} of 1200 frames)`);
  const fast = {}; let far = 0;
  for (let t = 0; t < 120; t += .1) { const L = riding.riderLife(fast, { level: 3, moving: 1, dt: .1, now: t, rand: riding.riderRand(7) }); far = Math.max(far, Math.abs(L.look)); }
  ok(far < riding.LOOK_MAX_RAD * .35, 'at a gallop he keeps his eyes ahead');
}
// Kevin, 2026-11-17: a carriage drove through a horse. A rider a team is about to meet pulls aside
// (right, GIVE_WAY_M) and the team waits for him (town-transport.js obstacles) till he has.
{
  const [ae, an] = riding.asideOf(p0, riding.GIVE_WAY_M);
  ok(Math.abs(ae) < 1e-9 && Math.abs(an + riding.GIVE_WAY_M) < 1e-9, 'aside is to the right of the way he rides (south, riding east)');
  const meets = teams => riding.teamMeets({ route: sq, distance: d0, pace: 1.4, teams });
  const headOn = (e, n = 0) => [0, 1.5, 3].map(t => footprintOfPose({ e: e - 3 * t, n, yaw: -east }, [-1.95, -1.86, 1.95, 5.1], .3));
  ok(meets([headOn(p0.e + 14)]) && meets([team(p0.e - 9, 0, 3)]) && !meets([headOn(p0.e + 14, 9)]) && !meets([headOn(p0.e + 40)]),
    'a team head on or catching him up meets him; one in its own lane or far off does not');
  ok(held({ teams: [headOn(p0.e + 8)] }) === 'a team' && held({ teams: [headOn(p0.e + 8)], aside: riding.GIVE_WAY_M }) === null,
    'on his line he pulls up for a team head on; pulled aside, it goes by him');
  // Pulled aside, the widest team (its OBSTACLE_M .6 m on) passes clear of him.
  const fop = footprintOfPose, { overlaps: overlapsPrint } = await import('../renderers/web/js/transport-crossings.js');
  const me = fop({ e: p0.e + ae, n: p0.n + an, yaw: riding.horseYaw(90) }, [-.5, -1.2, .5, 1.75], 0);
  ok(!overlapsPrint(fop({ e: p0.e, n: 0, yaw: -east }, [-1.95, -1.86, 1.95, 5.1], .6), me), 'the widest team, with its margin, misses a rider pulled aside');
  const shifted = riding.shiftPrint(me, 2, -1);
  ok(Math.abs(shifted.w - me.w - 2) < 1e-9 && Math.abs(shifted.s - me.s + 1) < 1e-9 && shifted.corners[0][0] === me.corners[0][0] + 2, 'a print moves whole');
}
console.log(`riding (T-3560): data, tack on the coat, rider seated without clipping, reins, holds, stands, getting down, the town's riders and stabled horses: ${checks} checks PASS`);

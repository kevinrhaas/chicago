// SPDX-License-Identifier: GPL-3.0-or-later
// T-3559: the driven horse's three levels and two gaits (renderers/web/js/horse-rig.js).
//
//  - the mid and far GLBs are bound by bytes in loops.json, carry the near horse's 26 joints and
//    inverse binds, its three material names, and far fewer triangles (EXPORT receipt numbers);
//  - bound to a near clone's bones, a far body follows the near body through the trot: at every
//    sampled phase its skinned bounds stay within 3 cm of the near's (no pop at a swap);
//  - the swap distances hold a band, so a horse standing at a line does not flicker;
//  - the gaits: walk alone at a walking pace, trot alone from 2.1 m/s, both advanced by the same
//    metres on their own cycles; the trot clip and its certificate are bound in loops.json.
//  - T-3560: the canter and gallop likewise, bound and inside the walk's domain; the level eases
//    a gait at a time; the far body follows the near through the gallop.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { registerHooks } from 'node:module';

const here = new URL('../', import.meta.url);
const read = rel => fs.readFileSync(new URL(rel, here));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
const hooks = registerHooks({ resolve: (s, c, next) => s === 'three' ? { url: threeURL, shortCircuit: true } : next(s, c) });
const THREE = await import(threeURL);
const { attachHorseLods, createHorseGait, clipFromJson, trotShare, gaitLevel, HORSE_LOD } = await import('../renderers/web/js/horse-rig.js');
const { gltfLoader, geometryOnly } = await import('./horse_walk_v2.mjs');
hooks.deregister();

const config = JSON.parse(read('data/transport/driven/loops.json'));
const spec = config.horse_models.current26_walk_v2;
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks++; };

// --- bindings
const nearBytes = read('renderers/web/' + spec.file);
ok(sha(nearBytes) === spec.sha256, 'near horse bound');
const trotBytes = read('renderers/web/' + spec.trot_clip_file);
ok(sha(trotBytes) === spec.trot_clip_sha256, 'trot clip bound by bytes');
const trotJson = JSON.parse(trotBytes);
ok(trotJson.name === spec.trot_clip && trotJson.model_sha256 === spec.sha256 && trotJson.cycle_m === spec.trot_stride_m, 'trot clip names its horse and cycle');
const trotCert = JSON.parse(read('data/transport/driven/current26-trot-v1-hoof-domain.json'));
ok(trotCert.clip_sha256 === spec.trot_clip_sha256 && trotCert.stance.maximum_hoof_slip_m <= 1e-3 && trotCert.stance.maximum_hoof_lift_m <= 1e-3, 'trot hooves planted in stance');
ok(trotCert.half_width_m <= spec.support_domain.half_width_m && trotCert.half_length_m <= spec.support_domain.half_length_m,
  'the trot stays inside the walk\'s certified support domain, so a route certified for the walk carries it');
// T-3560: the canter and the gallop, bound and certified the same way.
const fast = {};
for (const g of ['canter', 'gallop']) {
  const bytes = read('renderers/web/' + spec[`${g}_clip_file`]);
  ok(sha(bytes) === spec[`${g}_clip_sha256`], `${g} clip bound by bytes`);
  const json = fast[g] = JSON.parse(bytes);
  ok(json.name === spec[`${g}_clip`] && json.model_sha256 === spec.sha256 && json.cycle_m === spec[`${g}_stride_m`], `${g} clip names its horse and cycle`);
  const cert = JSON.parse(read(`data/transport/driven/current26-${g}-v1-hoof-domain.json`));
  ok(cert.clip_sha256 === spec[`${g}_clip_sha256`] && cert.stance.maximum_hoof_slip_m <= 1e-3 && cert.stance.maximum_hoof_lift_m <= 1e-3, `${g} hooves planted in stance`);
  ok(cert.half_width_m <= spec.support_domain.half_width_m && cert.half_length_m <= spec.support_domain.half_length_m,
    `the ${g} stays inside the walk's certified support domain`);
}
const receipt = JSON.parse(read(spec.lods_receipt));
const loader = await gltfLoader();
const parse = async bytes => loader.parseAsync(geometryOnly(bytes), '');
const near = await parse(nearBytes);
const rigOf = g => {
  const meshes = []; g.scene.traverse(n => { if (n.isSkinnedMesh) meshes.push(n); });
  return { meshes, joints: meshes[0].skeleton.bones.map(b => b.name), ibm: meshes[0].skeleton.boneInverses.flatMap(m => m.elements.map(x => +x.toFixed(5))),
    materials: meshes.map(m => m.material.name).sort(), triangles: meshes.reduce((n, m) => n + m.geometry.index.count / 3, 0) };
};
const nearRig = rigOf(near);
ok(nearRig.joints.length === 26, '26 joints');
const lodTemplates = {};
for (const level of ['mid', 'far']) {
  const bytes = read('renderers/web/' + spec.lods[level].file);
  ok(sha(bytes) === spec.lods[level].sha256, `${level} bound by bytes`);
  const row = receipt.lods.find(r => r.level === level);
  ok(row && row.sha256 === spec.lods[level].sha256, `${level} is the receipt's export`);
  const g = lodTemplates[level] = await parse(bytes), r = rigOf(g);
  ok(JSON.stringify(r.joints) === JSON.stringify(nearRig.joints), `${level} joints are the near horse's`);
  ok(JSON.stringify(r.ibm) === JSON.stringify(nearRig.ibm), `${level} inverse binds are the near horse's`);
  ok(JSON.stringify(r.materials) === JSON.stringify(nearRig.materials), `${level} material names are the near horse's (the coat binds by name)`);
  ok(r.triangles === row.triangles, `${level} triangle count is the receipt's`);
  console.log(`${level}: ${r.triangles} triangles (near ${nearRig.triangles}), ${(bytes.length / 1024).toFixed(0)} KiB, maps ${row.texture_dimensions.map(d => d[0]).join('/')} px`);
}
ok(rigOf(lodTemplates.mid).triangles <= .45 * nearRig.triangles && rigOf(lodTemplates.far).triangles <= .15 * nearRig.triangles, 'mid under 45%, far under 15% of the near triangles');

// --- one skeleton drives all three, through the trot
const { clone } = await import(new URL('renderers/web/vendor/three-0.185.1/addons/utils/SkeletonUtils.js', here).href).catch(async () => {
  const src = fs.readFileSync(new URL('renderers/web/vendor/three-0.185.1/addons/utils/SkeletonUtils.js', here), 'utf8').replace("from 'three'", `from '${threeURL}'`);
  return import(`data:text/javascript;base64,${Buffer.from(src).toString('base64')}`);
});
const root = clone(near.scene);
const lods = attachHorseLods(root, lodTemplates, { sourceSha256: spec.sha256 });
ok(lods.levels.mid.length === 3 && lods.levels.far.length === 3, 'three meshes a level, bound to the near clone');
const walkJson = JSON.parse(read('renderers/web/' + spec.walk_clip_file));
const gait = createHorseGait(root, { walk: clipFromJson(walkJson), walkCycle_m: spec.stride_m, trot: clipFromJson(trotJson), trotCycle_m: spec.trot_stride_m });
const boundsOf = meshes => {
  const box = new THREE.Box3(), v = new THREE.Vector3();
  root.updateMatrixWorld(true);
  for (const m of meshes) { m.skeleton.update(); const n = m.geometry.attributes.position.count;
    for (let i = 0; i < n; i += 3) box.expandByPoint(m.getVertexPosition(i, v).applyMatrix4(m.matrixWorld)); }
  return box;
};
let worst = 0;
gait.advance(0, 3, 0);
ok(gait.trot === 1, 'at 3 m/s the trot alone');
for (let k = 0; k < 12; k++) {
  gait.advance(spec.trot_stride_m / 12, 3, 0);
  const a = boundsOf(lods.levels.near.filter(m => m.material.name !== 'Eye_brown')), b = boundsOf(lods.levels.far.filter(m => m.material.name !== 'Eye_brown'));
  worst = Math.max(worst, a.min.distanceTo(b.min), a.max.distanceTo(b.max));
}
ok(worst < .03, `far body follows the near through the trot (bounds within ${worst.toFixed(4)} m)`);
console.log(`far vs near skinned bounds through a trot cycle: worst corner ${(worst * 100).toFixed(1)} cm`);

// --- swaps with a band
ok(lods.level === 'near' && lods.update(HORSE_LOD.mid + .5) === 'mid' && lods.update(HORSE_LOD.mid - 1) === 'mid'
  && lods.update(HORSE_LOD.mid - HORSE_LOD.band - .1) === 'near', 'mid swaps out past the line and back only inside the band');
ok(lods.update(HORSE_LOD.far + 1) === 'far' && lods.update(HORSE_LOD.far - 1) === 'far' && lods.update(HORSE_LOD.far - HORSE_LOD.band - 1) === 'mid', 'far likewise');
ok(lods.levels.far.every(m => m.visible) === false && lods.levels.mid.every(m => m.visible) && lods.levels.near.every(m => !m.visible), 'one level drawn at a time');
const noMid = attachHorseLods(clone(near.scene), { far: lodTemplates.far }, { sourceSha256: spec.sha256 });
ok(noMid.update(HORSE_LOD.mid + 2) === 'near' && noMid.update(HORSE_LOD.far + 2) === 'far', 'a phone with only the far level keeps the near one until the far line');
lods.dispose();
ok(lods.levels.far.every(m => !m.parent), 'levels removed on dispose');

// --- gaits by pace
ok(trotShare(1.3) === 0 && trotShare(1.6) === 0 && trotShare(2.1) === 1 && trotShare(1.85) > .4 && trotShare(1.85) < .6, 'walk to 1.6 m/s, trot from 2.1');
const g2 = createHorseGait(clone(near.scene), { walk: clipFromJson(walkJson), walkCycle_m: 1, trot: clipFromJson(trotJson), trotCycle_m: 1.5 });
g2.advance(.75, 1.3, .016);
ok(Math.abs(g2.walkAction.time - .75) < 1e-9 && Math.abs(g2.trotAction.time - .5) < 1e-9 && g2.trot === 0, 'same metres, each gait on its own cycle');
for (let i = 0; i < 40; i++) g2.advance(.04, 2.6, .016);
ok(g2.trot === 1, 'a third of a second to settle into the trot');
// --- T-3560: four gaits by pace
ok(gaitLevel(1.4) === 0 && gaitLevel(2.8) === 1 && gaitLevel(5) === 2 && gaitLevel(8.5) === 3 && gaitLevel(3.9) > 1 && gaitLevel(3.9) < 2,
  'walk, trot from 2.1, canter from 4.2, gallop from 6.8 m/s, blended between');
const g4 = createHorseGait(clone(near.scene), { walk: clipFromJson(walkJson), walkCycle_m: 1, trot: clipFromJson(trotJson), trotCycle_m: 1.5,
  canter: clipFromJson(fast.canter), canterCycle_m: 2, gallop: clipFromJson(fast.gallop), gallopCycle_m: 3.2 });
g4.advance(0, 8.5, 0);
ok(g4.name === 'gallop' && g4.gallopAction.getEffectiveWeight() === 1 && g4.walkAction.getEffectiveWeight() === 0, 'at 8.5 m/s the gallop alone');
g4.advance(1.6, 8.5, 0);
ok(Math.abs(g4.gallopAction.time - .5) < 1e-9 && Math.abs(g4.canterAction.time - .8) < 1e-9, 'the same metres on each gait\'s own cycle');
for (let i = 0; i < 10; i++) g4.advance(.05, 1.4, .1);
ok(g4.name === 'walk' && g4.walkAction.getEffectiveWeight() === 1, 'from a gallop back to a walk in under a second (a third of a second a gait)');
g4.advance(0, 5, .1);
ok(g4.level > 0 && g4.level < 1 && Math.abs(g4.walkAction.getEffectiveWeight() + g4.trotAction.getEffectiveWeight() - 1) < 1e-9, 'never two leg orders apart in one step: the walk eases into the trot first');
assert.throws(() => createHorseGait(clone(near.scene), { walk: clipFromJson(walkJson), walkCycle_m: 1, gallop: clipFromJson(fast.gallop), gallopCycle_m: 3.2 }), /faster gait/);
checks++;
// The far body follows the near through the gallop too (its legs fold furthest).
const root4 = clone(near.scene), lods4 = attachHorseLods(root4, lodTemplates, { sourceSha256: spec.sha256 });
const g5 = createHorseGait(root4, { walk: clipFromJson(walkJson), walkCycle_m: 1, trot: clipFromJson(trotJson), trotCycle_m: 1.5,
  canter: clipFromJson(fast.canter), canterCycle_m: 2, gallop: clipFromJson(fast.gallop), gallopCycle_m: 3.2 });
const bounds4 = meshes => { const box = new THREE.Box3(), v = new THREE.Vector3(); root4.updateMatrixWorld(true);
  for (const m of meshes) { m.skeleton.update(); const n = m.geometry.attributes.position.count;
    for (let i = 0; i < n; i += 3) box.expandByPoint(m.getVertexPosition(i, v).applyMatrix4(m.matrixWorld)); }
  return box; };
let worst4 = 0;
g5.advance(0, 8.5, 0);
for (let k = 0; k < 12; k++) {
  g5.advance(3.2 / 12, 8.5, 0);
  const a = bounds4(lods4.levels.near.filter(m => m.material.name !== 'Eye_brown')), b = bounds4(lods4.levels.far.filter(m => m.material.name !== 'Eye_brown'));
  worst4 = Math.max(worst4, a.min.distanceTo(b.min), a.max.distanceTo(b.max));
}
ok(worst4 < .03, `far body follows the near through the gallop (bounds within ${worst4.toFixed(4)} m)`);
console.log(`horse rig (T-3559, T-3560): near/mid/far bound by bytes on one skeleton, swaps banded, walk, trot, canter and gallop by pace: ${checks} checks PASS`);

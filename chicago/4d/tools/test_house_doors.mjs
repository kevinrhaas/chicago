#!/usr/bin/env node
/**
 * T-3442 — Glessner's front door opens on its hinges, and a visitor and a drawn person both
 * walk up its steps to it.
 *
 * With the real 1904 Glessner record, on flat ground at the house's base:
 *   - the plan read from the record is the door the shipped mesh draws (sill, leaf, jambs,
 *     threshold, approach paving — numbers measured off the light GLB);
 *   - the baked leaf is lifted out of a mesh, and only the leaf (the pane's backing behind
 *     it is dropped, a wall beside it is kept), once;
 *   - the door is an Interact thing: shut to start, Open door swings it 90 degrees inward on
 *     its north jamb, Close door brings it back, and Close is refused while the visitor
 *     stands in its swing;
 *   - the walker: shut, a walk from the sidewalk climbs the approach and the threshold and
 *     stops at the leaf, standing on the threshold, the camera easing each step; open, it
 *     goes on through into the vestibule and back out; walking along the façade past the
 *     door feels no doorway;
 *   - the step path: from the sidewalk up each tread to just inside the door, every height
 *     the tread's own, rising only at the risers;
 *   - a HumanActor walks that path: turns to it, its feet on each tread, and stops, idling,
 *     turned to the street, once.
 *
 *   node tools/test_house_doors.mjs
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
const { createWalker, footprintsFrom, WALK, outlineAt } = await import('../renderers/web/js/walker.js');
const { createIntent } = await import('../renderers/web/js/controls/intent.js');
const { createInteractions, createInteractKey } = await import('../renderers/web/js/interact.js');
const { HumanActor } = await import('../renderers/web/js/humans.js');
const { enuToWorld } = await import('../renderers/web/js/terrain.js');
const { bearingToYaw } = await import('../renderers/web/js/angles.js');
const { glessnerFrontPlan, takeDoorLeaf, doorLeafMaterial, createHouseDoors, leafBox, leafPose, planPoint,
  DOOR_SWING_S, VESTIBULE_DEPTH_M } = await import('../renderers/web/js/house-doors.js');

const ROOT = new URL('../', import.meta.url);
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks += 1; };
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const inside = (e, n, pts) => {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if ((yi > n) !== (yj > n) && e < ((xj - xi) * (n - yi)) / (yj - yi) + xi) hit = !hit;
  }
  return hit;
};

const sidecar = JSON.parse(fs.readFileSync(new URL('data/sidecars/1904/glessner_house.json', ROOT), 'utf8'));
const BASE = 4.33;                                  // the lot's heightfield (glessner_house grade_datum note)
const flat = { walkHeight: () => BASE, surfaceHeight: () => BASE, isWater: () => false };

// ---------------------------------------------------------------- the plan is the mesh's door
const plan = glessnerFrontPlan(sidecar);
ok(plan && plan.id === 'glessner_house:front', 'the record carries the front door');
// Measured off assets/web/glessner_house__as_built_1887.light.glb (structure frame, metres).
const face = plan.origin[0];
ok(near(face, 49.149, 0.002), `the Prairie face at u ${face.toFixed(3)}`);
ok(near(plan.sill, 0.226, 0.002) && near(plan.head, 2.511, 0.002), `the doorway's sill ${plan.sill.toFixed(3)} and head ${plan.head.toFixed(3)}`);
ok(near(plan.jambs[0], 11.765, 0.002) && near(plan.jambs[1], 13.289, 0.002), 'its jambs');
ok(near(face + plan.leaf.front, 48.903, 0.002) && near(face + plan.leaf.back, 48.844, 0.002), 'the leaf stands where the mesh draws it');
const [approach, threshold] = plan.treads;
ok(near(threshold.y, 0.226, 0.002) && near(face + threshold.d[0], 48.859, 0.002) && near(face + threshold.d[1], 49.332, 0.002),
  'the threshold, 0.6 ft out to 0.95 ft in, at the sill');
ok(near(approach.y, 0.125, 0.002) && near(face + approach.d[1], 53.94, 0.002), 'the approach paving to the walk join, at its drawn height');
ok(plan.hinge === 'right' && plan.grades.hinge === 'inferred' && plan.grades.swing === 'reconstructed',
  'hung on its right (north) jamb, inferred from the latch; the swing reconstructed');

// ---------------------------------------------------------------- the baked leaf is lifted
function quad(pos, a, b, c, d) { pos.push(...a, ...b, ...c, ...a, ...c, ...d); }
const box = leafBox(plan);
const leafU = face + plan.leaf.front, backU = face - 0.85;
function bakedMesh(name) {
  const pos = [];
  // The leaf's face (inside the box), a pane backing 0.6 m behind it, and the wall beside the door.
  quad(pos, [leafU, 0.3, -11.9], [leafU, 0.3, -13.1], [leafU, 2.4, -13.1], [leafU, 2.4, -11.9]);
  quad(pos, [backU + 0.2, 1.4, -12.2], [backU + 0.2, 1.4, -12.9], [backU + 0.2, 2.1, -12.9], [backU + 0.2, 2.1, -12.2]);
  quad(pos, [face, 0.3, -9.0], [face, 0.3, -11.0], [face, 2.4, -11.0], [face, 2.4, -9.0]);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(new Array(pos.length / 3 * 2).fill(0.5), 2));
  geo.setIndex([...Array(pos.length / 3).keys()]);
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ name }));
}
const record = { id: 'glessner_house', sidecar };
const oak = bakedMesh('oak');
const pieces = takeDoorLeaf(record, oak, new THREE.Matrix4());
ok(pieces.length === 1 && pieces[0].doorId === plan.id, 'the oak mesh gives up one leaf');
ok(pieces[0].geometry.getIndex().count === 6 && oak.geometry.getIndex().count === 6, 'the leaf (2 triangles) leaves, the backing is dropped, the wall stays');
const kept = oak.geometry.getAttribute('position');
ok([...oak.geometry.getIndex().array].every((i) => near(kept.getX(i), face, 1e-4)), 'what stays in the batch is the wall beside the door');
ok(takeDoorLeaf(record, oak, new THREE.Matrix4()) === pieces, 'and a second reading lifts nothing more');
ok(takeDoorLeaf(record, bakedMesh('granite'), new THREE.Matrix4()).length === 0, 'stone is never lifted');
ok(takeDoorLeaf({ id: 'glessner_lee_house_1700_prairie', sidecar }, bakedMesh('oak'), new THREE.Matrix4()).length === 0, 'nor any other house');
ok(box.x[1] < face && box.x[0] > face - 1.2, 'the leaf box stays behind the wall face');
const glass = new THREE.MeshPhysicalMaterial({ name: 'glass', transmission: 1 });
ok(!doorLeafMaterial(glass).transmission && doorLeafMaterial(glass).isMeshStandardMaterial, 'the grille pane costs no transmission pass');

// ---------------------------------------------------------------- the layer, the walker, the door
const registry = new Map([['glessner_house', record]]);
const p = sidecar.placement;
const matrix = new THREE.Matrix4().compose(enuToWorld(p.local_e, p.local_n, BASE),
  new THREE.Quaternion().setFromEuler(new THREE.Euler(0, bearingToYaw(p.rotation_deg ?? 0), 0)), new THREE.Vector3(1, 1, 1));
for (const piece of pieces) piece.material = doorLeafMaterial(oak.material);
const buildings = { matrixOf: (id) => (id === 'glessner_house' ? matrix : null), doorLeaves: new Map([[plan.id, pieces]]) };
const footprints = footprintsFrom(registry);
const decks = [];
const ix = createInteractions();
let visitor = null;
const problems = [];
const layer = createHouseDoors({ registry, buildings, footprints, decks, interactions: ix, visitor: () => visitor, problems });
ok(problems.filter((x) => x.startsWith(plan.id)).length === 0, `the door hangs without complaint: ${problems.join('; ')}`);
const door = layer.get(plan.id);
ok(door && ix.get(plan.id) === door && door.state === 'closed' && door.kind === 'door', 'the front door is an Interact thing, shut');
ok(decks.length === 3 && near(decks[0].y, BASE + approach.y, 1e-6) && near(decks[1].y, BASE + plan.sill, 1e-3), 'its two steps (and the vestibule floor) are decks at their drawn heights');
const fp = footprints.find((f) => f.id === 'glessner_house');
ok(fp.doorways?.length === 1, 'and the footprint has its doorway');

// Structure frame <-> ENU.
const enu = (u, v, y = 0) => { const w = new THREE.Vector3(u, y, -v).applyMatrix4(matrix); return { e: w.x, n: -w.z, y: w.y }; };
const inv = matrix.clone().invert();
const toPlan = (e, n) => { const w = new THREE.Vector3(e, 0, -n).applyMatrix4(inv); return { d: w.x - face, s: -w.z }; };
const mid = (plan.jambs[0] + plan.jambs[1]) / 2;
const westBearing = (270 + (p.rotation_deg ?? 0) + 360) % 360;

function walk(from, bearing, seconds, { onFrame = null } = {}) {
  const camera = new THREE.PerspectiveCamera();
  const w = createWalker({ camera, terrain: flat, footprints, decks, spawn: { local_e: from.e, local_n: from.n, yaw_deg: bearing } });
  const intent = createIntent();
  const trace = [];
  for (let i = 0; i < seconds * 60; i++) {
    intent.forward = 1;
    visitor = { e: w.state.e, n: w.state.n };
    ix.update(1 / 60);
    w.update(1 / 60, intent);
    trace.push({ ...toPlan(w.state.e, w.state.n), e: w.state.e, n: w.state.n, ground: w.state.groundY, cam: camera.position.y });
    onFrame?.(w, i);
  }
  visitor = { e: w.state.e, n: w.state.n };
  return { w, camera, trace, end: trace.at(-1) };
}
const sidewalk = enu(face + plan.sidewalk, mid);

{
  // Shut: up the approach and the threshold to the leaf, and no further.
  const shut = walk(sidewalk, westBearing, 8);
  ok(near(shut.end.d, plan.leaf.front + WALK.radius, 0.02), `at the shut door the walk stops at the leaf (${shut.end.d.toFixed(3)} m)`);
  ok(shut.trace.every((t) => t.d >= plan.leaf.front + WALK.radius - 0.01), 'and never reaches into it');
  ok(near(shut.end.ground, BASE + plan.sill, 1e-6), 'standing on the threshold, at the sill');
  ok(shut.trace.some((t) => near(t.ground, BASE + approach.y, 1e-6)), 'having climbed the approach paving on the way');
  const jumps = shut.trace.slice(1).map((t, i) => Math.abs(t.cam - shut.trace[i].cam));
  ok(Math.max(...jumps) < 0.03, `each step eased: the camera never moves ${Math.max(...jumps).toFixed(3)} m in a frame`);
  ok(near(shut.end.cam, BASE + plan.sill + WALK.eyeHeight, 1e-3) && near(shut.w.state.eyeY, BASE + plan.sill + WALK.eyeHeight, 1e-9),
    'and the eye settles at its standing height over the sill');
  ok(Math.abs(shut.end.s - mid) < 0.05, 'square in the doorway');

  // The Interact key offers it on foot, and R opens it.
  const keyEl = { hidden: true, textContent: '', dataset: {}, setAttribute() {}, addEventListener() {}, removeEventListener() {} };
  const said = [];
  const key = createInteractKey({ interactions: ix, keyEl, where: () => ({ e: shut.w.state.e, n: shut.w.state.n, bearing: westBearing, flying: false }), say: (t) => said.push(t) });
  ok(key.refresh() === door && keyEl.textContent === 'Open door', 'on the threshold the key offers Open door');
  ok(key.press().ok && door.running, 'a press starts the swing');
  ix.update(DOOR_SWING_S + 0.05);
  ok(door.state === 'open' && !door.running && said.at(-1) === 'Front door open', 'it ends open, and the key says so');
  // The leaf turned 90 degrees inward on its north jamb: its free edge is now inside.
  const pivot = layer.group.getObjectByName(`house-door:${plan.id}`).children[0];
  layer.group.updateMatrixWorld(true);
  const freeShut = planPoint(plan, plan.leaf.back, plan.leaf.s[0]);
  const freeNow = new THREE.Vector3(freeShut[0], 1, -freeShut[1]).applyMatrix4(pivot.children[0]?.matrixWorld ?? pivot.matrixWorld);
  const freePlan = toPlan(freeNow.x, -freeNow.z);
  const pose = leafPose(plan, 1);
  ok(near(freePlan.d, plan.leaf.back - pose.width, 0.01) && near(freePlan.s, plan.leaf.s[1], 0.01),
    `opened, the free edge stands ${(-freePlan.d).toFixed(2)} m inside, against the hinge jamb`);

  // Open: through the doorway into the vestibule.
  const through = walk(shut.w.enu, westBearing, 6);
  ok(through.end.d < plan.leaf.back - 1.0, `opened, the walk goes through (${through.end.d.toFixed(2)} m)`);
  ok(through.end.d >= plan.revealBack - VESTIBULE_DEPTH_M + WALK.radius - 0.01, 'and stops at the vestibule\'s back wall');
  ok(through.trace.every((t) => t.d > 0 || (t.s >= plan.jambs[0] + WALK.radius - 0.01 && t.s <= plan.jambs[1] - WALK.radius + 0.01)),
    'held off both jambs');
  ok(near(through.end.ground, BASE + plan.sill, 1e-6), 'on the vestibule\'s floor, at the sill');
  // Close is refused while the visitor stands where the leaf swings.
  const refused = ix.act(door);
  ok(!refused.ok && refused.refused && /doorway/.test(refused.why) && door.state === 'open' && !door.running,
    'Close door is refused while the visitor stands in its swing');
  // Back out to the sidewalk; then it closes.
  const out = walk(through.w.enu, (westBearing + 180) % 360, 9);
  ok(out.end.d > approach.d[1] && near(out.end.ground, BASE, 1e-6), 'back down the steps to the sidewalk');
  ok(Math.max(...out.trace.slice(1).map((t, i) => Math.abs(t.cam - out.trace[i].cam))) < 0.03, 'easing each step down as well');
  ok(ix.act(door).ok, 'from the sidewalk the door closes');
  ix.update(DOOR_SWING_S + 0.05);
  ok(door.state === 'closed' && Math.abs(pivot.rotation.y) < 1e-9, 'shut again, the leaf back in its frame');
  const again = walk(sidewalk, westBearing, 8);
  ok(near(again.end.d, plan.leaf.front + WALK.radius, 0.02), 'and the shut leaf stops the walk again');

  // Someone standing in the vestibule when it is shut (a teleport) is put out on the threshold.
  const camera = new THREE.PerspectiveCamera();
  const inner = enu(face + plan.leaf.back - 0.6, mid);
  const w = createWalker({ camera, terrain: flat, footprints, decks, spawn: { local_e: inner.e, local_n: inner.n, yaw_deg: westBearing } });
  w.update(1 / 60, createIntent());
  ok(toPlan(w.state.e, w.state.n).d >= plan.leaf.front + WALK.radius - 0.01, 'a visitor inside a shut door is put out in front of it');

  // Along the façade, past the door: no doorway felt.
  const north = enu(face + WALK.radius + 0.15, plan.jambs[1] + 2.5);
  const along = walk(north, (180 + (p.rotation_deg ?? 0) + 360) % 360, 4.5);
  ok(along.end.s < plan.jambs[0] - 1, 'a walk along the front passes the door');
  const sideways = along.trace.slice(1).map((t, i) => Math.abs(t.d - along.trace[i].d));
  ok(Math.max(...sideways) < 0.01, `without being pulled into it (${Math.max(...sideways).toFixed(4)} m a frame)`);
  ok(along.trace.every((t) => !inside(t.e, t.n, fp.pts)), 'and never inside the house');
  ok(outlineAt(fp, sidewalk.e, sidewalk.n) === fp.pts, 'beyond the door\'s zone the footprint is its own');
}

// ---------------------------------------------------------------- the step path
const path = layer.path(plan.id);
ok(Array.isArray(path) && path.length >= 6, `the path up to the door has ${path?.length} points`);
const pp = path.map((q) => ({ ...toPlan(q.e, q.n), y: q.y }));
ok(near(pp[0].d, plan.sidewalk, 1e-3) && near(pp[0].y, BASE, 1e-6), 'it starts on the sidewalk, on the ground');
ok(near(pp.at(-1).d, plan.leaf.back - 0.6, 1e-3) && near(pp.at(-1).y, BASE + plan.sill, 1e-6), 'and ends 0.6 m inside the leaf, at the sill');
ok(pp.every((q, i) => i === 0 || q.d < pp[i - 1].d), 'walking ever inward');
ok(pp.every((q, i) => i === 0 || q.y >= pp[i - 1].y - 1e-9), 'and only ever up');
ok(pp.every((q) => [BASE, BASE + approach.y, BASE + plan.sill].some((y) => near(q.y, y, 1e-6))), 'every height a tread\'s own (or the ground)');
const rise = (lo, hi) => pp.filter((q, i) => i > 0 && near(pp[i - 1].y, lo, 1e-6) && near(q.y, hi, 1e-6));
ok(rise(BASE, BASE + approach.y).length === 1 && rise(BASE + approach.y, BASE + plan.sill).length === 1, 'one riser onto the paving, one onto the threshold');
ok(pp.some((q) => near(q.d, threshold.d[1] - 0.12, 1e-3)) && pp.some((q) => near(q.d, threshold.d[1] + 0.12, 1e-3)),
  'each rise taken across the riser itself');
ok(near(path.outward, (90 + (p.rotation_deg ?? 0) + 360) % 360, 0.01), `facing out of the door is bearing ${path.outward.toFixed(2)}`);
const fromStreet = layer.path(plan.id, { from: [sidewalk.e + 6, sidewalk.n - 3], groundAt: () => BASE + 0.01 });
ok(fromStreet.length === path.length + 1 && near(fromStreet[0].y, BASE + 0.01, 1e-9), 'a path may start anywhere, the ground answering off the steps');

// ---------------------------------------------------------------- a person walks it
{
  const instance = { id: 'hi_test', person_id: 'test', appearance: { asset_id: 'none' },
    placement: { local_e: path[0].e, local_n: path[0].n, heading_deg: 0 }, behaviour: { state: 'standing' }, animation: { clip: 'idle' } };
  const actor = new HumanActor({ instance, assets: {}, heightAt: () => BASE });
  actor.walkSpeed = 0.6;                              // Mattie's walk clip's stated ground speed
  let arrived = 0;
  ok(actor.walkPath(path, { endHeading: path.outward, onArrive: () => { arrived += 1; } }) && actor.state === 'walking', 'a figure sets off along it, walking');
  const trail = [];
  for (let i = 0; i < 60 * 40 && actor.path; i++) {
    actor.walk(1 / 60);
    trail.push({ ...toPlan(actor.e, actor.n), y: actor.root.position.y, heading: actor.heading });
  }
  ok(!actor.path && arrived === 1 && actor.state === 'standing', `it arrives once and stands (${(trail.length / 60).toFixed(1)} s)`);
  ok(trail.slice(0, 4).every((t) => near(t.d, plan.sidewalk, 1e-6)) && trail.slice(0, 10).every((t) => near(t.d, plan.sidewalk, 0.03)),
    'facing north, it turns to the door before it walks');
  const onThreshold = trail.filter((t) => t.d < threshold.d[1] - 0.12 && t.d > plan.leaf.front);
  ok(onThreshold.length > 5 && onThreshold.every((t) => near(t.y, BASE + plan.sill, 1e-6)), 'its feet on the threshold at the sill');
  ok(trail.filter((t) => t.d < approach.d[1] - 0.12 && t.d > threshold.d[1] + 0.12).every((t) => near(t.y, BASE + approach.y, 1e-6)),
    'and on the paving at the paving\'s height');
  ok(Math.max(...trail.slice(1).map((t, i) => Math.abs(t.y - trail[i].y))) < 0.01, 'stepping up smoothly');
  ok(near(trail.at(-1).d, plan.leaf.back - 0.6, 1e-3) && near(actor.root.position.y, BASE + plan.sill, 1e-6), 'it stops just inside the door');
  ok(near(actor.heading, path.outward, 0.6), `turned to the street (${actor.heading.toFixed(1)})`);
  // And back out: the same path reversed.
  ok(actor.walkPath([...path].reverse(), { endHeading: path.outward }), 'and walks out again');
  for (let i = 0; i < 60 * 40 && actor.path; i++) actor.walk(1 / 60);
  ok(!actor.path && near(toPlan(actor.e, actor.n).d, plan.sidewalk, 1e-3) && near(actor.root.position.y, BASE, 1e-6), 'down the steps to the sidewalk');
  ok(!actor.walkPath([path[0]]), 'a path of one point is refused');
}

layer.dispose();
console.log(`PASS: ${checks} checks — Glessner's front door swings on its hinges and both the visitor and a drawn person walk up its steps (T-3442)`);

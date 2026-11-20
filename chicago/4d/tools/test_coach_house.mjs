#!/usr/bin/env node
/**
 * T-3557 — Glessner's coach-house doors on 18th Street swing, the man door opens for people,
 * a dark room stands behind them, and a carriage has a drivable way in over the carriage drive.
 *
 * With the real 1904 Glessner record, street grid and street section, on flat ground at the
 * house's base:
 *   - the coach plan read from the record is the doors the shipped mesh draws (numbers measured
 *     off assets/gltf/glessner_house__as_built_1887.glb);
 *   - the baked leaves (painted wood, their dark board backing, the iron latch) are lifted out of
 *     a mesh, split east and west, the casing and the wall left in the batch, and the front door's
 *     box never takes painted wood; the man door is cut out of the east leaf along its frame with
 *     no area lost;
 *   - the layer: shut to start; open() swings both leaves 90 degrees inward on their jambs and
 *     resolves; close() is refused while the visitor stands in the swing or in the room; the man
 *     door is an Interact thing that opens only while the leaves are shut, and opening the leaves
 *     shuts it first; reduced motion swings at once;
 *   - the walker: shut, a walk stops at the leaves; through the open man door, and through the
 *     open leaves, it goes on into the room, on its floor, and back out; past along the façade no
 *     doorway is felt;
 *   - the way in, from each end of 18th Street: samples a quarter metre apart along exact arcs,
 *     every lock inside the brougham's 15 degrees, the bicycle model (team-drive.js bicycleStep)
 *     driving it on its own curvature to within a centimetre; every wheel and hoof, with the live
 *     kerb rule's room, on the carriageway, the carriage drive or the room's floor the whole way;
 *     the measured envelope through the doorway, between the open leaves and into the room, clear
 *     of the 11.9-ft reading of the doorway, the casing, the leaves and the room's walls, and under
 *     the 12.6-ft lintel; at the stand the whole team inside and behind the leaves' swing;
 *   - clearFor: false while the leaves are shut, true for every step of the way that reaches over
 *     the kerb while they are open (so `road(pose) || clearFor` admits the whole way, where the
 *     kerb rule and the footprint clearance alone refuse it), false off the way or into a jamb.
 *
 *   node tools/test_coach_house.mjs
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
const { enuToWorld } = await import('../renderers/web/js/terrain.js');
const { bearingToYaw } = await import('../renderers/web/js/angles.js');
const { glessnerCoachPlan, glessnerFrontPlan, takeDoorLeaf, doorLeafMaterial, planPoint, createHouseDoors } =
  await import('../renderers/web/js/house-doors.js');
const CH = await import('../renderers/web/js/coach-house.js');
const { teamGroundPoints, createCarriagewayReader, bicycleStep, sampleOf, KERB_ROOM_M } = await import('../renderers/web/js/team-drive.js');
const { createTransportClearance } = await import('../renderers/web/js/transport-clearance.js');

const ROOT = new URL('../', import.meta.url);
let checks = 0;
const ok = (cond, msg) => { assert(cond, msg); checks += 1; };
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const read = (p) => JSON.parse(fs.readFileSync(new URL(p, ROOT), 'utf8'));
const FT = 0.3048, DEG = Math.PI / 180;
const report = [];

const sidecar = read('data/sidecars/1904/glessner_house.json');
const grid = read('data/street_grid/1904.json');
const section = read('data/street_section/1904.json');
const loops = read('data/transport/driven/loops.json');
const BASE = 4.33;                                  // the lot's heightfield (as test_house_doors.mjs)
const flat = { walkHeight: () => BASE, surfaceHeight: () => BASE, isWater: () => false };

// ---------------------------------------------------------------- the plan is the mesh's doors
const plan = glessnerCoachPlan(sidecar);
ok(plan && plan.id === 'glessner_house:coach' && plan.coach && plan.pair, 'the record carries the coach-house doors, a pair');
// Measured off assets/gltf/glessner_house__as_built_1887.glb (glTF metres: x = u, z = -v): the
// painted wood in the doorway spans u 4.343-8.031, y 0.061-3.901, v 22.255-22.350; the man
// door's latch (iron) u 6.918-6.950, y 1.041-1.221; the boards' dark backing from u 4.683.
const face = plan.origin[1];
ok(near(face, 22.555, 0.002), `the 18th Street face at v ${face.toFixed(3)}`);
ok(near(-plan.jambs[1], 4.343, 0.002) && near(-plan.jambs[0], 8.031, 0.002), 'the doorway W 134.9-147.0 where the mesh draws it');
ok(near(plan.sill, 0.061, 0.002) && near(plan.head, 3.901, 0.002), `its sill ${plan.sill.toFixed(3)} and lintel soffit ${plan.head.toFixed(3)}`);
ok(near(face + plan.leaf.back, 22.255, 0.002) && near(face + plan.leaf.front, 22.350, 0.002), 'the leaves stand 0.205-0.30 m behind the face');
ok(near(-plan.leaf.s[1], 4.343 + 0.17, 0.002) && near(-plan.leaf.s[0], 8.031 - 0.17, 0.002), 'between the casings');
ok(near(-plan.leaf.s[1] + 0.17, 4.683, 0.002), 'the west leaf\'s boards start inside its stile, as the dark backing does');
ok(plan.man && near(-plan.man.latch, (6.918 + 6.950) / 2, 0.003), `the man door's latch at u ${(-plan.man.latch).toFixed(3)}, as baked`);
ok(near(plan.man.s[0], plan.leaf.s[0], 1e-9) && near(plan.man.head - plan.sill, 2.62, 1e-6), 'the man door at the east jamb, 2.62 m high');
ok(plan.grades.hinge === 'inferred' && plan.grades.swing === 'inferred' && plan.grades.room === 'reconstructed',
  'hinges and swing inferred from the photographs, the room reconstructed');
const dims = CH.coachDims(plan);
const clearCasing = dims.ls1 - dims.ls0, clearLeaves = clearCasing - 2 * dims.thick;
const reveal119 = 11.9 * FT;

// ---------------------------------------------------------------- the baked leaves are lifted
function quad(pos, a, b, c, d) { pos.push(...a, ...b, ...c, ...a, ...c, ...d); }
const P3 = (d, s, y) => { const [u, v] = planPoint(plan, d, s); return [u, y, -v]; };
const record = { id: 'glessner_house', sidecar };
function mesh(name, quads) {
  const pos = [];
  for (const q of quads) quad(pos, ...q);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(new Array(pos.length / 3 * 2).fill(0.5), 2));
  geo.setIndex([...Array(pos.length / 3).keys()]);
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ name }));
}
const lo = plan.leaf.foot, hi = plan.leaf.top, dF = -0.245;
const westPanel = [P3(dF, dims.mid + 0.2, lo + 0.3), P3(dF, dims.ls1 - 0.2, lo + 0.3), P3(dF, dims.ls1 - 0.2, hi - 0.3), P3(dF, dims.mid + 0.2, hi - 0.3)];
// The east leaf's bottom rail runs under the man door and the fixed panel beside it.
const eastRail = [P3(dF, dims.mid + 0.13, lo), P3(dF, dims.ls0 + 0.17, lo), P3(dF, dims.ls0 + 0.17, lo + 0.24), P3(dF, dims.mid + 0.13, lo + 0.24)];
const manPanel = [P3(dF, plan.man.s[0] + 0.1, lo + 0.3), P3(dF, plan.man.s[1] - 0.1, lo + 0.3), P3(dF, plan.man.s[1] - 0.1, plan.man.head - 0.1), P3(dF, plan.man.s[0] + 0.1, plan.man.head - 0.1)];
const eastUpper = [P3(dF, dims.mid + 0.13, plan.man.head + 0.1), P3(dF, dims.ls0 + 0.17, plan.man.head + 0.1), P3(dF, dims.ls0 + 0.17, hi - 0.2), P3(dF, dims.mid + 0.13, hi - 0.2)];
const casing = [P3(-0.205, dims.j1, plan.sill), P3(-0.205, dims.ls1, plan.sill), P3(-0.205, dims.ls1, plan.head), P3(-0.205, dims.j1, plan.head)];
const loft = [P3(-0.25, dims.mid - 1, 5.5), P3(-0.25, dims.mid + 1, 5.5), P3(-0.25, dims.mid + 1, 7), P3(-0.25, dims.mid - 1, 7)];
const painted = mesh('painted_wood', [westPanel, eastRail, manPanel, eastUpper, casing, loft]);
const pieces = takeDoorLeaf(record, painted, new THREE.Matrix4());
const coach = pieces.filter((x) => x.doorId === plan.id);
ok(coach.length === 2 && coach.some((x) => x.leaf === 0) && coach.some((x) => x.leaf === 1), 'the painted mesh gives up two leaves, east and west');
ok(coach.find((x) => x.leaf === 1).geometry.getIndex().count === 6 && coach.find((x) => x.leaf === 0).geometry.getIndex().count === 18,
  'the west leaf its panel, the east its rail, man door and upper panel');
ok(painted.geometry.getIndex().count === 12, 'the casing and the loft door stay in the batch');
const backing = mesh('glass_dark', [[P3(-0.28, dims.mid + 0.3, 1), P3(-0.28, dims.ls1 - 0.3, 1), P3(-0.28, dims.ls1 - 0.3, 2), P3(-0.28, dims.mid + 0.3, 2)]]);
ok(takeDoorLeaf(record, backing, new THREE.Matrix4()).some((x) => x.doorId === plan.id), 'the boards\' dark backing goes with its leaf');
ok(takeDoorLeaf(record, mesh('granite', [westPanel]), new THREE.Matrix4()).length === 0, 'stone is never lifted');
// The front door's box takes no painted wood (it lifts only its own materials).
const front = glessnerFrontPlan(sidecar);
const F3 = (s, y) => { const dd = (front.leaf.front + front.leaf.back) / 2, [u, v] = planPoint(front, dd, s); return [u, y, -v]; };
const fs0 = front.leaf.s[0] + 0.1, fs1 = front.leaf.s[1] - 0.1, fy = front.leaf.foot + 0.5;
const inFront = [F3(fs0, fy), F3(fs1, fy), F3(fs1, fy + 1), F3(fs0, fy + 1)];
const paintedAtFront = mesh('painted_wood', [inFront]);
ok(takeDoorLeaf(record, paintedAtFront, new THREE.Matrix4()).length === 0 && paintedAtFront.geometry.getIndex().count === 6,
  'painted wood in the front door\'s box is left alone');
ok(takeDoorLeaf(record, mesh('oak', [inFront]), new THREE.Matrix4()).some((x) => x.doorId === 'glessner_house:front'), 'while its oak still lifts');

// ---------------------------------------------------------------- the man door's cut
{
  const east = coach.find((x) => x.leaf === 0).geometry;
  const rect = { s: [plan.man.s[0] - 0.02, plan.man.s[1]], y: [plan.man.foot - 0.02, plan.man.head] };
  const cut = CH.cutGeometry(east, plan, rect);
  const a0 = CH.areaOf(east), a1 = CH.areaOf(cut.inside), a2 = CH.areaOf(cut.outside);
  ok(near(a0, a1 + a2, 1e-6), `the cut loses no area (${a0.toFixed(4)} = ${a1.toFixed(4)} + ${a2.toFixed(4)} m2)`);
  const sOf = (x, z) => (x - plan.origin[0]) * plan.along[0] + (-z - plan.origin[1]) * plan.along[1];
  const ins = cut.inside.getAttribute('position');
  ok([...Array(ins.count).keys()].every((i) => sOf(ins.getX(i), ins.getZ(i)) >= rect.s[0] - 1e-6 && sOf(ins.getX(i), ins.getZ(i)) <= rect.s[1] + 1e-6
    && ins.getY(i) <= rect.y[1] + 1e-6), 'the man door takes what lies in its frame');
  const manRail = (plan.man.s[1] - dims.ls0 - 0.17) * 0.24;
  ok(near(a1, (plan.man.s[1] - plan.man.s[0] - 0.2) * (plan.man.head - 0.1 - lo - 0.3) + manRail, 1e-6),
    'its own panel and the rail behind it, so the opening it leaves is clear');
  ok(cut.inside.getAttribute('uv') && cut.outside.getAttribute('normal'), 'every attribute carried across the cut');
}

// ---------------------------------------------------------------- the layer
const p = sidecar.placement;
const matrix = new THREE.Matrix4().compose(enuToWorld(p.local_e, p.local_n, BASE),
  new THREE.Quaternion().setFromEuler(new THREE.Euler(0, bearingToYaw(p.rotation_deg ?? 0), 0)), new THREE.Vector3(1, 1, 1));
for (const piece of coach) piece.material = doorLeafMaterial(painted.material);
const registry = new Map([['glessner_house', record]]);
const buildings = { matrixOf: (id) => (id === 'glessner_house' ? matrix : null), doorLeaves: new Map([[plan.id, coach]]) };
const footprints = footprintsFrom(registry);
const decks = [];
const ix = createInteractions();
let visitor = null, reduced = false;
const problems = [];
// The house doors' own layer skips the coach plan (it is this layer's), and carries this one.
const houseDoors = createHouseDoors({ registry, buildings: { matrixOf: buildings.matrixOf, doorLeaves: new Map() }, footprints: [], decks: [], problems: [] });
ok(!houseDoors.get(plan.id), 'the house doors layer does not hang the coach-house doors itself');
const layer = CH.createCoachHouse({ registry, buildings, footprints, decks, interactions: ix, visitor: () => visitor,
  carriageways: grid.carriageways, drives: section.carriage_drives.drives, reducedMotion: () => reduced, problems });
ok(layer && problems.filter((x) => x.startsWith(plan.id)).length === 0, `the doors hang without complaint: ${problems.join('; ')}`);
ok(houseDoors.attach(layer) === layer, 'and ride on the house doors\' frame');
ok(CH.createCoachHouse({ registry: new Map(), buildings }) === null, 'a scene without the coach house has none');
const enu = (u, v, y = 0) => { const w = new THREE.Vector3(u, y, -v).applyMatrix4(matrix); return { e: w.x, n: -w.z, y: w.y }; };
const inv = matrix.clone().invert();
const toPlan = (e, n) => { const w = new THREE.Vector3(e, 0, -n).applyMatrix4(inv); return { d: w.x * plan.outward[0] - w.z * plan.outward[1] - (plan.origin[0] * plan.outward[0] + plan.origin[1] * plan.outward[1]),
  s: (w.x - plan.origin[0]) * plan.along[0] + (-w.z - plan.origin[1]) * plan.along[1] }; };
const at = (d, s) => { const [u, v] = planPoint(plan, d, s); return enu(u, v); };
const run = (seconds, dt = 1 / 60) => { for (let t = 0; t < seconds; t += dt) { ix.update(dt); houseDoors.update(dt); } };
const fp = footprints.find((f) => f.id === 'glessner_house');
ok(fp.doorways?.length === 1 && decks.length === 2 && near(decks[0].y, BASE + plan.sill, 1e-3),
  'the footprint has its doorway, and the doorway and room floors are decks at the sill');
ok(layer.state === 'shut' && layer.manDoor.state === 'shut' && ix.get(plan.id)?.state === 'closed' && ix.get(`${plan.id}:man`)?.state === 'closed',
  'shut to start, both Interact things closed');
ok(layer.room ?? layer.group.getObjectByName(`coach-house-room:${plan.id}`), 'with a dark room behind the doors');
const roomMesh = layer.group.getObjectByName(`coach-house-room:${plan.id}`);
ok(roomMesh.material.isMeshBasicMaterial && roomMesh.geometry.getAttribute('position').count === 8 * 6, 'plain and unlit: eight inward faces');

/** Where a structure-frame point of a hung mesh is now, in the plan's (d, s). */
function nowAt(meshName, d, s, y = 1.5) {
  layer.group.updateMatrixWorld(true);
  const m = layer.group.getObjectByName(meshName);
  const [u, v] = planPoint(plan, d, s);
  const w = new THREE.Vector3(u, y, -v).applyMatrix4(m.matrixWorld);
  return toPlan(w.x, -w.z);
}
const eastName = `coach-house-leaf:east:${coach[0].material.name}`, westName = `coach-house-leaf:west:${coach[0].material.name}`;
const manName = `coach-house-man-door:${coach[0].material.name}`;
ok(layer.group.getObjectByName(eastName) && layer.group.getObjectByName(westName) && layer.group.getObjectByName(manName),
  'the east leaf, the west leaf and the man door cut from the east one are hung');
{
  const shutAt = nowAt(eastName, dims.back, dims.mid);
  ok(near(shutAt.d, dims.back, 1e-6) && near(shutAt.s, dims.mid, 1e-6), 'shut, every leaf is where it was baked');
  visitor = at(3, dims.mid);
  const opened = layer.open();
  run(CH.COACH_SWING_S / 2);
  ok(layer.state === 'opening', 'open() sets them swinging');
  run(CH.COACH_SWING_S / 2 + 0.1);
  const res = await opened;
  ok(res.ok && layer.state === 'open' && ix.get(plan.id).state === 'open', 'and resolves once they stand open; the Interact thing agrees');
  const e = nowAt(eastName, dims.back, dims.mid), w = nowAt(westName, dims.back, dims.mid);
  ok(near(e.d, dims.back - dims.leafWidth, 0.01) && near(e.s, dims.ls0, 0.01), `the east leaf's meeting edge now stands ${(-e.d).toFixed(2)} m inside, on its own jamb`);
  ok(near(w.d, dims.back - dims.leafWidth, 0.01) && near(w.s, dims.ls1, 0.01), 'the west leaf the same on the west jamb: both inward');
  ok((await layer.open()).already, 'opening an open pair is nothing');
  // Close is refused with the visitor in the doorway, and from inside the room.
  visitor = at(-0.6, dims.mid);
  const r1 = await layer.close();
  ok(!r1.ok && r1.refused && /doorway/.test(r1.why) && layer.state === 'open', 'close is refused while the visitor stands in the swing');
  visitor = at(-5, dims.mid);
  ok(/coach house/.test((await layer.close()).why), 'and while they stand in the room');
  visitor = at(3, dims.mid);
  layer.setBlocker((poly) => (poly.length === 4 ? 'The carriage stands in the doorway' : null));
  ok(/carriage/.test((await layer.close()).why), 'and while the ride says its team stands in the swing');
  layer.setBlocker(null);
  const closing = layer.close();
  run(CH.COACH_SWING_S + 0.1);
  ok((await closing).ok && layer.state === 'shut' && ix.get(plan.id).state === 'closed', 'from the street they shut');
  ok(near(nowAt(eastName, dims.back, dims.mid).d, dims.back, 1e-6), 'back in their frame');
}
{
  // The man door, by the Interact key, standing before it.
  const before = at(0.9, (plan.man.s[0] + plan.man.s[1]) / 2);
  visitor = before;
  const keyEl = { hidden: true, textContent: '', dataset: {}, setAttribute() {}, addEventListener() {}, removeEventListener() {} };
  const said = [];
  const key = createInteractKey({ interactions: ix, keyEl, where: () => ({ ...before, bearing: 180, flying: false }), say: (t) => said.push(t) });
  const man = ix.get(`${plan.id}:man`);
  ok(key.refresh() === man && keyEl.textContent === 'Open door', 'before the man door the key offers Open door');
  ok(key.press().ok, 'a press opens it');
  run(CH.MAN_DOOR_SWING_S + 0.1);
  ok(man.state === 'open' && layer.manDoor.state === 'open' && layer.state === 'shut', 'the man door stands open, the leaves shut');
  const latch = nowAt(manName, dims.back, plan.man.s[1] - 0.05);
  ok(latch.d < dims.back - dims.manWidth + 0.1 && near(latch.s, plan.man.s[0], 0.06), `its free edge swung ${(-latch.d).toFixed(2)} m in, on the jamb side`);
  ok(near(nowAt(eastName, dims.back, dims.mid + 0.05).d, dims.back, 1e-6), 'while the rest of its leaf stays shut');
  // Opening the leaves shuts the man door first.
  visitor = at(3, dims.mid);
  const both = layer.open();
  run(CH.MAN_DOOR_SWING_S - 0.1);
  ok(layer.manDoor.state === 'closing' && layer.swing === 0, 'the leaves wait while the man door shuts');
  run(0.15);
  ok(layer.manDoor.state === 'shut' && layer.state === 'opening', 'and start once it is shut');
  run(CH.COACH_SWING_S + 0.1);
  ok((await both).ok && layer.state === 'open', 'then swing open');
  ok(!man.at, 'with the leaves open the man door is not offered');
  ok((await layer.manDoor.open()).refused, 'and will not open');
  const shut = layer.close(); run(CH.COACH_SWING_S + 0.1); await shut;
  // Reduced motion: at once.
  reduced = true;
  const quick = layer.open(); run(1 / 60);
  ok((await quick).ok && layer.state === 'open', 'reduced motion: the doors stand open at the next frame');
  const quickShut = layer.close(); run(1 / 60); await quickShut;
  reduced = false;
  ok(layer.state === 'shut', 'and shut the same way');
}

// ---------------------------------------------------------------- the walker
const southBearing = (180 + (p.rotation_deg ?? 0) + 360) % 360;
function walk(from, bearing, seconds) {
  const camera = new THREE.PerspectiveCamera();
  const w = createWalker({ camera, terrain: flat, footprints, decks, spawn: { local_e: from.e, local_n: from.n, yaw_deg: bearing } });
  const intent = createIntent();
  const trace = [];
  for (let i = 0; i < seconds * 60; i++) {
    intent.forward = 1;
    visitor = { e: w.state.e, n: w.state.n };
    ix.update(1 / 60); houseDoors.update(1 / 60);
    w.update(1 / 60, intent);
    trace.push({ ...toPlan(w.state.e, w.state.n), e: w.state.e, n: w.state.n, ground: w.state.groundY });
  }
  return { w, trace, end: trace.at(-1) };
}
{
  const street = at(3, dims.mid);
  const shut = walk(street, southBearing, 6);
  ok(near(shut.end.d, dims.casingFront + WALK.radius, 0.03) && shut.trace.every((t) => t.d >= dims.casingFront + WALK.radius - 0.02),
    `shut, a walk stops at the leaves (${shut.end.d.toFixed(3)} m)`);
  // Through the man door.
  visitor = at(1, plan.man.s[1] - 0.4);
  const mo = layer.manDoor.open(); run(CH.MAN_DOOR_SWING_S + 0.1); await mo;
  const manMid = (plan.man.s[0] + dims.thick + plan.man.s[1]) / 2;
  const inMan = walk(at(2.5, manMid), southBearing, 9);
  ok(inMan.end.d < dims.back - 4, `through the open man door into the room (${inMan.end.d.toFixed(2)} m)`);
  ok(inMan.trace.every((t) => t.d > dims.casingFront || (t.s >= plan.man.s[0] + dims.thick + WALK.radius - 0.02 && t.s <= plan.man.s[1] - WALK.radius + 0.02) || t.d < dims.back),
    'held off both sides of the man door');
  ok(near(inMan.end.ground, BASE + plan.sill, 1e-3), 'on the room\'s floor, at the sill');
  ok(!(await layer.manDoor.close()).ok, 'the man door will not shut on the visitor inside');
  const outMan = walk(inMan.w.enu, (southBearing + 180) % 360, 12);
  ok(outMan.end.d > 1, 'and back out to the street');
  visitor = outMan.end;
  const mc = layer.manDoor.close(); run(CH.MAN_DOOR_SWING_S + 0.1);
  ok((await mc).ok, 'then it shuts');
  // Through the open leaves.
  const lo2 = layer.open(); run(CH.COACH_SWING_S + 0.1); await lo2;
  const inLeaves = walk(street, southBearing, 14);
  ok(near(inLeaves.end.d, dims.roomBack + 0.05 + WALK.radius, 0.05), `through the open leaves to the room's back wall (${inLeaves.end.d.toFixed(2)} m)`);
  ok(inLeaves.trace.every((t) => t.d > dims.casingFront || (t.s >= dims.ls0 + dims.thick + WALK.radius - 0.02 && t.s <= dims.ls1 - dims.thick - WALK.radius + 0.02) || t.d < dims.leavesBack),
    'between the open leaves');
  const outLeaves = walk(inLeaves.w.enu, (southBearing + 180) % 360, 14);
  ok(outLeaves.end.d > 1, 'and out again');
  visitor = outLeaves.end;
  const lc2 = layer.close(); run(CH.COACH_SWING_S + 0.1); await lc2;
  // Along the façade past the doors: no doorway felt.
  const east = at(WALK.radius + 0.2, dims.j0 - 3);
  const westBearing = (270 + (p.rotation_deg ?? 0) + 360) % 360;
  const along = walk(east, westBearing, 6);
  ok(along.end.s > dims.j1 + 1, 'a walk along 18th Street passes the doors');
  ok(Math.max(...along.trace.slice(1).map((t, i) => Math.abs(t.d - along.trace[i].d))) < 0.01, 'without being pulled into them');
  ok(outlineAt(fp, east.e + 30, east.n) === fp.pts, 'beyond the doors\' zone the footprint is its own');
}

// ---------------------------------------------------------------- the way in
const row = loops.rows.find((r) => r.id === 'prairie_driven_brougham_loop_1904');
ok(row && row.steering_limit_deg === 15 && row.wheelbase_m === CH.BROUGHAM.wheelbase_m
  && row.envelope_measured_local_xz_m.every((x, i) => x === CH.BROUGHAM.envelope_measured_local_xz_m[i]), 'the brougham row is the default team');
const kMax = Math.tan(row.steering_limit_deg * DEG) / row.wheelbase_m;
const drive = section.carriage_drives.drives.find((x) => x.id === 'prairie_1800.carriage_drive');
ok(Math.hypot(drive.origin[0] - layer.frame.origin[0], drive.origin[1] - layer.frame.origin[1]) < 0.05, 'the drive\'s line is the doorway\'s');
ok(near(layer.frame.kerb, drive.ramp_from_m, 1e-9) && layer.frame.farKerb > layer.frame.kerb + 11, `18th Street, kerb to kerb, ${(layer.frame.farKerb - layer.frame.kerb).toFixed(2)} m before the doors`);
const roadReader = createCarriagewayReader(grid.carriageways);
const inPoly = CH.insidePoly;
const roads = grid.carriageways.map((c) => c.polygon_local_m);
const onRoad = (e, n) => roads.some((q) => inPoly(e, n, q));
const onDrive = (e, n) => [drive.flat, drive.ramp].some((q) => inPoly(e, n, q));
const dsOf = (e, n) => toPlan(e, n);
const onFloor = (e, n) => { const { d, s } = dsOf(e, n); return d <= 0.02 && CH.allowedInside(dims, Math.min(d, 0), s); };
const ground = (e, n) => onRoad(e, n) || onDrive(e, n) || onFloor(e, n);
const D = Math.SQRT1_2;
const ringOn = ([e, n], r) => [[0, 0], [r, 0], [-r, 0], [0, r], [0, -r], [r * D, r * D], [-r * D, r * D], [r * D, -r * D], [-r * D, -r * D]].every(([a, b]) => ground(e + a, n + b));
const roomOf = (q) => { let lo3 = 0, hi3 = 3; if (!ringOn(q, 0)) return -1; while (hi3 - lo3 > 0.005) { const m = (lo3 + hi3) / 2; if (ringOn(q, m)) lo3 = m; else hi3 = m; } return lo3; };
const rootPose = (way, i) => {
  const [e, n] = way.points_enu_m[i], yaw = way.yaw_rad[i], ra = row.root_ahead_of_rear_axle_m;
  return { e: e + Math.sin(yaw) * ra, n: n - Math.cos(yaw) * ra, yaw, steering: Math.atan(row.wheelbase_m * way.curvature_per_m[i]) };
};
const LINTEL = 12.6 * FT, CASING_HEAD = plan.head - plan.casing - plan.sill;
// The tallest thing on the team: the coachman's top hat (seat 1.776 m, brougham row; seated eye
// 0.78 m over the cushion, its passenger_basis; hat base 0.10 m over the eye; crown 0.152 m,
// data/humans/wardrobes/anonymous_working_driver_1904.json) = 2.81 m, taken as 2.85. The coach
// itself is 2.19 m (brougham-near.glb accessor bounds) and the horses 1.79 m (horse GLB bounds).
const TALLEST = 2.85;
for (const from of ['east', 'west']) {
  const way = layer.drivePath({ from });
  ok(way && way.points_enu_m.length > 100 && way.points_enu_m.length === way.yaw_rad.length, `from the ${from}: a way of ${way.points_enu_m.length} samples, ${way.length_m.toFixed(1)} m`);
  ok(way.inside_enu_m === way.points_enu_m.at(-1) && near(way.heading_in_deg, (180 + (p.rotation_deg ?? 0) + 360) % 360, 0.01),
    `ending at the stand inside, heading ${way.heading_in_deg.toFixed(2)} degrees`);
  const steps = way.points_enu_m.slice(1).map((q, i) => Math.hypot(q[0] - way.points_enu_m[i][0], q[1] - way.points_enu_m[i][1]));
  ok(Math.max(...steps) <= CH.PATH_STEP_M + 1e-6 && Math.min(...steps) > 0.05, 'samples at most a quarter metre apart');
  // Each chord's bearing is its two ends' headings' mean (an exact arc); a straight's, its own.
  const chordErr = Math.max(...way.points_enu_m.slice(1).map((q, i) => {
    const q0 = way.points_enu_m[i], chord = Math.atan2(q[0] - q0[0], -(q[1] - q0[1]));
    const mean = way.yaw_rad[i] + Math.atan2(Math.sin(way.yaw_rad[i + 1] - way.yaw_rad[i]), Math.cos(way.yaw_rad[i + 1] - way.yaw_rad[i])) / 2;
    return Math.abs(Math.atan2(Math.sin(chord - mean), Math.cos(chord - mean)));
  }));
  ok(chordErr < 0.01 * DEG, `the headings are the line's own (${(chordErr / DEG).toExponential(1)} degrees)`);
  ok(way.max_curvature_per_m <= kMax && way.max_steering_deg < row.steering_limit_deg,
    `every lock inside the brougham's: at most ${way.max_steering_deg.toFixed(2)} of ${row.steering_limit_deg} degrees (radius ${(1 / way.max_curvature_per_m).toFixed(2)} m, the lock's ${(1 / kMax).toFixed(2)} m)`);
  // The bicycle model drives it on its own curvature.
  let s = sampleOf(...way.points_enu_m[0], way.yaw_rad[0], way.curvature_per_m[0]), drift = 0;
  for (let i = 1; i < way.points_enu_m.length; i += 1) {
    // Each step is driven on the curvature of the stretch it covers (its end sample's, as every
    // arc's samples carry it, a straight's 0).
    s = bicycleStep(s, Math.atan(row.wheelbase_m * way.curvature_per_m[i]), steps[i - 1], row.wheelbase_m);
    drift = Math.max(drift, Math.hypot(s.e - way.points_enu_m[i][0], s.n - way.points_enu_m[i][1]));
  }
  ok(drift < 0.01, `the bicycle model, steered on the way's own curvature, stays within ${(drift * 100).toFixed(2)} cm of it to the stand`);
  // Every wheel and hoof on the carriageway, the drive or the floor, with the kerb rule's room.
  let wheelM = Infinity, hoofM = Infinity, refusedByKerb = 0, refusedByWalls = 0;
  const clearance = createTransportClearance({ footprints: () => footprints, envelope_local_xz_m: row.envelope_local_xz_m });
  for (let i = 0; i < way.points_enu_m.length; i += 1) {
    const pose = rootPose(way, i);
    const { wheels, hooves } = teamGroundPoints(row, pose);
    for (const q of wheels) wheelM = Math.min(wheelM, roomOf(q) - KERB_ROOM_M.wheel);
    for (const q of hooves) hoofM = Math.min(hoofM, roomOf(q) - KERB_ROOM_M.hoof);
    if (!roadReader(row, pose)) refusedByKerb += 1;
    if (!clearance(pose, pose)) refusedByWalls += 1;
  }
  ok(wheelM > 0 && hoofM > 0, `every wheel (${wheelM.toFixed(2)} m to spare) and hoof (${hoofM.toFixed(2)} m) stays on the carriageway, the drive or the floor, beyond the kerb rule's room`);
  ok(refusedByKerb > 20 && refusedByWalls > 10, `which the kerb rule (${refusedByKerb} poses) and the footprint clearance (${refusedByWalls}) alone refuse`);
  // The measured envelope through the doorway, between the open leaves, into the room.
  let mReveal = Infinity, mCasing = Infinity, mLeaves = Infinity, mRoom = Infinity, mBack = Infinity;
  for (let i = 0; i < way.points_enu_m.length; i += 1) {
    for (const poly of CH.teamOutline(row, rootPose(way, i), 0)) for (const [e, n] of CH.polygonSamples(poly, 0.02, 1)) {
      const { d, s: ss } = dsOf(e, n);
      if (d > 0) continue;
      if (d >= dims.back) {
        mCasing = Math.min(mCasing, ss - dims.ls0, dims.ls1 - ss);
        mReveal = Math.min(mReveal, ss - (dims.j0 + (dims.j1 - dims.j0 - reveal119) / 2), (dims.j1 - (dims.j1 - dims.j0 - reveal119) / 2) - ss);
      } else if (d >= dims.leavesBack) mLeaves = Math.min(mLeaves, ss - dims.ls0 - dims.thick, dims.ls1 - dims.thick - ss);
      else { mRoom = Math.min(mRoom, ss - dims.r0, dims.r1 - ss); mBack = Math.min(mBack, d - dims.roomBack); }
    }
  }
  ok(mReveal > 0.3 && mCasing > 0.3 && mLeaves > 0.3 && mRoom > 0.3 && mBack > 0.3,
    `the measured envelope clears the 11.9-ft doorway by ${mReveal.toFixed(2)} m a side, the casing by ${mCasing.toFixed(2)}, the open leaves by ${mLeaves.toFixed(2)}, the room's walls by ${mRoom.toFixed(2)} and its back by ${mBack.toFixed(2)}`);
  report.push({ from, mReveal, mCasing, mLeaves, wheelM, hoofM, steer: way.max_steering_deg, length: way.length_m, drift: way.drift_deg });
  // At the stand: all of it inside, behind the leaves' swing, so they can shut.
  const stand = CH.teamOutline(row, rootPose(way, way.points_enu_m.length - 1), 0).flat().map(([e, n]) => dsOf(e, n));
  ok(stand.every((q) => q.d < dims.back - dims.leafWidth - 0.1 && q.d > dims.roomBack), `at the stand the whole team is inside, ${(-Math.max(...stand.map((q) => q.d)) - (-(dims.back - dims.leafWidth))).toFixed(2)} m behind the leaves' swing`);
  // The lintel over the tallest of it.
  ok(LINTEL - TALLEST > 0.9 && CASING_HEAD - TALLEST > 0.7, `under the 12.6-ft lintel by ${(LINTEL - TALLEST).toFixed(2)} m (the casing's head by ${(CASING_HEAD - TALLEST).toFixed(2)})`);

  // ---- clearFor
  ok(layer.state === 'shut' && !layer.clearFor(row, rootPose(way, way.face_index), rootPose(way, way.face_index + 1)), 'with the leaves shut the doorway is a wall');
}
{
  const lo4 = layer.open(); run(CH.COACH_SWING_S + 0.1); await lo4;
  for (const from of ['east', 'west']) {
    const way = layer.drivePath({ from });
    let admitted = 0, mine = 0;
    for (let i = 0; i < way.points_enu_m.length; i += 1) {
      const a = rootPose(way, i), b = rootPose(way, Math.min(i + 1, way.points_enu_m.length - 1));
      const road = roadReader(row, a);
      const own = layer.clearFor(row, a, b);
      if (own) mine += 1;
      if (road || own) admitted += 1;
    }
    ok(admitted === way.points_enu_m.length, `from the ${from}, the kerb rule or clearFor admits every step of the way (${mine} of them clearFor's)`);
    const face = rootPose(way, way.face_index);
    ok(!layer.clearFor(row, { ...face, e: face.e + 0.8 }), 'a team 0.8 m off the line at the doors hits a jamb');
    ok(!layer.clearFor(row, { ...face, yaw: face.yaw + 25 * DEG }), 'nor one slewed 25 degrees');
    const lane = rootPose(way, 0);
    ok(!layer.clearFor(row, lane), 'out in the lane it is not the coach house\'s to admit');
  }
  ok(!layer.clearFor(row, { e: layer.frame.origin[0] + 20, n: layer.frame.origin[1] - 3, yaw: 0, steering: 0 }), 'nor anywhere off the way');
  ok(near(layer.floorAt(...layer.drivePath().inside_enu_m), BASE + plan.sill, 1e-3) && layer.floorAt(layer.frame.origin[0] + 30, layer.frame.origin[1]) === null,
    'the floor under the stand is the sill\'s height, and nothing outside');
}

// ---------------------------------------------------------------- rebind and dispose
{
  const again = coach.map((x) => ({ ...x }));
  layer.rebind({ matrixOf: buildings.matrixOf, doorLeaves: new Map([[plan.id, again]]) });
  ok(layer.group.getObjectByName(manName) && layer.state === 'open', 'a rebuilt house\'s leaves are hung in place, still open');
  houseDoors.dispose();
  ok(!ix.get(plan.id), 'and freed with the house doors');
}

for (const r of report) {
  console.log(`  from ${r.from}: ${r.length.toFixed(1)} m, drift ${r.drift.toFixed(1)} deg, lock ${r.steer.toFixed(2)} deg; `
    + `doorway ${r.mReveal.toFixed(2)} m (11.9 ft) / casing ${r.mCasing.toFixed(2)} / open leaves ${r.mLeaves.toFixed(2)} m a side; `
    + `kerb room to spare: wheels ${r.wheelM.toFixed(2)}, hooves ${r.hoofM.toFixed(2)} m`);
}
console.log(`PASS: ${checks} checks — Glessner's coach-house doors swing, the man door lets people in, and a carriage has a drivable way in (T-3557)`);

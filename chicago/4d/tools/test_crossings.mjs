#!/usr/bin/env node
/**
 * test_crossings.mjs — the 1812 crossing boats and Cross (T-3510).
 *
 * Builds every boat in data/boats/crossings_1812.json on the committed 1812 ground (the box
 * heightfield and the South Branch apron, read the way terrain.js reads them), then drives
 * Cross through the real interaction engine with a real walker, both ways, for every boat:
 *
 *   - every hull is built, no two alike (length, beam, depth and colour all differ by boat);
 *   - a hull at rest lies with its bow on the bank and its stern afloat, and its keel never
 *     sinks more than a few centimetres into the ground or below its own draft;
 *   - Cross runs its five steps in order and lands the boat on the far bank, where it stays;
 *     the visitor is on the seat over open water mid-way, and set down on dry ground at the
 *     far bank's stand, on foot, at the end; Cross from there brings boat and visitor back;
 *   - while one boat is crossing, another refuses ("Already in a boat");
 *   - the layer adds no texture of its own: its materials hold only sheets other layers
 *     loaded (none here, so the hulls fall back to their vertex colour).
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export async function resolve(s, c, n) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return n(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { createCrossings, buildBoat, buildWharfDeck } = await import('../renderers/web/js/crossings.js');
const { createInteractions } = await import('../renderers/web/js/interact.js');
const { createWalker, WALK } = await import('../renderers/web/js/walker.js');
const { createIntent } = await import('../renderers/web/js/controls/intent.js');

const ROOT = new URL('../', import.meta.url);
const read = (p) => JSON.parse(fs.readFileSync(new URL(p, ROOT), 'utf8'));
const doc = read('data/boats/crossings_1812.json');

// --- the 1812 ground, as terrain.js samples it -------------------------------------------
function grid(name) {
  const meta = read(`data/terrain/epochs/e1830_natural/${name}`);
  const buf = fs.readFileSync(new URL(`data/terrain/epochs/e1830_natural/${meta.bin}`, ROOT));
  const vals = new Int16Array(buf.buffer, buf.byteOffset, meta.rows * meta.cols);
  return { meta, vals };
}
const box = grid('heightfield.json');
const apron = grid('apron_south_branch.json');
function bil({ meta, vals }, e, n) {
  const c = (e - meta.origin_e) / meta.cell_m, r = (n - meta.origin_n) / meta.cell_m;
  const c0 = Math.floor(c), r0 = Math.floor(r);
  if (c0 < 0 || r0 < 0 || c0 + 1 >= meta.cols || r0 + 1 >= meta.rows) return null;
  const fc = c - c0, fr = r - r0, C = meta.cols;
  const v = (rr, cc) => vals[rr * C + cc];
  return ((v(r0, c0) * (1 - fc) + v(r0, c0 + 1) * fc) * (1 - fr)
    + (v(r0 + 1, c0) * (1 - fc) + v(r0 + 1, c0 + 1) * fc) * fr) * meta.scale + meta.offset;
}
function height(e, n) {
  const m = box.meta;
  const inBox = e >= m.origin_e && e <= m.origin_e + (m.cols - 1) * m.cell_m
    && n >= m.origin_n && n <= m.origin_n + (m.rows - 1) * m.cell_m;
  if (inBox) return bil(box, e, n);
  const cut = apron.meta.cut_local_enu_m;
  if (e >= cut.e[0] && e <= cut.e[1] && n >= cut.n[0] && n <= cut.n[1]) return bil(apron, e, n) ?? 0;
  return 0;
}
const terrain = {
  surfaceHeight: (e, n) => height(e, n) ?? 0,
  walkHeight: (e, n) => height(e, n) ?? 0,
  isWater: (e, n) => (height(e, n) ?? 1) < 0,
};

// --- fetch for the layer's one file -------------------------------------------------------
globalThis.fetch = async (url) => {
  const u = new URL(url);
  if (u.pathname.endsWith('boats/crossings_1812.json')) {
    return { ok: true, status: 200, json: async () => doc };
  }
  return { ok: false, status: 404, json: async () => ({}) };
};

let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks += 1; };

// 1. Every hull builds, and no two are alike.
const seen = new Set();
for (const boat of doc.boats) {
  const b = buildBoat(boat);
  const tris = (b.wood.pos.length + (b.bark?.pos.length ?? 0)) / 9;
  ok(tris > 400 && tris < 9000, `${boat.id}: ${tris} triangles is outside 400..9000`);
  const xs = [];
  const src = b.bark ?? b.wood;
  for (let k = 0; k < src.pos.length; k += 3) xs.push(src.pos[k]);
  const span = Math.max(...xs) - Math.min(...xs);
  ok(Math.abs(span - boat.hull.length_m) < 0.08 * boat.hull.length_m, `${boat.id}: hull spans ${span.toFixed(2)} m, not its ${boat.hull.length_m} m`);
  const sig = [boat.hull.length_m, boat.hull.beam_m, boat.hull.depth_m, ...(boat.look.tone ?? [])].join('|');
  ok(!seen.has(sig), `${boat.id}: the same hull and colour as another boat`);
  seen.add(sig);
  // The water lid closes the hollow above the waterline, inside the hull's beam.
  ok(b.mask.length >= 9 * 20, `${boat.id}: no water lid over the hollow`);
  let lidLow = Infinity, lidWide = 0;
  for (let k = 0; k < b.mask.length; k += 3) { lidLow = Math.min(lidLow, b.mask[k + 1]); lidWide = Math.max(lidWide, Math.abs(b.mask[k + 2])); }
  ok(lidLow > boat.hull.draft_m + 0.08, `${boat.id}: the water lid dips to ${lidLow.toFixed(3)}, near the waterline`);
  ok(lidWide < boat.hull.beam_m / 2, `${boat.id}: the water lid is wider than the hull`);
  const coarse = buildBoat(boat, { coarse: true });
  ok((coarse.wood.pos.length + (coarse.bark?.pos.length ?? 0)) < (b.wood.pos.length + (b.bark?.pos.length ?? 0)), `${boat.id}: the coarse hull is not lighter`);
}

// 2. The layer, the walker and Cross.
const problems = [];
const camera = new THREE.PerspectiveCamera();
const interactions = createInteractions();
const rides = [];
const crossings = await createCrossings({
  dataBase: 'http://x/data/', terrain, problems, walkEye: () => WALK.eyeHeight,
  onRide: (boat, on) => rides.push([boat.boat.id, on]),
});
ok(problems.length === 0, `problems: ${problems.join('; ')}`);
ok(crossings.boats.length === doc.boats.length, 'not every boat was drawn');
for (const thing of crossings.things) interactions.add(thing);
ok(crossings.keepOut.length >= doc.boats.length, 'drawn-up hulls keep the grass out');

// No texture of the layer's own: the meshes' maps can only be sheets other layers loaded.
crossings.group.traverse((o) => {
  if (!o.isMesh) return;
  ok(!o.material.map && !o.material.normalMap, `${o.name}: a sheet bound with no other layer having loaded one`);
});

// Resting poses: bow on the bank, stern afloat, keel not buried.
for (const entry of crossings.boats) {
  for (const bank of ['a', 'b']) {
    const r = entry.boat.banks[bank].rest;
    const pose = entry.rest[bank];
    const L = entry.boat.hull.length_m;
    const b = r.bearing * Math.PI / 180;
    const bowH = height(r.e + Math.sin(b) * 0.45 * L, r.n + Math.cos(b) * 0.45 * L);
    const sternH = height(r.e - Math.sin(b) * 0.45 * L, r.n - Math.cos(b) * 0.45 * L);
    if (!r.afloat) {
      ok(bowH >= 0, `${entry.boat.id} ${bank}: its bow is not on the bank (${bowH})`);
      ok(sternH < 0, `${entry.boat.id} ${bank}: its stern is not afloat (${sternH})`);
    }
    ok(pose.y > -(entry.boat.hull.draft_m + 0.05), `${entry.boat.id} ${bank}: keel below its draft`);
    ok(Math.abs(pose.pitch) < 14 * Math.PI / 180, `${entry.boat.id} ${bank}: pitched ${pose.pitch}`);
    const st = entry.boat.banks[bank].stand;
    // A stand on the wharf is its deck (a walk surface the real walker reads), not ground.
    if (!entry.boat.banks[bank].wharf) ok(height(st[0], st[1]) > 0.03, `${entry.boat.id} ${bank}: the stand is not dry ground`);
  }
}

const footprints = [];
const walker = createWalker({ camera, terrain, footprints, decks: [], spawn: { local_e: 0, local_n: 0, yaw_deg: 0 } });
const intent = createIntent ? createIntent() : null;

function stepWorld(dt) {
  interactions.update(dt);
  if (intent) walker.update(dt, intent);
  crossings.holdVisitor(walker, WALK);
  crossings.update(dt, camera);
}

function cross(entry, from, to) {
  const thing = crossings.things.find((t) => t.id === `boat:${entry.boat.id}`);
  const stand = entry.boat.banks[from].stand;
  walker.teleport({ local_e: stand[0], local_n: stand[1], yaw_deg: 0 });
  crossings.update(0, camera);
  const near = interactions.nearest(walker.state.e, walker.state.n, null);
  ok(near === thing, `${entry.boat.id}: standing at bank ${from}, the nearest thing is ${near?.id ?? 'nothing'}`);
  ok(thing.state === from, `${entry.boat.id}: the boat is not at bank ${from}`);
  const res = interactions.act(thing);
  ok(res.ok, `${entry.boat.id}: Cross refused at ${from}: ${res.why}`);
  const labels = [];
  let midWater = false, t = 0, maxGap = 0, last = null;
  const total = 2 + (entry.boat.crossing.seconds ?? 30) + 12;
  while (thing.running && t < total + 30) {
    stepWorld(0.05);
    t += 0.05;
    const r = thing.running;
    if (r && labels[labels.length - 1] !== r.action.steps[r.index].label) labels.push(r.action.steps[r.index].label);
    if (r && r.index === 2 && r.t > 0.4 && r.t < 0.6) {
      midWater = midWater || terrain.isWater(walker.state.e, walker.state.n);
      const y = walker.state.eyeY;
      ok(y > 0.5 && y < 1.4, `${entry.boat.id}: the seated eye mid-river is ${y.toFixed(2)} m above the water`);
    }
    if (last) maxGap = Math.max(maxGap, Math.hypot(walker.state.e - last[0], walker.state.n - last[1]));
    last = [walker.state.e, walker.state.n];
  }
  stepWorld(0.05);
  ok(!thing.running, `${entry.boat.id}: Cross did not finish in ${t.toFixed(1)} s`);
  ok(labels.length === 5, `${entry.boat.id}: steps ${labels.join(' > ')}`);
  ok(midWater, `${entry.boat.id}: the visitor was not over the water mid-way`);
  ok(maxGap < 0.6, `${entry.boat.id}: the eye jumped ${maxGap.toFixed(2)} m in a frame`);
  ok(thing.state === to, `${entry.boat.id}: the boat is not left at bank ${to}`);
  ok(entry.bank === to, `${entry.boat.id}: the layer did not move the boat to ${to}`);
  const st = entry.boat.banks[to].stand;
  ok(Math.hypot(walker.state.e - st[0], walker.state.n - st[1]) < 0.3, `${entry.boat.id}: the visitor is not set down at bank ${to}'s stand`);
  ok(!walker.state.flying && Math.abs(walker.state.eyeY - (height(st[0], st[1]) + WALK.eyeHeight)) < 0.05, `${entry.boat.id}: not standing on the far bank`);
  ok(crossings.riding === null, `${entry.boat.id}: still riding`);
}

for (const entry of crossings.boats) {
  cross(entry, 'a', 'b');
  cross(entry, 'b', 'a');
}
ok(rides.length === 4 * crossings.boats.length, `onRide told ${rides.length} times`);

// Two at once: the second refuses.
const [e1, e2] = crossings.boats;
const t1 = crossings.things.find((t) => t.id === `boat:${e1.boat.id}`);
const t2 = crossings.things.find((t) => t.id === `boat:${e2.boat.id}`);
interactions.act(t1);
stepWorld(0.05);
const second = interactions.act(t2);
ok(!second.ok && /Already in a boat/.test(second.why ?? ''), 'a second boat started while the first was crossing');
while (t1.running) stepWorld(0.1);

// The fort wharf's puncheon deck covers its crib top, a few centimetres proud, and no more.
for (const wharf of doc.wharves ?? []) {
  const deck = buildWharfDeck(wharf);
  const tris = deck.pos.length / 9;
  ok(tris > 400 && tris < 6000, `${wharf.id}: the deck has ${tris} triangles`);
  let lo = Infinity, hi = -Infinity;
  for (let i = 1; i < deck.pos.length; i += 3) { lo = Math.min(lo, deck.pos[i]); hi = Math.max(hi, deck.pos[i]); }
  ok(hi > wharf.deck_m && hi < wharf.deck_m + 0.06, `${wharf.id}: the deck's top is at ${hi.toFixed(3)}`);
  ok(lo > wharf.deck_m - 0.1, `${wharf.id}: the deck hangs to ${lo.toFixed(3)}`);
  ok(buildWharfDeck(wharf, { coarse: true }).pos.length < deck.pos.length, `${wharf.id}: the coarse deck is no lighter`);
}
ok((doc.wharves ?? []).length === 1, 'the fort wharf has no deck row');

// A card for a boat at rest.
const cardEntry = crossings.boats.find((e) => e.boat.existence.confidence === 'attested');
ok(!!cardEntry, 'no attested boat to card');

console.log(`test_crossings: ${checks} checks pass — ${crossings.boats.length} boats crossed both ways`);

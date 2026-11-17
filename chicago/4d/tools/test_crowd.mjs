// SPDX-License-Identifier: GPL-3.0-or-later
// T-3555: the town at a distance (renderers/web/js/crowd.js, traffic-cards.js, and the day's
// `outdoors` reader in human-days.js). Checks, on the real modules:
//  - every distance has a tier, with no gap and no double: a person not built is drawn from
//    the middle tier's near edge out to the far edge, the middle body and the card handed
//    over at one boundary, held across it by the hysteresis; a built figure is a card only
//    past its own drawing range;
//  - the eased weights are complementary (never both whole, never summing past one);
//  - a templated town's span read one at a time (templateSpanAt) is the span its whole day
//    (`entry.day`) gives, for every 1835 townsperson at every half hour, and makes no day;
//  - `outdoors` returns only people out, not built, nearest first, inside the reach asked for;
//  - a shared body merged from a stand-in figure: one point per cell, inner layers folded
//    under outer ones, a walk texture of WALK_FRAMES + 1 frames, and an idle frame at rest;
//  - a team's card kind is its vehicle file (light on a coarse device) and its horse.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

const threeURL = process.env.C4D_THREE_MODULE
  ? pathToFileURL(process.env.C4D_THREE_MODULE).href
  : new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
const { register } = await import('node:module');
register('data:text/javascript,' + encodeURIComponent(`
  import { readFile } from 'node:fs/promises';
  export async function resolve(s,c,n) {
    if(s==='three') return {url:${JSON.stringify(threeURL)},shortCircuit:true};
    if(s.startsWith('three/addons/')) return {url:${JSON.stringify(new URL('./addons/', threeURL).href)}+s.slice(13),shortCircuit:true};
    return n(s,c);
  }
  export async function load(u,c,n) {
    if(u.startsWith('file:')&&u.endsWith('.js'))
      return {format:'module',source:await readFile(new URL(u),'utf8'),shortCircuit:true};
    return n(u,c);
  }
`), import.meta.url);

const THREE = await import(threeURL);
const crowd = await import(new URL('../renderers/web/js/crowd.js', import.meta.url).href);
const days = await import(new URL('../renderers/web/js/human-days.js', import.meta.url).href);
const traffic = await import(new URL('../renderers/web/js/traffic-cards.js', import.meta.url).href);
const { MID, FAR, HYST_M, tierTargets, tierWeights, buildCrowdBody, WALK_FRAMES, MERGE_M } = crowd;
let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks++; };

// ── tiers: no gap, no double, held across each boundary ────────────────────────────────────
for (const tier of ['full', 'balanced', 'light']) {
  const [m0, m1] = MID[tier], f1 = FAR[tier];
  ok(m0 < m1 && m1 < f1, `${tier}: near < middle's far edge < far edge`);
  let was = { v: 0, t: 0 };
  for (let d = 0; d <= f1 + 20; d += 0.25) {
    const g = tierTargets(d, tier, { was: null });
    if (d < m0) ok(g.v === 0, `${tier}: nobody drawn at ${d} m, under the middle's near edge`);
    else if (d < f1) ok(g.v === 1, `${tier}: someone at ${d} m is drawn`);
    else ok(g.v === 0, `${tier}: nobody drawn past the far edge (${d} m)`);
    if (g.v) ok(g.t === (d > m1 + HYST_M ? 1 : 0), `${tier}: at ${d} m, coming from nowhere, ${d > m1 + HYST_M ? 'a card' : 'the middle body'}`);
    was = tierTargets(d, tier, { was });
  }
  // Held: a card stays a card until HYST_M inside the boundary, and a body a body until past it.
  ok(tierTargets(m1 - HYST_M + 0.5, tier, { was: { v: 1, t: 1 } }).t === 1, `${tier}: a card is held just inside the boundary`);
  ok(tierTargets(m1 + HYST_M - 0.5, tier, { was: { v: 1, t: 0 } }).t === 0, `${tier}: a body is held just past the boundary`);
  ok(tierTargets(m0 - HYST_M + 0.5, tier, { was: { v: 1, t: 0 } }).v === 1, `${tier}: someone drawn is held just inside the near edge`);
  // Built figures: only a card, and only past their own range.
  ok(tierTargets(100, tier, { built: true, drawM: 140 }).v === 0, `${tier}: a built figure in its range is humans.js's`);
  const b = tierTargets(150, tier, { built: true, drawM: 140 });
  ok(b.v === 1 && b.t === 1, `${tier}: a built figure past its range is a card`);
}
for (let v = 0; v <= 1; v += 0.125) for (let t = 0; t <= 1; t += 0.125) {
  const w = tierWeights(v, t);
  ok(w.mid >= 0 && w.far >= 0 && w.mid + w.far <= v + 1e-9, `weights at v ${v} t ${t} never sum past v`);
}

// ── the day, read one span at a time ───────────────────────────────────────────────────────
const inside = JSON.parse(fs.readFileSync(new URL('../data/humans/inside_1835.json', import.meta.url), 'utf8'));
const routines = inside.routines;
const sample = inside.people.filter((x, i) => x.routine && i % 7 === 0);
ok(sample.length > 300, `a sample of 1835's templated townspeople (${sample.length})`);
const raw = new Set(sample.map((x) => Object.prototype.hasOwnProperty.call(x, 'day')));
ok(!raw.has(true), 'the file holds no day (they are templates)');
const dates = ['1835-07-01', '1835-01-15', '1835-10-01'];
let compared = 0;
// The whole-day path, on copies, so the originals keep no day.
const copies = JSON.parse(JSON.stringify({ routines, people: sample }));
days.expandInside(copies);
for (const [i, x] of sample.entries()) {
  for (const date of dates) for (let h = 0; h < 24; h += 0.5) {
    const one = days.templateSpanAt(routines[x.routine], x, date, h);
    const whole = days.spanAt(days.dayOn(copies.people[i], date, x.person), h);
    assert.deepEqual(one, whole, `${x.person} ${date} ${h}h: one span read alone is its day's`);
    compared++;
  }
}
checks++;
ok(compared === sample.length * dates.length * 48, `compared ${compared} spans`);
ok(sample.every((x) => !Object.prototype.hasOwnProperty.call(x, 'day')), 'reading one span made no day on the entry');

// `outdoors`: out, not built, nearest first, in reach.
{
  const town = JSON.parse(JSON.stringify({ routines, people: inside.people.slice(0, 600) }));
  const humansStub = { shown: true, actors: [], crowdKept: null, keeps: () => true, isHeld: () => false };
  const layer = days.createHumanDays({ humans: humansStub, hour: () => 12.5, date: () => '1835-07-01', inside: town, doors: { structures: [] } });
  const v = { e: 500, n: -190 };
  const out = layer.outdoors(v, 300, 5000);
  ok(out.length > 0, `someone of the town is out at half past noon (${out.length})`);
  ok(out.every((o, i) => i === 0 || o.d >= out[i - 1].d), 'nearest first');
  ok(out.every((o) => o.d <= 300 && o.asset_id && Number.isFinite(o.at.e)), 'each within reach, with a dress and a place');
  for (const o of out.slice(0, 40)) {
    const x = town.people.find((p) => p.person === o.person);
    const s = days.templateSpanAt(routines[x.routine], x, '1835-07-01', 12.5);
    ok(s && !s.indoors && !s.away, `${o.person} is out by their own day`);
  }
  ok(layer.outdoors(v, 300, 5).length === 5, 'a limit keeps the nearest only');
  humansStub.shown = false;
  ok(layer.outdoors(v, 300).length === 0, 'Show › People hidden: nobody is read');
}

// ── a shared body, merged ──────────────────────────────────────────────────────────────────
{
  // A stand-in figure: a body (skin) and a coat over it 1 cm out, one bone, a walk that sways.
  const bone = new THREE.Bone(); bone.name = 'root';
  const mk = (name, mat, r, color) => {
    const g = new THREE.CylinderGeometry(r, r, 1.6, 24, 16).translate(0, 0.8, 0);
    const n = g.attributes.position.count;
    g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Uint16Array(n * 4), 4));
    const w = new Float32Array(n * 4); for (let i = 0; i < n; i++) w[i * 4] = 1;
    g.setAttribute('skinWeight', new THREE.BufferAttribute(w, 4));
    const m = new THREE.MeshStandardMaterial({ color }); m.name = mat;
    const mesh = new THREE.SkinnedMesh(g, m); mesh.name = name;
    return mesh;
  };
  const body = mk('fig_body_lod3', 'skin', 0.2, 0xd0a080);
  const coat = mk('fig_coat_lod3', 'garment_outer__coat', 0.21, 0x202840);
  const scene = new THREE.Group();
  scene.add(bone, body, coat);
  const skeleton = new THREE.Skeleton([bone]);
  body.bind(skeleton); coat.bind(skeleton);
  const walk = new THREE.AnimationClip('walk', 1, [new THREE.VectorKeyframeTrack('root.position', [0, 0.5, 1], [0, 0, 0, 0.1, 0, 0, 0, 0, 0])]);
  const idle = new THREE.AnimationClip('idle', 1, [new THREE.VectorKeyframeTrack('root.position', [0, 1], [0, 0, 0, 0, 0, 0])]);
  const made = buildCrowdBody({ scene, animations: [walk, idle] }, { cell: 0.07 });
  ok(made && made.reps > 0 && made.triangles > 0, `a body is made (${made?.reps} points, ${made?.triangles} triangles)`);
  const all = body.geometry.attributes.position.count + coat.geometry.attributes.position.count;
  ok(made.reps < all / 3, `clustered: ${made.reps} of ${all} points`);
  const region = made.geometry.attributes.aRegion.array;
  const skinShare = region.filter((r) => r === 1).length / region.length;
  ok(skinShare < 0.15, `the body under the coat is folded into it (skin points ${(skinShare * 100).toFixed(1)}%, MERGE_M ${MERGE_M} m)`);
  ok(made.vat.image.width * made.vat.image.height >= made.reps * (WALK_FRAMES + 1), 'the walk texture holds every frame');
  const half = (i) => THREE.DataUtils.fromHalfFloat(made.vat.image.data[i]);
  // Frame 4 of 8 is the walk's half: swayed 0.1 m in x from its idle place.
  const p0 = made.geometry.attributes.position.array;
  const dx = half((4 * made.reps + 0) * 4) - p0[0];
  ok(Math.abs(dx - 0.1) < 0.01, `the walk's middle frame is swayed by the clip (${dx.toFixed(3)} m)`);
  ok(Math.abs(made.height - 1.6) < 0.05, `its height is the figure's (${made.height.toFixed(2)} m)`);
}

// ── teams ──────────────────────────────────────────────────────────────────────────────────
{
  const row = { vehicle_file: 'a/near.glb', vehicle_file_light: 'a/mid.glb', horse_model: 'h' };
  ok(traffic.teamKind(row) === 'a/near.glb|h', 'a team kind is its vehicle and horse');
  ok(traffic.teamKind(row, true) === 'a/mid.glb|h', 'a coarse device bakes the light vehicle');
  ok(traffic.teamKind({}) === null, 'no vehicle, no kind');
  // Out of reach: town transport's own list where it gives one; else its loaded teams beyond reach.
  const given = [{ id: 'x', e: 1, n: 2, heading_deg: 0, moving: true }];
  const both = traffic.distantTeams({ distant: () => given, actors: [{ id: 'x', disposed: false, visible: false, mode: 'route', pose: { e: 0, n: 0 } },
    { id: 'y', disposed: false, visible: false, mode: 'route', state: 'moving', heading_deg: 0, pose: { e: 5, n: 5 } }] }, null);
  ok(both.map((t) => t.id).join() === 'x,y' && both[0] === given[0], "distant()'s unbuilt teams, and the built ones out of reach it does not list, once each");
  const actor = (id, o = {}) => ({ id, disposed: false, visible: false, mode: 'route', state: 'moving', heading_deg: 90, pose: { e: 10, n: -20 }, ...o });
  const teams = traffic.distantTeams({ actors: [actor('far'), actor('drawn', { visible: true }), actor('driven', { mode: 'reins' }),
    actor('gone', { disposed: true }), actor('night'), actor('waiting', { state: 'stopped' })] }, null,
    { hour: 23, rows: new Map([['night', { hours: [6, 19] }]]) });
  ok(teams.map((t) => t.id).join() === 'far,waiting', `only teams on their round out of reach and in their hours (${teams.map((t) => t.id)})`);
  ok(teams[0].e === 10 && teams[0].n === -20 && teams[0].heading_deg === 90 && teams[0].moving && !teams[1].moving, 'each at its vehicle root, heading, moving or not');
  const loops = JSON.parse(fs.readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url), 'utf8'));
  for (const r of loops.rows) {
    ok(!!traffic.teamKind(r), `${r.id} has a card kind`);
    ok(!r.horse_model || loops.horse_models[r.horse_model]?.file, `${r.id}'s horse has a file to bake from`);
  }
}

console.log(`test_crowd: PASS (${checks} checks)`);

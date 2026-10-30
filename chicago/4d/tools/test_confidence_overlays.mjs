#!/usr/bin/env node
// T-2650 (NAV-605): the Confidence view's overlays — street names, building labels, people
// pins and the Jaunt route, each with its own switch at the foot of the app.
//
// No browser. js/confidence-overlays.js imports nothing but the string table and the naming
// it reuses (display-name.js, fallback-summary.js), so it is loaded straight from the tree.
// The per-destination checks read the compiled sidecars themselves (data/sidecars/<year>),
// so "each switch shows only what the data has" is asked of the data, not of a fixture.
// The layer is driven on a small stand-in document with a hand-cranked animation frame, over
// a real three camera, so "off costs nothing" is a count of frames and listeners.
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const vendorDir = (await readdir(path.join(web, 'vendor'))).find((d) => /^three-/.test(d));
const THREE = await import(pathToFileURL(path.join(web, 'vendor', vendorDir, 'three.module.js')).href);
const O = await import(pathToFileURL(path.join(web, 'js/confidence-overlays.js')).href);

let failures = 0;
const check = async (label, fn) => {
  try { await fn(); console.log(`  ok   ${label}`); } catch (err) { failures++; console.log(`  FAIL ${label}\n       ${String(err.message).split('\n')[0]}`); }
};
console.log('T-2650 — the Confidence view overlays');

// ---- the destinations' own data ------------------------------------------------------ //
const YEARS = ['1812', '1835', '1904'];
async function sceneOf(year) {
  const dir = path.join(root, 'data/sidecars', year);
  const registry = new Map();
  const outlines = [];
  for (const f of await readdir(dir)) {
    if (!f.endsWith('.json')) continue;
    let d; try { d = JSON.parse(await readFile(path.join(dir, f), 'utf8')); } catch { continue; }
    const pl = d?.placement;
    if (!d?.id || !Number.isFinite(pl?.local_e) || !Number.isFinite(pl?.local_n)) continue;
    registry.set(d.id, { id: d.id, sidecar: d });
    const r = 4, e = pl.local_e, n = pl.local_n;
    const ring = [[e - r, n - r], [e + r, n - r], [e + r, n + r], [e - r, n + r]];
    ring.id = d.id;
    ring.grade = d.grade?.grade ?? d.grade?.level ?? (typeof d.grade === 'string' ? d.grade : null);
    outlines.push(ring);
  }
  const peopleFile = path.join(dir, 'people.json');
  const people = existsSync(peopleFile) ? JSON.parse(await readFile(peopleFile, 'utf8')) : null;
  const where = (id) => { const pl = registry.get(id)?.sidecar?.placement; return pl ? { e: pl.local_e, n: pl.local_n } : null; };
  return { registry, outlines, people, where };
}
const scenes = Object.fromEntries(await Promise.all(YEARS.map(async (y) => [y, await sceneOf(y)])));

await check('building labels: a name of its own only — "A vacant dwelling" is a description, and a ticket in brackets never shows', () => {
  assert.equal(O.ownName({ sidecar: { name: 'A vacant dwelling' } }, 'x'), null);
  assert.equal(O.ownName({ sidecar: { name: 'Rufus Brown\'s Boarding House' } }, 'brown_boarding_house'), 'Rufus Brown\'s Boarding House');
  const t = O.ownName({ sidecar: { name: '2115 Prairie Avenue — Kelley/Armour Second Empire (district draft; refined by T-1925)' } }, 'armour_house_2115_prairie');
  assert.equal(t, '2115 Prairie Avenue', 'a label is the title\'s lead phrase: here the address');
  assert.equal(O.labelText('The Burns house, on the north bank at the later foot of State Street'), 'The Burns house');
  assert.equal(O.labelText('Osborn R. Keith house (1808 Prairie Avenue), K01 frontage assembly'), 'Osborn R. Keith house');
  assert.equal(O.ownName({}, 'some_structure_id'), null, 'an id is never a label');
});

await check('each destination labels only buildings with a name of their own, and none of them reads as an id or a ticket', () => {
  const counts = {};
  for (const y of YEARS) {
    const set = O.labelSet(scenes[y].outlines, scenes[y].registry);
    counts[y] = [set.length, scenes[y].outlines.length];
    for (const b of set) assert.ok(!/[a-z0-9]_[a-z0-9]/i.test(b.name) && !/\bT-\d{3,}/.test(b.name) && !/^(A|An)\s/.test(b.name), `${y} ${b.id}: ${b.name}`);
  }
  assert.ok(counts['1835'][0] > 100 && counts['1835'][0] < counts['1835'][1], `1835 labels some, not every roof: ${counts['1835']}`);
  assert.ok(counts['1904'][0] > 50 && counts['1812'][0] > 10, JSON.stringify(counts));
  console.log(`       named buildings: ${YEARS.map((y) => `${y} ${counts[y][0]} of ${counts[y][1]}`).join(', ')}`);
});

await check('people pins: one per address in the directory, absent people left off, a standing review carried, no address no pin', () => {
  const p35 = O.pinPlaces(scenes['1835'].people.people, scenes['1835'].where);
  assert.ok(p35.places.length >= 30 && p35.people >= 300, `1835: ${p35.places.length} places, ${p35.people} people`);
  const rows = scenes['1835'].people.people;
  const absent = new Set(rows.filter((r) => r.present === 'absent').map((r) => r.id));
  const listed = p35.places.flatMap((pl) => pl.people.map((x) => x.id));
  assert.ok(!listed.some((id) => absent.has(id)), 'a person absent at the scene date is pinned');
  const flagged = new Set(rows.filter((r) => r.review_required === true).map((r) => r.id));
  for (const pl of p35.places) for (const x of pl.people) assert.equal(x.review, flagged.has(x.id), x.id);
  const p04 = O.pinPlaces(scenes['1904'].people.people, scenes['1904'].where);
  // T-3253: the Blue Book households put people at most of the street's houses.
  assert.ok(p04.places.length >= 60, `1904: ${p04.places.length} places`);
  const gl = p04.places.find((pl) => pl.id === 'glessner_house');
  assert.ok(gl, 'the Glessner house carries a pin');
  assert.equal(gl.people.length, 3);
  const p12 = O.pinPlaces(scenes['1812'].people.people, scenes['1812'].where);
  assert.equal(p12.people, 1);
  assert.equal(p12.places.length, 1);
  assert.equal(p12.places[0].id, 'kinzie_house_1812');
  assert.deepEqual(p12.places[0].people.map((p) => p.id), ['kinzie_john_elder']);
  assert.equal(scenes['1812'].people.people[0].grade, 'inferred');
  const none = O.pinPlaces([{ id: 'a', name: 'A. Nobody', lives_at: 'not_drawn' }], () => null);
  assert.equal(none.places.length, 0);
  console.log(`       pins: 1835 ${p35.places.length} addresses for ${p35.people} people, 1904 ${p04.places.length} for ${p04.people}, 1812 ${p12.places.length} for ${p12.people}`);
});

await check('each switch\'s line says what this destination has, or that it has none — never a fake layer', () => {
  const p35 = O.pinPlaces(scenes['1835'].people.people, scenes['1835'].where);
  const n35 = O.notes({ year: '1835', labels: 400, people: p35, jaunts: 20 });
  assert.match(n35.streets.text, /^The 1835 street/);
  assert.ok(n35.labels.ok && /400 buildings in 1835/.test(n35.labels.text));
  assert.ok(n35.people.ok && new RegExp(`at ${p35.places.length} known addresses in 1835`).test(n35.people.text));
  assert.ok(n35.route.ok && /^No Jaunt under way/.test(n35.route.text), 'no Jaunt under way: the switch waits for one');
  const n12 = O.notes({ year: '1812', streetsEmpty: true, labels: 40, people: null, jaunts: 0 });
  assert.ok(n12.streets.ok && /No streets are drawn in 1812/.test(n12.streets.text), 'today\'s names still show');
  assert.ok(!n12.people.ok && /No people directory for 1812/.test(n12.people.text));
  assert.ok(!n12.route.ok && /No Jaunts for 1812/.test(n12.route.text));
  const run = O.notes({ year: '1904', labels: 0, people: { places: [], people: 0 }, route: { stops: [[0, 0], [1, 1], [2, 2]], at: 1 } });
  assert.ok(!run.labels.ok && /No building in 1904/.test(run.labels.text));
  assert.ok(!run.people.ok && /known address/.test(run.people.text));
  assert.ok(run.route.ok && /3 stops/.test(run.route.text));
  assert.match(O.notes({ year: '1835', route: { stops: [], at: -1 } }).route.text, /no place in the town/);
  assert.match(O.notes({ year: '1835', labels: 9, hiddenGrades: 1 }).labels.text, /hidden grade are not labelled/);
  for (const n of [n35, n12, run]) for (const { text } of Object.values(n)) assert.doesNotMatch(text, /\{|undefined|null|[a-z]_[a-z]/, text);
});

// ---- projection, against three's own ------------------------------------------------- //
function cameraAt(e, n, y, yawDeg, w = 390, h = 780) {
  const cam = new THREE.PerspectiveCamera(60, w / h, 0.5, 4000);
  cam.position.set(e, y, -n);
  cam.rotation.order = 'YXZ';
  cam.rotation.y = -yawDeg * Math.PI / 180;
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();
  return cam;
}
await check('the layer places a point exactly where three projects it, and nothing behind the camera', () => {
  const cam = cameraAt(10, 20, 2, 30);
  const project = O.projector(cam);
  for (const [e, n, y] of [[12, 60, 3], [-40, 90, 10], [80, 150, 1], [10, 25, 5]]) {
    const ref = new THREE.Vector3(e, y, -n).project(cam);
    const q = project(e, y, -n);
    for (const k of ['x', 'y', 'z']) assert.ok(Math.abs(q[k] - ref[k]) < 1e-9, `${k}: ${q[k]} vs ${ref[k]}`);
  }
  assert.equal(O.toScreen(project, 10, -40, 2, 390, 780), null, 'a point behind you is not drawn');
  assert.equal(O.projector(null), null);
});

await check('labels: the nearest in sight, at most the phone\'s six, none at a hidden grade and none on top of a nearer one', () => {
  const cam = cameraAt(0, 0, 2, 0);
  const project = O.projector(cam);
  // Twenty named buildings in a fan ahead (north is the camera's forward: -z), one behind,
  // one beyond reach, and two stacked on one spot.
  const set = [];
  for (let i = 0; i < 20; i++) set.push({ id: `b${i}`, e: (i - 10) * 9, n: 30 + i * 4, h: 6, name: `House ${i}`, grade: i === 3 ? 'reconstructed' : 'attested' });
  set.push({ id: 'behind', e: 0, n: -30, h: 6, name: 'Behind', grade: 'attested' });
  set.push({ id: 'far', e: 0, n: 400, h: 6, name: 'Far', grade: 'attested' });
  set.push({ id: 'twinA', e: 50, n: 20, h: 6, name: 'Twin A', grade: 'attested' }, { id: 'twinB', e: 50.2, n: 20.1, h: 6, name: 'Twin B', grade: 'attested' });
  set.push({ id: 'house', e: -3, n: 25, h: 6, name: 'Same Name', grade: 'attested' }, { id: 'alley', e: 3, n: 40, h: 6, name: 'Same Name', grade: 'attested' });
  const out = O.pickLabels(set, { player: { e: 0, n: 0 }, project, w: 390, h: 780, hidden: ['reconstructed'], max: O.LABELS.phone, withinM: O.LABELS.withinM });
  const ids = out.map((b) => b.id);
  assert.ok(out.length <= 6 && out.length >= 3, ids.join());
  assert.ok(!ids.includes('behind') && !ids.includes('far') && !ids.includes('b3'), ids.join());
  assert.ok(!(ids.includes('twinA') && ids.includes('twinB')), 'two labels drawn on top of each other');
  assert.ok(ids.includes('house') && !ids.includes('alley'), 'one name labelled twice');
  for (let i = 1; i < out.length; i++) assert.ok(out[i].d >= out[i - 1].d, 'nearest first');
});

// ---- the layer and the switches, on a stand-in page ---------------------------------- //
class El {
  constructor(tag, doc) {
    Object.assign(this, { tagName: tag.toUpperCase(), ownerDocument: doc, children: [], parent: null, attrs: {}, dataset: {}, listeners: {},
      id: '', className: '', type: '', checked: false, disabled: false, hidden: false, _text: '', style: {} });
    const el = this;
    this.classList = {
      toggle(c, on) { const set = new Set(el.className.split(/\s+/).filter(Boolean)); if (on ?? !set.has(c)) set.add(c); else set.delete(c); el.className = [...set].join(' '); },
      contains: (c) => el.className.split(/\s+/).includes(c),
    };
  }
  append(...kids) { for (const k of kids) { const n = typeof k === 'string' ? Object.assign(new El('#text', this.ownerDocument), { _text: k }) : k; n.parent = this; this.children.push(n); } }
  remove() { if (this.parent) this.parent.children = this.parent.children.filter((c) => c !== this); this.parent = null; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k] ?? null; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  async fire(type, extra = {}) { for (const fn of this.listeners[type] || []) await fn({ type, target: this, ...extra }); }
  focus() { this.ownerDocument.activeElement = this; }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); }
  set textContent(v) { this._text = String(v); this.children = []; }
  *walk() { yield this; for (const c of this.children) yield* c.walk(); }
}
function page() {
  const frames = [];
  let nextId = 1;
  const win = { innerWidth: 390, innerHeight: 780,
    requestAnimationFrame: (fn) => { const id = nextId++; frames.push([id, fn]); return id; },
    cancelAnimationFrame: (id) => { const i = frames.findIndex(([x]) => x === id); if (i >= 0) frames.splice(i, 1); },
    setInterval: () => ({ unref() {} }), clearInterval: () => {} };
  const doc = { activeElement: null, defaultView: win };
  doc.createElement = (tag) => new El(tag, doc);
  doc.body = new El('body', doc);
  const crank = (n = 1) => { for (let i = 0; i < n; i++) { const batch = frames.splice(0); for (const [, fn] of batch) fn(); } };
  return { doc, win, frames, crank, all: () => [...doc.body.walk()] };
}
function fakeApi(year, { route = null } = {}) {
  const sc = scenes[year];
  const settings = { streetNames: true };
  const toggles = [];
  const scene = { touched: 0 };
  const opened = [];
  const camera = cameraAt(0, 0, 2, 0);
  const api = {
    year, scene: { id: year }, registry: sc.registry, camera, player: { e: 0, n: 0 },
    terrain: { surfaceHeight: () => 0 },
    navigation: { outlines: sc.outlines, eraEmpty: year === '1812' },
    structurePosition: sc.where,
    buildings: { instanceBounds: () => ({}) },
    hud: { settings, hiddenLevels: [], setToggle: (k, v) => { toggles.push([k, v]); settings[k] = v; } },
    // Anything that would rebuild the scene: the overlays must never reach for it.
    get scene3d() { scene.touched++; return null; },
    get renderer() { scene.touched++; return null; },
  };
  const actions = {
    peopleDirectory: async () => sc.people,
    jauntCatalog: async () => (year === '1812' ? [] : [{ id: 'j' }]),
    jauntRoute: () => route,
    openPerson: (id) => { opened.push(id); return true; },
  };
  return { api, actions, toggles, scene, opened, settings, camera };
}

await check('off costs nothing: no layer, no frame loop until a switch is on, and none again once all are off', async () => {
  const p = page();
  const f = fakeApi('1835');
  const ov = O.createOverlays(p.doc);
  ov.bind({ api: f.api, actions: f.actions, scene: { id: '1835' } });
  assert.equal(ov.running, false);
  assert.equal(p.frames.length, 0);
  assert.equal(ov.layer, null, 'no layer is made before a switch is on');
  await ov.set('labels', true);
  assert.equal(ov.running, true);
  p.crank(3);
  assert.equal(ov.frames, 3);
  await ov.set('labels', false);
  assert.equal(ov.running, false);
  assert.equal(p.frames.length, 0, 'a frame is still queued with every overlay off');
  p.crank(5);
  assert.equal(ov.frames, 3, 'the loop ran on with everything off');
  assert.equal(ov.layer.hidden, true);
  assert.equal(f.scene.touched, 0, 'an overlay switch reached for the renderer or the scene');
});

await check('street names are T-2741\'s readout: the switch is the HUD\'s own setting, not a second layer', async () => {
  const p = page();
  const f = fakeApi('1835');
  const ov = O.createOverlays(p.doc);
  ov.bind({ api: f.api, actions: f.actions });
  assert.equal(ov.get('streets'), true);
  await ov.set('streets', false);
  assert.deepEqual(f.toggles, [['streetNames', false]]);
  assert.equal(ov.get('streets'), false);
  assert.equal(ov.running, false, 'street names need no frame loop of their own');
  assert.equal(ov.layer, null);
});

await check('labels on: the nearest named buildings in sight are drawn over the town, and a hidden grade drops its labels', async () => {
  const p = page();
  const f = fakeApi('1835');
  // Stand in the middle of the 1835 town, looking north.
  const named = O.labelSet(scenes['1835'].outlines, scenes['1835'].registry);
  const anchor = named[Math.floor(named.length / 2)];
  f.api.player = { e: anchor.e, n: anchor.n - 40 };
  f.api.camera = cameraAt(anchor.e, anchor.n - 40, 2, 0);
  const ov = O.createOverlays(p.doc);
  ov.bind({ api: f.api, actions: f.actions, isPhone: true });
  await ov.set('labels', true);
  p.crank();
  const shown = () => p.all().filter((n) => n.className === 'cv-label' && !n.hidden);
  assert.ok(shown().length >= 1 && shown().length <= O.LABELS.phone, `labels drawn: ${shown().length}`);
  assert.equal(ov.drawn.labels, shown().length);
  for (const n of shown()) assert.match(n.style.transform, /^translate\(-?\d+px, -?\d+px\)$/);
  const grade = shown()[0].dataset.grade;
  if (grade) {
    f.api.hud.hiddenLevels = [grade];
    p.crank();
    assert.ok(!shown().some((n) => n.dataset.grade === grade), 'a label stayed on a hidden grade');
  }
  await ov.set('labels', false);
});

await check('people pins: a pin lists who is there with the review line, and a name opens that person\'s card', async () => {
  const p = page();
  const f = fakeApi('1835');
  const ov = O.createOverlays(p.doc);
  ov.bind({ api: f.api, actions: f.actions });
  const dir = O.pinPlaces(scenes['1835'].people.people, scenes['1835'].where);
  const target = dir.places.find((pl) => pl.people.some((x) => x.review)) ?? dir.places[0];
  f.api.player = { e: target.e, n: target.n - 60 };
  f.api.camera = cameraAt(target.e, target.n - 60, 2, 0);
  await ov.set('people', true);
  assert.equal(ov.places, dir.places.length);
  p.crank();
  const pin = p.all().find((n) => n.className === 'cv-pin' && n.dataset.place === target.id && !n.hidden);
  assert.ok(pin, `no pin drawn on ${target.id}`);
  assert.doesNotMatch(pin.getAttribute('aria-label'), /_/);
  await pin.fire('click');
  const pop = p.all().find((n) => n.id === 'cv-pop');
  assert.ok(pop, 'the pin opened no list');
  const people = [...pop.walk()].filter((n) => n.className === 'cv-pop-person');
  assert.equal(people.length, Math.min(target.people.length, O.PIN_LIST_MAX));
  if (target.people.some((x) => x.review)) assert.ok([...pop.walk()].some((n) => n.className === 'cv-pop-review' && /standing review/.test(n.textContent)));
  await people[0].fire('click');
  assert.deepEqual(f.opened, [people[0].dataset.person]);
  assert.ok(!p.all().some((n) => n.id === 'cv-pop'), 'the list stays open over the card');
  await ov.set('people', false);
  assert.equal(ov.running, false);
});

await check('the Jaunt route: a dotted line through the stops in front of you, numbered, the next one ringed; none without a Jaunt', async () => {
  const p = page();
  const route = { stops: [[0, 30], [8, 60], [-10, 90], [0, -50]], at: 1 };
  const f = fakeApi('1835', { route });
  const ov = O.createOverlays(p.doc);
  ov.bind({ api: f.api, actions: f.actions });
  await ov.set('route', true);
  p.crank();
  const path = p.all().find((n) => n.tagName === 'PATH');
  assert.match(path.getAttribute('d'), /^M[\d.-]+ [\d.-]+( L[\d.-]+ [\d.-]+){2}$/, path.getAttribute('d'));
  const stops = p.all().filter((n) => n.className.startsWith('cv-stop'));
  assert.equal(stops.filter((n) => !n.hidden).length, 3, 'the stop behind you is drawn');
  assert.ok(stops[1].classList.contains('is-next') && !stops[0].classList.contains('is-next'));
  const f2 = fakeApi('1835', { route: null });
  ov.bind({ api: f2.api, actions: f2.actions });
  p.crank();
  assert.equal(path.getAttribute('d'), '');
  assert.ok(stops.every((n) => n.hidden));
  await ov.set('route', false);
});

await check('the switches at the foot of the app: one per overlay, and a layer this destination lacks cannot be switched on', async () => {
  for (const year of YEARS) {
    const p = page();
    const f = fakeApi(year);
    const el = new El('div', p.doc);
    const m = O.mountOverlays(el, { api: f.api, actions: f.actions, scene: { id: year } });
    await new Promise((r) => setTimeout(r, 20));
    m.paint();
    const byId = (id) => [...el.walk()].find((n) => n.id === id);
    for (const id of O.OVERLAYS) assert.ok(byId(`cv-ov-${id}`) && byId(`cv-ov-${id}-note`).textContent, `${year} ${id}`);
    const disabled = O.OVERLAYS.filter((id) => byId(`cv-ov-${id}`).disabled);
    if (year === '1812') assert.deepEqual(disabled, ['route'], `1812: ${disabled}`);
    else assert.deepEqual(disabled, [], `${year}: ${disabled}`);
    assert.equal(byId('cv-ov-streets').checked, true);
    const words = [...el.walk()].map((n) => (n.tagName === '#TEXT' ? n._text : n.textContent)).join(' ');
    assert.doesNotMatch(words, /[a-z]_[a-z]|undefined|\{|null/, words);
    if (year === '1812') assert.match(byId('cv-ov-streets-note').textContent, /No streets are drawn in 1812/);
  }
});

if (failures) { console.log(`\n${failures} check(s) failed`); process.exit(1); }
console.log('\nall checks passed');

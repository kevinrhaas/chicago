#!/usr/bin/env node
/**
 * T-3674 — the on-site tour (renderers/web/js/onsite.js, its card js/onsite-view.js, its data
 * data/onsite/prairie_1904.json) and its wiring into Window mode (js/controls/window.js).
 *
 * Holds, against the committed records and stand-ins:
 *  - THE DATA: the tour is sound (onsite.js tourProblems), in 1904, ends at the Glessner
 *    House; every source id resolves in data/sources/ and its citation is carried verbatim;
 *    every stop names existing records under `evidence` (a jaunt's evidence row, a 1904
 *    household, a structure record), each of its sources is one of theirs and each record
 *    lends it at least one; its structure stands in the 1904 scene and its household lives
 *    there.
 *  - WHERE YOU STAND: each stop's latitude and longitude is re-derived from its parcel
 *    (data/street_grid/1904.json: the middle of the walk band in front of the parcel's
 *    street front, carried to today's ground by the 1904 registration and turned to WGS84),
 *    to within half a metre; projected the way Window mode projects a fix, it lands on that
 *    walk, the last one beside the glessner_house footprint and just outside the City's own
 *    landmark lot for 1800 S. Prairie (data/modern/landmark_sites.json).
 *  - STOP ORDER: a walk of the route fix by fix reaches every stop in order; standing at a
 *    later stop does not reach it out of turn; arrival never moves the tour on by itself.
 *  - ARRIVAL: inside a radius scaled to the reported accuracy (10 m plus it, at most 35 m); a
 *    fix rougher than 35 m calls none; "I'm here" always can.
 *  - OFF THE GROUND: a fix far from Prairie Avenue is said to be off the tour's ground, calls
 *    no arrival, still gives the distance to the next stop, and Window mode is held: the
 *    visitor is never walked there. Back on the ground, Window mode sets them down again.
 *  - THE WIRING: the card is imported on demand (no boot cost), offered only in 1904 when
 *    Window mode starts, and the tour's data is published.
 * A real device on the real street is not claimed here: that field test is the owner's.
 */
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const imp = (p) => import(pathToFileURL(path.join(web, p)).href);
const o = await imp('js/onsite.js');
const w = await imp('js/controls/window.js');
const geo = await imp('js/today-geo.js');
const { createRegistration } = await imp('js/today-register.js');
const THREE = await imp('vendor/three-0.185.1/three.module.js');
const { createIntent, createBackendSwitch } = await imp('js/controls/intent.js');
const json = async (p) => JSON.parse(await readFile(path.join(root, p), 'utf8'));
const datum = await json('data/datum.json');
const tour = await json('data/onsite/prairie_1904.json');
const grid = await json('data/street_grid/1904.json');
const landmarks = await json('data/modern/landmark_sites.json');
const libs = await json('data/liberties.json');
const libsMd = await readFile(path.join(root, 'docs/LIBERTIES.md'), 'utf8');
const main = await readFile(path.join(web, 'js/main.js'), 'utf8');
const view = await readFile(path.join(web, 'js/onsite-view.js'), 'utf8');
const publish = await readFile(path.join(root, 'tools/publish.sh'), 'utf8');
const toLocal = (lat, lon) => w.toLocal(lat, lon, datum);

const checks = [];
function check(name, run) { run(); checks.push(name); }
const SELF = process.argv.includes('--self-test');

// ---- the data ---------------------------------------------------------------------------- //

/** Every source id a record carries: under `sources`, `also_sources` and `source_id`, anywhere. */
function sourcesIn(node, out = new Set()) {
  if (Array.isArray(node)) node.forEach((v) => sourcesIn(v, out));
  else if (node && typeof node === 'object') {
    for (const [k, v] of Object.entries(node)) {
      if ((k === 'sources' || k === 'also_sources' || k === 'position_sources') && Array.isArray(v)) v.forEach((s) => typeof s === 'string' && out.add(s));
      else if (k === 'source_id' && typeof v === 'string') out.add(v);
      else sourcesIn(v, out);
    }
  }
  return out;
}

const jauntCache = new Map();
async function evidenceSources(ref) {
  const [kind, rest] = ref.split(':');
  if (kind === 'jaunt') {
    const [id, row] = rest.split('#');
    const file = `data/jaunts/${id}.json`;
    if (!existsSync(path.join(root, file))) return { problem: `${ref}: no jaunt ${file}` };
    if (!jauntCache.has(id)) jauntCache.set(id, await json(file));
    const ev = (jauntCache.get(id).evidence || []).find((e) => e.id === row);
    if (!ev) return { problem: `${ref}: jaunt ${id} has no evidence row ${row}` };
    if (ev.confidence === 'reconstructed') return { problem: `${ref}: a reconstructed row is framing, not a fact` };
    return { sources: new Set(ev.sources || []) };
  }
  if (kind === 'household') {
    const file = `data/residents_1904/households/${rest}.json`;
    if (!existsSync(path.join(root, file))) return { problem: `${ref}: no household ${file}` };
    return { sources: sourcesIn(await json(file)), record: await json(file) };
  }
  if (kind === 'structure') {
    const file = `data/structures/${rest}.json`;
    if (!existsSync(path.join(root, file))) return { problem: `${ref}: no structure ${file}` };
    return { sources: sourcesIn(await json(file)) };
  }
  return { problem: `${ref}: unknown evidence kind ${kind}` };
}

/** Everything wrong with a tour's provenance, as lines. */
async function provenanceProblems(doc) {
  const out = [...o.tourProblems(doc)];
  const known = new Set((await readdir(path.join(root, 'data/sources'))).filter((f) => f.endsWith('.json')).map((f) => f.slice(0, -5)));
  for (const [id, citation] of Object.entries(doc.citations || {})) {
    if (!known.has(id)) { out.push(`citation ${id} names no record in data/sources/`); continue; }
    const rec = await json(`data/sources/${id}.json`);
    if (rec.citation !== citation) out.push(`citation ${id} is not data/sources/${id}.json's own, verbatim`);
  }
  for (const s of doc.stops || []) {
    for (const id of s.sources || []) if (!known.has(id)) out.push(`stop ${s.id} cites ${id}, which is not in data/sources/`);
    if (!Array.isArray(s.evidence) || !s.evidence.length) { out.push(`stop ${s.id} names no record its text rests on`); continue; }
    const lent = new Set();
    for (const ref of s.evidence) {
      const got = await evidenceSources(ref);
      if (got.problem) { out.push(`stop ${s.id}: ${got.problem}`); continue; }
      const used = [...got.sources].filter((x) => s.sources.includes(x));
      if (!used.length) out.push(`stop ${s.id}: ${ref} lends none of the stop's sources`);
      used.forEach((x) => lent.add(x));
      if (ref.startsWith('household:') && !(got.record.associated_with || []).some((a) => a.place_or_structure_id === s.structure)) {
        out.push(`stop ${s.id}: ${ref} does not live in ${s.structure}`);
      }
    }
    for (const id of s.sources || []) if (!lent.has(id)) out.push(`stop ${s.id} cites ${id}, which none of its records carries`);
    if (!existsSync(path.join(root, `data/sidecars/1904/${s.structure}.json`))) out.push(`stop ${s.id}: ${s.structure} does not stand in the 1904 scene`);
  }
  return out;
}

if (SELF) {
  // Plant each provenance fault and require it refused, by name.
  const planted = [
    ['an invented source', (d) => { d.stops[0].sources.push('nobody_wrote_this_1904'); d.citations.nobody_wrote_this_1904 = 'Invented.'; }, /nobody_wrote_this_1904/],
    ['a citation paraphrased', (d) => { d.citations[d.stops[1].sources[0]] += ' (paraphrase)'; }, /verbatim/],
    ['a source no record lends', (d) => { d.stops[2].sources.push('chicago_blue_book_1904'); d.citations.chicago_blue_book_1904 ??= 'x'; }, /which none of its records carries/],
    ['a stop resting on framing', (d) => { d.stops[6].evidence.push('jaunt:prairie-avenue-orientation#outing'); }, /reconstructed row is framing/],
    ['a household in another house', (d) => { d.stops[0].evidence.push('household:hh_kimball_william_w'); }, /does not live in/],
    ['a stop with no position', (d) => { delete d.stops[3].lat; }, /has no position/],
  ];
  for (const [name, plant, want] of planted) {
    const d = structuredClone(tour); plant(d);
    const got = await provenanceProblems(d);
    const hit = got.some((l) => want.test(l));
    console.log(`   self-test | ${hit ? 'refused' : 'FAIL: not refused'} — ${name}${hit ? '' : ` (${got.join('; ') || 'no problem'})`}`);
    assert.ok(hit, `self-test: ${name} was not refused`);
  }
  console.log('check_onsite_tour --self-test: every planted fault refused');
  process.exit(0);
}

const problems = await provenanceProblems(tour);
check('the tour is sound, in 1904, and every line of it rests on an existing record and its sources, cited verbatim', () => {
  assert.deepEqual(problems, []);
  assert.equal(tour.scene, '1904');
  assert.equal(tour.stops.at(-1).structure, 'glessner_house', 'the tour ends at the Glessner House');
  assert.ok(tour.stops.length >= 5 && tour.stops.length <= 9, `${tour.stops.length} stops`);
  // The route itself is interpretation, and says so where the visitor's liberties are read.
  const lib = (libs.liberties || libs).find?.((l) => l.id === tour.liberty);
  assert.ok(lib, `the tour's liberty ${tour.liberty} is in data/liberties.json`);
  const md = libsMd.slice(libsMd.indexOf(`### ${tour.liberty} `));
  assert.ok(md.slice(0, md.indexOf('\n### ', 4)).includes('**Applies to:** `data/onsite/prairie_1904.json`'), 'the liberty applies to the tour');
});

check('the route is one walk: each stop within a block of the last, in the order the data gives, through the 1800 block', () => {
  assert.deepEqual(tour.stops.map((s) => s.id), ['pullman', 'kimball', 'coleman', 'field', 'elbridge-keith', 'osborn-keith', 'glessner']);
  let total = 0;
  for (let i = 1; i < tour.stops.length; i++) {
    const d = geo.distanceM({ lat: tour.stops[i - 1].lat, lng: tour.stops[i - 1].lon }, { lat: tour.stops[i].lat, lng: tour.stops[i].lon });
    assert.ok(d > 12 && d < 200, `${tour.stops[i - 1].id} to ${tour.stops[i].id}: ${d.toFixed(1)} m`);
    total += d;
  }
  assert.ok(total > 250 && total < 600, `the walk is ${total.toFixed(0)} m`);
  assert.ok(tour.stops.filter((s) => /^18\d\d /.test(s.address)).length >= 4, 'most stops are on the 1800 block');
});

// ---- where you stand --------------------------------------------------------------------- //

const reg = createRegistration('1904');
function standOf(parcelId) {
  const p = grid.parcels.find((x) => x.id === parcelId);
  assert.ok(p, `parcel ${parcelId}`);
  const face = grid.faces.find((f) => f.id === p.street_face);
  const c = p.corners_local_m;
  const ends = p.side === 'west' ? [c.NE_street, c.SE_street] : [c.NW_street, c.SW_street];
  const mid = [(ends[0][0] + ends[1][0]) / 2, (ends[0][1] + ends[1][1]) / 2];
  const q = face.bands.walk[0];
  const a = [(q[0][0] + q[3][0]) / 2, (q[0][1] + q[3][1]) / 2], b = [(q[1][0] + q[2][0]) / 2, (q[1][1] + q[2][1]) / 2];
  const dx = b[0] - a[0], dy = b[1] - a[1];
  const t = ((mid[0] - a[0]) * dx + (mid[1] - a[1]) * dy) / (dx * dx + dy * dy);
  const scene = [a[0] + t * dx, a[1] + t * dy];
  const today = reg.toToday(scene[0], scene[1]);
  return { scene, ll: geo.localToLatLng(today[0], today[1]), face: q, street: ends };
}
const segDist = (p, a, b) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], len2 = dx * dx + dy * dy;
  const t = len2 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / len2)) : 0;
  return Math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy);
};
const polyDist = (p, poly) => Math.min(...poly.map((v, i) => segDist(p, v, poly[(i + 1) % poly.length])));
const inside = (p, poly) => {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > p[1]) !== (yj > p[1]) && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
};
function footprintWorld(sc) {
  const pl = sc.placement, th = (pl.rotation_deg ?? 0) * Math.PI / 180, c = Math.cos(th), s = Math.sin(th);
  return sc.footprint.polygon.map(([x, y]) => [pl.local_e + x * c + y * s, pl.local_n - x * s + y * c]);
}

check('every stop stands where its parcel puts it: the walk in front of its 1904 street front, re-derived to half a metre', () => {
  for (const s of tour.stops) {
    const d = standOf(s.stand.parcel);
    const off = geo.distanceM({ lat: s.lat, lng: s.lon }, d.ll);
    assert.ok(off < 0.5, `${s.id}: ${off.toFixed(2)} m from its parcel's walk (${d.ll.lat.toFixed(6)}, ${d.ll.lng.toFixed(6)})`);
  }
});

for (const s of tour.stops) {
  const d = standOf(s.stand.parcel);
  const at = toLocal(s.lat, s.lon);
  // Window mode does not carry a fix through the registration; on Prairie Avenue that is about a metre.
  const drift = Math.hypot(at.e - d.scene[0], at.n - d.scene[1]);
  assert.ok(drift < 3, `${s.id}: Window mode puts it ${drift.toFixed(2)} m off its walk`);
  const fromLine = segDist([at.e, at.n], d.street[0], d.street[1]);
  assert.ok(fromLine < 4, `${s.id}: ${fromLine.toFixed(2)} m from its lot's street line`);
  const fp = footprintWorld(await json(`data/sidecars/1904/${s.structure}.json`));
  assert.ok(!inside([at.e, at.n], fp), `${s.id}: the stand is inside its own house`);
  assert.ok(polyDist([at.e, at.n], fp) < 25, `${s.id}: ${polyDist([at.e, at.n], fp).toFixed(1)} m from its house`);
}
checks.push('projected as Window mode projects a fix, each stop lands on its own walk, outside and within a few metres of its house');

{
  const g = tour.stops.at(-1);
  const at = toLocal(g.lat, g.lon);
  const fp = footprintWorld(await json('data/sidecars/1904/glessner_house.json'));
  const gap = polyDist([at.e, at.n], fp);
  assert.ok(!inside([at.e, at.n], fp) && gap < 10, `the Glessner stand is ${gap.toFixed(2)} m from the house`);
  const site = landmarks.sites.find((x) => x.id === 'glessner_house');
  const lot = site.polygon_lnglat.map(([lng, lat]) => { const p = toLocal(lat, lng); return [p.e, p.n]; });
  const lotGap = polyDist([at.e, at.n], lot);
  assert.ok(!inside([at.e, at.n], lot) && lotGap < 3, `the Glessner stand is ${lotGap.toFixed(2)} m outside the City's lot`);
  // And the brief's own reading of today's 1800 S. Prairie (about 41.8579 N, 87.6208 W) is the same corner.
  assert.ok(geo.distanceM({ lat: g.lat, lng: g.lon }, { lat: 41.8579, lng: -87.6208 }) < 30);
  checks.push('the Glessner stop is on the walk beside the glessner_house footprint, just outside the City\'s landmark lot for 1800 S. Prairie');
}

// ---- the walk: order, arrival, off the ground ---------------------------------------------- //

/** A point `metresN` north and `metresE` east of a stop, as latitude and longitude. */
const offset = (s, metresN, metresE = 0) => {
  const [e, n] = geo.latLngToLocal(s.lat, s.lon);
  const p = geo.localToLatLng(e + metresE, n + metresN);
  return { lat: p.lat, lon: p.lng };
};

check('the arrival radius grows with the reported accuracy, from 10 m to at most 35 m', () => {
  assert.equal(o.arrivalRadius(0), o.ARRIVE_MIN_M);
  assert.equal(o.arrivalRadius(8), 18);
  assert.equal(o.arrivalRadius(500), o.ARRIVE_MAX_M);
});

check('a walk of the route, fix by fix, reaches every stop in order, and arrival waits for "Next stop"', () => {
  const t = o.createOnsiteTour({ doc: tour, toLocal });
  for (let i = 0; i < tour.stops.length; i++) {
    const s = tour.stops[i];
    // Thirty metres short, then at the stop, at ±6 m.
    t.update({ ...offset(s, 30), accuracy: 6 });
    assert.equal(t.state.cursor, i);
    assert.equal(t.state.arrived, false, `${s.id}: 30 m short is not there at ±6 m`);
    assert.equal(t.state.toward.index, i);
    assert.ok(Math.abs(t.state.toward.distance - 30) < 1.5, `${s.id}: ${t.state.toward.distance}`);
    assert.equal(t.state.toward.point, 'S', 'the stop is south of a fix 30 m north of it');
    t.update({ lat: s.lat, lon: s.lon, accuracy: 6 });
    assert.equal(t.state.arrived, true, `${s.id} reached`);
    assert.equal(t.state.how, 'gps');
    // Reached: the card holds this stop and points at the next.
    t.update({ lat: s.lat, lon: s.lon, accuracy: 6 });
    assert.equal(t.state.cursor, i, 'arrival never moves the tour on by itself');
    if (i < tour.stops.length - 1) {
      assert.equal(t.state.toward.index, i + 1);
      t.next();
    }
  }
  assert.equal(t.state.complete, true);
  assert.ok(t.state.reached.every(Boolean));
});

check('standing at a later stop does not reach it out of turn', () => {
  const t = o.createOnsiteTour({ doc: tour, toLocal });
  const g = tour.stops.at(-1);
  t.update({ lat: g.lat, lon: g.lon, accuracy: 3 });
  assert.equal(t.state.cursor, 0);
  assert.equal(t.state.arrived, false, 'at Glessner, walking to the Pullman house, is not at the Pullman house');
  assert.equal(t.state.reached.at(-1), false);
  assert.ok(t.state.toward.distance > 40 && t.state.toward.index === 0);
});

check('two stops 17 m apart: reaching one does not swallow the next at a good fix', () => {
  const t = o.createOnsiteTour({ doc: tour, toLocal });
  const okeith = tour.stops.findIndex((s) => s.id === 'osborn-keith');
  for (let i = 0; i < okeith; i++) { t.here(); t.next(); }
  const s = tour.stops[okeith];
  t.update({ lat: s.lat, lon: s.lon, accuracy: 4 });
  assert.equal(t.state.arrived, true);
  t.next();
  assert.equal(t.stop.id, 'glessner');
  assert.equal(t.state.arrived, false, '17 m at ±4 m (radius 14 m) is not yet the Glessner House');
});

check('a rough fix calls no arrival and says so; "I\'m here" always can', () => {
  const t = o.createOnsiteTour({ doc: tour, toLocal });
  const s = tour.stops[0];
  t.update({ lat: s.lat, lon: s.lon, accuracy: 60 });
  assert.equal(t.state.rough, true);
  assert.equal(t.state.arrived, false, 'a ±60 m fix at the very stop is not called arrival');
  t.here();
  assert.equal(t.state.arrived, true);
  assert.equal(t.state.how, 'visitor');
  // A fix at ±20 m reaches a stop 25 m off: the radius is 30 m.
  t.next();
  t.update({ ...offset(tour.stops[1], 0, 25), accuracy: 20 });
  assert.equal(t.state.arrived, true);
});

check('back returns to the stop before, keeping what was reached', () => {
  const t = o.createOnsiteTour({ doc: tour, toLocal });
  t.here(); t.next(); t.back();
  assert.equal(t.state.cursor, 0);
  assert.equal(t.state.arrived, true);
  t.back();
  assert.equal(t.state.cursor, 0);
});

check('a fix off the tour\'s ground is said, calls no arrival, still gives the way, and asks Window mode to hold', () => {
  const t = o.createOnsiteTour({ doc: tour, toLocal });
  // The river forks, 3.7 km north-west: in Chicago, far off Prairie Avenue.
  t.update({ lat: datum.origin_lat, lon: datum.origin_lon, accuracy: 5 });
  assert.equal(t.state.off, true);
  assert.equal(t.state.arrived, false);
  assert.ok(t.state.toward.distance > 3000, `${t.state.toward.distance}`);
  assert.equal(t.state.toward.point, 'SE');
  assert.equal(t.hold(toLocal(datum.origin_lat, datum.origin_lon)), true);
  // A block east, on Michigan Avenue, is still the tour's ground.
  const near = offset(tour.stops[2], 0, 120);
  assert.equal(t.hold(toLocal(near.lat, near.lon)), false);
  assert.equal(o.sayDistance(3712), '3.7 km');
  assert.equal(o.sayDistance(56.4), '56 m');
  assert.equal(o.compassPoint(359), 'N');
  assert.equal(o.compassPoint(134), 'SE');
  assert.equal(o.turnDeg(10, 350), 20);
});

function rig({ search = '' } = {}) {
  const listeners = {};
  const win = { DeviceOrientationEvent: function () {}, screen: { orientation: { angle: 0 } },
    addEventListener: (k, fn) => { listeners[k] = fn; }, removeEventListener: (k) => { delete listeners[k]; } };
  const watched = [];
  const nav = { geolocation: { watchPosition: (ok) => { watched.push(ok); return 7; }, clearWatch: () => { watched.length = 0; } } };
  const state = { e: 0, n: 0, yaw: 0, pitch: 0 };
  const teleports = [];
  const walker = { state, get bearingDeg() { return 0; }, teleport: (q) => { teleports.push(q); state.e = q.local_e; state.n = q.local_n; } };
  const intent = createIntent();
  const backends = createBackendSwitch(intent);
  const page = { name: 'touch' };
  backends.activate(page);
  const said = [];
  const mode = w.createWindowMode({ THREE, walker, intent, backends, fallback: () => page, datum, inBounds: () => true,
    say: (l) => said.push(l), search, win, nav });
  return { mode, teleports, watched, said };
}

await (async () => {
  const r = rig();
  const t = o.createOnsiteTour({ doc: tour, toLocal });
  const seen = [];
  const off = r.mode.watchFix((fix, at) => { seen.push(fix); t.update(fix); return t.hold(at); });
  await r.mode.start();
  r.watched[0]({ coords: { latitude: datum.origin_lat, longitude: datum.origin_lon, accuracy: 5 } });
  assert.equal(r.teleports.length, 0, 'a fix off the tour\'s ground is never walked to');
  assert.equal(t.state.off, true);
  assert.equal(seen.length, 1, 'the tour sees every fix');
  const s = tour.stops[0];
  r.watched[0]({ coords: { latitude: s.lat, longitude: s.lon, accuracy: 5 } });
  assert.equal(r.teleports.length, 1, 'back on the ground, Window mode sets the visitor down');
  assert.equal(t.state.arrived, true);
  assert.deepEqual(r.mode.lastFix, { lat: s.lat, lon: s.lon, accuracy: 5 });
  // Wander under the hysteresis still reaches the tour.
  r.watched[0]({ coords: { latitude: s.lat + 0.00001, longitude: s.lon, accuracy: 5 } });
  assert.equal(seen.length, 3);
  off();
  r.watched[0]({ coords: { latitude: datum.origin_lat, longitude: datum.origin_lon, accuracy: 5 } });
  assert.equal(seen.length, 3, 'a tour that has ended hears nothing');
  r.mode.stop();
  checks.push('in Window mode the tour hears every fix, holds a fix off its ground where the visitor is, and lets go when it ends');
})();

await (async () => {
  const g = tour.stops.at(-1);
  const r = rig({ search: `?year=1904&window-at=${g.lat},${g.lon}` });
  await r.mode.start();
  assert.equal(r.teleports.length, 1, '?window-at= places the visitor without the GPS');
  const t = o.createOnsiteTour({ doc: tour, toLocal });
  t.update(r.mode.lastFix);
  assert.equal(r.mode.lastFix.accuracy, 0);
  assert.equal(t.state.radius, o.ARRIVE_MIN_M);
  assert.equal(t.state.arrived, false, 'the address stands at Glessner; the tour starts at the Pullman house');
  checks.push('?window-at= drives the tour as a fix of ±0 m, the smallest radius');
})();

// ---- the wiring ---------------------------------------------------------------------------- //

check('the card is imported on demand, offered only in 1904 when Window mode starts, and the data is published', () => {
  assert.ok(!/^import[^\n]*onsite/m.test(main), 'no static import of the tour: it costs the boot nothing');
  assert.ok((/import\('\.\/onsite-view\.js'\)/).test(main));
  assert.ok((new RegExp(`const ONSITE_YEAR = '${o.ONSITE_YEAR}';`)).test(main), 'main.js says the tour\'s year as onsite.js does');
  assert.ok((/String\(loaded\.scene\.id \?\? YEAR\) !== ONSITE_YEAR\) return;/).test(main), 'offered only in the tour\'s year');
  assert.ok(main.includes("hud.setFly(false, { announce: false }); offerOnsite(); }"), 'offered when Window mode starts');
  assert.ok((/onsite\?\.end\(\)/).test(main), 'closing Window mode ends the tour');
  assert.ok((/watchFix\(/).test(main));
  assert.ok((/onsite\/prairie_1904\.json/).test(main));
  assert.ok(/from '\.\/onsite\.js'/.test(view), 'the card runs the tour of onsite.js');
  assert.ok(/data\/onsite\/\*\.json/.test(publish), 'publish.sh ships the tour');
});

for (const name of checks) console.log(`ok - ${name}`);
console.log(`check_onsite_tour: ${checks.length} checks passed`);

#!/usr/bin/env node
// T-3601 — the Today window: the scene's local metres to latitude/longitude and a true
// heading (renderers/web/js/today-geo.js), and the window's throttling, link card and
// hide/show (renderers/web/js/today-view.js) against a stand-in for Google's Street View
// library. Pure: no browser, no network, no key.
import { localToLatLng, gridToTrueDeg, viewFromLocal, trueBearing, distanceM, streetViewUrl, DATUM }
  from '../renderers/web/js/today-geo.js';
import { createTodayView, keyFor, imageDateText, cardinal16, onToday, MOVE_M, QUERY_MS }
  from '../renderers/web/js/today-view.js';
import { latLngToLocal } from '../renderers/web/js/today-geo.js';
import { createRegistration, CONTROLS } from '../renderers/web/js/today-register.js';
import { createModernStreets, registerSegments, todayText } from '../renderers/web/js/modern-streets.js';
import { deriveControls, controlTable } from './today_registration.mjs';
import { readFileSync } from 'node:fs';

const fails = [];
const expect = (name, ok, got) => { if (!ok) fails.push(`${name}: ${JSON.stringify(got)}`); };
const near = (a, b, tol) => Math.abs(a - b) <= tol;
const m = (a, b) => distanceM(a, b);

// --- the projection ---------------------------------------------------------------
// The datum's own origin comes back as the datum says (data/datum.json).
const o = localToLatLng(0, 0);
expect('the origin is the datum origin, within 0.2 m', m(o, { lat: DATUM.origin_lat, lng: DATUM.origin_lon }) < 0.2, o);
// EPSG:26916 → WGS84 by pyproj 3.8 (2026-11-14), the transform tools/build_modern_streets.py
// projected today's streets with: the inverse here agrees to a centimetre.
const PYPROJ = [
  [1500, -3200, 41.857999309, -87.619593546],
  [-800, 1500, 41.900176009, -87.647729491],
  [3000, -6000, 41.832877418, -87.601286423],
];
for (const [e, n, lat, lng] of PYPROJ) {
  const p = localToLatLng(e, n);
  expect(`(${e}, ${n}) matches pyproj within 1 cm`, m(p, { lat, lng }) < 0.01, { p, lat, lng, off_m: m(p, { lat, lng }) });
}
// Prairie & 18th, the corner the 1904 control holds (data/traces/prairie_1904_control.json,
// lat 41.8579305 from OpenStreetMap), lands on its own latitude.
const corner = localToLatLng(1401.86, -3206.93);
expect('Prairie & 18th lands on its OSM latitude', near(corner.lat, 41.8579305, 2e-6), corner);
// Grid north is about 0.41° WEST of true north here (the town is east of zone 16's 87° W
// meridian... and so its grid north leans toward the pole's meridian, west).
const conv = gridToTrueDeg(1401.86, -3206.93);
expect('the convergence at Prairie is about -0.41°', conv < -0.39 && conv > -0.43, conv);
const v = viewFromLocal({ e: 1401.86, n: -3206.93, bearingDeg: 0 }, 40);
expect('facing grid north is a true heading of about 359.6°', near(v.heading, 360 + conv, 1e-9), v.heading);
expect('the look target is 40 m ahead', near(m(v, v.target), 40, 0.1), m(v, v.target));
expect('and on the heading', near(trueBearing(v, v.target), v.heading, 0.05), trueBearing(v, v.target));
const url = streetViewUrl({ lat: 41.8579305, lng: -87.6207753, heading: 25.4, pitch: -3 });
expect('the keyless link is Google Maps URLs Street View', url === 'https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=41.857931,-87.620775&heading=25&pitch=-3&fov=90', url);

// --- the registration (Kevin, 2026-11-16) ----------------------------------------
// "in today we are in the middle of the river near the north bank but in 1812 we are on
// the south bank". The table today-register.js holds is the tool's, to the decimetre.
const derived = controlTable(deriveControls().controls);
expect('today-register.js CONTROLS is tools/today_registration.mjs\'s output (re-run it and paste)',
  JSON.stringify(derived) === JSON.stringify(CONTROLS), { derived: derived.length, held: CONTROLS.length });
expect('every year has street controls, and 1812 and 1835 their fort',
  ['1812', '1835', '1904'].every((y) => createRegistration(y).count >= 60)
  && CONTROLS.some((r) => r[0] === 'fort:first_fort_1803' && r[1] === '1812')
  && CONTROLS.some((r) => r[0] === 'fort:picket_1816' && r[1] === '1835'), CONTROLS.length);
const json = (p) => JSON.parse(readFileSync(new URL(`../${p}`, import.meta.url), 'utf8'));
const sites = json('data/modern/landmark_sites.json').sites;
const ringCentre = (ring) => { const ps = ring.slice(0, -1); return [ps.reduce((a, p) => a + p[0], 0) / ps.length, ps.reduce((a, p) => a + p[1], 0) / ps.length]; };
const inRing = ([x, y], ring) => { let c = false; for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
  const [xi, yi] = ring[i], [xj, yj] = ring[j];
  if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; };
const fortRing = sites.find((s) => s.id === 'site_of_fort_dearborn').polygon_lnglat.map(([lng, lat]) => latLngToLocal(lat, lng));
const glessnerRing = sites.find((s) => s.id === 'glessner_house').polygon_lnglat.map(([lng, lat]) => latLngToLocal(lat, lng));
const modernDoc = json('data/modern/streets.json');
const anchor = (y, id) => json(`data/scenes/${y}.json`).anchors.find((a) => a.id === id);
for (const [y, fortId] of [['1812', 'fort:first_fort_1803'], ['1835', 'fort:picket_1816']]) {
  const reg = createRegistration(y);
  const row = CONTROLS.find((r) => r[0] === fortId);
  expect(`${y}: the fort's south wall lands on the City's site of Fort Dearborn`, inRing(reg.toToday(row[2], row[3]), fortRing), reg.toToday(row[2], row[3]));
  // Kevin's spot: the Lalime jaunt's stop 8, on the south bank across from the Kinzie house.
  const a = anchor('1812', 'kinzie_house_across_river');
  const ms = createModernStreets(registerSegments(modernDoc, reg.toScene));
  const t = todayText(ms.at(a.local_e, a.local_n));
  const num = Number(/^(\d+) N Michigan Ave$/.exec(t)?.[1]);
  if (y === '1812') {
    // The river was widened over the fort's site in 1856: the 1812 south bank, just north
    // of the fort, is under the bridge's south half today, not near its north end.
    expect('1812 stop 8 (south bank, across from the Kinzie house) reads the bridge\'s south half today (under 386 N Michigan), not 393 by the north bank',
      num > 300 && num < 386, t);
    const raw = createModernStreets(modernDoc).at(a.local_e, a.local_n);
    expect('and without the registration it read 393 N Michigan, the photo Kevin sent', todayText(raw) === '393 N Michigan Ave', todayText(raw));
  }
}
for (const y of ['1812', '1835', '1904']) {
  const reg = createRegistration(y);
  const back = [[1140, 250], [1405, -3300], [0, 0], [-1641.8, -4244.3], [995, 390]].map(([e, n]) => {
    const [te, tn] = reg.toToday(e, n); const [se, sn] = reg.toScene(te, tn); return Math.hypot(se - e, sn - n);
  });
  expect(`${y}: toScene undoes toToday to 5 cm`, back.every((d) => d < 0.05), back);
  // Prairie Avenue was georeferenced on the Sanborn sheets and agrees with today's grid:
  // the registration leaves it within a few metres, and Glessner's door on its own lot.
  const [ge, gn] = reg.toToday(1401.86, -3206.93);
  expect(`${y}: Prairie & 18th moves under 3 m`, Math.hypot(ge - 1401.86, gn + 3206.93) < 3, [ge, gn]);
  const g = json('data/structures/glessner_house.json').phases.find((p) => p.id === 'as_built_1887');
  const gc = ringCentre(g.footprint.polygon.map(([u, v]) => { const th = (g.position.rotation_deg ?? 0) * Math.PI / 180;
    return [g.position.utm_e - 447072.7 + u * Math.cos(th) + v * Math.sin(th), g.position.utm_n - 4637395.8 - u * Math.sin(th) + v * Math.cos(th)]; }).concat([[0, 0]]));
  expect(`${y}: Glessner House stays on the City's Glessner House lot`, inRing(reg.toToday(gc[0], gc[1]), glessnerRing), reg.toToday(gc[0], gc[1]));
}
// 1871 (Kevin, 2026-11-19: "we are standing on the shore and in today view we are in the
// river"). The 1871 city was read off Mitchell's 1870 map; its river runs 20 to 80 m from
// today's channel. It takes the map fit's own corners and today's river, none of the 1835 plat's.
{
  const reg = createRegistration('1871');
  const rows = CONTROLS.filter((r) => r[1].split(' ').includes('1871'));
  expect('1871: its controls are its own (every map-fit corner and the river), no 1835 or 1904 row',
    rows.every((r) => r[1] === '1871') && rows.filter((r) => r[0].startsWith('1871:map_')).length === 36
    && rows.filter((r) => r[0].startsWith('1871:river_')).length >= 100, rows.length);
  const water = json('data/modern/chicago_river.json').polygons
    .map((p) => p.rings.map((r) => r.map(([lng, lat]) => latLngToLocal(lat, lng))));
  // Inside the outer ring and no hole (an island) — or inside any other polygon.
  const wet = (q) => water.some(([outer, ...holes]) => inRing(q, outer) && !holes.some((h) => inRing(q, h)));
  // Two banks the 1871 river drew off today's: the North Branch's north bank at Goose
  // Island (50 m south of today's channel) and the South Branch's east bank at Randolph
  // (40 m west of today's). Standing on each, Today asked for the river; now for the bank.
  for (const [label, at] of [['the North Branch\'s north bank at Goose Island', [-1186, 1482.5]],
    ['the South Branch\'s east bank at Randolph', [1.4, -233.4]]]) {
    expect(`1871: on ${label}, Today without the registration was in today's river`, wet(at), at);
    expect(`1871: and with it, on today's ground`, !wet(reg.toToday(at[0], at[1])), reg.toToday(at[0], at[1]));
  }
  // Mid-channel in the 1871 river (between the controls too) is mid-channel today, along every
  // reach paired: the main stem, both Branches and the canal.
  const plan = json('data/context/1871/plan.json');
  let n = 0, inToday = 0;
  for (const id of ['main_stem', 'north_branch', 'north_branch_canal', 'south_branch']) {
    const P = plan.rivers.find((r) => r.id === id).points;
    for (let i = 0; i + 1 < P.length; i++) {
      const [a, b] = [P[i], P[i + 1]], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      for (let s = 0; s < L; s += 25) {
        const c = [a[0] + (b[0] - a[0]) * s / L, a[1] + (b[1] - a[1]) * s / L];
        if ((id === 'south_branch' && c[1] < -1620 && c[1] > -3250) || (id === 'main_stem' && c[0] > 1560)) continue;
        n++; if (wet(reg.toToday(c[0], c[1]))) inToday++;
      }
    }
  }
  expect('1871: at least 95% of the 1871 river\'s middle lands in today\'s river', inToday / n >= 0.95, { n, inToday });
  const back = [[-1186, 1482.5], [1.4, -233.4], [900, -534], [-2435, -558]].map(([e, nn]) => {
    const [te, tn] = reg.toToday(e, nn); const [se, sn] = reg.toScene(te, tn); return Math.hypot(se - e, sn - nn);
  });
  expect('1871: toScene undoes toToday to 5 cm', back.every((d) => d < 0.05), back);
}
expect('a year with no controls is the identity', (() => { const r = createRegistration('1999'); const [e, n] = r.toToday(12, 34); return r.count === 0 && e === 12 && n === 34; })(), null);
// The window turns with the registration: grid north at the fort stays near north.
const fortLook = onToday(createRegistration('1812'), { e: 1140, n: 250, bearingDeg: 0 });
expect('the look carried through the registration keeps its bearing within 15°', Math.min(fortLook.bearingDeg, 360 - fortLook.bearingDeg) < 15, fortLook);
expect('and the spot moves south-west toward the fort\'s site, about 44 m', (() => { const d = Math.hypot(fortLook.e - 1140, fortLook.n - 250); return d > 35 && d < 55 && fortLook.n < 225; })(), fortLook);

// --- small helpers ---------------------------------------------------------------
expect('the key is used only on its hosts', keyFor({ config: { googleMapsKey: 'K', hosts: ['chicago.polecat.live'] }, hostname: 'chicago.polecat.live' }) === 'K'
  && keyFor({ config: { googleMapsKey: 'K', hosts: ['chicago.polecat.live'] }, hostname: '127.0.0.1' }) === ''
  && keyFor({ config: { googleMapsKey: '', hosts: [] }, hostname: 'x', stored: 'L' }) === 'L', null);
expect('image dates read as a month', imageDateText('2024-07') === 'Jul 2024' && imageDateText('') === '', imageDateText('2024-07'));
expect('16 points', cardinal16(25) === 'NNE' && cardinal16(359) === 'N' && cardinal16(180) === 'S', cardinal16(25));

// --- the window -------------------------------------------------------------------
let clock = 0;
Object.defineProperty(globalThis, 'performance', { value: { now: () => clock }, configurable: true });

function fakeEl() {
  const attrs = new Map();
  const handlers = {};
  return {
    attrs, textContent: '', href: '', title: '',
    setAttribute(k, val) { attrs.set(k, String(val)); },
    getAttribute(k) { return attrs.get(k) ?? null; },
    toggleAttribute(k, on) { if (on) attrs.set(k, ''); else attrs.delete(k); return on; },
    addEventListener(t, fn) { handlers[t] = fn; },
    click() { handlers.click?.({ stopPropagation() {} }); },
  };
}
const IDS = ['today-view', 'today-pano', 'today-note', 'today-where', 'today-open', 'today-expand', 'today-close', 'street-today-key'];
const els = Object.fromEntries(IDS.map((id) => [id, fakeEl()]));
const root = { getElementById: (id) => els[id] ?? null };

const calls = { load: 0, getPanorama: 0, setPov: 0, setPano: 0, visible: [] };
const lib = {
  StreetViewPreference: { NEAREST: 'nearest' }, StreetViewSource: { OUTDOOR: 'outdoor' },
  StreetViewService: class { async getPanorama({ location }) {
    calls.getPanorama += 1;
    // A panorama every 10 m of latitude, 3 m east of where you asked.
    const step = 10 / 111320;
    const lat = Math.round(location.lat / step) * step;
    return { data: { location: { pano: `p${Math.round(location.lat / step)}`, latLng: { lat: () => lat, lng: () => location.lng + 3 / 83000 } }, imageDate: '2024-07' } };
  } },
  StreetViewPanorama: class {
    setPov() { calls.setPov += 1; }
    setPano() { calls.setPano += 1; }
    setVisible(on) { calls.visible.push(on); }
  },
};
const shownLog = [];
const tv = createTodayView({
  root, config: { googleMapsKey: 'TEST', hosts: ['test.host'] }, hostname: 'test.host',
  onShownChange: (on) => shownLog.push(on),
  load: async () => { calls.load += 1; return lib; },
});
const tick = () => new Promise((r) => setTimeout(r, 0));

// Hidden: updates cost nothing and nothing loads.
for (let i = 0; i < 100; i++) { clock += 16; tv.update({ e: 1405, n: -3300 + i * 0.05, bearingDeg: 10 }); }
expect('hidden, nothing loads', calls.load === 0 && calls.getPanorama === 0, calls);
expect('hidden at first', tv.shown === false && tv.state.mode === 'off', tv.state);

// Shown by the TODAY tag: loads once, asks once, aims.
els['street-today-key'].click();
await tick(); await tick(); await tick();
expect('the tag shows it and says so', tv.shown && shownLog.at(-1) === true && els['street-today-key'].getAttribute('aria-pressed') === 'true', tv.state);
expect('it loads Google once', calls.load === 1, calls);
expect('and goes live', tv.state.mode === 'live' && tv.state.pano?.id, tv.state);
expect('with the image date', /Jul 2024/.test(els['today-note'].textContent), els['today-note'].textContent);

// A minute of walking north at 1.4 m/s, 60 frames a second, turning slowly: queries are
// bounded by distance and time, the point of view by POV_MS.
const q0 = calls.getPanorama;
const p0 = calls.setPov;
let n = -3300;
for (let i = 0; i < 60 * 60; i++) {
  clock += 1000 / 60; n += 1.4 / 60;
  tv.update({ e: 1405, n, bearingDeg: 10 + i * 0.05, pitchDeg: -2 });
  if (i % 6 === 0) await tick();
}
const queries = calls.getPanorama - q0;
const walked = 1.4 * 60;
expect(`a minute's walk asks for at most one panorama per ${MOVE_M} m and per ${QUERY_MS} ms`,
  queries >= 10 && queries <= Math.ceil(walked / MOVE_M) + 1 && queries <= Math.ceil(60000 / QUERY_MS) + 1, { queries });
expect('the point of view is set at most 1 in 5 frames', calls.setPov - p0 <= 60 * 60 / 5 + 1 && calls.setPov - p0 > 100, calls.setPov - p0);
expect('the link follows you', /viewpoint=41\.8/.test(els['today-open'].href), els['today-open'].href);
expect('a panorama 3 m off is aimed at the spot 40 m ahead, not parallel to you', (() => {
  const s = tv.state; const d = Math.abs(((s.pov.heading - s.view.heading + 540) % 360) - 180); return d > 0.5 && d < 10;
})(), tv.state);

// Standing still and not turning: nothing more is asked or set.
const q1 = calls.getPanorama, p1 = calls.setPov;
for (let i = 0; i < 600; i++) { clock += 16; tv.update({ e: 1405, n, bearingDeg: 200, pitchDeg: -2 }); }
await tick();
expect('standing still costs nothing more', calls.getPanorama === q1 && calls.setPov - p1 <= 1, { q: calls.getPanorama - q1, p: calls.setPov - p1 });

// Big and small; hidden stops it drawing; shown again asks again.
els['today-expand'].click();
expect('expand makes it big', tv.expanded && els['today-view'].getAttribute('data-size') === 'big', tv.state);
els['today-close'].click();
expect('close hides it and the panorama stops drawing', !tv.shown && calls.visible.at(-1) === false && els['today-view'].attrs.has('hidden'), calls.visible);
const q2 = calls.getPanorama;
for (let i = 0; i < 100; i++) { clock += 16; tv.update({ e: 1405, n: n + i, bearingDeg: 0 }); }
expect('hidden again, nothing is asked', calls.getPanorama === q2, calls.getPanorama - q2);
tv.setShown(true);
await tick(); await tick();
expect('shown again, it asks afresh but does not load again', calls.getPanorama > q2 && calls.load === 1, calls);

// No key: the link card, and Google is never fetched.
let keylessLoads = 0;
const els2 = Object.fromEntries(IDS.map((id) => [id, fakeEl()]));
const card = createTodayView({ root: { getElementById: (id) => els2[id] }, config: { googleMapsKey: '', hosts: [] },
  hostname: 'chicago.polecat.live', load: async () => { keylessLoads += 1; return lib; } });
card.setShown(true);
card.update({ e: 1401.86, n: -3206.93, bearingDeg: 45 });
await tick();
expect('no key: a link card, nothing loads', card.state.mode === 'link' && keylessLoads === 0, card.state);
expect('no key: the link is at the corner, facing NE', /viewpoint=41\.857931,-87\.620775&heading=45/.test(els2['today-open'].href), els2['today-open'].href);
expect('no key: the card says how to see it', /Google Maps/.test(els2['today-note'].textContent), els2['today-note'].textContent);

if (fails.length) {
  console.log(`today window: ${fails.length} FAIL`);
  for (const f of fails) console.log(`  FAIL ${f}`);
  process.exit(1);
}
console.log('today window: projection, link, throttling and hide/show hold (T-3601)');

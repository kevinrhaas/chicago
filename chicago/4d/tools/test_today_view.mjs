#!/usr/bin/env node
// T-3601 — the Today window: the scene's local metres to latitude/longitude and a true
// heading (renderers/web/js/today-geo.js), and the window's throttling, link card and
// hide/show (renderers/web/js/today-view.js) against a stand-in for Google's Street View
// library. Pure: no browser, no network, no key.
import { localToLatLng, gridToTrueDeg, viewFromLocal, trueBearing, distanceM, streetViewUrl, DATUM }
  from '../renderers/web/js/today-geo.js';
import { createTodayView, keyFor, imageDateText, cardinal16, MOVE_M, QUERY_MS }
  from '../renderers/web/js/today-view.js';

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

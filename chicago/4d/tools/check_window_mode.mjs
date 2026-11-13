#!/usr/bin/env node
/**
 * T-3577 — Window mode (renderers/web/js/controls/window.js) and its wiring.
 *
 * Holds the projection to the datum (latitude and longitude land in the scene's own
 * East-North metres, checked against the datum's own origin and against a UTM point
 * computed independently), the compass corrections, the device-frame look (upright
 * and facing north looks north; turned left looks west; tipped back looks up), the
 * GPS hysteresis, the out-of-town refusal, the line-up drag and the hand-back, against
 * stand-ins; and reads main.js and index.html for the wiring. A real device's sensors
 * are not claimed here.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const w = await import(pathToFileURL(path.join(web, 'js/controls/window.js')).href);
const THREE = await import(pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href);
const { createIntent, createBackendSwitch } = await import(pathToFileURL(path.join(web, 'js/controls/intent.js')).href);
const datum = JSON.parse(await readFile(path.join(root, 'data/datum.json'), 'utf8'));
const main = await readFile(path.join(web, 'js/main.js'), 'utf8');
const html = await readFile(path.join(web, 'index.html'), 'utf8');

const checks = [];
function check(name, run) { run(); checks.push(name); }
const near = (a, b, eps) => Math.abs(a - b) <= eps;
const DEG = Math.PI / 180;

check('the datum\'s own origin projects to its own UTM origin, to within a metre', () => {
  const at = w.toLocal(datum.origin_lat, datum.origin_lon, datum);
  assert.ok(Math.hypot(at.e, at.n) < 1.5, `origin lands at ${at.e.toFixed(2)}, ${at.n.toFixed(2)}`);
});

check('UTM 16N matches a known point (the Krüger series, not a flat-earth guess)', () => {
  // 42 N, 87 W sits on zone 16's central meridian: easting 500000, northing 4649776.22 (GRS80).
  const u = w.latLonToUtm(42, -87);
  assert.ok(near(u.e, 500000, 0.01));
  assert.ok(near(u.n, 4649776.22, 0.05), `northing ${u.n}`);
  // A degree west of the meridian the easting falls by about 82.9 km.
  assert.ok(near(500000 - w.latLonToUtm(42, -88).e, 82_950, 300));
});

check('north is up and east is right: a fix 0.01 degrees north and east lands at about +1.1 km N, +0.83 km E', () => {
  const o = w.toLocal(datum.origin_lat, datum.origin_lon, datum);
  const p = w.toLocal(datum.origin_lat + 0.01, datum.origin_lon + 0.01, datum);
  assert.ok(near(p.n - o.n, 1110, 15) && near(p.e - o.e, 829, 15), `${p.e - o.e}, ${p.n - o.n}`);
});

check('the grid convergence west of the central meridian is small and negative here', () => {
  const g = w.gridConvergenceDeg(41.857, -87.623);
  assert.ok(g < 0 && g > -0.6, `${g}`);
});

check('?window-at= is read and checked', () => {
  assert.deepEqual(w.windowAt('?year=1904&window-at=41.8573,-87.6237'), { lat: 41.8573, lon: -87.6237 });
  assert.equal(w.windowAt('?window-at=95,0'), null);
  assert.equal(w.windowAt('?window-at=nope'), null);
  assert.equal(w.windowAt(''), null);
});

check('the compass: iOS\'s heading as given, an absolute alpha turned to clockwise, a relative one refused', () => {
  assert.equal(w.magneticHeading({ webkitCompassHeading: 90, alpha: 12 }), 90);
  assert.equal(w.magneticHeading({ absolute: true, alpha: 90 }), 270);
  assert.equal(w.magneticHeading({ absolute: false, alpha: 90 }), null);
});

check('the device frame: upright facing north looks north and level; turned left looks west; tipped back looks up', () => {
  let l = w.deviceLook(THREE, 0, 90, 0);
  assert.ok(near(l.yaw, 0, 1e-6) && near(l.pitch, 0, 1e-6), JSON.stringify(l));
  l = w.deviceLook(THREE, 90, 90, 0);
  assert.ok(near(l.yaw, 90 * DEG, 1e-6), JSON.stringify(l));
  l = w.deviceLook(THREE, 0, 120, 0);
  assert.ok(near(l.pitch, 30 * DEG, 1e-6), JSON.stringify(l));
  // A landscape iPad (screen turned 90) held upright still looks north.
  l = w.deviceLook(THREE, 90, 0, -90, 90);
  assert.ok(near(l.yaw, 0, 1e-6) && near(l.pitch, 0, 1e-6), JSON.stringify(l));
});

check('GPS wander under half the accuracy (never under 3 m) does not move you', () => {
  assert.equal(w.moveThreshold(2), w.MOVE_MIN_M);
  assert.equal(w.moveThreshold(20), 10);
});

function rig({ inBounds = () => true, search = '' } = {}) {
  const listeners = {};
  const win = {
    DeviceOrientationEvent: function () {},
    screen: { orientation: { angle: 0 } },
    addEventListener: (k, fn) => { listeners[k] = fn; },
    removeEventListener: (k) => { delete listeners[k]; },
  };
  const watched = [];
  const nav = { geolocation: { watchPosition: (ok) => { watched.push(ok); return 7; }, clearWatch: () => { watched.length = 0; } } };
  const state = { e: 0, n: 0, yaw: 0, pitch: 0 };
  const teleports = [];
  const walker = { state, get bearingDeg() { return 0; }, teleport: (t) => { teleports.push(t); state.e = t.local_e; state.n = t.local_n; } };
  const intent = createIntent();
  const backends = createBackendSwitch(intent);
  const page = { name: 'touch' };
  backends.activate(page);
  const said = [];
  const changes = [];
  const surfaceListeners = {};
  const surface = { addEventListener: (k, fn) => { surfaceListeners[k] = fn; }, removeEventListener: (k) => { delete surfaceListeners[k]; } };
  const mode = w.createWindowMode({ THREE, walker, intent, backends, fallback: () => page, datum, inBounds,
    say: (l) => said.push(l), onChange: (on) => changes.push(on), surface, search, win, nav });
  return { mode, walker, intent, backends, page, said, changes, teleports, watched, listeners, surfaceListeners, win };
}

await (async () => {
  const r = rig();
  assert.equal(r.mode.supported(), true);
  assert.equal(await r.mode.start(), true);
  assert.equal(r.backends.name, 'window');
  assert.equal(r.watched.length, 1, 'location is watched');
  // A fix at the river forks sets the visitor down there.
  r.watched[0]({ coords: { latitude: datum.origin_lat, longitude: datum.origin_lon, accuracy: 8 } });
  assert.equal(r.teleports.length, 1);
  assert.ok(Math.hypot(r.walker.state.e, r.walker.state.n) < 1.5);
  assert.match(r.said.at(-1), /GPS, ±8 m/);
  // Wander of a couple of metres does nothing; a real walk does.
  r.watched[0]({ coords: { latitude: datum.origin_lat + 0.00002, longitude: datum.origin_lon, accuracy: 8 } });
  assert.equal(r.teleports.length, 1, 'two metres of wander under ±8 m is not a move');
  r.watched[0]({ coords: { latitude: datum.origin_lat + 0.0002, longitude: datum.origin_lon, accuracy: 8 } });
  assert.equal(r.teleports.length, 2, 'twenty metres is');
  checks.push('a fix sets you down where you stand, and wander inside the accuracy does not move you');

  // iOS: facing magnetic east, upright. The view turns to (about) east in the grid.
  r.listeners.deviceorientation({ type: 'deviceorientation', alpha: 200, beta: 90, gamma: 0, webkitCompassHeading: 90 });
  r.mode.backend.update();
  const bearing = (-(r.intent.yawDelta) / DEG + 360) % 360;
  const expected = 90 + w.DECLINATION_DEG - w.gridConvergenceDeg(datum.origin_lat, datum.origin_lon);
  assert.ok(near(bearing, expected, 0.01), `bearing ${bearing} vs ${expected}`);
  checks.push('the compass turns the view, declination and grid convergence taken out');

  // A sideways drag lines the view up: dragging right turns the view left... by the drag.
  r.intent.clearLook();
  r.surfaceListeners.pointerdown({ pointerId: 1, clientX: 100 });
  r.surfaceListeners.pointermove({ pointerId: 1, clientX: 140 });
  r.listeners.pointerup({ pointerId: 1 });
  assert.ok(near(r.mode.offsetDeg, 40 * w.ALIGN_DEG_PER_PX, 1e-9));
  r.listeners.deviceorientation({ type: 'deviceorientation', alpha: 200, beta: 90, gamma: 0, webkitCompassHeading: 90 });
  r.mode.backend.update();
  const lined = (-(r.intent.yawDelta) / DEG + 360) % 360;
  assert.ok(near(degDiffAbs(lined, expected), 40 * w.ALIGN_DEG_PER_PX, 0.2), `lined ${lined}`);
  checks.push('a sideways drag lines the view up with the street');

  r.mode.stop();
  assert.equal(r.backends.active, r.page);
  assert.equal(r.watched.length, 0, 'location watch cleared');
  assert.deepEqual(r.changes, [true, false]);
  checks.push('closing the window hands the page\'s controls back and stops watching the location');
})();

function degDiffAbs(a, b) { return Math.abs(w.degDiff(a, b)); }

await (async () => {
  const r = rig({ inBounds: () => false });
  await r.mode.start();
  r.watched[0]({ coords: { latitude: 41.95, longitude: -87.65, accuracy: 5 } });
  assert.equal(r.teleports.length, 0);
  assert.match(r.said.at(-1), /outside this year's town/);
  checks.push('a fix outside the year\'s ground is said, never walked to');
})();

await (async () => {
  const r = rig({ search: '?window-at=41.8573,-87.6237' });
  await r.mode.start();
  assert.equal(r.watched.length, 0, '?window-at= stands in for the GPS');
  assert.equal(r.teleports.length, 1);
  checks.push('?window-at= places the visitor without the GPS');
})();

await (async () => {
  const r = rig();
  r.win.DeviceOrientationEvent.requestPermission = async () => 'denied';
  assert.equal(await r.mode.start(), false);
  assert.equal(r.backends.active, r.page);
  assert.match(r.said.at(-1), /motion access/);
  checks.push('iOS motion permission refused: nothing starts, and it says why');
})();

check('the key ships hidden, is offered only on a touch device or with ?window-at=, and pausing closes it', () => {
  assert.match(html, /<button[^>]*id="btn-window"[^>]*hidden/);
  assert.match(main, /windowKey\.hidden = !\(\(coarse \|\| windowAt\(location\.search\)\) && windowMode\.supported\(\)\)/);
  assert.match(main, /windowMode\.stop\(\); \/\/ T-3577/);
  assert.match(main, /if \(gateOpen \|\| xrMode\?\.presenting \|\| windowMode\?\.on/);
});

for (const name of checks) console.log(`ok - ${name}`);
console.log(`check_window_mode: ${checks.length} checks passed`);

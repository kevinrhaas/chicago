#!/usr/bin/env node
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createRouter } from '../renderers/web/js/route.js';
import { createTravel } from '../renderers/web/js/travel.js';
import { register } from 'node:module';
// Use the same vendored Three modules as the browser; the gate needs no npm install.
const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { createWalker, footprintsFrom } = await import('../renderers/web/js/walker.js');
import { createIntent } from '../renderers/web/js/controls/intent.js';
const read = path => JSON.parse(fs.readFileSync(new URL(`../data/${path}`, import.meta.url)));
const dry = { heightfield: { loaded: true, originE: -50, originN: -50, widthM: 200, depthM: 200 },
  surfaceHeight: () => 1, walkHeight: () => 1, isWater: () => false };
const obstacle = { id: 'house', pts: [[30, 25], [70, 25], [70, 75], [30, 75]] };
const street = { id: 'bent', path: [[0, 0], [100, 0], [100, 100]], track_width_m: 8, corridor_width_m: 16 };
const walks = [{ centreline_local_enu_m: [[0, -6], [106, -6], [106, 100]], width_m: 2 }];
const router = createRouter({ terrain: dry, streets: { records: [street] }, walks,
  footprints: [obstacle], cell: 1, inflate: 0.1 });
function safe(r, route) {
  assert(route?.points.length, 'a route exists');
  for (let i = 1; i < route.points.length; i++) assert(r.clearSegment(...route.points[i - 1], ...route.points[i]),
    `segment ${i} clears every building and unsafe step`);
}
for (const mode of ['walk', 'horse', 'wagon']) {
  const from = mode === 'walk' ? { e: 0, n: -6 } : { e: 0, n: 0 };
  const to = mode === 'walk' ? { e: 106, n: 100 } : { e: 100, n: 100 };
  const route = router.plan(from, to, { mode }); safe(router, route);
  assert(route.length_m > 190, 'street bend is not shortened through the block');
  let sidewalk = 0, count = 0;
  for (let i = 1; i < route.points.length; i++) {
    const [ae, an] = route.points[i - 1], [be, bn] = route.points[i];
    const steps = Math.ceil(Math.hypot(be - ae, bn - an) / 0.25);
    for (let s = 0; s <= steps; s++) {
      const c = router.classAt(ae + (be - ae) * s / steps, an + (bn - an) * s / steps);
      assert.notEqual(c, 'open', 'joined routes stay on the street network');
      if (mode !== 'walk') assert.equal(c, 'track', 'horse and wagon stay on the road');
      sidewalk += c === 'sidewalk'; count++;
    }
  }
  if (mode === 'walk') assert(sidewalk / count > 0.95, 'walking follows the plank sidewalk');
  assert.equal(router.plan({ e: 50, n: 50 }, to, { mode }), null, 'never snap through a building to reach a route');
}
// A barrier thinner than a grid cell must still prevent a pulled route crossing it.
const thin = createRouter({ terrain: dry, footprints: [{ id: 'thin', pts: [[49.9, -30], [50.1, -30], [50.1, 70], [49.9, 70]] }] });
const detour = thin.plan({ e: 40, n: 0 }, { e: 60, n: 0 }); safe(thin, detour);
assert(detour.length_m > 60, 'thin wall causes a real detour');

// The actual 1835 hotel has a short walk at its front and a board crossing.
// Arrival belongs on a sidewalk with room to see the facade, not in that crossing.
const hotel = read('sidecars/1835/sauganash_hotel.json');
const hotelFP = footprintsFrom(new Map([[hotel.id, { id: hotel.id, sidecar: hotel }]]));
const oldStreets = read('sidecars/1835/index.json').streets
  .filter(r => r.opened !== false && (r.track_width_m ?? 6) > 0)
  .map(r => ({ ...r, path: r.path_local_enu_m, drawn: r.drawn_track_local_enu_m }));
const oldWalks = fs.readdirSync(new URL('../data/frontage/', import.meta.url)).filter(n => n.endsWith('.json'))
  .flatMap(name => read(`frontage/${name}`).walks ?? []);
const town = createRouter({ streets: { records: oldStreets }, walks: oldWalks, footprints: hotelFP, cell: 1, inflate: 0.1 });
const hotelCentre = { e: 106.36, n: -126.6 };
const hotelArrival = town.standOff(hotel.id, hotelCentre, 6.5, { mode: 'walk', distance: 60 });
assert.equal(town.classAt(hotelArrival.e, hotelArrival.n), 'sidewalk');
assert(hotelArrival.n > -104, 'arrival uses the opposite sidewalk, with a view of the front');

// Read the real 1904 parcel and footprint geometry: the nearest side street is
// 18th, but Glessner's addressed front is Prairie. Flat ground isolates geometry;
// browser verification separately uses the published terrain and camera.
const registry = new Map();
for (const name of fs.readdirSync(new URL('../data/sidecars/1904/', import.meta.url)).filter(n => n.endsWith('.json'))) {
  const sidecar = read(`sidecars/1904/${name}`); if (sidecar.footprint) registry.set(sidecar.id, { id: sidecar.id, sidecar });
}
const footprints = footprintsFrom(registry), fp = footprints.find(f => f.id === 'glessner_house');
const centre = { e: fp.pts.reduce((s, p) => s + p[0], 0) / fp.pts.length, n: fp.pts.reduce((s, p) => s + p[1], 0) / fp.pts.length };
const terrain = { ...dry, heightfield: { loaded: true, originE: 1100, originN: -3800, widthM: 700, depthM: 900 } };
const city = createRouter({ terrain, streetGrid: read('street_grid/1904.json'), footprints, cell: 1, inflate: 0.1 });
// T-3264: two stands in Glessner's courtyard, ten metres apart, are walked between across
// the court, not out of the alley gate to 18th Street's walk and back in.
for (const mode of ['walk', 'horse', 'wagon']) {
  const inCourt = city.plan({ e: 1360.7, n: -3239.0 }, { e: 1370.6, n: -3234.6 }, { mode }); safe(city, inCourt);
  assert(inCourt.length_m < 20, `${mode}: a courtyard hop stays in the courtyard (${inCourt.length_m.toFixed(1)} m)`);
}
// …and the court is reached from Prairie Avenue's walk through the carriage passage the
// walker can use (T-2943), not round the block and in through the closed alley gate.
const viaPassage = city.plan({ e: 1393.4, n: -3237.4 }, { e: 1360.7, n: -3239.0 }, { mode: 'walk' }); safe(city, viaPassage);
assert(viaPassage.length_m < 50, `the court is entered by the passage (${viaPassage.length_m.toFixed(1)} m)`);
const lowSoffit = createRouter({ terrain, streetGrid: read('street_grid/1904.json'), footprints, cell: 1, inflate: 0.1, passageNeed: 3 });
assert(lowSoffit.plan({ e: 1393.4, n: -3237.4 }, { e: 1360.7, n: -3239.0 }, { mode: 'walk' }).length_m > 100,
  'a passage too low for the eye stays a wall');

// The start stands on Indiana Avenue's east walk in front of 1809, the far side of the block from
// Glessner's front. Until T-3151 it stood at e 1300, open ground behind T-3011's background row;
// the sheet-27 drafts put 1809's house on that spot, so the walker starts at its street instead.
const start = { e: 1273, n: -3230 };
for (const mode of ['walk', 'horse', 'wagon']) {
  const stand = city.standOff(fp.id, centre, 25, { mode, distance: 60 });
  assert.equal(stand.front.street, 'prairie'); assert(stand.e > 1390);
  assert(Math.abs(stand.n + 3229) < 3, 'arrival faces the middle of the east front');
  assert.equal(city.classAt(stand.e, stand.n), mode === 'walk' ? 'sidewalk' : 'track');
  const route = city.plan(start, stand, { mode }); safe(city, route);
  assert(route.length_m > 120, 'back-of-house approach goes around the block');
  const camera = new THREE.PerspectiveCamera();
  const walker = createWalker({ camera, terrain, footprints, spawn: { local_e: start.e, local_n: start.n } });
  const intent = createIntent();
  let arrivals = 0, teleports = 0, stops = 0;
  const travel = createTravel({ walker, intent, router: city, terrain,
    settings: { horseSpeed: 26.82, wagonSpeed: 13.41 },
    structurePosition: () => centre, standFor: () => ({ ...stand, aim: { x: stand.front.e, y: 6, z: -stand.front.n } }),
    frame: () => { teleports++; return true; } });
  travel.setMode(mode);
  assert(travel.go({ kind: 'structure', id: fp.id }, { onArrive: () => arrivals++, onStop: () => stops++ }));
  // Inspect every simulated step, including high-speed turns, not just waypoints.
  for (let i = 0; i < 15000 && travel.state.phase !== 'idle'; i++) {
    const before = { ...walker.state };
    travel.update(1 / 30, intent); walker.update(1 / 30, intent); travel.afterWalk(intent, 1 / 30);
    assert(city.clearSegment(before.e, before.n, walker.state.e, walker.state.n), 'actual movement clears buildings');
  }
  assert.equal(arrivals, 1); assert.equal(stops, 0); assert.equal(teleports, 0);
  assert(Math.hypot(walker.state.e - stand.e, walker.state.n - stand.n) < 0.1);
  assert(Math.abs(Math.atan2(Math.sin(walker.state.yaw - Math.PI / 2), Math.cos(walker.state.yaw - Math.PI / 2))) < 0.05,
    'arrival faces west towards the Prairie facade');
}
// Missing routes report failure without silently changing the visitor's position.
let jumped = false, stopped = false;
const failed = createTravel({ walker: { state: { e: 0, n: 0 }, resettle() {} }, intent: { flying: false },
  router: { plan: () => null }, structurePosition: () => ({ e: 20, n: 20 }), frame: () => { jumped = true; } });
failed.setMode('walk');
assert.equal(failed.go({ kind: 'structure', id: 'missing' }, { onStop: () => stopped = true }), false);
assert(stopped && !jumped);
console.log('STREET TRAVEL PASS — sidewalks, roadways, street bends, thin walls, Glessner frontage, high-speed obstacle-safe movement and no teleport fallback');

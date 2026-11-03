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
const { createWalker, footprintsFrom, WALK } = await import('../renderers/web/js/walker.js');
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

// A bridge's walkable deck is not an obstruction footprint. Execute the actual
// main.js framing closure: rotated rendered bounds and the water datum must win
// over its end placement, terrain bed and the router's synthetic frontage.
{
  const source = fs.readFileSync(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
  const actual = name => {
    const start = source.indexOf(`  function ${name}(`);
    const end = source.indexOf('\n  }\n', start);
    assert(start >= 0 && end > start, `Actual ${name} closure exists`);
    return source.slice(start, end + '\n  }'.length);
  };
  const functions = ['waterStructureFrame', 'structurePosition', 'focusPoint', 'framing', 'freeRegion'].map(actual).join('\n');
  const bridge = read('sidecars/1835/dearborn_street_drawbridge.json');
  const p = bridge.placement, yaw = -p.rotation_deg * Math.PI / 180;
  const matrix = new THREE.Matrix4().makeRotationY(yaw);
  // Deliberately different from the bed: the bridge's origin is its water datum.
  matrix.setPosition(p.local_e, 12.25, -p.local_n);
  const box = { min: [-0.8598391946505107, -0.5488836502837506, -5.479413607553664],
    max: [77.19000244140625, 8.61723773707279, 2.478221459650239],
    size: [78.04984163605675, 9.16612138735654, 7.957635067203904] };
  const bounds = { [bridge.id]: box, house: { min: [0, 0, -8], max: [10, 6, 0], size: [10, 6, 8] },
    camp: { min: [0, 0, -4], max: [4, 3, 0], size: [4, 3, 4] } };
  const registry = new Map([[bridge.id, { sidecar: bridge }],
    ['house', { sidecar: { placement: { local_e: 0, local_n: 0 }, attributes: {} } }],
    ['camp', { sidecar: { placement: { local_e: 30, local_n: 40 }, archetype: 'camp' } }],
    ['pen', { sidecar: { placement: { local_e: 50, local_n: 60 }, drawn_by: 'enclosures' } }]]);
  const syntheticFront = { e: 9999, n: -9999, width: 12 };
  const calls = [];
  const router = { standOff(id, centre, radius, options) {
    calls.push({ id, centre, radius, ...options });
    return { e: centre.e + options.distance, n: centre.n, front: syntheticFront };
  } };
  const deps = { THREE, buildingBounds: bounds, buildings: { matrixOf: id => id === bridge.id ? matrix : null },
    loaded: { registry }, footprints: [{ id: 'house', pts: [[0, 0], [10, 0], [10, 8], [0, 8]] }],
    terrain: { surfaceHeight: () => -7 }, enclosures: { records: [{ structure_id: 'pen',
      runs: [{ path_local_enu_m: [[50, 60], [60, 60], [60, 70], [50, 70]] }], form: { height_m: { value: 2 } } }] },
    enuToWorld: (e, n, y) => new THREE.Vector3(e, y, -n), router,
    popup: { openId: null }, handInspect: null, travel: { mode: 'walk' },
    camera: null, window: null, DEG: Math.PI / 180 };
  const make = profile => {
    const aspect = profile[0] / profile[1], fov = 2 * Math.atan(Math.tan(38 * Math.PI / 180) / aspect) * 180 / Math.PI;
    deps.camera = new THREE.PerspectiveCamera(fov, aspect, 0.1, 10000);
    deps.window = { innerWidth: profile[0], innerHeight: profile[1] };
    return new Function(...Object.keys(deps), functions + '\nreturn { framing, focusPoint, structurePosition, waterStructureFrame };')(...Object.values(deps));
  };
  const expectedCentre = new THREE.Vector3(...box.min).add(new THREE.Vector3(...box.max)).multiplyScalar(0.5).applyMatrix4(matrix);
  for (const profile of [[1280, 800], [390, 780]]) {
    const native = make(profile), f = native.framing(bridge.id, { card: false });
    const call = calls.at(-1);
    assert(Math.hypot(call.centre.e - expectedCentre.x, call.centre.n + expectedCentre.z) < 1e-10,
      'Use the rotated rendered centre rather than the south abutment');
    assert(Math.abs(f.radius - Math.hypot(box.size[0], box.size[2]) / 2) < 1e-10);
    assert(f.aim.distanceTo(expectedCentre) < 1e-10, 'Synthetic 12m frontage cannot override the bridge centre or water Y');
    assert.deepEqual(native.structurePosition(bridge.id), { e: p.local_e, n: p.local_n }, 'Navigation position stays unchanged');
    assert(f.distance <= 90, 'Existing stand-off cap remains');
    const camera = deps.camera;
    camera.position.set(f.e, -7 + WALK.eyeHeight, -f.n); camera.lookAt(f.aim); camera.updateMatrixWorld();
    for (const x of [box.min[0], box.max[0]]) for (const y of [box.min[1], box.max[1]]) for (const z of [box.min[2], box.max[2]]) {
      const point = new THREE.Vector3(x, y, z).applyMatrix4(matrix).project(camera);
      assert(Math.abs(point.x) < 1 && Math.abs(point.y) < 1 && point.z < 1,
        `${profile}: complete bridge bounds fit in the unchanged camera projection`);
    }
    const house = native.framing('house', { card: false });
    assert.equal(house.aim.x, syntheticFront.e); assert.equal(house.aim.z, -syntheticFront.n);
    assert.equal(house.radius, Math.hypot(10, 8) / 2, 'Ordinary footprint radius unchanged');
    assert.equal(house.aim.y, -4, 'Ordinary footprint ground datum unchanged');
    const camp = native.framing('camp', { card: false });
    assert.equal(camp.radius, 6); assert.equal(camp.aim.y, -5.5, 'Non-water missing-footprint fallback unchanged');
    assert.equal(native.waterStructureFrame('house'), null); assert.equal(native.waterStructureFrame('camp'), null);
    assert.deepEqual(native.focusPoint('pen').toArray(), [55, -5.9, -65], 'Enclosure focus path unchanged');
  }
  console.log('WATER STRUCTURE FRAMING PASS — actual main closures, rotated bounds/water datum, synthetic frontage, both viewports, house/camp/enclosure controls');
}

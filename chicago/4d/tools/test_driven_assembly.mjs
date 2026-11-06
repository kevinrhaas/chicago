// SPDX-License-Identifier: GPL-3.0-or-later
// Real THREE transforms plus the actual source GLB hierarchy, not a browser/mesh claim.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as THREE from '../renderers/web/vendor/three-0.185.1/three.module.js';
import { createDrivenAssembly, createTownTransport } from '../renderers/web/js/town-transport.js';
import { circleRoute, createTransportLoop } from '../renderers/web/js/transport-loop.js';

const path = new URL('../renderers/web/transport/wagon-driver/wagon-w01.glb', import.meta.url);
const until = async predicate => { for (let i = 0; i < 1000; i++) { if (predicate()) return; await new Promise(r => setTimeout(r, 2)); } throw Error('bounded asynchronous test did not reach expected state'); };
const bytes = readFileSync(path), doc = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)).toString());
const objects = doc.nodes.map(n => {
  const node = new THREE.Group(); node.name = n.name;
  if (n.translation) node.position.fromArray(n.translation);
  if (n.rotation) node.quaternion.fromArray(n.rotation);
  if (n.scale) node.scale.fromArray(n.scale);
  return node;
});
doc.nodes.forEach((n, i) => n.children?.forEach(child => objects[i].add(objects[child])));
const vehicle = new THREE.Group();
doc.scenes[doc.scene ?? 0].nodes.forEach(i => vehicle.add(objects[i]));
let vehicleReleased = 0, driverReleased = 0, horseReleased = 0, horseDistance = 0, driverTime = 0, stops = 0;
const driver = { root: new THREE.Group(), update(dt) { driverTime += dt; }, dispose() { driverReleased++; } };
const horse = { root: new THREE.Group(), advance(m) { horseDistance += m; }, stop() { stops++; }, dispose() { horseReleased++; } };
const options = { vehicle, driver, horse, driverSeat_m: [0, 1.58, .65], horseOffset_m: [0, 0, 5], disposeVehicle() { vehicleReleased++; } };
assert.throws(() => createDrivenAssembly({ ...options, driverSeat_m: [0, 1.6, .65] }), /actual vehicle seat/);
const assembly = createDrivenAssembly(options);
const route = circleRoute({ center_enu_m: [0, 0], radius_m: 20 });
const actor = createTransportLoop({ id: 'actual-source-hierarchy', name: 'Driver', route, assembly,
  speed_m_s: 1, wheelbase_m: 2.35, track_m: 1.21, root_ahead_of_rear_axle_m: 1.175, steering_limit_deg: 8,
  driver_local_m: [0, 1.58, .65], wheel_radii_m: [.685, .685, .535, .535], heightAt: () => 0 });
const seatBefore = vehicle.getObjectByName('vehicle_seat_driver').position.toArray();
actor.update(.2);
assert.equal(driver.root.parent, vehicle);
assert.equal(horse.root.parent, vehicle);
assert.deepEqual(vehicle.getObjectByName('vehicle_seat_driver').position.toArray(), seatBefore);
assert.equal(driverTime, .2);
assert(horseDistance > .2, 'horse centre on the forward offset travels its own longer arc');
assert(horseDistance < .25);
assert(vehicle.getObjectByName('vehicle_steer_front').rotation.y > 0);
assert(vehicle.getObjectByName('vehicle_wheel_rear_left').rotation.x > 0);
assert(vehicle.getObjectByName('vehicle_wheel_front_left').rotation.x > 0);
const expected = new THREE.Vector3(0, 1.58, .65).applyMatrix4(vehicle.matrixWorld);
const actual = vehicle.getObjectByName('vehicle_seat_driver').getWorldPosition(new THREE.Vector3());
assert(actual.distanceTo(expected) < 1e-12);
actor.stop(); const before = horseDistance; actor.update(2);
assert.equal(horseDistance, before); assert(stops > 0);
actor.dispose(); actor.dispose();
assert.equal(vehicleReleased, 1); assert.equal(driverReleased, 1); assert.equal(horseReleased, 1);
assert.equal(driver.root.parent, null); assert.equal(horse.root.parent, null);

// Light never acquires a heavy assembly; a pending asset finished after disposal is
// released exactly once, and cannot add a new actor to a disposed scene.
let acquired = 0, pendingRelease = 0, resolve;
const validRow = { id: 'a', name: 'Driver', scene: '1835', route: { center_enu_m: [0, 0], radius_m: 20 },
  speed_m_s: 1, wheelbase_m: 2.35, track_m: 1.21, root_ahead_of_rear_axle_m: 1.175,
  steering_limit_deg: 8, driver_local_m: [0, 1.58, .65], wheel_radii_m: [.685, .685, .535, .535] };
const layer = createTownTransport({ rows: [validRow], sceneId: '1835',
  makeAssembly: () => { acquired++; return new Promise(r => { resolve = r; }); },
  heightAt: () => 0, clear: () => true, detail: 'light' });
await layer.ready(); assert.equal(acquired, 0);
layer.update(0, { x: 20, z: 0 });
const pending = layer.setTier('full');
await until(() => acquired === 1);
assert.equal(acquired, 1);
layer.dispose(); resolve({ dispose() { pendingRelease++; } }); await pending;
assert.equal(pendingRelease, 1); assert.equal(layer.actors.length, 0);

// Full->Light->Full while the first parse is pending: retire that old generation,
// keep one new actor, and do not let the old Light completion clear the new load.
const pendingLoads = [];
const row = { id: 'race', name: 'Driver', scene: '1835', route: { center_enu_m: [0, 0], radius_m: 20 },
  speed_m_s: 1, wheelbase_m: 2.35, track_m: 1.21, root_ahead_of_rear_axle_m: 1.175,
  steering_limit_deg: 8, driver_local_m: [0, 1.58, .65], wheel_radii_m: [.685, .685, .535, .535] };
let retired = 0;
const race = createTownTransport({ rows: [row], sceneId: '1835', heightAt: () => 0, clear: () => true,
  makeAssembly: () => new Promise(r => pendingLoads.push(r)) });
race.update(0, { x: 20, z: 0 });
const oldReady = race.ready(); await until(() => pendingLoads.length === 1);
const light = race.setTier('light'), newReady = race.setTier('full');
await until(() => pendingLoads.length === 2);
assert.equal(pendingLoads.length, 2);
pendingLoads[0]({ root: {}, pose() {}, dispose() { retired++; } }); await oldReady; await light;
pendingLoads[1]({ root: {}, pose() {}, dispose() { retired++; } }); await newReady;
assert.equal(retired, 1); assert.equal(race.actors.length, 1);
await race.ready(); assert.equal(pendingLoads.length, 2);
race.actors[0].update(.2); race.actors[0].stop(); const journey = race.actors[0].snapshot();
await race.setTier('light'); assert.equal(retired, 2); assert.equal(race.actors.length, 0);
const reload = race.setTier('full'); await until(() => pendingLoads.length === 3); pendingLoads[2]({ root: {}, pose() {}, dispose() { retired++; } }); await reload;
assert.equal(race.actors[0].state, 'stopped');
assert.equal(race.actors[0].snapshot().distance_m, journey.distance_m);
assert.deepEqual(race.actors[0].snapshot().wheel_rotation_rad, journey.wheel_rotation_rad);
race.dispose(); assert.equal(retired, 3);

// The real new team path uses poseVehicle rather than advance: it still receives
// exactly one stop after motion and another after motion resumes then hides.
let teamStops = 0, teamPoses = 0;
const teamVehicle = vehicle.clone(true);
const teamAssembly = createDrivenAssembly({ vehicle: teamVehicle,
  driver: { root: new THREE.Group() },
  horse: { root: new THREE.Group(), poseVehicle() { teamPoses++; }, stop() { teamStops++; } },
  driverSeat_m: [0, 1.58, .65], horseOffset_m: [0, 0, 3.4987], disposeVehicle() {} });
const drivenTeam = createTransportLoop({ ...validRow, route, assembly: teamAssembly, heightAt: () => 0 });
drivenTeam.update(.1); drivenTeam.stop(); drivenTeam.stop();
assert.equal(teamStops, 1); assert(teamPoses > 1);
drivenTeam.resume(); drivenTeam.update(.1); drivenTeam.update(.1, { drawn: false });
assert.equal(teamStops, 2); drivenTeam.dispose();

// A Light switch while the first cooperative yield is pending cancels before
// any ground read, support sample or asset acquisition; an eligible scene only.
let earlyGround = 0, earlySupport = 0, earlyAssets = 0;
const early = createTownTransport({ rows: [{ ...validRow, horse_offset_m: [0, 0, 5] }], sceneId: '1835',
  heightAt() { earlyGround++; return 0; }, routeSupport() { earlySupport++; }, clear: () => true,
  makeAssembly() { earlyAssets++; throw Error('cancelled preflight must not acquire'); } });
const earlyReady = early.ready();
assert.equal(earlyGround, 0); assert.equal(earlySupport, 0); assert.equal(earlyAssets, 0);
await early.setTier('light'); await earlyReady;
assert.equal(earlyGround, 0); assert.equal(earlySupport, 0); assert.equal(earlyAssets, 0);
assert.equal(early.actors.length, 0); early.dispose();
let wrongSceneAssets = 0;
const wrongScene = createTownTransport({ rows: [validRow], sceneId: '1904', heightAt: () => 0, clear: () => true,
  makeAssembly() { wrongSceneAssets++; throw Error('wrong scene'); } });
await wrongScene.ready(); assert.equal(wrongSceneAssets, 0); wrongScene.dispose();

// Recover only a live visitor blocking the spawn, without hot-loading GLBs,
// re-reading the circuit, retrying fatal sources, or duplicating another row.
{
  let blocked = true, gets = 0, frees = 0, routeChecks = 0;
  const problems = [];
  const town = createTownTransport({ rows: [{ ...validRow, id: 'deferred' }], sceneId: '1835',
    heightAt: () => 0, routeClear() { routeChecks++; return true; }, clear: () => !blocked,
    problems, makeAssembly() { gets++; return { root: new THREE.Group(), pose() {}, dispose() { frees++; } }; } });
  town.update(0, { x: 20, z: 0 });
  await town.ready();
  assert.equal(gets, 1); assert.equal(frees, 1); assert.equal(town.actors.length, 0);
  assert.deepEqual(problems, [], 'live visitor obstruction is a deferred mount, not a failed source');
  const readOnce = routeChecks;
  for (let i = 0; i < 20; i++) { town.ensureNear({ x: 20, z: 0 }); await town.ready(); }
  assert.equal(gets, 1, 'repeated blocked approach must not reacquire a GLB');
  assert.equal(frees, 1); assert.equal(routeChecks, readOnce, 'successful route reading is cached in this generation');
  blocked = false; await town.ready();
  assert.equal(gets, 2); assert.equal(town.actors.length, 1); assert.equal(routeChecks, readOnce);
  const first = town.actors[0]; first.update(.2); first.stop('interaction');
  const journey = first.snapshot();
  await town.setTier('light');
  assert.equal(frees, 2); assert.equal(town.actors.length, 0);
  blocked = true; await town.setTier('full');
  assert.equal(gets, 3); assert.equal(frees, 3); assert.equal(town.actors.length, 0);
  const secondGenerationRead = routeChecks; assert(secondGenerationRead > readOnce);
  for (let i = 0; i < 20; i++) { town.ensureNear({ x: 20, z: 0 }); await town.ready(); }
  assert.equal(gets, 3); assert.equal(routeChecks, secondGenerationRead);
  blocked = false; await town.ready();
  assert.equal(gets, 4); assert.equal(routeChecks, secondGenerationRead);
  assert.equal(town.actors[0].state, 'stopped');
  assert.equal(town.actors[0].snapshot().distance_m, journey.distance_m);
  assert.equal(town.actors[0].snapshot().total_distance_m, journey.total_distance_m);
  assert.deepEqual(town.actors[0].snapshot().wheel_rotation_rad, journey.wheel_rotation_rad);
  town.dispose(); await town.ready();
  assert.equal(gets, 4); assert.equal(frees, 4); assert.equal(town.actors.length, 0);
}
{
  let blockedB = true;
  const counts = { a: 0, b: 0 }, frees = { a: 0, b: 0 };
  const town = createTownTransport({ rows: [{ ...validRow, id: 'a' }, { ...validRow, id: 'b' }], sceneId: '1835',
    heightAt: () => 0, routeClear: () => true, clear: row => row.id !== 'b' || !blockedB,
    makeAssembly(row) { counts[row.id]++; return { root: new THREE.Group(), pose() {}, dispose() { frees[row.id]++; } }; } });
  await town.ready(); const a = town.actors[0];
  for (let i = 0; i < 10; i++) await town.ready();
  assert.deepEqual(counts, { a: 1, b: 1 }); assert.deepEqual(frees, { a: 0, b: 1 });
  assert.equal(town.actors.length, 1); assert.strictEqual(town.actors[0], a);
  blockedB = false; await town.ready();
  assert.deepEqual(counts, { a: 1, b: 2 }); assert.equal(town.actors.length, 2);
  assert.equal(new Set(town.actors.map(actor => actor.id)).size, 2);
  assert.strictEqual(town.actors.find(actor => actor.id === 'a'), a, 'one mounted identity stays the same object');
  town.dispose(); assert.deepEqual(frees, { a: 1, b: 2 });
}
{
  const problems = [], acquisitions = { static: 0, asset: 0, deferred: 0 };
  let staticReads = 0;
  const town = createTownTransport({
    rows: ['static', 'asset', 'deferred'].map(id => ({ ...validRow, id })), sceneId: '1835',
    heightAt: () => 0,
    routeClear(row) { if (row.id === 'static') { staticReads++; return false; } return true; },
    clear: row => row.id !== 'deferred', problems,
    makeAssembly(row) {
      acquisitions[row.id]++;
      if (row.id === 'asset') throw Error('controlled metadata/network refusal');
      return { root: new THREE.Group(), pose() {}, dispose() {} };
    },
  });
  await town.ready(); const initialStaticReads = staticReads;
  for (let i = 0; i < 20; i++) { town.ensureNear({ x: 20, z: 0 }); await town.ready(); }
  assert.deepEqual(acquisitions, { static: 0, asset: 1, deferred: 1 });
  assert.equal(staticReads, initialStaticReads, 'a static spawn obstruction must not become a recoverable live one');
  assert.equal(problems.length, 2); assert(problems.some(s => s.includes('initial whole-team footprint')));
  assert(problems.some(s => s.includes('controlled metadata/network refusal')));
  town.dispose(); await town.ready(); assert.equal(town.actors.length, 0);
}
console.log('deferred live spawn: first approach/Light restoration, cached circuit, no GLB thrash/duplicate rows, fatal refusal cache and disposal PASS');

console.log('driven assembly: actual W01 source hierarchy/THREE transforms + lifecycle PASS');

// Actual factory source with controlled asynchronous I/O/portable-human leases.
// These are scheduling/ownership controls, not a substitute for real GLB/world proofs.
const { webcrypto } = await import('node:crypto');
const { resolveHumanIdentity } = await import('../renderers/web/js/human-identity.js');
const { teamSupportAt } = await import('../renderers/web/js/transport-support.js');
const factoryCode = readFileSync(new URL('../renderers/web/js/driven-assembly-loader.js', import.meta.url), 'utf8');
const fixtureBytes = readFileSync(path);
const fixtureHash = [...new Uint8Array(await webcrypto.subtle.digest('SHA-256', fixtureBytes))].map(n => n.toString(16).padStart(2, '0')).join('');
let fixtureNumber = 0;
const deferredAsset = () => { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; };
async function controlledFactory(code, { syncFailure = null, wrongMetadata = false, wrongHash = false } = {}) {
  const io = { vehicle: deferredAsset(), human: deferredAsset(), horse: deferredAsset() };
  const sourceHashesHorse = code.includes('actual horse differs from model/support binding');
  const events = [], stats = { vehicleDisposed: 0, horseDisposed: 0, humanRefs: 0, humanReleases: 0,
    constructed: 0, actorDisposed: 0, adopted: 0, restored: 0, ownership: null };
  const failure = Error('original controlled dependency failure');
  const gltfVehicle = { scene: vehicle.clone(true), animations: [] };
  const walk = new THREE.AnimationClip('fixture_walk', 1, []);
  const gltfHorse = { scene: new THREE.Group(), animations: [walk], parser: { json: { asset: { extras: {
    inplace_walk_source: { contract: { kind: 'IN_PLACE_EXTERNAL_ACTOR_TRAVEL_REQUIRED_ONCE',
      intendedCycleDistanceM: 1.5, rootZInClipM: [0, 0], serializedClipDurationSeconds: 1 } } } } } } };
  const row = { ...validRow, id: 'resource-control', driver_instance: { person_id: 'control_person' },
    driver_asset: 'control_asset', vehicle_file: 'wagon.glb', driver_seat_node_m: [0, 1.58, .65],
    horse_offset_m: [0, 0, 5], team_half_spacing_m: .63,
    driver_binding: { scene: '1835', asset_id: 'control_asset', vehicle_file: 'wagon.glb', root_offset_m: [0, 0, 0],
      vehicle_glb_sha256: wrongHash ? '0'.repeat(64) : fixtureHash, vehicle_sidecar_sha256: 'source-sidecar-binding' } };
  const human = { parser: { json: { scenes: [{ extras: {
    chicago4d_human: { person_reference_scene: wrongMetadata ? '1904' : '1835', person_reference_id: 'control_person' },
    driver_study_json: JSON.stringify({ scene: '1835', person_reference_id: 'control_person',
      vehicle_sidecar_sha256: row.driver_binding.vehicle_sidecar_sha256, vehicle_glb_sha256: fixtureHash }) } }] } } };
  let humanReady = false;
  const assets = {
    acquire() {
      events.push('human-start'); if (syncFailure === 'human') throw failure;
      stats.humanRefs++;
      if (humanReady) return Promise.resolve(human);
      return io.human.promise.then(value => { humanReady = true; return value; }, error => { stats.humanRefs--; throw error; });
    },
    release() { stats.humanRefs--; stats.humanReleases++; assert(stats.humanRefs >= 0); },
  };
  class FixtureActor {
    constructor({ instance, identity }) {
      stats.constructed++; this.instance = instance; this.identity = identity; this.personId = instance.person_id;
      this.id = instance.id; this.root = new THREE.Group(); this.proxy = new THREE.Mesh(new THREE.BoxGeometry(.6, 1, .45), new THREE.MeshBasicMaterial());
      this.root.add(this.proxy); this.disposed = false; this.owned = false;
    }
    async setLod() {
      await assets.acquire(); this.owned = true;
      const scene = new THREE.Group(); scene.add(new THREE.Mesh(new THREE.BoxGeometry(.4, 1.2, .3), new THREE.MeshBasicMaterial()));
      this.root.add(scene); this.body = { scene, mixer: new THREE.AnimationMixer(scene), meshes: [], clips: new Map([['sit_drive', {}]]) };
      return this.body;
    }
    play(name) { return name === 'sit_drive'; }
    dispose() {
      if (this.disposed) return; this.disposed = true; stats.actorDisposed++;
      if (this.owned) { assets.release(); this.owned = false; } this.root.removeFromParent();
    }
  }
  class FixtureLoader {
    loadAsync() { events.push('horse-start'); if (syncFailure === 'horse') throw failure; return io.horse.promise; }
    parseAsync(bytes, resourcePath) { const isHorse = resourcePath.includes('/horse/'); events.push(isHorse ? 'horse-parse' : 'vehicle-parse'); return Promise.resolve(isHorse ? gltfHorse : gltfVehicle); }
  }
  const dependencyKey = `__controlledDriverFactory${fixtureNumber++}`;
  globalThis[dependencyKey] = { THREE, GLTFLoader: FixtureLoader, cloneSkinned: root => root.clone(true),
    HumanActor: FixtureActor, resolveHumanIdentity, createDrivenAssembly, createDriverLife: () => null, clothHuman: () => [],
    fitHorseSupport: () => ({ height_m: 0, normal_local_xyz: [0, 1, 0] }), crypto: webcrypto,
    disposeLoadedAsset(value) {
      if (value === gltfVehicle) stats.vehicleDisposed++;
      else if (value === gltfHorse) stats.horseDisposed++;
      else assert.fail('unexpected disposable asset');
    },
    fetch(url) { const kind = String(url).includes('/horse/') ? 'horse' : 'vehicle'; events.push(kind + '-start'); if (syncFailure === kind) throw failure; return io[kind].promise; },
  };
  const injected = `const { THREE, GLTFLoader, cloneSkinned, HumanActor, resolveHumanIdentity, disposeLoadedAsset, createDrivenAssembly, createDriverLife, clothHuman, fitHorseSupport, crypto, fetch } = globalThis[${JSON.stringify(dependencyKey)}];\n`
    + code.replace(/^import .*;\n/gm, '');
  const module = await import('data:text/javascript;base64,' + Buffer.from(injected).toString('base64'));
  delete globalThis[dependencyKey];
  const factory = module.createDrivenAssemblyLoader({ sceneId: '1835', people: [{ id: 'control_person' }],
    humanAssets: assets, heightAt: () => 0, moduleBase: new URL('https://controlled.example/'),
    horseSpec: { file: 'horse/horse.glb', sha256: fixtureHash, stride_m: 1.5, walk_clip: 'fixture_walk', material_variant: 'source_native' },
    makeHitch() { events.push('hitch'); return { root: new THREE.Group(), update: () => ({ valid: true }), dispose() {} }; },
    adoptPerson(instance, actor) {
      stats.adopted++; stats.ownership = actor;
      return () => { stats.restored++; stats.ownership = null; };
    },
  });
  const resolve = name => io[name].resolve((name === 'vehicle' || (name === 'horse' && sourceHashesHorse))
    ? { ok: true, arrayBuffer: async () => fixtureBytes.buffer.slice(fixtureBytes.byteOffset, fixtureBytes.byteOffset + fixtureBytes.byteLength) }
    : name === 'human' ? human : gltfHorse);
  return { factory, row, io, events, stats, failure, resolve, resolveAll() { for (const name of ['vehicle', 'human', 'horse']) resolve(name); } };
}
async function successfulFactorySnapshot(code) {
  const f = await controlledFactory(code), pending = f.factory(f.row); f.resolveAll();
  const assembly = await pending;
  const tree = []; assembly.root.traverse(n => tree.push({ name: n.name, position: n.position.toArray(), quaternion: n.quaternion.toArray(), scale: n.scale.toArray() }));
  const source = { rootName: assembly.root.name, tree, assemblyState: assembly.snapshot() };
  assembly.dispose(); assembly.dispose();
  assert.equal(f.stats.vehicleDisposed, 1); assert.equal(f.stats.horseDisposed, 1);
  assert.equal(f.stats.humanRefs, 0); assert.equal(f.stats.humanReleases, 2);
  assert.equal(f.stats.actorDisposed, 1); assert.equal(f.stats.adopted, 1); assert.equal(f.stats.restored, 1);
  return source;
}
// ACTUAL-CONCURRENCY-CASES-BEGIN
for (const failedDependency of ['vehicle', 'human', 'horse']) {
  const f = await controlledFactory(factoryCode), pending = f.factory(f.row);
  assert.deepEqual(f.events.slice(0, 3), ['vehicle-start', 'human-start', 'horse-start']);
  let settled = false; pending.then(() => { settled = true; }, () => { settled = true; });
  f.io[failedDependency].reject(f.failure); await new Promise(r => setTimeout(r, 0));
  assert.equal(settled, false, 'a sibling rejection must not abandon unresolved leases');
  assert.equal(f.stats.adopted, 0); assert.equal(f.stats.constructed, 0);
  for (const name of ['vehicle', 'human', 'horse']) if (name !== failedDependency) f.resolve(name);
  await assert.rejects(pending, error => error === f.failure);
  assert.equal(f.stats.humanRefs, 0); assert.equal(f.stats.adopted, 0);
  assert.equal(f.stats.vehicleDisposed, failedDependency === 'vehicle' ? 0 : 1);
  assert.equal(f.stats.horseDisposed, failedDependency === 'horse' ? 0 : 1);
}
for (const syncFailure of ['vehicle', 'human', 'horse']) {
  const f = await controlledFactory(factoryCode, { syncFailure }), pending = f.factory(f.row);
  assert.deepEqual(f.events.slice(0, 3), ['vehicle-start', 'human-start', 'horse-start']);
  f.resolveAll(); await assert.rejects(pending, error => error === f.failure);
  assert.equal(f.stats.humanRefs, 0); assert.equal(f.stats.adopted, 0);
  assert.equal(f.stats.vehicleDisposed, syncFailure === 'vehicle' ? 0 : 1);
  assert.equal(f.stats.horseDisposed, syncFailure === 'horse' ? 0 : 1);
}
for (const flags of [{ wrongMetadata: true }, { wrongHash: true }]) {
  const f = await controlledFactory(factoryCode, flags), pending = f.factory(f.row); f.resolveAll();
  await assert.rejects(pending, /actual exported driver identity|actual vehicle differs/);
  assert.equal(f.stats.humanRefs, 0); assert.equal(f.stats.adopted, 0); assert.equal(f.stats.constructed, 0);
  assert.equal(f.stats.vehicleDisposed, flags.wrongHash ? 0 : 1); assert.equal(f.stats.horseDisposed, 1);
}
const unbound = await controlledFactory(factoryCode);
await assert.rejects(unbound.factory({ ...unbound.row, driver_binding: null }), /exact seated driver/);
assert.deepEqual(unbound.events, []);
const delayed = await controlledFactory(factoryCode), delayedReady = delayed.factory(delayed.row);
delayed.resolve('human'); delayed.resolve('horse'); await new Promise(r => setTimeout(r, 0));
assert.equal(delayed.stats.constructed, 0); assert.equal(delayed.stats.adopted, 0);
delayed.resolve('vehicle'); const delayedAssembly = await delayedReady;
assert.equal(delayed.stats.adopted, 1); delayedAssembly.dispose(); assert.equal(delayed.stats.humanRefs, 0);
const cancel = await controlledFactory(factoryCode); let publishedActors = 0;
const cancelledTown = createTownTransport({ rows: [cancel.row], sceneId: '1835', makeAssembly: cancel.factory,
  heightAt: () => 0, clear: () => true, routeSupport: (row, pose) => teamSupportAt(row, pose, () => 0),
  onActorsChanged: actors => { publishedActors += actors.length; } });
const cancelledReady = cancelledTown.ready(); await until(() => cancel.events.includes('horse-start'));
const cancelLight = cancelledTown.setTier('light'); cancel.resolveAll(); await cancelledReady; await cancelLight;
assert.equal(publishedActors, 0); assert.equal(cancelledTown.actors.length, 0);
assert.equal(cancel.stats.humanRefs, 0); assert.equal(cancel.stats.vehicleDisposed, 1); assert.equal(cancel.stats.horseDisposed, 1);
assert.equal(cancel.stats.ownership, null); cancelledTown.dispose();
await successfulFactorySnapshot(factoryCode);
console.log('driven factory: concurrent start/allSettled late ownership/sync throw/rejection/bindings/delayed adoption/Light cancellation/exactly-once release PASS');

// Actual 1904 directory/identity through the lazy real scene makeAssembly path.
// This reads392 compiled rows, creates no human geometry, and uses no browser.
const { supportsTownTransport } = await import('../renderers/web/js/transport-loop.js');
const sceneBindingSource = readFileSync(new URL('../renderers/web/js/town-transport-scene.js', import.meta.url), 'utf8');
const mainSource = readFileSync(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
const actualScene1904 = JSON.parse(readFileSync(new URL('../data/scenes/1904.json', import.meta.url)));
const actualPeople1904 = JSON.parse(readFileSync(new URL('../data/sidecars/1904/people.json', import.meta.url)));
const actualRoutes = JSON.parse(readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url)));
const actualDriverRow = actualRoutes.rows.find(r => r.scene === '1904');
assert(!actualScene1904.layers.includes('residents') && !actualScene1904.layers.includes('humans'));
assert.equal(actualPeople1904.people.length, 440); assert.equal(actualPeople1904.residents_root, 'data/residents_1904');
assert.equal(actualDriverRow.person_id, 'pa1904_otis_f_r_c1900_hans_johnson');
for (const id of ['1835', '1904', 1835, 1904]) assert(supportsTownTransport(id));
for (const id of ['1812', '1880', '1905', null]) assert(!supportsTownTransport(id));
assert(sceneBindingSource.includes('if (!supportsTownTransport(sceneId)) return null;'), 'Mount shares the same eligibility guard');
assert(mainSource.includes('if (supportsTownTransport(YEAR)) api.people = { open: openSceneDirectoryPerson };'), 'Only eligible scenes receive the native public card adapter');
assert(mainSource.includes("if (draws('residents')) try {"), 'Legacy1835 eager directory/UI layer gates retained');
assert(mainSource.includes("dataBase: layerBase('humans')"), 'No scene-wide human population enabled');
assert(mainSource.includes('getPeople: () => peopleDirectory.load()'), 'Actual mount uses existing lazy compiled catalog promise');
function actualAssemblyCallback(code, catalog = null) {
  const begin = code.indexOf('async makeAssembly(row) {'), end = code.indexOf('\n    onActorsChanged', begin);
  assert(begin >= 0 && end > begin); const method = code.slice(begin, end).trim().replace(/,$/, '').replace('async makeAssembly(row)', 'async function(row)');
  let gets = 0, nativeLoaderCalls = 0;
  const nativeLoader = options => { nativeLoaderCalls++; return async row => resolveHumanIdentity({ ...row.driver_instance, scene: row.scene }, { sceneId: '1904', people: options.people }); };
  const nativeHitch = () => {};
  const make = new Function('modelFor', 'people', 'getPeople', 'makeByHorse', 'createDrivenAssemblyLoader', 'sceneId', 'config', 'humans', 'confidence', 'heightAt', 'supportByHorse', 'makeHitch', 'coarse', 'getAssemblyTools', `return (${method});`)(
    row => row.horse_model, catalog, async () => { gets++; return actualPeople1904; }, new Map(), nativeLoader,
    '1904', actualRoutes, { assets: {} }, null, () => 0, new Map(), nativeHitch, false,
    async () => ({ createDrivenAssemblyLoader: nativeLoader, makeHitch: nativeHitch }));
  return { make, get gets() { return gets; }, get nativeLoaderCalls() { return nativeLoaderCalls; } };
}
const lazy = actualAssemblyCallback(sceneBindingSource);
assert.equal(lazy.gets, 0, 'No directory fetch before ordinary eligible makeAssembly');
const named = await lazy.make(actualDriverRow);
assert.equal(lazy.gets, 1); assert.equal(lazy.nativeLoaderCalls, 1);
assert.equal(named.kind, 'person'); assert.equal(named.personId, actualDriverRow.person_id);
assert.equal(named.person.name, 'Hans Johnson'); assert.equal(named.person.occupation, 'coachman');
const alreadyLoaded = actualAssemblyCallback(sceneBindingSource, actualPeople1904);
assert.equal((await alreadyLoaded.make(actualDriverRow)).personId, actualDriverRow.person_id); assert.equal(alreadyLoaded.gets, 0);
const oldNullDirectory = sceneBindingSource.replace('people: directory.people, profiles:', 'people: people?.people ?? [], profiles:');
assert.notEqual(oldNullDirectory, sceneBindingSource);
await assert.rejects(() => actualAssemblyCallback(oldNullDirectory).make(actualDriverRow), /not in sidecars\/1904\/people.json/, 'Old null-directory failure remains a real named-identity refusal');
await assert.rejects(() => actualAssemblyCallback(sceneBindingSource).make({ ...actualDriverRow, driver_instance: { ...actualDriverRow.driver_instance, person_id: 'no_such_hans' } }), /not in sidecars/, 'No anonymous or invented-person fallback');
// Execute actual shared public opener:1904 card targets Hans in his own building,
// whose native Navigator household reader already uses residents_root.
const openBegin = mainSource.indexOf('async function openSceneDirectoryPerson(id) {');
const openEnd = mainSource.indexOf('\n  async function openPersonCard', openBegin);
assert(openBegin >= 0 && openEnd > openBegin);
const opened = [], cardOpen = new Function('peopleDirectory', 'loaded', 'openBuilding', 'navigatorUi', mainSource.slice(openBegin, openEnd) + '\nreturn openSceneDirectoryPerson;')(
  { load: async () => actualPeople1904 }, { registry: new Map([[named.person.lives_at, {}]]) },
  (id, options) => { opened.push({ id, ...options }); return true; }, { select: () => true });
assert.equal(await cardOpen(named.personId), true);
assert.deepEqual(opened, [{ id: 'otis_house_2033_prairie', person: named.personId }]);
assert(!mainSource.slice(mainSource.indexOf('// 1904 uses its existing scene-aware'), mainSource.indexOf("// …and the town's FIRMS")).includes('state:'), 'Adapter never synthesizes a card-open state');
console.log('1904 actual392-person catalog: lazy eligible namedHans identity, native scene-aware card/Find path, no human-layer population or anonymous fallback PASS');
// The real native person renderer exposes Find only through the supplied public
// action; Back/card state stays owned by the existing Navigator.
const { renderPersonCard, personModel } = await import('../renderers/web/js/person-card.js');
class CardNode {
  constructor(tag) { this.tag = tag; this.children = []; this.dataset = {}; this.events = {}; }
  append(...nodes) { this.children.push(...nodes); } prepend(...nodes) { this.children.unshift(...nodes); }
  setAttribute() {} addEventListener(name, fn) { this.events[name] = fn; }
}
const cardDoc = { createElement: tag => new CardNode(tag), createTextNode: text => ({ text }) };
const foundPeople = [], cardModel = personModel({ row: named.person, sceneYear: 1904 });
const nativeCard = renderPersonCard(cardDoc, cardModel, { onFind: id => foundPeople.push(id) });
const findButton = nativeCard.children.find(n => n.dataset?.personFind);
assert(findButton, 'Actual native card renders the optional public Find action');
findButton.events.click(); assert.deepEqual(foundPeople, [actualDriverRow.person_id]);
assert(!renderPersonCard(cardDoc, cardModel).children.some(n => n.dataset?.personFind), 'Nontransport/default cards gain no action');
assert(mainSource.includes("findPerson: supportsTownTransport(YEAR) && !draws('residents')"), 'NativeFind is limited to eligible nonlegacy scene');
assert(mainSource.includes("? (id) => findSceneDirectoryPerson(id) : null"), 'Find reaches existing actual live driver-anchor travel path');
console.log('native1904 card Find forwards exactHans identity; default card/Back remains unchanged PASS');

const findStart = mainSource.indexOf('async function findSceneDirectoryPerson(id) {');
const findEnd = mainSource.indexOf('\n  async function openPersonCard', findStart);
const targets = [], findNativePerson = new Function('peopleDirectory', 'loaded', 'api', 'goToTarget', mainSource.slice(findStart, findEnd) + '\nreturn findSceneDirectoryPerson;')(
  { load: async () => actualPeople1904 }, { registry: new Map([[named.person.lives_at, {}]]) },
  { townTransport: { driverAnchorForPerson: id => id === named.personId ? { actor: 'actual named driver' } : null } },
  target => { targets.push(target); return true; });
assert.equal(await findNativePerson(named.personId), true);
assert.deepEqual(targets, [{ kind: 'person', id: named.personId }]);
// Execute the exact1835 branch with the existing visible-tab fallback guard.
const sharedBegin = mainSource.indexOf('async function openPersonCard(id) {'), sharedEnd = mainSource.indexOf('\n  // T-2618:', sharedBegin);
const legacyCalls = [], sharedOpen = new Function('api', 'document', 'hud', 'openSceneDirectoryPerson', mainSource.slice(sharedBegin, sharedEnd) + '\nreturn openPersonCard;')(
 { people: { open: id => { legacyCalls.push(['open', id]); return true; } } },
 { querySelector: () => ({ hidden: false }) }, { setPanel: on => legacyCalls.push(['panel', on]), selectTab: tab => legacyCalls.push(['tab', tab]) }, () => { throw Error('visible1835 branch must not change'); });
assert.equal(await sharedOpen('rc_bardwell_otis'), true);
assert.deepEqual(legacyCalls, [['panel', true], ['tab', 'people'], ['open', 'rc_bardwell_otis']]);
console.log('actual nativeFind keeps live Hans actor target and visible1835 legacy panel/tab/open sequence PASS');

// Original Navigator legacy timing: the public result is true while the actual
// household/joins request is still unresolved; opening proceeds asynchronously.
let legacyFinish, legacyStarted = false;
const unresolvedLegacyCard = new Promise(resolve => { legacyFinish = resolve; });
const immediateLegacyOpen = new Function('api', 'document', 'hud', 'openSceneDirectoryPerson', mainSource.slice(sharedBegin, sharedEnd) + '\nreturn openPersonCard;')(
 { people: { open() { legacyStarted = true; return unresolvedLegacyCard; } } },
 { querySelector: () => ({ hidden: false }) }, { setPanel() {}, selectTab() {} }, () => { throw Error('legacy fallback changed'); });
const legacyPublicResult = immediateLegacyOpen('rc_bardwell_otis');
assert.equal(legacyStarted, true);
assert.equal(await Promise.race([legacyPublicResult, Promise.resolve('unresolved-legacy-request')]), true, 'Legacy Navigator returns true without waiting for card household/joins');
legacyFinish(true);
console.log('original1835 Navigator immediate return preserved while household promise remains unresolved PASS');

// Eligible preparation overlaps only JavaScript imports, never a GLB/model lease.
// The actual factory still starts only after the complete ordinary static proof.
{
  let warmed = 0, models = 0, reads = 0;
  const modules = deferredAsset();
  const town = createTownTransport({ rows: [validRow], sceneId: '1835', detail: 'light',
    heightAt() { reads++; return 0; }, clear: () => true,
    prepareAssembly() { warmed++; return modules.promise; },
    makeAssembly() { models++; throw Error('cancelled generation must not acquire'); } });
  assert.throws(() => createTownTransport({ rows: [], sceneId: '1835', heightAt: () => 0,
    clear: () => true, makeAssembly() {}, prepareAssembly: 1 }), /preparation callback/);
  await town.ready(); assert.equal(warmed, 0); assert.equal(models, 0);
  town.update(0, { x: 20, z: 0 }, { paused: true }); // welcome remains held
  await town.setTier('full'); assert.equal(warmed, 0);
  assert.equal(town.ensureNear({ x: 10000, z: 10000 }, true), false);
  assert.equal(town.ensureNear({ x: 20, z: 0 }, false), false); assert.equal(warmed, 0);
  const pending = town.ready(); assert.equal(warmed, 1); assert.equal(reads, 0); assert.equal(models, 0);
  await town.setTier('light'); await pending;
  assert.equal(reads, 0); assert.equal(models, 0); assert.equal(town.actors.length, 0);
  modules.resolve(['modules only']); await modules.promise; await Promise.resolve();
  assert.equal(models, 0); assert.equal(town.actors.length, 0); town.dispose();
}
{
  const modules = deferredAsset(); let warmed = 0, makes = 0, models = 0, staticReads = 0;
  const town = createTownTransport({ rows: [validRow], sceneId: '1835', heightAt: () => 0,
    clear: () => true, routeClear() { staticReads++; return true; },
    prepareAssembly() { warmed++; return modules.promise; },
    async makeAssembly() {
      makes++; assert(staticReads >= 505, 'entire20m circle must pass before actual factory');
      await modules.promise; models++;
      return { root: new THREE.Group(), pose() {}, dispose() {} };
    } });
  const pending = town.ready(); assert.equal(warmed, 1); assert.equal(makes, 0); assert.equal(models, 0);
  await until(() => makes === 1); assert.equal(models, 0);
  for (let i = 0; i < 5; i++) town.ensureNear({ x: 20, z: 0 });
  assert.equal(warmed, 1); assert.equal(makes, 1);
  modules.resolve(['same cached modules']); await pending;
  assert.equal(models, 1); assert.equal(town.actors.length, 1); town.dispose();
}
{
  const failure = Error('controlled module import refusal'), problems = [], unhandled = [];
  const onUnhandled = error => unhandled.push(error); process.on('unhandledRejection', onUnhandled);
  let warmed = 0, makes = 0;
  try {
    const rejected = Promise.reject(failure);
    const town = createTownTransport({ rows: [validRow], sceneId: '1835', heightAt: () => 0,
      clear: () => true, problems, prepareAssembly() { warmed++; return rejected; },
      async makeAssembly() { makes++; await rejected; throw Error('must not reach models'); } });
    await town.ready(); await new Promise(resolve => setImmediate(resolve));
    assert.equal(warmed, 1); assert.equal(makes, 1, 'actual factory remains authoritative after import warmup refusal');
    assert.equal(town.actors.length, 0); assert(problems.some(p => p.includes(failure.message)));
    assert.deepEqual(unhandled, []); town.dispose();
  } finally { process.removeListener('unhandledRejection', onUnhandled); }
}
{
  let warmed = 0, models = 0;
  const problems = [], town = createTownTransport({ rows: [validRow], sceneId: '1835', heightAt: () => 0,
    clear: () => true, routeClear: () => false, problems,
    prepareAssembly() { warmed++; return Promise.resolve(['onlyJS']); },
    makeAssembly() { models++; throw Error('static proof failure must not acquire'); } });
  await town.ready(); assert.equal(warmed, 1); assert.equal(models, 0); assert.equal(town.actors.length, 0);
  assert.equal(problems.length, 1); town.dispose();
}
// Execute the ACTUAL scene import/tool-cache closures with controlled module I/O.
// Resolving the warm modules must not construct loaders/factories or touch assets.
{
  const begin = sceneBindingSource.indexOf('let assemblyModules = null'), end = sceneBindingSource.indexOf('  const makeByHorse', begin);
  assert(begin >= 0 && end > begin);
  const events = [], pendingModules = deferredAsset(); let loaders = 0, hitchFactories = 0;
  class Loader { constructor() { loaders++; } loadAsync() { events.push('GLB'); throw Error('no GLB before actual makeHitch'); } }
  const modules = {
    './driven-assembly-loader.js': { createDrivenAssemblyLoader() {} },
    './draft-hitch.js': { createDraftHitchFactory() { hitchFactories++; return () => {}; } },
    'three/addons/loaders/GLTFLoader.js': { GLTFLoader: Loader },
  };
  const source = sceneBindingSource.slice(begin, end).replace(/\bimport\(/g, 'loadModule(');
  const caches = new Function('loadModule', 'confidence', 'json', 'moduleBase', source + '\nreturn { prepareAssemblyModules, getAssemblyTools };')(
    path => { events.push(path); return pendingModules.promise.then(() => modules[path]); }, null,
    () => { events.push('JSON'); throw Error('directory/binding JSON must remain lazy'); }, new URL('https://controlled.example/'));
  const first = caches.prepareAssemblyModules(), second = caches.prepareAssemblyModules();
  assert.strictEqual(first, second); assert.equal(events.length, 3);
  assert(events.every(path => path.endsWith('.js'))); assert.equal(loaders, 0); assert.equal(hitchFactories, 0);
  pendingModules.resolve(); await first;
  assert.equal(loaders, 0); assert.equal(hitchFactories, 0); assert.equal(events.length, 3);
  const tools = caches.getAssemblyTools(), sameTools = caches.getAssemblyTools(); assert.strictEqual(tools, sameTools);
  const readyTools = await tools; assert.equal(typeof readyTools.createDrivenAssemblyLoader, 'function');
  assert.equal(loaders, 1); assert.equal(hitchFactories, 1); assert.equal(events.length, 3);
}
console.log('eligibleJSprewarm: zeroGLBs/leases beforecomplete route, Light/remote/welcome/cancel/refusal/cache ownership PASS');
// One cached JS request can finish across Light->Full generations; only the
// new complete preflight may acquire an assembly, which remains singly owned.
{
  const modules = deferredAsset(); let warmed = 0, makes = 0, models = 0, frees = 0;
  const town = createTownTransport({ rows: [validRow], sceneId: '1835', heightAt: () => 0,
    clear: () => true, prepareAssembly() { warmed++; return modules.promise; },
    async makeAssembly() { makes++; await modules.promise; models++;
      return { root: new THREE.Group(), pose() {}, dispose() { frees++; } }; } });
  town.update(0, { x: 20, z: 0 });
  const oldReady = town.ready(); assert.equal(warmed, 1);
  const light = town.setTier('light'), latest = town.setTier('full');
  await until(() => makes === 1); await oldReady; await light;
  assert.equal(warmed, 2); assert.equal(makes, 1); assert.equal(models, 0);
  modules.resolve(); await latest;
  assert.equal(models, 1); assert.equal(town.actors.length, 1);
  town.dispose(); town.dispose(); assert.equal(frees, 1);
}
{
  let warmed = 0, models = 0;
  const town = createTownTransport({ rows: [validRow], sceneId: '1904', heightAt: () => 0,
    clear: () => true, prepareAssembly() { warmed++; }, makeAssembly() { models++; } });
  await town.ready(); assert.equal(warmed, 0); assert.equal(models, 0); town.dispose();
}
console.log('module-warm oldgeneration cancels beforemodels/newgeneration mounts once; wrongscene remains cold PASS');

// The real eligible scene preparation fans out to optional card metadata only.
// It must not acquire a model, wait for the card, or replace the authoritative opener.
{
  const begin = sceneBindingSource.indexOf('    prepareAssembly(row) {');
  const end = sceneBindingSource.indexOf('    clear:', begin);
  assert(begin >= 0 && end > begin);
  const method = sceneBindingSource.slice(begin, end).trim().replace(/,$/, '').replace('prepareAssembly(row)', 'function(row)');
  const modules = deferredAsset(), card = deferredAsset(), calls = [];
  const prepare = new Function('prepareAssemblyModules', 'preparePersonCard', `return (${method});`)(
    () => { calls.push('modules'); return modules.promise; }, id => { calls.push(id); return card.promise; });
  assert.strictEqual(prepare(actualDriverRow), modules.promise);
  assert.deepEqual(calls, ['modules', actualDriverRow.person_id]);
  modules.resolve(); await modules.promise; // An unresolved card cannot stall the actual factory.
  card.reject(Error('optional card is offline')); await new Promise(resolve => setTimeout(resolve, 0));
  for (const warm of [null, () => { throw Error('card synchronous refusal'); }, () => Promise.reject(Error('card async refusal'))]) {
    const callback = new Function('prepareAssemblyModules', 'preparePersonCard', `return (${method});`)(() => modules.promise, warm);
    assert.strictEqual(callback(actualDriverRow), modules.promise);
  }
  await new Promise(resolve => setTimeout(resolve, 0));
  let models = 0; calls.length = 0;
  const town = createTownTransport({ rows: [validRow], sceneId: '1835', detail: 'light', heightAt: () => 0,
    clear: () => true, prepareAssembly: prepare, makeAssembly() { models++; } });
  await town.ready(); await town.setTier('balanced');
  assert.equal(town.ensureNear({ x: 10000, z: 10000 }, true), false);
  assert.equal(town.ensureNear({ x: 20, z: 0 }, false), false);
  assert.equal(calls.length, 0); assert.equal(models, 0); town.dispose();
}
// Execute the actual main card warmup with the actual392-row catalog. Test its no-device
// fallback and code-only Navigator port; no HUD, popup-open, figure loader or renderer.
{
  const begin = mainSource.indexOf('  async function prepareSceneDirectoryPerson(id) {');
  const end = mainSource.indexOf('  function ensureResidentCitations()', begin);
  assert(begin >= 0 && end > begin);
  const code = mainSource.slice(begin, end).replace(/\bimport\(/g, 'loadModule(');
  const events = [], pending = deferredAsset();
  const warm = (year, residents, failing = false, navigatorUi = null) => new Function('supportsTownTransport', 'YEAR', 'draws', 'loadModule',
    'ensureInspect', 'ensureReaderText', 'ensurePictures', 'peopleDirectory', 'householdRecord', 'ensureResidentCitations', 'navigatorUi',
    code + '\nreturn prepareSceneDirectoryPerson;')(supportsTownTransport, year, () => residents,
    path => { events.push(path); return pending.promise; },
    () => { events.push('summary'); return failing ? Promise.reject(Error('summary offline')) : pending.promise; },
    () => { events.push('reader'); return pending.promise; }, () => { events.push('pictures'); return pending.promise; },
    { load() { events.push('directory'); return Promise.resolve(actualPeople1904); } },
    file => { events.push(['household', file]); return failing ? Promise.reject(Error('household offline')) : pending.promise; },
    () => { events.push('citations'); return pending.promise; }, navigatorUi);
  await warm('1835', true)(actualDriverRow.person_id);
  await warm('1812', false)(actualDriverRow.person_id); assert.equal(events.length, 0);
  const waiting = warm('1904', false)(actualDriverRow.person_id);
  assert.deepEqual(events, ['./apps/inspect-view.js', 'summary', 'reader', 'pictures', 'directory']);
  await Promise.resolve();
  const actualPerson = actualPeople1904.people.find(row => row.id === actualDriverRow.person_id);
  assert.deepEqual(events.slice(-2), [['household', actualPerson.file], 'citations']);
  pending.resolve(); await waiting;
  events.length = 0;
  await warm('1904', false, false, { preload(id) { events.push(['preload', id]); return Promise.resolve(true); } })(actualDriverRow.person_id);
  assert.deepEqual(events[0], ['preload', 'inspect'], 'eligible driver prepares the exact Navigator app code');
  assert(!events.includes('./apps/inspect-view.js'), 'a registered preload avoids a separate import on the opening path');
  assert(events.includes('summary') && events.includes('reader') && events.includes('pictures'));
  assert(events.some(event => Array.isArray(event) && event[0] === 'household' && event[1] === actualPerson.file));
  await warm('1904', false, true)(actualDriverRow.person_id); // Optional failures remain handled.
  assert(mainSource.includes("preparePersonCard: !draws('residents') ? prepareSceneDirectoryPerson : null"));
  assert(mainSource.includes('residentCitations: () => ensureResidentCitations(),'));
}
// The actual citation cache is shared by warmup and the real Inspector action, including retry.
{
  const begin = mainSource.indexOf('  function ensureResidentCitations() {');
  const end = mainSource.indexOf('  // One public person-card route', begin);
  const code = mainSource.slice(begin, end);
  let requests = 0, fail = false;
  const ensure = new Function('fetch', 'URL', 'loaded', 'YEAR', 'resolveBases',
    'let residentCitations = null;\n' + code + '\nreturn ensureResidentCitations;')(
    async url => { requests++; assert.equal(url.href, 'https://metadata.example/sidecars/1904/residents_sources.json');
      if (fail) throw Error('offline'); return { ok: true, json: async () => ({ citations: { real: 'citation' } }) }; },
    URL, { scene: { id: '1904' } }, '1904', () => ({ dataBase: 'https://metadata.example/' }));
  const first = ensure(), second = ensure(); assert.strictEqual(first, second);
  assert.deepEqual(await first, { real: 'citation' }); assert.equal(requests, 1);
  assert.strictEqual(ensure(), first); assert.equal(requests, 1);
  fail = true;
  // A separate cold cache proves the original retry-after-rejection contract.
  const retry = new Function('fetch', 'URL', 'loaded', 'YEAR', 'resolveBases',
    'let residentCitations = null;\n' + code + '\nreturn ensureResidentCitations;')(
    async () => { requests++; if (fail) throw Error('offline'); return { ok: true, json: async () => ({ citations: {} }) }; },
    URL, { scene: { id: '1904' } }, '1904', () => ({ dataBase: 'https://metadata.example/' }));
  await assert.rejects(retry(), /offline/); fail = false; assert.deepEqual(await retry(), {});
}
console.log('eligible named-card warm: actual directory household/citation cache, no UI/model dependency, guarded optional failures PASS');

// A qualified seated look consumes one visual interval even when its vehicle is
// stopped. It never consumes the bounded vehicle substeps as a second clock.
{
  let phase = 0, legacyUpdates = 0, freed = 0, mounts = 0;
  const visualCalls = [];
  const town = createTownTransport({ rows: [{ ...validRow, id: 'visual-driver' }], sceneId: '1835',
    heightAt: () => 0, clear: () => true,
    makeAssembly(row) {
      mounts++;
      phase = row.initial_assembly_state?.driver?.time_s ?? 0;
      const scene = vehicle.clone(true);
      return createDrivenAssembly({ vehicle: scene,
        driver: { root: new THREE.Group(), update() { legacyUpdates++; },
          updateVisual(dt) { phase += dt; visualCalls.push(dt); },
          snapshot() { return { time_s: phase }; } },
        horse: { root: new THREE.Group(), advance() {}, stop() {} },
        driverSeat_m: [0, 1.58, .65], horseOffset_m: [0, 0, 5], disposeVehicle() { freed++; } });
    } });
  const near = { x: 20, z: 0 };
  await town.ready();
  town.update(.2, near, { visualDt: .7 });
  assert.equal(phase, 0, 'first actual visual frame begins at the restored pose');
  town.update(.2, near, { visualDt: .7 });
  assert.equal(phase, .7);
  assert.equal(legacyUpdates, 0, 'vehicle substeps cannot double-advance the looking clip');
  const moving = town.actors[0]; moving.stop();
  const stopped = moving.snapshot(), stoppedRoot = town.roots[0].matrixWorld.toArray();
  town.update(.25, near, { visualDt: 3 });
  assert.equal(phase, 3.7, 'driver can look while the vehicle remains stopped');
  assert.equal(moving.snapshot().distance_m, stopped.distance_m);
  assert.deepEqual(moving.snapshot().wheel_rotation_rad, stopped.wheel_rotation_rad);
  assert.deepEqual(town.roots[0].matrixWorld.toArray(), stoppedRoot);
  for (const hold of [{ paused: true }, { reducedMotion: true }, { hidden: true }]) {
    const saved = phase;
    town.update(.25, near, { ...hold, visualDt: 8 });
    assert.equal(phase, saved);
    town.update(.25, near, { visualDt: 8 });
    assert.equal(phase, saved, 'first frame after each hold discards held elapsed time');
    town.update(.25, near, { visualDt: .25 });
    assert.equal(phase, saved + .25);
  }
  const beforeRange = phase;
  town.update(.25, { x: 1000, z: 1000 }, { visualDt: 8 });
  town.update(.25, near, { visualDt: 8 });
  assert.equal(phase, beforeRange, 'out-of-range/first return frame is frozen');
  town.update(.25, near, { visualDt: .5 });
  const beforeLight = phase;
  await town.setTier('light');
  assert.equal(freed, 1); assert.equal(town.actors.length, 0);
  await town.setTier('full');
  assert.equal(mounts, 2); assert.equal(phase, beforeLight);
  assert.equal(town.actors[0].state, 'stopped');
  assert.deepEqual(town.actors[0].snapshot().wheel_rotation_rad, stopped.wheel_rotation_rad);
  town.update(.25, near, { visualDt: .125 });
  assert.equal(phase, beforeLight + .125, 'Light restoration keeps the driver phase');
  assert(visualCalls.every(dt => Number.isFinite(dt) && dt >= 0));
  town.dispose(); assert.equal(freed, 2);
}
console.log('seated driver visual clock: stop, holds, range, Light restoration and no doubled vehicle time PASS');


// Real createDrivenAssembly adapter: synthetic visibility refreshes must never
// prime an elapsed journey OR its independent visual clock. No copied adapter.
{
  let phase = 0, mounts = 0;
  const calls = [];
  const town = createTownTransport({ rows: [{ ...validRow, id: 'elapsed-adapter-clock' }], sceneId: '1835',
    heightAt: () => 0, clear: () => true,
    makeAssembly(row) {
      mounts++; phase = row.initial_assembly_state?.driver?.time_s ?? 0;
      return createDrivenAssembly({ vehicle: vehicle.clone(true),
        driver: { root: new THREE.Group(),
          updateVisual(dt) { phase += dt; calls.push(dt); },
          snapshot() { return { time_s: phase }; } },
        horse: { root: new THREE.Group(), advance() {}, stop() {} },
        driverSeat_m: [0, 1.58, .65], horseOffset_m: [0, 0, 5], disposeVehicle() {} });
    } });
  const near = { x: 20, z: 0 };
  const frame = (dt, extra = {}) => town.update(dt, near, { elapsedFrame: true, visualDt: dt, ...extra });
  frame(0); await town.ready();
  assert.equal(calls.length, 0, 'Actual town admission replays visibility without calling/priming the driver');
  frame(8); assert.equal(phase, 0); assert.equal(calls.at(-1), 0);
  assert.equal(town.snapshot()[0].total_distance_m, 0);
  frame(.5); assert.equal(phase, .5);
  const moving = town.actors[0]; moving.stop(); const stopped = town.snapshot()[0].total_distance_m;
  const count = calls.length; frame(.5);
  assert.equal(calls.length, count + 1, 'One visual call per actual frame even when stopped');
  assert.equal(phase, 1); assert.equal(town.snapshot()[0].total_distance_m, stopped);
  assert(moving.resume()); frame(8);
  assert.equal(town.snapshot()[0].total_distance_m, stopped, 'Continue rebases journey but keeps the independently active look');
  assert.equal(phase, 9);
  town.update(.5, { x: 1000, z: 1000 }, { elapsedFrame: true, visualDt: .5 });
  const beforeReturn = phase, beforeSynthetic = calls.length;
  frame(0, { motionFrame: false });
  assert.equal(calls.length, beforeSynthetic, 'A near synthetic replay cannot prime the real assembly visual latch');
  frame(8); assert.equal(phase, beforeReturn);
  frame(.125); assert.equal(phase, beforeReturn + .125);
  moving.stop(); const beforeLight = phase;
  await town.setTier('light'); await town.setTier('full');
  assert.equal(mounts, 2); assert.equal(phase, beforeLight);
  const beforeRestoredFrame = calls.length;
  frame(8); assert.equal(phase, beforeLight);
  assert.equal(calls.length, beforeRestoredFrame + 1);
  frame(.125); assert.equal(phase, beforeLight + .125);
  town.dispose();
  console.log('elapsed actual assembly: synthetic admission/range/Light cannot prime visual reset; real stopped frame gets exactly one independent look update PASS');
}

// Cold named-driver rendezvous: actual town/loop/main/Travel/Interact behavior.
// Append to the existing test_driven_assembly.mjs; no new gate declaration.
{
  const { createInteractions } = await import('../renderers/web/js/interact.js');
  const { registerTransportInteraction } = await import('../renderers/web/js/transport-interactions.js');
  const { createTravel } = await import('../renderers/web/js/travel.js');
  const config = JSON.parse(readFileSync(new URL('../data/transport/driven/loops.json', import.meta.url)));
  const main = readFileSync(new URL('../renderers/web/js/main.js', import.meta.url), 'utf8');
  const start = main.indexOf('  function goToTarget(target) {');
  const end = main.indexOf('  /** The future welcome picker', start);
  assert(start >= 0 && end > start);
  const actualGo = main.slice(start, end);
  const pending = () => { let resolve, reject; const promise = new Promise((a, b) => { resolve = a; reject = b; }); return {promise, resolve, reject}; };
  const fixture = (sourceRow, options = {}) => {
    const loads = [], publications = [], problems = [], disposed = [], poses = [], visual = [];
    const rows = options.rows ?? [sourceRow];
    let liveClear = options.liveClear ?? true;
    const town = createTownTransport({ rows, sceneId: options.sceneId ?? sourceRow.scene,
      detail: options.detail ?? 'full', heightAt: options.heightAt ?? (() => 0),
      routeClear: () => true, routeSupport: () => ({ valid: true }),
      clear: () => liveClear, problems,
      makeAssembly(row) {
        const gate = pending(), number = loads.length;
        const assembly = { root: new THREE.Group(), pose(p) { poses.push([number, p]); }, advance() {}, visible() {}, stop() {},
          updateVisual(dt) { visual.push(dt); }, dispose() { disposed.push(number); } };
        const load = { row, assembly, gate }; loads.push(load); return gate.promise;
      },
      onActorsChanged(actors) { publications.push(actors.map(a => ({ id:a.id, personId:a.personId, state:a.state, reason:a.snapshot().reason }))); },
    });
    const anchor = town.driverAnchorForPerson(sourceRow.person_id);
    const camera = anchor ? { x:anchor.at[0], z:-anchor.at[1] } : { x:0, z:0 };
    town.update(0, camera); // Existing lastUpdate path, not a fake source mutation.
    const load = async number => { await until(() => loads.length > number); return loads[number]; };
    return {town, loads, publications, problems, disposed, poses, visual, camera,
      setClear(value) { liveClear = value; }, load,
    };
  };
  const settle = async (f, loadNumber = 0) => {
    const ready = f.town.ready(), load = await f.load(loadNumber);
    load.gate.resolve(load.assembly); await ready; return f.town.actors[0];
  };
  const makeGo = (town, travel, options = {}) => Function('api','jauntRuntime','travel','router','hud','destinations',
    'openBusiness','openBuilding','supportsTownTransport','YEAR','draws','openPersonCard', actualGo + '\nreturn goToTarget;')(
    { townTransport:town, humans:{ external:() => null } }, null, travel,
    { blockedAt:options.blockedAt ?? (() => false) }, { say(){}, setPanel(){}, selectTab(){} },
    { resolve:options.resolve ?? (() => null), byId:() => null }, () => {}, () => {}, () => true, '1835', () => true, () => {});
  const target = row => ({kind:'person', id:row.person_id, label:row.name});
  const assertStopped = (actor, row) => {
    assert.equal(actor.id, row.id); assert.equal(actor.personId, row.person_id);
    assert.equal(actor.state, 'stopped'); assert.equal(actor.snapshot().reason, 'approach');
  };

  // Both actual configured identities: no load at request, stop before publication,
  // no later automatic resume, and no change to the route/seat side-stand owner.
  for (const row of config.rows) {
    const f = fixture(row), original = JSON.stringify(row), visits = [];
    const cold = f.town.driverAnchorForPerson(row.person_id);
    const go = makeGo(f.town, { go(destination, callbacks) { visits.push({destination, callbacks}); return true; } });
    assert.equal(go(target(row)), true); assert.equal(f.loads.length, 0); assert.equal(f.town.actors.length, 0);
    assert.equal(visits[0].destination.local_e, cold.at[0] + Math.cos(cold.yaw_rad) * 4);
    assert.equal(visits[0].destination.local_n, cold.at[1] + Math.sin(cold.yaw_rad) * 4);
    assert.equal(JSON.stringify(row), original);
    const actor = await settle(f); assertStopped(actor, row);
    assert.deepEqual(f.publications.at(-1), [{id:row.id,personId:row.person_id,state:'stopped',reason:'approach'}]);
    const saved = actor.snapshot();
    for (let i=0;i<8;i++) f.town.update(.25, f.camera, {visualDt:.25});
    assert.equal(actor.snapshot().total_distance_m, saved.total_distance_m);
    assert.deepEqual(actor.snapshot().wheel_rotation_rad, saved.wheel_rotation_rad);
    visits[0].callbacks.onStop({reason:'input'}); assertStopped(actor,row);
    f.town.dispose(); assert.equal(f.disposed.length,1);
  }

  const row = config.rows.find(r => r.scene === '1835');
  // Cancellation is observable through the subsequently admitted actor state.
  {
    const f = fixture(row); const request = f.town.requestDriverApproach(row.person_id);
    assert(request); request.cancel(); request.cancel();
    const actor = await settle(f); assert.equal(actor.state,'moving','Canceled intent is idempotent');
    f.town.dispose();
  }
  for (const outcome of ['false','throw']) {
    const f=fixture(row); const go=makeGo(f.town,{go(){if(outcome==='throw')throw Error('planned travel refusal');return false;}});
    if(outcome==='throw')assert.throws(()=>go(target(row)),/planned travel refusal/);else assert.equal(go(target(row)),false);
    const actor=await settle(f);assert.equal(actor.state,'moving');f.town.dispose();
  }
  // Actual Travel onStop wiring, including the real manual-input branch.
  for (const reason of ['input','button','unreachable','replaced']) {
    const f=fixture(row), walker={state:{e:0,n:0,yaw:0,pitch:0,altitude:0,flying:false,speed:0,bob:0},resettle(){}};
    const intent={flying:false,moving:false,yawDelta:0,pitchDelta:0};
    const travel=createTravel({walker,intent,router:{plan:()=>reason==='unreachable'?null:{points:[[1,1],[2,2]]}},hud:{},settings:{}});
    travel.setMode('walk');const go=makeGo(f.town,travel);
    assert.equal(go(target(row)),reason!=='unreachable');
    if(reason==='input'){intent.moving=true;travel.update(.1,intent);}else if(reason==='button')travel.stop('button');
    else if(reason==='replaced'){assert(travel.go({kind:'intersection',local_e:3,local_n:4}));travel.stop('button');}
    const actor=await settle(f);assert.equal(actor.state,'moving');f.town.dispose();
  }
  // Native instant arrival retains rendezvous intent; the real Move Stop callback
  // cancels it even though the instant Travel controller is already idle.
  for(const cancelAfterInstantArrival of [false,true]){
    const f=fixture(row), visits=[], walker={state:{e:0,n:0,flying:false},resettle(){}};
    const travel=createTravel({walker,intent:{flying:false},settings:{},teleport:p=>visits.push(p),setFly(){}});
    assert.equal(makeGo(f.town,travel)(target(row)),true);assert.equal(visits.length,1);
    if(cancelAfterInstantArrival){
      const match=main.match(/onTravelStop: \(\) => \{ ([^\n]+) \},/);assert(match,'Actual Move Stop callback missing');
      Function('api','travel',match[1])({townTransport:f.town},travel);
    }
    const actor=await settle(f);assert.equal(actor.state,cancelAfterInstantArrival?'moving':'stopped');f.town.dispose();
  }
  // A second real Find installs its new token before native Travel replaces the
  // old ride; the old onStop closure must not remove that new rendezvous.
  {
    const f=fixture(row),walker={state:{e:0,n:0,yaw:0,pitch:0,altitude:0,flying:false,speed:0,bob:0},resettle(){}};
    const travel=createTravel({walker,intent:{flying:false},settings:{},router:{plan:()=>({points:[[1,1],[2,2]]})}});
    travel.setMode('walk');const go=makeGo(f.town,travel);assert(go(target(row)));assert(go(target(row)));
    assertStopped(await settle(f),row);travel.stop('button');assertStopped(f.town.actors[0],row);f.town.dispose();
  }
  // Actual fatal-row refusal is transactional: it cannot replace a still-valid
  // cold Find or its real Travel ride. The older actor must stop after load.
  {
    const failedRow=structuredClone(row);failedRow.id='fixture-terminal-row';failedRow.person_id='fixture-terminal-person';
    failedRow.name='Fixture terminal driver';failedRow.driver_instance.person_id=failedRow.person_id;
    const f=fixture(row,{rows:[failedRow,row]});const loading=f.town.ready(),bad=await f.load(0);
    bad.gate.reject(Error('planned terminal row refusal'));const oldLoad=await f.load(1);
    const walker={state:{e:0,n:0,yaw:0,pitch:0,altitude:0,flying:false,speed:0,bob:0},resettle(){}};
    const travel=createTravel({walker,intent:{flying:false},settings:{},router:{plan:()=>({points:[[1,1],[2,2]]})}});
    travel.setMode('walk');const go=makeGo(f.town,travel);assert(go(target(row)));
    const oldRide=travel.state,oldRoute=travel.routeAhead();assert.equal(go(target(failedRow)),false);
    assert.equal(travel.state.phase,oldRide.phase);assert.equal(travel.state.dest,oldRide.dest);assert.deepEqual(travel.routeAhead(),oldRoute);
    oldLoad.gate.resolve(oldLoad.assembly);await loading;assertStopped(f.town.driverForPerson(row.person_id),row);
    travel.stop('button');assertStopped(f.town.driverForPerson(row.person_id),row);f.town.dispose();
  }

  // The old handle cannot cancel a newer request for the same identity.
  {
    const f=fixture(row), old=f.town.requestDriverApproach(row.person_id);
    const current=f.town.requestDriverApproach(row.person_id);old.cancel();
    const actor=await settle(f);assertStopped(actor,row);current.cancel();assertStopped(actor,row);
    const interactions=createInteractions(), handle=registerTransportInteraction(interactions,actor);
    f.setClear(false);assert.equal(handle.thing.actions.stopped[0].id,'give-room');
    assert.equal(interactions.act(handle.thing.id,'continue').ok,false);assert.equal(actor.state,'stopped');
    f.setClear(true);assert.equal(interactions.act(handle.thing.id,'continue').ok,true);interactions.update(0);
    assert.equal(actor.state,'moving');f.town.update(.1,f.camera);assert.equal(actor.state,'moving');
    assert.equal(interactions.act(handle.thing.id,'stop').ok,true);interactions.update(0);assert.equal(actor.state,'stopped');
    current.cancel();assert.equal(actor.state,'stopped');handle.dispose();f.town.dispose();
  }
  // A namespaced synthetic second metadata row exercises map-key isolation only;
  // no assertion here qualifies that fixture identity/asset for a historical scene.
  {
    const other=structuredClone(row);other.id='fixture-other-route';other.person_id='fixture-other-person';
    other.driver_instance.person_id=other.person_id;
    const f=fixture(row,{rows:[row,other]});const first=f.town.requestDriverApproach(row.person_id);
    f.town.requestDriverApproach(other.person_id);first.cancel();
    const loading=f.town.ready(), a=await f.load(0);a.gate.resolve(a.assembly);
    const b=await f.load(1);b.gate.resolve(b.assembly);await loading;
    assert.equal(f.town.driverForPerson(row.person_id).state,'moving');
    assertStopped(f.town.driverForPerson(other.person_id),other);f.town.dispose();
  }
  // Blocked/invalid proposed destinations preserve current pending intent; a new
  // valid coordinate destination cancels unresolved intent, never fulfilled Stop.
  {
    const f=fixture(row);f.town.requestDriverApproach(row.person_id);
    assert.equal(makeGo(f.town,{go(){throw Error('blocked target must not navigate');}},{blockedAt:()=>true})(target(row)),false);
    assert.equal(makeGo(f.town,{go(){throw Error('invalid target must not navigate');}})({kind:'person',id:'unknown'}),false);
    assertStopped(await settle(f),row);f.town.dispose();
    const g=fixture(row);g.town.requestDriverApproach(row.person_id);
    assert.equal(makeGo(g.town,{go:()=>true})({kind:'intersection',local_e:12,local_n:34}),true);
    assert.equal((await settle(g)).state,'moving');g.town.dispose();
  }
  // Identity/date/eligibility/Light guards remain lazy metadata operations.
  for (const variant of ['unknown','wrongyear','mismatch','unselectable','missingasset','light']) {
    const changed=structuredClone(row);if(variant==='mismatch')changed.driver_instance.person_id='someone-else';
    if(variant==='unselectable')changed.driver_instance.interaction.selectable=false;
    if(variant==='missingasset')delete changed.driver_asset;
    const f=fixture(changed,{sceneId:variant==='wrongyear'?'1904':changed.scene,detail:variant==='light'?'light':'full'});
    assert.equal(f.town.requestDriverApproach(variant==='unknown'?'unknown':changed.person_id),null);
    assert.equal(f.loads.length,0);f.town.dispose();
  }
  // Fulfilled Stop remains the saved native journey through Light restoration.
  {
    const f=fixture(row);const request=f.town.requestDriverApproach(row.person_id);const actor=await settle(f);assertStopped(actor,row);
    const saved=actor.snapshot(),savedPose=f.poses.at(-1)[1];
    await f.town.setTier('light');assert.equal(f.town.actors.length,0);assert.equal(f.disposed.length,1);
    const restoring=f.town.setTier('full'), next=await f.load(1);next.gate.resolve(next.assembly);await restoring;
    const restored=f.town.actors[0];assert.equal(restored.id,row.id);assert.equal(restored.personId,row.person_id);
    assert.equal(restored.state,'stopped');assert.equal(restored.snapshot().reason,null,'Existing Light serialization preserves stopped state, not its diagnostic reason');
    assert.equal(restored.snapshot().total_distance_m,saved.total_distance_m);assert.equal(restored.snapshot().distance_m,saved.distance_m);
    assert.deepEqual(restored.snapshot().wheel_rotation_rad,saved.wheel_rotation_rad);assert.deepEqual(f.poses.at(-1)[1],savedPose);
    request.cancel();f.town.update(8,f.camera);assert.equal(restored.state,'stopped');
    assert.equal(restored.snapshot().total_distance_m,saved.total_distance_m);assert.deepEqual(f.poses.at(-1)[1],savedPose);
    f.setClear(false);assert.equal(restored.canResume(),false);assert.equal(restored.resume(),false);assert.equal(restored.state,'stopped');
    f.setClear(true);assert(restored.resume());f.town.update(.1,f.camera);
    assert.equal(restored.state,'moving');assert(restored.snapshot().total_distance_m>saved.total_distance_m);
    assert.equal(restored.id,row.id);assert.equal(restored.personId,row.person_id);f.town.dispose();
  }
  // Retired generation cannot consume active intent; cancel while Light removes it.
  for(const cancelWhileLight of [false,true]){
    const f=fixture(row), request=f.town.requestDriverApproach(row.person_id), firstReady=f.town.ready(), old=await f.load(0);
    const light=f.town.setTier('light');if(cancelWhileLight)request.cancel();
    const full=f.town.setTier('full'), next=await f.load(1);
    old.gate.resolve(old.assembly);await firstReady;await light;assert.deepEqual(f.disposed,[0]);
    next.gate.resolve(next.assembly);await full;
    assert.equal(f.town.actors.length,1);assert.equal(f.town.actors[0].state,cancelWhileLight?'moving':'stopped');
    assert.equal(f.publications.filter(p=>p.some(a=>a.id===row.id)).length,1);f.town.dispose();
  }
  // Disposed layer callbacks cannot touch a same-person request in another layer.
  {
    const old=fixture(row), oldRequest=old.town.requestDriverApproach(row.person_id), oldReady=old.town.ready(), load=await old.load(0);
    old.town.dispose();const current=fixture(row);current.town.requestDriverApproach(row.person_id);oldRequest.cancel();
    load.gate.resolve(load.assembly);await oldReady;assert.equal(old.town.actors.length,0);assert.deepEqual(old.disposed,[0]);
    assertStopped(await settle(current),row);current.town.dispose();
  }
  // Real recoverable post-asset spawn error retains intent; fatal factory failure
  // clears it and retains the original no-automatic-retry row owner.
  {
    const f=fixture(row);f.town.requestDriverApproach(row.person_id);f.setClear(false);
    await settle(f);assert.equal(f.town.actors.length,0);assert.deepEqual(f.disposed,[0]);assert.equal(f.problems.length,0);
    await f.town.ready();assert.equal(f.loads.length,1);
    f.setClear(true);assertStopped(await settle(f,1),row);f.town.dispose();
    const g=fixture(row);g.town.requestDriverApproach(row.person_id);const loading=g.town.ready(), failed=await g.load(0);
    failed.gate.reject(Error('actual fatal fixture factory refusal'));await loading;assert.equal(g.problems.length,1);
    await g.town.ready();assert.equal(g.loads.length,1);
    assert.equal(g.town.requestDriverApproach(row.person_id),null,'Known terminal failed row cannot acquire an unfulfillable new request');
    await g.town.setTier('light');const restoring=g.town.setTier('full'), next=await g.load(1);next.gate.resolve(next.assembly);await restoring;
    assert.equal(g.town.actors[0].state,'moving','Fatal row removed its old intent before a later explicit tier reset');g.town.dispose();
    const ground=fixture(row,{heightAt:()=>null});ground.town.requestDriverApproach(row.person_id);await ground.town.ready();
    assert.equal(ground.loads.length,0,'Fatal actual route-ground refusal must precede any model acquisition');
    assert.equal(ground.problems.length,1);assert.equal(ground.town.requestDriverApproach(row.person_id),null);ground.town.dispose();
  }
  console.log('cold named-driver Find: exact configured identities, stop-before-publication, real Travel cancellation, stale tokens, shared Continue, Light/generation/dispose and recoverable/fatal ownership PASS');
}

// Optional composed-parcel acceptance: requires BOTH motion V2 and cold Find.
// Exercise the actual createDrivenAssembly adapter, town and loop together.
{
  const config=JSON.parse(readFileSync(new URL('../data/transport/driven/loops.json',import.meta.url)));
  const row=config.rows.find(r=>r.scene==='1835');let phase=0;const calls=[];let town;
  town=createTownTransport({rows:[row],sceneId:row.scene,heightAt:()=>0,clear:()=>true,routeSupport:()=>({valid:true}),
    makeAssembly:async liveRow=>createDrivenAssembly({vehicle:vehicle.clone(true),
      driver:{root:new THREE.Group(),updateVisual(dt){phase+=dt;calls.push(dt);},snapshot(){return{time_s:phase};}},
      horse:{root:new THREE.Group(),advance(){},stop(){}},driverSeat_m:row.driver_seat_node_m,
      horseOffset_m:row.horse_offset_m,disposeVehicle(){}}),
    onActorsChanged(actors){for(const actor of actors)assert.equal(actor.state,'stopped','Cold Find owns stop before publication and synthetic replay');}});
  const anchor=town.driverAnchorForPerson(row.person_id),camera={x:anchor.at[0],z:-anchor.at[1]};
  town.update(0,camera,{elapsedFrame:true,visualDt:0});const request=town.requestDriverApproach(row.person_id);await town.ready();
  assert.equal(calls.length,0,'Motion V2 synthetic admission cannot prime the independent driver visual clock');
  let actor=town.driverForPerson(row.person_id);assert.equal(actor.state,'stopped');assert.equal(actor.personId,row.person_id);
  const frame=dt=>town.update(dt,camera,{elapsedFrame:true,visualDt:dt});
  frame(8);assert.equal(phase,0);assert.equal(actor.snapshot().total_distance_m,0);
  frame(.5);assert.equal(phase,.5);request.cancel();assert.equal(actor.state,'stopped');
  const saved=actor.snapshot(),savedPhase=phase;
  await town.setTier('light');await town.setTier('full');actor=town.driverForPerson(row.person_id);
  assert.equal(actor.id,row.id);assert.equal(actor.personId,row.person_id);assert.equal(actor.state,'stopped');assert.equal(actor.snapshot().reason,null);
  assert.equal(actor.snapshot().distance_m,saved.distance_m);assert.equal(actor.snapshot().total_distance_m,saved.total_distance_m);
  assert.deepEqual(actor.snapshot().wheel_rotation_rad,saved.wheel_rotation_rad);
  frame(8);assert.equal(phase,savedPhase,'First actual restored visual clock rejects the unseen interval');
  assert.equal(actor.snapshot().total_distance_m,saved.total_distance_m);assert.deepEqual(actor.snapshot().wheel_rotation_rad,saved.wheel_rotation_rad);
  frame(.125);assert.equal(phase,savedPhase+.125);assert.equal(actor.state,'stopped');request.cancel();assert.equal(actor.state,'stopped');
  const before=actor.snapshot(),beforeContinuePhase=phase;assert(actor.resume());frame(8);
  assert.equal(actor.snapshot().total_distance_m,before.total_distance_m,'Continue consumes no pre-action interval');
  assert.deepEqual(actor.snapshot().wheel_rotation_rad,before.wheel_rotation_rad);
  assert.equal(phase,beforeContinuePhase+8,'Qualified independent look continues during a journey-only Stop/Continue');
  frame(.5);assert(Math.abs(actor.snapshot().total_distance_m-Math.min(row.speed_m_s*.5,.25))<1e-9); // one elapsed frame travels at most .25 m
  assert.equal(actor.state,'moving','Fulfilled/canceled Find intent cannot stop a resumed native journey again');
  town.dispose();console.log('composed motionV2+cold Find: actual assembly publication/visual admission, fulfilled Stop, native Continue zero and configured next-frame pace PASS');
}

// The supported later-scene public card adapter is not an 1835 directory mount.
// Exercise its real main function, using the actual named1904 directory above.
{
  const publicPeople = { open: cardOpen };
  const before = opened.length;
  assert.equal(await publicPeople.open(named.personId), true);
  assert.deepEqual(opened.slice(before), [{ id: 'otis_house_2033_prairie', person: named.personId }]);
  assert.equal(publicPeople.people, undefined, 'the public card bridge never claims a mounted directory');
}

// Exercise two actual scene-adapter Light transitions with native Object3D.add.
// Metadata comes from the real configured route/certificates; no assembly/model
// is acquired because the visitor has not approached and lastUpdate is absent.
{
  const { registerHooks } = await import('node:module');
  const threeURL = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
  const hooks = registerHooks({ resolve(specifier, context, next) {
    return specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context);
  } });
  const oldFetch = globalThis.fetch, oldError = console.error, errors = [], requests = [];
  let town;
  try {
    globalThis.fetch = async url => {
      requests.push(String(url));
      assert(String(url).endsWith('.json'), 'Light transitions never acquire a model');
      return new Response(readFileSync(new URL(url)));
    };
    console.error = (...args) => { errors.push(args); };
    const { mountTownTransport } = await import('../renderers/web/js/town-transport-scene.js');
    town = await mountTownTransport({ sceneId: '1835', dataBase: new URL('../data/', import.meta.url),
      humans: { assets: {} }, heightAt: () => 0, footprints: [], visitor: () => null,
      interactions: {}, detail: 'full' });
    await town.setTier('light');
    await town.setTier('full');
    await town.setTier('light');
    assert.deepEqual(errors, [], 'both actual Light callbacks keep the original zero-console-errors contract');
    assert.equal(town.group.children.length, 0);
    assert.deepEqual(town.snapshot(), []);
    assert(requests.length > 0 && requests.every(url => url.endsWith('.json')));
  } finally {
    town?.dispose(); globalThis.fetch = oldFetch; console.error = oldError; hooks.deregister();
  }
}
console.log('LIGHT SCENE CALLBACK + HANS PUBLIC CARD PASS — native scene adapter has zero errors and preserves the named card API');

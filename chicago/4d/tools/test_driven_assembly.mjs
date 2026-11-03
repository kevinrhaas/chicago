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
    HumanActor: FixtureActor, resolveHumanIdentity, createDrivenAssembly,
    fitHorseSupport: () => ({ height_m: 0, normal_local_xyz: [0, 1, 0] }), crypto: webcrypto,
    disposeLoadedAsset(value) {
      if (value === gltfVehicle) stats.vehicleDisposed++;
      else if (value === gltfHorse) stats.horseDisposed++;
      else assert.fail('unexpected disposable asset');
    },
    fetch(url) { const kind = String(url).includes('/horse/') ? 'horse' : 'vehicle'; events.push(kind + '-start'); if (syncFailure === kind) throw failure; return io[kind].promise; },
  };
  const injected = `const { THREE, GLTFLoader, cloneSkinned, HumanActor, resolveHumanIdentity, disposeLoadedAsset, createDrivenAssembly, fitHorseSupport, crypto, fetch } = globalThis[${JSON.stringify(dependencyKey)}];\n`
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
assert.equal(actualPeople1904.people.length, 392); assert.equal(actualPeople1904.residents_root, 'data/residents_1904');
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
  const make = new Function('modelFor', 'people', 'getPeople', 'makeByHorse', 'createDrivenAssemblyLoader', 'sceneId', 'config', 'humans', 'confidence', 'heightAt', 'supportByHorse', 'makeHitch', 'coarse', `return (${method});`)(
    row => row.horse_model, catalog, async () => { gets++; return actualPeople1904; }, new Map(),
    options => { nativeLoaderCalls++; return async row => resolveHumanIdentity({ ...row.driver_instance, scene: row.scene }, { sceneId: '1904', people: options.people }); },
    '1904', actualRoutes, { assets: {} }, null, () => 0, new Map(), () => {}, false);
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

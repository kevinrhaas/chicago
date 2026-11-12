// Focused seasonal nature tests; no browser, network or media decode needed.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { habitatCandidates, createHabitatAudio, HABITAT_AUDIO_LIMITS } from '../renderers/web/js/habitat-audio.js';
import { NATURE_1812_DATES, seasonalHabitatPlacement } from '../renderers/web/js/habitat-seasons.js';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const catalog = JSON.parse(fs.readFileSync(process.env.C4D_AUDIO_CATALOG ?? path.join(root, 'renderers/web/audio/catalog.json'), 'utf8'));
const ids = candidates => candidates.map(c => c.asset.id).sort();
const allAssets = ['coyote-distant', 'late-summer-katydid', 'redwing-call', 'robin-calls', 'summer-cicada-proxy', 'summer-crickets'];
function env(season = 'summer', zone = 'z01_wet_prairie', period = 'day') {
  const [hhmm, sunElevation] = { dawn: ['05:00', 0], day: ['15:00', 55], dusk: ['20:00', -3], night: ['23:00', -20] }[period];
  return { season, time: { date: NATURE_1812_DATES[season], hhmm }, sunElevation,
    camera: { position: { x: 0, y: 2.6, z: 0 }, quaternion: { x: 0, y: 0, z: 0, w: 1 } },
    flora: { zoneAt: () => zone }, terrain: { loaded: true, epochId: 'e1830_natural', isWater: () => false,
      surfaceHeight: () => 1, height: () => { throw Error('navigation height is not audible ground'); }, heightfield: { contains: () => true } } };
}
const candidates = e => habitatCandidates(catalog, e, '1812');
const flush = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
function audioContext() {
  const sources = [], gains = [], panners = [];
  const param = () => ({ value: 0, events: [], setTargetAtTime(v) { this.value = v; this.events.push(['target', v]); },
    setValueAtTime(v) { this.value = v; this.events.push(['set', v]); }, linearRampToValueAtTime(v) { this.value = v; this.events.push(['ramp', v]); } });
  const node = () => ({ connect(n) { this.target = n; }, disconnect() { this.disconnected = true; } });
  return { currentTime: 0, sources, gains, panners,
    createGain() { const n = { ...node(), gain: param() }; gains.push(n); return n; },
    createPanner() { const n = { ...node(), positionX: param(), positionY: param(), positionZ: param() }; panners.push(n); return n; },
    createBufferSource() { const n = { ...node(), start() { this.started = true; }, stop(t) { this.stopAt = t; }, end() { this.onended?.(); } }; sources.push(n); return n; },
    decodeAudioData: async () => ({ duration: 24, sampleRate: 48000, length: 24 * 48000, numberOfChannels: 1 }) };
}
function setup(environment = env(), overrides = {}) {
  const ctx = audioContext(), requests = []; let time = 0, currentCatalog = catalog;
  const engine = createHabitatAudio({ ctx, output: {}, catalog: () => currentCatalog, environment: () => environment,
    now: () => time, random: () => 0,
    fetcher: async (url, options) => { requests.push({ url: String(url), options }); return { ok: true, arrayBuffer: async () => new ArrayBuffer(8) }; }, ...overrides });
  const tick = async (t = time, enabled = true, year = '1812') => { time = t; engine.sync({ enabled, year }); await flush(); };
  return { ctx, requests, engine, tick, env: environment, replaceCatalog(value) { currentCatalog = value; } };
}

test('all six recorded assets have distinct reconstructed placements over existing 1812 flora', () => {
  const scoped = catalog.assets.filter(a => a.seasonal_placements?.some(p => p.scene_id === '1812'));
  assert.deepEqual(scoped.map(a => a.id).sort(), allAssets);
  const flora = read('data/flora/index.json').zones;
  const scene = read('data/scenes/1812.json');
  assert(scene.layers.includes('flora')); assert(!scene.layers.includes('fauna'));
  for (const a of scoped) {
    assert.equal(a.runtime_enabled, true); assert(a.approved_eras.includes('1812'));
    assert.equal(a.license, 'CC0-1.0'); assert(a.delivery.sha256); assert(a.duration_s <= 24);
    for (const p of a.seasonal_placements) {
      const e = env(p.season); assert.equal(seasonalHabitatPlacement(a, e, '1812')?.id, p.id);
      for (const id of p.flora_zone_ids) {
        const z = flora.find(z => z.id === id); assert(z, id);
        assert(!z.scenes || z.scenes.includes('1812'), `${id} is genuinely used by 1812 flora`);
      }
    }
  }
  assert(!scoped.some(a => a.id === 'frog-call'), 'unidentified frog is not silently assigned a species');
});
test('season/period/habitat matrix is sparse; no universal nature bed', () => {
  for (const [season, zone, period, expected] of [
    ['spring', 'z06_dense_forest', 'dawn', ['robin-calls']],
    ['spring', 'z04_marsh', 'day', ['redwing-call']],
    ['spring', 'z06_dense_forest', 'night', []],
    ['spring', 'z01_wet_prairie', 'day', []],
    ['summer', 'z01_wet_prairie', 'day', ['summer-cicada-proxy']],
    ['summer', 'z01_wet_prairie', 'night', ['coyote-distant', 'summer-crickets']],
    ['summer', 'z06_dense_forest', 'night', ['late-summer-katydid']],
    ['summer', 'z04_marsh', 'day', ['redwing-call']],
    ['fall', 'z05_riverbank_timber', 'day', ['robin-calls']],
    ['fall', 'z06_dense_forest', 'night', []],
    ['winter', 'z01_wet_prairie', 'day', []],
    ['winter', 'z06_dense_forest', 'night', []],
    ['winter', 'z01_wet_prairie', 'night', ['coyote-distant']],
    ['summer', 'z10_settled_town', 'night', []],
    ['summer', 'z08_lakeshore', 'day', []],
  ]) assert.deepEqual(ids(candidates(env(season, zone, period))), expected, `${season}/${zone}/${period}`);
});
test('visitor season works with actual seasonal date or retained Aug14; unrelated jaunt dates stay quiet', () => {
  const e = env('spring', 'z06_dense_forest'); e.time.date = '1812-08-14';
  assert.deepEqual(ids(candidates(e)), ['robin-calls']);
  for (const date of ['1812-04-06', '1804-05-20', '1835-07-01', '1812-10-15', undefined]) {
    e.time.date = date; assert.deepEqual(candidates(e), [], String(date));
  }
  e.time.date = '1812-08-14'; e.season = 'winter'; assert.deepEqual(candidates(e), []);
  e.season = 'toString'; assert.deepEqual(candidates(e), []);
});
test('1812 does not depend on copied July1835 fauna or allow another terrain/era', () => {
  const e = env(); assert.deepEqual(ids(candidates(e)), ['summer-cicada-proxy']);
  e.faunaZones = []; assert.deepEqual(ids(candidates(e)), ['summer-cicada-proxy']);
  e.faunaZones = [{ scene_date: '1835-07-01', species: [] }]; assert.deepEqual(ids(candidates(e)), ['summer-cicada-proxy']);
  for (const year of ['1835', '1904', 'unknown']) assert.deepEqual(habitatCandidates(catalog, e, year), []);
  e.terrain.epochId = 'e1834_harbor_cut'; assert.deepEqual(candidates(e), []);
  e.terrain.epochId = 'e1830_natural'; e.terrain.loaded = false; assert.deepEqual(candidates(e), []);
});
test('supplied cold suppresses summer insects; absent temperature is not an invented measurement', () => {
  const cases = [['z01_wet_prairie', 'day', 18, 'summer-cicada-proxy'], ['z01_wet_prairie', 'night', 10, 'summer-crickets'],
    ['z06_dense_forest', 'night', 15, 'late-summer-katydid']];
  for (const [zone, period, floor, id] of cases) {
    const e = env('summer', zone, period); assert(ids(candidates(e)).includes(id));
    e.temperatureC = floor - 0.1; assert(!ids(candidates(e)).includes(id));
    e.temperatureC = floor; assert(ids(candidates(e)).includes(id));
    e.temperatureC = NaN; assert.deepEqual(candidates(e), []);
  }
  const winter = env('winter', 'z01_wet_prairie', 'night'); winter.temperatureC = -15;
  assert.deepEqual(ids(candidates(winter)), ['coyote-distant'], 'resident mammal is not an insect cold gate');
  winter.temperatureC = 25; assert.deepEqual(ids(candidates(winter)), ['coyote-distant'], 'warm February does not authorize a summer chorus');
});
test('sun/hour gates suppress afternoon insects in morning and all nature without solar state', () => {
  const e = env(); e.time.hhmm = '09:00'; assert.deepEqual(candidates(e), []);
  e.time.hhmm = '15:00'; e.sunElevation = undefined; assert.deepEqual(candidates(e), []);
  const c = env('winter', 'z01_wet_prairie', 'night'); c.sunElevation = -6; assert.deepEqual(candidates(c), []);
  c.sunElevation = -6.01; assert.deepEqual(ids(candidates(c)), ['coyote-distant']);
});
test('dry terrestrial sources use actual ground, water/unknown ground and unmodelled habitat stay quiet', () => {
  for (const mutate of [e => e.terrain.surfaceHeight = () => 0, e => e.terrain.isWater = () => true,
    e => delete e.terrain.surfaceHeight, e => e.terrain.surfaceHeight = () => { throw Error('replaced terrain'); },
    e => e.terrain.heightfield.contains = () => false, e => e.flora.zoneAt = () => { throw Error('disposed flora'); }]) {
    const e = env('winter', 'z01_wet_prairie', 'night'); mutate(e); assert.deepEqual(candidates(e), []);
  }
  const e = env('spring', 'z04_marsh'); e.terrain.surfaceHeight = () => -2; e.terrain.isWater = () => true;
  assert.equal(candidates(e)[0].anchor.y, 1.5, 'wetland bird still uses a perch above the water plane');
});
test('coyote requires prairie at listener and source; mammal height/range differ from bird', () => {
  const e = env('winter', 'z01_wet_prairie', 'night'); const c = candidates(e)[0];
  assert.equal(c.anchor.y, 1.65); assert(c.distance === undefined);
  assert(Math.hypot(c.anchor.x, c.anchor.z) >= 120); assert(c.gain > 0 && c.gain < c.placement.gain);
  e.flora.zoneAt = (x, n) => n === 0 ? 'z10_settled_town' : 'z01_wet_prairie'; assert.deepEqual(candidates(e), []);
  e.flora.zoneAt = (x, n) => n === 0 ? 'z01_wet_prairie' : 'z04_marsh'; assert.deepEqual(candidates(e), []);
});
test('all nature culls with height, full3D range, off-grid habitat, or absent metadata', () => {
  const insect = env(); insect.camera.position.y = 34; assert.deepEqual(candidates(insect), []);
  const bird = env('spring', 'z06_dense_forest'); bird.camera.position.y = 200; assert.deepEqual(candidates(bird), []);
  const mammal = env('winter', 'z01_wet_prairie', 'night'); mammal.camera.position.y = 400; assert.deepEqual(candidates(mammal), []);
  const missing = structuredClone(catalog); missing.assets.forEach(a => delete a.seasonal_placements);
  assert.deepEqual(habitatCandidates(missing, env(), '1812'), []);
  const duplicate = structuredClone(catalog), a = duplicate.assets.find(a => a.id === 'summer-cicada-proxy');
  a.seasonal_placements.push(a.seasonal_placements[0]); assert.deepEqual(habitatCandidates(duplicate, env(), '1812'), []);
});
test('coyote is one rare complete phrase with real initial and recurring quiet', async () => {
  const f = setup(env('winter', 'z01_wet_prairie', 'night'));
  await f.tick(0); await f.tick(119000); assert.equal(f.requests.length, 0);
  await f.tick(120000); assert.deepEqual(f.engine.state.voices, ['coyote-distant']); assert.equal(f.ctx.sources[0].loop, false);
  const fixed = f.engine.state.anchor; f.env.camera.position.x += 1; await f.tick(121000); assert.deepEqual(f.engine.state.anchor, fixed);
  f.ctx.sources[0].end(); await f.tick(144000); await f.tick(443000); assert.equal(f.ctx.sources.length, 1);
  await f.tick(444000); assert.equal(f.ctx.sources.length, 2); assert.equal(f.requests.length, 1, 'reuse only the one retained clip');
  f.engine.dispose();
});
test('approved due insect wins over rare coyote without overlap; one cache remains bounded', async () => {
  const f = setup(env('summer', 'z01_wet_prairie', 'night'));
  await f.tick(0); await f.tick(120000); assert.deepEqual(f.engine.state.voices, ['summer-crickets']);
  await f.tick(121000); assert.equal(f.ctx.sources.length, 1);
  assert(f.engine.state.decodedBytes <= HABITAT_AUDIO_LIMITS.decodedBytes); assert.equal(f.engine.state.loading, 0);
  f.ctx.sources[0].end(); await f.tick(156000); assert.deepEqual(f.engine.state.voices, ['coyote-distant']);
  assert.equal(f.requests.length, 2); assert(f.engine.state.decodedBytes <= HABITAT_AUDIO_LIMITS.decodedBytes);
  f.engine.dispose();
});
test('season change cancels a pending summer decode even when runtime date remains Aug14', async () => {
  let complete; const f = setup(env(), { decodeAudio: () => new Promise(r => { complete = r; }) });
  await f.tick(0); await f.tick(6000); assert.equal(f.engine.state.loading, 1);
  f.env.season = 'winter'; await f.tick(6001); assert(f.requests[0].options.signal.aborted);
  complete({ duration: 22, sampleRate: 48000, length: 1056000, numberOfChannels: 1 }); await flush();
  assert.deepEqual(f.engine.state.voices, []); assert.equal(f.engine.state.decodedBytes, 0); assert.equal(f.engine.state.loading, 0);
  f.engine.dispose();
});
test('mute/hidden-effective disable and resume retain pending reservation; stale decode cannot restart', async () => {
  let complete; const f = setup(env('spring', 'z06_dense_forest'), { decodeAudio: () => new Promise(r => { complete = r; }) });
  await f.tick(0); await f.tick(15000); assert.equal(f.engine.state.loading, 1);
  await f.tick(15001, false); await f.tick(15002); await f.tick(100000); assert.equal(f.requests.length, 1);
  complete({ duration: 24, sampleRate: 48000, length: 1152000, numberOfChannels: 1 }); await flush();
  assert.deepEqual(f.engine.state.voices, []); assert.equal(f.engine.state.decodedBytes, 0);
  f.engine.dispose(); await f.tick(200000); assert.equal(f.requests.length, 1);
});
test('date/year or same-epoch terrain replacement invalidates a pending decode', async () => {
  for (const change of [f => f.env.time.date = '1804-05-20', f => f.env.terrain = { ...f.env.terrain }]) {
    let complete; const f = setup(env(), { decodeAudio: () => new Promise(r => { complete = r; }) });
    await f.tick(0); await f.tick(6000); change(f); await f.tick(6001);
    complete({ duration: 22, sampleRate: 48000, length: 1056000, numberOfChannels: 1 }); await flush();
    assert.deepEqual(f.engine.state.voices, []); assert.equal(f.engine.state.decodedBytes, 0); f.engine.dispose();
  }
});
test('near/in-view mammal stops at fixed anchor; winter cooldown survives mute', async () => {
  const f = setup(env('winter', 'z01_wet_prairie', 'night')); await f.tick(0); await f.tick(120000);
  const a = f.engine.state.anchor; f.env.camera.position = { x: a.x, y: a.y, z: a.z - 20 };
  await f.tick(121000); assert.equal(f.ctx.sources[0].stopAt, 0.08); f.ctx.sources[0].end();
  f.env.camera.position = { x: 0, y: 2.6, z: 0 }; await f.tick(150000, false); await f.tick(151000); await f.tick(300000);
  assert.equal(f.ctx.sources.length, 1); await f.tick(444000); assert.equal(f.ctx.sources.length, 2);
  f.env.camera.quaternion = { x: 0, y: 1, z: 0, w: 0 }; await f.tick(445000); assert.equal(f.ctx.sources[1].stopAt, 0.08);
  f.engine.dispose();
});
test('catalog revocation stops active seasonal source without using its stale asset object', async () => {
  const f = setup(env()); await f.tick(0); await f.tick(6000); assert.equal(f.ctx.sources.length, 1);
  const removed = structuredClone(catalog); removed.assets.find(a => a.id === 'summer-cicada-proxy').runtime_enabled = false;
  f.replaceCatalog(removed); await f.tick(7000); assert.equal(f.ctx.sources[0].stopAt, 0.08); f.engine.dispose();
});
test('wrong channel/rate/duration/size remains rejected and failed clips are not refetched', async () => {
  for (const bad of [{ numberOfChannels: 2 }, { sampleRate: 96000 }, { duration: 25 }, { length: NaN }]) {
    const f = setup(env(), { decodeAudio: async () => ({ duration: 22, sampleRate: 48000, length: 1056000, numberOfChannels: 1, ...bad }) });
    await f.tick(0); await f.tick(6000); await f.tick(100000);
    assert.deepEqual(f.engine.state.voices, []); assert.equal(f.engine.state.decodedBytes, 0); assert.equal(f.requests.length, 1);
    assert.match(f.engine.state.errors[0], /budget/); f.engine.dispose();
  }
});

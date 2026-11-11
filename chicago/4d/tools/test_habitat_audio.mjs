import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHabitatAudio, habitatCandidates, habitatPeriod, HABITAT_AUDIO_LIMITS } from '../renderers/web/js/habitat-audio.js';
import { createRecordedAudio } from '../renderers/web/js/recorded-audio.js';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const source = process.env.C4D_SOURCE_ROOT ?? root;
const read = rel => JSON.parse(fs.readFileSync(path.join(source, rel), 'utf8'));
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'renderers/web/audio/catalog.json'), 'utf8'));
const index = read('data/fauna/index.json');
const zones = index.zones.map(z => read('data/fauna/' + z.file));
const ids = list => list.map(c => c.asset.id).sort();
const selected = catalog.assets.filter(a => a.runtime_enabled === true);
assert.deepEqual(selected.map(a => a.id).sort(), ['redwing-call', 'summer-cicada-proxy', 'summer-crickets']);
for (const a of selected) {
  assert.deepEqual(a.approved_eras, ['1835']);
  assert.equal(a.scene_placement.scene_date, index.scene_date);
  for (const id of a.scene_placement.zone_ids) {
    const z = zones.find(z => z.id === id), sp = z.species.find(s => s.id === a.scene_placement.species_id);
    assert(z.in_modelled_extent && sp, `${a.id}: actual record and ground exist`);
    assert(['audible', 'visible_and_audible'].includes(sp.july.presence.value));
    assert.notEqual(sp.july.vocalization, 'silent');
  }
}
function environment(zone = 'z01_wet_prairie') {
  return { season: 'summer', time: { date: '1835-07-01', hhmm: '15:00' }, sunElevation: 55,
    faunaZones: structuredClone(zones), camera: { position: { x: 0, y: 2, z: 0 }, quaternion: { x: 0, y: 0, z: 0, w: 1 } },
    flora: { zoneAt: () => zone }, terrain: { loaded: true, isWater: () => false, surfaceHeight: () => 0, height: () => 4, heightfield: { contains: () => true } } };
}
{
  const env = environment();
  assert.deepEqual(ids(habitatCandidates(catalog, env, '1835')), ['summer-cicada-proxy']);
  env.time.hhmm = '22:00'; env.sunElevation = -20;
  assert.equal(habitatPeriod(env), 'night');
  assert.deepEqual(ids(habitatCandidates(catalog, env, '1835')), ['summer-crickets']);
  env.time.hhmm = '05:00'; env.sunElevation = 0;
  assert.equal(habitatPeriod(env), 'dawn');
  assert.deepEqual(habitatCandidates(catalog, env, '1835'), [], 'no early-July dawn cricket or afternoon cicada');
  env.time.hhmm = '20:00'; env.sunElevation = -3;
  assert.equal(habitatPeriod(env), 'dusk');
  assert.deepEqual(ids(habitatCandidates(catalog, env, '1835')), ['summer-cicada-proxy', 'summer-crickets']);
  const airborne = environment(); airborne.camera.position.y = 40;
  assert.deepEqual(habitatCandidates(catalog, airborne, '1835'), [], 'flying away from ground insects becomes quiet');
  for (const year of ['1812', '1904', '1880', 'unknown']) assert.deepEqual(habitatCandidates(catalog, env, year), []);
  for (const season of ['spring', 'fall', 'winter']) assert.deepEqual(habitatCandidates(catalog, { ...env, season }, '1835'), []);
  for (const date of ['1835-06-17', '1835-08-15', '1812-07-01'])
    assert.deepEqual(habitatCandidates(catalog, { ...env, time: { ...env.time, date } }, '1835'), [], 'jaunt date is not silently treated as July');
  assert.deepEqual(habitatCandidates(catalog, { ...env, temperatureC: 0 }, '1835'), []);
  assert.deepEqual(habitatCandidates(catalog, { ...env, sunElevation: undefined }, '1835'), []);
  assert.deepEqual(habitatCandidates(catalog, { ...env, faunaZones: [] }, '1835'), []);
  assert.deepEqual(habitatCandidates(catalog, { ...env, terrain: { loaded: false } }, '1835'), []);
  env.faunaZones[0].species.find(s => s.id === 'gryllus_spp').july.vocalization = 'silent';
  assert(!ids(habitatCandidates(catalog, env, '1835')).includes('summer-crickets'), 'the record can suppress its sound');
  env.faunaZones[0].species.find(s => s.id === 'neotibicen_spp').july.status.value = 'absent_anachronism';
  assert.deepEqual(habitatCandidates(catalog, env, '1835'), [], 'an absent animal never acquires sound from its old metadata');
  const undeclared = structuredClone(catalog); undeclared.assets.find(a => a.id === 'summer-cicada-proxy').runtime_enabled = false;
  assert.deepEqual(habitatCandidates(undeclared, env, '1835'), []);
}
{
  const env = environment('z06_dense_forest'); env.time.hhmm = '22:00'; env.sunElevation = -20;
  const forged = structuredClone(catalog), katydid = forged.assets.find(a => a.id === 'late-summer-katydid');
  katydid.runtime_enabled = true; katydid.approved_eras = ['1835'];
  katydid.scene_placement = { ...selected.find(a => a.id === 'summer-crickets').scene_placement,
    species_id: 'pterophylla_camellifolia', zone_ids: ['f06_north_timber'] };
  assert.deepEqual(habitatCandidates(forged, env, '1835'), [], 'a catalogue edit cannot override the July katydid silence');
}
{
  const env = environment('z10_settled_town');
  assert.deepEqual(habitatCandidates(catalog, env, '1835'), [], 'town is not silently labelled wet prairie');
  const queries = [];
  env.flora.zoneAt = (e, n) => { queries.push([e, n]); return n < -35 ? 'z04_marsh' : 'z10_settled_town'; };
  const calls = habitatCandidates(catalog, env, '1835');
  assert.deepEqual(ids(calls), ['redwing-call']);
  const c = calls[0];
  assert(c.anchor.z > 35 && Math.hypot(c.anchor.x, c.anchor.z) >= 44, 'source is behind the -Z camera and genuinely distant');
  assert(queries.some(([e, n]) => e === c.anchor.x && n === -c.anchor.z), 'habitat is sampled in e/n, not Three x/z');
  assert(c.gain < c.placement.gain && c.gain > 0, 'distant call is attenuated');
  env.camera.position.y = 200;
  assert.deepEqual(habitatCandidates(catalog, env, '1835'), [], 'flying above range does not hear a horizontally near bird');
  env.camera.position.y = 60; env.camera.quaternion = { x: -Math.SQRT1_2, y: 0, z: 0, w: Math.SQRT1_2 };
  assert.deepEqual(habitatCandidates(catalog, env, '1835'), [], 'a bird below a downward camera is in front, not behind');
  env.camera.position.y = 2; env.camera.quaternion = { x: 0, y: 0, z: 0, w: 1 };
  env.terrain.heightfield.contains = () => false;
  assert.deepEqual(habitatCandidates(catalog, env, '1835'), [], 'unmodelled/off-grid habitat is quiet');
}
{
  const env = environment('z04_marsh');
  env.terrain.surfaceHeight = () => -2; env.terrain.groundHeight = () => 20;
  const bird = habitatCandidates(catalog, env, '1835')[0];
  assert.equal(bird.anchor.y, 1.5, 'marsh call sits above water, not on the 4 m walk barrier or underwater');
  delete env.terrain.surfaceHeight; env.terrain.groundHeight = () => 2;
  assert.equal(habitatCandidates(catalog, env, '1835')[0].anchor.y, 3.5, 'groundHeight is an actual-surface fallback');
  delete env.terrain.groundHeight;
  assert.deepEqual(habitatCandidates(catalog, env, '1835'), [], 'walk barrier alone is never substituted for measured ground');
  const insect = environment(); insect.camera.position.y = 33;
  assert.deepEqual(habitatCandidates(catalog, insect, '1835'), [], 'actual ground suppresses high listener even when walk barrier would not');
}
const flush = async () => { for (let i = 0; i < 15; i++) await Promise.resolve(); };
function audioContext() {
  const sources = [], gains = [], panners = [];
  const param = () => ({ value: 0, events: [], setTargetAtTime(v, ...rest) { this.value = v; this.events.push(['target', v, ...rest]); },
    setValueAtTime(v, ...rest) { this.value = v; this.events.push(['set', v, ...rest]); },
    linearRampToValueAtTime(v, ...rest) { this.value = v; this.events.push(['ramp', v, ...rest]); } });
  const node = () => ({ connect(n) { this.target = n; }, disconnect() { this.disconnected = true; } });
  return { currentTime: 0, listener: {}, sources, gains, panners,
    createGain() { const n = { ...node(), gain: param() }; gains.push(n); return n; },
    createPanner() { const n = { ...node(), positionX: param(), positionY: param(), positionZ: param() }; panners.push(n); return n; },
    createBufferSource() { const n = { ...node(), start() { this.started = true; }, stop(t) { this.stopAt = t; }, end() { this.onended?.(); } }; sources.push(n); return n; },
    decodeAudioData: async () => ({ duration: 22, sampleRate: 48000, length: 22 * 48000, numberOfChannels: 1 }),
  };
}
function setup(env = environment(), overrides = {}) {
  const ctx = audioContext(), requests = []; let time = 0;
  const engine = createHabitatAudio({ ctx, output: {}, catalog: () => catalog, environment: () => env,
    now: () => time, random: () => 0.5,
    fetcher: async (url, options) => { requests.push({ url: String(url), options }); return { ok: true, arrayBuffer: async () => new ArrayBuffer(8) }; }, ...overrides });
  const tick = async (t = time, enabled = true, year = '1835') => { time = t; engine.sync({ enabled, year }); await flush(); };
  return { ctx, requests, engine, tick, env };
}
{
  const { ctx, requests, engine, tick } = setup();
  await tick(0, false); assert.equal(requests.length, 0);
  await tick(1000); assert.equal(requests.length, 0, 'initial quiet interval is real');
  await tick(15000); assert.equal(requests.length, 1);
  assert.deepEqual(engine.state.voices, ['summer-cicada-proxy']);
  assert(engine.state.decodedBytes <= HABITAT_AUDIO_LIMITS.decodedBytes);
  assert.equal(ctx.sources[0].loop, false, 'loop-ready file is still one finite phrase');
  const envelope = ctx.gains.find(n => n.gain.events.some(e => e[0] === 'ramp'));
  const envelopeEvents = structuredClone(envelope.gain.events);
  engine.setDuck(0.3);
  assert.deepEqual(envelope.gain.events, envelopeEvents, 'speech ducking must not overwrite the phrase edge fades');
  assert(ctx.gains.some(n => n.gain.events.some(e => e[0] === 'target' && e[1] === 0.065 * (1 - 2 / 32) ** 2 * 0.3)));
  await tick(20000); assert.equal(ctx.sources.length, 1, 'no second voice or overlapping decode');
  ctx.sources[0].end();
  await tick(40000); assert.equal(ctx.sources.length, 1, 'silence persists after the phrase');
  await tick(100000); assert.equal(ctx.sources.length, 2); assert.equal(requests.length, 1, 'reuse the one retained clip');
  await tick(100001, false); assert.equal(engine.state.decodedBytes, 0); assert.deepEqual(engine.state.voices, []);
  assert(ctx.sources.at(-1).disconnected);
  engine.dispose(); await tick(200000); assert.equal(requests.length, 1);
}
{
  const env = environment(); env.time.hhmm = '20:00'; env.sunElevation = -3;
  const { ctx, engine, tick } = setup(env);
  await tick(0); await tick(15000); assert.equal(ctx.sources.length, 1);
  ctx.sources[0].end(); await tick(37000);
  assert.equal(ctx.sources.length, 1, 'another due insect cannot fill the global quiet interval');
  await tick(56000); assert.equal(ctx.sources.length, 2);
  engine.dispose();
}
{
  const env = environment('z04_marsh'), { ctx, engine, tick } = setup(env);
  await tick(0); await tick(20000);
  assert.deepEqual(engine.state.voices, ['redwing-call']);
  const anchor = engine.state.anchor;
  assert.equal(ctx.panners.length, 1);
  env.camera.position.x = anchor.x; env.camera.position.z = anchor.z - 10;
  await tick(20250); assert.equal(ctx.sources.at(-1).stopAt, ctx.currentTime + 0.08); ctx.sources.at(-1).end();
  assert.deepEqual(engine.state.voices, [], 'approaching an invisible bird stops its call');
  env.camera.position.x = 0; env.camera.position.z = 0;
  await tick(21000); assert.deepEqual(engine.state.voices, [], 'no instant re-anchoring around the listener');
  engine.reset(); await tick(22000); await tick(42000);
  assert.deepEqual(engine.state.voices, ['redwing-call']);
  env.camera.quaternion = { x: 0, y: 1, z: 0, w: 0 };
  await tick(42250); ctx.sources.at(-1).end(); assert.deepEqual(engine.state.voices, [], 'turning toward the absent bird suppresses a close identifiable source');
  engine.dispose();
}
{
  const env = environment(); let completeDecode;
  const { ctx, requests, engine, tick } = setup(env);
  ctx.decodeAudioData = () => new Promise(r => { completeDecode = r; });
  await tick(0); await tick(15000); assert.equal(engine.state.loading, 1);
  await tick(15001, false); assert(requests[0].options.signal.aborted);
  await tick(15002); await tick(30000);
  assert.equal(requests.length, 1, 'a pending decode remains reserved through mute/unmute');
  completeDecode({ duration: 22, sampleRate: 48000, length: 1056000, numberOfChannels: 1 }); await flush();
  assert.equal(engine.state.decodedBytes, 0); assert.deepEqual(engine.state.voices, [], 'late decode cannot resurrect a reset voice');
  assert.equal(engine.state.loading, 0);
  engine.dispose();
}
{
  for (const invalid of [{ numberOfChannels: 2 }, { duration: 25 }, { sampleRate: 96000 }, { length: NaN }]) {
    const { ctx, requests, engine, tick } = setup();
    ctx.decodeAudioData = async () => ({ duration: 22, sampleRate: 48000, length: 1056000, numberOfChannels: 1, ...invalid });
    await tick(0); await tick(15000); await tick(200000);
    assert.deepEqual(engine.state.voices, []); assert.equal(engine.state.decodedBytes, 0);
    assert.equal(requests.length, 1, 'invalid delivery is not repeatedly fetched');
    assert.match(engine.state.errors[0], /budget/); engine.dispose();
  }
}
{
  // Integration through the existing recorded-audio facade: ambience/master
  // controls stop habitat sound even while the independent music bus is enabled.
  const env = environment(), ctx = audioContext(); let time = 0, fetched = [];
  const engine = createRecordedAudio({ ctx, ambience: {}, music: { gain: { setTargetAtTime() {} } },
    environment: () => env, now: () => time,
    fetcher: async url => { fetched.push(String(url)); return { ok: true, json: async () => catalog, arrayBuffer: async () => new ArrayBuffer(8) }; } });
  engine.sync({ active: true, ambienceOn: true, musicOn: false, year: '1835' }); await flush();
  time = 30000; engine.update(); await flush();
  assert(engine.state.voices.includes('summer-cicada-proxy'));
  assert(engine.state.decodedBytes <= 14 * 1024 * 1024 + HABITAT_AUDIO_LIMITS.decodedBytes);
  engine.sync({ active: true, ambienceOn: false, musicOn: false, year: '1835' });
  assert.deepEqual(engine.state.habitat.voices, []); assert.equal(engine.state.habitat.decodedBytes, 0);
  const count = fetched.length; time = 90000; engine.update(); await flush(); assert.equal(fetched.length, count);
  engine.dispose();
}
console.log('HABITAT AUDIO PASS: actual dated records/ground; sun, season, era and cold gates; distant offscreen bird anchors; finite phrases and real silence; bounded memory/voices; mute/disposal/decode races; existing mixer integration');

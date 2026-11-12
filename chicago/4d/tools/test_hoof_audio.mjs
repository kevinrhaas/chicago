// SPDX-License-Identifier: GPL-3.0-or-later
// Fake WebAudio validates lifecycle/accounting; this is not a listening test.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import { createTransportAudio, TRANSPORT_AUDIO_LIMITS as LIMITS } from '../renderers/web/js/transport-audio.js';
import { HOOF_RECORDING as R, WALK_V2_CONTACTS as GAIT, hoofCandidates,
  hoofSurfaceProfile, extractHoofBuffers } from '../renderers/web/js/hoof-contact-events.js';
const root = new URL('../', import.meta.url);
const delivered = fs.readFileSync(new URL('renderers/web/audio/candidates/horse-walking.mp3', root));
const encoded = delivered.buffer.slice(delivered.byteOffset, delivered.byteOffset + delivered.byteLength);
const ids = ['fort_wagon_loop_1812', 'shore_road_wagon_haul_1812'];
const dates = { summer: '1812-08-14', spring: '1812-04-15', fall: '1812-10-15', winter: '1812-02-15' };
const waitFor = async predicate => {
  const deadline = Date.now() + 3000;
  while (!predicate()) { assert.ok(Date.now() < deadline, 'fixture asynchronous completion'); await new Promise(r => setTimeout(r, 1)); }
};
const settled = s => waitFor(() => s.engine.state.loading === 0);
const point = { x: 0, y: 0, z: 0 };
const horse = (id, distanceM = .2) => ({ id, distanceM, strideM: GAIT.strideM,
  clipSha256: GAIT.clipSha256, modelSha256: GAIT.modelSha256,
  hooves: Object.fromEntries(GAIT.contacts.map(c => [c.foot, { ...point }])) });
const actor = id => ({ id, scene: '1812', moving: true, speed: 1.3, anchors: {
  harness: { ...point }, wagon: { ...point },
  hoof: { epoch: 'spawn-1', horses: [horse('left'), horse('right')] },
} });
const bindings = Object.entries(dates).map(([season, scene_date]) => ({ scene: '1812', season, scene_date, actor_ids: ids }));
const hoofAsset = () => ({ id: R.id, runtime_enabled: true, approved_eras: ['1812'], url: 'horse-walking.mp3',
  delivery: { sha256: R.sha256, bytes: R.encodedBytes },
  scene_placement: { mode: 'hoof-contact', gain: .24, max_distance_m: 32, bindings } });
const mechanical = id => ({ id, runtime_enabled: true, approved_eras: ['1812', '1835', '1904'],
  url: `${id}.mp3`, delivery: { sha256: 'fixture' }, scene_placement: { mode: 'moving-transport',
    anchor: id, gain: .1, max_distance_m: 32, bindings: [...bindings,
      ...['1835', '1904'].map(scene => ({ scene, scene_date: `${scene}-07-01`, actor_ids: ids }))] } });
const sourceSamples = new Float32Array(508094).fill(.25);
const sourceBuffer = () => ({ numberOfChannels: 1, sampleRate: 48000, length: sourceSamples.length,
  duration: sourceSamples.length / 48000, getChannelData: () => sourceSamples });
function context() {
  const sources = [], filters = [], cuts = [];
  const param = () => ({ value: 1, setValueAtTime(v) { this.value = v; },
    linearRampToValueAtTime(v) { this.value = v; }, setTargetAtTime(v) { this.value = v; } });
  const node = () => ({ connect() {}, disconnect() { this.disconnected = true; } });
  return { currentTime: 0, sources, filters, cuts,
    createGain: () => ({ ...node(), gain: param() }),
    createPanner: () => ({ ...node(), positionX: param(), positionY: param(), positionZ: param() }),
    createBiquadFilter() { const f = { ...node(), frequency: param(), Q: param() }; filters.push(f); return f; },
    createBuffer(channels, length, rate) { const samples = new Float32Array(length);
      const b = { numberOfChannels: channels, length, sampleRate: rate, duration: length / rate, getChannelData: () => samples }; cuts.push(b); return b; },
    createBufferSource() { const s = { ...node(), playbackRate: param(),
      start(...args) { this.started = args; }, stop(...args) { this.stopped = args; }, end() { this.onended?.(); } }; sources.push(s); return s; },
  };
}
function setup({ contact = true, decode, fetcher } = {}) {
  const ctx = context(), assets = [mechanical('harness'), mechanical('wagon'), ...(contact ? [hoofAsset()] : [])];
  const env = { camera: { position: { x: 0, y: 1, z: 5 } }, season: 'summer', snowCover: 0,
    time: { date: dates.summer }, transport: ids.map(actor) };
  let time = 0, fetches = 0, decodes = 0, reads = 0;
  const engine = createTransportAudio({ ctx, output: {}, catalog: () => ({ assets }),
    environment: () => { reads++; return env; }, now: () => time, random: () => 0,
    base: new URL('https://fixture.invalid/'),
    fetcher: fetcher ?? (async url => { fetches++; return { ok: true, arrayBuffer: async () =>
      url.pathname.includes('horse-walking') ? encoded : Uint8Array.of(url.pathname.includes('harness') ? 1 : 2).buffer }; }),
    decodeAudio: async data => { decodes++; if (decode) return decode(data);
      if (data.byteLength > 2) return sourceBuffer();
      const duration = new Uint8Array(data)[0] === 1 ? 24 : 11.0901875;
      return { duration, length: Math.round(duration * 48000), sampleRate: 48000, numberOfChannels: 1 }; },
  });
  return { ctx, env, assets, engine, get reads() { return reads; }, get fetches() { return fetches; }, get decodes() { return decodes; },
    sync(enabled = true, year = '1812') { engine.sync({ enabled, year }); },
    frame(ms, enabled = true, year = '1812') { time = ms; ctx.currentTime = ms / 1000; engine.frame({ enabled, year }); },
    move(distanceM) { for (const a of env.transport) for (const h of a.anchors.hoof.horses) h.distanceM = distanceM; },
  };
}
async function mechanicsReady(s) { s.sync(); await settled(s); s.sync(); await settled(s); s.sync(); }
async function prime(s) { await mechanicsReady(s); s.frame(0); await settled(s); s.frame(16); }
test('source bytes and actual clip remain bound to the measured excerpts and gait', () => {
  assert.equal(delivered.length, R.encodedBytes); assert.equal(createHash('sha256').update(delivered).digest('hex'), R.sha256);
  const bytes = fs.readFileSync(new URL('renderers/web/transport/driven/horse-walk-v2.json', root));
  const clip = JSON.parse(bytes); assert.equal(createHash('sha256').update(bytes).digest('hex'), GAIT.clipSha256);
  assert.equal(clip.model_sha256, GAIT.modelSha256); assert.equal(clip.cycle_m, GAIT.strideM);
  for (const contact of GAIT.contacts) assert.equal((clip.params.phase[contact.foot] + .96484375) % 1, contact.phase);
});
test('only the actual two 1812 actors on their exact seasonal viewing dates qualify', () => {
  const s = setup(), asset = hoofAsset();
  for (const [season, date] of Object.entries(dates)) {
    s.env.season = season; s.env.time.date = date;
    assert.equal(hoofCandidates(asset, s.env, '1812').length, 2);
    s.env.time.date = '1812-08-15'; assert.equal(hoofCandidates(asset, s.env, '1812').length, 0);
  }
  s.env.season = 'summer'; s.env.time.date = dates.summer;
  assert.deepEqual(hoofCandidates(asset, s.env, '1904'), []);
  s.env.transport[0].id = 'invented'; assert.equal(hoofCandidates(asset, s.env, '1812').length, 1);
  s.env.transport[1].moving = false; assert.equal(hoofCandidates(asset, s.env, '1812').length, 0);
  s.engine.dispose();
});
test('extraction retains only 55,296 bytes, preserves interior samples and fades both edges', () => {
  const ctx = context(), cuts = extractHoofBuffers(ctx, sourceBuffer());
  assert.deepEqual(cuts.map(b => b.length), [6144, 7680]);
  assert.equal(cuts.reduce((n, b) => n + b.length * 4, 0), 55296);
  for (const b of cuts) { assert.equal(b.getChannelData(0)[0], 0); assert.equal(b.getChannelData(0).at(-1), 0); assert.equal(b.getChannelData(0)[100], .25); }
  assert.throws(() => extractHoofBuffers(ctx, { ...sourceBuffer(), numberOfChannels: 2 }));
  assert.throws(() => extractHoofBuffers(ctx, sourceBuffer(), 50000));
});
test('six-voice 1812 budget keeps all four mechanicals and adds two rate-one finite contacts', async () => {
  const s = setup(); await prime(s);
  assert.equal(s.engine.state.voices.length, 4); assert.equal(s.engine.state.contactVoices, 0);
  s.move(.22); s.frame(32);
  assert.equal(s.engine.state.voices.length, 6); assert.equal(s.engine.state.contactVoices, 2);
  const shots = s.ctx.sources.filter(n => n.buffer.duration < 1);
  assert.equal(shots.length, 2); for (const shot of shots) { assert.equal(shot.loop, false); assert.equal(shot.playbackRate.value, 1); assert.equal(shot.started[1], 0); assert.ok(shot.started[2] <= .16); }
  s.move(.47); s.frame(48); assert.equal(s.ctx.sources.filter(n => n.buffer.duration < 1).length, 2, 'busy contact slots drop, never queue');
  shots.forEach(n => n.end()); s.frame(64); assert.equal(s.engine.state.contactVoices, 0);
  assert.equal(s.engine.state.contactDecodedBytes, 55296);
  assert.equal(s.engine.state.peakDecodedBytes, 8824988);
  assert.equal(s.engine.state.decodedBytes, 6792612);
  assert.equal(s.engine.state.voiceLimit, 6); assert.equal(s.engine.state.decodedByteLimit, 10 * 1024 * 1024);
  s.engine.dispose();
});
test('1835 and 1904 keep four voices / 8MiB and never fetch or sample hoofs', async () => {
  for (const year of ['1835', '1904']) {
    const s = setup(); s.env.time.date = `${year}-07-01`; for (const a of s.env.transport) a.scene = year;
    s.sync(true, year); await settled(s); s.sync(true, year); await settled(s); s.sync(true, year);
    assert.equal(s.engine.state.voices.length, 4); assert.equal(s.fetches, 2);
    const reads = s.reads; s.frame(16, true, year); assert.equal(s.reads, reads);
    assert.equal(s.engine.state.voiceLimit, LIMITS.voices); assert.equal(s.engine.state.decodedByteLimit, LIMITS.decodedBytes);
    s.engine.dispose();
  }
});
test('renderer snow amount changes recorded gain and lowpass, not cadence, pitch or source identity', async () => {
  const dry = hoofSurfaceProfile(0), snow = hoofSurfaceProfile(1);
  assert.equal(dry.lowpassHz, 18000); assert.equal(snow.lowpassHz, 900); assert.equal(snow.gain, .55);
  assert.equal(snow.surface, 'snow-damped-dirt-recording-proxy');
  const s = setup(); s.env.season = 'winter'; s.env.time.date = dates.winter; s.env.snowCover = 1;
  await prime(s); s.move(.22); s.frame(32);
  assert.ok(s.ctx.filters.every(f => f.type === 'lowpass' && f.frequency.value === 900));
  assert.ok(s.engine.state.contacts.every(c => c.snowCover === 1 && c.surface === snow.surface));
  assert.ok(s.ctx.sources.filter(n => n.buffer.duration < 1).every(n => n.playbackRate.value === 1));
  s.engine.dispose();
});
test('stops, hidden actors and changed epochs cancel shots and resume with baseline only', async () => {
  const s = setup(); await prime(s); s.move(.22); s.frame(32); assert.equal(s.engine.state.contactVoices, 2);
  for (const a of s.env.transport) a.moving = false; s.frame(48);
  assert.equal(s.engine.state.contactVoices, 0); assert.equal(s.engine.state.contactTracker.trackedHorses, 0);
  for (const a of s.env.transport) a.moving = true; s.move(.47); s.frame(64); assert.equal(s.engine.state.contactVoices, 0);
  for (const a of s.env.transport) a.anchors.hoof.epoch = 'new-instance'; s.move(.72); s.frame(80);
  assert.equal(s.engine.state.contactVoices, 0); s.engine.dispose();
});
test('paused/zero-time disabled frames skip environment, stop shots and never catch up', async () => {
  const s = setup(); await prime(s); s.move(.22); s.frame(32); const reads = s.reads;
  s.frame(48, false); assert.equal(s.reads, reads); assert.equal(s.engine.state.contactVoices, 0);
  s.move(.72); s.frame(64); assert.equal(s.engine.state.contactVoices, 0);
  s.move(.97); s.frame(300); assert.equal(s.engine.state.contactVoices, 0, 'long elapsed frames are silent');
  s.engine.dispose();
});
test('date change stops current contacts before settings sync and primes the new season silently', async () => {
  const s = setup(); await prime(s); s.move(.22); s.frame(32);
  s.env.season = 'winter'; s.env.time.date = dates.winter; s.env.snowCover = 1; s.frame(48);
  assert.equal(s.engine.state.contactVoices, 0); s.sync(); await settled(s);
  assert.equal(s.engine.state.contactVoices, 0); s.engine.dispose();
});
test('late or failed hoof decode never removes the four existing mechanical voices', async () => {
  let reject;
  const s = setup({ decode: data => data.byteLength > 2 ? new Promise((resolve, fail) => { reject = fail; })
    : Promise.resolve({ duration: 4, length: 192000, sampleRate: 48000, numberOfChannels: 1 }) });
  await mechanicsReady(s); s.frame(0); await waitFor(() => !!reject); s.move(.47); s.frame(16); s.sync();
  assert.equal(s.engine.state.voices.length, 4); assert.equal(s.engine.state.contactVoices, 0);
  reject(Error('fixture failure')); await settled(s); s.frame(32); s.sync();
  assert.equal(s.engine.state.voices.length, 4); assert.equal(s.engine.state.contactDecodedBytes, 0);
  s.engine.dispose();
});
test('one source reservation survives reset; stale decoded data cannot resurrect contacts', async () => {
  let finish, contactsDecoded = 0;
  const s = setup({ decode: data => data.byteLength > 2 ? (contactsDecoded++, new Promise(resolve => { finish = resolve; }))
    : Promise.resolve({ duration: 4, length: 192000, sampleRate: 48000, numberOfChannels: 1 }) });
  await mechanicsReady(s); s.frame(0); await waitFor(() => !!finish);
  s.sync(false); s.sync(); s.frame(16); assert.equal(contactsDecoded, 1); assert.equal(s.engine.state.loading, 1);
  finish(sourceBuffer()); await settled(s); assert.equal(s.engine.state.contactDecodedBytes, 0);
  assert.equal(s.engine.state.contactVoices, 0); s.engine.dispose();
});
test('wrong delivered bytes are rejected before decode', async () => {
  const s = setup({ fetcher: async url => ({ ok: true, arrayBuffer: async () =>
    url.pathname.includes('horse-walking') ? new Uint8Array(R.encodedBytes).buffer : Uint8Array.of(1).buffer }) });
  await mechanicsReady(s); const decoded = s.decodes; s.frame(0); await settled(s);
  assert.equal(s.decodes, decoded); assert.equal(s.engine.state.contactVoices, 0);
  assert.ok(s.engine.state.errors.some(e => e.includes('differs from bounded source'))); s.engine.dispose();
});
test('absent hoof catalog entry and mute never traverse per-frame horse snapshots', async () => {
  const s = setup({ contact: false }); await mechanicsReady(s); const reads = s.reads;
  s.frame(0); s.frame(16, false); assert.equal(s.reads, reads); assert.equal(s.engine.state.voices.length, 4);
  s.engine.dispose();
});

// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { transportCandidates, createTransportAudio, TRANSPORT_AUDIO_LIMITS } from '../renderers/web/js/transport-audio.js';
import { createRecordedAudio } from '../renderers/web/js/recorded-audio.js';
import { circleRoute, createTransportLoop } from '../renderers/web/js/transport-loop.js';
const read = rel => JSON.parse(fs.readFileSync(new URL('../' + rel, import.meta.url)));
const catalog = read('renderers/web/audio/catalog.json'), rows = read('data/transport/driven/loops.json').rows;
const selected = catalog.assets.filter(a => a.runtime_enabled && a.scene_placement?.mode === 'moving-transport');
assert.deepEqual(selected.map(a => a.id).sort(), ['horse-harness', 'wood-wagon']);
for (const a of selected) {
  assert.equal(a.license, 'CC0-1.0');
  assert.deepEqual(a.approved_eras, a.id === 'horse-harness' ? ['1812', '1835', '1904'] : ['1812', '1835']);
  for (const b of a.scene_placement.bindings) {
    if (b.scene === '1812' && b.season) {
      const dates = { spring: '1812-04-15', fall: '1812-10-15', winter: '1812-02-15' };
      assert.equal(b.scene_date, dates[b.season], 'only the existing 1812 seasonal viewing dates are added');
    } else assert.equal(b.scene_date, read(`data/scenes/${b.scene}.json`).target_date);
    assert.deepEqual(b.actor_ids, rows.filter(r => r.scene === b.scene).map(r => r.id));
  }
}
function env(year = '1835') {
  return { camera: { position: { x: 0, y: 2, z: 0 }, quaternion: { x: 0, y: 0, z: 0, w: 1 } },
    time: { date: read(`data/scenes/${year}.json`).target_date },
    transport: rows.filter(r => r.scene === year).map(r => ({ id: r.id, scene: year, moving: true, speed: 1.3,
      anchors: { harness: { x: 3, y: 0, z: 2 }, wagon: { x: 3, y: 0, z: 5 } } })) };
}
{
  assert.equal(transportCandidates(catalog, env('1812'), '1812').length, 4);
  for (const date of ['1812-04-15','1812-10-15','1812-02-15']) {
    const seasonal = env('1812'); seasonal.time.date = date;
    assert.equal(transportCandidates(catalog, seasonal, '1812').length, 4, 'visible seasonal teams retain both mechanical textures');
  }
  const unrelated = env('1812'); unrelated.time.date = '1812-08-15';
  assert.deepEqual(transportCandidates(catalog, unrelated, '1812'), [], 'no battle-day or arbitrary-date transfer');
  assert.equal(transportCandidates(catalog, env('1904'), '1904').length, 1, 'brougham never uses wooden-wagon recording');
  const e = env(), near = transportCandidates(catalog, e, '1835');
  e.camera.position.x = 20;
  assert(transportCandidates(catalog, e, '1835')[0].gain < near[0].gain);
  e.camera.position.y = 100;
  assert.deepEqual(transportCandidates(catalog, e, '1835'), [], 'vertical distance counts');
  for (const mutate of [e => e.time.date = '1835-08-01', e => e.transport = [],
    e => e.transport[0].moving = false, e => e.transport[0].speed = 0,
    e => e.transport[0].anchors = null, e => e.transport[0].id = 'unregistered',
    e => e.transport[0].scene = '1904']) {
    const e = env(); mutate(e); assert.deepEqual(transportCandidates(catalog, e, '1835'), []);
  }
}
{
  let pose, blocked = false;
  const actor = createTransportLoop({ id: 'actual', name: 'Moving team',
    route: circleRoute({ center_enu_m: [100, 200], radius_m: 20 }), speed_m_s: 1.3,
    wheelbase_m: 2, track_m: 1.2, root_ahead_of_rear_axle_m: 1, steering_limit_deg: 12,
    wheel_radii_m: [.7, .7, .5, .5], driver_local_m: [0, 1.58, .65], heightAt: () => 2,
    clear: () => !blocked, stops: [{ distance_m: .2, dwell_s: 2 }],
    assembly: { pose(p) { pose = p; }, audioAnchors: () => ({ wagon: { x: pose.e, y: pose.height, z: -pose.n } }) } });
  assert(!actor.audioState.moving);
  actor.update(.1); assert(actor.audioState.moving); assert.equal(actor.audioState.speed, 1.3);
  assert.equal(actor.audioState.anchors.wagon.x, pose.e);
  actor.update(.1); assert.equal(actor.state, 'moving'); assert(!actor.audioState.moving, 'dwell is quiet despite moving state');
  actor.update(2); actor.update(.1); assert(actor.audioState.moving);
  for (const flags of [{ paused: true }, { reducedMotion: true }, { enabled: false }, { drawn: false }]) {
    actor.update(.1, flags); assert(!actor.audioState.moving); actor.update(.1);
  }
  actor.stop(); assert(!actor.audioState.moving); actor.resume(); actor.update(.1); assert(actor.audioState.moving);
  blocked = true; actor.update(.1); assert(!actor.audioState.moving);
  actor.dispose(); assert(!actor.audioState.moving); assert.equal(actor.audioState.anchors, null);
}
const param = () => ({ value: 0, setValueAtTime(v) { this.value = v; },
  setTargetAtTime(v) { this.value = v; }, linearRampToValueAtTime(v) { this.value = v; } });
function context() {
  const sources = [], pans = [];
  const node = () => ({ connect(to) { this.to = to; }, disconnect() { this.disconnected = true; }, gain: param() });
  const listener = Object.fromEntries(['position', 'forward', 'up'].flatMap(k => ['X', 'Y', 'Z'].map(a => [k + a, param()])));
  return { currentTime: 0, sources, pans, listener, createGain: node,
    createPanner() { const p = { ...node(), positionX: param(), positionY: param(), positionZ: param() }; pans.push(p); return p; },
    createBufferSource() { const s = { ...node(), start(...args) { this.args = args; }, stop(t) { this.stopAt = t ?? 0; } }; sources.push(s); return s; },
    decodeAudioData: async () => buffer() };
}
const buffer = (rate = 48000) => ({ duration: 10, length: 10 * rate, sampleRate: rate, numberOfChannels: 1 });
const flush = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
function fixture({ decode = async () => buffer(), fetcher } = {}) {
  const ctx = context(), e = env('1812'), requests = [], output = ctx.createGain(); let time = 0;
  const engine = createTransportAudio({ ctx, output, catalog: () => catalog, environment: () => e,
    now: () => time, random: () => .5, decodeAudio: decode,
    fetcher: fetcher ?? (async url => { requests.push(String(url)); return { ok: true, arrayBuffer: async () => new ArrayBuffer(0) }; }) });
  const sync = enabled => engine.sync({ enabled, year: '1812' });
  return { ctx, e, engine, requests, output, sync, tick: n => time += n };
}
{
  const f = fixture(); f.sync(false); await flush(); assert.equal(f.requests.length, 0);
  for (let i = 0; i < 4; i++) { f.sync(true); await flush(); }
  assert.equal(f.requests.length, 2); assert.equal(f.engine.state.voices.length, 4);
  assert(f.engine.state.decodedBytes <= TRANSPORT_AUDIO_LIMITS.decodedBytes);
  for (const s of f.ctx.sources) { assert.equal(s.loop, false); assert.equal(s.args[2], 5); assert.equal(s.playbackRate, undefined); }
  assert(f.ctx.pans.every(p => p.to === f.output));
  const before = f.engine.state.sources[0].gain;
  f.e.transport[0].anchors.harness.x = 15; f.sync(true);
  assert(f.ctx.pans.some(p => p.positionX.value === 15), 'panner follows source');
  f.engine.setDuck(.3); assert(f.engine.state.sources.every(c => c.gain < before));
  f.e.transport = []; f.sync(true); assert(f.ctx.sources.every(s => s.stopAt === .08));
  for (const s of f.ctx.sources) s.onended?.();
  assert.equal(f.engine.state.voices.length, 0);
  f.sync(false); assert.equal(f.engine.state.decodedBytes, 0); f.engine.dispose();
}
{
  let resolve, decodes = 0;
  const f = fixture({ decode: () => { decodes++; return new Promise(r => resolve = r); } });
  f.sync(true); await flush(); assert.equal(decodes, 1);
  f.sync(false); f.sync(true); await flush(); assert.equal(decodes, 1, 'uncancellable decode slot survives mute');
  resolve(buffer()); await flush(); assert.equal(f.engine.state.decodedBytes, 0); assert.equal(f.ctx.sources.length, 0);
  f.sync(true); await flush(); assert.equal(decodes, 2);
  f.engine.dispose(); resolve(buffer()); await flush(); assert.equal(f.engine.state.decodedBytes, 0);
}
{
  const f = fixture({ decode: async () => buffer(192000) });
  for (let i = 0; i < 4; i++) { f.sync(true); await flush(); }
  assert.equal(f.ctx.sources.length, 0); assert.equal(f.engine.state.decodedBytes, 0);
  assert.equal(f.engine.state.errors.length, 2); f.engine.dispose();
}
{
  // Shared mixer: Effects alone must fetch/play and position the listener, while
  // habitat, environmental loops and music remain off. Mute retires everything.
  const ctx = context(), e = env(), requests = [];
  e.camera.position.x = 1;
  const engine = createRecordedAudio({ ctx, effects: ctx.createGain(), ambience: ctx.createGain(), music: ctx.createGain(),
    environment: () => e, fetcher: async url => { requests.push(String(url)); return { ok: true, json: async () => catalog, arrayBuffer: async () => new ArrayBuffer(0) }; } });
  const sync = active => engine.sync({ active, effectsOn: true, ambienceOn: false, musicOn: false, year: '1835' });
  sync(false); await flush(); assert.equal(requests.length, 0);
  for (let i = 0; i < 5; i++) { sync(true); await flush(); }
  assert.equal(engine.state.voices.length, 2); assert.equal(requests.length, 3);
  assert.equal(ctx.listener.positionX.value, 1); assert.equal(engine.state.habitat.voices.length, 0);
  engine.sync({ active: true, effectsOn: false, ambienceOn: false, musicOn: false, year: '1835' });
  assert.equal(engine.state.transport.voices.length, 0); assert.equal(engine.state.transport.decodedBytes, 0);
  for (let i = 0; i < 4; i++) { sync(true); await flush(); }
  assert.equal(engine.state.transport.voices.length, 2, 'Effects can be re-enabled independently');
  sync(false); assert.equal(engine.state.voices.length, 0); assert.equal(engine.state.decodedBytes, 0); engine.dispose();
}
console.log('TRANSPORT AUDIO PASS: dated actual actors, movement/dwell/holds, distance/pan, effects-only, four voices, two buffers, stale decode, mute and disposal');

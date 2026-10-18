#!/usr/bin/env node
/**
 * T-2659 (NAV-S01, DESIGN §13 "Sound") — the Navigator's sounds, against a fake AudioContext:
 * the ticker's ticks capped at 12 a second, nothing before the gesture gate has a context,
 * Master at 0 is silence with no node started, a hidden tab stops the hum and the ambience,
 * Settings › Sound's three levels reach the graph, each destination its own bed tone, and the
 * module is fetched after the boot (main.js imports it dynamically) with no audio file anywhere.
 *
 *   node tools/test_sound.mjs
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  createSound, createTickCap, digitsChanged, mayStartEarly, ambienceFor, curve, AMBIENCE,
  TICK_CAP, RELAY_GAP_MS,
} from '../renderers/web/js/sound.js';
import { createJourney } from '../renderers/web/js/journey.js';
import { createGestureGate } from '../renderers/web/js/gesture-gate.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = path.join(ROOT, 'renderers/web');

// ---- a fake Web Audio graph: every node made, every source started and stopped ----------
class Param {
  constructor(v = 0) { this.value = v; this.target = v; }
  setValueAtTime(v) { this.value = v; return this; }
  linearRampToValueAtTime(v) { this.value = v; return this; }
  exponentialRampToValueAtTime(v) { this.value = v; return this; }
  setTargetAtTime(v) { this.target = v; this.value = v; return this; }
  cancelScheduledValues() { return this; }
}
class Node {
  constructor(ctx, kind) { this.ctx = ctx; this.kind = kind; this.out = []; ctx.made.push(this); }
  connect(to) { this.out.push(to); return to; }
  disconnect() { this.out = []; }
}
class Source extends Node {
  start(at) { this.started = at ?? 0; this.ctx.started.push(this); }
  stop(at) { this.stopped = at ?? 0; }
}
class FakeContext {
  constructor() {
    this.made = []; this.started = []; this.listeners = {};
    this.state = 'suspended'; this.currentTime = 0; this.sampleRate = 8000;
    this.destination = { kind: 'destination' };
    FakeContext.last = this;
  }
  createGain() { const n = new Node(this, 'gain'); n.gain = new Param(1); return n; }
  createBiquadFilter() { const n = new Node(this, 'filter'); n.frequency = new Param(350); n.Q = new Param(1); n.type = 'lowpass'; return n; }
  createConvolver() { return new Node(this, 'convolver'); }
  createOscillator() { const n = new Source(this, 'osc'); n.frequency = new Param(440); n.type = 'sine'; return n; }
  createBufferSource() { return new Source(this, 'buffer'); }
  createBuffer(channels, length, rate) {
    const data = Array.from({ length: channels }, () => new Float32Array(length));
    return { numberOfChannels: channels, length, sampleRate: rate, duration: length / rate, getChannelData: (c) => data[c] };
  }
  addEventListener(type, fn) { (this.listeners[type] ??= []).push(fn); }
  resume() { this.setState('running'); return Promise.resolve(); }
  setState(s) { this.state = s; for (const fn of this.listeners.statechange ?? []) fn(); }
}
const near = (a, b) => Math.abs(a - b) < 1e-3;
const sources = (ctx, kind) => ctx.started.filter((n) => !kind || n.kind === kind);

function fakeDoc({ transfer = false } = {}) {
  const listeners = {};
  return {
    visibilityState: 'visible', hidden: false,
    documentElement: { dataset: transfer ? { transfer: 'true' } : {} },
    addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
    removeEventListener(type, fn) { listeners[type] = (listeners[type] ?? []).filter((f) => f !== fn); },
    fire(type, event = {}) { for (const fn of listeners[type] ?? []) fn({ type, ...event }); },
    count: (type) => (listeners[type] ?? []).length,
  };
}
const fakeNav = () => {
  const fns = new Set();
  return { app: 'home', level: 0, onChange(fn) { fns.add(fn); return () => fns.delete(fn); },
    set(app, level) { this.app = app; this.level = level; for (const fn of fns) fn({ app, level }); } };
};
const button = (inside) => ({ closest: (sel) => (sel.includes(inside) ? {} : null) });

/** A landed page whose first tap has made and resumed a running context. */
function landed({ settings = {}, scene = '1835', doc = fakeDoc(), nav = fakeNav() } = {}) {
  const journey = createJourney({ root: null });
  journey.land(); journey.landed();
  const ctx = new FakeContext();
  ctx.state = 'running';
  let t = 0;
  const clock = { now: () => t, advance: (ms) => { t += ms; } };
  const sound = createSound({ audio: () => ctx, journey, settings: () => settings, scene: () => scene,
    navigator: () => nav, doc, now: clock.now, storage: null });
  return { sound, ctx, journey, doc, nav, clock, settings };
}

// ---- the arithmetic: digits flipped, the 12-a-second cap, the curve ----------------------
{
  assert.equal(digitsChanged(1905, 1904), 1);
  assert.equal(digitsChanged(1910, 1909), 2);
  assert.equal(digitsChanged(2000, 1999), 4, 'every digit of 2000 → 1999 flips');
  assert.equal(digitsChanged(1835, 1835), 0);
  const cap = createTickCap();
  let let1 = 0;
  for (let i = 0; i < 40; i++) if (cap.allow(i * 10)) let1++;
  assert.equal(let1, TICK_CAP, '40 ticks in 400 ms: twelve sound');
  assert.equal(cap.allow(999), false, 'still inside the second of the first tick');
  assert.equal(cap.allow(1000), true, 'a second after the first, one more');
  assert.equal(curve(1), 1); assert.equal(curve(0.5), 0.25); assert.equal(curve(0), 0); assert.equal(curve('x'), 0);
}

// ---- the ticker: a tick per flipped digit, never more than 12 in any second -------------
{
  const { sound, ctx, clock } = landed();
  const before = sources(ctx, 'buffer').length;
  assert.equal(sound.ticker(2026), 0, 'the first year shown only sets the ticker');
  assert.equal(sound.ticker(2026), 0, 'the same year again is no flip');
  assert.equal(sound.ticker(2025), 1, 'one digit, one tick');
  assert.equal(sources(ctx, 'buffer').length, before + 1);
  // The ticker racing: a year a frame for half a second (30 frames, many digits).
  let played = 1;
  for (let y = 2024, i = 0; i < 30; i++, y--) { clock.advance(16); played += sound.ticker(y); }
  assert.equal(played, TICK_CAP, `a racing ticker sounds ${TICK_CAP} ticks in its first second, not ${played}`);
  assert.ok(sound.state.dropped > 0, 'the rest are dropped, not queued');
  // Any one-second window holds at most twelve tick starts.
  const times = [];
  const { sound: s2, clock: c2 } = landed();
  s2.ticker(2100);
  for (let y = 2099; y > 1835; y--) { c2.advance(7 + (y % 5) * 9); const n = s2.ticker(y); for (let k = 0; k < n; k++) times.push(c2.now() + k * 18); }
  for (let i = 0; i < times.length; i++) {
    const inWindow = times.filter((t) => t >= times[i] && t < times[i] + 1000).length;
    assert.ok(inWindow <= TICK_CAP, `${inWindow} ticks in the second from ${times[i]} ms`);
  }
  // A call that makes no sound allocates no node.
  const made = ctx.made.length;
  sound.ticker(1900); sound.ticker(1900);
  assert.equal(ctx.made.length, made, 'the same year twice makes no node');
}

// ---- the gesture gate: no context, no sound; the first tap makes one ---------------------
{
  const journey = createJourney({ root: null });
  const target = { listeners: {}, addEventListener(type, fn) { (this.listeners[type] ??= []).push(fn); } };
  const gate = createGestureGate({ target, journey, AudioContext: FakeContext });
  const doc = fakeDoc();
  const sound = createSound({ audio: () => gate.audio, journey, settings: () => ({}), scene: () => '1904', doc, storage: null });
  for (let y = 2026; y > 2000; y--) sound.ticker(y);
  assert.equal(gate.audio, null, 'no context before the first gesture');
  assert.equal(sound.state.context, 'none');
  assert.equal(sound.state.ticks, 0, 'the ticker is silent with no context');
  assert.ok(sound.state.held > 0, 'its flips are counted as held, not played later');
  journey.land();
  assert.equal(sound.state.clunks, 0, 'the landing, with no context, owes its clunk');
  assert.equal(sound.state.clunkOwed, true);
  journey.landed();
  // The first trusted tap on the scene: the gate makes and resumes the context.
  const tap = { type: 'pointerup', isTrusted: true, target: { closest: () => ({}) } };
  for (const fn of target.listeners.pointerup) fn(tap);
  assert.ok(gate.audio, 'the tap made the context');
  sound.sync();
  await Promise.resolve();
  assert.equal(gate.audio.state, 'running');
  assert.equal(sound.state.clunks, 1, 'the owed clunk plays as the tap lets audio run');
  assert.equal(sound.state.ambience, '1904', 'and the destination\'s bed tone starts');
  // An untrusted (scripted) click is never a gesture.
  const g2 = createGestureGate({ target: { addEventListener(t, fn) { this[t] = fn; } }, journey, AudioContext: FakeContext });
  g2.handle({ type: 'click', isTrusted: false, target: { closest: () => ({}) } });
  assert.equal(g2.audio, null);
}

// ---- a suspended context: nothing queues up, the clunk waits for it to run -------------
{
  const journey = createJourney({ root: null });
  const ctx = new FakeContext(); // suspended
  const sound = createSound({ audio: () => ctx, journey, settings: () => ({}), scene: () => '1835', doc: fakeDoc(), storage: null });
  sound.ticker(2026); sound.ticker(2025); sound.ticker(2024);
  assert.equal(sound.state.ticks, 0, 'no tick is scheduled on a context that is not running');
  journey.land();
  assert.equal(sound.state.clunks, 0);
  ctx.setState('running');
  assert.equal(sound.state.clunks, 1, 'the clunk plays once the context runs');
  journey.landed(); journey.explore();
  assert.equal(sound.state.clunks, 1, 'and only once');
}

// ---- the early start: only where the browser says, or after a tapped jump --------------
{
  assert.equal(mayStartEarly({ nav: { getAutoplayPolicy: () => 'allowed' } }), true);
  assert.equal(mayStartEarly({ nav: { getAutoplayPolicy: () => 'disallowed' }, transfer: true }), false, 'the browser\'s answer wins');
  assert.equal(mayStartEarly({ nav: { getAutoplayPolicy: () => { throw new TypeError('x'); } }, transfer: true }), true);
  assert.equal(mayStartEarly({ nav: {}, transfer: true }), true, 'a jump tapped on this site');
  assert.equal(mayStartEarly({ nav: {}, transfer: false }), false, 'a cold visit waits for a tap');
  let unlocked = 0;
  createSound({ early: true, unlock: () => unlocked++, journey: createJourney({ root: null }), doc: fakeDoc({ transfer: false }), storage: null });
  assert.equal(unlocked, 0, 'no context is made early on a cold visit');
  createSound({ early: true, unlock: () => unlocked++, journey: createJourney({ root: null }), doc: fakeDoc({ transfer: true }), storage: null });
  assert.equal(unlocked, 1, 'a page opened by a tapped jump makes it on the way in');
}

// ---- Master at 0 is silence: no gain, no node started ---------------------------------
{
  const { sound, ctx, nav } = landed({ settings: { soundMaster: 0, soundEffects: 1, soundAmbience: 1 } });
  assert.ok(near(sound.state.gains.master, 0), 'master gain is 0');
  assert.equal(sound.state.silent, true);
  const started = ctx.started.length;
  sound.ticker(2026); sound.ticker(2025); sound.relay(); sound.land();
  nav.set('settings', 1);
  assert.equal(ctx.started.length, started, 'nothing at all is started with Master at 0');
  assert.equal(sound.state.hum, false, 'no hum');
  assert.equal(sound.state.ambience, null, 'no bed tone');
  assert.equal(sound.state.ticks + sound.state.clicks + sound.state.clunks, 0);
}

// ---- Settings › Sound's levels reach the graph, live ----------------------------------
{
  const settings = { soundMaster: 0.8, soundEffects: 0.5, soundAmbience: 0.25 };
  const { sound, ctx } = landed({ settings });
  const master = ctx.made.find((n) => n.kind === 'gain' && n.out.includes(ctx.destination));
  assert.ok(master, 'a master gain feeds the destination');
  assert.ok(near(sound.state.gains.master, curve(0.8)));
  assert.ok(near(sound.state.gains.effects, curve(0.5)));
  assert.ok(near(sound.state.gains.ambience, curve(0.25)));
  assert.equal(sound.nodes.master, master);
  settings.soundEffects = 1; sound.setting('soundEffects');
  assert.ok(near(sound.state.gains.effects, 1), 'a slider move is applied at once');
  settings.soundMaster = 0.1; sound.setting('fov');
  assert.ok(near(sound.state.gains.master, curve(0.8)), 'another setting is not a sound setting');
  sound.setting('soundMaster');
  assert.ok(near(sound.state.gains.master, curve(0.1)));
  // Ambience to 0 stops the bed; back up starts it again.
  assert.equal(sound.state.ambience, '1835');
  settings.soundAmbience = 0; sound.setting('soundAmbience');
  assert.equal(sound.state.ambience, null, 'Ambience at Off stops the bed tone');
  settings.soundAmbience = 1; sound.setting('soundAmbience');
  assert.equal(sound.state.ambience, '1835');
  // Effects at 0: no ticks, clicks or hum.
  settings.soundEffects = 0; sound.setting('soundEffects');
  const n = ctx.started.length;
  sound.ticker(2026); sound.ticker(2025); sound.relay();
  assert.equal(ctx.started.length, n, 'Effects at Off plays no effect');
  // Before the HUD has read them, the stored levels are used.
  const store = { getItem: () => JSON.stringify({ soundMaster: 0.5 }) };
  const ctx2 = new FakeContext(); ctx2.state = 'running';
  const early = createSound({ audio: () => ctx2, journey: createJourney({ root: null }), settings: () => null, storage: store, doc: fakeDoc() });
  assert.ok(near(early.state.gains.master, 0.25), 'the stored Master is heard on the way in');
}

// ---- a hidden tab stops the hum and the ambience, and they come back -------------------
{
  const { sound, doc, nav, ctx } = landed();
  nav.set('home', 1);
  assert.equal(sound.state.hum, true, 'the Navigator open hums');
  assert.equal(sound.state.ambience, '1835');
  const running = ctx.started.filter((n) => n.stopped == null).length;
  assert.ok(running >= 5, 'the hum and the bed are running voices');
  doc.visibilityState = 'hidden'; doc.hidden = true; doc.fire('visibilitychange');
  assert.equal(sound.state.hum, false, 'hidden: no hum');
  assert.equal(sound.state.ambience, null, 'hidden: no bed');
  assert.equal(ctx.started.filter((n) => n.stopped == null).length, 0, 'every continuous voice is stopped');
  const n = ctx.started.length;
  sound.relay(); sound.ticker(2026); sound.ticker(2025);
  assert.equal(ctx.started.length, n, 'and no one-shot plays to a hidden tab');
  doc.visibilityState = 'visible'; doc.hidden = false; doc.fire('visibilitychange');
  assert.equal(sound.state.hum, true, 'seen again: the hum is back');
  assert.equal(sound.state.ambience, '1835');
}

// ---- the Navigator: relay clicks on its keys and its switches, a hum while open -------
{
  const { sound, doc, nav, clock } = landed();
  assert.equal(sound.state.hum, false, 'docked: no hum');
  nav.set('home', 1);
  assert.equal(sound.state.clicks, 1, 'opening is a relay click');
  assert.equal(sound.state.hum, true);
  clock.advance(RELAY_GAP_MS + 1);
  doc.fire('click', { target: button('#navigator') });
  nav.set('settings', 1);
  assert.equal(sound.state.clicks, 2, 'a rail tap (its click and its switch at once) is one click');
  clock.advance(RELAY_GAP_MS + 1);
  doc.fire('click', { target: button('#welcome') });
  assert.equal(sound.state.clicks, 3, 'a Home choice clicks');
  clock.advance(RELAY_GAP_MS + 1);
  doc.fire('click', { target: button('#hud-elsewhere') });
  assert.equal(sound.state.clicks, 3, 'a press outside the device does not');
  clock.advance(RELAY_GAP_MS + 1);
  nav.set('settings', 0);
  assert.equal(sound.state.hum, false, 'docked again: the hum stops');
  assert.equal(sound.state.clicks, 4);
  // Recall: the page is leaving; the bed stops.
  const { sound: s2, journey } = landed();
  journey.recall();
  assert.equal(s2.state.ambience, null);
  sound.dispose();
  assert.equal(doc.count('click') + doc.count('visibilitychange'), 0, 'dispose lets go of the page');
}

// ---- each destination its own bed tone; none is a recording ----------------------------
{
  assert.notDeepEqual(ambienceFor('1904'), ambienceFor('1835'));
  assert.notDeepEqual(ambienceFor('1812'), ambienceFor('1835'));
  assert.equal(ambienceFor('1904-07-01'), AMBIENCE[1904]);
  assert.equal(ambienceFor('1880'), AMBIENCE[1835], 'a year without its own tone has the default');
  const { ctx } = landed({ scene: '1904' });
  const band = ctx.made.find((n) => n.kind === 'filter' && n.type === 'bandpass' && n.frequency.value === AMBIENCE[1904].band);
  assert.ok(band, '1904 plays its own band');
  const loop = ctx.started.find((n) => n.kind === 'buffer' && n.loop);
  assert.ok(loop, 'its noise loops, made in the page, not fetched');
}

// ---- the page: hooks of one call, the module after the boot, no audio file -------------
{
  const main = fs.readFileSync(path.join(WEB, 'js/main.js'), 'utf8');
  assert.doesNotMatch(main, /^import[^;]*'\.\/sound\.js'/m, 'sound.js is not in the boot payload (no static import)');
  assert.match(main, /import\('\.\/sound\.js'\)/, 'main.js fetches it when there is audio to play');
  assert.match(main, /onYear: year => \{[^}]*api\.sound\?\.ticker\(year\);/, 'the ticker tells the sound each year');
  assert.match(main, /onSetting: \(key, value\) => \{\s*api\.sound\?\.setting\(key\);/, 'every setting reaches the sound');
  assert.match(main, /onGesture: \(\) => \{ void loadSound\(\)/, 'the first gesture loads it');
  const sound = fs.readFileSync(path.join(WEB, 'js/sound.js'), 'utf8');
  assert.doesNotMatch(sound, /new\s+(window\.)?(webkit)?AudioContext|fetch\(|decodeAudioData|new Audio\(/, 'sound.js makes no context and fetches nothing');
  const audioFiles = [];
  const walk = (dir) => { for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    if (e.isDirectory()) { if (!['node_modules', 'vendor'].includes(e.name)) walk(path.join(dir, e.name)); }
    else if (/\.(mp3|ogg|oga|wav|m4a|aac|flac|opus|weba)$/i.test(e.name)) audioFiles.push(path.join(dir, e.name));
  } };
  walk(WEB);
  assert.deepEqual(audioFiles, [], 'every sound is synthesized: no audio file under renderers/web');
  const libs = fs.readFileSync(path.join(ROOT, 'docs/LIBERTIES.md'), 'utf8');
  assert.ok(libs.includes('### L-ambience-2659 '), 'the ambience is recorded as a liberty');
  const strings = fs.readFileSync(path.join(WEB, 'js/strings/settings.js'), 'utf8');
  assert.ok(strings.includes('not a recording of the past'), 'Settings › Sound says the ambience is no recording');
}

console.log('SOUND PASS — a tick per flipped digit, at most 12 a second; nothing before the first gesture, the owed clunk at it; '
  + 'Master at 0 starts nothing; the three levels reach the graph live; a hidden tab stops the hum and the bed; '
  + 'relay clicks on the device, a hum while open; a bed tone per destination; loaded after the boot, no audio file');

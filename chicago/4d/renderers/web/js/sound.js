/**
 * T-2659 (NAV-S01; DESIGN §13 "Sound"): the Navigator's sounds, on by default (owner ruling,
 * 2026-10-16), every one of them made here with the Web Audio API — oscillators, one buffer of
 * noise and envelopes. There is no audio file to fetch, source or license.
 *
 *   ticker    a soft flap tick for each digit of the year that changes as the arrival's
 *             ticker rolls, never more than 12 in any second (TICK_CAP)
 *   landing   a low clunk with a short reverb tail as the last digit drops into place
 *   relay     a relay's click-clack on a Navigator key, a rail tap or an app switch
 *   hum       a low mains hum while the Navigator is open
 *   ambience  a quiet bed tone for each destination
 *
 * The ambience is NOT a recording of the past and does not pretend to be one: it is a band of
 * filtered noise and two soft drone notes, pitched differently for each destination so 1812,
 * 1835 and 1904 each have their own mood. No birds, wagons or bells are imitated, and nothing
 * here is a claim about how a place sounded (docs/LIBERTIES.md, L-ambience-2659).
 *
 * The browser's rules come first. The page's one AudioContext is the gesture gate's
 * (gesture-gate.js, T-2614): it exists after the visitor's first tap, or — `mayStartEarly` —
 * when the jump that opened this page was itself a tap the browser honours, so the ticker can
 * be heard on the way in. A one-shot plays only on a running context, so nothing queued while
 * audio was held back bursts out when it is let go; the landing's clunk, if the landing came
 * before audio was allowed, waits and plays at the first tap instead. Settings › Sound's three
 * levels (settings-app.js) are read live: Master at 0 is silence, and no node is even started
 * for a sound nobody can hear. The hum and the ambience stop while the tab is hidden and come
 * back with it.
 *
 * Reduced motion: the design ties none of these sounds to it. Under reduced motion the ticker
 * rolls in five steps (arrival.js reducedProgress), so it ticks five times, on those steps.
 *
 * Nothing here runs per frame. The ticker is told each year as it is shown (main.js onYear),
 * and it counts changed digits with arithmetic, so a call that makes no sound allocates nothing.
 */
import { SOUND_DEFAULTS, normalVolume } from './settings-app.js';

/** At most this many ticks in any one second (DESIGN §13). */
export const TICK_CAP = 12;
/** The gap between the ticks of digits that flip together, so four flips read as four. */
export const TICK_STAGGER_S = 0.018;
/** Relay clicks closer together than this are one click (a rail tap is a click AND a switch). */
export const RELAY_GAP_MS = 45;
/** The hum and the ambience fade in and out over the sheet's own 280 ms (DESIGN §13). */
export const FADE_S = 0.28;

/** The journey's states in which the visitor is at the destination (journey.js). */
const AT_DESTINATION = Object.freeze(['landed', 'exploring', 'inspecting', 'on-jaunt', 'touring']);
const LANDED = Object.freeze(['landing', ...AT_DESTINATION]);
/** What a press may land on to click the relay: the Navigator's controls and Home's choices. */
export const RELAY_TARGETS = '#navigator :is(button, [role="tab"], [role="button"]), #welcome button';

/**
 * Each destination's bed tone: a band of noise (`band` Hz, `q`) swaying slowly (`sway` Hz)
 * under two drone notes (`drone` Hz). Mood, chosen for each place; never a recording.
 */
export const AMBIENCE = Object.freeze({
  1812: Object.freeze({ band: 300, q: 0.6, sway: 0.06, drone: Object.freeze([49, 73.5]), noise: 0.05, tone: 0.012 }),
  1835: Object.freeze({ band: 520, q: 0.7, sway: 0.08, drone: Object.freeze([65.4, 98]), noise: 0.045, tone: 0.011 }),
  1904: Object.freeze({ band: 820, q: 0.5, sway: 0.11, drone: Object.freeze([73.4, 110]), noise: 0.04, tone: 0.01 }),
});
export const AMBIENCE_DEFAULT = AMBIENCE[1835];
export function ambienceFor(scene) {
  const year = /^(\d{4})/.exec(String(scene ?? ''))?.[1];
  return AMBIENCE[year] ?? AMBIENCE_DEFAULT;
}

/** A slider's 0..1 as a gain: squared, so the travel of the slider sounds even. */
export function curve(v) {
  const n = normalVolume(v, 0);
  return n * n;
}

/** How many of the four digits differ between two years — arithmetic, no strings. */
export function digitsChanged(a, b) {
  let n = 0;
  let x = Math.abs(Math.trunc(a)), y = Math.abs(Math.trunc(b));
  for (let k = 0; k < 4; k++) {
    if (x % 10 !== y % 10) n++;
    x = Math.floor(x / 10);
    y = Math.floor(y / 10);
  }
  return n;
}

/**
 * The 12-a-second cap as a ring of the last TICK_CAP tick times: a tick at `at` (ms) is let
 * through only when the oldest of the last twelve is a full second behind it.
 */
export function createTickCap(cap = TICK_CAP, windowMs = 1000) {
  const ring = new Float64Array(cap).fill(-Infinity);
  let head = 0;
  return {
    allow(at) {
      if (at - ring[head] < windowMs) return false;
      ring[head] = at;
      head = (head + 1) % cap;
      return true;
    },
  };
}

/**
 * Should the page make its AudioContext before a tap? Only where the browser says it will
 * run one (`navigator.getAutoplayPolicy`), or, where it cannot say, when this page was opened
 * by a jump the visitor tapped on this site (the Observatory's or the Jump app's transfer,
 * <html data-transfer>, skin.js) — the activation a same-site jump carries over.
 */
export function mayStartEarly({ nav = globalThis.navigator, transfer = false } = {}) {
  try {
    const policy = nav?.getAutoplayPolicy?.('audiocontext');
    if (policy) return policy === 'allowed';
  } catch { /* an engine that does not know the question */ }
  return !!transfer;
}

/** The stored levels, for a sound made before the HUD has read them (the ticker on the way in). */
function storedLevels(storage) {
  try { return JSON.parse(storage?.getItem?.('chicago4d.settings') || '{}') ?? {}; } catch { return {}; }
}

export function createSound({
  audio = () => null,
  unlock = null,
  early = false,
  journey = null,
  settings = () => null,
  storage = (() => { try { return globalThis.localStorage; } catch { return null; } })(),
  scene = () => '',
  navigator: navigatorOf = () => null,
  doc = globalThis.document ?? null,
  now = () => (globalThis.performance?.now?.() ?? Date.now()),
  random = Math.random,
  later = (fn, ms) => setTimeout(fn, ms),
} = {}) {
  let ctx = null;
  let master = null, effects = null, bed = null, tickBand = null, impulse = null;
  let noise = null;
  let hum = null, amb = null, ambScene = null;
  let navOpen = false, navApp = null, navLevel = 0, unNav = null;
  let lastYear = null;
  let clunkOwed = false, clunked = false;
  let lastRelay = -Infinity;
  const cap = createTickCap();
  const counts = { ticks: 0, dropped: 0, clunks: 0, clicks: 0, held: 0 };
  const level = { master: 1, effects: 1, ambience: 1 };

  const hidden = () => doc?.visibilityState === 'hidden' || doc?.hidden === true;
  const running = () => !!ctx && ctx.state === 'running';
  const atDestination = () => AT_DESTINATION.includes(journey?.state ?? 'landed');

  function readLevels() {
    const s = settings?.() ?? storedLevels(storage);
    level.master = normalVolume(s?.soundMaster, SOUND_DEFAULTS.soundMaster);
    level.effects = normalVolume(s?.soundEffects, SOUND_DEFAULTS.soundEffects);
    level.ambience = normalVolume(s?.soundAmbience, SOUND_DEFAULTS.soundAmbience);
  }
  const effectsOn = () => level.master > 0 && level.effects > 0;
  const ambienceOn = () => level.master > 0 && level.ambience > 0;

  function glide(param, value, at = ctx.currentTime, tau = 0.04) {
    param.cancelScheduledValues(at);
    param.setTargetAtTime(value, at, tau);
  }

  /** The graph, made once on the page's context: master ← effects (with a reverb send) and bed. */
  function graph() {
    const c = audio?.() ?? null;
    if (!c) return false;
    if (c === ctx) return true;
    ctx = c;
    try { if (globalThis.navigator?.audioSession) globalThis.navigator.audioSession.type = 'ambient'; } catch { /* Safari only */ }
    master = ctx.createGain();
    master.connect(ctx.destination);
    effects = ctx.createGain();
    effects.connect(master);
    bed = ctx.createGain();
    bed.connect(master);
    tickBand = ctx.createBiquadFilter();
    tickBand.type = 'bandpass';
    tickBand.frequency.value = 2400;
    tickBand.Q.value = 1.4;
    tickBand.connect(effects);
    // One buffer of noise (a quarter second) serves every tick, click and thump.
    const n = Math.max(1, Math.round(ctx.sampleRate * 0.25));
    noise = ctx.createBuffer(1, n, ctx.sampleRate);
    const data = noise.getChannelData(0);
    for (let i = 0; i < n; i++) data[i] = random() * 2 - 1;
    for (const p of [master.gain, effects.gain, bed.gain]) p.value = 0;
    ctx.addEventListener?.('statechange', sync);
    apply();
    return true;
  }

  /** The reverb, for one landing: a convolver on 1.1 s of decaying noise (the impulse made
   * once), let go once its tail has rung out, so nothing convolves silence afterwards. */
  function reverb() {
    const sr = ctx.sampleRate, len = Math.max(1, Math.round(sr * 1.1));
    if (!impulse) {
      impulse = ctx.createBuffer(2, len, sr);
      for (let ch = 0; ch < 2; ch++) {
        const d = impulse.getChannelData(ch);
        for (let i = 0; i < len; i++) d[i] = (random() * 2 - 1) * (1 - i / len) ** 3;
      }
    }
    const verb = ctx.createConvolver();
    verb.buffer = impulse;
    verb.connect(effects);
    const send = ctx.createGain();
    send.gain.value = 0.35;
    send.connect(verb);
    later(() => { try { send.disconnect(); verb.disconnect(); } catch { /* gone */ } }, 1800);
    return send;
  }

  /** A burst of the noise buffer through `into`, shaped by an attack/decay envelope. */
  function burst(into, at, peak, decay, duration = decay * 3) {
    const src = ctx.createBufferSource();
    src.buffer = noise;
    const env = ctx.createGain();
    env.gain.setValueAtTime(0, at);
    env.gain.linearRampToValueAtTime(peak, at + 0.002);
    env.gain.exponentialRampToValueAtTime(0.0001, at + decay);
    src.connect(env);
    env.connect(into);
    const offset = random() * Math.max(0, noise.duration - duration);
    src.start(at, offset, duration);
    src.stop(at + duration + 0.01);
    return src;
  }

  /** A one-shot may sound: the context runs, the tab is seen, and effects are up. */
  const mayPlay = () => running() && !hidden() && effectsOn();

  function tick(at) {
    burst(tickBand, at, 0.22, 0.03, 0.04);
  }

  /** The landing: a low clunk falling in pitch, a thump, a latch, and a short reverb tail. */
  function clunk() {
    if (!graph()) { clunkOwed = true; return false; }
    if (!mayPlay()) { clunkOwed = true; return false; }
    clunkOwed = false;
    clunked = true;
    counts.clunks++;
    const at = ctx.currentTime + 0.005;
    const tail = reverb();
    const body = ctx.createOscillator();
    body.type = 'sine';
    body.frequency.setValueAtTime(96, at);
    body.frequency.exponentialRampToValueAtTime(42, at + 0.2);
    const env = ctx.createGain();
    env.gain.setValueAtTime(0, at);
    env.gain.linearRampToValueAtTime(0.6, at + 0.004);
    env.gain.exponentialRampToValueAtTime(0.0001, at + 0.38);
    body.connect(env);
    env.connect(effects);
    env.connect(tail);
    body.start(at);
    body.stop(at + 0.42);
    const low = ctx.createBiquadFilter();
    low.type = 'lowpass';
    low.frequency.value = 520;
    low.connect(effects);
    low.connect(tail);
    burst(low, at, 0.5, 0.09, 0.12);
    const latch = ctx.createBiquadFilter();
    latch.type = 'bandpass';
    latch.frequency.value = 1700;
    latch.Q.value = 5;
    latch.connect(effects);
    burst(latch, at + 0.012, 0.18, 0.05, 0.06);
    return true;
  }

  /** A relay: a click and its clack 14 ms later, with a little ring in it. */
  function relay() {
    const t = now();
    if (t - lastRelay < RELAY_GAP_MS) return false;
    lastRelay = t;
    if (!graph() || !mayPlay()) return false;
    counts.clicks++;
    const at = ctx.currentTime + 0.002;
    burst(tickBand, at, 0.16, 0.012, 0.015);
    burst(tickBand, at + 0.014, 0.09, 0.01, 0.012);
    const ring = ctx.createOscillator();
    ring.type = 'triangle';
    ring.frequency.value = 1320;
    const env = ctx.createGain();
    env.gain.setValueAtTime(0, at);
    env.gain.linearRampToValueAtTime(0.03, at + 0.002);
    env.gain.exponentialRampToValueAtTime(0.0001, at + 0.03);
    ring.connect(env);
    env.connect(effects);
    ring.start(at);
    ring.stop(at + 0.04);
    return true;
  }

  // ---- the continuous voices: the hum and the bed ------------------------------------
  function voice(into, parts) {
    const out = ctx.createGain();
    out.gain.value = 0;
    out.connect(into);
    const nodes = [];
    for (const make of parts) nodes.push(...make(out));
    for (const n of nodes) n.start?.(ctx.currentTime);
    glide(out.gain, 1, ctx.currentTime, FADE_S / 3);
    return { out, nodes };
  }
  function silence(v) {
    if (!v) return null;
    const at = ctx.currentTime;
    glide(v.out.gain, 0, at, FADE_S / 4);
    for (const n of v.nodes) { try { n.stop?.(at + FADE_S + 0.05); } catch { /* already stopped */ } }
    // Once its sources have ended, the voice lets go of the bus, so a tab hidden and shown
    // many times leaves nothing behind.
    if (v.nodes[0]) v.nodes[0].onended = () => { try { v.out.disconnect(); } catch { /* gone */ } };
    return null;
  }
  function osc(type, freq, gain, into, filter = null) {
    const o = ctx.createOscillator();
    o.type = type;
    o.frequency.value = freq;
    const g = ctx.createGain();
    g.gain.value = gain;
    o.connect(g);
    g.connect(filter ?? into);
    return o;
  }
  function startHum() {
    return voice(effects, [(out) => {
      const low = ctx.createBiquadFilter();
      low.type = 'lowpass';
      low.frequency.value = 380;
      low.connect(out);
      return [osc('sine', 110, 0.03, out, low), osc('triangle', 220, 0.012, out, low), osc('sine', 330, 0.004, out, low)];
    }]);
  }
  function startBed(spec) {
    return voice(bed, [(out) => {
      const src = ctx.createBufferSource();
      src.buffer = noise;
      src.loop = true;
      const band = ctx.createBiquadFilter();
      band.type = 'bandpass';
      band.frequency.value = spec.band;
      band.Q.value = spec.q;
      const swell = ctx.createGain();
      swell.gain.value = spec.noise;
      const lfo = ctx.createOscillator();
      lfo.frequency.value = spec.sway;
      const depth = ctx.createGain();
      depth.gain.value = spec.noise * 0.5;
      lfo.connect(depth);
      depth.connect(swell.gain);
      src.connect(band);
      band.connect(swell);
      swell.connect(out);
      return [src, lfo, ...spec.drone.map((f) => osc('sine', f, spec.tone, out))];
    }]);
  }

  /** Bring every level and voice in line with the settings, the journey, the device and the tab. */
  function sync() {
    if (!graph()) return state();
    attachNav();
    if (clunkOwed && running() && effectsOn() && !hidden()) clunk();
    const seen = !hidden() && ctx.state !== 'closed';
    const wantHum = seen && navOpen && atDestination() && effectsOn();
    if (wantHum && !hum) hum = startHum();
    else if (!wantHum && hum) hum = silence(hum);
    const want = seen && atDestination() && ambienceOn() ? String(scene?.() ?? '') : null;
    if (want !== ambScene) {
      amb = silence(amb);
      ambScene = want;
      if (want != null) amb = startBed(ambienceFor(want));
    }
    return state();
  }

  /** Settings › Sound, read again and applied (main.js onSetting, on every slider move). */
  function apply() {
    readLevels();
    if (!ctx) return state();
    glide(master.gain, curve(level.master));
    glide(effects.gain, curve(level.effects));
    glide(bed.gain, curve(level.ambience));
    return sync();
  }

  function onNav({ app = null, level: lv = 0 } = {}) {
    const moved = app !== navApp || lv !== navLevel;
    navApp = app;
    navLevel = lv;
    navOpen = lv > 0;
    if (moved) relay();
    sync();
  }
  function attachNav() {
    if (unNav) return;
    const nav = navigatorOf?.();
    if (!nav?.onChange) return;
    unNav = nav.onChange(onNav);
    navApp = nav.app ?? null;
    navLevel = nav.level ?? 0;
    navOpen = navLevel > 0;
  }

  // ---- what it hears ---------------------------------------------------------------
  const onPress = (event) => { if (event?.target?.closest?.(RELAY_TARGETS)) relay(); };
  doc?.addEventListener?.('click', onPress, { capture: true, passive: true });
  doc?.addEventListener?.('visibilitychange', sync);
  const unJourney = journey?.on?.(({ to }) => {
    if (to === 'landing') clunk();
    sync();
  }) ?? null;
  // A landing that came before audio was allowed owes its clunk to the first tap.
  if (LANDED.includes(journey?.state) && !clunked) clunkOwed = true;
  if (early && mayStartEarly({ transfer: doc?.documentElement?.dataset?.transfer === 'true' })) {
    try { unlock?.(); } catch { /* audio is optional */ }
  }
  readLevels();
  sync();

  function state() {
    const g = (node) => (node ? Math.round(node.gain.value * 1000) / 1000 : null);
    return {
      context: ctx?.state ?? 'none',
      levels: { ...level },
      gains: { master: g(master), effects: g(effects), ambience: g(bed) },
      silent: !(level.master > 0),
      hum: !!hum, ambience: ambScene, navOpen,
      clunked, clunkOwed, ...counts,
    };
  }

  return {
    /** The arrival's ticker showed `year` (main.js onYear): a tick for each digit that flipped. */
    ticker(year) {
      const y = Math.round(Number(year));
      if (!Number.isFinite(y)) return 0;
      const was = lastYear;
      lastYear = y;
      if (was == null || was === y) return 0;
      const flips = digitsChanged(was, y);
      if (!graph() || !mayPlay()) { counts.held += flips; return 0; }
      const t = now(), at = ctx.currentTime + 0.002;
      let played = 0;
      for (let i = 0; i < flips; i++) {
        if (!cap.allow(t + i * TICK_STAGGER_S * 1000)) { counts.dropped++; continue; }
        tick(at + i * TICK_STAGGER_S);
        played++;
      }
      counts.ticks += played;
      return played;
    },
    land: clunk,
    relay,
    /** A Settings › Sound slider moved (or any setting: others are ignored). */
    setting(key) { if (key == null || /^sound/.test(String(key))) apply(); },
    apply,
    sync,
    get state() { return state(); },
    /** The live gain nodes, for the smoke to read the real graph. */
    get nodes() { return ctx ? { master, effects, ambience: bed } : null; },
    dispose() {
      doc?.removeEventListener?.('click', onPress, { capture: true });
      doc?.removeEventListener?.('visibilitychange', sync);
      unJourney?.();
      unNav?.();
      if (ctx) { hum = silence(hum); amb = silence(amb); ambScene = null; }
    },
  };
}

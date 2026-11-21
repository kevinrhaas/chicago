// SPDX-License-Identifier: GPL-3.0-or-later
// T-3532. Small decoded environmental loops; one streamed music cue at a time.
import { createHabitatAudio } from './habitat-audio.js';
import { createTransportAudio } from './transport-audio.js';
import { createWorkAudio } from './work-audio.js';
import { gustAtScene, windGustGain } from './wind-gust.js';

export const AUDIO_BASE = new URL('../audio/', import.meta.url);
export const MUSIC_YEARS = Object.freeze(['1812', '1835', '1904']);

/** Nearest wet sample on the scene's own loaded terrain, never a modern map.
 * Bounded 128 samples, at 4 Hz only while ambience is enabled. The 8 m radial
 * spacing is a declared acoustic approximation, not a new shoreline survey. */
export function nearbyWater(terrain, eye) {
  if (!terrain?.loaded || !eye) return null;
  // The scene's water plane is Y=0. A listener flying above it must leave
  // acoustic range even when their horizontal position is over the river.
  const height = eye.y ?? 0;
  for (let radius = 0; radius <= 56; radius += 8) {
    const distance = Math.hypot(radius, height);
    if (distance > 56) break;
    for (let i = 0; i < (radius ? 16 : 1); i++) {
      const angle = i * Math.PI / 8;
      const x = eye.x + Math.cos(angle) * radius, z = eye.z + Math.sin(angle) * radius;
      if (terrain.heightfield?.contains && !terrain.heightfield.contains(x, -z)) continue;
      if (terrain.isWater(x, -z)) return { x, y: 0, z, distance };
    }
  }
  return null;
}

export function musicFor(catalog, year) {
  // A retired cue (runtime_enabled false) stays catalogued for provenance, never played.
  // T-3710: the jaunts' score (playlist false) plays only under its jaunts, never in the era's playlist.
  return catalog.assets.filter(a => a.kind === 'music' && a.era === String(year) && a.runtime_enabled !== false && a.playlist !== false);
}

/** T-3710: the score cue a jaunt wants now, from catalog.jaunt_score. A jaunt (or a grade
 * band's or audience's version of one, by version_of) opens on its opening cue during the
 * flight to the first stop, then loops its bed, or the cue its current stop names (the
 * battle's four movements); its closing cue plays once over the closing scene and the
 * Outing complete card, then the music rests until the jaunt is over. `played` holds the
 * one-shot cues already heard in this outing. null: no score, the era's playlist plays. */
export function scoreCueFor(catalog, jaunt, played = new Set()) {
  const score = catalog?.jaunt_score; if (!score || !jaunt?.id) return null;
  const plan = score.jaunts?.[jaunt.id] ?? (jaunt.version_of ? score.jaunts?.[jaunt.version_of] : null);
  if (!plan) return null;
  const asset = id => id ? catalog.assets.find(a => a.id === id && a.kind === 'music' && a.runtime_enabled !== false) ?? null : null;
  const bed = () => { const a = asset(plan.stops?.[jaunt.stop] ?? plan.bed); return a && { asset: a, loop: true, role: 'bed' }; };
  if (jaunt.phase === 'opening') {
    const a = asset(plan.opening);
    return a && !played.has(a.id) ? { asset: a, loop: false, role: 'opening' } : bed();
  }
  if (['closing', 'outcome'].includes(jaunt.phase)) {
    const a = asset(plan.closing);
    return a && !played.has(a.id) ? { asset: a, loop: false, role: 'closing' } : { quiet: true };
  }
  return bed();
}

/** T-3569: shuffled eras (catalog.music_shuffle_eras) start at a random track and
 * play every track once before any repeats; a fresh shuffle never reopens with the
 * track that just ended. Other eras keep their catalogue order. */
export function playlistOrder(n, shuffle, random = Math.random, avoid = -1) {
  const order = [...Array(n).keys()];
  if (!shuffle) return order;
  for (let i = n - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [order[i], order[j]] = [order[j], order[i]];
  }
  if (n > 1 && order[0] === avoid) {
    const j = 1 + Math.floor(random() * (n - 1));
    [order[0], order[j]] = [order[j], order[0]];
  }
  return order;
}

/** Listening mix, not simulated weather: town leaf rustle stays subdued, with
 * a bounded increase beside the scene's classified lake shore. */
export function windGain(year, season, water, distance = Infinity) {
  if (season === 'winter') return 0;
  const town = { '1812': .03, '1835': .022, '1904': .012 }[String(year)] ?? .012;
  const shore = water === 'lake' && Number.isFinite(distance)
    ? Math.max(0, 1 - Math.max(0, distance) / 56) ** 2 : 0;
  return (town + (.055 - town) * shore) * (season === 'fall' ? .5 : 1);
}

function insideRing(x, n, ring) {
  let inside = false;
  for (let i=0,j=ring.length-1;i<ring.length;j=i++) {
    const a=ring[i],b=ring[j];
    if ((a[1]>n)!==(b[1]>n) && x<(b[0]-a[0])*(n-a[1])/(b[1]-a[1])+a[0]) inside=!inside;
  }
  return inside;
}
/** Type before loudness: sloughs never borrow river/lake waves. */
export function waterKind(wet, terrain, zone) {
  if (!wet || !zone || zone.epoch !== terrain?.epochId) return null;
  const x=wet.x,n=-wet.z;
  for (const f of zone.features.filter(f=>f.kind==='slough')) {
    for (let i=1;i<f.line.length;i++) {
      const a=f.line[i-1],b=f.line[i],dx=b[0]-a[0],dn=b[1]-a[1];
      const t=Math.max(0,Math.min(1,((x-a[0])*dx+(n-a[1])*dn)/(dx*dx+dn*dn||1)));
      if (Math.hypot(x-a[0]-t*dx,n-a[1]-t*dn)<=f.width_m/2+8) return 'slough';
    }
  }
  const line=terrain.lakeShore;
  if (line && n>=line.n0 && n<=line.n0+(line.e.length-1)*line.step) {
    const t=(n-line.n0)/line.step,i=Math.min(line.e.length-2,Math.floor(t));
    const shore=line.e[i]*(1-(t-i))+line.e[i+1]*(t-i);
    if (x>shore+6) return 'lake';
  }
  for (const f of zone.features.filter(f=>f.kind==='river')) {
    if (insideRing(x,n,f.polygon[0]) && !f.polygon.slice(1).some(r=>insideRing(x,n,r))) return 'river';
  }
  return null; // Unknown water remains quiet until classified, never generic surf.
}

export function createRecordedAudio({ ctx, ambience, effects, music, environment = () => ({}), workEnvironment = () => ({}),
  fetcher = globalThis.fetch?.bind(globalThis), media = () => new Audio(),
  base = AUDIO_BASE, onStatus = () => {}, now = () => Date.now(), random = Math.random,
  later = (fn, ms) => setTimeout(fn, ms) } = {}) {
  let disposed = false, enabled = false, effectsOn = false, musicOn = false, catalog = null, pending = null;
  let year = '', generation = 0, controller = null, musicFailed = false;
  let player = null, mediaNode = null, track = null, trackIndex = 0, order = null, fallback = false;
  let decoder = null;
  const buffers = new Map(), loads = new Map(), voices = new Map(), failed = new Set();
  const errors = new Set();
  let targets = new Map();
  let musicLevel = 0, duck = 1;
  // T-3710: what the one streamed player is playing ({ kind: 'era' } or a jaunt's score cue),
  // the fader it plays through (a cue change dips it rather than cutting), and the jaunt.
  let current = null, fader = null, switching = false, attemptId = 0;
  let jaunt = null, session = null, played = new Set();
  const habitat = createHabitatAudio({ ctx, output: ambience, catalog: () => catalog, environment,
    fetcher, base, now, decodeAudio: decode, onError: message => report(message) });
  const transport = createTransportAudio({ ctx, output: effects, catalog: () => catalog, environment,
    fetcher, base, now, decodeAudio: decode, onError: message => report(message) });
  const work = createWorkAudio({ ctx, output: effects, catalog: () => catalog,
    fetcher, base, decodeAudio: decode, onError: message => report(message) });
  function report(message) { if (message) errors.add(message); onStatus(state()); }
  function state() { return { year, voices: [...voices.keys(), ...habitat.state.voices, ...transport.state.voices, ...work.state.voices], decodedBytes: [...buffers.values()].reduce((n, b) => n + b.length * b.numberOfChannels * 4, 0) + habitat.state.decodedBytes + transport.state.decodedBytes + work.state.decodedBytes,
    track: track?.title ?? null, playing: !!player && !player.paused, score: current?.kind === 'cue' ? current.asset.id : null, errors: [...errors], loading: loads.size + (pending ? 1 : 0) + habitat.state.loading + transport.state.loading + work.state.loading, habitat: habitat.state, transport: transport.state, work: work.state }; }
  function fade(param, value) { param.setTargetAtTime(value, ctx.currentTime, 0.3); }
  function stopVoice(id) {
    const v = voices.get(id); if (!v) return;
    voices.delete(id); fade(v.gain.gain, 0);
    v.source.onended = () => { v.source.disconnect(); v.gain.disconnect(); v.pan?.disconnect(); };
    v.source.stop(ctx.currentTime + 1.5);
  }
  function stopMusic() {
    if (player) { player.pause(); player.onended = null; player.onerror = null; player.removeAttribute('src'); player.load(); }
    mediaNode?.disconnect(); fader?.disconnect(); player = null; mediaNode = null; fader = null; track = null;
    current = null; switching = false;
  }
  function reset() {
    habitat.reset(); transport.reset(); work.reset();
    generation++; controller?.abort(); controller = null; pending = null;
    loads.clear(); targets.clear(); failed.clear(); buffers.clear();
    decoder = null;
    for (const id of [...voices.keys()]) stopVoice(id);
    stopMusic(); trackIndex = 0; order = null; musicFailed = false;
  }
  async function readCatalog() {
    if (catalog || pending || disposed || (!enabled && !musicOn && !effectsOn) || failed.has('catalog')) return;
    const own = generation; controller ??= new AbortController();
    pending = (async () => {
      try {
        const r = await fetcher(new URL('catalog.json', base), { signal: controller.signal });
        if (!r.ok) throw Error(`HTTP ${r.status}`);
        const value = await r.json();
        if (!disposed && own === generation) { catalog = value; pending = null; update(); }
      } catch (e) {
        if (own === generation) { pending = null; if (e.name !== 'AbortError') { failed.add('catalog'); report(`Audio catalogue: ${e.message}`); } }
      }
    })();
  }
  function startVoice(id, buffer) {
    if (disposed || !enabled || !targets.has(id) || voices.has(id)) return;
    const source = ctx.createBufferSource(), gain = ctx.createGain();
    source.buffer = buffer; source.loop = true; gain.gain.value = 0;
    source.connect(gain);
    const pan = ['river', 'lake'].includes(id) ? ctx.createPanner() : null;
    if (pan) {
      // Distance attenuation is authored below; panner supplies direction only.
      pan.panningModel = 'HRTF'; pan.rolloffFactor = 0;
      gain.connect(pan); pan.connect(ambience);
    } else gain.connect(ambience);
    voices.set(id, { source, gain, pan }); source.start(0, Math.random() * buffer.duration);
    applyVoice(id); report();
  }
  function applyVoice(id) {
    const v = voices.get(id), t = targets.get(id); if (!v || !t) return;
    fade(v.gain.gain, t.gain * duck);
    if (v.pan) {
      for (const axis of ['x', 'y', 'z']) v.pan[`position${axis.toUpperCase()}`].setTargetAtTime(t[axis], ctx.currentTime, 0.15);
    }
  }
  function decode(bytes) {
    if (!decoder) {
      // Shared environmental/habitat decoding stays at the masters'48kHz,
      // independently of a96/192kHz hardware output context.
      const Offline = globalThis.OfflineAudioContext ?? globalThis.webkitOfflineAudioContext;
      try { decoder = Offline ? new Offline(1, 1, 48000) : ctx; }
      catch { decoder = ctx; }
    }
    return decoder.decodeAudioData(bytes);
  }
  async function want(id) {
    if (buffers.has(id)) { startVoice(id, buffers.get(id)); return; }
    if (loads.has(id) || failed.has(id) || !catalog) return;
    const asset = catalog.assets.find(a => a.id === id); if (!asset || asset.runtime_enabled === false) return;
    const own = generation; controller ??= new AbortController();
    loads.set(id, true);
    try {
      const r = await fetcher(new URL(asset.url, base), { signal: controller.signal });
      if (!r.ok) throw Error(`HTTP ${r.status}`);
      const bytes = await r.arrayBuffer();
      if (own !== generation || disposed) return;
      const buffer = await decode(bytes);
      if (own !== generation || disposed) return;
      // Fixed pilot budget: three <=24s mono loops, under 14 MiB decoded.
      if (buffer.duration > 24 || buffer.numberOfChannels !== 1) throw Error('loop exceeds audio memory budget');
      const bytesDecoded = buffer.length * buffer.numberOfChannels * 4;
      if (bytesDecoded + [...buffers.values()].reduce((n, b) => n + b.length * b.numberOfChannels * 4, 0) > 14 * 1024 * 1024)
        throw Error('decoded cache exceeds 14 MiB audio memory budget');
      buffers.set(id, buffer); startVoice(id, buffer);
    } catch (e) {
      if (own === generation && e.name !== 'AbortError') { failed.add(id); report(`${id}: ${e.message}`); }
    } finally { if (own === generation) loads.delete(id); }
  }
  // One gesture-unlocked streaming element plays everything, the era's playlist and the
  // jaunts' score alike: an iPhone lets only an element a tap has started play on later.
  function attempt() {
    const element = player, own = generation, id = ++attemptId;
    element.src = new URL(fallback ? track.aac : track.opus, base).href;
    element.play().catch(e => {
      if (own !== generation || player !== element || id !== attemptId) return;
      // The rejected Opus play promise can arrive after onerror has already
      // started AAC. Only the current attempt may stop or replace playback.
      if (e.name === 'NotSupportedError') fail(e);
      else { report(`Music playback: ${e.message}`); stopMusic(); musicFailed = true; }
    });
  }
  function fail(e) {
    if (!fallback) { fallback = true; attempt(); }
    else { report(`Music unavailable: ${track.title}: ${e?.message ?? 'media error'}`); stopMusic(); musicFailed = true; }
  }
  function begin(asset, loop) {
    track = asset; player.loop = !!loop;
    fallback = !player.canPlayType('audio/ogg; codecs="opus"');
    attempt(); report();
  }
  function ensurePlayer() {
    if (player) return;
    const element = player = media(); element.preload = 'none'; element.crossOrigin = 'anonymous';
    mediaNode = ctx.createMediaElementSource(element); fader = ctx.createGain(); fader.gain.value = 1;
    mediaNode.connect(fader); fader.connect(music);
    const own = generation;
    element.onerror = () => {
      if (own !== generation || player !== element) return;
      fail(element.error);
    };
    element.onended = () => {
      if (disposed || !musicOn || own !== generation || player !== element) return;
      // A one-shot score cue that ends is heard; the jaunt moves on to what it wants next.
      if (current?.kind === 'cue') { played.add(current.asset.id); current = null; steer(); return; }
      // Keep the gesture-unlocked streaming element and its graph connection.
      // Advance immediately, then wrap within this era; no full-playlist preload.
      // A shuffled era deals a new order at the wrap, never repeating the last track.
      const list = musicFor(catalog, year), shuffle = (catalog.music_shuffle_eras ?? []).includes(String(year));
      if (!list.length) return;
      if (order?.length !== list.length) { order = playlistOrder(list.length, shuffle, random); trackIndex = -1; }
      trackIndex = (trackIndex + 1) % order.length;
      if (!trackIndex && shuffle) order = playlistOrder(list.length, true, random, order.at(-1));
      begin(list[order[trackIndex]], false);
    };
  }
  function wanted() {
    const cue = scoreCueFor(catalog, jaunt, played);
    if (cue?.quiet) return { kind: 'quiet' };
    if (cue) return { kind: 'cue', asset: cue.asset, loop: cue.loop, role: cue.role };
    return musicFor(catalog, year).length ? { kind: 'era' } : { kind: 'quiet' };
  }
  function start(want) {
    current = want;
    if (want.kind === 'quiet') { if (player && !player.paused) player.pause(); report(); return; }
    ensurePlayer();
    if (want.kind === 'cue') { begin(want.asset, want.loop); return; }
    const list = musicFor(catalog, year), shuffle = (catalog.music_shuffle_eras ?? []).includes(String(year));
    if (order?.length !== list.length) { order = playlistOrder(list.length, shuffle, random); trackIndex = 0; }
    begin(list[order[trackIndex % order.length]], false);
  }
  /** T-3710: bring the player to what is wanted now. A change of cue dips the fader over about
   * a second and starts the next one rising, never a cut; a closing cue is never cut short, so
   * its cadence lands even when the visitor closes the card. */
  function steer() {
    if (disposed || !musicOn || !catalog || musicFailed || switching) return;
    const want = wanted();
    if (current && current.kind === want.kind && (want.kind !== 'cue' || current.asset.id === want.asset.id)) return;
    if (!player) { if (want.kind !== 'quiet') start(want); return; }
    const sounding = !player.paused && current && current.kind !== 'quiet';
    if (sounding && current.kind === 'cue' && current.role === 'closing') return;
    if (!sounding) { start(want); return; }
    switching = true;
    const own = generation, element = player;
    fader.gain.setTargetAtTime(0, ctx.currentTime, .3);
    later(() => {
      if (disposed || own !== generation || player !== element) return;
      switching = false;
      fader.gain.setTargetAtTime(1, ctx.currentTime, .25);
      const next = wanted();
      if (current && current.kind === next.kind && (next.kind !== 'cue' || current.asset.id === next.asset.id)) return;
      start(next);
    }, 1200);
  }
  function playMusic() { steer(); }
  function update() {
    if (disposed || (!enabled && !musicOn && !effectsOn)) {
      habitat.sync({ enabled: false, year, duck }); transport.sync({ enabled: false, year, duck }); return;
    }
    if (!catalog) { void readCatalog(); return; }
    const env = environment() ?? {}, camera = env.camera;
    if ((enabled || effectsOn) && camera) {
      const eye = camera.position, q = camera.quaternion;
      if (q && ctx.listener.positionX) {
        // Camera looks along local -Z, up local +Y; Three and Web Audio both use Y-up.
        const forward = [-2*(q.x*q.z+q.w*q.y), -2*(q.y*q.z-q.w*q.x), -(1-2*(q.x*q.x+q.y*q.y))];
        const up = [2*(q.x*q.y-q.w*q.z), 1-2*(q.x*q.x+q.z*q.z), 2*(q.y*q.z+q.w*q.x)];
        for (const [i, axis] of ['X','Y','Z'].entries()) {
          ctx.listener[`position${axis}`].setTargetAtTime(eye[axis.toLowerCase()], ctx.currentTime, .05);
          ctx.listener[`forward${axis}`].setTargetAtTime(forward[i], ctx.currentTime, .05);
          ctx.listener[`up${axis}`].setTargetAtTime(up[i], ctx.currentTime, .05);
        }
      }
    }
    if (enabled && camera) {
      const eye = camera.position;
      targets = new Map();
      const wet = nearbyWater(env.terrain, eye);
      const kind = waterKind(wet, env.terrain, catalog.water_zones?.[year]);
      // T-3586: the leaf rustle swells with the gust where the listener stands, the
      // same gust that bends the crowns and grass round them; never above its old level.
      const wind = windGain(year, env.season, kind, wet?.distance) * windGustGain(gustAtScene(eye.x, eye.z));
      if (wind > 0) targets.set('wind', { gain: wind });
      // A recording rejected in listening review remains auditionable in the
      // library, but cannot imply water movement absent from the scene.
      if ((kind === 'river' || kind === 'lake') && catalog.assets.find(a => a.id === kind)?.runtime_enabled !== false)
        targets.set(kind, { ...wet, gain: (kind === 'lake' ? .32 : .22) * (1 - wet.distance / 64) ** 2 });
      for (const id of [...voices.keys()]) if (!targets.has(id)) stopVoice(id);
      for (const id of targets.keys()) { void want(id); applyVoice(id); }
    } else {
      targets.clear();
      for (const id of [...voices.keys()]) stopVoice(id);
    }
    habitat.sync({ enabled, year, duck });
    transport.sync({ enabled: effectsOn, year, duck });
    playMusic();
  }
  return {
    sync({ active, ambienceOn, effectsOn: wantsEffects, musicOn: wantsMusic, year: nextYear, musicLevel: level = .4, jaunt: nextJaunt = null } = {}) {
      if (disposed) return;
      // T-3710: the jaunt under way, if any ({ id, version_of, phase, stop, session }).
      jaunt = nextJaunt?.id ? nextJaunt : null;
      const outing = jaunt ? `${jaunt.id}#${jaunt.session ?? ''}` : null;
      if (outing !== session) { session = outing; played = new Set(); }
      const next = String(nextYear ?? '');
      if (year !== next) { reset(); year = next; }
      const nextEnabled = !!active && !!ambienceOn, nextMusic = !!active && !!wantsMusic;
      const nextEffects = !!active && !!wantsEffects && !!effects;
      if ((!nextEnabled && !nextMusic && !nextEffects) && (enabled || musicOn || effectsOn)) reset();
      enabled = nextEnabled; musicOn = nextMusic; effectsOn = nextEffects; musicLevel = level;
      if (!effectsOn) work.reset();
      fade(music.gain, Math.min(1, Math.max(0, level)) ** 2 * .5 * duck);
      if (!enabled) { targets.clear(); for (const id of [...voices.keys()]) stopVoice(id); }
      if (!musicOn) { stopMusic(); musicFailed = false; }
      update();
    },
    update,
    transportFrame({ active = true } = {}) {
      transport.frame?.({ enabled: active && effectsOn && !disposed, year });
    },
    workFrame({ active = true } = {}) {
      if (!active || !effectsOn || disposed) { work.frame({ enabled: false }); return; }
      work.frame({ ...workEnvironment(), enabled: true });
    },
    // Future narration can duck both buses without coupling to a voice provider.
    setSpeechActive(on) { duck = on ? .3 : 1; habitat.setDuck(duck); transport.setDuck(duck); work.setDuck(duck); fade(music.gain, musicLevel ** 2 * .5 * duck); for (const id of voices.keys()) applyVoice(id); },
    get state() { return state(); },
    dispose() { disposed = true; enabled = false; musicOn = false; effectsOn = false; reset(); habitat.dispose(); transport.dispose(); work.dispose(); },
  };
}

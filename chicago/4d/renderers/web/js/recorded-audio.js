// SPDX-License-Identifier: GPL-3.0-or-later
// T-3532. Small decoded environmental loops; one streamed music cue at a time.
import { createHabitatAudio } from './habitat-audio.js';
import { createTransportAudio } from './transport-audio.js';

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
  return catalog.assets.filter(a => a.kind === 'music' && a.era === String(year));
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

export function createRecordedAudio({ ctx, ambience, effects, music, environment = () => ({}),
  fetcher = globalThis.fetch?.bind(globalThis), media = () => new Audio(),
  base = AUDIO_BASE, onStatus = () => {}, now = () => Date.now() } = {}) {
  let disposed = false, enabled = false, effectsOn = false, musicOn = false, catalog = null, pending = null;
  let year = '', generation = 0, controller = null, musicFailed = false;
  let player = null, mediaNode = null, track = null, trackIndex = 0, fallback = false;
  let decoder = null;
  const buffers = new Map(), loads = new Map(), voices = new Map(), failed = new Set();
  const errors = new Set();
  let targets = new Map();
  let musicLevel = 0, duck = 1;
  const habitat = createHabitatAudio({ ctx, output: ambience, catalog: () => catalog, environment,
    fetcher, base, now, decodeAudio: decode, onError: message => report(message) });
  const transport = createTransportAudio({ ctx, output: effects, catalog: () => catalog, environment,
    fetcher, base, now, decodeAudio: decode, onError: message => report(message) });
  function report(message) { if (message) errors.add(message); onStatus(state()); }
  function state() { return { year, voices: [...voices.keys(), ...habitat.state.voices, ...transport.state.voices], decodedBytes: [...buffers.values()].reduce((n, b) => n + b.length * b.numberOfChannels * 4, 0) + habitat.state.decodedBytes + transport.state.decodedBytes,
    track: track?.title ?? null, playing: !!player && !player.paused, errors: [...errors], loading: loads.size + (pending ? 1 : 0) + habitat.state.loading + transport.state.loading, habitat: habitat.state, transport: transport.state }; }
  function fade(param, value) { param.setTargetAtTime(value, ctx.currentTime, 0.3); }
  function stopVoice(id) {
    const v = voices.get(id); if (!v) return;
    voices.delete(id); fade(v.gain.gain, 0);
    v.source.onended = () => { v.source.disconnect(); v.gain.disconnect(); v.pan?.disconnect(); };
    v.source.stop(ctx.currentTime + 1.5);
  }
  function stopMusic() {
    if (player) { player.pause(); player.onended = null; player.onerror = null; player.removeAttribute('src'); player.load(); }
    mediaNode?.disconnect(); player = null; mediaNode = null; track = null;
  }
  function reset() {
    habitat.reset(); transport.reset();
    generation++; controller?.abort(); controller = null; pending = null;
    loads.clear(); targets.clear(); failed.clear(); buffers.clear();
    decoder = null;
    for (const id of [...voices.keys()]) stopVoice(id);
    stopMusic(); trackIndex = 0; musicFailed = false;
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
  function playMusic() {
    if (disposed || !musicOn || !catalog || player || musicFailed) return;
    const list = musicFor(catalog, year); if (!list.length) return;
    track = list[trackIndex % list.length]; player = media(); player.preload = 'none';
    player.crossOrigin = 'anonymous'; fallback = !player.canPlayType('audio/ogg; codecs="opus"');
    mediaNode = ctx.createMediaElementSource(player); mediaNode.connect(music);
    const own = generation, element = player;
    let attemptId = 0;
    const fail = e => {
      if (!fallback) { fallback = true; attempt(); }
      else { report(`Music unavailable: ${track.title}: ${e?.message ?? 'media error'}`); stopMusic(); musicFailed = true; }
    };
    const attempt = () => {
      const id = ++attemptId;
      element.src = new URL(fallback ? track.aac : track.opus, base).href;
      element.play().catch(e => {
        if (own !== generation || player !== element || id !== attemptId) return;
        // The rejected Opus play promise can arrive after onerror has already
        // started AAC. Only the current attempt may stop or replace playback.
        if (e.name === 'NotSupportedError') fail(e);
        else { report(`Music playback: ${e.message}`); stopMusic(); musicFailed = true; }
      });
    };
    element.onerror = () => {
      if (own !== generation || player !== element) return;
      fail(element.error);
    };
    element.onended = () => {
      if (disposed || !musicOn || own !== generation || player !== element) return;
      // Keep the gesture-unlocked streaming element and its graph connection.
      // Advance immediately, then wrap within this era; no full-playlist preload.
      trackIndex = (trackIndex + 1) % list.length;
      track = list[trackIndex];
      fallback = !element.canPlayType('audio/ogg; codecs="opus"');
      attempt(); report();
    };
    attempt(); report();
  }
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
      const wind = windGain(year, env.season, kind, wet?.distance);
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
    sync({ active, ambienceOn, effectsOn: wantsEffects, musicOn: wantsMusic, year: nextYear, musicLevel: level = .4 } = {}) {
      if (disposed) return;
      const next = String(nextYear ?? '');
      if (year !== next) { reset(); year = next; }
      const nextEnabled = !!active && !!ambienceOn, nextMusic = !!active && !!wantsMusic;
      const nextEffects = !!active && !!wantsEffects && !!effects;
      if ((!nextEnabled && !nextMusic && !nextEffects) && (enabled || musicOn || effectsOn)) reset();
      enabled = nextEnabled; musicOn = nextMusic; effectsOn = nextEffects; musicLevel = level;
      fade(music.gain, Math.min(1, Math.max(0, level)) ** 2 * .5 * duck);
      if (!enabled) { targets.clear(); for (const id of [...voices.keys()]) stopVoice(id); }
      if (!musicOn) { stopMusic(); musicFailed = false; }
      update();
    },
    update,
    // Future narration can duck both buses without coupling to a voice provider.
    setSpeechActive(on) { duck = on ? .3 : 1; habitat.setDuck(duck); transport.setDuck(duck); fade(music.gain, musicLevel ** 2 * .5 * duck); for (const id of voices.keys()) applyVoice(id); },
    get state() { return state(); },
    dispose() { disposed = true; enabled = false; musicOn = false; effectsOn = false; reset(); habitat.dispose(); transport.dispose(); },
  };
}

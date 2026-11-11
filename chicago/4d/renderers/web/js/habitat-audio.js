// SPDX-License-Identifier: GPL-3.0-or-later
// Recorded habitat phrases, qualified by the scene's own fauna and flora records.
// No animal is invented near the listener: audible-only insects are a broad bed;
// the one bird proxy is a distant, offscreen habitat call with a fixed world anchor.
export const HABITAT_AUDIO_LIMITS = Object.freeze({
  voices: 1, decodedBytes: 24 * 48000 * 4, sourceSeconds: 24, sampleRate: 48000,
  birdNearMetres: 36, birdFarMetres: 96,
});

const AUDIBLE = new Set(['audible', 'visible_and_audible']);
const VOCAL = new Set(['song_full', 'song_reduced', 'call_only', 'chorus']);
const PRESENT = new Set(['breeding_resident', 'year_round_resident']);
const MODES = new Set(['habitat-insects', 'distant-bird']);
const finite = n => typeof n === 'number' && Number.isFinite(n);
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));
const hourOf = hhmm => {
  const m = /^(\d{2}):(\d{2})$/.exec(String(hhmm ?? ''));
  return m && +m[1] < 24 && +m[2] < 60 ? +m[1] + +m[2] / 60 : null;
};

/** Same date/hour/sun that lights the scene, including custom hours and jaunts.
 * The 6-degree twilight boundary is an acoustic scheduling choice, not an
 * observation of a particular animal. Missing scene state always means quiet. */
export function habitatPeriod(env) {
  const hour = hourOf(env?.time?.hhmm), elevation = env?.sunElevation;
  if (hour === null || !finite(elevation)) return null;
  return elevation > 6 ? 'day' : elevation >= -6 ? (hour < 12 ? 'dawn' : 'dusk') : 'night';
}

function validScene(env, year) {
  return String(year) === '1835' && env?.time?.date === '1835-07-01'
    && env.season === 'summer' && env.terrain?.loaded === true
    && typeof env.flora?.zoneAt === 'function' && Array.isArray(env.faunaZones)
    && finite(env.camera?.position?.x) && finite(env.camera?.position?.y) && finite(env.camera?.position?.z)
    && (env.temperatureC == null || (finite(env.temperatureC) && env.temperatureC > 0));
}

function zoneAt(env, x, z) {
  try {
    if (env.terrain.heightfield?.contains && !env.terrain.heightfield.contains(x, -z)) return null;
    return env.flora.zoneAt(x, -z);
  } catch { return null; } // A replaced/disposed terrain must not keep a voice alive.
}

function behindListener(camera, x, y, z) {
  const q = camera?.quaternion;
  if (![q?.x, q?.y, q?.z, q?.w].every(finite)) return false;
  const fx = -2 * (q.x * q.z + q.w * q.y), fy = -2 * (q.y * q.z - q.w * q.x),
    fz = -(1 - 2 * (q.x * q.x + q.y * q.y));
  const dx = x - camera.position.x, dy = y - camera.position.y, dz = z - camera.position.z;
  const length = Math.hypot(fx, fy, fz) * Math.hypot(dx, dy, dz);
  // Use the full 3D rear hemisphere, including a flying listener looking down.
  return length > 0.01 && (fx * dx + fy * dy + fz * dz) / length < -0.2;
}

// terrain.height() is a navigation barrier over water (4 m), not ground.
// Read the rendered surface API; missing measured ground remains silent.
function groundAt(terrain, e, n) {
  const sample = typeof terrain?.surfaceHeight === 'function' ? terrain.surfaceHeight : terrain?.groundHeight;
  return typeof sample === 'function' ? sample.call(terrain, e, n) : undefined;
}

function insectGain(env, placement) {
  const eye = env.camera.position, ground = groundAt(env.terrain, eye.x, -eye.z);
  const height = finite(ground) ? Math.abs(eye.y - ground) : Infinity;
  return height < 32 ? placement.gain * (1 - height / 32) ** 2 : 0;
}

function recordFor(env, placement, floraZone, period) {
  return env.faunaZones.find(zone => zone.scene_date === placement.scene_date
    && zone.in_modelled_extent === true && placement.zone_ids.includes(zone.id)
    && zone.extent_from?.flora_zone === floraZone
    && zone.species?.some(sp => sp.id === placement.species_id
      && sp.active_periods?.includes(period) && AUDIBLE.has(sp.july?.presence?.value)
      && VOCAL.has(sp.july?.vocalization) && PRESENT.has(sp.july?.status?.value)
      && (placement.mode !== 'habitat-insects' || sp.july.presence.value === 'audible')));
}

function placementFor(asset, year) {
  if (asset.runtime_enabled !== true || !asset.approved_eras?.includes(String(year))) return null;
  const p = asset.scene_placement;
  if (!p || p.scene_date !== '1835-07-01' || !MODES.has(p.mode)
    || !Array.isArray(p.zone_ids) || !p.zone_ids.length || typeof p.species_id !== 'string'
    || !finite(p.gain) || p.gain <= 0 || p.gain > 0.2
    || !Array.isArray(p.gap_seconds) || p.gap_seconds.length !== 2
    || !p.gap_seconds.every(finite) || p.gap_seconds[0] < 20 || p.gap_seconds[1] < p.gap_seconds[0]
    || typeof asset.url !== 'string' || !asset.delivery?.sha256) return null;
  return p;
}

/** Read the live habitat at candidate source points. No second habitat geometry,
 * era transfer, fixed invented coordinates, or per-frame fetches are introduced.
 * At most 3 rings x 16 samples are asked for a bird, once per second while idle. */
export function habitatCandidates(catalog, env, year, { birds = true, birdPhase = 0 } = {}) {
  if (!validScene(env, year)) return [];
  const period = habitatPeriod(env), hour = hourOf(env.time.hhmm);
  if (!period) return [];
  const eye = env.camera.position, here = zoneAt(env, eye.x, eye.z), result = [];
  for (const asset of catalog?.assets ?? []) {
    const p = placementFor(asset, year);
    if (!p || (finite(p.from_hour) && hour < p.from_hour)) continue;
    if (p.mode === 'habitat-insects') {
      const zone = recordFor(env, p, here, period);
      const gain = insectGain(env, p);
      if (zone && gain > 0) result.push({ asset, placement: p, zone: zone.id, gain, mode: p.mode });
      continue;
    }
    if (!birds) continue;
    let candidate = null;
    for (const radius of [44, 64, 84]) {
      for (let i = 0; i < 16 && !candidate; i++) {
        const angle = birdPhase + i * Math.PI / 8;
        const x = eye.x + Math.cos(angle) * radius, z = eye.z + Math.sin(angle) * radius;
        const zone = recordFor(env, p, zoneAt(env, x, z), period);
        if (!zone) continue;
        const ground = groundAt(env.terrain, x, -z);
        if (!finite(ground)) continue;
        // The model's water plane is Y=0: a marsh call must not sit underwater.
        const sourceY = Math.max(0, ground) + 1.5;
        if (!behindListener(env.camera, x, sourceY, z)) continue;
        const distance = Math.hypot(x - eye.x, sourceY - eye.y, z - eye.z);
        if (distance >= HABITAT_AUDIO_LIMITS.birdFarMetres) continue;
        candidate = { asset, placement: p, zone: zone.id, mode: p.mode,
          anchor: { x, y: sourceY, z }, gain: p.gain * (1 - distance / HABITAT_AUDIO_LIMITS.birdFarMetres) ** 2 };
      }
      if (candidate) break;
    }
    if (candidate) result.push(candidate);
  }
  return result;
}

function stillEligible(candidate, catalog, env, year) {
  if (!validScene(env, year)) return false;
  const p = placementFor(candidate.asset, year), period = habitatPeriod(env), hour = hourOf(env.time.hhmm);
  if (!p || !period || (finite(p.from_hour) && hour < p.from_hour)) return false;
  if (p.mode === 'habitat-insects') {
    candidate.gain = insectGain(env, p);
    return candidate.gain > 0 && !!recordFor(env, p, zoneAt(env, env.camera.position.x, env.camera.position.z), period);
  }
  const { x, y, z } = candidate.anchor, eye = env.camera.position;
  const distance = Math.hypot(x - eye.x, y - eye.y, z - eye.z);
  if (distance < HABITAT_AUDIO_LIMITS.birdNearMetres || distance >= HABITAT_AUDIO_LIMITS.birdFarMetres
    || !behindListener(env.camera, x, y, z) || !recordFor(env, p, zoneAt(env, x, z), period)) return false;
  candidate.gain = p.gain * (1 - distance / HABITAT_AUDIO_LIMITS.birdFarMetres) ** 2;
  return true;
}

/** One short phrase at a time, with real gaps. One decoded mono file and one
 * in-flight fetch/decode are retained at most. Decode cannot be aborted, so its
 * promise stays reserved across resets; a late result is discarded before use. */
export function createHabitatAudio({ ctx, output, catalog, environment,
  fetcher = globalThis.fetch?.bind(globalThis), decodeAudio = null, base = new URL('../audio/', import.meta.url),
  now = () => performance.now(), random = Math.random, onError = () => {} } = {}) {
  let disposed = false, active = false, year = '', scope = '', generation = 0;
  let loading = null, controller = null, cached = null, voice = null, decoder = null, duck = 1, lastNow = 0;
  let nextInspect = 0, nextPhraseAt = 0;
  const nextDue = new Map(), failed = new Set(), errors = new Set();
  const jitter = (a, b) => a + clamp(random(), 0, 1) * (b - a);
  const error = message => { errors.add(message); onError(message); };
  function stop(fade = false) {
    if (!voice) return;
    if (fade) {
      if (!voice.stopping) {
        voice.stopping = true;
        voice.gain.gain.setTargetAtTime(0, ctx.currentTime, 0.02);
        voice.source.stop(ctx.currentTime + 0.08);
      }
      return; // Keep the voice slot reserved until the short fade has ended.
    }
    const old = voice; voice = null;
    old.source.onended = null;
    try { old.source.stop(); } catch { /* already ended */ }
    old.source.disconnect(); old.envelope.disconnect(); old.gain.disconnect(); old.pan?.disconnect();
  }
  function reset() {
    generation++; active = false; controller?.abort(); controller = null;
    cached = null; decoder = null; nextDue.clear(); failed.clear(); nextInspect = 0; nextPhraseAt = 0; stop();
    // loading is deliberately NOT cleared until the fetch/decode settles.
  }
  function updateVoice() {
    if (!voice || voice.stopping) return;
    if (!stillEligible(voice.candidate, catalog(), environment(), year)) { stop(true); return; }
    voice.gain.gain.setTargetAtTime(voice.candidate.gain * duck, ctx.currentTime, 0.2);
  }
  function start(candidate, buffer) {
    if (!active || disposed || voice || !stillEligible(candidate, catalog(), environment(), year)) return;
    const source = ctx.createBufferSource(), gain = ctx.createGain(), envelope = ctx.createGain();
    source.buffer = buffer; source.loop = false; gain.gain.value = candidate.gain * duck;
    envelope.gain.value = 0; source.connect(envelope); envelope.connect(gain);
    let pan = null;
    if (candidate.anchor) {
      pan = ctx.createPanner(); pan.panningModel = 'HRTF'; pan.rolloffFactor = 0;
      for (const axis of ['x', 'y', 'z']) pan[`position${axis.toUpperCase()}`].value = candidate.anchor[axis];
      gain.connect(pan); pan.connect(output);
    } else gain.connect(output);
    const duration = buffer.duration;
    const attack = Math.min(0.3, duration / 8), release = Math.min(0.7, duration / 4), t = ctx.currentTime;
    envelope.gain.setValueAtTime(0, t);
    envelope.gain.linearRampToValueAtTime(1, t + attack);
    envelope.gain.setValueAtTime(1, t + duration - release);
    envelope.gain.linearRampToValueAtTime(0, t + duration);
    const own = { source, gain, envelope, pan, candidate };
    voice = own;
    source.onended = () => {
      source.disconnect(); envelope.disconnect(); gain.disconnect(); pan?.disconnect();
      if (voice === own) voice = null;
    };
    // A full recorded phrase, with unaltered pitch and no synthesized sound.
    source.start(t); source.stop(t + duration);
    nextPhraseAt = now() + 1000 * (duration + jitter(12, 25));
    nextDue.set(candidate.asset.id, now() + 1000 * (duration + jitter(...candidate.placement.gap_seconds)));
  }
  async function load(candidate) {
    if (loading || disposed || !active) return;
    if (cached?.id === candidate.asset.id) { start(candidate, cached.buffer); return; }
    cached = null;
    const own = generation, token = {}, abort = new AbortController();
    loading = token; controller = abort;
    try {
      const response = await fetcher(new URL(candidate.asset.url, base), { signal: abort.signal });
      if (!response.ok) throw Error(`HTTP ${response.status}`);
      const bytes = await response.arrayBuffer();
      if (disposed || generation !== own || !active) return;
      let buffer;
      if (decodeAudio) buffer = await decodeAudio(bytes);
      else {
        // The mixer injects its shared fixed-rate decoder. Standalone consumers
        // use the same 48 kHz policy, never hardware 96/192 kHz cache multiplication.
        if (!decoder) {
          const Offline = globalThis.OfflineAudioContext ?? globalThis.webkitOfflineAudioContext;
          try { decoder = Offline ? new Offline(1, 1, 48000) : ctx; }
          catch { decoder = ctx; }
        }
        buffer = await decoder.decodeAudioData(bytes);
      }
      if (disposed || generation !== own || !active) return;
      const size = buffer.length * buffer.numberOfChannels * 4;
      if (buffer.numberOfChannels !== 1 || !finite(buffer.duration) || buffer.duration <= 0
        || buffer.duration > HABITAT_AUDIO_LIMITS.sourceSeconds || !finite(buffer.sampleRate)
        || buffer.sampleRate > HABITAT_AUDIO_LIMITS.sampleRate || !finite(buffer.length) || buffer.length <= 0
        || !finite(size) || size > HABITAT_AUDIO_LIMITS.decodedBytes)
        throw Error('habitat recording exceeds mono 24-second / 48 kHz memory budget');
      if (!stillEligible(candidate, catalog(), environment(), year)) return;
      cached = { id: candidate.asset.id, buffer, bytes: size }; start(candidate, buffer);
    } catch (e) {
      if (generation === own && !disposed && e.name !== 'AbortError') {
        failed.add(candidate.asset.id); error(`${candidate.asset.id}: ${e.message}`);
      }
    } finally {
      if (loading === token) loading = null;
      if (controller === abort) controller = null;
    }
  }
  return {
    sync({ enabled, year: nextYear, duck: nextDuck = 1 } = {}) {
      if (disposed) return;
      const env = environment(), next = String(nextYear ?? ''), t = now();
      const nextScope = `${next}|${env?.time?.date ?? ''}|${env?.season ?? ''}`;
      const willRun = !!enabled && validScene(env, next);
      if (nextScope !== scope || (!willRun && active) || t < lastNow) reset();
      scope = nextScope; year = next; active = willRun; lastNow = t; duck = clamp(nextDuck, 0, 1);
      if (!active) return;
      updateVoice();
      if (voice || loading || t < nextInspect || t < nextPhraseAt) return;
      // Nearby habitat lookups are bounded to once per second, not every frame.
      nextInspect = t + 1000;
      const candidates = habitatCandidates(catalog(), env, year, { birdPhase: jitter(0, Math.PI * 2) });
      for (const c of candidates) if (!nextDue.has(c.asset.id))
        nextDue.set(c.asset.id, t + jitter(c.mode === 'distant-bird' ? 12000 : 6000, 20000));
      const due = candidates.filter(c => !failed.has(c.asset.id) && nextDue.get(c.asset.id) <= t)
        .sort((a, b) => nextDue.get(a.asset.id) - nextDue.get(b.asset.id));
      if (due.length) void load(due[0]);
    },
    reset,
    setDuck(value) {
      duck = clamp(value, 0, 1);
      if (voice && !voice.stopping) voice.gain.gain.setTargetAtTime(voice.candidate.gain * duck, ctx.currentTime, 0.2);
    },
    get state() { return { active, voices: voice ? [voice.candidate.asset.id] : [],
      anchor: voice?.candidate.anchor ? { ...voice.candidate.anchor } : null,
      decodedBytes: cached?.bytes ?? 0, loading: loading ? 1 : 0, errors: [...errors] }; },
    dispose() { disposed = true; active = false; reset(); },
  };
}

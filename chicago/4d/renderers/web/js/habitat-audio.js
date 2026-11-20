// SPDX-License-Identifier: GPL-3.0-or-later
// Recorded habitat phrases, qualified by the scene's own fauna and flora records.
// No animal is invented near the listener: audible-only insects are a broad bed;
// bird/mammal proxies are distant, offscreen calls with fixed world anchors.
import { seasonalHabitatScene, seasonalHabitatPlacement, seasonalHabitatEligible, seasonalSourceProfile }
  from './habitat-seasons.js';
import { TOWN_HABITAT, townHabitatScene, townHabitatPlacement, townHabitatEligible, parkwayElms, nearestElm }
  from './habitat-town.js';
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
  const dated1835 = String(year) === '1835' && env?.time?.date === '1835-07-01'
    && env.season === 'summer' && Array.isArray(env.faunaZones)
    && (env.temperatureC == null || (finite(env.temperatureC) && env.temperatureC > 0));
  const seasonal1812 = seasonalHabitatScene(env, year)
    && (env.temperatureC == null || finite(env.temperatureC));
  const camera = finite(env?.camera?.position?.x) && finite(env?.camera?.position?.y) && finite(env?.camera?.position?.z);
  // T-3585: 1904's habitat is its parkway elms, not a flora zone; it needs no zone finder.
  if (townHabitatScene(env, year)) return env.terrain?.loaded === true && camera
    && (env.temperatureC == null || finite(env.temperatureC));
  return (dated1835 || seasonal1812) && env?.terrain?.loaded === true
    && typeof env.flora?.zoneAt === 'function' && camera;
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
  try { return typeof sample === 'function' ? sample.call(terrain, e, n) : undefined; }
  catch { return undefined; }
}

function dryGround(terrain, e, n) {
  try {
    const ground = groundAt(terrain, e, n);
    return finite(ground) && ground > 0 && (typeof terrain?.isWater !== 'function' || !terrain.isWater(e, n));
  } catch { return false; }
}
function profileFor(p) {
  return p.scene_id === '1812' ? seasonalSourceProfile(p)
    : { rings: [44, 64, 84], near: HABITAT_AUDIO_LIMITS.birdNearMetres, far: HABITAT_AUDIO_LIMITS.birdFarMetres, height: 1.5 };
}

function insectGain(env, placement) {
  const eye = env.camera.position, ground = groundAt(env.terrain, eye.x, -eye.z);
  const height = finite(ground) ? Math.abs(eye.y - ground) : Infinity;
  return height < 32 ? placement.gain * (1 - height / 32) ** 2 : 0;
}

function recordFor(env, placement, floraZone, period) {
  if (placement.scene_id === '1812') return seasonalHabitatEligible(placement, env, floraZone, period, hourOf(env.time.hhmm))
    ? { id: placement.id } : null;
  return env.faunaZones.find(zone => zone.scene_date === placement.scene_date
    && zone.in_modelled_extent === true && placement.zone_ids.includes(zone.id)
    && zone.extent_from?.flora_zone === floraZone
    && zone.species?.some(sp => sp.id === placement.species_id
      && sp.active_periods?.includes(period) && AUDIBLE.has(sp.july?.presence?.value)
      && VOCAL.has(sp.july?.vocalization) && PRESENT.has(sp.july?.status?.value)
      && (placement.mode !== 'habitat-insects' || sp.july.presence.value === 'audible')));
}

function placementFor(asset, year, env) {
  if (String(year) === '1812') return seasonalHabitatPlacement(asset, env, year);
  if (String(year) === TOWN_HABITAT.scene) return townHabitatPlacement(asset, env, year);
  if (asset.runtime_enabled !== true || !asset.approved_eras?.includes(String(year))) return null;
  const p = asset.scene_placement;
  if (!p || (p.scene_id != null && p.scene_id !== '1835') || p.scene_date !== '1835-07-01' || !MODES.has(p.mode)
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
  if (String(year) === TOWN_HABITAT.scene) return townCandidates(catalog, env, year, { birds, birdPhase });
  const period = habitatPeriod(env), hour = hourOf(env.time.hhmm);
  if (!period) return [];
  const eye = env.camera.position, here = zoneAt(env, eye.x, eye.z), result = [];
  for (const asset of catalog?.assets ?? []) {
    const p = placementFor(asset, year, env);
    if (!p || (finite(p.from_hour) && hour < p.from_hour)) continue;
    if (p.listener_flora_zone_ids && !p.listener_flora_zone_ids.includes(here)) continue;
    if (p.require_dry_ground && !dryGround(env.terrain, eye.x, -eye.z)) continue;
    if (p.mode === 'habitat-insects') {
      const zone = recordFor(env, p, here, period);
      const gain = insectGain(env, p);
      if (zone && gain > 0) result.push({ asset, placement: p, zone: zone.id, gain, mode: p.mode });
      continue;
    }
    if (!birds) continue;
    let candidate = null;
    const spatial = profileFor(p);
    for (const radius of spatial.rings) {
      for (let i = 0; i < 16 && !candidate; i++) {
        const angle = birdPhase + i * Math.PI / 8;
        const x = eye.x + Math.cos(angle) * radius, z = eye.z + Math.sin(angle) * radius;
        const zone = recordFor(env, p, zoneAt(env, x, z), period);
        if (!zone) continue;
        const ground = groundAt(env.terrain, x, -z);
        if (!finite(ground) || (p.require_dry_ground && !dryGround(env.terrain, x, -z))) continue;
        // The model's water plane is Y=0: a marsh call must not sit underwater.
        const sourceY = Math.max(0, ground) + spatial.height;
        if (!behindListener(env.camera, x, sourceY, z)) continue;
        const distance = Math.hypot(x - eye.x, sourceY - eye.y, z - eye.z);
        if (distance >= spatial.far || (p.scene_id === '1812' && distance < spatial.near)) continue;
        candidate = { asset, placement: p, zone: zone.id, mode: p.mode,
          anchor: { x, y: sourceY, z }, gain: p.gain * (1 - distance / spatial.far) ** 2 };
      }
      if (candidate) break;
    }
    if (candidate) result.push(candidate);
  }
  return result;
}

/** T-3585: 1904 robins sing from one real parkway elm's crown, 24-110 m away and
 * behind the listener when the phrase begins; insect beds need the listener on
 * the parkway, near its trees. At most 415 trees are read, once per second. */
function townCandidates(catalog, env, year, { birds, birdPhase }) {
  const period = habitatPeriod(env), hour = hourOf(env.time.hhmm);
  if (!period) return [];
  const eye = env.camera.position, elms = parkwayElms(env), near = nearestElm(env, elms), result = [];
  for (const asset of catalog?.assets ?? []) {
    const p = placementFor(asset, year, env);
    if (!p || !townHabitatEligible(p, env, period, hour)) continue;
    if (p.mode === 'habitat-insects') {
      const gain = near <= TOWN_HABITAT.insectReach ? insectGain(env, p) : 0;
      if (gain > 0) result.push({ asset, placement: p, zone: TOWN_HABITAT.habitat, gain, mode: p.mode });
      continue;
    }
    if (!birds) continue;
    const perches = [];
    for (const t of elms) {
      const ground = groundAt(env.terrain, t.x, -t.z);
      if (!finite(ground)) continue;
      const y = Math.max(0, ground) + TOWN_HABITAT.crownHeight;
      const distance = Math.hypot(t.x - eye.x, y - eye.y, t.z - eye.z);
      if (distance < TOWN_HABITAT.birdNear || distance >= TOWN_HABITAT.birdFar) continue;
      if (!behindListener(env.camera, t.x, y, t.z)) continue;
      perches.push({ tree: t.id, x: t.x, y, z: t.z, distance });
    }
    if (!perches.length) continue;
    const turn = ((birdPhase % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
    const perch = perches[Math.min(perches.length - 1, Math.floor(turn / (Math.PI * 2) * perches.length))];
    result.push({ asset, placement: p, zone: TOWN_HABITAT.habitat, mode: p.mode, tree: perch.tree,
      anchor: { x: perch.x, y: perch.y, z: perch.z },
      gain: p.gain * (1 - perch.distance / TOWN_HABITAT.birdFar) ** 2 });
  }
  return result;
}

function townStillEligible(candidate, catalog, env, year) {
  const asset = catalog?.assets?.find(a => a.id === candidate.asset.id);
  const p = placementFor(asset, year, env), period = habitatPeriod(env), hour = hourOf(env.time.hhmm);
  if (!p || !period || p.id !== candidate.placement.id || asset.delivery?.sha256 !== candidate.asset.delivery?.sha256
    || !townHabitatEligible(p, env, period, hour)) return false;
  if (p.mode === 'habitat-insects') {
    candidate.gain = nearestElm(env) <= TOWN_HABITAT.insectReach ? insectGain(env, p) : 0;
    return candidate.gain > 0;
  }
  // A phrase that began out of sight keeps singing if the visitor turns toward
  // its tree: the bird is in a crown the scene draws, never a body in the open.
  const { x, y, z } = candidate.anchor, eye = env.camera.position;
  const distance = Math.hypot(x - eye.x, y - eye.y, z - eye.z);
  if (distance < TOWN_HABITAT.birdNear || distance >= TOWN_HABITAT.birdFar) return false;
  candidate.gain = p.gain * (1 - distance / TOWN_HABITAT.birdFar) ** 2;
  return true;
}

function stillEligible(candidate, catalog, env, year) {
  if (!validScene(env, year)) return false;
  if (String(year) === TOWN_HABITAT.scene) return townStillEligible(candidate, catalog, env, year);
  const currentAsset = String(year) === '1812'
    ? catalog?.assets?.find(a => a.id === candidate.asset.id) : candidate.asset;
  const p = placementFor(currentAsset, year, env), period = habitatPeriod(env), hour = hourOf(env.time.hhmm);
  if (!p || !period || (finite(p.from_hour) && hour < p.from_hour)) return false;
  if (p.scene_id === '1812' && (p.id !== candidate.placement.id
    || currentAsset.delivery?.sha256 !== candidate.asset.delivery?.sha256)) return false;
  if (p.listener_flora_zone_ids && !p.listener_flora_zone_ids.includes(zoneAt(env, env.camera.position.x, env.camera.position.z))) return false;
  if (p.require_dry_ground && !dryGround(env.terrain, env.camera.position.x, -env.camera.position.z)) return false;
  if (p.mode === 'habitat-insects') {
    candidate.gain = insectGain(env, p);
    return candidate.gain > 0 && !!recordFor(env, p, zoneAt(env, env.camera.position.x, env.camera.position.z), period);
  }
  const { x, y, z } = candidate.anchor, eye = env.camera.position;
  const distance = Math.hypot(x - eye.x, y - eye.y, z - eye.z), spatial = profileFor(p);
  if (p.require_dry_ground && !dryGround(env.terrain, x, -z)) return false;
  if (distance < spatial.near || distance >= spatial.far
    || !behindListener(env.camera, x, y, z) || !recordFor(env, p, zoneAt(env, x, z), period)) return false;
  candidate.gain = p.gain * (1 - distance / spatial.far) ** 2;
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
  let nextInspect = 0, nextPhraseAt = 0, rareNextDue = 0, terrainScope = null;
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
    // A coyote whose decode finished late yields to already-due ordinary nature.
    // The shared scheduler keeps those existing deadlines and the one voice.
    if (year === '1812' && candidate.mode === 'distant-fauna'
      && habitatCandidates(catalog(), environment(), year).some(c => c.mode !== 'distant-fauna'
        && !failed.has(c.asset.id) && nextDue.get(c.asset.id) <= now())) return;
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
    if (year === '1812' && candidate.mode === 'distant-fauna') rareNextDue = nextDue.get(candidate.asset.id);
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
      if (t < lastNow) rareNextDue = 0;
      if (nextScope !== scope || (!willRun && active) || t < lastNow
        || (next === '1812' && terrainScope !== env?.terrain)) reset();
      terrainScope = env?.terrain;
      scope = nextScope; year = next; active = willRun; lastNow = t; duck = clamp(nextDuck, 0, 1);
      if (!active) return;
      updateVoice();
      if (voice || loading || t < nextInspect || t < nextPhraseAt) return;
      // Nearby habitat lookups are bounded to once per second, not every frame.
      nextInspect = t + 1000;
      const candidates = habitatCandidates(catalog(), env, year, { birdPhase: jitter(0, Math.PI * 2) });
      for (const c of candidates) if (!nextDue.has(c.asset.id)) {
        const initial = c.placement.initial_gap_seconds
          ? 1000 * jitter(...c.placement.initial_gap_seconds)
          : jitter(c.mode === 'distant-bird' ? 12000 : 6000, 20000);
        nextDue.set(c.asset.id, Math.max(t + initial, next === '1812' && c.mode === 'distant-fauna' ? rareNextDue : 0));
      }
      const due = candidates.filter(c => !failed.has(c.asset.id) && nextDue.get(c.asset.id) <= t)
        .sort((a, b) => (next === '1812' ? Number(a.mode === 'distant-fauna') - Number(b.mode === 'distant-fauna') : 0)
          || nextDue.get(a.asset.id) - nextDue.get(b.asset.id));
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

// SPDX-License-Identifier: GPL-3.0-or-later
// Recorded mechanical textures and 1812 gait contacts, never synthetic hoofs.
import { createHoofContactEvents, hoofRecording, hoofCandidates, hoofSurfaceProfile,
  extractHoofBuffers, HOOF_RECORDING, WALK_V2_CONTACTS, TEAM_FALLOFF } from './hoof-contact-events.js';
export const TRANSPORT_AUDIO_LIMITS = Object.freeze({ actors: 2, voices: 4,
  decodedBytes: 8 * 1024 * 1024, sampleRate: 48000, sourceSeconds: 24,
  // Hoofbeats (1812 first; every year since T-3587): retain all four mechanical
  // voices, add two short hoofs. Measured peak including original decode + copied
  // cuts is 8,824,988 bytes; retained cuts are 55,296 bytes. A year with no
  // approved hoof recording keeps 4 voices / 8 MiB.
  voices1812: 6, decodedBytes1812: 10 * 1024 * 1024,
  contactVoices: 2, contactBytes: 256 * 1024 });
const finite = Number.isFinite;
const point = p => p && [p.x, p.y, p.z].every(finite);
const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));

/** Only catalogued, dated, visible moving assemblies qualify. Selection is by
 * distance to each actual source, including vertical distance when flying. */
export function transportCandidates(catalog, env, year) {
  const eye = env?.camera?.position;
  if (!point(eye) || !Array.isArray(env?.transport)) return [];
  const candidates = [];
  for (const asset of catalog?.assets ?? []) {
    const p = asset.scene_placement;
    if (asset.runtime_enabled !== true || !asset.approved_eras?.includes(String(year))
      || p?.mode !== 'moving-transport' || !['harness', 'wagon'].includes(p.anchor)
      || !finite(p.gain) || p.gain <= 0 || p.gain > .3
      || !finite(p.max_distance_m) || p.max_distance_m <= 0 || p.max_distance_m > 48
      || !Array.isArray(p.bindings) || !asset.delivery?.sha256 || typeof asset.url !== 'string') continue;
    const binding = p.bindings.find(b => b.scene === String(year) && b.scene_date === env.time?.date);
    if (!Array.isArray(binding?.actor_ids)) continue;
    // T-3587: a binding may carry its own level (a light 1904 brougham's wheels
    // are quieter than a loaded wagon's), never above the placement's own cap.
    const level = finite(binding.gain) && binding.gain > 0 && binding.gain <= p.gain ? binding.gain : p.gain;
    for (const actor of env.transport) {
      const anchor = actor.anchors?.[p.anchor];
      if (actor.scene !== String(year) || actor.moving !== true || !finite(actor.speed) || actor.speed <= 0
        || !binding.actor_ids.includes(actor.id) || !point(anchor)) continue;
      const distance = Math.hypot(anchor.x - eye.x, anchor.y - eye.y, anchor.z - eye.z);
      if (distance >= p.max_distance_m) continue;
      candidates.push({ key: `${actor.id}:${asset.id}`, actor: actor.id, asset, anchor, distance,
        gain: level * (1 - distance / p.max_distance_m) ** TEAM_FALLOFF * clamp(actor.speed / 1.3, 0, 1) });
    }
  }
  candidates.sort((a, b) => a.distance - b.distance || a.key.localeCompare(b.key));
  const actors = [...new Set(candidates.map(c => c.actor))].slice(0, TRANSPORT_AUDIO_LIMITS.actors);
  return candidates.filter(c => actors.includes(c.actor)).slice(0, TRANSPORT_AUDIO_LIMITS.voices);
}

/** Two mechanical buffers and two tiny recorded hoof cuts share ONE fetch/decode
 * reservation, retained across resets until it settles. Contact timing comes
 * from the actual loaded horse's gait; the full hoof recording is never looped. */
export function createTransportAudio({ ctx, output, catalog, environment, decodeAudio,
  fetcher = globalThis.fetch?.bind(globalThis), base = new URL('../audio/', import.meta.url),
  now = () => performance.now(), random = Math.random, onError = () => {} } = {}) {
  let disposed = false, active = false, year = '', scope = '', generation = 0, duck = 1;
  let loading = null, controller = null, lastNow = 0;
  let targets = new Map();
  let hoofAsset = null, hoofBuffers = [], contactSerial = 0, peakDecodedBytes = 0;
  const contacts = createHoofContactEvents();
  const buffers = new Map(), voices = new Map(), due = new Map(), failed = new Set(), errors = new Set();
  const bufferBytes = b => b.length * b.numberOfChannels * 4;
  const contactBytes = () => hoofBuffers.reduce((n, b) => n + bufferBytes(b), 0);
  const bytes = () => [...buffers.values()].reduce((n, b) => n + bufferBytes(b), contactBytes());
  // T-3587: the hoof allowance follows an approved hoof recording, in any year.
  const hoofs = () => !!hoofRecording(catalog?.(), year);
  const byteLimit = () => hoofs() ? TRANSPORT_AUDIO_LIMITS.decodedBytes1812 : TRANSPORT_AUDIO_LIMITS.decodedBytes;
  const voiceLimit = () => hoofs() ? TRANSPORT_AUDIO_LIMITS.voices1812 : TRANSPORT_AUDIO_LIMITS.voices;
  const countVoices = kind => [...voices.values()].filter(v => v.kind === kind).length;
  const jitter = (a, b) => a + clamp(random(), 0, 1) * (b - a);
  function release(key, v) {
    v.source.onended = null;
    v.source.disconnect(); v.filter?.disconnect(); v.envelope.disconnect(); v.gain.disconnect(); v.pan.disconnect();
    if (voices.get(key) === v) voices.delete(key);
  }
  function stop(key, immediate = false) {
    const v = voices.get(key); if (!v) return;
    if (immediate) {
      try { v.source.stop(); } catch { /* already ended */ }
      release(key, v);
    } else if (!v.stopping) {
      v.stopping = true; v.gain.gain.setTargetAtTime(0, ctx.currentTime, .02);
      v.source.stop(ctx.currentTime + .08);
    } // Reserve the slot until its fade has actually ended.
  }
  function reset() {
    generation++; active = false; controller?.abort(); controller = null;
    targets.clear(); buffers.clear(); due.clear(); failed.clear();
    contacts.reset(); hoofBuffers = []; hoofAsset = null; peakDecodedBytes = 0;
    for (const key of voices.keys()) stop(key, true);
    // A decode cannot be cancelled: keep loading reserved until finally.
  }
  function apply(key, candidate) {
    const v = voices.get(key); if (!v || v.stopping) return;
    v.gain.gain.setTargetAtTime(candidate.gain * duck, ctx.currentTime, .08);
    for (const axis of ['x', 'y', 'z'])
      v.pan[`position${axis.toUpperCase()}`].setTargetAtTime(candidate.anchor[axis], ctx.currentTime, .1);
  }
  function start(candidate, buffer) {
    const hoof = candidate.kind === 'hoof', kind = hoof ? 'hoof' : 'mechanical';
    if (!active || disposed || voices.has(candidate.key) || voices.size >= voiceLimit()
      || (hoof && !hoofAsset) || countVoices(kind) >= (hoof ? TRANSPORT_AUDIO_LIMITS.contactVoices : TRANSPORT_AUDIO_LIMITS.voices)) return;
    const source = ctx.createBufferSource(), envelope = ctx.createGain(), gain = ctx.createGain(), pan = ctx.createPanner();
    const filter = hoof ? ctx.createBiquadFilter() : null;
    source.buffer = buffer; source.loop = false; gain.gain.value = candidate.gain * duck;
    pan.panningModel = 'HRTF'; pan.rolloffFactor = 0;
    for (const axis of ['x', 'y', 'z']) pan[`position${axis.toUpperCase()}`].value = candidate.anchor[axis];
    if (filter) {
      filter.type = 'lowpass'; filter.frequency.value = candidate.lowpassHz; filter.Q.value = Math.SQRT1_2;
      source.connect(filter); filter.connect(envelope);
    } else source.connect(envelope);
    envelope.connect(gain); gain.connect(pan); pan.connect(output);
    const t = ctx.currentTime, duration = hoof ? buffer.duration : Math.min(buffer.duration, jitter(4, 6));
    const offset = hoof ? 0 : jitter(0, Math.max(0, buffer.duration - duration));
    if (hoof) {
      source.playbackRate.value = 1; envelope.gain.setValueAtTime(1, t);
    } else {
      envelope.gain.setValueAtTime(0, t);
      envelope.gain.linearRampToValueAtTime(1, t + .15);
      envelope.gain.setValueAtTime(1, t + duration - .3);
      envelope.gain.linearRampToValueAtTime(0, t + duration);
    }
    const v = { source, filter, envelope, gain, pan, kind, actor: candidate.actor,
      epoch: candidate.epoch, candidate, asset: candidate.asset.id, stopping: false };
    voices.set(candidate.key, v); source.onended = () => release(candidate.key, v);
    source.start(t, offset, duration);
    if (!hoof) due.set(candidate.key, now() + 1000 * (duration + jitter(.25, 1)));
  }
  async function load(candidate) {
    const hoof = candidate.kind === 'hoof';
    if (loading || failed.has(candidate.asset.id) || (hoof ? hoofBuffers.length > 0 || !hoofAsset : buffers.size >= 2)) return;
    const own = generation, token = {}, abort = new AbortController();
    loading = token; controller = abort;
    try {
      const r = await fetcher(new URL(candidate.asset.url, base), { signal: abort.signal });
      if (!r.ok) throw Error(`HTTP ${r.status}`);
      const encoded = await r.arrayBuffer();
      if (disposed || own !== generation || !active) return;
      if (hoof) {
        if (encoded.byteLength !== HOOF_RECORDING.encodedBytes) throw Error('hoof recording delivery size mismatch');
        const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', encoded))]
          .map(n => n.toString(16).padStart(2, '0')).join('');
        if (hash !== HOOF_RECORDING.sha256) throw Error('hoof recording differs from bounded source windows');
        if (disposed || own !== generation || !active) return;
      }
      const b = await decodeAudio(encoded);
      if (disposed || own !== generation || !active) return;
      const size = b.length * b.numberOfChannels * 4;
      if (b.numberOfChannels !== 1 || !finite(b.duration) || b.duration < 1 || b.duration > TRANSPORT_AUDIO_LIMITS.sourceSeconds
        || !finite(b.sampleRate) || b.sampleRate > TRANSPORT_AUDIO_LIMITS.sampleRate || b.sampleRate <= 0
        || !finite(b.length) || b.length <= 0 || !finite(size) || bytes() + size > byteLimit())
        throw Error('transport recording exceeds shared mono 48 kHz decode budget');
      if (hoof) {
        // Account for both the full decode and the copies simultaneously. Only
        // the cuts survive this call; no full recording is retained or replayed.
        const cutsBytes = HOOF_RECORDING.windows.reduce((n, w) => n
          + (Math.round(w.end * b.sampleRate) - Math.round(w.start * b.sampleRate)) * 4, 0);
        const peak = bytes() + size + cutsBytes;
        if (peak > byteLimit() || cutsBytes > TRANSPORT_AUDIO_LIMITS.contactBytes)
          throw Error('hoof source plus excerpt copies exceed peak decode budget');
        hoofBuffers = extractHoofBuffers(ctx, b, TRANSPORT_AUDIO_LIMITS.contactBytes);
        peakDecodedBytes = Math.max(peakDecodedBytes, peak);
      } else {
        buffers.set(candidate.asset.id, b); peakDecodedBytes = Math.max(peakDecodedBytes, bytes());
      }
      // The next sync re-reads the live actor before playing a late load.
    } catch (e) {
      if (own === generation && !disposed && e.name !== 'AbortError') {
        failed.add(candidate.asset.id); const message = `${candidate.asset.id}: ${e.message}`;
        errors.add(message); onError(message);
      }
    } finally {
      if (loading === token) loading = null;
      if (controller === abort) controller = null;
    }
  }
  function stopContacts() {
    contacts.reset();
    for (const [key, v] of voices) if (v.kind === 'hoof') stop(key, true);
  }
  return {
    frame({ enabled = false, year: nextYear } = {}) {
      if (disposed) return;
      // Do not traverse horse matrices while muted, in other eras, or before
      // catalog eligibility. Door audio uses a separate cheap environment read.
      if (!active || !enabled || String(nextYear) !== year || !hoofAsset) {
        stopContacts(); return;
      }
      const env = environment() ?? {}, t = now();
      if (`${year}|${env.time?.date ?? ''}` !== scope) { stopContacts(); return; }
      const live = hoofCandidates(hoofAsset, env, year);
      for (const [key, v] of voices) if (v.kind === 'hoof'
        && !live.some(c => c.actor === v.actor && c.epoch === v.epoch)) stop(key, true);
      const events = contacts.sync({ enabled: true, scope, nowMs: t,
        actors: hoofBuffers.length ? live.map(c => ({ id: c.actor, epoch: c.epoch, eligible: true, horses: c.horses })) : [] });
      events.sort((a, b) => live.find(c => c.actor === a.actor).distance - live.find(c => c.actor === b.actor).distance
        || a.actor.localeCompare(b.actor) || a.horse.localeCompare(b.horse));
      for (const event of events) {
        const candidate = live.find(c => c.actor === event.actor);
        const snow = typeof env.snowCoverAt === 'function' ? env.snowCoverAt(event.position) : env.snowCover;
        const profile = hoofSurfaceProfile(snow);
        const foot = WALK_V2_CONTACTS.contacts.findIndex(c => c.foot === event.foot);
        const variant = Math.abs(event.cycle + foot + (event.horse === 'left' ? 1 : 0)) % hoofBuffers.length;
        start({ ...candidate, ...profile, gain: candidate.gain * profile.gain, anchor: event.position,
          key: `hoof:${event.actor}:${event.horse}:${event.foot}:${++contactSerial}` }, hoofBuffers[variant]);
      }
      // Existing mechanics get both buffers first; one shared decode remains the
      // limit. A late hoof decode primes only a fresh subsequent observation.
      if (live.length && !hoofBuffers.length
        && ![...targets.values()].some(c => !buffers.has(c.asset.id) && !failed.has(c.asset.id))) void load(live[0]);
    },
    sync({ enabled, year: nextYear, duck: nextDuck = 1 } = {}) {
      if (disposed) return;
      const env = environment() ?? {}, next = String(nextYear ?? ''), t = now();
      const nextScope = `${next}|${env.time?.date ?? ''}`;
      const willRun = !!enabled && !!output;
      if (nextScope !== scope || (!willRun && active) || t < lastNow) reset();
      scope = nextScope; year = next; active = willRun; lastNow = t; duck = clamp(nextDuck, 0, 1);
      if (!active) return;
      const currentCatalog = catalog();
      hoofAsset = hoofRecording(currentCatalog, year);
      targets = new Map(transportCandidates(currentCatalog, env, year).map(c => [c.key, c]));
      const liveHoofs = hoofAsset ? hoofCandidates(hoofAsset, env, year) : [];
      for (const [key, v] of voices) {
        if (v.kind === 'hoof') { if (!liveHoofs.some(c => c.actor === v.actor && c.epoch === v.epoch)) stop(key, true); }
        else if (!targets.has(key)) stop(key);
      }
      for (const key of due.keys()) if (!targets.has(key)) due.delete(key);
      for (const [key, candidate] of targets) {
        if (voices.has(key)) { apply(key, candidate); continue; }
        if (failed.has(candidate.asset.id) || (due.get(key) ?? 0) > t) continue;
        const buffer = buffers.get(candidate.asset.id);
        if (buffer) start(candidate, buffer);
        else void load(candidate);
      }
    },
    reset,
    setDuck(value) {
      duck = clamp(value, 0, 1); for (const [key, c] of targets) apply(key, c);
      for (const [key, v] of voices) if (v.kind === 'hoof') apply(key, v.candidate);
    },
    get state() { return { active, voices: [...voices.keys()], decodedBytes: bytes(), loading: loading ? 1 : 0,
      decodedByteLimit: byteLimit(), voiceLimit: voiceLimit(), peakDecodedBytes,
      contactDecodedBytes: contactBytes(), contactVoices: countVoices('hoof'), contactTracker: contacts.state,
      contacts: [...voices.values()].filter(v => v.kind === 'hoof').map(v => ({ actor: v.actor,
        surface: v.candidate.surface, snowCover: v.candidate.snowCover, lowpassHz: v.candidate.lowpassHz })),
      sources: [...targets.values()].map(c => ({ actor: c.actor, asset: c.asset.id, anchor: { ...c.anchor }, gain: c.gain * duck })), errors: [...errors] }; },
    dispose() { disposed = true; reset(); },
  };
}

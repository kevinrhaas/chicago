// SPDX-License-Identifier: GPL-3.0-or-later
// Recorded mechanical textures, never a synthetic gait or an invisible actor.
export const TRANSPORT_AUDIO_LIMITS = Object.freeze({ actors: 2, voices: 4,
  decodedBytes: 8 * 1024 * 1024, sampleRate: 48000, sourceSeconds: 24 });
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
    for (const actor of env.transport) {
      const anchor = actor.anchors?.[p.anchor];
      if (actor.scene !== String(year) || actor.moving !== true || !finite(actor.speed) || actor.speed <= 0
        || !binding.actor_ids.includes(actor.id) || !point(anchor)) continue;
      const distance = Math.hypot(anchor.x - eye.x, anchor.y - eye.y, anchor.z - eye.z);
      if (distance >= p.max_distance_m) continue;
      candidates.push({ key: `${actor.id}:${asset.id}`, actor: actor.id, asset, anchor, distance,
        gain: p.gain * (1 - distance / p.max_distance_m) ** 2 * clamp(actor.speed / 1.3, 0, 1) });
    }
  }
  candidates.sort((a, b) => a.distance - b.distance || a.key.localeCompare(b.key));
  const actors = [...new Set(candidates.map(c => c.actor))].slice(0, TRANSPORT_AUDIO_LIMITS.actors);
  return candidates.filter(c => actors.includes(c.actor)).slice(0, TRANSPORT_AUDIO_LIMITS.voices);
}

/** Two shared mono buffers; one fetch/decode in flight, retained across resets
 * until it settles. Short unpitched excerpts have independent edge envelopes.
 * Motion changes gain and position, not the recorded timing of discrete hoofs. */
export function createTransportAudio({ ctx, output, catalog, environment, decodeAudio,
  fetcher = globalThis.fetch?.bind(globalThis), base = new URL('../audio/', import.meta.url),
  now = () => performance.now(), random = Math.random, onError = () => {} } = {}) {
  let disposed = false, active = false, year = '', scope = '', generation = 0, duck = 1;
  let loading = null, controller = null, lastNow = 0;
  let targets = new Map();
  const buffers = new Map(), voices = new Map(), due = new Map(), failed = new Set(), errors = new Set();
  const bytes = () => [...buffers.values()].reduce((n, b) => n + b.length * b.numberOfChannels * 4, 0);
  const jitter = (a, b) => a + clamp(random(), 0, 1) * (b - a);
  function release(key, v) {
    v.source.onended = null;
    v.source.disconnect(); v.envelope.disconnect(); v.gain.disconnect(); v.pan.disconnect();
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
    if (!active || disposed || voices.has(candidate.key) || voices.size >= TRANSPORT_AUDIO_LIMITS.voices) return;
    const source = ctx.createBufferSource(), envelope = ctx.createGain(), gain = ctx.createGain(), pan = ctx.createPanner();
    source.buffer = buffer; source.loop = false; gain.gain.value = candidate.gain * duck;
    pan.panningModel = 'HRTF'; pan.rolloffFactor = 0;
    for (const axis of ['x', 'y', 'z']) pan[`position${axis.toUpperCase()}`].value = candidate.anchor[axis];
    source.connect(envelope); envelope.connect(gain); gain.connect(pan); pan.connect(output);
    const t = ctx.currentTime, duration = Math.min(buffer.duration, jitter(4, 6));
    const offset = jitter(0, Math.max(0, buffer.duration - duration));
    envelope.gain.setValueAtTime(0, t);
    envelope.gain.linearRampToValueAtTime(1, t + .15);
    envelope.gain.setValueAtTime(1, t + duration - .3);
    envelope.gain.linearRampToValueAtTime(0, t + duration);
    const v = { source, envelope, gain, pan, asset: candidate.asset.id, stopping: false };
    voices.set(candidate.key, v); source.onended = () => release(candidate.key, v);
    source.start(t, offset, duration);
    due.set(candidate.key, now() + 1000 * (duration + jitter(.25, 1)));
  }
  async function load(candidate) {
    if (loading || buffers.size >= 2) return;
    const own = generation, token = {}, abort = new AbortController();
    loading = token; controller = abort;
    try {
      const r = await fetcher(new URL(candidate.asset.url, base), { signal: abort.signal });
      if (!r.ok) throw Error(`HTTP ${r.status}`);
      const encoded = await r.arrayBuffer();
      if (disposed || own !== generation || !active) return;
      const b = await decodeAudio(encoded);
      if (disposed || own !== generation || !active) return;
      const size = b.length * b.numberOfChannels * 4;
      if (b.numberOfChannels !== 1 || !finite(b.duration) || b.duration < 1 || b.duration > TRANSPORT_AUDIO_LIMITS.sourceSeconds
        || !finite(b.sampleRate) || b.sampleRate > TRANSPORT_AUDIO_LIMITS.sampleRate || b.sampleRate <= 0
        || !finite(b.length) || b.length <= 0 || !finite(size) || bytes() + size > TRANSPORT_AUDIO_LIMITS.decodedBytes)
        throw Error('transport recording exceeds two mono 48 kHz buffers / 8 MiB');
      buffers.set(candidate.asset.id, b);
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
  return {
    sync({ enabled, year: nextYear, duck: nextDuck = 1 } = {}) {
      if (disposed) return;
      const env = environment() ?? {}, next = String(nextYear ?? ''), t = now();
      const nextScope = `${next}|${env.time?.date ?? ''}`;
      const willRun = !!enabled && !!output;
      if (nextScope !== scope || (!willRun && active) || t < lastNow) reset();
      scope = nextScope; year = next; active = willRun; lastNow = t; duck = clamp(nextDuck, 0, 1);
      if (!active) return;
      targets = new Map(transportCandidates(catalog(), env, year).map(c => [c.key, c]));
      for (const key of voices.keys()) if (!targets.has(key)) stop(key);
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
    setDuck(value) { duck = clamp(value, 0, 1); for (const [key, c] of targets) apply(key, c); },
    get state() { return { active, voices: [...voices.keys()], decodedBytes: bytes(), loading: loading ? 1 : 0,
      sources: [...targets.values()].map(c => ({ actor: c.actor, asset: c.asset.id, anchor: { ...c.anchor }, gain: c.gain * duck })), errors: [...errors] }; },
    dispose() { disposed = true; reset(); },
  };
}

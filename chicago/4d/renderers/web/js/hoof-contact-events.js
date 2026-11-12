// SPDX-License-Identifier: GPL-3.0-or-later
// Reconstructed gait-synchronous contacts. No independent beat clock or queue.
// Phases describe settling near each hoof's own rest surface in the measured
// clip. They do not certify literal world-ground contact or biological gait.
export const WALK_V2_CONTACTS = Object.freeze({
  clipSha256: 'b122c987c5dd7fdd33b77516e532f3fea54919cd4a28ec0028a5cdb708e6f50f',
  modelSha256: 'ad9dc060f8630d0de04fef97d716e8c82be3ac8bf070684e78107720c5221ec6',
  strideM: 1,
  contacts: Object.freeze([
    Object.freeze({ foot: 'fore_l', phase: .21484375 }),
    Object.freeze({ foot: 'hind_r', phase: .46484375 }),
    Object.freeze({ foot: 'fore_r', phase: .71484375 }),
    Object.freeze({ foot: 'hind_l', phase: .96484375 }),
  ]),
});
export const LIMITS = Object.freeze({ actors: 2, horsesPerActor: 2, eventsPerFrame: 4,
  frameGapMs: 125, eventAgeMs: 50, advanceM: .25, cyclesPerFrame: .25 });
const finite = Number.isFinite;
const point = p => p && [p.x, p.y, p.z].every(finite);

/** A pure event producer fed once AFTER the accepted simulation steps for a
 * rendered frame. Call even while muted/paused/dwelling/culled, or call reset.
 * Inputs must carry the live clip/model bindings, a per-assembly epoch (changed
 * on reload/teleport), real horse distance, and actual hoof-bone world positions.
 * The caller admits nearest actors and sets eligible only for loaded, drawn,
 * moving, supported, era/date/surface-approved actors with a ready recorded excerpt.
 * Missing or ineligible horses lose their baseline immediately. First sightings
 * only establish phase. Crossing events are returned once, never retained.
 */
export function createHoofContactEvents({ contract = WALK_V2_CONTACTS } = {}) {
  if (!(finite(contract.strideM) && contract.strideM > 0)
    || typeof contract.clipSha256 !== 'string' || typeof contract.modelSha256 !== 'string'
    || !Array.isArray(contract.contacts) || contract.contacts.length !== 4
    || new Set(contract.contacts.map(c => c.foot)).size !== 4
    || !contract.contacts.every(c => typeof c.foot === 'string' && finite(c.phase) && c.phase >= 0 && c.phase < 1))
    throw Error('A measured bound four-contact gait contract is required');
  let prior = new Map(), scope = null, lastTime = null, disposed = false;
  function reset() { prior.clear(); scope = null; lastTime = null; }
  return {
    reset,
    dispose() { disposed = true; reset(); },
    get state() { return { trackedHorses: prior.size, queuedEvents: 0, disposed }; },
    sync({ enabled = false, scope: nextScope, nowMs, actors = [] } = {}) {
      if (disposed) return [];
      if (!enabled || typeof nextScope !== 'string' || !nextScope || !finite(nowMs)
        || !Array.isArray(actors)) { reset(); return []; }
      if (scope !== nextScope || (lastTime !== null && (nowMs <= lastTime || nowMs - lastTime > LIMITS.frameGapMs))) prior.clear();
      scope = nextScope; lastTime = nowMs;
      const next = new Map(), events = [], actorIds = new Set();
      for (const actor of actors) {
        if (actorIds.size >= LIMITS.actors) break;
        if (!actor || actor.eligible !== true || typeof actor.id !== 'string' || !actor.id
          || actorIds.has(actor.id) || typeof actor.epoch !== 'string' || !actor.epoch
          || !Array.isArray(actor.horses)) continue;
        actorIds.add(actor.id);
        const horseIds = new Set();
        for (const horse of actor.horses) {
          if (horseIds.size >= LIMITS.horsesPerActor) break;
          if (!horse || typeof horse.id !== 'string' || !horse.id || horseIds.has(horse.id)
            || horse.clipSha256 !== contract.clipSha256 || horse.modelSha256 !== contract.modelSha256
            || horse.strideM !== contract.strideM || !finite(horse.distanceM) || horse.distanceM < 0
            || !contract.contacts.every(c => point(horse.hooves?.[c.foot]))) continue;
          horseIds.add(horse.id);
          const key = JSON.stringify([actor.id, actor.epoch, horse.id]), old = prior.get(key);
          next.set(key, { distanceM: horse.distanceM, nowMs });
          if (!old) continue;
          const delta = horse.distanceM - old.distanceM, elapsed = nowMs - old.nowMs;
          if (!(delta > 0) || delta > LIMITS.advanceM || delta / contract.strideM > LIMITS.cyclesPerFrame
            || !(elapsed > 0) || elapsed > LIMITS.frameGapMs) continue;
          const before = old.distanceM / contract.strideM, after = horse.distanceM / contract.strideM;
          for (const contact of contract.contacts) {
            // Half-open (before, after] interval prevents duplicate boundary hits.
            const crossing = Math.floor(before - contact.phase) + 1 + contact.phase;
            if (crossing > after) continue;
            const atMs = old.nowMs + (crossing - before) / (after - before) * elapsed;
            if (nowMs - atMs > LIMITS.eventAgeMs) continue; // drop old impacts; never catch up
            events.push({ actor: actor.id, horse: horse.id, epoch: actor.epoch, scope,
              foot: contact.foot, phase: contact.phase, cycle: Math.floor(crossing),
              atMs, observedAtMs: nowMs, position: { ...horse.hooves[contact.foot] },
              clipSha256: contract.clipSha256 });
          }
        }
      }
      prior = next;
      // Stable ordering; newest first if a frame exceeds the explicit event cap.
      return events.sort((a, b) => b.atMs - a.atMs || a.actor.localeCompare(b.actor)
        || a.horse.localeCompare(b.horse) || a.foot.localeCompare(b.foot))
        .slice(0, LIMITS.eventsPerFrame);
    },
  };
}

// Freesound 159498, davilca, CC0: two real horses walking on a dirt road.
// These short transients were bounded from the delivered MP3's 1ms RMS envelope,
// not by a claimed audition. They are reconstructed individual-contact proxies.
// No pitch shift, stretching, synthetic impact or new uploaded derivative.
export const HOOF_RECORDING = Object.freeze({
  id: 'horse-walking',
  sha256: '1e9d75c58b4bb7bc87bd8251433afd60ccdfbda20571efce62262b23d598836c',
  encodedBytes: 170540, maxSeconds: 12,
  windows: Object.freeze([
    Object.freeze({ start: 3.297, end: 3.425 }),
    Object.freeze({ start: 6.710, end: 6.870 }),
  ]),
});
const VIEW_DATES_1812 = Object.freeze({ summer: '1812-08-14', spring: '1812-04-15',
  fall: '1812-10-15', winter: '1812-02-15' });
const ACTORS_1812 = new Set(['fort_wagon_loop_1812', 'shore_road_wagon_haul_1812']);
const clamp01 = n => Math.max(0, Math.min(1, n));

/** Uses the ground renderer's actual snow-look amount, not a month heuristic.
 * A damped dirt recording is an explicit acoustic proxy for snow-covered ground;
 * it is neither a real snow recording nor a measurement of depth at this hoof. */
export function hoofSurfaceProfile(snowCover) {
  const amount = finite(snowCover) ? clamp01(snowCover) : 0;
  return { snowCover: amount, gain: 1 - .45 * amount,
    lowpassHz: 18000 * (900 / 18000) ** amount,
    surface: amount > 0 ? 'snow-damped-dirt-recording-proxy' : 'recorded-dirt-contact-proxy' };
}

export function hoofRecording(catalog) {
  return (catalog?.assets ?? []).find(a => a.id === HOOF_RECORDING.id
    && a.runtime_enabled === true && a.approved_eras?.includes('1812')
    && a.scene_placement?.mode === 'hoof-contact'
    && a.delivery?.sha256 === HOOF_RECORDING.sha256
    && a.delivery?.bytes === HOOF_RECORDING.encodedBytes
    && typeof a.url === 'string') ?? null;
}

/** Exact seasonal viewing dates preserve the scene's dated interpretation.
 * Winter/spring/fall are the existing reconstructed viewing modes, not claims
 * that the August scene's people were documented at these places on those days. */
export function hoofCandidates(asset, env, year) {
  const eye = env?.camera?.position, p = asset?.scene_placement;
  const season = env?.season ?? 'summer';
  if (String(year) !== '1812' || !asset || !point(eye) || !Array.isArray(env?.transport)
    || VIEW_DATES_1812[season] !== env.time?.date
    || !finite(p?.gain) || p.gain <= 0 || p.gain > .3
    || !finite(p.max_distance_m) || p.max_distance_m <= 0 || p.max_distance_m > 48) return [];
  const binding = p.bindings?.find(b => b.scene === '1812' && b.scene_date === env.time.date && b.season === season);
  if (!Array.isArray(binding?.actor_ids)) return [];
  const out = [];
  for (const actor of env.transport) {
    const team = actor.anchors?.hoof;
    if (actor.scene !== '1812' || !ACTORS_1812.has(actor.id) || !binding.actor_ids.includes(actor.id)
      || actor.moving !== true || !finite(actor.speed) || actor.speed <= 0
      || !team || typeof team.epoch !== 'string' || !team.epoch || !Array.isArray(team.horses)) continue;
    const horses = team.horses.filter(h => h.modelSha256 === WALK_V2_CONTACTS.modelSha256
      && h.clipSha256 === WALK_V2_CONTACTS.clipSha256 && h.strideM === WALK_V2_CONTACTS.strideM
      && finite(h.distanceM) && h.distanceM >= 0
      && WALK_V2_CONTACTS.contacts.every(c => point(h.hooves?.[c.foot]))).slice(0, 2);
    if (!horses.length) continue;
    const distance = Math.min(...horses.flatMap(h => WALK_V2_CONTACTS.contacts.map(c => {
      const at = h.hooves[c.foot]; return Math.hypot(at.x - eye.x, at.y - eye.y, at.z - eye.z);
    })));
    if (distance >= p.max_distance_m) continue;
    out.push({ kind: 'hoof', key: `${actor.id}:${asset.id}`, actor: actor.id, epoch: team.epoch,
      horses, asset, distance, gain: p.gain * (1 - distance / p.max_distance_m) ** 2 });
  }
  return out.sort((a, b) => a.distance - b.distance || a.key.localeCompare(b.key)).slice(0, 2);
}

/** Copy only the two bounded excerpts; caller drops the full decoded recording.
 * Peak memory includes that full buffer AND both new cuts until this returns. */
export function extractHoofBuffers(ctx, decoded, maxBytes = 256 * 1024) {
  if (decoded.numberOfChannels !== 1 || !finite(decoded.sampleRate) || decoded.sampleRate <= 0
    || decoded.sampleRate > 48000 || !finite(decoded.duration) || decoded.duration > HOOF_RECORDING.maxSeconds
    || decoded.duration < HOOF_RECORDING.windows.at(-1).end || typeof decoded.getChannelData !== 'function')
    throw Error('hoof recording exceeds mono 48kHz bounded source contract');
  const lengths = HOOF_RECORDING.windows.map(w => Math.round(w.end * decoded.sampleRate) - Math.round(w.start * decoded.sampleRate));
  if (lengths.some(n => n <= 0) || lengths.reduce((n, x) => n + x * 4, 0) > maxBytes)
    throw Error('hoof excerpts exceed their shared 256KiB cache');
  const samples = decoded.getChannelData(0);
  return HOOF_RECORDING.windows.map((w, index) => {
    const start = Math.round(w.start * decoded.sampleRate), length = lengths[index];
    if (start + length > samples.length) throw Error('hoof excerpt runs beyond decoded source');
    const cut = ctx.createBuffer(1, length, decoded.sampleRate), target = cut.getChannelData(0);
    target.set(samples.subarray(start, start + length));
    const fade = Math.max(1, Math.min(Math.round(.002 * decoded.sampleRate), Math.floor(length / 2)));
    for (let i = 0; i < fade; i++) { target[i] *= i / fade; target[length - 1 - i] *= i / fade; }
    return cut;
  });
}

/** T-1275: researched content over boot events; never part of readiness. */
import { EARLY_ENTRIES } from './loading-early.js';
export const ARRIVAL_LINE = 'You have arrived in Chicago, summer 1835.';
export const CONTENT_PHASE = { scene:'assess', terrain:'collect', buildings:'collect',
  ground:'prepare', flora:'prepare', people:'resolve', census:'resolve', interaction:'resolve' };
export function randomFor(seed) {
  let s = 2166136261;
  for (const c of String(seed)) s = Math.imul(s ^ c.charCodeAt(0), 16777619);
  return () => { s += 0x6D2B79F5; let t = s; t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61); return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
export function createBags(entries, seed) {
  const random = randomFor(seed), humorAllowed = random() < 0.005;
  const seen = new Map(); let last = null, humorUsed = false;
  return {
    replace(next) { entries = next; },
    next(phase, preferredKind) {
      if (phase === 'land') return null;
      const eligible = entries.filter(e => e.phase === phase &&
        (e.kind !== 'humor' || humorAllowed && !humorUsed));
      if (!eligible.length) return null;
      if (!seen.has(phase)) seen.set(phase, new Set());
      const used = seen.get(phase);
      let pool = eligible.filter(e => !used.has(e.id));
      if (!pool.length) { used.clear(); pool = eligible; }
      const fresh = pool.filter(e => e.id !== last); if (fresh.length) pool = fresh;
      const preferred = pool.filter(e => e.kind === preferredKind);
      if (preferred.length) pool = preferred;
      let n = random() * pool.reduce((sum, e) => sum + e.weight, 0);
      const entry = pool.find(e => (n -= e.weight) < 0) || pool.at(-1);
      used.add(entry.id); last = entry.id;
      if (entry.kind === 'humor') humorUsed = true;
      return entry;
    },
    get humorAllowed() { return humorAllowed; },
  };
}
export function dwellMs(entry, expectedSeconds = 2.4) {
  return Math.max(2000, Math.min(4000, Math.max(entry.min_dwell_ms, expectedSeconds * 1000)));
}
export function createLoadingContent({ boot, cardEl, seed = Math.random(),
  now = () => performance.now(), schedule = setTimeout, cancel = clearTimeout,
  entries = EARLY_ENTRIES, warm = false } = {}) {
  const bags = createBags(entries, seed);
  let phase = 'assess', bootPhase = 'scene', stopped = false, landed = false, failed = false;
  let timer = null, shownAt = -Infinity, current = null, count = 0, renderedBoot = null;
  function paint(entry) {
    if (!entry || !cardEl) return;
    current = entry; shownAt = now(); count++; renderedBoot = bootPhase;
    cardEl.textContent = entry.text + (entry.source_label ? ` — ${entry.source_label}` : '');
    cardEl.dataset.loadingId = entry.id; cardEl.dataset.loadingKind = entry.kind;
    cardEl.dataset.loadingPhase = entry.phase;
  }
  function tick() {
    timer = null;
    if (stopped || warm && count >= 1) return;
    const wait = current ? dwellMs(current, boot.expected?.[bootPhase]) - (now() - shownAt) : 0;
    if (wait > 0) { timer = schedule(tick, wait); return; }
    // Introduce each building/flora phase with a build, then let facts circulate.
    const preferred = renderedBoot !== bootPhase && ['buildings','flora'].includes(bootPhase) ? 'build' : undefined;
    paint(bags.next(phase, preferred));
    timer = schedule(tick, dwellMs(current, boot.expected?.[bootPhase]));
  }
  paint(bags.next('assess', 'source'));
  timer = schedule(tick, dwellMs(current, boot.expected?.scene));
  boot.on('phasestart', ({phase:p}) => {
    if (stopped || !CONTENT_PHASE[p.id]) return;
    // Optional people/census can start while the prairie is still being made.
    if (p.essential === false && boot.phases.some(q => q.essential && q.startedAt !== null && q.endedAt === null)) return;
    phase = CONTENT_PHASE[p.id]; bootPhase = p.id;
    if (timer !== null) cancel(timer);
    tick();
  });
  function stop(error = false) {
    stopped = true; failed ||= error;
    if (timer !== null) cancel(timer); timer = null;
    if (error && cardEl) { cardEl.textContent = 'The reconstruction could not finish. Please retry.';
      cardEl.dataset.loadingKind = 'error'; }
  }
  boot.on('ready', () => stop());
  boot.on('error', e => { if (e.phase?.essential !== false) stop(true); });
  return {
    stop,
    land() { if (landed || failed) return; stop(); landed = true;
      paint({id:'arrival',phase:'land',kind:'operational',text:ARRIVAL_LINE}); },
    async load(url, fetcher = fetch) {
      try { const res = await fetcher(url); if (!res.ok) return;
        const data = await res.json();
        if (!stopped && Array.isArray(data.entries) && data.entries.length && data.schema_version === 1 &&
            data.entries.every(e => typeof e.id === 'string' && typeof e.text === 'string' &&
              ['assess','collect','prepare','resolve','land'].includes(e.phase) &&
              ['source','build','fact','operational','humor'].includes(e.kind) &&
              Number.isFinite(e.weight) && e.weight > 0 &&
              Number.isFinite(e.min_dwell_ms) && e.min_dwell_ms >= 2000)) bags.replace(data.entries);
      } catch { /* Early cards remain usable; content cannot block the scene. */ }
    },
    get state() { return { phase, stopped, landed, count, id:current?.id }; },
  };
}

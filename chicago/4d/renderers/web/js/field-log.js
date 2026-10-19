/**
 * The field log (T-2660, NAV-S02; DESIGN §14 "Measure fun"): a few counts kept on this
 * device, for the student playtest, and shown in Settings › About (js/field-log-view.js).
 *
 * OWNER RULING, 2026-10-16: local-only counts. Nothing leaves the device; the audience is
 * 14 to 16. So this module imports nothing and calls nothing but localStorage: no fetch,
 * no beacon, no request of any kind, and no analytics. tools/test_field_log.mjs reads this
 * file's source for every network door and runs every event with each one trapped, and the
 * smoke (part 13) watches the page's requests while the events fire.
 *
 * What it counts, each from one call at its own hook (`count(event)`):
 *
 *   landed            the journey reaching `landed` (main.js)
 *   inspect           a building opened in Inspect or on its card; only the FIRST after a
 *                     landing counts, as `firstInspect`, with the seconds it took
 *                     (popup onShow in main.js, apps/inspect-view.js render)
 *   tab               an Inspect tab opened by the visitor (apps/inspect-view.js selectTab)
 *   showMe            Show me (main.js showMeFor)
 *   jauntStarted      a Jaunt under way at its first stop (jaunts.js start)
 *   jauntFinished     a Jaunt reaching its ending (jaunts.js dispatch)
 *   tourStep          a Field Check step reached; a reload resuming one is not (tour.js)
 *   confidencePreset  a preset picked in the Confidence view app (apps/confidence-view.js)
 *
 * The design's target is a first inspect within 90 s, so the log keeps the last time taken
 * and how many landings met it. Storage refused (a private window, blocked site data), the
 * counts are kept for this page only and nothing throws, as roam-tip.js and tour-offer.js do.
 */
export const FIELD_LOG_KEY = 'chicago4d.fieldLog';
export const QUICK_INSPECT_S = 90;

/** What is stored, in the order Settings › About lists it. */
export const COUNTS = Object.freeze(['landed', 'firstInspect', 'tab', 'showMe',
  'jauntStarted', 'jauntFinished', 'tourStep', 'confidencePreset']);
/** What the hooks may say: every count but `firstInspect`, which `inspect` decides. */
export const EVENTS = Object.freeze(['landed', 'inspect', 'tab', 'showMe',
  'jauntStarted', 'jauntFinished', 'tourStep', 'confidencePreset']);

const whole = (v) => (Number.isFinite(Number(v)) && Number(v) >= 0 ? Math.floor(Number(v)) : 0);

/** An empty log. */
export function emptyLog() {
  return { counts: Object.fromEntries(COUNTS.map((k) => [k, 0])), lastFirstInspectS: null, quick: 0 };
}

/** A log read back from storage, with anything that is not a whole count dropped. */
export function normalLog(raw) {
  const out = emptyLog();
  if (!raw || typeof raw !== 'object') return out;
  for (const k of COUNTS) out.counts[k] = whole(raw.counts?.[k]);
  out.lastFirstInspectS = raw.lastFirstInspectS == null ? null : whole(raw.lastFirstInspectS);
  out.quick = whole(raw.quick);
  return out;
}

const local = () => { try { return globalThis.localStorage ?? null; } catch { return null; } };
const clock = () => (globalThis.performance?.now?.() ?? Date.now());

export function createFieldLog({ storage = local, now = clock } = {}) {
  let memory = null;            // the log, read once from storage, then kept here as well
  let landedAt = null;          // when this page landed (now()), for time to first inspect
  let inspectedHere = false;    // the first inspect since that landing is counted
  const listeners = new Set();
  const store = () => { try { return typeof storage === 'function' ? storage() : storage; } catch { return null; } };

  function load() {
    if (memory) return memory;
    try { memory = normalLog(JSON.parse(store()?.getItem(FIELD_LOG_KEY) ?? 'null')); } catch { memory = emptyLog(); }
    return memory;
  }
  function save() {
    try { store()?.setItem(FIELD_LOG_KEY, JSON.stringify(memory)); } catch { /* kept for this page only */ }
    for (const fn of [...listeners]) { try { fn(read()); } catch { /* a painter's fault is its own */ } }
  }
  /** A copy of the log as it stands. */
  function read() {
    const log = load();
    return { counts: { ...log.counts }, lastFirstInspectS: log.lastFirstInspectS, quick: log.quick };
  }

  /** Count one event. Returns the count it changed, or null for an event this does not keep. */
  function count(event) {
    if (!EVENTS.includes(event)) return null;
    const log = load();
    if (event === 'landed') {
      landedAt = now();
      inspectedHere = false;
    }
    if (event === 'inspect') {
      if (inspectedHere) return null;
      inspectedHere = true;
      log.counts.firstInspect += 1;
      if (landedAt !== null) {
        const s = Math.max(0, Math.round((now() - landedAt) / 1000));
        log.lastFirstInspectS = s;
        if (s <= QUICK_INSPECT_S) log.quick += 1;
      }
      save();
      return log.counts.firstInspect;
    }
    log.counts[event] += 1;
    save();
    return log.counts[event];
  }

  /** Empty the log, here and in storage. */
  function clear() {
    memory = emptyLog();
    try { store()?.removeItem(FIELD_LOG_KEY); } catch { /* nothing was kept */ }
    for (const fn of [...listeners]) { try { fn(read()); } catch { /* a painter's fault is its own */ } }
    return read();
  }

  return {
    count, clear, read,
    /** Told the log after every change; returns the way to stop. */
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}

/** The page's one field log, and the one call every hook makes. */
export const fieldLog = createFieldLog();
export const count = (event) => fieldLog.count(event);

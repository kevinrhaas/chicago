/** Real boot work, independent of the gate's presentation (T-1246). */
import { BOOT_WEIGHTS } from './boot-weights.js';
export const PHASES = [
  ['scene', 'Reading the scene…'], ['terrain', 'Laying the ground and the river…'],
  ['buildings', 'Placing the buildings…'], ['ground', 'Laying the ground and the river…'],
  ['flora', 'Planting the prairie…'], ['people', 'Reading the scene…', false],
  ['census', 'Reading the scene…', false], ['interaction', 'Planting the prairie…'],
];
const KEY = 'c4d.boot.timings.v1';
const clamp = (n, base) => Math.max(base * 0.25, Math.min(base * 4, n));

export function expectedDurations({ device, detail, cache = 'cold', build, storage }) {
  const defaults = BOOT_WEIGHTS[device]?.[detail]?.[cache] ?? {};
  const result = { ...defaults };
  try {
    const history = JSON.parse(storage?.getItem(KEY) || 'null');
    const sample = history?.build === build && history?.cells?.[`${device}/${detail}`];
    for (const [id, value] of Object.entries(sample || {})) {
      if (Number.isFinite(value) && value > 0 && defaults[id] > 0) result[id] = clamp(value, defaults[id]);
    }
  } catch { /* Storage denial/corruption must never prevent entering town. */ }
  return result;
}

export function createBoot({ device = 'desktop', detail = 'full', build = '', storage,
  now = () => performance.now(), problems = [], present = () => {} } = {}) {
  const phases = PHASES.map(([id, label, essential = true]) => ({
    id, label, essential, startedAt: null, endedAt: null, units: null, unitsDone: 0, error: null,
  }));
  const listeners = new Map();
  const expected = expectedDurations({ device, detail, build, storage });
  let renderedAt = null, readyAt = null, failed = false, lastPercent = 0;
  const phase = id => {
    const p = phases.find(p => p.id === id);
    if (!p) throw new Error(`Unknown boot phase: ${id}`);
    return p;
  };
  function emit(type, p) {
    const event = { type, at: now(), phase: p ? { ...p } : null };
    for (const fn of listeners.get(type) || []) {
      try { fn(event); } catch (err) { console.warn('[boot listener]', err); }
    }
  }
  function paint(p) {
    if (!p.essential || readyAt !== null) return;
    const essential = phases.filter(p => p.essential);
    const total = essential.reduce((s, p) => s + (expected[p.id] || 1), 0);
    const done = essential.reduce((s, p) => s + (expected[p.id] || 1)
      * (p.endedAt !== null && !p.error ? 1 : p.units ? Math.min(0.99, p.unitsDone / p.units) : 0), 0);
    lastPercent = Math.max(lastPercent, Math.min(99, 100 * done / total));
    present(lastPercent, p.label);
  }
  const api = {
    phases, expected,
    get readyAt() { return readyAt; },
    get renderedAt() { return renderedAt; },
    on(type, fn) {
      if (!listeners.has(type)) listeners.set(type, new Set());
      listeners.get(type).add(fn);
      return () => listeners.get(type)?.delete(fn);
    },
    start(id, units = null) {
      const p = phase(id);
      if (p.startedAt !== null) return;
      p.startedAt = now(); p.units = units;
      emit('phasestart', p); paint(p);
    },
    progress(id, unitsDone, units = phase(id).units) {
      const p = phase(id);
      if (p.startedAt === null || p.endedAt !== null) return;
      if (Number.isFinite(units) && units >= 0) p.units = units;
      if (Number.isFinite(unitsDone)) p.unitsDone = Math.max(p.unitsDone, Math.min(p.units ?? unitsDone, unitsDone));
      emit('phaseprogress', p); paint(p);
    },
    end(id) {
      const p = phase(id);
      if (p.startedAt === null) throw new Error(`Boot phase never started: ${id}`);
      if (p.endedAt !== null) return;
      p.endedAt = now(); if (!p.error && p.units !== null) p.unitsDone = p.units;
      emit('phaseend', p); paint(p);
    },
    fail(id, err) {
      const p = phase(id);
      if (p.endedAt !== null) return;
      api.start(id); p.error = String(err?.message || err);
      problems.push(`${id}: ${p.error}`);
      if (p.essential) failed = true;
      emit('error', p); api.end(id);
    },
    frameRendered() { if (renderedAt === null) renderedAt = now(); },
    finish() {
      if (readyAt !== null || failed || renderedAt === null
        || phases.some(p => p.essential && (p.endedAt === null || p.error))) return false;
      readyAt = now(); present(100, 'Ready');
      try {
        let history = JSON.parse(storage?.getItem(KEY) || 'null');
        if (history?.build !== build) history = { build, cells: {} };
        history.cells ??= {};
        history.cells[`${device}/${detail}`] = Object.fromEntries(phases
          .filter(p => !p.error && p.endedAt !== null)
          .map(p => [p.id, clamp((p.endedAt - p.startedAt) / 1000, BOOT_WEIGHTS[device]?.[detail]?.cold?.[p.id] || 1)]));
        // One build, at most six device/tier cells; no unbounded browsing history.
        history.cells = Object.fromEntries(Object.entries(history.cells).slice(-6));
        storage?.setItem(KEY, JSON.stringify(history));
      } catch { /* Timing history is optional. */ }
      emit('ready'); return true;
    },
    timings() { return phases.map(p => ({ ...p,
      seconds: p.endedAt === null ? null : (p.endedAt - p.startedAt) / 1000,
      expectedSeconds: expected[p.id] ?? null })); },
  };
  return api;
}

/** A macrotask after a frame gives the browser a chance to paint. Hidden tabs
 * use the timer directly; no frame queue accumulates while rAF is suspended. */
export function yieldToPaint() {
  return new Promise(resolve => {
    let raf, timer, paintTimer;
    const done = () => { clearTimeout(timer); clearTimeout(paintTimer); if (raf != null) cancelAnimationFrame(raf); resolve(); };
    if (typeof document !== 'undefined' && !document.hidden && typeof requestAnimationFrame === 'function') {
      raf = requestAnimationFrame(() => { paintTimer = setTimeout(done, 0); });
      timer = setTimeout(done, 50);
    } else timer = setTimeout(done, 0);
  });
}

/** Call only at deterministic boundaries; the caller skips await when no yield
 * is due, avoiding a promise/microtask per plant. */
export function createCheckpoint({ budgetMs = 12, onProgress = () => {} } = {}) {
  let last = performance.now();
  return (done, total) => {
    if (performance.now() - last < budgetMs && !(done != null && done === total)) return null;
    onProgress(done, total);
    return yieldToPaint().then(() => { last = performance.now(); });
  };
}

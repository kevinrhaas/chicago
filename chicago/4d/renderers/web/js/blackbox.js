/**
 * blackbox.js — the page's last moments, kept where a reset cannot take them
 * (T-2826, from T-2822: an iPhone's display reset by the Glessner House that no
 * desktop or emulated phone reproduces).
 *
 * The page writes a short flight record to localStorage as it goes: what the
 * visitor just did (a tap, a card, the Navigator, a detail switch, a GPU pick
 * starting and ending) and, every few seconds, what the renderer is holding
 * (draw calls, triangles, geometries, textures, the drawing buffer, the
 * sharpness ratio) and where the eye is. It is the last `max` entries and one
 * sample, a few kilobytes, written as each entry lands, so a page the device
 * kills mid-step still leaves its last line behind.
 *
 * The next load reads the record the last page left. A record that ends in a
 * lost context, or simply stops without the page having left cleanly, is the
 * one worth showing: `summary()` puts its last steps in a line for the crash
 * card, and `report()` is the whole record as text for the card's Copy button,
 * to paste where the owner reports it. A page that left cleanly says nothing.
 *
 * No DOM and no THREE: `sample()` is handed in, and tools/test_blackbox.mjs
 * drives it with a fake store and clock.
 */

export const BLACKBOX_KEY = 'c4d.blackbox';
/** A record older than this when the next page reads it is not shown. */
export const STALE_MS = 30 * 60_000;
export const SAMPLE_MS = 3_000;

function readStore(store, key) {
  try { const raw = store?.getItem(key); return raw ? JSON.parse(raw) : null; } catch { return null; }
}

export function createBlackbox({
  year,
  build = '',
  store = (() => { try { return window.localStorage; } catch { return null; } })(),
  now = () => Date.now(),
  max = 40,
  sample = () => null,
} = {}) {
  const previous = readStore(store, BLACKBOX_KEY);
  const page = `${now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;
  const box = { page, year, build, start: now(), ended: null, last: null, entries: [] };
  let sampledAt = -Infinity;

  function write() {
    try { store?.setItem(BLACKBOX_KEY, JSON.stringify(box)); } catch { /* storage refused or full */ }
  }

  /** One step: `kind` and a few plain fields. Written at once. */
  function log(kind, data = null) {
    box.entries.push(data ? { t: now() - box.start, k: kind, ...data } : { t: now() - box.start, k: kind });
    if (box.entries.length > max) box.entries.splice(0, box.entries.length - max);
    write();
  }

  /** Once a frame; reads the renderer every SAMPLE_MS and keeps only the latest. */
  function tick() {
    const t = now();
    if (t - sampledAt < SAMPLE_MS) return;
    sampledAt = t;
    let s = null;
    try { s = sample(); } catch { s = null; }
    if (!s) return;
    box.last = { t: t - box.start, ...s };
    write();
  }

  /** The page is leaving on its own (pagehide): the record is clean. */
  function end(why = 'left') {
    tick();
    box.ended = why;
    write();
  }

  write();
  return { log, tick, end, previous, get box() { return box; } };
}

/**
 * Whether the record a previous page left is worth showing: it ended in a lost
 * context, or it stopped without leaving, and recently.
 */
export function wasCut(record, now = Date.now()) {
  if (!record || !Array.isArray(record.entries)) return false;
  const lastT = record.start + Math.max(record.last?.t ?? 0, record.entries.at(-1)?.t ?? 0);
  if (now - lastT > STALE_MS) return false;
  const lost = record.entries.some((e) => e.k === 'lost');
  // A page put in the background and later discarded by the system was not cut off
  // doing anything: its last step is the hiding.
  return lost || (!record.ended && record.entries.at(-1)?.k !== 'hidden');
}

const ago = (ms) => (ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`);
const k = (n) => (n >= 1e6 ? `${(n / 1e6).toFixed(2)}M` : n >= 1e3 ? `${Math.round(n / 1e3)}k` : `${n}`);

/** What a step says in words: the few fields that name it. */
function words(e) {
  const bits = [e.k];
  for (const key of ['id', 'app', 'level', 'to', 'meshes', 'batches', 'hit', 'msg']) {
    if (e[key] !== undefined && e[key] !== null) bits.push(`${key}=${e[key]}`);
  }
  return bits.join(' ');
}

/**
 * One line for the crash card: the last steps before the cut, newest last, and
 * the renderer as last sampled.
 */
export function summary(record) {
  if (!record?.entries?.length) return '';
  const cut = record.entries.findIndex((e) => e.k === 'lost');
  const end = cut >= 0 ? cut : record.entries.length;
  const at = cut >= 0 ? record.entries[cut].t : record.entries.at(-1).t;
  const steps = record.entries.slice(Math.max(0, end - 4), end)
    .filter((e) => e.k !== 'lost')
    .map((e) => `${words(e)} (${ago(at - e.t)} before)`);
  const s = record.last;
  // T-2828: the bytes behind the counts, where the page could read them.
  const mb = (v) => (Number.isFinite(v) ? ` (${v} MB)` : '');
  // T-2970: `draws` is what the driver received; a record written before it has only `calls`.
  const gpu = s ? ` Last read: ${s.draws ?? s.calls ?? '?'} draws, ${k(s.tris ?? 0)} triangles, ${s.tex ?? '?'} textures${mb(s.texMB)}, `
    + `${s.geo ?? '?'} geometries${mb(s.geoMB)}, ${s.w ?? '?'}×${s.h ?? '?'} at ${s.ratio ?? '?'}×.` : '';
  const how = cut >= 0 ? 'Display reset' : 'Page stopped';
  return `${how} ${ago(at)} into the visit. Just before: ${steps.join('; ') || 'nothing logged'}.${gpu}`;
}

/** The whole record as text, for the card's Copy button. */
export function report(record) {
  return JSON.stringify(record);
}

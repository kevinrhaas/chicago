/**
 * met-found.js — people met and places found, kept only in this browser (T-3673).
 *
 * The owner's classroom list, item 14: "People met, places found", a collection in the
 * People directory and the Map, by year, stored locally, with no streaks or leaderboards.
 * docs/CLASSROOM-FEATURES.md binds it: opening a card must never be reported as entering
 * a building or physically meeting someone. So the two words keep their plain meaning:
 *
 *   MET    you talked with them here: you were on foot within TALK_M (8 m) of someone
 *          standing in the town, and a Greet, Tell me a story or Ask a question with them
 *          finished. 8 m is the Interact key's own hold on a person (their 2.5 m reach,
 *          plus the few metres it keeps them while they turn to you). Opening their card from
 *          People, a search, Inspect, a jaunt or a shared link is not meeting them, and
 *          neither is a figure picked from across the street: the rule reads where you
 *          stand and where they stand when the talk ends.
 *   FOUND  you stood there: on foot (not flying, riding, aboard or at a helm), not in
 *          Inspect or on the arrival screen, inside a place's footprint or within FOUND_M
 *          (3 m) of its walls, a doorstep's depth. A place is a structure with a footprint
 *          on the Map and a name a visitor reads; an unnamed building, a privy and a shed
 *          are not counted as places. Map previews, Go to's cards and Inspect never record.
 *
 * The record is per year and per kind: an id and the day it was first recorded, nothing
 * else (no times, no totals across days, no streaks, no scores). It is bounded
 * (LIMITS.perKind each), never evicts, and never leaves the browser. A stored copy that
 * cannot be read is left unchanged and said so; a browser that cannot save keeps this
 * visit's list in memory and says that too. tools/test_met_found.mjs holds all of it.
 */

import { displayName } from './display-name.js';

export const METFOUND_KEY = 'chicago4d.metfound.v1';
export const LIMITS = Object.freeze({ perKind: 2500, years: 12, idChars: 160, chars: 900000 });
export const KINDS = Object.freeze(['met', 'found']);
/** How near a person must be when the talk ends, in metres. */
export const TALK_M = 8;
/** How far outside a place's walls still counts as standing at it, in metres. */
export const FOUND_M = 3;
/** The person actions that are talking with someone. */
export const TALK_ACTIONS = Object.freeze(['greet', 'tale', 'ask']);

const YEAR_RE = /^\d{4}$/;
const DAY_RE = /^\d{4}-\d{2}-\d{2}$/;
const validId = (id) => typeof id === 'string' && id.length > 0 && id.length <= LIMITS.idChars;
const empty = () => ({ version: 1, years: {} });

/** Today in the visitor's own calendar, as YYYY-MM-DD. */
export function localDay(now = new Date()) {
  const p = (x) => String(x).padStart(2, '0');
  return `${now.getFullYear()}-${p(now.getMonth() + 1)}-${p(now.getDate())}`;
}

/** The stored shape, checked whole: anything else is a damaged copy, never repaired. */
export function parseMetFound(raw) {
  let data;
  try { data = JSON.parse(raw); } catch { return null; }
  if (!data || data.version !== 1 || typeof data.years !== 'object' || Array.isArray(data.years) || !data.years) return null;
  const years = Object.keys(data.years);
  if (years.length > LIMITS.years) return null;
  for (const y of years) {
    const row = data.years[y];
    if (!YEAR_RE.test(y) || !row || typeof row !== 'object' || Array.isArray(row)) return null;
    for (const k of Object.keys(row)) if (!KINDS.includes(k)) return null;
    for (const k of KINDS) {
      const list = row[k] ?? {};
      if (typeof list !== 'object' || Array.isArray(list)) return null;
      const ids = Object.keys(list);
      if (ids.length > LIMITS.perKind) return null;
      for (const id of ids) if (!validId(id) || typeof list[id] !== 'string' || !DAY_RE.test(list[id])) return null;
    }
  }
  return data;
}

const local = () => { try { return globalThis.localStorage ?? null; } catch { return null; } };

/**
 * The store. `error` on what it returns is null (saved in this browser), 'storage' (this
 * browser is not saving: the list lasts this visit), 'damaged' (the saved copy could not
 * be read and is left as it was; this visit's list is kept apart from it) or, from a
 * record, 'full'.
 */
export function createMetFound({ storage = local, today = () => localDay() } = {}) {
  const listeners = new Set();
  const store = () => (typeof storage === 'function' ? storage() : storage);
  let memory = null;      // this visit's copy, once the browser's cannot be used
  let problem = null;     // why: 'storage' or 'damaged'

  function load() {
    if (memory) return { data: memory, error: problem };
    try {
      const s = store();
      if (!s) { memory = empty(); problem = 'storage'; return { data: memory, error: problem }; }
      const raw = s.getItem(METFOUND_KEY);
      if (raw == null) return { data: empty(), error: null };
      const data = String(raw).length <= LIMITS.chars ? parseMetFound(raw) : null;
      if (!data) { memory = empty(); problem = 'damaged'; return { data: memory, error: problem }; }
      return { data, error: null };
    } catch {
      memory = empty(); problem = 'storage';
      return { data: memory, error: problem };
    }
  }
  function tell() { for (const fn of listeners) { try { fn(); } catch { /* a view cannot undo a write */ } } }
  function save(data) {
    if (memory) { memory = data; tell(); return { ok: true, saved: false, error: problem }; }
    const raw = JSON.stringify(data);
    if (raw.length > LIMITS.chars) return { ok: false, reason: 'full' };
    try {
      const s = store();
      if (!s) throw new Error('no storage');
      s.setItem(METFOUND_KEY, raw);
    } catch {
      memory = data; problem = 'storage'; tell();
      return { ok: true, saved: false, error: problem };
    }
    tell();
    return { ok: true, saved: true, error: null };
  }

  return {
    /** One year's lists: `{ met, found, error }`, each list `{ id: 'YYYY-MM-DD' }` (a copy). */
    year(year) {
      const { data, error } = load();
      const row = data.years[String(year)] ?? {};
      return { met: { ...(row.met ?? {}) }, found: { ...(row.found ?? {}) }, error };
    },
    has(year, kind, id) {
      const row = load().data.years[String(year)];
      return !!row?.[kind] && Object.prototype.hasOwnProperty.call(row[kind], id);
    },
    /** Add one id; never evicts. `{ ok, added, reason?, error }`. */
    record(year, kind, id) {
      const y = String(year);
      if (!YEAR_RE.test(y) || !KINDS.includes(kind) || !validId(id)) return { ok: false, reason: 'invalid' };
      const { data, error } = load();
      const row = data.years[y];
      if (row?.[kind] && Object.prototype.hasOwnProperty.call(row[kind], id)) return { ok: true, added: false, error };
      if (!row && Object.keys(data.years).length >= LIMITS.years) return { ok: false, reason: 'full', error };
      if (Object.keys(row?.[kind] ?? {}).length >= LIMITS.perKind) return { ok: false, reason: 'full', error };
      const next = { version: 1, years: { ...data.years, [y]: { ...(row ?? {}), [kind]: { ...(row?.[kind] ?? {}), [id]: today() } } } };
      const r = save(next);
      return r.ok ? { ok: true, added: true, error: r.error } : { ...r, error };
    },
    /** Forget one year (both lists); other years are kept. A damaged saved copy is left alone. */
    clearYear(year) {
      const { data } = load();
      const years = { ...data.years };
      delete years[String(year)];
      return save({ version: 1, years });
    },
    /** Replace a damaged saved copy with an empty one: only on the visitor's explicit ask. */
    reset() {
      memory = null; problem = null;
      return save(empty());
    },
    get error() { return load().error; },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}

export const metFound = createMetFound();

// ---- the two rules ------------------------------------------------------------------- //

const finite = (w) => !!w && Number.isFinite(w.e) && Number.isFinite(w.n);

/** On foot in the town: not flying, riding, aboard, at a helm, in Inspect or on the arrival screen. */
export function onFoot(w) {
  return finite(w) && !w.flying && !w.aboard && !w.riding && !w.piloting && !w.inspecting && !w.gate;
}

/** The directory id of a person in the town (an Interact thing). */
export function personIdOf(thing) {
  if (thing?.kind !== 'person') return null;
  const id = thing.personId ?? thing.actor?.personId ?? null;
  return validId(id) ? id : null;
}

/**
 * Does this finished action mean you MET them? Only a talk (`TALK_ACTIONS`) that came from
 * the town (`via: 'town'`, the Interact engine), with someone standing in it (`at`), while
 * you were not flying and within TALK_M. A card, a search, Inspect or a link is never it.
 */
export function meetingCounts({ thing, actionId, walker, via = 'town' } = {}) {
  if (via !== 'town' || !TALK_ACTIONS.includes(actionId) || !personIdOf(thing)) return false;
  const at = thing.at;
  if (!Array.isArray(at) || !Number.isFinite(at[0]) || !Number.isFinite(at[1])) return false;
  if (!finite(walker) || walker.flying) return false;
  return Math.hypot(at[0] - walker.e, at[1] - walker.n) <= TALK_M;
}

const NOT_A_PLACE = /\b(privy|privies|necessary|outhouse|shed|woodshed|pen|fence)\b/i;

/** A place's name for a visitor, or null where it has none (an id-like or generic title). */
export function placeTitle(title) {
  const t = String(title ?? '').trim();
  if (!t || t === 'A building' || /[a-z0-9]_[a-z0-9]/i.test(t) || NOT_A_PLACE.test(t)) return null;
  return t;
}

/** A structure's visitor title off the scene registry (what the Map's preview names it). */
export const sceneTitle = (registry, id) => displayName(registry?.get?.(id)?.sidecar ?? {}, id ?? '').title;

/**
 * The places of a scene, from the Map's footprints (navigation.js structureOutlines: rings of
 * [e, n] with an `id`): `{ ids, count, has(id), rings, boxes }`, built once. `nameOf(id)` gives
 * a structure's visitor title; ids without one are not places.
 */
export function placeIndex(outlines, nameOf = () => null) {
  const named = new Map();
  const rings = [];
  for (const ring of outlines ?? []) {
    const id = ring?.id;
    if (!id || ring.length < 3) continue;
    if (!named.has(id)) named.set(id, !!placeTitle(nameOf(id)));
    if (named.get(id)) rings.push(ring);
  }
  const boxes = new Float64Array(rings.length * 4);
  rings.forEach((ring, i) => {
    let a = Infinity, b = Infinity, c = -Infinity, d = -Infinity;
    for (const [e, n] of ring) { if (e < a) a = e; if (n < b) b = n; if (e > c) c = e; if (n > d) d = n; }
    boxes[i * 4] = a; boxes[i * 4 + 1] = b; boxes[i * 4 + 2] = c; boxes[i * 4 + 3] = d;
  });
  const ids = [...new Set(rings.map((r) => r.id))];
  const set = new Set(ids);
  return { ids, count: ids.length, has: (id) => set.has(id), rings, boxes };
}

/** Is [e, n] inside the ring (even-odd), or within `reach` metres of its edge? */
export function nearRing(ring, e, n, reach) {
  let hit = false, best = Infinity;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const ei = ring[i][0], ni = ring[i][1], ej = ring[j][0], nj = ring[j][1];
    if ((ni > n) !== (nj > n) && e < ((ej - ei) * (n - ni)) / (nj - ni) + ei) hit = !hit;
    const de = ej - ei, dn = nj - ni, len = de * de + dn * dn;
    const t = len > 0 ? Math.max(0, Math.min(1, ((e - ei) * de + (n - ni) * dn) / len)) : 0;
    const d = Math.hypot(ei + t * de - e, ni + t * dn - n);
    if (d < best) best = d;
  }
  return hit || best <= reach;
}

/**
 * The places where the walker stands now, written into `out` (cleared; reused, so a check
 * allocates nothing). Nothing while not on foot (`onFoot`).
 */
export function placesAt(index, walker, out = [], reach = FOUND_M) {
  out.length = 0;
  if (!index || !onFoot(walker)) return out;
  const { e, n } = walker, b = index.boxes;
  for (let i = 0; i < index.rings.length; i++) {
    if (e < b[i * 4] - reach || n < b[i * 4 + 1] - reach || e > b[i * 4 + 2] + reach || n > b[i * 4 + 3] + reach) continue;
    const ring = index.rings[i];
    if (!out.includes(ring.id) && nearRing(ring, e, n, reach)) out.push(ring.id);
  }
  return out;
}

/**
 * The town's watch, wired by main.js: `talked(thing, actionId)` after every finished
 * Interact action, `tick()` about once a second. `walker()` answers the visitor's pose and
 * state (`{ e, n, flying, aboard, riding, piloting, inspecting, gate }`); `places()` the
 * place index (or null until the Map's footprints exist).
 */
export function createMetFoundWatch({ store = metFound, year, walker, places }) {
  const y = String(year);
  const out = [];
  let known = null;
  const fresh = () => { known = new Set(Object.keys(store.year(y).found)); };
  const off = store.subscribe(() => { known = null; });
  return {
    talked(thing, actionId) {
      if (!meetingCounts({ thing, actionId, walker: walker(), via: 'town' })) return null;
      return store.record(y, 'met', personIdOf(thing));
    },
    tick() {
      const index = places();
      if (!index?.count) return 0;
      placesAt(index, walker(), out);
      if (!out.length) return 0;
      if (!known) fresh();
      let added = 0;
      for (const id of out) {
        if (known.has(id)) continue;
        known.add(id);   // a refused write (full) is not retried every second
        if (store.record(y, 'found', id).added) added++;
      }
      return added;
    },
    dispose() { off(); },
  };
}

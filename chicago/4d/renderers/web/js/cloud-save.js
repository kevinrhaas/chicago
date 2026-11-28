/**
 * T-3777: cloud save. The field notebook, people met and places found, and Settings follow a
 * signed-in student to another device through Firestore.
 *
 * Stage 1 of the owner's server plan (2026-11-26). Behind `cloudFeatures` (T-3776,
 * js/student-data.js): while that switch is off, nothing here runs.
 *
 * OFFLINE FIRST. The browser's own copy (chicago4d.notebook.v1, chicago4d.metfound.v1,
 * chicago4d.settings and a few single-value keys) stays the working copy every module
 * reads and writes as before. This module only reconciles it with the account:
 *
 *   users/<uid>/notebook/<entry id>        one notebook entry
 *   users/<uid>/metfound/<year>-<met|found> one year's list of one kind, { id: first day }
 *   users/<uid>/settings/prefs             the Settings that are the person's, not the device's
 *
 * Each document is { v: the value as JSON, deleted: bool, at: the server's time }. A
 * delete is kept as a tombstone (deleted: true) so another device learns of it.
 *
 * THE MERGE is three-way, per document, against the BASE: what this browser and the
 * account last agreed on (kept as a short hash in chicago4d.cloudsave.v1, with the keys of
 * the two list-shaped parts). Changed on one side only, that side wins. Changed on both:
 *   - a list (met/found, settings) merges key by key the same way; a key changed on both
 *     sides takes the newer side, and met/found keeps the earlier day;
 *   - a notebook entry: an edit always beats a delete (an entry is never silently
 *     dropped); two edits keep the newer.
 * On a browser's first sync with an account (no base yet) a clash goes to the account: a new
 * browser's Settings are its defaults, not the person's choices. Lists still join.
 *
 * WRITES are few: only documents whose value changed, in one commit, debounced (15 s after
 * the last change, at most 60 s), plus a flush when the page is hidden and a look every two
 * minutes for Settings, which other modules write straight to the browser. A pull asks only
 * for documents changed since the last one. tools/test_cloud_save.mjs holds the merge,
 * the rules and the lesson's write count to account.
 *
 * Signed out, signed in with the email alone (no password: anyone could type it), offline,
 * or refused by the account: the browser's copy works exactly as it did, and the Settings ›
 * About line says the work is kept on this device.
 */

import { NOTEBOOK_KEY, LIMITS as NOTEBOOK_LIMITS, cleanEntry } from './field-notebook.js';
import { METFOUND_KEY, LIMITS as METFOUND_LIMITS, KINDS, parseMetFound } from './met-found.js';
import { t } from './strings/index.js';
import './strings/settings.js';

export const CLOUD_PARTS = Object.freeze(['notebook', 'metfound', 'settings']);
export const STATE_KEY = 'chicago4d.cloudsave.v1';
export const SETTINGS_KEY = 'chicago4d.settings';
/** Single-value Settings kept under their own keys: the look, light or dark, motion, letter keys. */
export const SETTING_KEYS = Object.freeze(['chicago4d.skin', 'chicago4d.theme', 'chicago4d.motion', 'chicago4d.letterKeys']);
/** Settings fields that belong to the device, not the person (its graphics and its pacing). */
export const DEVICE_FIELDS = Object.freeze(['quality', 'pacing', 'antialias', 'detail', 'detailKept', 'paceDefaults']);
/** The longest `v` the rules accept, in characters (a Firestore document holds 1 MiB). */
export const MAX_V = 800000;
export const TIMING = Object.freeze({ debounceMs: 15000, maxWaitMs: 60000, lookMs: 120000, pullAfterMs: 300000, overlapMs: 60000 });

// ---------------------------------------------------------------------------------------
// Values, hashes and the three-way merge (pure; the tests drive these directly).
// ---------------------------------------------------------------------------------------

/** JSON with object keys sorted, so two equal values always hash alike. */
export function stable(value) {
  if (value === undefined) return 'undefined';
  if (value === null || typeof value !== 'object') return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  return `{${Object.keys(value).sort().map((k) => `${JSON.stringify(k)}:${stable(value[k])}`).join(',')}}`;
}
/** A short hash of a value (cyrb53); `null` for no value. */
export function hashOf(value) {
  if (value === undefined) return null;
  const str = stable(value);
  let h1 = 0xdeadbeef, h2 = 0x41c6ce57;
  for (let i = 0; i < str.length; i++) {
    const ch = str.charCodeAt(i);
    h1 = Math.imul(h1 ^ ch, 2654435761);
    h2 = Math.imul(h2 ^ ch, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36);
}

const partOf = (docId) => docId.slice(0, docId.indexOf('/'));
const isMap = (docId) => partOf(docId) !== 'notebook';
const newer = (a, b) => String(a ?? '') > String(b ?? '');

/**
 * Merge two versions of a map against their base, key by key. `baseMap` is the base's
 * values where kept (settings) or just its keys with `true` (met/found). `both(l, r)`
 * settles a key changed on both sides.
 */
export function mergeMap(baseMap = {}, local = {}, remote = {}, both) {
  const out = {};
  const keys = new Set([...Object.keys(local), ...Object.keys(remote)]);
  for (const k of keys) {
    const inL = Object.prototype.hasOwnProperty.call(local, k);
    const inR = Object.prototype.hasOwnProperty.call(remote, k);
    const inB = Object.prototype.hasOwnProperty.call(baseMap, k);
    const b = baseMap[k];
    const known = b !== true; // a list's base keeps only its keys
    if (inL && inR) {
      const l = local[k], r = remote[k];
      if (stable(l) === stable(r)) out[k] = l;
      else if (known && inB && stable(l) === stable(b)) out[k] = r;
      else if (known && inB && stable(r) === stable(b)) out[k] = l;
      else out[k] = both(l, r, k);
    } else if (inL) {
      // Absent on the account: deleted there if the base had it (and this side did not change it).
      if (!inB) out[k] = local[k];
      else if (known && stable(local[k]) !== stable(b)) out[k] = local[k];
    } else if (inR) {
      if (!inB) out[k] = remote[k];
      else if (known && stable(remote[k]) !== stable(b)) out[k] = remote[k];
    }
  }
  return out;
}

/**
 * One document's merge. `base` is { h, keys?, map? } or undefined; `local` the browser's
 * value or undefined; `remote` { value, at } (value undefined for a tombstone) when the pull
 * brought it, else undefined (unchanged on the account since the base). `localAt` is when
 * this browser's change was seen. Returns { value, push }: the value both sides should
 * hold (undefined: deleted) and whether the account needs it written.
 */
export function mergeDoc(docId, base, local, remote, localAt) {
  const baseH = base?.h ?? null;
  const localChanged = hashOf(local) !== baseH;
  if (!remote) return { value: local, push: localChanged };
  const r = remote.value;
  const remoteChanged = hashOf(r) !== baseH;
  if (!localChanged) return { value: r, push: false };
  if (!remoteChanged || hashOf(local) === hashOf(r)) return { value: local, push: hashOf(local) !== hashOf(r) };
  // Changed on both sides. Never agreed before (a first sync on this browser): the account
  // wins a clash, since a new browser's values are its defaults, not the person's choices.
  const localWins = base ? newer(localAt, remote.at) : false;
  if (!isMap(docId)) {
    if (local === undefined) return { value: r, push: false };     // an edit beats a delete
    if (r === undefined) return { value: local, push: true };
    return localWins ? { value: local, push: true } : { value: r, push: false };
  }
  if (local === undefined || r === undefined) {
    // One side cleared the whole list: what the other side added since the base stays.
    const kept = mergeMap(base?.map ?? Object.fromEntries((base?.keys ?? []).map((k) => [k, true])),
      local ?? {}, r ?? {}, (l, rr) => (localWins ? l : rr));
    const value = Object.keys(kept).length ? kept : undefined;
    return { value, push: hashOf(value) !== hashOf(r) };
  }
  const baseMap = base?.map ?? Object.fromEntries((base?.keys ?? []).map((k) => [k, true]));
  const pick = partOf(docId) === 'metfound'
    ? (l, rr) => (String(l) <= String(rr) ? l : rr)   // the earlier first day
    : (l, rr) => (localWins ? l : rr);
  const value = mergeMap(baseMap, local, r, pick);
  return { value, push: hashOf(value) !== hashOf(r) };
}

/** What the base keeps of an agreed value. */
export function baseOf(docId, value) {
  if (value === undefined) return undefined;
  const h = hashOf(value);
  if (partOf(docId) === 'settings') return { h, map: value };
  if (partOf(docId) === 'metfound') return { h, keys: Object.keys(value) };
  return { h };
}

// ---------------------------------------------------------------------------------------
// The browser's copy, read as documents and written back.
// ---------------------------------------------------------------------------------------

const json = (raw) => { try { return JSON.parse(raw); } catch { return undefined; } };
const validDocId = (id) => typeof id === 'string' && id.length > 0 && id.length <= 200 && !id.includes('/') && !/^__.*__$/.test(id) && id !== '.' && id !== '..';

/** The browser's copy as documents: Map docId → value. A part that cannot be read is left out
 * (and listed in `unreadable`), so a damaged copy is never written over or pushed. */
export function readLocal(storage) {
  const docs = new Map();
  const unreadable = [];
  const get = (k) => { try { return storage?.getItem?.(k) ?? null; } catch { return undefined; } };

  const nb = get(NOTEBOOK_KEY);
  if (nb === undefined) unreadable.push('notebook');
  else if (nb !== null) {
    const data = json(nb);
    const entries = data?.version === 1 && Array.isArray(data.entries) ? data.entries.map((e) => cleanEntry(e)) : null;
    if (!entries || entries.some((e) => !e || !validDocId(e.id))) unreadable.push('notebook');
    else for (const e of entries) docs.set(`notebook/${e.id}`, e);
  }

  const mf = get(METFOUND_KEY);
  if (mf === undefined) unreadable.push('metfound');
  else if (mf !== null) {
    const data = parseMetFound(mf);
    if (!data) unreadable.push('metfound');
    else {
      for (const [year, row] of Object.entries(data.years)) {
        for (const kind of KINDS) {
          const list = row[kind] ?? {};
          if (Object.keys(list).length) docs.set(`metfound/${year}-${kind}`, { ...list });
        }
      }
    }
  }

  const prefs = {};
  const blob = get(SETTINGS_KEY);
  if (blob === undefined) unreadable.push('settings');
  else {
    const data = blob === null ? {} : json(blob);
    if (!data || typeof data !== 'object' || Array.isArray(data)) unreadable.push('settings');
    else {
      for (const [k, v] of Object.entries(data)) if (!DEVICE_FIELDS.includes(k) && v !== undefined) prefs[k] = v;
      for (const key of SETTING_KEYS) { const v = get(key); if (typeof v === 'string') prefs[`@${key}`] = v; }
      if (Object.keys(prefs).length) docs.set('settings/prefs', prefs);
    }
  }
  return { docs, unreadable };
}

/**
 * Write the merged documents back into the browser's copy. `changes` is Map docId → value
 * (undefined: deleted) for the documents whose browser value moves. What does not fit the
 * notebook's or the list's own limits stays on the account only and is reported in
 * `skipped`, never forced in (which would leave the browser's copy unreadable).
 */
export function writeLocal(storage, changes) {
  const skipped = [];
  const byPart = (p) => [...changes].filter(([id]) => partOf(id) === p);

  const nbChanges = byPart('notebook');
  if (nbChanges.length) {
    const data = json(storage.getItem(NOTEBOOK_KEY)) ?? { version: 1, entries: [] };
    let entries = Array.isArray(data.entries) ? data.entries : [];
    const at = new Map(entries.map((e, i) => [e.id, i]));
    const added = [];
    for (const [docId, value] of nbChanges) {
      const id = docId.slice('notebook/'.length);
      const clean = value === undefined ? undefined : cleanEntry(value);
      if (value !== undefined && (!clean || clean.id !== id)) { skipped.push(docId); continue; }
      if (at.has(id)) entries[at.get(id)] = clean;         // undefined marks a removal
      else if (clean) added.push(clean);
    }
    entries = [...entries.filter(Boolean), ...added.sort((a, b) => String(a.createdAt).localeCompare(String(b.createdAt)))];
    // Over the notebook's own limits: the newest arrivals wait on the account.
    while (entries.length > NOTEBOOK_LIMITS.entries
      || entries.filter((e) => e.kind === 'photo').length > NOTEBOOK_LIMITS.photos
      || JSON.stringify({ version: 1, entries }).length > NOTEBOOK_LIMITS.chars) {
      const drop = added.pop();
      if (!drop) break;
      entries = entries.filter((e) => e !== drop);
      skipped.push(`notebook/${drop.id}`);
    }
    storage.setItem(NOTEBOOK_KEY, JSON.stringify({ version: 1, entries }));
  }

  const mfChanges = byPart('metfound');
  if (mfChanges.length) {
    const data = parseMetFound(storage.getItem(METFOUND_KEY) ?? '{"version":1,"years":{}}') ?? { version: 1, years: {} };
    const next = { version: 1, years: JSON.parse(JSON.stringify(data.years)) };
    for (const [docId, value] of mfChanges) {
      const [year, kind] = docId.slice('metfound/'.length).split('-');
      const row = { ...(next.years[year] ?? {}) };
      if (value === undefined) delete row[kind]; else row[kind] = value;
      if (Object.keys(row).length) next.years[year] = row; else delete next.years[year];
    }
    const raw = JSON.stringify(next);
    if (parseMetFound(raw) && raw.length <= METFOUND_LIMITS.chars) storage.setItem(METFOUND_KEY, raw);
    else skipped.push(...mfChanges.map(([id]) => id));
  }

  if (changes.has('settings/prefs')) {
    const prefs = changes.get('settings/prefs') ?? {};
    const current = json(storage.getItem(SETTINGS_KEY) ?? '{}') ?? {};
    const blob = Object.fromEntries(Object.entries(current).filter(([k]) => DEVICE_FIELDS.includes(k)));
    for (const [k, v] of Object.entries(prefs)) if (!k.startsWith('@')) blob[k] = v;
    storage.setItem(SETTINGS_KEY, JSON.stringify(blob));
    for (const key of SETTING_KEYS) {
      const v = prefs[`@${key}`];
      if (typeof v === 'string') storage.setItem(key, v); else storage.removeItem(key);
    }
  }
  return { skipped };
}

// ---------------------------------------------------------------------------------------
// The account, over Firestore's REST API (as visitor-store.js and reading-level.js do).
// ---------------------------------------------------------------------------------------

const API = 'https://firestore.googleapis.com/v1';
const root = (projectId) => `projects/${projectId}/databases/(default)/documents`;

/** The query for one part's documents changed since `since` (all of them without). */
export function partQuery(part, since, offset = 0, limit = 300) {
  const q = { from: [{ collectionId: part }], limit, offset };
  if (since) q.where = { fieldFilter: { field: { fieldPath: 'at' }, op: 'GREATER_THAN', value: { timestampValue: since } } };
  return q;
}

/** The write that puts one document on the account (`at` set by the server). */
export function writeOf(projectId, uid, docId, value) {
  return {
    update: {
      name: `${root(projectId)}/users/${uid}/${docId}`,
      fields: value === undefined
        ? { v: { stringValue: '' }, deleted: { booleanValue: true } }
        : { v: { stringValue: JSON.stringify(value) }, deleted: { booleanValue: false } },
    },
    updateTransforms: [{ fieldPath: 'at', setToServerValue: 'REQUEST_TIME' }],
  };
}

async function pull({ projectId, uid, token, since, fetchFn }) {
  const out = new Map();
  let maxAt = since ?? null;
  const from = since ? new Date(Date.parse(since) - TIMING.overlapMs).toISOString() : null;
  for (const part of CLOUD_PARTS) {
    for (let page = 0; page < 20; page++) {
      const res = await fetchFn(`${API}/${root(projectId)}/users/${encodeURIComponent(uid)}:runQuery`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ structuredQuery: partQuery(part, from, page * 300) }),
      });
      if (!res.ok) throw Object.assign(new Error(`pull ${part}: ${res.status}`), { status: res.status });
      const rows = (await res.json()).map((r) => r.document).filter(Boolean);
      for (const d of rows) {
        const id = d.name.slice(d.name.lastIndexOf('/') + 1);
        const docId = `${part}/${id}`;
        const at = d.fields?.at?.timestampValue ?? '';
        const deleted = d.fields?.deleted?.booleanValue === true;
        const value = deleted ? undefined : json(d.fields?.v?.stringValue ?? '');
        if (!deleted && value === undefined) continue;                 // unreadable: left alone
        out.set(docId, { value, at });
        if (newer(at, maxAt)) maxAt = at;
      }
      if (rows.length < 300) break;
    }
  }
  return { remote: out, maxAt };
}

async function push({ projectId, uid, token, writes, fetchFn }) {
  // Commits of at most 400 writes and about 4 MB each.
  let batch = [], size = 0, sent = 0;
  const send = async () => {
    if (!batch.length) return;
    const res = await fetchFn(`${API}/${root(projectId)}:commit`, {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ writes: batch }),
    });
    if (!res.ok) throw Object.assign(new Error(`commit: ${res.status}`), { status: res.status });
    sent += batch.length;
    batch = []; size = 0;
  };
  for (const w of writes) {
    const n = JSON.stringify(w).length;
    if (batch.length >= 400 || size + n > 4_000_000) await send();
    batch.push(w); size += n;
  }
  await send();
  return sent;
}

// ---------------------------------------------------------------------------------------
// One sync, and the controller that schedules them.
// ---------------------------------------------------------------------------------------

function readState(storage, uid) {
  const s = json(storage.getItem(STATE_KEY) ?? 'null');
  if (s?.v === 1 && s.uid === uid && s.base && typeof s.base === 'object') return { ...s, dirtyAt: s.dirtyAt ?? {} };
  return { v: 1, uid, since: null, base: {}, dirtyAt: {} };
}
function saveState(storage, state) {
  try { storage.setItem(STATE_KEY, JSON.stringify(state)); return true; } catch { return false; }
}

/** Mark the documents that now differ from the base with when the change was seen. */
export function noteChanges(storage, uid, now = () => new Date().toISOString()) {
  const state = readState(storage, uid);
  const { docs } = readLocal(storage);
  const ids = new Set([...docs.keys(), ...Object.keys(state.base)]);
  let marked = 0;
  for (const id of ids) {
    if (hashOf(docs.get(id)) !== (state.base[id]?.h ?? null)) {
      if (!state.dirtyAt[id]) { state.dirtyAt[id] = now(); marked++; }
    } else delete state.dirtyAt[id];
  }
  saveState(storage, state);
  return { marked, dirty: Object.keys(state.dirtyAt).length };
}

/**
 * Pull, merge, write back, push. Returns { ok, pulled, pushed, applied, skipped, why }.
 * Never throws; a refusal or no network leaves the browser's copy as it was.
 */
export async function syncOnce({ projectId, account, storage, fetchFn, now = () => new Date().toISOString(), pullRemote = true } = {}) {
  const uid = account?.uid;
  if (!projectId || !uid || typeof account.idToken !== 'function' || !storage || !fetchFn) return { ok: false, why: 'not signed in' };
  let token;
  try { token = await account.idToken(); } catch { return { ok: false, why: 'not signed in' }; }
  const state = readState(storage, uid);
  const { docs: local, unreadable } = readLocal(storage);
  let remote = new Map(), maxAt = state.since;
  if (pullRemote) {
    try { ({ remote, maxAt } = await pull({ projectId, uid, token, since: state.since, fetchFn })); }
    catch (err) { return { ok: false, why: err.status ? `refused (${err.status})` : 'offline' }; }
  }

  const ids = new Set([...local.keys(), ...Object.keys(state.base), ...remote.keys()]);
  const writes = [];
  const applied = new Map();
  const nextBase = { ...state.base };
  const tooBig = [];
  for (const id of ids) {
    if (unreadable.includes(partOf(id))) continue;                     // a damaged copy is never touched
    const l = local.get(id);
    const { value, push } = mergeDoc(id, state.base[id], l, remote.get(id), state.dirtyAt[id] ?? now());
    if (hashOf(value) !== hashOf(l)) applied.set(id, value);
    if (push) {
      if (value !== undefined && JSON.stringify(value).length > MAX_V) { tooBig.push(id); continue; }
      if (value === undefined && !state.base[id] && !remote.has(id)) { delete nextBase[id]; continue; } // never on the account
      writes.push([id, value]);
    }
    const b = baseOf(id, value);
    if (b) nextBase[id] = b; else delete nextBase[id];
  }

  let skipped = [];
  if (applied.size) {
    try { ({ skipped } = writeLocal(storage, applied)); }
    catch { return { ok: false, why: 'this browser could not save' }; }
    for (const id of skipped) { if (state.base[id]) nextBase[id] = state.base[id]; else delete nextBase[id]; }
  }

  let pushed = 0;
  if (writes.length) {
    try { pushed = await push({ projectId, uid, token, writes: writes.map(([id, v]) => writeOf(projectId, uid, id, v)), fetchFn }); }
    catch (err) {
      // The account kept nothing: the base stays where it was, so the next sync tries again.
      for (const [id] of writes) { if (state.base[id]) nextBase[id] = state.base[id]; else delete nextBase[id]; }
      saveState(storage, { ...state, since: maxAt, base: nextBase });
      return { ok: false, pulled: remote.size, pushed: 0, applied: applied.size, why: err.status ? `refused (${err.status})` : 'offline' };
    }
  }
  const dirtyAt = {};
  for (const id of [...skipped, ...tooBig]) if (state.dirtyAt[id]) dirtyAt[id] = state.dirtyAt[id];
  saveState(storage, { v: 1, uid, since: maxAt, base: nextBase, dirtyAt });
  return { ok: true, pulled: remote.size, pushed, applied: applied.size, skipped: [...skipped, ...tooBig], at: now() };
}

/** May this account's work travel? A real sign-in only: the email alone proves nothing. */
export function cloudSaveFor(account, config) {
  return Boolean(config?.enabled && config?.cloudFeatures === true && account?.uid
    && typeof account.idToken === 'function' && account.method && account.method !== 'email' && account.method !== 'preview');
}

/**
 * Start cloud save for this visit. Returns { ready, flush, status, stop }: `ready` settles
 * after the first sync (or its failure), which main.js waits for briefly before the town
 * reads its Settings. Every later sync is scheduled here; none is per keystroke.
 */
export function startCloudSave({
  account, projectId, storage = globalThis.localStorage, fetchFn = globalThis.fetch?.bind(globalThis),
  sources = [], doc = globalThis.document, timers = globalThis, onStatus = () => {}, now = () => new Date().toISOString(),
} = {}) {
  let status = { state: 'syncing', at: null, why: '' };
  let chain = Promise.resolve();
  let debounce = null, firstChange = 0, lastPull = 0, stopped = false;
  const tell = (s) => { status = s; try { onStatus(s); } catch { /* a view cannot stop a save */ } };
  const run = (pullRemote) => (chain = chain.then(async () => {
    if (stopped) return status;
    tell({ ...status, state: 'syncing' });
    const r = await syncOnce({ projectId, account, storage, fetchFn, now, pullRemote });
    if (pullRemote && r.ok) lastPull = Date.now();
    tell(r.ok ? { state: 'saved', at: r.at, why: '' } : { state: 'device', at: status.at, why: r.why });
    return status;
  }));
  const flush = () => { if (debounce) { timers.clearTimeout(debounce); debounce = null; } firstChange = 0; return run(true); };
  const changed = () => {
    if (stopped) return;
    try { noteChanges(storage, account.uid, now); } catch { /* the next sync sees it anyway */ }
    const t = Date.now();
    if (!firstChange) firstChange = t;
    if (debounce) timers.clearTimeout(debounce);
    const wait = Math.max(0, Math.min(TIMING.debounceMs, firstChange + TIMING.maxWaitMs - t));
    debounce = timers.setTimeout(flush, wait);
  };
  const unsubs = sources.map((s) => { try { return s.subscribe(changed); } catch { return () => {}; } });
  const look = timers.setInterval?.(() => {
    try { if (noteChanges(storage, account.uid, now).dirty) changed(); } catch { /* next look */ }
  }, TIMING.lookMs);
  const onVisibility = () => {
    if (doc?.visibilityState === 'hidden') { if (debounce || firstChange) void flush(); }
    else if (Date.now() - lastPull > TIMING.pullAfterMs) void run(true);
  };
  doc?.addEventListener?.('visibilitychange', onVisibility);
  const ready = run(true);
  return {
    ready,
    flush,
    get status() { return status; },
    stop() {
      stopped = true;
      if (debounce) timers.clearTimeout(debounce);
      if (look) timers.clearInterval?.(look);
      for (const u of unsubs) { try { u(); } catch { /* gone */ } }
      doc?.removeEventListener?.('visibilitychange', onVisibility);
    },
  };
}

/** The Settings › About line: where the work is kept right now. */
export function cloudSaveLine(status, { clock = (iso) => new Date(iso).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) } = {}) {
  if (!status) return '';
  if (status.state === 'saved') return t('settings.cloud.saved', { time: clock(status.at) });
  if (status.state === 'syncing') return t('settings.cloud.saving');
  return t('settings.cloud.device');
}

// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * reading-level.js — the reader's age, and every card's words at each age (T-3645).
 *
 * The owner, 2026-11-17: "a person can set a grade level age level in their settings and
 * then the cards they read about people etc are targeted at their age level and they just
 * see their jaunts for their level. i can add multiple levels to see and then you would see
 * all jaunts and also there would be a tab to read the different levels of all of the
 * cards, the default level is the highest level". Ages, not grades, for now (T-3640).
 *
 * Three parts, none of which knows the town:
 *
 *  - THE CHOICE (`readingChoice`): none, one or several of the five ages, kept on this
 *    device under `chicago4d.reading.ages`; the Jaunts menu's age row and Settings › Display
 *    › Reading age are two views of it. Signed in, `syncReading` keeps it on the account
 *    (Firestore `readers/<uid>`, docs/SIGN-IN.md), so another device opens at the same age.
 *  - THE TABLES: for a string a card shows, its words at other ages. A scene's written
 *    levels are `data/reading/<scene>.json` (entries of the text as shown, and its levels),
 *    fetched the first time a card opens; a jaunt's are built from its other tellings
 *    (`tellingTable`), which already exist for every grade band (T-3621).
 *  - THE TABS (`readingTabs`): over a card that holds a string with words at another age, a
 *    row of age tabs; the card opens at the highest age the reader chose (none chosen: the
 *    words as written) and a tab swaps its text in place. A card with nothing at another
 *    age shows no row: a tab that changes nothing is not a choice.
 *
 * The swap is of text nodes, never of markup: a grade dot, a link or a Find key beside the
 * words stays where it was, and the words as written come back on the tab that holds them.
 */
import { rovingTabs, syncRoving } from './card-a11y.js';

/** The five ages, youngest first. `grade` is the US school band each stands for (T-3640:
 *  the age pupils are when the school year starts); 18+ is the words as written. */
export const LEVELS = Object.freeze([
  Object.freeze({ id: '8-10', label: '8–10', grade: '3-5' }),
  Object.freeze({ id: '11-13', label: '11–13', grade: '6-8' }),
  Object.freeze({ id: '14-15', label: '14–15', grade: '9-10' }),
  Object.freeze({ id: '16-17', label: '16–17', grade: '11-12' }),
  Object.freeze({ id: '18+', label: '18+', grade: null }),
]);
export const LEVEL_IDS = Object.freeze(LEVELS.map((l) => l.id));
/** The words as an author wrote them, for a card: the top of the ladder. */
export const WRITTEN = '18+';
const rankOf = (id) => LEVEL_IDS.indexOf(id);
export const levelLabel = (id) => LEVELS.find((l) => l.id === id)?.label ?? '';
/** The age a grade band (data/jaunts/schema.json grade_band) is read at; K-2 reads with 8-10. */
export const levelOfGrade = (band) => (band === 'K-2' ? '8-10' : LEVELS.find((l) => l.grade === band)?.id ?? '');
export const gradeOfLevel = (id) => LEVELS.find((l) => l.id === id)?.grade ?? '';
/** Ages in ladder order, unknown ones and repeats dropped. */
export const tidy = (ids) => LEVEL_IDS.filter((id) => (ids ?? []).includes(id));

export const AGES_KEY = 'chicago4d.reading.ages';
/** T-3629's single remembered grade band, read once as the first choice of age. */
export const LEGACY_GRADE_KEY = 'chicago4d.jaunts.grade';

function local() { try { return globalThis.localStorage ?? null; } catch { return null; } }

/**
 * The reader's choice. `get()` is the chosen ages in ladder order (empty: none chosen, read
 * everything as written); `top()` the highest of them, or 18+ with none. `set` and `toggle`
 * tell every subscriber, with `from` saying who changed it ('device', 'account', 'reader').
 */
export function createReadingChoice({ storage = local() } = {}) {
  let ages = [];
  try {
    const raw = storage?.getItem(AGES_KEY);
    if (raw != null) ages = tidy(JSON.parse(raw));
    else {
      const legacy = storage?.getItem(LEGACY_GRADE_KEY) ?? '';
      const age = legacy === WRITTEN ? WRITTEN : levelOfGrade(legacy);
      if (age) ages = [age];
    }
  } catch { ages = []; }
  const subs = new Set();
  const write = () => { try { storage?.setItem(AGES_KEY, JSON.stringify(ages)); } catch { /* a convenience */ } };
  const api = {
    get: () => ages.slice(),
    has: (id) => ages.includes(id),
    top: () => (ages.length ? ages[ages.length - 1] : WRITTEN),
    set(next, from = 'reader') {
      const tidied = tidy(next);
      if (tidied.join() === ages.join()) return false;
      ages = tidied; write();
      for (const fn of subs) { try { fn(ages.slice(), from); } catch (err) { console.warn('[4D Chicago] reading age', err); } }
      return true;
    },
    toggle(id, from = 'reader') { return api.set(ages.includes(id) ? ages.filter((a) => a !== id) : [...ages, id], from); },
    clear(from = 'reader') { return api.set([], from); },
    subscribe(fn) { subs.add(fn); return () => subs.delete(fn); },
  };
  return api;
}

let shared = null;
/** The one choice the page shares (Settings, the Jaunts menu, every card). */
export function readingChoice() { return (shared ??= createReadingChoice()); }
/** Tests only: a fresh shared choice over the given storage. */
export function resetReadingChoice(storage) { shared = createReadingChoice({ storage }); return shared; }

// ---------------------------------------------------------------------------------------
// The account: Firestore readers/<uid> { ages: [..], at: ISO }, over REST like visitor-store.
// ---------------------------------------------------------------------------------------

/** The fields readers/<uid> holds; docs/SIGN-IN.md's rule lists exactly these. */
export const READER_FIELDS = Object.freeze(['ages', 'at']);
const docUrl = (projectId, uid) =>
  `https://firestore.googleapis.com/v1/projects/${encodeURIComponent(projectId)}/databases/(default)/documents/readers/${encodeURIComponent(uid)}`;
/** The document body that keeps `ages` on the account. */
export function readerFields(ages, now = new Date()) {
  return { ages: { arrayValue: { values: tidy(ages).map((a) => ({ stringValue: a })) } }, at: { stringValue: now.toISOString() } };
}
/** The ages a readers/<uid> document holds, or null when it holds none. */
export function remoteAges(doc) {
  const values = doc?.fields?.ages?.arrayValue;
  if (!values) return null;
  return tidy((values.values ?? []).map((v) => v.stringValue));
}

/**
 * Keep the choice on a signed-in account. The account's ages, where it has some, win over
 * this device's (the reader set them on another device); with none, this device's are
 * written up. Every later change is written. A refusal (the rule not pasted yet, offline)
 * leaves the choice on the device and says so once in the console.
 */
export async function syncReading({ choice = readingChoice(), account, projectId, fetchFn = fetch } = {}) {
  if (!account?.uid || typeof account.idToken !== 'function' || !projectId) return { synced: false, why: 'not signed in' };
  const url = docUrl(projectId, account.uid);
  let warned = false;
  const warn = (what) => { if (!warned) { warned = true; console.warn(`[4D Chicago] reading age kept on this device only: ${what}`); } };
  const put = async (ages) => {
    try {
      const token = await account.idToken();
      const mask = READER_FIELDS.map((f) => `updateMask.fieldPaths=${f}`).join('&');
      const res = await fetchFn(`${url}?${mask}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ fields: readerFields(ages) }) });
      if (!res.ok) warn(`the account refused it (${res.status})`);
      return res.ok;
    } catch (err) { warn(err?.message ?? 'offline'); return false; }
  };
  let remote = null;
  try {
    const token = await account.idToken();
    const res = await fetchFn(url, { headers: { Authorization: `Bearer ${token}` } });
    if (res.ok) remote = remoteAges(await res.json());
    else if (res.status !== 404) warn(`the account could not be read (${res.status})`);
  } catch (err) { warn(err?.message ?? 'offline'); }
  if (remote) choice.set(remote, 'account');
  else if (choice.get().length) await put(choice.get());
  choice.subscribe((ages, from) => { if (from !== 'account') void put(ages); });
  return { synced: true, from: remote ? 'account' : 'device' };
}

// ---------------------------------------------------------------------------------------
// The tables: a shown string's words at other ages.
// ---------------------------------------------------------------------------------------

/** A string as the tables key it: spaces run together, ends trimmed. */
export const keyOf = (text) => String(text ?? '').replace(/\s+/g, ' ').trim();

/**
 * Where a key sits in a table. A long one (a building's "why" note runs to thousands of
 * characters, and 1835 has 3,368 of them) is held as a 53-bit hash and its length rather
 * than as the whole string, so a scene's table keeps its tellings and not a second copy of
 * every note it tells (1835's table held about 23 MB, and 14 MB so).
 */
export function slotOf(key) {
  if (key.length <= 96) return key;
  let h1 = 0xdeadbeef, h2 = 0x41c6ce57;
  for (let i = 0; i < key.length; i++) {
    const c = key.charCodeAt(i);
    h1 = Math.imul(h1 ^ c, 2654435761); h2 = Math.imul(h2 ^ c, 1597334677);
  }
  h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
  h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
  return `#${(4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36)}:${key.length}`;
}

/**
 * A table of entries `{ text, own?, levels: { <age>: words } }`: `own` is the age the text
 * itself is written at (18+ for a card's words as written; a telling's own band for a
 * jaunt). Returns a Map from slotOf(keyOf(text)) to { own, levels }.
 */
export function tableOf(entries = []) {
  const map = new Map();
  for (const e of entries ?? []) {
    if (!e || typeof e.text !== 'string') continue;
    const levels = {};
    for (const id of LEVEL_IDS) if (typeof e.levels?.[id] === 'string' && e.levels[id].trim()) levels[id] = e.levels[id];
    const own = LEVEL_IDS.includes(e.own) ? e.own : WRITTEN;
    delete levels[own];
    if (Object.keys(levels).length) map.set(slotOf(keyOf(e.text)), { own, levels });
  }
  return map;
}

const tables = new Set();
/** Add a table to those every card reads; returns a function that takes it away. */
export function addTable(table) {
  const t = table instanceof Map ? table : tableOf(table);
  tables.add(t);
  refreshAll();
  return () => { tables.delete(t); refreshAll(); };
}
export function lookup(text) {
  const key = keyOf(text);
  if (!key) return null;
  const slot = slotOf(key);
  for (const t of tables) { const hit = t.get(slot); if (hit) return hit; }
  return null;
}
/** Tests only. */
export function clearTables() { tables.clear(); }

/** The words of `entry` at age `id`: that age's own, else the nearest older age written,
 *  else the nearest younger; the text itself where `id` is its own age. */
export function wordsAt(entry, original, id) {
  if (!entry || id === entry.own) return original;
  const at = (a) => (a === entry.own ? original : entry.levels[a]);
  if (at(id) != null) return at(id);
  const r = rankOf(id);
  for (let i = r + 1; i < LEVEL_IDS.length; i++) if (at(LEVEL_IDS[i]) != null) return at(LEVEL_IDS[i]);
  for (let i = r - 1; i >= 0; i--) if (at(LEVEL_IDS[i]) != null) return at(LEVEL_IDS[i]);
  return original;
}

/** A scene's written levels, data/reading/<scene>.json, fetched once and added. */
const loads = new Map();
export function loadSceneLevels(dataBase, scene, fetchFn = (u) => fetch(u, { cache: 'no-cache' })) {
  const key = `${String(dataBase)}|${scene}`;
  if (!loads.has(key)) {
    loads.set(key, Promise.resolve().then(() => fetchFn(new URL(`reading/${encodeURIComponent(scene)}.json`, dataBase)))
      .then((res) => (res.ok ? res.json() : res.status === 404 ? { entries: [] } : Promise.reject(new Error(`reading/${scene}.json: ${res.status}`))))
      .then((doc) => { addTable(doc.entries ?? []); return true; })
      .catch((err) => { console.warn('[4D Chicago] reading levels: cards keep their words as written', err); return false; }));
  }
  return loads.get(key);
}

/**
 * A jaunt's other tellings as a table over the one being walked (T-3621: every jaunt is
 * told at 3-5, 6-8, 9-10 and 11-12, `version_of` naming the jaunt it retells, stop for
 * stop). `walked` and each of `tellings` are compiled jaunts; a telling is used only where
 * its stops line up with the walked one's, one for one. The 18+ tellings stage other
 * scenes, so they are not read here.
 */
export function tellingTable(walked, tellings = []) {
  const ownOf = (j) => levelOfGrade(j?.grade_band) || WRITTEN;
  const own = ownOf(walked);
  const entries = new Map();
  const add = (text, id, words) => {
    const k = keyOf(text), w = keyOf(words);
    if (!k || !w || k === w) return;
    if (!entries.has(k)) entries.set(k, { text: k, own, levels: {} });
    entries.get(k).levels[id] ??= words;
  };
  const paras = (t) => String(t ?? '').split(/\n\s*\n/).map((s) => s.trim()).filter(Boolean);
  const pair = (a, b, id) => { const A = paras(a), B = paras(b); if (A.length === B.length) A.forEach((p, i) => add(p, id, B[i])); };
  for (const other of tellings) {
    if (!other || other.audience === 'adults' || other.id === walked?.id) continue;
    const id = ownOf(other);
    if (!id || id === own) continue;
    const S = walked?.stops ?? [], T = other.stops ?? [];
    if (S.length !== T.length) continue;
    const each = (list, other, words) => { const A = list ?? [], B = other ?? []; if (A.length === B.length) A.forEach((x, i) => pair(words(x), words(B[i]), id)); };
    pair(walked.opening?.text, other.opening?.text, id);
    // The panel shows the opening without its "JAUNT: ITS TITLE." (jaunt-panel.js openingParagraphs).
    const head = (t) => paras(t)[0]?.replace(/^JAUNT:\s*[^.!?]*[.!?]\s*/, '') ?? '';
    add(head(walked.opening?.text), id, head(other.opening?.text));
    pair(walked.premise, other.premise, id);
    each(S, T, (s) => s?.text);
    each(S, T, (s) => s?.narrative);
    each(walked.legs, other.legs, (l) => l?.story);
    each(walked.endings, other.endings, (e) => e?.text);
    pair(walked.keepsake?.text, other.keepsake?.text, id);
  }
  return tableOf([...entries.values()]);
}

// ---------------------------------------------------------------------------------------
// The tabs.
// ---------------------------------------------------------------------------------------

const ORIGINAL = new WeakMap();
const SKIP = '.reading-tabs, script, style, input, textarea, select, button, summary, [data-reading-skip]';

/**
 * A line drawn as its words and then its last word in a span of its own, so that the last word
 * and the grade dot after it never part at a wrap (inspect-design.js `tailed`, marked
 * `data-reading-line`). The tabs read and say it as one string: this stands in for its text
 * node, the same object every time, its words the two nodes' together.
 */
function lineNode(el) {
  if (el.__readingLine) return el.__readingLine;
  const first = (n) => (n?.childNodes?.[0]?.nodeType === 3 ? n.childNodes[0] : null);
  const head = () => first(el);
  const tail = () => first(el.querySelector?.('.sg-tail'));
  el.__readingLine = {
    get data() { return `${head()?.data ?? ''}${tail()?.data ?? ''}`; },
    set data(text) {
      const words = String(text).split(' ');
      const last = words.pop();
      const h = head(), t = tail();
      if (!t) { if (h) h.data = String(text); return; }
      t.data = last;
      if (h) h.data = words.length ? `${words.join(' ')} ` : '';
    },
  };
  return el.__readingLine;
}

function proseNodes(root) {
  const out = [];
  const walk = (n) => {
    for (const c of Array.from(n.childNodes ?? [])) {
      if (c.nodeType === 3) { if ((ORIGINAL.get(c) ?? c.data).trim().length > 1) out.push(c); }
      else if (c.nodeType === 1 && c.dataset && 'readingLine' in c.dataset) {
        const line = lineNode(c);
        if ((ORIGINAL.get(line) ?? line.data).trim().length > 1) out.push(line);
      } else if (c.nodeType === 1 && !(c.matches?.(SKIP))) walk(c);
    }
  };
  walk(root);
  return out;
}

/** Each text node under `root` that a table holds, with its words as written and its entry. */
export function levelledIn(root) {
  const found = [];
  for (const n of proseNodes(root)) {
    const original = ORIGINAL.get(n) ?? n.data;
    const entry = lookup(original);
    if (entry) found.push({ node: n, original, entry });
  }
  return found;
}

/** The ages a card can be read at: every age one of its strings is written at. */
export function cardAges(found) {
  const ages = new Set();
  for (const { entry } of found) { ages.add(entry.own); for (const id of Object.keys(entry.levels)) ages.add(id); }
  return tidy([...ages]);
}

/** The age a card opens at: the highest the reader chose, where the card has it; else the
 *  nearest older age it has; else its highest. With no age chosen, the card's own words
 *  (the age its first levelled string is written at). */
export function openingAge(ages, choice = readingChoice(), found = []) {
  if (!ages.length) return WRITTEN;
  if (!choice.get().length) return found[0]?.entry.own ?? ages[ages.length - 1];
  const want = choice.top();
  if (ages.includes(want)) return want;
  const above = ages.find((a) => rankOf(a) > rankOf(want));
  return above ?? ages[ages.length - 1];
}

/** Say every levelled string under `root` at age `id`. */
export function sayAt(root, id, found = levelledIn(root)) {
  for (const { node, original, entry } of found) {
    if (!ORIGINAL.has(node)) ORIGINAL.set(node, original);
    const words = wordsAt(entry, original, id);
    // Keep the node's own leading and trailing space: it sits between other inline nodes.
    const lead = /^\s*/.exec(original)[0], tail = /\s*$/.exec(original)[0];
    const next = words === original ? original : `${lead}${words.trim()}${tail}`;
    if (node.data !== next) node.data = next;
  }
}

/** The page names where its scene's written levels come from; the first card to open asks. */
let source = null, asked = false;
export function setLevelsSource(fn) { source = fn; asked = false; }
function ask() { if (!asked && typeof source === 'function') { asked = true; try { void source(); } catch { /* the card keeps its words */ } } }

const mounted = new Set();
function refreshAll() {
  for (const ref of [...mounted]) {
    const root = ref.deref?.() ?? ref;
    if (!root || root.isConnected === false) { mounted.delete(ref); continue; }
    try { readingTabs(root, root.__readingOptions ?? {}); } catch (err) { console.warn('[4D Chicago] reading tabs', err); }
  }
}

/**
 * Lay the age tabs over a card. `root` is the card; the row goes after `after` (an element
 * inside it, e.g. its header) or first in `into` (default: first in the card). Call it
 * again after the card is redrawn; it finds and re-uses its row. Returns the age shown.
 */
export function readingTabs(root, { after = null, into = null, choice = readingChoice(), label = 'Reading age' } = {}) {
  if (!root) return WRITTEN;
  ask();
  root.__readingOptions = { after, into, choice, label };
  if (!root.__readingRef) { root.__readingRef = typeof WeakRef === 'function' ? new WeakRef(root) : root; mounted.add(root.__readingRef); }
  const doc = root.ownerDocument ?? globalThis.document;
  const found = levelledIn(root);
  const ages = cardAges(found);
  let row = root.querySelector?.('.reading-tabs') ?? null;
  if (ages.length < 2) {
    if (row) row.remove();
    for (const node of proseNodes(root)) { const original = ORIGINAL.get(node); if (original != null && node.data !== original) node.data = original; }
    if (root.dataset) delete root.dataset.readingAge;
    return WRITTEN;
  }
  root.dataset ??= {};
  let age = root.dataset.readingAge && ages.includes(root.dataset.readingAge) ? root.dataset.readingAge : openingAge(ages, choice, found);
  if (!row) {
    row = doc.createElement('div');
    row.className = 'reading-tabs';
    row.setAttribute('role', 'tablist');
    row.setAttribute('aria-label', label);
    if (after?.after) after.after(row);
    else if (into) into.prepend(row);
    else root.prepend(row);
  }
  const head = doc.createElement('span');
  head.className = 'reading-tabs-label'; head.textContent = 'Age'; head.setAttribute('aria-hidden', 'true');
  // The oldest tab, where it is the card's own words, is read by every older age too: "11+".
  const owns = new Set(found.map((f) => f.entry.own));
  const oldest = ages[ages.length - 1];
  const covers = owns.size === 1 && owns.has(oldest) && oldest !== WRITTEN;
  const tabs = ages.map((id) => {
    const b = doc.createElement('button');
    b.type = 'button'; b.className = 'reading-tab'; b.setAttribute('role', 'tab');
    b.dataset.readingAge = id;
    const open = covers && id === oldest;
    const low = levelLabel(id).split('–')[0];
    b.textContent = open ? `${low}+` : levelLabel(id);
    b.setAttribute('aria-label', id === WRITTEN ? 'Ages 18 and over' : open ? `Ages ${low} and over` : `Ages ${levelLabel(id)}`);
    const yours = choice.has(id) || (open && choice.get().some((a) => rankOf(a) > rankOf(id)));
    b.title = [b.getAttribute('aria-label'), owns.size === 1 && owns.has(id) ? 'as first written' : '', yours ? 'your reading age' : ''].filter(Boolean).join(' · ');
    if (yours) b.classList.add('reading-tab-yours');
    b.addEventListener('click', (ev) => {
      ev?.stopPropagation?.();
      root.dataset.readingAge = id;
      sayAt(root, id);
      for (const t of row.querySelectorAll('.reading-tab')) t.setAttribute('aria-selected', String(t.dataset.readingAge === id));
      syncRoving(row);
    });
    return b;
  });
  row.replaceChildren(head, ...tabs);
  root.dataset.readingAge = age;
  sayAt(root, age, found);
  for (const t of tabs) t.setAttribute('aria-selected', String(t.dataset.readingAge === age));
  // T-3671: one Tab stop for the row, the arrows and Home/End along it.
  syncRoving(row);
  rovingTabs(row);
  return age;
}

/** A redrawn card keeps the age its reader picked only while it is the same card: forget it. */
export function forgetAge(root) { if (root?.dataset) delete root.dataset.readingAge; }

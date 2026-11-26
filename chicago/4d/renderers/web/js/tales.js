// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553: "Tell me a story". Everyone in town has stories, told in their own voice.
 *
 * Kevin, 2026-11-16: "For all characters in all years, add to interactions a tell me a story
 * action, pick a random story from a personal and if no personal one exisists, pull a story
 * from the story library ... once you hear one you don't hear that one again from them."
 *
 * The library for a scene is data/tales/<scene>.json, written by tools/build_tales.py from
 * docs/RESEARCH/tales-3553 (a reconstruction, liberty L-tales-3553):
 *   tales     [{ id, roles[], title, text[], sex?, age?: [low, high], origin?: [code], from?, to?, meet?: { person, name } }]
 *   personal  { personId: [tale] }   a named person's own stories, told before any other
 *   tellers   { personId: 'role,role/sex[/c][/a<age>][/o<origin>]' }   precomputed, so the 4 MB 1835 directory
 *             is never read at run time
 *   fallback  { m: role, f: role }   for a figure the builder did not know
 *
 * The file is fetched on the first story asked for, never at boot (phone memory).
 *
 * Which story, for person P:
 *   1. one of P's own that P has not told you yet, at random;
 *   2. else from the library for P's roles, one nobody has told you yet, at random but leaning
 *      to what P's temperament and history make them talk about, so that forty soldiers tell
 *      forty different stories, each his own kind;
 *   3. else one P has not told you, the one you heard longest ago from anyone;
 *   4. else (P has told you all of them) the one P told you longest ago.
 * A tale with a date window (`from` / `to`, ISO dates) is told only inside it while any
 * other tale is left; the 1812 jaunts move the date. What has been heard is kept per scene
 * in localStorage (`chicago4d.tales.heard.<scene>`), every access guarded.
 */

export const HEARD_KEY = 'chicago4d.tales.heard';
const HEARD_MAX = 4000;               // remembered tellings per scene; the oldest go first

const local = () => { try { return globalThis.localStorage ?? null; } catch { return null; } };

/** A teller row ('soldier,militia/m/c/a9/oirish') as { roles, sex, child, age, origin }: after
 *  the roles and sex, `c` marks a child, `a<n>` their age where the record gives one, and
 *  `o<code>` where they come from (the owner, 2026-11-26: every story fits its teller's age,
 *  sex and situation). */
export function readTeller(key) {
  const [roles = '', sex = 'm', ...rest] = String(key ?? '').split('/');
  const who = { roles: roles.split(',').filter(Boolean), sex: sex === 'f' ? 'f' : 'm', child: false, age: null, origin: null };
  for (const r of rest) {
    if (r === 'c') who.child = true;
    else if (/^a\d+$/.test(r)) who.age = Number(r.slice(1));
    else if (/^o[a-z_]+$/.test(r)) who.origin = r.slice(1);
  }
  return who;
}

/**
 * Whether a tale or question can be told by this teller, beyond their roles: a story written for
 * one sex (`sex`), for an age (`age: [low, high]`, either end open) or for people from somewhere
 * (`origin: [code]`) is never told by anyone else. A teller whose record gives no age or origin
 * is not refused for it. Louis Ream, sixteen, is never again the girl who saw the Fair of 1893.
 */
export function suits(item, who) {
  if (!item || !who) return false;
  if (item.sex && item.sex !== who.sex) return false;
  const [low = null, high = null] = item.age ?? [];
  if (who.age != null && ((low != null && who.age < low) || (high != null && who.age > high))) return false;
  if (item.origin?.length && who.origin && !item.origin.includes(who.origin)) return false;
  return true;
}

const inWindow = (t, date) => !date || ((!t.from || date >= t.from) && (!t.to || date <= t.to));

/** A small stable hash (FNV-1a) of a string, for choices that must not change between visits. */
export function hash(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
  return h >>> 0;
}

const PRONOUNS = {
  m: { He: 'He', he: 'he', His: 'His', his: 'his', him: 'him', himself: 'himself' },
  f: { He: 'She', he: 'she', His: 'Her', his: 'her', him: 'her', himself: 'herself' },
};

/**
 * T-3553 (the owner, 2026-11-16: "Give everyone a unique personality as well their words and
 * perspectives are driven from their history"). A person's temperament(s), the things they talk
 * about, and who their record says they are, from `persona` ("temper+second|topic.topic|who").
 * A figure the library does not know gets a temperament from a hash of their id.
 * @returns {{ tempers: string[], topics: string[], who: string, label: string, sex: 'm'|'f' }}
 */
export function personaOf(lib, personId, sex = null) {
  const row = lib?.persona?.[personId];
  const codes = Object.keys(lib?.tempers ?? {});
  const teller = lib?.tellers?.[personId] ? readTeller(lib.tellers[personId]) : null;
  const s = teller?.sex ?? (sex === 'f' ? 'f' : 'm');
  let tempers, topics = [], who = '';
  if (row) {
    const [t = '', k = '', ...w] = row.split('|');
    tempers = t.split('+').filter((x) => lib.tempers?.[x]);
    topics = k.split('.').filter(Boolean);
    who = w.join('|');
  } else {
    tempers = codes.length ? [codes[hash(String(personId)) % codes.length]] : [];
  }
  const names = tempers.map((x) => lib.tempers[x].name);
  const label = names.length > 1 ? `${names[0]}, a little ${names[1].toLowerCase()}` : (names[0] ?? '');
  return { tempers, topics, who, label, sex: s };
}

/** How this person comes to an answer: one of their temperaments' lines, chosen by `key`. */
export function mannerOf(lib, persona, key) {
  const t = persona?.tempers ?? [];
  if (!t.length) return '';
  const h = hash(`${key}`);
  const temper = lib.tempers[t[(h % 3 === 2 && t[1]) ? 1 : 0]];
  const line = temper.lines[(h >>> 3) % temper.lines.length];
  const p = PRONOUNS[persona.sex === 'f' ? 'f' : 'm'];
  return line.replace(/\{(He|he|His|his|him|himself)\}/g, (_, w) => p[w]);
}

/** How much a tale or question is the kind of thing this person talks about (0..3). */
export const leaning = (item, persona) => (item?.k ?? []).filter((k) => persona?.topics?.includes(k)).length;

/**
 * Pick a tale for `personId` from a loaded library. Pure: the caller keeps `heard`.
 * @param {object} lib      a data/tales/<scene>.json
 * @param {string} personId
 * @param {object} heard    { n, told: { taleId: n }, by: { personId: { taleId: n } } }
 * @param {object} [o]
 * @param {string} [o.sex]  'm' | 'f' for a figure the library has no teller row for
 * @param {string} [o.date] the scene date (ISO), for tales with a date window
 * @param {() => number} [o.random]
 * @returns {{ tale: object, own: boolean } | null}
 */
export function pickTale(lib, personId, heard, { sex = null, date = null, random = Math.random } = {}) {
  if (!lib) return null;
  const persona = personaOf(lib, personId, sex);
  const mine = heard.by?.[personId] ?? {};
  const told = heard.told ?? {};
  const any = (list) => list.length ? list[Math.floor(random() * list.length) % list.length] : null;
  // From several, the ones nearer what this person talks about are likelier (T-3553 personas).
  const likely = (list) => {
    if (!list.length) return null;
    const w = list.map((t) => 1 + 2 * leaning(t, persona));
    let r = random() * w.reduce((a, b) => a + b, 0);
    for (let i = 0; i < list.length; i++) { r -= w[i]; if (r < 0) return list[i]; }
    return list[list.length - 1];
  };
  const dated = (list) => { const d = list.filter((t) => inWindow(t, date)); return d.length ? d : list; };
  const oldest = (list, seen) => list.reduce((a, t) => ((seen[t.id] ?? -1) < (seen[a.id] ?? -1) ? t : a), list[0]);

  const own = dated(lib.personal?.[personId] ?? []);
  const fresh = own.filter((t) => !(t.id in mine));
  if (fresh.length) return { tale: any(fresh), own: true };

  const row = lib.tellers?.[personId];
  const who = row ? readTeller(row) : { ...readTeller(''), roles: [lib.fallback?.[sex === 'f' ? 'f' : 'm']].filter(Boolean), sex: sex === 'f' ? 'f' : 'm' };
  // Nobody sends you to find themselves; and nobody tells a story that is not theirs to tell.
  const mayTell = (t) => suits(t, who) && t.meet?.person !== personId;
  let pool = dated(lib.tales.filter((t) => t.roles.some((r) => who.roles.includes(r)) && mayTell(t)));
  // Short of their own roles' stories, the town's common ones for their sex, never a wrong one.
  if (!pool.length) pool = dated(lib.tales.filter((t) => t.roles.includes(lib.fallback?.[who.sex]) && mayTell(t)));
  const untold = pool.filter((t) => !(t.id in mine));
  const unheard = untold.filter((t) => !(t.id in told));
  if (unheard.length) return { tale: likely(unheard), own: false };
  if (untold.length) return { tale: oldest(untold, told), own: false };
  const all = [...own, ...pool];
  if (!all.length) return null;
  const again = oldest(all, mine);
  return { tale: again, own: own.includes(again) };
}

/** Note that `personId` told `taleId`; the oldest tellings are forgotten past HEARD_MAX. */
export function noteTold(heard, personId, taleId) {
  heard.n = (heard.n ?? 0) + 1;
  heard.told ??= {};
  heard.by ??= {};
  heard.told[taleId] = heard.n;
  (heard.by[personId] ??= {})[taleId] = heard.n;
  const cut = heard.n - HEARD_MAX;
  if (cut > 0 && heard.n % 200 === 0) {
    for (const [id, n] of Object.entries(heard.told)) if (n <= cut) delete heard.told[id];
    for (const [p, ids] of Object.entries(heard.by)) {
      for (const [id, n] of Object.entries(ids)) if (n <= cut) delete ids[id];
      if (!Object.keys(ids).length) delete heard.by[p];
    }
  }
  return heard;
}

/**
 * The scene's storyteller: loads its library on first use and remembers what you heard.
 * @param {object} o
 * @param {string} o.scene
 * @param {string} [o.base]     where data/tales/ is served
 * @param {(url: string) => Promise<object>} [o.fetchJson]
 * @param {Storage|null} [o.storage]
 * @param {() => string|null} [o.date]
 * @param {() => number} [o.random]
 */
export function createTales({ scene, base = './data/tales/', fetchJson = null, storage = local(),
  date = () => null, random = Math.random } = {}) {
  const key = `${HEARD_KEY}.${scene}`;
  let lib = null, loading = null;
  let heard = { n: 0, told: {}, by: {} };
  try { const saved = JSON.parse(storage?.getItem(key) || 'null'); if (saved && typeof saved === 'object') heard = { n: 0, told: {}, by: {}, ...saved }; } catch { /* a fresh memory */ }
  const get = fetchJson ?? (async (url) => {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`${url}: ${r.status}`);
    return r.json();
  });
  function load() {
    if (lib) return Promise.resolve(lib);
    loading ??= get(`${base}${scene}.json`).then((d) => { lib = d; return d; }).catch((e) => { loading = null; throw e; });
    return loading;
  }
  return {
    load,
    get loaded() { return !!lib; },
    get heard() { return heard; },
    /** The next story `personId` tells you: { tale, own } (and it is remembered as heard). */
    async tell(personId, { sex = null } = {}) {
      const l = await load();
      const got = pickTale(l, personId, heard, { sex, date: date(), random });
      if (!got) return null;
      noteTold(heard, personId, got.tale.id);
      try { storage?.setItem(key, JSON.stringify(heard)); } catch { /* the memory lasts the visit */ }
      return got;
    },
    /** Forget every story heard in this scene. */
    forget() { heard = { n: 0, told: {}, by: {} }; try { storage?.removeItem(key); } catch { /* none kept */ } },
  };
}

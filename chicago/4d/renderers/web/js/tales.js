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
 *   tales     [{ id, roles[], title, text[], sex?, from?, to?, meet?: { person, name } }]
 *   personal  { personId: [tale] }   a named person's own stories, told before any other
 *   tellers   { personId: 'role,role/sex[/c]' }   precomputed, so the 4 MB 1835 directory
 *             is never read at run time
 *   fallback  { m: role, f: role }   for a figure the builder did not know
 *
 * The file is fetched on the first story asked for, never at boot (phone memory).
 *
 * Which story, for person P:
 *   1. one of P's own that P has not told you yet, at random;
 *   2. else from the library for P's roles, one nobody has told you yet, at random, so that
 *      forty soldiers tell forty different stories;
 *   3. else one P has not told you, the one you heard longest ago from anyone;
 *   4. else (P has told you all of them) the one P told you longest ago.
 * A tale with a date window (`from` / `to`, ISO dates) is told only inside it while any
 * other tale is left; the 1812 jaunts move the date. What has been heard is kept per scene
 * in localStorage (`chicago4d.tales.heard.<scene>`), every access guarded.
 */

export const HEARD_KEY = 'chicago4d.tales.heard';
const HEARD_MAX = 4000;               // remembered tellings per scene; the oldest go first

const local = () => { try { return globalThis.localStorage ?? null; } catch { return null; } };

/** A teller row ('soldier,militia/m/c') as { roles, sex, child }. */
export function readTeller(key) {
  const [roles = '', sex = 'm', c = ''] = String(key ?? '').split('/');
  return { roles: roles.split(',').filter(Boolean), sex: sex === 'f' ? 'f' : 'm', child: c === 'c' };
}

const inWindow = (t, date) => !date || ((!t.from || date >= t.from) && (!t.to || date <= t.to));

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
  const mine = heard.by?.[personId] ?? {};
  const told = heard.told ?? {};
  const any = (list) => list.length ? list[Math.floor(random() * list.length) % list.length] : null;
  const dated = (list) => { const d = list.filter((t) => inWindow(t, date)); return d.length ? d : list; };
  const oldest = (list, seen) => list.reduce((a, t) => ((seen[t.id] ?? -1) < (seen[a.id] ?? -1) ? t : a), list[0]);

  const own = dated(lib.personal?.[personId] ?? []);
  const fresh = own.filter((t) => !(t.id in mine));
  if (fresh.length) return { tale: any(fresh), own: true };

  const row = lib.tellers?.[personId];
  const who = row ? readTeller(row) : { roles: [lib.fallback?.[sex === 'f' ? 'f' : 'm']].filter(Boolean), sex: sex === 'f' ? 'f' : 'm' };
  // Nobody sends you to find themselves.
  const fits = (t) => t.roles.some((r) => who.roles.includes(r)) && (!t.sex || t.sex === who.sex) && t.meet?.person !== personId;
  let pool = dated(lib.tales.filter(fits));
  if (!pool.length) pool = dated(lib.tales.filter((t) => t.roles.some((r) => who.roles.includes(r)) && t.meet?.person !== personId));
  const untold = pool.filter((t) => !(t.id in mine));
  const unheard = untold.filter((t) => !(t.id in told));
  if (unheard.length) return { tale: any(unheard), own: false };
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

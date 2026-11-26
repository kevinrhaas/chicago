// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3553: "Ask a question". Everyone you can greet offers you five questions about their life and
 * times; each answer has one or two follow-ups that reveal more, and often sends you to someone.
 *
 * The owner, 2026-11-16: "add ask a question to everyone and give 5 different options for
 * everyone, you can reuse questions but answers should be unique for the person and role ...
 * allow one or two follow on questions for each quest to get more detail and context ... don't
 * repeat stories"; and "Give everyone a unique personality ... the kinds of perspectives and
 * language and story would be related to the kinds of things they would discuss with you".
 *
 * The questions live beside the stories in data/tales/<scene>.json (tools/build_tales.py, from
 * docs/RESEARCH/asks-3553; a reconstruction, liberty L-tales-3553):
 *   asks           [{ id, roles[], q, a[], more: [{ q, a[] }], k[], sex?, age?, origin?, meet? }]
 *   personal_asks  { personId: [ask] }   what only that person is asked, offered first
 *   persona        { personId: 'temper+temper|topic.topic|who' }  (tales.js personaOf)
 *
 * Which five, for person P:
 *   1. P's own questions they have not answered yet;
 *   2. then questions for P's roles that P has not answered, the ones nobody has answered for you
 *      first, and among those the ones nearer what P talks about (their topics);
 *   3. then, if still short, questions for kindred roles (`ask_wider`, by sex), so that a man
 *      of a small trade still has five things to be asked; never another people's.
 * The five stay P's until every one is answered; then five more, never one P answered before
 * until P has answered them all. Kept per scene in localStorage (`chicago4d.asks.<scene>`).
 */

import { readTeller, suits, personaOf, leaning } from './tales.js';

export const ASKED_KEY = 'chicago4d.asks';
export const ASK_COUNT = 5;
const ASKED_MAX = 4000;

const local = () => { try { return globalThis.localStorage ?? null; } catch { return null; } };
/** The roles and sex of `personId` as the library knows them (or the fallback). */
export function whoAsked(lib, personId, sex = null) {
  const row = lib?.tellers?.[personId];
  if (row) {
    const t = readTeller(row);
    return t;
  }
  const s = sex === 'f' ? 'f' : 'm';
  return { ...readTeller(''), roles: [lib?.fallback?.[s]].filter(Boolean), sex: s };
}

/**
 * The five questions `personId` offers now. Pure: the caller keeps `state`.
 * @param {object} lib    a data/tales/<scene>.json
 * @param {object} state  { n, asked: { askId: n }, by: { personId: { set: [askId], done: { askId: n } } } }
 * @returns {{ asks: object[], done: Set<string> }}
 */
export function pickAsks(lib, personId, state, { sex = null, random = Math.random, count = ASK_COUNT } = {}) {
  if (!lib) return { asks: [], done: new Set() };
  const byId = new Map([...(lib.asks ?? []), ...(lib.personal_asks?.[personId] ?? [])].map((a) => [a.id, a]));
  const mine = (state.by ??= {})[personId] ??= { set: [], done: {} };
  const kept = (mine.set ?? []).map((id) => byId.get(id)).filter(Boolean);
  if (kept.length && kept.some((a) => !(a.id in mine.done))) {
    return { asks: kept, done: new Set(kept.filter((a) => a.id in mine.done).map((a) => a.id)) };
  }
  const who = whoAsked(lib, personId, sex);
  const persona = personaOf(lib, personId, sex);
  const asked = state.asked ?? {};
  // A question is answered only by someone it fits: their sex, their age, where they are from.
  const sexOk = (a) => suits(a, who);
  const notMe = (a) => a.meet?.person !== personId;
  const choose = (list, n, fresh) => {
    const scored = list.filter((a) => fresh(a)).map((a) => ({ a,
      s: (a.id in asked ? 0 : 3) + 1.5 * leaning(a, persona) + 2 * random() }));
    return scored.sort((x, y) => y.s - x.s).slice(0, n).map((x) => x.a);
  };
  const build = (fresh) => {
    const own = (lib.personal_asks?.[personId] ?? []).filter(fresh);
    const out = own.slice(0, count);
    const have = new Set(out.map((a) => a.id));
    const add = (list) => { for (const a of choose(list.filter((x) => !have.has(x.id)), count - out.length, fresh)) { out.push(a); have.add(a.id); } };
    const lib2 = (lib.asks ?? []).filter((a) => sexOk(a) && notMe(a));
    add(lib2.filter((a) => a.roles.some((r) => who.roles.includes(r))));
    if (out.length < count) {
      const wider = new Set(who.roles.flatMap((r) => lib.ask_wider?.[r]?.[who.sex] ?? []));
      add(lib2.filter((a) => a.roles.some((r) => wider.has(r))));
    }
    return out;
  };
  let asks = build((a) => !(a.id in mine.done));
  if (!asks.length) {                    // P has answered everything: begin again, oldest first
    mine.done = {};
    asks = build(() => true);
  }
  mine.set = asks.map((a) => a.id);
  return { asks, done: new Set() };
}

/** Note that `personId` answered `askId`; the oldest answers are forgotten past ASKED_MAX. */
export function noteAsked(state, personId, askId) {
  state.n = (state.n ?? 0) + 1;
  (state.asked ??= {})[askId] = state.n;
  const mine = ((state.by ??= {})[personId] ??= { set: [], done: {} });
  (mine.done ??= {})[askId] = state.n;
  const cut = state.n - ASKED_MAX;
  if (cut > 0 && state.n % 200 === 0) {
    for (const [id, n] of Object.entries(state.asked)) if (n <= cut) delete state.asked[id];
    for (const [p, m] of Object.entries(state.by)) {
      const last = Math.max(0, ...Object.values(m.done ?? {}));
      if (last <= cut) delete state.by[p];
    }
  }
  return state;
}

/**
 * The scene's questions: shares the stories' library (one fetch), remembers what you asked.
 * @param {object} o
 * @param {string} o.scene
 * @param {() => Promise<object>} o.load     the library loader (createTales().load)
 * @param {Storage|null} [o.storage]
 * @param {() => number} [o.random]
 */
export function createAsks({ scene, load, storage = local(), random = Math.random } = {}) {
  const key = `${ASKED_KEY}.${scene}`;
  let state = { n: 0, asked: {}, by: {} };
  try { const saved = JSON.parse(storage?.getItem(key) || 'null'); if (saved && typeof saved === 'object') state = { n: 0, asked: {}, by: {}, ...saved }; } catch { /* a fresh memory */ }
  const save = () => { try { storage?.setItem(key, JSON.stringify(state)); } catch { /* the memory lasts the visit */ } };
  return {
    get state() { return state; },
    /** `personId`'s questions now, with their persona: { lib, asks, done, persona }. */
    async offer(personId, { sex = null } = {}) {
      const lib = await load();
      const got = pickAsks(lib, personId, state, { sex, random });
      save();
      return { lib, ...got, persona: personaOf(lib, personId, sex) };
    },
    /** Note an answered question. */
    asked(personId, askId) { noteAsked(state, personId, askId); save(); },
    /** Forget every question asked in this scene. */
    forget() { state = { n: 0, asked: {}, by: {} }; try { storage?.removeItem(key); } catch { /* none kept */ } },
  };
}

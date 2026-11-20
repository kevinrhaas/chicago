/** A small, curated hunt from the existing picture catalogue. No image or world is loaded here. */
import { creditOf, yearLabel } from './photos-tab.js';

/**
 * One hunt per year that has at least three pictures whose solved camera stands on safe ground
 * in that year's world (T-3657, T-3677). Each set keeps its own share link (`year=` must name
 * it), its own daily order and its own saved record. Identity only: dates, credit, kind, images
 * and solved positions always come from the catalogue. 1904 keeps its first key, seed and
 * record format, so earlier links and progress still open.
 * No set, and why (docs/STATUS.md, T-3677): 1812 has two such pictures (Eastman 1854, the
 * Chicago Magazine 1857); Lossing's and Sarony's views stand in the river, Currey's Hardscrabble
 * view across the South Branch outside the modelled ground, and Cram's, the Teich postcard's and
 * Gemmell's eyes are 18 to 66 m up. 1871 has no catalogued picture of its scene at all.
 */
const PRINTS = Object.freeze(['ENGRAVING', 'LITHO', 'PLATE', 'ILLUSTRATION', 'PHOTO']);
export const HUNT_SETS = Object.freeze({
  1904: Object.freeze({ year: '1904', version: 1, storageKey: 'chicago4d.photoHunt.v1', seed: 'photo-hunt',
    noun: 'photo', kinds: Object.freeze(['PHOTO']), latest: 1904,
    pictures: Object.freeze({
      'a18-rba-taylor-2135-glessner-ne': 'glessner_house',
      'a18-gh-cornell-glessner-rear-c1887': 'glessner_house',
      'a18-rba-taylor-1801-kimball-c1895': 'kimball_house_1801_prairie',
      'a18-rba-levy-1812-wheeler': 'wheeler_house_1812_prairie',
      'a16-pullman-det-4a08065': 'pullman_house_1729_prairie',
    }) }),
  // Prints and drawings, all made after 1835. Only three pictures of 1835 have a camera solved as
  // a place to stand: a shorter set, not a padded one.
  1835: Object.freeze({ year: '1835', version: 1, storageKey: 'chicago4d.photoHunt.1835.v1', seed: 'photo-hunt:1835',
    noun: 'picture', kinds: PRINTS, latest: 1930,
    pictures: Object.freeze({
      'early-green-tree-andreas-1884': 'green_tree_tavern',
      'early-green-tree-kurz-allison-1893': 'green_tree_tavern',
      'early-green-tree-trowbridge-1902': 'green_tree_tavern',
    }) }),
});
export const huntSet = (year) => (Object.hasOwn(HUNT_SETS, String(year)) ? HUNT_SETS[String(year)] : null);
export const huntCount = (year = '1904') => Object.keys(huntSet(year)?.pictures ?? {}).length;
// The 1904 names T-3657 exported, unchanged.
export const HUNT_VERSION = HUNT_SETS[1904].version;
export const HUNT_YEAR = HUNT_SETS[1904].year;
export const HUNT_STORAGE_KEY = HUNT_SETS[1904].storageKey;
export const HUNT_PHOTOS = HUNT_SETS[1904].pictures;
// A solved eye higher than this is a bird's-eye, not a spot someone stood on the ground.
export const HUNT_MAX_EYE_M = 10;

export function validHuntDay(value) {
  if (typeof value !== 'string' || !/^20\d{2}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.valueOf()) && date.toISOString().slice(0, 10) === value;
}
export const huntDay = (now = new Date()) => now.toISOString().slice(0, 10);

/** An invalid challenge cannot name a file, change the year or carry arbitrary pictures. */
export function parseHuntLink(search = '') {
  const q = new URLSearchParams(search);
  const day = q.get('huntDay'), set = q.getAll('year').length === 1 ? huntSet(q.get('year')) : null;
  return set && q.getAll('hunt').length === 1 && q.get('hunt') === String(set.version)
    && q.getAll('huntDay').length === 1 && validHuntDay(day) ? { day, version: set.version, year: set.year } : null;
}

export function huntLink(day, href = globalThis.location?.href, year = HUNT_YEAR) {
  const set = huntSet(year);
  if (!set || !validHuntDay(day)) return null;
  try {
    const url = new URL(href);
    if (!/^https?:$/.test(url.protocol)) return null;
    // Retain this site's source/dev/production path; never copy account or debug state.
    url.search = ''; url.hash = ''; url.username = ''; url.password = '';
    url.searchParams.set('year', set.year); url.searchParams.set('nav', 'home');
    url.searchParams.set('hunt', String(set.version)); url.searchParams.set('huntDay', day);
    return url.href;
  } catch { return null; }
}

/** Stable FNV-1a seed and Fisher–Yates permutation. The same pictures; a different daily order. */
export function huntOrder(day, year = HUNT_YEAR) {
  const set = huntSet(year);
  if (!set || !validHuntDay(day)) return [];
  let state = 2166136261;
  for (const c of `${set.seed}:${set.version}:${day}`) state = Math.imul(state ^ c.charCodeAt(0), 16777619) >>> 0;
  const ids = Object.keys(set.pictures);
  for (let i = ids.length - 1; i > 0; i--) {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    const j = state % (i + 1); [ids[i], ids[j]] = [ids[j], ids[i]];
  }
  return ids;
}

export function safeHuntURL(value, base) {
  try { const url = new URL(value, base); return /^https?:$/.test(url.protocol) ? url.href : null; }
  catch { return null; }
}
const position = p => p && [p.e, p.n].every(v => Number.isFinite(v) && Math.abs(v) <= 100000);

/** A solved camera is evidence of a position, not permission to enter a wall or water. */
export function huntSpotSafe(row, { inBounds, isWater, blockedAt, barrierAt } = {}) {
  return !!(position(row) && inBounds?.(row.e, row.n) && !isWater?.(row.e, row.n)
    && !blockedAt?.(row.e, row.n) && !barrierAt?.(row.e, row.n));
}

/** `destinations` has already applied the catalogue's ownership rule to shared pictures. */
export function huntRounds(doc, destinations, day, year = HUNT_YEAR) {
  const set = huntSet(year);
  if (!set || !doc?.by_structure || !destinations?.byId || !validHuntDay(day)) return [];
  const base = safeHuntURL(doc.image_store?.base_url);
  if (!base) return [];
  const rounds = [];
  for (const id of huntOrder(day, set.year)) {
    const row = destinations.byId('photo', id), p = row?.picture;
    const years = p?.years, eye = p?.spot?.h;
    const thumbnail = p?.held?.t && safeHuntURL(p.held.t, base);
    // A failed catalogue check disables the round set instead of silently replacing evidence.
    if (!row || row.of !== set.pictures[id] || p?.id !== id || !set.kinds.includes(p.kind)
      || !creditOf(p) || !thumbnail || new URL(thumbnail).origin !== new URL(base).origin
      || !/^(public domain|no known restrictions)/i.test(p.rights ?? '')
      || !Array.isArray(years) || years.length !== 2
      || !years.every(y => Number.isInteger(y) && y >= 1800 && y <= set.latest) || years[0] > years[1]
      || !Number.isFinite(eye) || eye < 0 || eye > HUNT_MAX_EYE_M
      || !position(row) || ![row.yaw_deg, row.pitch_deg].every(Number.isFinite)) return [];
    rounds.push({ id, structure: row.of, title: p.title || row.label, kind: p.kind,
      name: doc.names?.[row.of] || row.label, credit: creditOf(p), holder: p.holder || '',
      rights: p.rights, date: p.date || '', years: yearLabel(p), made: years[0],
      later: years[0] > Number(set.year), image: thumbnail,
      source: safeHuntURL(p.url), full: p.held.f ? safeHuntURL(p.held.f, base) : null,
      target: { e: row.e, n: row.n, yaw: row.yaw_deg, pitch: row.pitch_deg } });
  }
  return rounds;
}

export function huntResult(round, guess) {
  if (!position(round?.target) || !position(guess)) return null;
  const distance = Math.hypot(round.target.e - guess.e, round.target.n - guess.n);
  return { distance, score: Math.round(1000 * Math.exp(-Math.max(0, distance - 5) / 50)) };
}

/** One challenge of a year's set, under 4 KiB. Answers remain usable in memory if storage refuses. */
export function createHuntSession({ day, rounds, storage = () => globalThis.localStorage, year = HUNT_YEAR } = {}) {
  const set = huntSet(year), total = huntCount(year);
  if (!set || !validHuntDay(day) || !total || rounds?.length !== total) throw new Error('Invalid photo hunt');
  // 1904's record keeps T-3657's shape; every later set names its year inside its own key.
  const own = set.year !== HUNT_YEAR;
  let cursor = 0, answers = [], issue = null, persisted = false;
  const store = () => typeof storage === 'function' ? storage() : storage;
  try {
    const raw = store()?.getItem(set.storageKey);
    if (raw) {
      if (raw.length > 4096) throw new Error('Too large');
      const saved = JSON.parse(raw);
      if (saved?.version !== set.version || (own ? saved.year !== set.year : 'year' in saved)
        || !validHuntDay(saved.day) || !Array.isArray(saved.answers)
        || saved.answers.length > total || !Number.isInteger(saved.cursor) || saved.cursor < 0
        || saved.cursor > total || saved.cursor > saved.answers.length || saved.answers.length > saved.cursor + 1)
        throw new Error('Invalid progress');
      const ids = huntOrder(saved.day, set.year);
      if (!saved.answers.every((a, i) => a?.id === ids[i] && (a.skipped === true || (a.skipped === false && position(a)))))
        throw new Error('Invalid answer');
      if (saved.day === day) { cursor = saved.cursor; answers = saved.answers; persisted = true; }
    }
  } catch { issue = 'unreadable'; }
  function save() {
    persisted = false;
    // A corrupt or inaccessible record is not overwritten until the visitor explicitly resets it.
    if (issue === 'unreadable') return;
    try {
      if (!store()?.setItem) throw new Error('No storage');
      store().setItem(set.storageKey, JSON.stringify(own ? { version: set.version, year: set.year, day, cursor, answers }
        : { version: set.version, day, cursor, answers }));
      issue = null; persisted = true;
    } catch { issue = 'unsaved'; }
  }
  return {
    get state() {
      const results = answers.map((answer, i) => answer.skipped ? { score: 0, distance: null } : huntResult(rounds[i], answer));
      return { day, year: set.year, total, cursor, answers: answers.map(a => ({ ...a })), results,
        score: results.reduce((sum, result) => sum + result.score, 0), issue, persisted, complete: cursor === total };
    },
    guess(at) {
      if (cursor >= total || answers[cursor] || !position(at)) return false;
      answers.push({ id: rounds[cursor].id, e: at.e, n: at.n, skipped: false }); save(); return true;
    },
    skip() {
      if (cursor >= total || answers[cursor]) return false;
      answers.push({ id: rounds[cursor].id, skipped: true }); save(); return true;
    },
    next() {
      if (cursor >= total || !answers[cursor]) return false;
      cursor++; save(); return true;
    },
    reset() { cursor = 0; answers = []; issue = null; save(); },
  };
}

/** A small, curated hunt from the existing picture catalogue. No image or world is loaded here. */
import { creditOf, yearLabel } from './photos-tab.js';

export const HUNT_VERSION = 1;
export const HUNT_YEAR = '1904';
export const HUNT_STORAGE_KEY = 'chicago4d.photoHunt.v1';
// Identity only: dates, credit, images and solved positions always come from the catalogue.
export const HUNT_PHOTOS = Object.freeze({
  'a18-rba-taylor-2135-glessner-ne': 'glessner_house',
  'a18-gh-cornell-glessner-rear-c1887': 'glessner_house',
  'a18-rba-taylor-1801-kimball-c1895': 'kimball_house_1801_prairie',
  'a18-rba-levy-1812-wheeler': 'wheeler_house_1812_prairie',
  'a16-pullman-det-4a08065': 'pullman_house_1729_prairie',
});

export function validHuntDay(value) {
  if (typeof value !== 'string' || !/^20\d{2}-\d{2}-\d{2}$/.test(value)) return false;
  const date = new Date(`${value}T00:00:00Z`);
  return Number.isFinite(date.valueOf()) && date.toISOString().slice(0, 10) === value;
}
export const huntDay = (now = new Date()) => now.toISOString().slice(0, 10);

/** An invalid challenge cannot name a file, change the year or carry arbitrary pictures. */
export function parseHuntLink(search = '') {
  const q = new URLSearchParams(search);
  const day = q.get('huntDay');
  return q.getAll('hunt').length === 1 && q.get('hunt') === String(HUNT_VERSION)
    && q.getAll('huntDay').length === 1 && validHuntDay(day)
    && q.getAll('year').length === 1 && q.get('year') === HUNT_YEAR ? { day, version: HUNT_VERSION } : null;
}

export function huntLink(day, href = globalThis.location?.href) {
  if (!validHuntDay(day)) return null;
  try {
    const url = new URL(href);
    if (!/^https?:$/.test(url.protocol)) return null;
    // Retain this site's source/dev/production path; never copy account or debug state.
    url.search = ''; url.hash = ''; url.username = ''; url.password = '';
    url.searchParams.set('year', HUNT_YEAR); url.searchParams.set('nav', 'home');
    url.searchParams.set('hunt', String(HUNT_VERSION)); url.searchParams.set('huntDay', day);
    return url.href;
  } catch { return null; }
}

/** Stable FNV-1a seed and Fisher–Yates permutation. Same five photos; a different daily order. */
export function huntOrder(day) {
  if (!validHuntDay(day)) return [];
  let state = 2166136261;
  for (const c of `photo-hunt:${HUNT_VERSION}:${day}`) state = Math.imul(state ^ c.charCodeAt(0), 16777619) >>> 0;
  const ids = Object.keys(HUNT_PHOTOS);
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

/** `destinations` has already applied the catalogue's ownership rule to shared photographs. */
export function huntRounds(doc, destinations, day) {
  if (!doc?.by_structure || !destinations?.byId || !validHuntDay(day)) return [];
  const base = safeHuntURL(doc.image_store?.base_url);
  if (!base) return [];
  const rounds = [];
  for (const id of huntOrder(day)) {
    const row = destinations.byId('photo', id), p = row?.picture;
    const years = p?.years;
    const thumbnail = p?.held?.t && safeHuntURL(p.held.t, base);
    // A failed catalogue check disables the round set instead of silently replacing evidence.
    if (!row || row.of !== HUNT_PHOTOS[id] || p?.id !== id || p.kind !== 'PHOTO'
      || !creditOf(p) || !thumbnail || new URL(thumbnail).origin !== new URL(base).origin
      || !/^(public domain|no known restrictions)/i.test(p.rights ?? '')
      || !Array.isArray(years) || years.length !== 2
      || !years.every(y => Number.isInteger(y) && y >= 1800 && y <= 1904) || years[0] > years[1]
      || !position(row) || ![row.yaw_deg, row.pitch_deg].every(Number.isFinite)) return [];
    rounds.push({ id, structure: row.of, title: p.title || row.label,
      name: doc.names?.[row.of] || row.label, credit: creditOf(p), holder: p.holder || '',
      rights: p.rights, date: p.date || '', years: yearLabel(p), image: thumbnail,
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

/** One five-photo challenge, under 4 KiB. Answers remain usable in memory if storage refuses. */
export function createHuntSession({ day, rounds, storage = () => globalThis.localStorage } = {}) {
  if (!validHuntDay(day) || rounds?.length !== 5) throw new Error('Invalid photo hunt');
  let cursor = 0, answers = [], issue = null, persisted = false;
  const store = () => typeof storage === 'function' ? storage() : storage;
  try {
    const raw = store()?.getItem(HUNT_STORAGE_KEY);
    if (raw) {
      if (raw.length > 4096) throw new Error('Too large');
      const saved = JSON.parse(raw);
      if (saved?.version !== HUNT_VERSION || !validHuntDay(saved.day) || !Array.isArray(saved.answers)
        || saved.answers.length > 5 || !Number.isInteger(saved.cursor) || saved.cursor < 0
        || saved.cursor > 5 || saved.cursor > saved.answers.length || saved.answers.length > saved.cursor + 1)
        throw new Error('Invalid progress');
      const ids = huntOrder(saved.day);
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
      store().setItem(HUNT_STORAGE_KEY, JSON.stringify({ version: HUNT_VERSION, day, cursor, answers }));
      issue = null; persisted = true;
    } catch { issue = 'unsaved'; }
  }
  return {
    get state() {
      const results = answers.map((answer, i) => answer.skipped ? { score: 0, distance: null } : huntResult(rounds[i], answer));
      return { day, cursor, answers: answers.map(a => ({ ...a })), results,
        score: results.reduce((total, result) => total + result.score, 0), issue, persisted, complete: cursor === 5 };
    },
    guess(at) {
      if (cursor >= 5 || answers[cursor] || !position(at)) return false;
      answers.push({ id: rounds[cursor].id, e: at.e, n: at.n, skipped: false }); save(); return true;
    },
    skip() {
      if (cursor >= 5 || answers[cursor]) return false;
      answers.push({ id: rounds[cursor].id, skipped: true }); save(); return true;
    },
    next() {
      if (cursor >= 5 || !answers[cursor]) return false;
      cursor++; save(); return true;
    },
    reset() { cursor = 0; answers = []; issue = null; save(); },
  };
}

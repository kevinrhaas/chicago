/** T-1258: the visitor's Chicago daybook — keepsakes in five families, ranked from data.
 *  Awards are idempotent per jaunt + keepsake, so replays, Previous/Revise and a duplicate
 *  completion can never inflate a count. No DOM here; jaunt-preview.js draws it. */
export const DAYBOOK_KEY = 'c4d.daybook.v1';
export const DAYBOOK_SCHEMA = 1;
const ENTRY_KEYS = ['key', 'jaunt', 'id', 'family', 'title', 'text'];

export const familyNamed = (book, name) => book.families.find(f => f.name === name || f.id === name) || null;
const familiesOf = (book, entry) => [...new Set([entry.family, entry.secondary_family])]
  .map(name => name && familyNamed(book, name)).filter(Boolean);

/** Distinct keepsakes per family id; a keepsake counts for its family and its jaunt's secondary. */
export function countsFor(book, keepsakes) {
  const counts = Object.fromEntries(book.families.map(f => [f.id, 0]));
  for (const entry of keepsakes) for (const family of familiesOf(book, entry)) counts[family.id] += 1;
  return counts;
}
/** The highest rank whose threshold EVERY family meets — four full families and a thin fifth is not a level. */
export function rankFor(book, keepsakes) {
  const least = Math.min(...Object.values(countsFor(book, keepsakes)));
  return book.ranks.filter(r => r.threshold <= least).at(-1) || book.ranks[0];
}
export function nextRankFor(book, keepsakes) {
  const now = rankFor(book, keepsakes);
  return book.ranks.find(r => r.threshold > now.threshold) || null;
}
/** What a keepsake looks like, from its family's template: a receipt reads as a receipt. */
export function presentKeepsake(book, entry) {
  const family = familyNamed(book, entry.family);
  return { family: family?.name || entry.family, style: family?.template.style || 'note', form: family?.template.form || 'Keepsake',
    lead: family?.template.lead || '', title: entry.title, text: entry.text,
    secondary: entry.secondary_family && entry.secondary_family !== entry.family ? familyNamed(book, entry.secondary_family)?.name || null : null };
}
const validEntry = e => e && typeof e === 'object' && ENTRY_KEYS.every(k => typeof e[k] === 'string' && e[k])
  && (e.secondary_family == null || typeof e.secondary_family === 'string');

export function createJournal({ book, scene = '1835', storage: suppliedStorage } = {}) {
  const key = scene === '1835' ? DAYBOOK_KEY : `${DAYBOOK_KEY}.${scene}`;
  let storage = suppliedStorage, keepsakes = [], notice = null, persistent = true, lastAward = null;
  if (storage === undefined) { try { storage = globalThis.localStorage; } catch { storage = null; } }
  const memoryOnly = () => { persistent = false; notice = 'Saving is unavailable here, so this daybook lasts for this visit only.'; };
  // A damaged save is set aside under its own key rather than destroyed, and the visitor is told.
  const setAside = (raw, why) => {
    notice = why;
    try { storage.setItem(`${key}.damaged`, raw); storage.removeItem(key); } catch { /* the notice still stands */ }
  };
  function load() {
    if (!storage) return memoryOnly();
    let raw;
    try { raw = storage.getItem(key); } catch { return memoryOnly(); }
    if (!raw) return;
    let saved;
    try { saved = JSON.parse(raw); } catch { return setAside(raw, 'Your saved daybook was damaged and could not be read. It has been set aside and a fresh one begun.'); }
    if (!saved || typeof saved !== 'object' || !Array.isArray(saved.keepsakes))
      return setAside(raw, 'Your saved daybook was damaged and could not be read. It has been set aside and a fresh one begun.');
    if (saved.schema_version !== DAYBOOK_SCHEMA)
      return setAside(raw, 'Your saved daybook came from an older version and could not be read. It has been set aside and a fresh one begun.');
    const seen = new Set();
    keepsakes = saved.keepsakes.filter(e => validEntry(e) && familyNamed(book, e.family) && !seen.has(e.key) && seen.add(e.key));
    const dropped = saved.keepsakes.length - keepsakes.length;
    if (dropped) notice = `${dropped} saved keepsake${dropped === 1 ? '' : 's'} could not be read and ${dropped === 1 ? 'was' : 'were'} left out.`;
    if (dropped || saved.content_version !== book.content_version) persist();
  }
  function persist() {
    if (!persistent || !storage) return;
    try { storage.setItem(key, JSON.stringify({ schema_version: DAYBOOK_SCHEMA, content_version: book.content_version, keepsakes })); }
    catch { memoryOnly(); }
  }
  load();
  const snapshot = () => ({ counts: countsFor(book, keepsakes), level: rankFor(book, keepsakes) });
  return {
    key, get keepsakes() { return keepsakes.slice(); }, get notice() { return notice; }, get persistent() { return persistent; },
    get lastAward() { return lastAward; }, book,
    counts: () => countsFor(book, keepsakes), level: () => rankFor(book, keepsakes), nextRank: () => nextRankFor(book, keepsakes),
    has: (jauntId, keepsakeId) => keepsakes.some(e => e.key === `${jauntId}:${keepsakeId}`),
    /** Award on completion only: a fallback or ineligible ending leaves the book untouched. */
    award(jaunt, outcome = { completion_eligible: true }) {
      if (!jaunt?.keepsake || !outcome || outcome.fallback || !outcome.completion_eligible || !familyNamed(book, jaunt.keepsake.family)) return null;
      const entryKey = `${jaunt.id}:${jaunt.keepsake.id}`, before = snapshot();
      const added = !keepsakes.some(e => e.key === entryKey);
      if (added) {
        const { family, id, title, text } = jaunt.keepsake;
        const secondary = jaunt.secondary_family && familyNamed(book, jaunt.secondary_family) && jaunt.secondary_family !== family ? jaunt.secondary_family : null;
        keepsakes = [...keepsakes, { key: entryKey, jaunt: jaunt.id, id, family, title, text, ...(secondary ? { secondary_family: secondary } : {}) }];
        persist();
      }
      const after = snapshot();
      lastAward = { jaunt: jaunt.id, added, entry: keepsakes.find(e => e.key === entryKey), before, after,
        rankChanged: before.level.id !== after.level.id };
      return lastAward;
    },
    reset() {
      keepsakes = []; lastAward = null; notice = persistent ? null : notice;
      if (persistent && storage) { try { storage.removeItem(key); } catch { memoryOnly(); } }
    },
  };
}

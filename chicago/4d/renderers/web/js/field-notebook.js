/** A small notebook kept only in this browser. No account, network, or background capture.
 * Writes either persist completely or return a visible error; existing work is never evicted.
 */
export const NOTEBOOK_KEY = 'chicago4d.notebook.v1';
// A source's title is its full citation: the longest a case cites (Moses and Kirkland, the
// Whistler draught) run to about a thousand characters, so it is kept whole (T-3765).
export const LIMITS = Object.freeze({ entries: 100, photos: 12, chars: 1500000, photoChars: 160000, noteChars: 6000, sourceTitle: 1500 });
const text = (value, max = 2000) => typeof value === 'string' ? value.slice(0, max) : '';
export function safeNotebookURL(value) {
  try { const u = new URL(value); return ['https:', 'http:'].includes(u.protocol) ? u.href : ''; } catch { return ''; }
}
function sourceRows(value) {
  return (Array.isArray(value) ? value : []).slice(0, 40).filter(s => s && typeof s.id === 'string')
    .map(s => ({ id: text(s.id, 200), title: text(s.title || s.id, LIMITS.sourceTitle), url: safeNotebookURL(s.url) }));
}
function entryOf(value, { id, now } = {}) {
  if (!value || !['note', 'person', 'photo'].includes(value.kind)) return null;
  const photo = value.kind === 'photo' && typeof value.photo === 'string'
    && /^data:image\/(jpeg|png);base64,[A-Za-z0-9+/=]+$/.test(value.photo)
    && value.photo.length <= LIMITS.photoChars ? value.photo : '';
  if (value.kind === 'photo' && !photo) return null;
  return {
    id: text(id || value.id, 100), kind: value.kind, title: text(value.title, 200),
    year: ['1812', '1835', '1871', '1904'].includes(String(value.year)) ? String(value.year) : '',
    place: text(value.place, 300), person: text(value.person, 200), grade: text(value.grade, 40),
    text: text(value.text, LIMITS.noteChars), excerpt: text(value.excerpt, 12000),
    sources: sourceRows(value.sources), photo, link: safeNotebookURL(value.link),
    createdAt: text(now || value.createdAt, 40),
    // T-3778: what a written entry is, for the teacher's page: a jaunt's reflection, a Make
    // your case answer, a route answer. Kept only when set, so older entries are unchanged.
    ...(TOPICS.includes(value.topic) ? { topic: value.topic } : {}),
  };
}
export const TOPICS = Object.freeze(['reflection', 'case', 'route']);
/** One stored entry as the notebook would keep it, or null (T-3777: cloud save checks an
 * entry from the account with this before it goes into the browser's copy). */
export const cleanEntry = (value) => entryOf(value);
const local = () => { try { return globalThis.localStorage; } catch { return null; } };
export function createFieldNotebook({ storage = local, now = () => new Date().toISOString(), id = () => globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}` } = {}) {
  const listeners = new Set();
  const store = () => typeof storage === 'function' ? storage() : storage;
  function read() {
    try {
      const s = store();
      if (!s) return { entries: [], error: 'storage' };
      const raw = s.getItem(NOTEBOOK_KEY);
      if (raw == null) return { entries: [], error: null };
      if (raw.length > LIMITS.chars) return { entries: [], error: 'damaged' };
      const data = JSON.parse(raw);
      if (data?.version !== 1 || !Array.isArray(data.entries) || data.entries.length > LIMITS.entries) return { entries: [], error: 'damaged' };
      const entries = data.entries.map(e => entryOf(e));
      if (entries.some(e => !e || !e.id) || new Set(entries.map(e => e.id)).size !== entries.length) return { entries: [], error: 'damaged' };
      return { entries, error: null };
    } catch { return { entries: [], error: 'storage' }; }
  }
  function write(entries) {
    const raw = JSON.stringify({ version: 1, entries });
    if (entries.length > LIMITS.entries || entries.filter(e => e.kind === 'photo').length > LIMITS.photos || raw.length > LIMITS.chars)
      return { ok: false, reason: 'full' };
    try {
      const s = store();
      if (!s) return { ok: false, reason: 'storage' };
      s.setItem(NOTEBOOK_KEY, raw);
    } catch { return { ok: false, reason: 'storage' }; }
    for (const listener of listeners) { try { listener(read()); } catch { /* a view cannot undo a write */ } }
    return { ok: true };
  }
  return {
    read,
    add(value) {
      const state = read();
      if (state.error) return { ok: false, reason: state.error };
      const entry = entryOf(value, { id: id(), now: now() });
      if (!entry || (!entry.title.trim() && !entry.text.trim())) return { ok: false, reason: 'empty' };
      if (entry.kind === 'person' && entry.person) {
        const old = state.entries.find(e => e.kind === 'person' && e.person === entry.person && e.year === entry.year);
        if (old) return { ok: true, duplicate: true, entry: old };
      }
      const result = write([...state.entries, entry]);
      return result.ok ? { ...result, entry } : result;
    },
    update(entryId, note) {
      const state = read();
      if (state.error) return { ok: false, reason: state.error };
      if (!state.entries.some(e => e.id === entryId)) return { ok: false, reason: 'missing' };
      return write(state.entries.map(e => e.id === entryId ? { ...e, text: text(note, LIMITS.noteChars) } : e));
    },
    remove(entryId) {
      const state = read();
      if (state.error) return { ok: false, reason: state.error };
      return write(state.entries.filter(e => e.id !== entryId));
    },
    subscribe(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}
export const fieldNotebook = createFieldNotebook();

/** Store a small JPEG copy; the full stamped PNG is a separate download. */
export async function saveNotebookPhoto(blob, context, { notebook = fieldNotebook, doc = globalThis.document } = {}) {
  let url;
  try {
    url = URL.createObjectURL(blob);
    const img = doc.createElement('img');
    await new Promise((resolve, reject) => { img.onload = resolve; img.onerror = reject; img.src = url; });
    const canvas = doc.createElement('canvas');
    const scale = Math.min(1, 640 / Math.max(img.naturalWidth, img.naturalHeight));
    canvas.width = Math.max(1, Math.round(img.naturalWidth * scale));
    canvas.height = Math.max(1, Math.round(img.naturalHeight * scale));
    canvas.getContext('2d').drawImage(img, 0, 0, canvas.width, canvas.height);
    let photo = canvas.toDataURL('image/jpeg', .7);
    if (photo.length > LIMITS.photoChars) photo = canvas.toDataURL('image/jpeg', .4);
    canvas.width = canvas.height = 1;
    if (photo.length > LIMITS.photoChars) return { ok: false, reason: 'photo' };
    return notebook.add({ ...context, kind: 'photo', photo });
  } catch { return { ok: false, reason: 'photo' }; }
  finally { if (url) URL.revokeObjectURL(url); }
}

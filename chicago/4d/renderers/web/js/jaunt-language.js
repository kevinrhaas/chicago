/**
 * A jaunt in the visitor's language (gap analysis item 15: Spanish). tools/jaunts_es.py compiles
 * each jaunt's Spanish words file (data/jaunts/_es/<id>.txt) into an overlay beside the English,
 * sidecars/<scene>/jaunts/es/<id>.json: the passages, keyed as the words file keys them, each as
 * [mark, text], the mark being the first eight hex of the SHA-1 of the English it was translated
 * from. This puts a passage over the English the jaunt was fetched as only while that English
 * still has its mark. A passage the overlay lacks, or whose English has been corrected since it
 * was translated, stays in English, and a jaunt with no overlay reads wholly in English.
 *
 * Only the words a visitor reads change: the walk, its stops, choices, evidence and sources are
 * the English jaunt's. The evidence under "Sources for this stop" stays as recorded.
 */
import { LANG } from './strings/index.js';
import { originalOf } from './reader-text.js';

/** Shown once on a translated jaunt's preview and first card (the owner's choice, 2026-11-19:
 * quotations are given in the visitor's language, saying so). */
export const QUOTES_NOTE = Object.freeze({
  es: 'Las citas de las fuentes están traducidas del inglés.',
});

const overlays = new Map();

function overlay(base, name, fetcher) {
  const url = new URL(`${LANG}/${name}`, base).href;
  if (!overlays.has(url)) {
    overlays.set(url, Promise.resolve()
      .then(() => fetcher(url, { cache: 'no-cache' }))
      .then((res) => (res?.ok ? res.json() : null))
      .catch(() => null));
  }
  return overlays.get(url);
}

/** Put `passages` ({key: text}) over a jaunt document, in place; returns how many landed. */
export function applyPassages(doc, passages) {
  if (!doc || !passages) return 0;
  const stops = new Map((doc.stops || []).map((s) => [s.id, s]));
  let n = 0;
  for (const [key, text] of Object.entries(passages)) {
    if (typeof text !== 'string' || !text) continue;
    const [kind, a, b] = key.split(' ');
    const stop = a ? stops.get(a) : null;
    let ok = true;
    if (kind === 'title') doc.title = text;
    else if (kind === 'premise') doc.premise = text;
    else if (kind === 'opening' && doc.opening) doc.opening.text = text;
    else if (kind === 'stop' && stop) stop.text = text;
    else if (kind === 'narrative' && stop) stop.narrative = text;
    else if (kind === 'caption' && stop?.stage) stop.stage.caption = text;
    else if ((kind === 'label' || kind === 'consequence') && stop) {
      const choice = (stop.choices || []).find((c) => c.id === b);
      if (choice) choice[kind] = text; else ok = false;
    } else if ((kind === 'leg' || kind === 'note') && doc.legs?.[Number(a)]) doc.legs[Number(a)][kind === 'leg' ? 'story' : 'note'] = text;
    else if (kind === 'ending') {
      const end = (doc.endings || []).find((e) => e.id === a);
      if (end) end.text = text; else ok = false;
    } else if (kind === 'keepsake' && doc.keepsake && (a === 'title' || a === 'text')) doc.keepsake[a] = text;
    else ok = false;
    if (ok) n++;
  }
  return n;
}

/** The English a words-file key names in `doc` (tools/jaunts_es.py `english`), or undefined. */
export function englishOf(doc, key) {
  const [kind, a, b] = key.split(' ');
  const stop = a ? (doc.stops || []).find((s) => s.id === a) : null;
  if (kind === 'title') return doc.title;
  if (kind === 'premise') return doc.premise;
  if (kind === 'opening') return doc.opening?.text;
  if (kind === 'stop') return stop?.text;
  if (kind === 'narrative') return stop?.narrative;
  if (kind === 'caption') return stop?.stage?.caption;
  if (kind === 'label' || kind === 'consequence') return (stop?.choices || []).find((c) => c.id === b)?.[kind];
  if (kind === 'leg') return doc.legs?.[Number(a)]?.story;
  if (kind === 'note') return doc.legs?.[Number(a)]?.note;
  if (kind === 'ending') return (doc.endings || []).find((e) => e.id === a)?.text;
  if (kind === 'keepsake') return doc.keepsake?.[a];
  return undefined;
}

const encoder = new TextEncoder();
/** The first eight hex of the SHA-1 of `text` (tools/jaunts_es.py `mark`). */
export async function markOf(text) {
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-1', encoder.encode(text)));
  return [...digest.slice(0, 4)].map((n) => n.toString(16).padStart(2, '0')).join('');
}

/** {key: text} of the overlay passages ({key: [mark, text]}) whose English in `doc` still has
 * its mark. A reworded passage is matched against the authored English it was reworded from. */
export async function current(doc, passages) {
  const out = {};
  if (!doc || !passages || !globalThis.crypto?.subtle) return out;
  await Promise.all(Object.entries(passages).map(async ([key, entry]) => {
    if (!Array.isArray(entry) || typeof entry[1] !== 'string' || !entry[1]) return;
    const shown = englishOf(doc, key);
    if (typeof shown !== 'string') return;
    if (await markOf(originalOf(shown) ?? shown) === entry[0]) out[key] = entry[1];
  }));
  return out;
}

/** The jaunt `doc` (fetched from `base`, its scene's jaunts/ folder) in the visitor's language. */
export async function localJaunt(doc, base, fetcher = fetch) {
  if (LANG === 'en' || !doc?.id) return doc;
  const o = await overlay(base, `${encodeURIComponent(doc.id)}.json`, fetcher);
  if (!o?.passages) return doc;
  const passages = await current(doc, o.passages);
  const copy = structuredClone(doc);
  if (applyPassages(copy, passages)) {
    copy.lang = LANG;
    copy.quotesNote = QUOTES_NOTE[LANG] || '';
  }
  return copy;
}

/** Catalog rows with their titles and premises in the visitor's language. */
export async function localCatalog(rows, base, fetcher = fetch) {
  if (LANG === 'en' || !Array.isArray(rows)) return rows;
  const o = await overlay(base, 'catalog.json', fetcher);
  const by = o?.jaunts;
  if (!by) return rows;
  return Promise.all(rows.map(async (row) => {
    const own = by[row.id] && await current(row, by[row.id]);
    return own && Object.keys(own).length ? { ...row, ...own } : row;
  }));
}

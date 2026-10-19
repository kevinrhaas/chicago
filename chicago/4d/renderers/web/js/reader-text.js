/**
 * reader-text.js — a record's research prose as a person reads it (T-2825).
 *
 * The owner, 2026-10-18: "You should rewrite the records so you are not referring to
 * internal ticket numbers or internal record ids in researcher or educator mode." Some of
 * the records a person opens are fetched exactly as they are authored — a plant community,
 * a household behind a person's card, a firm's record, a building's sidecar — and their
 * notes are the builders' working record: "(T-1460)", "see fort_dearborn_barracks",
 * "read off data/streets/1835.json". Those files stay as written, because the next builder
 * and two dozen tools read them.
 *
 * So the rewrite is compiled, not computed here. tools/compile_reader_text.py runs the one
 * rule every research surface shares (tools/readable_text.py) over each family of records
 * and writes, to data/reader/<family>.json, the edits that turn each string a reader would
 * be refused into the sentence they get. This module fetches that overlay once and applies
 * it to a record before it is rendered. A string the overlay does not hold is already
 * clean, and is shown as it is. The gate reads the same overlay through readable_text's
 * `reader_copy`, the twin of `readerCopy` below, so what it lints is what is shown.
 *
 * The key is the original string's CRC-32, Adler-32 and UTF-8 length; the edits are
 * `[start, delete, insert]` in this string's own (UTF-16) indices, in order.
 *
 * WITHOUT THE OVERLAY a record is shown as authored, and the failure is reported. A building's
 * card asks for its scene's overlay the first time a card opens and is redrawn when it lands
 * (popup.js `setReader`); every other surface waits for its overlay before it draws.
 */

let CRC_TABLE = null;
function crcTable() {
  if (CRC_TABLE) return CRC_TABLE;
  CRC_TABLE = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
    CRC_TABLE[n] = c >>> 0;
  }
  return CRC_TABLE;
}

const encoder = typeof TextEncoder === 'function' ? new TextEncoder() : null;

/** CRC-32 and Adler-32 of the UTF-8 bytes, then the byte length, all hex —
 *  readable_text.reader_key. Two independent checksums, so a sentence the overlay holds no
 *  edit for cannot pass for one it does, and one record's edits never reach another's text
 *  (tools/compile_reader_text.py also refuses any family where a clean string shares a key). */
export function readerKey(text) {
  const bytes = encoder ? encoder.encode(String(text)) : new Uint8Array(0);
  const table = crcTable();
  let c = 0xFFFFFFFF;
  let a = 1;
  let b = 0;
  for (let i = 0; i < bytes.length; i++) {
    c = table[(c ^ bytes[i]) & 0xFF] ^ (c >>> 8);
    a = (a + bytes[i]) % 65521;
    b = (b + a) % 65521;
  }
  const hex = (n) => (n >>> 0).toString(16).padStart(8, '0');
  return `${hex(c ^ 0xFFFFFFFF)}${hex((b << 16) | a)}:${bytes.length.toString(16)}`;
}

/** The string the edits make of `text`. */
export function applyEdits(text, edits) {
  let out = '';
  let pos = 0;
  for (const [start, del, ins] of edits) {
    out += text.slice(pos, start) + ins;
    pos = start + del;
  }
  return out + text.slice(pos);
}

// Each rewritten sentence, against the one it was written from: a renderer that finds the
// sources a sentence names (residents.js `prose`) reads them off the original, so the
// citations under a block still list every source its sentences named.
const ORIGINAL = new Map();
const ORIGINAL_MAX = 20000;

/** The authored string a rewritten one was said from, or null when it was not rewritten. */
export function originalOf(text) {
  return ORIGINAL.get(text) ?? null;
}

// Two words at least: an id, a grade, a date or a key is one token and never rewritten.
// The same class as readable_text.PROSE, spelt out because the two languages' `\s` differ.
const WS = ' \\t\\n\\r\\f\\v\\u00a0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000\\ufeff';
const PROSE = new RegExp(`[^${WS}][${WS}]+[^${WS}]`);

// A field a card prints as a sentence even when its value is one token (a note that is only
// a file reference, a locator that is only a claim id): readable_text.PROSE_KEYS.
const PROSE_KEYS = new Set(['note', 'locator']);

/** One string as a reader gets it. `key` is the field it sits in, where there is one. */
export function say(text, overlay, key = null) {
  if (typeof text !== 'string' || !overlay?.edits) return text;
  if (!PROSE.test(text) && !(PROSE_KEYS.has(key) && text.trim())) return text;
  const e = overlay.edits[readerKey(text)];
  if (!e) return text;
  const out = applyEdits(text, e);
  if (ORIGINAL.size >= ORIGINAL_MAX) ORIGINAL.clear();
  ORIGINAL.set(out, text);
  return out;
}

/** A copy of `doc` with every string the overlay holds said for a reader. The record
 *  itself is never changed: other views, and the smoke's hash of a sidecar, hold it. */
export function readerCopy(doc, overlay) {
  if (!overlay?.edits) return doc;
  const walk = (v, key) => {
    if (typeof v === 'string') return say(v, overlay, key);
    if (Array.isArray(v)) return v.map((x) => walk(x, key));
    if (v && typeof v === 'object') {
      const out = {};
      for (const k of Object.keys(v)) out[k] = walk(v[k], k);
      return out;
    }
    return v;
  };
  return walk(doc, null);
}

const overlays = new Map();

/**
 * The overlay for one family (`flora`, `fauna`, `residents`, `businesses`,
 * `structures_<scene>`), fetched once per data base. Resolves to null when it cannot be
 * read, and reports why: the records are then shown as authored, which is poorer and
 * never wrong about the evidence.
 */
export function loadReaderText(dataBase, family, problems = null) {
  const key = `${String(dataBase)}|${family}`;
  if (!overlays.has(key)) {
    overlays.set(key, fetch(new URL(`reader/${family}.json`, dataBase), { cache: 'no-cache' })
      .then((res) => {
        if (!res.ok) throw new Error(`reader/${family}.json: ${res.status}`);
        return res.json();
      })
      .catch((err) => {
        overlays.delete(key);
        problems?.push?.(`${err.message} — these records are shown in their builders' words`);
        return null;
      }));
  }
  return overlays.get(key);
}

const ISSUE = /^([a-z]+(?:_[a-z]+)*)_(1[78]\d\d)_(\d\d)_(\d\d)(?:#c\d+)?$/;

/** A record id said as words, for the few places a card prints one bare: the overlay's
 *  own name for it where the data gives one; a newspaper notice as its paper and date
 *  (`chicago_democrat_1834_07_02#c008` → "the Chicago Democrat of 1834-07-02", the rule
 *  readable_text.py `_name` holds); and otherwise its words. Never the id. */
export function nameOf(id, overlay = null) {
  const s = String(id ?? '');
  const hit = overlay?.names?.[s];
  if (hit) return hit;
  const issue = ISSUE.exec(s);
  if (issue) {
    const paper = issue[1].split('_').map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    return `the ${paper} of ${issue[2]}-${issue[3]}-${issue[4]}`;
  }
  return s.replace(/#c\d+$/, '').replace(/^(?:hh|rc|biz|cand)_/, '').replace(/[_:/.]+/g, ' ').trim();
}

/**
 * fallback-summary.js — the opening of a building's card when nobody has written one
 * (T-2636, design doc "Field Navigator Mk II" §12).
 *
 * A notable building gets an AUTHORED front page, data/summaries/<id>.json, gated by
 * tools/compile_summaries.py. Everything else — most of the town — gets this: a summary
 * built from the sidecar by TEMPLATES, never by printing a raw field. The finding it
 * fixes is the owner's phone screenshot of the 1904 Glessner card (IMG_6942), which
 * opened with the address three times and "on parcel prairie_1800
 * (data/street_grid/1904.json)" twice, because the head printed `symbolic_location`
 * whole and the lead was composed around it.
 *
 * THE RULES, and the test (tools/test_fallback_summary.mjs) holds every structure in
 * every scene to them:
 *
 *  - The address is given ONCE, in the head. It is the first short, clean phrase of the
 *    recorded location — "1800 S. Prairie Avenue", "South bank of the main stem" — and
 *    never the whole field: the field carries survey reasoning, parcel ids and file
 *    paths that belong to the Evidence tab, where they still are. Other names (`aka`)
 *    that only restate the address are not repeated.
 *  - The summary is at most three sentences, each from a template filled with words
 *    the card already prints elsewhere: what it is (its use, its material, its
 *    storeys), when it was built or stood as the record dates it (never a bound), and
 *    who lived here or what it is today.
 *    Nothing is paraphrased and no adjective is added.
 *  - Every phrase that goes in is linted first — no id, snake_case word, file path,
 *    link or ticket number, the same refusals compile_summaries.py makes of an authored
 *    record — and a phrase that fails is LEFT OUT, never shown "cleaned". A visitor
 *    loses a clause; they never read plumbing.
 *
 * Pure: no DOM, so the test can run it over every sidecar in node.
 */

import { whenSentence } from './range-words.js';

const SNAKE = /[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+/g;
const PATH = new RegExp(
  '(?:(?<![\\w])(?:\\.{1,2}/|/)?(?:data|tools|docs|assets|renderers|generators|site|'
  + 'tickets|research|chicago|walk|js|css)/\\S*)'
  + '|(?:\\b[\\w.-]+\\.(?:json|jsonl|js|mjs|cjs|ts|py|sh|md|html?|css|glb|gltf|bin|png|'
  + 'jpe?g|webp|gif|svg|csv|tsv|txt|pdf|tiff?|xml|ya?ml)\\b)', 'gi');
const LINK = /\b(?:https?:\/\/|www\.)\S+/gi;
const TICKET = /\b(?:T|NAV|PR)-?#?\d{2,5}\b/g;

/**
 * What in a visitor-facing string a visitor must never see. The JavaScript twin of
 * `lint_string` in tools/compile_summaries.py; the test holds the two to the same cases.
 * @param {string} text
 * @returns {string[]} one entry per problem, empty when the text may be shown
 */
export function visitorTextProblems(text) {
  const t = String(text ?? '');
  const out = [];
  for (const m of t.matchAll(LINK)) out.push(`a link "${m[0]}"`);
  const scrubbed = t.replace(LINK, ' ');
  for (const m of scrubbed.matchAll(PATH)) out.push(`a file path "${m[0]}"`);
  for (const m of scrubbed.matchAll(SNAKE)) out.push(`an id or snake_case word "${m[0]}"`);
  for (const m of scrubbed.matchAll(TICKET)) out.push(`a ticket number "${m[0]}"`);
  return out;
}

/** The phrase if it may be shown, else ''. */
export function clean(text) {
  const t = String(text ?? '').trim();
  return t && !visitorTextProblems(t).length ? t : '';
}

const words = (t) => String(t).split(/\s+/).filter((w) => /[A-Za-z0-9]/.test(w));

/**
 * The address line: the first phrase of the recorded location that is short, says
 * something in words, and is clean. The location is cut at its first colon,
 * semicolon, comma, bracket or dash, and each piece is tried in order, so
 * "1800 S. Prairie Avenue: the south-west corner …, on parcel prairie_1800 (…)" gives
 * "1800 S. Prairie Avenue", and "Anonymous reconstructed roof in … cluster
 * wolcott_kinzie_core; between the north bank and Michigan Street" gives
 * "Between the north bank and Michigan Street". A lot address a source printed
 * (`lot_address`) comes first when the record has one. No clean piece, no line.
 * @param {object} sidecar
 * @returns {string}
 */
export function fallbackAddress(sidecar) {
  const lot = sidecar?.attributes?.lot_address?.value;
  if (typeof lot === 'string' && clean(lot) && words(lot).length <= 12) return lot.trim();
  const where = sidecar?.placement?.symbolic_location;
  if (typeof where !== 'string') return '';
  for (const raw of where.split(/[;:,()[\]]|\s[—–-]\s/)) {
    const piece = raw.trim().replace(/[.\s]+$/, '');
    if (!piece || !clean(piece)) continue;
    if (/^(anonymous|reconstructed|parcel|lot)\b/i.test(piece)) continue;
    const w = words(piece);
    if (w.length > 12 || w.filter((x) => /[A-Za-z]{2,}/.test(x)).length < 2) continue;
    return piece.charAt(0).toUpperCase() + piece.slice(1);
  }
  return '';
}

/** Lower-case, no punctuation, no compass letters — so "1800 Prairie Avenue" and
 *  "1800 S. Prairie Avenue" are one address. */
function addressKey(t) {
  return String(t).toLowerCase().replace(/[.,]/g, ' ')
    .replace(/\b(?:s|south|n|north|e|east|w|west)\b/g, ' ')
    .replace(/\s+/g, ' ').trim();
}

/**
 * The other names the head may print: clean ones that do not restate the address.
 * @param {object} sidecar
 * @param {string} address  what fallbackAddress gave
 * @returns {string[]}
 */
export function otherNames(sidecar, address = '') {
  const aka = Array.isArray(sidecar?.aka) ? sidecar.aka : [];
  const key = address ? addressKey(address) : '';
  const seen = new Set();
  const out = [];
  for (const a of aka) {
    const t = clean(a);
    if (!t) continue;
    const k = addressKey(t);
    if ((key && k === key) || seen.has(k)) continue;
    seen.add(k);
    out.push(t);
  }
  return out;
}

/**
 * The title the card prints. The record's name, less what a visitor must not read: a
 * bracketed aside carrying an id or a ticket number ("(district draft; refined by
 * T-1894)") is dropped whole, and a name that opens with the address the head already
 * gives ("1823 Prairie Avenue — Dent masonry mansion") loses that prefix, so the address
 * is printed once. A name that IS the address, or already contains it ("The trading camp
 * at Wolf Point"), keeps it, and the head prints no second address line (`addressInTitle`).
 * @param {string} title    what display-name.js calls it
 * @param {string} address  what fallbackAddress gave
 * @returns {{ title: string, addressInTitle: boolean }}
 */
export function cardTitle(title, address = '') {
  let t = String(title ?? '').replace(/\s*\(([^()]*)\)/g, (m, inner) => (clean(inner) ? m : '')).trim();
  if (!clean(t)) t = t.split(/\s[—–]\s/).filter((part) => clean(part)).join(' — ');
  let addressInTitle = false;
  if (address && t) {
    const parts = t.split(/\s[—–]\s/);
    if (parts.length > 1 && addressKey(parts[0]) === addressKey(address)) {
      const rest = parts.slice(1).join(' — ');
      t = rest.charAt(0).toUpperCase() + rest.slice(1);
    } else if (addressKey(t) === addressKey(address) || t.toLowerCase().includes(address.toLowerCase())) {
      // "The trading camp at Wolf Point" already says where it is.
      addressInTitle = true;
    }
  }
  if (!t) { t = address || 'A building'; addressInTitle = !!address; }
  return { title: t, addressInTitle };
}

/** A material as an adjective, before the building's noun. */
const MATERIAL = {
  balloon_frame: 'balloon-frame', braced_frame: 'braced-frame', light_frame: 'light-frame',
  frame: 'frame', log: 'log', plank: 'plank', brick: 'brick', stone: 'stone', earth: 'earth',
  split_rail: 'split-rail', timber_crib: 'timber-crib',
  brick_with_stone_front: 'stone-fronted brick', stone_with_brick_rear: 'stone',
};

const NUMBER = ['', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];

function storeys(value) {
  return Number.isInteger(value) && value >= 1 && value < NUMBER.length
    ? `${NUMBER[value]}-storey` : '';
}

const article = (w) => (/^(?:one\b|one-|uni|eu)/i.test(w) ? 'a' : /^[aeiou]/i.test(w) ? 'an' : 'a');

/**
 * The templated summary, at most three sentences.
 *
 * @param {object} sidecar  the compiled record
 * @param {object} opts
 * @param {string} [opts.kind]  its use in words, as the card's kind line prints it
 * @param {string} [opts.today] its present status in words, where the record has one
 * @returns {{ text: string, sentences: string[] }}
 */
export function fallbackSummary(sidecar, { kind = '', today = '' } = {}) {
  const attrs = sidecar?.attributes ?? {};
  const noun = clean(kind);
  const material = MATERIAL[attrs.construction?.value] ?? '';
  const tall = storeys(attrs.stories?.value);
  const sentences = [];

  // 1. What it is: its storeys, its material and its use, in that order. The title is
  // printed just above, so the sentence does not repeat it (or the address it may hold).
  const mat = material && !(noun && noun.toLowerCase().includes(material)) ? material : '';
  const what = [tall, mat, noun || ((tall || mat) ? 'building' : '')].filter(Boolean).join(' ');
  sentences.push(what ? `It was ${article(what)} ${what}.` : 'It stood here.');

  // 2. When it stood, and only what the record dates (T-3037, range-words.js): its build
  // date as the sources give it, a phase start a source dates, or a first sighting. The
  // range's start alone is usually a bound — 1736 Prairie's is the 1904 scene's own day,
  // under a picture of the house drawn in 1893 — so an unmarked start says nothing.
  const when = whenSentence(sidecar);
  if (when) sentences.push(when);

  // 3. Who lived here, as the record's first household says it, or else what it is today.
  const h = Array.isArray(sidecar?.residents) ? sidecar.residents[0] : null;
  const who = h?.name && h?.relation
    ? clean(`${String(h.name).trim()} ${String(h.relation).trim().replace(/\.$/, '')}.`) : '';
  const now = clean(today);
  if (who) sentences.push(who);
  else if (now) sentences.push(`Today: ${now.charAt(0).toLowerCase()}${now.slice(1).replace(/\.$/, '')}.`);

  const kept = sentences.filter((s) => clean(s)).slice(0, 3);
  return { text: kept.join(' '), sentences: kept };
}

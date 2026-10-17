/**
 * T-2624 — the locked and renamed terms of design doc section 03, "Audience, voice and
 * terms". The locked terms stay exactly as written across the product, each with its one
 * plain line (shown on a first-appearance tap and in the Guide glossary, T-2662). The
 * retired words never reach a visitor; tools/check_strings.mjs refuses them in every
 * section of the table, and refuses a locked term spelled any other way.
 */
import { register } from './index.js';

/** Section 03's order, with the Guide glossary's plain lines (data/guide/glossary.json,
 * T-2662). The gate holds this list equal to tools/check_guide.py LOCKED and these lines
 * equal to the glossary's whenever both are in the tree. */
export const LOCKED_TERMS = [
  ['Attested', 'A source says so, and we name it.'],
  ['Inferred', 'Worked out from clues about this exact thing.'],
  ['Reconstructed', 'No record exists. We built it so the street makes sense, and say so.'],
  ['Confidence view', 'Recolor the world by grade, or hide a grade completely.'],
  ['Liberties', 'Our list of the choices we made without a source, and why.'],
  ['Sources', 'Where our facts come from: books, maps, photos, newspapers and more, each one named.'],
  ['Jaunts', 'Short guided walks through the town, stop by stop.'],
];

/** Retired words (tools/check_guide.py RETIRED, T-2662): a lower-case one is refused in
 * any case, a capitalised one as written. "Sources" retires both Evidence and Citations. */
export const RETIRED_TERMS = ['documented', 'conjectural', 'Evidence', 'Citations'];

/** Section 03's renames: the old word a visitor must no longer read, and its new one. */
export const RENAMED_TERMS = [
  ['Coordinate', 'Destination'],
  ['Starting at…', 'Go to'],
  ['Pick a place', 'Go to'],
  ['Explore by myself', 'Free roam'],
  ['Travel', 'Move'],
  ['Controls', 'Guide'],
  ['Help', 'Guide'],
  ['Firms', 'Shops & work'],
  ['Modeled phase', 'Stood here'],
  ['Present status', 'Today'],
  ['STRUCT', 'BUILDINGS'],
  ['SYNC', 'PEOPLE'],
  ['Not recorded', 'Unknown'],
];

const slug = term => term.toLowerCase().replace(/\s+/g, '-');
export default register('terms', Object.fromEntries(LOCKED_TERMS.flatMap(([term, meaning]) => [
  [slug(term), term], [`${slug(term)}.meaning`, meaning],
])));

/** The plain line for a grade value as the data spells it (attested, inferred, reconstructed). */
export function gradeTerm(grade) {
  const row = LOCKED_TERMS.find(([term]) => term.toLowerCase() === String(grade || '').toLowerCase());
  return row ? { label: row[0], meaning: row[1] } : { label: '', meaning: '' };
}

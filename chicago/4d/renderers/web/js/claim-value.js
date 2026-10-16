/**
 * claim-value.js — an attribute's value, as a visitor reads it on the card (T-2609).
 *
 * A record's attribute holds whatever its generator needs: a word, a number, a
 * yes/no, a short list of numbers — and, on 151 structures, a structured value: a
 * plan's parts, an elevation's datums, a bay's outline as a list of points
 * (`glessner_house` `bay_dining`). The card printed every one through `String()`,
 * so the 1904 Glessner card read "bay dining [object Object]" under Attributes, a
 * HIGH finding of the Navigator Mk II design review.
 *
 * A structured value is geometry for a generator, not a sentence, and none of it
 * reads as one: ids, seeds and coordinate pairs are not something a visitor can
 * check against anything. So it prints NOTHING — `null`, which the card's claim
 * row renders as no value cell — while the row keeps its chip, its sources and its
 * `why`, because how sure we are and where it came from is still true and still
 * the point. The note under `why` is where a structured claim is put in words.
 *
 * Pure, with no imports, so tools/test_claim_value.mjs reads it in the gate.
 */

function scalarText(v) {
  if (v === true) return 'yes';
  if (v === false) return 'no';
  if (v === null || v === undefined) return '—';
  if (typeof v === 'number') return String(v);
  return String(v).replace(/_/g, ' ');
}

function isScalar(v) {
  return v === null || typeof v !== 'object';
}

/**
 * @param {*} v  an attribute's `value`
 * @returns {string|null}  the text for the value cell, or null for a value that
 *   has no printable form (an object, or a list holding one)
 */
export function claimValueText(v) {
  if (Array.isArray(v)) {
    if (!v.every(isScalar)) return null;
    return v.length ? v.map(scalarText).join(', ') : 'none';
  }
  if (!isScalar(v)) return null;
  return scalarText(v);
}

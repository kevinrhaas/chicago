/**
 * range-words.js — what a card may say about WHEN a building stood (T-3037).
 *
 * A phase's `documented_range` is the span the record claims, and most of its ends are
 * BOUNDS the record chose, not dates anybody wrote down: 195 of the 209 Prairie Avenue
 * houses of 1904 open on the scene's own day, because the record claims the 1904 target
 * and no more, and 572 roofs of 1835 open on 1 January 1835 for the same reason. The card
 * printed the start as "It had stood like this since 1904", and the owner found it under
 * a picture of the same house drawn in 1893 (1736 Prairie, 2026-10-22).
 *
 * So a card prints a date only where the record says what the date IS:
 *
 *  - the structure's `built` attribute, its build date as the sources give it — a year,
 *    "about 1834", "by 1886", "between 1870 and 1876", or "1864 or 1875" where they
 *    disagree — printed "Built in 1886.";
 *  - a range end the record marks: `from_is` 'began' (a source dates this phase's start)
 *    or 'seen' (the first date a source shows it standing; it may be older), and `to_is`
 *    'ended' or 'seen' (the last date a source shows it).
 *
 * An unmarked end is a bound and is never printed as a date. Pure: no DOM, so the test
 * (tools/test_fallback_summary.mjs) runs it over every sidecar in node.
 */

const YEAR = /^(\d{4})-\d{2}-\d{2}$/;
const FORMS = /^(?:(?:about|by) \d{4}|between \d{4} and \d{4}|\d{4} or \d{4})$/;

/** A `built` value as the words after "Built": "in 1886", "about 1834", "in 1864 or 1875",
 *  "between 1870 and 1876"; '' for a value in no form the card reads (tools/validate.py
 *  refuses those). */
export function builtPhrase(value) {
  if (Number.isInteger(value)) return `in ${value}`;
  const v = String(value ?? '').trim();
  if (!FORMS.test(v)) return '';
  return /^\d/.test(v) ? `in ${v}` : v;
}

/** The structure's build date as a sentence, "Built in 1886.", or ''. */
export function builtSentence(sidecar) {
  const phrase = builtPhrase(sidecar?.attributes?.built?.value);
  return phrase ? `Built ${phrase}.` : '';
}

/** Each end of a range as the card may state it: { from: {year, is}|null, to: {…}|null }. */
export function rangeEnds(range) {
  const end = (date, is, kinds) => {
    const y = YEAR.exec(String(date ?? ''))?.[1];
    return y && kinds.includes(is) ? { year: y, is } : null;
  };
  return {
    from: end(range?.from, range?.from_is, ['began', 'seen']),
    to: end(range?.to, range?.to_is, ['ended', 'seen']),
  };
}

/**
 * The span in words, from the marked ends only: "1887 – 1946" where both are dated
 * events, "by 1890, still in 1911", "from 1833", "until 1856"; '' where neither
 * end is marked, which a caller says as "not recorded" rather than inventing a span.
 * @param {object} range  a sidecar's `documented_range`
 * @returns {string}
 */
export function rangeWords(range) {
  const { from, to } = rangeEnds(range);
  if (from?.is === 'began' && to?.is === 'ended') {
    return from.year === to.year ? from.year : `${from.year} – ${to.year}`;
  }
  const start = from ? (from.is === 'began' ? `from ${from.year}` : `by ${from.year}`) : '';
  const stop = to ? (to.is === 'seen' ? `still in ${to.year}` : `until ${to.year}`) : '';
  return [start, stop].filter(Boolean).join(', ');
}

/**
 * The summary's sentence on when it stood: the build date where the record has one
 * ("Built in 1864 or 1875."), with the phase's own dated start where that is later
 * ("Built in 1831, and like this since 1833."); else a dated start ("It had stood like
 * this since 1833.") or a first sighting ("Recorded here by 1830."); else ''.
 * @param {object} sidecar
 * @returns {string}
 */
export function whenSentence(sidecar) {
  const scene = Number(/^\d{4}/.exec(String(sidecar?.target_date ?? sidecar?.scene ?? ''))?.[0] ?? NaN);
  const phrase = builtPhrase(sidecar?.attributes?.built?.value);
  // A build date after the visit is a fault in the record, not a sentence (validate.py).
  const built = phrase && !(Math.min(...(phrase.match(/\d{4}/g) ?? []).map(Number)) > scene) ? phrase : '';
  const { from } = rangeEnds(sidecar?.documented_range);
  if (built) {
    const builtYears = (built.match(/\d{4}/g) ?? []).map(Number);
    const later = from?.is === 'began' && builtYears.length && Number(from.year) > Math.max(...builtYears);
    return later ? `Built ${built}, and like this since ${from.year}.` : `Built ${built}.`;
  }
  if (from?.is === 'began') return `It had stood like this since ${from.year}.`;
  if (from?.is === 'seen') return `Recorded here by ${from.year}.`;
  return '';
}

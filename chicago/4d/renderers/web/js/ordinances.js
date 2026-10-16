/**
 * ordinances.js — the town's own law, where a visitor stands in it.
 *
 * One ordinance so far, and it is the only DOCUMENTED statement this project
 * holds about where the built-up town ended in the scene year. Section 22 of the
 * by-laws the Trustees passed on 5 August 1835 forbids stacking hay inside a
 * boundary the ordinance walks street by street — Washington, Canal, Kinzie,
 * Wolcott, Illinois, and then Lake Michigan — under twenty-five dollars a stack,
 * the heaviest penalty in the whole ordinance except gaming. It is a fire rule,
 * and that is what makes it evidence: the Trustees fenced the ground they thought
 * was built up closely enough that a hay stack inside it would take the town.
 *
 * NOTHING IS DRAWN. A legal limit is not a fence, and putting a visible line
 * through the town where nobody in 1835 could see one would be an invention. The
 * limit reaches a visitor on the CARD instead: pick any building and it says
 * whether the Trustees' line ran round it or left it out, and quotes the section
 * that decides.
 *
 * The ring is derived, never authored: `tools/derive_hay_limits.py` builds it out
 * of committed street centrelines, the committed reservation ring and the traced
 * 1834 shore, and `tools/check.sh` re-derives it on every commit. This module
 * only reads the file and answers the one question the card asks of it.
 */

/**
 * Crossing-number test — the same rule the derivation applies, so the card and
 * the dataset cannot disagree about a building.
 *
 * @param {number} e  local ENU easting, metres
 * @param {number} n  local ENU northing, metres
 * @param {number[][]} ring  closed ring, local ENU metres
 */
export function ringContains(e, n, ring) {
  let inside = false;
  for (let i = 0; i < ring.length; i += 1) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[(i - 1 + ring.length) % ring.length];
    if ((y1 > n) !== (y2 > n) && e < ((x2 - x1) * (n - y1)) / (y2 - y1) + x1) inside = !inside;
  }
  return inside;
}

/** The derived limits, and the scene year they were derived for (T-2609). */
export const HAY_LIMITS = { path: 'reconstruction/1835_hay_limits.json', year: '1835' };

/** The year of an ISO date or a scene id: '1904-07-01' and '1904' are both 1904. */
function yearOf(date) {
  const m = /^(\d{4})/.exec(String(date ?? ''));
  return m ? m[1] : null;
}

/**
 * Whether a law derived for `lawDate` belongs on the cards of a scene dated
 * `sceneDate` (T-2609). A town's law is a fact about its own year: the 1835 hay
 * limit printed on a 1904 Prairie Avenue house — what the Navigator Mk II review
 * found — tells a visitor something about that house that was never true of it.
 * Same year, or nothing; an undated scene is not this law's scene either.
 */
export function lawServesScene(lawDate, sceneDate) {
  const law = yearOf(lawDate);
  return law !== null && law === yearOf(sceneDate);
}

/**
 * Load the derived limits.
 *
 * Degrades the way every other layer here degrades: a failure pushes a problem
 * and returns null, and null means "not loaded", which the card treats as a
 * reason to say nothing rather than as a reason to say a building was outside.
 *
 * Another scene's year is null too, and not a problem: the file is not fetched,
 * because nothing is wrong — the law is simply not this scene's (T-2609). The
 * file's own `target_date` is checked again once it is read, so a re-derivation
 * for another date cannot reach the wrong scene through the path's name.
 *
 * @param {object} o
 * @param {URL} o.dataBase        where data/ lives
 * @param {string} o.sceneDate    the scene's `target_date` (or its year)
 * @param {string[]} [o.problems] the shared collector
 * @returns {Promise<object|null>}
 */
export async function loadOrdinanceLimits({ dataBase, sceneDate, problems = [] }) {
  if (!lawServesScene(HAY_LIMITS.year, sceneDate)) return null;
  try {
    const url = new URL(HAY_LIMITS.path, dataBase);
    const res = await fetch(url, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    const doc = await res.json();
    if (!lawServesScene(doc?.target_date, sceneDate)) return null;
    const ring = doc?.ring_local_enu_m;
    if (!Array.isArray(ring) || ring.length < 4) {
      throw new Error('no ring in the derived limits');
    }
    return {
      id: doc.id,
      ordinance: doc.ordinance ?? {},
      ring,
      areaAcres: doc.area_acres,
      /** @returns {boolean|null} null when the building has no committed position */
      coversPlacement(placement) {
        const e = placement?.local_e;
        const n = placement?.local_n;
        if (typeof e !== 'number' || typeof n !== 'number') return null;
        return ringContains(e, n, ring);
      },
    };
  } catch (err) {
    problems.push(`ordinances: ${err.message} — the hay-stacking limit is not shown on cards`);
    return null;
  }
}

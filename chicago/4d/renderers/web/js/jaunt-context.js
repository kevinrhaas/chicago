import { displayName } from './display-name.js';

/** Shortest distance between segments a→b and c→d, in the plane. */
function segmentGap(a, b, c, d) {
  const point = (p, s, e) => {
    const de = e[0] - s[0], dn = e[1] - s[1], length2 = de * de + dn * dn;
    const t = length2 ? Math.max(0, Math.min(1, ((p[0] - s[0]) * de + (p[1] - s[1]) * dn) / length2)) : 0;
    return Math.hypot(p[0] - s[0] - t * de, p[1] - s[1] - t * dn);
  };
  const cross = (o, p, q) => (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0]);
  if (cross(a, b, c) * cross(a, b, d) < 0 && cross(c, d, a) * cross(c, d, b) < 0) return 0;
  return Math.min(point(a, c, d), point(b, c, d), point(c, a, b), point(d, a, b));
}

/**
 * Geometry is an observation of this reconstruction, never a historical citation.
 *
 * T-2946: a place is passed when the route comes within `distance` metres of its WALLS
 * (`outline`, the footprint in local E/N), and its side is read from its centre (`point`).
 * It used to be measured to the spot a ride stops at to frame the building, which can sit
 * across the street or out in the road: walking south past Glessner on its own side of
 * Prairie read "on your left", and coach houses on the alley were "passed" from the
 * sidewalk. A place with no outline is measured to its centre. `minor` places (coach
 * houses, sheds, privies) are not road notes.
 */
export function passingPlaces(points, places, { exclude = [], distance = 20 } = {}) {
  const omitted = new Set(exclude), found = [];
  for (const place of places) {
    if (omitted.has(place.id) || !place.point || place.minor) continue;
    const outline = place.outline?.length >= 3 ? place.outline : [[place.point.e, place.point.n]];
    const centre = [place.point.e, place.point.n];
    let best = null, arc = 0;
    for (let i = 1; i < points.length; i++) {
      const a = points[i - 1], b = points[i], de = b[0] - a[0], dn = b[1] - a[1];
      const length = Math.hypot(de, dn);
      if (!length) continue;
      let gap = Infinity;
      for (let k = 0; k < outline.length; k++) {
        gap = Math.min(gap, outline.length === 1 ? segmentGap(a, b, outline[0], outline[0])
          : segmentGap(a, b, outline[k], outline[(k + 1) % outline.length]));
      }
      const pe = centre[0] - a[0], pn = centre[1] - a[1];
      const t = Math.max(0, Math.min(1, (pe * de + pn * dn) / (length * length)));
      const cross = (de * pn - dn * pe) / length;
      if (!best || gap < best.distance) best = { distance: gap, along: arc + t * length,
        side: Math.abs(cross) < 0.5 ? 'along the route' : cross > 0 ? 'on your left' : 'on your right' };
      arc += length;
    }
    if (best && best.distance <= distance) found.push({ id: place.id, label: place.label, ...best });
  }
  return found.sort((a, b) => a.along - b.along || a.id.localeCompare(b.id));
}

/** Out-buildings a walker sees past the house in front of them; never a road note. */
const MINOR_FUNCTIONS = new Set(['barn_or_carriage_shed', 'outbuilding', 'stable', 'privy', 'woodshed_or_storage_shed',
  'small_utility_building', 'tavern_stable']);
const MINOR_ARCHETYPES = new Set(['outbuilding', 'k12_coach_house', 'k13_conservatories']);
export function minorPlace(sidecar) {
  const fn = sidecar?.attributes?.function;
  return MINOR_ARCHETYPES.has(sidecar?.archetype) || MINOR_FUNCTIONS.has(fn?.value ?? fn);
}

/**
 * T-2946: what a jaunt calls a building, the same in its stop headings and its road notes:
 * the jaunt's own `places` name where its scene has one ("Marshall Field House, 1905
 * Prairie", written by compile_jaunts.py from data/jaunts/_names/place-names.json), and the card's
 * title otherwise, never the record's production name.
 */
export function placeName(jaunt, id, sidecar, fallback) {
  return jaunt?.places?.[id] || (sidecar ? displayName(sidecar, id).title : '') || fallback || id;
}

export function legContext(jaunt, fromId, toId, points, places, exclude = []) {
  const fromIndex = jaunt.stops.findIndex(s => s.id === fromId);
  const authored = (jaunt.legs || []).find((leg, i) =>
    (leg.from ?? jaunt.stops[i]?.id) === fromId && (leg.to ?? jaunt.stops[i + 1]?.id) === toId);
  const passed = passingPlaces(points, places, { exclude });
  const claims = authored?.evidence || [];
  const lines = authored?.note ? [{ text: authored.note, evidence: claims }] : passed.slice(0, authored?.story ? 1 : 2)
    .map(p => ({ text: `Passing ${p.label}, ${p.side}.`, generated: true, place: p.id }));
  if (authored?.story) lines.push({ text: authored.story, evidence: authored.story_evidence || [] });
  return { from: fromId, to: toId, lines, passed, authored: !!authored, fromIndex };
}

/** Also enforce the content contract when an old/corrupt cached payload bypasses compilation. */
export function claimPresentation(claim) {
  if (!claim || !['attested', 'inferred', 'reconstructed'].includes(claim.confidence))
    return { label: '[?]', text: 'Sources unavailable.', narrative: false };
  if (claim.confidence === 'reconstructed' && (claim.speaker || claim.quote || claim.attribution))
    return { label: '[?]', text: 'Unverified attribution withheld.', narrative: true };
  return { label: { attested: '[DOC]', inferred: '[INF]', reconstructed: '[CONJ]' }[claim.confidence],
    text: claim.text, narrative: claim.confidence === 'reconstructed' };
}

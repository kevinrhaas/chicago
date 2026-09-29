/** Geometry is an observation of this reconstruction, never a historical citation. */
export function passingPlaces(points, places, { exclude = [], distance = 25 } = {}) {
  const omitted = new Set(exclude), found = [];
  for (const place of places) {
    if (omitted.has(place.id) || !place.point) continue;
    let best = null, arc = 0;
    for (let i = 1; i < points.length; i++) {
      const [e, n] = points[i - 1], de = points[i][0] - e, dn = points[i][1] - n;
      const length = Math.hypot(de, dn);
      if (!length) continue;
      const pe = place.point.e - e, pn = place.point.n - n;
      const t = Math.max(0, Math.min(1, (pe * de + pn * dn) / (length * length)));
      const gap = Math.hypot(pe - t * de, pn - t * dn), cross = de * pn - dn * pe;
      if (!best || gap < best.distance) best = { distance: gap, along: arc + t * length,
        side: Math.abs(cross / length) < 0.5 ? 'along the route' : cross > 0 ? 'on your left' : 'on your right' };
      arc += length;
    }
    if (best && best.distance <= distance) found.push({ id: place.id, label: place.label, ...best });
  }
  return found.sort((a, b) => a.along - b.along || a.id.localeCompare(b.id));
}

export function legContext(jaunt, fromId, toId, points, places, exclude = []) {
  const fromIndex = jaunt.stops.findIndex(s => s.id === fromId);
  const authored = (jaunt.legs || []).find((leg, i) =>
    (leg.from ?? jaunt.stops[i]?.id) === fromId && (leg.to ?? jaunt.stops[i + 1]?.id) === toId);
  const passed = passingPlaces(points, places, { exclude });
  const claims = authored?.evidence || [];
  const lines = authored?.note ? [{ text: authored.note, evidence: claims }] : passed.slice(0, authored?.story ? 1 : 2)
    .map(p => ({ text: `Passing ${p.label} ${p.side}.`, generated: true, place: p.id }));
  if (authored?.story) lines.push({ text: authored.story, evidence: authored.story_evidence || [] });
  return { from: fromId, to: toId, lines, passed, authored: !!authored, fromIndex };
}

/** Also enforce the content contract when an old/corrupt cached payload bypasses compilation. */
export function claimPresentation(claim) {
  if (!claim || !['attested', 'inferred', 'reconstructed'].includes(claim.confidence))
    return { label: '[?]', text: 'Evidence unavailable.', narrative: false };
  if (claim.confidence === 'reconstructed' && (claim.speaker || claim.quote || claim.attribution))
    return { label: '[?]', text: 'Unverified attribution withheld.', narrative: true };
  return { label: { attested: '[DOC]', inferred: '[INF]', reconstructed: '[CONJ]' }[claim.confidence],
    text: claim.text, narrative: claim.confidence === 'reconstructed' };
}

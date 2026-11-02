/** Numeric span floors, shared by walking, routing, anchors and human roots.
 * Scalar-only decks retain the previous descriptor and height exactly. */
const EPS = 1e-8;
const finite = Number.isFinite;

export function insideDeck(e, n, pts) {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [x, y] = pts[i], [a, b] = pts[j];
    if ((y > n) !== (b > n) && e < (a - x) * (n - y) / (b - y) + x) hit = !hit;
  }
  return hit;
}

/** Version1 is a bounded closed rise, not arbitrary terrain or an operating leaf. */
export function validateSpanProfile(profile, base, poly = null) {
  const fail = () => { throw new Error('Invalid declared walk-surface span profile'); };
  if (!profile || Object.keys(profile).some(k => !['version', 'axis', 'stations_m'].includes(k))
      || profile.version !== 1 || profile.axis !== 'local_x' || !finite(base)
      || !Array.isArray(profile.stations_m) || profile.stations_m.length < 2) fail();
  const stations = profile.stations_m;
  let last = -Infinity;
  for (const point of stations) {
    if (!Array.isArray(point) || point.length !== 2 || !point.every(finite)
        || point[0] <= last || point[1] < base - EPS || point[1] > base + 3 + EPS) fail();
    last = point[0];
  }
  if (Math.abs(stations[0][0]) > EPS || !(last > 0)
      || Math.abs(stations[0][1] - base) > EPS || Math.abs(stations.at(-1)[1] - base) > EPS) fail();
  if (poly && (!Array.isArray(poly) || poly.length < 3
      || poly.some(vertex => !Array.isArray(vertex) || vertex.length !== 2 || !vertex.every(finite))
      || Math.abs(Math.min(...poly.map(vertex => vertex[0]))) > EPS
      || Math.abs(Math.max(...poly.map(vertex => vertex[0])) - last) > EPS)) fail();
  return profile;
}

export function deckFromSidecar(id, sidecar) {
  const p = sidecar?.placement ?? {}, h = p.walk_surface_m;
  const declared = p.walk_surface_profile != null;
  if (declared && (!finite(h) || p.vertical_anchor !== 'water')) {
    throw new Error('Invalid declared profile: finite water-anchored floor required');
  }
  if (typeof h !== 'number' || p.vertical_anchor !== 'water') return null;
  const raw = sidecar.footprint;
  const poly = Array.isArray(raw) ? raw : raw?.polygon;
  if (!Array.isArray(poly) || poly.length < 3) {
    if (declared) throw new Error('Invalid declared profile footprint');
    return null;
  }
  if (declared) validateSpanProfile(p.walk_surface_profile, h, poly);
  const th = (p.rotation_deg ?? 0) * (Math.PI / 180);
  const cos = Math.cos(th), sin = Math.sin(th);
  const e0 = p.local_e ?? 0, n0 = p.local_n ?? 0;
  const deck = { id, y: h, pts: poly.map(([u, v]) => [e0 + u * cos + v * sin, n0 - u * sin + v * cos]) };
  if (declared) {
    if (![e0, n0, th].every(finite) || !deck.pts.every(point => point.every(finite))) {
      throw new Error('Invalid profile coordinate frame');
    }
    deck.profile = p.walk_surface_profile;
    deck.profileFrame = { e0, n0, cos, sin };
  }
  return deck;
}

/** Nominal plank top; callers retain polygon, highest-deck and ground policy.
 * Bridges8mm board gaps and omits55mm proud thresholds; not a mesh/IK raycast. */
export function deckHeightAt(deck, e, n) {
  if (!deck.profile) return deck.y;
  validateSpanProfile(deck.profile, deck.y);
  const f = deck.profileFrame;
  if (!f || ![e, n, f.e0, f.n0, f.cos, f.sin].every(finite)
      || Math.abs(f.cos * f.cos + f.sin * f.sin - 1) > EPS) {
    throw new Error('Invalid profile sample frame');
  }
  const x = (e - f.e0) * f.cos - (n - f.n0) * f.sin;
  const s = deck.profile.stations_m;
  if (x < -EPS || x > s.at(-1)[0] + EPS) return null;
  const u = Math.max(0, Math.min(s.at(-1)[0], x));
  for (let i = 1; i < s.length; i++) {
    if (u <= s[i][0]) {
      const [a, z] = s[i - 1], [b, w] = s[i];
      return z + (w - z) * ((u - a) / (b - a));
    }
  }
  return s.at(-1)[1];
}

/** Existing human root sampler; unrelated ground and all scalar decks unchanged. */
export function profiledGroundHeight(terrain, decks, e, n) {
  if (!decks.some(d => d.profile && insideDeck(e, n, d.pts))) return terrain.surfaceHeight(e, n);
  let height = null;
  for (const d of decks) {
    if (!insideDeck(e, n, d.pts)) continue;
    const y = deckHeightAt(d, e, n);
    if (typeof y === 'number' && (height === null || y > height)) height = y;
  }
  if (height === null) return terrain.surfaceHeight(e, n);
  return terrain.isWater(e, n) ? height : Math.max(height, terrain.surfaceHeight(e, n));
}

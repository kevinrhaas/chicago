/**
 * where.js — the street you are standing on, in words (T-2617, Navigator Home's
 * YOU ARE AT).
 *
 * Two scenes carry their streets in two different records, and both are read
 * rather than invented:
 *
 *   1835  the scene index's street records (streets.js `status(e, n, bearing)`),
 *         named by their 1835 names, the same words the street readout prints;
 *   1904  the Sanborn-traced street grid (street-grid.js `grid`): one carriageway
 *         polygon per street segment, named by the grid's own `name_1904`.
 *
 * T-2741: and, in 1904, the faded context city's named centrelines (context.js, data/
 * context/1904.json `streets`) where the traced grid does not reach, so the compass can
 * say "Michigan Avenue" a block west of the grid. A centreline counts from the edge of
 * its carriageway (`lineHalfWidth`), the way a grid polygon counts from its kerb.
 *
 * Where two streets are both within `corner` metres you are at their corner
 * ("Prairie Avenue & East Eighteenth Street"); one street within that is the street
 * you are on; one within `near` metres is the street you are near. Otherwise the
 * answer is null and Home says so plainly. Pure: no DOM, no THREE.
 */

function segmentDistance(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay;
  const len2 = dx * dx + dy * dy;
  const t = len2 ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / len2)) : 0;
  return Math.hypot(px - (ax + t * dx), py - (ay + t * dy));
}

function inside(px, py, poly) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > py) !== (yj > py) && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

/** Metres from a point to a polygon: 0 inside it. */
export function polygonDistance(e, n, poly) {
  if (!poly?.length) return Infinity;
  if (inside(e, n, poly)) return 0;
  let best = Infinity;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    best = Math.min(best, segmentDistance(e, n, poly[j][0], poly[j][1], poly[i][0], poly[i][1]));
  }
  return best;
}

export function createWhere({ streets = null, grid = null, lines = [], lineHalfWidth = 5.8, corner = 10, near = 60 } = {}) {
  const ways = (grid?.carriageways ?? [])
    .filter((c) => c?.street && c.polygon_local_m?.length >= 3)
    .map((c) => ({ street: c.street, name: grid.streets?.[c.street]?.name_1904 ?? null, poly: c.polygon_local_m }))
    .filter((w) => w.name);
  // `{ name, e0, n0, e1, n1 }`, keyed by name so a street the grid also draws is one street.
  const named = (lines ?? []).filter((l) => l?.name && [l.e0, l.n0, l.e1, l.n1].every(Number.isFinite));
  const gridNames = new Set(ways.map((w) => w.name));

  function fromGrid(e, n) {
    const byStreet = new Map();
    for (const w of ways) {
      const d = polygonDistance(e, n, w.poly);
      if (!byStreet.has(w.street) || d < byStreet.get(w.street).d) byStreet.set(w.street, { name: w.name, d });
    }
    for (const l of named) {
      if (gridNames.has(l.name)) continue;
      const d = Math.max(0, segmentDistance(e, n, l.e0, l.n0, l.e1, l.n1) - lineHalfWidth);
      const k = `line:${l.name}`;
      if (!byStreet.has(k) || d < byStreet.get(k).d) byStreet.set(k, { name: l.name, d });
    }
    const ranked = [...byStreet.values()].sort((a, b) => a.d - b.d);
    const close = ranked.filter((r) => r.d <= corner);
    if (close.length >= 2) return { mode: 'corner', place: `${close[0].name} & ${close[1].name}` };
    if (close.length === 1) return { mode: 'on', place: close[0].name };
    if (ranked[0] && ranked[0].d <= near) return { mode: 'near', place: `near ${ranked[0].name}` };
    return null;
  }

  function fromStreets(e, n, bearingDeg) {
    const s = streets?.status?.(e, n, bearingDeg);
    const names = [...new Set((s?.streets ?? []).map((r) => r.name_1835).filter(Boolean))];
    if (!s || !names.length) return null;
    if (s.mode === 'intersection' && names.length >= 2) return { mode: 'corner', place: `${names[0]} & ${names[1]}` };
    if (s.mode === 'ahead') return (s.distance_m ?? Infinity) <= near ? { mode: 'near', place: `near ${names[0]}` } : null;
    return { mode: 'on', place: names[0] };
  }

  return {
    /** T-2741: the scene draws no streets at all (1812), so "none here" means "none yet". */
    get empty() { return !ways.length && !named.length && !(streets?.records?.length); },
    /** `{ mode: 'corner'|'on'|'near', place }` or null. */
    at(e, n, bearingDeg = 0) {
      if (ways.length || named.length) return fromGrid(e, n);
      return fromStreets(e, n, bearingDeg);
    },
  };
}

const WINDS = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'];
/** "facing west": the eight winds, from a compass bearing. */
export function facingWords(bearingDeg) {
  const b = ((Number(bearingDeg) || 0) % 360 + 360) % 360;
  return `facing ${WINDS[Math.round(b / 45) % 8]}`;
}

/** "10:30" → "10:30 am"; the scene's own clock (`lighting.local_time`), said plainly. */
export function clockWords(hhmm) {
  const m = /^(\d{1,2}):(\d{2})$/.exec(String(hhmm ?? '').trim());
  if (!m) return '';
  const h = Number(m[1]) % 24;
  return `${h % 12 || 12}:${m[2]} ${h < 12 ? 'am' : 'pm'}`;
}

/** "1904-07-01" → "1904.07.01", the screen header's date. */
export function screenDate(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso ?? ''));
  return m ? `${m[1]}.${m[2]}.${m[3]}` : '';
}

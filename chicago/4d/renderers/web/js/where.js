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
 * In 1904 the street you are on also gets the house number of the lot beside you (T-2741,
 * the owner, 2026-10-19: "1904 Prairie Avenue" read like an address, so give the real
 * one): the number the 1911 Sanborn prints on the traced parcel (`addresses_1911`). It
 * is carried back to 1904 on the avenues only. The 1909 renumbering moved the east-west
 * streets' numbers (the sheet prints 16th Street's old ones in parentheses, and the
 * parcel trace notes them and does not carry them), while the avenue numbers of the
 * district stood: Glessner's 1800 Prairie Avenue is his own 1887 address, and Pullman's
 * 1729 and Coleman's 1811 are the numbers the 1880s sources print. So a cross-street lot,
 * or one whose note flags a pre-1909 number, names no number. A lot with several numbers
 * names the run ("1605–1613 Indiana Avenue").
 *
 * Where two streets are both within `corner` metres you are at their corner
 * ("Prairie Avenue & East Eighteenth Street"); one street within that is the street
 * you are on; one within `near` metres is the street you are near. Otherwise the
 * answer is null and Home says so plainly. Pure: no DOM, no THREE.
 *
 * T-3684: a city that lists where its named streets meet (`junctions`, `[e, n, a, b]`,
 * data/context/1871.json) says it the way the 1871 directory does. Within `junctionReach`
 * metres of a junction you are at the intersection ("State and Madison streets"); on a
 * street otherwise, you are between its nearest cross streets on either side ("Clark
 * Street, between Washington and Randolph"), or past the last one ("Clark Street, north of
 * Kinzie"). Off the streets, within `nearJunction` metres of one, you are near it.
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

const SUFFIX = / (Street|Avenue|Place|Court|Road)$/;
/** "State Street" + "Madison Street" → "State and Madison streets"; mixed kinds stay whole. */
export function intersectionWords(a, b) {
  const ka = SUFFIX.exec(a)?.[1], kb = SUFFIX.exec(b)?.[1];
  if (ka && ka === kb) return `${a.replace(SUFFIX, '')} and ${b.replace(SUFFIX, '')} ${ka.toLowerCase()}${ka.endsWith('y') ? '' : 's'}`;
  return `${a} and ${b}`;
}
/** A cross street said short, as the directory does: "Washington", "Fifth Avenue". */
const crossWords = (name) => name.replace(/ Street$/, '');

export function createWhere({ streets = null, grid = null, lines = [], junctions = [], lineHalfWidth = 5.8, corner = 10, near = 60, lotReach = 25, junctionReach = 25, betweenReach = 600, nearJunction = 200 } = {}) {
  const ways = (grid?.carriageways ?? [])
    .filter((c) => c?.street && c.polygon_local_m?.length >= 3)
    .map((c) => ({ street: c.street, name: grid.streets?.[c.street]?.name_1904 ?? null,
      name2026: grid.streets?.[c.street]?.name_2026 ?? null, poly: c.polygon_local_m }))
    .filter((w) => w.name);
  // `{ name, e0, n0, e1, n1 }`, keyed by name so a street the grid also draws is one street.
  const named = (lines ?? []).filter((l) => l?.name && [l.e0, l.n0, l.e1, l.n1].every(Number.isFinite));
  const gridNames = new Set(ways.map((w) => w.name));
  // Lots on the avenues' east and west faces, with the numbers the sheet prints on them.
  const lots = (grid?.parcels ?? [])
    .filter((p) => (p?.side === 'east' || p?.side === 'west') && p.addresses_1911?.length
      && p.polygon_local_m?.length >= 3 && !/pre-1909/.test(p.note ?? ''))
    .map((p) => ({ street: p.street, numbers: p.addresses_1911, poly: p.polygon_local_m }));

  /** The number of the lot on `street` nearest you, within `lotReach` metres, or null. */
  function numberOn(street, e, n) {
    let best = null;
    for (const l of lots) {
      if (l.street !== street) continue;
      const d = polygonDistance(e, n, l.poly);
      if (d <= lotReach && (!best || d < best.d)) best = { d, numbers: l.numbers };
    }
    if (!best) return null;
    const ns = best.numbers;
    return ns.length > 1 ? `${ns[0]}–${ns[ns.length - 1]}` : ns[0];
  }

  const meets = (junctions ?? []).filter((j) => Array.isArray(j) && j[2] && j[3] && Number.isFinite(j[0]) && Number.isFinite(j[1]));
  const junctionsOf = new Map();
  for (const j of meets) {
    for (const [own, other] of [[j[2], j[3]], [j[3], j[2]]]) {
      if (!junctionsOf.has(own)) junctionsOf.set(own, []);
      junctionsOf.get(own).push({ e: j[0], n: j[1], other });
    }
  }

  /** The named line nearest you (of `only` that name), with its direction: `{ name, d, ux, uy }`. */
  function nearestLine(e, n, only = null) {
    let best = null;
    for (const l of named) {
      if (only && l.name !== only) continue;
      const d = segmentDistance(e, n, l.e0, l.n0, l.e1, l.n1);
      if (!best || d < best.d) {
        const len = Math.hypot(l.e1 - l.e0, l.n1 - l.n0) || 1;
        best = { name: l.name, d, ux: (l.e1 - l.e0) / len, uy: (l.n1 - l.n0) / len };
      }
    }
    return best;
  }

  /** T-3684: the intersection you stand at, or the street and the cross streets either side. */
  function fromJunctions(e, n) {
    let at = null;
    for (const j of meets) {
      const d = Math.hypot(j[0] - e, j[1] - n);
      if (d <= junctionReach && (!at || d < at.d)) at = { d, a: j[2], b: j[3] };
    }
    const line = nearestLine(e, n);
    if (at) {
      // The street you are on first; in the middle of the crossing, the north–south one.
      const la = nearestLine(e, n, at.a), lb = nearestLine(e, n, at.b);
      let first = at.a;
      if (la && lb && Math.abs(la.d - lb.d) > 3) first = la.d < lb.d ? at.a : at.b;
      else if (la && lb) first = Math.abs(la.uy) >= Math.abs(lb.uy) ? at.a : at.b;
      const second = first === at.a ? at.b : at.a;
      return { mode: 'corner', place: intersectionWords(first, second), streets: [first, second] };
    }
    if (!line || line.d > lineHalfWidth + corner) {
      // Off the street, on a bank, a lot or open ground: the crossing nearest you, then
      // the street nearest you.
      let close = null;
      for (const j of meets) {
        const d = Math.hypot(j[0] - e, j[1] - n);
        if (d <= nearJunction && (!close || d < close.d)) close = { d, a: j[2], b: j[3] };
      }
      if (close) return { mode: 'near', place: `near ${intersectionWords(close.a, close.b)}` };
      return line && line.d <= lineHalfWidth + near ? { mode: 'near', place: `near ${line.name}` } : null;
    }
    // Cross streets of this street, measured along its direction where you stand.
    let ahead = null, behind = null;
    for (const j of junctionsOf.get(line.name) ?? []) {
      const dx = j.e - e, dy = j.n - n;
      const along = dx * line.ux + dy * line.uy, across = Math.abs(dx * line.uy - dy * line.ux);
      if (across > 40 || Math.abs(along) > betweenReach) continue;
      if (along >= 0 && (!ahead || along < ahead.along)) ahead = { along, name: j.other };
      if (along < 0 && (!behind || -along < behind.along)) behind = { along: -along, name: j.other };
    }
    if (ahead && behind && ahead.name !== behind.name) {
      // South before north on a north–south street, west before east otherwise.
      const forward = Math.abs(line.uy) >= Math.abs(line.ux) ? line.uy >= 0 : line.ux >= 0;
      const [x, y] = forward ? [behind, ahead] : [ahead, behind];
      return { mode: 'on', place: `${line.name}, between ${crossWords(x.name)} and ${crossWords(y.name)}`, street: line.name };
    }
    const one = ahead ?? behind;
    if (one) {
      // "north of Kinzie": which side of the cross street you are on, in the eight winds.
      const sign = one === ahead ? -1 : 1;
      const deg = (Math.atan2(sign * line.ux, sign * line.uy) * 180) / Math.PI;
      const wind = ['north', 'east', 'south', 'west'][Math.round(((deg % 360) + 360) % 360 / 90) % 4];
      return { mode: 'on', place: `${line.name}, ${wind} of ${crossWords(one.name)}`, street: line.name };
    }
    return { mode: 'on', place: line.name, street: line.name };
  }

  function fromGrid(e, n) {
    if (!ways.length && meets.length) {
      const said = fromJunctions(e, n);
      if (said) return said;
    }
    const byStreet = new Map();
    for (const w of ways) {
      const d = polygonDistance(e, n, w.poly);
      if (!byStreet.has(w.street) || d < byStreet.get(w.street).d) byStreet.set(w.street, { street: w.street, name: w.name, name2026: w.name2026, d });
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
    if (close.length === 1) {
      const number = close[0].street ? numberOn(close[0].street, e, n) : null;
      return number
        ? { mode: 'on', place: close[0].name, address: `${number} ${close[0].name}`, number, street_2026: close[0].name2026 }
        : { mode: 'on', place: close[0].name };
    }
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
    /** T-3684: the city lists where its named streets meet. */
    get junctions() { return meets.length; },
    /** `{ mode: 'corner'|'on'|'near', place, address?, number?, street_2026? }` or null;
     *  `address` is the period house number and street, where the lot beside you carries
     *  one, and `street_2026` that street's name today (the grid's `name_2026`). */
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

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
  'August', 'September', 'October', 'November', 'December'];

/** T-3437: "1904-02-15" → "15 February", the year chip's day as it is spoken. */
export function spokenDay(iso) {
  const m = /^\d{4}-(\d{2})-(\d{2})/.exec(String(iso ?? ''));
  return m && MONTHS[+m[1] - 1] ? `${+m[2]} ${MONTHS[+m[1] - 1]}` : '';
}

/** "1904-07-01" → "1904.07.01", the screen header's date. */
export function screenDate(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(iso ?? ''));
  return m ? `${m[1]}.${m[2]}.${m[3]}` : '';
}

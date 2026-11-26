// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * fire-map.js — the Great Fire of 1871 as data: where it burned and when (T-3687).
 *
 * Pure: no renderer, no DOM, so a node test, the people (T-3690) and the fire as drawn
 * (city-fire.js) all read the same answer. It reads data/fire/1871.json, which
 * tools/fire_1871.py derives into the scene's local east/north metres:
 *
 *   zones     the burnt district's outlines (the West, South and North divisions, and
 *             the ground the Saturday fire of 7 October had already cleared)
 *   controls  places with an hour from the accounts (Andreas vol. 2 p. 719's epitome and
 *             its neighbours), each attested or inferred, with its source
 *   spared    the places inside the district the fire passed by (the Ogden house, the
 *             Water Tower, the O'Leary cottage)
 *
 * A place inside a zone catches at the hour interpolated from the nearest controls,
 * measured with the across-wind distance stretched so the hours run down the south-west
 * gale; a building's own seeded jitter roughens the front. Times are minutes from
 * 1871-10-08T00:00 on the accounts' clock (Chicago local time, the scene's clock).
 */

const DAY0 = Date.UTC(1871, 9, 8, 0, 0);

/** 'YYYY-MM-DDTHH:MM' (or with seconds) -> minutes from 1871-10-08T00:00, or null. */
export function minutesOf(iso) {
  const m = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?/.exec(String(iso ?? '').trim());
  if (!m) return null;
  const t = Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +(m[6] ?? 0));
  return Number.isFinite(t) ? (t - DAY0) / 60000 : null;
}

/** Minutes from 1871-10-08T00:00 -> 'YYYY-MM-DDTHH:MM'. */
export function isoOf(minutes) {
  const d = new Date(DAY0 + Math.floor(minutes) * 60000);
  const p = (v) => String(v).padStart(2, '0');
  return `${d.getUTCFullYear()}-${p(d.getUTCMonth() + 1)}-${p(d.getUTCDate())}T${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`;
}

/** A small seeded number in [0, 1) for a string (FNV-1a, then an xorshift). */
export function hash01(key) {
  let s = 2166136261 >>> 0;
  for (const ch of String(key)) { s ^= ch.charCodeAt(0); s = Math.imul(s, 16777619) >>> 0; }
  s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0;
  return s / 4294967296;
}

const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };

/** Delaunay triangles (index triples) of a few points, by Bowyer-Watson. */
export function triangulate(pts) {
  if (pts.length < 3) return [];
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const d = Math.max(x1 - x0, y1 - y0) * 20 + 1, mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
  const P = [...pts, [mx - d, my - d], [mx + d, my - d], [mx, my + d]], N = pts.length;
  const circ = (a, b, c) => {
    const [ax, ay] = P[a], [bx, by] = P[b], [cx, cy] = P[c];
    const D = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));
    const ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / D;
    const uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / D;
    return { a, b, c, ux, uy, r2: (ax - ux) ** 2 + (ay - uy) ** 2 };
  };
  let tris = [circ(N, N + 1, N + 2)];
  for (let i = 0; i < N; i++) {
    const [px, py] = P[i], bad = [], keep = [];
    for (const t of tris) ((px - t.ux) ** 2 + (py - t.uy) ** 2 < t.r2 ? bad : keep).push(t);
    const edges = new Map();
    for (const t of bad) for (const [u, v] of [[t.a, t.b], [t.b, t.c], [t.c, t.a]]) {
      const key = u < v ? `${u},${v}` : `${v},${u}`;
      edges.set(key, edges.has(key) ? null : [u, v]);
    }
    for (const edge of edges.values()) if (edge) keep.push(circ(edge[0], edge[1], i));
    tris = keep;
  }
  return tris.filter((t) => t.a < N && t.b < N && t.c < N).map((t) => [t.a, t.b, t.c]);
}

function inside(e, n, poly) {
  let res = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[i], b = poly[j];
    if ((a[1] > n) !== (b[1] > n) && e < (b[0] - a[0]) * (n - a[1]) / (b[1] - a[1]) + a[0]) res = !res;
  }
  return res;
}

/**
 * The map and clock of one fire document. `catchAt(e, n, key)` is the minute the fire
 * reaches a place (null where it never burned); `key` seeds that building's own jitter.
 */
/** How far from a timed place (m) a building's own few minutes either way take full effect. */
export const JITTER_FREE_M = 60;

export function createFireMap(doc) {
  if (!doc || !Array.isArray(doc.zones) || !Array.isArray(doc.controls)) throw Error('fire map: not a fire document');
  const zones = doc.zones.filter((z) => Array.isArray(z.local) && z.local.length >= 3).map((z) => {
    const es = z.local.map((p) => p[0]), ns = z.local.map((p) => p[1]);
    return { id: z.id, poly: z.local, e0: Math.min(...es), e1: Math.max(...es), n0: Math.min(...ns), n1: Math.max(...ns),
      burntAt: z.burnt_at ? minutesOf(z.burnt_at) : null };
  });
  const controls = doc.controls.filter((c) => Array.isArray(c.local)).map((c) => ({ id: c.id, e: c.local[0], n: c.local[1], m: minutesOf(c.t) }))
    .filter((c) => Number.isFinite(c.m));
  const spared = (doc.spared ?? []).filter((s) => Array.isArray(s.local)).map((s) => ({ id: s.id, e: s.local[0], n: s.local[1], r: s.r_m ?? 10 }));
  // The wind blows FROM `from_deg` (clockwise from north); the fire runs the other way.
  const toward = ((doc.wind?.from_deg ?? 225) + 180) * Math.PI / 180;
  const wind = { e: Math.sin(toward), n: Math.cos(toward), mps: doc.wind?.gale_mps ?? 10 };
  const model = doc.model ?? {};
  const stretch = model.across_wind_stretch ?? 1.8, jitter = model.jitter_min ?? 6;
  const survivors = new Set(doc.survivors ?? []);
  const fates = Object.fromEntries(Object.entries(doc.structures ?? {}).map(([id, r]) => [id, r.fate]));
  for (const id of survivors) fates[id] = 'survives';
  // T-3751: a landmark an account has alight at an hour (`burning_by`) burns at that hour, no
  // jitter: its rise (frame or masonry, by its fate) is begun so that it is ablaze then, as the
  // jaunt's stop at that hour tells it.
  const pins = new Map();
  for (const [id, r] of Object.entries(doc.structures ?? {})) {
    const t = minutesOf(r.burning_by?.t);
    if (!Number.isFinite(t) || fates[id] === 'survives') continue;
    const rise = r.fate === 'collapses' ? (model.frame?.rise_min ?? 5) : (model.masonry?.rise_min ?? 9);
    pins.set(id, t - rise);
  }
  const zoneAt0 = (z, e, n) => e >= z.e0 && e <= z.e1 && n >= z.n0 && n <= z.n1 && inside(e, n, z.poly);
  const zoneAt = (e, n) => zones.find((z) => zoneAt0(z, e, n)) ?? null;
  const isSpared = (e, n) => spared.some((s) => (e - s.e) ** 2 + (n - s.n) ** 2 <= s.r * s.r);
  // The hours are laid on a triangulation of the timed places, in a frame where the
  // across-wind distance counts `stretch` times (the front runs down the gale), and read
  // linearly within each triangle: the hour at a timed place is its own, and between two
  // the front moves steadily from one to the next (an inverse-distance average does not:
  // it pulls every point toward the mean of all the hours and lets the front run backward).
  const frame = (e, n) => [e * wind.e + n * wind.n, stretch * (-e * wind.n + n * wind.e)];
  // Each division is laid on its own: the river between two was a gap the fire took
  // its own time to cross, so no triangle spans it.
  function network(list) {
    const pts = list.map((c) => frame(c.e, c.n));
    const tris = triangulate(pts).map(([a, b, c]) => {
      const [ax, ay] = pts[a], [bx, by] = pts[b], [cx, cy] = pts[c];
      return { a: list[a].m, b: list[b].m, c: list[c].m, ax, ay, bx, by, cx, cy, det: (by - cy) * (ax - cx) + (cx - bx) * (ay - cy) };
    }).filter((t) => Math.abs(t.det) > 1e-6);
    return { list, tris };
  }
  const everywhere = network(controls);
  const networks = new Map(zones.map((z) => {
    const own = controls.filter((c) => zoneAt0(z, c.e, c.n));
    return [z.id, own.length >= 3 ? network(own) : everywhere];
  }));
  /** The interpolated hour at a place, before any building's jitter. */
  function hourAt(e, n, zone = zoneAt(e, n)) {
    const net = (zone && networks.get(zone.id)) || everywhere;
    if (!net.tris.length) return net.list.length ? net.list[0].m : null;
    const [x, y] = frame(e, n);
    let best = null, bestMin = -Infinity, bw = null;
    for (const t of net.tris) {
      const l1 = ((t.by - t.cy) * (x - t.cx) + (t.cx - t.bx) * (y - t.cy)) / t.det;
      const l2 = ((t.cy - t.ay) * (x - t.cx) + (t.ax - t.cx) * (y - t.cy)) / t.det;
      const l3 = 1 - l1 - l2, lo = Math.min(l1, l2, l3);
      if (lo > bestMin) { bestMin = lo; best = t; bw = [l1, l2, l3]; if (lo >= 0) break; }
    }
    // Beyond the outermost timed places: the hour of the nearest edge of the network.
    if (bestMin < 0) {
      const w = bw.map((v) => Math.max(0, v)), sum = w[0] + w[1] + w[2];
      bw = w.map((v) => v / sum);
    }
    return bw[0] * best.a + bw[1] * best.b + bw[2] * best.c;
  }
  function catchAt(e, n, key = null) {
    if (key !== null && pins.has(key)) return pins.get(key);
    const z = zoneAt(e, n);
    if (!z || isSpared(e, n)) return null;
    if (z.burntAt !== null) return z.burntAt;
    const h = hourAt(e, n, z);
    if (h === null) return null;
    // Blocks catch in clumps and each building a few minutes from its neighbours; a timed
    // place keeps its own hour (T-3751: the jitter fades in over JITTER_FREE_M from the
    // nearest timed place, so the building an account names catches when it says).
    const cell = hash01(`${Math.floor(e / 45)},${Math.floor(n / 45)}`) - 0.5;
    const own = key === null ? 0 : hash01(key) - 0.5;
    const net = networks.get(z.id) || everywhere;
    let near = Infinity;
    for (const c of net.list) { const d = (c.e - e) ** 2 + (c.n - n) ** 2; if (d < near) near = d; }
    return h + jitter * Math.min(1, Math.sqrt(near) / JITTER_FREE_M) * (1.2 * cell + 0.8 * own);
  }
  return {
    doc, zones, controls, spared, wind, model, survivors, fates,
    start: minutesOf(doc.start), end: minutesOf(doc.end), rain: minutesOf(doc.rain?.t),
    zoneAt, isSpared, hourAt, catchAt, pins,
    /** A named structure's fate: 'survives', 'walls_stand', 'roof_burns' or 'collapses' (null: by its build). */
    fateOf: (id) => fates[id] ?? null,
  };
}

/**
 * Where a building is in its burning `m` minutes after it caught (negative: not yet):
 *   heat    0..1, how hard it burns (flames at its windows and over its roof)
 *   char    0..1, how blackened its walls are
 *   fall    0..1, how far it has come down (a frame house to its heap; masonry walls only where they fall)
 *   roof    0..1, how far its roof has burned through (masonry: the shell stands open)
 *   embers  0..1, the glow of what is left
 *   smoke   0..1, the smoke still going up from it
 * `rain` (minutes after the rain began, or null) damps the flames over about three hours.
 */
export function burnState(kind, m, model = {}, { wallsFall = false, rainAfter = null } = {}) {
  const none = { heat: 0, char: 0, fall: 0, roof: 0, embers: 0, smoke: 0 };
  if (!Number.isFinite(m) || m < 0) return none;
  const damp = rainAfter === null || rainAfter < 0 ? 1 : 1 - 0.85 * smooth(rainAfter / 180);
  if (kind === 'frame') {
    const p = { rise_min: 5, full_min: 22, fall_start_min: 20, fall_min: 10, embers_min: 150, smoke_min: 420, ...(model.frame ?? {}) };
    const heat = smooth(m / p.rise_min) * (1 - smooth((m - p.full_min) / 10));
    const fall = smooth((m - p.fall_start_min) / p.fall_min);
    const embers = m < p.fall_start_min ? 0 : smooth((m - p.fall_start_min) / 4) * (1 - smooth((m - p.fall_start_min) / p.embers_min));
    return { heat: heat * damp, char: smooth((m - 1) / (p.full_min * 0.7)), fall, roof: fall,
      embers: embers * damp, smoke: 1 - smooth((m - p.full_min) / p.smoke_min) };
  }
  const p = { rise_min: 9, full_min: 55, roof_fall_min: 40, fade_min: 45, embers_min: 240, smoke_min: 720, ...(model.masonry ?? {}) };
  const heat = smooth(m / p.rise_min) * (1 - smooth((m - p.full_min) / p.fade_min));
  const roof = smooth((m - p.roof_fall_min) / 15);
  const fall = wallsFall ? smooth((m - p.full_min) / 25) : 0;
  const after = m - p.full_min;
  const embers = after < 0 ? 0 : smooth(after / 10) * (1 - smooth(after / p.embers_min));
  return { heat: heat * damp, char: smooth((m - 2) / (p.full_min * 0.8)), fall, roof,
    embers: embers * damp, smoke: 1 - smooth((m - p.full_min) / p.smoke_min) };
}

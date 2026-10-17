/**
 * modern-streets.js — today's street and house number under any year (T-2741).
 *
 * The owner, 2026-10-17: "i want the current modern day map overlaid on all of them
 * 1812, 1835 and 1904 so you have the current street name/address you are at". This
 * reads data/modern/streets.json — the City of Chicago's own street centerlines,
 * clipped and projected by tools/build_modern_streets.py — and answers, for a point in
 * the scene's local metres, the street you stand on today, the corner you stand at,
 * or the house number you stand in front of.
 *
 * THE NUMBER IS READ OFF THE CITY'S OWN BLOCK RANGE, never computed from a rule of
 * thumb: Chicago is not 800 numbers a mile near the Loop (Madison to Roosevelt is 1200
 * in about a mile), so a formula off State and Madison would put Glessner House at
 * 1733 S Prairie when its door says 1800. Along a segment the number runs linearly
 * from the range's from-node to its to-node, on the side of the street you are on,
 * with that side's parity.
 *
 * Today's map is a navigation aid. Nothing in a period layer is read off it. Pure: no
 * DOM, no THREE.
 */

/** A centreline within this of you is the street you are on. */
export const ON_M = 14;
/** Within this you are near it, and a house number on it is yours. */
export const NEAR_M = 70;
const CELL = 100;

function project(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay;
  const len2 = dx * dx + dy * dy;
  const t = len2 ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / len2)) : 0;
  const fx = ax + t * dx, fy = ay + t * dy;
  return { t, d: Math.hypot(px - fx, py - fy), cross: dx * (py - ay) - dy * (px - ax) };
}

/** The house number at fraction `t` of a range, on a side of parity `parity`. */
export function houseNumber(from, to, t, parity) {
  if (!from && !to) return null;
  const lo = Math.min(from, to), hi = Math.max(from, to);
  let x = Math.round(from + (to - from) * t);
  const want = parity === 'O' ? 1 : 0;
  if (Math.abs(x % 2) !== want) x += x + 1 <= hi ? 1 : -1;
  return Math.max(lo, Math.min(hi, x));
}

/** "S Prairie Ave" + 1800 -> "1800 S Prairie Ave". */
export function addressText(number, name) {
  return Number.isFinite(number) ? `${number} ${name}` : name;
}

export function createModernStreets(doc) {
  const names = doc?.names ?? [];
  const segs = [];
  const cells = new Map();
  const key = (cx, cy) => `${cx},${cy}`;
  for (const raw of doc?.segments ?? []) {
    const [ni, axis, grid, cls, lf, lt, rf, rt, lpar, flat] = raw;
    if (!Array.isArray(flat) || flat.length < 4) continue;
    const pts = new Float32Array(flat);
    // Cumulative length, so a point's fraction runs along the whole block.
    const cum = new Float32Array(pts.length / 2);
    let eMin = Infinity, eMax = -Infinity, nMin = Infinity, nMax = -Infinity;
    for (let i = 0; i < pts.length; i += 2) {
      if (i) cum[i / 2] = cum[i / 2 - 1] + Math.hypot(pts[i] - pts[i - 2], pts[i + 1] - pts[i - 1]);
      eMin = Math.min(eMin, pts[i]); eMax = Math.max(eMax, pts[i]);
      nMin = Math.min(nMin, pts[i + 1]); nMax = Math.max(nMax, pts[i + 1]);
    }
    const s = {
      name: names[ni] ?? '', axis, grid, cls, lf, lt, rf, rt, lpar, pts, cum,
      length: cum[cum.length - 1], box: [eMin, nMin, eMax, nMax],
    };
    const id = segs.push(s) - 1;
    for (let cx = Math.floor(eMin / CELL); cx <= Math.floor(eMax / CELL); cx++) {
      for (let cy = Math.floor(nMin / CELL); cy <= Math.floor(nMax / CELL); cy++) {
        const k = key(cx, cy);
        if (!cells.has(k)) cells.set(k, []);
        cells.get(k).push(id);
      }
    }
  }

  /** Every segment within `r` metres of (e, n), nearest point first, one per name. */
  function near(e, n, r = NEAR_M) {
    const seen = new Set();
    const best = new Map();
    for (let cx = Math.floor((e - r) / CELL); cx <= Math.floor((e + r) / CELL); cx++) {
      for (let cy = Math.floor((n - r) / CELL); cy <= Math.floor((n + r) / CELL); cy++) {
        for (const id of cells.get(key(cx, cy)) ?? []) {
          if (seen.has(id)) continue;
          seen.add(id);
          const s = segs[id];
          if (e < s.box[0] - r || e > s.box[2] + r || n < s.box[1] - r || n > s.box[3] + r) continue;
          let hit = null;
          for (let i = 0; i + 3 < s.pts.length; i += 2) {
            const p = project(e, n, s.pts[i], s.pts[i + 1], s.pts[i + 2], s.pts[i + 3]);
            if (!hit || p.d < hit.d) {
              const along = s.cum[i / 2] + p.t * (s.cum[i / 2 + 1] - s.cum[i / 2]);
              hit = { d: p.d, t: s.length ? along / s.length : 0, left: p.cross > 0 };
            }
          }
          if (!hit || hit.d > r) continue;
          const prev = best.get(s.name);
          if (!prev || hit.d < prev.d) best.set(s.name, { ...hit, seg: s });
        }
      }
    }
    return [...best.values()].sort((a, b) => a.d - b.d);
  }

  function numberOn(hit) {
    const s = hit.seg;
    const leftPar = s.lpar === 'O' ? 'O' : 'E';
    const rightPar = leftPar === 'O' ? 'E' : 'O';
    // Your side's range; a side with no numbers (a park, the river) lends the other's.
    const own = hit.left ? [s.lf, s.lt, leftPar] : [s.rf, s.rt, rightPar];
    const other = hit.left ? [s.rf, s.rt, rightPar] : [s.lf, s.lt, leftPar];
    const [from, to, parity] = (own[0] || own[1]) ? own : other;
    return houseNumber(from, to, hit.t, parity);
  }

  return {
    get segments() { return segs; },
    near,
    /**
     * Where you are today: `{ mode: 'corner'|'on'|'near', street, cross?, number,
     * address, distance_m }`, or null with no street within NEAR_M.
     */
    at(e, n) {
      const hits = near(e, n, NEAR_M);
      if (!hits.length) return null;
      const first = hits[0];
      const number = numberOn(first);
      const out = {
        mode: first.d <= ON_M ? 'on' : 'near',
        street: first.seg.name,
        number,
        address: number == null ? null : addressText(number, first.seg.name),
        distance_m: first.d,
      };
      const second = hits[1];
      // A court or place (class 5) is a street you can stand on, never the corner you name.
      if (out.mode === 'on' && second && second.d <= ON_M && second.seg.axis !== first.seg.axis
        && first.seg.cls !== 5 && second.seg.cls !== 5) {
        out.mode = 'corner';
        out.cross = second.seg.name;
      }
      return out;
    },
  };
}

/** One line of text for the readout: the corner, the house number, or the street. */
export function todayText(today) {
  if (!today) return 'no street here today';
  if (today.mode === 'corner') return `${today.street} & ${today.cross}`;
  return today.address ?? today.street;
}

/** Today's streets from the data base, or null (the readout then says so and the scene is unharmed). */
export async function loadModernStreets(dataBase) {
  if (!dataBase) return null;
  try {
    const res = await fetch(new URL('modern/streets.json', dataBase), { cache: 'no-cache' });
    if (!res.ok) return null;
    return createModernStreets(await res.json());
  } catch {
    return null;
  }
}

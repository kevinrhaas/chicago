/**
 * kept-ground.js — where on a town lot the weeds may stand (T-2086).
 *
 * The owner, 2026-10-04: the town should be "less 'weedy' ... in front of
 * stores and houses, and in the house back yards", without cutting "the
 * beautiful plants and grass and flowers". `data/yard/town_kept_ground.json`
 * (written by `tools/generate_kept_ground.py`, re-derived by check.sh) states,
 * per improved lot, a KEPT RING — the lot pulled in from its lot lines, its rear
 * corners cut back — and the REFUGES at the foot of its outbuildings, with the
 * strip's width and the share of turned-out weeds it takes. This file only
 * answers the question the record poses: where does a forb slot stand? Outside
 * every kept ring, or in a refuge, where it always did. Inside a kept ring, a
 * stated share of slots is RE-SEATED in the strip beside the nearest lot line
 * and the rest stand empty — the weeds move to the fence foot rather than
 * vanish, and the town draws no more of them than before. Which ground is kept,
 * and how much the strip takes, is the record's claim, never this file's.
 *
 * The low layer (the trodden Poa, plantain, knotweed and clover) is NOT asked:
 * a kept yard is cropped ground, not bare ground. Docs/LIBERTIES.md L376.
 */

/** The bin the lots are indexed in, in metres. A lot is ~24 x 44 m, so one lot
 *  touches at most a few bins and a lattice slot tests one bin's list. */
const BIN_M = 16;

function inside(pts, e, n) {
  let hit = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [ei, ni] = pts[i];
    const [ej, nj] = pts[j];
    if ((ni > n) !== (nj > n) && e < ((ej - ei) * (n - ni)) / (nj - ni) + ei) hit = !hit;
  }
  return hit;
}

function boxOf(pts) {
  let minE = Infinity, minN = Infinity, maxE = -Infinity, maxN = -Infinity;
  for (const [e, n] of pts) {
    if (e < minE) minE = e;
    if (e > maxE) maxE = e;
    if (n < minN) minN = n;
    if (n > maxN) maxN = n;
  }
  return { minE, minN, maxE, maxN };
}

const within = (b, e, n) => e >= b.minE && e <= b.maxE && n >= b.minN && n <= b.maxN;

/** A stable 0..1 draw off a position, so a re-seated forb lands on the same spot
 *  every rebuild and never swims as the walker moves. */
function hash01(e, n, salt) {
  let h = Math.imul(Math.round(e * 100) | 0, 0x27d4eb2d) ^ Math.imul(Math.round(n * 100) | 0, 0x165667b1);
  h = Math.imul(h ^ salt ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}

/** Each edge of a ring with its unit direction and OUTWARD normal. */
function edgesOf(ring) {
  let a2 = 0;
  for (let i = 0; i < ring.length; i++) {
    const p = ring[i], q = ring[(i + 1) % ring.length];
    a2 += p[0] * q[1] - q[0] * p[1];
  }
  const out = a2 > 0 ? 1 : -1;   // counter-clockwise: the outward normal is to the right
  const edges = [];
  for (let i = 0; i < ring.length; i++) {
    const p = ring[i], q = ring[(i + 1) % ring.length];
    const len = Math.hypot(q[0] - p[0], q[1] - p[1]);
    if (len < 1e-6) continue;
    const ux = (q[0] - p[0]) / len, un = (q[1] - p[1]) / len;
    edges.push({ p, ux, un, len, ox: un * out, on: -ux * out });
  }
  return edges;
}

/**
 * @param {object|null} record the `town_kept_ground` record, or null
 * @returns {{blocksForb: (e: number, n: number) => boolean,
 *            forbSeat: (e: number, n: number) => (null|false|number[]),
 *            census: {lots: number, refuges: number}}}
 */
export function keptGround(record) {
  const lots = [];
  for (const lot of record?.lots ?? []) {
    const ring = lot.kept_ring_local_enu_m;
    if (!Array.isArray(ring) || ring.length < 3) continue;
    const refuges = (lot.refuges_local_enu_m ?? []).filter((r) => Array.isArray(r) && r.length >= 3)
      .map((pts) => ({ pts, box: boxOf(pts) }));
    lots.push({ ring, box: boxOf(ring), refuges, edges: edgesOf(ring) });
  }
  const census = { lots: lots.length, refuges: lots.reduce((s, l) => s + l.refuges.length, 0) };
  if (!lots.length) return { blocksForb: () => false, forbSeat: () => null, census };
  const strip = Number(record.strip_m) > 0 ? Number(record.strip_m) : 0;
  const share = Number(record.moved_share) > 0 ? Math.min(1, Number(record.moved_share)) : 0;

  const bins = new Map();
  lots.forEach((lot, i) => {
    const b = lot.box;
    for (let x = Math.floor(b.minE / BIN_M); x <= Math.floor(b.maxE / BIN_M); x++) {
      for (let y = Math.floor(b.minN / BIN_M); y <= Math.floor(b.maxN / BIN_M); y++) {
        const k = `${x},${y}`;
        if (!bins.has(k)) bins.set(k, []);
        bins.get(k).push(i);
      }
    }
  });
  /** The kept lot this point stands in (outside its refuges), or null. */
  const keptAt = (e, n) => {
    const list = bins.get(`${Math.floor(e / BIN_M)},${Math.floor(n / BIN_M)}`);
    if (!list) return null;
    for (const i of list) {
      const lot = lots[i];
      if (!within(lot.box, e, n) || !inside(lot.ring, e, n)) continue;
      for (const r of lot.refuges) if (within(r.box, e, n) && inside(r.pts, e, n)) return null;
      return lot;
    }
    return null;
  };
  const blocksForb = (e, n) => keptAt(e, n) !== null;
  /**
   * Where a forb slot at (e, n) stands: `null` — where it is, the ring does not
   * reach it; `false` — nowhere, the slot stands empty; `[e, n]` — re-seated in
   * the strip, off the nearest edge of the kept ring, a draw of the strip's
   * width outward and slid a little along the line so the turned-out slots do
   * not stack in rows.
   */
  const forbSeat = (e, n) => {
    const lot = keptAt(e, n);
    if (!lot) return null;
    if (!(strip > 0) || hash01(e, n, 0x5eed) >= share) return false;
    let best = null, bestD = Infinity;
    for (const ed of lot.edges) {
      const t = Math.max(0, Math.min(ed.len, (e - ed.p[0]) * ed.ux + (n - ed.p[1]) * ed.un));
      const d = Math.hypot(ed.p[0] + ed.ux * t - e, ed.p[1] + ed.un * t - n);
      if (d < bestD) { bestD = d; best = { ed, t }; }
    }
    const { ed } = best;
    const t = Math.max(0, Math.min(ed.len, best.t + (hash01(e, n, 0xa11e) - 0.5) * 3.0));
    const out = strip * (0.12 + 0.76 * hash01(e, n, 0x0f75));
    return [ed.p[0] + ed.ux * t + ed.ox * out, ed.p[1] + ed.un * t + ed.on * out];
  };
  return { blocksForb, forbSeat, census };
}

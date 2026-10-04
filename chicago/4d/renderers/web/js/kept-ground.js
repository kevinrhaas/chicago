/**
 * kept-ground.js — where on a town lot the weeds may stand (T-2086).
 *
 * The owner, 2026-10-04: the town should be "less 'weedy' ... in front of
 * stores and houses, and in the house back yards", without cutting "the
 * beautiful plants and grass and flowers". `data/yard/town_kept_ground.json`
 * (written by `tools/generate_kept_ground.py`, re-derived by check.sh) states,
 * per improved lot, a KEPT RING — the lot pulled in from its lot lines, its rear
 * corners cut back — and the REFUGES at the foot of its outbuildings. This file
 * only answers the question the record poses: is a forb allowed here? Inside a
 * kept ring and outside every refuge, no; anywhere else, the zone decides as it
 * always did. Which ground is kept is the record's claim, never this file's.
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

/**
 * @param {object|null} record the `town_kept_ground` record, or null
 * @returns {{blocksForb: (e: number, n: number) => boolean,
 *            census: {lots: number, refuges: number}}}
 */
export function keptGround(record) {
  const lots = [];
  for (const lot of record?.lots ?? []) {
    const ring = lot.kept_ring_local_enu_m;
    if (!Array.isArray(ring) || ring.length < 3) continue;
    const refuges = (lot.refuges_local_enu_m ?? []).filter((r) => Array.isArray(r) && r.length >= 3)
      .map((pts) => ({ pts, box: boxOf(pts) }));
    lots.push({ ring, box: boxOf(ring), refuges });
  }
  const census = { lots: lots.length, refuges: lots.reduce((s, l) => s + l.refuges.length, 0) };
  if (!lots.length) return { blocksForb: () => false, census };

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
  const blocksForb = (e, n) => {
    const list = bins.get(`${Math.floor(e / BIN_M)},${Math.floor(n / BIN_M)}`);
    if (!list) return false;
    for (const i of list) {
      const lot = lots[i];
      if (!within(lot.box, e, n) || !inside(lot.ring, e, n)) continue;
      for (const r of lot.refuges) if (within(r.box, e, n) && inside(r.pts, e, n)) return false;
      return true;
    }
    return false;
  };
  return { blocksForb, census };
}

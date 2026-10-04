/**
 * WHAT HANGS IN A GATEWAY (T-2112) — the gate posts, leaves and slip bars a
 * fence record's `openings[].gate` states, as plain boxes the calling layer
 * pushes into its own buffer with its own `pushBox`.
 *
 * Two layers draw fences — `enclosures.js` (the yards, pens and lot lines) and
 * `frontage.js` (the street-lining board fences) — and both already leave the
 * gap. This module is only what stands IN the gap, so the two say the same
 * thing about a gate and neither has to know the other's buffer.
 *
 * The gate itself is `tools/gate_kinds.py`'s, and every number below is a
 * reconstruction like the record that asks for it: a 3 ft 6 in house gate on
 * one leaf, a pair of cart leaves, or slip bars let down out of a rail fence.
 * The leaf frame is two rails and a closing stile with the fence's own stock
 * nailed across it; no brace is drawn, because this layer only draws boxes
 * that stand upright, and a leaning one would be a claim about the gate it
 * does not make.
 *
 * Coordinates: the caller hands local ENU jambs with their ground heights; a
 * box comes back in the renderer's world frame (E, up, −N), with `u` its
 * horizontal along-direction and `part` the face set the caller should use.
 */

const POST_HALF_M = 0.08;          // a 6-inch gate post, heavier than the fence's
const POST_OVER_M = 0.12;          // and standing a little above it
const LEAF_RAIL_H_M = 0.09;
const LEAF_T_M = 0.025;
const BAR_H_M = 0.09;
const CLEAR_M = 0.03;              // hinge and latch play either side of a leaf
const PITCH = { board: 0.16, picket: 0.17, rail: 0.25 };
const STOCK_W = { board: 0.15, picket: 0.075, rail: 0.07 };

function box(out, e, y, n, ue, un, halfLen, halfW, halfH, part) {
  out.push({ cx: e, cy: y, cz: -n, ux: ue, uz: -un, halfLen, halfW, halfH, part });
}

/**
 * One leaf, hinged at `h` (ENU + ground y) and closing along the unit `d`,
 * swung `deg` toward the unit `inward`.
 */
function leaf(out, h, d, inward, len, deg, height, stock) {
  const r = (deg * Math.PI) / 180;
  const ue = d[0] * Math.cos(r) + inward[0] * Math.sin(r);
  const un = d[1] * Math.cos(r) + inward[1] * Math.sin(r);
  const at = (t) => [h.e + ue * t, h.n + un * t];
  const top = height - 0.12;
  const low = 0.18;
  const mid = at(len / 2);
  // The frame: a rail low and a rail high, and the stile the latch is on.
  box(out, mid[0], h.y + low, mid[1], ue, un, len / 2, LEAF_T_M, LEAF_RAIL_H_M / 2, 'rail');
  box(out, mid[0], h.y + top, mid[1], ue, un, len / 2, LEAF_T_M, LEAF_RAIL_H_M / 2, 'rail');
  const st = at(len - 0.04);
  box(out, st[0], h.y + (low + top) / 2, st[1], ue, un, 0.04, LEAF_T_M,
    (top - low) / 2 + LEAF_RAIL_H_M / 2, 'post');
  // The stock across it, the fence's own: boards butted, pales spaced and
  // standing a hand above the top rail the way the fence's do.
  const pitch = PITCH[stock] ?? PITCH.board;
  const w = STOCK_W[stock] ?? STOCK_W.board;
  const count = Math.max(1, Math.floor((len - 0.08) / pitch));
  const first = (len - 0.08 - (count - 1) * pitch) / 2;
  const tall = stock === 'picket' ? top + 0.08 : top;
  for (let k = 0; k < count; k++) {
    const p = at(first + k * pitch);
    box(out, p[0], h.y + (0.06 + tall) / 2, p[1], ue, un, w / 2, LEAF_T_M / 2,
      (tall - 0.06) / 2, 'pale');
  }
}

/**
 * The boxes for one opening. `a` and `b` are the gap's two jambs, `{ e, n, y }`
 * in local ENU with ground height; `height` is the fence's; `into` is the
 * record's `opens_into_local_enu_m`, the side a leaf swings to and slip bars
 * are laid on. Returns [] for a plain opening.
 */
export function gateBoxes(gate, a, b, height, into) {
  const out = [];
  if (!gate || gate.kind === 'opening') return out;
  const de = b.e - a.e;
  const dn = b.n - a.n;
  const width = Math.hypot(de, dn);
  if (width < 0.5) return out;
  const d = [de / width, dn / width];
  // Inward is whichever normal points at `into`; a record that names no side
  // swings to the left of a→b.
  let inward = [-d[1], d[0]];
  if (Array.isArray(into)) {
    const mx = (a.e + b.e) / 2;
    const my = (a.n + b.n) / 2;
    if ((into[0] - mx) * inward[0] + (into[1] - my) * inward[1] < 0) {
      inward = [-inward[0], -inward[1]];
    }
  }
  const postH = height + POST_OVER_M;
  for (const j of [a, b]) {
    box(out, j.e, j.y + postH / 2, j.n, d[0], d[1], POST_HALF_M, POST_HALF_M, postH / 2, 'post');
  }
  const span = width - 2 * POST_HALF_M - 2 * CLEAR_M;
  if (gate.kind === 'bars') {
    // Slip bars let down: the rails drawn out of the posts and laid along the
    // fence on the lot's side, one on another, and any left in place across
    // the top. A rail fence's way in, and no hinge anywhere on it.
    const down = Math.max(0, Math.min(3, gate.bars_down ?? 3));
    const lay = [a.e + de / 2 + inward[0] * 0.7, a.n + dn / 2 + inward[1] * 0.7];
    const y0 = Math.min(a.y, b.y);
    for (let k = 0; k < down; k++) {
      box(out, lay[0], y0 + BAR_H_M / 2 + k * BAR_H_M, lay[1], d[0], d[1],
        width / 2 + 0.25, 0.05, BAR_H_M / 2, 'rail');
    }
    for (let k = down; k < 3; k++) {
      const f = 1 - k / 3;
      box(out, a.e + de / 2, (a.y + b.y) / 2 + height * f - BAR_H_M / 2, a.n + dn / 2,
        d[0], d[1], width / 2 + 0.1, 0.05, BAR_H_M / 2, 'rail');
    }
    return out;
  }
  const stock = gate.leaf_stock ?? 'board';
  const leafH = Math.max(0.9, height - 0.05);
  const hingeA = { e: a.e + d[0] * (POST_HALF_M + CLEAR_M), n: a.n + d[1] * (POST_HALF_M + CLEAR_M), y: a.y };
  const hingeB = { e: b.e - d[0] * (POST_HALF_M + CLEAR_M), n: b.n - d[1] * (POST_HALF_M + CLEAR_M), y: b.y };
  if ((gate.leaves ?? 1) >= 2) {
    const sw = Array.isArray(gate.swing_deg) ? gate.swing_deg : [gate.swing_deg ?? 0, gate.swing_deg ?? 0];
    leaf(out, hingeA, d, inward, span / 2 - CLEAR_M, sw[0] ?? 0, leafH, stock);
    leaf(out, hingeB, [-d[0], -d[1]], inward, span / 2 - CLEAR_M, sw[1] ?? 0, leafH, stock);
  } else {
    const fromB = gate.hinge === 'b';
    leaf(out, fromB ? hingeB : hingeA, fromB ? [-d[0], -d[1]] : d, inward, span,
      Number(gate.swing_deg) || 0, leafH, stock);
  }
  return out;
}

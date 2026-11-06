/**
 * fort-gates.js — Fort Dearborn's gates, hung so a visitor can work them (T-3319).
 *
 * The owner, 2026-11-02: *"you should be able to enter the fort in both 1812 and 1835,
 * be able to walk through the gate ... the gate by default is closed and you can click
 * on interact"*. Until then each stockade was one solid footprint to the walker, so the
 * whole fort was a block a visitor was pushed out of, and its gates were two shut leaves
 * baked into the picket mesh.
 *
 * So for the stockades named in FORT_GATES this layer:
 *
 *   - reads the stockade's own record (footprint, gate_sides, gate_width_m,
 *     gate_offset_m, bastions, picket height) exactly as generators/archetypes/
 *     palisade.py builds it, and hands the walker its WALLS: the curtain with each
 *     gateway cut out, the bastions' returns, and across each gateway a span that blocks
 *     while the gate is shut (walker.js § enclosure). The footprint stays in the array
 *     whole, so nothing grows in the fort and the router and framing read what they did;
 *   - draws each gate's two leaves itself, hinged on the jambs the mesh draws, and the
 *     buildings layer leaves out the baked shut leaves of these records only
 *     (`drawsLeaves`, read in buildings.js) — the `dark` primitive, which on a palisade
 *     is the leaves and nothing else (tools/measure_fort_gates.py reads the same one);
 *   - offers each gate to interact.js as a thing with two states, `closed` (where every
 *     gate starts) and `open`, and one action from each: a swing of the two leaves
 *     inward through 90 degrees.
 *
 * What is ours, and claimed at docs/LIBERTIES.md L-t3319-fort-gate-leaves: the leaves'
 * planking, ledges and brace, that they swing inward, how far and how fast. The sources
 * say "large gates" (Kinzie, of the second fort) and "Main Gate" (Whistler's index no. 7,
 * of the first) and nothing about how they hung.
 *
 * T-3407 — A GARDEN'S WICKET. The commanding officer's garden south of the first fort
 * (Whistler's "Comm'g Officers Garden") is a five-foot paling whose draught brings a
 * walk in at the middle of its north side. Its record's `gate_kind` is `wicket`: the
 * palisade bakes two posts and nothing between them, and this layer hangs ONE leaf of
 * the fence's own pales on two rails with a brace, on the west post, opening inward into
 * the garden. The owner, 2026-11-06: *"cant seem to enter the garden"*. The leaf and its
 * swing are ours: docs/LIBERTIES.md L-t3407-officers-garden.
 */
import * as THREE from 'three';
import { footprintToWorld } from './walker.js';

/** The stockades whose gates a visitor works, and what each gate is called. Only these:
 * every other palisade (the covered way, the gardens) keeps its baked leaves, shut. */
export const FORT_GATES = Object.freeze({
  // 1835 — the second fort's two gates, north and south (Kinzie; Andreas).
  fort_dearborn_palisade: { n: 'North gate', s: 'South gate' },
  // 1812 — the first fort's main gate, through both rows of pickets (Whistler no. 7).
  first_fort_dearborn_pickets_outer: { s: 'Main gate, outer row' },
  first_fort_dearborn_pickets_inner: { s: 'Main gate, inner row' },
  // 1812 — the commanding officer's garden, its walk in from the fort (T-3407).
  first_fort_outer_officers_garden: { n: 'Garden gate' },
});

/** How far a leaf swings from shut, and how long it takes. Ours (the header). */
export const OPEN_DEG = 90;
export const SWING_S = 1.4;
/** Within this far of a gate's middle, on foot, the Interact key offers it. */
export const GATE_REACH_M = 5;
/** Half the curtain's thickness as the walker keeps off it: a picket and its ribband. */
export const WALL_HALF_M = 0.2;

// palisade.py's own constants, so the leaves meet the frame the mesh draws.
const JAMB_M = 0.20;          // _gate(): `jamb`
const HEAD_FRAC = 0.86;       // _gate(): head = picket_height_m * 0.86
const LEAF_FOOT_M = 0.02;     // the shut leaf's foot and head, as _gate() beamed them
const LEAF_HEAD_GAP_M = 0.05;

/** T-3407: palisade.py's WICKET_POST_HALF_M and WICKET_POST_RISE_M — a wicket's posts
 * stand in the gateway's cut, so its leaf hangs between their inner faces. */
const WICKET_POST_HALF_M = 0.08;
/** The wicket leaf's pales stop this far under the fence's own heads, its foot this far
 * over the ground (a leaf that dragged would not swing). */
const WICKET_HEAD_DROP_M = 0.06;
const WICKET_FOOT_M = 0.07;
/** A wicket swings a little further than a fort's leaf: it is light and stands back
 * against the paling inside. */
const WICKET_OPEN_DEG = 100;

/** Sawn plank weathered dark: the archetype's GATE_RGBA (0.38, 0.31, 0.24) under the
 * weather a gate takes standing out, in linear colour as the GLB carries its own. */
const LEAF_RGB = [0.25, 0.2, 0.155];

/** One of the record's attributes, its value where it is graded ({ value, confidence }). */
function val(sidecar, name, dflt) {
  const attrs = sidecar?.attributes ?? {};
  const graded = attrs[name];
  const v = graded && typeof graded === 'object' && !Array.isArray(graded) ? graded['value'] : graded;
  return v === undefined || v === null ? dflt : v;
}

/** The _confidence value of one attribute's grade (attested 0, inferred 0.5, reconstructed 1). */
function gradeOf(sidecar, name) {
  const attrs = sidecar?.attributes ?? {};
  const grade = attrs[name] && typeof attrs[name] === 'object' ? attrs[name]['confidence'] : null;
  return { attested: 0, inferred: 0.5, reconstructed: 1 }[grade] ?? 0.5;
}

/**
 * T-3320: is this record a fort's parade, whose ground the yards layer lays as
 * trodden earth feathered into the sward (data/enclosures/*parade_ground.json)?
 * The buildings layer then leaves out the archetype's flat 6 cm slab (its `earth`
 * primitive) and keeps the rest (Fergus's sun-dial).
 */
export const PARADE_GROUNDS = Object.freeze({
  first_fort_dearborn_parade: { scene: '1812', id: 'first_fort_dearborn_parade_ground' },
  fort_dearborn_parade: { scene: '1835', id: 'fort_dearborn_parade_ground' },
});

/** The T-3320 ground owner, whose generated record supplies this parade's surface. */
export function paradeGroundOwner(record) {
  const ground = PARADE_GROUNDS[record?.id];
  const kind = record?.sidecar?.attributes?.['kind'];
  return ground && record.sidecar?.id === record.id
    && String(record.sidecar?.scene) === ground.scene
    && (kind && typeof kind === 'object' ? kind['value'] : kind) === 'parade'
    ? ground.id : null;
}

export function paradeLaidAsGround(record) {
  return paradeGroundOwner(record) !== null;
}

/** Does the buildings layer leave this record's baked leaves to this layer? */
export function drawsLeaves(record) {
  return !!record && Object.prototype.hasOwnProperty.call(FORT_GATES, record.id)
    && stockadePlan(record.sidecar).gates.length > 0;
}

/**
 * The stockade as palisade.py builds it, in its footprint frame [u, v] (metres; +u east
 * and +v north at rotation 0): `walls` the curtain and bastion runs as [a, b] segments,
 * and one entry per gate with its middle, the axis along the wall, the inward normal,
 * its half-width and the leaves' foot and head.
 */
export function stockadePlan(sidecar) {
  const fp = sidecar?.footprint;
  const poly = Array.isArray(fp) ? fp : fp?.polygon;
  if (sidecar?.archetype !== 'palisade' || !Array.isArray(poly) || poly.length < 3
      || val(sidecar, 'wall_kind', 'picket_stockade') !== 'picket_stockade') {
    return { w: 0, d: 0, walls: [], gates: [] };
  }
  const us = poly.map((p) => p[0]), vs = poly.map((p) => p[1]);
  const w = Math.max(...us) - Math.min(...us), d = Math.max(...vs) - Math.min(...vs);
  const sides = [].concat(val(sidecar, 'gate_sides', [])).map((s) => String(s).toLowerCase());
  const gw = Number(val(sidecar, 'gate_width_m', 3.6));
  const kind = String(val(sidecar, 'gate_kind', 'gateway'));
  const off = Number(val(sidecar, 'gate_offset_m', 0));
  const height = Number(val(sidecar, 'picket_height_m', 3.7));
  const corners = [].concat(val(sidecar, 'bastion_corners', [])).map((c) => String(c).toLowerCase());
  const L = Number(val(sidecar, 'bastion_length_m', 7.0));
  const P = Number(val(sidecar, 'bastion_projection_m', 3.0));

  // palisade.py _stockade(): each side walked so, its corners at its ends in this order.
  const run = { s: [[0, 0], [w, 0]], e: [[w, 0], [w, d]], n: [[w, d], [0, d]], w: [[0, d], [0, 0]] };
  const cornerAt = { s: ['sw', 'se'], e: ['se', 'ne'], n: ['ne', 'nw'], w: ['nw', 'sw'] };
  // _gate_shift(): gate_offset_m is toward +u (n, s) or +v (e, w); n and w are walked back.
  const shift = (side) => (side === 's' || side === 'e' ? off : -off);
  const lerp = (a, z, t) => [a[0] + (z[0] - a[0]) * t, a[1] + (z[1] - a[1]) * t];
  const walls = [];
  for (const side of ['s', 'e', 'n', 'w']) {
    const [a, z] = run[side];
    const len = Math.hypot(z[0] - a[0], z[1] - a[1]);
    const cuts = [];
    if (sides.includes(side)) {
      const mid = len / 2 + shift(side);
      cuts.push([mid - gw / 2, mid + gw / 2]);
    }
    cornerAt[side].forEach((corner, i) => {
      if (corners.includes(corner)) cuts.push(i === 0 ? [0, L] : [len - L, len]);
    });
    for (const [t0, t1] of keepOutside(len, cuts)) walls.push([lerp(a, z, t0 / len), lerp(a, z, t1 / len)]);
  }
  // _bastion(): out from the wall, along, and back.
  for (const corner of corners) {
    const sx = corner === 'ne' || corner === 'se' ? 1 : -1;
    const sy = corner === 'ne' || corner === 'nw' ? 1 : -1;
    const ox = sx > 0 ? w : 0, oy = sy > 0 ? d : 0;
    const path = [[ox - sx * L, oy], [ox - sx * L, oy + sy * P], [ox + sx * P, oy + sy * P],
      [ox + sx * P, oy - sy * L], [ox, oy - sy * L]];
    for (let i = 1; i < path.length; i += 1) walls.push([path[i - 1], path[i]]);
  }
  // _gate(): the gateway's middle, its run and its inward side.
  const head = height * HEAD_FRAC;
  const gates = sides.map((side) => {
    const ns = side === 'n' || side === 's';
    const centre = ns ? [w / 2 + off, side === 'n' ? d : 0] : [side === 'e' ? w : 0, d / 2 + off];
    const along = ns ? [1, 0] : [0, 1];
    const inward = { s: [0, 1], n: [0, -1], w: [1, 0], e: [-1, 0] }[side];
    if (kind === 'wicket') {
      // One leaf between the posts' inner faces, as tall as the pales less a hand.
      return { side, kind, centre, along, inward, half: gw / 2 - 2 * WICKET_POST_HALF_M,
        foot: WICKET_FOOT_M, head: height - WICKET_HEAD_DROP_M,
        pale: { width: Number(val(sidecar, 'picket_width_m', 0.12)), spacing: Number(val(sidecar, 'picket_spacing_m', 0.2)) } };
    }
    return { side, kind: 'gateway', centre, along, inward, half: gw / 2, foot: LEAF_FOOT_M, head: head - LEAF_HEAD_GAP_M };
  });
  return { w, d, walls, gates };
}

/** [0, len] with every cut removed (palisade.py _intervals). */
function keepOutside(len, cuts) {
  let keep = [[0, len]];
  for (const [c0, c1] of [...cuts].sort((x, y) => x[0] - y[0])) {
    const out = [];
    for (const [k0, k1] of keep) {
      if (c1 <= k0 || c0 >= k1) { out.push([k0, k1]); continue; }
      if (c0 > k0) out.push([k0, Math.min(c0, k1)]);
      if (c1 < k1) out.push([Math.max(c1, k0), k1]);
    }
    keep = out;
  }
  return keep.filter(([a, z]) => z - a > 1e-6);
}

/** The leaves' directions at swing fraction `t` (0 shut, 1 open), in the plan frame:
 * each runs from its hinge toward the gateway's middle when shut and turns inward. */
export function leafDirections(gate, t) {
  const wicket = gate.kind === 'wicket';
  const a = ((wicket ? WICKET_OPEN_DEG : OPEN_DEG) * Math.PI / 180) * Math.max(0, Math.min(1, t));
  const c = Math.cos(a), s = Math.sin(a);
  // A wicket is one leaf, hung on the post at -along and closing across the whole way.
  return (wicket ? [-1] : [-1, 1]).map((side) => {
    const shut = [-side * gate.along[0], -side * gate.along[1]];
    const dir = [c * shut[0] + s * gate.inward[0], c * shut[1] + s * gate.inward[1]];
    const hinge = [gate.centre[0] + side * gate.half * gate.along[0], gate.centre[1] + side * gate.half * gate.along[1]];
    return { hinge, dir, len: wicket ? 2 * gate.half : gate.half };
  });
}

// ---------------------------------------------------------------- leaf mesh

/** Push a six-faced solid onto pos/nrm as flat triangles: `lo` and `hi` are its four
 * bottom and four top corners [x, y, z], in the same order round. Each face is wound
 * away from the solid's middle, so the normals point out whichever way round the
 * corners were given. */
function solid(pos, nrm, lo, hi) {
  const all = [...lo, ...hi];
  const mid = [0, 1, 2].map((k) => all.reduce((acc, p) => acc + p[k], 0) / all.length);
  const quad = (a, b, c, d) => {
    const ab = [b[0] - a[0], b[1] - a[1], b[2] - a[2]], ad = [d[0] - a[0], d[1] - a[1], d[2] - a[2]];
    let n = [ab[1] * ad[2] - ab[2] * ad[1], ab[2] * ad[0] - ab[0] * ad[2], ab[0] * ad[1] - ab[1] * ad[0]];
    const c0 = [0, 1, 2].map((k) => (a[k] + b[k] + c[k] + d[k]) / 4 - mid[k]);
    let order = [a, b, c, a, c, d];
    if (n[0] * c0[0] + n[1] * c0[1] + n[2] * c0[2] < 0) { n = n.map((x) => -x); order = [a, d, c, a, c, b]; }
    const l = Math.hypot(...n) || 1;
    for (const p of order) { pos.push(...p); nrm.push(n[0] / l, n[1] / l, n[2] / l); }
  };
  for (let i = 0; i < 4; i += 1) {
    const j = (i + 1) % 4;
    quad(lo[i], lo[j], hi[j], hi[i]);
  }
  quad(hi[0], hi[1], hi[2], hi[3]);
  quad(lo[0], lo[3], lo[2], lo[1]);
}

/** An axis-aligned box in the leaf's frame. */
function box(pos, nrm, x0, x1, y0, y1, z0, z1) {
  solid(pos, nrm,
    [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]],
    [[x0, y1, z0], [x1, y1, z0], [x1, y1, z1], [x0, y1, z1]]);
}

/**
 * One leaf in its hinge's frame: it runs along +x from the hinge (x = 0) to `len`, its
 * boards from `foot` to `head` in y, and its ledges and brace on the `back` side in z
 * (+1 or -1, the side that faces the fort). Boards butted with a hairline between them,
 * two ledges and a brace rising from the hinge's foot to the free end — the ledged and
 * braced door every carpenter hangs where a leaf must not sag. About 100 triangles.
 */
export function leafGeometry({ len, foot, head, back = 1 }) {
  const pos = [], nrm = [];
  const T = 0.07;                                   // the boards' thickness
  const boards = Math.max(3, Math.round(len / 0.28));
  const pitch = len / boards;
  for (let i = 0; i < boards; i += 1) {
    box(pos, nrm, i * pitch + 0.004, (i + 1) * pitch - 0.004, foot, head, -T / 2, T / 2);
  }
  const zb = [back * T / 2, back * (T / 2 + 0.045)].sort((a, b) => a - b);
  const ledgeH = 0.16;
  const yLow = foot + 0.32, yHigh = head - 0.42 - ledgeH;
  box(pos, nrm, 0.06, len - 0.06, yLow, yLow + ledgeH, zb[0], zb[1]);
  box(pos, nrm, 0.06, len - 0.06, yHigh, yHigh + ledgeH, zb[0], zb[1]);
  // The brace: from the hinge end's lower ledge up to the free end's upper one, a board
  // 0.14 m wide laid flat on the back between them.
  const a = [0.12, yLow + ledgeH], b = [len - 0.12, yHigh];
  const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
  const px = (-dy / l) * 0.07, py = (dx / l) * 0.07;
  const q = [[a[0] - px, a[1] - py], [b[0] - px, b[1] - py], [b[0] + px, b[1] + py], [a[0] + px, a[1] + py]];
  solid(pos, nrm, q.map(([x, y]) => [x, y, zb[0]]), q.map(([x, y]) => [x, y, zb[1]]));

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  geo.computeBoundingSphere();
  return geo;
}

/**
 * T-3407 — a wicket leaf in its hinge's frame, as leafGeometry: +x from the hinge to
 * `len`, up in y from `foot` to `head`, its rails and brace on the `back` side in z.
 * Pales of the fence's own width and pitch, each with its riven point; two rails and a
 * brace from the hinge's foot up to the free end's top rail, the way a light gate is
 * kept from dropping at its latch. Every face carries a UV along its own length (u
 * across, v along), so the grain runs up a pale and along a rail. About 250 triangles.
 */
export function wicketGeometry({ len, foot, head, back = 1, pale = { width: 0.12, spacing: 0.2 } }) {
  const pos = [], nrm = [], uv = [], col = [];
  let n = 0;
  const T = 0.035;                                  // a riven pale's thickness
  const quad = (a, b, c, d, nx, ny, nz, uvs, tone) => {
    for (const [p, t] of [[a, uvs[0]], [b, uvs[1]], [c, uvs[2]], [a, uvs[0]], [c, uvs[2]], [d, uvs[3]]]) {
      pos.push(...p); nrm.push(nx, ny, nz); uv.push(...t); col.push(tone, tone, tone);
    }
    n += 6;
  };
  // An upright with a pointed head: front, back, two sides, and the two slopes of the point.
  const point = Math.min(0.14, (head - foot) * 0.1);
  const count = Math.max(3, Math.round(len / pale.spacing));
  const pitch = len / count;
  const w = Math.min(pale.width, pitch * 0.85) / 2;
  for (let i = 0; i < count; i += 1) {
    const x = (i + 0.5) * pitch;
    const tone = 0.86 + 0.28 * (((i * 2654435761) >>> 0) % 1000) / 1000;
    const top = head - point - (((i * 40503) % 7) * 0.006);
    const u0 = (i * 0.37) % 1;
    for (const z of [-T / 2, T / 2]) {
      const nz = z > 0 ? 1 : -1;
      quad([x - w, foot, z], [x + w, foot, z], [x + w, top, z], [x - w, top, z], 0, 0, nz,
        [[u0, 0], [u0 + 0.12, 0], [u0 + 0.12, 1], [u0, 1]], tone);
      // the point: a triangle each face (written as a degenerate quad)
      quad([x - w, top, z], [x + w, top, z], [x, top + point, z], [x, top + point, z], 0, 0, nz,
        [[u0, 1], [u0 + 0.12, 1], [u0 + 0.06, 1.1], [u0 + 0.06, 1.1]], tone * 1.04);
    }
    for (const sx of [-1, 1]) {
      const xe = x + sx * w;
      quad([xe, foot, -T / 2], [xe, foot, T / 2], [xe, top, T / 2], [xe, top, -T / 2], sx, 0, 0,
        [[u0, 0], [u0 + 0.03, 0], [u0 + 0.03, 1], [u0, 1]], tone * 0.9);
      const l = Math.hypot(w, point) || 1;
      quad([xe, top, -T / 2], [xe, top, T / 2], [x, top + point, T / 2], [x, top + point, -T / 2],
        sx * point / l, w / l, 0, [[u0, 1], [u0 + 0.03, 1], [u0 + 0.03, 1.1], [u0, 1.1]], tone);
    }
  }
  // rails and brace on the back
  const zb = [back * T / 2, back * (T / 2 + 0.04)].sort((a, b) => a - b);
  const bar = (a, b, half, tone) => {
    const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
    const px = (-dy / l) * half, py = (dx / l) * half;
    const c = [[a[0] - px, a[1] - py], [b[0] - px, b[1] - py], [b[0] + px, b[1] + py], [a[0] + px, a[1] + py]];
    const L = l / 1.2;
    for (const z of zb) {
      quad([c[0][0], c[0][1], z], [c[1][0], c[1][1], z], [c[2][0], c[2][1], z], [c[3][0], c[3][1], z], 0, 0, z === zb[1] ? back : -back,
        [[0, 0], [0, L], [0.2, L], [0.2, 0]], tone);
    }
    for (const [e0, e1] of [[0, 1], [3, 2]]) {
      const p0 = c[e0], p1 = c[e1];
      const ex = -(p1[1] - p0[1]), ey = p1[0] - p0[0], el = Math.hypot(ex, ey) || 1;
      const sgn = e0 === 0 ? 1 : -1;
      quad([p0[0], p0[1], zb[0]], [p1[0], p1[1], zb[0]], [p1[0], p1[1], zb[1]], [p0[0], p0[1], zb[1]],
        -sgn * ex / el, -sgn * ey / el, 0, [[0, 0], [0, L], [0.05, L], [0.05, 0]], tone * 0.9);
    }
  };
  const yLow = foot + 0.22, yHigh = head - point - 0.32;
  bar([0.03, yLow], [len - 0.03, yLow], 0.045, 0.8);
  bar([0.03, yHigh], [len - 0.03, yHigh], 0.045, 0.8);
  bar([0.08, yLow + 0.04], [len - 0.1, yHigh - 0.04], 0.04, 0.84);

  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
  geo.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  geo.computeBoundingSphere();
  return geo;
}

/** Weathered split oak, grain running up the pale: a small canvas painted once. Pales
 * that stood out two summers go silver-grey over the brown (the paling's own log tone,
 * HEWN_RGBA, under the weather). */
let wicketMaterial = null;
function wicketMaterialOf() {
  if (wicketMaterial) return wicketMaterial;
  let map = null;
  try {
    const S = 128;
    const cv = typeof OffscreenCanvas !== 'undefined' ? new OffscreenCanvas(S, S * 2)
      : Object.assign(document.createElement('canvas'), { width: S, height: S * 2 });
    const ctx = cv.getContext('2d');
    ctx.fillStyle = 'rgb(100,90,77)';
    ctx.fillRect(0, 0, S, S * 2);
    let seed = 7;
    const r = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    for (let i = 0; i < 90; i += 1) {
      const x = r() * S, k = r();
      ctx.strokeStyle = k < 0.5 ? `rgba(52,45,37,${0.25 + r() * 0.35})` : `rgba(150,142,128,${0.15 + r() * 0.25})`;
      ctx.lineWidth = 0.6 + r() * 1.8;
      ctx.beginPath(); ctx.moveTo(x, 0);
      ctx.bezierCurveTo(x + (r() - 0.5) * 6, S * 0.6, x + (r() - 0.5) * 6, S * 1.4, x + (r() - 0.5) * 4, S * 2);
      ctx.stroke();
    }
    for (let i = 0; i < 6; i += 1) {                // checks where the wood split as it dried
      const x = r() * S, y = r() * S * 2;
      ctx.strokeStyle = 'rgba(40,32,26,0.55)'; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + (r() - 0.5) * 2, y + 12 + r() * 30); ctx.stroke();
    }
    map = new THREE.CanvasTexture(cv);
    map.colorSpace = THREE.SRGBColorSpace;
    map.wrapS = map.wrapT = THREE.RepeatWrapping;
    map.name = 'garden-wicket-grain';
  } catch { map = null; }
  wicketMaterial = new THREE.MeshStandardMaterial({ map, vertexColors: true, roughness: 0.92, metalness: 0,
    side: THREE.DoubleSide });
  wicketMaterial.name = 'garden-wicket';
  return wicketMaterial;
}

// ---------------------------------------------------------------- the layer

/**
 * @param {object} o
 * @param {Map} o.registry              scene-loader's records
 * @param {object} o.buildings          the buildings layer (matrixOf)
 * @param {Array} o.footprints          walker.js footprints — the stockades' entries get `walls`
 * @param {object} [o.confidence]       createConfidenceView
 * @param {string[]} [o.problems]
 */
export function createFortGates({ registry, buildings, footprints = [], confidence = null, problems = [] }) {
  const group = new THREE.Group();
  group.name = 'fort-gates';
  const material = new THREE.MeshStandardMaterial({
    color: new THREE.Color().setRGB(...LEAF_RGB), roughness: 0.9, metalness: 0,
  });
  if (confidence?.patch) confidence.patch(material);
  const gates = [];

  for (const id of Object.keys(FORT_GATES)) {
    const record = registry.get(id);
    if (!record) continue;                            // not in this year's scene
    const plan = stockadePlan(record.sidecar);
    const m = buildings?.matrixOf?.(id);
    const obstacle = footprints.find((f) => f.id === id);
    if (!m || !obstacle || !plan.gates.length) {
      problems.push(`${id}: a fort gate to hang, but ${!m ? 'its stockade was not drawn' : !obstacle ? 'it has no footprint' : 'its record names no gate'} — the fort stays shut`);
      continue;
    }
    const toWorld = footprintToWorld(record.sidecar.placement);
    const conf = gradeOf(record.sidecar, 'gate_sides');
    // The walls: the curtain and bastions always, each gateway's span while it is shut.
    const walls = plan.walls.map(([a, b]) => ({ a: toWorld(a), b: toWorld(b), half: WALL_HALF_M }));
    obstacle.walls = walls;
    footprints.wallsVersion = (footprints.wallsVersion ?? 0) + 1;   // walker.js re-reads

    const holder = new THREE.Group();
    holder.name = `fort-gates:${id}`;
    holder.matrixAutoUpdate = false;
    holder.matrix.copy(m);
    group.add(holder);

    for (const gate of plan.gates) {
      const name = FORT_GATES[id][gate.side];
      if (!name) continue;
      // The leaves, each on a pivot at its hinge. Plan (x, y) is glTF (x, -z), so a plan
      // direction at angle phi from +x is a turn of phi about +y.
      const wicket = gate.kind === 'wicket';
      const leafMaterial = wicket ? wicketMaterialOf() : material;
      if (wicket && confidence?.patch && !leafMaterial.userData.confidencePatched) {
        confidence.patch(leafMaterial);
        leafMaterial.userData.confidencePatched = true;
      }
      const leaves = leafDirections(gate, 0).map(({ hinge, dir, len }) => {
        const pivot = new THREE.Object3D();
        pivot.position.set(hinge[0], 0, -hinge[1]);
        // The fort's side of the leaf: +z of the pivot is the plan direction turned
        // clockwise; the ledges go on whichever of +z and -z faces the inward normal.
        const cw = [dir[1], -dir[0]];
        const back = cw[0] * gate.inward[0] + cw[1] * gate.inward[1] >= 0 ? 1 : -1;
        const geo = wicket
          ? wicketGeometry({ len: len - 0.012, foot: gate.foot, head: gate.head, back, pale: gate.pale })
          : leafGeometry({ len: gate.half - 0.004, foot: gate.foot, head: gate.head, back });
        const n = geo.getAttribute('position').count;
        geo.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(n).fill(conf), 1));
        const mesh = new THREE.Mesh(geo, leafMaterial);
        mesh.name = `fort-gate-leaf:${id}:${gate.side}`;
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData.structure_id = id;
        pivot.add(mesh);
        holder.add(pivot);
        return pivot;
      });
      holder.updateMatrixWorld(true);

      const thing = {
        id: `${id}:${gate.side}`,
        kind: 'gate',
        structureId: id,
        name,
        states: ['closed', 'open'],
        state: 'closed',
        at: toWorld(gate.centre),
        reach: GATE_REACH_M,
        swing: 0,
        actions: {
          closed: [{ id: 'open', label: 'Open gate', to: 'open',
            steps: [{ label: 'Opening', seconds: SWING_S, run: (t) => setSwing(t) }] }],
          open: [{ id: 'close', label: 'Close gate', to: 'closed',
            steps: [{ label: 'Closing', seconds: SWING_S, run: (t) => setSwing(1 - t) }] }],
        },
      };
      function setSwing(t) {
        thing.swing = t;
        // Eased so the leaf starts and stops like a weight on a hinge, not a wiper.
        const eased = t * t * (3 - 2 * t);
        leafDirections(gate, eased).forEach(({ dir }, i) => {
          leaves[i].rotation.y = Math.atan2(dir[1], dir[0]);
        });
        holder.updateMatrixWorld(true);
      }
      setSwing(0);
      // The gateway's span stands across the way unless the gate is open and still.
      walls.push({ a: toWorld([gate.centre[0] - gate.half * gate.along[0], gate.centre[1] - gate.half * gate.along[1]]),
        b: toWorld([gate.centre[0] + gate.half * gate.along[0], gate.centre[1] + gate.half * gate.along[1]]),
        half: 0.06, gate: thing.id, blocks: () => !(thing.state === 'open' && !thing.running) });
      // And open, each leaf is a board standing out from its jamb.
      for (const { hinge, dir, len } of leafDirections(gate, 1)) {
        walls.push({ a: toWorld(hinge), b: toWorld([hinge[0] + dir[0] * len, hinge[1] + dir[1] * len]),
          half: 0.06, gate: thing.id, blocks: () => thing.state === 'open' && !thing.running });
      }
      gates.push(thing);
    }
  }

  return {
    group,
    gates,
    dispose() {
      group.traverse((o) => { if (o.isMesh) o.geometry.dispose(); });
      material.dispose();
    },
  };
}

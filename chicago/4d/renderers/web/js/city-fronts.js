/**
 * city-fronts.js — T-3686: the 1871 city's fronts, and their full detail around
 * the jaunt stops.
 *
 * Two halves, one look.
 *
 *  * The COLOUR of a front (`facadeTint`): brick, cream stone ("Athens marble",
 *    Joliet and Lemont stone), painted brick or painted weatherboard. The cheap
 *    instanced stand-in (city-context.js) and the detail built here wear the same
 *    tint, so a front keeps its colour as it crosses the ring's edge.
 *  * The DETAIL (`buildFronts`): within `radius_m` of a ring in
 *    data/context/1871/detail-rings.json, each street front is built over its
 *    stand-in from the kit's own wall textures (the 1835 brick and white-lead
 *    clapboard, the 1904 Lemont limestone, the 1835 brick under paint) and a
 *    parts atlas: cast-iron storefronts with plate glass and a door in every
 *    shop, painted signboards and awnings, window openings with sills, hoods
 *    and keystones, string courses, a bracketed cornice; houses get their door,
 *    and where a front yard was laid out, a picket fence with a gate on the
 *    1835 town's dimensions (gates.js). Proportions follow the 1904 kit: K10
 *    cornices, K09 hoods and keystones, K06 sills, K07 doors and steps.
 *
 * Everything here is reconstructed (L-1871-city-baseline, Fronts): generic period fronts on
 * generated lots, never a record of a particular building. T-3803: inside the rings
 * each shop's signs are the firm Edwards' 1871 directory lists at the number its
 * place on the block face falls on, or a trade of that street, lettered at runtime
 * by city-signs-1871.js (L-1871-directory-signs); the kit's trade boards are the
 * fallback when that file or the lettering is missing.
 *
 * Cost. The detail is merged per 100 m cell and per material (five draws a
 * cell at most) and shown only within `show_m` of the camera; the stand-ins
 * beneath keep drawing, so a hidden cell costs nothing but its memory.
 */
import * as THREE from 'three';
import { gateBoxes } from './gates.js';

/** Atlas rows of the kit's facade families (city_context_emit.py). */
export const FAMILY_ROW = { brick: 0, timber: 1, stone: 2, weathered: 3 };
/** Which atlas row a front's facade wears: painted brick is the stone row, tinted. */
export const FACADE_ROW = { brick: 0, frame: 1, stone: 2, painted: 2 };

// Reconstructed palettes (L-1871-city-baseline, Fronts). Multipliers over the atlas row.
// Stone: the cream and buff of new-cut Athens marble and Joliet stone.
const STONE_TINT = [[1.02, 1.01, .99], [1, .99, .95], [.98, .97, .95], [1.02, .99, .92], [.96, .95, .92], [1.01, .98, .9]];
// Painted brick: stone colour, cream, buff, drab, grey, olive drab, brown.
const PAINTED_TINT = [[1.08, 1.06, 1.02], [1.08, 1.03, .9], [1.02, .95, .8], [.9, .86, .76], [.9, .9, .9], [.86, .86, .74], [.78, .68, .58]];
// Brick: red, brown and salmon kilns.
const BRICK_TINT = [[1, 1, 1], [1.05, 1.02, .98], [.92, .88, .88], [1.04, .97, .9], [.88, .82, .8], [1.08, 1.06, 1.02]];
// T-3683: a frame house's paint over the pale weatherboard: mostly white,
// some buff, grey or drab, a few unpainted or barn red.
export const FRAME_PAINT = [[.98, .97, .94], [.98, .97, .94], [.96, .95, .91], [.98, .97, .94], [.95, .94, .90],
  [.97, .88, .70], [.83, .83, .81], [.80, .76, .64], [.76, .80, .72], [.62, .55, .45], [.66, .58, .48], [.72, .50, .40]];
const AWNING_TINT = [[1, 1, 1], [1, .96, .9], [.86, .9, .84], [1, .92, .82]];

export const jitterOf = (e, n) => ((Math.sin(e * 12.9898 + n * 78.233) * 43758.5453) % 1 + 1) % 1;
const hash = (s) => { let h = 2166136261; for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619); return h >>> 0; };

/** The facade a placement wears: its row's own, else its template family's. */
export function facadeOf(facade, material) {
  if (facade) return facade;
  return material === 'stone' ? 'stone' : material === 'brick' ? 'brick' : 'frame';
}

/** The tint of a front over its atlas row, shared by stand-in and detail. */
export function facadeTint(facade, tone, jitter, out = [1, 1, 1]) {
  const t = Number(tone) || 0;
  let base, k;
  if (facade === 'stone') { base = STONE_TINT[t % STONE_TINT.length]; k = .96 + .06 * jitter; }
  else if (facade === 'painted') { base = PAINTED_TINT[t % PAINTED_TINT.length]; k = .95 + .06 * jitter; }
  else if (facade === 'brick') { base = BRICK_TINT[t % BRICK_TINT.length]; k = .9 + .12 * jitter; }
  else { base = FRAME_PAINT[t % FRAME_PAINT.length]; k = .95 + .05 * jitter; }
  out[0] = base[0] * k; out[1] = base[1] * k; out[2] = base[2] * k;
  return out;
}

const WALL_OF = { brick: 'brick', stone: 'stone', painted: 'painted', frame: 'clapboard' };
const HOUSE_FLOOR = { brick_rowhouse: 1.36, brick_mansard: 1.19, villa_hip: 1.02, brick_cottage: .51,
  timber_cottage: .34, timber_house: .51, timber_hip: .51 };
const PORCH = new Set(['timber_house', 'timber_hip', 'timber_cottage']);
// 1835 dooryard pickets (enclosures.js / gates.js): pale 0.075 m on a 0.17 m pitch.
const PALE_PITCH_M = .17, PALE_W_M = .075, FENCE_H_M = 1.1, POST_PITCH_M = 2.4, GATE_W_M = 1.07;

/** Distance from (e, n) to a ring's point or polyline. */
function ringDistance(ring, e, n) {
  const p = ring.points;
  if (p.length === 1) return Math.hypot(e - p[0][0], n - p[0][1]);
  let best = Infinity;
  for (let i = 0; i + 1 < p.length; i++) {
    const [ax, ay] = p[i], [bx, by] = p[i + 1];
    const dx = bx - ax, dy = by - ay, L = dx * dx + dy * dy;
    const t = L ? Math.max(0, Math.min(1, ((e - ax) * dx + (n - ay) * dy) / L)) : 0;
    best = Math.min(best, Math.hypot(e - ax - t * dx, n - ay - t * dy));
  }
  return best;
}

class Buffer {
  constructor() { this.p = []; this.n = []; this.uv = []; this.c = []; this.i = []; }
  get vertices() { return this.p.length / 3; }
  /** A quad (or triangle) wound to face `normal`; uvs follow the points. */
  poly(points, uvs, normal, color) {
    const [a, b, c] = points;
    const ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
    const vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    if (nx * normal[0] + ny * normal[1] + nz * normal[2] < 0) { points = [...points].reverse(); uvs = [...uvs].reverse(); }
    const base = this.vertices;
    for (let k = 0; k < points.length; k++) {
      this.p.push(points[k][0], points[k][1], points[k][2]);
      this.n.push(normal[0], normal[1], normal[2]);
      this.uv.push(uvs[k][0], uvs[k][1]);
      this.c.push(color[0], color[1], color[2]);
    }
    for (let k = 1; k + 1 < points.length; k++) this.i.push(base, base + k, base + k + 1);
  }
  geometry() {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(this.p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(this.n, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(this.uv, 2));
    g.setAttribute('color', new THREE.Float32BufferAttribute(this.c, 3));
    g.setAttribute('_confidence', new THREE.Float32BufferAttribute(new Float32Array(this.vertices).fill(1), 1));
    g.setIndex(this.vertices > 65535 ? new THREE.Uint32BufferAttribute(this.i, 1) : new THREE.Uint16BufferAttribute(this.i, 1));
    g.computeBoundingSphere(); g.computeBoundingBox();
    return g;
  }
}

/** Is a placement a shop or house front inside the rings at this tier? */
function ringKind(r, rings, radius, value) {
  if (r.isTree) return null;
  const t = r.t;
  const shop = !!t.shop || value(r.row, 'row', null) === 'attached';
  const house = !shop && HOUSE_FLOOR[t.id] != null;
  if (!shop && !house) return null;
  let near = Infinity;
  for (const ring of rings.rings ?? []) near = Math.min(near, ringDistance(ring, r.e, r.n));
  if (near > radius) return null;
  return { shop, near };
}

/** A shop front's storefront and storey heights, shared by the fronts and their signs. */
function shopDims(r) {
  const storeys = Math.max(1, r.t.storeys ?? 2);
  const gf = Math.min(4.6, Math.max(3.6, r.h / storeys * 1.2));
  const bays = Math.max(2, Math.round(r.w / 2.9));
  const sh = storeys > 1 ? (r.h - gf - .62) / (storeys - 1) : 0;
  const h0 = hash(String(r.id));
  return { storeys, gf, bays, bw: r.w / bays, sh, h0, awning: h0 % 10 < 6 };
}

export const cellKeyOf = (e, n, cellM = 100) => `${Math.floor(e / cellM)},${Math.floor(n / cellM)}`;

/**
 * T-3803: the shop fronts the rings build at this tier, as the sign planner wants
 * them — the front's centre and outward direction in local e/n, its size, and the
 * heights of the bands its signs can take.
 */
export function shopFrames({ rows, rings, detail = 'full', value }) {
  const radius = rings.radius_m?.[detail] ?? 200;
  const out = [];
  for (const r of rows) {
    const k = ringKind(r, rings, radius, value);
    if (!k?.shop) continue;
    const d = shopDims(r), c = r.cos, s = r.sin;
    // The front's centre: local x = 0, z = -d/2 (P() below), and OUT = (-s, c) in e/n.
    const centre = [r.e + s * (-r.d / 2), r.n - c * (-r.d / 2)];
    out.push({ r, w: r.w, h: r.h, gf: d.gf, storeys: d.storeys, bays: d.bays, bw: d.bw, awning: d.awning,
      bandH: d.storeys > 1 ? d.sh * .2 - .2 : 0, upperH: d.storeys > 2 ? d.sh * .48 - .35 : 0,
      out: [-s, c], centre, focus: k.near < 70, cell: cellKeyOf(r.e, r.n) });
  }
  return out;
}

/**
 * Build the detail cells. `rows` are city-context placements ({e, n, w, d, h,
 * base, cos, sin, t, row}); `fronts` is kit.json's `fronts` section; `materials`
 * maps its material names to the loaded kit materials.
 */
export function buildFronts({ rows, rings, fronts, materials, detail = 'full', value, signs = null }) {
  const radius = rings.radius_m?.[detail] ?? 200;
  const cellM = 100;
  const cells = new Map();
  const census = { buildings: 0, houses: 0, shops: 0, fences: 0, gates: 0, triangles: 0, cells: 0 };
  const atlasCells = fronts.atlas_cells ?? 4;
  const inset = 1.5 / 1024;
  const cellUv = (name, top = 0, bottom = 1) => {
    const [col, row] = fronts.cells[name];
    return [(col + inset * atlasCells) / atlasCells, (row + top + inset * atlasCells) / atlasCells,
      (col + 1 - inset * atlasCells) / atlasCells, (row + bottom - inset * atlasCells) / atlasCells];
  };
  const match = name => fronts.materials[name]?.match ?? [1, 1, 1];
  // T-3804: the light tier keeps every form and spends fewer triangles on the iron and dormers.
  const lite = detail === 'light';
  const tint = [1, 1, 1];

  for (const r of rows) {
    const k = ringKind(r, rings, radius, value);
    if (!k) continue;
    const t = r.t, kind = t.id, shop = k.shop;
    const key = cellKeyOf(r.e, r.n, cellM);
    if (!cells.has(key)) cells.set(key, { e: (Math.floor(r.e / cellM) + .5) * cellM, n: (Math.floor(r.n / cellM) + .5) * cellM, buffers: {} });
    const cell = cells.get(key);
    const buf = name => cell.buffers[name] ??= new Buffer();

    // Front frame: a runs left to right as the street sees the front, y up,
    // o outward from the stand-in's face. Local x = w/2 - a, z = -d/2 - o.
    const { w, d, h, base } = r, c = r.cos, s = r.sin;
    const P = (a, y, o) => {
      const x = w / 2 - a, z = -d / 2 - o;
      return [r.e + c * x + s * z, base + y, -(r.n + s * x - c * z)];
    };
    const OUT = [-s, 0, -c], RIGHT = [-c, 0, s], UP = [0, 1, 0];
    const neg = v => [-v[0], -v[1], -v[2]];
    const facade = facadeOf(value(r.row, 'facade', null), t.material);
    const wall = WALL_OF[facade];
    const span = fronts.materials[wall]?.span_m ?? 4;
    const jitter = jitterOf(r.e, r.n);
    facadeTint(facade, value(r.row, 'tone', 0), jitter, tint);
    const m = match(wall);
    const wallColor = [tint[0] * m[0], tint[1] * m[1], tint[2] * m[2]];
    // Trim and cast iron are painted to the front's own stone or paint colour;
    // a brick front's are cream stone.
    const trimColor = facade === 'brick' ? [1, .97, .9] : facade === 'frame' ? [tint[0], tint[1], tint[2]] : [tint[0] * 1.05, tint[1] * 1.04, tint[2] * 1.02];
    const WHITE = [1, 1, 1];
    const wallQuad = (a0, a1, y0, y1, o) => {
      if (a1 - a0 < .01 || y1 - y0 < .01) return;
      buf(wall).poly([P(a0, y0, o), P(a1, y0, o), P(a1, y1, o), P(a0, y1, o)],
        [[a0 / span, -y0 / span], [a1 / span, -y0 / span], [a1 / span, -y1 / span], [a0 / span, -y1 / span]], OUT, wallColor);
    };
    const wallSide = (a, y0, y1, o0, o1, normal) => buf(wall).poly([P(a, y0, o0), P(a, y0, o1), P(a, y1, o1), P(a, y1, o0)],
      [[o0 / span, -y0 / span], [o1 / span, -y0 / span], [o1 / span, -y1 / span], [o0 / span, -y1 / span]], normal, wallColor);
    const part = (name, a0, a1, y0, y1, o, color = WHITE, uv = cellUv(name)) => {
      buf(name.startsWith('sign') ? name : 'parts').poly([P(a0, y0, o), P(a1, y0, o), P(a1, y1, o), P(a0, y1, o)],
        [[uv[0], uv[3]], [uv[2], uv[3]], [uv[2], uv[1]], [uv[0], uv[1]]], OUT, color);
    };
    // A box in the front frame; `faces` picks front/top/bottom/left/right.
    const box = (name, a0, a1, y0, y1, o0, o1, color, faces = 'ftblr') => {
      const uv = cellUv(name), q = [[uv[0], uv[3]], [uv[2], uv[3]], [uv[2], uv[1]], [uv[0], uv[1]]];
      const b = buf('parts');
      if (faces.includes('f')) b.poly([P(a0, y0, o1), P(a1, y0, o1), P(a1, y1, o1), P(a0, y1, o1)], q, OUT, color);
      if (faces.includes('t')) b.poly([P(a0, y1, o1), P(a1, y1, o1), P(a1, y1, o0), P(a0, y1, o0)], q, UP, color);
      if (faces.includes('b')) b.poly([P(a0, y0, o0), P(a1, y0, o0), P(a1, y0, o1), P(a0, y0, o1)], q, [0, -1, 0], color);
      if (faces.includes('l')) b.poly([P(a0, y0, o0), P(a0, y0, o1), P(a0, y1, o1), P(a0, y1, o0)], q, neg(RIGHT), color);
      if (faces.includes('r')) b.poly([P(a1, y0, o1), P(a1, y0, o0), P(a1, y1, o0), P(a1, y1, o1)], q, RIGHT, color);
    };

    /**
     * One storey's row of openings in a wall plane at `O`: the wall around
     * them, the sash recessed behind, reveals, sill, and a head that is flat
     * (frame), segmental (brick, painted) or round (stone) under its hood.
     */
    const openings = (centres, ww, y0, y1, ys, wh, O, style, doorAt = -1, doorW = 1.1, doorH = 2.4) => {
      const half = ww / 2;
      const rise = style === 'round' ? half : style === 'segmental' ? ww * .2 : 0;
      const yt = ys + wh, crown = yt + rise;
      const spans = centres.map((cx, k) => k === doorAt
        ? { cx, half: doorW / 2, ys: y0 + .02, yt: y0 + doorH, crown: y0 + doorH, rise: 0, door: true }
        : { cx, half, ys, yt, crown, rise, door: false });
      const top = Math.max(...spans.map(o => o.crown));
      const low = Math.min(...spans.map(o => o.ys));
      wallQuad(0, w, y0, low, O);
      wallQuad(0, w, top, y1, O);
      let from = 0;
      for (const o of spans) {
        wallQuad(from, o.cx - o.half, low, top, O);
        wallQuad(o.cx - o.half, o.cx + o.half, low, o.ys, O);
        wallQuad(o.cx - o.half, o.cx + o.half, o.crown, top, O);
        from = o.cx + o.half;
        const inner = .045;
        // Reveals: the wall's thickness at the jambs and sill.
        wallSide(o.cx - o.half, o.ys, o.yt, inner, O, RIGHT);
        wallSide(o.cx + o.half, o.ys, o.yt, inner, O, neg(RIGHT));
        if (o.door) {
          part('house_door', o.cx - o.half, o.cx + o.half, o.ys, o.yt, inner);
          box('trim', o.cx - o.half - .12, o.cx + o.half + .12, o.yt, o.yt + .2, O, O + .1, trimColor, 'ftb');
          continue;
        }
        part('sash', o.cx - o.half, o.cx + o.half, o.ys, o.crown, inner);
        buf(wall).poly([P(o.cx - o.half, o.ys, inner), P(o.cx + o.half, o.ys, inner), P(o.cx + o.half, o.ys, O), P(o.cx - o.half, o.ys, O)],
          [[0, 0], [ww / span, 0], [ww / span, O / span], [0, O / span]], UP, wallColor);
        box('trim', o.cx - o.half - .08, o.cx + o.half + .08, o.ys - .1, o.ys, O, O + .06, trimColor, 'ftb');
        if (!o.rise) {
          if (style === 'hood') {
            // T-3804: a corniced hood on two consoles (McVicker's, the Tribune's neighbours).
            box('trim', o.cx - o.half - .2, o.cx + o.half + .2, o.yt + .1, o.yt + .34, O, O + .17, trimColor, 'ftb');
            box('trim', o.cx - o.half - .08, o.cx + o.half + .08, o.yt, o.yt + .1, O, O + .07, trimColor, 'f');
            for (const a of [o.cx - o.half - .13, o.cx + o.half + .13]) box('trim', a - .05, a + .05, o.yt - .3, o.yt + .1, O, O + .13, trimColor, 'flr');
            continue;
          }
          // A flat head: a plain cap (frame) or a stone lintel.
          box('trim', o.cx - o.half - .1, o.cx + o.half + .1, o.yt, o.yt + .2, O, O + .08, trimColor, 'ftb');
          continue;
        }
        // The arched head: wall spandrels fill the corners above the arc, and
        // a hood (K09: 0.26 m deep, 0.12 m proud) follows the arc over it.
        const R = (o.half * o.half + o.rise * o.rise) / (2 * o.rise), yc = o.yt + o.rise - R;
        const phi = Math.asin(Math.min(1, o.half / R)), K = 6, arc = [], hood = [];
        for (let k = 0; k <= K; k++) {
          const f = -phi + 2 * phi * k / K;
          arc.push([o.cx + R * Math.sin(f), yc + R * Math.cos(f)]);
          hood.push([o.cx + (R + .2) * Math.sin(f), yc + (R + .2) * Math.cos(f)]);
        }
        for (let k = 0; k < K; k++) {
          const corner = k < K / 2 ? [o.cx - o.half, o.crown] : [o.cx + o.half, o.crown];
          const tri = [corner, arc[k], arc[k + 1]];
          buf(wall).poly(tri.map(([a, y]) => P(a, y, O)), tri.map(([a, y]) => [a / span, -y / span]), OUT, wallColor);
          const q = [arc[k], arc[k + 1], hood[k + 1], hood[k]];
          const uv = cellUv('trim');
          buf('parts').poly(q.map(([a, y]) => P(a, y, O + .12)), [[uv[0], uv[3]], [uv[2], uv[3]], [uv[2], uv[1]], [uv[0], uv[1]]], OUT, trimColor);
          const qt = [hood[k], hood[k + 1]];
          const da = (qt[0][0] + qt[1][0]) / 2 - o.cx, dy = (qt[0][1] + qt[1][1]) / 2 - yc, dl = Math.hypot(da, dy) || 1;
          const radial = [RIGHT[0] * da / dl, dy / dl, RIGHT[2] * da / dl];
          buf('parts').poly([P(qt[0][0], qt[0][1], O), P(qt[1][0], qt[1][1], O), P(qt[1][0], qt[1][1], O + .12), P(qt[0][0], qt[0][1], O + .12)],
            [[uv[0], uv[3]], [uv[2], uv[3]], [uv[2], uv[1]], [uv[0], uv[1]]], radial, trimColor);
        }
        if (style === 'round') box('trim', o.cx - .1, o.cx + .1, o.crown - .06, o.crown + .3, O, O + .16, trimColor, 'ftlr');
      }
      wallQuad(from, w, low, top, O);
    };

    // T-3804: an iron railing from a0 to a1 at height y, `o` out: rails and posts.
    const balcony = (a0, a1, y, o, color) => {
      for (const yr of [y + .12, y + .55, y + 1]) box('iron', a0, a1, yr, yr + .05, o - .04, o, color, 'ftb');
      for (let a = a0; a <= a1 + 1e-6; a += lite ? 1.8 : .9) box('iron', a - .025, a + .025, y, y + 1.05, o - .045, o, color, 'flr');
    };
    // T-3804: a slated mansard over the front's whole depth, its dormers on the bays.
    const mansard = (y0, color, bays, bw) => {
      const slate = [.4, .41, .45], rise = 2.9, inset = 1.5, of = .16, ob = -d;
      const uv = cellUv('trim'), q = [[uv[0], uv[3]], [uv[2], uv[3]], [uv[2], uv[1]], [uv[0], uv[1]]];
      const y1 = y0 + rise, fT = of - inset, bT = ob + inset;
      const nf = [OUT[0] * rise, inset, OUT[2] * rise], Lf = Math.hypot(...nf);
      buf('parts').poly([P(0, y0, of), P(w, y0, of), P(w, y1, fT), P(0, y1, fT)], q, nf.map(v => v / Lf), slate);
      buf('parts').poly([P(0, y0, ob), P(w, y0, ob), P(w, y1, bT), P(0, y1, bT)], q, nf.map((v, i) => i === 1 ? v / Lf : -v / Lf), slate.map(v => v * .9));
      buf('parts').poly([P(0, y1, fT), P(w, y1, fT), P(w, y1, bT), P(0, y1, bT)], q, UP, slate.map(v => v * .85));
      for (const [a, nrm] of [[0, neg(RIGHT)], [w, RIGHT]]) {
        buf('parts').poly([P(a, y0, of), P(a, y1, fT), P(a, y1, bT), P(a, y0, ob)], [q[0], q[3], q[2], q[1]], nrm, slate.map(v => v * .95));
      }
      box('cornice', -.04, w + .04, y1 - .05, y1 + .12, fT - .1, fT + .1, color, 'ftb');
      for (let k = 0; k < bays; k++) {
        const cx = (k + .5) * bw, dw = Math.min(.95, bw * .4);
        // The dormer's face stands on the slope's foot; its cheeks run back into the slate.
        const yb = y0 + .35, yt = y0 + 2.05, oF = of - .25;
        wallQuad(cx - dw / 2 - .12, cx + dw / 2 + .12, yb, yt, oF);
        part('sash', cx - dw / 2, cx + dw / 2, yb + .2, yt - .2, oF + .02);
        if (!lite) { wallSide(cx - dw / 2 - .12, yb, yt, oF - 1.2, oF, neg(RIGHT)); wallSide(cx + dw / 2 + .12, yb, yt, oF, oF - 1.2, RIGHT); }
        box('trim', cx - dw / 2 - .25, cx + dw / 2 + .25, yt, yt + .2, oF - 1.2, oF + .12, color, 'ftb');
      }
    };
    if (shop) {
      census.shops++;
      const { storeys, gf, bays, bw, h0 } = shopDims(r);
      // T-3804: the front's street style (street_walls.json): window heads, paired windows, a
      // round-headed top storey or an arcaded attic, the ground storey (iron piers, an iron
      // arcade, a colonnade, or a house front over an areaway), the cornice, a mansard, an
      // iron balcony, a belvedere. A front with none keeps the T-3686 rule by its facade.
      const st = r.wall ?? {};
      const awning = st.awning ?? shopDims(r).awning;
      const ground = st.ground ?? 'piers';
      const O = .16;
      const plan = signs?.plans.get(r.id);
      // T-3803: a lettered sign: a quad on its atlas page, `uv` [u0, vTop, u1, vBottom].
      const sign = (sg, a0, a1, y0, y1, o) => {
        if (!sg?.uv) return;
        part(`sign${sg.page}`, a0, a1, y0, y1, o, WHITE, sg.uv);
      };
      const signOf = kind => plan?.signs.find(sg => sg.kind === kind && sg.uv);
      const doorBay = bays >= 3 ? Math.floor(bays / 2) : 0;
      // An arch from x0 to x1 springing at ys with its crown at yc: the fill above the
      // arc up to `top` and an archivolt band along it, `o` out from the wall.
      const arch = (x0, x1, ys, yc, top, o, color, band = .16) => {
        const half = (x1 - x0) / 2, rise = yc - ys, cx = x0 + half;
        if (rise < .05 || half < .1) return;
        const R = (half * half + rise * rise) / (2 * rise), y0c = yc - R, phi = Math.asin(Math.min(1, half / R)), K = lite ? 4 : 6;
        const arc = [], outer = [];
        for (let k = 0; k <= K; k++) {
          const f = -phi + 2 * phi * k / K;
          arc.push([cx + R * Math.sin(f), y0c + R * Math.cos(f)]);
          outer.push([cx + (R + band) * Math.sin(f), y0c + (R + band) * Math.cos(f)]);
        }
        const uv = cellUv('iron'), q = [[uv[0], uv[3]], [uv[2], uv[3]], [uv[2], uv[1]], [uv[0], uv[1]]];
        for (let k = 0; k < K; k++) {
          const tri = [[k < K / 2 ? x0 : x1, top], arc[k], arc[k + 1]];
          buf('parts').poly(tri.map(([a, y]) => P(a, y, o)), q.slice(0, 3), OUT, color);
          buf('parts').poly([arc[k], arc[k + 1], outer[k + 1], outer[k]].map(([a, y]) => P(a, y, o + .03)), q, OUT, color.map(v => v * 1.06));
        }
        // The spandrel strip either side of the crown up to `top`.
        if (top > yc + band) buf('parts').poly([P(x0, yc + band, o), P(x1, yc + band, o), P(x1, top, o), P(x0, top, o)], q, OUT, color);
      };
      if (ground === 'house') {
        // Crosby's west neighbour: no shop, a ground storey of windows and an arched door over an areaway.
        const centres = Array.from({ length: bays }, (_, k) => (k + .5) * bw);
        openings(centres, Math.min(bw * .45, 1.1), 0, gf, .9, gf - 1.6, O, 'round', doorBay, Math.min(1.2, bw * .7), Math.min(3, gf - .5));
        box('trim', 0, w, gf - .14, gf, O, O + .1, trimColor, 'ftb');
        balcony(0, w, 0, O + 1.14, [.2, .2, .2]);
      } else {
        // The storefront: cast-iron piers, plate glass on a panelled bulkhead,
        // a door in every shop, the lintel and a lettered signboard over it.
        for (let k = 0; k <= bays; k++) {
          const a = k * bw;
          box('iron', Math.max(0, a - .17), Math.min(w, a + .17), 0, gf - .7, 0, O + .06, trimColor, 'flr');
        }
        // An arcade (the Lake and Clark Street views): each bay's glass rises into a
        // segmental iron arch under the lintel, the door's bay too, clear of its transom.
        const archRise = ground === 'arcade' ? Math.max(0, Math.min(bw * .3, .75, gf - .7 - Math.min(3.05, gf - .8) - .12)) : 0;
        const glassTop = gf - .7;
        for (let k = 0; k < bays; k++) {
          const a0 = k * bw + .17, a1 = (k + 1) * bw - .17;
          if (k === doorBay) {
            const cx = (k + .5) * bw;
            part('shop_door', cx - .76, cx + .76, 0, Math.min(3.05, gf - .8), .06);
            part('dark', cx - .76, cx + .76, Math.min(3.05, gf - .8), glassTop, .06);
            if (cx - .76 - a0 > .3) part('shop_glass', a0, cx - .76, 0, glassTop, .06);
            if (a1 - cx - .76 > .3) part('shop_glass', cx + .76, a1, 0, glassTop, .06);
          } else part('shop_glass', a0, a1, 0, glassTop, .06);
          if (archRise > .1) arch(a0, a1, glassTop - archRise, glassTop - .02, glassTop, .1, trimColor);
        }
        box('cornice', 0, w, gf - .7, gf, 0, O + .12, trimColor, 'fb');
      }
      const boards = fronts.boards ?? [];
      if (ground === 'house') { /* a house front carries no shop board */ }
      else if (plan) {
        const fascia = signOf('fascia'), fw = Math.min(w - .4, fascia?.wM ?? 0);
        sign(fascia, w / 2 - fw / 2, w / 2 + fw / 2, gf - .66, gf - .05, O + .135);
        // Gilt letters on the glass of the first shop bay that is not the door's.
        const glass = signOf('glass');
        if (glass) {
          const k = doorBay === 0 ? 1 : 0, gw = Math.min(glass.wM, bw - .5), cx = (k + .5) * bw;
          sign(glass, cx - gw / 2, cx + gw / 2, 1.85, 1.85 + glass.hM * gw / glass.wM, .072);
        }
        // Narrow boards on the iron piers either side of the door.
        const pier = signOf('pier');
        if (pier) for (const kk of [doorBay, doorBay + 1]) {
          const a = kk * bw;
          if (a < .3 || a > w - .3) continue;
          sign(pier, a - .14, a + .14, .55, .55 + pier.hM, O + .075);
        }
      } else if (boards.length) {
        const b = boards[h0 % boards.length], sw = Math.min(w - .6, 5.4);
        part('board', w / 2 - sw / 2, w / 2 + sw / 2, gf - .66, gf - .05, O + .13, WHITE, b);
      }
      if (awning && ground !== 'house' && ground !== 'porch') {
        // A canvas awning let down over the walk.
        const uv = cellUv('awning', (h0 >>> 4) & 1 ? 0 : .5, (h0 >>> 4) & 1 ? .5 : 1);
        const col = AWNING_TINT[(h0 >>> 5) % AWNING_TINT.length];
        const yTop = gf - .82, yLow = 2.55, oFar = O + 1.9;
        const q = [P(.1, yLow, oFar), P(w - .1, yLow, oFar), P(w - .1, yTop, O + .13), P(.1, yTop, O + .13)];
        const quv = [[uv[0], uv[3]], [uv[2], uv[3]], [uv[2], uv[1]], [uv[0], uv[1]]];
        const slope = [OUT[0] * (yTop - yLow), 1.77, OUT[2] * (yTop - yLow)], L = Math.hypot(...slope);
        buf('parts').poly(q, quv, slope.map(v => v / L), col);
        buf('parts').poly(q, quv, slope.map(v => -v / L), col.map(v => v * .7));
        buf('parts').poly([P(.1, yLow - .25, oFar), P(w - .1, yLow - .25, oFar), P(w - .1, yLow, oFar), P(.1, yLow, oFar)],
          [[uv[0], uv[1] + .02], [uv[2], uv[1] + .02], [uv[2], uv[1]], [uv[0], uv[1]]], OUT, col);
        const valance = signOf('valance'), vw = Math.min(w - .4, valance?.wM ?? 0);
        sign(valance, w / 2 - vw / 2, w / 2 + vw / 2, yLow - .24, yLow - .02, oFar + .012);
      }
      if (ground === 'porch') {
        // McVicker's: an iron colonnade over the walk carrying a railed balcony at the first floor.
        const oc = O + 2.3, yd = gf - .05;
        box('iron', 0, w, yd - .3, yd, O, oc + .12, trimColor, 'ftblr');
        for (let k = 0; k <= bays; k++) {
          const a = Math.min(w - .12, Math.max(.12, k * bw));
          box('iron', a - .1, a + .1, 0, yd - .3, oc - .1, oc + .1, trimColor, 'flr');
          box('iron', a - .16, a + .16, yd - .48, yd - .3, oc - .16, oc + .16, trimColor, 'fblr');
        }
        balcony(0, w, yd, oc + .1, trimColor);
      }
      // Upper storeys: windows on the bays, hoods by material, string courses.
      const sh = storeys > 1 ? (h - gf - .62) / (storeys - 1) : 0;
      const style = st.heads ?? (facade === 'stone' ? 'round' : facade === 'frame' ? 'flat' : 'segmental');
      const bayCentres = Array.from({ length: bays }, (_, k) => (k + .5) * bw);
      const centres = st.pair ? bayCentres.flatMap(c => [c - bw * .19, c + bw * .19]) : bayCentres;
      const ww = st.pair ? Math.min(bw * .27, .78) : Math.min(bw * .5, 1.2);
      for (let k = 1; k < storeys; k++) {
        const y0 = gf + (k - 1) * sh, y1 = k === storeys - 1 ? h : y0 + sh;
        const top = k === storeys - 1;
        if (top && st.attic) {
          // An arcade of small round-headed attic lights under the cornice.
          const ac = bayCentres.flatMap(c => [c - bw * .25, c, c + bw * .25]), aw = Math.min(bw * .15, .42);
          openings(ac, aw, y0, y1, y0 + sh * .22, Math.max(.6, sh * .3), O, 'round');
        } else {
          const kStyle = top && st.top ? 'round' : style;
          const wh = sh * .5 - (kStyle === 'round' ? ww * .25 : 0);
          openings(centres, ww, y0, y1, y0 + sh * .2, Math.max(.8, wh), O, kStyle);
        }
        if (k > 1 && facade !== 'frame') box('trim', 0, w, y0 - .1, y0 + .08, O, O + .07, trimColor, 'ftb');
      }
      if (storeys === 1) wallQuad(0, w, gf, h, O);
      if (st.balcony && storeys > 1 && ground !== 'porch') {
        // An iron balcony along the first upper storey, on the storefront's cornice.
        box('iron', .1, w - .1, gf - .02, gf + .1, O, O + .95, [.22, .22, .22], 'ftb');
        balcony(.1, w - .1, gf + .1, O + .9, [.2, .2, .2]);
      }
      const band = signOf('band'), upper = signOf('upper'), frieze = signOf('frieze'), hanging = signOf('hanging');
      // A board nailed to the wall stands in front of everything on it: proud of the string
      // courses (0.07), sills (0.06) and hoods (0.12) it crosses, on a dark edge of its own
      // thickness, so the trim never reads over the lettering (the owner, 2026-11-27).
      const wallBoard = (sg, a0, a1, y0, y1) => {
        box('trim', a0 - .03, a1 + .03, y0 - .03, y1 + .03, O, O + .15, [.16, .14, .12], 'ftblr');
        sign(sg, a0, a1, y0, y1, O + .155);
      };
      // A board on the wall between the storefront and the first upper windows.
      if (band && storeys > 1 && !st.balcony && ground !== 'porch') {
        const bh = Math.min(band.hM, sh * .2 - .2), bw2 = band.wM * bh / band.hM;
        wallBoard(band, w / 2 - bw2 / 2, w / 2 + bw2 / 2, gf + .06, gf + .06 + bh);
      }
      // An upstairs office's board between the first and second upper storeys' windows.
      // It clears the first upper windows' arches and hoods and the next storey's sills.
      if (upper && storeys > 2) {
        const rise = style === 'round' ? ww / 2 : style === 'segmental' ? ww * .2 : style === 'hood' ? .34 : 0;
        const crown = gf + sh * .2 + Math.max(.8, sh * .5 - (style === 'round' ? ww * .25 : 0)) + rise;
        const y0 = crown + .4, uh = Math.min(upper.hM, gf + sh * 1.2 - .22 - y0), uw = upper.wM * uh / upper.hM;
        if (uh > .3) wallBoard(upper, w / 2 - uw / 2, w / 2 + uw / 2, y0, y0 + uh);
      }
      // A board hung at right angles to the walk off an iron bracket, above the storefront.
      if (hanging && storeys > 1 && !st.balcony && ground !== 'porch') {
        const a = hanging.at ? w - .35 : .35, y0 = gf + .35, y1 = y0 + hanging.hM, o0 = O + .3, o1 = o0 + hanging.wM;
        const [u0, vt, u1, vb] = hanging.uv, b = buf(`sign${hanging.page}`);
        b.poly([P(a, y0, o1), P(a, y0, o0), P(a, y1, o0), P(a, y1, o1)], [[u0, vb], [u1, vb], [u1, vt], [u0, vt]], RIGHT, WHITE);
        b.poly([P(a, y0, o0), P(a, y0, o1), P(a, y1, o1), P(a, y1, o0)], [[u0, vb], [u1, vb], [u1, vt], [u0, vt]], neg(RIGHT), WHITE);
        box('iron', a - .025, a + .025, y1 + .04, y1 + .1, O, o1 + .08, [.22, .22, .22], 'ftblr');
        box('iron', a - .02, a + .02, y0 - .02, y1 + .06, O, O + .08, [.22, .22, .22], 'flr');
      }
      // K10's bracketed cornice: frieze, brackets on a 0.72 m rhythm, crown. A lettered
      // frieze keeps its brackets to its ends. A heavy cornice (Booksellers' Row, the
      // marble front on Clark) is deeper, on larger brackets; a parapet cornice carries a
      // row of blocks (the St. James).
      const heavy = st.cornice === 'heavy' || st.cornice === 'parapet';
      const fz0 = heavy ? h - .9 : h - .62, bd = heavy ? .62 : .42, bwid = heavy ? .09 : .06;
      box('cornice', 0, w, fz0, h - .12, O, O + .04, trimColor, 'f');
      const zw = Math.min(w - .6, frieze?.wM ?? 0);
      if (frieze) sign(frieze, w / 2 - zw / 2, w / 2 + zw / 2, h - .58, h - .16, O + .048);
      const count = Math.max(2, Math.round(w / (heavy ? .95 : .72)));
      for (let k = 0; k <= count; k++) {
        const a = .15 + (w - .3) * k / count;
        if (frieze && Math.abs(a - w / 2) < zw / 2 + .12) continue;
        box('cornice', a - bwid, a + bwid, fz0 + .02, h - .12, O, O + bd, trimColor, 'flr');
      }
      const crown = heavy ? .34 : .22, reach = heavy ? .85 : .62;
      box('cornice', -.04, w + .04, h - .12, h + crown, 0, O + reach, trimColor, 'ftb');
      if (st.cornice === 'parapet') {
        for (let a = .5; a < w - .3; a += 2.1) box('trim', a - .24, a + .24, h + crown, h + crown + .62, O - .2, O + .3, wallColor, 'ftlr');
      }
      if (st.mansard) mansard(h + crown, trimColor, bays, bw);
      if (st.tower) {
        // McVicker's belvedere: a storey over the middle of the front, its own cornice and flagstaff.
        // `tower` is [e, n, width]: the middle of the building's whole front, which may span rows.
        const [te, tn, tw] = Array.isArray(st.tower) ? st.tower : [r.e, r.n, Math.min(w * .4, 8)];
        const ac = w / 2 - (c * (te - r.e) + s * (tn - r.n));
        const a0 = ac - tw / 2, a1 = ac + tw / 2, y0 = h + crown, y1 = y0 + 4.2, of = O - .5, ob = -Math.min(8, d - 1);
        wallQuad(a0, a1, y0, y1, of);
        wallSide(a0, y0, y1, ob, of, neg(RIGHT)); wallSide(a1, y0, y1, of, ob, RIGHT);
        for (const cx of [ac - tw * .3, ac, ac + tw * .3]) {
          part('sash', cx - .38, cx + .38, y0 + 1, y0 + 2.9, of + .03);
          box('trim', cx - .55, cx + .55, y0 + 2.9, y0 + 3.15, of, of + .14, trimColor, 'ftb');
        }
        box('cornice', a0 - .3, a1 + .3, y1 - .1, y1 + .3, ob - .3, of + .5, trimColor, 'ftblr');
        box('iron', ac - .05, ac + .05, y1 + .3, y1 + 6.5, ob / 2 - .05, ob / 2 + .05, [.3, .28, .25], 'flr');
      }
    } else {
      census.houses++;
      const floor = HOUSE_FLOOR[kind];
      const storeys = Math.max(1, t.storeys ?? 1);
      const bays = Math.max(1, t.front_bays ?? 3), bw = w / bays;
      const O = .1, sh = h / storeys;
      const style = facade === 'stone' ? 'round' : facade === 'frame' ? 'flat' : 'segmental';
      const centres = Array.from({ length: bays }, (_, k) => (k + .5) * bw);
      const doorAt = Math.floor(bays / 2);
      const ww = Math.min(bw * .45, 1.0);
      wallQuad(0, w, .3, floor, O);
      for (let k = 0; k < storeys; k++) {
        const y0 = k === 0 ? floor : k * sh, y1 = k === storeys - 1 ? h : (k + 1) * sh;
        const ys = k === 0 ? floor + .75 : y0 + .75;
        const wh = Math.max(.9, Math.min(y1 - ys - .5 - (style === 'flat' ? 0 : ww * .3), 1.9));
        if (k === 0) {
          // The door stands at the floor, over the kit's own steps or porch.
          const doorH = Math.min(2.4, y1 - floor - .35);
          openings(centres, ww, floor, y1, ys, wh, O, style, doorAt, Math.min(1.1, bw * .8), doorH);
        } else openings(centres, ww, y0, y1, ys, wh, O, style);
      }
      // The front gable's wall over the eave.
      if (t.roof === 'gable' && t.rise_m) {
        const rise = t.rise_m * h / t.eave_m, tri = [[0, h], [w, h], [w / 2, h + rise]];
        buf(wall).poly(tri.map(([a, y]) => P(a, y, O)), tri.map(([a, y]) => [a / span, -y / span]), OUT, wallColor);
      }
      // The front yard's fence, with a gate on the door's line (1835 dooryard
      // pickets, gates.js leaf), and the path from the gate to the steps.
      const yard = +value(r.row, 'yard_m', 0);
      if (yard >= 2) {
        census.fences++;
        const o = yard - .2, cx = centres[doorAt];
        const paint = facade === 'frame' ? [tint[0], tint[1], tint[2]] : FRAME_PAINT[(hash(String(r.id)) >>> 3) % FRAME_PAINT.length];
        const color = paint.map(v => v * .98);
        const a0 = -.8, a1 = w + .8, g0 = cx - GATE_W_M / 2, g1 = cx + GATE_W_M / 2;
        for (let a = a0; a <= a1 + 1e-6; a += POST_PITCH_M) box('boards', a - .06, a + .06, 0, FENCE_H_M + .15, o - .06, o + .06, color, 'ftlr');
        for (const a of [g0, g1]) box('boards', a - .07, a + .07, 0, FENCE_H_M + .2, o - .07, o + .07, color, 'ftlr');
        for (const [r0, r1] of [[a0, g0 - .07], [g1 + .07, a1]]) {
          if (r1 - r0 < .2) continue;
          for (const y of [.25, FENCE_H_M - .2]) box('boards', r0, r1, y, y + .08, o + .04, o + .07, color, 'ft');
          for (let a = r0 + PALE_PITCH_M / 2; a < r1 - PALE_W_M / 2; a += PALE_PITCH_M) {
            box('boards', a - PALE_W_M / 2, a + PALE_W_M / 2, .08, FENCE_H_M, o - .07, o - .05, color, 'ft');
          }
        }
        // The 1835 house gate: one paled leaf, hung on the left post, shut.
        const toEnu = ([X, Y, Z]) => ({ e: X, n: -Z, y: Y });
        const ja = toEnu(P(g0, 0, o)), jb = toEnu(P(g1, 0, o)), into = P(cx, 0, 0);
        for (const bx of gateBoxes({ kind: 'gate', leaves: 1, leaf_stock: 'picket', swing_deg: 0 }, ja, jb, FENCE_H_M, [into[0], -into[2]])) {
          orientedBox(buf('parts'), bx, cellUv('boards'), color);
        }
        census.gates++;
        const step = PORCH.has(kind) ? 1.9 : 1.1;
        const risers = Math.max(2, Math.round(floor / .17));
        const from = step + .3 * (risers - 1);
        if (o - from > .2) {
          const uv = cellUv(facade === 'frame' ? 'boards' : 'flags');
          buf('parts').poly([P(cx - .6, .05, from), P(cx + .6, .05, from), P(cx + .6, .05, o), P(cx - .6, .05, o)],
            [[uv[0], uv[3]], [uv[2], uv[3]], [uv[2], uv[1]], [uv[0], uv[1]]], UP, [.95, .93, .9]);
        }
      }
    }
    census.buildings++;
  }

  const meshes = [];
  for (const cell of cells.values()) {
    cell.meshes = [];
    for (const [name, b] of Object.entries(cell.buffers)) {
      const material = materials.get(name);
      if (!material || !b.vertices) continue;
      const mesh = new THREE.Mesh(b.geometry(), material);
      mesh.name = `context:1871:fronts:${cell.e},${cell.n}:${name}`;
      mesh.receiveShadow = true; mesh.castShadow = false; mesh.visible = false;
      mesh.userData = { contextTier: 'detail', triangles: b.i.length / 3, confidence: 'reconstructed' };
      census.triangles += b.i.length / 3;
      cell.meshes.push(mesh); meshes.push(mesh);
    }
    delete cell.buffers;
  }
  census.cells = cells.size;
  return { cells: [...cells.values()], meshes, census, showM: rings.show_m?.[detail] ?? 300, signPlans: signs?.plans ?? null };
}

/** One gates.js box (world centre, horizontal axis u, half sizes) as six faces. */
function orientedBox(b, box, uv, color) {
  const ux = box.ux, uz = box.uz, L = Math.hypot(ux, uz) || 1;
  const u = [ux / L, 0, uz / L], v = [-uz / L, 0, ux / L], up = [0, 1, 0];
  const at = (su, sy, sv) => [box.cx + u[0] * su * box.halfLen + v[0] * sv * box.halfW,
    box.cy + sy * box.halfH, box.cz + u[2] * su * box.halfLen + v[2] * sv * box.halfW];
  const q = [[uv[0], uv[3]], [uv[2], uv[3]], [uv[2], uv[1]], [uv[0], uv[1]]];
  for (const sv of [-1, 1]) b.poly([at(-1, -1, sv), at(1, -1, sv), at(1, 1, sv), at(-1, 1, sv)], q, v.map(x => x * sv), color);
  b.poly([at(-1, 1, -1), at(1, 1, -1), at(1, 1, 1), at(-1, 1, 1)], q, up, color);
  for (const su of [-1, 1]) b.poly([at(su, -1, -1), at(su, -1, 1), at(su, 1, 1), at(su, 1, -1)], q, u.map(x => x * su), color);
}

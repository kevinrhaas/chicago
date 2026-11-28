// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * horse-railway-1871.js — the 1871 city's horse railways (T-3806).
 *
 * The owner, 2026-11-27: "1871 horse railways: tracks and running horse cars on the State,
 * Madison, Randolph and North Side lines".
 *
 * data/transport/horse_railways_1871.json (tools/lay_horse_railways_1871.py) gives the track
 * centrelines of every line a source names, and the four double-track lines the cars run (State
 * Street, Randolph, Madison, Clark Street north), each a closed run with its headway from Edwards'
 * 1871 timetable.
 *
 * THE TRACK. Two flat strap rails on each centreline, flush with the paving: a dark band (the rail
 * and the stringer it is spiked to) and the bright, wheel-polished head on it. Drawn as ground
 * decals over the roadways (STREET_DECAL_ORDER), merged per CELL_M cell, one draw a cell; the
 * cells near the eye are drawn (every tier: Light keeps them).
 *
 * THE CARS. Built here from simple geometry, one shape for all, painted per company (a light body,
 * a darker dash and lower panel, the company's name on the letter board, the route on the dash):
 * a closed car of the 1860s, its two platforms and dashboards, a clerestory roof with deck lights,
 * seven windows a side, on two axles. A pair of the driven teams' horses (horse-rig.js: their
 * coats, levels and gaits) draws it at a trot, in collars and traces; the driver stands on the
 * front platform with the reins and the conductor on the back one (the people layer's own figures,
 * anonymous). Every car of a line has a place on its run at every moment (its headway apart); the
 * ones within REACH of the eye are built, nearest first, up to CAP. At each end of its run a car
 * stops at the stub, the horses are walked round to the other end, and it goes back through the
 * crossover onto the other track. A car pulls up for the visitor, a team or a rider in its way,
 * and for the car ahead.
 *
 * No car runs outside the hours of service, nor on the night of the fire from ten o'clock on
 * Sunday, nor on the Monday (the file's `hours`, with its sources).
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { loadMeshoptDecoder } from './scene-loader.js';
import { acquireDraftHorse, draftHorseTextureCap } from './draft-horse-assets.js';
import { loadHorseRecipe, applyHorseAppearance } from './horse-appearance.js';
import { attachHorseLods, createHorseGait, loadGaitClip } from './horse-rig.js';
import { STREET_DECAL_ORDER } from './street-surfaces-1871.js';
import { footprintOfPose } from './team-drive.js';
import { overlaps } from './transport-crossings.js';

export const CELL_M = 256;
const TRACK_ORDER = STREET_DECAL_ORDER.crossings + 0.05;
/** How far from the eye a car is built, and how many at once, by detail. */
export const REACH = Object.freeze({ full: 190, balanced: 150, light: 110 });
export const CAP = Object.freeze({ full: 6, balanced: 4, light: 2 });
const TRACK_REACH = Object.freeze({ full: 700, balanced: 550, light: 380 });
const ACCEL_S = 4;
const HOLD_GIVE_UP_S = 25;
const DEG = Math.PI / 180;
const yawOf = (de, dn) => Math.atan2(de, -dn);   // model forward is +z (horseYaw's convention)

// ---- the run -------------------------------------------------------------------------------

/** A polyline's arclength table and a sampler: at(s) → { e, n, de, dn } (unit direction). */
export function pathOf(points, closed = false) {
  const pts = closed ? [...points, points[0]] : points.slice();
  const c = [0];
  for (let i = 1; i < pts.length; i++) c.push(c[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const length = c[c.length - 1];
  let hint = 1;
  const at = (s, out = {}) => {
    s = Math.max(0, Math.min(length, s));
    let i = Math.min(Math.max(1, hint), pts.length - 1);
    while (i > 1 && c[i - 1] > s) i--;
    while (i < pts.length - 1 && c[i] < s) i++;
    hint = i;
    const L = (c[i] - c[i - 1]) || 1e-9, f = (s - c[i - 1]) / L;
    out.e = pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f;
    out.n = pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f;
    out.de = (pts[i][0] - pts[i - 1][0]) / L; out.dn = (pts[i][1] - pts[i - 1][1]) / L;
    return out;
  };
  return { length, at, points: pts };
}

/** Distance along a straight run of `L` m at `v` m/s, accelerating and braking over ACCEL_S. */
export function runDistance(t, L, v) {
  const a = v / ACCEL_S, ta = ACCEL_S, da = a * ta * ta / 2;
  if (L <= 2 * da) { const T = 2 * Math.sqrt(L / a); return t < T / 2 ? a * t * t / 2 : L - a * (T - t) * (T - t) / 2; }
  const cruise = (L - 2 * da) / v, T = 2 * ta + cruise;
  if (t <= ta) return a * t * t / 2;
  if (t <= ta + cruise) return da + v * (t - ta);
  if (t >= T) return L;
  const r = T - t; return L - a * r * r / 2;
}
export const runTime = (L, v) => { const a = v / ACCEL_S, da = a * ACCEL_S * ACCEL_S / 2; return L <= 2 * da ? 2 * Math.sqrt(L / a) : 2 * ACCEL_S + (L - 2 * da) / v; };

/**
 * One line's timetable: car k's place at clock t (s). Returns { s, leg: 'out'|'back', dwell: null |
 * { u (0..1 through the stop), end: 'a'|'b' }, speed }. The run is out (0..cusp) then back
 * (cusp..length); a stop of `dwell_s` at each end.
 */
export function createTimetable(service, car) {
  const v = car.speed_m_s;
  const outL = service.cusp_m[1], backL = service.length_m - outL;
  const tOut = runTime(outL, v), tBack = runTime(backL, v);
  // the round trip is a whole number of headways: the layover at each stub takes up the rest
  const count = Math.max(1, Math.ceil((2 * car.dwell_s + tOut + tBack) / service.headway_s));
  const T = count * service.headway_s, D = (T - tOut - tBack) / 2;
  return {
    period: T, count,
    place(t) {
      let u = ((t % T) + T) % T;
      if (u < D) return { s: 0, leg: 'out', dwell: { u: u / D, end: 'a' }, speed: 0 };
      u -= D;
      if (u < tOut) { const s = runDistance(u, outL, v); return { s, leg: 'out', dwell: null, speed: Math.min(v, (runDistance(u + .1, outL, v) - s) / .1) }; }
      u -= tOut;
      if (u < D) return { s: outL, leg: 'back', dwell: { u: u / D, end: 'b' }, speed: 0 };
      u -= D;
      const s = runDistance(u, backL, v);
      return { s: outL + s, leg: 'back', dwell: null, speed: Math.min(v, (runDistance(u + .1, backL, v) - s) / .1) };
    },
  };
}

/** Whether the cars run at `hour` on `date` (YYYY-MM-DD), by the file's `hours`. */
/** A gait clip's binding in the driven horse spec. The walk's cycle is the spec's `stride_m`
 *  (not `walk_stride_m`): loadGaitClip refuses a clip whose cycle differs from its binding. */
export function gaitBinding(spec, gait) {
  const file = spec?.[`${gait}_clip_file`];
  if (!file) return null;
  return { file, sha256: spec[`${gait}_clip_sha256`], name: spec[`${gait}_clip`], modelSha256: spec.sha256,
    cycle_m: gait === 'walk' ? spec.stride_m : spec[`${gait}_stride_m`] };
}

export function inService(hours, hour, date) {
  if (!Number.isFinite(hour)) return true;
  const [from, to] = hours?.service_hours ?? [5.5, 24];
  if (hour < from || hour >= to) return false;
  const stop = String(hours?.fire_stop ?? '');
  if (stop && date) {
    const [d, hm] = stop.split('T'); const [h, m] = (hm ?? '0:0').split(':').map(Number);
    if (date > d) return false;
    if (date === d && hour >= h + (m || 0) / 60) return false;
  }
  return true;
}

// ---- the track -----------------------------------------------------------------------------

/**
 * The rails as one geometry a cell: for each centreline two rails (± half the gauge plus half a
 * head), each a dark band and a bright head ribbon on it. `height(e, n)` the roadway there.
 */
export function trackGeometries(doc, height, { gradeOf = () => 1 } = {}) {
  const half = doc.gauge_m / 2 + doc.rail.head_m / 2;
  const cells = new Map();
  const dark = new THREE.Color('#2c2822'), bright = new THREE.Color('#857f74');
  const get = key => { if (!cells.has(key)) cells.set(key, { pos: [], col: [], conf: [], band: [], bandCol: [], bandConf: [] }); return cells.get(key); };
  const ribbon = (cell, which, a, b, off, w, y, color, grade) => {
    const de = b[0] - a[0], dn = b[1] - a[1], L = Math.hypot(de, dn);
    if (L < 0.01) return;
    const rx = dn / L, rn = -de / L; // right of a→b
    const p = (q, o) => [q[0] + rx * o, q[1] + rn * o];
    const a0 = p(a, off - w / 2), a1 = p(a, off + w / 2), b0 = p(b, off - w / 2), b1 = p(b, off + w / 2);
    const ya = height(a[0], a[1]) + y, yb = height(b[0], b[1]) + y;
    const arr = which === 'band' ? cell.band : cell.pos, cols = which === 'band' ? cell.bandCol : cell.col, conf = which === 'band' ? cell.bandConf : cell.conf;
    for (const [q, yy] of [[a0, ya], [b1, yb], [b0, yb], [a0, ya], [a1, ya], [b1, yb]]) { // wound to face up
      arr.push(q[0], yy, -q[1]); cols.push(color.r, color.g, color.b); conf.push(grade);
    }
  };
  for (const rail of doc.rails ?? []) {
    const grade = gradeOf(rail);
    const pts = rail.pts;
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i];
      // long segments are cut so a ribbon follows the roadway's height and lands in its cell
      const L = Math.hypot(b[0] - a[0], b[1] - a[1]), steps = Math.max(1, Math.ceil(L / 24));
      for (let k = 0; k < steps; k++) {
        const f0 = k / steps, f1 = (k + 1) / steps;
        const p = [a[0] + (b[0] - a[0]) * f0, a[1] + (b[1] - a[1]) * f0], q = [a[0] + (b[0] - a[0]) * f1, a[1] + (b[1] - a[1]) * f1];
        const cell = get(`${Math.floor((p[0] + q[0]) / 2 / CELL_M)},${Math.floor((p[1] + q[1]) / 2 / CELL_M)}`);
        for (const side of [-1, 1]) {
          ribbon(cell, 'band', p, q, side * half, 0.15, 0.006, dark, grade);
          ribbon(cell, 'head', p, q, side * half, 0.05, 0.008, bright, grade);
        }
      }
    }
  }
  const out = [];
  for (const [key, c] of cells) {
    // the bands first, then the heads over them (one draw, drawn in index order without depth writes)
    const pos = [...c.band, ...c.pos], col = [...c.bandCol, ...c.col], conf = [...c.bandConf, ...c.conf];
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(new Float32Array(pos.length).map((_, i) => (i % 3 === 1 ? 1 : 0)), 3));
    g.setAttribute('_confidence', new THREE.Float32BufferAttribute(conf, 1));
    g.computeBoundingSphere();
    const [i, j] = key.split(',').map(Number);
    out.push({ key, geometry: g, centre: [(i + .5) * CELL_M, (j + .5) * CELL_M], triangles: pos.length / 9 });
  }
  return out;
}

// ---- the car -------------------------------------------------------------------------------

/** The car's shape (x across, y up from the rail, z forward), in the company's colours. */
export function carGeometry(car, livery, gauge_m = 1.435) {
  const parts = [];
  const C = k => new THREE.Color(k);
  const body = C(livery.body), panel = C(livery.panel), trim = C(livery.trim), glass = C('#1a1e21'),
    iron = C('#262422'), roof = C('#5d5a54'), wood = C('#4a3a2a'), brass = C('#8f7a45');
  const box = (w, h, d, x, y, z, color, { ry = 0 } = {}) => {
    const g = new THREE.BoxGeometry(w, h, d);
    if (ry) g.rotateY(ry);
    g.translate(x, y, z); paint(g, color); parts.push(g);
  };
  const cyl = (r, len, x, y, z, color, axis = 'x', seg = 14) => {
    const g = new THREE.CylinderGeometry(r, r, len, seg);
    if (axis === 'x') g.rotateZ(Math.PI / 2); else if (axis === 'z') g.rotateX(Math.PI / 2);
    g.translate(x, y, z); paint(g, color); parts.push(g);
  };
  const paint = (g, color) => {
    const n = g.getAttribute('position').count, a = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) { a[i * 3] = color.r; a[i * 3 + 1] = color.g; a[i * 3 + 2] = color.b; }
    g.setAttribute('color', new THREE.BufferAttribute(a, 3));
    if (g.index) { const ng = g.toNonIndexed(); g.copy(ng); }
  };
  const Lb = car.body_m, P = car.platform_m, W = car.width_m, hw = W / 2;
  const r = car.wheel_d_m / 2, wb = car.wheelbase_m / 2, gx = gauge_m / 2;
  // running gear
  for (const z of [-wb, wb]) {
    for (const x of [-gx, gx]) { cyl(r, .07, x, r, z, iron, 'x', 16); cyl(r * .3, .1, x, r, z, trim, 'x', 8); }
    cyl(.045, gauge_m + .1, 0, r, z, iron, 'x', 6);
    for (const x of [-gx - .1, gx + .1]) box(.1, .22, .34, x, r + .08, z, iron);
  }
  box(W - .16, .14, Lb + .1, 0, .71, 0, trim);                       // sills and floor
  // the body: lower panels, belt rail, window posts and glass, header
  const yLow = .78, yBelt = 1.46, yWin = 1.52, yHead = 2.28, yLetter = 2.34, yEave = 2.6;
  for (const s of [-1, 1]) {
    box(.05, yBelt - yLow, Lb, s * hw, (yLow + yBelt) / 2, 0, panel);
    box(.07, .05, Lb + .02, s * (hw + .01), yBelt + .025, 0, trim);
    box(.06, .12, Lb + .02, s * (hw + .005), yLow + .06, 0, trim);    // the rocker moulding
    const n = car.windows, post = .1, end = .16, ww = (Lb - 2 * end - (n - 1) * post) / n;
    box(.035, yWin - yBelt, Lb, s * (hw - .005), (yBelt + yWin) / 2, 0, body);
    for (let i = 0; i <= n; i++) {
      const z = -Lb / 2 + end + i * (ww + post) - post / 2;
      const w = i === 0 || i === n ? end + post / 2 : post;
      const zc = i === 0 ? -Lb / 2 + w / 2 : i === n ? Lb / 2 - w / 2 : z;
      box(.05, yHead - yWin, w, s * hw, (yWin + yHead) / 2, zc, body);
    }
    for (let i = 0; i < n; i++) {
      const zc = -Lb / 2 + end + i * (ww + post) + ww / 2;
      box(.02, yHead - yWin, ww, s * (hw - .03), (yWin + yHead) / 2, zc, glass);
      box(.04, .035, ww, s * (hw - .01), yWin + (yHead - yWin) * .62, zc, body);   // the sash's meeting rail
    }
    box(.05, yLetter - yHead, Lb, s * hw, (yHead + yLetter) / 2, 0, body);
    box(.05, yEave - yLetter, Lb, s * hw, (yLetter + yEave) / 2, 0, trim);       // under the letter board
    box(.09, .06, Lb + 2 * P * .92, s * (hw + .03), yEave + .03, 0, trim);       // the cornice, out over the hoods
  }
  // the ends: wall, door, two windows
  for (const s of [-1, 1]) {
    const z = s * Lb / 2;
    box(W, yBelt - yLow, .05, 0, (yLow + yBelt) / 2, z, panel);
    box(W, yEave - yBelt, .05, 0, (yBelt + yEave) / 2, z, body);
    box(.62, 1.5, .02, 0, .82 + .75, z + s * .03, wood);                       // the door
    box(.5, .68, .02, 0, 1.9, z + s * .045, glass);                             // its light
    for (const x of [-.72, .72]) box(.42, yHead - yWin, .02, x, (yWin + yHead) / 2, z + s * .03, glass);
  }
  // the roof: a low arch from the eaves to the clerestory, the clerestory's deck lights, its roof
  const RL = Lb + 2 * P * .92, cx = .7, yC = 2.84, yCT = 3.08;
  const arch = (x0, y0, x1, y1, len, color, steps = 3) => {
    for (let k = 0; k < steps; k++) {
      const f0 = k / steps, f1 = (k + 1) / steps;
      const ax = x0 + (x1 - x0) * f0, bx = x0 + (x1 - x0) * f1;
      const ay = y0 + (y1 - y0) * Math.sin(f0 * Math.PI / 2), by = y0 + (y1 - y0) * Math.sin(f1 * Math.PI / 2);
      const g = new THREE.BoxGeometry(Math.hypot(bx - ax, by - ay) + .01, .04, len);
      g.rotateZ(Math.atan2(by - ay, bx - ax)); g.translate((ax + bx) / 2, (ay + by) / 2, 0); paint(g, color); parts.push(g);
    }
  };
  arch(hw + .06, yEave + .06, cx, yC, RL, roof); arch(-hw - .06, yEave + .06, -cx, yC, RL, roof);
  const CL = Lb - .2;
  for (const s of [-1, 1]) {
    box(.04, yCT - yC, CL, s * cx, (yC + yCT) / 2, 0, body);
    for (let i = 0; i < 8; i++) box(.02, .13, .34, s * (cx + .015), (yC + yCT) / 2, -CL / 2 + .3 + i * (CL - .6) / 7, glass);
    // the clerestory's ends sweep down to the hoods
    box(1.42, .04, .9, 0, yC + .1, s * (CL / 2 + .38), roof, {});
  }
  box(1.42, .05, CL + .04, 0, yCT, 0, body);
  arch(cx + .02, yCT, 0, yCT + .1, CL + .04, roof); arch(-cx - .02, yCT, 0, yCT + .1, CL + .04, roof);
  // the platforms: floor, dashboard, step, brake staff, the hood's posts and the end grab rails
  for (const s of [-1, 1]) {
    const z0 = s * Lb / 2, z1 = s * (Lb / 2 + P);
    box(W - .22, .08, P, 0, .68, (z0 + z1) / 2, wood);
    box(W - .26, .86, .04, 0, .72 + .43, z1, panel);                            // the dash
    for (const x of [-1, 1]) box(.04, .86, .36, x * (hw - .15), .72 + .43, z1 - s * .17, panel, { ry: 0 });
    box(W - .2, .04, .05, 0, 1.6, z1, brass);                                    // the dash rail
    for (const x of [-1, 1]) {
      // the step: an iron tread hung on two straps under the platform's side, 0.4 m up
      box(.2, .03, .42, x * (hw - .02), .4, (z0 + z1) / 2, iron);
      for (const dz of [-.18, .18]) box(.025, .26, .03, x * (hw - .1), .53, (z0 + z1) / 2 + dz, iron);
      cyl(.018, 1.9, x * (hw - .1), .72 + .95, z0 + s * .04, brass, 'y', 6);    // the grab rail
    }
    cyl(.016, 1.05, .55, .72 + .52, z1 - s * .22, iron, 'y', 6);                // the brake staff
    cyl(.12, .025, .55, 1.27, z1 - s * .22, iron, 'y', 12);                     // its wheel
    cyl(.035, .3, 0, .62, z1 + s * .12, iron, 'z', 6);                          // the drawbar
  }
  const merged = mergeGeometries(parts.map(g => (g.index ? g.toNonIndexed() : g)), false);
  for (const g of parts) g.dispose();
  merged.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(merged.getAttribute('position').count).fill(1), 1));
  merged.computeBoundingSphere();
  return merged;
}

/** The car's lettering: the company on each letter board, the route on each dash. */
export function letteringGeometry(car) {
  const Lb = car.body_m, P = car.platform_m, hw = car.width_m / 2;
  const quads = [];
  const quad = (x, y, z, w, h, ry, v0, v1) => {
    const g = new THREE.PlaneGeometry(w, h);
    const uv = g.getAttribute('uv');
    for (let i = 0; i < uv.count; i++) uv.setY(i, uv.getY(i) > .5 ? v1 : v0);
    g.rotateY(ry); g.translate(x, y, z); quads.push(g);
  };
  for (const s of [-1, 1]) quad(s * (hw + .028), 2.47, 0, Lb - .3, .2, s * Math.PI / 2, .5, 1);
  for (const s of [-1, 1]) quad(0, 1.28, s * (Lb / 2 + P + .023), car.width_m - .5, .34, s > 0 ? 0 : Math.PI, 0, .5);
  const g = mergeGeometries(quads, false);
  for (const q of quads) q.dispose();
  g.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(g.getAttribute('position').count).fill(1), 1));
  return g;
}

function letteringTexture(company, service, px, doc = globalThis.document) {
  const canvas = doc.createElement('canvas');
  canvas.width = px; canvas.height = px / 4;
  const c = canvas.getContext('2d'), h = canvas.height;
  // top half: the letter board (company); bottom half: the dash (route)
  c.fillStyle = company.livery.trim; c.fillRect(0, 0, px, h / 2);
  c.fillStyle = company.livery.panel; c.fillRect(0, h / 2, px, h / 2);
  c.textAlign = 'center'; c.textBaseline = 'middle';
  c.fillStyle = company.livery.letter;
  c.font = `bold ${Math.round(h * .3)}px Georgia, 'Times New Roman', serif`;
  c.fillText(company.short, px / 2, h * .26, px * .96);
  c.strokeStyle = company.livery.letter; c.lineWidth = Math.max(1, px / 512);
  c.strokeRect(px * .01, h * .04, px * .98, h * .42);
  c.font = `bold ${Math.round(h * .27)}px Georgia, 'Times New Roman', serif`;
  c.fillText(service.board, px / 2, h * .76, px * .9);
  const t = new THREE.CanvasTexture(canvas);
  t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4;
  return t;
}

// ---- the scene binding ---------------------------------------------------------------------

/**
 * Mount the horse railways. `height(e, n)` the roadway (or bridge deck) there; `humans()` the
 * people layer (createActor) or null; `hour()`/`date()` the scene clock; `blockers()` the
 * footprints a car must not drive into ({ print } lists: teams, riders); `visitor()` { e, n } or null.
 */
export async function mountHorseRailway1871({ dataBase, moduleBase = new URL('../', import.meta.url), height,
  humans = () => null, confidence = null, detail = () => 'full', coarse = false, problems = [],
  hour = () => null, date = () => null, hidden = () => false, visitor = () => null, blockers = () => [],
  doc: given = null }) {
  const doc = given ?? await (async () => {
    const r = await fetch(new URL('transport/horse_railways_1871.json', dataBase));
    if (!r.ok) throw Error(`horse railways: HTTP${r.status}`);
    return r.json();
  })();
  const group = new THREE.Group(); group.name = 'horse-railways-1871';
  const ground = (e, n) => { const y = height(e, n); return Number.isFinite(y) ? y : 3.23; };

  // the track
  const sectionGrade = new Map((doc.sections ?? []).map(s => [s.id, s.track_grade]));
  const gradeValue = g => (g === 'attested' ? 0 : g === 'inferred' ? .5 : 1);
  const trackMat = new THREE.MeshStandardMaterial({ name: '1871_horse_railway_track', vertexColors: true, roughness: .6, metalness: .25 });
  trackMat.depthWrite = false;
  confidence?.patch?.(trackMat);
  const cells = trackGeometries(doc, ground, { gradeOf: rail => gradeValue(sectionGrade.get(rail.section)) }).map(cell => {
    const mesh = new THREE.Mesh(cell.geometry, trackMat);
    mesh.name = `horse-railway:track:${cell.key}`;
    mesh.renderOrder = TRACK_ORDER; mesh.receiveShadow = true; mesh.frustumCulled = true;
    mesh.userData = { layer: 'infrastructure', confidence: 'mixed', liberty: doc.liberty, triangles: cell.triangles };
    group.add(mesh);
    return { mesh, centre: cell.centre };
  });

  // the cars
  const car = doc.car, two = !coarse && detail() !== 'light';
  const carGeom = carGeometry(car, { body: '#888', panel: '#666', trim: '#444' }, doc.gauge_m);
  const bodyMats = new Map(), letterMats = new Map(), lettering = letteringGeometry(car);
  const bodyMat = companyId => {
    if (!bodyMats.has(companyId)) {
      const m = new THREE.MeshStandardMaterial({ name: `horse-car:${companyId}`, vertexColors: true, roughness: .62 });
      confidence?.patch?.(m); bodyMats.set(companyId, m);
    }
    return bodyMats.get(companyId);
  };
  // each company's paint: the shape is painted grey; the company's colours are vertex colours of its own copy
  const paintedGeom = new Map();
  const geomFor = companyId => {
    if (paintedGeom.has(companyId)) return paintedGeom.get(companyId);
    const lv = doc.companies[companyId].livery;
    const g = carGeometry(car, lv, doc.gauge_m);
    paintedGeom.set(companyId, g);
    return g;
  };
  carGeom.dispose();
  const letterMat = service => {
    if (!letterMats.has(service.id)) {
      const tex = letteringTexture(doc.companies[service.operator], service, detail() === 'light' || coarse ? 256 : 512);
      const m = new THREE.MeshStandardMaterial({ name: `horse-car-lettering:${service.id}`, map: tex, roughness: .6 });
      confidence?.patch?.(m); letterMats.set(service.id, m);
    }
    return letterMats.get(service.id);
  };
  const strapGeom = new THREE.BoxGeometry(1, 1, 1);
  strapGeom.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(strapGeom.getAttribute('position').count).fill(1), 1));
  const strapMat = new THREE.MeshStandardMaterial({ name: 'horse-car-harness', color: '#2a1d14', roughness: .7 });
  confidence?.patch?.(strapMat);
  const collarGeom = new THREE.TorusGeometry(.3, .065, 8, 18);
  collarGeom.scale(.78, 1.12, 1);
  collarGeom.setAttribute('_confidence', new THREE.BufferAttribute(new Float32Array(collarGeom.getAttribute('position').count).fill(1), 1));
  const collarMat = new THREE.MeshStandardMaterial({ name: 'horse-car-collar', color: '#3a2618', roughness: .55 });
  confidence?.patch?.(collarMat);

  const lines = (doc.services ?? []).map(service => {
    const path = pathOf(service.loop, true);
    const table = createTimetable({ ...service, length_m: path.length }, car);
    const cars = [];
    for (let k = 0; k < table.count; k++) cars.push({ id: `${service.id}:${k}`, k, delay: 0, held: 0, built: null, building: null, place: null, pose: null });
    return { service, path, table, cars, cusp: service.cusp_m[1] };
  });

  // horses: the driven teams' model, leased when the first car is built
  let tools = null;
  const getTools = () => (tools ??= (async () => {
    const r = await fetch(new URL('transport/driven/loops.json', dataBase));
    if (!r.ok) throw Error(`horse railways: loops HTTP${r.status}`);
    const loops = await r.json();
    const spec = loops.horse_models?.current26_walk_v2;
    if (!spec?.walk_clip_file) throw Error('horse railways: the driven horse model is missing');
    const loader = new GLTFLoader(); loader.setMeshoptDecoder(await loadMeshoptDecoder());
    const url = f => new URL(f, moduleBase).href;
    const recipe = await loadHorseRecipe(dataBase, loops.horse_appearance.recipe_file);
    const clip = g => { const b = gaitBinding(spec, g); return b ? loadGaitClip(url(b.file), b) : null; };
    const [walk, trot] = await Promise.all([clip('walk'), clip('trot')]);
    return { spec, loader, recipe, walk, trot, url };
  })().catch(error => { tools = null; throw error; }));

  const people = (role, line) => {
    const layer = humans();
    if (!layer?.createActor) return null;
    const asset = role === 'driver' ? 'billings_august_1904_stable_helper' : 'mahoney_patrick_1835';
    const instance = { id: `horse-car:${line.service.id}:${role}`, contract_version: 1, display: 'shown', scene: '1871',
      appearance: { asset_id: asset }, placement: { local_e: 0, local_n: 0, heading_deg: 0, anchor: 'terrain' },
      behaviour: { state: 'standing' }, animation: { clip: 'idle', loop: true, phase: role === 'driver' ? .1 : .6 },
      lod: { policy: 'auto' }, interaction: { opens: 'none', selectable: false },
      provenance: { grade: 'reconstructed', basis: `The ${role} of a ${doc.companies[line.service.operator].name} car (an anonymous figure; no source names him).`, liberty: doc.liberty } };
    try {
      return layer.createActor(instance, { identity: { kind: 'anonymous', personId: null, person: null, profile: null, role: null } });
    } catch (error) { problems.push(`horse railways: ${role}: ${error.message}`); return null; }
  };

  async function build(line, c) {
    const { service } = line;
    const root = new THREE.Group(); root.name = `horse-car:${c.id}`;
    const body = new THREE.Mesh(geomFor(service.operator), bodyMat(service.operator));
    const letters = new THREE.Mesh(lettering, letterMat(service));
    const shadows = detail() === 'full' && !coarse;
    body.castShadow = shadows; body.receiveShadow = true;
    root.add(body, letters);
    const straps = new THREE.InstancedMesh(strapGeom, strapMat, 8);
    straps.frustumCulled = false; straps.count = 0;
    const out = { root, body, letters, straps, horses: [], leases: [], driver: null, conductor: null, coats: [] };
    group.add(root, straps);
    try {
      const T = await getTools();
      const levels = Object.keys(T.spec.lods ?? {}).filter(l => l === 'far' || !draftHorseTextureCap());
      const n = two ? 2 : 1;
      for (let i = 0; i < n; i++) {
        const leases = await Promise.all([T.spec, ...levels.map(l => T.spec.lods[l])].map(s => acquireDraftHorse({ url: T.url(s.file), sha256: s.sha256,
          materialVariant: T.spec.material_variant, loader: T.loader })));
        out.leases.push(...leases);
        const h = cloneSkinned(leases[0].asset.scene);
        h.name = `horse-car-horse:${c.id}:${i}`;
        h.traverse(m => { if (m.isMesh) { m.frustumCulled = false; m.castShadow = shadows; } });
        const lods = attachHorseLods(h, Object.fromEntries(levels.map((l, j) => [l, leases[j + 1].asset])), { sourceSha256: T.spec.sha256 });
        const coat = applyHorseAppearance(h, { recipe: T.recipe, sourceSha: T.spec.sha256, scene: '1871', row: `horse_car_${service.id}_${c.k % 9}`,
          individual: i === 0 ? 'left' : 'right', confidence });
        // the collar, on the neck (fitted at the rest pose, before the gait runs)
        const bones = {}; h.traverse(b => { if (b.isBone) bones[b.name] = b; });
        h.updateMatrixWorld(true);
        const collar = new THREE.Mesh(collarGeom, collarMat);
        collar.position.set(0, 1.3, .78); collar.rotation.x = -.42;
        h.add(collar); h.updateMatrixWorld(true);
        const neck = bones.horse_neck ?? bones.horse_body;
        if (neck) neck.attach(collar);
        const ride = p => { if (!neck) return () => p.clone(); const local = neck.worldToLocal(h.localToWorld(p.clone())); return () => neck.localToWorld(local.clone()); };
        const hook = { 1: ride(new THREE.Vector3(.27, 1.2, .74)), [-1]: ride(new THREE.Vector3(-.27, 1.2, .74)) };
        const head = bones.horse_head;
        const bit = head ? (() => { const local = head.worldToLocal(h.localToWorld(new THREE.Vector3(0, 1.36, 1.48))); return () => head.localToWorld(local.clone()); })() : null;
        const gait = createHorseGait(h, { walk: T.walk, walkCycle_m: T.spec.stride_m, trot: T.trot, trotCycle_m: T.spec.trot_stride_m, rest: true });
        group.add(h);
        out.horses.push({ root: h, lods, gait, hook, bit, side: n === 2 ? (i === 0 ? -1 : 1) : 0 });
        out.coats.push(coat);
      }
    } catch (error) {
      if (error.message !== 'gone') problems.push(`horse railways: horses: ${error.message}`);
    }
    out.driver = people('driver', line); out.conductor = people('conductor', line);
    for (const p of [out.driver, out.conductor]) if (p) group.add(p.root);
    return out;
  }

  function release(b) {
    if (!b) return;
    for (const h of b.horses) {
      h.gait?.dispose(); h.lods?.dispose();
      const skeletons = new Set(); h.root.traverse(n => { if (n.isSkinnedMesh) skeletons.add(n.skeleton); });
      for (const s of skeletons) s.dispose();
      h.root.removeFromParent();
    }
    for (const coat of b.coats) coat?.dispose?.();
    for (const l of b.leases) l.release();
    for (const p of [b.driver, b.conductor]) { if (p) { p.dispose?.(); p.root?.removeFromParent(); } }
    b.root.removeFromParent(); b.straps.removeFromParent(); b.straps.dispose?.();
  }

  // where a car of `line` stands at loop distance s on `leg`, and which way it faces
  const tmp = {}, tmp2 = {};
  function poseAt(line, place) {
    const { path, cusp } = line;
    const p = path.at(place.s, tmp);
    let de = p.de, dn = p.dn, leave = null;
    if (place.dwell) {
      // at a stub the car faces the way it leaves (after the horses are round) or came in (before)
      const leaving = place.dwell.u >= .5;
      const sLeave = place.dwell.end === 'a' ? 0 : cusp, sCame = place.dwell.end === 'a' ? path.length : cusp;
      const l = path.at(sLeave + .5, tmp2);
      leave = { e: l.de, n: l.dn };
      const q = leaving ? l : path.at(Math.max(0, sCame - .5), tmp2);
      de = q.de; dn = q.dn;
    }
    return { e: p.e, n: p.n, de, dn, yaw: yawOf(de, dn), s: place.s, speed: place.speed, dwell: place.dwell, leave };
  }
  const ENVELOPE = [-car.width_m / 2 - .05, -(car.body_m / 2 + car.platform_m) - .1, car.width_m / 2 + .05, car.horse_ahead_m + 1.4];
  const printOf = (pose, margin = 0) => footprintOfPose({ e: pose.e, n: pose.n, yaw: pose.yaw }, ENVELOPE, margin);

  let clock = 0, running = true, lastHour = null, lastDate = null;
  const held = { why: null };

  /** Is the way ahead of car c (pose) clear? Returns the word for what holds it, or null. */
  function wayClear(line, c, pose) {
    if (!pose || pose.dwell || !(pose.speed > .05)) return null;
    const ahead = line.path.at(Math.min(line.path.length, pose.s + 3), tmp2);
    const aheadPose = { e: ahead.e, n: ahead.n, yaw: yawOf(ahead.de, ahead.dn) };
    const mine = printOf(aheadPose, .2), now = printOf(pose, 0);
    const v = visitor();
    if (v && Number.isFinite(v.e)) {
      const sq = { corners: [[v.e - .35, v.n - .35], [v.e + .35, v.n - .35], [v.e + .35, v.n + .35], [v.e - .35, v.n + .35]], w: v.e - .35, e: v.e + .35, s: v.n - .35, n: v.n + .35 };
      if (overlaps(mine, sq) && !overlaps(now, sq)) return 'someone on the track';
    }
    let list = [];
    try { list = blockers() ?? []; } catch { list = []; }
    for (const o of list) {
      const p = o?.print ?? o;
      if (Array.isArray(p)) { if (p.some(x => x?.corners && overlaps(mine, x) && !overlaps(now, x))) return 'a team'; continue; }
      if (p?.corners && overlaps(mine, p) && !overlaps(now, p)) return o.word ?? 'a team';
    }
    for (const other of line.cars) {
      if (other === c || !other.pose) continue;
      const d = other.pose.s - pose.s;
      if (d > 0 && d < 22 && (pose.s < line.cusp) === (other.pose.s < line.cusp)) return 'the car ahead';
    }
    return null;
  }

  function placeBuilt(line, c, dt, cameraPosition) {
    const b = c.built, pose = c.pose;
    const y = ground(pose.e, pose.n);
    b.root.position.set(pose.e, y, -pose.n);
    b.root.rotation.set(0, pose.yaw, 0);
    b.root.updateMatrixWorld(true);
    const dist = cameraPosition ? Math.hypot(cameraPosition.x - pose.e, cameraPosition.z + pose.n) : 0;
    const step = c.lastS == null ? 0 : Math.abs(pose.s - c.lastS);
    c.lastS = pose.s;
    // the horses: on the track ahead of the car (or, at a stub, walked round to its other end)
    const fwd = { e: Math.sin(pose.yaw), n: -Math.cos(pose.yaw) };
    const leftOf = { e: -fwd.n, n: fwd.e };   // left of the facing
    const ahead = car.horse_ahead_m;
    let k = 0;
    const strap = (a, bpt, w = .035, t = .012) => {
      if (k >= 8) return;
      const d = new THREE.Vector3().subVectors(bpt, a), L = d.length();
      if (L < .01) return;
      const m = new THREE.Matrix4(), q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 0, 1), d.clone().normalize());
      m.compose(a.clone().add(bpt).multiplyScalar(.5), q, new THREE.Vector3(w, t, L));
      b.straps.setMatrixAt(k++, m);
    };
    const front = new THREE.Vector3(0, .95, car.body_m / 2 + car.platform_m + .1).applyMatrix4(b.root.matrixWorld);
    for (const h of b.horses) {
      let e, n, yaw, moved = step;
      const dw = pose.dwell;
      if (dw && dw.u > .15 && dw.u < .85) {
        // walking round: out along the car's left (of the way it will leave), down its length, in at the far end
        const u = (dw.u - .15) / .7;
        // in the frame of the way it will leave: the came-in front is behind it, so a U from
        // (−ahead) to (+ahead) round its left side
        const lf = pose.leave, ll = { e: -lf.n, n: lf.e };
        const side = 2.3 + .4 * (h.side || 0);
        const pts = [[-ahead, h.side * car.horse_half_spacing_m], [-ahead - 1.5, side], [ahead + 1.5, side], [ahead, h.side * car.horse_half_spacing_m]];
        const seg = [0, 1, 2].map(i => Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]));
        const total = seg[0] + seg[1] + seg[2];
        let t = u * total, i = 0;
        while (i < 2 && t > seg[i]) { t -= seg[i]; i++; }
        const f = t / seg[i];
        const z = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, x = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f;
        e = pose.e + lf.e * z + ll.e * x; n = pose.n + lf.n * z + ll.n * x;
        const dz = pts[i + 1][0] - pts[i][0], dx = pts[i + 1][1] - pts[i][1];
        const de = lf.e * dz + ll.e * dx, dn = lf.n * dz + ll.n * dx;
        yaw = yawOf(de, dn);
        moved = (total / (.7 * car.dwell_s)) * dt;
        h.walking = true;
      } else {
        let q;
        if (!dw) {
          // on the track ahead, following its curves; past a stub's end, straight on
          const s = pose.s + ahead, cuspAt = pose.s < line.cusp ? line.cusp : line.path.length;
          if (s <= cuspAt) q = line.path.at(s, tmp2); else q = { e: pose.e + fwd.e * ahead, n: pose.n + fwd.n * ahead, de: fwd.e, dn: fwd.n };
        } else q = { e: pose.e + fwd.e * ahead, n: pose.n + fwd.n * ahead, de: fwd.e, dn: fwd.n };
        const lx = -q.dn, ln = q.de;
        e = q.e + lx * h.side * car.horse_half_spacing_m; n = q.n + ln * h.side * car.horse_half_spacing_m;
        yaw = yawOf(q.de, q.dn);
        h.walking = false;
      }
      h.root.position.set(e, ground(e, n), -n);
      h.root.rotation.set(0, yaw, 0);
      const speed = pose.dwell ? (h.walking ? 1.2 : 0) : pose.speed;
      h.gait.advance(moved, speed, dt);
      h.lods.update(dist);
      h.root.updateMatrixWorld(true);
      // traces from the collar to the dash, and a rein from the bit to the driver's hands
      if (!h.walking) {
        for (const s of [1, -1]) {
          const a = h.hook[s]();
          const whip = front.clone().add(new THREE.Vector3(leftOf.e * s * .25 + leftOf.e * h.side * .35, 0, -(leftOf.n * s * .25 + leftOf.n * h.side * .35)));
          strap(a, whip);
        }
        if (h.bit && b.driver) {
          const hands = new THREE.Vector3(0, 1.85, car.body_m / 2 + car.platform_m * .45).applyMatrix4(b.root.matrixWorld);
          strap(h.bit(), hands, .02, .008);
        }
      }
    }
    // the pole between a pair
    if (b.horses.length === 2 && !b.horses.some(h => h.walking)) {
      const tip = new THREE.Vector3(0, 1.05, car.body_m / 2 + car.platform_m + ahead - .8).applyMatrix4(b.root.matrixWorld);
      strap(front, tip, .07, .07);
    }
    b.straps.count = k;
    b.straps.instanceMatrix.needsUpdate = true;
    // the driver at the front dash, the conductor at the back
    const placeMan = (actor, z, x) => {
      if (!actor) return;
      const at = new THREE.Vector3(x, 0, z).applyMatrix4(b.root.matrixWorld);
      const ey = b.root.position.y + .72;
      const heading = ((pose.yaw / DEG) % 360 + 360) % 360;
      const bearing = (180 - heading + 360) % 360;
      actor.standY = ey;
      actor.tow = () => ({ e: at.x, n: -at.z, heading: bearing });
      actor.update(dt, cameraPosition ?? b.root.position, dt);
    };
    const driverZ = car.body_m / 2 + car.platform_m * .48, conductorZ = -(car.body_m / 2 + car.platform_m * .5);
    if (pose.dwell && pose.dwell.u > .15 && pose.dwell.u < .85) {
      // changing ends: the driver goes through the car to the other platform
      placeMan(b.driver, pose.dwell.u < .5 ? -driverZ : driverZ, 0);
    } else placeMan(b.driver, driverZ, .2);
    placeMan(b.conductor, conductorZ, -.35);
  }

  function update(dt, cameraPosition, { paused = false, hidden: hide = false } = {}) {
    if (!Number.isFinite(dt) || dt < 0) dt = 0;
    const tier = detail();
    const level = coarse || tier === 'light' ? 'light' : tier === 'balanced' ? 'balanced' : 'full';
    // the track cells near the eye
    const tr = TRACK_REACH[level];
    if (cameraPosition) for (const cell of cells) {
      cell.mesh.visible = Math.hypot(cell.centre[0] - cameraPosition.x, cell.centre[1] + cameraPosition.z) < tr + CELL_M * .71;
    }
    const h = hour(), d = date();
    lastHour = h; lastDate = d;
    running = inService(doc.hours, h, d);
    const showCars = running && !hide && !hidden();
    if (!paused) clock += dt;
    const reach = REACH[level], cap = CAP[level];
    const want = [];
    for (const line of lines) {
      for (const c of line.cars) {
        // a car out of sight makes up the time it lost
        if (!c.built && c.delay > 0) c.delay = Math.max(0, c.delay - dt * .5);
        c.place = line.table.place(clock + c.k * line.service.headway_s - c.delay + 30);
        c.pose = poseAt(line, c.place);
        if (!showCars || !cameraPosition) continue;
        const dist = Math.hypot(c.pose.e - cameraPosition.x, c.pose.n + cameraPosition.z);
        if (dist < reach) want.push({ line, c, dist });
      }
    }
    want.sort((a, b) => a.dist - b.dist);
    const keep = new Set(want.slice(0, cap).map(w => w.c));
    for (const line of lines) for (const c of line.cars) {
      if (c.built && !keep.has(c)) { release(c.built); c.built = null; c.lastS = null; }
    }
    if (!showCars) return;
    for (const { line, c } of want.slice(0, cap)) {
      if (!c.built && !c.building) {
        c.building = true;
        build(line, c).then(b => { c.building = null; if (keep.has(c) && running) { c.built = b; } else release(b); })
          .catch(error => { c.building = null; problems.push(`horse railways: ${error.message}`); });
        continue;
      }
      if (!c.built) continue;
      // held by what is in its way: it stands, and its time slips
      if (!paused) {
        const why = wayClear(line, c, c.pose);
        if (why && c.held < HOLD_GIVE_UP_S) {
          c.held += dt; c.delay += dt; c.why = why;
          c.place = line.table.place(clock + c.k * line.service.headway_s - c.delay + 30);
          c.pose = poseAt(line, c.place); c.pose.speed = 0;
        } else { if (!why) c.held = 0; c.why = null; }
      }
      try { placeBuilt(line, c, paused ? 0 : dt, cameraPosition); } catch (error) { problems.push(`horse railways: ${error.message}`); release(c.built); c.built = null; }
    }
  }

  return {
    group, doc,
    update,
    get running() { return running; },
    /** What a team must not drive into: each built car, its horses and its platforms. */
    obstacles() {
      const out = [];
      for (const line of lines) for (const c of line.cars) if (c.built && c.pose) out.push({ id: `horse-car:${c.id}`, word: 'a horse car', print: printOf(c.pose, 0) });
      return out;
    },
    snapshot() {
      const built = [];
      for (const line of lines) for (const c of line.cars) if (c.built && c.pose) built.push({ id: c.id, e: +c.pose.e.toFixed(2), n: +c.pose.n.toFixed(2),
        yaw: +c.pose.yaw.toFixed(3), dwell: !!c.pose.dwell, held: c.why ?? null, horses: c.built.horses.length, people: [c.built.driver, c.built.conductor].filter(Boolean).length });
      return { running, hour: lastHour, date: lastDate, clock: +clock.toFixed(2), cells: cells.length, cellsShown: cells.filter(x => x.mesh.visible).length,
        lines: lines.map(l => ({ id: l.service.id, cars: l.cars.length, period_s: Math.round(l.table.period) })), built };
    },
    /** The cars of a line nearest (e, n): for a stand or a test. */
    nearest(e, n) {
      let best = null;
      for (const line of lines) for (const c of line.cars) if (c.pose) {
        const d = Math.hypot(c.pose.e - e, c.pose.n - n);
        if (!best || d < best.d) best = { id: c.id, d, e: c.pose.e, n: c.pose.n };
      }
      return best;
    },
    /** Jump the clock (a test or a stand): seconds. */
    setClock(t) { clock = t; },
    dispose() {
      for (const line of lines) for (const c of line.cars) { release(c.built); c.built = null; }
      for (const cell of cells) cell.mesh.geometry.dispose();
      trackMat.dispose(); strapGeom.dispose(); strapMat.dispose(); collarGeom.dispose(); collarMat.dispose(); lettering.dispose();
      for (const g of paintedGeom.values()) g.dispose();
      for (const m of bodyMats.values()) m.dispose();
      for (const m of letterMats.values()) { m.map?.dispose(); m.dispose(); }
      group.removeFromParent();
    },
  };
}

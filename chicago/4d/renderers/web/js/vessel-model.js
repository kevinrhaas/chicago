/**
 * vessel-model.js — the lake schooner and the trade boats, built plank by plank (T-3612).
 *
 * The owner, 2026-11-16: *"the schooners boats in 1835 we're not realistic they should photo
 * match correct boats for 1835 with realistic wood and working crews on the boats"*. The
 * picture this is built to is the one period drawing of a vessel in Chicago's own river that
 * this project holds whole: the plate "Dearborn Street Drawbridge, built in 1834" (Andreas,
 * History of Chicago I, 1884, p. 631; data/sources/andreas_1884_dearborn_drawbridge_plate.json),
 * whose right half is a two-masted TOPSAIL SCHOONER lying at the bank: raked lower masts with
 * pole topmasts and vanes at the trucks, a square fore yard and fore topsail yard with their
 * sails hung loose, a long bowsprit and jibboom with the headsails loose along it, shrouds with
 * ratlines set up to deadeyes at the rail, a bluff bow and a dark hull. That is the lake carrier
 * of the 1830s, and it is what every schooner here is: the rig, the proportions and the parts the
 * plate draws. What no picture gives — the colours of the paint, the run of the planking, the
 * deck furniture, the yawl at the stern davits — is the general practice of the lakes and is
 * declared as a liberty (docs/LIBERTIES.md L-vessels-3612).
 *
 * WHAT IT BUILDS. One function per kind, each returning a three.js Group in the vessel's own
 * frame: x forward (the stem at +L/2), y up from the design waterline (y = 0 floats on the
 * water plane), z to starboard. The caller poses the group. Parts that move are their own
 * groups so a pose needs no rebuild: each gaff sail swings with its boom about its mast, the
 * square yards brace together, and every sail has a set and a furled form.
 *
 * THE WOOD AND THE PAINT ARE DRAWN, NOT TEXTURED. 1835's phone memory has a line to keep, so no
 * picture is loaded: one material per vessel draws every surface from four numbers carried on
 * the vertex — its colour, its kind (painted planking, deck planking, spar, iron, canvas,
 * plain paint, cordage) and where on it the fragment lies, in metres. From those the shader
 * lays the strakes of the hull and their butts, the deck's caulked seams, the grain of the
 * spars and the cloths of the sails, and in winter the snow on what faces up. Rope is drawn as
 * lines. A vessel is a handful of draw calls: the hull and everything fixed to it, each swinging
 * rig, the standing rigging, the running rigging that moves with it.
 */

import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { seasonUniforms } from './season.js';

const DEG = Math.PI / 180;

/** How much daylight there is to come through a sail (0 night … 1 day); vessels.js sets it. */
export const vesselLight = { value: 1 };

/** The kinds of surface the shader draws. */
export const SURF = Object.freeze({
  hullPlank: 0, deckPlank: 1, spar: 2, iron: 3, canvas: 4, paint: 5, cordage: 6,
});

/** sRGB 0..255 triple → linear 0..1 (vertex colours are read as linear). */
function lin(rgb) {
  const c = new THREE.Color().setRGB(rgb[0] / 255, rgb[1] / 255, rgb[2] / 255, THREE.SRGBColorSpace);
  return [c.r, c.g, c.b];
}

/** A seeded run of numbers in [0, 1). */
export function rng(seed) {
  let s = (Math.floor(seed) >>> 0) || 1;
  return () => {
    s ^= s << 13; s >>>= 0;
    s ^= s >>> 17;
    s ^= s << 5; s >>>= 0;
    return s / 4294967296;
  };
}
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;

/* -------------------------------------------------------------------------- */
/* the one material                                                            */
/* -------------------------------------------------------------------------- */

const SHADER_VERT_DECL = /* glsl */`
attribute vec2 aSurf;
attribute float aKind;
varying vec2 vSurf;
varying float vKind;
varying vec3 vVesselWN;
varying float vVesselY;
`;
const SHADER_VERT_MAIN = /* glsl */`
  vSurf = aSurf;
  vKind = aKind;
  vVesselWN = normalize(mat3(modelMatrix) * objectNormal);
  vVesselY = position.y;
`;
const SHADER_FRAG_DECL = /* glsl */`
varying vec2 vSurf;
varying float vKind;
varying vec3 vVesselWN;
varying float vVesselY;
uniform float uVesselSnow;
uniform vec3 uVesselBottom;
uniform vec3 uVesselBoot;
uniform float uVesselSeed;
uniform float uVesselLight;
float vH1(float n) { return fract(sin(n * 127.1 + uVesselSeed * 17.0) * 43758.5453); }
float vH2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7)) + uVesselSeed * 3.1) * 43758.5453); }
float vNoise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(vH2(i), vH2(i + vec2(1.0, 0.0)), u.x), mix(vH2(i + vec2(0.0, 1.0)), vH2(i + vec2(1.0, 1.0)), u.x), u.y);
}
// One plank field: rows across v, butts staggered along u. Returns (seam 0..1, grain tone, row).
vec3 vPlanks(vec2 s, float w, float runM) {
  float row = floor(s.y / w);
  float fy = fract(s.y / w);
  float off = vH1(row) * runM;
  float fu = fract((s.x + off) / runM);
  float edge = min(fy, 1.0 - fy) * w;                 // metres to the nearest seam
  float butt = min(fu, 1.0 - fu) * runM;
  float seam = 1.0 - smoothstep(0.004, 0.014, min(edge, butt * 1.4));
  float plank = floor((s.x + off) / runM) + row * 7.0;
  float tone = 0.86 + 0.22 * vH1(plank);
  float grain = vNoise(vec2(s.x * 0.9 + plank * 3.0, s.y * 48.0)) * 0.6 + vNoise(vec2(s.x * 4.0, s.y * 160.0)) * 0.4;
  return vec3(seam, tone * (0.84 + 0.3 * grain), row);
}
`;
const SHADER_FRAG_APPLY = /* glsl */`
  {
    float k = floor(vKind + 0.5);
    vec3 base = diffuseColor.rgb;
    float rough = 0.85;
    if (k < 0.5) {                                   // hull planking under paint
      // Tarred below the water, a dark boot-top at it, the topsides' own paint above.
      if (vVesselY < 0.05) base = uVesselBottom;
      else if (vVesselY < 0.17) base = uVesselBoot;
      vec3 p = vPlanks(vSurf, 0.17, 5.6);
      float wear = vNoise(vSurf * vec2(0.7, 2.2));
      base *= mix(1.0, 0.55, p.x) * (0.9 + 0.16 * wear);
      base = mix(base, base * vec3(1.05, 0.98, 0.9), smoothstep(0.65, 0.9, vNoise(vSurf * 1.7)) * 0.4);
      rough = 0.62 + 0.25 * wear;
    } else if (k < 1.5) {                            // deck planking, bare wood, caulked
      vec3 p = vPlanks(vSurf, 0.13, 6.4);
      base *= p.y;
      base = mix(base, vec3(0.012, 0.010, 0.008), p.x * 0.9);
      rough = 0.9;
    } else if (k < 2.5) {                            // spars and bare wood: the grain runs along u
      float g = vNoise(vec2(vSurf.x * 1.1, vSurf.y * 26.0)) * 0.6 + vNoise(vec2(vSurf.x * 6.0, vSurf.y * 90.0)) * 0.4;
      base *= 0.82 + 0.3 * g;
      rough = 0.72;
    } else if (k < 3.5) {                            // iron, blacked
      base *= 0.85 + 0.3 * vNoise(vSurf * 9.0);
      rough = 0.55;
    } else if (k < 4.5) {                            // canvas: cloths about two feet wide, seamed
      float c = fract(vSurf.x / 0.61);
      float seam = 1.0 - smoothstep(0.0, 0.05, min(c, 1.0 - c));
      float weave = vNoise(vSurf * vec2(40.0, 40.0)) * 0.05;
      float soil = smoothstep(0.0, 1.0, vNoise(vSurf * 0.35)) * 0.12;
      base *= (0.97 - 0.12 * seam - soil + weave);
      rough = 0.95;
      vVesselGlowK = 1.0;                            // daylight comes through a sail
    } else if (k < 5.5) {                            // plain paint
      base *= 0.94 + 0.1 * vNoise(vSurf * 3.0);
      rough = 0.6;
    } else {                                         // cordage, served and tarred
      base *= 0.8 + 0.3 * vNoise(vec2(vSurf.x * 30.0, 0.0));
      rough = 0.9;
    }
    // Winter: snow lies on what faces up (and none on the canvas, which is unbent then).
    float up = smoothstep(0.55, 0.85, vVesselWN.y);
    float snow = uVesselSnow * up;
    base = mix(base, vec3(0.86, 0.88, 0.92), snow * (0.75 + 0.25 * vNoise(vSurf * 2.0)));
    diffuseColor.rgb = base;
    vVesselRough = mix(rough, 0.95, snow);
  }
`;

/**
 * The material every surface of a vessel shares. `seed` varies the planking from hull to hull.
 * DoubleSide, because an open boat shows its inside and a sail both its faces.
 */
export function vesselMaterial({ seed = 1, confidence = null, bottom = [44, 36, 30], boot = [38, 34, 30] } = {}) {
  const mat = new THREE.MeshStandardMaterial({
    color: 0xffffff, vertexColors: true, roughness: 0.85, metalness: 0, side: THREE.DoubleSide,
  });
  mat.name = 'vessel';
  const uniforms = { uVesselSnow: seasonUniforms.uChiSnow, uVesselLight: vesselLight, uVesselSeed: { value: (seed % 97) / 9.7 },
    uVesselBottom: { value: new THREE.Vector3(...lin(bottom)) }, uVesselBoot: { value: new THREE.Vector3(...lin(boot)) } };
  mat.userData.vesselUniforms = uniforms;
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = SHADER_VERT_DECL + shader.vertexShader.replace(
      '#include <beginnormal_vertex>', `#include <beginnormal_vertex>\n${SHADER_VERT_MAIN}`);
    shader.fragmentShader = SHADER_FRAG_DECL + 'float vVesselRough = 0.85;\nfloat vVesselGlowK = 0.0;\n' + shader.fragmentShader
      .replace('#include <color_fragment>', `#include <color_fragment>\n${SHADER_FRAG_APPLY}`)
      .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\n  totalEmissiveRadiance += diffuseColor.rgb * vVesselGlowK * 0.24 * uVesselLight;')
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = vVesselRough;');
  };
  mat.customProgramCacheKey = () => 'chicago4d-vessel-v4';
  confidence?.patch?.(mat);
  return mat;
}

/** The lines of the rigging: hemp, tarred dark. */
export function ropeMaterial() {
  const mat = new THREE.LineBasicMaterial({ color: new THREE.Color().setRGB(0.055, 0.045, 0.035) });
  mat.name = 'vessel-rope';
  return mat;
}

/** A depth-only lid at the waterline inside an open hull, drawn before the water (crossings.js). */
export function waterLidMaterial() {
  return new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: true, side: THREE.DoubleSide });
}

/* -------------------------------------------------------------------------- */
/* a geometry builder                                                          */
/* -------------------------------------------------------------------------- */

class Parts {
  constructor() { this.geos = []; this.lines = []; }

  /** A grid of points P(i, j) (rows × cols), smooth-shaded, one kind and colour function. */
  grid(rows, cols, P, { kind, color, surf, flip = false }) {
    const pos = [], col = [], srf = [], knd = [], idx = [];
    for (let i = 0; i <= rows; i++) {
      for (let j = 0; j <= cols; j++) {
        const p = P(i / rows, j / cols);
        pos.push(p[0], p[1], p[2]);
        const c = typeof color === 'function' ? color(p, i / rows, j / cols) : color;
        col.push(c[0], c[1], c[2]);
        const s = surf ? surf(p, i / rows, j / cols) : [p[0], p[1]];
        srf.push(s[0], s[1]);
        knd.push(kind);
      }
    }
    const w = cols + 1;
    for (let i = 0; i < rows; i++) {
      for (let j = 0; j < cols; j++) {
        const a = i * w + j, b = a + 1, c = a + w, d = c + 1;
        if (flip) idx.push(a, b, c, b, d, c); else idx.push(a, c, b, b, c, d);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    g.setAttribute('aSurf', new THREE.Float32BufferAttribute(srf, 2));
    g.setAttribute('aKind', new THREE.Float32BufferAttribute(knd, 1));
    g.setIndex(idx);
    g.computeVertexNormals();
    this.geos.push(g.toNonIndexed());
    g.dispose();
    return this;
  }

  /** A tube along a polyline of [x,y,z] with radii per point. */
  tube(pts, radii, { kind = SURF.spar, color, sides = 7 }) {
    const n = pts.length;
    const frames = [];
    for (let i = 0; i < n; i++) {
      const a = new THREE.Vector3(...pts[Math.max(0, i - 1)]);
      const b = new THREE.Vector3(...pts[Math.min(n - 1, i + 1)]);
      const t = b.sub(a).normalize();
      const ref = Math.abs(t.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
      const u = new THREE.Vector3().crossVectors(t, ref).normalize();
      const v = new THREE.Vector3().crossVectors(t, u).normalize();
      frames.push([u, v]);
    }
    let along = 0;
    const alongAt = [0];
    for (let i = 1; i < n; i++) {
      along += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1], pts[i][2] - pts[i - 1][2]);
      alongAt.push(along);
    }
    const r = (i) => (Array.isArray(radii) ? radii[i] : radii);
    this.grid(n - 1, sides, (ti, tj) => {
      const i = Math.round(ti * (n - 1));
      const a = tj * Math.PI * 2;
      const [u, v] = frames[i];
      const R = r(i);
      return [pts[i][0] + (u.x * Math.cos(a) + v.x * Math.sin(a)) * R,
        pts[i][1] + (u.y * Math.cos(a) + v.y * Math.sin(a)) * R,
        pts[i][2] + (u.z * Math.cos(a) + v.z * Math.sin(a)) * R];
    }, { kind, color, surf: (p, ti, tj) => [alongAt[Math.round(ti * (n - 1))], tj * 2 * Math.PI * r(Math.round(ti * (n - 1)))] });
    return this;
  }

  /** A straight spar from a to b, radius ra to rb. */
  spar(a, b, ra, rb = ra, opts = {}) {
    const steps = 4;
    const pts = [], rs = [];
    for (let i = 0; i <= steps; i++) {
      const t = i / steps;
      pts.push([lerp(a[0], b[0], t), lerp(a[1], b[1], t), lerp(a[2], b[2], t)]);
      rs.push(lerp(ra, rb, t));
    }
    return this.tube(pts, rs, opts);
  }

  /** An oriented box: centre c, axes (unit) ax/ay/az, half sizes h. */
  box(c, h, { kind = SURF.paint, color, ax = [1, 0, 0], ay = [0, 1, 0], az = [0, 0, 1] }) {
    const P = (sx, sy, sz) => [
      c[0] + ax[0] * sx * h[0] + ay[0] * sy * h[1] + az[0] * sz * h[2],
      c[1] + ax[1] * sx * h[0] + ay[1] * sy * h[1] + az[1] * sz * h[2],
      c[2] + ax[2] * sx * h[0] + ay[2] * sy * h[1] + az[2] * sz * h[2],
    ];
    const faces = [
      [[1, -1, -1], [1, 1, -1], [1, 1, 1], [1, -1, 1]],
      [[-1, -1, 1], [-1, 1, 1], [-1, 1, -1], [-1, -1, -1]],
      [[-1, 1, -1], [-1, 1, 1], [1, 1, 1], [1, 1, -1]],
      [[-1, -1, 1], [-1, -1, -1], [1, -1, -1], [1, -1, 1]],
      [[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]],
      [[1, -1, -1], [-1, -1, -1], [-1, 1, -1], [1, 1, -1]],
    ];
    const pos = [], col = [], srf = [], knd = [], nrm = [];
    for (const f of faces) {
      const q = f.map(([x, y, z]) => P(x, y, z));
      const e1 = new THREE.Vector3(q[1][0] - q[0][0], q[1][1] - q[0][1], q[1][2] - q[0][2]);
      const e2 = new THREE.Vector3(q[2][0] - q[0][0], q[2][1] - q[0][1], q[2][2] - q[0][2]);
      const nn = new THREE.Vector3().crossVectors(e1, e2).normalize();
      for (const k of [0, 1, 2, 0, 2, 3]) {
        pos.push(...q[k]);
        nrm.push(nn.x, nn.y, nn.z);
        col.push(...color);
        srf.push(q[k][0] + q[k][2], q[k][1]);
        knd.push(kind);
      }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(nrm, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    g.setAttribute('aSurf', new THREE.Float32BufferAttribute(srf, 2));
    g.setAttribute('aKind', new THREE.Float32BufferAttribute(knd, 1));
    this.geos.push(g);
    return this;
  }

  /** One rope, as straight segments through `pts`. */
  line(...pts) {
    for (let i = 1; i < pts.length; i++) this.lines.push(...pts[i - 1], ...pts[i]);
    return this;
  }

  /** A mesh of everything gathered, in `mat`; null if nothing was. */
  mesh(mat, name) {
    if (!this.geos.length) return null;
    const geo = mergeGeometries(this.geos, false);
    for (const g of this.geos) g.dispose();
    this.geos = [];
    geo.setAttribute('_confidence', new THREE.Float32BufferAttribute(new Float32Array(geo.getAttribute('position').count).fill(1), 1));
    geo.computeBoundingSphere();
    const m = new THREE.Mesh(geo, mat);
    m.name = name;
    m.castShadow = true;
    m.receiveShadow = true;
    return m;
  }

  /** Line segments of everything gathered by line(). */
  rope(mat, name) {
    if (!this.lines.length) return null;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.Float32BufferAttribute(this.lines, 3));
    geo.computeBoundingSphere();
    this.lines = [];
    const l = new THREE.LineSegments(geo, mat);
    l.name = name;
    return l;
  }
}

/* -------------------------------------------------------------------------- */
/* the hull                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * The lines of a hull: half-breadth at the sheer, the keel's height and the sheer's height, at
 * station t (0 = stem, 1 = stern), and how full the section is (2 round … 5 boxy). All in metres
 * in the vessel's frame (waterline y = 0).
 */
function schoonerLines(h) {
  const { L, B, T, F } = h;
  const half = (t) => {
    if (t < 0.42) return (B / 2) * Math.pow(1 - Math.pow(1 - t / 0.42, 2.1), 0.55);
    if (t > 0.62) return (B / 2) * (1 - 0.36 * Math.pow((t - 0.62) / 0.38, 1.8));
    return B / 2;
  };
  const sheer = (t) => F + 0.62 * Math.pow(1 - t, 3.2) + 0.32 * Math.pow(t, 4);
  const keel = (t) => {
    if (t < 0.1) { const u = 1 - t / 0.1; return -T + (T + sheer(0) - 0.25) * (1 - Math.sqrt(Math.max(0, 1 - u * u))); }
    if (t > 0.9) return -T + 0.15 * (t - 0.9) / 0.1;
    return -T;
  };
  const full = (t) => 2.2 + 2.6 * Math.sin(Math.PI * clamp((t - 0.04) / 0.9, 0, 1)) ** 1.4;
  const x = (t) => L / 2 - t * L;
  return { half, sheer, keel, full, x, L, B, T, F };
}

/** A point on a hull section: s 0 (keel) … 1 (sheer), on the starboard side (side = 1). */
function sectionPoint(ln, t, s, side = 1) {
  const hb = ln.half(t);
  const k = ln.keel(t), sh = ln.sheer(t);
  const n = ln.full(t);
  const phi = s * Math.PI / 2;
  const z = hb * Math.pow(Math.sin(phi), 2 / n);
  const y = k + (sh - k) * (1 - Math.pow(Math.cos(phi), 2 / n));
  return [ln.x(t), y, side * z];
}

/**
 * Plank the topsides and bottom of a hull. `paint(y, t)` is the colour at height y; the surface
 * coordinate is (along, girth) so the strakes run fore and aft and their seams follow the girth.
 * A transom closes the stern when the lines leave it open.
 */
function plankHull(parts, ln, paint, { transomPaint = null, stations = 28, girth = 12 } = {}) {
  for (const side of [1, -1]) {
    // Girth arc length per (station, s), for the strakes' run.
    const girthAt = (t, s) => {
      let acc = 0, prev = sectionPoint(ln, t, 0, side);
      const steps = 12;
      for (let k = 1; k <= steps; k++) {
        const q = sectionPoint(ln, t, (s * k) / steps, side);
        acc += Math.hypot(q[0] - prev[0], q[1] - prev[1], q[2] - prev[2]);
        prev = q;
      }
      return acc;
    };
    parts.grid(stations, girth, (ti, sj) => sectionPoint(ln, ti * 0.995, sj, side), {
      kind: SURF.hullPlank,
      color: (p, ti) => paint(p[1], ti),
      surf: (p, ti, sj) => [p[0], girthAt(ti * 0.995, sj)],
      flip: side < 0,
    });
  }
  // The transom: a flat panel across the stern, from the counter up to the sheer.
  const t = 0.995;
  const hb = ln.half(t);
  const yb = Math.max(ln.keel(t) + 0.8, -0.35), yt = ln.sheer(t);
  const x = ln.x(t);
  parts.grid(3, 6, (i, j) => {
    const y = lerp(yb, yt, i);
    const z = lerp(-hb, hb, j) * (0.82 + 0.18 * i);
    return [x - 0.04 * i, y, z];
  }, { kind: SURF.paint, color: (p) => (transomPaint ?? paint)(p[1], 1), surf: (p) => [p[2], p[1]] });
}

/** The deck: planks along the length, on the sheer, a hand under it so the waterway reads. */
function deckOf(parts, ln, color, { inset = 0.12, drop = 0.06, t0 = 0.02, t1 = 0.99 } = {}) {
  parts.grid(26, 8, (ti, sj) => {
    const t = lerp(t0, t1, ti);
    const hb = Math.max(0, ln.half(t) - inset);
    return [ln.x(t), ln.sheer(t) - drop, lerp(-hb, hb, sj)];
  }, { kind: SURF.deckPlank, color, surf: (p) => [p[0], p[2] + 4] });
}

/** Bulwarks from the sheer up `hgt`: an outer face (the hull's paint), an inner face, a cap rail. */
function bulwarks(parts, ln, hgt, outer, inner, cap, { t0 = 0.015, t1 = 0.995 } = {}) {
  for (const side of [1, -1]) {
    const at = (t, up, inward = 0) => [ln.x(t), ln.sheer(t) + up, side * Math.max(0.02, ln.half(t) - inward)];
    parts.grid(26, 2, (ti, sj) => at(lerp(t0, t1, ti), sj * hgt), { kind: SURF.hullPlank, color: outer, surf: (p) => [p[0], p[1] + 9], flip: side < 0 });
    parts.grid(26, 2, (ti, sj) => at(lerp(t0, t1, ti), sj * hgt, 0.07), { kind: SURF.paint, color: inner, surf: (p) => [p[0], p[1]], flip: side > 0 });
    parts.grid(26, 1, (ti, sj) => at(lerp(t0, t1, ti), hgt + 0.02, lerp(-0.03, 0.12, sj)), { kind: SURF.spar, color: cap, surf: (p) => [p[0], p[2] * 3] });
  }
}

/* -------------------------------------------------------------------------- */
/* sails                                                                       */
/* -------------------------------------------------------------------------- */

/**
 * A sail between four corners (tack, throat/head, peak, clew), billowed `depth` (a fraction of
 * its chord) toward `+n` (a unit vector in the sail's frame). Rows run luff to leech.
 */
function sailQuad(parts, tack, throat, peak, clew, depth, nrm, color) {
  const rows = 8, cols = 10;
  const P = (u, v) => {
    // u: luff (0) → leech (1); v: foot (0) → head (1)
    const lo = [lerp(tack[0], clew[0], u), lerp(tack[1], clew[1], u), lerp(tack[2], clew[2], u)];
    const hi = [lerp(throat[0], peak[0], u), lerp(throat[1], peak[1], u), lerp(throat[2], peak[2], u)];
    const p = [lerp(lo[0], hi[0], v), lerp(lo[1], hi[1], v), lerp(lo[2], hi[2], v)];
    const chord = Math.hypot(clew[0] - tack[0], clew[2] - tack[2]) * (1 - v) + Math.hypot(peak[0] - throat[0], peak[2] - throat[2]) * v;
    // Deepest a third aft of the luff, flat at the edges; a little less belly toward the head.
    const b = depth * chord * Math.sin(Math.PI * Math.pow(u, 0.75)) * Math.sin(Math.PI * clamp(v * 0.92 + 0.08, 0, 1)) ** 0.5;
    return [p[0] + nrm[0] * b, p[1] + nrm[1] * b, p[2] + nrm[2] * b];
  };
  parts.grid(rows, cols, (i, j) => P(j, i), {
    kind: SURF.canvas, color,
    surf: (p, i, j) => [j * Math.hypot(clew[0] - tack[0], clew[1] - tack[1], clew[2] - tack[2]), i * Math.hypot(throat[1] - tack[1], throat[0] - tack[0])],
  });
}

/** A triangular headsail: tack, head, clew. */
function sailTri(parts, tack, head, clew, depth, nrm, color) {
  sailQuad(parts, tack, head, head, clew, depth, nrm, color);
}

/** A furled sail: a soft roll along a spar from a to b. */
function furl(parts, a, b, r, color) {
  const pts = [], rs = [];
  for (let i = 0; i <= 8; i++) {
    const t = i / 8;
    pts.push([lerp(a[0], b[0], t), lerp(a[1], b[1], t) + r * 0.6, lerp(a[2], b[2], t)]);
    rs.push(r * (0.55 + 0.45 * Math.sin(Math.PI * clamp(t * 1.1, 0, 1))) * (0.85 + 0.3 * ((i * 7) % 3) / 3));
  }
  parts.tube(pts, rs, { kind: SURF.canvas, color, sides: 6 });
}

/* -------------------------------------------------------------------------- */
/* the topsail schooner                                                        */
/* -------------------------------------------------------------------------- */

/** The colours of a schooner's paint and wood, from its record's `look` (sRGB triples). */
const LOOKS = {
  topsides: { black: [24, 23, 22], green: [28, 42, 34], blue: [26, 30, 40], white: [214, 210, 196] },
  stripe: { white: [222, 218, 204], yellow: [196, 158, 70], red: [128, 40, 32], green: [52, 92, 60], blue: [52, 70, 108] },
};

/**
 * Build a topsail schooner from `spec` (data/boats/vessels_*.json): hull, deck, rig.
 * Returns { group, rigs, helm, deckY, stations, dims, setSails, update, dispose }.
 */
export function buildSchooner(spec, { confidence = null, coarse = false } = {}) {
  const hull = spec.hull ?? {};
  const look = spec.look ?? {};
  const L = hull.length_m ?? 21, B = hull.beam_m ?? 5.8, T = hull.draft_m ?? 1.5, F = hull.freeboard_m ?? 1.2;
  const r = rng(look.seed ?? 7);
  const ln = schoonerLines({ L, B, T, F });
  const mat = vesselMaterial({ seed: look.seed ?? 7, confidence, bottom: look.bottom ?? [44, 36, 30] });
  const rope = ropeMaterial();
  const group = new THREE.Group();
  group.name = `vessel-${spec.id}`;

  const topsides = lin(LOOKS.topsides[look.topsides] ?? LOOKS.topsides.black);
  const stripe = lin(LOOKS.stripe[look.stripe] ?? LOOKS.stripe.white);
  const bottom = lin(look.bottom ?? [44, 36, 30]);        // tarred and weeded below the water
  const bulwarkIn = lin(look.bulwark_inside ?? [196, 190, 172]);
  const deckWood = lin([150 + r() * 14, 136 + r() * 10, 110 + r() * 10]);   // scrubbed pine, greyed
  const sparWood = lin([182, 150, 104]);                  // oiled pine
  const blackPaint = lin([20, 19, 18]);
  const whitePaint = lin([214, 208, 192]);
  const iron = lin([30, 28, 27]);
  const canvas = lin(look.canvas ?? [222, 212, 188]);
  const hemp = lin([92, 74, 52]);

  // Below the water and at it the shader paints (uVesselBottom/uVesselBoot); above, this.
  const paint = () => topsides;

  /* --- the hull and everything fixed to it --------------------------------------- */
  const fixed = new Parts();
  plankHull(fixed, ln, paint, { stations: coarse ? 18 : 28, girth: coarse ? 8 : 12 });
  deckOf(fixed, ln, deckWood);
  bulwarks(fixed, ln, 0.86, topsides, bulwarkIn, stripe);
  // The painted strake under the rail, a moulding standing proud of the planking.
  for (const side of [1, -1]) {
    fixed.grid(30, 1, (ti, sj) => {
      const t = lerp(0.012, 0.99, ti);
      const y = ln.sheer(t) - 0.42 + sj * 0.14;
      return [ln.x(t), y, side * (halfAtY(ln, t, y) + 0.012)];
    }, { kind: SURF.paint, color: stripe, surf: (p) => [p[0], p[1]], flip: side < 0 });
  }
  // The keel and the stem, a sided timber down the centreline.
  fixed.grid(30, 1, (ti, sj) => {
    const t = lerp(0.0, 0.98, ti);
    return [ln.x(t), ln.keel(t) - sj * 0.22, 0];
  }, { kind: SURF.paint, color: bottom, surf: (p) => [p[0], p[1]] });
  // The rudder, hung on the sternpost, and its head through the counter.
  const xs = ln.x(0.985);
  fixed.box([xs - 0.45, -T * 0.45, 0], [0.45, T * 0.55, 0.07], { kind: SURF.paint, color: bottom });
  fixed.spar([xs - 0.05, ln.sheer(1) - 0.1, 0], [xs + 1.6, ln.sheer(1) + 0.55, 0], 0.07, 0.05, { color: sparWood });  // the tiller
  // Hatches, the cabin trunk aft and its skylight, the galley's stovepipe, the windlass forward.
  const deckAt = (x) => ln.sheer(clamp((L / 2 - x) / L, 0, 1)) - 0.06;
  const hatch = (x, len, wid, hgt) => {
    fixed.box([x, deckAt(x) + hgt / 2, 0], [len / 2, hgt / 2, wid / 2], { kind: SURF.paint, color: whitePaint });
    fixed.box([x, deckAt(x) + hgt + 0.03, 0], [len / 2 - 0.04, 0.03, wid / 2 - 0.04], { kind: SURF.deckPlank, color: deckWood, ax: [1, 0, 0], az: [0, 0, 1] });
  };
  hatch(L * 0.09, 2.2, 1.9, 0.42);       // main hatch
  hatch(L * 0.3, 1.2, 1.1, 0.38);        // fore hatch
  const cabX = -L * 0.33;
  fixed.box([cabX, deckAt(cabX) + 0.38, 0], [1.7, 0.38, B * 0.27], { kind: SURF.paint, color: whitePaint });
  fixed.box([cabX, deckAt(cabX) + 0.79, 0], [1.75, 0.04, B * 0.28], { kind: SURF.deckPlank, color: deckWood });
  fixed.box([cabX + 0.4, deckAt(cabX) + 0.95, 0], [0.45, 0.14, 0.4], { kind: SURF.paint, color: lin([60, 64, 60]) });
  for (const side of [-1, 1]) for (const dx of [-1.0, 0, 1.0]) {
    fixed.box([cabX + dx, deckAt(cabX) + 0.45, side * (B * 0.27 + 0.005)], [0.16, 0.1, 0.01], { kind: SURF.iron, color: lin([40, 46, 52]) });
  }
  fixed.spar([L * 0.18, deckAt(L * 0.18), 0.6], [L * 0.18, deckAt(L * 0.18) + 1.3, 0.6], 0.09, 0.09, { kind: SURF.iron, color: iron });
  const wx = L * 0.41;
  fixed.spar([wx, deckAt(wx) + 0.5, -B * 0.32], [wx, deckAt(wx) + 0.5, B * 0.32], 0.2, 0.2, { color: sparWood });
  for (const side of [-1, 1]) fixed.box([wx, deckAt(wx) + 0.45, side * B * 0.34], [0.14, 0.45, 0.1], { kind: SURF.spar, color: sparWood });
  // Catheads and the anchors stowed at them.
  for (const side of [-1, 1]) {
    const t = 0.1, cx = ln.x(t), cz = side * (ln.half(t) + 0.25);
    fixed.box([cx, ln.sheer(t) + 0.55, cz], [0.12, 0.1, 0.42], { kind: SURF.spar, color: sparWood });
    fixed.box([cx - 0.1, ln.sheer(t) - 0.4, side * (ln.half(t) + 0.32)], [0.06, 0.9, 0.06], { kind: SURF.iron, color: iron });
    fixed.box([cx - 0.1, ln.sheer(t) - 1.25, side * (ln.half(t) + 0.32)], [0.5, 0.06, 0.06], { kind: SURF.iron, color: iron });
    fixed.box([cx - 0.1, ln.sheer(t) + 0.45, side * (ln.half(t) + 0.32)], [0.04, 0.04, 0.6], { kind: SURF.spar, color: sparWood });
  }
  // The channels (the ledges the shrouds are set up to), outboard at the rail by each mast.
  const masts = [
    { x: L * 0.215, rake: 3.5 * DEG, h: (hull.fore_mast_m ?? 15), top: (hull.fore_topmast_m ?? 7), r0: 0.24 },
    { x: -L * 0.13, rake: 5.5 * DEG, h: (hull.main_mast_m ?? 16), top: (hull.main_topmast_m ?? 6.5), r0: 0.25 },
  ];
  for (const m of masts) {
    const t = clamp((L / 2 - m.x) / L, 0, 1);
    for (const side of [-1, 1]) {
      fixed.box([m.x - 0.3, ln.sheer(t) + 0.15, side * (ln.half(t) + 0.16)], [1.3, 0.05, 0.16], { kind: SURF.paint, color: topsides });
    }
  }

  /* --- the spars ------------------------------------------------------------------ */
  // A point on a raked mast at height h above the deck.
  const mastAt = (m, h) => [m.x - Math.sin(m.rake) * h, deckAt(m.x) + Math.cos(m.rake) * h, 0];
  const heads = [];
  for (const m of masts) {
    const foot = mastAt(m, -0.1), head = mastAt(m, m.h);
    fixed.spar(foot, head, m.r0, m.r0 * 0.72, { color: sparWood });
    // The doubling: trestle trees and crosstrees, the cap, the topmast above.
    const trestle = mastAt(m, m.h - 2.2);
    fixed.box(trestle, [0.45, 0.07, 0.9], { kind: SURF.spar, color: sparWood });
    const cap = mastAt(m, m.h + 0.05);
    fixed.box([cap[0] + 0.2, cap[1], 0], [0.42, 0.12, 0.2], { kind: SURF.paint, color: blackPaint });
    const tFoot = [trestle[0] + 0.42, trestle[1] - 0.1, 0];
    const tHead = [tFoot[0] - Math.sin(m.rake) * (m.top + 2.2), tFoot[1] + Math.cos(m.rake) * (m.top + 2.2), 0];
    fixed.spar(tFoot, tHead, 0.13, 0.07, { color: sparWood });
    fixed.box([tHead[0], tHead[1] + 0.05, 0], [0.08, 0.06, 0.08], { kind: SURF.paint, color: whitePaint });   // the truck
    // The mastheads painted, as the lakes did.
    fixed.spar(mastAt(m, m.h - 2.2), head, m.r0 * 0.78, m.r0 * 0.72, { kind: SURF.paint, color: whitePaint });
    heads.push({ m, head, trestle, tFoot, tHead });
  }
  // The bowsprit and jibboom, steeved up, with the dolphin striker under the cap.
  const stemTop = [ln.x(0) - 0.2, ln.sheer(0) + 0.15, 0];
  const steeve = 13 * DEG;
  const sprit = hull.bowsprit_m ?? 5.6, jib = hull.jibboom_m ?? 4.4;
  const bsHeel = [stemTop[0] - 2.2 * Math.cos(steeve), stemTop[1] - 2.2 * Math.sin(steeve), 0];
  const bsEnd = [stemTop[0] + sprit * Math.cos(steeve), stemTop[1] + sprit * Math.sin(steeve), 0];
  fixed.spar(bsHeel, bsEnd, 0.21, 0.15, { color: sparWood });
  const jbHeel = [bsEnd[0] - 2.4 * Math.cos(steeve), bsEnd[1] - 2.4 * Math.sin(steeve) + 0.24, 0];
  const jbEnd = [bsEnd[0] + jib * Math.cos(steeve), bsEnd[1] + jib * Math.sin(steeve) + 0.24, 0];
  fixed.spar(jbHeel, jbEnd, 0.11, 0.06, { color: sparWood });
  fixed.box([bsEnd[0], bsEnd[1] + 0.12, 0], [0.2, 0.2, 0.18], { kind: SURF.paint, color: blackPaint });
  const striker = [bsEnd[0] - 0.3, bsEnd[1] - 1.4, 0];
  fixed.spar([bsEnd[0] - 0.3, bsEnd[1] - 0.15, 0], striker, 0.05, 0.04, { color: sparWood });
  // The yawl, the ship's boat, hung at the stern davits (a lake schooner's own boat).
  const yawl = { x: ln.x(1) - 1.2, y: ln.sheer(1) + 0.35 };
  if (!spec.no_yawl) {
    const yl = 4.2, yb = 1.45;
    const yln = { half: (t) => (yb / 2) * Math.sin(Math.PI * clamp(0.06 + 0.9 * t, 0, 1)) ** 0.8, keel: (t) => -0.25 + 0.2 * (Math.pow(1 - t, 4)), sheer: (t) => 0.32 + 0.12 * (Math.pow(1 - t, 2)), full: () => 3, x: (t) => yl / 2 - t * yl };
    const yp = new Parts();
    plankHull(yp, yln, () => lin([120, 110, 92]), { stations: 10, girth: 5 });
    // Turned bow to starboard across the stern, as a yawl hangs in the davits.
    for (const g of yp.geos) { g.rotateY(Math.PI / 2); g.translate(yawl.x, yawl.y, 0); fixed.geos.push(g); }
    yp.geos = [];
    for (const side of [-1, 1]) {
      fixed.spar([ln.x(0.97), ln.sheer(1), side * ln.half(0.97) * 0.75], [yawl.x - 0.3, yawl.y + 1.2, side * 0.9], 0.06, 0.05, { kind: SURF.iron, color: iron });
    }
  }

  /* --- the standing rigging ------------------------------------------------------- */
  const standing = new Parts();
  const ratlines = !coarse;
  for (const { m, head, trestle, tFoot, tHead } of heads) {
    const t = clamp((L / 2 - m.x) / L, 0, 1);
    const hb = ln.half(t) + 0.3;
    const below = [head[0], head[1] - 2.4, 0];
    for (const side of [-1, 1]) {
      const shrouds = [];
      for (let k = 0; k < 3; k++) {
        const foot = [m.x + 0.4 - k * 0.75, ln.sheer(t) + 0.2, side * hb];
        const dead = [foot[0], foot[1] + 0.9, foot[2] * 0.995];
        const top = [below[0] + 0.1, below[1], side * 0.28];
        standing.line(foot, dead);
        standing.line(dead, top);
        shrouds.push([dead, top]);
        fixed.box(dead, [0.09, 0.09, 0.04], { kind: SURF.paint, color: blackPaint });
      }
      if (ratlines) {
        const [[a0, a1], , [c0, c1]] = shrouds;
        const rise = a1[1] - a0[1];
        for (let y = 0.45; y < rise - 0.6; y += 0.4) {
          const f = y / rise;
          standing.line([lerp(a0[0], a1[0], f), lerp(a0[1], a1[1], f), lerp(a0[2], a1[2], f)],
            [lerp(c0[0], c1[0], f), lerp(c0[1], c1[1], f), lerp(c0[2], c1[2], f)]);
        }
      }
      // Topmast shrouds from the crosstree ends; topmast backstays to the rail aft.
      const xt = [trestle[0], trestle[1], side * 0.9];
      standing.line(xt, [tHead[0], tHead[1] - 1.2, 0]);
      standing.line([tHead[0], tHead[1] - 0.6, 0], [m.x - 2.8, ln.sheer(clamp(t + 0.13, 0, 1)) + 0.5, side * (ln.half(clamp(t + 0.13, 0, 1)) + 0.1)]);
    }
  }
  const [fore, main] = heads;
  standing.line([fore.head[0], fore.head[1] - 1.6, 0], [stemTop[0] + 0.4, stemTop[1] + 0.2, 0]);           // forestay
  standing.line([fore.head[0], fore.head[1] - 0.6, 0], [bsEnd[0], bsEnd[1] + 0.12, 0]);                       // fore topmast stay
  standing.line([fore.tHead[0], fore.tHead[1] - 0.8, 0], [jbEnd[0], jbEnd[1], 0]);                            // jib stay
  standing.line([main.head[0], main.head[1] - 1.2, 0], [fore.head[0] + 0.1, fore.head[1] - 2.6, 0]);         // main spring stay
  standing.line([main.tHead[0], main.tHead[1] - 0.6, 0], [fore.tHead[0], fore.tHead[1] - 0.8, 0]);           // main topmast stay
  standing.line([bsEnd[0], bsEnd[1], 0], [ln.x(0.02), -0.2, 0]);                                              // bobstay
  standing.line([jbEnd[0], jbEnd[1], 0], striker, [ln.x(0.03), ln.sheer(0.03) - 0.2, 0]);                     // martingale
  for (const side of [-1, 1]) standing.line([bsEnd[0] - 0.4, bsEnd[1], 0], [ln.x(0.06), ln.sheer(0.06), side * ln.half(0.06)]);
  // Halyards down the masts (they lie close along them).
  for (const { m, head } of heads) {
    standing.line([head[0] + 0.25, head[1] - 0.4, 0.15], [m.x + 0.3, deckAt(m.x) + 0.3, 0.3]);
    standing.line([head[0] + 0.25, head[1] - 0.4, -0.15], [m.x + 0.3, deckAt(m.x) + 0.3, -0.3]);
  }
  // The vanes at the trucks (the plate draws them streaming).
  for (const { tHead } of heads) standing.line([tHead[0], tHead[1] + 0.1, 0], [tHead[0] - 1.1, tHead[1] + 0.35, 0.05]);

  /* --- the swinging rigs: each gaff sail with its boom and gaff -------------------- */
  const rigs = [];
  const buildGaffRig = (m, boomLen, gaffLen, jawUp, name) => {
    // The boom jaws stand head-high and the boom is topped up aft, clear over the helmsman.
    const JAW = 1.75;
    const pivot = mastAt(m, JAW);
    const g = new THREE.Group();
    g.name = name;
    g.position.set(...pivot);
    g.rotation.order = 'ZYX';
    g.rotation.z = m.rake;                     // the rig's y is the mast's axis
    const H = m.h - JAW - jawUp;               // boom jaws to gaff jaws, along the mast
    // The rig's frame leans with the mast; these heights are the world's, above the jaws.
    const sR = Math.sin(m.rake), cR = Math.cos(m.rake);
    const up = (x, yWorld) => (yWorld - x * sR) / cR;
    const endY = up(-boomLen, 0.9);
    const boomY = (x) => -x / boomLen * endY;
    const peakAng = 34 * DEG;                  // the gaff peaked up
    const throat = [0, H, 0], peak = [-gaffLen * Math.cos(peakAng), H + gaffLen * Math.sin(peakAng), 0];
    const clew = [-boomLen, endY - 0.1, 0];
    const tack = [0, 0.1, 0];
    const make = (furled, side) => {
      const p = new Parts();
      p.spar([0.25, 0, 0], [-boomLen, endY, 0], 0.13, 0.09, { color: sparWood });
      const gaffFurled = [-gaffLen * 0.96, 0.6 + 0.35, 0];
      const gp = furled ? gaffFurled : peak;
      const gt = furled ? [0, 0.95, 0] : throat;
      p.spar([gt[0] + 0.2, gt[1], 0], gp, 0.1, 0.07, { color: sparWood });
      if (furled) {
        furl(p, [-0.3, boomY(-0.3) + 0.12, 0], [-boomLen * 0.92, boomY(-boomLen * 0.92) + 0.05, 0], 0.22, canvas);
      } else {
        sailQuad(p, tack, throat, peak, clew, 0.07, [0, 0, side], canvas);
      }
      const mesh = p.mesh(mat, `${name}-${furled ? 'furled' : 'set'}`);
      const lines = new Parts();
      // The sheet to the deck, the topping lift to the masthead, the peak halyard.
      lines.line([-boomLen * 0.9, boomY(-boomLen * 0.9), 0], [-boomLen * 0.9, up(-boomLen * 0.9, -JAW + 0.9), 0]);
      lines.line([-boomLen + 0.1, boomY(-boomLen + 0.1), 0], [0.2, m.h - JAW - 0.05, 0]);
      if (!furled) lines.line(peak, [0.2, m.h - JAW, 0]);
      const rl = lines.rope(rope, `${name}-lines`);
      const sub = new THREE.Group();
      sub.add(mesh);
      if (rl) sub.add(rl);
      return sub;
    };
    const set = [make(false, 1), make(false, -1)];
    const furledG = make(true, 1);
    set[1].visible = false;
    g.add(set[0], set[1], furledG);
    group.add(g);
    rigs.push({ kind: 'gaff', group: g, set, furled: furledG, boomLen, swing: 0 });
  };
  buildGaffRig(fore.m, hull.fore_boom_m ?? 7.0, hull.fore_gaff_m ?? 5.2, 2.2, 'fore-rig');
  buildGaffRig(main.m, hull.main_boom_m ?? 10.2, hull.main_gaff_m ?? 6.0, 2.2, 'main-rig');

  // The square yards on the foremast: the fore (course) yard and the fore topsail yard,
  // braced together; the fore topsail set between them, or furled on its yard.
  {
    const m = fore.m;
    const yardY = m.h - 1.6;
    const topY = m.h + 0.4 + (m.top + 2.2) * 0.55;
    const course = hull.fore_yard_m ?? 12.0, topsail = hull.topsail_yard_m ?? 9.4;
    const g = new THREE.Group();
    g.name = 'fore-yards';
    const base = mastAt(m, 0);
    g.position.set(base[0], base[1], 0);
    g.rotation.order = 'ZYX';
    g.rotation.z = m.rake;
    const make = (furled) => {
      const p = new Parts();
      const yAt = (y, len) => { p.spar([0.35, y, -len / 2], [0.35, y, len / 2], 0.13, 0.13, { kind: SURF.paint, color: blackPaint }); };
      yAt(yardY, course);
      yAt(topY, topsail);
      const l = new Parts();
      for (const [y, len] of [[yardY, course], [topY, topsail]]) {
        for (const s of [-1, 1]) {
          l.line([0.35, y, s * len / 2], [0.35, y + 2.6, s * 0.3]);           // lifts
          l.line([0.35, y, s * len / 2], [-8.5, y - 6, s * 0.6]);             // braces, aft to the mainmast
          l.line([0.5, y - 0.75, s * len / 2.05], [0.5, y - 0.75, 0]);        // footropes
        }
      }
      if (furled) {
        furl(p, [0.45, topY, -topsail / 2.1], [0.45, topY, topsail / 2.1], 0.16, canvas);
        furl(p, [0.45, yardY, -course / 2.15], [0.45, yardY, course / 2.15], 0.13, canvas);
      } else {
        // The topsail set flying between the yards, bellied forward by a wind from abaft.
        const bot = yardY + 0.15, top = topY - 0.1;
        sailQuad(p, [0.5, bot, course / 2.08], [0.5, top, topsail / 2.05], [0.5, top, -topsail / 2.05], [0.5, bot, -course / 2.08], 0.07, [1, 0, 0], canvas);
        furl(p, [0.45, yardY, -course / 2.15], [0.45, yardY, course / 2.15], 0.13, canvas);
      }
      const sub = new THREE.Group();
      sub.add(p.mesh(mat, `fore-yards-${furled ? 'furled' : 'set'}`));
      const rl = l.rope(rope, 'fore-yard-lines');
      if (rl) sub.add(rl);
      return sub;
    };
    const set = make(false), furledG = make(true);
    g.add(set, furledG);
    group.add(g);
    rigs.push({ kind: 'yards', group: g, set: [set], furled: furledG, swing: 0 });
  }

  // The headsails: the fore staysail on the forestay and the jib on the jib stay, set or furled.
  {
    const g = new THREE.Group();
    g.name = 'headsails';
    const make = (furled, side) => {
      const p = new Parts();
      const fsTack = [stemTop[0] + 0.4, stemTop[1] + 0.3, 0];
      const fsHead = [lerp(fsTack[0], fore.head[0], 0.8), lerp(fsTack[1], fore.head[1] - 1.6, 0.8), 0];
      const jTack = [lerp(bsEnd[0], jbEnd[0], 0.55), lerp(bsEnd[1], jbEnd[1], 0.55), 0];
      const jHead = [lerp(jTack[0], fore.tHead[0], 0.82), lerp(jTack[1], fore.tHead[1] - 0.8, 0.82), 0];
      if (furled) {
        furl(p, fsTack, [lerp(fsTack[0], fore.head[0], 0.18), lerp(fsTack[1], fore.head[1], 0.18), 0], 0.12, canvas);
        furl(p, [bsEnd[0] - 0.3, bsEnd[1] + 0.2, 0], [jbEnd[0] - 0.6, jbEnd[1] + 0.1, 0], 0.12, canvas);
      } else {
        sailTri(p, fsTack, fsHead, [fore.m.x + 1.2, deckAt(fore.m.x) + 1.4, side * 1.2], 0.08, [0, 0, side], canvas);
        sailTri(p, jTack, jHead, [ln.x(0.03) + 0.6, ln.sheer(0.03) + 1.6, side * 1.4], 0.08, [0, 0, side], canvas);
      }
      const sub = new THREE.Group();
      sub.add(p.mesh(mat, `headsails-${furled ? 'furled' : 'set'}`));
      return sub;
    };
    const set = [make(false, 1), make(false, -1)];
    set[1].visible = false;
    const furledG = make(true, 1);
    g.add(set[0], set[1], furledG);
    group.add(g);
    rigs.push({ kind: 'head', group: g, set, furled: furledG, swing: 0 });
  }

  /* --- assemble --------------------------------------------------------------------- */
  const fixedMesh = fixed.mesh(mat, 'hull');
  group.add(fixedMesh);
  const standingLines = standing.rope(rope, 'standing-rigging');
  if (standingLines) group.add(standingLines);
  // The anchor's cable, from the hawse down into the water, shown while she lies at anchor.
  const cableParts = new Parts();
  cableParts.line([ln.x(0.04), ln.sheer(0.04) - 0.5, 0.45], [ln.x(0.04) + 4.5, -2.0, 0.6]);
  const cable = cableParts.rope(rope, 'anchor-cable');
  cable.visible = false;
  group.add(cable);

  /** Where the crew can stand (vessel frame) and which way they face, and the helm. */
  const deck = (x) => deckAt(x) + 0.06;
  const helm = { x: ln.x(0.93), z: 0.45 };
  const stations = [
    { id: 'helm', x: ln.x(0.93), z: -0.35, heading: 0, role: 'master' },
    { id: 'windlass', x: L * 0.36, z: 0.9, heading: 180, role: 'hand' },
    { id: 'main_hatch_s', x: L * 0.06, z: 1.5, heading: 270, role: 'hand' },
    { id: 'main_hatch_p', x: L * 0.12, z: -1.6, heading: 90, role: 'hand' },
    { id: 'fore_rail', x: L * 0.25, z: -B * 0.36, heading: 300, role: 'hand' },
    { id: 'galley', x: L * 0.17, z: 1.2, heading: 200, role: 'cook' },
    { id: 'main_rail', x: -L * 0.2, z: B * 0.35, heading: 80, role: 'mate' },
  ];
  const walk = [[L * 0.32, 1.4], [L * 0.0, 1.9], [-L * 0.22, 1.7], [-L * 0.22, -1.7], [L * 0.0, -1.9], [L * 0.32, -1.4]];

  let sails = 'furled', side = 1;
  /**
   * Set the canvas: 'set' (sailing), 'furled' (at anchor or moored) or 'bare' (unbent, laid up
   * for the winter). `windSide` is +1 when the wind comes over the port side (the booms swing
   * to starboard), -1 over the starboard side. `boomDeg` is how far off the centreline the
   * booms lie, `braceDeg` how far the yards are braced round.
   */
  function setSails(state, windSide = side, boomDeg = 22, braceDeg = 20) {
    sails = state;
    side = windSide >= 0 ? 1 : -1;
    for (const rig of rigs) {
      const setOn = state === 'set';
      rig.set.forEach((s, i) => { s.visible = setOn && (rig.set.length === 1 || (i === 0) === (side > 0)); });
      rig.furled.visible = !setOn;   // 'bare' (laid up) shows the spars with the canvas stowed on them
      if (rig.kind === 'gaff') rig.group.rotation.y = setOn ? side * boomDeg * DEG : 0;
      if (rig.kind === 'yards') rig.group.rotation.y = setOn ? -side * braceDeg * DEG : 0;
    }
    cable.visible = state !== 'set';
  }
  setSails('furled');

  return {
    group, rigs, mat, kind: 'topsail_schooner', masted: true, decked: true,
    dims: { length: L, beam: B, draft: T, freeboard: F, airDraft: masts[1].h + masts[1].top + 2 },
    deckY: deck, helm: { x: helm.x, y: deck(helm.x) + 1.62, z: helm.z }, stations, walk,
    hullOutline: () => {
      const pts = [];
      for (let i = 0; i <= 12; i++) { const t = i / 12; pts.push([ln.x(t), ln.half(t)]); }
      for (let i = 12; i >= 0; i--) { const t = i / 12; pts.push([ln.x(t), -ln.half(t)]); }
      return pts;
    },
    setSails,
    get sails() { return sails; },
    /** For the far view: drop the rope (a hairline at 300 m is noise) and the ratlines. */
    setDetail(near) {
      group.traverse((o) => { if (o.isLineSegments) o.visible = near && (o !== cable || sails !== 'set'); });
    },
    dispose() {
      group.traverse((o) => { o.geometry?.dispose?.(); });
      mat.dispose(); rope.dispose();
    },
  };
}

/* -------------------------------------------------------------------------- */
/* the trade boats of 1812: the Mackinaw boat and the bateau                    */
/* -------------------------------------------------------------------------- */

/**
 * An open boat of the fur trade. `kind` 'mackinaw_boat' (double-ended, raised ends, a mast and
 * a spritsail) or 'bateau' (flat-bottomed, flared, pointed both ends, oars only).
 */
export function buildTradeBoat(spec, { confidence = null, coarse = false } = {}) {
  const kind = spec.kind;
  const hull = spec.hull ?? {};
  const look = spec.look ?? {};
  const mack = kind === 'mackinaw_boat';
  const L = hull.length_m ?? (mack ? 11.5 : 9.6), B = hull.beam_m ?? (mack ? 2.7 : 2.0);
  const T = hull.draft_m ?? (mack ? 0.5 : 0.35), D = hull.depth_m ?? (mack ? 1.05 : 0.8);
  const r = rng(look.seed ?? 3);
  const mat = vesselMaterial({ seed: look.seed ?? 3, confidence, bottom: [40, 34, 28], boot: [52, 44, 36] });
  const rope = ropeMaterial();
  const group = new THREE.Group();
  group.name = `vessel-${spec.id}`;
  const ln = {
    half: (t) => (B / 2) * Math.pow(Math.sin(Math.PI * clamp(0.02 + 0.96 * t, 0, 1)), mack ? 0.85 : 0.7),
    keel: (t) => -T + (mack ? 0.35 : 0.12) * (Math.pow(Math.abs(2 * t - 1), 4)),
    sheer: (t) => (D - T) + (mack ? 0.55 : 0.3) * Math.pow(Math.abs(2 * t - 1), 3),
    full: (t) => (mack ? 2.6 : 4.5) - (mack ? 0.6 : 1.4) * Math.pow(Math.abs(2 * t - 1), 2),
    x: (t) => L / 2 - t * L,
  };
  const wood = lin(look.wood ?? [118 + r() * 20, 96 + r() * 14, 70 + r() * 10]);
  const tar = lin([40, 34, 28]);
  const paint = (y) => (y < 0.06 ? tar : wood);
  const p = new Parts();
  for (const side of [1, -1]) {
    p.grid(coarse ? 14 : 22, coarse ? 6 : 9, (ti, sj) => sectionPoint(ln, lerp(0.01, 0.99, ti), sj, side), {
      kind: SURF.hullPlank, color: (q) => paint(q[1]), surf: (q, ti, sj) => [q[0], sj * (D + B / 2)], flip: side < 0,
    });
  }
  // Stem and stern posts, the gunwales, thwarts, the floorboards.
  for (const t of [0.01, 0.99]) p.box([ln.x(t), (ln.keel(t) + ln.sheer(t)) / 2 + 0.1, 0], [0.05, (ln.sheer(t) - ln.keel(t)) / 2 + 0.12, 0.05], { kind: SURF.spar, color: wood });
  for (const side of [1, -1]) {
    p.grid(20, 1, (ti, sj) => { const t = lerp(0.02, 0.98, ti); return [ln.x(t), ln.sheer(t) + 0.02, side * (ln.half(t) - sj * 0.07)]; }, { kind: SURF.spar, color: wood, surf: (q) => [q[0], q[2]] });
  }
  const thwarts = mack ? [0.22, 0.36, 0.5, 0.64, 0.78] : [0.25, 0.42, 0.58, 0.75];
  for (const t of thwarts) p.box([ln.x(t), ln.sheer(t) - 0.28, 0], [0.13, 0.025, ln.half(t) - 0.06], { kind: SURF.deckPlank, color: wood });
  p.grid(16, 2, (ti, sj) => { const t = lerp(0.12, 0.88, ti); const w = ln.half(t) * 0.55; return [ln.x(t), ln.keel(t) + 0.14, lerp(-w, w, sj)]; }, { kind: SURF.deckPlank, color: wood, surf: (q) => [q[0], q[2] + 3] });
  // Bales of the trade under a tarpaulin amidships, and the oars laid along the thwarts.
  if (spec.laden !== false) {
    p.box([ln.x(0.5), ln.keel(0.5) + 0.42, 0], [1.3, 0.26, ln.half(0.5) * 0.6], { kind: SURF.canvas, color: lin([118, 104, 78]) });
  }
  const oars = mack ? 6 : 4;
  for (let k = 0; k < oars / 2; k++) {
    for (const side of [1, -1]) {
      const t = thwarts[k + 1] ?? 0.5;
      p.spar([ln.x(t) - 2.2, ln.sheer(t) + 0.05, side * (ln.half(t) - 0.15)], [ln.x(t) + 2.4, ln.sheer(t) + 0.05, side * (ln.half(t) - 0.25)], 0.035, 0.03, { color: wood });
    }
  }
  const rigs = [];
  if (mack) {
    // One mast stepped forward, with a spritsail: set or brailed up against the mast.
    const mx = ln.x(0.3), mh = 6.4;
    p.spar([mx, ln.keel(0.3) + 0.1, 0], [mx - 0.2, mh, 0], 0.075, 0.05, { color: wood });
    const g = new THREE.Group();
    g.position.set(mx, ln.sheer(0.3) + 0.25, 0);
    const make = (furled, side) => {
      const q = new Parts();
      if (furled) furl(q, [-0.1, 0.1, 0], [-0.15, mh - ln.sheer(0.3) - 0.6, 0], 0.13, lin([214, 202, 172]));
      else {
        const tack = [0, 0.05, 0], head = [-0.1, mh - ln.sheer(0.3) - 0.5, 0], peak = [-3.8, mh - ln.sheer(0.3) + 0.1, 0], clew = [-3.9, 0.15, 0];
        sailQuad(q, tack, head, peak, clew, 0.08, [0, 0, side], lin([214, 202, 172]));
        q.spar([0, 0.4, 0], [-3.9, mh - ln.sheer(0.3) + 0.1, 0], 0.035, 0.03, { color: wood });   // the sprit
      }
      const sub = new THREE.Group();
      sub.add(q.mesh(mat, `sprit-${furled ? 'furled' : 'set'}`));
      return sub;
    };
    const set = [make(false, 1), make(false, -1)];
    set[1].visible = false;
    const furledG = make(true, 1);
    g.add(set[0], set[1], furledG);
    group.add(g);
    rigs.push({ kind: 'gaff', group: g, set, furled: furledG, boomLen: 3.9, swing: 0 });
    const l = new Parts();
    l.line([mx - 0.15, mh - 0.3, 0], [ln.x(0.01), ln.sheer(0.01), 0]);
    for (const side of [1, -1]) l.line([mx - 0.12, mh - 0.6, 0], [mx - 0.2, ln.sheer(0.3), side * ln.half(0.3)]);
    const rl = l.rope(rope, 'stays');
    if (rl) group.add(rl);
  }
  group.add(p.mesh(mat, 'hull'));
  // The lid across the open hull, so the river does not show through it.
  const lidMat = waterLidMaterial();
  group.add(gunwaleLid(ln, 16, lidMat));

  let sails = 'furled', side = 1;
  function setSails(state, windSide = side, boomDeg = 30) {
    sails = state;
    side = windSide >= 0 ? 1 : -1;
    for (const rig of rigs) {
      rig.set.forEach((s, i) => { s.visible = state === 'set' && (i === 0) === (side > 0); });
      rig.furled.visible = state !== 'set';
      rig.group.rotation.y = state === 'set' ? side * boomDeg * DEG : 0;
    }
  }
  setSails('furled');
  const seatT = mack ? 0.88 : 0.86;
  return {
    group, rigs, mat, kind, masted: false, decked: false, hasSail: mack,
    dims: { length: L, beam: B, draft: T, freeboard: D - T, airDraft: mack ? 6.4 : 1 },
    deckY: (x) => ln.keel(clamp((L / 2 - x) / L, 0, 1)) + 0.2,
    helm: { x: ln.x(seatT), y: ln.keel(seatT) + 0.62 + 0.95, z: 0 },
    stations: [
      { id: 'stern', x: ln.x(0.86), z: 0, heading: 0, role: 'steersman', seated: true },
      { id: 'bow', x: ln.x(0.14), z: 0, heading: 0, role: 'bowman', seated: true },
    ],
    walk: [],
    hullOutline: () => {
      const pts = [];
      for (let i = 0; i <= 10; i++) { const t = i / 10; pts.push([ln.x(t), ln.half(t)]); }
      for (let i = 10; i >= 0; i--) { const t = i / 10; pts.push([ln.x(t), -ln.half(t)]); }
      return pts;
    },
    setSails,
    get sails() { return sails; },
    setDetail(near) { group.traverse((o) => { if (o.isLineSegments) o.visible = near; }); },
    dispose() { group.traverse((o) => { o.geometry?.dispose?.(); }); mat.dispose(); rope.dispose(); lidMat.dispose(); },
  };
}

/** How far under the sheer the lid lies, and how far inside the planking. */
export const LID_UNDER_SHEER_M = 0.03;
const LID_INSET_M = 0.03;

/**
 * The depth-only lid across an open hull's opening, a few centimetres under the sheer and
 * inside the planking. It used to lie 4 mm over the waterline, and a boat that rides the
 * water (vessels.js ride: a couple of centimetres of heave and a degree of roll in the river,
 * more in the lake, more again heeled under sail) put it under the river half the time, so
 * the water showed between the floorboards of a boat the visitor was steering (Kevin,
 * 2026-11-21, the Kinzies' Mackinaw boat in 1812). Up at the gunwale it stays dry until the
 * boat would ship water over her side, as crossings.js lays its own. It hides only what is
 * drawn after it (the river, at renderOrder 1), so the floor, thwarts, bales and crew drawn
 * before it still show.
 */
function gunwaleLid(ln, n, mat) {
  const lid = [];
  const at = (t) => {
    const y = ln.sheer(t) - LID_UNDER_SHEER_M;
    return [ln.x(t), y, Math.max(0, halfAtY(ln, t, y) - LID_INSET_M)];
  };
  for (let i = 0; i < n; i++) {
    const [xa, ya, wa] = at(0.03 + (0.94 * i) / n), [xb, yb, wb] = at(0.03 + (0.94 * (i + 1)) / n);
    lid.push(xa, ya, -wa, xb, yb, -wb, xb, yb, wb, xa, ya, -wa, xb, yb, wb, xa, ya, wa);
  }
  const lg = new THREE.BufferGeometry();
  lg.setAttribute('position', new THREE.Float32BufferAttribute(lid, 3));
  const lidMesh = new THREE.Mesh(lg, mat);
  lidMesh.renderOrder = 0.5;
  lidMesh.name = 'water-lid';
  return lidMesh;
}

/** The half-breadth of a hull's section at height y, at station t. */
function halfAtY(ln, t, y) {
  let lo = 0, hi = 1;
  for (let k = 0; k < 18; k++) {
    const mid = (lo + hi) / 2;
    if (sectionPoint(ln, t, mid)[1] < y) lo = mid; else hi = mid;
  }
  return sectionPoint(ln, t, lo)[2];
}

/* -------------------------------------------------------------------------- */
/* the small boats of 1835: a planked rowboat and a bark canoe                  */
/* -------------------------------------------------------------------------- */

/**
 * `kind` 'rowboat' (a lapstrake yawl of the river, a transom, three thwarts and a pair of oars
 * in their rowlocks) or 'bark_canoe' (bark sewn over ribs, high ends, a paddle across the
 * thwarts). The oars pull: `stroke(phase, on)` swings them with the pilot's pace.
 */
export function buildSmallBoat(spec, { confidence = null } = {}) {
  const kind = spec.kind;
  const canoe = kind === 'bark_canoe';
  const hull = spec.hull ?? {};
  const look = spec.look ?? {};
  const L = hull.length_m ?? (canoe ? 6.0 : 5.4), B = hull.beam_m ?? (canoe ? 1.1 : 1.6);
  const T = hull.draft_m ?? (canoe ? 0.2 : 0.25), D = hull.depth_m ?? (canoe ? 0.5 : 0.62);
  const r = rng(look.seed ?? 5);
  const mat = vesselMaterial({ seed: look.seed ?? 5, confidence, bottom: canoe ? [70, 52, 36] : [40, 34, 28], boot: canoe ? [92, 70, 48] : [56, 48, 38] });
  const rope = ropeMaterial();
  const group = new THREE.Group();
  group.name = `vessel-${spec.id}`;
  const ln = canoe ? {
    half: (t) => (B / 2) * Math.pow(Math.sin(Math.PI * clamp(0.015 + 0.97 * t, 0, 1)), 0.75),
    keel: (t) => -T + 0.1 * Math.pow(Math.abs(2 * t - 1), 3),
    sheer: (t) => (D - T) + 0.42 * Math.pow(Math.abs(2 * t - 1), 5),
    full: (t) => 2.4 - 0.6 * Math.pow(Math.abs(2 * t - 1), 2),
    x: (t) => L / 2 - t * L,
  } : {
    half: (t) => (B / 2) * Math.pow(Math.sin(Math.PI * clamp(0.05 + 0.75 * t, 0, 1)), 0.6),
    keel: (t) => -T + 0.06 * Math.pow(1 - t, 3),
    sheer: (t) => (D - T) + 0.16 * Math.pow(1 - t, 2) + 0.06 * t * t,
    full: () => 3.2,
    x: (t) => L / 2 - t * L,
  };
  const wood = lin(look.wood ?? (canoe ? [136, 108, 76] : [126 + r() * 18, 104 + r() * 12, 78 + r() * 10]));
  const bark = lin(look.bark ?? [118 + r() * 16, 92 + r() * 12, 66 + r() * 8]);
  const paintTop = lin(look.paint ?? ([[92, 84, 70], [62, 70, 64], [120, 106, 84]][Math.floor(r() * 3)]));
  const p = new Parts();
  for (const side of [1, -1]) {
    p.grid(canoe ? 18 : 16, canoe ? 7 : 8, (ti, sj) => sectionPoint(ln, lerp(0.01, canoe ? 0.99 : 0.995, ti), sj, side), {
      kind: SURF.hullPlank,
      color: canoe ? bark : paintTop,
      // Bark panels run long and wide; a lapstrake's strakes are a hand broad.
      surf: (q, ti, sj) => (canoe ? [q[0] * 0.5, sj * (D + B / 2) * 0.3] : [q[0], sj * (D + B / 2)]),
      flip: side < 0,
    });
  }
  if (!canoe) {
    // The transom.
    const t = 0.995, hb = ln.half(t), x = ln.x(t);
    p.grid(2, 4, (i, j) => [x, lerp(ln.keel(t) + 0.12, ln.sheer(t), i), lerp(-hb, hb, j) * (0.7 + 0.3 * i)],
      { kind: SURF.paint, color: paintTop, surf: (q) => [q[2], q[1]] });
  }
  // Gunwales, stem (and the canoe's stern) posts, thwarts, the bottom boards or ribs.
  for (const side of [1, -1]) {
    p.grid(18, 1, (ti, sj) => { const t = lerp(0.02, 0.985, ti); return [ln.x(t), ln.sheer(t) + 0.015, side * (ln.half(t) - sj * 0.05)]; },
      { kind: SURF.spar, color: wood, surf: (q) => [q[0], q[2]] });
  }
  p.box([ln.x(0.012), (ln.keel(0.012) + ln.sheer(0.012)) / 2 + 0.05, 0], [0.04, (ln.sheer(0.012) - ln.keel(0.012)) / 2 + 0.06, 0.035], { kind: SURF.spar, color: wood });
  if (canoe) p.box([ln.x(0.988), (ln.keel(0.988) + ln.sheer(0.988)) / 2 + 0.05, 0], [0.04, (ln.sheer(0.988) - ln.keel(0.988)) / 2 + 0.06, 0.035], { kind: SURF.spar, color: wood });
  const thwarts = canoe ? [0.3, 0.5, 0.7] : [0.3, 0.52, 0.8];
  for (const t of thwarts) p.box([ln.x(t), ln.sheer(t) - (canoe ? 0.08 : 0.2), 0], [0.08, 0.02, ln.half(t) - 0.03], { kind: SURF.deckPlank, color: wood });
  if (canoe) {
    for (let k = 0; k < 14; k++) {
      const t = 0.12 + k * 0.055;
      const pts = [];
      for (let j = 0; j <= 6; j++) pts.push(sectionPoint(ln, t, j / 6, -1).map((v, i) => (i === 2 ? v * 0.96 : i === 1 ? v + 0.012 : v)));
      for (let j = 6; j >= 0; j--) pts.push(sectionPoint(ln, t, j / 6, 1).map((v, i) => (i === 2 ? v * 0.96 : i === 1 ? v + 0.012 : v)));
      p.tube(pts, 0.012, { color: wood, sides: 4 });
    }
  } else {
    p.grid(12, 2, (ti, sj) => { const t = lerp(0.15, 0.9, ti); const w = ln.half(t) * 0.5; return [ln.x(t), ln.keel(t) + 0.09, lerp(-w, w, sj)]; },
      { kind: SURF.deckPlank, color: wood, surf: (q) => [q[0], q[2] + 3] });
  }
  group.add(p.mesh(mat, 'hull'));
  // The oars (or the paddle), on their own so they can pull.
  const oars = [];
  const rowT = canoe ? 0.7 : 0.52;
  const lock = { x: ln.x(rowT) - (canoe ? 0 : 0.35), y: ln.sheer(rowT) + 0.05, z: ln.half(rowT) };
  if (canoe) {
    const o = new Parts();
    o.spar([0.0, 0, -0.75], [0.0, 0, 0.6], 0.02, 0.018, { color: wood });
    o.box([0, 0, 0.75], [0.05, 0.008, 0.2], { kind: SURF.spar, color: wood });
    const g = new THREE.Group();
    g.add(o.mesh(mat, 'paddle'));
    g.position.set(ln.x(0.86) + 0.3, ln.sheer(0.86) + 0.12, 0);
    g.rotation.y = 0.1;
    group.add(g);
    oars.push({ g, side: 1, rest: true });
  } else {
    for (const side of [1, -1]) {
      const o = new Parts();
      o.spar([0, 0, -side * 0.9], [0, 0, side * 1.6], 0.025, 0.022, { color: wood });
      o.box([0, 0, side * 2.0], [0.06, 0.01, 0.42], { kind: SURF.spar, color: wood });
      const g = new THREE.Group();
      g.add(o.mesh(mat, 'oar'));
      g.position.set(lock.x, lock.y, side * lock.z);
      group.add(g);
      oars.push({ g, side });
    }
  }
  const lidMat = waterLidMaterial();
  group.add(gunwaleLid(ln, 12, lidMat));

  /** Swing the oars: `phase` 0..1 through one stroke; `on` false lays them in along the gunwales. */
  function stroke(phase, on) {
    for (const o of oars) {
      if (canoe) {
        o.g.rotation.set(on ? -0.9 : 0, on ? 0.2 + Math.sin(phase * Math.PI * 2) * 0.5 : 0.1, on ? 0.35 : 0);
        o.g.position.set(ln.x(0.86) + (on ? 0.05 : 0.3), ln.sheer(0.86) + (on ? 0.35 : 0.12), on ? 0.45 : 0);
        continue;
      }
      if (!on) { o.g.rotation.set(0, o.side * 1.38, 0); continue; }
      const a = phase * Math.PI * 2;
      // Feathered back, dipped and pulled: sweep about the rowlock, lift out on the return.
      o.g.rotation.set(o.side * (0.18 + 0.12 * Math.max(0, Math.sin(a))), o.side * 0.55 * Math.cos(a), 0, 'YXZ');
    }
  }
  stroke(0, false);
  const seatT = canoe ? 0.86 : 0.52;
  return {
    group, rigs: [], mat, kind, masted: false, decked: false, hasSail: false, stroke,
    dims: { length: L, beam: B, draft: T, freeboard: D - T, airDraft: 0.8 },
    deckY: (x) => ln.keel(clamp((L / 2 - x) / L, 0, 1)) + 0.15,
    helm: { x: ln.x(seatT), y: ln.keel(seatT) + 0.42 + 0.85, z: 0 },
    stations: [{ id: 'oars', x: ln.x(seatT), z: 0, heading: canoe ? 0 : 180, role: 'rower', seated: true }],
    walk: [],
    hullOutline: () => {
      const pts = [];
      for (let i = 0; i <= 8; i++) { const t = i / 8; pts.push([ln.x(t), ln.half(t)]); }
      for (let i = 8; i >= 0; i--) { const t = i / 8; pts.push([ln.x(t), -ln.half(t)]); }
      return pts;
    },
    setSails() {},
    get sails() { return 'none'; },
    setDetail() {},
    dispose() { group.traverse((o) => { o.geometry?.dispose?.(); }); mat.dispose(); rope.dispose(); lidMat.dispose(); },
  };
}

/** Build whatever kind a record names. */
export function buildVessel(spec, opts = {}) {
  if (spec.kind === 'topsail_schooner') return buildSchooner(spec, opts);
  if (spec.kind === 'mackinaw_boat' || spec.kind === 'bateau') return buildTradeBoat(spec, opts);
  if (spec.kind === 'rowboat' || spec.kind === 'bark_canoe') return buildSmallBoat(spec, opts);
  throw new Error(`vessel: unknown kind '${spec.kind}'`);
}

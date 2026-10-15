/**
 * T-2109 — a cheaper glass for a model whose GLB asks for transmission.
 *
 * 1904's Glessner house carries `KHR_materials_transmission` on its one glass
 * material (both the full and the `.light` model). Any visible transmissive
 * material makes three draw every opaque object a second time into a target
 * the glass samples, and T-2099's still-frame reading put that pass at about
 * half of every frame at the 1904 landing, at both viewports.
 *
 * Two cheaper glasses replace it at load, without touching the GLB (the file
 * still says what the glass is; this is how the browser draws it):
 *
 *   clear — see-through: no transmission, alpha-blended, the interior shows
 *           through un-refracted. One sorted transparent batch.
 *   dark  — opaque dark plate: no transmission, no blending; reads the way
 *           plate glass reads from a street in daylight. Batches with the
 *           house's own opaque surfaces.
 *
 * `transmission` keeps the GLB's own glass.
 *
 * T-2183 (owner, 2026-10-08): dark panes are the default at every detail
 * setting, including full inspection. T-2109 previously applied the choice
 * only at balanced and light. `?glass=transmission|clear|dark` still overrides
 * the default for comparison; the underlying GLB material is unchanged.
 *
 * T-2213 (GA-12): every dark pane used to be the same plate — one albedo, one
 * roughness, one plane — so every light on a front caught the same diagonal of
 * sky. The dark pane now reads each pane as the thing it is, still without
 * touching the GLB: `paneLayout()` finds the panes (each is its own little slab
 * in the mesh) and the windows they stack into, and the shader gives each pane
 * its own few hundredths of a radian out of plane and its own sheen, a shallow
 * backing whose head and jambs fall into shadow behind the glass, and each
 * window a pale roller blind at its own drop, seen at its depth behind the
 * glass rather than painted on it. The blinds stand on the Glessner front
 * photographed with the Keith house (`a18-gh-glessner-front-with-keith`, undated,
 * probably 1890s-1920s; cited, not derived from): pale shades at the meeting
 * rail, part-way and up, window by window. Which window has which drop is
 * reconstructed (docs/LIBERTIES.md). The dark default and its cost are kept: one
 * opaque batch, no transmission, a few dozen instructions on glass alone.
 */
import * as THREE from 'three';
import { captureHooks, registerPatch } from './batch-material.js';

export const GLASS_MODES = Object.freeze(['transmission', 'clear', 'dark']);
/** The GLB's own glass: what a caller that names no mode gets. */
export const DEFAULT_GLASS = 'transmission';
/** The owner's pick, per Scene detail setting (T-2109, answer c). */
export const GLASS_BY_DETAIL = Object.freeze({ full: 'dark', balanced: 'dark', light: 'dark' });

/** `?glass=clear|dark|transmission`, or null when the address names none. */
export function readGlassRequest(params) {
  const asked = params?.get?.('glass');
  return GLASS_MODES.includes(asked) ? asked : null;
}

/** The glass drawn at `detail`: the address's own mode when it names one,
 * otherwise the owner's pick for that setting. An unknown setting keeps the
 * GLB's glass rather than guessing a cheaper one. */
export function glassForDetail(detail, requested = null) {
  if (GLASS_MODES.includes(requested)) return requested;
  return Object.hasOwn(GLASS_BY_DETAIL, detail) ? GLASS_BY_DETAIL[detail] : DEFAULT_GLASS;
}

export function isTransmissive(material) {
  return Boolean(material && material.transmission > 0);
}

/** The material to draw instead of `material`, or `material` itself when it is
 * not transmissive or the mode keeps transmission. Never mutates its input. */
export function cheapenGlass(material, mode = DEFAULT_GLASS) {
  if (mode === 'transmission' || !isTransmissive(material)) return material;
  const glass = new THREE.MeshStandardMaterial({
    name: material.name,
    color: material.color.clone(),
    roughness: material.roughness,
    metalness: material.metalness,
    side: material.side,
    envMap: material.envMap ?? null,
    envMapIntensity: material.envMapIntensity ?? 1,
  });
  if (mode === 'clear') {
    // The GLB's near-white tint at full strength would read as frosted; a
    // quarter of it over the room behind is a pane with the room seen through.
    glass.color.multiplyScalar(0.35);
    glass.transparent = true;
    glass.opacity = 0.28;
    glass.depthWrite = false;
  } else {
    glass.color.multiplyScalar(0.12);
    patchPanes(glass);
  }
  glass.userData.cheapenedFrom = 'KHR_materials_transmission';
  glass.userData.glassMode = mode;
  return glass;
}

/** The key a pane-patched batch is grouped under, and the program it compiles. */
export const PANE_PATCH = 'glass-panes-v1';

/**
 * A blind's drop is a fraction of its window's height, from the head. `RAIL` is
 * the meeting rail, where most of the front's shades stand in the photograph;
 * three of ten windows have their shade up. Dealt by the window's own seed.
 */
const RAIL = -1;
export const BLIND_DROPS = Object.freeze([0, 0, 0, 0.16, 0.27, RAIL, RAIL, RAIL, 0.4, 0.68]);
/** No blind on a light narrower than this (a door's or a transom's grid of
 * small lights) or on a window shorter than this (a cellar light). */
export const BLIND_MIN_WIDTH_M = 0.3;
export const BLIND_MIN_HEIGHT_M = 0.6;

/** A number in [0, 1) that depends only on where a thing is, to the millimetre,
 * so the same pane draws the same at every detail setting and on every load. */
export function seedAt(x, y, z) {
  const q = (v) => Math.round(v * 1000);
  let h = 2166136261 >>> 0;
  for (const v of [q(x), q(y), q(z)]) {
    h = Math.imul(h ^ (v & 0xffff), 16777619) >>> 0;
    h = Math.imul(h ^ ((v >>> 16) & 0xffff), 16777619) >>> 0;
  }
  h ^= h >>> 15; h = Math.imul(h, 0x2c1b3c6d) >>> 0; h ^= h >>> 12;
  return (h >>> 0) / 4294967296;
}

/**
 * The panes and windows in a glass mesh. `position` is xyz floats in the
 * structure's own frame (metres, y up); `index` its triangles, or null.
 * A pane is a connected island (vertices joined by triangles or by sharing a
 * point); a window is panes that face the same way in the same plane, overlap
 * across, and stack with a gap no deeper than a meeting rail or transom bar.
 * Returns per-vertex `pane` (u, v, width m, height m) and `win` (v in window,
 * window height m, pane seed, blind drop), and the panes and windows found.
 */
export function paneLayout(position, index = null) {
  const count = position.length / 3;
  const tris = index ?? Uint32Array.from({ length: count }, (_, i) => i);
  const parent = Int32Array.from({ length: count }, (_, i) => i);
  const find = (x) => { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
  const join = (a, b) => { a = find(a); b = find(b); if (a !== b) parent[a] = b; };
  for (let k = 0; k + 2 < tris.length; k += 3) { join(tris[k], tris[k + 1]); join(tris[k], tris[k + 2]); }
  const at = new Map();
  for (let i = 0; i < count; i += 1) {
    const key = `${Math.round(position[i * 3] * 1000)},${Math.round(position[i * 3 + 1] * 1000)},${Math.round(position[i * 3 + 2] * 1000)}`;
    if (at.has(key)) join(i, at.get(key)); else at.set(key, i);
  }
  const islandOf = new Int32Array(count);
  const panes = [];
  const byRoot = new Map();
  for (let i = 0; i < count; i += 1) {
    const r = find(i);
    if (!byRoot.has(r)) { byRoot.set(r, panes.length); panes.push({ cxx: 0, cxz: 0, czz: 0, verts: [] }); }
    islandOf[i] = byRoot.get(r);
    panes[islandOf[i]].verts.push(i);
  }
  // Orientation: the principal horizontal direction of the island's faces, area-weighted.
  for (let k = 0; k + 2 < tris.length; k += 3) {
    const [a, b, c] = [tris[k], tris[k + 1], tris[k + 2]];
    const ux = position[b * 3] - position[a * 3], uy = position[b * 3 + 1] - position[a * 3 + 1], uz = position[b * 3 + 2] - position[a * 3 + 2];
    const vx = position[c * 3] - position[a * 3], vy = position[c * 3 + 1] - position[a * 3 + 1], vz = position[c * 3 + 2] - position[a * 3 + 2];
    const nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
    const len = Math.hypot(nx, ny, nz);
    if (len === 0 || Math.abs(ny) > 0.5 * len) continue;
    const p = panes[islandOf[a]];
    p.cxx += (nx * nx) / len; p.cxz += (nx * nz) / len; p.czz += (nz * nz) / len;
  }
  for (const p of panes) {
    const th = 0.5 * Math.atan2(2 * p.cxz, p.cxx - p.czz);
    p.n = [Math.cos(th), Math.sin(th)];
    p.t = [-p.n[1], p.n[0]];
    p.flat = p.cxx + p.czz === 0;
    let sMin = Infinity, sMax = -Infinity, yMin = Infinity, yMax = -Infinity, d = 0, cx = 0, cz = 0;
    for (const i of p.verts) {
      const x = position[i * 3], y = position[i * 3 + 1], z = position[i * 3 + 2];
      const s = x * p.t[0] + z * p.t[1];
      sMin = Math.min(sMin, s); sMax = Math.max(sMax, s); yMin = Math.min(yMin, y); yMax = Math.max(yMax, y);
      d += x * p.n[0] + z * p.n[1]; cx += x; cz += z;
    }
    const m = p.verts.length;
    Object.assign(p, { sMin, sMax, yMin, yMax, d: d / m, cx: cx / m, cz: cz / m,
      width: sMax - sMin, height: yMax - yMin });
    p.seed = seedAt(p.cx, (yMin + yMax) / 2, p.cz);
    delete p.cxx; delete p.cxz; delete p.czz;
  }
  // Windows: panes in one plane that overlap across and stack.
  const wp = Int32Array.from({ length: panes.length }, (_, i) => i);
  const wfind = (x) => { while (wp[x] !== x) { wp[x] = wp[wp[x]]; x = wp[x]; } return x; };
  if (panes.length <= 4000) {
    for (let i = 0; i < panes.length; i += 1) {
      const a = panes[i];
      if (a.flat) continue;
      for (let j = i + 1; j < panes.length; j += 1) {
        const b = panes[j];
        if (b.flat || Math.abs(a.n[0] * b.n[0] + a.n[1] * b.n[1]) < 0.985) continue;
        if (Math.abs(b.cx * a.n[0] + b.cz * a.n[1] - a.d) > 0.2) continue;
        const sc = b.cx * a.t[0] + b.cz * a.t[1];
        const overlap = Math.min(a.sMax, sc + b.width / 2) - Math.max(a.sMin, sc - b.width / 2);
        if (overlap < 0.5 * Math.min(a.width, b.width)) continue;
        if (Math.max(b.yMin - a.yMax, a.yMin - b.yMax) > 0.35) continue;
        const ra = wfind(i), rb = wfind(j);
        if (ra !== rb) wp[ra] = rb;
      }
    }
  }
  const windows = new Map();
  panes.forEach((p, i) => {
    const r = wfind(i);
    const w = windows.get(r) ?? { panes: [], yMin: Infinity, yMax: -Infinity, cx: 0, cz: 0 };
    w.panes.push(p); w.yMin = Math.min(w.yMin, p.yMin); w.yMax = Math.max(w.yMax, p.yMax);
    w.cx += p.cx; w.cz += p.cz;
    windows.set(r, w);
  });
  for (const w of windows.values()) {
    w.cx /= w.panes.length; w.cz /= w.panes.length;
    w.height = w.yMax - w.yMin;
    w.seed = seedAt(w.cx + 0.5, (w.yMin + w.yMax) / 2, w.cz + 0.5);
    w.blind = blindFor(w);
    for (const p of w.panes) p.window = w;
  }
  const pane = new Float32Array(count * 4);
  const win = new Float32Array(count * 4);
  for (let i = 0; i < count; i += 1) {
    const p = panes[islandOf[i]];
    const w = p.window;
    const x = position[i * 3], y = position[i * 3 + 1], z = position[i * 3 + 2];
    const s = x * p.t[0] + z * p.t[1];
    pane.set([p.width > 0 ? (s - p.sMin) / p.width : 0.5, p.height > 0 ? (y - p.yMin) / p.height : 0.5,
      p.width, p.height], i * 4);
    win.set([w.height > 0 ? (y - w.yMin) / w.height : 0.5, w.height, p.seed, w.blind], i * 4);
  }
  return { pane, win, panes, windows: [...windows.values()] };
}

/** The drop of a window's blind, 0 for none. */
export function blindFor(w) {
  const narrowest = Math.min(...w.panes.map((p) => p.width));
  if (w.panes.some((p) => p.flat) || narrowest < BLIND_MIN_WIDTH_M || w.height < BLIND_MIN_HEIGHT_M) return 0;
  const drop = BLIND_DROPS[Math.min(BLIND_DROPS.length - 1, Math.floor(w.seed * BLIND_DROPS.length))];
  if (drop !== RAIL) return drop;
  // The meeting rail: the head of the window down to the top of its lower lights.
  const lower = w.panes.filter((p) => p.yMax < w.yMax - 0.05);
  if (!lower.length) return 0.5;
  const rail = Math.max(...lower.map((p) => p.yMax));
  return Math.min(0.9, (w.yMax - rail) / w.height + 0.01);
}

/** Writes `_pane` and `_paneWin` on a pane-patched geometry, in its structure's frame. */
export function writePaneAttributes(geometry, THREEns = THREE) {
  const pos = geometry.getAttribute('position');
  const index = geometry.getIndex();
  const { pane, win } = paneLayout(pos.array, index ? index.array : null);
  geometry.setAttribute('_pane', new THREEns.BufferAttribute(pane, 4));
  geometry.setAttribute('_paneWin', new THREEns.BufferAttribute(win, 4));
  return geometry;
}

/**
 * The pane shader. Two injections: the albedo before `<color_fragment>` (so the
 * building's tone and the confidence tint still apply over it), and the pane's
 * tilt and sheen after `<normal_fragment_maps>`.
 */
const PANE_DECL = /* glsl */`
varying vec4 vChiPane;
varying vec4 vChiPaneWin;
`;
// Depths behind the glass, metres: where the blind hangs and where the backing's
// head and sill stand. Blind albedo as a multiple of the dark pane's own (≈0.11),
// so a blind is a pale holland shade seen through glass: about 0.36 linear.
const PANE_ALBEDO = /* glsl */`
  float chiFace = gl_FrontFacing ? 1.0 : -1.0;
  vec3 chiN = normalize(vNormal) * chiFace;
  vec3 chiV = normalize(vViewPosition);
  vec3 chiUp = normalize((viewMatrix * vec4(0.0, 1.0, 0.0, 0.0)).xyz);
  float chiSeed = vChiPaneWin.z;
  float chiS1 = fract(chiSeed * 7.13 + 0.31);
  float chiS2 = fract(chiSeed * 13.7 + 0.57);
  float chiLift = -dot(chiV, chiUp) / max(dot(chiV, chiN), 0.25);
  {
    float h = max(vChiPane.w, 0.05);
    float w = max(vChiPane.z, 0.05);
    float vb = vChiPane.y + chiLift * 0.10 / h;
    float edgeV = clamp(min(vb, 1.0 - vb) * h / 0.08, 0.0, 1.0);
    float edgeU = clamp(min(vChiPane.x, 1.0 - vChiPane.x) * w / 0.05, 0.0, 1.0);
    vec3 gain = vec3(mix(0.5, 1.0, edgeV * edgeU) * (0.8 + 0.4 * chiS1));
    float drop = vChiPaneWin.w;
    if (drop > 0.0 && vChiPaneWin.y > 0.0) {
      float vw = vChiPaneWin.x + chiLift * 0.06 / vChiPaneWin.y;
      float above = vw - (1.0 - drop);
      float cover = step(0.0, above);
      float hem = 1.0 - smoothstep(0.012, 0.03, above * vChiPaneWin.y);
      float shade = mix(1.0, 0.62, hem) * (0.88 + 0.24 * fract(chiSeed * 3.1 + 0.7))
        * mix(0.8, 1.0, edgeU);
      gain = mix(gain, 4.6 * shade * vec3(1.0, 0.95, 0.84), cover);
    }
    diffuseColor.rgb *= gain;
  }
`;
const PANE_SHEEN = /* glsl */`
  {
    vec3 across = cross(chiUp, normal);
    across = dot(across, across) > 1e-6 ? normalize(across) : vec3(1.0, 0.0, 0.0);
    float h = max(vChiPane.w, 0.05);
    float w = max(vChiPane.z, 0.05);
    // Each pane a little out of plane, and the long low wave of old plate.
    float tiltA = (chiS1 - 0.5) * 0.06 + 0.006 * sin(vChiPane.x * w * 6.0 + chiSeed * 40.0);
    float tiltB = (chiS2 - 0.5) * 0.06 + 0.006 * sin(vChiPane.y * h * 5.0 + chiSeed * 23.0);
    normal = normalize(normal + tiltA * across + tiltB * chiUp);
    roughnessFactor = clamp(roughnessFactor * (0.6 + 1.2 * fract(chiSeed * 3.7 + 0.11)) + 0.02, 0.03, 0.22);
  }
`;

function patchPanes(material) {
  const batchHooks = captureHooks(material);
  material.userData.glassPanes = PANE_PATCH;
  const prior = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prior?.(shader, renderer);
    shader.vertexShader = 'attribute vec4 _pane;\nattribute vec4 _paneWin;\n' + PANE_DECL
      + shader.vertexShader.replace('#include <begin_vertex>',
        '#include <begin_vertex>\n  vChiPane = _pane;\n  vChiPaneWin = _paneWin;');
    shader.fragmentShader = PANE_DECL + shader.fragmentShader
      .replace('#include <color_fragment>', PANE_ALBEDO + '#include <color_fragment>')
      .replace('#include <normal_fragment_maps>', '#include <normal_fragment_maps>' + PANE_SHEEN);
  };
  material.customProgramCacheKey = () => PANE_PATCH;
  registerPatch(material, batchHooks, 'pane-v1', { patch: PANE_PATCH });
  material.needsUpdate = true;
}

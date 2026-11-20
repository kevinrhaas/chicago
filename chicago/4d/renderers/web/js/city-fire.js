// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * city-fire.js — the Great Fire burns the 1871 city on its own clock (T-3687).
 *
 * The owner, 2026-11-19: "i definitiely want a follow the chicago fire like a timeline and you
 * follow the start of the fire and you see it engulf an area and then you move to the next stop
 * and see that, through burning the north side, etc. you shoul be sure to make it seasonal time
 * of day etc", "its ok and good if we look at the main landmarks and watch them burn along with
 * the whole streetscape".
 *
 * Where and when it burned is fire-map.js's (data/fire/1871.json, from the accounts). This draws
 * it, at the fire time `set(minutes)` names, and lets that time run on (`rate` fire seconds to
 * the real second) so a stop watches the front come down its street:
 *
 *   the city's own buildings   the 1871 context city's instances (city-context.js) and every
 *                              named structure in the buildings layer: blackened, glowing at
 *                              their windows while they burn (the near kit's material is taught
 *                              to read a heat packed into each instance's colour), frame houses
 *                              brought down to a black slab with a chimney left standing,
 *                              masonry left as charred walls, a share of them fallen. Per-instance
 *                              colour and matrix only, written when a building's state moves.
 *   the fire as drawn          fort-fire.js's flames, smoke and sparks: near buildings burn at
 *                              every window and over the roof, farther ones as one flame each,
 *                              the far city in whole-block flames; a plume of big lit smoke
 *                              puffs leaning down the gale, the ground glowing under the fires.
 *   the light                  two orange point lights on the strongest fires near the eye (the
 *                              walls, the street and faces), and a glow in the sky over the
 *                              burning district, red at night and faint by day (onDaylight).
 *
 * Nothing here is built until a fire time is first set; free walk never loads this module.
 * The traps fort-fire.js lists hold here: flames draw after smoke; value noise is fed small
 * numbers; emissives stay modest (ACES and the night's exposure whiten them, so the gain falls
 * with the eye's adaptation); the sky glow is unlit and so listens to the daylight.
 */
import * as THREE from 'three';
import { createFireFx } from './fort-fire.js';
import { onDaylight } from './time-of-day.js';
import { createFireMap, burnState, minutesOf, isoOf, hash01 } from './fire-map.js';

const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const lerp = (a, b, t) => a + (b - a) * t;

const CHAR = [0.075, 0.064, 0.058];   // burnt timber, as a multiplier of the paint
const SOOT = [0.2, 0.17, 0.155];      // stone and brick walls, smoked black but still brick
const TREE = [0.16, 0.13, 0.1];       // a scorched tree
const FIRE_UNIFORMS = { uFireTime: { value: 0 }, uFireGain: { value: 1 } };

/** How much each detail tier draws. A phone keeps the whole fire, in fewer, larger pieces. */
export function cityFireBudget(tier = 'full') {
  return tier === 'light'
    ? { flames: 150, smoke: 150, sparks: 110, plume: 64, octaves: 3, spacing: 1.4, nearR: 130, midR: 560, perBuilding: 7, chimneys: 260, chimneyR: 260, cell: 160 }
    : tier === 'balanced'
      ? { flames: 260, smoke: 260, sparks: 200, plume: 100, octaves: 4, spacing: 1.15, nearR: 190, midR: 760, perBuilding: 12, chimneys: 600, chimneyR: 420, cell: 130 }
      : { flames: 360, smoke: 360, sparks: 300, plume: 140, octaves: 4, spacing: 1, nearR: 250, midR: 950, perBuilding: 18, chimneys: 1100, chimneyR: 560, cell: 110 };
}

/** The near kit material learns the heat packed in each instance's colour (see `pack`). */
const patched = new WeakSet();
function teachNear(material) {
  if (!material || patched.has(material)) return;
  patched.add(material);
  const prior = material.onBeforeCompile;
  material.onBeforeCompile = function cityFireNear(shader, renderer) {
    if (typeof prior === 'function') prior.call(this, shader, renderer);
    shader.uniforms.uFireTime = FIRE_UNIFORMS.uFireTime;
    shader.uniforms.uFireGain = FIRE_UNIFORMS.uFireGain;
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying float vFireHeat;\nvarying float vFireSeed;\nvarying float vFireY;')
      .replace('#include <color_vertex>', `#include <color_vertex>
        vFireHeat = 0.0; vFireSeed = 0.0; vFireY = position.y;
        #ifdef USE_INSTANCING_COLOR
          { float hq = floor(vColor.r * 0.5); vFireHeat = hq / 15.0; vColor.r -= hq * 2.0; }
        #endif
        #ifdef USE_INSTANCING
          vFireSeed = fract(instanceMatrix[3].x * 0.0173 + instanceMatrix[3].z * 0.0071) * 6.2831;
        #endif`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform float uFireTime;\nuniform float uFireGain;\nvarying float vFireHeat;\nvarying float vFireSeed;\nvarying float vFireY;')
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
        if (vFireHeat > 0.001) {
          #ifdef USE_MAP
            float fireTex = dot(sampledDiffuseColor.rgb, vec3(0.3, 0.59, 0.11));
          #else
            float fireTex = 0.5;
          #endif
          // The openings (the kit's darkest texels, read in linear light) blaze; the wall
          // between them barely glows (its own lit face is the point lights' work).
          float fireWin = smoothstep(0.02, 0.004, fireTex);
          float fireFl = 0.72 + 0.28 * sin(uFireTime * 7.0 + vFireSeed + vFireY * 2.1) * sin(uFireTime * 2.9 + vFireSeed * 1.7);
          totalEmissiveRadiance += vec3(1.0, 0.3, 0.06) * vFireHeat * (0.02 + 0.45 * fireWin) * fireFl * uFireGain;
        }`);
  };
  const priorKey = typeof material.customProgramCacheKey === 'function' ? material.customProgramCacheKey.bind(material) : () => '';
  material.customProgramCacheKey = () => `${priorKey()}|city-fire-near-v1`;
  material.needsUpdate = true;
}

/** A sky that glows over the burning district: unlit, so it follows the daylight. */
function makeSkyGlow() {
  const mat = new THREE.ShaderMaterial({
    uniforms: { uDir: { value: new THREE.Vector3(1, 0, 0) }, uSpread: { value: 0.5 }, uK: { value: 0 }, uAround: { value: 0 } },
    vertexShader: /* glsl */`
      varying vec3 vDir;
      void main() { vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: /* glsl */`
      uniform vec3 uDir; uniform float uSpread; uniform float uK; uniform float uAround;
      varying vec3 vDir;
      void main() {
        vec3 d = normalize(vDir);
        vec2 h = normalize(d.xz + vec2(1e-5)), f = normalize(uDir.xz + vec2(1e-5));
        float ang = acos(clamp(dot(h, f), -1.0, 1.0));
        float side = exp(-ang * ang / (2.0 * uSpread * uSpread));
        float up = max(d.y, 0.0);
        float low = exp(-up / 0.45) * smoothstep(-0.04, 0.03, d.y);
        float g = uK * low * (side + uAround * 0.4) + uK * uAround * 0.2 * exp(-up / 0.7);
        gl_FragColor = vec4(vec3(1.0, 0.32, 0.07) * g, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
    side: THREE.BackSide, transparent: true, depthWrite: false, depthTest: true, fog: false,
    blending: THREE.AdditiveBlending,
  });
  mat.name = 'city_fire_sky';
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(1, 32, 16), mat);
  mesh.name = 'city-fire:sky'; mesh.frustumCulled = false; mesh.renderOrder = -1; mesh.visible = false;
  return mesh;
}

/**
 * The fire over a city. `context()` is the 1871 context city (city-context.js; a detail
 * change builds a new one), `buildings()` the named structures' layer (buildings.js),
 * `tier()` the detail level, `groundAt(e, n)` the ground's height.
 */
export function createCityFire({ doc, parent, context = () => null, buildings = () => null, tier = () => 'full', groundAt = () => 3.2 } = {}) {
  const map = createFireMap(doc);
  const group = new THREE.Group(); group.name = 'city-fire'; parent?.add?.(group);
  let minute = null, rate = 0, budget = cityFireBudget(tier()), budgetTier = tier();
  let fx = null, plume = null, sky = null, lights = [], chimneys = null;
  let city = null, recs = [], nearEntries = [], farEntries = [], named = [], namedLayer = null;
  let active = [], stateClock = Infinity, lastMinute = null, visual = 0;
  let night = 0, adapt = 1;
  const v3 = new THREE.Vector3(), cam = new THREE.Vector3(), fwd = new THREE.Vector3();
  const rnd = (() => { let s = 0x3687; return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; })();
  const windWorld = new THREE.Vector3(map.wind.e, 0, -map.wind.n).normalize();

  const unDaylight = onDaylight(({ display = 1, grade }) => {
    night = 1 - clamp(display, 0, 1);
    adapt = grade?.adapt ?? 1;
    const g = 1 / adapt ** 0.65;
    FIRE_UNIFORMS.uFireGain.value = g;
    fx?.setGain(g); plume?.setGain(g);
  });

  function build() {
    if (fx) return;
    budget = cityFireBudget(budgetTier = tier());
    fx = createFireFx(group, { budget, wind: windWorld, windMps: map.wind.mps * 0.5 });
    plume = createFireFx(group, { budget: { flames: 1, smoke: budget.plume, sparks: 1, octaves: 2, spacing: 1 }, wind: windWorld, windMps: map.wind.mps });
    fx.group.name = 'city-fire:near'; plume.group.name = 'city-fire:plume';
    const g = 1 / adapt ** 0.65; fx.setGain(g); plume.setGain(g);
    sky = makeSkyGlow(); group.add(sky);
    for (let i = 0; i < 2; i++) {
      const l = new THREE.PointLight(0xff8a3a, 0, 420, 2);
      l.name = `city-fire:light:${i}`; l.castShadow = false; l.visible = false;
      lights.push(l); group.add(l);
    }
    const box = new THREE.BoxGeometry(1, 1, 1); box.translate(0, 0.5, 0);
    const brick = new THREE.MeshStandardMaterial({ color: 0x3a2a22, roughness: 0.95, metalness: 0 });
    brick.name = 'city_fire_chimney';
    chimneys = new THREE.InstancedMesh(box, brick, budget.chimneys);
    chimneys.name = 'city-fire:chimneys'; chimneys.count = 0; chimneys.castShadow = false; chimneys.receiveShadow = true;
    chimneys.frustumCulled = false;
    group.add(chimneys);
  }

  // ── the city's buildings ───────────────────────────────────────────────────────────────────
  function kindOf(r) {
    const m = String(r.row?.construction ?? r.row?.material ?? r.t?.material ?? '');
    return /brick|stone|masonry|iron/.test(m) ? 'masonry' : 'frame';
  }
  function recordOf(r, byRow) {
    if (byRow.has(r)) return byRow.get(r);
    let rec = null;
    const key = String(r.id ?? `${r.e},${r.n}`);
    const tc = map.catchAt(r.e, r.n, key);
    if (tc !== null) {
      const t = r.t ?? {};
      const ridge = r.h * ((t.eave_m ?? r.h) + (t.rise_m ?? 0)) / (t.eave_m ?? r.h);
      rec = { key, e: r.e, n: r.n, x: r.e, z: -r.n, base: r.base, h: r.h, top: r.base + ridge, w: r.w, d: r.d,
        pts: r.pts ?? null, storeys: Math.max(1, t.storeys ?? Math.round(r.h / 3.6)), area: r.w * r.d,
        kind: r.isTree ? 'tree' : kindOf(r), tc, wallsFall: hash01(`${key}:walls`) < (map.model.masonry?.walls_fall_share ?? 0.3),
        st: null, code: -1, m: -1, emit: null, chimney: null };
      recs.push(rec);
    }
    byRow.set(r, rec);
    return rec;
  }
  function bindCity() {
    const c = context();
    if (c === city && (nearEntries.length || farEntries.length || !c)) return;
    city = c; recs = []; nearEntries = []; farEntries = [];
    if (!c?.group) return;
    const byRow = new Map();
    c.group.traverse((o) => {
      const tierName = o.userData?.contextTier;
      if (tierName === 'near' && o.isInstancedMesh && o.instanceColor && Array.isArray(o.userData.rows)) {
        teachNear(o.material);
        o.userData.rows.forEach((r, i) => {
          const rec = recordOf(r, byRow);
          if (!rec) return;
          nearEntries.push({ mesh: o, i, rec, m0: o.instanceMatrix.array.slice(i * 16, i * 16 + 16),
            c0: o.instanceColor.array.slice(i * 3, i * 3 + 3), code: -1 });
        });
      } else if (tierName === 'far' && o.isMesh && Array.isArray(o.userData.ranges)) {
        const index = o.geometry.index?.array, pos = o.geometry.getAttribute('position'), col = o.geometry.getAttribute('color');
        if (!index || !pos || !col) return;
        for (const range of o.userData.ranges) {
          const rec = recordOf(range.row, byRow);
          if (!rec) continue;
          let v0 = Infinity, v1 = -1;
          for (let k = range.first * 3, end = (range.first + range.count) * 3; k < end; k++) { const v = index[k]; if (v < v0) v0 = v; if (v > v1) v1 = v; }
          if (v1 < v0) continue;
          const y0 = new Float32Array(v1 - v0 + 1);
          for (let v = v0; v <= v1; v++) y0[v - v0] = pos.array[v * 3 + 1];
          farEntries.push({ mesh: o, v0, v1, rec, y0, c0: col.array.slice(v0 * 3, v1 * 3 + 3), code: -1 });
        }
      }
    });
  }

  // ── the named structures (buildings.js batches) ──────────────────────────────────────────
  function bindNamed() {
    const layer = buildings();
    if (layer === namedLayer) return;
    restoreNamed();
    namedLayer = layer; named = [];
    const byId = new Map();
    for (const batch of layer?.batches ?? []) {
      const idx = batch.userData?.batchIndex;
      if (!idx) continue;
      for (let i = 0; i < idx.length; i++) {
        const id = idx[i];
        if (!id || map.fateOf(id) === 'survives') continue;
        let box = null;
        try { box = batch.getBoundingBoxAt(batch.getGeometryIdAt(i), new THREE.Box3()); } catch { box = null; }
        if (!box || box.isEmpty()) continue;
        const matrix = batch.getMatrixAt(i, new THREE.Matrix4());
        box.applyMatrix4(matrix).applyMatrix4(batch.matrixWorld);
        if (!byId.has(id)) byId.set(id, []);
        byId.get(id).push({ batch, i, matrix, paint: batch.getColorAt(i, new THREE.Color()), box, k: -1 });
      }
    }
    for (const [id, pieces] of byId) {
      const bb = new THREE.Box3();
      for (const p of pieces) bb.union(p.box);
      const cx = (bb.min.x + bb.max.x) / 2, cz = (bb.min.z + bb.max.z) / 2;
      const tc = map.catchAt(cx, -cz, id);
      if (tc === null) continue;
      const fate = map.fateOf(id) ?? 'walls_stand';
      const lo = Math.min(...pieces.map((p) => (p.box.min.y + p.box.max.y) / 2)), hi = Math.max(...pieces.map((p) => (p.box.min.y + p.box.max.y) / 2));
      for (const p of pieces) p.hfrac = hi > lo ? ((p.box.min.y + p.box.max.y) / 2 - lo) / (hi - lo) : 0.5;
      const H = bb.max.y - bb.min.y, sx = bb.max.x - bb.min.x, sz = bb.max.z - bb.min.z;
      const rec = { key: id, named: id, fate, e: cx, n: -cz, x: cx, z: cz, base: bb.min.y, h: H * 0.8, top: bb.max.y, w: sx, d: sz,
        pts: [[bb.min.x, -bb.min.z], [bb.max.x, -bb.min.z], [bb.max.x, -bb.max.z], [bb.min.x, -bb.max.z]],
        storeys: Math.max(1, Math.round(H * 0.8 / 4)), area: sx * sz, kind: fate === 'collapses' ? 'frame' : 'masonry', tc,
        wallsFall: false, st: null, code: -1, m: -1, emit: null, chimney: null };
      named.push({ id, rec, pieces, ground: Math.max(bb.min.y, groundAt(cx, -cz) - 0.3), cx, cz, H });
      recs.push(rec);
    }
  }
  const m4 = new THREE.Matrix4(), s4 = new THREE.Matrix4(), col = new THREE.Color();
  function poseNamed(nb) {
    const st = nb.rec.st;
    for (const p of nb.pieces) {
      const roofPiece = p.hfrac > 0.72;
      let charK = st.char, k = 0;
      if (nb.rec.fate === 'collapses') k = st.fall;
      else if (roofPiece) k = st.roof;
      if (nb.rec.fate === 'roof_burns' && !roofPiece) charK *= 0.5;
      const mult = nb.rec.kind === 'frame' ? CHAR : SOOT;
      if (p.paint) {
        col.setRGB(p.paint.r * lerp(1, mult[0], charK), p.paint.g * lerp(1, mult[1], charK), p.paint.b * lerp(1, mult[2], charK));
        p.batch.setColorAt(p.i, col);
      }
      const kk = k >= 0.999 ? 1 : k <= 0.001 ? 0 : Math.round(k * 40) / 40;
      if (kk === p.k) continue;
      p.k = kk;
      if (kk === 0) { p.batch.setMatrixAt(p.i, p.matrix); continue; }
      // A roof burned through is gone; a frame structure brought down is a black heap, not nothing.
      if (kk === 1 && roofPiece && nb.rec.fate !== 'collapses') { p.batch.setMatrixAt(p.i, m4.makeScale(0, 0, 0)); continue; }
      // Brought down where it stood: crushed onto its sills, sinking. World metres about the
      // building's foot, then into the batch's own frame.
      const squash = nb.rec.fate === 'collapses' ? lerp(1, 0.12, kk) : lerp(1, 0.3, kk);
      m4.makeTranslation(-nb.cx, -nb.ground, -nb.cz)
        .premultiply(s4.makeScale(1, squash, 1))
        .premultiply(s4.makeTranslation(nb.cx, nb.ground - (roofPiece && nb.rec.fate !== 'collapses' ? nb.H * 0.25 * kk : 0), nb.cz));
      if (!p.batch.matrixWorld.equals(IDENTITY)) m4.premultiply(s4.copy(p.batch.matrixWorld).invert()).multiply(p.batch.matrixWorld);
      p.batch.setMatrixAt(p.i, m4.multiply(p.matrix));
    }
  }
  function restoreNamed() {
    for (const nb of named) for (const p of nb.pieces) { p.batch.setMatrixAt(p.i, p.matrix); if (p.paint) p.batch.setColorAt(p.i, p.paint); p.k = -1; }
    for (const nb of named) nb.rec.code = -1;
  }

  // ── the state of every building at the fire time ──────────────────────────────────────────
  function codeOf(st) {
    return Math.round(clamp(Math.max(st.heat, st.embers * 0.55), 0, 1) * 15)
      + 16 * Math.round(st.char * 12) + 16 * 13 * Math.round(st.fall * 20) + 16 * 13 * 21 * Math.round(st.roof * 4);
  }
  function stateAll() {
    const rainAfter = Number.isFinite(map.rain) ? minute - map.rain : null;
    active = [];
    for (const rec of recs) {
      rec.m = minute - rec.tc;
      if (rec.kind === 'tree') {
        const c = smooth((rec.m - 2) / 20);
        rec.st = { heat: 0, char: c, fall: c * 0.35, roof: 0, embers: 0, smoke: 0 };
      } else rec.st = burnState(rec.kind, rec.m, map.model, { wallsFall: rec.wallsFall, rainAfter });
      rec.code = codeOf(rec.st);
      if (rec.kind !== 'tree' && (rec.st.heat > 0.02 || rec.st.embers > 0.04 || (rec.m >= 0 && rec.st.smoke > 0.05))) active.push(rec);
    }
    const dirty = new Set();
    for (const en of nearEntries) {
      if (en.code === en.rec.code) continue;
      en.code = en.rec.code; dirty.add(en.mesh);
      const st = en.rec.st, a = en.mesh.instanceMatrix.array, c = en.mesh.instanceColor.array, o = en.i * 16;
      for (let k = 0; k < 16; k++) a[o + k] = en.m0[k];
      const ys = en.rec.kind === 'frame' ? 1 - 0.94 * st.fall : en.rec.kind === 'tree' ? 1 - st.fall : 1 - 0.68 * st.fall;
      if (ys !== 1) { a[o + 4] *= ys; a[o + 5] *= ys; a[o + 6] *= ys; }
      const mult = en.rec.kind === 'frame' ? CHAR : en.rec.kind === 'tree' ? TREE : SOOT;
      const heatQ = en.rec.kind === 'tree' ? 0 : Math.round(clamp(Math.max(st.heat, st.embers * 0.55), 0, 1) * 15);
      for (let k = 0; k < 3; k++) c[en.i * 3 + k] = en.c0[k] * lerp(1, mult[k], st.char);
      c[en.i * 3] = Math.min(c[en.i * 3], 0.999) + 2 * heatQ;
    }
    for (const mesh of dirty) { mesh.instanceMatrix.needsUpdate = true; mesh.instanceColor.needsUpdate = true; }
    const farDirty = new Set();
    for (const en of farEntries) {
      if (en.code === en.rec.code) continue;
      en.code = en.rec.code; farDirty.add(en.mesh);
      const st = en.rec.st, pos = en.mesh.geometry.getAttribute('position').array, cl = en.mesh.geometry.getAttribute('color').array;
      const ys = en.rec.kind === 'frame' ? 1 - 0.94 * st.fall : en.rec.kind === 'tree' ? 1 - st.fall : 1 - 0.68 * st.fall;
      const base = en.rec.base, mult = en.rec.kind === 'frame' ? CHAR : en.rec.kind === 'tree' ? TREE : SOOT;
      // A far building burning is lit from within: a little of the fire's colour in its paint.
      const hot = Math.max(st.heat, st.embers * 0.5) * (0.35 + 0.65 * night);
      for (let v = en.v0; v <= en.v1; v++) {
        pos[v * 3 + 1] = base + (en.y0[v - en.v0] - base) * ys;
        const j = (v - en.v0) * 3;
        for (let k = 0; k < 3; k++) {
          const charred = en.c0[j + k] * lerp(1, mult[k], st.char);
          cl[v * 3 + k] = Math.round(clamp(lerp(charred, [255, 110, 40][k], hot * 0.6), 0, 255));
        }
      }
    }
    for (const mesh of farDirty) { mesh.geometry.getAttribute('position').needsUpdate = true; mesh.geometry.getAttribute('color').needsUpdate = true; }
    for (const nb of named) if (nb.code !== nb.rec.code) { nb.code = nb.rec.code; poseNamed(nb); }
  }
  function restoreCity() {
    for (const en of nearEntries) {
      if (en.code === -1) continue;
      en.code = -1;
      en.mesh.instanceMatrix.array.set(en.m0, en.i * 16);
      en.mesh.instanceColor.array.set(en.c0, en.i * 3);
      en.mesh.instanceMatrix.needsUpdate = true; en.mesh.instanceColor.needsUpdate = true;
    }
    for (const en of farEntries) {
      if (en.code === -1) continue;
      en.code = -1;
      const pos = en.mesh.geometry.getAttribute('position'), cl = en.mesh.geometry.getAttribute('color');
      for (let v = en.v0; v <= en.v1; v++) pos.array[v * 3 + 1] = en.y0[v - en.v0];
      cl.array.set(en.c0, en.v0 * 3);
      pos.needsUpdate = true; cl.needsUpdate = true;
    }
    for (const rec of recs) { rec.code = -1; rec.st = null; }
    restoreNamed();
    active = [];
  }

  // ── the fire as drawn ─────────────────────────────────────────────────────────────────────
  function stream(seed) {
    let s = Math.floor(hash01(seed) * 4294967296) >>> 0 || 1;
    return () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
  }
  function cornersOf(rec) {
    if (rec.pts) return rec.pts;
    const hw = rec.w / 2, hd = rec.d / 2;
    return [[rec.e - hw, rec.n - hd], [rec.e + hw, rec.n - hd], [rec.e + hw, rec.n + hd], [rec.e - hw, rec.n + hd]];
  }
  /** A near building's flames: at its windows storey by storey, and over its roof. */
  function emittersOf(rec) {
    if (rec.emit && rec.emit.cap === budget.perBuilding) return rec.emit;
    const r = stream(`emit:${rec.key}`), pts = cornersOf(rec), wins = [], roof = [];
    const S = rec.storeys, sh = rec.h / S;
    for (let k = 0; k < 4; k++) {
      const a = pts[k], b = pts[(k + 1) % 4], L = Math.hypot(b[0] - a[0], b[1] - a[1]);
      if (L < 1) continue;
      let nx = (b[1] - a[1]) / L, nn = -(b[0] - a[0]) / L;
      const mx = (a[0] + b[0]) / 2 - rec.e, mn = (a[1] + b[1]) / 2 - rec.n;
      if (nx * mx + nn * mn < 0) { nx = -nx; nn = -nn; }
      const per = Math.max(1, Math.round(L / (4.2 * budget.spacing)));
      for (let s = 0; s < S; s++) for (let i = 0; i < per; i++) {
        const f = (i + 0.5) / per, e = lerp(a[0], b[0], f) + nx * 0.7, n = lerp(a[1], b[1], f) + nn * 0.7;
        wins.push({ x: e, z: -n, y: rec.base + sh * (s + 0.25), w: 2.1 + 0.9 * r(), h: sh * (0.95 + 0.5 * r()), lag: 0.15 * s + 0.6 * r(), seed: r() * 100, roof: false });
      }
    }
    const nR = clamp(Math.round(rec.area / 55), 1, 6);
    for (let i = 0; i < nR; i++) {
      const u = 0.15 + 0.7 * r(), v = 0.15 + 0.7 * r();
      const e = lerp(lerp(pts[0][0], pts[1][0], u), lerp(pts[3][0], pts[2][0], u), v);
      const n = lerp(lerp(pts[0][1], pts[1][1], u), lerp(pts[3][1], pts[2][1], u), v);
      roof.push({ x: e, z: -n, y: rec.base + rec.h * 0.97, w: Math.min(rec.w, rec.d) * 0.55 + 2, h: (rec.top - rec.base) * 0.55 + 3, lag: 0.25 + 0.6 * r(), seed: r() * 100, roof: true });
    }
    for (let i = wins.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [wins[i], wins[j]] = [wins[j], wins[i]]; }
    const keep = Math.max(1, budget.perBuilding - roof.length);
    const heap = [];
    for (let i = 0; i < 3; i++) {
      const u = 0.2 + 0.6 * r(), v = 0.2 + 0.6 * r();
      heap.push({ x: lerp(lerp(pts[0][0], pts[1][0], u), lerp(pts[3][0], pts[2][0], u), v), z: -lerp(lerp(pts[0][1], pts[1][1], u), lerp(pts[3][1], pts[2][1], u), v), seed: r() * 100 });
    }
    rec.emit = { cap: budget.perBuilding, list: [...roof, ...wins.slice(0, keep)], heap, riseMin: rec.kind === 'frame' ? 5 : 9 };
    return rec.emit;
  }
  function flick(seed) { return 0.86 + 0.14 * Math.sin(visual * 1.7 + seed) + 0.08 * Math.sin(visual * 4.3 + seed * 2.1); }

  let smokeCarry = 0, plumeCarry = 0, sparkCarry = 0;
  function draw(dt, camera) {
    fx.begin(); plume.begin();
    let flames = 0;
    const F = budget.flames;
    camera.getWorldPosition(cam); camera.getWorldDirection(fwd);
    const near = [], mid = [], cells = new Map();
    let heatSum = 0, cx = 0, cz = 0;
    for (const rec of active) {
      const d = Math.hypot(rec.x - cam.x, rec.z - cam.z);
      rec.dist = d;
      const glowing = rec.st.heat + rec.st.embers * 0.4;
      if (glowing > 0.02) { const w = glowing * Math.sqrt(rec.area); heatSum += w; cx += rec.x * w; cz += rec.z * w; }
      if (d < budget.nearR) near.push(rec);
      else if (d < budget.midR) mid.push(rec);
      if (d >= budget.midR * 0.8 && rec.st.heat > 0.04) {
        const key = `${Math.floor(rec.x / budget.cell)},${Math.floor(rec.z / budget.cell)}`;
        let c = cells.get(key);
        if (!c) cells.set(key, c = { x: 0, z: 0, y: 0, top: 0, w: 0, heat: 0, n: 0, area: 0 });
        const w = rec.st.heat * rec.area;
        c.x += rec.x * w; c.z += rec.z * w; c.y += rec.base * w; c.top = Math.max(c.top, rec.top - rec.base); c.w += w; c.heat += rec.st.heat; c.n++; c.area += rec.area;
      }
    }
    near.sort((a, b) => a.dist - b.dist);
    const lightPick = [];
    // Near: every window and the roof, the nearest first.
    for (const rec of near) {
      if (flames >= F * 0.72) break;
      const st = rec.st, em = emittersOf(rec);
      if (st.heat > 0.02) {
        const down = rec.kind === 'frame' ? st.fall : 0;
        for (const e of em.list) {
          if (flames >= F * 0.72) break;
          const I = st.heat * smooth((rec.m / em.riseMin - e.lag) / 0.5) * (1 - 0.8 * down);
          if (I <= 0.03) continue;
          const open = e.roof && rec.kind === 'masonry' ? 1 + 0.7 * st.roof : 1;
          const y = lerp(e.y, rec.base + 0.2, down);
          fx.flame(e.x, y, e.z, e.w * (0.7 + 0.3 * I) * open, e.h * (0.45 + 0.55 * I) * open * flick(e.seed), e.roof ? 0.5 + 0.5 * I : 0.4 + 0.35 * I, e.seed);
          flames++;
        }
        lightPick.push(rec);
      }
      if (rec.kind === 'frame' && st.fall > 0.4 && st.embers > 0.08) {
        for (const h of em.heap) {
          if (flames >= F * 0.75) break;
          const I = st.embers * (0.6 + 0.4 * hash01(`${rec.key}:${h.seed}`));
          if (I < 0.1) continue;
          fx.flame(h.x, rec.base + 0.1, h.z, 1.4 + rec.w * 0.12, (0.5 + 1.8 * I) * flick(h.seed), 0.55 + 0.4 * I, h.seed);
          flames++;
        }
      }
      if (st.heat > 0.05) fx.glow(rec.x, rec.base, rec.z, Math.max(rec.w, rec.d) * 0.6 + 5, 0.3 * st.heat);
    }
    // Farther: one flame over each building.
    mid.sort((a, b) => a.dist - b.dist);
    for (const rec of mid) {
      if (flames >= F * 0.86) break;
      const st = rec.st;
      if (st.heat <= 0.05) continue;
      const down = rec.kind === 'frame' ? st.fall : 0;
      const H = rec.top - rec.base;
      fx.flame(rec.x, rec.base + H * 0.55 * (1 - 0.85 * down), rec.z, Math.max(rec.w, rec.d) * 0.9 + 2, (H * 0.9 + 4) * (0.5 + 0.5 * st.heat) * (1 - 0.5 * down) * flick(rec.tc),
        0.6 + 0.5 * st.heat, (rec.tc * 7.13) % 97);
      flames++;
      if (rec.dist < budget.midR * 0.6) lightPick.push(rec);
    }
    // The far city: whole blocks alight, the hottest and nearest first, none behind the eye.
    const far = [...cells.values()].map((c) => {
      const x = c.x / c.w, z = c.z / c.w, d = Math.hypot(x - cam.x, z - cam.z);
      return { x, z, y: c.y / c.w, top: c.top, heat: c.heat / c.n, area: c.area, d, score: c.heat * Math.sqrt(c.area) / (d + 200) };
    }).filter((c) => (c.x - cam.x) * fwd.x + (c.z - cam.z) * fwd.z > -0.2 * c.d).sort((a, b) => b.score - a.score);
    for (const c of far) {
      if (flames >= F) break;
      const big = clamp(c.d / 1500, 1, 2), w = clamp(Math.sqrt(c.area) * 0.75, 14, 110) * big;
      fx.flame(c.x, c.y + c.top * 0.25, c.z, w, (c.top * 1.6 + w * 0.55) * (0.6 + 0.4 * c.heat), 0.65 + 0.5 * c.heat, (c.x * 0.37 + c.z * 0.11) % 97);
      flames++;
    }
    // Smoke: thick and dark off the near fires, grey off the ruins; the budget shared by heat.
    const step = Number.isFinite(dt) && dt > 0 ? Math.min(dt, 0.25) : 0;
    let want = 0;
    for (const rec of near) want += (0.25 + 2.2 * rec.st.heat + 0.6 * rec.st.embers) * Math.sqrt(rec.area) / 14;
    const life = 22, cap = budget.smoke / life;
    const scale = want > cap ? cap / want : 1;
    smokeCarry += step * Math.min(want, cap);
    while (smokeCarry >= 1 && near.length) {
      smokeCarry -= 1;
      let r = rnd() * want, pick = near[0];
      for (const rec of near) { r -= (0.25 + 2.2 * rec.st.heat + 0.6 * rec.st.embers) * Math.sqrt(rec.area) / 14; if (r <= 0) { pick = rec; break; } }
      const st = pick.st, H = pick.top - pick.base, down = pick.kind === 'frame' ? st.fall : 0;
      const u = rnd(), v = rnd(), pts = cornersOf(pick);
      const e = lerp(lerp(pts[0][0], pts[1][0], u), lerp(pts[3][0], pts[2][0], u), v), n = lerp(lerp(pts[0][1], pts[1][1], u), lerp(pts[3][1], pts[2][1], u), v);
      fx.smoke({ x: e, y: pick.base + H * (1 - 0.85 * down) + 1, z: -n }, { dark: st.heat > 0.1 ? 0.6 + 0.4 * st.heat : 0.25, glow: Math.min(1, st.heat + 0.4 * st.embers),
        size: 2.5 + Math.sqrt(pick.area) * 0.12, up: 2.5 + 3.5 * st.heat, life, spread: Math.min(pick.w, pick.d) * 0.4, glowLife: 2.5, thin: 0.025 });
    }
    void scale;
    sparkCarry += step * Math.min(budget.sparks / 2.4, near.reduce((s, rec) => s + 6 * rec.st.heat, 0));
    while (sparkCarry >= 1 && near.length) {
      sparkCarry -= 1;
      const rec = near[Math.floor(rnd() * Math.min(near.length, 8))];
      if (rec.st.heat < 0.1) continue;
      fx.sparks({ x: rec.x + (rnd() - 0.5) * rec.w * 0.6, y: rec.top - 0.5, z: rec.z + (rnd() - 0.5) * rec.d * 0.6 }, 1, { up: 4 + 6 * rec.st.heat, spread: 2 });
    }
    // The plume: great billows over the burning district, from the fires the eye is not among.
    const sources = [];
    let plumeWant = 0;
    for (const c of [...cells.values()]) {
      const x = c.x / c.w, z = c.z / c.w, s = c.heat * Math.sqrt(c.area);
      sources.push({ x, z, y: c.y / c.w + c.top, s, heat: c.heat / c.n, area: c.area }); plumeWant += s;
    }
    for (const rec of mid) if (rec.st.heat > 0.1) { const s = rec.st.heat * Math.sqrt(rec.area) * 0.6; sources.push({ x: rec.x, z: rec.z, y: rec.top, s, heat: rec.st.heat, area: rec.area * 2 }); plumeWant += s; }
    plumeCarry += step * (sources.length ? budget.plume / 40 : 0);
    while (plumeCarry >= 1 && sources.length) {
      plumeCarry -= 1;
      let r = rnd() * plumeWant, src = sources[0];
      for (const s of sources) { r -= s.s; if (r <= 0) { src = s; break; } }
      const d = Math.hypot(src.x - cam.x, src.z - cam.z);
      // Far off, a plume is the fire's whole sign: its billows are drawn the larger the farther.
      const size = clamp(16 + Math.sqrt(src.area) * 0.5, 16, 85) * clamp(d / 450, 0.35, 3.2);
      plume.smoke({ x: src.x, y: src.y + 6, z: src.z }, { dark: 0.9, glow: 0.6 + 0.6 * src.heat, size, up: (7 + 4 * src.heat) * clamp(d / 900, 1, 2), life: 40, spread: size * 0.5, glowLife: 16, thin: 0.004 });
    }
    fx.update(dt, camera); plume.update(dt, camera);
    // The light: the strongest fires near the eye light the walls, the street and faces.
    lightPick.sort((a, b) => b.st.heat * Math.sqrt(b.area) / (b.dist + 25) ** 2 - a.st.heat * Math.sqrt(a.area) / (a.dist + 25) ** 2);
    const g = 1 / adapt ** 0.5;
    lights.forEach((l, i) => {
      const rec = lightPick[i];
      // The lights stay in the scene while the fire is on, dark when unused: a light coming
      // or going changes every lit material's program.
      l.visible = true;
      if (!rec) { l.intensity = 0; return; }
      l.position.set(rec.x + (cam.x - rec.x) * Math.min(0.25, 6 / Math.max(rec.dist, 1)), rec.base + Math.min(14, (rec.top - rec.base) * 0.6 + 2), rec.z + (cam.z - rec.z) * Math.min(0.25, 6 / Math.max(rec.dist, 1)));
      l.intensity = g * 30 * rec.st.heat * clamp(Math.sqrt(rec.area) / 14, 0.6, 2.6) * flick(rec.tc + i);
    });
    // The sky: a glow over the burning district, toward wherever the fire is.
    if (heatSum > 0) {
      const fxp = cx / heatSum, fzp = cz / heatSum, dist = Math.hypot(fxp - cam.x, fzp - cam.z);
      sky.material.uniforms.uDir.value.set(fxp - cam.x, 0, fzp - cam.z);
      sky.material.uniforms.uSpread.value = clamp(Math.atan2(900, Math.max(dist, 1)), 0.35, 1.5);
      sky.material.uniforms.uAround.value = smooth(1 - dist / 1800);
      sky.material.uniforms.uK.value = clamp(Math.sqrt(heatSum) / 70, 0, 1) * lerp(0.04, 0.35, night);
      const far = camera.far ?? 20000;
      sky.scale.setScalar(Math.min(far * 0.85, 30000));
      sky.position.copy(cam);
      sky.visible = true;
    } else sky.visible = false;
  }
  let chimneyAt = new THREE.Vector3(Infinity, 0, 0), chimneyClock = -1;
  function placeChimneys(camera) {
    camera.getWorldPosition(v3);
    if (chimneyAt.distanceToSquared(v3) < 900 && chimneyClock === minute) return;
    chimneyAt.copy(v3); chimneyClock = minute;
    let n = 0;
    const R2 = budget.chimneyR ** 2;
    for (const rec of recs) {
      if (n >= budget.chimneys) break;
      if (rec.kind !== 'frame' || rec.named || !rec.st || rec.st.fall < 0.85) continue;
      if ((rec.x - v3.x) ** 2 + (rec.z - v3.z) ** 2 > R2) continue;
      if (!rec.chimney) {
        const r = stream(`chimney:${rec.key}`), pts = cornersOf(rec);
        const u = r() < 0.5 ? 0.18 + 0.15 * r() : 0.67 + 0.15 * r(), v = 0.3 + 0.4 * r();
        const e = lerp(lerp(pts[0][0], pts[1][0], u), lerp(pts[3][0], pts[2][0], u), v), nn = lerp(lerp(pts[0][1], pts[1][1], u), lerp(pts[3][1], pts[2][1], u), v);
        rec.chimney = new THREE.Matrix4().compose(new THREE.Vector3(e, rec.base - 0.1, -nn), new THREE.Quaternion(), new THREE.Vector3(0.75, clamp((rec.top - rec.base) * 0.85, 3.5, 11), 0.6));
      }
      chimneys.setMatrixAt(n++, rec.chimney);
    }
    chimneys.count = n;
    if (n) chimneys.instanceMatrix.needsUpdate = true;
  }

  const listeners = new Set();
  const api = {
    map, group,
    get minute() { return minute; },
    get iso() { return minute === null ? null : isoOf(minute); },
    get rate() { return rate; },
    get active() { return minute !== null; },
    /** Set the fire time (minutes from 1871-10-08T00:00, or an ISO local time; null: the city before the fire). */
    set(t, { rate: r = 0 } = {}) {
      const m = typeof t === 'string' ? minutesOf(t) : t;
      rate = Number.isFinite(r) ? Math.max(0, r) : 0;
      if (m === null || m === undefined || !Number.isFinite(m)) {
        if (minute !== null) {
          minute = null;
          restoreCity();
          fx?.clear(); plume?.clear();
          for (const l of lights) { l.visible = false; l.intensity = 0; }
          if (sky) sky.visible = false;
          if (chimneys) chimneys.count = 0;
          group.visible = false;
          for (const fn of listeners) { try { fn(null); } catch { /* the listener's own */ } }
        }
        return api;
      }
      build();
      group.visible = true;
      // A jump in the fire time (a new stop, a QA stand) starts the drawn fire afresh.
      if (minute === null || Math.abs(m - minute) > 2) { fx.clear(); plume.clear(); }
      if (tier() !== budgetTier) api.retier();
      bindCity(); bindNamed();
      minute = m; stateClock = Infinity;
      stateAll(); lastMinute = minute;
      for (const fn of listeners) { try { fn(api.iso); } catch { /* the listener's own */ } }
      return api;
    },
    setRate(r) { rate = Number.isFinite(r) ? Math.max(0, r) : 0; return rate; },
    onFire(fn) { listeners.add(fn); try { fn(api.iso); } catch { /* its own */ } return () => listeners.delete(fn); },
    /** The minute (from 1871-10-08T00:00) the fire reaches a place, or null where it never burned. */
    catchAt: (e, n, key = null) => map.catchAt(e, n, key),
    /** The same, as 'YYYY-MM-DDTHH:MM'. */
    catchTime(e, n) { const m = map.catchAt(e, n); return m === null ? null : isoOf(m); },
    /** What the fire is doing at a place now: { phase, heat, ... } ('none' outside the district). */
    stateAt(e, n) {
      const tc = map.catchAt(e, n);
      if (tc === null || minute === null) return { phase: 'none', tc };
      const st = burnState('frame', minute - tc, map.model, { rainAfter: Number.isFinite(map.rain) ? minute - map.rain : null });
      const phase = minute < tc ? 'before' : st.heat > 0.05 ? 'burning' : 'burnt';
      return { phase, tc, minutesToFront: tc - minute, ...st };
    },
    /** Rebuild the drawn fire for the current detail tier. */
    retier() {
      if (!fx) return;
      fx.dispose(); plume.dispose(); fx = null; plume = null;
      for (const l of lights) l.removeFromParent();
      lights = [];
      sky?.removeFromParent(); sky?.geometry.dispose(); sky?.material.dispose(); sky = null;
      chimneys?.removeFromParent(); chimneys?.geometry.dispose(); chimneys?.material.dispose(); chimneys = null;
      for (const rec of recs) rec.emit = null;
      build();
    },
    update(dt, camera, { advance = true } = {}) {
      if (minute === null || !fx) return;
      const step = Number.isFinite(dt) && dt > 0 ? Math.min(dt, 0.25) : 0;
      visual += step;
      FIRE_UNIFORMS.uFireTime.value = visual % 600;
      if (advance && rate > 0) minute += step * rate / 60;
      if (context() !== city || buildings() !== namedLayer) { bindCity(); bindNamed(); lastMinute = null; }
      stateClock += step;
      if (lastMinute === null || (minute !== lastMinute && stateClock > 0.25)) {
        stateAll(); stateClock = 0;
        if (Math.floor(minute) !== Math.floor(lastMinute ?? -1)) for (const fn of listeners) { try { fn(api.iso); } catch { /* its own */ } }
        lastMinute = minute;
      }
      if (camera) { draw(step, camera); placeChimneys(camera); }
    },
    /** Run the drawn fire on for `seconds` (the smoke and sparks fill in) without moving the fire time. */
    warm(seconds = 8, camera = null) {
      for (let t = 0; t < seconds; t += 1 / 15) api.update(1 / 15, camera, { advance: false });
    },
    snapshot() {
      const counts = { unburnt: 0, burning: 0, collapsing: 0, burnt: 0 };
      for (const rec of recs) {
        if (rec.kind === 'tree' || !rec.st) continue;
        if (rec.m < 0) counts.unburnt++;
        else if (rec.st.heat > 0.05) counts[rec.st.fall > 0.05 ? 'collapsing' : 'burning']++;
        else counts.burnt++;
      }
      return { iso: api.iso, minute, rate, buildings: recs.filter((r) => r.kind !== 'tree').length, named: named.map((nb) => ({ id: nb.id, tc: isoOf(nb.rec.tc), fate: nb.rec.fate, heat: +(nb.rec.st?.heat ?? 0).toFixed(2) })),
        ...counts, active: active.length, ...(fx ? { fx: fx.counts, plume: plume.counts.smoke } : {}),
        lights: lights.filter((l) => l.visible && l.intensity > 0).length, chimneys: chimneys?.count ?? 0, sky: sky?.visible ? +sky.material.uniforms.uK.value.toFixed(3) : 0 };
    },
    dispose() {
      api.set(null); unDaylight();
      fx?.dispose(); plume?.dispose();
      sky?.geometry.dispose(); sky?.material.dispose();
      chimneys?.geometry.dispose(); chimneys?.material.dispose();
      group.removeFromParent();
    },
  };
  group.visible = false;
  return api;
}

const IDENTITY = new THREE.Matrix4();

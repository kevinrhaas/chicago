// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * fire-goods.js — the household goods the families carried out of the fire's way (T-3751).
 *
 * The owner, 2026-11-26, on the Great Fire jaunt's stop at the Ogden house: "The narration
 * describes a burned park, but the park appears undamaged and the referenced furniture is
 * missing. Add the furniture and depict it burning or show the appropriate aftermath."
 *
 * data/fire/1871.json `goods` names the open grounds the accounts fill with goods (Washington
 * Square: "the accumulated furniture of fifty families"; the old City Cemetery: "the household
 * gods and valuables which they had moved into the cemetery ... burn up before their eyes"),
 * and tools/fire_1871.py lays the heaps on each (`local_heaps`: e, n, bearing, seed). Here each
 * heap is drawn as a few pieces of furniture of the period's ordinary kinds (chairs, a table,
 * a bedstead, a bureau, a trunk, a mattress, bundles), all reconstructed, and each heap is a
 * small frame fire to city-fire.js: it catches at its place's hour (`catch: 'place'`) or inside
 * the goods' own window (`window`, a share of the heaps), burns, falls in and smokes, and its
 * pieces char and sink as it does. The heaps are on the ground from `appear` (the families
 * came in ahead of the fire), and the ground of a square the fire went through (`scorch`) is
 * burnt under its goods and over its whole footprint (`local_ground`) from the place's hour. Nothing is drawn while the fire is out (free walk is the city
 * before the fire).
 */
import * as THREE from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { minutesOf, hash01 } from './fire-map.js';

const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
const lerp = (a, b, t) => a + (b - a) * t;
const smoothK = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
/** Is (e, n) inside the polygon `poly` ([[e, n], ...])? */
function inside(poly, e, n) {
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [ei, ni] = poly[i], [ej, nj] = poly[j];
    if ((ni > n) !== (nj > n) && e < ((ej - ei) * (n - ni)) / (nj - ni) + ei) c = !c;
  }
  return c;
}

const WALNUT = [0.36, 0.24, 0.15], PINE = [0.55, 0.42, 0.28], PAINTED = [0.42, 0.36, 0.3];
const TICKING = [0.74, 0.71, 0.64], QUILT = [0.52, 0.3, 0.26], SHAWL = [0.3, 0.32, 0.4], LINEN = [0.78, 0.76, 0.7], LEATHER = [0.3, 0.2, 0.13];
/** Burnt: wood to char, cloth to ash. A multiplier of each piece's colour. */
// Linear (the colour's working space): about sRGB 0.2, the black of burnt wood and cloth in daylight.
const CHARRED = [0.032, 0.028, 0.026];

/** One box part, its corner at (x0, y0, z0) and size (w, h, d), in one colour. */
function part(x0, y0, z0, w, h, d, rgb) {
  const g = new THREE.BoxGeometry(w, h, d);
  g.translate(x0 + w / 2, y0 + h / 2, z0 + d / 2);
  const n = g.getAttribute('position').count, c = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) c.set(rgb, i * 3);
  g.setAttribute('color', new THREE.BufferAttribute(c, 3));
  return g;
}
function legs(w, d, h, t, rgb, inset = 0) {
  return [[inset, inset], [w - t - inset, inset], [inset, d - t - inset], [w - t - inset, d - t - inset]].map(([x, z]) => part(x, 0, z, t, h, t, rgb));
}
/** The kinds of piece, each centred on its own foot at the origin, long along local x. */
function kinds() {
  const centre = (g) => { g.computeBoundingBox(); const b = g.boundingBox; g.translate(-(b.min.x + b.max.x) / 2, 0, -(b.min.z + b.max.z) / 2); return g; };
  const merge = (parts) => centre(mergeGeometries(parts, false));
  return {
    chair: merge([...legs(0.42, 0.42, 0.44, 0.04, WALNUT), part(0, 0.44, 0, 0.42, 0.04, 0.42, WALNUT),
      part(0, 0.48, 0.38, 0.04, 0.46, 0.04, WALNUT), part(0.38, 0.48, 0.38, 0.04, 0.46, 0.04, WALNUT), part(0, 0.8, 0.38, 0.42, 0.12, 0.03, WALNUT)]),
    table: merge([...legs(1.1, 0.72, 0.69, 0.06, PINE, 0.05), part(0, 0.69, 0, 1.1, 0.04, 0.72, PINE)]),
    bed: merge([...legs(1.95, 1.3, 0.3, 0.07, WALNUT), part(0, 0.22, 0, 1.95, 0.14, 0.05, WALNUT), part(0, 0.22, 1.25, 1.95, 0.14, 0.05, WALNUT),
      part(0, 0, 0, 0.07, 1.15, 1.3, WALNUT), part(1.88, 0, 0, 0.07, 0.75, 1.3, WALNUT), part(0.07, 0.32, 0.05, 1.81, 0.16, 1.2, TICKING)]),
    bureau: merge([part(0, 0.08, 0, 1.0, 0.92, 0.5, WALNUT), ...legs(1.0, 0.5, 0.08, 0.06, WALNUT),
      ...[0.2, 0.45, 0.7].map((y) => part(0.04, 0.08 + y, 0.5, 0.92, 0.02, 0.012, PAINTED)), part(-0.02, 1.0, -0.02, 1.04, 0.04, 0.54, WALNUT)]),
    trunk: merge([part(0, 0, 0, 0.9, 0.44, 0.52, LEATHER), part(0, 0.44, 0, 0.9, 0.12, 0.52, LEATHER), part(0.1, 0.02, -0.01, 0.04, 0.54, 0.54, PINE), part(0.76, 0.02, -0.01, 0.04, 0.54, 0.54, PINE)]),
    mattress: merge([part(0, 0, 0, 1.9, 0.18, 1.25, TICKING), part(0.1, 0.18, 0.1, 0.55, 0.06, 0.45, LINEN)]),
    bundle: merge([part(0, 0, 0, 0.6, 0.32, 0.42, SHAWL), part(0.18, 0.32, 0.08, 0.24, 0.1, 0.26, SHAWL)]),
    quilt: merge([part(0, 0, 0, 1.6, 0.05, 1.3, QUILT)]),
  };
}
const CLOTH = new Set(['mattress', 'bundle', 'quilt']);

/** What one heap holds and how it lies, from its seed: a family's goods dropped where they stopped. */
function heapPieces(seed) {
  let s = (seed >>> 0) || 1;
  const r = () => { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; };
  const list = [];
  const add = (kind, u, v, yaw, tilt = 0, lift = 0) => list.push({ kind, u, v, yaw, tilt, lift });
  if (r() < 0.55) add('bed', -0.4, 0.2, r() * 0.6 - 0.3);
  else add('mattress', -0.3, 0.3, r() * 0.8 - 0.4);
  if (r() < 0.6) add('bureau', 1.0 + r() * 0.3, -0.7, r() * 0.5 - 0.25 + Math.PI / 2);
  if (r() < 0.55) add('table', 0.9, 0.9 + r() * 0.3, r() * 0.8);
  const chairs = 1 + Math.floor(r() * 3);
  for (let i = 0; i < chairs; i++) add('chair', -1.4 + r() * 2.8, -1.3 + r() * 0.5, r() * Math.PI * 2, r() < 0.3 ? Math.PI / 2 : 0, 0);
  if (r() < 0.7) add('trunk', -1.5, 1.0 + r() * 0.4, r() * 0.6);
  const bundles = 1 + Math.floor(r() * 3);
  for (let i = 0; i < bundles; i++) add('bundle', -1.2 + r() * 2.6, 1.5 + r() * 0.6, r() * Math.PI);
  if (r() < 0.4) add('quilt', 0.3, -1.6, r());
  return list;
}

/** A soft scorch: black at the middle, grey ash in drifts, ragged to nothing at its edge (a canvas,
 *  made once). The noise is smooth (value noise, three octaves), so it reads as burnt ground and
 *  not as a grid of squares. */
function scorchTexture() {
  const N = 128, c = document.createElement('canvas'); c.width = c.height = N;
  const g = c.getContext('2d'), img = g.createImageData(N, N);
  const value = (x, y, cell, salt) => {
    const gx = x / cell, gy = y / cell, x0 = Math.floor(gx), y0 = Math.floor(gy), fx = gx - x0, fy = gy - y0;
    const h = (i, j) => hash01(`${salt}:${i},${j}`), sx = fx * fx * (3 - 2 * fx), sy = fy * fy * (3 - 2 * fy);
    return lerp(lerp(h(x0, y0), h(x0 + 1, y0), sx), lerp(h(x0, y0 + 1), h(x0 + 1, y0 + 1), sx), sy);
  };
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const dx = x / N - 0.5, dy = y / N - 0.5, r = Math.hypot(dx, dy) * 2;
    const n = value(x, y, 32, 'a') * 0.55 + value(x, y, 12, 'b') * 0.3 + value(x, y, 5, 'c') * 0.15;
    const a = clamp((1 - r) * 2.4 - (n - 0.5) * 1.1, 0, 1);
    const ash = clamp((value(x, y, 9, 'd') - 0.58) * 4, 0, 1), i = (y * N + x) * 4;
    img.data[i] = 20 + ash * 70; img.data[i + 1] = 17 + ash * 66; img.data[i + 2] = 15 + ash * 62; img.data[i + 3] = Math.round(255 * a * 0.96);
  }
  g.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/**
 * The goods of `doc.goods`, drawn into `parent`. `groundAt(e, n)` is the ground's height;
 * `map` the fire map (fire-map.js). `recs()` are the heaps as small frame fires for city-fire.js;
 * `pose(minute)` places, chars and sinks every piece for the fire time (null: none shown).
 */
export function createFireGoods({ doc, map, parent, groundAt = () => 3.2 }) {
  const group = new THREE.Group(); group.name = 'city-fire:goods'; group.visible = false; parent?.add?.(group);
  const heaps = [];
  for (const g of doc?.goods ?? []) {
    const appear = minutesOf(g.appear) ?? -Infinity, w = g.window;
    const from = minutesOf(w?.from), to = minutesOf(w?.to);
    for (const [e, n, bearing, seed] of g.local_heaps ?? []) {
      const key = `goods:${g.id}:${seed}`;
      let tc = null;
      if (w && Number.isFinite(from) && Number.isFinite(to)) {
        if (hash01(`${key}:burns`) < (w.share ?? 1)) tc = lerp(from, to, hash01(`${key}:when`));
      } else if (g.catch === 'place') {
        // The place's own hour (the spared ring round a survivor does not spare goods heaped by it).
        const z = map.zoneAt(e, n), h = z ? map.hourAt(e, n, z) : null;
        if (h !== null) tc = h + (map.model.jitter_min ?? 6) * (hash01(key) - 0.5) * 2;
      }
      const base = groundAt(e, n);
      const rec = { key, goods: g.id, e, n, x: e, z: -n, base, h: 1.0, top: base + 1.2, w: 3.2, d: 3.2, pts: null, storeys: 1, area: 10,
        kind: 'frame', tc: tc ?? Infinity, wallsFall: false, st: null, code: -1, m: -1, emit: null, chimney: null, appear, scorch: !!g.scorch };
      const th = bearing * Math.PI / 180, c = Math.cos(th), s = Math.sin(th);
      rec.pts = [[-1.6, -1.6], [1.6, -1.6], [1.6, 1.6], [-1.6, 1.6]].map(([u, v]) => [e + u * c + v * s, n - u * s + v * c]);
      // Its flames: low over the heap while it burns, then its embers where it lay.
      const rr = (k) => hash01(`${key}:${k}`);
      rec.goodsEmit = { cap: Infinity, riseMin: 4,
        list: [0, 1, 2, 3].map((i) => ({ x: e + (rr(`fx${i}`) - 0.5) * 2.2, z: -(n + (rr(`fz${i}`) - 0.5) * 2.2), y: base + 0.1, w: 1.1 + rr(`fw${i}`) * 0.9, h: 1.6 + rr(`fh${i}`) * 1.8, lag: 0.15 * i, seed: rr(`fs${i}`) * 100, roof: i === 0 })),
        heap: [0, 1].map((i) => ({ x: e + (rr(`hx${i}`) - 0.5) * 1.6, z: -(n + (rr(`hz${i}`) - 0.5) * 1.6), seed: rr(`hs${i}`) * 100 })) };
      rec.pieces = heapPieces(seed).map((p) => ({ ...p, cloth: CLOTH.has(p.kind), u: p.u * c + p.v * s, v: -p.u * s + p.v * c, yaw: th + p.yaw }));
      heaps.push(rec);
    }
  }
  // The ground a `scorch` entry's fire ran over (`local_ground`, its footprint): ragged burnt
  // patches about 6 m apart over all of it, each from the place's own hour, so a square the fire
  // went through reads black and grey between the heaps and not only under them.
  const patches = [];
  for (const g of doc?.goods ?? []) {
    const poly = g.scorch && Array.isArray(g.local_ground) && g.local_ground.length >= 3 ? g.local_ground : null;
    if (!poly) continue;
    const es = poly.map((p) => p[0]), ns = poly.map((p) => p[1]), STEP = 6;
    for (let e = Math.min(...es) + STEP / 2; e < Math.max(...es); e += STEP) {
      for (let n = Math.min(...ns) + STEP / 2; n < Math.max(...ns); n += STEP) {
        const key = `ground:${g.id}:${Math.round(e)},${Math.round(n)}`;
        const pe = e + (hash01(`${key}:e`) - 0.5) * STEP * 0.8, pn = n + (hash01(`${key}:n`) - 0.5) * STEP * 0.8;
        if (!inside(poly, pe, pn)) continue;
        const z = map.zoneAt(pe, pn), h = z ? map.hourAt(pe, pn, z) : null;
        if (h === null) continue;
        patches.push({ e: pe, n: pn, tc: h + (map.model.jitter_min ?? 6) * (hash01(key) - 0.5) * 2,
          size: 8 + 4 * hash01(`${key}:s`), rot: hash01(`${key}:r`) * 6.28 });
      }
    }
  }
  const geos = kinds();
  const material = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.92, metalness: 0 });
  material.name = 'city_fire_goods';
  const meshes = {}, slots = [];
  for (const kind of Object.keys(geos)) {
    const count = heaps.reduce((k, h) => k + h.pieces.filter((p) => p.kind === kind).length, 0);
    if (!count) continue;
    const m = new THREE.InstancedMesh(geos[kind], material, count);
    m.name = `city-fire:goods:${kind}`; m.castShadow = true; m.receiveShadow = true; m.count = count;
    m.instanceColor = new THREE.InstancedBufferAttribute(new Float32Array(count * 3).fill(1), 3);
    m.frustumCulled = false; meshes[kind] = { mesh: m, next: 0 };
    group.add(m);
  }
  for (const h of heaps) for (const p of h.pieces) { const k = meshes[p.kind]; slots.push({ heap: h, p, mesh: k.mesh, i: k.next++, code: -1 }); }
  // The scorch under each heap, and over a square the fire went through.
  const tex = heaps.length ? scorchTexture() : null;
  const scorchMat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false, opacity: 1, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, toneMapped: true });
  scorchMat.name = 'city_fire_goods_scorch';
  const disc = new THREE.PlaneGeometry(1, 1).rotateX(-Math.PI / 2);
  const scorch = new THREE.InstancedMesh(disc, scorchMat, Math.max(1, heaps.length * 4 + patches.length));
  scorch.name = 'city-fire:goods:scorch'; scorch.renderOrder = 2; scorch.frustumCulled = false; scorch.count = 0; scorch.receiveShadow = false;
  group.add(scorch);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), qt = new THREE.Quaternion(), v = new THREE.Vector3(), sc = new THREE.Vector3(), ax = new THREE.Vector3(1, 0, 0), ay = new THREE.Vector3(0, 1, 0);
  const col = new THREE.Color();
  let shown = null;

  function pose(minute) {
    const on = Number.isFinite(minute);
    group.visible = on;
    if (!on) { shown = null; return; }
    const dirty = new Set();
    let sn = 0;
    for (const sl of slots) {
      const h = sl.heap, st = h.st, p = sl.p, here = minute >= h.appear;
      const charK = st?.char ?? 0, fall = st?.fall ?? 0;
      const sink = here ? (p.cloth ? 1 - 0.85 * fall : 1 - 0.55 * fall) : 0;
      const code = here ? Math.round(charK * 20) + 21 * Math.round(sink * 20) : -2;
      if (code === sl.code) continue;
      sl.code = code; dirty.add(sl.mesh);
      if (!here) { sl.mesh.setMatrixAt(sl.i, m4.makeScale(0, 0, 0)); continue; }
      const e = h.e + p.u, n = h.n + p.v, y = groundAt(e, n) + p.lift;
      q.setFromAxisAngle(ay, Math.PI - p.yaw);
      if (p.tilt) q.multiply(qt.setFromAxisAngle(ax, p.tilt));
      sl.mesh.setMatrixAt(sl.i, m4.compose(v.set(e, y + (p.tilt ? 0.22 : 0), -n), q, sc.set(1, Math.max(0.05, sink), 1)));
      const c = CHARRED;
      sl.mesh.setColorAt(sl.i, col.setRGB(lerp(1, c[0], charK), lerp(1, c[1], charK), lerp(1, c[2], charK)));
    }
    for (const m of dirty) { m.instanceMatrix.needsUpdate = true; if (m.instanceColor) m.instanceColor.needsUpdate = true; }
    for (const h of heaps) {
      const k = h.st?.char ?? 0;
      if (k <= 0.02 || minute < h.appear) continue;
      const size = 4.2 + 1.2 * hash01(`${h.key}:sz`);
      scorch.setMatrixAt(sn, m4.compose(v.set(h.e, groundAt(h.e, h.n) + 0.03, -h.n), q.setFromAxisAngle(ay, hash01(`${h.key}:rot`) * 6.28), sc.set(size * k, 1, size * k)));
      sn++;
      if (h.scorch) for (let i = 0; i < 3 && sn < scorch.instanceMatrix.count; i++) {
        // The grass the fire ran over between the heaps.
        const e = h.e + (hash01(`${h.key}:s${i}e`) - 0.5) * 9, n = h.n + (hash01(`${h.key}:s${i}n`) - 0.5) * 9, s = (5 + 4 * hash01(`${h.key}:s${i}`)) * k;
        scorch.setMatrixAt(sn++, m4.compose(v.set(e, groundAt(e, n) + 0.025, -n), q.setFromAxisAngle(ay, hash01(`${h.key}:r${i}`) * 6.28), sc.set(s, 1, s)));
      }
    }
    for (const p of patches) {
      const k = smoothK((minute - p.tc) / 12);
      if (k <= 0.02 || sn >= scorch.instanceMatrix.count) continue;
      const s = p.size * (0.4 + 0.6 * k);
      scorch.setMatrixAt(sn++, m4.compose(v.set(p.e, groundAt(p.e, p.n) + 0.02, -p.n), q.setFromAxisAngle(ay, p.rot), sc.set(s, 1, s)));
    }
    scorch.count = sn;
    if (sn) scorch.instanceMatrix.needsUpdate = true;
    shown = minute;
  }

  return {
    group,
    get heaps() { return heaps; },
    pose,
    get shown() { return shown; },
    counts() { return { heaps: heaps.length, pieces: slots.length, burning: heaps.filter((h) => (h.st?.heat ?? 0) > 0.05).length, burnt: heaps.filter((h) => (h.st?.char ?? 0) > 0.5).length, ground: patches.length, scorched: shown === null ? 0 : patches.filter((p) => shown - p.tc > 0).length }; },
    dispose() { group.removeFromParent(); for (const g of Object.values(geos)) g.dispose(); material.dispose(); disc.dispose(); scorchMat.dispose(); tex?.dispose(); },
  };
}

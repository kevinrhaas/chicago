// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-blood.js — blood and wounds, for the 18+ jaunts only.
 *
 * The owner, 2026-11-15: *"this one is targeted at adults and shows everything incredibly
 * graphically"*; *"Yes scalpings did occur so we want to be honest about it"*. human-fight.js
 * stages the weapons and the blows; this draws what they do. A stage beat `wound` (body, head,
 * neck, shoulder, scalp) on the one hit, at the moment the blow or the ball lands, and
 * tools/compile_jaunts.py refuses it in any jaunt that is not `audience: adults`, as it refuses
 * `arm` and `act`; nothing here is reached from a students' jaunt.
 *
 * What a wound draws, each part measured on the real figures by tools/test_human_fight.mjs:
 *
 *   - spatter: dark drops thrown out of the wound, falling under gravity and lying where they
 *     land as small splashes on the ground;
 *   - a stain on the body where it was hit, found by a ray from the side the blow came from onto
 *     the figure's own (skinned, posed) clothing or skin, laid on that surface and carried by
 *     the bone under it, spreading as cloth soaks; a scalping's is on the crown of the head;
 *   - a few drops still falling from a wound on someone standing or kneeling;
 *   - a pool on the ground under the wound once the figure is down, spreading over some
 *     seconds: wide under the fallen, small under the kneeling or seated.
 *
 * Held even here, as AGENTS.md and the liberty say: no child is ever wounded (the gate refuses
 * a `wound` on a child), and the mutilations the accounts tell (Wells's heart, White's wounds
 * after death) are told, not drawn. How much blood, where it lies and how it spreads are
 * reconstructed (liberty L-1812-adult-jaunts).
 *
 * `createBloodFx(parent)` -> { wound(actor, kind, { from }), update(dt), clear(), counts,
 * visible }. `actor` is a humans.js figure (or anything with `root`, `body { scene, meshes }`,
 * `posture`, and optionally `heightAt(e, n)`, `standY`, `e`, `n`, `disposed`). `from` is where
 * the blow or the shot came from, in the parent's frame (null: from ahead of the figure).
 */
import * as THREE from 'three';

export const WOUND_KINDS = Object.freeze(['body', 'head', 'neck', 'shoulder', 'scalp']);
/** Per kind: the bone it is on, the stain's radius (m), the drops thrown, their speed (m/s),
 *  the pool's radius under the fallen (m), and whether it still drips from someone up. */
export const WOUND = Object.freeze({
  body: { bone: 'spine_03', up: 1.25, stain: 0.11, drops: 16, speed: [0.8, 2.2], pool: 0.85, drip: true },
  head: { bone: 'head', up: 1.62, stain: 0.07, drops: 22, speed: [1.0, 2.8], pool: 0.6, drip: true },
  neck: { bone: 'neck_01', up: 1.5, stain: 0.08, drops: 20, speed: [0.9, 2.6], pool: 0.7, drip: true },
  shoulder: { bone: 'upperarm_l', up: 1.42, stain: 0.09, drops: 12, speed: [0.7, 1.8], pool: 0.55, drip: true },
  scalp: { bone: 'head', up: 1.7, stain: 0.085, drops: 8, speed: [0.3, 1.0], pool: 0.6, drip: false },
});
const LYING = new Set(['fallen', 'lie', 'prone']);
const LOW = new Set(['kneel', 'kneel2', 'sit', 'crouch']);
const GRAVITY = 9.8;
export const POOL_GROW_S = 16;
const STAIN_GROW_S = 2.5;
const DRIP_S = 25, DRIP_EVERY_S = 0.7;
const LOW_POOL_M = 0.3, POOL_MAX_M = 1.1;

const V = () => new THREE.Vector3();
const UP = new THREE.Vector3(0, 1, 0), FWD = new THREE.Vector3(0, 0, 1);

// ── the pictures: soft irregular blots, made from numbers (no canvas, so the gate can draw them) ──

/** A 64 px blot's alpha: a disc whose rim wanders by a few seeded harmonics, softened at the edge. */
export function blotAlpha(seed, size = 64, { lobes = 0.16, satellites = 3 } = {}) {
  const rnd = random(seed);
  const harm = [2, 3, 5, 7].map((k) => ({ k, a: lobes * (0.35 + rnd()) / k * 1.6, p: rnd() * Math.PI * 2 }));
  const sats = Array.from({ length: satellites }, () => {
    const a = rnd() * Math.PI * 2, d = 0.6 + rnd() * 0.25;
    return { x: Math.cos(a) * d, y: Math.sin(a) * d, r: 0.07 + rnd() * 0.08 };
  });
  const out = new Uint8Array(size * size * 4);
  for (let j = 0; j < size; j++) {
    for (let i = 0; i < size; i++) {
      const x = (i + 0.5) / size * 2 - 1, y = (j + 0.5) / size * 2 - 1;
      const r = Math.hypot(x, y), th = Math.atan2(y, x);
      let rim = 0.62;
      for (const h of harm) rim += h.a * Math.sin(h.k * th + h.p);
      let v = 1 - smooth((r - rim + 0.04) / 0.08);
      for (const s of sats) v = Math.max(v, 1 - smooth((Math.hypot(x - s.x, y - s.y) - s.r + 0.02) / 0.04));
      const o = (j * size + i) * 4, b = Math.round(255 * clamp(v, 0, 1));
      out[o] = out[o + 1] = out[o + 2] = out[o + 3] = b;
    }
  }
  return out;
}

const clamp = (x, a, b) => Math.min(b, Math.max(a, x));
const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };
function random(seed) {
  let s = (seed >>> 0) || 1;
  return () => { s = (s + 0x6d2b79f5) >>> 0; let t = s; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}

let shared = null;
function looks() {
  if (shared) return shared;
  const tex = (seed, opts) => {
    const t = new THREE.DataTexture(blotAlpha(seed, 64, opts), 64, 64, THREE.RGBAFormat);
    t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearFilter; t.needsUpdate = true;
    return t;
  };
  const flat = new THREE.PlaneGeometry(2, 2).rotateX(-Math.PI / 2);   // lies on the ground, radius 1
  const card = new THREE.PlaneGeometry(2, 2);                          // faces +Z, radius 1
  // Fresh blood is a deep red with a soft sheen; soaked into cloth it is duller. Not glossy: a
  // mirror-wet pool seen low across the ground shows the sky, and reads grey, not red (QA,
  // 2026-11-15: Lee's place at dusk), so the sheen is rough and the sky's share of it small.
  const wet = (alphaMap, color, roughness, offset) => new THREE.MeshStandardMaterial({ color, roughness, metalness: 0, alphaMap,
    envMapIntensity: 0.3, transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: offset, polygonOffsetUnits: offset });
  const pools = [11, 23, 37, 41].map((s) => wet(tex(s, { lobes: 0.2, satellites: 4 }), 0x7a0907, 0.42, -2));
  const stains = [5, 17, 29].map((s) => wet(tex(s, { lobes: 0.24, satellites: 2 }), 0x6e0a08, 0.6, -4));
  const splat = wet(tex(3, { lobes: 0.12, satellites: 2 }), 0x800b08, 0.5, -3);
  const drop = new THREE.MeshStandardMaterial({ color: 0x8a0c09, roughness: 0.4, metalness: 0, envMapIntensity: 0.3 });
  shared = { flat, card, pools, stains, splat, drop, bead: new THREE.IcosahedronGeometry(1, 0) };
  return shared;
}

const bones = new WeakMap();
/** The bone called `name` in `scene` (a contract skeleton's), or null. */
function boneOf(scene, name) {
  if (!scene) return null;
  let m = bones.get(scene);
  if (!m) { m = new Map(); scene.traverse((o) => { if (o.isBone && !m.has(o.name)) m.set(o.name, o); }); bones.set(scene, m); }
  return m.get(name) ?? null;
}

/** Where on the figure a `kind` of wound is (the parent's frame) and, for the head, the crown's way. */
export function woundSite(actor, kind) {
  const w = WOUND[kind] ?? WOUND.body;
  const scene = actor.body?.scene ?? null;
  actor.root.updateMatrixWorld(true);
  const bone = boneOf(scene, w.bone);
  const at = bone ? bone.getWorldPosition(V()) : actor.root.localToWorld(V().set(0, w.up, 0));
  let crown = null;
  if (kind === 'head' || kind === 'scalp') {
    const neck = boneOf(scene, 'neck_01');
    crown = neck && bone ? at.clone().sub(neck.getWorldPosition(V())) : UP.clone().transformDirection(actor.root.matrixWorld);
    if (crown.lengthSq() < 1e-8) crown.copy(UP);
    crown.normalize();
    at.addScaledVector(crown, 0.09);      // the head bone is at the skull's base; the head's middle is above it
  }
  return { bone, at, crown };
}

/** The way a ray comes onto the wound: from the blow's side, from above onto someone down, and
 *  down the crown for a scalping. */
export function woundWay(actor, kind, site, from) {
  if (kind === 'scalp') return site.crown.clone();
  const d = from ? from.clone().sub(site.at) : null;
  if (d) d.y = 0;
  let way = d && d.lengthSq() > 1e-6 ? d.normalize() : FWD.clone().applyAxisAngle(UP, actor.root.rotation.y);
  const down = actor.posture && LYING.has(actor.posture.kind) && (actor.posture.w ?? 1) > 0.5;
  if (down) way = way.multiplyScalar(0.35).add(UP).normalize();
  else if (kind === 'head') way.y += 0.25, way.normalize();
  return way;
}

/** The bones whose flesh and cloth a wound of each kind can be on. */
const NEAR_BONES = Object.freeze({
  body: ['spine_02', 'spine_03', 'clavicle_l', 'clavicle_r'],
  head: ['head', 'neck_01'],
  neck: ['neck_01', 'head', 'spine_03', 'clavicle_l', 'clavicle_r'],
  shoulder: ['upperarm_l', 'clavicle_l', 'spine_03'],
  scalp: ['head'],
});
const owned = new WeakMap();   // geometry -> Map(bone name -> the vertices that bone carries most)
function vertsOf(mesh, names) {
  const g = mesh.geometry, si = g?.attributes?.skinIndex, sw = g?.attributes?.skinWeight, bones = mesh.skeleton?.bones;
  if (!si || !sw || !bones) return [];
  let by = owned.get(g);
  if (!by) {
    const lists = new Map();
    for (let i = 0; i < si.count; i++) {
      let best = 0, w = -1;
      for (let k = 0; k < 4; k++) { const x = sw.getComponent(i, k); if (x > w) { w = x; best = si.getComponent(i, k); } }
      const name = bones[best]?.name;
      if (!name) continue;
      if (!lists.has(name)) lists.set(name, []);
      lists.get(name).push(i);
    }
    by = new Map([...lists].map(([k, v]) => [k, Uint32Array.from(v)]));
    owned.set(g, by);
  }
  return names.map((n) => by.get(n)).filter(Boolean);
}
const _bm = new THREE.Matrix4(), _nv = V(), _acc = V(), _pv = V(), _off = V();
/** A skinned vertex's normal, posed, in the world (the bone blend applied to the direction). */
function skinNormal(mesh, i, out) {
  const g = mesh.geometry, nrm = g.attributes.normal, si = g.attributes.skinIndex, sw = g.attributes.skinWeight, sk = mesh.skeleton;
  if (!nrm) return null;
  out.fromBufferAttribute(nrm, i).transformDirection(mesh.bindMatrix);
  _acc.set(0, 0, 0);
  for (let k = 0; k < 4; k++) {
    const w = sw.getComponent(i, k);
    if (!w) continue;
    const b = si.getComponent(i, k);
    _bm.multiplyMatrices(sk.bones[b].matrixWorld, sk.boneInverses[b]);
    _acc.addScaledVector(_nv.copy(out).transformDirection(_bm), w);
  }
  if (_acc.lengthSq() < 1e-12) return null;
  return out.copy(_acc).transformDirection(mesh.bindMatrixInverse).transformDirection(mesh.matrixWorld);
}

/**
 * The figure's own surface (its posed clothing or skin) where a line coming in along -`way`
 * onto `at` first meets it: { p, n, hit }, world. Only the vertices the wound's own bones carry
 * are posed and tried (a whole-body ray test poses every triangle: 80 ms on a near figure, a
 * stutter at every blow); of those within a finger's breadth of the line, the outermost.
 */
export function woundSurface(actor, at, way, kind = 'body') {
  const meshes = (actor.body?.meshes ?? []).filter((m) => m.isSkinnedMesh && m.visible !== false);
  const O = at.clone().addScaledVector(way, 0.7), D = way.clone().negate();
  for (const tol of [0.025, 0.05]) {
    let best = null, along = Infinity;
    for (const mesh of meshes) {
      for (const list of vertsOf(mesh, NEAR_BONES[kind] ?? NEAR_BONES.body)) {
        for (let j = 0; j < list.length; j++) {
          mesh.getVertexPosition(list[j], _pv).applyMatrix4(mesh.matrixWorld);
          const s = _off.copy(_pv).sub(O).dot(D);
          if (s <= 0 || s >= along) continue;
          if (_off.addScaledVector(D, -s).lengthSq() > tol * tol) continue;
          along = s; best = { mesh, i: list[j], p: _pv.clone() };
        }
      }
    }
    if (best) {
      const n = skinNormal(best.mesh, best.i, V()) ?? way.clone();
      if (n.dot(way) < 0) n.negate();
      // Lean the card toward the blow's line a little: a vertex normal on a fold can be steep.
      n.lerp(way, 0.35).normalize();
      return { p: O.clone().addScaledVector(D, along), n, hit: true };
    }
  }
  return { p: at.clone().addScaledVector(way, 0.12), n: way.clone(), hit: false };
}

/**
 * Blood under `parent`. `wound(actor, kind, { from })` marks the figure there and then;
 * `update(dt)` each frame spreads, drips, falls and follows a figure's change of level.
 */
export function createBloodFx(parent, { maxDrops = 320, maxSplats = 640, maxPools = 48, seed = 1812 } = {}) {
  const L = parent ? looks() : null;
  const group = new THREE.Group();
  group.name = 'jaunt_blood';
  parent?.add?.(group);
  const rnd = random(seed);
  const U = (a, b) => a + (b - a) * rnd();
  const drops = L ? new THREE.InstancedMesh(L.bead, L.drop, maxDrops) : null;
  const splats = L ? new THREE.InstancedMesh(L.flat, L.splat, maxSplats) : null;
  for (const m of [drops, splats]) if (m) { m.count = 0; m.frustumCulled = false; m.castShadow = false; m.receiveShadow = true; group.add(m); }
  drops?.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const flying = [];          // { p, v, ground, r }
  let splatN = 0;
  const pools = [];           // { mesh, r, target, age }
  const hurt = new Map();     // actor -> { scene, stains: [], pools: Map, drips: [] }
  const M = new THREE.Matrix4(), Q = new THREE.Quaternion(), S = V(), P = V();
  const inv = new THREE.Matrix4();

  /** world -> the parent's frame (the frame the figures stand in). */
  const local = (v) => { if (!parent) return v.clone(); parent.updateWorldMatrix(true, false); return v.clone().applyMatrix4(inv.copy(parent.matrixWorld).invert()); };
  const localDir = (d) => { if (!parent) return d.clone(); return d.clone().transformDirection(inv.copy(parent.matrixWorld).invert()); };

  /** The ground under (x, z) of the parent's frame, by the figure standing there. */
  function ground(actor, x, z) {
    const h = actor.heightAt;
    const e0 = (actor.e ?? 0) + (actor.spaceE ?? 0), n0 = (actor.n ?? 0) + (actor.spaceN ?? 0);
    const feet = Number.isFinite(actor.standY) ? actor.standY : typeof h === 'function' ? h(e0, n0) : actor.root.position.y;
    if (typeof h !== 'function') return feet;
    const slope = h(x, -z) - h(e0, n0);
    return feet + (Number.isFinite(slope) && Math.abs(slope) < 0.6 ? slope : 0);
  }
  /** The ground's tilt under (x, z): a quaternion turning +Y to its normal (identity on the flat
   *  or with no `heightAt`), so a splash or a pool lies on a slope instead of over it. */
  const TILT_STEP_M = 0.25;
  function tilt(actor, x, z, out) {
    const h = actor.heightAt;
    if (typeof h !== 'function') return out.identity();
    const e = x, n = -z, d = TILT_STEP_M;
    const dx = (h(e + d, n) - h(e - d, n)) / (2 * d), dn = (h(e, n + d) - h(e, n - d)) / (2 * d);
    if (!Number.isFinite(dx) || !Number.isFinite(dn) || Math.abs(dx) > 1.2 || Math.abs(dn) > 1.2) return out.identity();
    // In the parent's frame x is east and z is south (-n): the normal is (-dh/dx, 1, -dh/dz).
    return out.setFromUnitVectors(UP, V().set(-dx, 1, dn).normalize());
  }

  function throwDrops(actor, at, n, kind, count) {
    if (!drops) return;
    const w = WOUND[kind];
    for (let i = 0; i < count; i++) {
      if (flying.length >= maxDrops) flying.shift();
      const v = n.clone().multiplyScalar(U(w.speed[0], w.speed[1]))
        .add(V().set(U(-0.6, 0.6), U(0.3, 1.3), U(-0.6, 0.6)).multiplyScalar(w.speed[1] * 0.4));
      flying.push({ p: at.clone().addScaledVector(n, 0.02), v, actor, r: U(0.006, 0.014) });
    }
  }

  function land(f) {
    if (!splats) return;
    const r = f.r * U(3.0, 5.5) * (1 + Math.min(1.5, f.v.length() * 0.25));
    // Where it lands, on the ground there and lying with its slope (the owner, 2026-11-16,
    // "Floating blood": every drop came down to the height of the ground under the wound, so
    // on the dunes the ones that flew downhill hung in the air and the uphill ones were lost).
    const spin = Q.setFromAxisAngle(UP, U(0, Math.PI * 2));
    const q = tilt(f.actor, f.p.x, f.p.z, new THREE.Quaternion()).multiply(spin);
    M.compose(P.set(f.p.x, f.p.y + 0.004, f.p.z), q, S.set(r * U(0.8, 1.4), 1, r));
    splats.setMatrixAt(splatN % maxSplats, M);
    splatN++;
    splats.count = Math.min(splatN, maxSplats);
    splats.instanceMatrix.needsUpdate = true;
  }

  /** A stain on the figure at world `p`, normal `n`, carried by `bone` (or the figure's root). */
  function stainAt(entry, actor, kind, site, p, n) {
    const w = WOUND[kind];
    const mesh = new THREE.Mesh(L.card, L.stains[entry.stains.length % L.stains.length]);
    mesh.name = `wound_${kind}`;
    mesh.renderOrder = 2;
    mesh.position.copy(p).addScaledVector(n, 0.004);
    mesh.quaternion.setFromUnitVectors(FWD, n).multiply(Q.setFromAxisAngle(FWD, U(0, Math.PI * 2)));
    mesh.scale.setScalar(w.stain * U(0.85, 1.2));
    const holder = site.bone ?? actor.root;
    holder.updateWorldMatrix(true, false);
    holder.attach(mesh);
    entry.stains.push({ mesh, bone: site.bone ? site.bone.name : null, unit: mesh.scale.clone(), age: 0, kind });
    mesh.scale.copy(entry.stains.at(-1).unit).multiplyScalar(0.35);
  }

  function entryFor(actor) {
    let e = hurt.get(actor);
    if (!e) { e = { scene: actor.body?.scene ?? null, stains: [], pools: new Map(), drips: [] }; hurt.set(actor, e); }
    return e;
  }

  /** Pools for a figure that is down: one under each wounded place, once the fall is done. */
  function poolUnder(actor, e) {
    const p = actor.posture;
    if (!p || (p.w ?? 1) < 0.95) return;
    const lying = LYING.has(p.kind);
    if (!lying && !LOW.has(p.kind)) return;
    for (const d of e.drips) {
      const place = d.kind === 'body' || d.kind === 'shoulder' ? 'torso' : 'head';
      const key = `${place}:${lying ? 'down' : 'low'}`;
      const had = e.pools.get(key);
      const want = lying ? WOUND[d.kind].pool * U(0.85, 1.15) : LOW_POOL_M;
      if (had) { if (!d.pooled) { had.target = Math.min(POOL_MAX_M, Math.max(had.target, want) * 1.12); d.pooled = true; } continue; }
      d.pooled = true;
      const site = woundSite(actor, d.kind === 'shoulder' ? 'body' : d.kind);
      const at = local(site.at);
      if (pools.length >= maxPools) { const old = pools.shift(); group.remove(old.mesh); }
      const mesh = new THREE.Mesh(L.flat, L.pools[pools.length % L.pools.length]);
      mesh.name = 'blood_pool';
      mesh.receiveShadow = true;
      mesh.position.set(at.x, ground(actor, at.x, at.z) + 0.006 + 0.0015 * (pools.length % 4), at.z);
      mesh.quaternion.copy(tilt(actor, at.x, at.z, new THREE.Quaternion())).multiply(Q.setFromAxisAngle(UP, U(0, Math.PI * 2)));
      mesh.scale.setScalar(0.04);
      group.add(mesh);
      const pool = { mesh, r: 0.04, target: want, age: 0 };
      pools.push(pool);
      e.pools.set(key, pool);
    }
  }

  /** After a change of level the figure's bones are new: the stains go onto the same bones. */
  function rebind(actor, e) {
    const scene = actor.body?.scene ?? null;
    if (scene === e.scene || !scene) return;
    for (const s of e.stains) {
      const bone = s.bone ? boneOf(scene, s.bone) : null;
      const holder = bone ?? (s.bone ? null : actor.root);
      if (!holder) { s.mesh.removeFromParent(); continue; }
      const { position, quaternion, scale } = s.mesh;
      const keep = [position.clone(), quaternion.clone(), scale.clone()];
      holder.add(s.mesh);
      s.mesh.position.copy(keep[0]); s.mesh.quaternion.copy(keep[1]); s.mesh.scale.copy(keep[2]);
    }
    e.scene = scene;
  }

  const api = {
    /** `actor` is hit: a `kind` of wound (WOUND_KINDS), the blow from `from` (the parent's frame). */
    wound(actor, kind, { from = null } = {}) {
      if (!L || !actor?.root || actor.disposed) return false;
      if (!WOUND[kind]) kind = 'body';
      const e = entryFor(actor);
      const site = woundSite(actor, kind);
      const way = woundWay(actor, kind, site, from && parent ? from.clone().applyMatrix4(parent.matrixWorld) : from);
      const s = woundSurface(actor, site.at, way, kind);
      stainAt(e, actor, kind, site, s.p, s.n);
      throwDrops(actor, local(s.p), localDir(s.n), kind, WOUND[kind].drops);
      e.drips.push({ kind, age: 0, next: DRIP_EVERY_S, stain: e.stains.at(-1), pooled: false });
      return true;
    },
    update(dt) {
      if (!(dt > 0) || !L) return;
      // Drops in the air: under gravity, onto the ground.
      for (let i = flying.length - 1; i >= 0; i--) {
        const f = flying[i];
        f.v.y -= GRAVITY * dt;
        f.p.addScaledVector(f.v, dt);
        const g = ground(f.actor, f.p.x, f.p.z);
        if (f.p.y <= g + 0.003) { f.p.y = g; land(f); flying.splice(i, 1); }
      }
      if (drops) {
        drops.count = flying.length;
        flying.forEach((f, i) => drops.setMatrixAt(i, M.compose(f.p, Q.identity(), S.setScalar(f.r))));
        drops.instanceMatrix.needsUpdate = true;
      }
      for (const [actor, e] of hurt) {
        if (actor.disposed) { for (const s of e.stains) s.mesh.removeFromParent(); hurt.delete(actor); continue; }
        rebind(actor, e);
        for (const s of e.stains) {
          if (s.age >= STAIN_GROW_S) continue;
          s.age += dt;
          s.mesh.scale.copy(s.unit).multiplyScalar(0.35 + 0.65 * smooth(s.age / STAIN_GROW_S));
        }
        poolUnder(actor, e);
        // Someone still up keeps bleeding a little where the wound is.
        const up = !actor.posture || !LYING.has(actor.posture.kind);
        for (const d of e.drips) {
          d.age += dt;
          if (!up || !WOUND[d.kind].drip || d.age > DRIP_S || !d.stain.mesh.parent || !actor.root.visible) continue;
          d.next -= dt;
          if (d.next > 0) continue;
          d.next = DRIP_EVERY_S * U(0.6, 1.5);
          const at = local(d.stain.mesh.getWorldPosition(V()));
          throwDrops(actor, at, V().set(0, -1, 0), d.kind, 1);
          flying.at(-1).v.set(U(-0.05, 0.05), -0.2, U(-0.05, 0.05));
        }
      }
      for (const p of pools) {
        if (p.r >= p.target - 1e-4 && p.age > POOL_GROW_S) continue;
        p.age += dt;
        p.r = Math.max(0.04, p.target * Math.sqrt(Math.min(1, p.age / POOL_GROW_S)));
        p.mesh.scale.setScalar(p.r);
      }
    },
    get counts() {
      let stains = 0;
      for (const e of hurt.values()) stains += e.stains.filter((s) => s.mesh.parent).length;
      return { wounded: hurt.size, stains, drops: flying.length, splats: splats?.count ?? 0, pools: pools.length };
    },
    /** The pools drawn now, for the gate: where and how wide. */
    get pools() { return pools.map((p) => ({ x: p.mesh.position.x, y: p.mesh.position.y, z: p.mesh.position.z, r: p.r, target: p.target })); },
    get splatsAt() {
      const out = [];
      for (let i = 0; i < (splats?.count ?? 0); i++) { splats.getMatrixAt(i, M); out.push(V().setFromMatrixPosition(M)); }
      return out;
    },
    set visible(v) { group.visible = !!v; },
    get visible() { return group.visible; },
    clear() {
      for (const e of hurt.values()) for (const s of e.stains) s.mesh.removeFromParent();
      hurt.clear();
      for (const p of pools) group.remove(p.mesh);
      pools.length = 0; flying.length = 0; splatN = 0;
      if (drops) drops.count = 0;
      if (splats) splats.count = 0;
    },
    dispose() { api.clear(); group.removeFromParent(); drops?.dispose(); splats?.dispose(); },
  };
  return api;
}

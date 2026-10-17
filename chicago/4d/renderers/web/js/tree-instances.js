/**
 * tree-instances.js — a wood of grown trees, each species built ONCE and stood
 * wherever the planters put it (T-2743).
 *
 * WHY. Until this, every stem in the 1835 and 1812 timber was its own geometry,
 * merged into 120 m chunks: about 92 KB of CPU copy and as much again on the GPU
 * per tree, which is why the wood was drawn at 40 % of its recorded density on
 * full detail and 19 % on light. A grown tree (`tree-model.js`) is a few thousand
 * triangles near and a hundred far, and the same few variants of a species stand
 * for hundreds of stems, so a stem costs one instance — a matrix — and the wood
 * can be drawn at the density its records state.
 *
 * WHAT. Per species archetype (a zone record's species, form and colours) a few
 * VARIANTS, each grown once and meshed at three levels (`near`, `mid`, `far`).
 * Every stem is one instance in two `BatchedMesh` pairs (wood and leaves):
 *
 *   the SHADE set   stems within SHADOW_M of the eye, near or mid, casting shadow;
 *   the FAR set     stems beyond it, mid or far, casting none.
 *
 * Each stem sits in both and is visible in one, the parkway elms' arrangement
 * (street-trees.js, T-2493). The level and the set are re-chosen when the eye has
 * moved STEP_M, never per frame. Every instance is culled by three per stem in
 * the view and the sun.
 *
 * Positions, species, heights and the density are the planters' (`trees.js`),
 * unchanged; this file decides only how a stem is drawn.
 */

import * as THREE from 'three';
import { buildTreeTemplate, archFor, mulberry32 } from './tree-model.js';
import { loadCompressed, countSheet } from './ktx2.js';

/** Level distances by Scene detail, metres from the eye. A near tree is a few
 *  thousand triangles, so the near ring is kept to the trees a visitor walks
 *  among; past `mid` a tree is its far masses. */
const LEVELS = {
  full: { near: 42, mid: 170 },
  balanced: { near: 32, mid: 140 },
  light: { near: 22, mid: 110 },
};
/** Only the stems this close cast shadows. The sun's box reaches 240 m
 *  (world.js), and a far tree's shadow is a few pixels of dapple. */
const SHADOW_M = { full: 150, balanced: 120, light: 80 };
const STEP_M = 4;
/** Variants per archetype, by how many stems it carries: a minority species
 *  repeated twice reads as one tree twice; a cottonwood stand of four hundred
 *  needs more faces than that. */
const variantsFor = (n) => (n >= 150 ? 3 : n >= 25 ? 2 : 1);
/** The phone's tier grows fewer, and draws no `near` level at all: its nearest
 *  trees are the `mid` mesh, which is what a 390-px screen resolves at a walk. */
const variantsForLight = (n) => (n >= 150 ? 2 : 1);

/** The forms drawn as grown trees. A thicket and a dooryard shrub are many
 *  small stems, not a tree, and stay on trees.js's own path, as does a stem
 *  carrying a July head (that file draws the head). */
export const isGrownForm = (spec) => spec.form !== 'thicket' && spec.form !== 'shrub' && !spec.head;

function archetypeKey(spec) {
  return [spec.speciesId ?? spec.common, spec.form, spec.common, spec.dark, spec.light, spec.bark,
    spec.conf ?? 0.5].join('|');
}

/**
 * Collects stems, then builds the batches. `add` is called by the planters in
 * place of trees.js `addTree` for every tree-form stem.
 */
export class TreeInstances {
  constructor({ level = 'full', shadowM = null, variants = null, name = 'timber', levels = null } = {}) {
    this.name = name;
    this.level = LEVELS[level] ? level : 'full';
    this.dist = levels?.[this.level] ?? LEVELS[this.level];
    variants ??= this.level === 'light' ? variantsForLight : variantsFor;
    this.shadowM = shadowM ?? SHADOW_M[this.level];
    this.variantsFor = variants;
    this.kinds = new Map();
    this.stems = [];
  }

  /** One stem. Its height in the spec's band, its turn and its variant are drawn
   *  from a stream seeded by where it stands, so the planter's own stream is not
   *  consumed and a re-grown species moves no other stem. */
  add(spec, x, groundY, z, scale = 1, { yaw = null, variant = null } = {}) {
    const rnd = mulberry32(hashString(`${Math.round(x * 100)},${Math.round(z * 100)}`));
    const key = archetypeKey(spec);
    let kind = this.kinds.get(key);
    if (!kind) {
      kind = { key, spec, count: 0, hMin: Infinity, hMax: 0 };
      this.kinds.set(key, kind);
    }
    const h = (spec.h[0] + (spec.h[1] - spec.h[0]) * rnd()) * scale;
    kind.count++;
    kind.hMin = Math.min(kind.hMin, h);
    kind.hMax = Math.max(kind.hMax, h);
    const turn = rnd() * Math.PI * 2;
    const pick = rnd();
    this.stems.push({ kind, x, y: groundY, z, h, yaw: yaw ?? turn, pick, variant });
    return h;
  }

  get count() { return this.stems.length; }

  /**
   * Grow the variants and build the four batches.
   * @returns {{ group: THREE.Group, update(eye: THREE.Vector3): void, stats: object, dispose(): void }}
   */
  async build({ woodMat, leafMat, woodDepth, leafDepth, woodDistance, leafDistance, checkpoint = () => null,
    season = {} }) {
    const group = new THREE.Group();
    group.name = `${this.name}s-grown`;
    const stats = { stems: this.stems.length, archetypes: this.kinds.size, variants: 0,
      triangles: 0, templateTriangles: 0, near: 0, mid: 0, far: 0, shade: 0, drawCalls: 0 };
    if (!this.stems.length) return { group, stats, update() {}, dispose() {} };

    // 1. Grow each archetype's variants at its own median height, and mesh each
    //    at the three levels.
    const geo = { shade: { wood: [], leaves: [] }, far: { wood: [], leaves: [] } };
    for (const kind of this.kinds.values()) {
      const n = this.variantsFor(kind.count);
      const midH = (kind.hMin + kind.hMax) / 2;
      const spec = { ...kind.spec, h: [midH, midH] };
      kind.variants = [];
      for (let v = 0; v < n; v++) {
        const pause = checkpoint(); if (pause) await pause;
        const seed = (hashString(kind.key) + v * 7919) >>> 0;
        const o = { conf: spec.conf ?? 0.5, ...season };
        const light = this.level === 'light';
        const first = buildTreeTemplate(spec, seed, light ? 'mid' : 'near', o);
        const mid = light ? first : buildTreeTemplate(spec, seed, 'mid', { ...o, skeleton: first.skeleton });
        const far = buildTreeTemplate(spec, seed, 'far', { ...o, skeleton: first.skeleton });
        first.skeleton = null;
        far.skeleton = null;
        kind.variants.push({ H: first.height, levels: light ? { mid, far } : { near: first, mid, far } });
        stats.variants++;
      }
    }

    // 2. The geometry each set holds: the shade set near and mid, the far set mid
    //    and far; on the phone's tier the shade set mid and the far set far.
    const sets = this.level === 'light' ? { shade: ['mid'], far: ['far'] } : { shade: ['near', 'mid'], far: ['mid', 'far'] };
    const sizes = {};
    for (const [set, lv] of Object.entries(sets)) {
      const s = { wood: [0, 0], leaves: [0, 0] };
      for (const kind of this.kinds.values()) {
        for (const v of kind.variants) {
          for (const l of lv) {
            for (const part of ['wood', 'leaves']) {
              const g = v.levels[l][part];
              s[part][0] += g.attributes.position.count;
              s[part][1] += g.index.count;
            }
          }
        }
      }
      sizes[set] = s;
    }
    const n = this.stems.length;
    const make = (set, part, mat, depth, distance) => {
      const [vc, ic] = sizes[set][part];
      const b = new THREE.BatchedMesh(n, Math.max(3, vc), Math.max(3, ic), mat);
      b.name = `${this.name}-${set}-${part}`;
      b.sortObjects = false;
      b.castShadow = set === 'shade';
      b.receiveShadow = true;
      if (depth) b.customDepthMaterial = depth;
      if (distance) b.customDistanceMaterial = distance;
      return b;
    };
    const batches = {
      shade: { wood: make('shade', 'wood', woodMat, woodDepth, woodDistance),
        leaves: make('shade', 'leaves', leafMat, leafDepth, leafDistance) },
      far: { wood: make('far', 'wood', woodMat, null, null),
        leaves: make('far', 'leaves', leafMat, null, null) },
    };
    for (const [set, lv] of Object.entries(sets)) {
      for (const kind of this.kinds.values()) {
        for (const v of kind.variants) {
          v.ids = v.ids ?? {};
          v.ids[set] = {};
          for (const l of lv) {
            v.ids[set][l] = {
              wood: batches[set].wood.addGeometry(v.levels[l].wood),
              leaves: batches[set].leaves.addGeometry(v.levels[l].leaves),
            };
          }
        }
      }
    }
    const tris = (v, l) => (v.levels[l].wood.index.count + v.levels[l].leaves.index.count) / 3;
    for (const kind of this.kinds.values()) {
      for (const v of kind.variants) {
        v.tris = {};
        for (const l of Object.keys(v.levels)) {
          v.tris[l] = tris(v, l);
          stats.templateTriangles += v.tris[l];
        }
      }
    }

    // 3. Every stem in both sets, starting far and unshaded until the first update.
    const m = new THREE.Matrix4();
    const q = new THREE.Quaternion();
    const up = new THREE.Vector3(0, 1, 0);
    const pos = new THREE.Vector3();
    const scl = new THREE.Vector3();
    for (const s of this.stems) {
      const nv = s.kind.variants.length;
      const v = s.kind.variants[s.variant != null ? s.variant % nv : Math.min(nv - 1, Math.floor(s.pick * nv))];
      s.v = v;
      const k = s.h / v.H;
      // A width jitter, so two stems of one variant side by side
      // are not the same silhouette.
      q.setFromAxisAngle(up, s.yaw);
      pos.set(s.x, s.y - 0.2 * k, s.z);
      const w = k * (0.92 + s.pick * 0.16);
      scl.set(w, k, w);
      m.compose(pos, q, scl);
      s.inst = {};
      for (const set of ['shade', 'far']) {
        const l = sets[set][sets[set].length - 1];
        s.inst[set] = {
          wood: batches[set].wood.addInstance(v.ids[set][l].wood),
          leaves: batches[set].leaves.addInstance(v.ids[set][l].leaves),
        };
        batches[set].wood.setMatrixAt(s.inst[set].wood, m);
        batches[set].leaves.setMatrixAt(s.inst[set].leaves, m);
      }
      batches.shade.wood.setVisibleAt(s.inst.shade.wood, false);
      batches.shade.leaves.setVisibleAt(s.inst.shade.leaves, false);
      s.level = sets.far[sets.far.length - 1];
      s.shade = false;
    }
    for (const set of Object.values(batches)) {
      for (const b of Object.values(set)) {
        b.computeBoundingBox();
        b.computeBoundingSphere();
        group.add(b);
        stats.drawCalls++;
      }
    }
    // The templates are copied into the batches; their own buffers are scratch,
    // and are let go here, not kept beside the copies.
    for (const kind of this.kinds.values()) {
      for (const v of kind.variants) {
        for (const l of Object.values(v.levels)) { l.wood.dispose(); l.leaves.dispose(); }
        v.levels = null;
      }
    }

    // 4. Level and set by distance, re-chosen when the eye has moved STEP_M.
    const dist = this.dist;
    const shadeM = this.shadowM;
    let at = null;
    const update = (eye) => {
      if (!eye) return;
      if (at && (at.x - eye.x) ** 2 + (at.z - eye.z) ** 2 < STEP_M * STEP_M) return;
      at = { x: eye.x, z: eye.z };
      let t = 0; let nn = 0; let nm = 0; let nf = 0; let ns = 0;
      for (const s of this.stems) {
        const dx = s.x - eye.x; const dz = s.z - eye.z;
        const d = Math.sqrt(dx * dx + dz * dz);
        const shade = d <= shadeM;
        const level = d <= dist.near ? 'near' : d <= dist.mid ? 'mid' : 'far';
        if (shade !== s.shade) {
          batches.shade.wood.setVisibleAt(s.inst.shade.wood, shade);
          batches.shade.leaves.setVisibleAt(s.inst.shade.leaves, shade);
          batches.far.wood.setVisibleAt(s.inst.far.wood, !shade);
          batches.far.leaves.setVisibleAt(s.inst.far.leaves, !shade);
          s.shade = shade;
          s.level = null;
        }
        // The nearest level the set holds to the one wanted (see `sets`).
        const want = nearestLevel(sets[shade ? 'shade' : 'far'], level);
        if (want !== s.level) {
          const set = shade ? 'shade' : 'far';
          batches[set].wood.setGeometryIdAt(s.inst[set].wood, s.v.ids[set][want].wood);
          batches[set].leaves.setGeometryIdAt(s.inst[set].leaves, s.v.ids[set][want].leaves);
          s.level = want;
        }
        t += s.v.tris[want] * 1;
        if (want === 'near') nn++; else if (want === 'mid') nm++; else nf++;
        if (shade) ns++;
      }
      stats.triangles = Math.round(t);
      stats.near = nn; stats.mid = nm; stats.far = nf; stats.shade = ns;
    };
    const dispose = () => {
      for (const set of Object.values(batches)) for (const b of Object.values(set)) { group.remove(b); b.dispose(); }
    };
    return { group, stats, update, dispose, batches };
  }
}

const ORDER = { near: 0, mid: 1, far: 2 };
function nearestLevel(held, level) {
  let best = held[0];
  for (const l of held) if (Math.abs(ORDER[l] - ORDER[level]) < Math.abs(ORDER[best] - ORDER[level])) best = l;
  return best;
}

function hashString(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); }
  return h >>> 0;
}

/**
 * The two materials a grown tree draws with, and their shadow-pass twins.
 * Bark: the species' tile from the bark atlas with its normal map. Leaves: the
 * species' spray from the leaf atlas, cut out by alpha test, with a little
 * skylight transmitted through the blade. Both sway with the trees.js wind.
 */
export async function createGrownTreeMaterials({ assetBase, uWind, confidence = null, patchWind, lowSpec = false,
  alphaCutoff = 0.5, problems = [] }) {
  const base = new URL('textures/trees/', assetBase);
  // A phone takes each atlas at half size: a quarter of the GPU memory, and the
  // level it would sample from a crown a few metres off on a 390-px screen anyway
  // (the parkway elms' rule since T-2158, PR 773).
  // The .ktx2 first, where this GPU takes a block format (ktx2.js: a quarter to an
  // eighth of the memory, and the phone's tier drops its top level there too);
  // the WebP otherwise.
  const load = async (name, srgb) => {
    const packed = await loadCompressed(new URL(name.replace(/\.webp$/, '.ktx2'), base).href, { srgb });
    if (packed) {
      countSheet(packed);
      packed.anisotropy = lowSpec ? 2 : 8;
      // Once on the GPU the transcoded levels are scratch: let them go, as the
      // terrain's tiles do (a lost context reloads the page, upload-release.js).
      packed.onUpdate = () => { for (const m of packed.mipmaps) m.data = null; };
      return packed;
    }
    try {
      const res = await fetch(new URL(name, base).href);
      if (!res.ok) throw new Error(`${res.status}`);
      const blob = await res.blob();
      const full = await createImageBitmap(blob, { imageOrientation: 'flipY', premultiplyAlpha: 'none',
        colorSpaceConversion: 'none' });
      const bmp = lowSpec
        ? await createImageBitmap(full, { resizeWidth: full.width >> 1, resizeHeight: full.height >> 1,
          resizeQuality: 'high', premultiplyAlpha: 'none', colorSpaceConversion: 'none' })
        : full;
      if (bmp !== full) full.close();
      const t = new THREE.Texture(bmp);
      t.flipY = false;
      if (srgb) t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = lowSpec ? 2 : 8;
      t.minFilter = THREE.LinearMipmapLinearFilter;
      t.generateMipmaps = true;
      t.needsUpdate = true;
      return t;
    } catch (err) {
      problems.push(`trees: the grown-tree texture ${name} did not load (${err.message}) — trees draw untextured`);
      return null;
    }
  };
  const [barkC, barkN, leafA] = await Promise.all([
    // A phone draws bark without its relief, so it does not fetch the map.
    load('bark_basecolor.webp', true), lowSpec ? null : load('bark_normal.webp', false), load('leaf_atlas.webp', true),
  ]);
  const woodMat = new THREE.MeshStandardMaterial({
    vertexColors: true, map: barkC, normalMap: lowSpec ? null : barkN, roughness: 0.94, metalness: 0,
  });
  woodMat.name = 'timber-wood';
  const leafMat = new THREE.MeshStandardMaterial({
    vertexColors: true, map: leafA, roughness: 0.78, metalness: 0,
    side: THREE.DoubleSide, alphaTest: alphaCutoff,
  });
  leafMat.name = 'timber-leaves';
  patchWind(woodMat, uWind);
  patchLeaves(leafMat, uWind, patchWind);
  confidence?.patch(woodMat);
  confidence?.patch(leafMat);
  const leafDepth = new THREE.MeshDepthMaterial({ map: leafA, alphaTest: alphaCutoff, side: THREE.DoubleSide,
    depthPacking: THREE.RGBADepthPacking });
  const leafDistance = new THREE.MeshDistanceMaterial({ map: leafA, alphaTest: alphaCutoff, side: THREE.DoubleSide });
  const woodDepth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  const woodDistance = new THREE.MeshDistanceMaterial();
  for (const mm of [leafDepth, leafDistance, woodDepth, woodDistance]) {
    patchWind(mm, uWind);
    confidence?.patch(mm);
  }
  return {
    woodMat, leafMat, woodDepth, leafDepth, woodDistance, leafDistance,
    dispose() {
      for (const x of [woodMat, leafMat, woodDepth, leafDepth, woodDistance, leafDistance, barkC, barkN, leafA]) x?.dispose();
      for (const t of [barkC, barkN, leafA]) t?.image?.close?.();
    },
  };
}

/** The wind, then a little skylight through the blade: a thin leaf transmits,
 *  so a crown's shaded side is green, not black. */
function patchLeaves(material, uWind, patchWind) {
  patchWind(material, uWind);
  const wind = material.onBeforeCompile;
  material.onBeforeCompile = (shader, r) => {
    wind(shader, r);
    shader.fragmentShader = shader.fragmentShader.replace('#include <lights_fragment_end>', `
#include <lights_fragment_end>
reflectedLight.indirectDiffuse += diffuseColor.rgb * 0.22;
`);
  };
  material.customProgramCacheKey = () => 'grown-tree-leaves-t2743';
}

export { archFor };

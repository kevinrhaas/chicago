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
 * With `cull` (the timber, T-2808) the far set also holds a `distant` level past
 * DISTANT_M, and a stem too small to see is hidden (CULL_PER_M).
 * Each stem sits in both and is visible in one, the parkway elms' arrangement
 * (street-trees.js, T-2493). The level and the set are re-chosen when the eye has
 * moved STEP_M, never per frame. Every instance is culled by three per stem in
 * the view and the sun.
 *
 * T-2948 — A LEVEL CHANGE DISSOLVES, IT DOES NOT SNAP. With `fadeS` (the parkway
 * elms', street-trees.js) a stem changing level or set is drawn at both for that
 * many seconds, the old one dithered out as the new one is dithered in on the
 * same screen pattern (`patchFade`), so a crown's leaves thicken and its shadow
 * comes and goes over a few frames instead of in one. Each set holds a second,
 * GHOST instance per stem for the level going out. A stem stays at its finer
 * level HYSTERESIS_M past a ring's edge, so a visitor standing on the edge does
 * not set it flickering, and a jump (a teleport, a Jump in time) settles at once.
 * With `castFar` the far set casts too, with its coarse crowns, out to the sun's
 * own box: the owner saw the street's shade end 32 m ahead and pop in as he walked.
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
/** T-2948: how far past a ring's edge a stem keeps its finer level and set, and
 *  how far the eye must move between two updates for it to be a jump (no fade). */
const HYSTERESIS_M = 3;
const JUMP_M = 40;
/**
 * T-2808 — SMALL STEMS ARE NOT DRAWN WHERE THEY ARE A FEW PIXELS. With `cull`
 * (the timber's own; the 1904 street elms do not ask), a stem is hidden past
 * this many metres per metre of its height: at 175 a stem stands about four
 * pixels tall on a 800-px-high view (a 60-degree field) when it goes. That
 * is a woods-edge shrub at 300-450 m and a young tree at a kilometre; a grown
 * tree goes only in the haze. Coarser tiers let go sooner.
 */
const CULL_PER_M = { full: 175, balanced: 150, light: 120 };
/**
 * T-2808 — THE DISTANT LEVEL. Past this many metres (with `cull`, the timber's
 * own) a tree is drawn as its trunk and a crown of half the far level's masses:
 * a 20 m tree at 600 m stands about 25 px tall, and the far level's limbs and
 * second cards are below what those pixels resolve. Measured at the west
 * prairie stand, which looks across a kilometre of wood, it is most of the trees
 * any stand draws.
 */
const DISTANT_M = { full: 620, balanced: 520, light: 400 };
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

/** The name of the group a wood's batches stand in (`TreeInstances.build`), so a
 *  caller can find them by it: the 1835 timber's is `grownGroupName('timber')`,
 *  which main.js hands the Confidence view to ghost as a dither (T-2863). */
export const grownGroupName = (name) => `${name}s-grown`;

function archetypeKey(spec) {
  // A habit named outright (`spec.arch`, T-3017) is its own archetype.
  return [spec.speciesId ?? spec.common, spec.form, spec.common, spec.dark, spec.light, spec.bark,
    spec.conf ?? 0.5].join('|') + (spec.arch ? `|${spec.arch}` : '');
}

/**
 * Collects stems, then builds the batches. `add` is called by the planters in
 * place of trees.js `addTree` for every tree-form stem.
 */
export class TreeInstances {
  constructor({ level = 'full', shadowM = null, variants = null, name = 'timber', levels = null, cull = false,
    fadeS = 0, castFar = false } = {}) {
    this.name = name;
    this.fadeS = fadeS;
    this.castFar = castFar;
    this.level = LEVELS[level] ? level : 'full';
    this.cullPerM = cull ? CULL_PER_M[this.level] : Infinity;
    this.dist = levels?.[this.level] ?? LEVELS[this.level];
    // T-2833: a caller's own rings may name a `distant` reach without culling.
    this.distantM = cull ? DISTANT_M[this.level] : (this.dist.distant ?? Infinity);
    variants ??= this.level === 'light' ? variantsForLight : variantsFor;
    this.shadowM = shadowM ?? SHADOW_M[this.level];
    this.variantsFor = variants;
    this.kinds = new Map();
    this.stems = [];
  }

  /** One stem. Its height in the spec's band, its turn and its variant are drawn
   *  from a stream seeded by where it stands, so the planter's own stream is not
   *  consumed and a re-grown species moves no other stem. */
  add(spec, x, groundY, z, scale = 1, { yaw = null, variant = null, lodK = 1, crownW = null } = {}) {
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
    // T-3223: a planter that measured a stem's spread (the front yards keep doors clear
    // by it) names its crown width, and the stem is drawn to it.
    this.stems.push({ kind, x, y: groundY, z, h, yaw: yaw ?? turn, pick, variant, lodK, crownW });
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
    group.name = grownGroupName(this.name);
    const stats = { stems: this.stems.length, archetypes: this.kinds.size, variants: 0,
      triangles: 0, templateTriangles: 0, near: 0, mid: 0, far: 0, shade: 0, drawCalls: 0 };
    if (!this.stems.length) return { group, stats, update() {}, settle() {}, dispose() {} };
    const t0 = performance.now();
    let paused = 0;

    // 1. Grow each archetype's variants at its own median height, and mesh each
    //    at the three levels.
    const geo = { shade: { wood: [], leaves: [] }, far: { wood: [], leaves: [] } };
    for (const kind of this.kinds.values()) {
      const n = this.variantsFor(kind.count);
      const midH = (kind.hMin + kind.hMax) / 2;
      const spec = { ...kind.spec, h: [midH, midH] };
      kind.variants = [];
      for (let v = 0; v < n; v++) {
        const pause = checkpoint(); if (pause) { const p0 = performance.now(); await pause; paused += performance.now() - p0; }
        const seed = (hashString(kind.key) + v * 7919) >>> 0;
        const light = this.level === 'light';
        // T-3017: the phone's tier asks a grown habit that has one (the parkway
        // elm) for its coarse leaf: fewer, larger sprays.
        // T-3223: an evergreen (the front yards' arborvitae) keeps its summer crown in every Season.
        const o = { conf: spec.conf ?? 0.5, ...(spec.evergreen ? {} : season), coarse: light };
        const first = buildTreeTemplate(spec, seed, light ? 'mid' : 'near', o);
        const mid = light ? first : buildTreeTemplate(spec, seed, 'mid', { ...o, skeleton: first.skeleton });
        const far = buildTreeTemplate(spec, seed, 'far', { ...o, skeleton: first.skeleton });
        const distant = Number.isFinite(this.distantM)
          ? buildTreeTemplate(spec, seed, 'distant', { ...o, skeleton: first.skeleton }) : null;
        first.skeleton = null;
        far.skeleton = null;
        if (distant) distant.skeleton = null;
        const levels = light ? { mid, far } : { near: first, mid, far };
        if (distant) levels.distant = distant;
        kind.variants.push({ H: first.height, R: first.crownR, levels });
        stats.variants++;
      }
    }

    stats.growMs = Math.round(performance.now() - t0 - paused);
    // 2. The geometry each set holds: the shade set near and mid, the far set mid
    //    and far; on the phone's tier the shade set mid and the far set far.
    const sets = this.level === 'light' ? { shade: ['mid'], far: ['far'] } : { shade: ['near', 'mid'], far: ['mid', 'far'] };
    if (Number.isFinite(this.distantM)) sets.far.push('distant');
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
    const fading = this.fadeS > 0;
    const castFar = this.castFar;
    const make = (set, part, mat, depth, distance) => {
      const [vc, ic] = sizes[set][part];
      // T-2948: a fading wood holds a ghost instance per stem beside its own.
      const b = new THREE.BatchedMesh(fading ? 2 * n : n, Math.max(3, vc), Math.max(3, ic), mat);
      b.name = `${this.name}-${set}-${part}`;
      b.sortObjects = false;
      b.castShadow = set === 'shade' || castFar;
      b.receiveShadow = true;
      if (depth) b.customDepthMaterial = depth;
      if (distance) b.customDistanceMaterial = distance;
      return b;
    };
    const batches = {
      shade: { wood: make('shade', 'wood', woodMat, woodDepth, woodDistance),
        leaves: make('shade', 'leaves', leafMat, leafDepth, leafDistance) },
      far: { wood: make('far', 'wood', woodMat, castFar ? woodDepth : null, castFar ? woodDistance : null),
        leaves: make('far', 'leaves', leafMat, castFar ? leafDepth : null, castFar ? leafDistance : null) },
    };
    // A stem's instance pair (wood and leaves) in one set: shown, given a level,
    // given a fade (1 whole; 0..1 coming in; -1..0 going out, see patchFade).
    const show = (p, set, on) => {
      batches[set].wood.setVisibleAt(p.wood, on);
      batches[set].leaves.setVisibleAt(p.leaves, on);
    };
    const shape = (p, set, v, l) => {
      batches[set].wood.setGeometryIdAt(p.wood, v.ids[set][l].wood);
      batches[set].leaves.setGeometryIdAt(p.leaves, v.ids[set][l].leaves);
    };
    const fadeTo = (p, set, a) => {
      _fade.set(1, 1, 1, a);
      batches[set].wood.setColorAt(p.wood, _fade);
      batches[set].leaves.setColorAt(p.leaves, _fade);
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

    stats.batchMs = Math.round(performance.now() - t0 - paused - stats.growMs);
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
      // The foot is set a little into the ground, under its root flare; T-3223: a small
      // plant (the front yards' bedding) names its own, so a geranium is not half buried.
      pos.set(s.x, s.y - (s.kind.spec.sinkM ?? 0.2) * k, s.z);
      const w = s.crownW && v.R ? (s.crownW / (2 * v.R)) * (0.96 + s.pick * 0.04) : k * (0.92 + s.pick * 0.16);
      scl.set(w, k, w);
      m.compose(pos, q, scl);
      s.inst = {};
      s.ghost = fading ? {} : null;
      for (const set of ['shade', 'far']) {
        const l = sets[set][sets[set].length - 1];
        const pair = () => {
          const p = {
            wood: batches[set].wood.addInstance(v.ids[set][l].wood),
            leaves: batches[set].leaves.addInstance(v.ids[set][l].leaves),
          };
          batches[set].wood.setMatrixAt(p.wood, m);
          batches[set].leaves.setMatrixAt(p.leaves, m);
          return p;
        };
        s.inst[set] = pair();
        if (fading) {
          s.ghost[set] = pair();
          show(s.ghost[set], set, false);
        }
      }
      show(s.inst.shade, 'shade', false);
      s.level = sets.far[sets.far.length - 1];
      s.shade = false;
      s.fade = null;
      // A re-build (trees.js setSeason, T-2864) starts every stem drawn, so none is culled yet.
      s.culled = false;
    }
    // Every instance's fade starts whole (three fills a new colour texture with 1).
    if (fading) {
      for (const set of Object.values(batches)) for (const b of Object.values(set)) b.setColorAt(0, WHOLE);
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
    const cullPerM = this.cullPerM;
    const distantM = this.distantM;
    const fadeS = this.fadeS;
    const hyst = fading ? HYSTERESIS_M : 0;
    const levelAt = (d) => (d <= dist.near ? 'near' : d <= dist.mid ? 'mid' : d <= distantM ? 'far' : 'distant');
    // T-2948: the stems dissolving from one level (or set) to another.
    const live = new Set();
    const settle = (s) => {
      const f = s.fade;
      show(f.out, f.outSet, false);
      fadeTo(f.out, f.outSet, 1);
      fadeTo(s.inst[f.inSet], f.inSet, 1);
      s.fade = null;
      live.delete(s);
    };
    const settleAll = () => { for (const s of live) settle(s); stats.fading = 0; };
    /** Draw a stem at `want` in the shade set or the far set, at once or dissolving. */
    const move = (s, shade, want, smooth) => {
      const from = s.shade ? 'shade' : 'far';
      const to = shade ? 'shade' : 'far';
      if (s.fade) settle(s);
      if (!smooth || s.level == null) {
        if (from !== to) { show(s.inst[from], from, false); show(s.inst[to], to, true); }
        shape(s.inst[to], to, s.v, want);
      } else if (from !== to) {
        // The other set's own instance comes in; this set's goes out where it is.
        shape(s.inst[to], to, s.v, want);
        fadeTo(s.inst[to], to, 0);
        show(s.inst[to], to, true);
        fadeTo(s.inst[from], from, -1);
        s.fade = { t: 0, inSet: to, out: s.inst[from], outSet: from };
      } else {
        // The same set: its ghost takes the old level out while the stem's own
        // instance brings the new one in.
        const g = s.ghost[to];
        shape(g, to, s.v, s.level);
        fadeTo(g, to, -1);
        show(g, to, true);
        shape(s.inst[to], to, s.v, want);
        fadeTo(s.inst[to], to, 0);
        s.fade = { t: 0, inSet: to, out: g, outSet: to };
      }
      s.shade = shade;
      s.level = want;
      if (s.fade) live.add(s);
    };
    let at = null;
    const update = (eye, dt = 0) => {
      if (!eye) return;
      if (live.size && dt > 0) {
        for (const s of live) {
          const f = s.fade;
          f.t += dt / fadeS;
          if (f.t >= 1) { settle(s); continue; }
          fadeTo(s.inst[f.inSet], f.inSet, f.t);
          fadeTo(f.out, f.outSet, f.t - 1);
        }
        stats.fading = live.size;
      }
      if (at && (at.x - eye.x) ** 2 + (at.z - eye.z) ** 2 < STEP_M * STEP_M) return;
      // A jump (the first look, a teleport, a Jump) is drawn as it stands, no dissolve.
      const smooth = fading && !!at && (at.x - eye.x) ** 2 + (at.z - eye.z) ** 2 < JUMP_M * JUMP_M;
      if (!smooth) settleAll();
      at = { x: eye.x, z: eye.z };
      let t = 0; let nn = 0; let nm = 0; let nf = 0; let nd = 0; let ns = 0; let nc = 0;
      for (const s of this.stems) {
        const dx = s.x - eye.x; const dz = s.z - eye.z;
        // `lodK` (T-2833): a stem the caller marks as background takes its levels and
        // its shadow as if it stood that many times further off.
        const d = Math.sqrt(dx * dx + dz * dz) * s.lodK;
        // T-2948: a stem keeps its finer set and level `hyst` past the ring's edge.
        const shade = d <= shadeM || (s.shade && d <= shadeM + hyst);
        // Too small to see from here (CULL_PER_M): hidden in both sets.
        if (d > s.h * cullPerM) {
          if (!s.culled) {
            if (s.fade) settle(s);
            for (const set of ['shade', 'far']) show(s.inst[set], set, false);
            s.culled = true;
          }
          nc++;
          continue;
        }
        if (s.culled) {
          show(s.inst.shade, 'shade', shade);
          show(s.inst.far, 'far', !shade);
          s.shade = shade;
          s.level = null;
          s.culled = false;
        }
        let level = levelAt(d);
        if (hyst && s.level && ORDER[level] > ORDER[s.level]) level = levelAt(Math.max(0, d - hyst));
        // The nearest level the set holds to the one wanted (see `sets`).
        const want = nearestLevel(sets[shade ? 'shade' : 'far'], level);
        if (shade !== s.shade || want !== s.level) move(s, shade, want, smooth);
        t += s.v.tris[want] * 1;
        if (want === 'near') nn++; else if (want === 'mid') nm++; else if (want === 'far') nf++; else nd++;
        if (shade) ns++;
      }
      stats.triangles = Math.round(t);
      stats.near = nn; stats.mid = nm; stats.far = nf; stats.shade = ns; stats.culled = nc; stats.distant = nd;
      stats.fading = live.size;
    };
    const dispose = () => {
      live.clear();
      for (const set of Object.values(batches)) for (const b of Object.values(set)) { group.remove(b); b.dispose(); }
    };
    return { group, stats, update, settle: settleAll, dispose, batches };
  }
}

const ORDER = { near: 0, mid: 1, far: 2, distant: 3 };
const WHOLE = new THREE.Vector4(1, 1, 1, 1);
const _fade = new THREE.Vector4();
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
  alphaCutoff = 0.5, problems = [], fade = false }) {
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
  if (fade) { patchFade(woodMat); patchFade(leafMat); }
  confidence?.patch(woodMat);
  confidence?.patch(leafMat);
  const leafDepth = new THREE.MeshDepthMaterial({ map: leafA, alphaTest: alphaCutoff, side: THREE.DoubleSide,
    depthPacking: THREE.RGBADepthPacking });
  const leafDistance = new THREE.MeshDistanceMaterial({ map: leafA, alphaTest: alphaCutoff, side: THREE.DoubleSide });
  const woodDepth = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  const woodDistance = new THREE.MeshDistanceMaterial();
  for (const mm of [leafDepth, leafDistance, woodDepth, woodDistance]) {
    patchWind(mm, uWind);
    if (fade) patchFade(mm);
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

/**
 * T-2948 — THE DISSOLVE. A fading wood (`TreeInstances` with `fadeS`) writes each
 * instance's fade into the alpha of its batch colour: 1 whole, 0..1 the share of a
 * level coming in, -1..0 (minus) the share of one going out. A fragment is kept by
 * one screen-space noise against that share, coming in below it and going out
 * above it, so the two levels of one stem cover the screen between them and never
 * both. The batch colour's alpha is taken off the surface colour, so the leaves'
 * alpha test sees only the leaf. Without a colour texture (a wood that does not
 * fade) every fragment is whole. The shadow materials take it too, so a crown's
 * shadow dissolves with the crown.
 */
function patchFade(material) {
  const prior = material.onBeforeCompile;
  const isDefaultKey = material.customProgramCacheKey === THREE.Material.prototype.customProgramCacheKey;
  const priorKey = isDefaultKey ? String(prior) : material.customProgramCacheKey();
  material.onBeforeCompile = (shader, r) => {
    prior.call(material, shader, r);
    shader.vertexShader = 'varying float vTreeFade;\n' + shader.vertexShader
      .replace('#include <color_vertex>', `#include <color_vertex>
#ifdef USE_BATCHING_COLOR
vColor.a = 1.0;
#endif`)
      .replace('#include <project_vertex>', `#include <project_vertex>
#ifdef USE_BATCHING_COLOR
vTreeFade = getBatchingColor( getIndirectIndex( gl_DrawID ) ).a;
#else
vTreeFade = 1.0;
#endif`);
    shader.fragmentShader = `varying float vTreeFade;
float chiTreeNoise(vec2 p) { return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715)))); }
` + shader.fragmentShader.replace('void main() {', `void main() {
if (vTreeFade < 1.0) {
  float chiN = chiTreeNoise(gl_FragCoord.xy);
  if (vTreeFade < 0.0 ? chiN < 1.0 + vTreeFade : chiN >= vTreeFade) discard;
}`);
  };
  material.customProgramCacheKey = () => `${priorKey}|tree-fade-t2948`;
}

export { archFor };

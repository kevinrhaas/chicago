/**
 * near-field.js — T-2698, the near deal's FIELD as textures: the five things the
 * near ring's deal asks of the ground at every slot, rasterised into one
 * world-anchored tile a vertex shader can sample instead of asking the CPU.
 *
 * WHY. T-2557 moves the near ring's grass into the vertex shader: each instance
 * finds its own slot from `gl_InstanceID` and the lattice hash (T-2697), and
 * then has to answer, with no CPU in the loop, the questions `flora.js` asks of
 * every near slot today — which community stands here (`finder`), is it water
 * (`water.isWater`), is it short turf (`zone.turf`, where the near ring plants
 * nothing), may anything root here (`station`'s floors and travelways, and the
 * verge a turf community's tall plants give way on), and how high is the ground
 * (`terrain.surfaceHeight`). This module is those answers as a raster.
 *
 * WHAT IS IN A TEXEL, and what is NOT. A texel holds the CPU's own answer at
 * its CENTRE, asked through the same closures the deal asks (`flora.js`'s
 * `nearField.at`), so nothing here re-derives a rule; the only thing the tile
 * changes is WHERE the question is asked — at the texel's centre rather than at
 * the slot. That is the whole of the disagreement `tools/measure_near_field.mjs`
 * quotes, slot by slot. The species-dependent halves of `station()` are not in
 * the tile and cannot be: the substrate test is the wet bit plus the species'
 * own record, the woody band is the height channel against the zone record's
 * `woody_stratum`, and the trodden verge is the TRODDEN bit against the
 * species' height and the zone's `turfCeiling` — all three a lookup the shader
 * makes per species, not per texel.
 *
 *   class texture (RG8UI, texelFetch, nearest):
 *     R  community: index into `flora.communities()` plus one; 0 = no zone
 *     G  flags: WET · TURF · BLOCKED · TRODDEN (see FIELD_FLAGS)
 *   height texture (R32F, texelFetch four times, bilinear between centres):
 *     R  terrain.surfaceHeight at the texel centre, metres
 *
 * WORLD-ANCHORED. The tile's origin is a multiple of its own re-centre step, so
 * a texel centre is a fixed point of the world and two walkers standing a metre
 * apart sample the same texel for the same slot. It is rebuilt only when the
 * camera's snapped origin moves — every `recentre` metres of walking, where the
 * near deal re-deals every 0.6 m (`TUNE.step.near`). The spec below keeps the
 * near ring's whole lattice (7.6 m at `full`) inside the tile from anywhere in
 * the re-centre cell: half the tile less half a step is 12 m.
 *
 * TOROIDAL (T-2707). The keeper below holds ONE tile and, on a re-centre,
 * re-rasterises only the strip the step exposes — a quarter of the tile for an
 * 8 m step along one axis, 7/16 on a diagonal — writing it where the strip that
 * fell off the far side stood. A texel's place in the arrays is its WORLD texel
 * index modulo `size`, so a tile is its origin plus that wrap (`fieldWrap`), and
 * `sampleField` and `FIELD_GLSL` add the wrap before they index. A tile built
 * whole by `buildField` has a wrap of zero, and reads exactly as it did.
 *
 * Nothing here imports three.js, for the reason `turf-tile.js` gives: the tool
 * builds and samples the tile from the same code the page uploads.
 */

/**
 * 0.125 m a texel over 32 m: 256 x 256, re-centred every 8 m.
 *
 * Read at every near slot of the 22 critic stations
 * (docs/measurements/t-2698-near-field.json): 1.17 % of slots on the phone and
 * 0.90 % on the desktop disagree with the CPU on some channel, height p95
 * under 0.6 mm. Halving the texel buys a quarter of a point; doubling it costs
 * half a point and doubles the community misses. About half of the phone's
 * misses were the worked bank at the wharf, whose bare patches were a per-point
 * hash; since T-2715 `working-bank.js` answers once per texel of this grid
 * (BANK_PATCH_M) and the tile holds it exactly, and a street track's edge is
 * asked at a texel's corners (flora.js `nearField.atTexel`): 0.27 % of phone
 * slots and 0.26 % of desktop slots now disagree, and no slot the CPU blocks
 * is unblocked in the tile.
 *
 * THE BUILD IS THE COST: about 0.4 s a tile on the runner, ~50 ms per metre
 * walked against the near re-deal's 2-9 ms. It cannot be built on the main
 * thread as it is — it wants the job pool and a strip at a time, which is what
 * `fieldKeeper` does (T-2707).
 */
export const FIELD_SPEC = Object.freeze({ texel: 0.125, size: 256, recentre: 8 });

/** The flag bits of the class texture's G channel. */
export const FIELD_FLAGS = Object.freeze({
  /** `water.isWater` — which half of the community the slot may pick from. */
  WET: 1,
  /** `zone.turf` — the near ring plants nothing on short turf (T-2122). */
  TURF: 2,
  /** No rooted plant at all: a dated travelway (`growthBlocked`) or a floor
   *  whose polygon holds the point (the plank walks and the decks, T-0085). */
  BLOCKED: 4,
  /** A plant taller than its turf community's `turfCeiling` is cropped here:
   *  the worked roadway and the verge, less the kept patches (T-2094). */
  TRODDEN: 8,
});

/** Where the tile covering a camera at (`camE`, `camN`) starts: snapped to the
 *  re-centre step, so the origin moves only when the walker crosses a step. */
export function fieldOrigin(camE, camN, spec = FIELD_SPEC) {
  const span = spec.texel * spec.size;
  const snap = (v) => Math.round(v / spec.recentre) * spec.recentre - span / 2;
  return { e0: snap(camE), n0: snap(camN) };
}

/**
 * Build the tile at an origin. `at(e, n, out)` is the CPU's answer at one point
 * — `out[0]` community (0 = none), `out[1]` flags, `out[2]` ground height — and
 * is asked once per texel centre, row by row northward. `ms` is the wall time
 * the build took, which is the number the ticket asks to be set against today's
 * near re-deal.
 */
export function buildField(at, e0, n0, spec = FIELD_SPEC) {
  const { texel, size } = spec;
  const cls = new Uint8Array(size * size * 2);
  const height = new Float32Array(size * size);
  const out = [0, 0, 0];
  const t0 = performance.now();
  for (let j = 0; j < size; j++) {
    const n = n0 + (j + 0.5) * texel;
    for (let i = 0; i < size; i++) {
      at(e0 + (i + 0.5) * texel, n, out);
      const k = j * size + i;
      cls[2 * k] = out[0];
      cls[2 * k + 1] = out[1];
      height[k] = out[2];
    }
  }
  return { e0, n0, texel, size, cls, height, ms: performance.now() - t0 };
}

/**
 * The CPU mirror of `FIELD_GLSL`, line for line: the texel a slot falls in for
 * the class, and the bilinear blend of the four texel centres around it for the
 * height, clamped at the tile's edge. `out` is [community, flags, height], and
 * null comes back for a point outside the tile.
 */
export function sampleField(tile, e, n, out = [0, 0, 0]) {
  const { e0, n0, texel, size, cls, height } = tile;
  // T-2707: where a tile's local texel (0, 0) stands in its arrays.
  const wi = tile.wi ?? 0, wj = tile.wj ?? 0;
  const fx = (e - e0) / texel;
  const fy = (n - n0) / texel;
  const i = Math.floor(fx);
  const j = Math.floor(fy);
  if (i < 0 || j < 0 || i >= size || j >= size) return null;
  const at = (a, b) => ((b + wj) % size) * size + (a + wi) % size;
  const k = at(i, j);
  out[0] = cls[2 * k];
  out[1] = cls[2 * k + 1];
  const gx = fx - 0.5, gy = fy - 0.5;
  const i0 = Math.min(Math.max(Math.floor(gx), 0), size - 1);
  const j0 = Math.min(Math.max(Math.floor(gy), 0), size - 1);
  const i1 = Math.min(i0 + 1, size - 1);
  const j1 = Math.min(j0 + 1, size - 1);
  const tx = Math.min(Math.max(gx - Math.floor(gx), 0), 1);
  const ty = Math.min(Math.max(gy - Math.floor(gy), 0), 1);
  const h0 = height[at(i0, j0)] * (1 - tx) + height[at(i1, j0)] * tx;
  const h1 = height[at(i0, j1)] * (1 - tx) + height[at(i1, j1)] * tx;
  out[2] = h0 * (1 - ty) + h1 * ty;
  return out;
}

/**
 * The shader's half (GLSL ES 3.00). `en` is a point in the town's (east, north)
 * metres — world x and -z. The uniforms are the tile's origin, its texel in
 * metres and its size in texels, and `uFieldWrap` where its local texel (0, 0)
 * stands in the textures (T-2707: zero for a tile built whole, `fieldWrap` for
 * a kept one); `uFieldClass` is the RG8UI texture and `uFieldHeight` the R32F
 * one, both uploaded with `NearestFilter`. The near
 * grass material (T-2699) includes this chunk; `measure_near_field.mjs` reads
 * it back through the GPU against `sampleField` and the CPU's own answers.
 */
export const FIELD_GLSL = /* glsl */ `
uniform highp usampler2D uFieldClass;
uniform highp sampler2D uFieldHeight;
uniform vec2 uFieldOrigin;
uniform float uFieldTexel;
uniform int uFieldSize;
uniform ivec2 uFieldWrap;

ivec2 fieldWrapped(ivec2 t) { return (t + uFieldWrap) % uFieldSize; }

uvec2 fieldClass(vec2 en) {
  ivec2 t = ivec2(floor((en - uFieldOrigin) / uFieldTexel));
  t = clamp(t, ivec2(0), ivec2(uFieldSize - 1));
  return texelFetch(uFieldClass, fieldWrapped(t), 0).rg;
}

float fieldHeight(vec2 en) {
  vec2 g = (en - uFieldOrigin) / uFieldTexel - 0.5;
  vec2 f = clamp(g - floor(g), 0.0, 1.0);
  ivec2 a = clamp(ivec2(floor(g)), ivec2(0), ivec2(uFieldSize - 1));
  ivec2 b = min(a + 1, ivec2(uFieldSize - 1));
  float h00 = texelFetch(uFieldHeight, fieldWrapped(a), 0).r;
  float h10 = texelFetch(uFieldHeight, fieldWrapped(ivec2(b.x, a.y)), 0).r;
  float h01 = texelFetch(uFieldHeight, fieldWrapped(ivec2(a.x, b.y)), 0).r;
  float h11 = texelFetch(uFieldHeight, fieldWrapped(b), 0).r;
  return mix(mix(h00, h10, f.x), mix(h01, h11, f.x), f.y);
}
`;

/** T-2707. A texel the pool did not answer (off the measured grid, or no
 *  ground held there): the page asks `at` for it, so a missing answer costs
 *  time and never a different texel. */
export const FIELD_UNASKED = 255;

/** Where a tile at origin (`e0`, `n0`) keeps its local texel (0, 0): its world
 *  texel index modulo `size`, so every tile over a point keeps it in one place. */
export function fieldWrap(e0, n0, spec = FIELD_SPEC) {
  const m = (v) => ((Math.round(v / spec.texel) % spec.size) + spec.size) % spec.size;
  return { wi: m(e0), wj: m(n0) };
}

/**
 * The texels a tile at (`e0`, `n0`) has that `prev` does not, as rectangles in
 * the new tile's local texels: the columns the step east or west exposed, then
 * the rows north or south of them less those columns. The whole tile when
 * there is no `prev` or the step is a tile or more.
 */
export function exposedRects(prev, e0, n0, spec = FIELD_SPEC) {
  const { texel, size } = spec;
  const whole = [{ i0: 0, j0: 0, w: size, h: size }];
  if (!prev || prev.texel !== texel || prev.size !== size) return whole;
  const di = Math.round((e0 - prev.e0) / texel);
  const dj = Math.round((n0 - prev.n0) / texel);
  if (Math.abs(di) >= size || Math.abs(dj) >= size) return whole;
  const rects = [];
  const cw = Math.abs(di);
  if (cw) rects.push({ i0: di > 0 ? size - cw : 0, j0: 0, w: cw, h: size });
  if (dj) rects.push({ i0: di > 0 ? 0 : cw, j0: dj > 0 ? size - dj : 0, w: size - cw, h: Math.abs(dj) });
  return rects;
}

/** A tile-local rectangle as the rectangles of the arrays it lands in once
 *  wrapped (one to four), for an upload that sends only what changed. */
export function storageRects(r, wi, wj, size) {
  const cut = (a0, len) => {
    const s = a0 % size;
    return s + len <= size ? [[s, len]] : [[s, size - s], [0, s + len - size]];
  };
  const out = [];
  for (const [y, h] of cut((r.j0 + wj) % size, r.h)) {
    for (const [x, w] of cut((r.i0 + wi) % size, r.w)) out.push({ x, y, w, h });
  }
  return out;
}

/**
 * T-2707 — THE TILE KEPT AROUND A WALKER, a strip at a time.
 *
 * `ask(rect, e0, n0, texel)` starts the answers for one tile-local rectangle of
 * the tile at (e0, n0) and resolves with whatever it got (the pool's reply, or
 * null); `finish(got, rect, e0, n0, texel, cls, height)` then fills the rect's
 * own arrays — `cls` two bytes and `height` one float a texel, row by row
 * northward — on the main thread, from `got` and from whatever only the main
 * thread can answer. A texel's centre is always `e0 + (i0 + i + 0.5) * texel`
 * from the TILE's origin, as `buildField` places it, so a kept tile and a built
 * one ask the same points.
 *
 * `update(camE, camN)` is cheap when the origin has not moved. When it has, the
 * rects the step exposed are asked, and the tile moves to its new origin only
 * when every one has come home and been written over the strip that fell off:
 * until then `tile` is the old one, which still covers the near lattice for the
 * 4 m past the re-centre line (half the tile less half a step, against 7.6 m of
 * lattice). One re-centre is in flight at a time; a step taken meanwhile is
 * queued, and only the latest one is kept.
 *
 * `stats.mainMs` is the main thread's share — `update`, the asks being sent,
 * and the finishes and the writes — and nothing the pool spent; `written` is
 * where the last re-centre wrote, in the arrays' own texels (`storageRects`).
 *
 * T-2969 — A WHOLE TILE LANDS A BAND AT A TIME. The first tile, and the one
 * after a tier change or a jump of a tile or more, is every texel at once, and
 * its finish and write were one main-thread task: on the phone profile the
 * kept tiles' whole landings read as single long tasks, the carry tile's
 * 85-101 ms. So a landing of the whole tile is finished and written
 * `LAND_BAND_ROWS` rows at a time into a SECOND pair of arrays, handing the
 * thread back (`defer`) whenever a slice has run `sliceMs`, and the tile moves
 * to it only when the last band is in: until then `tile` is the old one,
 * untouched, exactly as a strip in flight leaves it. Every band is handed to
 * `finish` as a rect of its own with its rows of `got`, so a band is the same
 * texels a whole finish would have written (`check_near_field_keeper.mjs`
 * holds it byte for byte). A strip is still landed in one task, in place: it
 * is a quarter of the tile or less, and writing it over the strip that fell
 * off is what keeps it cheap. `sliceMs` (else `LAND.sliceMs`) = Infinity lands
 * the whole tile in one slice, as before — the tool's before. `stats.slices` and `stats.sliceMaxMs`
 * count the landings' slices and the longest one (strips included).
 */
export const LAND_BAND_ROWS = 16;
/** The page's budget for one slice of a whole landing, read at every slice of
 *  a keeper not given its own; `tools/measure_tile_landing.mjs` sets it to
 *  Infinity in the page for its before. */
export const LAND = { sliceMs: 6 };

/** One band of rows of a pool reply: every per-texel array cut to the band's
 *  rows (`got` is row by row northward, `w` texels a row). */
function gotRows(got, w, h, j, hb) {
  if (!got) return got;
  const out = {};
  for (const key of Object.keys(got)) {
    const v = got[key];
    if (!ArrayBuffer.isView(v) || v.length % (w * h)) { out[key] = v; continue; }
    const per = (v.length / (w * h)) * w;
    out[key] = v.subarray(j * per, (j + hb) * per);
  }
  return out;
}

export function fieldKeeper({ ask, finish, spec = FIELD_SPEC, now = () => performance.now(),
  defer = (f) => setTimeout(f, 0), sliceMs }) {
  const { texel, size } = spec;
  let cls = new Uint8Array(size * size * 2);
  let height = new Float32Array(size * size);
  let tile = null;
  let target = null;
  let want = null;
  let pending = null;
  let waiters = [];
  // T-2716: bumped by `adopt`, so a re-centre started before it lands as nothing.
  let generation = 0;
  const stats = { mainMs: 0, finishMs: 0, recentres: 0, texels: 0, whole: 0, lastMs: 0, adopted: 0,
    slices: 0, sliceMaxMs: 0 };
  const keeper = { stats, spec, written: [], sliceMs,
    get tile() { return tile; },
    update(camE, camN) {
      const t0 = now();
      const o = fieldOrigin(camE, camN, spec);
      const at = target ?? tile;
      if (!at || at.e0 !== o.e0 || at.n0 !== o.n0) {
        want = o;
        if (!pending) start();
      } else want = null;
      stats.mainMs += now() - t0;
      return tile;
    },
    /**
     * T-2716. Take a tile built whole elsewhere (`buildField`, wrap zero) as the
     * kept one, in this keeper's own wrap, so the next step is a strip again. A
     * re-centre in flight is dropped when it lands: it was asked against the
     * tile this replaces.
     */
    adopt(built) {
      const t0 = now();
      generation++;
      const { wi, wj } = fieldWrap(built.e0, built.n0, spec);
      for (let j = 0; j < size; j++) {
        const row = ((j + wj) % size) * size;
        for (let i = 0; i < size; i++) {
          const k = row + (i + wi) % size;
          const q = j * size + i;
          cls[2 * k] = built.cls[2 * q];
          cls[2 * k + 1] = built.cls[2 * q + 1];
          height[k] = built.height[q];
        }
      }
      tile = { e0: built.e0, n0: built.n0, wi, wj, texel, size, cls, height };
      keeper.written = [{ x: 0, y: 0, w: size, h: size }];
      target = null;
      want = null;
      stats.adopted++;
      stats.mainMs += now() - t0;
      return tile;
    },
    /** Resolves when nothing is in flight (the tool's walk waits on it). */
    settled() {
      return pending ? new Promise((r) => waiters.push(r)) : Promise.resolve(tile);
    },
  };
  function start() {
    const o = want;
    want = null;
    target = o;
    const rects = exposedRects(tile, o.e0, o.n0, spec);
    const asked = rects.map((r) => Promise.resolve(ask(r, o.e0, o.n0, texel)).catch(() => null));
    const g = generation;
    pending = Promise.all(asked).then((gots) => (rects.length === 1 && rects[0].w * rects[0].h === size * size
      ? landWhole(o, rects[0], gots[0], g) : land(o, rects, gots, g)));
  }
  function stale(o) {
    // Asked against a tile `adopt` has since replaced: its strips are not
    // this tile's, so nothing is written.
    pending = null;
    if (target === o) target = null;
    if (want && tile && (want.e0 !== tile.e0 || want.n0 !== tile.n0)) start();
    else want = null;
    if (!pending) {
      const w = waiters;
      waiters = [];
      for (const r of w) r(tile);
    }
  }
  function slice(ms) {
    stats.slices++;
    if (ms > stats.sliceMaxMs) stats.sliceMaxMs = ms;
    stats.mainMs += ms;
  }
  /** T-2969: the whole tile, a band of rows at a time, into new arrays. */
  function landWhole(o, rect, got, g) {
    const { wi, wj } = fieldWrap(o.e0, o.n0, spec);
    const nc = new Uint8Array(size * size * 2);
    const nh = new Float32Array(size * size);
    const rc = new Uint8Array(size * LAND_BAND_ROWS * 2);
    const rh = new Float32Array(size * LAND_BAND_ROWS);
    let j = 0;
    let total = 0;
    return new Promise((resolve) => {
      const run = () => {
        if (g !== generation) { stale(o); resolve(); return; }
        const s0 = now();
        do {
          const hb = Math.min(LAND_BAND_ROWS, size - j);
          const bc = hb === LAND_BAND_ROWS ? rc : rc.subarray(0, size * hb * 2);
          const bh = hb === LAND_BAND_ROWS ? rh : rh.subarray(0, size * hb);
          const f0 = now();
          finish(gotRows(got, size, size, j, hb), { i0: 0, j0: j, w: size, h: hb }, o.e0, o.n0, texel, bc, bh);
          stats.finishMs += now() - f0;
          for (let b = 0; b < hb; b++) {
            const row = ((j + b + wj) % size) * size;
            for (let i = 0; i < size; i++) {
              const k = row + (i + wi) % size;
              const q = b * size + i;
              nc[2 * k] = bc[2 * q];
              nc[2 * k + 1] = bc[2 * q + 1];
              nh[k] = bh[q];
            }
          }
          j += hb;
        } while (j < size && now() - s0 < (keeper.sliceMs ?? LAND.sliceMs));
        if (j < size) {
          const ms = now() - s0;
          slice(ms);
          total += ms;
          defer(run);
          return;
        }
        cls = nc;
        height = nh;
        tile = { e0: o.e0, n0: o.n0, wi, wj, texel, size, cls, height };
        keeper.written = storageRects(rect, wi, wj, size);
        stats.texels += size * size;
        stats.whole++;
        landed(o);
        const ms = now() - s0;
        slice(ms);
        stats.lastMs = total + ms;
        resolve();
      };
      run();
    });
  }
  function landed(o) {
    stats.recentres++;
    target = null;
    pending = null;
    if (want && (want.e0 !== o.e0 || want.n0 !== o.n0)) start();
    else want = null;
    if (!pending) {
      const w = waiters;
      waiters = [];
      for (const r of w) r(tile);
    }
  }
  function land(o, rects, gots, g = generation) {
    if (g !== generation) { stale(o); return; }
    const t0 = now();
    const { wi, wj } = fieldWrap(o.e0, o.n0, spec);
    const written = [];
    let texels = 0;
    for (let r = 0; r < rects.length; r++) {
      const { i0, j0, w, h } = rects[r];
      const rc = new Uint8Array(w * h * 2);
      const rh = new Float32Array(w * h);
      const f0 = now();
      finish(gots[r], rects[r], o.e0, o.n0, texel, rc, rh);
      stats.finishMs += now() - f0;
      for (let j = 0; j < h; j++) {
        const row = ((j0 + j + wj) % size) * size;
        for (let i = 0; i < w; i++) {
          const k = row + (i0 + i + wi) % size;
          const q = j * w + i;
          cls[2 * k] = rc[2 * q];
          cls[2 * k + 1] = rc[2 * q + 1];
          height[k] = rh[q];
        }
      }
      texels += w * h;
      written.push(...storageRects(rects[r], wi, wj, size));
    }
    tile = { e0: o.e0, n0: o.n0, wi, wj, texel, size, cls, height };
    keeper.written = written;
    stats.texels += texels;
    if (texels === size * size) stats.whole++;
    landed(o);
    stats.lastMs = now() - t0;
    slice(stats.lastMs);
  }
  return keeper;
}

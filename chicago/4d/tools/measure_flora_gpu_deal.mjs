/**
 * T-2706 — THE NEAR DEAL IN A SHADER, READ BACK AGAINST FLORA.JS AT EVERY NEAR SLOT.
 *
 *   node tools/measure_flora_gpu_deal.mjs [--source] [--viewport mobile|desktop]
 *                                         [--stations a,b] [--write] [--self-test]
 *
 * THE QUESTION. T-2557 deals the near ring's grass in the vertex shader. T-2697
 * put the lattice walk there (`flora-gpu-lattice.js`) and T-2698 the ground's
 * answers (`near-field.js`'s tile); `flora-gpu-deal.js` is the rule between
 * them — community, turf, the matrix share and the weight walk, the floors, the
 * trodden verge, water substrates, the woody band, the walker's clearance, and
 * placeGraminoid's height, spread, arch, yaw and colour. This tool says whether
 * the shader's deal IS flora.js's, slot for slot, and what it changes where not.
 *
 * WHAT IT DOES, per station and viewport (the detail level each boots into, so
 * the near lattice is the one that viewport deals):
 *
 *   1. flora.js's own deal at every slot of the near lattice, no view cone
 *      (`flora.nearField.deal`, which calls `dealNearSlot` — the function the
 *      draw calls — with the census left alone): what each slot came to, its
 *      species row, and the instance it would push.
 *   2. The field tile at the station (`nearField.build`), the deal table
 *      (`nearField.table`) and the lattice's uniforms (`latticeUniforms`) put
 *      on the GPU, and one point per instance id drawn through LATTICE_GLSL,
 *      FIELD_GLSL and DEAL_GLSL into a float target, four passes of four
 *      numbers, read back.
 *   3. The two held together. The slots the ring keeps must be the same, in the
 *      same order, within a millimetre. A slot whose OUTCOME, species or
 *      instance differs is put in one of three bins:
 *        field   — the tile answers differently from the CPU at that slot
 *                  (community or a flag): T-2698's disagreement, inherited;
 *        float32 — the tile agrees, and a double and a float32 put the slot on
 *                  either side of one of the deal's thresholds (stated below);
 *        rule    — anything else. That is the shader disagreeing with
 *                  flora.js, and it FAILS the run.
 *      Attributes are held to: ground 1 mm (against the tile's own height,
 *      the mirror — the height error against the CPU is quoted beside it),
 *      height, spread and arch 1 mm, yaw 1e-4 rad, colour 2e-3, confidence
 *      exact.
 *   4. The placement statistics the parent ticket asks for, CPU against GPU
 *      over the same slots: plants per m², each species' share (with the
 *      CPU's sampling error), and exclusion hits — a GPU plant where the CPU
 *      says BLOCKED (a floor or a travelway).
 *
 * THE THRESHOLDS a float32 may honestly round the other way at: `u` within
 * 1e-6 of the matrix share; the weight walk's target within 1e-6 of a
 * cumulative weight; the slot's distance within 1e-5 m of the walker's
 * clearance; the woody ramp within 1e-3 of its hash, or `e * 4` / `n * 4`
 * within 1e-3 of a half; and (colour only) the thatch draw within 1e-4 of its
 * chance.
 *
 * `--self-test` draws one station through a shader with the tint's two draws
 * swapped and must find rule disagreements, so a green run is a reading and not
 * a tolerance wide enough to pass anything.
 *
 * `--write` keeps the reading at docs/measurements/t-2706-flora-gpu-deal.json
 * (one `--viewport` at a time replaces only its own entry there). It renders,
 * so it needs Playwright and is not part of `tools/check.sh`.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { LATTICE_GLSL, latticeUniforms } from '../renderers/web/js/flora-gpu-lattice.js';
import { DEAL_GLSL, DEAL_STRIDE, NEAR_DEAL } from '../renderers/web/js/flora-gpu-deal.js';

async function loadPlaywright() {
  let ns;
  try {
    ns = await import('playwright');
  } catch {
    const root = (process.env.NODE_PATH
      || execSync('npm root -g', { encoding: 'utf8' })).trim().split(path.delimiter)[0];
    ns = await import(path.join(root, 'playwright', 'index.js'));
  }
  return ns.chromium ? ns : ns.default;
}
const { chromium } = await loadPlaywright();

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');
const argv = process.argv.slice(2);
const flag = (name) => { const i = argv.indexOf(name); return i < 0 ? null : argv[i + 1]; };
const wantSource = argv.includes('--source');
const wantWrite = argv.includes('--write');
const SELF_TEST = argv.includes('--self-test');
const ONLY_VIEW = flag('--viewport') || '';
const PICK = (flag('--stations') || '').split(',').filter(Boolean);
const ROOT = wantSource ? APP : path.resolve(APP, '../../site/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.DEAL_PORT || 4199);
const YEAR = process.env.DEAL_YEAR || '1835';
const OUT = path.join(APP, 'docs/measurements/t-2706-flora-gpu-deal.json');

/** tools/critic_shots.mjs SWEEP_STATIONS, the four that are poses (as
 *  measure_near_field.mjs copies them: that module shoots on import). */
const POSES = [
  { id: 'prairie_south', local_e: 120, local_n: -330, yaw_deg: 90 },
  { id: 'prairie_west', local_e: -250, local_n: -150, yaw_deg: 90 },
  { id: 'public_square', local_e: 550, local_n: -370, yaw_deg: 292 },
  { id: 'river_bank', local_e: 180, local_n: 0, yaw_deg: 0 },
];
const scene = JSON.parse(fs.readFileSync(path.join(APP, 'data/scenes', `${YEAR}.json`), 'utf8'));
let STATIONS = [
  ...scene.anchors.map((a) => ({ id: a.id, local_e: a.local_e, local_n: a.local_n })),
  ...POSES,
].filter((s) => !PICK.length || PICK.includes(s.id));

const VIEWPORTS = [
  { id: 'mobile', width: 390, height: 780, touch: true, scale: 2 },
  { id: 'desktop', width: 1280, height: 800, touch: false, scale: 1 },
];

/** The broken shader the self-test must refuse: the tint's two draws swapped. */
const BROKEN = DEAL_GLSL.replace('float tu = flDraw(s);\n  float tv = flDraw(s);',
  'float tv = flDraw(s);\n  float tu = flDraw(s);');
if (BROKEN === DEAL_GLSL) throw new Error('measure_flora_gpu_deal: the self-test break no longer applies');
if (SELF_TEST) STATIONS = STATIONS.filter((s) => s.id === 'sixteenth_prairie');

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown',
  '.ktx2': 'image/ktx2', '.webp': 'image/webp',
};
const server = http.createServer((req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (url.endsWith('/')) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    res.writeHead(404); res.end('not found'); return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] ?? 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(PORT, r));
const base = `http://127.0.0.1:${PORT}`;

/** Runs in the page: one station's two deals, CPU and GPU, side by side. */
async function pageRead({ st, uni, lattice, deal, stride }) {
  const api = window.__chicago4d;
  const nf = api.flora.nearField;
  const THREE = await import('three');
  const e = st.local_e, n = st.local_n;
  const table = nf.table();
  const t0 = performance.now();
  const cpu = nf.deal(e, n, table.rowOf);
  const cpuMs = performance.now() - t0;
  const tile = nf.build(e, n);

  const r = api.renderer;
  const { size } = tile;
  const cls = new THREE.DataTexture(tile.cls, size, size, THREE.RGIntegerFormat, THREE.UnsignedByteType);
  cls.internalFormat = 'RG8UI';
  const hgt = new THREE.DataTexture(tile.height, size, size, THREE.RedFormat, THREE.FloatType);
  hgt.internalFormat = 'R32F';
  const tab = new THREE.DataTexture(table.data, table.width, table.height, THREE.RGBAFormat,
    THREE.FloatType);
  tab.internalFormat = 'RGBA32F';
  for (const t of [cls, hgt, tab]) {
    t.minFilter = t.magFilter = THREE.NearestFilter;
    t.generateMipmaps = false; t.flipY = false; t.needsUpdate = true;
  }
  const N = uni.count;
  const W = 256, H = Math.max(1, Math.ceil(N / W));
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N * 3), 3));
  const mat = new THREE.RawShaderMaterial({
    glslVersion: THREE.GLSL3,
    uniforms: {
      uFieldClass: { value: cls }, uFieldHeight: { value: hgt },
      uFieldOrigin: { value: new THREE.Vector2(tile.e0, tile.n0) },
      uFieldTexel: { value: tile.texel }, uFieldSize: { value: size },
      uLatGrid: { value: [...uni.grid] },
      uLatDeal: { value: [...uni.deal] },
      uLatMode: { value: uni.mode },
      uLatRing: { value: new THREE.Vector4(...uni.ring) },
      uLatCell: { value: new THREE.Vector2(...uni.cell) },
      uDealTable: { value: tab },
      uDealLayout: { value: [table.width, table.itemBase] },
      uDealCam: { value: new THREE.Vector2(e, n) },
      uDealEye: { value: new THREE.Vector3(nf.waterY, 0, 0) },
      uTarget: { value: new THREE.Vector2(W, H) },
      uPass: { value: 0 },
    },
    vertexShader: `precision highp float; precision highp int; precision highp usampler2D;
in vec3 position;
uniform vec2 uTarget;
uniform int uPass;
${lattice}
${nf.glsl}
${deal}
flat out vec4 vOut;
void main() {
  int id = gl_VertexID;
  vec2 rel; float u; uint rng; uint cellSeed;
  bool kept = flLatticeSlot(id, rel, u, rng, cellSeed);
  int code = 0, row = -1;
  float vig = 0.0;
  vec3 ground = vec3(0.0);
  vec4 fl = vec4(0.0), col = vec4(0.0);
  if (kept) code = flNearDeal(rel, length(rel), u, rng, row, vig, ground, fl, col);
  uint s = rng;
  for (int k = 0; k < 4; k++) s = flXorshift(s);
  float thatch = flDraw(s);
  if (uPass == 0) vOut = vec4(float(code), float(row), ground.y, fl.x);
  else if (uPass == 1) vOut = vec4(fl.y, fl.z, fl.w, col.w);
  else if (uPass == 2) vOut = vec4(col.rgb, u);
  else vOut = vec4(rel, vig, thatch);
  float x = float(id % int(uTarget.x)), y = float(id / int(uTarget.x));
  gl_Position = vec4((x + 0.5) / uTarget.x * 2.0 - 1.0, (y + 0.5) / uTarget.y * 2.0 - 1.0, 0.0, 1.0);
  gl_PointSize = 1.0;
}`,
    fragmentShader: `precision highp float; precision highp int;
flat in vec4 vOut; out vec4 o;
void main() { o = vOut; }`,
  });
  const pts = new THREE.Points(geo, mat);
  pts.frustumCulled = false;
  const sc = new THREE.Scene();
  sc.add(pts);
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.FloatType, format: THREE.RGBAFormat,
    minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, depthBuffer: false });
  const gl = r.getContext();
  while (gl.getError() !== gl.NO_ERROR) { /* the page's own frames' errors are not this pass's */ }
  const prev = r.getRenderTarget();
  const prevClear = r.getClearColor(new THREE.Color()).clone();
  const prevAlpha = r.getClearAlpha();
  const passes = [];
  const g0 = performance.now();
  for (let p = 0; p < 4; p++) {
    mat.uniforms.uPass.value = p;
    const buf = new Float32Array(W * H * 4);
    r.setRenderTarget(rt);
    r.setClearColor(0x000000, 0);
    r.clear();
    r.render(sc, new THREE.Camera());
    r.readRenderTargetPixels(rt, 0, 0, W, H, buf);
    passes.push(buf);
  }
  r.setRenderTarget(prev);
  r.setClearColor(prevClear, prevAlpha);
  const gpuMs = performance.now() - g0;
  const glError = gl.getError();

  // The GPU's kept slots, in instance order: the CPU's emits, in scatter's order.
  const gpu = [];
  for (let id = 0; id < N; id++) {
    const P = (k, c) => passes[k][4 * id + c];
    if (P(0, 0) === 0) continue;
    gpu.push({ code: P(0, 0), row: P(0, 1), y: P(0, 2), h: P(0, 3), spread: P(1, 0), arch: P(1, 1),
      yaw: P(1, 2), conf: P(1, 3), rgb: [P(2, 0), P(2, 1), P(2, 2)], u: P(2, 3),
      e: e + P(3, 0), n: n + P(3, 1), vig: P(3, 2), thatch: P(3, 3) });
  }
  const C = cpu.length / stride;
  const at = [0, 0, 0], mirror = [0, 0, 0];
  const F = nf.flags;
  const slots = [];
  for (let s = 0; s < C; s++) {
    const o = s * stride;
    nf.at(cpu[o], cpu[o + 1], at);
    const m = nf.sample(tile, cpu[o], cpu[o + 1], mirror);
    slots.push({
      e: cpu[o], n: cpu[o + 1], u: cpu[o + 2], code: cpu[o + 3], row: cpu[o + 4], y: cpu[o + 5],
      yaw: cpu[o + 6], h: cpu[o + 7], spread: cpu[o + 8], arch: cpu[o + 9],
      rgb: [cpu[o + 10], cpu[o + 11], cpu[o + 12]], conf: cpu[o + 13], thatch: cpu[o + 14],
      at: [...at], mirror: m ? [...m] : null,
    });
  }
  for (const d of [cls, hgt, tab, rt, geo, mat]) d.dispose();
  return {
    id: st.id, e, n, instances: N, cpuMs, gpuMs, glError, tileMs: tile.ms,
    flags: { ...F }, species: table.species,
    slots, gpu,
    // What the threshold bins need of the table: per community its subsets'
    // weights, per row its clump radius and woody binding (header and rows).
    table: { data: Array.from(table.data.subarray(0, (table.itemBase + table.rows * 5) * 4)),
      itemBase: table.itemBase, rows: table.rows },
  };
}

const T = (tab, i) => tab.data.slice(4 * i, 4 * i + 4);
function hash3(a, b, c) {
  let h = Math.imul(a, 0x27d4eb2d) ^ Math.imul(b, 0x165667b1) ^ Math.imul(c, 0x9e3779b1);
  h = Math.imul(h ^ (h >>> 15), 0x85ebca6b);
  h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
  return (h ^ (h >>> 16)) >>> 0;
}
function ramp(lo, hi, x) {
  const t = Math.min(1, Math.max(0, (x - lo) / (hi - lo)));
  return t * t * (3 - 2 * t);
}

/** Does a double and a float32 honestly straddle one of the deal's thresholds
 *  at this slot? `c` is the CPU's slot, `g` the GPU's. */
function atThreshold(c, g, tab) {
  const z = c.at[0] - 1;
  if (z < 0) return null;
  const [share] = T(tab, 4 * z);
  const z1 = T(tab, 4 * z + 1);
  const side = T(tab, 4 * z + ((c.at[1] & 1) ? 3 : 2));
  if (Math.abs(c.u - share) < 1e-6) return 'share';
  const target = (c.u / share) * side[2];
  let acc = 0;
  for (let i = 0; i < side[1]; i++) {
    acc += T(tab, side[0] + i)[0];
    if (Math.abs(target - acc) < 1e-6 * Math.max(1, side[2])) return 'weight';
  }
  for (const row of [c.row, g.row]) {
    if (!(row >= 0)) continue;
    const it = tab.itemBase + 5 * row;
    const clump = T(tab, it + 1)[3];
    const d = Math.hypot(c.e - c.camE, c.n - c.camN);
    if (Math.abs(d - (0.34 + clump)) < 1e-5) return 'walker';
    if (z1[2] > 0.5 && T(tab, it + 3)[3] > 0.5) {
      const y = c.mirror ? c.mirror[2] : c.at[2];
      const t = ramp(z1[0], z1[1], y);
      const hv = hash3(Math.round(c.e * 4), Math.round(c.n * 4), 0x5ad8a1) / 4294967296;
      const half = (v) => Math.abs((v * 4) - Math.floor(v * 4) - 0.5) < 1e-3;
      if (Math.abs(hv - t) < 1e-3 || Math.abs(t) < 1e-3 || Math.abs(t - 1) < 1e-3
        || half(c.e) || half(c.n)) return 'woody';
    }
  }
  return null;
}

const TOL = { groundM: 1e-3, sizeM: 1e-3, yaw: 1e-4, rgb: 2e-3 };

/** Hold one station's GPU deal to its CPU deal. */
function judge(r) {
  const tab = r.table;
  const bins = { field: 0, float32: 0, rule: 0 };
  const why = {};
  const rule = [];
  let posMax = 0, orderFaults = 0;
  const dGround = [], dCpuGround = [];
  const maxD = { h: 0, spread: 0, arch: 0, yaw: 0, rgb: 0 };
  const count = { cpuPlaced: 0, gpuPlaced: 0, cpuBlockedHits: 0, gpuBlockedHits: 0 };
  const shares = { cpu: {}, gpu: {} };
  const codes = { cpu: {}, gpu: {} };
  const kept = Math.min(r.slots.length, r.gpu.length);
  if (r.slots.length !== r.gpu.length) orderFaults += Math.abs(r.slots.length - r.gpu.length);
  for (let s = 0; s < kept; s++) {
    const c = r.slots[s];
    const g = r.gpu[s];
    c.camE = r.e; c.camN = r.n;
    const dp = Math.max(Math.abs(c.e - g.e), Math.abs(c.n - g.n));
    posMax = Math.max(posMax, dp);
    if (dp > 1e-3) orderFaults++;
    codes.cpu[c.code] = (codes.cpu[c.code] ?? 0) + 1;
    codes.gpu[g.code] = (codes.gpu[g.code] ?? 0) + 1;
    const blocked = (c.at[1] & r.flags.BLOCKED) !== 0;
    if (c.code === 6) {
      count.cpuPlaced++;
      shares.cpu[r.species[c.row]] = (shares.cpu[r.species[c.row]] ?? 0) + 1;
      if (blocked) count.cpuBlockedHits++;
    }
    if (g.code === 6) {
      count.gpuPlaced++;
      shares.gpu[r.species[g.row]] = (shares.gpu[r.species[g.row]] ?? 0) + 1;
      if (blocked) count.gpuBlockedHits++;
    }
    let same = c.code === g.code && (c.code < 4 || c.row === g.row);
    let colourOnly = false;
    if (same && c.code === 6) {
      const ref = c.mirror ? (c.at[1] & r.flags.WET ? c.y : c.mirror[2]) : c.y;
      dGround.push(Math.abs(g.y - ref));
      dCpuGround.push(Math.abs(g.y - c.y));
      const d = { h: Math.abs(g.h - c.h), spread: Math.abs(g.spread - c.spread),
        arch: Math.abs(g.arch - c.arch), yaw: Math.abs(g.yaw - c.yaw),
        rgb: Math.max(...g.rgb.map((v, k) => Math.abs(v - c.rgb[k]))) };
      const sizeBad = Math.abs(g.y - ref) > TOL.groundM || d.h > TOL.sizeM || d.spread > TOL.sizeM
        || d.arch > TOL.sizeM || d.yaw > TOL.yaw || g.conf !== Math.fround(c.conf);
      if (d.rgb > TOL.rgb && !sizeBad && Math.abs(c.thatch - 0.14 * (1 - g.vig)) < 1e-4) colourOnly = true;
      else for (const k in maxD) maxD[k] = Math.max(maxD[k], d[k]);
      if (sizeBad || (d.rgb > TOL.rgb && !colourOnly)) same = false;
    }
    if (same && !colourOnly) continue;
    const tileAgrees = c.mirror && c.mirror[0] === c.at[0] && c.mirror[1] === c.at[1];
    if (!tileAgrees) { bins.field++; continue; }
    const t = colourOnly ? 'thatch' : atThreshold(c, g, tab);
    if (t) { bins.float32++; why[t] = (why[t] ?? 0) + 1; continue; }
    bins.rule++;
    if (rule.length < 6) {
      rule.push({ e: +c.e.toFixed(4), n: +c.n.toFixed(4), u: c.u, cpu: { code: c.code, row: c.row,
        y: c.y, h: c.h, spread: c.spread, arch: c.arch, yaw: c.yaw, rgb: c.rgb, conf: c.conf },
      gpu: { code: g.code, row: g.row, y: g.y, h: g.h, spread: g.spread, arch: g.arch, yaw: g.yaw,
        rgb: g.rgb, conf: g.conf, u: g.u }, at: c.at, mirror: c.mirror });
    }
  }
  const q = (v, p) => { const a = [...v].sort((x, y) => x - y); return a[Math.floor((a.length - 1) * p)] ?? 0; };
  return { id: r.id, e: r.e, n: r.n, instances: r.instances, slots: r.slots.length,
    gpuKept: r.gpu.length, orderFaults, posMaxMm: posMax * 1000, ...count, codes, shares, bins, why,
    groundVsMirrorMm: { p95: q(dGround, 0.95) * 1000, max: q(dGround, 1) * 1000 },
    groundVsCpuMm: { p95: q(dCpuGround, 0.95) * 1000, max: q(dCpuGround, 1) * 1000 },
    maxDiff: maxD, cpuMs: r.cpuMs, gpuMs: r.gpuMs, tileMs: r.tileMs, glError: r.glError, rule };
}

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const report = { ticket: 'T-2706', year: YEAR, measured: new Date().toISOString(),
  source: wantSource ? 'working tree' : 'published mirror', tolerances: TOL, viewports: [] };
let failed = false;
for (const vp of VIEWPORTS) {
  if (ONLY_VIEW && vp.id !== ONLY_VIEW) continue;
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height },
    hasTouch: vp.touch, isMobile: false, deviceScaleFactor: vp.scale });
  const page = await ctx.newPage();
  page.setDefaultTimeout(180_000);
  const errors = [];
  page.on('pageerror', (x) => errors.push(String(x)));
  const b0 = Date.now();
  await page.goto(`${base}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 480000 });
  await page.evaluate(() => window.__chicago4d.setAnimationHold?.(true));
  const meta = await page.evaluate(() => ({ detail: window.__chicago4d.detail,
    walk: window.__chicago4d.flora.nearField.walk,
    ring: window.__chicago4d.flora.rings.layers.near.lattice }));
  console.log(`\n${vp.id} (${meta.detail}, booted in ${((Date.now() - b0) / 1000).toFixed(0)} s): `
    + `near lattice ${meta.ring.inner}-${meta.ring.outer} m, cell ${meta.walk.cell} m x ${meta.walk.perCell}`);
  const rows = [];
  for (const st of STATIONS) {
    const uni = latticeUniforms({ camE: st.local_e, camN: st.local_n, cell: meta.walk.cell,
      perCell: meta.walk.perCell, radius: meta.ring.outer, inner: meta.ring.inner,
      salt: meta.walk.salt, draw: meta.walk.draw });
    const raw = await page.evaluate(pageRead, { st, uni, lattice: LATTICE_GLSL,
      deal: SELF_TEST ? BROKEN : DEAL_GLSL, stride: DEAL_STRIDE });
    const j = judge(raw);
    rows.push(j);
    console.log(`  ${st.id.padEnd(26)} ${String(j.slots).padStart(5)} slots  placed cpu ${String(j.cpuPlaced).padStart(4)}`
      + ` gpu ${String(j.gpuPlaced).padStart(4)} | differ: field ${j.bins.field} float32 ${j.bins.float32}`
      + ` rule ${j.bins.rule} | pos ${j.posMaxMm.toFixed(3)} mm, ground ${j.groundVsMirrorMm.max.toFixed(3)} mm`
      + ` (cpu p95 ${j.groundVsCpuMm.p95.toFixed(2)} mm) h ${(j.maxDiff.h * 1000).toFixed(3)} mm`
      + ` rgb ${j.maxDiff.rgb.toExponential(1)} | blocked hits cpu ${j.cpuBlockedHits} gpu ${j.gpuBlockedHits}`
      + ` | cpu deal ${j.cpuMs.toFixed(1)} ms | codes cpu ${JSON.stringify(j.codes.cpu)} gpu ${JSON.stringify(j.codes.gpu)}`);
    if (j.rule.length && !SELF_TEST) console.log(`    RULE: ${JSON.stringify(j.rule.slice(0, 2))}`);
    if (j.orderFaults || j.glError) {
      console.log(`    READ-BACK FAULT: ${JSON.stringify({ orderFaults: j.orderFaults, glError: j.glError,
        slots: j.slots, gpuKept: j.gpuKept })}`);
      failed = true;
    }
    if (j.bins.rule && !SELF_TEST) failed = true;
  }
  const sum = (f) => rows.reduce((a, r) => a + f(r), 0);
  if (SELF_TEST) {
    const refused = sum((r) => r.bins.rule);
    console.log(refused ? `   self-test | refused, as it must be: the tint's two draws swapped — `
      + `${refused} rule disagreement(s)` : 'FAIL — the read-back did not refuse a shader with the tint draws swapped');
    if (!refused || errors.length) failed = true;
    await ctx.close();
    continue;
  }
  // Placement statistics over every slot of every station.
  const area = Math.PI * (meta.ring.outer ** 2 - meta.ring.inner ** 2) * rows.length;
  const tally = (side) => {
    const t = {};
    for (const r of rows) for (const [k, v] of Object.entries(r.shares[side])) t[k] = (t[k] ?? 0) + v;
    return t;
  };
  const cpuSp = tally('cpu'), gpuSp = tally('gpu');
  const cpuN = sum((r) => r.cpuPlaced), gpuN = sum((r) => r.gpuPlaced);
  const species = [...new Set([...Object.keys(cpuSp), ...Object.keys(gpuSp)])].sort();
  const shareRows = species.map((id) => {
    const pc = (cpuSp[id] ?? 0) / cpuN, pg = (gpuSp[id] ?? 0) / gpuN;
    const se = Math.sqrt(Math.max(pc * (1 - pc), 1 / cpuN) / cpuN);
    return { id, cpu: pc, gpu: pg, diff: pg - pc, se, sigmas: Math.abs(pg - pc) / se };
  });
  const bins = { field: sum((r) => r.bins.field), float32: sum((r) => r.bins.float32), rule: sum((r) => r.bins.rule) };
  const why = {};
  for (const r of rows) for (const [k, v] of Object.entries(r.why)) why[k] = (why[k] ?? 0) + v;
  const slotsAll = sum((r) => r.slots);
  const densitySe = Math.sqrt(cpuN) / area;
  const summary = {
    stations: rows.length, slots: slotsAll, bins, share: Object.fromEntries(Object.entries(bins)
      .map(([k, v]) => [k, v / slotsAll])), float32Why: why,
    density: { cpuPerM2: cpuN / area, gpuPerM2: gpuN / area, seCpuPerM2: densitySe,
      sigmas: Math.abs(gpuN - cpuN) / area / densitySe },
    speciesShare: { maxAbsDiff: Math.max(...shareRows.map((x) => Math.abs(x.diff))),
      maxSigmas: Math.max(...shareRows.map((x) => x.sigmas)),
      totalVariation: shareRows.reduce((a, x) => a + Math.abs(x.diff), 0) / 2, rows: shareRows },
    blockedHits: { cpu: sum((r) => r.cpuBlockedHits), gpu: sum((r) => r.gpuBlockedHits) },
    posMaxMm: Math.max(...rows.map((r) => r.posMaxMm)),
    groundVsMirrorMaxMm: Math.max(...rows.map((r) => r.groundVsMirrorMm.max)),
    groundVsCpuP95MmMax: Math.max(...rows.map((r) => r.groundVsCpuMm.p95)),
    maxDiff: Object.fromEntries(Object.keys(TOL).length ? ['h', 'spread', 'arch', 'yaw', 'rgb']
      .map((k) => [k, Math.max(...rows.map((r) => r.maxDiff[k]))]) : []),
  };
  console.log(`  ALL ${slotsAll} slots at ${rows.length} stations: differ field ${bins.field} `
    + `(${(summary.share.field * 100).toFixed(3)}%), float32 ${bins.float32} ${JSON.stringify(why)}, rule ${bins.rule}`);
  console.log(`    plants per m2: cpu ${summary.density.cpuPerM2.toFixed(4)} gpu ${summary.density.gpuPerM2.toFixed(4)} `
    + `(${summary.density.sigmas.toFixed(2)} sigma); species share max |diff| `
    + `${(summary.speciesShare.maxAbsDiff * 100).toFixed(3)} pts (${summary.speciesShare.maxSigmas.toFixed(2)} sigma), `
    + `total variation ${(summary.speciesShare.totalVariation * 100).toFixed(3)} pts; blocked hits cpu `
    + `${summary.blockedHits.cpu} gpu ${summary.blockedHits.gpu}`);
  console.log(`    instance: position <= ${summary.posMaxMm.toFixed(3)} mm, ground vs tile <= `
    + `${summary.groundVsMirrorMaxMm.toFixed(3)} mm (vs cpu p95 <= ${summary.groundVsCpuP95MmMax.toFixed(2)} mm), `
    + `h ${(summary.maxDiff.h * 1000).toFixed(4)} spread ${(summary.maxDiff.spread * 1000).toFixed(4)} `
    + `arch ${(summary.maxDiff.arch * 1000).toFixed(4)} mm, yaw ${summary.maxDiff.yaw.toExponential(1)}, `
    + `rgb ${summary.maxDiff.rgb.toExponential(1)}`);
  console.log(`  pageerrors: ${errors.length}${errors.length ? ` ${JSON.stringify(errors.slice(0, 3))}` : ''}`);
  if (errors.length) failed = true;
  report.viewports.push({ id: vp.id, detail: meta.detail, ring: meta.ring, walk: meta.walk, summary,
    stations: rows.map(({ shares, ...r }) => r), pageerrors: errors });
  await ctx.close();
}
await browser.close();
server.close();
if (wantWrite && !SELF_TEST) {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  if (fs.existsSync(OUT)) {
    const kept = JSON.parse(fs.readFileSync(OUT, 'utf8')).viewports ?? [];
    const fresh = new Set(report.viewports.map((v) => v.id));
    report.viewports = [...kept.filter((v) => !fresh.has(v.id)), ...report.viewports]
      .sort((a, b) => a.id.localeCompare(b.id));
  }
  fs.writeFileSync(OUT, `${JSON.stringify(report, (k, v) => (typeof v === 'number'
    ? Math.round(v * 1e6) / 1e6 : v), 1)}\n`);
  console.log(`\nwrote ${path.relative(APP, OUT)}`);
}
if (SELF_TEST && !failed) console.log('PASS — the read-back refuses a broken shader');
process.exit(failed ? 1 : 0);

/**
 * T-2698 — THE NEAR DEAL'S FIELD AS TEXTURES, READ BACK AT EVERY NEAR SLOT.
 *
 *   node tools/measure_near_field.mjs [--source] [--viewport mobile|desktop]
 *                                     [--stations a,b] [--texels 0.125,0.25]
 *                                     [--write]
 *
 * THE QUESTION. T-2557 deals the near ring's grass in the vertex shader. The
 * deal asks five things of the ground at every slot — community, water, short
 * turf, may anything root here, and the ground's height — and the shader can
 * only ask them of a texture. `renderers/web/js/near-field.js` rasterises the
 * CPU's own answers into a world-anchored tile; this tool says what the tile
 * gets WRONG, slot by slot, and what it costs to build.
 *
 * WHAT IT DOES, per station and viewport (the detail level each boots into, so
 * the near lattice is the one that viewport deals):
 *
 *   1. Every slot of the near lattice at the station, with no view cone
 *      (`flora.nearField.slots`): the cone only drops slots, so this is the
 *      superset every heading deals from.
 *   2. The CPU's answer at every slot (`flora.nearField.at`) — the deal's own
 *      closures — timed: that is the field-query share of a near re-deal, the
 *      part the tile replaces.
 *   3. The tile at each texel size in `--texels` (32 m square), its build
 *      timed, and its CPU mirror (`sampleField`) held to (2): per channel, the
 *      share of slots whose answer differs, and the height error in mm.
 *   4. At the spec texel, THE GPU READ-BACK: both textures uploaded as the page
 *      uploads them, one point per slot drawn through `FIELD_GLSL` into a float
 *      target and read back. It is held to the mirror (they must agree — the
 *      shader and the CPU index the same texel) and to the CPU answers (that is
 *      the disagreement the ticket asks quoted).
 *   5. Today's near re-deal at the station: the walker teleported a metre short
 *      and then onto the station, and the second `flora.update` — one near pass,
 *      the far shrubs' 4 m step not crossed — timed in one frame.
 *
 * THE STATIONS are the critic's: every anchor of the year's scene, plus the four
 * pose stations `tools/critic_shots.mjs` keeps (SWEEP_STATIONS there — copied,
 * not imported, because that module shoots on import).
 *
 * `--write` keeps the reading at docs/measurements/t-2698-near-field.json (one
 * `--viewport` at a time replaces only its own entry there). It
 * renders, so it needs Playwright and is not part of `tools/check.sh`.
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

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
const ONLY_VIEW = flag('--viewport') || '';
const PICK = (flag('--stations') || '').split(',').filter(Boolean);
const TEXELS = (flag('--texels') || '0.0625,0.125,0.25,0.5').split(',').map(Number);
const SPAN_M = 32;
const ROOT = wantSource ? APP : path.resolve(APP, '../../site/4d');
const ENTRY = wantSource ? '/renderers/web/index.html' : '/walk/';
const PORT = Number(process.env.FIELD_PORT || 4198);
const YEAR = process.env.FIELD_YEAR || '1835';
const OUT = path.join(APP, 'docs/measurements/t-2698-near-field.json');

/** tools/critic_shots.mjs SWEEP_STATIONS, the four that are poses. */
const POSES = [
  { id: 'prairie_south', local_e: 120, local_n: -330, yaw_deg: 90 },
  { id: 'prairie_west', local_e: -250, local_n: -150, yaw_deg: 90 },
  { id: 'public_square', local_e: 550, local_n: -370, yaw_deg: 292 },
  { id: 'river_bank', local_e: 180, local_n: 0, yaw_deg: 0 },
];
const scene = JSON.parse(fs.readFileSync(path.join(APP, 'data/scenes', `${YEAR}.json`), 'utf8'));
const STATIONS = [
  ...scene.anchors.map((a) => ({ id: a.id, local_e: a.local_e, local_n: a.local_n,
    yaw_deg: a.yaw_deg ?? 0 })),
  ...POSES,
].filter((s) => !PICK.length || PICK.includes(s.id));

const VIEWPORTS = [
  { id: 'mobile', width: 390, height: 780, touch: true, scale: 2 },
  { id: 'desktop', width: 1280, height: 800, touch: false, scale: 1 },
];

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

/** Runs in the page: one station, every reading above. */
async function pageRead({ st, texels, span }) {
  const api = window.__chicago4d;
  const nf = api.flora.nearField;
  const F = nf.flags;
  const BITS = Object.entries(F);
  const e = st.local_e, n = st.local_n;

  // 5 first, so the reading of the re-deal is not taken on a cache the tile
  // builds below have just warmed.
  // Five re-deals, a metre apart, and their median: one is at the mercy of a
  // collection or a worker's first reply.
  api.flora.settle?.();
  api.walker.teleport({ local_e: e - 1, local_n: n, yaw_deg: st.yaw_deg });
  api.flora.update(0, api.camera);
  const redeals = [];
  const rebuilt0 = api.flora.stats.rebuilds;
  for (let k = 0; k < 5; k++) {
    api.walker.teleport({ local_e: k % 2 ? e - 1 : e, local_n: n, yaw_deg: st.yaw_deg });
    const r0 = performance.now();
    api.flora.update(0, api.camera);
    redeals.push(performance.now() - r0);
  }
  api.walker.teleport({ local_e: e, local_n: n, yaw_deg: st.yaw_deg });
  api.flora.update(0, api.camera);
  const redealMs = redeals.sort((a, b) => a - b)[2];
  // Each of the five has to have been a re-deal, or the median is of no-ops.
  const redealt = api.flora.stats.rebuilds - rebuilt0;

  const slots = nf.slots(e, n);
  const N = slots.length / 2;
  const cpu = new Float64Array(N * 3);
  const o = [0, 0, 0];
  // Three passes and the median, so the first one's compile is not the reading.
  const queries = [];
  for (let k = 0; k < 3; k++) {
    const q0 = performance.now();
    for (let s = 0; s < N; s++) {
      nf.at(slots[2 * s], slots[2 * s + 1], o);
      cpu[3 * s] = o[0]; cpu[3 * s + 1] = o[1]; cpu[3 * s + 2] = o[2];
    }
    queries.push(performance.now() - q0);
  }
  const queryMs = queries.sort((a, b) => a - b)[1];

  /** Hold a reading (`got(s)` → [community, flags, height]) to the CPU's. */
  function compare(got) {
    const miss = { community: 0, any: 0 };
    for (const [k] of BITS) miss[k] = 0;
    const dh = [];
    for (let s = 0; s < N; s++) {
      const g = got(s);
      let bad = false;
      if (g[0] !== cpu[3 * s]) { miss.community++; bad = true; }
      for (const [k, b] of BITS) {
        if ((g[1] & b) !== (cpu[3 * s + 1] & b)) { miss[k]++; bad = true; }
      }
      if (bad) miss.any++;
      dh.push(Math.abs(g[2] - cpu[3 * s + 2]) * 1000);
    }
    dh.sort((a, b) => a - b);
    const share = {};
    for (const k in miss) share[k] = N ? miss[k] / N : 0;
    return { miss, share, heightMm: { p50: dh[Math.floor(N * 0.5)] ?? 0,
      p95: dh[Math.floor(N * 0.95)] ?? 0, max: dh[N - 1] ?? 0 } };
  }

  const tiles = [];
  let specTile = null;
  for (const texel of texels) {
    const spec = { texel, size: Math.round(span / texel), recentre: nf.spec.recentre };
    const tile = nf.build(e, n, spec);
    const m = [0, 0, 0];
    const mirror = compare((s) => nf.sample(tile, slots[2 * s], slots[2 * s + 1], m) ?? [-1, -1, NaN]);
    tiles.push({ texel, size: spec.size, buildMs: tile.ms, ...mirror });
    if (texel === nf.spec.texel) specTile = tile;
  }

  // 4. Through the GPU, at the spec texel.
  let gpu = null;
  if (specTile) {
    const THREE = await import('three');
    const r = api.renderer;
    const { size } = specTile;
    const cls = new THREE.DataTexture(specTile.cls, size, size, THREE.RGIntegerFormat,
      THREE.UnsignedByteType);
    cls.internalFormat = 'RG8UI';
    const hgt = new THREE.DataTexture(specTile.height, size, size, THREE.RedFormat,
      THREE.FloatType);
    hgt.internalFormat = 'R32F';
    for (const t of [cls, hgt]) {
      t.minFilter = t.magFilter = THREE.NearestFilter;
      t.generateMipmaps = false; t.flipY = false; t.needsUpdate = true;
    }
    const W = 256, H = Math.max(1, Math.ceil(N / W));
    const geo = new THREE.BufferGeometry();
    const en = new Float32Array(N * 2), idx = new Float32Array(N);
    for (let s = 0; s < N; s++) { en[2 * s] = slots[2 * s]; en[2 * s + 1] = slots[2 * s + 1]; idx[s] = s; }
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(N * 3), 3));
    geo.setAttribute('aEN', new THREE.BufferAttribute(en, 2));
    geo.setAttribute('aIdx', new THREE.BufferAttribute(idx, 1));
    const mat = new THREE.RawShaderMaterial({
      glslVersion: THREE.GLSL3,
      uniforms: {
        uFieldClass: { value: cls }, uFieldHeight: { value: hgt },
        uFieldOrigin: { value: new THREE.Vector2(specTile.e0, specTile.n0) },
        uFieldTexel: { value: specTile.texel }, uFieldSize: { value: size },
        uTarget: { value: new THREE.Vector2(W, H) },
      },
      vertexShader: `precision highp float; precision highp int;
in vec3 position; in vec2 aEN; in float aIdx;
uniform vec2 uTarget;
${nf.glsl}
flat out uvec2 vCls; out float vH;
void main() {
  vCls = fieldClass(aEN); vH = fieldHeight(aEN);
  float x = mod(aIdx, uTarget.x), y = floor(aIdx / uTarget.x);
  gl_Position = vec4((x + 0.5) / uTarget.x * 2.0 - 1.0, (y + 0.5) / uTarget.y * 2.0 - 1.0, 0.0, 1.0);
  gl_PointSize = 1.0;
}`,
      fragmentShader: `precision highp float; precision highp int;
flat in uvec2 vCls; in float vH; out vec4 o;
void main() { o = vec4(float(vCls.x), float(vCls.y), vH, 1.0); }`,
    });
    const pts = new THREE.Points(geo, mat);
    pts.frustumCulled = false;
    const sc = new THREE.Scene();
    sc.add(pts);
    const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.FloatType, format: THREE.RGBAFormat,
      minFilter: THREE.NearestFilter, magFilter: THREE.NearestFilter, depthBuffer: false });
    // Whatever the page's own frames left queued is not this pass's error.
    const gl = r.getContext();
    while (gl.getError() !== gl.NO_ERROR) { /* cleared */ }
    const prev = r.getRenderTarget();
    const buf = new Float32Array(W * H * 4);
    const g0 = performance.now();
    r.setRenderTarget(rt);
    r.render(sc, new THREE.Camera());
    r.readRenderTargetPixels(rt, 0, 0, W, H, buf);
    r.setRenderTarget(prev);
    const gpuMs = performance.now() - g0;
    const glErr = gl.getError();
    const back = (s) => [buf[4 * s], buf[4 * s + 1], buf[4 * s + 2]];
    const m = [0, 0, 0];
    // A slot the shader puts in the NEIGHBOURING texel because its position is
    // a float32 (the attribute, and the subtraction, are single precision) is
    // an edge case of the arithmetic and not of the indexing: counted apart.
    // Anything else that differs from the mirror is the GLSL disagreeing with
    // `sampleField`, and fails the run.
    const f = Math.fround;
    const texelOf = (v, o) => [Math.floor((v - o) / specTile.texel),
      Math.floor(f(f(f(v) - f(o)) / f(specTile.texel)))];
    let mirrorMiss = 0, float32Edge = 0, mirrorDh = 0;
    for (let s = 0; s < N; s++) {
      const g = back(s);
      const c = nf.sample(specTile, slots[2 * s], slots[2 * s + 1], m);
      if (!c || g[0] !== c[0] || g[1] !== c[1]) {
        const [i64, i32] = texelOf(slots[2 * s], specTile.e0);
        const [j64, j32] = texelOf(slots[2 * s + 1], specTile.n0);
        if (i64 !== i32 || j64 !== j32) float32Edge++;
        else mirrorMiss++;
      }
      if (c) mirrorDh = Math.max(mirrorDh, Math.abs(g[2] - c[2]) * 1000);
    }
    gpu = { texel: specTile.texel, size, readMs: gpuMs, glError: glErr,
      unwritten: buf.filter((_, i) => i % 4 === 3 && i / 4 < N && buf[i] !== 1).length,
      vsMirror: { classMiss: mirrorMiss, float32Edge, heightMaxMm: mirrorDh },
      vsCpu: compare(back) };
    for (const d of [cls, hgt, rt, geo, mat]) d.dispose();
  }
  const present = new Set();
  for (let s = 0; s < N; s++) present.add(cpu[3 * s]);
  return { id: st.id, e, n, slots: N, communities: [...present].sort((a, b) => a - b),
    queryMs, redealMs, redealt, tiles, gpu };
}

const browser = await chromium.launch({
  executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--enable-unsafe-swiftshader'],
});
const report = { ticket: 'T-2698', year: YEAR, measured: new Date().toISOString(),
  source: wantSource ? 'working tree' : 'published mirror', spanM: SPAN_M, viewports: [] };
let failed = false;
for (const vp of VIEWPORTS) {
  if (ONLY_VIEW && vp.id !== ONLY_VIEW) continue;
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height },
    hasTouch: vp.touch, isMobile: false, deviceScaleFactor: vp.scale });
  const page = await ctx.newPage();
  page.setDefaultTimeout(180_000);
  const errors = [];
  page.on('pageerror', (x) => errors.push(String(x)));
  await page.goto(`${base}${ENTRY}?year=${YEAR}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 480000 });
  await page.evaluate(() => window.__chicago4d.setAnimationHold?.(true));
  const meta = await page.evaluate(() => ({ detail: window.__chicago4d.detail,
    spec: window.__chicago4d.flora.nearField.spec,
    ring: window.__chicago4d.flora.rings.layers.near.lattice,
    step: window.__chicago4d.flora.rings.step,
    communities: window.__chicago4d.flora.communities().map((c) => c.id) }));
  console.log(`\n${vp.id} (${meta.detail}): near lattice ${meta.ring.inner}-${meta.ring.outer} m, `
    + `spec texel ${meta.spec.texel} m x ${meta.spec.size}, re-centre ${meta.spec.recentre} m`);
  const rows = [];
  for (const st of STATIONS) {
    const r = await page.evaluate(pageRead, { st, texels: TEXELS, span: SPAN_M });
    rows.push(r);
    const t = r.tiles.map((x) => `${x.texel}m ${(x.share.any * 100).toFixed(2)}%/${x.buildMs.toFixed(0)}ms`).join('  ');
    const g = r.gpu;
    console.log(`  ${st.id.padEnd(26)} ${String(r.slots).padStart(5)} slots  query ${r.queryMs.toFixed(1)} ms  `
      + `re-deal ${r.redealMs.toFixed(1)} ms (${r.redealt}/5) | ${t} | gpu any ${g ? (g.vsCpu.share.any * 100).toFixed(2) : '-'}% `
      + `vs-mirror ${g?.vsMirror.classMiss ?? '-'}+${g?.vsMirror.float32Edge ?? '-'}f32 dh ${g?.vsMirror.heightMaxMm.toFixed(3) ?? '-'} mm `
      + `h p95 ${g?.vsCpu.heightMm.p95.toFixed(1) ?? '-'} mm`);
    if (g && (g.vsMirror.classMiss || g.unwritten || g.glError)) {
      console.log(`    GPU READ-BACK FAILED: ${JSON.stringify({ classMiss: g.vsMirror.classMiss, unwritten: g.unwritten, glError: g.glError })}`);
      failed = true;
    }
  }
  // Totals over every slot of every station, each station weighted by its slots.
  const sum = (f) => rows.reduce((a, r) => a + f(r), 0);
  const slotsAll = sum((r) => r.slots);
  const byTexel = TEXELS.map((texel) => {
    const pick = (r) => r.tiles.find((x) => x.texel === texel);
    const share = {};
    for (const k of Object.keys(pick(rows[0]).miss)) share[k] = sum((r) => pick(r).miss[k]) / slotsAll;
    const builds = rows.map((r) => pick(r).buildMs).sort((a, b) => a - b);
    return { texel, size: pick(rows[0]).size, share,
      buildMsMedian: builds[Math.floor(builds.length / 2)], buildMsMax: builds.at(-1),
      heightP95MmMax: Math.max(...rows.map((r) => pick(r).heightMm.p95)) };
  });
  const gpuShare = {};
  if (rows[0].gpu) {
    for (const k of Object.keys(rows[0].gpu.vsCpu.miss)) {
      gpuShare[k] = sum((r) => r.gpu.vsCpu.miss[k]) / slotsAll;
    }
  }
  const med = (f) => { const v = rows.map(f).sort((a, b) => a - b); return v[Math.floor(v.length / 2)]; };
  const summary = { slots: slotsAll, byTexel, gpuVsCpuShare: gpuShare,
    gpuVsMirrorClassMiss: sum((r) => r.gpu?.vsMirror.classMiss ?? 0),
    gpuFloat32Edge: sum((r) => r.gpu?.vsMirror.float32Edge ?? 0),
    queryMsMedian: med((r) => r.queryMs), redealMsMedian: med((r) => r.redealMs) };
  // Per metre walked: the near deal re-deals every `step`, the tile is built
  // again every `recentre`. The same main thread pays both today.
  summary.perMetre = { redealMs: summary.redealMsMedian / meta.step,
    tileMs: Object.fromEntries(byTexel.map((b) => [b.texel, b.buildMsMedian / meta.spec.recentre])) };
  console.log(`  ALL ${slotsAll} slots: query median ${summary.queryMsMedian.toFixed(1)} ms, `
    + `near re-deal median ${summary.redealMsMedian.toFixed(1)} ms`);
  for (const b of byTexel) {
    console.log(`    texel ${b.texel} m (${b.size}^2): disagree any ${(b.share.any * 100).toFixed(3)}% `
      + `[community ${(b.share.community * 100).toFixed(3)}, wet ${(b.share.WET * 100).toFixed(3)}, `
      + `turf ${(b.share.TURF * 100).toFixed(3)}, blocked ${(b.share.BLOCKED * 100).toFixed(3)}, `
      + `trodden ${(b.share.TRODDEN * 100).toFixed(3)}]  build median ${b.buildMsMedian.toFixed(0)} ms `
      + `max ${b.buildMsMax.toFixed(0)} ms  height p95 <= ${b.heightP95MmMax.toFixed(1)} mm`);
  }
  console.log(`    GPU read-back at the spec texel: any ${((gpuShare.any ?? 0) * 100).toFixed(3)}%, `
    + `class differs from the CPU mirror at ${summary.gpuVsMirrorClassMiss} slots `
    + `(+${summary.gpuFloat32Edge} where float32 puts the slot in the next texel)`);
  console.log(`    per metre walked: near re-deal ${summary.perMetre.redealMs.toFixed(1)} ms; tile `
    + Object.entries(summary.perMetre.tileMs).map(([t, v]) => `${t} m ${v.toFixed(1)} ms`).join(', '));
  console.log(`  pageerrors: ${errors.length}${errors.length ? ` ${JSON.stringify(errors.slice(0, 3))}` : ''}`);
  if (errors.length) failed = true;
  report.viewports.push({ id: vp.id, detail: meta.detail, ring: meta.ring, step: meta.step, spec: meta.spec,
    communities: meta.communities, summary, stations: rows, pageerrors: errors });
  await ctx.close();
}
await browser.close();
server.close();
if (wantWrite) {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  // One viewport at a time fits a run's foreground ceiling, so a reading of
  // one keeps the other's from the file rather than dropping it.
  if (fs.existsSync(OUT)) {
    const kept = JSON.parse(fs.readFileSync(OUT, 'utf8')).viewports ?? [];
    const fresh = new Set(report.viewports.map((v) => v.id));
    report.viewports = [...kept.filter((v) => !fresh.has(v.id)), ...report.viewports]
      .sort((a, b) => a.id.localeCompare(b.id));
  }
  fs.writeFileSync(OUT, `${JSON.stringify(report, (k, v) => (typeof v === 'number'
    ? Math.round(v * 1e4) / 1e4 : v), 1)}\n`);
  console.log(`\nwrote ${path.relative(APP, OUT)}`);
}
process.exit(failed ? 1 : 0);

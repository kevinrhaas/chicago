/**
 * THE H0 BAKE-OFF READING (T-2558, docs/RENDERING.md section 8 "H0 — kill criteria").
 *
 *   node tools/measure_hd_spike.mjs --dir /tmp/h0 [--pages gpu,gl,classic] [--only phone|desktop|both]
 *        [--frames 60] [--throttle 4]
 *   node tools/measure_hd_spike.mjs --evaluate /tmp/h0 [--json docs/measurements/t-2558-h0-bakeoff.json]
 *
 * Three pages draw the identical Glessner block from the identical published GLBs
 * (`renderers/web-hd/`, see its block.js):
 *
 *   gpu ....... index.html, three's WebGPURenderer, on a browser that offers a WebGPU
 *               adapter (SwiftShader's, with the flags below).
 *   gl ........ index.html again, the same code, on a browser that offers NO adapter, so
 *               WebGPURenderer falls back to WebGL2 by itself (K7).
 *   classic ... classic.html, three's WebGLRenderer + walk/'s own confidence.js: walk/'s
 *               engine on the same block, the baseline.
 *
 * Each (page x viewport) is its own browser. It boots, shoots each stand with the
 * confidence view off and on, reads memory after two forced GCs, then drives the dolly
 * for the moving reading. The run mode writes one JSON and the PNGs per run into --dir,
 * so the six runs can be taken in separate foreground calls under the 600 s ceiling;
 * --evaluate diffs the captures against classic's and answers K1-K7.
 *
 * MEMORY is counted at the API each backend calls, the same way for both:
 *   WebGL (gl, classic) ... measure_memory.mjs's own GL meter, READ OUT OF THAT FILE at
 *                           run time (installGlMeter), so the two tools cannot drift.
 *   WebGPU (gpu) .......... GPUDevice.createBuffer / createTexture, less destroy(), each
 *                           texture at its format's bytes a texel over every mip level,
 *                           layer and sample.
 * plus the JS heap and ArrayBuffer backing store from Runtime.getHeapUsage. It is the
 * same RESIDENT ESTIMATE measure_memory gates: a floor on what a phone pays.
 *
 * FRAME TIME here is SwiftShader, a software rasteriser, on all three pages (T-2592's
 * finding). The ratio between pages is what K6 reads; the milliseconds are not a phone's.
 */

import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT4D = path.resolve(HERE, '..');
const SITE = path.resolve(ROOT4D, '../../site/4d');
const SPIKE = path.join(ROOT4D, 'renderers/web-hd');

const argv = process.argv.slice(2);
const argAt = (flag, dflt = null) => { const i = argv.indexOf(flag); return i >= 0 ? argv[i + 1] : dflt; };

// THE FLAGS, AND WHY EACH (measured on the steward runner, T-2558). Without
// `--use-angle=swiftshader` the compositor has no shared-image path for a WebGPU canvas
// ("Could not find SharedImageBackingFactory … Webgpu"): nothing presents, the canvas
// reads back empty, and seconds later the device is lost ("Instance dropped in
// popErrorScope"). And `--enable-features` REPLACES the list Playwright passes, so
// CDPScreenshotNewSurface is named again or page screenshots hang. A 64 px canvas
// cleared red read back red, by screenshot and by toDataURL, with this set and with no
// other set tried. The WebGL pages run on the same ANGLE SwiftShader, offered no adapter.
const GPU_ARGS = ['--enable-unsafe-webgpu', '--enable-features=Vulkan,CDPScreenshotNewSurface',
  '--use-vulkan=swiftshader', '--use-webgpu-adapter=swiftshader', '--enable-unsafe-swiftshader',
  '--use-angle=swiftshader'];
const PLAIN_ARGS = ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'];
const PAGES = {
  gpu: { file: 'index.html', args: GPU_ARGS, expect: 'webgpu' },
  gl: { file: 'index.html', args: PLAIN_ARGS, expect: 'webgl2-fallback' },
  classic: { file: 'classic.html', args: PLAIN_ARGS, expect: 'webgl-classic' },
};
// The phone profile of the kill criteria: 390 x 780 at ratio 1, touch, CPU throttled
// for the moving reading as measure_walk_frames throttles its phone.
const VIEWPORTS = {
  phone: { width: 390, height: 780, mobile: true },
  desktop: { width: 1280, height: 800, mobile: false },
};
const STANDS = ['spawn', 'oblique-ne'];

const pct = (xs, p) => {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  return s[Math.min(s.length - 1, Math.floor((p / 100) * s.length))];
};
const sd = (xs) => {
  if (xs.length < 2) return null;
  const m = xs.reduce((a, b) => a + b, 0) / xs.length;
  return Math.sqrt(xs.reduce((a, b) => a + (b - m) ** 2, 0) / (xs.length - 1));
};
const r1 = (x) => (x == null ? null : Math.round(x * 10) / 10);
const mib = (b) => r1(b / 1048576);

/** measure_memory.mjs's GL meter, as source, so the WebGL pages are metered identically. */
function glMeterSource() {
  const src = fs.readFileSync(path.join(HERE, 'measure_memory.mjs'), 'utf8');
  const start = src.indexOf('function installGlMeter() {');
  const end = src.indexOf('\n}\n', start);
  if (start < 0 || end < 0) throw new Error('installGlMeter not found in measure_memory.mjs');
  return `(${src.slice(start, end + 2)})();`;
}

/** The WebGPU allocation meter, installed before any page script runs. */
function installGpuMeter() {
  if (!window.GPUDevice) return;
  const BPT = {
    r8unorm: 1, r8snorm: 1, r8uint: 1, r8sint: 1, rg8unorm: 2, rg8snorm: 2, r16float: 2, r16uint: 2,
    r16sint: 2, depth16unorm: 2, rgba8unorm: 4, 'rgba8unorm-srgb': 4, bgra8unorm: 4, 'bgra8unorm-srgb': 4,
    rgba8snorm: 4, rgba8uint: 4, rg16float: 4, r32float: 4, r32uint: 4, r32sint: 4, rgb10a2unorm: 4,
    rg11b10ufloat: 4, depth24plus: 4, 'depth24plus-stencil8': 4, depth32float: 4, 'depth32float-stencil8': 5,
    rgba16float: 8, rgba16uint: 8, rg32float: 8, rgba32float: 16, rgba32uint: 16, stencil8: 1,
  };
  // Block formats, bytes a texel over whole 4 x 4 blocks.
  const block = (fmt) => (/^(bc1|bc4|etc2-rgb8|etc2-rgb8a1|eac-r11)/.test(fmt) ? 0.5
    : /^(bc2|bc3|bc5|bc6h|bc7|etc2-rgba8|eac-rg11|astc-4x4)/.test(fmt) ? 1 : 0);
  const dim = (size) => (Array.isArray(size) || size?.[Symbol.iterator]
    ? [...size] : [size?.width ?? 1, size?.height ?? 1, size?.depthOrArrayLayers ?? 1]);
  // WEAK, ON PURPOSE. three makes short-lived buffers it never destroy()s and leaves to
  // the collector; a Map holding them would keep every one alive and read them as
  // resident. So the meter keeps sizes in WeakMaps and lets a FinalizationRegistry take
  // a collected object's bytes off, which is also what the GPU does with it.
  const live = { buffer: { bytes: 0, count: 0 }, texture: { bytes: 0, count: 0 } };
  const byFormat = {};
  const sizes = new WeakMap();
  const drop = ({ kind, bytes, format }) => {
    live[kind].bytes -= bytes;
    live[kind].count -= 1;
    if (format) { byFormat[format].bytes -= bytes; byFormat[format].count -= 1; }
  };
  const gone = new FinalizationRegistry(drop);
  const track = (obj, kind, bytes, format = null) => {
    const rec = { kind, bytes, format };
    sizes.set(obj, rec);
    live[kind].bytes += bytes;
    live[kind].count += 1;
    if (format) {
      byFormat[format] ??= { bytes: 0, count: 0 };
      byFormat[format].bytes += bytes;
      byFormat[format].count += 1;
    }
    gone.register(obj, rec, obj);
  };
  const untrack = (obj) => {
    const s = sizes.get(obj);
    if (!s) return;
    sizes.delete(obj);
    gone.unregister(obj);
    drop(s);
  };
  const P = window.GPUDevice.prototype;
  const cb = P.createBuffer;
  P.createBuffer = function createBuffer(desc) {
    const b = cb.call(this, desc);
    try { track(b, 'buffer', desc.size || 0); } catch { /* never break the page */ }
    return b;
  };
  const ct = P.createTexture;
  P.createTexture = function createTexture(desc) {
    const t = ct.call(this, desc);
    try {
      const [w, h = 1, d = 1] = dim(desc.size);
      const levels = desc.mipLevelCount || 1;
      const blk = block(desc.format);
      const bpt = blk || BPT[desc.format] || 4;
      let bytes = 0;
      for (let l = 0; l < levels; l += 1) {
        let lw = Math.max(1, w >> l);
        let lh = Math.max(1, h >> l);
        if (blk) { lw = Math.max(4, Math.ceil(lw / 4) * 4); lh = Math.max(4, Math.ceil(lh / 4) * 4); }
        const ld = desc.dimension === '3d' ? Math.max(1, d >> l) : d;
        bytes += lw * lh * ld * bpt;
      }
      track(t, 'texture', bytes * (desc.sampleCount || 1),
        `${desc.format}${(desc.sampleCount || 1) > 1 ? ` x${desc.sampleCount}` : ''}${levels > 1 ? ' mipped' : ''}`);
    } catch { /* never break the page */ }
    return t;
  };
  const bd = window.GPUBuffer.prototype.destroy;
  window.GPUBuffer.prototype.destroy = function destroy() { untrack(this); return bd.call(this); };
  const td = window.GPUTexture.prototype.destroy;
  window.GPUTexture.prototype.destroy = function destroy() { untrack(this); return td.call(this); };
  window.__gpuMeter = () => ({
    gpuBuffers: live.buffer.bytes, gpuTextures: live.texture.bytes, gpuRenderbuffers: 0,
    liveBuffers: live.buffer.count, liveTextures: live.texture.count,
    texturesByFormat: Object.fromEntries(Object.entries(byFormat).filter(([, v]) => v.count > 0)),
  });
}

const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.glb': 'model/gltf-binary', '.bin': 'application/octet-stream',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.wasm': 'application/wasm',
  '.ktx2': 'image/ktx2', '.svg': 'image/svg+xml', '.woff2': 'font/woff2',
};

/** /4d/hd/* from the source spike (unpublished), every other /4d/* from the published mirror. */
function serve() {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split('?')[0]);
    let file = null;
    if (url.startsWith('/4d/hd/')) file = path.join(SPIKE, url.slice('/4d/hd/'.length));
    else if (url.startsWith('/4d/')) file = path.join(SITE, url.slice('/4d/'.length));
    const inside = file && (file.startsWith(SPIKE) || file.startsWith(SITE));
    if (!inside || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404, { 'content-type': 'text/plain' });
      res.end(`not found: ${url}`);
      return;
    }
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

async function runOne(pageId, vpId, dir, { frames, throttle, port }) {
  const spec = PAGES[pageId];
  const vp = VIEWPORTS[vpId];
  const browser = await chromium.launch({ args: spec.args, executablePath: process.env.PW_EXECUTABLE || undefined });
  const t0 = Date.now();
  const out = { page: pageId, viewport: vpId, args: spec.args, expect: spec.expect, errors: [], console: [] };
  try {
    const ctx = await browser.newContext({
      viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1, isMobile: vp.mobile, hasTouch: vp.mobile,
    });
    await ctx.addInitScript({ content: glMeterSource() });
    await ctx.addInitScript(installGpuMeter);
    const page = await ctx.newPage();
    page.on('pageerror', (e) => out.errors.push(String(e).slice(0, 400)));
    page.on('console', (m) => { if (m.type() === 'error') out.console.push(m.text().slice(0, 400)); });
    const cdp = await ctx.newCDPSession(page);
    await page.goto(`http://127.0.0.1:${port}/4d/hd/${spec.file}`, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__hd && 'ready' in window.__hd, null, { timeout: 420_000 });
    const hd = await page.evaluate(() => {
      const h = window.__hd;
      return h.ready ? { ready: true, backend: h.backend, bootMs: h.bootMs, loadMs: h.loadMs, loaded: h.loaded,
        problems: h.problems, bytes: h.bytes, sun: h.sun, materials: h.materials ?? null, info: h.info() }
        : { ready: false, error: h.error };
    });
    Object.assign(out, hd);
    out.wallBootS = Math.round((Date.now() - t0) / 1000);
    if (!hd.ready) return out;

    await page.evaluate(() => document.body.classList.add('capture'));
    out.shots = [];
    for (const stand of STANDS) {
      await page.evaluate((s) => window.__hd.setStand(s), stand);
      for (const on of [false, true]) {
        await page.evaluate((v) => window.__hd.setView(v), on);
        const name = `${pageId}-${vpId}-${stand}-${on ? 'on' : 'off'}.png`;
        const url = await page.evaluate(() => window.__hd.capture());
        fs.writeFileSync(path.join(dir, name), Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
        out.shots.push({ stand, view: on ? 'on' : 'off', file: name });
      }
    }
    await page.evaluate(() => window.__hd.setView(false));
    await page.evaluate((s) => window.__hd.setStand(s), 'spawn');
    await page.evaluate(() => window.__hd.settle(2));

    await cdp.send('HeapProfiler.enable');
    const readMemory = async () => {
      await cdp.send('HeapProfiler.collectGarbage');
      await cdp.send('HeapProfiler.collectGarbage');
      // A collected GPU object's bytes come off in a FinalizationRegistry callback, which
      // runs on a later task than the collection.
      await page.evaluate(() => new Promise((r) => setTimeout(r, 100)));
      const heap = await cdp.send('Runtime.getHeapUsage');
      const meter = await page.evaluate(() => (window.__hd.backend === 'webgpu' ? window.__gpuMeter?.() : window.__memoryMeter?.()) ?? null);
      const m = { jsHeap: heap.usedSize, arrayBuffers: heap.backingStorageSize ?? 0, ...meter };
      m.total = m.jsHeap + m.arrayBuffers + (meter?.gpuBuffers ?? 0) + (meter?.gpuTextures ?? 0) + (meter?.gpuRenderbuffers ?? 0);
      m.meter = meter ? (out.backend === 'webgpu' ? 'webgpu createBuffer/createTexture' : 'measure_memory GL meter') : 'NONE';
      return m;
    };
    // As booted, at the spawn: what each renderer chose to put on the GPU by itself.
    out.memoryAtBoot = await readMemory();
    // K5's reading: every block texture resident on both pages (uploadAll's note).
    out.texturesUploaded = await page.evaluate(() => window.__hd.uploadAll());
    out.memory = await readMemory();

    const rate = vp.mobile ? throttle : 1;
    if (rate > 1) await cdp.send('Emulation.setCPUThrottlingRate', { rate });
    await page.evaluate(() => window.__hd.dolly(8)); // warm: pipelines, shadow map, first poses
    const moving = await page.evaluate((n) => window.__hd.dolly(n), frames);
    const synced = await page.evaluate((n) => window.__hd.dollySynced(n), frames);
    if (rate > 1) await cdp.send('Emulation.setCPUThrottlingRate', { rate: 1 });
    out.moving = {
      frames, throttle: rate,
      interval: { p50: r1(pct(moving.intervals, 50)), p95: r1(pct(moving.intervals, 95)), sd: r1(sd(moving.intervals)) },
      render: { p50: r1(pct(moving.renderMs, 50)), p95: r1(pct(moving.renderMs, 95)) },
      finished: { p50: r1(pct(synced.costMs, 50)), p95: r1(pct(synced.costMs, 95)), sd: r1(sd(synced.costMs)) },
    };
    out.infoAfter = await page.evaluate(() => window.__hd.info());
    out.textures = await page.evaluate(() => window.__hd.textures());
  } catch (err) {
    out.errors.push(`harness: ${String(err?.message ?? err).slice(0, 400)}`);
  } finally {
    out.wallS = Math.round((Date.now() - t0) / 1000);
    await browser.close();
  }
  return out;
}

/** Pixel parity of two same-size PNGs, decoded by the browser. */
async function diffAll(pairs, dir) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const results = [];
  for (const p of pairs) {
    const a = fs.readFileSync(path.join(dir, p.a)).toString('base64');
    const b = fs.readFileSync(path.join(dir, p.b)).toString('base64');
    const d = await page.evaluate(async ([a64, b64]) => {
      const load = (s) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = `data:image/png;base64,${s}`; });
      const [ia, ib] = await Promise.all([load(a64), load(b64)]);
      if (ia.width !== ib.width || ia.height !== ib.height) return { error: 'size mismatch' };
      const px = (img) => { const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const g = c.getContext('2d'); g.drawImage(img, 0, 0); return g.getImageData(0, 0, c.width, c.height).data; };
      const da = px(ia); const db = px(ib);
      let sum = 0; let big = 0; const n = ia.width * ia.height;
      for (let i = 0; i < da.length; i += 4) {
        const dr = Math.abs(da[i] - db[i]); const dg = Math.abs(da[i + 1] - db[i + 1]); const dbb = Math.abs(da[i + 2] - db[i + 2]);
        sum += dr + dg + dbb;
        if (Math.max(dr, dg, dbb) > 40) big += 1;
      }
      return { meanAbs: sum / (n * 3), over40: big / n };
    }, [a, b]);
    results.push({ ...p, meanAbs255: d.meanAbs == null ? null : Math.round(d.meanAbs * 100) / 100,
      over40Pct: d.over40 == null ? null : Math.round(d.over40 * 10000) / 100, error: d.error });
  }
  await browser.close();
  return results;
}

async function evaluate(dir) {
  const runs = fs.readdirSync(dir).filter((f) => /^run-.*\.json$/.test(f))
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), 'utf8')));
  const get = (p, v) => runs.find((r) => r.page === p && r.viewport === v);
  const pairs = [];
  for (const vp of Object.keys(VIEWPORTS)) {
    const base = get('classic', vp);
    for (const p of ['gpu', 'gl']) {
      const r = get(p, vp);
      if (!r?.shots || !base?.shots) continue;
      for (const s of r.shots) {
        const b = base.shots.find((x) => x.stand === s.stand && x.view === s.view);
        if (b) pairs.push({ page: p, viewport: vp, stand: s.stand, view: s.view, a: s.file, b: b.file });
      }
    }
  }
  const diffs = await diffAll(pairs, dir);
  const parity = (rows) => rows.length > 0 && rows.every((d) => d.meanAbs255 != null && d.meanAbs255 <= 6 && d.over40Pct <= 4);
  const clean = (r) => !!r?.ready && r.backend === r.expect && r.errors.length === 0 && r.console.length === 0;
  const ratio = (a, b) => (a != null && b ? Math.round((a / b) * 100) / 100 : null);
  const K = {};
  const vps = Object.keys(VIEWPORTS);
  K.K1 = { pass: vps.every((v) => clean(get('gpu', v)) && clean(get('gl', v))),
    detail: Object.fromEntries(['gpu', 'gl', 'classic'].flatMap((p) => vps.map((v) => {
      const r = get(p, v);
      return [`${p}/${v}`, r ? { ready: !!r.ready, backend: r.backend ?? null, pageErrors: r.errors.length, consoleErrors: r.console.length, bootMs: r.bootMs ?? null } : 'not run'];
    }))) };
  const nBlock = get('classic', 'phone')?.loaded?.length ?? null;
  K.K2 = { pass: ['gpu', 'gl'].every((p) => vps.every((v) => { const r = get(p, v); return r?.ready && r.problems.length === 0 && r.loaded.length === nBlock; })),
    detail: Object.fromEntries(['gpu', 'gl', 'classic'].flatMap((p) => vps.map((v) => { const r = get(p, v); return [`${p}/${v}`, r?.ready ? { loaded: r.loaded.length, problems: r.problems } : 'not ready']; }))) };
  K.K3 = { pass: parity(diffs.filter((d) => d.view === 'on')), detail: diffs.filter((d) => d.view === 'on') };
  K.K4 = { pass: parity(diffs.filter((d) => d.view === 'off')), detail: diffs.filter((d) => d.view === 'off') };
  const memPhone = (p) => get(p, 'phone')?.memory ?? null;
  K.K5 = { pass: memPhone('gpu') && memPhone('classic') ? memPhone('gpu').total <= memPhone('classic').total : false,
    detail: Object.fromEntries(['gpu', 'gl', 'classic'].flatMap((p) => vps.map((v) => {
      const m = get(p, v)?.memory;
      const b = get(p, v)?.memoryAtBoot;
      return [`${p}/${v}`, m ? { atBootTotalMiB: b ? mib(b.total) : null, totalMiB: mib(m.total), jsHeapMiB: mib(m.jsHeap), arrayBuffersMiB: mib(m.arrayBuffers), gpuBuffersMiB: mib(m.gpuBuffers ?? 0), gpuTexturesMiB: mib(m.gpuTextures ?? 0), gpuRenderbuffersMiB: mib(m.gpuRenderbuffers ?? 0), meter: m.meter } : 'not read'];
    }))) };
  const p95 = (p, v) => get(p, v)?.moving?.interval?.p95 ?? null;
  const k6 = ratio(p95('gpu', 'phone'), p95('classic', 'phone'));
  K.K6 = { pass: k6 != null && k6 <= 1.5, band: k6 == null ? 'unread' : k6 <= 1 ? 'go' : k6 <= 1.5 ? 'go with conditions' : 'no-go',
    gpuOverClassicPhone: k6, glOverClassicPhone: ratio(p95('gl', 'phone'), p95('classic', 'phone')),
    gpuOverClassicDesktop: ratio(p95('gpu', 'desktop'), p95('classic', 'desktop')),
    finishedGpuOverClassicPhone: ratio(get('gpu', 'phone')?.moving?.finished?.p95, get('classic', 'phone')?.moving?.finished?.p95),
    finishedGlOverClassicPhone: ratio(get('gl', 'phone')?.moving?.finished?.p95, get('classic', 'phone')?.moving?.finished?.p95),
    detail: Object.fromEntries(['gpu', 'gl', 'classic'].flatMap((p) => vps.map((v) => [`${p}/${v}`, get(p, v)?.moving ?? 'not read']))) };
  K.K7 = { pass: vps.every((v) => clean(get('gl', v))), detail: 'the gl runs: a browser launched with no WebGPU adapter; the backend each reported is in K1' };
  const go = K.K1.pass && K.K2.pass && K.K3.pass && K.K4.pass && K.K5.pass && K.K6.pass && K.K7.pass;
  const flip = !(K.K1.pass && K.K2.pass && K.K3.pass);
  return {
    ticket: 'T-2558', measured: new Date().toISOString(), tool: 'tools/measure_hd_spike.mjs',
    note: 'SwiftShader rasterises every page on the steward runner: frame times are a software stand-in, read as ratios.',
    verdict: go ? 'GO' : flip ? 'NO-GO (engine cannot carry the contract: flip to Babylon per section 3)' : 'NO-GO on a named criterion',
    criteria: K,
    runs: runs.map((r) => ({ page: r.page, viewport: r.viewport, backend: r.backend, bootMs: r.bootMs, loadMs: r.loadMs,
      bytes: r.bytes, info: r.info, materials: r.materials, loaded: r.loaded, wallS: r.wallS, args: r.args,
      errors: r.errors, console: r.console })),
  };
}

function printSummary(res) {
  console.log(`\nH0 bake-off (T-2558) — verdict: ${res.verdict}`);
  for (const [k, v] of Object.entries(res.criteria)) {
    console.log(`  ${k} ${v.pass ? 'PASS' : 'FAIL'}${v.band ? ` (${v.band}, gpu/classic p95 ${v.gpuOverClassicPhone})` : ''}`);
  }
  const K5 = res.criteria.K5.detail;
  for (const [k, v] of Object.entries(K5)) if (typeof v === 'object') console.log(`    mem ${k}: ${v.totalMiB} MiB, at boot ${v.atBootTotalMiB} (heap ${v.jsHeapMiB}, ab ${v.arrayBuffersMiB}, buf ${v.gpuBuffersMiB}, tex ${v.gpuTexturesMiB}, rb ${v.gpuRenderbuffersMiB})`);
  for (const [k, v] of Object.entries(res.criteria.K6.detail)) if (typeof v === 'object') console.log(`    moving ${k}: interval p50 ${v.interval.p50} p95 ${v.interval.p95} sd ${v.interval.sd} ms · render p50 ${v.render.p50} p95 ${v.render.p95} ms · finished p50 ${v.finished?.p50} p95 ${v.finished?.p95} ms · throttle ${v.throttle}x`);
  for (const d of [...res.criteria.K3.detail, ...res.criteria.K4.detail]) console.log(`    parity ${d.page}/${d.viewport} ${d.stand} view-${d.view}: mean ${d.meanAbs255}/255, >40: ${d.over40Pct} %`);
  for (const r of res.runs) if (r.errors?.length || r.console?.length) console.log(`    ${r.page}/${r.viewport} errors: ${[...r.errors, ...r.console].slice(0, 3).join(' | ')}`);
}

// ------------------------------------------------------------------------------ main

const evalDir = argAt('--evaluate');
if (evalDir) {
  const res = await evaluate(evalDir);
  printSummary(res);
  const json = argAt('--json');
  if (json) { fs.writeFileSync(json, `${JSON.stringify(res, null, 2)}\n`); console.log(`\nwrote ${json}`); }
  process.exit(0);
}

const dir = argAt('--dir');
if (!dir) { console.error('usage: --dir <out> [--pages gpu,gl,classic] [--only phone|desktop|both] | --evaluate <dir>'); process.exit(2); }
if (!fs.existsSync(path.join(SITE, 'data/sidecars/1904/index.json'))) {
  console.error(`no published mirror at ${SITE} — run tools/publish.sh first`);
  process.exit(2);
}
fs.mkdirSync(dir, { recursive: true });
const pages = (argAt('--pages', 'gpu,gl,classic')).split(',');
const only = argAt('--only', 'both');
const vps = only === 'both' ? ['phone', 'desktop'] : [only];
const frames = Number(argAt('--frames', '60'));
const throttle = Number(argAt('--throttle', '4'));
const server = await serve();
const port = server.address().port;
for (const p of pages) {
  for (const v of vps) {
    const r = await runOne(p, v, dir, { frames, throttle, port });
    fs.writeFileSync(path.join(dir, `run-${p}-${v}.json`), `${JSON.stringify(r, null, 2)}\n`);
    console.log(`${p}/${v}: ${r.ready ? `${r.backend} ready ${r.bootMs} ms, ${r.loaded?.length} structures` : `NOT READY ${r.error ?? ''}`}`
      + `${r.memory ? `, ${mib(r.memory.total)} MiB` : ''}${r.moving ? `, moving p95 ${r.moving.interval.p95} ms` : ''}`
      + `, errors ${r.errors.length}/${r.console.length}, ${r.wallS} s`);
    for (const e of [...r.errors, ...r.console].slice(0, 4)) console.log(`   ! ${e}`);
  }
}
server.close();

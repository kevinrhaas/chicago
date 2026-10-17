/**
 * THE GL METER AUDITED AGAINST THE PAGE (T-2720).
 *
 *   node tools/audit_gl_meter.mjs [--site <published 4d mirror>] [--only phone|desktop]
 *        [--json docs/measurements/t-2720-gl-meter.json]
 *
 * measure_memory.mjs's GL meter (`installGlMeter`) is what walk/'s memory ceilings and
 * the H0 bake-off's K5 stand on. This boots the H0 CLASSIC page (renderers/web-hd/
 * classic.html, three's WebGLRenderer on the Glessner block), makes every block texture
 * resident as measure_hd_spike.mjs does, and reads three ways at once:
 *
 *   meter ...... window.__memoryMeter(), the meter READ OUT OF measure_memory.mjs at run
 *                time, exactly as measure_hd_spike.mjs reads it, so the two cannot drift.
 *   calls ...... every allocating WebGL call the page made (texStorage2D, texImage2D, the
 *                compressed and 3D forms, generateMipmap, renderbufferStorage*), logged
 *                by a second wrapper and summed here independently, by internal format.
 *   three ...... every Texture object on the block's materials, with its image Source
 *                and the WebGLTexture three's own `properties` gave it, so a Texture that
 *                shares another's GPU texture shows as one.
 *
 * The meter is right when meter == calls. The page holds less than three's per-Texture
 * arithmetic when Texture objects share a GL texture: three's WebGLTextures keys a GPU
 * texture on (image Source, sampling state), not on the Texture object.
 *
 * --site lets the reading be taken on another build's published mirror: the H0 reading
 * (2026-10-16) is a `git worktree` of that commit with `tools/publish.sh` run in it.
 */

import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT4D = path.resolve(HERE, '..');
const argv = process.argv.slice(2);
const argAt = (flag, dflt = null) => { const i = argv.indexOf(flag); return i >= 0 ? argv[i + 1] : dflt; };
const SITE = path.resolve(argAt('--site', path.resolve(ROOT4D, '../../site/4d')));
// The page and its JS come from the mirror's own build when it has the spike beside it.
const SPIKE = path.resolve(SITE, '../../chicago/4d/renderers/web-hd');
const VIEWPORTS = { phone: { width: 390, height: 780, mobile: true }, desktop: { width: 1280, height: 800, mobile: false } };
const MiB = (b) => Math.round((b / 1048576) * 100) / 100;

function glMeterSource() {
  const src = fs.readFileSync(path.join(HERE, 'measure_memory.mjs'), 'utf8');
  const start = src.indexOf('function installGlMeter() {');
  const end = src.indexOf('\n}\n', start);
  if (start < 0 || end < 0) throw new Error('installGlMeter not found in measure_memory.mjs');
  return `(${src.slice(start, end + 2)})();`;
}

/** The second wrapper: a log of every allocating call, with the texture it landed on. */
function installCallLog() {
  const ids = new WeakMap();
  let next = 1;
  const id = (o) => { if (!o) return 0; if (!ids.has(o)) ids.set(o, next++); return ids.get(o); };
  window.__glTexId = id;
  const log = [];
  window.__glCalls = log;
  const BINDING = { 0x0DE1: 0x8069, 0x8513: 0x8514, 0x806F: 0x806A, 0x8C1A: 0x8C1D };
  const binding = (t) => (t >= 0x8515 && t <= 0x851A ? 0x8514 : BINDING[t] ?? 0x8069);
  const NAMES = ['texStorage2D', 'texImage2D', 'compressedTexImage2D', 'texStorage3D', 'texImage3D',
    'generateMipmap', 'renderbufferStorage', 'renderbufferStorageMultisample'];
  for (const Ctx of [window.WebGL2RenderingContext, window.WebGLRenderingContext]) {
    if (!Ctx) continue;
    for (const name of NAMES) {
      const orig = Ctx.prototype[name];
      if (!orig) continue;
      Ctx.prototype[name] = function logged(...a) {
        const rb = name.startsWith('renderbuffer');
        const on = rb ? this.getParameter(this.RENDERBUFFER_BINDING) : this.getParameter(binding(a[0]));
        const src = a.find((x) => x && typeof x === 'object' && 'width' in x && !ArrayBuffer.isView(x));
        log.push({ name, obj: (rb ? 'rb' : 'tex') + id(on), args: a.map((x) => (typeof x === 'number' ? x : null)),
          src: src ? [src.width, src.height] : null });
        return orig.apply(this, a);
      };
    }
  }
}

// Bytes a texel by internal format, for the formats this page allocates; anything else is
// reported unpriced rather than guessed.
const BPP = { 0x8058: 4, 0x8C43: 4, 0x881A: 8, 0x822F: 4, 0x8230: 8, 0x81A5: 2, 0x81A6: 4, 0x8CAC: 4, 0x88F0: 4, 0x8229: 1 };
const BLOCK = { 0x8E8C: 1, 0x8E8D: 1, 0x93B0: 1, 0x93D0: 1, 0x9278: 1, 0x9279: 1, 0x9274: 0.5, 0x9275: 0.5, 0x83F0: 0.5, 0x83F1: 0.5 };
const UNSIZED_RGBA = 0x1908;
const TYPE_BPP = { 0x1401: 1, 0x140B: 2, 0x8D61: 2, 0x1406: 4 };
const blocks = (n) => Math.max(4, Math.ceil(n / 4) * 4);
const levelBytes = (fmt, w, h) => (BLOCK[fmt] ? blocks(w) * blocks(h) * BLOCK[fmt] : w * h * (BPP[fmt] ?? NaN));

/** The calls summed here, by object: what WebGL was actually asked to hold. */
function sumCalls(calls) {
  const objs = new Map();
  const get = (k) => { if (!objs.has(k)) objs.set(k, { levels: new Map(), mipped: false, fmt: null }); return objs.get(k); };
  for (const c of calls) {
    const a = c.args;
    const o = get(c.obj);
    if (c.name === 'texStorage2D') {
      // WebGL takes `levels` as a GLsizei: a fractional count (three passes log2(n) + 1
      // for a non-power-of-two image) is truncated.
      o.fmt = a[2];
      for (let l = 0; l < Math.trunc(a[1]); l += 1) {
        o.levels.set(`${a[0]}:${l}`, levelBytes(a[2], Math.max(1, a[3] >> l), Math.max(1, a[4] >> l)) * (a[0] === 0x8513 ? 6 : 1));
      }
    } else if (c.name === 'texImage2D') {
      const [w, h] = c.src ?? [a[3], a[4]];
      const type = c.src ? a[4] : a[7];
      o.fmt = a[2];
      const bpp = a[2] === UNSIZED_RGBA ? 4 * (TYPE_BPP[type] ?? 1) : BPP[a[2]] ?? NaN;
      o.levels.set(`${a[0]}:${a[1]}`, w * h * bpp);
    } else if (c.name === 'texImage3D') {
      o.fmt = a[2];
      o.levels.set(`${a[0]}:${a[1]}`, a[3] * a[4] * a[5] * (a[2] === UNSIZED_RGBA ? 4 : BPP[a[2]] ?? NaN));
    } else if (c.name === 'generateMipmap') {
      o.mipped = true;
    } else if (c.name.startsWith('renderbuffer')) {
      const [samples, fmt, w, h] = c.name === 'renderbufferStorage' ? [1, a[1], a[2], a[3]] : [a[1], a[2], a[3], a[4]];
      o.fmt = fmt;
      o.levels.set('rb', w * h * (BPP[fmt] ?? NaN) * Math.max(1, samples));
    } else {
      o.unpriced = c.name;
    }
  }
  const out = { textures: 0, renderbuffers: 0, byFormat: {}, unpriced: [] };
  for (const [k, o] of objs) {
    let b = 0;
    for (const v of o.levels.values()) b += v;
    // generateMipmap on a texture holding only level 0 allocates the rest of the chain.
    if (o.mipped && o.levels.size === 1 && !o.levels.has('rb')) b = Math.round((b * 4) / 3);
    if (Number.isNaN(b) || o.unpriced) { out.unpriced.push(k); continue; }
    if (k.startsWith('rb')) out.renderbuffers += b; else out.textures += b;
    const key = `${k.startsWith('rb') ? 'rb ' : ''}0x${(o.fmt ?? 0).toString(16)}`;
    out.byFormat[key] ??= { count: 0, MiB: 0, bytes: 0 };
    out.byFormat[key].count += 1;
    out.byFormat[key].bytes += b;
    out.byFormat[key].MiB = MiB(out.byFormat[key].bytes);
  }
  return out;
}

/** three's side, on the page: each block Texture, its Source, and the GL texture it got. */
async function readThree() {
  const THREE = await import('/4d/walk/vendor/three-0.185.1/three.module.js');
  // The renderer and scene are the page's own; the next frame hands them to onBeforeRender.
  let renderer = null; let scene = null;
  const P = THREE.Object3D.prototype;
  const before = P.onBeforeRender;
  P.onBeforeRender = function grab(r, s) { renderer = r; scene = s; };
  await window.__hd.settle(1);
  P.onBeforeRender = before;
  const seen = new Set(); const rows = [];
  scene.traverse((o) => {
    if (!o.isMesh) return;
    for (const m of [].concat(o.material)) {
      for (const v of Object.values(m)) {
        if (!v?.isTexture || seen.has(v)) continue;
        seen.add(v);
        const gl = renderer.properties.get(v).__webglTexture;
        rows.push({ name: v.name || null, compressed: !!v.isCompressedTexture, source: v.source.uuid,
          w: v.image?.width ?? v.mipmaps?.[0]?.width ?? 0, h: v.image?.height ?? v.mipmaps?.[0]?.height ?? 0,
          colorSpace: v.colorSpace, gl: gl ? `tex${window.__glTexId(gl)}` : null });
      }
    }
  });
  return rows;
}

function serve() {
  const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
    '.json': 'application/json', '.wasm': 'application/wasm', '.ktx2': 'image/ktx2', '.png': 'image/png', '.jpg': 'image/jpeg' };
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent(req.url.split('?')[0]);
    let file = null;
    if (url.startsWith('/4d/hd/')) file = path.join(SPIKE, url.slice('/4d/hd/'.length));
    else if (url.startsWith('/4d/')) file = path.join(SITE, url.slice('/4d/'.length));
    if (!file || !(file.startsWith(SPIKE) || file.startsWith(SITE)) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      res.writeHead(404, { 'content-type': 'text/plain' }); res.end(`not found: ${url}`); return;
    }
    res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)));
}

async function auditOne(vpId, port) {
  const vp = VIEWPORTS[vpId];
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-angle=swiftshader'],
    executablePath: process.env.PW_EXECUTABLE || undefined });
  const out = { viewport: vpId, errors: [] };
  try {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 1, isMobile: vp.mobile, hasTouch: vp.mobile });
    await ctx.addInitScript({ content: glMeterSource() });
    await ctx.addInitScript(installCallLog);
    const page = await ctx.newPage();
    page.on('pageerror', (e) => out.errors.push(String(e).slice(0, 300)));
    await page.goto(`http://127.0.0.1:${port}/4d/hd/classic.html`, { waitUntil: 'load' });
    await page.waitForFunction(() => window.__hd && 'ready' in window.__hd, null, { timeout: 420_000 });
    if (!(await page.evaluate(() => window.__hd.ready))) { out.errors.push(await page.evaluate(() => window.__hd.error)); return out; }
    out.uploaded = await page.evaluate(() => window.__hd.uploadAll());
    const meter = await page.evaluate(() => window.__memoryMeter());
    const calls = sumCalls(await page.evaluate(() => window.__glCalls));
    const three = await page.evaluate(readThree);
    const perTexture = (rows) => rows.reduce((s, r) => s + (r.compressed ? 1 : 4) * r.w * r.h * (4 / 3), 0);
    const byGl = new Map();
    for (const r of three) { if (!byGl.has(r.gl)) byGl.set(r.gl, []); byGl.get(r.gl).push(r); }
    const shared = [...byGl.values()].filter((rs) => rs.length > 1).map((rs) => ({
      name: rs[0].name, size: `${rs[0].w}x${rs[0].h}`, textures: rs.length, gl: rs[0].gl,
      sources: new Set(rs.map((r) => r.source)).size, uncountedMiB: MiB(perTexture(rs.slice(1))),
    }));
    const kind = (c) => three.filter((r) => r.compressed === c);
    out.meter = { texturesMiB: MiB(meter.gpuTextures), renderbuffersMiB: MiB(meter.gpuRenderbuffers), liveTextures: meter.liveTextures };
    out.calls = { texturesMiB: MiB(calls.textures), renderbuffersMiB: MiB(calls.renderbuffers), byFormat: calls.byFormat, unpriced: calls.unpriced };
    out.meterMinusCallsBytes = { textures: meter.gpuTextures - calls.textures, renderbuffers: meter.gpuRenderbuffers - calls.renderbuffers };
    out.three = {
      textureObjects: three.length,
      image: { objects: kind(false).length, glTextures: new Set(kind(false).map((r) => r.gl)).size, perTextureMiB: MiB(perTexture(kind(false))) },
      compressed: { objects: kind(true).length, glTextures: new Set(kind(true).map((r) => r.gl)).size, perTextureMiB: MiB(perTexture(kind(true))) },
      distinctSources: new Set(three.map((r) => r.source)).size,
      glTextures: byGl.size,
      shared,
      sharedUncountedMiB: MiB(shared.reduce((s, x) => s + x.uncountedMiB * 1048576, 0)),
    };
  } catch (err) {
    out.errors.push(`harness: ${String(err?.message ?? err).slice(0, 300)}`);
  } finally {
    await browser.close();
  }
  return out;
}

if (!fs.existsSync(path.join(SITE, 'data/sidecars/1904/index.json'))) {
  console.error(`no published mirror at ${SITE} — run tools/publish.sh first`);
  process.exit(2);
}
const only = argAt('--only', 'phone');
const server = await serve();
const runs = [];
for (const v of only === 'both' ? ['phone', 'desktop'] : [only]) {
  const r = await auditOne(v, server.address().port);
  runs.push(r);
  if (!r.meter) { console.log(`${v}: not read — ${r.errors.join(' | ')}`); continue; }
  console.log(`${v}: meter ${r.meter.texturesMiB} MiB textures + ${r.meter.renderbuffersMiB} rb · calls ${r.calls.texturesMiB} + ${r.calls.renderbuffersMiB}`
    + ` · meter - calls ${r.meterMinusCallsBytes.textures} / ${r.meterMinusCallsBytes.renderbuffers} bytes`);
  console.log(`   three: ${r.three.textureObjects} Texture objects, ${r.three.distinctSources} sources, ${r.three.glTextures} GL textures;`
    + ` image ${r.three.image.objects} objects on ${r.three.image.glTextures} (${r.three.image.perTextureMiB} MiB per-Texture arithmetic),`
    + ` compressed ${r.three.compressed.objects} on ${r.three.compressed.glTextures}`);
  for (const s of r.three.shared) console.log(`   shared: ${s.name} ${s.size} x${s.textures} on ${s.gl} (${s.sources} source) — ${s.uncountedMiB} MiB three counts and WebGL does not hold`);
  for (const [k, f] of Object.entries(r.calls.byFormat)) console.log(`   calls ${k}: ${f.count} objects, ${f.MiB} MiB`);
  if (r.errors.length) console.log(`   errors: ${r.errors.join(' | ')}`);
}
server.close();
const json = argAt('--json');
if (json) {
  let build = null;
  try { build = fs.readFileSync(path.join(SITE, 'build.txt'), 'utf8').trim(); } catch { /* not every mirror stamps one */ }
  fs.writeFileSync(json, `${JSON.stringify({ ticket: 'T-2720', tool: 'tools/audit_gl_meter.mjs', measured: new Date().toISOString(), site: SITE, build, runs }, null, 2)}\n`);
  console.log(`wrote ${json}`);
}

#!/usr/bin/env node
// T-2288: capture the K02 stone library in raking and diffuse light, at 1280x800 and 390x780.
//
//   node tools/k02_stone_study.mjs            # write docs/RESEARCH/k02-stone-library-2288/
//
// Serves chicago/4d on a loopback port, opens tools/k02_stone_study.html (a study page that
// is never published), and for each viewport, light and view writes a JPEG and the page's
// own load, draw-call, triangle, texture and frame readings. It fails on any page error.
// The texture costs are read off the library's manifest: the bytes a renderer would fetch
// (the three web JPEGs per fabric) and the GPU pixels they decode to.
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'docs/RESEARCH/k02-stone-library-2288');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.json': 'application/json', '.jpg': 'image/jpeg', '.png': 'image/png' };

const server = createServer(async (req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT)) { res.writeHead(403).end(); return; }
  try {
    res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream' });
    res.end(await readFile(p));
  } catch { res.writeHead(404).end(); }
});
await new Promise((ok) => server.listen(0, '127.0.0.1', ok));
const base = `http://127.0.0.1:${server.address().port}/tools/k02_stone_study.html`;

const { chromium } = await import('playwright');
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const viewports = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };
const readings = [];
const errors = [];
await mkdir(OUT, { recursive: true });
try {
  for (const [vp, size] of Object.entries(viewports)) {
    for (const light of ['raking', 'diffuse']) {
      for (const view of ['panel', 'close']) {
        const page = await browser.newPage({ viewport: size });
        page.on('pageerror', (e) => errors.push(`${vp} ${light} ${view}: ${e.message}`));
        await page.goto(`${base}?light=${light}&view=${view}`);
        await page.waitForFunction(() => window.__study?.ready, null, { timeout: 120000 });
        const r = await page.evaluate(() => window.__study);
        const file = `${vp}-${light}-${view}.jpg`;
        await page.screenshot({ path: path.join(OUT, file), type: 'jpeg', quality: 84 });
        readings.push({ file, ...r });
        console.log(`${file}: load ${r.load_ms} ms, ${r.draw_calls} draws, ${r.triangles} tris, ${r.textures} textures, frame ${r.frame_ms_median.toFixed(2)} ms`);
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
  server.close();
}

const manifest = JSON.parse(await readFile(path.join(ROOT, 'assets/textures/prairie_1904_stone/manifest.json'), 'utf8'));
const textures = manifest.materials.map((m) => {
  const web = Object.fromEntries(Object.entries(m.web).map(([k, f]) => [k, m.bytes[f.slice(m.id.length + 1)]]));
  const px = m.resolution_px;
  return { id: m.id, tile_m: m.tile_m[0], px_per_m: m.px_per_m, web_bytes: web,
    web_bytes_total: Object.values(web).reduce((a, b) => a + b, 0),
    gpu_pixels: px.basecolor ** 2 + px.normal_gl ** 2 + px.orm ** 2,
    gpu_bytes_rgba_with_mips: Math.round((px.basecolor ** 2 + px.normal_gl ** 2 + px.orm ** 2) * 4 * 4 / 3) };
});
const report = {
  ticket: 'T-2288',
  page: 'tools/k02_stone_study.html (served by tools/k02_stone_study.mjs; not published)',
  what: 'each K02 fabric laid as blocks from k02_stone_profiles.json with metric UVs, 1.2 x 1.0 m panels and 0.5 m close windows, in an 8-degree raking sun and in diffuse sky light',
  renderer: 'three.js 0.185.1, headless Chromium (SwiftShader): frame times are a software-GL reading, comparable only with each other',
  page_errors: errors,
  readings,
  textures,
  library_web_bytes: textures.reduce((a, t) => a + t.web_bytes_total, 0),
  library_gpu_bytes_rgba_with_mips: textures.reduce((a, t) => a + t.gpu_bytes_rgba_with_mips, 0),
};
await writeFile(path.join(OUT, 'browser-validation.json'), JSON.stringify(report, null, 2) + '\n');
console.log(`${readings.length} captures, ${errors.length} page error(s); library web ${(report.library_web_bytes / 1048576).toFixed(2)} MiB`);
if (errors.length) { for (const e of errors) console.error('PAGEERROR', e); process.exit(1); }

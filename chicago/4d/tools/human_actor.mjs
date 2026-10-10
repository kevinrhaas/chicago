#!/usr/bin/env node
/**
 * human_actor.mjs — T-1788. THE BROWSER HUMAN ACTOR, PROVED IN THE BROWSER.
 *
 *   node tools/human_actor.mjs     the actor harness, at 1280x800 and 390x780
 *
 * Serves chicago/4d on a loopback port and opens tools/human_actor.html (never published),
 * which drives renderers/web/js/humans.js with the CI fixture on a sloped heightfield beside
 * a real building GLB: load by person id, a safe clone, feet on the terrain, the § 2
 * heading, idle / walk / a library gesture, morphs and the LOD that has none, LOD by distance
 * and by detail tier with hysteresis, what a far figure is spared (face, shadow, mixer, and
 * beyond DRAW_M every per-frame update), pick / select / hover / approach / leave and the
 * resident-card `open`, disposal back to the renderer's memory baseline, and the scene
 * path's refusals (no layer, withheld, L1, unknown person, review, one person twice).
 *
 * The other half of the scene-year gate is the walkthrough's own: tools/smoke_renderer.mjs
 * holds every scene it boots to a mounted, empty human layer and no request under humans/.
 * It is not booted here because the source tree is not the town — the smoke boots the
 * published mirror, which has the baked GLBs this tree does not.
 *
 * Every check passes at both viewports with no page error and no console error, or the
 * command exits 1. Frame times are SwiftShader's: a reading, not a phone's frame rate.
 * Run by .github/workflows/chicago-4d-humans.yml beside human_fixture.mjs.
 */
import { createServer } from 'node:http';
import { execSync } from 'node:child_process';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.glb': 'model/gltf-binary', '.wasm': 'application/wasm', '.bin': 'application/octet-stream',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const server = createServer(async (req, res) => {
  const p = path.join(ROOT, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  if (!p.startsWith(ROOT)) { res.writeHead(403).end(); return; }
  try {
    const body = await readFile(p);
    res.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream' });
    res.end(body);
  } catch { res.writeHead(404).end(); }
});
await new Promise((ok) => server.listen(0, '127.0.0.1', ok));
const origin = `http://127.0.0.1:${server.address().port}`;

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
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
const viewports = { desktop: { width: 1280, height: 800 }, mobile: { width: 390, height: 780 } };

let failed = 0;
const say = (ok, line) => { if (!ok) failed++; console.log(`${ok ? 'ok  ' : 'FAIL'} ${line}`); };

try {
  for (const [vp, size] of Object.entries(viewports)) {
    const page = await browser.newPage({ viewport: size });
    const errors = [];
    page.on('pageerror', (e) => errors.push(`pageerror ${e.message}`));
    page.on('console', (m) => { if (m.type() === 'error') errors.push(`console.error ${m.text()}`); });
    const t0 = Date.now();
    await page.goto(`${origin}/tools/human_actor.html`);
    await page.waitForFunction(() => window.__actor?.ready, null, { timeout: 180000 })
      .catch((e) => errors.push(`never ready (${e.message.split('\n')[0]})`));
    const run = (await page.evaluate(() => window.__actor)) || { results: [] };
    await page.close();
    for (const e of errors) say(false, `${vp}: ${e}`);
    if (run.error) say(false, `${vp}: the harness threw — ${run.error}`);
    for (const r of run.results) say(r.ok, `${vp}: ${r.check}${r.ok ? '' : `\n       got ${r.got}`}`);
    say(run.results.length >= 30, `${vp}: ${run.results.length} actor checks ran in ${((Date.now() - t0) / 1000).toFixed(1)} s; `
      + `one near figure, update + render, median ${run.frame_ms_median} ms`);
  }
} finally {
  await browser.close();
  server.close();
}
console.log(failed ? `\n${failed} finding(s)` : '\nhuman actor: OK');
process.exit(failed ? 1 : 0);

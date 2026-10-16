#!/usr/bin/env node
/**
 * WHAT THE BOOT HOLDS AT ONCE, AND WHAT BOUNDING IT COSTS (T-2597).
 *
 *   node tools/measure_boot_peak.mjs [--year 1835,1904] [--only desktop|mobile|both]
 *        [--pools 0,8,24] [--latency 60] [--json out.json]
 *
 * `loadScene` starts every structure's sidecar + GLB at once by default; `?boot-pool=N`
 * runs them N at a time (`BOOT_POOL` in renderers/web/js/scene-loader.js, where the
 * reading that kept the default unbounded is written), and `?boot-pool=0` names the
 * default, so any pool is read against today in the same build. Per year × viewport ×
 * pool, from the published mirror (bash tools/publish.sh first):
 *
 *   held peak ..... the loader's own count (`__chicago4d.bootPool`): the most GLB
 *                   bytes, and files, fetched and not yet parsed at one moment. Exact.
 *   buffers peak .. `Runtime.getHeapUsage().backingStorageSize` — every live
 *                   ArrayBuffer in the tab — sampled every 25 ms from navigation to
 *                   `ready`, no GC forced; printed twice, for the scene phase (until
 *                   `loadScene` returns, which is all the pool governs) and the boot. SAMPLED: the reply waits on the page's main
 *                   thread, so a long parse is read either side of, not inside; it is
 *                   a floor on the true peak and is printed as one.
 *   boot .......... navigation to `ready`, with every request delayed by `--latency`
 *                   ms (CDP network emulation; default 60, a fair phone round trip).
 *                   Headless Chromium draws through SwiftShader, so the CPU half of
 *                   this is the runner's, not a phone's: compare pools to each other,
 *                   never to a device.
 *
 * SERVED OVER HTTP/2 on purpose. The live host speaks HTTP/2, where the browser puts
 * every request on one connection with no per-host cap; over HTTP/1.1 Chromium allows
 * six sockets per host, so an "unbounded" load would already be a pool of six at the
 * network and the latency the pool adds would read as nothing. A throwaway self-signed
 * certificate is made with `openssl` and the context ignores it.
 */
import http2 from 'node:http2';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execSync, execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '../../../site/4d');
const argAt = (name) => {
  const i = process.argv.indexOf(name);
  return i >= 0 ? process.argv[i + 1] : null;
};
const YEARS = (argAt('--year') || '1835,1904').split(',').filter(Boolean);
const ONLY = argAt('--only') || 'both';
const POOLS = (argAt('--pools') || '0,8,24').split(',').map(Number);
const LATENCY = Number(argAt('--latency') ?? 60);
const jsonOut = argAt('--json');
const MB = (b) => (b / 1048576).toFixed(1);

const VIEWPORTS = [
  { id: 'desktop', width: 1280, height: 800, dsf: 1, mobile: false },
  { id: 'mobile', width: 390, height: 780, dsf: 3, mobile: true },
].filter((v) => ONLY === 'both' || v.id === ONLY);

if (!fs.existsSync(path.join(ROOT, '1835', 'index.html'))) {
  console.error(`no published mirror at ${ROOT} — run tools/publish.sh first`);
  process.exit(2);
}

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

const certDir = fs.mkdtempSync(path.join(os.tmpdir(), 'boot-peak-'));
execFileSync('openssl', ['req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
  '-subj', '/CN=127.0.0.1', '-keyout', path.join(certDir, 'key.pem'),
  '-out', path.join(certDir, 'cert.pem')], { stdio: 'ignore' });
const TYPES = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.webp': 'image/webp', '.svg': 'image/svg+xml', '.wasm': 'application/wasm',
  '.woff2': 'font/woff2', '.ktx2': 'image/ktx2',
};
const server = http2.createSecureServer({
  key: fs.readFileSync(path.join(certDir, 'key.pem')),
  cert: fs.readFileSync(path.join(certDir, 'cert.pem')),
  allowHTTP1: true,
}, (req, res) => {
  const url = decodeURIComponent(req.url.split('?')[0]);
  let file = path.join(ROOT, url);
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
  if (!file.startsWith(ROOT) || !fs.existsSync(file)) {
    res.writeHead(404, { 'content-type': 'text/plain' });
    res.end(`not found: ${url}`);
    return;
  }
  res.writeHead(200, { 'content-type': TYPES[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const PORT = server.address().port;

const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
const rows = [];
try {
  for (const year of YEARS) {
    for (const vp of VIEWPORTS) {
      for (const pool of POOLS) {
        const ctx = await browser.newContext({
          viewport: { width: vp.width, height: vp.height }, ignoreHTTPSErrors: true,
          deviceScaleFactor: vp.dsf, isMobile: vp.mobile, hasTouch: vp.mobile,
        });
        const page = await ctx.newPage();
        const errors = [];
        page.on('pageerror', (e) => errors.push(String(e)));
        const cdp = await ctx.newCDPSession(page);
        await cdp.send('Network.enable');
        await cdp.send('Network.emulateNetworkConditions', {
          offline: false, latency: LATENCY, downloadThroughput: -1, uploadThroughput: -1,
        });
        let peakBuffers = 0;
        let peakScene = 0;
        let samples = 0;
        let sampling = true;
        const sampler = (async () => {
          while (sampling) {
            try {
              const h = await cdp.send('Runtime.getHeapUsage');
              const b = h.backingStorageSize ?? 0;
              peakBuffers = Math.max(peakBuffers, b);
              // `api.scene` is set the moment loadScene returns: until then this is
              // the scene phase, the one the pool governs.
              const inScene = await page.evaluate(() => !window.__chicago4d?.scene);
              if (inScene) peakScene = Math.max(peakScene, b);
              samples += 1;
            } catch { /* navigating */ }
            await new Promise((r) => { setTimeout(r, 25); });
          }
        })();
        const t0 = Date.now();
        await page.goto(`https://127.0.0.1:${PORT}/${year}/?boot-pool=${pool}`, { waitUntil: 'load' });
        await page.waitForFunction(() => window.__chicago4d?.ready === true || window.__chicago4d?.error,
          null, { timeout: 420_000, polling: 100 });
        const bootMs = Date.now() - t0;
        sampling = false;
        await sampler;
        const got = await page.evaluate(() => ({ pool: window.__chicago4d.bootPool,
          error: window.__chicago4d.error ? String(window.__chicago4d.error) : null,
          structures: window.__chicago4d.registry?.size ?? 0 }));
        const row = { year, viewport: vp.id, pool, latencyMs: LATENCY, bootMs,
          structures: got.structures, held: got.pool, peakScene, peakBuffers, samples,
          errors: [...errors, ...(got.error ? [got.error] : [])] };
        rows.push(row);
        console.log(`/${year}/ ${vp.id.padEnd(7)} pool ${String(pool || '∞').padStart(2)}`
          + `  held peak ${MB(row.held?.peakBytes ?? 0).padStart(6)} MB in ${String(row.held?.peakAssets ?? 0).padStart(3)} GLBs`
          + `  · buffers ≥ ${MB(peakScene).padStart(6)} MB in scene, ≥ ${MB(peakBuffers).padStart(6)} MB boot (${samples} samples)`
          + `  · boot ${(bootMs / 1000).toFixed(1)} s at ${LATENCY} ms`
          + `  · ${row.structures} structures${row.errors.length ? `  · ${row.errors.length} ERRORS: ${row.errors[0]}` : ''}`);
        await ctx.close();
      }
    }
  }
} finally {
  await browser.close();
  server.close();
  fs.rmSync(certDir, { recursive: true, force: true });
}
if (jsonOut) fs.writeFileSync(jsonOut, `${JSON.stringify({ measured: new Date().toISOString(), rows }, null, 2)}\n`);
process.exit(rows.some((r) => r.errors.length) ? 1 : 0);

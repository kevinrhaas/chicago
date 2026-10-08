#!/usr/bin/env node
/**
 * T-2164 — the bytes each boot phase downloads, for the arrival clock's first visit.
 *
 *   node tools/measure_boot_bytes.mjs           measure all six device/detail cells, print
 *   node tools/measure_boot_bytes.mjs --write   ...and rewrite renderers/web/js/boot-bytes.js
 *
 * The arrival forecast (boot-forecast.js) times each phase as `cpu × pace + bytes / link`.
 * After one visit it uses the bytes that build actually downloaded; this is the figure
 * a FIRST visit forecasts from. It is read from the app's own meter (decoded bytes from
 * Resource Timing, attributed to the essential phase running when each request
 * finished), in a fresh context against the published mirror (bash tools/publish.sh).
 * Bytes do not depend on the machine, so unlike boot-weights.js this needs no
 * reference hardware — only a current mirror. Rerun it when the payload moves a lot;
 * a stale figure only costs the first visit's accuracy, never correctness.
 *
 * WIRE BYTES: the live origin gzips everything (measure_boot_payload.mjs, checked
 * 2026-09-16), and the meter reads `encodedBodySize`, so this origin gzips too.
 */
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import zlib from 'node:zlib';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(here, '../renderers/web/js/boot-bytes.js');
const PHASES = ['scene', 'terrain', 'buildings', 'ground', 'flora', 'interaction'];
const ROOT = path.resolve(here, '../../../site/4d');
const TYPES = { '.js': 'text/javascript', '.json': 'application/json', '.html': 'text/html',
  '.css': 'text/css', '.wasm': 'application/wasm', '.webp': 'image/webp', '.woff2': 'font/woff2' };
async function environment() {
  let pw;
  try { pw = await import('playwright'); } catch {
    pw = await import(path.join(execSync('npm root -g', { encoding: 'utf8' }).trim(), 'playwright/index.mjs'));
  }
  const server = http.createServer((q, r) => {
    let p = path.resolve(ROOT, '.' + decodeURIComponent(q.url.split('?')[0]));
    if (!p.startsWith(ROOT + path.sep) && p !== ROOT) { r.writeHead(403); r.end(); return; }
    if (q.url.split('?')[0].endsWith('/')) p += '/index.html';
    fs.readFile(p, (err, data) => {
      if (err) { r.writeHead(404); r.end(); return; }
      zlib.gzip(data, (gerr, gz) => {
        r.writeHead(200, { 'content-type': TYPES[path.extname(p)] || 'application/octet-stream',
          'content-encoding': 'gzip', 'content-length': gz.length });
        r.end(gz);
      });
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await pw.chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
  return { browser, url: `http://127.0.0.1:${server.address().port}/walk/?year=1835`,
    async close() { await browser.close(); await new Promise(resolve => server.close(resolve)); } };
}
const env = await environment();
const result = { mobile: {}, desktop: {} };
try {
  for (const device of ['mobile', 'desktop']) for (const detail of ['light', 'balanced', 'full']) {
    const ctx = await env.browser.newContext(device === 'mobile'
      ? { viewport: { width: 390, height: 780 }, hasTouch: true, isMobile: true, deviceScaleFactor: 2 }
      : { viewport: { width: 1280, height: 800 } });
    await ctx.addInitScript(d => localStorage.setItem('chicago4d.settings', JSON.stringify({ detail: d })), detail);
    const page = await ctx.newPage();
    await page.goto(env.url);
    await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 600000 });
    const got = await page.evaluate(() => ({ error: window.__chicago4d.error,
      bytes: window.__chicago4d.boot.forecast?.phaseBytes, cell: window.__chicago4d.boot.forecast && 1 }));
    await ctx.close();
    if (got.error || !got.bytes) throw new Error(`${device}/${detail}: ${got.error || 'no forecast on the boot'}`);
    result[device][detail] = Object.fromEntries(PHASES.map(id => [id, Math.round(got.bytes[id] || 0)]));
    const total = Object.values(result[device][detail]).reduce((s, n) => s + n, 0);
    console.log(`${device}/${detail}`.padEnd(18), (total / 1e6).toFixed(2).padStart(6), 'MB ',
      PHASES.map(id => `${id} ${(result[device][detail][id] / 1e6).toFixed(2)}`).join('  '));
  }
} finally { await env.close(); }
if (process.argv.includes('--write')) {
  fs.writeFileSync(OUT, `// T-2164 measured ${new Date().toISOString()} by tools/measure_boot_bytes.mjs\n`
    + '// Wire (gzip) bytes each essential boot phase downloads on a first visit, from the app\'s own\n'
    + '// Resource Timing meter, fresh context, published mirror. Bytes, not seconds: the\n'
    + '// arrival forecast divides them by the link it measures (boot-forecast.js).\n'
    + `export const BOOT_BYTES = ${JSON.stringify(result, null, 2)};\n`);
  console.log(`wrote ${path.relative(process.cwd(), OUT)}`);
}

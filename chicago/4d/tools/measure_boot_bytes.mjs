#!/usr/bin/env node
/**
 * T-2164 — the bytes each boot phase downloads, for the arrival clock's first visit.
 *
 *   node tools/measure_boot_bytes.mjs           measure every year × device × detail cell, print
 *   node tools/measure_boot_bytes.mjs --write   ...and rewrite renderers/web/js/boot-bytes.js
 *   --origin https://dev.chicago.polecat.live/4d/dev/   measure the published site instead of a
 *                                                local mirror (it gzips as the live origin does)
 *   --years 1835,1904   only these years      --parallel 3   cells measured at once
 *
 * Each year downloads a different town (T-3758: one table for all four had the 1904 loading
 * screen forecast 15 MB and then climb to 86 MB), so the table is keyed year › device › detail.
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
const arg = (name, fallback) => { const i = process.argv.indexOf(name); return i > 0 ? process.argv[i + 1] : fallback; };
const YEARS = arg('--years', '1812,1835,1871,1904').split(',');
const ORIGIN = arg('--origin', null);
const PARALLEL = Math.max(1, Number(arg('--parallel', 3)) || 3);
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
  const proxy = ORIGIN && process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
  if (!ORIGIN) await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const browser = await pw.chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, proxy });
  const site = ORIGIN ? ORIGIN.replace(/\/?$/, '/') : `http://127.0.0.1:${server.address().port}/`;
  return { browser, url: (year) => `${site}walk/?year=${year}`, ignoreHTTPSErrors: !!proxy,
    async close() { await browser.close(); if (!ORIGIN) await new Promise(resolve => server.close(resolve)); } };
}
const env = await environment();
const result = {};
const cells = [];
for (const year of YEARS) for (const device of ['mobile', 'desktop']) for (const detail of ['light', 'balanced', 'full']) cells.push({ year, device, detail });
async function measure({ year, device, detail }) {
  const ctx = await env.browser.newContext({ ignoreHTTPSErrors: env.ignoreHTTPSErrors, ...(device === 'mobile'
    ? { viewport: { width: 390, height: 780 }, hasTouch: true, isMobile: true, deviceScaleFactor: 2 }
    : { viewport: { width: 1280, height: 800 } }) });
  try {
    await ctx.addInitScript(d => localStorage.setItem('chicago4d.settings', JSON.stringify({ detail: d })), detail);
    const page = await ctx.newPage();
    await page.goto(env.url(year));
    // Every essential phase over: the bytes are counted (the first frame can take a while longer).
    await page.waitForFunction(() => window.__chicago4d?.error || window.__chicago4d?.boot?.phases?.every(p => !p.essential || p.endedAt != null),
      null, { timeout: 900000 });
    const got = await page.evaluate(() => ({ error: window.__chicago4d.error,
      bytes: window.__chicago4d.boot.forecast?.phaseBytes }));
    if (got.error || !got.bytes) throw new Error(`${year} ${device}/${detail}: ${got.error || 'no forecast on the boot'}`);
    const row = Object.fromEntries(PHASES.map(id => [id, Math.round(got.bytes[id] || 0)]));
    ((result[year] ??= {})[device] ??= {})[detail] = row;
    const total = Object.values(row).reduce((s, n) => s + n, 0);
    console.log(`${year} ${device}/${detail}`.padEnd(22), (total / 1e6).toFixed(2).padStart(6), 'MB ',
      PHASES.map(id => `${id} ${(row[id] / 1e6).toFixed(2)}`).join('  '));
  } finally { await ctx.close(); }
}
try {
  const queue = cells.slice();
  await Promise.all(Array.from({ length: PARALLEL }, async () => { while (queue.length) await measure(queue.shift()); }));
} finally { await env.close(); }
// Same key order whatever finished first, so a rerun diffs cleanly.
const ordered = Object.fromEntries(YEARS.map(y => [y, Object.fromEntries(['mobile', 'desktop'].map(d =>
  [d, Object.fromEntries(['light', 'balanced', 'full'].map(q => [q, result[y][d][q]]))]))]));
if (process.argv.includes('--write')) {
  fs.writeFileSync(OUT, `// T-2164 measured ${new Date().toISOString()} by tools/measure_boot_bytes.mjs\n`
    + '// Wire (gzip) bytes each essential boot phase downloads on a first visit, from the app\'s own\n'
    + `// Resource Timing meter, fresh context, ${ORIGIN ? ORIGIN : 'published mirror'}. Bytes, not seconds: the\n`
    + '// arrival forecast divides them by the link it measures (boot-forecast.js). Keyed\n'
    + '// year › device › detail: each year is a different town (T-3758).\n'
    + `export const BOOT_BYTES = ${JSON.stringify(ordered, null, 2)};\n`);
  console.log(`wrote ${path.relative(process.cwd(), OUT)}`);
}

#!/usr/bin/env node
// measure_boot_payload.mjs — T-0727: the bytes a first-time visitor actually
// downloads to stand in the 1835 street.
//
//   node tools/measure_boot_payload.mjs            measure; print a report
//   node tools/measure_boot_payload.mjs --json     print the machine reading
//   node tools/measure_boot_payload.mjs --check    exit 1 if over the budget in docs/SITE-BUDGET.md §4
//
// WHY THIS EXISTS (T-0722 / T-0727): the 32 MB whole-tree budget is this
// project's own number and a poor proxy for the thing a size budget is for.
// A visitor never downloads the tree — they download the walkthrough's boot
// payload. The 1,385 household cards are 28 % of the tree and cost a first-time
// visitor nothing until one is opened; a careless import into walk/js/ costs
// every visitor immediately and moves the total barely at all. So the real
// number is measured HERE, from real responses, and budgeted tightly — and the
// whole-tree cap relaxes into the repository-hygiene guard it actually is
// (docs/SITE-BUDGET.md §4).
//
// THE MEASUREMENT, and why each choice is made:
//   * REAL RESPONSES, not a file list: a static server hands the published
//     mirror (site/chicago/4d, built by tools/publish.sh) to a real headless
//     Chromium, and every byte the server writes is counted per request. What
//     the browser ACTUALLY asked for, byte for byte — the smoke's own layout.
//   * GZIP ON EVERYTHING: the live origin (checked 2026-09-16) answers
//     content-encoding: gzip for .js, .json, .html AND .glb alike. The budget
//     is wire bytes, so this server compresses every response the same way.
//   * FIRST-TIME VISITOR: a fresh browser context — no cache, no cookies, no
//     service worker.
//   * "STANDS IN THE STREET" = the app's own ready flag: window.__chicago4d.ready
//     === true (the same signal tools/smoke_renderer.mjs gates on), plus a 3 s
//     settle for the immediate surroundings that stream in right behind it.
//   * --check re-runs the measurement and refuses past the §4 budget, so the
//     number cannot drift silently between measurements.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SITE = path.resolve(HERE, '../../../site/chicago/4d');
const SETTLE_MS = 3000;

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

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8',
  '.mjs': 'application/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.glb': 'model/gltf-binary',
  '.bin': 'application/octet-stream', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.md': 'text/markdown; charset=utf-8',
  '.geojson': 'application/json; charset=utf-8', '.sha256': 'text/plain; charset=utf-8',
};

function serve(root) {
  const bytes = new Map(); // url -> {bytes, status, type}
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent((req.url || '/').split('?')[0]);
    let p = path.join(root, url.endsWith('/') ? url + 'index.html' : url);
    if (!p.startsWith(root)) { res.writeHead(403); res.end(); return; }
    fs.readFile(p, (err, data) => {
      if (err) {
        bytes.set(url, { bytes: 0, status: 404, type: '' });
        res.writeHead(404); res.end('not found'); return;
      }
      const type = TYPES[path.extname(p).toLowerCase()] || 'application/octet-stream';
      // GitHub Pages gzips everything it serves from this site (verified
      // against the live origin, 2026-09-16, .js/.json/.glb/.html alike) — the
      // budget is wire bytes, so the local origin does the same.
      zlib.gzip(data, (gerr, gz) => {
        if (gerr) { res.writeHead(500); res.end(); return; }
        bytes.set(url, { bytes: gz.length, status: 200, type });
        res.writeHead(200, { 'content-type': type, 'content-encoding': 'gzip', 'content-length': gz.length });
        res.end(gz);
      });
    });
  });
  return { server, bytes };
}

async function measure() {
  if (!fs.existsSync(path.join(SITE, 'walk/index.html'))) {
    console.error(`published mirror not found at ${SITE} — run tools/publish.sh first`);
    process.exit(2);
  }
  const { chromium } = await loadPlaywright();
  const { server, bytes } = serve(SITE);
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const browser = await chromium.launch({
    // T-0153: every Playwright tool must be pointable at a browser — the gate
    // asserts this line exists in any tool that calls chromium.launch().
    executablePath: process.env.PW_EXECUTABLE || undefined,
  });
  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    const failures = [];
    page.on('requestfailed', (r) => failures.push(`${r.url()} ${r.failure()?.errorText}`));
    page.on('response', (r) => { if (r.status() >= 400) failures.push(`${r.url()} HTTP ${r.status()}`); });
    await page.goto(`http://127.0.0.1:${port}/walk/?year=1835`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.__chicago4d?.ready === true, null, { timeout: 90000 });
    await page.waitForTimeout(SETTLE_MS);
    const entries = [...bytes.entries()].map(([url, b]) => ({ url, ...b }));
    const total = entries.filter((e) => e.status === 200).reduce((s, e) => s + e.bytes, 0);
    return { total, requests: entries.length, entries, failures, settleMs: SETTLE_MS };
  } finally {
    await browser.close();
    server.close();
  }
}

const fmt = (n) => `${(n / 1048576).toFixed(3)} MB`;

function report(m) {
  const byExt = {};
  for (const e of m.entries) {
    if (e.status !== 200) continue;
    const ext = (e.url.match(/\.([a-z0-9]+)$/)?.[1] || '(none)');
    byExt[ext] = (byExt[ext] || 0) + e.bytes;
  }
  console.log(`BOOT PAYLOAD — first visit stands in the 1835 street`);
  console.log(`  ${fmt(m.total)} across ${m.requests} request(s) (gzip on the wire, fresh context, ready + ${m.settleMs / 1000}s settle)`);
  console.log('');
  console.log('BY TYPE');
  for (const [ext, b] of Object.entries(byExt).sort((a, b) => b[1] - a[1])) {
    console.log(`  ${fmt(b)}  .${ext}`);
  }
  console.log('');
  console.log('THE 15 LARGEST');
  for (const e of [...m.entries].filter((e) => e.status === 200).sort((a, b) => b.bytes - a.bytes).slice(0, 15)) {
    console.log(`  ${fmt(e.bytes)}  ${e.url}`);
  }
  if (m.failures.length) {
    console.log('');
    console.log(`FAILED REQUESTS: ${m.failures.length}`);
    for (const f of m.failures.slice(0, 10)) console.log(`  ${f}`);
  }
}

async function main() {
  const m = await measure();
  if (process.argv.includes('--json')) {
    console.log(JSON.stringify({
      measured_at: new Date().toISOString(),
      total_bytes: m.total,
      requests: m.requests,
      settle_ms: m.settleMs,
      by_ext: Object.fromEntries(Object.entries(
        m.entries.filter((e) => e.status === 200).reduce((a, e) => {
          const ext = (e.url.match(/\.([a-z0-9]+)$/)?.[1] || '(none)');
          a[ext] = (a[ext] || 0) + e.bytes; return a;
        }, {})).sort((a, b) => b[1] - a[1])),
      largest: m.entries.filter((e) => e.status === 200).sort((a, b) => b.bytes - a.bytes).slice(0, 15),
      failures: m.failures,
    }, null, 2));
  } else {
    report(m);
  }
  if (process.argv.includes('--check')) {
    const doc = fs.readFileSync(path.join(HERE, '../docs/SITE-BUDGET.md'), 'utf8');
    const b = doc.match(/boot payload budget[^0-9]*([0-9]+(?:\.[0-9]+)?)\s*MB/i);
    if (!b) { console.error('no boot payload budget found in docs/SITE-BUDGET.md §4'); process.exit(2); }
    const budget = Number(b[1]) * 1048576;
    if (m.total > budget) {
      console.error(`BOOT PAYLOAD OVER BUDGET: ${fmt(m.total)} > ${fmt(budget)} (docs/SITE-BUDGET.md §4) — what every visitor downloads grew past the number this project chose.`);
      process.exit(1);
    }
    console.log(`within budget: ${fmt(m.total)} of ${fmt(budget)}`);
  }
}

main().catch((e) => { console.error(e.message); process.exit(2); });

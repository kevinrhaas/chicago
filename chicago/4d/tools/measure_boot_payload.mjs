#!/usr/bin/env node
// measure_boot_payload.mjs — T-0727: the bytes a first-time visitor actually
// downloads to stand in the 1835 street.
//
//   node tools/measure_boot_payload.mjs            measure; print a report
//   node tools/measure_boot_payload.mjs --json     print the machine reading
//   node tools/measure_boot_payload.mjs --check    exit 1 if over the budget in docs/SITE-BUDGET.md §4
//   node tools/measure_boot_payload.mjs --entries F  also write every request (url, bytes) to F
//   node tools/measure_boot_payload.mjs --against F  print what grew, shrank, arrived and left since F
//
// T-3300: the report names the 15 largest files, and a breach is rarely one of
// them — 2026-11-01's 5.3 MB over budget was the prebuilt layers drifting up a
// little each and a dozen new boot files, none in the top 15 alone. --entries
// keeps a reading whole, and --against answers "what grew since then" by URL.
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
//     mirror (site/4d, built by tools/publish.sh) to a real headless
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
const SITE = path.resolve(HERE, '../../../site/4d');
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
    // T-2693's before: the ground prebuild refused, so the page fetches and cuts
    // the ground GLB itself, as dev did. Refused here, so never counted or failed.
    if (process.argv.includes('--no-prebuilt-ground')) {
      await context.route('**/data/prebuilt/*/ground.*', (route) => route.fulfill({ status: 404, body: '' }));
    }
    // T-2709's before: the distant base's prebuild refused, so the page lays and cuts its own.
    if (process.argv.includes('--no-prebuilt-base')) {
      await context.route('**/data/prebuilt/*/base.*', (route) => route.fulfill({ status: 404, body: '' }));
    }
    // T-2710's before: the streets prebuild refused, so the page lays its own road.
    if (process.argv.includes('--no-prebuilt-streets')) {
      await context.route('**/data/prebuilt/*/streets.*', (route) => route.fulfill({ status: 404, body: '' }));
    }
    // T-2711's before, the same way: the yards refused, so the page lays its own.
    if (process.argv.includes('--no-prebuilt-yards')) {
      await context.route('**/data/prebuilt/*/yards.*', (route) => route.fulfill({ status: 404, body: '' }));
    }
    const page = await context.newPage();
    const failures = [];
    // A layer refused above is the before being measured, not a failure.
    const refused = (url) => [['--no-prebuilt-ground', 'ground'], ['--no-prebuilt-base', 'base'], ['--no-prebuilt-streets', 'streets'], ['--no-prebuilt-yards', 'yards']]
      .some(([flag, layer]) => process.argv.includes(flag) && new RegExp(`/data/prebuilt/\\d{4}/${layer}\\.`).test(url));
    page.on('requestfailed', (r) => { if (!refused(r.url())) failures.push(`${r.url()} ${r.failure()?.errorText}`); });
    page.on('response', (r) => {
      if (r.status() >= 400 && !refused(r.url())) {
        failures.push(`${r.url()} HTTP ${r.status()}`);
      }
    });
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
  // T-2151: the type split cannot say WHICH records grew — 547 sidecars and a
  // dozen panel files all read as `.json`. The folder split does.
  const byDir = {};
  for (const e of m.entries) {
    if (e.status !== 200) continue;
    const dir = e.url.split('?')[0].split('/').slice(1, -1).slice(0, 3).join('/') || '(root)';
    (byDir[dir] ||= { bytes: 0, n: 0 }).bytes += e.bytes;
    byDir[dir].n += 1;
  }
  console.log('');
  console.log('BY FOLDER (the 15 heaviest)');
  for (const [dir, v] of Object.entries(byDir).sort((a, b) => b[1].bytes - a[1].bytes).slice(0, 15)) {
    console.log(`  ${fmt(v.bytes)}  ${String(v.n).padStart(4)}  /${dir}/`);
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

function argValue(flag) {
  const i = process.argv.indexOf(flag);
  return i > 0 ? process.argv[i + 1] : null;
}

// T-3300: a reading kept whole, and the difference between two of them by URL.
function entriesOf(m) {
  return m.entries.filter((e) => e.status === 200)
    .map((e) => ({ url: e.url.split('?')[0], bytes: e.bytes }))
    .sort((a, b) => b.bytes - a.bytes);
}

function compare(before, after) {
  const sum = (list) => {
    const out = new Map();
    for (const e of list) out.set(e.url, (out.get(e.url) || 0) + e.bytes);
    return out;
  };
  const a = sum(before), b = sum(after);
  const rows = [];
  for (const url of new Set([...a.keys(), ...b.keys()])) {
    const d = (b.get(url) || 0) - (a.get(url) || 0);
    if (d) rows.push({ url, before: a.get(url) || 0, after: b.get(url) || 0, delta: d });
  }
  rows.sort((x, y) => Math.abs(y.delta) - Math.abs(x.delta));
  const tot = (m) => [...m.values()].reduce((s, v) => s + v, 0);
  console.log('');
  console.log(`AGAINST THE EARLIER READING: ${fmt(tot(a))} -> ${fmt(tot(b))} (${tot(b) >= tot(a) ? '+' : ''}${fmt(tot(b) - tot(a))})`);
  const band = (label, pick) => {
    const r = rows.filter(pick);
    if (!r.length) return;
    console.log(`  ${label}: ${r.length} file(s), ${fmt(r.reduce((s, x) => s + x.delta, 0))}`);
    for (const x of r.slice(0, 25)) console.log(`    ${x.delta >= 0 ? '+' : ''}${fmt(x.delta)}  ${x.url}`);
  };
  band('ARRIVED', (x) => !x.before);
  band('GREW', (x) => x.before && x.after && x.delta > 0);
  band('SHRANK', (x) => x.before && x.after && x.delta < 0);
  band('LEFT', (x) => !x.after);
}

async function main() {
  const m = await measure();
  const entriesFile = argValue('--entries');
  if (entriesFile) {
    fs.writeFileSync(entriesFile, JSON.stringify({ total_bytes: m.total, entries: entriesOf(m) }, null, 1) + '\n');
  }
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
  const againstFile = argValue('--against');
  if (againstFile) compare(JSON.parse(fs.readFileSync(againstFile, 'utf8')).entries, entriesOf(m));
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

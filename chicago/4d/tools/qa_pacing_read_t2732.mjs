#!/usr/bin/env node
// T-2732: Read frame pacing pressed in the real app, at 390x780 on the published mirror.
//
//   node tools/qa_pacing_read_t2732.mjs [--seconds 2]
//
// What it shows: `?pacing=read` shows the button (production without it is
// tools/test_pacing_read.mjs's rule, not a second boot here); pressing it closes the panel, drives the six readings, writes the copyable text,
// reopens Settings, and puts back the visitor's detail, pacing, place and flight — with
// zero page errors. The NUMBERS this runner prints are SwiftShader's (a frame every
// second or so, T-2721) and are not the governor's reading; T-2733 takes that on a phone.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';

const root = process.cwd();
const require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const site = path.resolve(root, '../../site/4d');
const at = process.argv.indexOf('--seconds');
const SECONDS = at > 0 ? Number(process.argv[at + 1]) : 4;

const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary',
  '.svg': 'image/svg+xml', '.ktx2': 'image/ktx2', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  let p = path.join(site, decodeURIComponent(req.url.split('?')[0]));
  try {
    if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
    res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
const context = await browser.newContext({ viewport: { width: 390, height: 780 }, deviceScaleFactor: 1,
  isMobile: true, hasTouch: true });
const errors = [];
const fail = [];
const check = (ok, what) => { console.log(`${ok ? 'ok  ' : 'FAIL'} ${what}`); if (!ok) fail.push(what); };

async function boot(url) {
  const page = await context.newPage();
  page.setDefaultTimeout(240_000);
  page.on('pageerror', (e) => errors.push(`${url}: ${e}`));
  await page.goto(`${base}${url}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null,
    { timeout: 240_000, polling: 500 });
  return page;
}

try {
  const page = await boot('/walk/?pacing=read');
  await page.waitForFunction(() => window.__chicago4d.welcome.state === 'welcome', null,
    { timeout: 240_000, polling: 1000 });
  const shown = await page.evaluate(() => !document.getElementById('pacing-read').hidden
    && !!window.__chicago4d.pacingRead);
  check(shown, '?pacing=read shows the row under Settings → Performance');

  // A visitor who had chosen Fixed and Balanced, standing somewhere of their own.
  const before = await page.evaluate(async () => {
    const a = window.__chicago4d;
    a.welcome.enter('spawn');
    document.exitPointerLock?.();
    document.getElementById('control-help-gotit')?.click();
    await a.setDetail('balanced');
    a.setGovernor(false);
    a.setFly(false);
    a.walker.teleport({ local_e: a.player.e + 7, local_n: a.player.n - 5, yaw_deg: 33 });
    await new Promise((r) => setTimeout(r, 400));
    const p = a.player;
    return { detail: a.detail, mode: a.governor.mode, e: p.e, n: p.n, bearing: p.bearingDeg, flying: p.flying };
  });
  // Shorten the drive for the runner: READ_SECONDS is for a phone.
  const t0 = Date.now();
  await page.evaluate((seconds) => { window.__chicago4d.pacingRead.seconds = seconds; }, SECONDS);
  // The button itself: closes the panel, writes the box, reopens Settings with Copy.
  const viaButton = await page.evaluate(async () => {
    const a = window.__chicago4d;
    a.hud.setPanel(true);
    a.hud.selectTab?.('settings');
    const btn = document.getElementById('s-pacing-read');
    btn.click();
    const closed = document.getElementById('panel')?.hidden ?? null;
    const deadline = Date.now() + 400_000;
    while (a.pacingRead.running && Date.now() < deadline) await new Promise((r) => setTimeout(r, 500));
    const out = document.getElementById('pacing-read-out');
    return { closed, reopened: !document.getElementById('panel')?.hidden, outShown: !out.hidden,
      steps: a.pacingRead.result ? Object.keys(a.pacingRead.result.pairs) : [],
      draws: a.pacingRead.result ? Object.values(a.pacingRead.result.pairs).flatMap((p) => [p.fixed.draws, p.adaptive.draws]) : [],
      text: out.value, copyShown: !document.getElementById('s-pacing-copy').hidden,
      status: document.getElementById('pacing-read-status').textContent.trim() };
  });
  check(viaButton.closed === true, 'pressing Read frame pacing closes the panel for the reading');
  check(viaButton.reopened && viaButton.outShown && viaButton.copyShown, `Settings reopens with the result and Copy (${viaButton.status})`);
  console.log(`\n${viaButton.text}\n`);
  check(viaButton.steps.join() === 'walk,turn,flight' && viaButton.draws.length === 6 && viaButton.draws.every((d) => d >= 1),
    `walk, turn and flight each drawn at Fixed and Adaptive (draws ${viaButton.draws.join(', ')})`);
  check(/^Read frame pacing \(T-2733\)/.test(viaButton.text)
    && (viaButton.text.match(/^ {2}(FELL|DID NOT FALL|TOO FEW FRAMES TO SAY):/gm) ?? []).length === 3,
    'the box holds the reading, a verdict per move');
  await page.screenshot({ path: '/tmp/qa-pacing-read-t2732.png' });

  const after = await page.evaluate(() => {
    const a = window.__chicago4d;
    const p = a.player;
    return { detail: a.detail, mode: a.governor.mode, e: p.e, n: p.n, bearing: p.bearingDeg, flying: p.flying };
  });
  check(after.detail === before.detail && after.mode === before.mode && after.flying === before.flying,
    `detail, pacing and flight restored (${JSON.stringify(after)})`);
  check(Math.hypot(after.e - before.e, after.n - before.n) < 0.5 && Math.abs(after.bearing - before.bearing) < 1,
    'the visitor stands where they stood');
  console.log(`drive took ${((Date.now() - t0) / 1000).toFixed(0)} s on this runner`);
} finally {
  await browser.close();
  server.close();
}
check(errors.length === 0, `zero page errors${errors.length ? `: ${errors.join(' | ')}` : ''}`);
console.log(fail.length ? `\nFAIL — ${fail.length} check(s)` : '\nPASS — Read frame pacing drives, reports and restores (T-2732)');
process.exit(fail.length ? 1 : 0);

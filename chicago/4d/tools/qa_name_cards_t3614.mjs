#!/usr/bin/env node
// T-3614 — the owner, 2026-11-16: "an option setting that is default on that puts a small 3d
// hovering card floating over each person of what their name is, clicking on the card brings up
// their detail, make sure the names fit and follow the style of the app", "For all years jaunt
// people and time". Boots the app from the source tree (QA_SCENE: 1812, 1835 or 1904), stands
// QA_DIST metres from the nearest named person drawn, and takes pictures with the cards off
// (before) and on in each appearance (QA_SKINS), at QA_TIMES; then clicks (or taps) the nearest
// card and checks that person's card opened. A JSON report beside the pictures.
//   QA_SCENE=1812 node tools/qa_name_cards_t3614.mjs          (phone, 390 x 780)
//   QA_DESKTOP=1 QA_OUT=/tmp/x QA_TIMES=daytime,night ...
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { createRequire } from 'node:module';
const root = process.cwd(), require = createRequire(path.join(root, 'tools/qa.mjs'));
const { chromium } = require('playwright');
const out = process.env.QA_OUT || path.join(os.tmpdir(), 'name-cards-3614');
fs.mkdirSync(out, { recursive: true });
const SCENE = process.env.QA_SCENE || '1812';
const desktop = !!process.env.QA_DESKTOP, BOOT_MS = Number(process.env.QA_BOOT_MS) || 1500000;
const SKINS = (process.env.QA_SKINS || 'control-room,brass,worlds-fair,deep-space').split(',').filter(Boolean);
const TIMES = (process.env.QA_TIMES || 'daytime').split(',').filter(Boolean);
const DIST = Number(process.env.QA_DIST) || 7;
const types = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.glb': 'model/gltf-binary', '.svg': 'image/svg+xml', '.wasm': 'application/wasm', '.ktx2': 'image/ktx2',
  '.mp3': 'audio/mpeg', '.webp': 'image/webp', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  let p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  try {
    if (fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
    res.writeHead(200, { 'Content-Type': types[path.extname(p)] || 'application/octet-stream' });
    fs.createReadStream(p).pipe(res);
  } catch { res.writeHead(404); res.end('missing'); }
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined,
  args: ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const viewport = desktop ? { width: 1280, height: 800 } : { width: 390, height: 780 };
const context = await browser.newContext({ viewport, deviceScaleFactor: 1, isMobile: !desktop, hasTouch: !desktop });
const page = await context.newPage(); page.setDefaultTimeout(BOOT_MS);
const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
const tag = `${SCENE}-${desktop ? 'desktop' : 'phone'}`, report = { scene: SCENE, tag, shots: [] }, fail = [];
const sleep = (ms) => page.evaluate((t) => new Promise((r) => setTimeout(r, t)), ms);
const shot = async (name) => {
  const file = path.join(out, `${tag}-${name}.jpg`);
  await page.screenshot({ path: file, type: 'jpeg', quality: 86, timeout: 300000 });
  report.shots.push(file);
  console.log('  shot', file);
};
const cards = () => page.evaluate(() => __chicago4d.nameCards?.snapshot() ?? null);
const waitCards = async (min = 1, ms = 120000) => {
  const end = Date.now() + ms;
  let s = null;
  while (Date.now() < end) { s = await cards(); if (s && s.drawn >= min) return s; await sleep(1500); }
  return s;
};
try {
  await page.goto(`http://127.0.0.1:${server.address().port}/renderers/web/index.html?year=${SCENE}`, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: BOOT_MS, polling: 1000 });
  console.log('booted');
  for (let i = 0; i < 30 && await page.evaluate(() => __chicago4d.welcome.state) !== 'world'; i++) {
    await page.evaluate(() => __chicago4d.welcome.enter('spawn')); await sleep(2000);
  }
  await page.evaluate(() => document.exitPointerLock?.());
  console.log('in the world', await page.evaluate(() => JSON.stringify(__chicago4d.nameCards?.snapshot() ?? null)));
  // The nearest named, drawn person, stood in front of; their card to come up.
  let target = null;
  for (let k = 0; k < 40 && !target; k++) {
    target = await page.evaluate((only) => {
      const c = __chicago4d, v = c.walker.state;
      const named = c.humans.actors.filter((a) => a.body && a.root.visible && a.root.parent && !a.indoors && a.person?.name
        && a.instance?.interaction?.selectable && a.state !== 'walking' && (!only || a.personId === only));
      named.sort((a, b) => Math.hypot(a.e - v.e, a.n - v.n) - Math.hypot(b.e - v.e, b.n - v.n));
      const a = named[0];
      return a ? { id: a.personId, name: a.person.name, e: a.e, n: a.n, heading: a.heading } : null;
    }, process.env.QA_PERSON || null);
    if (!target) await sleep(3000);
  }
  if (!target) throw new Error('nobody named is drawn');
  console.log('target', target);
  const stand = async () => page.evaluate(({ t, d }) => {
    const c = __chicago4d;
    const a = c.humans.get(t.id) ?? c.humans.actors.find((x) => x.personId === t.id);
    const e = a?.e ?? t.e, n = a?.n ?? t.n;
    const h = (t.heading * Math.PI) / 180;
    const se = e + Math.sin(h) * d, sn = n + Math.cos(h) * d;
    const yaw = (Math.atan2(e - se, n - sn) * 180) / Math.PI;
    c.walker.teleport({ local_e: se, local_n: sn, yaw_deg: yaw });
    return { se, sn, yaw };
  }, { t: target, d: DIST });
  await stand();
  report.target = target;
  report.first = await waitCards(1);
  console.log('cards', JSON.stringify(report.first));
  for (const time of TIMES) {
    if (time !== 'daytime') { await page.evaluate((t) => __chicago4d.timeOfDay.set(t), time); await sleep(4000); }
    await stand();
    await page.evaluate(() => __chicago4d.nameCards.setShown(false));
    await sleep(2500);
    await shot(`${time}-before`);
    await page.evaluate(() => __chicago4d.nameCards.setShown(true));
    for (const skin of SKINS) {
      await page.evaluate((s) => {
        const tone = { 'worlds-fair': 'light' }[s] ?? 'dark';
        document.documentElement.dataset.skin = s; document.documentElement.dataset.theme = tone;
      }, skin);
      await waitCards(1, 30000);
      await sleep(2500);
      report[`${time}-${skin}`] = await cards();
      await shot(`${time}-after-${skin}`);
    }
  }
  // Every name of every card drawn fits (none cut).
  const s = await cards();
  const cut = (s?.cards ?? []).filter((c) => c.cut);
  if (cut.length) fail.push(`cut names: ${cut.map((c) => c.name).join(', ')}`);
  // A click or tap on the nearest card opens that person's card.
  const card = (s?.cards ?? []).find((c) => c.personId === target.id) ?? s?.cards?.[0] ?? null;
  if (!card) fail.push('no card drawn to click');
  else {
    const x = (card.ndc[0] + 1) / 2 * viewport.width, y = (1 - card.ndc[1]) / 2 * viewport.height;
    report.clicked = { name: card.name, x: Math.round(x), y: Math.round(y) };
    if (desktop) await page.mouse.click(x, y); else await page.touchscreen.tap(x, y);
    await sleep(6000);
    report.opened = await page.evaluate(() => {
      // Inspect's person card (1812, 1904) or the drawer's (1835): whichever pane is showing.
      const panes = [...document.querySelectorAll('.insp-pane, #people-directory')].filter((p) => p.offsetParent);
      return { text: panes.map((p) => p.innerText).join(' ').replace(/\s+/g, ' ').slice(0, 2000) };
    });
    if (!report.opened.text.includes(card.name.split(' ').slice(-1)[0])) fail.push(`clicking ${card.name}'s card did not open their card`);
    await shot('clicked');
  }
} catch (err) {
  fail.push(String(err?.stack ?? err));
} finally {
  report.errors = errors; report.fail = fail;
  fs.writeFileSync(path.join(out, `${tag}-report.json`), JSON.stringify(report, null, 2));
  console.log(fail.length ? `FAIL\n${fail.join('\n')}` : 'PASS', errors.length ? `\npage errors:\n${errors.join('\n')}` : '');
  await browser.close(); server.close();
  process.exit(fail.length ? 1 : 0);
}

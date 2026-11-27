// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * test_person_creator.mjs — the character creator (T-3553; Kevin, 2026-11-27: "much more rich with
 * more preview simpler buttons and graphics ... best practice build your character style
 * interfaces from aaa games").
 *
 * In a browser, the real You tab, creator, catalog and face library, with a stand-in portrait (no
 * 3D world: the drawing is person-portrait.js's, held to its rules here by its source): the tab
 * opens the creator; every category draws its choices; a choice is the person's at once, Undo
 * takes it back, Randomize keeps the body style, Esc closes; the option pictures are drawn for
 * the open category only, the person's own from their own figure; on a phone (390 x 780) nothing
 * runs off the side and the foot's buttons are a finger wide.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { execSync } from 'node:child_process';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const web = path.join(root, 'renderers/web');
let n = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); n++; };
const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');

// --- the drawing's rules, by its source (the browser here has no people layer to draw)
const pp = read('renderers/web/js/person-portrait.js');
ok(/PIXEL_PACK_BUFFER/.test(pp) && /fenceSync/.test(pp) && /clientWaitSync/.test(pp) && !/readRenderTargetPixelsAsync/.test(pp),
  'the portrait reads its pixels through a pack buffer behind a fence (crowd.js readLater), never three\'s async read');
ok(/gl\.bindBuffer\(gl\.PIXEL_PACK_BUFFER, null\);\s*const fence/.test(pp), 'the pack buffer is unbound before the fence (gpu-pick reads after it)');
ok(/targets\.get\(size\)/.test(pp) && (pp.match(/new THREE\.WebGLRenderTarget/g) ?? []).length === 1, 'one render target a size, made once');
ok(/PREVIEW_PERSON_ID = `\$\{VISITOR_PERSON_ID\}:preview`/.test(pp) && /personId: PREVIEW_PERSON_ID/.test(pp),
  'a preview is built under a row of its own, never the visitor\'s');
ok(/function forget\(\) \{\s*gen\+\+;/.test(pp) && /if \(g !== gen \|\| held\) \{ actor\.dispose\(\); continue; \}/.test(pp),
  'a figure built for a choice changed while it built is let go, not kept as the person (Randomize pressed twice)');
ok(/function turnTo/.test(pp) && /while \(wanted\)/.test(pp), 'a drag draws only the newest turn');
ok(!/<link[^>]+person-creator\.css/.test(read('renderers/web/index.html')), 'the creator\'s styles load with it, not with the page');
const pc = read('renderers/web/js/person-creator.js');
ok(pc.includes('faceGroups(') && pc.includes("role: 'tablist'") && pc.includes('pc-band'), 'the creator shows the face library by type, in bands');
ok(!/\b(men|women|man|woman|male|female|masculine|feminine|gender)\b/i.test(pc.match(/CREATOR_TABS = [\s\S]*?\]\);/)[0]), 'no category named for a sex');

// --- in a browser
const types = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.css': 'text/css', '.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp' };
const page = `<!doctype html><html lang="en" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="/renderers/web/css/walk.css"><link rel="stylesheet" href="/renderers/web/css/navigator.css">
<script type="importmap">{"imports":{"three":"/renderers/web/vendor/three-0.185.1/three.module.js"}}</script>
<style>body{margin:0;padding:12px;background:var(--panel-solid)}</style></head>
<body><div class="settings-group" data-set-pane="show" hidden></div><script type="module">
import { loadVisitorPerson } from '/renderers/web/js/visitor-person.js';
import { wirePersonSettings } from '/renderers/web/js/person-settings.js';
import { COMPLEXION_TINT, EYE_COLOUR } from '/renderers/web/js/human-looks.js';
const person = await loadVisitorPerson({ dataBase: new URL('/data/', location.href), assetBase: new URL('/assets/', location.href), storage: localStorage });
const calls = [];
const fill = (c) => { const x = c.getContext('2d'); x.fillStyle = '#888'; x.fillRect(c.width * .4, c.height * .1, c.width * .2, c.height * .8); };
const portrait = {
  draw(c, o) { calls.push({ kind: 'draw', w: c.width, ...o }); fill(c); return Promise.resolve(true); },
  preview(c, who, o) { calls.push({ kind: 'preview', w: c.width, record: who.record(o.year), asset: who.asset(o.year), ...o }); fill(c); return Promise.resolve(true); },
  turnTo(c, o) { return this.draw(c, o); }, forget() { calls.push({ kind: 'forget' }); },
};
window.t = { person, calls, ui: wirePersonSettings({ person, year: '1904', portrait, tints: COMPLEXION_TINT, eyes: EYE_COLOUR }) };
document.querySelector('[data-set-pane="you"]').hidden = false;
document.body.dataset.ready = '1';
</script></body></html>`;
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (u === '/') { res.writeHead(200, { 'content-type': 'text/html' }); return res.end(page); }
  const f = path.join(root, path.normalize(u));
  if (!f.startsWith(root)) { res.writeHead(403); return res.end(); }
  fs.readFile(f, (e, b) => { if (e) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'content-type': types[path.extname(f)] ?? 'application/octet-stream' }); res.end(b); });
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}/`;

let ns;
try { ns = await import('playwright'); } catch { ns = await import(path.join(execSync('npm root -g').toString().trim(), 'playwright', 'index.js')); }
const { chromium } = ns.chromium ? ns : ns.default;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
try {
  for (const [name, width, height] of [['desktop', 1280, 800], ['phone', 390, 780]]) {
    const ctx = await browser.newContext({ viewport: { width, height } });
    const p = await ctx.newPage();
    const errors = [];
    p.on('pageerror', (e) => errors.push(e.message));
    await p.goto(base);
    await p.waitForSelector('body[data-ready="1"]', { timeout: 60000 });
    const summary = await p.textContent('#s-person .person-summary');
    ok(/Style 1/.test(summary) && !/male|female/i.test(summary), `${name}: the You tab says what the person is (${summary})`);
    ok(await p.locator('#s-person select').count() === 0, `${name}: the You tab has no lists to scroll: one button opens the creator`);
    await p.click('#s-person .person-edit');
    await p.waitForSelector('dialog.person-creator[open]');
    ok(await p.evaluate(() => getComputedStyle(document.querySelector('dialog.person-creator')).position === 'fixed'), `${name}: the creator is full screen, its styles loaded with it`);
    ok(await p.locator('.pc-tab[role="tab"]').count() === 5, `${name}: five categories, each a tab`);
    const tiles = {};
    for (const tab of ['body', 'face', 'skin', 'hair', 'clothes']) {
      await p.click(`.pc-tab[data-tab="${tab}"]`);
      await p.waitForTimeout(150);
      tiles[tab] = await p.locator('.pc-panel [role="radio"]').count();
      const wide = await p.evaluate(() => { const d = document.querySelector('dialog.person-creator'); return Math.max(d.scrollWidth, document.querySelector('.pc-panel').scrollWidth) - innerWidth; });
      ok(wide <= 0, `${name}/${tab}: nothing runs off the side (${wide} px over)`);
    }
    ok(tiles.body === 6 && tiles.skin >= 14 && tiles.hair >= 13 && tiles.clothes >= 2 && tiles.face > 20,
      `${name}: every category is picture choices (${Object.entries(tiles).map(([k, v]) => `${k} ${v}`).join(', ')})`);
    // The pictures: the open category's only; the person's own from their own figure.
    const seen = await p.evaluate(() => t.calls.filter((c) => c.kind === 'preview').map((c) => c.record.looks?.face_pick ?? c.record.sex));
    ok(seen.length > 0, `${name}: option pictures are drawn (${seen.length})`);
    const own = await p.evaluate(() => t.calls.filter((c) => c.kind === 'preview' && c.asset === t.person.asset('1904')
      && JSON.stringify(c.record) === JSON.stringify(t.person.record('1904'))).length);
    ok(own === 0, `${name}: the person as they are is drawn from their own figure, never built again`);
    // A choice, Undo, Randomize.
    await p.click('.pc-tab[data-tab="hair"]');
    const was = await p.evaluate(() => t.person.choice.hair_colour);
    await p.click('.pc-swatch[aria-checked="false"] >> nth=0');
    const now = await p.evaluate(() => t.person.choice.hair_colour);
    ok(now !== was && await p.locator('.pc-swatch[aria-checked="true"]').count() === 1, `${name}: a swatch is the person's at once (${was} to ${now})`);
    await p.click('.pc-undo');
    ok(await p.evaluate(() => t.person.choice.hair_colour) === was, `${name}: Undo takes it back`);
    ok(await p.locator('.pc-undo').isDisabled(), `${name}: and has nothing more to undo`);
    const sex = await p.evaluate(() => t.person.choice.sex);
    await p.click('.pc-roll');
    ok(await p.evaluate((s) => t.person.choice.sex === s, sex), `${name}: Randomize keeps the body style`);
    if (name === 'phone') {
      const foot = await p.evaluate(() => [...document.querySelectorAll('.pc-foot-btn')].map((b) => { const r = b.getBoundingClientRect(); return [r.height, r.right <= innerWidth, r.bottom <= innerHeight]; }));
      ok(foot.length === 4 && foot.every(([h, inX, inY]) => h >= 44 && inX && inY), `${name}: the foot's four buttons are a finger tall and on the screen (${JSON.stringify(foot)})`);
      const pad = await p.evaluate(() => innerWidth - document.querySelector('.pc-done').getBoundingClientRect().right);
      ok(pad >= 6, `${name}: Done sits clear of the screen's edge (${pad} px)`);
      const view = await p.evaluate(() => document.querySelector('.pc-view').getBoundingClientRect().height);
      ok(view >= 200, `${name}: the person stands ${Math.round(view)} px tall over the choices`);
    }
    // Turning: the arrows draw the same figure turned, no build.
    const before = await p.evaluate(() => t.calls.filter((c) => c.kind === 'forget').length);
    await p.click('.pc-turn-right');
    await p.waitForTimeout(450);
    ok(await p.evaluate((b) => t.calls.filter((c) => c.kind === 'forget').length === b && t.calls.some((c) => c.kind === 'draw' && c.turn > 0), before),
      `${name}: a turn draws the figure turned, nothing built again`);
    // The face up close is looked at from the front, whatever the turn.
    await p.click('.pc-seg [data-frame="face"]');
    await p.waitForTimeout(200);
    ok(await p.evaluate(() => { const d = t.calls.filter((c) => c.kind === 'draw' && c.w === 480).at(-1); return d.frame === 'face' && d.turn === 0; }), `${name}: the face zoom turns to the front`);
    await p.keyboard.press('Escape');
    ok(await p.evaluate(() => !document.querySelector('dialog.person-creator').open), `${name}: Esc closes it`);
    const after = await p.evaluate(() => t.calls.length);
    await p.waitForTimeout(300);
    ok(await p.evaluate((a) => t.calls.filter((c, i) => i >= a && c.kind === 'preview').length === 0, after), `${name}: closed, no more pictures are drawn`);
    ok(errors.length === 0, `${name}: no page errors (${errors.join('; ')})`);
    await ctx.close();
  }
} finally {
  await browser.close();
  server.close();
}
console.log(`person creator (T-3553): ${n} checks PASS`);

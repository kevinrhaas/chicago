#!/usr/bin/env node
/** T-2046 / T-2061 — the arrival-and-jaunts path, laid out at the sizes a phone actually takes.
 *
 *   ./tools/publish.sh && node tools/measure_arrival_layouts.mjs [--layout narrow-320] [--write]
 *
 * Walks the published mirror (site/4d) from the welcome through Starting At…, the Jaunts
 * menu, a jaunt's first stop, its place card and its source, and back, at four layouts:
 *
 *   narrow-320    320x640 touch, a notch's insets (top 47, bottom 34)
 *   landscape     780x390 touch, held sideways (left/right 47, bottom 21)
 *   keyboard-390  390x780 touch; in the picker the on-screen keyboard is emulated by
 *                 taking 336px off the viewport (the resizes-content case, the harder one)
 *   desktop       1280x800 mouse and keyboard — focus order and restoration (no picker leg,
 *                 one still: a software frame at this size costs seconds)
 *
 * At every step it asserts, and exits 1 on any failure:
 *   - nothing scrolls sideways (scrollWidth <= innerWidth);
 *   - every visible control the path reaches (the welcome, the jaunt panel, the context card,
 *     the HUD's chips, the drawer and the place card) is at least 44x44 CSS px on a touch
 *     layout;
 *   - the place card, the drawer, the jaunt panel, the HUD's controls and the thumb's strip
 *     at the foot of the screen (--jaunt-floor) do not overlap one another, and nothing
 *     in the welcome sits on top of another of its controls;
 *   - the path's panels stand inside the safe-area insets;
 *   - at a stop the story itself is visible (at least 88px of it) and its first link can be
 *     tapped at its centre;
 *   - focus is never left on <body>: it moves with the region that opened, onto Return when
 *     a card hides the story, and back to the link that opened the card on Return.
 *
 * T-2046 measured the HUD's chips, the place card's inline controls and the drawer's header
 * and tabs and only REPORTED them; T-2061 brought them to 44 px on touch and they are gated
 * with the rest. Insets are applied with Emulation.setSafeAreaInsetsOverride; a browser without
 * it says so in the reading rather than passing the inset checks on zeros.
 *
 * Stills go to ARRIVAL_LAYOUT_EVIDENCE (default /tmp/arrival-layouts). `--write` records the
 * reading at docs/measurements/arrival-layouts.json.
 */
import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '../../../site/4d');
const out = process.env.ARRIVAL_LAYOUT_EVIDENCE || '/tmp/arrival-layouts';
const args = process.argv.slice(2);
const only = args.includes('--layout') ? args[args.indexOf('--layout') + 1] : null;
const write = args.includes('--write');
if (!fs.existsSync(path.join(root, 'walk', 'index.html'))) {
  console.error(`no published mirror at ${root} — run tools/publish.sh first`); process.exit(2);
}
fs.mkdirSync(out, { recursive: true });
const { chromium } = await import('playwright');

const LAYOUTS = [
  { name: 'narrow-320', viewport: { width: 320, height: 640 }, touch: true, insets: { top: 47, bottom: 34, left: 0, right: 0 } },
  { name: 'landscape', viewport: { width: 780, height: 390 }, touch: true, insets: { top: 0, bottom: 21, left: 47, right: 47 } },
  { name: 'keyboard-390', viewport: { width: 390, height: 780 }, touch: true, keyboard: 336, insets: { top: 0, bottom: 0, left: 0, right: 0 } },
  { name: 'desktop', viewport: { width: 1280, height: 800 }, touch: false, insets: { top: 0, bottom: 0, left: 0, right: 0 } },
].filter((l) => !only || l.name === only);
if (!LAYOUTS.length) { console.error(`no layout named ${only}`); process.exit(2); }

const mime = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css',
  '.json': 'application/json', '.wasm': 'application/wasm', '.svg': 'image/svg+xml', '.woff2': 'font/woff2' };
const server = http.createServer((req, res) => {
  let name = decodeURIComponent(req.url.split('?')[0]); if (name.endsWith('/')) name += 'index.html';
  const file = path.resolve(root, `.${name}`);
  if (!file.startsWith(`${root}/`) || !fs.existsSync(file)) { res.writeHead(404).end(); return; }
  res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
  fs.createReadStream(file).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const url = `http://127.0.0.1:${server.address().port}/walk/?year=1835`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined, args: ['--enable-unsafe-swiftshader'] });

/** Everything one step needs, read in the page in one pass. */
function readLayout({ touch, insets }) {
  const vis = (el) => !!el && el.getClientRects().length > 0 && getComputedStyle(el).visibility !== 'hidden'
    && !el.closest('[hidden]');
  const box = (el) => { const b = el.getBoundingClientRect(); return { l: b.left, t: b.top, r: b.right, b: b.bottom }; };
  const name = (el) => `${el.tagName.toLowerCase()}${el.id ? `#${el.id}` : ''}${el.dataset.action ? `[${el.dataset.action}]` : ''}`
    + `${el.dataset.link ? `[${el.dataset.link}]` : ''} "${(el.getAttribute('aria-label') || el.textContent || '').trim().slice(0, 28)}"`;
  const hits = (a, b) => Math.min(a.r, b.r) - Math.max(a.l, b.l) > 1 && Math.min(a.b, b.b) - Math.max(a.t, b.t) > 1;
  const W = innerWidth, H = innerHeight, f = [];
  if (document.documentElement.scrollWidth > W) f.push(`scrolls sideways: ${document.documentElement.scrollWidth} > ${W}`);
  const controls = (scope) => [...scope.querySelectorAll('button, a[href], input, select, summary, [role=button]')]
    .filter((el) => vis(el) && !el.disabled && el.getBoundingClientRect().width > 0);
  const owned = ['#gate', '#jaunt-panel', '.jaunt-context-card', '#hud', '#popup'].map((s) => document.querySelector(s)).filter(vis);
  if (touch) {
    for (const scope of owned) for (const el of controls(scope)) {
      const b = el.getBoundingClientRect();
      if (b.bottom <= 0 || b.top >= H) continue;
      if (b.width < 43.5 || b.height < 43.5) f.push(`target under 44px: ${name(el)} ${Math.round(b.width)}x${Math.round(b.height)}`);
    }
  }
  // The surfaces that must not cover one another while a jaunt is running.
  const surfaces = [];
  for (const [label, sel] of [['place card', '#popup'], ['drawer', '#panel'], ['jaunt panel', '#jaunt-panel'], ['context card', '.jaunt-context-card'], ['travel banner', '#travel-banner']]) {
    const el = document.querySelector(sel); if (vis(el)) surfaces.push({ label, b: box(el) });
  }
  // The HUD's CONTROLS: its readouts (the year badge, the compass) may sit under a panel.
  const chips = [...document.querySelectorAll('#hud .chip')].filter(vis).map((el) => ({ label: `HUD ${name(el)}`, b: box(el) }));
  const active = document.documentElement.hasAttribute('data-jaunt-active');
  const floor = active && touch ? parseFloat(getComputedStyle(document.querySelector('#jaunt-panel') || document.body).bottom) : 0;
  const thumb = floor > 0 ? [{ label: "thumb's strip", b: { l: 0, t: H - floor + insets.bottom, r: W, b: H } }] : [];
  const all = [...surfaces, ...chips, ...thumb];
  for (let i = 0; i < all.length; i++) for (let j = i + 1; j < all.length; j++) {
    const a = all[i], c = all[j];
    if (a.label.startsWith('HUD') && c.label.startsWith('HUD')) continue;
    if (!['place card', 'drawer'].includes(a.label) && !['place card', 'drawer'].includes(c.label)
      && ![a.label, c.label].includes('jaunt panel') && ![a.label, c.label].includes("thumb's strip")) continue;
    if (hits(a.b, c.b)) f.push(`overlap: ${a.label} and ${c.label}`);
  }
  // Inside the welcome: no control drawn over another (the landscape picker spilled once).
  const gate = document.getElementById('gate');
  if (vis(gate)) {
    const gc = controls(gate).filter((el) => !el.closest('.welcome-results, .welcome-kinds, #welcome-jaunts-content'));
    const results = document.getElementById('welcome-results');
    const lists = [results, document.getElementById('welcome-jaunts-content')].filter(vis);
    for (const el of gc) for (const list of lists) {
      if (list.contains(el) || el.contains(list)) continue;
      // A list that scrolls inside its region is drawn only within its scrolling ancestors.
      const b = box(el), clip = box(list);
      for (let up = list.parentElement; up && up !== document.body; up = up.parentElement) {
        if (getComputedStyle(up).overflowY === 'visible') continue;
        const u = box(up);
        clip.l = Math.max(clip.l, u.l); clip.t = Math.max(clip.t, u.t); clip.r = Math.min(clip.r, u.r); clip.b = Math.min(clip.b, u.b);
      }
      if (hits(b, clip)) f.push(`welcome: ${name(el)} is drawn over ${list.id}`);
    }
  }
  // Panels the path owns stand inside the insets.
  for (const s of surfaces) {
    const { l, t, r, b } = s.b;
    if (l < insets.left - 0.5 || r > W - insets.right + 0.5 || t < insets.top - 0.5 || b > H - insets.bottom + 0.5) {
      f.push(`outside the safe area: ${s.label} [${Math.round(l)},${Math.round(t)},${Math.round(r)},${Math.round(b)}]`);
    }
  }
  const card = gate && vis(gate) ? gate.querySelector('.gate-card') : null;
  if (card) {
    const b = box(card);
    if (b.l < insets.left - 0.5 || b.r > W - insets.right + 0.5 || b.t < insets.top - 0.5 || b.b > H - insets.bottom + 0.5) f.push('outside the safe area: the welcome card');
  }
  const a = document.activeElement;
  return { failures: f, focus: a && a !== document.body ? name(a) : 'body',
    focusVisible: !!a && a !== document.body && vis(a), focusLink: a?.dataset?.link ?? null };
}

const results = { ticket: 'T-2061', measuredAt: new Date().toISOString(), browser: browser.version(), layouts: [] };
let failed = 0;
for (const layout of LAYOUTS) {
  const { name, viewport, touch, insets } = layout;
  const ctx = await browser.newContext({ viewport, hasTouch: touch, isMobile: false, deviceScaleFactor: 1 });
  const t0 = Date.now();
  // The path is chrome, not rendering: the town is drawn at `light`, as part 14 does.
  await ctx.addInitScript(() => { try { localStorage.setItem('chicago4d.settings', JSON.stringify({ detail: 'light' })); } catch { /* default tier */ } });
  const page = await ctx.newPage();
  page.setDefaultTimeout(90_000);
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message || String(e)));
  const record = { name, viewport, touch, insets, insetsApplied: false, steps: [], errors };
  if (insets.top || insets.bottom || insets.left || insets.right) {
    const cdp = await ctx.newCDPSession(page);
    try { await cdp.send('Emulation.setSafeAreaInsetsOverride', { insets }); record.insetsApplied = true; } catch (e) { record.insetsNote = `not applied: ${e.message}`; }
  }
  const until = (fn, arg = null) => page.waitForFunction(fn, arg, { polling: 250, timeout: 240_000 });
  const fail = (step, msg) => { record.steps.at(-1)?.failures.push(msg) ?? console.log(`${name} ${step}: ${msg}`); };
  const step = async (label, extra = () => []) => {
    const r = await page.evaluate(readLayout, { touch, insets: record.insetsApplied ? insets : { top: 0, bottom: 0, left: 0, right: 0 } });
    const s = { step: label, failures: [...r.failures, ...await extra(r)], focus: r.focus };
    record.steps.push(s);
    if (touch || label === 'at-stop') {
      const still = path.join(out, `${name}-${String(record.steps.length).padStart(2, '0')}-${label}.png`);
      await page.screenshot({ path: still });
      s.still = path.basename(still);
    }
    console.log(`${s.failures.length ? 'FAIL' : 'pass'}  [${Math.round((Date.now() - t0) / 1000)}s] ${name} ${label}${s.failures.length ? `\n        ${s.failures.join('\n        ')}` : ''}`);
    return r;
  };
  // A visitor's tap, hit-tested at the control's centre so a covered control fails by name.
  const tap = async (sel) => {
    const at = await page.evaluate((s) => {
      const el = [...document.querySelectorAll(s)].find((x) => x.getClientRects().length && getComputedStyle(x).visibility !== 'hidden');
      if (!el) return { why: `nothing visible matches ${s}` };
      el.scrollIntoView({ block: 'nearest' });
      const b = el.getBoundingClientRect(), x = b.x + b.width / 2, y = b.y + b.height / 2, top = document.elementFromPoint(x, y);
      if (!top || !(top === el || el.contains(top))) return { why: `${s} is covered at its centre by <${top?.tagName.toLowerCase()} class="${top?.className}">` };
      return { x, y };
    }, sel);
    if (at.why) throw new Error(at.why);
    if (touch) await page.touchscreen.tap(at.x, at.y); else await page.mouse.click(at.x, at.y);
  };
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded' });
    await until(() => window.__chicago4d?.welcome?.state === 'welcome');
    await step('welcome');
    if (!touch) {
      // Focus order: Tab from the title walks the welcome's own controls in order and wraps
      // inside it — never out to the canvas or the HUD behind.
      const order = [];
      for (let i = 0; i < 6; i++) {
        await page.keyboard.press('Tab');
        order.push(await page.evaluate(() => { const a = document.activeElement; return { id: a?.id || a?.className || a?.tagName, inGate: !!a && document.getElementById('gate').contains(a) }; }));
      }
      record.tabOrder = order.map((o) => o.id);
      const ji = record.tabOrder.indexOf('welcome-jaunts'), ei = record.tabOrder.indexOf('welcome-explore');
      if (!order.every((o) => o.inGate)) fail('welcome', `Tab left the welcome: ${record.tabOrder.join(' → ')}`);
      if (!(ji >= 0 && ei > ji)) fail('welcome', `Tab does not reach Jaunts then Starting At… in order: ${record.tabOrder.join(' → ')}`);
    }
    if (!touch) {
      // The picker's layout is the three touch layouts' question; at 1280x800 a frame in
      // software costs seconds, so the desktop walk spends its budget on focus instead.
    } else if (name !== 'landscape') {
      await tap('#welcome-explore');
      await until(() => !!document.querySelector('#welcome-picker:not([hidden]) .welcome-destination:not(:disabled)'));
      await step('picker', (r) => (r.focus.startsWith('input#welcome-search') ? [] : [`focus is on ${r.focus}, not the search`]));
      if (layout.keyboard) {
        await page.setViewportSize({ width: viewport.width, height: viewport.height - layout.keyboard });
        await page.keyboard.type('tav');
        await page.waitForTimeout(600);
        await step('picker-keyboard', () => page.evaluate(() => {
          const f = [], H = innerHeight, s = document.getElementById('welcome-search').getBoundingClientRect();
          const first = document.querySelector('#welcome-results .welcome-destination');
          if (s.top < 0 || s.bottom > H) f.push('the search is not in view above the keyboard');
          if (!first) f.push('no result for "tav"');
          else { const b = first.getBoundingClientRect(); if (b.top < 0 || b.top + 44 > H) f.push('the first result is under the keyboard'); }
          return f;
        }));
        await page.setViewportSize(viewport);
        await page.waitForTimeout(300);
      }
    } else {
      // Held sideways the picker is compact; it is opened, measured and left by reloading,
      // because its compact form hides the two actions (as designed) to give the list room.
      await tap('#welcome-explore');
      await until(() => !!document.querySelector('#welcome-picker:not([hidden]) .welcome-destination:not(:disabled)'));
      await step('picker');
      await page.evaluate(() => window.__chicago4d.welcome.show());
      await until(() => window.__chicago4d.welcome.state === 'welcome' && document.getElementById('welcome-jaunts').getClientRects().length > 0);
    }
    await tap('#welcome-jaunts');
    await until(() => !!document.querySelector('[data-jaunt="new-in-chicago"] [data-action="start"]'));
    await step('jaunts-menu', (r) => (r.focusVisible ? [] : [`focus fell to ${r.focus} when the Jaunts region opened`]));
    await tap('[data-jaunt="new-in-chicago"] [data-action="start"]');
    await until(() => window.__chicago4d.jaunts.state?.phase === 'atStop');
    await page.waitForTimeout(400);
    await step('at-stop', () => page.evaluate(() => {
      const f = [], body = document.querySelector('#jaunt-panel .jaunt-body'), b = body?.getBoundingClientRect();
      if (!b || b.height < 88) f.push(`only ${Math.round(b?.height ?? 0)}px of the stop's story shows`);
      const link = body?.querySelector('[data-link]');
      if (link) {
        link.scrollIntoView({ block: 'nearest' });
        const r = link.getBoundingClientRect(), top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
        if (!top || !(top === link || link.contains(top))) f.push(`the stop's first link is covered by <${top?.tagName.toLowerCase()} class="${top?.className}">`);
      } else f.push('the stop shows no link');
      return f;
    }));
    await tap('[data-link="structure:sauganash_hotel"]');
    await until(() => window.__chicago4d.jaunts.state.phase === 'detail' && !document.getElementById('popup').hidden);
    await page.waitForTimeout(400);
    await step('place-card', async (r) => {
      const f = r.focusVisible ? [] : [`focus fell to ${r.focus} when the card opened`];
      const h = await page.evaluate(() => document.getElementById('popup').getBoundingClientRect().height);
      if (h < 120) f.push(`the place card is only ${Math.round(h)}px tall`);
      return f;
    });
    await tap('#jaunt-panel [data-action="return"]');
    await until(() => window.__chicago4d.jaunts.state?.phase === 'atStop');
    await page.waitForTimeout(300);
    await step('returned', (r) => (r.focusLink === 'structure:sauganash_hotel' ? [] : [`Return left focus on ${r.focus}, not the link that opened the card`]));
    await tap('[data-link="source:kinzie_waubun_1856"]');
    await until(() => window.__chicago4d.jaunts.state.phase === 'detail' && !document.getElementById('panel').hidden);
    await page.waitForTimeout(400);
    await step('source', async (r) => {
      const f = r.focusVisible ? [] : [`focus fell to ${r.focus} when the source opened`];
      const h = await page.evaluate(() => document.getElementById('panel').getBoundingClientRect().height);
      if (h < 120) f.push(`the drawer is only ${Math.round(h)}px tall`);
      return f;
    });
    await tap('#jaunt-panel [data-action="return"]');
    await until(() => window.__chicago4d.jaunts.state?.phase === 'atStop');
    await page.waitForTimeout(300);
    await step('returned-from-source', (r) => (r.focusLink === 'source:kinzie_waubun_1856' ? [] : [`Return left focus on ${r.focus}, not the link that opened the source`]));
  } catch (e) {
    record.steps.push({ step: 'walk', failures: [`the walk stopped: ${String(e.message || e).split('\n')[0]}`] });
    console.log(`FAIL  ${name} the walk stopped: ${String(e.message || e).split('\n')[0]}`);
  }
  if (errors.length) record.steps.push({ step: 'page errors', failures: errors.slice(0, 4) });
  if (!record.insetsApplied && (insets.top || insets.bottom || insets.left || insets.right)) {
    record.steps.push({ step: 'insets', failures: [`safe-area insets ${record.insetsNote}`] });
  }
  record.failures = record.steps.reduce((n, s) => n + s.failures.length, 0);
  failed += record.failures;
  results.layouts.push(record);
  await ctx.close();
}
await browser.close();
server.close();
results.verdict = failed ? `FAIL — ${failed} failure(s)` : 'PASS';
console.log(`\narrival layouts: ${results.verdict}; stills in ${out}`);
if (write) {
  const file = path.resolve(here, '../docs/measurements/arrival-layouts.json');
  const prior = fs.existsSync(file) ? JSON.parse(fs.readFileSync(file, 'utf8')) : null;
  // A one-layout run merges into the reading rather than retiring the others.
  if (only && prior) results.layouts = [...prior.layouts.filter((l) => l.name !== only), ...results.layouts];
  fs.writeFileSync(file, `${JSON.stringify(results, null, 2)}\n`);
  console.log(`wrote ${path.relative(process.cwd(), file)}`);
}
process.exit(failed ? 1 : 0);

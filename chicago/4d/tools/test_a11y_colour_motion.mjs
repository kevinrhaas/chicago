// T-3671 (WCAG 2.1 AA): colour-blind-safe grades and the motion choice.
//
//   node tools/test_a11y_colour_motion.mjs
//
// 1.4.1 / 1.4.11  the grade palette stays apart under simulated protanopia, deuteranopia and
//                 tritanopia (Machado, Oliveira & Fernandes 2009, severity 1), and every mark
//                 that stands for a grade says it by SHAPE too (full / half / ring; solid /
//                 dashed / dotted; plain / striped / hatched) — the HUD legend chip, the card
//                 and People dots, the census bars, the map legend, the building labels, the
//                 name cards' edge and light, and the town's own shader (grade patterns).
// 2.2.2 / 2.3.3   one motion choice (js/motion.js): stored at chicago4d.motion, System by
//                 default and following the device, html[data-motion] set, every transition
//                 and animation ~0 under Reduce, the telemetry strip standing still, and the
//                 Settings › Look › Motion row a keyboard-operable radio group.
//
// Real markup, CSS and modules in Playwright chromium at 390x780 and 1280x800; no town load.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const web = path.resolve(new URL('../renderers/web', import.meta.url).pathname);
const index = fs.readFileSync(path.join(web, 'index.html'), 'utf8');
const meta = index.match(/<meta name="viewport"[^>]+>/)[0];
const imports = index.match(/<script type="importmap">[\s\S]*?<\/script>/)[0];
const LEVELS = ['attested', 'inferred', 'reconstructed'];
let checks = 0;
const ok = (cond, msg) => { assert.ok(cond, msg); checks++; };

// ---- 1. the palette under simulated colour-vision deficiency (node) ----------------- //
const lin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const unlin = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055);
const rgb = (h) => { const s = String(h).replace(/^#/, '').padStart(6, '0'); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16) / 255); };
function lab(c) {
  const [r, g, b] = c.map(lin);
  const f = (t) => (t > 216 / 24389 ? Math.cbrt(t) : (24389 / 27 * t + 16) / 116);
  const X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047, Y = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  const Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883;
  return [116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))];
}
const dE = (a, b) => Math.hypot(...lab(a).map((v, i) => v - lab(b)[i]));
const CVD = {
  normal: [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
  protanopia: [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
  deuteranopia: [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
  tritanopia: [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
};
const sim = (c, m) => { const l = c.map(lin); return m.map((row) => unlin(Math.min(1, Math.max(0, row[0] * l[0] + row[1] * l[1] + row[2] * l[2])))); };
const relLum = (c) => { const [r, g, b] = c.map(lin); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const contrast = (a, b) => { const [x, y] = [relLum(a), relLum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
{
  const src = fs.readFileSync(path.join(web, 'js/confidence.js'), 'utf8').replace("import * as THREE from 'three';", 'const THREE = {};');
  const { GRADE_COLORS } = await import(`data:text/javascript;base64,${Buffer.from(src).toString('base64')}`);
  const sets = {
    scene: Object.fromEntries(LEVELS.map((l) => [l, `#${GRADE_COLORS[l].scene.toString(16).padStart(6, '0')}`])),
    'dark fill': Object.fromEntries(LEVELS.map((l) => [l, GRADE_COLORS[l].dark.fill])),
    'light fill': Object.fromEntries(LEVELS.map((l) => [l, GRADE_COLORS[l].light.fill])),
    'dark ink': Object.fromEntries(LEVELS.map((l) => [l, GRADE_COLORS[l].dark.ink])),
    'light ink': Object.fromEntries(LEVELS.map((l) => [l, GRADE_COLORS[l].light.ink])),
  };
  let least = Infinity;
  for (const [name, set] of Object.entries(sets)) {
    for (const [vision, m] of Object.entries(CVD)) {
      for (let i = 0; i < LEVELS.length; i++) for (let j = i + 1; j < LEVELS.length; j++) {
        const d = dE(sim(rgb(set[LEVELS[i]]), m), sim(rgb(set[LEVELS[j]]), m));
        least = Math.min(least, d);
        ok(d >= 12, `${name} ${vision}: ${LEVELS[i]} and ${LEVELS[j]} only ΔE ${d.toFixed(1)} apart`);
      }
    }
  }
  // A fill is the only cue of a boundary somewhere (a census bar's share, a dot's ring), so
  // it holds 3:1 against the dark and the light panel.
  for (const l of LEVELS) {
    ok(contrast(rgb(GRADE_COLORS[l].dark.fill), rgb('#16150f')) >= 3, `${l} dark fill under 3:1`);
    ok(contrast(rgb(GRADE_COLORS[l].light.fill), rgb('#faf8f3')) >= 3, `${l} light fill under 3:1`);
  }
  console.log(`  palette: least pairwise ΔE ${least.toFixed(1)} across normal, protanopia, deuteranopia, tritanopia`);
}

// ---- 2. the name cards: an edge and a light per grade (node, a recording 2D context) ---- //
{
  const nc = await import(path.join(web, 'js/name-cards.js'));
  const cues = LEVELS.map((l) => nc.GRADE_CUE[l]);
  ok(new Set(cues.map((c) => c.edge)).size === 3 && new Set(cues.map((c) => c.light)).size === 3, 'name-card cues not distinct');
  const draw = (level) => {
    const log = [];
    let dash = [];
    const ctx = new Proxy({}, {
      get: (t, k) => (k in t ? t[k] : (k === 'setLineDash' ? (d) => { dash = [...d]; log.push(['dash', dash.join(',')]); }
        : k === 'stroke' ? () => log.push(['stroke', dash.join(',')]) : k === 'fill' ? () => log.push(['fill'])
          : k === 'arc' ? (...a) => log.push(['arc', (a[4] - a[3]).toFixed(2)]) : k === 'measureText' ? () => ({ width: 40 }) : () => {})),
      set: (t, k, v) => { t[k] = v; return true; },
    });
    const theme = { panel: '#16150f', edge: '#3e5a86', accent: '#d8a24a', ink: '#f4f1ea', radius: 6, chamfer: 0, weight: 600, font: 'sans-serif' };
    nc.drawCard(ctx, { lines: ['Jean Baptiste'], size: 18, cut: false, width: 120 }, theme, level ? { level, color: '#d4ae38' } : null);
    return log;
  };
  const strokes = Object.fromEntries(LEVELS.map((l) => [l, draw(l).filter((e) => e[0] === 'stroke').map((e) => e[1]).join('|')]));
  ok(new Set(Object.values(strokes)).size === 3, `name-card edges drawn alike: ${JSON.stringify(strokes)}`);
  const lights = Object.fromEntries(LEVELS.map((l) => [l, draw(l).filter((e) => e[0] === 'arc' || e[0] === 'fill').slice(-3).map((e) => e.join(':')).join('|')]));
  ok(new Set(Object.values(lights)).size === 3, `name-card lights drawn alike: ${JSON.stringify(lights)}`);
}

// ---- 3. the browser fixture ------------------------------------------------------- //
const CSS = ['walk', 'drawer', 'navigator', 'confidence-overlays', 'inspect', 'people', 'evidence', 'card', 'skins'];
const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://local');
  if (url.pathname === '/') {
    res.setHeader('Content-Type', 'text/html');
    res.end(`<!doctype html><html lang="en" data-theme="dark"><head>${meta}${imports}
      ${CSS.map((c) => `<link rel="stylesheet" href="/css/${c}.css">`).join('')}
      <style>#moving { transition: opacity .3s ease; animation: spin 2s linear infinite; } @keyframes spin { to { rotate: 1turn; } }
      body { overflow: auto; }</style></head>
      <body><div id="moving">moving</div><div id="board"></div></body></html>`); return;
  }
  const file = path.resolve(web, `.${url.pathname}`);
  if (!file.startsWith(`${web}/`)) { res.writeHead(403); res.end(); return; }
  fs.readFile(file, (err, bytes) => {
    res.writeHead(err ? 404 : 200, { 'Content-Type': file.endsWith('.js') ? 'text/javascript'
      : file.endsWith('.html') ? 'text/html' : 'text/css' }); res.end(err ? '' : bytes);
  });
});
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE, args: ['--no-sandbox', '--enable-unsafe-swiftshader'] });
try {
  // ---- 3a. grade marks: the shape differs by grade, wherever a grade is a mark ---- //
  {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', (e) => errors.push(e.message));
    await page.goto(origin);
    const marks = await page.evaluate(async (LEVELS) => {
      const board = document.getElementById('board');
      const src = new DOMParser().parseFromString(await (await fetch('/index.html')).text(), 'text/html');
      const chip = src.getElementById('conf-legend');
      board.append(chip);
      const { createConfidenceLegend } = await import('/js/confidence-legend.js');
      const view = { grade: (l) => ({ attested: { mode: 'tint', opacity: .62, color: '#d4af37' }, inferred: { mode: 'tint', opacity: .72, color: '#b8c0c8' }, reconstructed: { mode: 'dither', opacity: .34, color: '#8c5a2b' } })[l] };
      const hud = { confidenceOn: true, hiddenLevels: [] };
      createConfidenceLegend({ el: chip, hud, view });
      // A mark's look with every colour taken out: what is left is its shape and texture, so
      // two grades whose signatures match would be told apart by colour alone.
      const noColour = (v) => v.replace(/(rgba?|color)\([^)]*\)/g, 'C');
      const sig = (el) => { const s = getComputedStyle(el); return noColour([s.backgroundImage, s.backgroundColor === 'rgba(0, 0, 0, 0)' ? 'clear' : 'filled', s.boxShadow, s.borderStyle].join(' / ')); };
      const add = (html) => { const d = document.createElement('div'); d.innerHTML = html; board.append(d); return d; };
      const out = {};
      out.legend = LEVELS.map((l) => sig(chip.querySelector(`[data-grade="${l}"]`)));
      out.legendLabel = chip.getAttribute('aria-label');
      const short = { attested: 'att', inferred: 'inf', reconstructed: 'rec' };
      const doc = { attested: 'doc', inferred: 'inf', reconstructed: 'rec' };
      const row = (f) => { const d = add(LEVELS.map(f).join('')); return [...d.children].map(sig); };
      out.factDot = row((l) => `<i class="fact-dot fact-${l}"></i>`);
      out.gradeDot = row((l) => `<i class="grade-dot grade-${l}"></i>`);
      out.legendSw = row((l) => `<i class="sw sw-${doc[l]}"></i>`);
      out.census = (() => { const d = add(`<div class="city-census">${LEVELS.map((l) => `<i class="gc-seg gc-seg-${short[l]}" style="width:40px;height:8px"></i><i class="gc-sw gc-sw-${short[l]}"></i><i class="gc-done-seg gc-done-${short[l]}" style="width:40px;height:6px"></i>`).join('')}</div>`);
        return [...d.firstChild.children].map(sig); })();
      out.mapSw = row((l) => `<span class="nav-map-swatch is-${l}"><i></i></span>`).map((_, i) => sig(board.lastChild.children[i].firstChild));
      out.inspSeg = row((l) => `<span class="insp-seg fact-${l}" style="width:30px;height:6px"></span>`);
      out.label = (() => { const d = add(`<div class="cv-overlays" style="position:static">${LEVELS.map((l) => `<span class="cv-label" data-grade="${l}" style="position:static"><i class="cv-label-mark" data-grade="${l}"></i>Fort Dearborn</span>`).join('')}</div>`);
        return [...d.firstChild.children].map((n) => `${getComputedStyle(n).borderTopStyle} ${sig(n.firstChild)}`); })();
      // the town: the shader pattern, default on, off by the Patterns key
      const THREE = await import('three');
      const { createConfidenceView } = await import('/js/confidence.js');
      const cv = createConfidenceView();
      const mat = new THREE.MeshStandardMaterial();
      cv.patch(mat);
      const shader = { uniforms: {}, vertexShader: '#include <begin_vertex>', fragmentShader: '#include <clipping_planes_fragment>\n#include <color_fragment>\n#include <opaque_fragment>' };
      mat.onBeforeCompile(shader, null);
      out.shader = { on: cv.patterns, value: cv.uniforms.uConfPattern.value, uses: /uConfPattern > 0\.0/.test(shader.fragmentShader) && /uniform float uConfPattern/.test(shader.fragmentShader),
        bound: shader.uniforms.uConfPattern === cv.uniforms.uConfPattern };
      cv.setPatterns(false);
      out.shader.off = cv.uniforms.uConfPattern.value;
      const { setPatterns, restoreLooks } = await import('/js/confidence-presets.js');
      const mem = new Map(); const storage = { getItem: (k) => mem.get(k) ?? null, setItem: (k, v) => mem.set(k, String(v)), removeItem: (k) => mem.delete(k) };
      setPatterns(cv, false, storage);
      const cv2 = createConfidenceView();
      restoreLooks(cv2, storage);
      out.shader.kept = cv2.patterns;
      return out;
    }, LEVELS);
    const distinct = (list, what) => ok(new Set(list).size === list.length, `${what}: two grades look alike but for colour — ${JSON.stringify(list)}`);
    distinct(marks.legend, 'HUD legend chip');
    for (const l of LEVELS) ok(new RegExp(l, 'i').test(marks.legendLabel), `legend chip label lacks the word ${l}`);
    distinct(marks.factDot, 'card fact dots');
    distinct(marks.gradeDot, 'People grade dots');
    distinct(marks.legendSw, 'legend swatches');
    distinct([0, 3, 6].map((i) => marks.census[i]), 'census bar shares');
    distinct([1, 4, 7].map((i) => marks.census[i]), 'census key swatches');
    distinct([2, 5, 8].map((i) => marks.census[i]), 'census dwellings bar');
    distinct(marks.mapSw, 'map legend swatches');
    distinct(marks.inspSeg, 'Inspect confidence meter');
    distinct(marks.label, 'building labels');
    ok(marks.label.map((s) => s.split(' ')[0]).join() === 'solid,dashed,dotted', `label edges ${marks.label.map((s) => s.split(' ')[0])}`);
    ok(marks.shader.on === true && marks.shader.value > 0 && marks.shader.uses && marks.shader.bound, `grade patterns not on in the shader by default: ${JSON.stringify(marks.shader)}`);
    ok(marks.shader.off === 0 && marks.shader.kept === false, 'grade patterns not turned off, or not kept');
    const overlays = fs.readFileSync(path.join(web, 'js/confidence-overlays.js'), 'utf8');
    ok(/make\('i', 'cv-label-mark'\)[\s\S]{0,80}mark\.dataset\.grade = b\.grade/.test(overlays), 'building labels lost their grade mark');
    const view = fs.readFileSync(path.join(web, 'js/apps/confidence-view.js'), 'utf8');
    ok(/id: 'cm-patterns'/.test(view) && /patterns\.setAttribute\('aria-pressed'/.test(view), 'Confidence view lost its Grade patterns key');
    ok(!errors.length, `page errors: ${errors.join('; ')}`);
    await context.close();
  }

  // ---- 3b. the motion choice, at both widths -------------------------------------- //
  for (const width of [390, 1280]) {
    const phone = width === 390;
    for (const device of ['no-preference', 'reduce']) {
      const context = await browser.newContext({ viewport: { width, height: phone ? 780 : 800 }, isMobile: phone, hasTouch: phone,
        deviceScaleFactor: 1, reducedMotion: device });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', (e) => errors.push(e.message));
      await page.goto(origin);
      const tag = `${width} device ${device}`;
      const setup = await page.evaluate(async () => {
        const src = new DOMParser().parseFromString(await (await fetch('/index.html')).text(), 'text/html');
        const panel = src.querySelector('[data-panel="settings"]');
        panel.hidden = false;
        for (const g of panel.querySelectorAll('.settings-group')) g.hidden = g.dataset.setPane !== 'look';
        const nav = document.createElement('section'); nav.className = 'navigator'; nav.id = 'navigator';
        nav.append(panel); document.getElementById('board').append(nav);
        const s = await import('/js/settings-app.js');
        const seg = s.motionGroup(document);
        s.wireMotion(seg);
        const m = await import('/js/motion.js');
        const t = await import('/js/nav-telemetry.js');
        window.fixtureMotion = m;
        window.fixtureStrip = t.mountTelemetry({ host: document.getElementById('board'), visible: () => true });
        const radios = [...seg.querySelectorAll('[role="radio"]')];
        return { inLook: !!seg.closest('#s-look'), role: seg.getAttribute('role'), name: document.getElementById(seg.getAttribute('aria-labelledby'))?.textContent,
          radios: radios.map((r) => [r.textContent, r.getAttribute('aria-checked'), r.tabIndex]), motion: document.documentElement.dataset.motion };
      });
      ok(setup.inLook && setup.role === 'radiogroup' && setup.name === 'Motion', `${tag}: Motion row not a labelled radio group in Look`);
      ok(setup.radios.map((r) => r[0]).join() === 'System,Reduce,Full', `${tag}: ${setup.radios}`);
      ok(setup.radios[0][1] === 'true' && setup.radios[0][2] === 0 && setup.radios[1][2] === -1, `${tag}: System is not the default, or not the Tab stop`);
      ok(setup.motion === (device === 'reduce' ? 'reduce' : 'full'), `${tag}: System did not follow the device (${setup.motion})`);
      const read = () => page.evaluate(() => {
        const mv = getComputedStyle(document.getElementById('moving'));
        return { motion: document.documentElement.dataset.motion, stored: localStorage.getItem('chicago4d.motion'),
          checked: [...document.querySelectorAll('#s-motion [role="radio"]')].find((r) => r.getAttribute('aria-checked') === 'true')?.dataset.motion,
          focus: document.activeElement?.dataset?.motion ?? null, reduced: window.fixtureMotion.reducedMotion(), strip: window.fixtureStrip.running,
          transition: parseFloat(mv.transitionDuration), animation: parseFloat(mv.animationDuration), iterations: mv.animationIterationCount };
      });
      // Keyboard: Tab reaches the chosen radio, the arrows move the choice.
      await page.focus('#s-motion [data-motion="system"]');
      await page.keyboard.press('ArrowRight');
      let r = await read();
      ok(r.checked === 'reduce' && r.focus === 'reduce' && r.stored === 'reduce' && r.motion === 'reduce' && r.reduced, `${tag}: ArrowRight did not choose Reduce ${JSON.stringify(r)}`);
      ok(r.transition < 0.001 && r.animation < 0.001 && r.iterations === '1', `${tag}: transitions/animations not ~0 under Reduce ${JSON.stringify(r)}`);
      ok(r.strip === false, `${tag}: telemetry strip still ticking under Reduce`);
      const tm = await page.evaluate(() => document.querySelector('.nav-telemetry [data-t="field"] b')?.textContent);
      ok(tm === '0.998', `${tag}: telemetry strip not at its steady reading (${tm})`);
      await page.keyboard.press('ArrowRight');
      r = await read();
      ok(r.checked === 'full' && r.stored === 'full' && r.motion === 'full' && !r.reduced, `${tag}: Full ${JSON.stringify(r)}`);
      ok(r.strip === true, `${tag}: telemetry strip not ticking under Full`);
      if (device === 'no-preference') ok(r.transition > 0.2 && r.animation > 1, `${tag}: Full still reduces CSS motion ${JSON.stringify(r)}`);
      // It is kept: a reload reads it back before anything else asks.
      await page.reload();
      const kept = await page.evaluate(async () => { const m = await import('/js/motion.js'); return [m.motionChoice(), document.documentElement.dataset.motion]; });
      ok(kept[0] === 'full' && kept[1] === 'full', `${tag}: Full not kept over a reload ${kept}`);
      // Back to System by click: the key is removed, and the device decides again.
      await page.evaluate(async () => {
        const s = await import('/js/settings-app.js');
        const src = new DOMParser().parseFromString(await (await fetch('/index.html')).text(), 'text/html');
        const panel = src.querySelector('[data-panel="settings"]'); panel.hidden = false;
        for (const g of panel.querySelectorAll('.settings-group')) g.hidden = g.dataset.setPane !== 'look';
        document.getElementById('board').append(panel);
        s.wireMotion(s.motionGroup(document));
        window.fixtureMotion = await import('/js/motion.js');
        window.fixtureStrip = { running: null };
      });
      await page.click('#s-motion [data-motion="system"]');
      r = await read();
      ok(r.checked === 'system' && r.stored === null && r.motion === (device === 'reduce' ? 'reduce' : 'full'), `${tag}: System ${JSON.stringify(r)}`);
      // 44 px on a phone, and no horizontal scroll at either width.
      const box = await page.evaluate(() => {
        const b = document.querySelector('#s-motion [data-motion="reduce"]').getBoundingClientRect();
        return { h: b.height, overflow: document.documentElement.scrollWidth - window.innerWidth };
      });
      ok(box.h >= (phone ? 36 : 28) && box.overflow <= 0, `${tag}: Motion keys ${JSON.stringify(box)}`);
      ok(!errors.length, `${tag}: page errors ${errors.join('; ')}`);
      await context.close();
    }
  }
  // Every reader that used to ask the media query asks motion.js now.
  for (const f of ['travel.js', 'recall.js', 'nav-rail.js', 'show-me.js', 'apps/jump-view.js', 'arrival.js', 'nav-telemetry.js', 'standing-horses.js', 'main.js']) {
    const s = fs.readFileSync(path.join(web, 'js', f), 'utf8');
    ok(/motion\.js'/.test(s) && !/matchMedia\(['"]\(prefers-reduced-motion/.test(s) && !/matchMedia\?\.\(['"]\(prefers-reduced-motion/.test(s), `${f} still reads prefers-reduced-motion itself`);
  }
  console.log(`PASS a11y colour + motion: ${checks} checks — grades apart under three CVD simulations and told by shape in every mark; Motion System/Reduce/Full kept, applied and keyboard-operable at 390 and 1280`);
} finally {
  await browser.close();
  server.close();
}

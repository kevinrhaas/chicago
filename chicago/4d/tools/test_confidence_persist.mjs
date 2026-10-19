#!/usr/bin/env node
// T-2649 (NAV-604): the Confidence view persists and shows a HUD legend.
//
//   - The choices — the colouring, the hidden grades and each grade's look — are kept in
//     ONE record at localStorage['chicago4d.confidence'] that every writer merges into, so
//     none drops another's part (before, the HUD's '1'/'0' and the looks' JSON overwrote
//     each other, and the colouring never survived a reload or a Jump). QA-11: hide
//     Reconstructed, set Attested to 30 %, and the next page — the same year reloaded, or
//     another year after a Jump — boots into both.
//   - Storage refused, nothing breaks and the view opens at Normal.
//   - The legend chip under the year chip shows exactly while the view is not Normal, says
//     each grade's colour in words, and a tap opens the app.
//
// No browser: confidence.js is loaded with `three` pointed at the vendored copy and the
// modules copied beside it, as test_confidence_rows.mjs does. The stand-in HUD keeps the
// colouring and the hidden set through confidence-store.js exactly as js/hud.js does, and
// the source checks at the end hold hud.js, main.js and the page to that.
import assert from 'node:assert/strict';
import { readFile, readdir, mkdtemp, writeFile, mkdir, cp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const vendorDir = (await readdir(path.join(web, 'vendor'))).find((d) => /^three-/.test(d));
const threeURL = pathToFileURL(path.join(web, 'vendor', vendorDir, 'three.module.js')).href;
const tmp = await mkdtemp(path.join(os.tmpdir(), 'persist-'));
const js = path.join(tmp, 'js');
await mkdir(js, { recursive: true });
await writeFile(path.join(js, 'confidence.js'),
  (await readFile(path.join(web, 'js/confidence.js'), 'utf8')).replace("from 'three'", `from '${threeURL}'`));
for (const f of ['confidence-presets.js', 'confidence-rows.js', 'confidence-store.js', 'confidence-legend.js']) {
  await writeFile(path.join(js, f), await readFile(path.join(web, 'js', f), 'utf8'));
}
await cp(path.join(web, 'js/strings'), path.join(js, 'strings'), { recursive: true });
const load = (f) => import(pathToFileURL(path.join(js, f)).href);
const C = await load('confidence.js');
const R = await load('confidence-rows.js');
const P = await load('confidence-presets.js');
const K = await load('confidence-store.js');
const L = await load('confidence-legend.js');
const read = (p) => readFile(path.join(root, p), 'utf8');

const memory = () => {
  const m = new Map();
  return { m, getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) };
};
const refused = { getItem: () => { throw new Error('denied'); }, setItem: () => { throw new Error('denied'); } };

/** One page: the renderer's view and a HUD booted from `storage` as main.js boots them —
 * restoreLooks before the first frame, the hidden set with the settings, the colouring on
 * the way in (hud.restore). The HUD's writes are hud.js's: keepChoices({ on }) and
 * keepChoices({ hidden }). */
function page(storage) {
  const view = C.createConfidenceView();
  P.restoreLooks(view, storage);
  const hidden = new Set(K.readChoices(storage).hidden ?? []);
  for (const l of hidden) view.setHidden(l, true);
  const hud = {
    confidenceOn: false,
    get hiddenLevels() { return [...hidden]; },
    setHidden(level, hide) {
      if (hide) hidden.add(level); else hidden.delete(level);
      view.setHidden(level, hide);
      K.keepChoices({ hidden: [...hidden] }, storage);
      return hide;
    },
    setConfidence(on) { this.confidenceOn = !!on; view.set(on); K.keepChoices({ on: this.confidenceOn }, storage); return this.confidenceOn; },
    restore() { if (K.readChoices(storage).on === true) this.setConfidence(true); },
    say: () => {},
  };
  return { view, hud, storage, deps: { hud, view, storage }, state: () => ({ on: hud.confidenceOn, hidden: hud.hiddenLevels, view }) };
}

let failures = 0;
const check = async (label, fn) => {
  try { await fn(); console.log(`  ok   ${label}`); } catch (err) { failures++; console.log(`  FAIL ${label}\n       ${String(err.message).split('\n')[0]}`); }
};

console.log('T-2649 — the Confidence view persists and shows a HUD legend');

await check('one record at chicago4d.confidence: the colouring, the hidden set and the looks, each write merged', () => {
  const s = memory();
  assert.equal(K.STORE_KEY, 'chicago4d.confidence');
  assert.equal(P.STORE_KEY, K.STORE_KEY, 'the presets keep the same key');
  K.keepChoices({ on: true }, s);
  K.keepChoices({ hidden: ['reconstructed', 'nonsense', 'reconstructed'] }, s);
  K.keepChoices({ looks: { attested: { mode: 'tint', opacity: 0.3, color: '#ffffff' } } }, s);
  const rec = JSON.parse(s.getItem(K.STORE_KEY));
  assert.equal(rec.on, true, 'the looks did not write over the colouring');
  assert.deepEqual(rec.hidden, ['reconstructed'], 'only grade names, once each');
  assert.equal(rec.looks.attested.opacity, 0.3);
  assert.deepEqual(JSON.parse(s.getItem(K.HIDDEN_KEY)), ['reconstructed'], 'the hidden set\'s own key still written, for an older build');
  K.keepChoices({ on: false }, s);
  assert.deepEqual(K.readChoices(s), { on: false, hidden: ['reconstructed'], looks: rec.looks });
});

await check('a field another part of the view adds later (T-2650\'s overlays) is carried by every other write', () => {
  const s = memory();
  K.keepChoices({ overlays: { streetNames: true } }, s);
  K.keepChoices({ on: true }, s);
  K.keepChoices({ hidden: [] }, s);
  P.saveLooks(C.createConfidenceView(), s);
  assert.deepEqual(K.readChoices(s).overlays, { streetNames: true });
});

await check('a visitor from before keeps their choice: the HUD\'s old "1" and the old hidden key are read', () => {
  const s = memory();
  s.setItem(K.STORE_KEY, '1');
  s.setItem(K.HIDDEN_KEY, '["inferred"]');
  assert.deepEqual(K.readChoices(s), { on: true, hidden: ['inferred'] });
  s.setItem(K.STORE_KEY, '0');
  assert.equal(K.readChoices(s).on, false);
  // A looks-only record from T-2647, with the hidden set in its own key.
  s.setItem(K.STORE_KEY, JSON.stringify({ looks: { inferred: { mode: 'ghost', opacity: 0.5 } } }));
  const kept = K.readChoices(s);
  assert.equal(kept.on, undefined, 'no colouring was kept, so none is claimed');
  assert.deepEqual(kept.hidden, ['inferred']);
  assert.equal(kept.looks.inferred.mode, 'ghost');
});

await check('before the fix\'s order: a preset, then a row control, then a reload keeps the colouring on', () => {
  const s = memory();
  const a = page(s);
  P.applyPreset('bygrade', a.deps);           // the HUD switch first, then the looks (saveLooks)
  R.setOpacity(a.deps, 'inferred', 40);
  P.saveLooks(a.view, s);                       // as the row's change event does
  const b = page(s);
  b.hud.restore();
  assert.equal(b.hud.confidenceOn, true, 'the colouring came back');
  assert.equal(R.percentOf(b.view.grade('inferred')), 40);
});

await check('QA-11: hide Reconstructed, Attested at 30 %, reload — both persist; and Jump to another year carries them', async () => {
  const s = memory();
  const a = page(s);
  // As a visitor does it in the app: the Attested row's slider to 30 (it turns the colouring
  // on, as a row control does), its change event keeps the looks; then Reconstructed's Show off.
  R.setOpacity(a.deps, 'attested', 30);
  P.saveLooks(a.view, s);
  a.hud.setHidden('reconstructed', true);
  for (const [why, next] of [['reload', page(s)], ['the next year after a Jump', page(s)]]) {
    // The colouring is restored as the visitor walks in, after the first frame's looks.
    assert.equal(R.percentOf(next.view.grade('attested')), 30, `${why}: Attested at 30 % before the colouring is on`);
    next.hud.restore();
    assert.equal(next.hud.confidenceOn, true, `${why}: the colouring on`);
    assert.deepEqual(next.hud.hiddenLevels, ['reconstructed'], `${why}: Reconstructed hidden`);
    assert.equal(next.view.hidden.reconstructed, true, `${why}: and gone from the renderer`);
    assert.equal(next.view.grade('attested').mode, 'tint');
    assert.equal(L.legendOf(next.state()).shown, true, `${why}: the legend shows`);
  }
  // X-RAY's ghosts and the colour-blind-safe set carry too.
  const x = page(s);
  R.applySet(x.deps, R.SAFE_SET);
  P.applyPreset('xray', x.deps);
  const y = page(s);
  y.hud.restore();
  assert.equal(P.presetOf(y.state()), 'xray');
  assert.equal(R.setInForce(y.view), R.SAFE_SET);
  // And back to Normal is kept as Normal.
  P.applyPreset('normal', y.deps);
  const z = page(s);
  z.hud.restore();
  assert.equal(P.presetOf(z.state()), 'normal');
  assert.equal(L.legendOf(z.state()).shown, false);
});

await check('storage refused or unreadable: nothing throws, and the view opens at Normal', () => {
  for (const s of [refused, { getItem: () => '{not json' }, { getItem: () => '[1,2]', setItem: () => {} }, null]) {
    const a = page(s);
    a.hud.restore();
    assert.equal(P.presetOf(a.state()), 'normal');
    if (s === refused || s === null) assert.equal(K.keepChoices({ on: true }, s), false, 'nothing kept, and it says so');
    assert.doesNotThrow(() => P.applyPreset('xray', a.deps));
    assert.doesNotThrow(() => a.hud.setHidden('inferred', true));
  }
  // A full store (setItem throws) leaves the scene as chosen.
  const full = { getItem: () => null, setItem: () => { throw new Error('QuotaExceededError'); } };
  const f = page(full);
  P.applyPreset('bygrade', f.deps);
  assert.equal(f.hud.confidenceOn, true);
});

await check('the legend shows exactly while the view is not Normal — each preset, and a grade hidden by hand', () => {
  const a = page(memory());
  const shown = (id) => { P.applyPreset(id, a.deps); return L.legendOf(a.state()).shown; };
  assert.equal(shown('normal'), false);
  assert.equal(shown('bygrade'), true);
  assert.equal(shown('attested'), true, 'ATTESTED ONLY is not Normal, with the colouring off');
  assert.equal(shown('xray'), true);
  P.applyPreset('normal', a.deps);
  a.hud.setHidden('inferred', true);
  assert.equal(L.legendOf(a.state()).shown, true);
  assert.equal(K.viewIsOn({}), false);
});

await check('the legend\'s dots and words: the colour each grade wears, a ghost see-through, a hidden grade empty', () => {
  const a = page(memory());
  P.applyPreset('bygrade', a.deps);
  let g = L.legendOf(a.state());
  assert.deepEqual(g.dots.map((d) => d.state), ['tint', 'tint', 'dither']);
  assert.equal(g.dots[0].color, a.view.grade('attested').color);
  assert.equal(g.label, 'Confidence view on: Attested gold, Inferred silver, Reconstructed bronze. Tap to open it.');
  P.applyPreset('xray', a.deps);
  g = L.legendOf(a.state());
  assert.deepEqual(g.dots.map((d) => d.state), ['tint', 'ghost', 'ghost']);
  assert.equal(g.dots[2].opacity, 0.25);
  P.applyPreset('attested', a.deps);
  g = L.legendOf(a.state());
  assert.deepEqual(g.dots.map((d) => d.state), ['plain', 'hidden', 'hidden']);
  assert.equal(g.label, 'Confidence view on: Attested shown, Inferred hidden, Reconstructed hidden. Tap to open it.');
  P.applyPreset('normal', a.deps);
  R.applySet(a.deps, R.SAFE_SET);
  assert.match(L.legendOf(a.state()).label, /Attested blue, Inferred yellow, Reconstructed vermilion/);
  a.view.setGrade('attested', { color: '#123456' });
  assert.match(L.legendOf(a.state()).label, /Attested own colour/);
  assert(!/[a-z]+_[a-z]+|#|\{/.test(L.legendOf(a.state()).label), 'no id, colour code or placeholder in the words');
});

await check('the chip on a stand-in page: hidden at Normal, painted when the view moves, a tap opens the app', () => {
  const listeners = {};
  const doc = { addEventListener: (t, fn) => { (listeners[t] ||= []).push(fn); } };
  const dot = () => { const p = {}; return { dataset: {}, style: { setProperty: (k, v) => { p[k] = v; }, removeProperty: (k) => { delete p[k]; }, get: (k) => p[k] } }; };
  const dots = { attested: dot(), inferred: dot(), reconstructed: dot() };
  const attrs = {};
  let clicked = null, opened = 0;
  const el = { ownerDocument: doc, hidden: true, title: '',
    querySelector: (sel) => dots[/data-grade="(\w+)"/.exec(sel)?.[1]] ?? null,
    setAttribute: (k, v) => { attrs[k] = v; }, addEventListener: (t, fn) => { if (t === 'click') clicked = fn; } };
  const a = page(memory());
  const chip = L.createConfidenceLegend({ el, hud: a.hud, view: a.view, open: () => { opened++; } });
  assert.equal(el.hidden, true, 'Normal: no chip');
  assert.equal(chip.shown, false);
  P.applyPreset('xray', a.deps);
  for (const fn of listeners['chicago4d-confidence'] ?? []) fn();
  assert.equal(el.hidden, false);
  assert.equal(dots.reconstructed.dataset.state, 'ghost');
  assert.equal(dots.reconstructed.style.get('--c'), a.view.grade('reconstructed').color);
  assert.equal(dots.reconstructed.style.get('--a'), '0.3', 'a 25 % ghost dot is never fainter than 30 %');
  assert.match(attrs['aria-label'], /^Confidence view on: /);
  assert.equal(el.title, attrs['aria-label']);
  clicked();
  assert.equal(opened, 1, 'a tap opens the Confidence view');
  P.applyPreset('normal', a.deps);
  chip.paint();
  assert.equal(el.hidden, true);
});

await check('the wiring: hud.js keeps its part in the record, main.js binds the chip, the page holds it under the year chip', async () => {
  const hud = await read('renderers/web/js/hud.js');
  assert.match(hud, /keepChoices\(\{ on: confidenceOn \}\)/, 'the colouring is merged into the record');
  assert.match(hud, /keepChoices\(\{ hidden: \[\.\.\.hiddenLevels\] \}\)/, 'and the hidden set');
  assert.match(hud, /if \(readChoices\(\)\.on === true\) setConfidence\(true, \{ announce: false \}\)/, 'restored on the way in');
  assert.match(hud, /readChoices\(\)\.hidden/, 'the hidden set read from the record');
  assert(!/store\(CONF_KEY/.test(hud) && !/CONF_KEY = /.test(hud), 'no second writer of the key');
  const main = await read('renderers/web/js/main.js');
  assert.match(main, /createConfidenceLegend\(\{ el: document\.getElementById\('conf-legend'\), hud, view: confidence,\s*open: \(\) => \{ void navigatorUi\?\.select\('confidence'\); \} \}\)/);
  assert(main.indexOf('restoreLooks(confidence, safeStorage())') < main.indexOf('hud.applyHidden();'), 'the looks before the first frame');
  const html = await read('renderers/web/index.html');
  const chips = html.slice(html.indexOf('<div class="hud-chips">'), html.indexOf('<div class="hud-actions">'));
  assert(chips.indexOf('id="year-badge"') > 0 && chips.indexOf('id="conf-legend"') > chips.indexOf('id="year-badge"'), 'the legend comes after the year chip, in its column');
  assert.match(chips, /<button type="button" class="conf-legend" id="conf-legend" hidden /, 'hidden until the view is on');
  for (const l of R.LEVELS) assert(chips.includes(`data-grade="${l}"`), `a dot for ${l}`);
  const css = await read('renderers/web/css/walk.css');
  assert.match(css, /\.conf-legend\[hidden\] \{ display: none; \}/);
  assert.match(css, /\.hud-chips \{ display: flex; flex-direction: column;/, 'under the year chip on a phone');
});

await rm(tmp, { recursive: true, force: true });
if (failures) { console.log(`\n${failures} check(s) failed`); process.exit(1); }
console.log('\nall checks passed');

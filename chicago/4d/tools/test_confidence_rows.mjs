#!/usr/bin/env node
// T-2648 (NAV-602): the Confidence view's per-grade rows — Show, four curated swatches with
// a colour-blind-safe set, Look (Tint, Ghost, Dither), opacity 0-100 % and a count per grade.
//
// No browser. confidence.js is loaded with `three` pointed at the vendored copy; the rows,
// the presets, the string table and the app itself (apps/confidence-view.js) are copied
// beside it in their own tree, so they share one module instance, and the app is mounted on
// a small stand-in document over the real renderer view and a stand-in HUD.
import assert from 'node:assert/strict';
import { readFile, readdir, mkdtemp, writeFile, mkdir, cp, rm } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const vendorDir = (await readdir(path.join(web, 'vendor'))).find((d) => /^three-/.test(d));
const threeURL = pathToFileURL(path.join(web, 'vendor', vendorDir, 'three.module.js')).href;
const tmp = await mkdtemp(path.join(os.tmpdir(), 'rows-'));
const js = path.join(tmp, 'js');
await mkdir(path.join(js, 'apps'), { recursive: true });
await writeFile(path.join(js, 'confidence.js'),
  (await readFile(path.join(web, 'js/confidence.js'), 'utf8')).replace("from 'three'", `from '${threeURL}'`));
for (const f of ['confidence-presets.js', 'confidence-rows.js', 'confidence-store.js', 'apps/confidence-view.js']) {
  await writeFile(path.join(js, f), await readFile(path.join(web, 'js', f), 'utf8'));
}
// T-2660: the app counts a preset picked in the field log, which it imports.
await writeFile(path.join(js, 'field-log.js'), await readFile(path.join(web, 'js/field-log.js'), 'utf8'));
await cp(path.join(web, 'js/strings'), path.join(js, 'strings'), { recursive: true });
// T-2650: the app mounts its overlays at its foot, with the naming they reuse.
for (const f of ['confidence-overlays.js', 'display-name.js', 'fallback-summary.js', 'range-words.js']) await writeFile(path.join(js, f), await readFile(path.join(web, 'js', f), 'utf8'));
const load = (f) => import(pathToFileURL(path.join(js, f)).href);
const THREE = await import(threeURL);
const C = await load('confidence.js');
const R = await load('confidence-rows.js');
const P = await load('confidence-presets.js');
const S = await load('strings/index.js');
const V = await load('apps/confidence-view.js');

// ---- colour arithmetic: the same measure tools/check_grade_colors.mjs holds the defaults to
const hexRgb = (h) => { const s = String(h).replace(/^#/, ''); return [0, 2, 4].map((i) => parseInt(s.slice(i, i + 2), 16) / 255); };
const lin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const unlin = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055);
function lab(c) {
  const [r, g, b] = c.map(lin);
  const X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047;
  const Y = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  const Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883;
  const f = (t) => (t > 216 / 24389 ? Math.cbrt(t) : (24389 / 27 * t + 16) / 116);
  return [116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))];
}
const dE = (a, b) => Math.hypot(...lab(a).map((v, i) => v - lab(b)[i]));
// Machado, Oliveira & Fernandes (2009), severity 1.0 — as check_grade_colors.mjs.
const CVD = {
  protanopia: [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
  deuteranopia: [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]],
  tritanopia: [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]],
};
const simulate = (c, m) => { const l = c.map(lin); return m.map((row) => unlin(Math.min(1, Math.max(0, row[0] * l[0] + row[1] * l[1] + row[2] * l[2])))); };
const MIN_DE = 12;

function standIn() {
  const said = [];
  const view = C.createConfidenceView();
  const hidden = new Set();
  let changes = 0;
  const hud = {
    confidenceOn: false,
    get hiddenLevels() { return [...hidden]; },
    setHidden(level, hide) { if (hide) hidden.add(level); else hidden.delete(level); view.setHidden(level, hide); changes++; return hide; },
    setConfidence(on) { this.confidenceOn = !!on; view.set(on); changes++; return this.confidenceOn; },
    levelCounts: () => ({ attested: 12, inferred: 34, reconstructed: 190 }),
    say: (t) => said.push(t),
  };
  const store = new Map();
  const storage = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, String(v)) };
  return { view, hud, storage, said, changes: () => changes, state: () => ({ on: hud.confidenceOn, hidden: hud.hiddenLevels, view }) };
}
let failures = 0;
const check = async (label, fn) => {
  try { await fn(); console.log(`  ok   ${label}`); } catch (err) { failures++; console.log(`  FAIL ${label}\n       ${String(err.message).split('\n')[0]}`); }
};

console.log('T-2648 — the Confidence view per-grade rows');

await check('four swatches per grade, the first the grade colour (gold, silver, bronze), one set colour-blind safe', () => {
  assert.equal(R.SWATCH_SETS.length, 4);
  for (const level of R.LEVELS) {
    const sw = R.swatchesOf(level);
    assert.equal(sw.length, 4, level);
    assert.equal(sw[0].hex, `#${C.GRADE_COLORS[level].scene.toString(16).padStart(6, '0')}`, `${level}'s default is GRADE_COLORS`);
    for (const s of sw) assert.match(s.hex, /^#[0-9a-f]{6}$/, `${level} ${s.name}`);
  }
  assert.deepEqual(R.SWATCH_SETS.filter((s) => s.colourBlindSafe).map((s) => s.id), [R.SAFE_SET]);
  assert.equal(R.DEFAULT_SET, R.SWATCH_SETS[0].id);
});

await check('the colour-blind-safe set stays apart under protanopia, deuteranopia and tritanopia', () => {
  const safe = R.setById(R.SAFE_SET).colours;
  const pairs = [['attested', 'inferred'], ['attested', 'reconstructed'], ['inferred', 'reconstructed']];
  for (const vision of ['normal', ...Object.keys(CVD)]) {
    const see = (h) => (vision === 'normal' ? hexRgb(h) : simulate(hexRgb(h), CVD[vision]));
    for (const [a, b] of pairs) {
      const d = dE(see(safe[a]), see(safe[b]));
      assert.ok(d >= MIN_DE, `${vision}: ${a} ${safe[a]} and ${b} ${safe[b]} are ΔE ${d.toFixed(1)} apart (needs ${MIN_DE})`);
    }
  }
});

await check('every set keeps its three grades apart, and every row its four swatches, to ordinary vision', () => {
  for (const s of R.SWATCH_SETS) {
    const c = s.colours;
    for (const [a, b] of [['attested', 'inferred'], ['attested', 'reconstructed'], ['inferred', 'reconstructed']]) {
      assert.ok(dE(hexRgb(c[a]), hexRgb(c[b])) >= MIN_DE, `${s.id}: ${a} and ${b}`);
    }
  }
  for (const level of R.LEVELS) {
    const sw = R.swatchesOf(level);
    for (let i = 0; i < sw.length; i++) for (let j = i + 1; j < sw.length; j++) {
      assert.ok(dE(hexRgb(sw[i].hex), hexRgb(sw[j].hex)) >= MIN_DE, `${level}: ${sw[i].name} and ${sw[j].name}`);
    }
  }
});

await check('every swatch, look and row word is in the string table, and none is an id', () => {
  for (const level of R.LEVELS) for (const sw of R.swatchesOf(level)) assert.ok(S.has(`confidence.swatch.${sw.name}`), sw.name);
  for (const mode of R.LOOKS) { assert.ok(S.has(`confidence.look.${mode}`)); assert.ok(S.has(`confidence.look.${mode}.note`)); }
  assert.deepEqual(R.LOOKS, ['tint', 'ghost', 'dither']);
  for (const [k, v] of S.entries().filter(([k]) => k.startsWith('confidence.'))) assert.doesNotMatch(v, /[a-z]+_[a-z]+|\bcm-|#[0-9a-f]{3,6}\b/, k);
});

await check('each swatch reads back as itself off the renderer (the hex survives the colour space)', () => {
  const s = standIn();
  for (const set of R.SWATCH_SETS) {
    for (const level of R.LEVELS) {
      assert.ok(R.setSwatch(s, level, set.id));
      assert.equal(R.swatchOf(s.view, level), set.id, `${level} ${set.id}`);
    }
    assert.equal(R.setInForce(s.view), set.id);
  }
  s.view.setGrade('inferred', { color: '#123456' });
  assert.equal(R.swatchOf(s.view, 'inferred'), null, 'a stray colour is no swatch');
  assert.equal(R.setInForce(s.view), null);
});

await check('a swatch, a look or an opacity changes the scene: the colouring comes on, and a hidden grade is shown', () => {
  const s = standIn();
  s.hud.setHidden('reconstructed', true);
  const before = s.view.uniforms.uTintReconstructed.value.clone();
  R.setSwatch(s, 'reconstructed', 'ember');
  assert.equal(s.hud.confidenceOn, true, 'the colouring came on');
  assert.deepEqual(s.hud.hiddenLevels, [], 'the grade is shown again');
  assert.ok(!s.view.uniforms.uTintReconstructed.value.equals(before), 'its tint uniform moved');
  const t = standIn();
  R.setLook(t, 'attested', 'ghost');
  assert.equal(t.hud.confidenceOn, true);
  assert.equal(t.view.grade('attested').mode, 'ghost');
  assert.equal(t.view.uniforms.uGradeMode.value.x, C.GRADE_MODES.ghost);
  const u = standIn();
  R.setOpacity(u, 'inferred', 35);
  assert.equal(u.hud.confidenceOn, true);
  assert.equal(u.view.uniforms.uGradeOpacity.value.y.toFixed(2), '0.35');
});

await check('opacity is a whole percent from 0 to 100; a bad look or value is refused and changes nothing', () => {
  const s = standIn();
  R.setOpacity(s, 'attested', 140); assert.equal(R.percentOf(s.view.grade('attested')), 100);
  R.setOpacity(s, 'attested', -5); assert.equal(R.percentOf(s.view.grade('attested')), 0);
  R.setOpacity(s, 'attested', '42.6'); assert.equal(R.percentOf(s.view.grade('attested')), 43);
  const before = JSON.stringify(s.view.grade('attested'));
  assert.equal(R.setOpacity(s, 'attested', 'lots'), null);
  assert.equal(R.setLook(s, 'attested', 'sparkle'), null);
  assert.equal(R.setSwatch(s, 'attested', 'neon'), null);
  assert.equal(R.setLook(s, 'certain', 'tint'), null);
  assert.equal(JSON.stringify(s.view.grade('attested')), before);
});

await check('the colour-blind-safe set goes on all three grades in one, and every preset keeps it', () => {
  const s = standIn();
  assert.equal(R.applySet(s, R.SAFE_SET), R.SAFE_SET);
  assert.equal(s.hud.confidenceOn, true);
  assert.equal(R.setInForce(s.view), R.SAFE_SET);
  for (const id of ['xray', 'bygrade', 'normal', 'attested']) {
    P.applyPreset(id, s);
    assert.equal(R.setInForce(s.view), R.SAFE_SET, `${id} kept the set`);
    s.hud.setConfidence(true);
    if (id === 'xray') assert.equal(P.presetOf(s.state()), 'xray', 'X-RAY in the safe set is still X-RAY');
  }
  P.toggleByGrade(s); P.toggleByGrade(s);
  assert.equal(R.setInForce(s.view), R.SAFE_SET, 'so does C');
  P.applyPreset('bygrade', s);
  assert.equal(s.said.at(-1), 'By grade', 'BY GRADE does not name gold under another set');
});

await check('a mix of sets is the visitor\'s own: no preset matches it, and a preset puts the grade colours back', () => {
  const s = standIn();
  P.applyPreset('bygrade', s);
  R.setSwatch(s, 'attested', 'garden');
  assert.equal(P.presetOf(s.state()), null);
  P.applyPreset('bygrade', s);
  assert.equal(R.setInForce(s.view), R.DEFAULT_SET);
  assert.equal(P.presetOf(s.state()), 'bygrade');
});

await check('no row control rebuilds anything: no material recompiles, no geometry is touched, and an opacity drag never walks the scene', () => {
  const s = standIn();
  const scene = new THREE.Scene();
  const geometry = new THREE.BoxGeometry(1, 1, 1);
  const n = geometry.getAttribute('position').count;
  const conf = new Float32Array(n); for (let i = 0; i < n; i++) conf[i] = i % 2 ? 1 : 0.5;
  geometry.setAttribute('_confidence', new THREE.BufferAttribute(conf, 1));
  const material = s.view.patch(new THREE.MeshStandardMaterial());
  scene.add(new THREE.Mesh(geometry, material));
  const renderer = { render() {}, info: { render: { calls: 0 }, autoReset: true }, shadowMap: { autoUpdate: true, needsUpdate: false }, autoClear: true };
  const camera = new THREE.PerspectiveCamera();
  let walks = 0;
  const traverse = scene.traverse.bind(scene);
  scene.traverse = (fn) => { walks++; return traverse(fn); };
  R.setLook(s, 'reconstructed', 'ghost');
  s.view.render(renderer, scene, camera);
  const version = material.version;
  const versions = Object.values(geometry.attributes).map((a) => a.version);
  const walked = walks;
  assert.ok(walked >= 1, 'the first ghosted frame walks the scene once (else this check measures nothing)');
  for (let p = 0; p <= 100; p += 5) { R.setOpacity(s, 'reconstructed', p); s.view.render(renderer, scene, camera); }
  for (const set of R.SWATCH_SETS) { R.setSwatch(s, 'reconstructed', set.id); s.view.render(renderer, scene, camera); }
  assert.equal(walks, walked, 'an opacity drag and the swatches walked the scene again');
  for (const mode of R.LOOKS) { R.setLook(s, 'inferred', mode); s.view.render(renderer, scene, camera); }
  assert.equal(material.version, version, 'a row control asked for a recompile');
  assert.deepEqual(Object.values(geometry.attributes).map((a) => a.version), versions, 'a row control rewrote geometry');
});

// ---- the app, mounted on a stand-in document ----------------------------------------- //
class El {
  constructor(tag, doc) {
    Object.assign(this, { tagName: tag.toUpperCase(), ownerDocument: doc, children: [], attrs: {}, dataset: {}, listeners: {},
      id: '', className: '', type: '', title: '', checked: false, value: '', hidden: false, min: '', max: '', step: '', htmlFor: '', _text: '' });
    const props = {};
    this.style = { setProperty: (k, v) => { props[k] = String(v); }, getPropertyValue: (k) => props[k] ?? '' };
    const el = this;
    this.classList = {
      toggle(c, on) { const set = new Set(el.className.split(/\s+/).filter(Boolean)); if (on ?? !set.has(c)) set.add(c); else set.delete(c); el.className = [...set].join(' '); },
      contains: (c) => el.className.split(/\s+/).includes(c),
    };
  }
  append(...kids) { for (const k of kids) this.children.push(typeof k === 'string' ? Object.assign(new El('#text', this.ownerDocument), { _text: k }) : k); }
  replaceChildren() { this.children = []; }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k] ?? null; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  fire(type) { for (const fn of this.listeners[type] || []) fn({ type, target: this }); }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(''); }
  set textContent(v) { this._text = String(v); this.children = []; }
  *walk() { yield this; for (const c of this.children) yield* c.walk(); }
}
function mountApp() {
  const listeners = {};
  const doc = { activeElement: null, addEventListener: (t, fn) => { listeners[t] = fn; }, removeEventListener: () => {} };
  doc.createElement = (tag) => new El(tag, doc);
  const el = new El('div', doc);
  const s = standIn();
  V.mount(el, { api: { hud: s.hud, confidence: s.view, registry: { size: 236 }, stats: () => ({ fps: 58 }) } });
  const all = () => [...el.walk()];
  const q = (fn) => all().find(fn);
  const byId = (id) => q((n) => n.id === id);
  return { el, s, all, q, byId, repaint: () => listeners['chicago4d-confidence']?.() };
}

await check('the app: a row per grade with its Show switch (ids kept), its count, and one row opened at a time', () => {
  const { el, all, byId, q } = mountApp();
  try {
    for (const level of R.LEVELS) {
      assert.ok(byId(`cm-${level}`), `#cm-${level} kept`);
      assert.equal(byId(`cm-count-${level}`).textContent, String({ attested: 12, inferred: 34, reconstructed: 190 }[level]));
    }
    assert.ok(byId('cm-reset') && byId('cm-note') && byId('cm-safe'));
    const open = () => R.LEVELS.filter((l) => !byId(`cm-controls-${l}`).hidden);
    assert.deepEqual(open(), ['reconstructed'], 'Reconstructed opens first, as M9 draws it');
    byId('cm-look-attested').fire('click');
    assert.deepEqual(open(), ['attested']);
    assert.equal(byId('cm-look-attested').getAttribute('aria-expanded'), 'true');
    byId('cm-look-attested').fire('click');
    assert.deepEqual(open(), [], 'and closes again');
    byId('cm-look-reconstructed').fire('click');
    const words = all().flatMap((n) => [n.tagName === '#TEXT' ? n._text : '', n.title, n.attrs['aria-label'] ?? '']).filter(Boolean);
    for (const w of words) assert.doesNotMatch(w, /[a-z]+_[a-z]+|\bcm-|#[0-9a-f]{6}\b|undefined|\{/, w);
    assert.equal(q((n) => n.className.includes('nav-readout')).textContent, 'GRADE MASK 3/3MESHES 236FRAME CLK 58');
  } finally { V.unmount(el); }
});

await check('the app: a swatch tap, a Look tap and the slider each reach the renderer, and the row says so', () => {
  const { el, s, all, byId } = mountApp();
  try {
    const row = all().find((n) => n.dataset.grade === 'inferred');
    byId('cm-look-inferred').fire('click');
    const swatches = [...row.walk()].filter((n) => n.className === 'nav-swatch');
    assert.equal(swatches.length, 4);
    swatches.find((n) => n.dataset.set === 'garden').fire('click');
    assert.equal(R.swatchOf(s.view, 'inferred'), 'garden');
    assert.equal(s.hud.confidenceOn, true);
    assert.equal(swatches.find((n) => n.dataset.set === 'garden').getAttribute('aria-checked'), 'true');
    assert.equal(swatches.find((n) => n.dataset.set === 'medal').getAttribute('aria-checked'), 'false');
    [...row.walk()].find((n) => n.dataset.look === 'ghost').fire('click');
    assert.equal(s.view.grade('inferred').mode, 'ghost');
    const slider = byId('cm-opacity-inferred');
    slider.value = '35'; slider.fire('input'); slider.fire('change');
    assert.equal(R.percentOf(s.view.grade('inferred')), 35);
    assert.equal(byId('cm-look-inferred').textContent, 'Ghost · 35%');
  } finally { V.unmount(el); }
});

await check('the app: the colour-blind-safe switch puts the set on all three grades and reads pressed', () => {
  const { el, s, byId } = mountApp();
  try {
    assert.equal(byId('cm-safe').getAttribute('aria-pressed'), 'false');
    byId('cm-safe').fire('click');
    for (const level of R.LEVELS) assert.equal(R.swatchOf(s.view, level), R.SAFE_SET, level);
    assert.equal(byId('cm-safe').getAttribute('aria-pressed'), 'true');
    assert.match(s.said.at(-1), /^Colour-blind-safe colours on$/);
  } finally { V.unmount(el); }
});

await rm(tmp, { recursive: true, force: true });
if (failures) { console.log(`\n${failures} check(s) failed`); process.exit(1); }
console.log('\nall checks passed');

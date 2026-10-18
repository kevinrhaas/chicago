#!/usr/bin/env node
// T-2647 (NAV-601): the Confidence view's presets — NORMAL, BY GRADE, ATTESTED ONLY, X-RAY —
// over the real renderer view (js/confidence.js) and a stand-in HUD that keeps the
// colouring switch and the hidden set the way js/hud.js does.
//
// No browser: confidence.js is loaded with `three` pointed at the vendored copy, and
// confidence-presets.js (and confidence-rows.js, T-2648) beside it, importing it.
import assert from 'node:assert/strict';
import { readFile, readdir, mkdtemp, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const vendorDir = (await readdir(path.join(web, 'vendor'))).find((d) => /^three-/.test(d));
const threeURL = pathToFileURL(path.join(web, 'vendor', vendorDir, 'three.module.js')).href;
const tmp = await mkdtemp(path.join(os.tmpdir(), 'presets-'));
const conf = (await readFile(path.join(web, 'js/confidence.js'), 'utf8')).replace("from 'three'", `from '${threeURL}'`);
await writeFile(path.join(tmp, 'confidence.js'), conf);
await writeFile(path.join(tmp, 'confidence-presets.js'), await readFile(path.join(web, 'js/confidence-presets.js'), 'utf8'));
// T-2648: the presets keep the curated swatch set in force (confidence-rows.js).
await writeFile(path.join(tmp, 'confidence-rows.js'), await readFile(path.join(web, 'js/confidence-rows.js'), 'utf8'));
const C = await import(pathToFileURL(path.join(tmp, 'confidence.js')).href);
const P = await import(pathToFileURL(path.join(tmp, 'confidence-presets.js')).href);

function standIn() {
  const said = [];
  const view = C.createConfidenceView();
  const hidden = new Set();
  const hud = {
    confidenceOn: false,
    get hiddenLevels() { return [...hidden]; },
    setHidden(level, hide) { if (hide) hidden.add(level); else hidden.delete(level); view.setHidden(level, hide); return hide; },
    setConfidence(on) { this.confidenceOn = !!on; view.set(on); return this.confidenceOn; },
    say: (t) => said.push(t),
  };
  const store = new Map();
  const storage = { getItem: (k) => store.get(k) ?? null, setItem: (k, v) => store.set(k, String(v)) };
  return { view, hud, storage, said, state: () => ({ on: hud.confidenceOn, hidden: hud.hiddenLevels, view }) };
}
let failures = 0;
const check = (label, fn) => {
  try { fn(); console.log(`  ok   ${label}`); } catch (err) { failures++; console.log(`  FAIL ${label}\n       ${String(err.message).split('\n')[0]}`); }
};

console.log('T-2647 — the Confidence view presets');

check('four presets, in the design\'s order, each with a plain note', () => {
  assert.deepEqual(P.PRESETS.map((p) => p.id), ['normal', 'bygrade', 'attested', 'xray']);
  assert.deepEqual(P.PRESETS.map((p) => p.label), ['Normal', 'By grade', 'Attested only', 'X-ray']);
  for (const p of P.PRESETS) assert.ok(p.note.length > 0 && !/[_#]/.test(p.note));
});

check('the scene starts in NORMAL', () => {
  const s = standIn();
  assert.equal(P.presetOf(s.state()), 'normal');
});

check('BY GRADE: the colouring on, nothing hidden, the default looks — the view as it always was', () => {
  const s = standIn();
  assert.equal(P.applyPreset('bygrade', s), 'bygrade');
  assert.equal(s.hud.confidenceOn, true);
  assert.deepEqual(s.hud.hiddenLevels, []);
  assert.deepEqual(s.view.modes, { attested: 'tint', inferred: 'tint', reconstructed: 'dither' });
  assert.equal(P.presetOf(s.state()), 'bygrade');
});

check('ATTESTED ONLY is exactly hiding Inferred and Reconstructed by hand, colour off (QA-12)', () => {
  const a = standIn(), b = standIn();
  P.applyPreset('attested', a);
  b.hud.setHidden('inferred', true); b.hud.setHidden('reconstructed', true);
  assert.deepEqual(a.view.uniforms.uHideLevel.value.toArray(), [0, 1, 1]);
  assert.deepEqual(a.view.uniforms.uHideLevel.value.toArray(), b.view.uniforms.uHideLevel.value.toArray());
  assert.equal(a.view.uniforms.uConfMode.value, b.view.uniforms.uConfMode.value);
  assert.equal(P.presetOf(b.state()), 'attested', 'and hiding them by hand reads as the preset');
});

check('X-RAY: Attested solid, Inferred ghosted at 50 %, Reconstructed ghosted at 25 %', () => {
  const s = standIn();
  P.applyPreset('xray', s);
  assert.deepEqual(s.view.modes, { attested: 'tint', inferred: 'ghost', reconstructed: 'ghost' });
  assert.equal(s.view.grade('inferred').opacity.toFixed(2), '0.50');
  assert.equal(s.view.grade('reconstructed').opacity.toFixed(2), '0.25');
  assert.equal(s.view.ghosting, true);
  assert.equal(P.presetOf(s.state()), 'xray');
});

check('NORMAL after X-RAY puts the looks back, so BY GRADE later is BY GRADE', () => {
  const s = standIn();
  P.applyPreset('xray', s);
  P.applyPreset('normal', s);
  assert.equal(s.hud.confidenceOn, false);
  assert.equal(s.view.ghosting, false);
  s.hud.setConfidence(true);
  assert.equal(P.presetOf(s.state()), 'bygrade', 'turning the colouring on by itself is BY GRADE again');
});

check('a state no preset matches presses none', () => {
  const s = standIn();
  P.applyPreset('bygrade', s);
  s.view.setGrade('attested', { mode: 'dither', opacity: 0.4 });
  assert.equal(P.presetOf(s.state()), null);
  s.view.setGrade('attested', { mode: 'tint', opacity: 0.62, color: '#00ff00' });
  assert.equal(P.presetOf(s.state()), null, 'a changed colour is not the preset either');
  P.applyPreset('normal', s);
  s.hud.setHidden('reconstructed', true);
  assert.equal(P.presetOf(s.state()), null);
});

check('C toggles BY GRADE on, and from any coloured state back to NORMAL', () => {
  const s = standIn();
  assert.equal(P.toggleByGrade(s), 'bygrade');
  assert.equal(P.toggleByGrade(s), 'normal');
  P.applyPreset('xray', s);
  assert.equal(P.toggleByGrade(s), 'normal');
  assert.equal(s.view.ghosting, false);
});

check('the looks persist in chicago4d.confidence and come back at the next boot', () => {
  const s = standIn();
  P.applyPreset('xray', s);
  assert.ok(JSON.parse(s.storage.getItem(P.STORE_KEY)).looks.reconstructed.mode === 'ghost');
  const next = C.createConfidenceView();
  assert.equal(P.restoreLooks(next, s.storage), true);
  assert.deepEqual(next.modes, { attested: 'tint', inferred: 'ghost', reconstructed: 'ghost' });
  assert.equal(P.restoreLooks(C.createConfidenceView(), { getItem: () => '{not json' }), false, 'a bad stored value is ignored');
  assert.equal(P.restoreLooks(C.createConfidenceView(), { getItem: () => { throw new Error('denied'); } }), false, 'refused storage is ignored');
});

check('a preset announces itself in words, and an unknown one does nothing', () => {
  const s = standIn();
  P.applyPreset('attested', s);
  assert.match(s.said.at(-1), /^Attested only: Only the parts somebody wrote down\.$/);
  assert.equal(P.applyPreset('everything', s), null);
});

if (failures) { console.log(`\n${failures} check(s) failed`); process.exit(1); }
console.log('\nall checks passed');

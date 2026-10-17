#!/usr/bin/env node
// T-2633 (NAV-403b): Go to follows the Confidence view. The "Include reconstructed roofs"
// checkbox is gone; every roof is listed, and a row whose grade the Confidence view hides
// is dimmed with a one-line reason, then itself again once the grade is shown. Drives the
// real goto.js over a stub panel and the real destinations inventory; the smoke (part 13)
// hides Reconstructed in a page and reads both Go to lists.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createDestinations } from '../renderers/web/js/destinations.js';
import { createGoTo, hiddenReason } from '../renderers/web/js/goto.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

assert.equal(hiddenReason('reconstructed'), 'Reconstructed is hidden in the Confidence view, so it is not drawn in the town now.',
  'one line, in the locked terms');
assert.match(hiddenReason('inferred'), /^Inferred is hidden in the Confidence view/);

// ---- the real Go to over a stub panel ---------------------------------------------------------
const stub = (extra = {}) => ({ textContent: '', innerHTML: '', value: '', dataset: {}, hidden: false, disabled: false,
  setAttribute() {}, removeAttribute() {}, hasAttribute: () => false, addEventListener() {}, querySelectorAll: () => [],
  querySelector: () => stub(), classList: { toggle() {}, add() {}, remove() {} }, closest: () => null, ...extra });
const results = stub();
results.querySelectorAll = () => Array.from({ length: (results.innerHTML.match(/class="jump-result/g) ?? []).length }, () => stub());
const els = { '#jump-search': stub(), '#jump-results': results, '#jump-count': stub(), '#jump-note': stub() };
let html = '';
const root = stub({ classList: { toggle() {} }, set innerHTML(v) { html = v; }, get innerHTML() { return html; },
  querySelector: (sel) => els[sel] ?? null, querySelectorAll: () => [] });
const realInterval = globalThis.setInterval;
globalThis.setInterval = () => 0;
globalThis.document = { hidden: false };
const terrain = { surfaceHeight: () => 2, isWater: () => false };
const record = (name, fn, e, n, confidence) => ({ sidecar: { name, attributes: { function: { value: fn } }, documented_range: { confidence },
  placement: { local_e: e, local_n: n, position_confidence: confidence } } });
const destinations = createDestinations({ terrain, router: null, people: null, index: { intersections: [] }, scene: { anchors: [] },
  registry: new Map([['peck_store', record("Peck's Store", 'store', 0, 0, 'attested')],
    ['workshop', record('A workshop', 'cooper_shop', 80, 70, 'reconstructed')]]) });
let hidden = [];
const goTo = createGoTo({ root, destinations, visitor: () => ({ e: 0, n: 0, bearingDeg: 0 }), hiddenGrades: () => hidden });
globalThis.setInterval = realInterval;
assert(!/jump-reconstructed|Include reconstructed roofs/.test(html), 'the checkbox is gone');
assert.equal(typeof goTo.setIncludeReconstructed, 'undefined', 'and so is its setter');
const rowsOf = () => [...els['#jump-results'].innerHTML.matchAll(/<button[^>]*data-jump-id="([^"]+)"[^>]*>([\s\S]*?)<\/button>/g)]
  .map(([whole, id, body]) => ({ id, dimmed: /is-hidden-grade/.test(whole) && /data-jump-hidden="true"/.test(whole), why: /class="jump-why"/.test(body) }));
goTo.paint('');
let rows = rowsOf().filter((r) => r.id === 'workshop' || r.id === 'peck_store');
assert(rows.some((r) => r.id === 'workshop'), 'every roof is listed, the reconstructed one too');
assert(rows.every((r) => !r.dimmed && !r.why), 'nothing hidden in the Confidence view: nothing dimmed');
assert.match(els['#jump-note'].textContent, /structures — every one listed/);
hidden = ['reconstructed'];
goTo.paint('');
rows = rowsOf();
const shop = rows.filter((r) => r.id === 'workshop');
assert(shop.length && shop.every((r) => r.dimmed && r.why), `Reconstructed hidden: the reconstructed rows are dimmed with the reason ${JSON.stringify(rows)}`);
assert(rows.filter((r) => r.id === 'peck_store').every((r) => !r.dimmed), 'an attested place is not');
assert.match(els['#jump-note'].textContent, /the reconstructed ones are dimmed, because the Confidence view is hiding them/);
hidden = [];
goTo.paint('');
assert(rowsOf().every((r) => !r.dimmed), 'shown again when the grade is shown');

// ---- the wiring: one choice for what you see -------------------------------------------------
const hud = read('renderers/web/js/hud.js');
assert(/hiddenGrades: \(\) => \[\.\.\.hiddenLevels\]/.test(hud), 'the drawer\'s Go to reads the Confidence view');
assert(/afterHide\?\.\(\);/.test(hud) && /afterHide = \(\) => goTo\.paint\(\);/.test(hud), 'and repaints when it changes');
assert(!/gotoReconstructed: false/.test(hud), 'the checkbox\'s setting is gone');
const main = read('renderers/web/js/main.js');
assert(/hiddenGrades: \(\) => hud\.hiddenLevels,/.test(main), 'the Navigator\'s Go to reads it too');
assert(/onHideLevel: \(level, hide\) => \{[^}]*api\.welcome\?\.refresh\?\.\(\); \}/.test(main), 'and repaints when it changes');
const welcome = read('renderers/web/js/welcome.js');
assert(/button\.classList\.add\('is-hidden-grade'\)/.test(welcome) && /why\.textContent = hiddenReason\(row\.presence\)/.test(welcome));
assert(!/jump-reconstructed/.test(read('tools/smoke_renderer.mjs').replace(/const noCheckbox = !document\.getElementById\('jump-reconstructed'\);/, '')),
  'no smoke step depends on the checkbox');

console.log('test_goto_confidence: no checkbox; Go to dims what the Confidence view hides, with the reason, and restores it');

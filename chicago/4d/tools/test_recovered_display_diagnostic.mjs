// SPDX-License-Identifier: GPL-3.0-or-later
// Real blackbox navigation records and the actual smoke predicate; no browser.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { createBlackbox, wasCut, summary, report } from '../renderers/web/js/blackbox.js';

const source = readFileSync(new URL('./smoke_renderer.mjs', import.meta.url), 'utf8');
const match = source.match(/^function recoveredDisplayDiagnostic\(state, priorPage\) \{[\s\S]*?^\}/m);
assert(match, 'the actual browser smoke must declare its recovery diagnostic predicate');
const accepts = vm.runInNewContext(`(${match[0]})`);
const records = new Map();
const store = {
  getItem: key => records.get(key) ?? null,
  setItem: (key, value) => records.set(key, value),
};
let time = 10_000;
const now = () => time;
function navigate(previous, detail) {
  previous?.end('left');
  const box = createBlackbox({ year: '1835', store, now });
  box.log('boot', { to: `${detail}@1` });
  return box;
}
function diagnostic(box) {
  return {
    notice: summary(box.previous),
    text: summary(box.previous),
    readable: true,
    reloadButton: false,
    diagnostic: {
      previousLost: box.previous.entries.some(entry => entry.k === 'lost'),
      previousPage: box.previous.page,
      currentPage: box.box.page,
      copyVisible: true,
      copyMatchesPrevious: report(box.previous) === JSON.stringify(box.previous),
    },
  };
}

let box = navigate(null, 'balanced');
box.log('ready');
time += 142_500;
box.log('lost');
box.log('restored');
const firstPage = box.box.page;
box = navigate(box, 'balanced');
assert.equal(wasCut(box.previous, time), true,
  'the actual blackbox retains a recent lost-context record after a clean reload');
const expected = diagnostic(box);
assert.equal(accepts(expected, firstPage), true);
const failures = [
  { ...expected, notice: null },
  { ...expected, notice: 'Unrelated notice', text: 'Unrelated notice' },
  { ...expected, reloadButton: true },
  { ...expected, readable: false },
  { ...expected, text: 'Different rendered text' },
  { ...expected, diagnostic: { ...expected.diagnostic, copyMatchesPrevious: false } },
  { ...expected, diagnostic: { ...expected.diagnostic, copyVisible: false } },
  { ...expected, diagnostic: { ...expected.diagnostic, previousPage: expected.diagnostic.currentPage } },
  { ...expected, diagnostic: { ...expected.diagnostic, previousLost: false } },
];
for (const state of failures) assert.equal(accepts(state, firstPage), false);
assert.equal(accepts(null, firstPage), false);
assert.equal(accepts(expected, expected.diagnostic.currentPage), false,
  'an unrelated prior record must not substitute for the page that just reset');

time += 3_200;
box.log('lost');
box.log('restored');
const secondPage = box.box.page;
box = navigate(box, 'light');
assert.equal(accepts(diagnostic(box), secondPage), true,
  'the next lowered-tier navigation retains the second actual reset record');

// Exercise the actual caller's loss callback too: a correct predicate cannot
// recover a prior page that loseAndRestore failed to return before navigation.
const lossCallback = source.match(/const loseAndRestore = \(\) => pc\.evaluate\((async \(\) => \{[\s\S]*?^      \})\);/m);
assert(lossCallback, 'the smoke must expose its actual loss/restore callback');
let resolveLost;
const contextWindow = { __chicago4d: {
  crashGuard: { notice: 'Display reset' }, blackbox: { box: { page: secondPage } },
} };
const extension = {
  loseContext() { resolveLost(); },
  restoreContext() { contextWindow.__chicago4d.blackbox.box.page = 'new-page-after-restore'; },
};
const canvas = { addEventListener(event, callback) {
  assert.equal(event, 'webglcontextlost'); resolveLost = callback;
} };
const gl = { canvas, getExtension(name) {
  assert.equal(name, 'WEBGL_lose_context'); return extension;
} };
const actualLoss = vm.runInNewContext(`(${lossCallback[1]})`, {
  window: contextWindow,
  document: { getElementById: () => ({ getContext: () => gl }) },
  setTimeout: callback => callback(),
});
const loss = await actualLoss();
assert.equal(loss.diagnostic.currentPage, secondPage,
  'the actual loss callback returns the old page before restore navigates');
assert.equal(contextWindow.__chicago4d.blackbox.box.page, 'new-page-after-restore');
console.log('PASS: actual blackbox records across two clean reloads; exact prior-page smoke diagnostic predicate and eleven refusals. Browser reload/tier mechanics remain covered by the published smoke.');

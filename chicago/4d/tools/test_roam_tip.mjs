#!/usr/bin/env node
// T-2634 (NAV-404): Free roam docks the Navigator and shows the one-time tip "Tap any
// building to inspect it." — once per device, storage behind try/catch. Drives
// js/roam-tip.js over a fake element, storage and clock; the smoke (part 13) takes Free
// roam from the Navigator's Jaunts app in a page.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRoamTip, tipText, ROAM_TIP_KEY, ROAM_TIP_MS } from '../renderers/web/js/roam-tip.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(ROOT, p), 'utf8');

assert.equal(tipText(true), 'Tap any building to inspect it.', 'the words of the design, on a touch screen');
assert.equal(tipText(false), 'Click any building, or press E, to inspect it.', 'and with a mouse');

const el = () => { const fns = {}; return { hidden: true, textContent: '', addEventListener: (t, fn) => { (fns[t] ??= []).push(fn); }, click: () => (fns.click ?? []).forEach((f) => f()) }; };
const store = () => { const m = new Map(); return { getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), m }; };
const clock = () => { const q = []; return { wait: (fn, ms) => { q.push({ fn, ms }); return q.length; }, cancel: (id) => { if (q[id - 1]) q[id - 1].fn = null; }, run: () => q.splice(0).forEach((t) => t.fn?.()), q }; };

// Once per device.
{
  const e = el(), s = store(), c = clock();
  const tip = createRoamTip({ el: e, storage: s, wait: c.wait, cancel: c.cancel });
  assert.equal(tip.show({ touch: true }), true, 'the first Free roam shows it');
  assert.equal(e.hidden, false);
  assert.equal(e.textContent, 'Tap any building to inspect it.');
  assert.equal(s.m.get(ROAM_TIP_KEY), '1', 'and remembers it on this device');
  assert.equal(c.q[0].ms, ROAM_TIP_MS, 'it goes by itself after a few seconds');
  c.run();
  assert.equal(e.hidden, true);
  assert.equal(tip.show({ touch: true }), false, 'never twice on a page');
  const again = createRoamTip({ el: el(), storage: s, wait: c.wait, cancel: c.cancel });
  assert.equal(again.show({ touch: true }), false, 'nor on the next visit from this device');
}
// A tap puts it away.
{
  const e = el(), c = clock();
  const tip = createRoamTip({ el: e, storage: store(), wait: c.wait, cancel: c.cancel });
  tip.show({ touch: false });
  assert.equal(e.textContent, 'Click any building, or press E, to inspect it.');
  e.click();
  assert.equal(e.hidden, true, 'a tap on it puts it away');
  assert.equal(tip.showing, false);
}
// Storage refused: no error, and once per page.
{
  const refusing = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }, removeItem() { throw new Error('denied'); } };
  const e = el(), c = clock();
  const tip = createRoamTip({ el: e, storage: refusing, wait: c.wait, cancel: c.cancel });
  assert.equal(tip.show({ touch: true }), true, 'refused storage still shows the tip');
  assert.equal(tip.show({ touch: true }), false, '…once for the page');
  tip.forget();
  assert.equal(tip.show({ touch: true }), true, 'the harness can forget it');
  const none = createRoamTip({ el: null, storage: null, wait: c.wait, cancel: c.cancel });
  assert.equal(none.show(), true, 'no element and no storage: nothing throws');
}

// The page: Free roam from Home and from the Navigator both dock and show it.
const main = read('renderers/web/js/main.js');
assert(/freeRoam: \(\) => \{ navigatorUi\?\.dock\(\); roamTip\.show\(\{ touch: backends\.name === 'touch' \}\); \}/.test(main), 'the Navigator\'s Free roam docks it and shows the tip');
assert(/if \(!resume && !destination\) roamTip\.show\(/.test(main), 'Home\'s Free roam (no destination) shows it; a quick start or a Jaunt does not');
assert(/navigatorUi\?\.dock\(\);[\s\S]{0,400}backends\.activate/.test(main), 'entering the town docks the Navigator');
assert(/<button type="button" class="roam-tip" id="roam-tip" hidden><\/button>/.test(read('renderers/web/index.html')));
assert(/\.roam-tip\[hidden\] \{ display: none; \}/.test(read('renderers/web/css/walk.css')));
assert(/prefers-reduced-motion: reduce\) \{ \.roam-tip \{ animation: none; \}/.test(read('renderers/web/css/walk.css')), 'still with reduced motion');

console.log('test_roam_tip: Free roam docks the Navigator and says "Tap any building to inspect it." once per device');

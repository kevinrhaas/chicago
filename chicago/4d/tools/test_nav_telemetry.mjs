#!/usr/bin/env node
// T-2623 (NAV-207): the Navigator's telemetry strip, and the machine numbers it shares
// with the portal's console.
//
// No browser: the strip runs over a hand-made element and document, a fake clock and
// fake timers, so every condition it ticks under (open, seen, the tab, reduced motion)
// can be turned on and off and the timer read back. The portal's side is read as
// source: it must take its numbers from machine-drift.js, which its page must load first.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { mountTelemetry, stripText, signalBars, STEADY, TICK_MS, SIGNAL_BARS } from '../renderers/web/js/nav-telemetry.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = path.join(ROOT, 'renderers/web');
const D = globalThis.chicagoMachineDrift;

// ---- machine-drift.js: the numbers the portal showed before, now shared ---------------
{
  assert.equal(TICK_MS, 800, 'the strip ticks every 800 ms (DESIGN §06)');
  assert.ok(Object.isFrozen(D), 'one frozen definition');
  const lo = D.readings(false, () => 0), hi = D.readings(false, () => 0.999999);
  assert.ok(lo.coherence >= 0.994 && hi.coherence <= 0.999, 'a steady field reads 0.994 to 0.999');
  assert.ok(lo.drift >= 0.3 && hi.drift <= 0.5, 'a steady drift reads ±0.3 to ±0.5 d');
  const slo = D.readings(true, () => 0), shi = D.readings(true, () => 0.999999);
  assert.ok(slo.coherence >= 0.962 && shi.coherence <= 0.981, 'a slipping field reads 0.962 to 0.981');
  assert.ok(slo.drift >= 1.2 && shi.drift <= 2.1, 'a slipping drift reads ±1.2 to ±2.1 d');
  assert.equal(D.format.coherence(0.9981), '0.998');
  assert.equal(D.format.drift(0.44), '±0.4 d');
  assert.ok(D.nextDriftIn(true, () => 0) === 5000 && D.nextDriftIn(false, () => 0) === 9000, 'the portal\'s cadence');
  assert.equal(signalBars(3), '▮▮▮▯');
  assert.equal(signalBars(9), '▮▮▮▮', 'clamped to four');
  assert.deepEqual(stripText({ coherence: 0.9975, drift: 0.41 }), { field: '0.998', drift: '±0.4 D', sig: '▮▮▮▯' });
  assert.equal(stripText({ coherence: 0.97, drift: 1.5 }, true).sig, '▮▮▯▯', 'a drift event drops a bar');
}

// ---- the portal reads them, and its page loads them first ------------------------------
{
  const portal = fs.readFileSync(path.join(WEB, 'portal/portal.js'), 'utf8');
  assert.match(portal, /globalThis\.chicagoMachineDrift/, 'portal.js reads the shared numbers');
  assert.doesNotMatch(portal, /rand\(\.994, \.999\)|rand\(\.3, \.5\)|rand\(5000, 8000\)|rand\(9000, 14000\)/,
    'and keeps no second copy of them');
  const page = fs.readFileSync(path.join(WEB, 'portal/index.html'), 'utf8');
  const drift = page.indexOf('walk/js/machine-drift.js'), main = page.indexOf('walk/portal/portal.js');
  assert.ok(drift > 0 && drift < main, 'the portal page loads machine-drift.js before portal.js');
  const nav = fs.readFileSync(path.join(WEB, 'js/navigator.js'), 'utf8');
  assert.match(nav, /mountTelemetry\(/, 'the device mounts the strip');
}

// ---- a hand-made element and document ----------------------------------------------------
function fakeDom() {
  const listeners = {};
  const make = (tag) => {
    const el = {
      tagName: tag.toUpperCase(), children: [], parent: null, dataset: {}, attrs: {}, textContent: '', className: '',
      innerHTML: '', isConnected: true,
      setAttribute(k, v) { this.attrs[k] = String(v); }, getAttribute(k) { return this.attrs[k] ?? null; },
      append(...cs) { for (const c of cs) { c.parent = el; el.children.push(c); } },
      remove() { if (el.parent) el.parent.children.splice(el.parent.children.indexOf(el), 1); el.parent = null; el.isConnected = false; },
    };
    return el;
  };
  const doc = {
    hidden: false,
    createElement: make,
    addEventListener(type, fn) { (listeners[type] ??= []).push(fn); },
    removeEventListener(type, fn) { listeners[type] = (listeners[type] ?? []).filter((f) => f !== fn); },
    fire(type) { for (const fn of listeners[type] ?? []) fn(); },
    listeners,
  };
  return { doc, host: make('section') };
}
function fakeTimers() {
  const live = new Map();
  let id = 0;
  return {
    set: (fn, ms) => { live.set(++id, { fn, ms }); return id; },
    clear: (i) => live.delete(i),
    fire() { for (const { fn } of [...live.values()]) fn(); },
    live,
  };
}
function reduced(matches = false) {
  const fns = [];
  return { matches, addEventListener: (_t, fn) => fns.push(fn), removeEventListener: () => {}, set(v) { this.matches = v; fns.forEach((f) => f()); } };
}
const textOf = (el) => el.children.map((c) => c.children[1]?.textContent ?? '').join('|');

// ---- the strip -------------------------------------------------------------------------
{
  const { doc, host } = fakeDom();
  const timers = fakeTimers();
  const rm = reduced(false);
  let open = false, seen = true, t = 0, r = 0.5;
  const tm = mountTelemetry({ host, doc, open: () => open, reducedMotion: rm, random: () => r, now: () => t,
    setTimer: timers.set, clearTimer: timers.clear, visible: () => seen });
  const el = tm.el;
  assert.equal(el.getAttribute('aria-hidden'), 'true', 'decorative, so aria-hidden');
  assert.deepEqual(el.children.map((c) => c.dataset.t), ['field', 'drift', 'sig', 'recall']);
  assert.equal(el.children[3].className, 'nav-tm-cell nav-tm-recall', 'RECALL is a lamp');
  assert.equal(textOf(el), `${STEADY.field}|${STEADY.drift}|${STEADY.sig}|`, 'it starts at its steady reading');
  assert.equal(tm.running, false, 'a docked device does not tick');

  open = true; tm.sync();
  assert.equal(tm.running, true, 'open and seen: it ticks');
  assert.equal([...timers.live.values()][0].ms, 800, 'every 800 ms');
  tm.sync();
  assert.equal(timers.live.size, 1, 'one timer, however often it is synced');
  t = 100; timers.fire(); timers.fire();
  assert.equal(tm.ticks, 2);
  assert.match(textOf(el), /^0\.99\d\|±0\.\d D\|▮▮▮▯\|$/, 'FIELD, DRIFT and SIG on each tick');

  // A drift event: due 5-8 s in (here 5 s + 0.5 of 3 s), held 2.9 s, then the next 9-14 s on.
  t = 6600; timers.fire();
  assert.equal(tm.slipping, true, 'the drift event arrives on the portal\'s cadence');
  assert.equal(el.dataset.state, 'drift');
  assert.match(textOf(el), /^0\.9[67]\d\|±[12]\.\d D\|▮▮▯▯\|$/, 'the field sags, the drift widens and a bar drops');
  t = 6600 + 2900; timers.fire();
  assert.equal(tm.slipping, false, 'and passes');
  assert.equal(el.dataset.state, 'steady');

  doc.hidden = true; doc.fire('visibilitychange');
  assert.equal(tm.running, false, 'the tab hidden: it stops at once');
  assert.equal(timers.live.size, 0);
  doc.hidden = false; doc.fire('visibilitychange');
  assert.equal(tm.running, true, 'and starts again when the tab comes back');

  seen = false; tm.sync();
  assert.equal(tm.running, false, 'the device covered or hidden: it stops');
  seen = true; tm.sync();
  open = false; tm.sync();
  assert.equal(tm.running, false, 'docked again: it stops');
  open = true; tm.sync();

  rm.set(true);
  assert.equal(tm.running, false, 'reduced motion: no ticking (QA-06)');
  assert.equal(textOf(el), `${STEADY.field}|${STEADY.drift}|${STEADY.sig}|`, 'and it stands at its steady reading');
  tm.sync();
  assert.equal(tm.running, false, 'still, however often it is synced');
  rm.set(false);
  assert.equal(tm.running, true, 'motion allowed again: it ticks');

  const before = doc.listeners.visibilitychange.length;
  tm.destroy();
  assert.equal(timers.live.size, 0, 'destroy stops the timer');
  assert.equal(doc.listeners.visibilitychange.length, before - 1, 'and lets go of the tab');
  assert.equal(host.children.length, 0, 'and takes the strip away');
  assert.equal(SIGNAL_BARS, 4);
}

console.log('NAV TELEMETRY PASS — FIELD, DRIFT, SIG and RECALL, aria-hidden, on the portal\'s own numbers and drift cadence; ticks every 800 ms only while the device is open and seen, never with the tab hidden, and stands still under reduced motion');

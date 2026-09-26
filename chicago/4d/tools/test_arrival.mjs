import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  bootProgress, createArrival, easeInOut, reducedProgress, settleDurationMs, yearForProgress,
} from '../renderers/web/js/arrival.js';
import { createBoot } from '../renderers/web/js/boot-phases.js';

assert.equal(easeInOut(0), 0);
assert.equal(easeInOut(1), 1);

let previous = 2026;
for (let i = 0; i <= 100; i++) {
  const y = yearForProgress(i / 100, 2026, false);
  assert.ok(y <= previous + 1e-9, `year rolled forward at ${i}%: ${y} > ${previous}`);
  assert.ok(y >= 1836, `pre-ready year crossed 1836: ${y}`);
  previous = y;
}
assert.equal(yearForProgress(1, 2026, false), 1836);
assert.equal(yearForProgress(0.6, 2026, true), 1835);

const phases = [
  { id: 'scene', essential: true, startedAt: 0, endedAt: 1000, units: 10, unitsDone: 10, error: null },
  { id: 'flora', essential: true, startedAt: 1000, endedAt: null, units: null, unitsDone: 0, error: null },
  { id: 'people', essential: false, startedAt: 0, endedAt: null, units: null, unitsDone: 0, error: null },
];
const expected = { scene: 1, flora: 10, people: 99 };
const early = bootProgress(phases, expected, 2000);
const late = bootProgress(phases, expected, 20000);
assert.ok(late >= early, 'elapsed progress must be monotone');
assert.ok(late < 1, 'an overrunning active phase must not claim completion');
assert.ok(late <= (1 + 10 * 0.92) / 11 + 1e-9, 'elapsed phase must ease only to 92% of its weight');

const unitPhases = [
  { id: 'scene', essential: true, startedAt: 0, endedAt: null, units: 100, unitsDone: 50, error: null },
];
assert.equal(bootProgress(unitPhases, { scene: 2 }, 999999), 0.5);

assert.equal(settleDurationMs({ reducedMotion: true, bootDurationMs: 9000 }), 0);
assert.equal(settleDurationMs({ reducedMotion: false, bootDurationMs: 1499 }), 0);
assert.equal(settleDurationMs({ reducedMotion: false, bootDurationMs: 1500 }), 300);

const reduced = new Set([0, .1, .24, .26, .49, .51, .74, .9, .999].map(reducedProgress));
assert.ok(reduced.size <= 4, `reduced motion produced ${reduced.size} pre-ready updates`);

console.log('ARRIVAL PASS — monotone, bounded, honest readiness and reduced-motion pacing');

const here = path.dirname(fileURLToPath(import.meta.url));
const index = readFileSync(path.join(here, '../renderers/web/index.html'), 'utf8');
assert.match(index, /id="arrival-year"[^>]*aria-hidden="true"/,
  'the changing year must stay out of the accessibility tree');
assert.match(index, /id="gate-sub"[^>]*aria-live="polite"/,
  'the phase/arrival line is the gate\'s one live announcement');
assert.match(index, /id="arrival-card"/, 'the source/status card slot must exist');

console.log('ARRIVAL A11Y PASS — year hidden, phase line polite, card slot present');

// Exercise the real event controller, including writes that the pure mapping
// tests cannot see (failure followed by phaseend, and reduced phase announcements).
function fixture(reducedMotion = false) {
  let clock = 0, id = 0, reloaded = false;
  const frames = new Map();
  const phaseEl = { textContent: '', setAttribute() {} };
  const buttonEl = { disabled: true, dataset: {}, addEventListener(_, fn) { this.click = fn; } };
  const barEl = { setAttribute(_, v) { this.percent = v; }, firstElementChild: { style: {} }, classList: { add() {} } };
  const boot = createBoot({ now: () => clock });
  // Fixed phase weights make the controller scenarios independent of device benchmarks.
  for (const p of boot.phases) boot.expected[p.id] = 1;
  const arrival = createArrival({ boot, phaseEl, buttonEl, barEl, currentYear: 2026, reducedMotion,
    now: () => clock, requestFrame: fn => { frames.set(++id, fn); return id; },
    cancelFrame: id => frames.delete(id), reload: () => { reloaded = true; } });
  const step = ms => { clock += ms; const pending = [...frames.values()]; frames.clear(); pending.forEach(fn => fn()); };
  const complete = () => { for (const p of boot.phases.filter(p => p.essential)) { boot.start(p.id); boot.end(p.id); } boot.frameRendered(); assert.ok(boot.finish()); };
  return { boot, arrival, phaseEl, buttonEl, barEl, frames, step, complete, get reloaded() { return reloaded; } };
}
const slow = fixture();
slow.boot.start('scene');
const years = [slow.arrival.state.year];
for (let i = 0; i < 20; i++) { slow.step(100); years.push(slow.arrival.state.year); }
assert.ok(new Set(years).size > 2, 'elapsed phases animate between boot events');
assert.ok(years.every((y, i) => y >= 1836 && (!i || y <= years[i - 1])));
slow.boot.progress('scene', 0, 1000); // newly counted work must never roll forward
slow.step(100);
assert.ok(slow.arrival.state.year <= years.at(-1));
slow.complete();
slow.step(200);
assert.ok(slow.arrival.state.year >= 1836);
assert.doesNotMatch(slow.phaseEl.textContent, /arrived/);
slow.step(100);
assert.equal(slow.arrival.state.year, 1835);
assert.equal(slow.buttonEl.disabled, false);
assert.equal(slow.barEl.percent, '100');
assert.equal(slow.frames.size, 0, 'no ticker remains after arrival');
const arrived = slow.phaseEl.textContent;
slow.boot.fail('people', 'optional failure');
assert.equal(slow.phaseEl.textContent, arrived);

const fast = fixture(); fast.boot.start('scene'); fast.step(100); fast.complete();
assert.equal(fast.arrival.state.year, 1835);
assert.equal(fast.frames.size, 0, 'fast boot has no cosmetic delay');
assert.match(fast.phaseEl.textContent, /You have arrived/);

const reducedFixture = fixture(true);
reducedFixture.boot.start('scene');
const reducedYears = new Set([reducedFixture.arrival.state.year]);
for (const p of reducedFixture.boot.phases.filter(p => p.essential)) {
  reducedFixture.boot.start(p.id); reducedFixture.step(350); reducedFixture.boot.end(p.id);
  reducedYears.add(reducedFixture.arrival.state.year);
  assert.equal(reducedFixture.phaseEl.textContent, p.label);
}
reducedFixture.complete(); reducedYears.add(reducedFixture.arrival.state.year);
assert.ok(reducedYears.size <= 5);
assert.equal(reducedFixture.frames.size, 0);

const failed = fixture(); failed.boot.start('terrain'); failed.step(2000);
failed.boot.fail('terrain', 'ground unavailable');
const stopped = failed.arrival.state.year;
failed.step(10000);
assert.equal(failed.arrival.state.year, stopped);
assert.ok(stopped >= 1836);
assert.match(failed.phaseEl.textContent, /ground unavailable/);
assert.doesNotMatch(failed.phaseEl.textContent, /arrived/);
assert.equal(failed.buttonEl.textContent, 'Retry');
assert.equal(failed.frames.size, 0);
failed.buttonEl.click({ preventDefault() {}, stopImmediatePropagation() {} });
assert.ok(failed.reloaded);
assert.ok(!failed.boot.finish());
console.log('ARRIVAL CONTROLLER PASS — real events, smooth ticks, monotone corrections, instant fast/reduced, optional/essential failure and retry');


/* Real-controller integration: an elapsed-only essential phase keeps moving
 * between boot events, while optional work never steals the essential status. */
let clock = 0;
let scheduled = null;
let frameId = 0;
const phaseEl = {
  textContent: '',
  attrs: {},
  setAttribute(name, value) { this.attrs[name] = value; },
};
const buttonEl = {
  disabled: true,
  textContent: '',
  dataset: {},
  addEventListener() {},
};
const boot = createBoot({
  device: 'desktop',
  detail: 'full',
  now: () => clock,
});
const integrated = createArrival({
  boot,
  phaseEl,
  buttonEl,
  currentYear: 2026,
  now: () => clock,
  reducedMotion: false,
  requestFrame(cb) { scheduled = cb; return ++frameId; },
  cancelFrame() { scheduled = null; },
});

boot.start('scene');
assert.equal(phaseEl.textContent, 'Reading the scene…');
const initialYear = integrated.state.year;
assert.equal(typeof scheduled, 'function', 'an active essential phase schedules elapsed progress');

clock = boot.expected.scene * 1000 * 0.92;
const elapsedFrame = scheduled;
elapsedFrame();
assert.ok(integrated.state.year < initialYear,
  'the year advances between boot events from elapsed/expected progress');

const essentialLabel = phaseEl.textContent;
boot.start('people');
assert.equal(phaseEl.textContent, essentialLabel,
  'an optional phase start must not replace the essential phase announcement');
boot.fail('people', new Error('optional unavailable'));
assert.equal(integrated.state.failed, false, 'an optional phase failure must not stop arrival');
assert.equal(phaseEl.textContent, essentialLabel,
  'an optional phase failure/end must not replace the essential phase announcement');

boot.fail('scene', new Error('essential unavailable'));
assert.equal(integrated.state.failed, true, 'an essential failure stops arrival');
assert.equal(buttonEl.textContent, 'Retry');
assert.equal(buttonEl.disabled, false);

const main = readFileSync(path.join(here, '../renderers/web/js/main.js'), 'utf8');
assert.doesNotMatch(main, /present:\s*progress/,
  'arrival.js must be the sole gate presenter; legacy progress cannot compete');
assert.doesNotMatch(main, /gateBtn\.disabled\s*=\s*false[^\n]*Tap to enter/,
  'main.js must not enable entry before the arrival ready/settle path');

console.log('ARRIVAL CONTROLLER PASS — elapsed tick, optional isolation, failure and sole presenter');

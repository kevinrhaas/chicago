#!/usr/bin/env node
// T-2164 — the arrival clock's download forecast. Runs in check.sh, no browser.
import assert from 'node:assert/strict';
import { createNetMeter, createForecast, expectedBytes } from '../renderers/web/js/boot-forecast.js';
import { BOOT_BYTES } from '../renderers/web/js/boot-bytes.js';
import { createBoot } from '../renderers/web/js/boot-phases.js';
import { createArrival, formatReadout } from '../renderers/web/js/arrival.js';

const ESSENTIAL = ['scene', 'terrain', 'buildings', 'ground', 'flora', 'interaction'];
for (const device of ['desktop', 'mobile']) for (const detail of ['light', 'balanced', 'full']) {
  const cell = BOOT_BYTES[device]?.[detail];
  assert.ok(cell, `committed first-visit bytes for ${device}/${detail}`);
  for (const id of ESSENTIAL) assert.ok(Number.isFinite(cell[id]) && cell[id] >= 0, `${device}/${detail}/${id}`);
  assert.ok(cell.scene > 1e6, 'the scene phase is where the town downloads');
}

// The meter: wire bytes over the time anything was on the wire, overlaps merged.
const meter = createNetMeter({ Observer: null, connection: { downlink: 8 } });
assert.equal(meter.hinted, 1e6, 'a connection hint of 8 Mb/s is 1 MB/s');
meter.add({ encodedBodySize: 1e6, decodedBodySize: 3e6, startTime: 0, responseEnd: 1000 });
meter.add({ encodedBodySize: 1e6, startTime: 500, responseEnd: 2000 });   // overlaps the first
meter.add({ encodedBodySize: 0, decodedBodySize: 5e5, startTime: 5000, responseEnd: 5000 }); // zero-length
assert.equal(meter.bytes, 2.5e6, 'encoded size first, decoded when that is all there is');
assert.equal(meter.busySeconds, 2, 'overlapping requests count their wall time once');
assert.ok(Math.abs(meter.rate() - (2e5 + 2.5e6) / (0.2 + 2)) < 1, 'prior blended with the measured link');
for (let i = 0; i < 500; i++) meter.add({ encodedBodySize: 10, startTime: 10000 + i * 10, responseEnd: 10000 + i * 10 + 5 });
assert.ok(Math.abs(meter.busySeconds - (2 + 500 * 0.005)) < 1e-9, 'folding old intervals keeps their time');

// History: same build trusted, other builds and corrupt storage ignored.
const store = (value = null) => ({ value, getItem() { return this.value; }, setItem(k, v) { this.value = v; } });
const bytesKeyed = new Map();
const multi = { getItem: k => bytesKeyed.get(k) ?? null, setItem: (k, v) => bytesKeyed.set(k, v) };
const base = { device: 'desktop', detail: 'full', build: 'b1' };
assert.deepEqual(expectedBytes({ ...base, storage: store('{bad') }), BOOT_BYTES.desktop.full);
assert.deepEqual(expectedBytes({ ...base, storage: { getItem() { throw Error('denied'); } } }), BOOT_BYTES.desktop.full);
assert.deepEqual(expectedBytes({ ...base, storage: store(JSON.stringify({ build: 'old', cells: { 'desktop/full': { scene: 1 } } })) }), BOOT_BYTES.desktop.full);
assert.equal(expectedBytes({ ...base, storage: store(JSON.stringify({ build: 'b1', cells: { 'desktop/full': { scene: 42 } } })) }).scene, 42);

// A simulated slow boot: 10 MB in the scene phase over a 0.5 MB/s link, CPU at 2x the
// reference. The forecast has to see that before the scene finishes, and the year has
// to keep rolling the whole way without running out early.
function simulate({ rate = 5e5, cpuFactor = 2, bytes = { scene: 1e7, terrain: 2e6, buildings: 2e6, ground: 1e6, flora: 1e5, interaction: 1e6 } } = {}) {
  let clock = 0, frameId = 0;
  const frames = new Map();
  const m = createNetMeter({ Observer: null, connection: null });
  // The page itself: 1 MB of modules at the real link before main.js ran.
  m.add({ encodedBodySize: 1e6, startTime: -1e6 / rate * 1000, responseEnd: 0 });
  const boot = createBoot({ now: () => clock });
  const cpu = { scene: 0.2, terrain: 0.2, buildings: 0.1, ground: 0.2, flora: 2.8, people: 0.1, census: 0.01, interaction: 1.3 };
  for (const p of boot.phases) boot.expected[p.id] = cpu[p.id];
  const forecast = createForecast({ boot, meter: m, bytes, now: () => clock, device: 'desktop' });
  const barEl = { setAttribute(_, v) { this.percent = +v; }, firstElementChild: { style: {} }, classList: { add() {} } };
  const buttonEl = { disabled: true, dataset: {}, addEventListener() {} };
  const arrival = createArrival({ boot, barEl, buttonEl, currentYear: 2026, forecast, now: () => clock,
    reducedMotion: false, requestFrame: fn => { frames.set(++frameId, fn); return frameId; }, cancelFrame: id => frames.delete(id) });
  const readings = [];
  const step = ms => {
    clock += ms;
    const pending = [...frames.values()]; frames.clear(); pending.forEach(fn => fn());
    readings.push({ t: clock / 1000, year: arrival.state.year, bar: barEl.percent, eta: forecast.remaining(clock) });
  };
  for (const id of ESSENTIAL) {
    boot.start(id);
    const download = (bytes[id] || 0) / rate * 1000, work = cpu[id] * cpuFactor * 1000;
    const chunks = 20;
    for (let i = 0; i < chunks; i++) {
      const t0 = clock;
      step((download + work) / chunks);
      // Requests finish through the download, as the scene's ~1,300 do.
      if (download) m.add({ encodedBodySize: bytes[id] / chunks, startTime: t0, responseEnd: clock });
    }
    boot.end(id);
  }
  const total = clock / 1000;
  boot.frameRendered(); boot.finish();
  for (let i = 0; i < 5; i++) step(100);
  return { readings, total, forecast, arrival, boot };
}
const slow = simulate();
const pre = slow.readings.filter(r => r.year !== 1835);
for (let i = 1; i < pre.length; i++) assert.ok(pre[i].year <= pre[i - 1].year, 'the year never rolls forward');
// No stall: over any five-second window before ready the year moves.
for (let i = 0; i < pre.length; i++) {
  const later = pre.find(r => r.t >= pre[i].t + 5);
  if (later && later.t < slow.total - 0.5) assert.ok(later.year < pre[i].year, `the year sat still from ${pre[i].t.toFixed(1)}s`);
}
// The forecast saw the download from the first frame: within 35 % of the real total.
const first = slow.readings[0];
assert.ok(Math.abs(first.eta - slow.total) / slow.total < 0.35, `first ETA ${first.eta.toFixed(1)}s vs ${slow.total.toFixed(1)}s`);
// Halfway through the real boot the year is near the middle of its roll, not parked at the end.
const mid = pre.find(r => r.t >= slow.total / 2);
assert.ok(mid.bar >= 30 && mid.bar <= 75, `half-time progress ${mid.bar}%`);
assert.equal(slow.arrival.state.year, 1835, 'ready lands on the destination year');

// A machine far slower than the prior (a weak phone, 6x the reference desktop): the year still moves and
// the pace is learned live, not only at phase ends.
const crawl = simulate({ rate: 2e6, cpuFactor: 6 });
const crawlPre = crawl.readings.filter(r => r.year !== 1835);
if (process.env.DEBUG) for (const r of crawl.readings.filter((_, i) => i % 6 === 0)) console.log(r.t.toFixed(1), r.year, r.bar, r.eta.toFixed(1));
assert.ok(crawl.forecast.pace > 3, `pace learned ${crawl.forecast.pace}`);
for (let i = 0; i < crawlPre.length; i++) {
  const later = crawlPre.find(r => r.t >= crawlPre[i].t + 6);
  if (later && later.t < crawl.total - 0.5) assert.ok(later.year < crawlPre[i].year, `slow machine stalled at ${crawlPre[i].t.toFixed(1)}s`);
}
// An overrunning phase never claims to be about to finish.
assert.ok(crawl.readings.every(r => r.eta >= 0.25 || r.year === 1835));

// Recording: this build's bytes and the machine's pace survive for the next visit.
{
  let clock = 0;
  const boot = createBoot({ now: () => clock });
  const m = createNetMeter({ Observer: null });
  const f = createForecast({ boot, meter: m, now: () => clock, storage: multi, build: 'b2', device: 'mobile', detail: 'light' });
  for (const id of ESSENTIAL) { boot.start(id); clock += 500; m.add({ encodedBodySize: 1000, startTime: clock - 400, responseEnd: clock - 1 }); boot.end(id); }
  boot.start('people'); boot.end('people'); boot.start('census'); boot.end('census');
  boot.frameRendered(); assert.ok(boot.finish());
  const learned = expectedBytes({ device: 'mobile', detail: 'light', build: 'b2', storage: multi });
  for (const id of ESSENTIAL) assert.equal(learned[id], 1000, `learned ${id}`);
  assert.ok(JSON.parse(bytesKeyed.get('c4d.boot.pace.v1'))['mobile/light'] > 0, 'pace kept across builds');
  assert.equal(f.phaseBytes.scene, 1000);
}

// The readout's strings: fixed shapes, so the strip never reflows.
assert.deepEqual(formatReadout({ bytes: 3.2e6, total: 12.9e6, rate: 4.1e5, eta: 65.4 }), { bytes: '3.2 / 12.9 MB', rate: '0.4 MB/s', eta: 'T-01:05' });
assert.equal(formatReadout({ bytes: 0, total: 0, rate: null, eta: NaN }).rate, '— MB/s');
assert.equal(formatReadout({}, true).eta, 'LOCKED');
console.log(`BOOT FORECAST PASS — meter, history, no stall on a slow link (${slow.total.toFixed(0)} s simulated, first ETA ${first.eta.toFixed(0)} s) or a slow machine (pace ${crawl.forecast.pace.toFixed(1)}), learned bytes and pace, fixed readout`);

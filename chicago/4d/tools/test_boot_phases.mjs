#!/usr/bin/env node
// Controller/fetch-failure contract runs in check.sh without a browser install.
// --browser additionally injects failed fetches into the REAL published app.
import assert from 'node:assert/strict';
import { createBoot, PHASES, expectedDurations, createCheckpoint, yieldToPaint } from '../renderers/web/js/boot-phases.js';
import { BOOT_WEIGHTS } from '../renderers/web/js/boot-weights.js';
const key = 'c4d.boot.timings.v1';
const memory = value => ({ value, getItem() { return this.value; }, setItem(k, v) { assert.equal(k, key); this.value = v; } });
for (const id of ['people', 'census', 'terrain']) {
  let time = 0; const problems = [], events = [], percents = [];
  const boot = createBoot({ now: () => ++time, problems, present: n => percents.push(n) });
  for (const type of ['phasestart', 'phaseprogress', 'phaseend', 'ready', 'error']) boot.on(type, e => events.push(e));
  const fetch = async () => { throw Error(`forced ${id} fetch failure`); };
  for (const [phase] of PHASES) {
    boot.start(phase, 2); boot.progress(phase, 1); boot.progress(phase, 0);
    assert.equal(boot.phases.find(p => p.id === phase).unitsDone, 1);
    if (phase === id) { try { await fetch(`${id}.json`); } catch (err) { boot.fail(phase, err); } }
    else boot.end(phase);
  }
  assert.equal(boot.finish(), false, 'ready requires a rendered frame');
  boot.frameRendered();
  assert.equal(boot.finish(), id !== 'terrain');
  assert.equal(boot.finish(), false, 'ready emitted once');
  assert.equal(events.filter(e => e.type === 'error').length, 1);
  assert.equal(events.filter(e => e.type === 'ready').length, id === 'terrain' ? 0 : 1);
  assert.equal(problems.length, 1);
  assert.ok(boot.phases.every(p => p.startedAt < p.endedAt));
  assert.ok(percents.every((n, i) => !i || n >= percents[i - 1]));
}
for (const device of ['desktop', 'mobile']) for (const detail of ['full', 'balanced', 'light']) {
  for (const cache of ['cold', 'warm']) for (const [id] of PHASES) assert.ok(BOOT_WEIGHTS[device]?.[detail]?.[cache]?.[id] > 0, `measured ${device}/${detail}/${cache}/${id}`);
  const defaults = BOOT_WEIGHTS[device][detail].cold;
  const args = { device, detail, build: 'today' };
  for (const factor of [0.001, 1000]) {
    const storage = memory(JSON.stringify({ build: 'today', cells: { [`${device}/${detail}`]: Object.fromEntries(Object.entries(defaults).map(([k, v]) => [k, v * factor])) } }));
    const expected = expectedDurations({ ...args, storage });
    for (const [id, base] of Object.entries(defaults)) assert.equal(expected[id], base * (factor < 1 ? 0.25 : 4));
  }
  for (const storage of [{ getItem() { return null; }, setItem() { throw Error('quota'); } }, memory('{bad'), memory(JSON.stringify({ build: 'old', cells: { [`${device}/${detail}`]: { flora: 999 } } })), { getItem() { throw Error('denied'); }, setItem() { throw Error('denied'); } }]) {
    assert.deepEqual(expectedDurations({ ...args, storage }), defaults);
    const b = createBoot({ ...args, storage });
    for (const [id] of PHASES) { b.start(id); b.end(id); } b.frameRendered(); assert.equal(b.finish(), true);
  }
  const storage = memory(null);
  for (let run = 0; run < 3; run++) {
    let t = 0; const b = createBoot({ ...args, storage, now: () => t += 1e6 });
    for (const [id] of PHASES) { b.start(id); b.end(id); } b.frameRendered(); b.finish();
    const h = JSON.parse(storage.value); assert.ok(Object.keys(h.cells).length <= 6);
    for (const [id, v] of Object.entries(h.cells[`${device}/${detail}`])) assert.equal(v, defaults[id] * 4, 'history never compounds beyond committed default');
  }
}
assert.equal(createCheckpoint({ budgetMs: 1e6 })(), null, 'no unconditional yield when units omitted');
// A hidden tab schedules timers, not a frame per work item to replay on resume.
let frames = 0;
globalThis.document = { hidden: true };
globalThis.requestAnimationFrame = () => { frames++; return 1; };
globalThis.cancelAnimationFrame = () => {};
await yieldToPaint(); assert.equal(frames, 0);
globalThis.document.hidden = false;
let cancelled = 0; globalThis.cancelAnimationFrame = () => cancelled++;
const pendingPaint = yieldToPaint(); globalThis.document.hidden = true;
await pendingPaint; assert.equal(frames, 1); assert.equal(cancelled, 1, 'suspended frame is cancelled by timer fallback');
delete globalThis.document; delete globalThis.requestAnimationFrame; delete globalThis.cancelAnimationFrame;
console.log('boot phases PASS: readiness, fetch failures, monotone work, all 12 timing cells, bounded history, hidden yields');
if (process.argv.includes('--browser')) {
  const { environment, observeBoot } = await import('./measure_boot_phases.mjs');
  const env = await environment();
  try {
    for (const failed of ['people', 'census', 'terrain']) {
      const ctx = await env.browser.newContext({ viewport: { width: 390, height: 780 }, hasTouch: true });
      await ctx.addInitScript(observeBoot, { detail: 'light' });
      await ctx.route(failed === 'people' ? '**/people.json' : failed === 'census' ? '**/town_census.json' : '**/terrain/**', route => route.abort());
      const page = await ctx.newPage(); await page.goto(env.url);
      await page.waitForFunction(() => window.__chicago4d?.ready || window.__chicago4d?.error, null, { timeout: 180000 });
      const result = await page.evaluate(() => ({ ready: window.__chicago4d.ready, phases: window.__chicago4d.boot.phases, readyAt: window.__chicago4d.boot.readyAt, renderedAt: window.__chicago4d.boot.renderedAt, problems: window.__chicago4d.problems, events: bootProbe.events }));
      assert.equal(!!result.ready, failed !== 'terrain', failed);
      assert.ok(result.phases.find(p => p.id === failed).error, `${failed} recorded error`);
      assert.ok(result.problems.some(p => p.startsWith(`${failed}:`)), `${failed} in problems`);
      if (failed !== 'terrain') {
        assert.ok(result.renderedAt <= result.readyAt);
        assert.ok(result.phases.filter(p => p.essential).every(p => p.endedAt <= result.readyAt));
      } else assert.equal(result.readyAt, null);
      console.log(`published fetch stub ${failed} PASS`); await ctx.close();
    }
    const ctx = await env.browser.newContext({ viewport: { width: 390, height: 780 }, hasTouch: true });
    await ctx.addInitScript(observeBoot, { detail: 'light' });
    const page = await ctx.newPage(); const cdp = await ctx.newCDPSession(page);
    await page.goto(env.url);
    await page.waitForFunction(() => window.__chicago4d?.boot?.phases.find(p => p.id === 'flora')?.startedAt != null);
    await cdp.send('Page.setWebLifecycleState', { state: 'frozen' });
    await new Promise(resolve => setTimeout(resolve, 300));
    await cdp.send('Page.setWebLifecycleState', { state: 'active' });
    await page.waitForFunction(() => window.__chicago4d?.ready, null, { timeout: 180000 });
    const events = await page.evaluate(() => bootProbe.events);
    assert.equal(events.filter(e => e.type === 'ready').length, 1);
    for (const [id] of PHASES) assert.ok(events.filter(e => e.type === 'phaseend' && e.phase.id === id).length <= 1, 'resume does not replay events');
    assert.ok(events.every((e, i) => !i || e.at >= events[i - 1].at));
    console.log('published background freeze/resume PASS'); await ctx.close();
  } finally { await env.close(); }
}

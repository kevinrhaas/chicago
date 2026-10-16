// T-2611 — the time-stream captions (js/time-stream.js) against the committed decks.
//
//   node tools/test_time_stream.mjs
//
// The acceptance this holds: a caption shows only as the ticker passes its year, for
// about 2 s, one at a time and never twice (so a screen reader hears it at most once);
// at most 3 on a fast load and at most 8 on a slow one (QA-03); and reduced motion's
// five-step ticker still only shows captions for years it actually crossed.
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  createTimeStream, eligibleYears, pickCaption, FAST_LIMIT, SLOW_LIMIT, HOLD_MS, SLOW_AFTER_MS,
} from '../renderers/web/js/time-stream.js';
import { createArrival, easeInOut, reducedProgress, yearForProgress } from '../renderers/web/js/arrival.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const deckDir = path.join(here, '../data/timestream');
const decks = Object.fromEntries(readdirSync(deckDir).filter(f => f.endsWith('.json'))
  .map(f => [f.replace('.json', ''), JSON.parse(readFileSync(path.join(deckDir, f), 'utf8'))]));
assert.deepEqual(Object.keys(decks).sort(), ['1812', '1835', '1904'], 'one deck per destination');

/** A fake clock and timer queue, so a 60-second trip runs in a millisecond. */
function clock() {
  let t = 0;
  const timers = [];
  return {
    now: () => t,
    wait: (fn, ms) => { const id = { at: t + ms, fn }; timers.push(id); return id; },
    cancel: id => { const i = timers.indexOf(id); if (i >= 0) timers.splice(i, 1); },
    advance(ms) {
      const end = t + ms;
      for (;;) {
        timers.sort((a, b) => a.at - b.at);
        const next = timers[0];
        if (!next || next.at > end) break;
        timers.shift(); t = next.at; next.fn();
      }
      t = end;
    },
  };
}

/** The device's caption block and polite line, as plain objects. */
function device() {
  const parts = { year: { textContent: '', dataset: {} }, text: { textContent: '', dataset: {} },
    grade: { textContent: '', title: '', dataset: {} } };
  const screen = { dataset: {} };
  const el = { dataset: { state: 'off' }, parentElement: screen,
    querySelector: sel => parts[/data-ts="(\w+)"/.exec(sel)?.[1]] ?? null };
  const spoken = [];
  const sayEl = { set textContent(v) { spoken.push(v); }, get textContent() { return spoken.at(-1) ?? ''; } };
  return { el, sayEl, parts, screen, spoken };
}

/** Roll the ticker the way arrival.js does — the eased year at each frame, never back up —
 * over `seconds`, and record each caption with the ticker year it showed on. */
function trip(deck, { seconds, reduced = false, forecastLeft = null, scene }) {
  const c = clock();
  const d = device();
  const handlers = {};
  const boot = { on: (type, fn) => { (handlers[type] ||= []).push(fn); } };
  const forecast = forecastLeft == null ? null : { remaining: at => Math.max(0.25, forecastLeft - at / 1000) };
  const ts = createTimeStream({ el: d.el, sayEl: d.sayEl, boot, forecast, currentYear: 2026,
    now: c.now, wait: c.wait, cancel: c.cancel, fetcher: null });
  ts.setDeck(deck);
  const target = Number(scene);
  const shows = [];
  let last = 2026, prevTicker = 2026, onScreen = null, onSince = 0, durations = [];
  const frameMs = 16;
  const frames = Math.ceil(seconds * 1000 / frameMs);
  for (let i = 1; i <= frames; i++) {
    c.advance(frameMs);
    const p = i / frames;
    const y = Math.round(yearForProgress(reduced ? reducedProgress(p) : p, 2026, false, target));
    if (y < last) {
      ts.passYear(y);
      last = y;
    }
    const state = d.el.dataset.state;
    if (state === 'on' && d.el.dataset.year !== onScreen) {
      if (onScreen) durations.push(c.now() - onSince);
      onScreen = d.el.dataset.year; onSince = c.now();
      shows.push({ year: Number(onScreen), ticker: last, before: prevTicker });
    } else if (state !== 'on' && onScreen) {
      durations.push(c.now() - onSince); onScreen = null;
    }
    prevTicker = last;
  }
  for (const fn of handlers.ready || []) fn({});
  c.advance(5000);
  return { ts, shows, durations, spoken: d.spoken, d };
}

// The pick: the top N by importance, and a pass shows the most important crossed one.
{
  const caps = decks['1904'].captions;
  const top3 = eligibleYears(caps, FAST_LIMIT);
  assert.equal(top3.size, 3);
  assert.deepEqual([...top3].sort(), [1909, 1933, 1966], 'the fast three for 1904 are the doc\'s own examples, less the Black Sox');
  assert.equal(eligibleYears(caps, SLOW_LIMIT).size, 8);
  const c = pickCaption({ captions: caps, from: 1970, to: 1960, shown: new Set(), eligible: eligibleYears(caps, 12),
    busy: false, count: 0, cap: 8 });
  assert.equal(c.year, 1966, 'a pass from 1970 to 1960 crosses 1966 and 1963, and shows the more important');
  assert.equal(pickCaption({ captions: caps, from: 1960, to: 1970, shown: new Set(), eligible: top3,
    busy: false, count: 0, cap: 8 }), null, 'a year moving up crosses nothing');
  // A lesser caption gives way to a better one the ticker is about to pass (1861 for 1860).
  const c35 = decks['1835'].captions, all35 = eligibleYears(c35, 12);
  const at = reach => pickCaption({ captions: c35, from: 1862, to: 1861, shown: new Set(), eligible: all35,
    busy: false, count: 0, cap: 8, reach });
  assert.equal(at(0)?.year, 1861);
  assert.equal(at(2), null, 'a lesser caption one year above a better one gives way to it');
  // ...and a caption the landing would cut off does not start.
  const k = clock();
  const late = createTimeStream({ currentYear: 2026, now: k.now, wait: k.wait, cancel: k.cancel, fetcher: null,
    forecast: { remaining: () => 0.3 } });
  late.setDeck(decks['1904']);
  late.passYear(1960);
  assert.equal(late.state.count, 0, 'a caption started 0.3 s before landing');
}

for (const [scene, deck] of Object.entries(decks)) {
  const years = new Set(deck.captions.map(c => c.year));
  for (const [label, opts, cap] of [
    ['fast', { seconds: 4 }, FAST_LIMIT],
    ['fast, slow forecast', { seconds: 6, forecastLeft: 30 }, FAST_LIMIT],
    ['slow', { seconds: 75, forecastLeft: 80 }, SLOW_LIMIT],
    ['slow, no forecast', { seconds: 75 }, SLOW_LIMIT],
    ['reduced motion, fast', { seconds: 4, reduced: true }, FAST_LIMIT],
    ['reduced motion, slow', { seconds: 75, reduced: true }, SLOW_LIMIT],
  ]) {
    const { ts, shows, durations, spoken, d } = trip(deck, { ...opts, scene });
    const where = `${scene} ${label}`;
    assert.ok(shows.length <= cap, `${where}: ${shows.length} captions shown, the cap is ${cap}`);
    assert.equal(new Set(shows.map(s => s.year)).size, shows.length, `${where}: a caption showed twice`);
    for (const s of shows) {
      assert.ok(years.has(s.year), `${where}: ${s.year} is not in the deck`);
      // Only as the ticker passes: on the frame it first reads that year or below it.
      assert.ok(s.ticker <= s.year && s.before > s.year,
        `${where}: ${s.year} showed with the ticker at ${s.ticker} (was ${s.before}), not as it passed`);
    }
    for (const ms of durations.slice(0, -1)) {
      assert.ok(Math.abs(ms - HOLD_MS) <= 40, `${where}: a caption stayed ${ms} ms, not about ${HOLD_MS}`);
    }
    assert.equal(spoken.length, shows.length, `${where}: spoken ${spoken.length} times for ${shows.length} captions`);
    assert.equal(new Set(spoken).size, spoken.length, `${where}: a caption was spoken twice`);
    assert.equal(d.el.dataset.state, 'off', `${where}: the caption is still up after ready`);
    assert.equal(ts.state.stopped, true, `${where}: ready did not stop the stream`);
    if (label === 'slow' || label === 'slow, no forecast') {
      assert.ok(shows.length > FAST_LIMIT, `${where}: a slow trip showed only ${shows.length}`);
    }
    if (label === 'fast') assert.ok(shows.length >= 1, `${where}: a 4 s trip showed nothing`);
  }
}

// A fast load is one that lands inside SLOW_AFTER_MS; the fourth caption waits for it.
{
  const c = clock();
  const d = device();
  const ts = createTimeStream({ el: d.el, sayEl: d.sayEl, currentYear: 2026, now: c.now, wait: c.wait,
    cancel: c.cancel, forecast: { remaining: () => 100 }, fetcher: null });
  ts.setDeck(decks['1904']);
  for (const y of [1977, 1975, 1965, 1962, 1945, 1936, 1932, 1923, 1918, 1910, 1908]) {
    c.advance(HOLD_MS + 1);
    ts.passYear(y);
  }
  assert.ok(c.now() > SLOW_AFTER_MS);
  assert.ok(ts.state.count > FAST_LIMIT && ts.state.count <= SLOW_LIMIT,
    `a long trip passing every year shows ${ts.state.count}`);
  const early = ts.state.shown.filter(s => s.at < SLOW_AFTER_MS).length;
  assert.ok(early <= FAST_LIMIT, `${early} captions before the trip was slow`);
}

// No deck, or a broken fetch, shows nothing and throws nothing.
{
  const ts = createTimeStream({ fetcher: async () => { throw new Error('offline'); } });
  assert.equal(await ts.load('timestream/1904.json'), 0);
  ts.passYear(1966);
  assert.equal(ts.state.count, 0);
  const ts404 = createTimeStream({ fetcher: async () => ({ ok: false }) });
  assert.equal(await ts404.load('timestream/1866.json'), 0);
}

// An essential failure stops it; an optional one does not.
{
  const handlers = {};
  const ts = createTimeStream({ boot: { on: (t, fn) => { (handlers[t] ||= []).push(fn); } }, fetcher: null,
    currentYear: 2026 });
  ts.setDeck(decks['1835']);
  handlers.error[0]({ phase: { essential: false } });
  assert.equal(ts.state.stopped, false, 'an optional failure stops the captions');
  handlers.error[0]({ phase: { essential: true } });
  assert.equal(ts.state.stopped, true, 'an essential failure leaves the captions running');
  ts.passYear(1870);
  assert.equal(ts.state.count, 0);
}

// arrival.js hands the stream every year the ticker shows (the onYear hook).
{
  const seen = [];
  createArrival({ boot: { phases: [], expected: {}, on() {} }, targetYear: 1904, currentYear: 2026,
    reducedMotion: true, requestFrame: null, onYear: y => seen.push(y) });
  assert.deepEqual(seen, [2026], 'the ticker\'s first year reaches onYear');
  createArrival({ boot: { phases: [], expected: {}, on() {} }, targetYear: 1904, currentYear: 2026,
    reducedMotion: true, requestFrame: null, onYear: () => { throw new Error('a broken caption'); } });
}

// The page: the caption block stays silent, one polite line speaks; both sit on the screen.
{
  const index = readFileSync(path.join(here, '../renderers/web/index.html'), 'utf8');
  assert.match(index, /id="arrival-timestream"[^>]*aria-hidden="true"/, 'the visible caption is aria-hidden');
  assert.match(index, /id="arrival-timestream-say"[^>]*aria-live="polite"/, 'the caption is announced politely');
  assert.match(index, /class="arrival-screen"[\s\S]*id="arrival-timestream"[\s\S]*id="arrival-readout"/,
    'the caption lives on the arrival screen');
}

assert.equal(easeInOut(0.5), 0.5);
console.log('TIME-STREAM PASS — shown only as passed, ~2 s, once each; fast ≤ 3, slow ≤ 8, reduced motion and ready hold');

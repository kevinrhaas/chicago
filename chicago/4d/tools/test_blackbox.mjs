#!/usr/bin/env node
// T-2826: the black box's record, without a browser — what a page leaves, which
// records the next page shows, and the line it shows.
import assert from 'node:assert/strict';
import { createBlackbox, wasCut, summary, report, BLACKBOX_KEY, SAMPLE_MS, STALE_MS } from '../renderers/web/js/blackbox.js';

const store = () => {
  const m = new Map();
  return { getItem: k => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: k => m.delete(k), m };
};
let clock = 5_000_000;
const now = () => clock;
const sample = () => ({ calls: 236, tris: 907703, geo: 410, tex: 61, w: 390, h: 844, ratio: 1, at: '1352,-3236' });

// Every step is written as it lands, and the record keeps only the last `max`.
{
  const ls = store();
  const box = createBlackbox({ year: '1904', store: ls, now, max: 5, sample });
  assert.equal(box.previous, null, 'a first page finds no record');
  for (let i = 0; i < 8; i += 1) { clock += 10; box.log('pick', { meshes: i, batches: 1 }); }
  const kept = JSON.parse(ls.getItem(BLACKBOX_KEY));
  assert.equal(kept.entries.length, 5);
  assert.equal(kept.entries.at(-1).meshes, 7, 'the newest step is on disk at once');
}

// The renderer is read at most every SAMPLE_MS, and only the latest reading is kept.
{
  const ls = store();
  let reads = 0;
  const box = createBlackbox({ year: '1904', store: ls, now, sample: () => { reads += 1; return sample(); } });
  box.tick(); box.tick(); clock += SAMPLE_MS - 1; box.tick();
  assert.equal(reads, 1);
  clock += 1; box.tick();
  assert.equal(reads, 2);
  assert.equal(JSON.parse(ls.getItem(BLACKBOX_KEY)).last.tris, 907703);
}

// A page that left cleanly is not shown; one cut off, or one that lost its context, is.
{
  const ls = store();
  const a = createBlackbox({ year: '1904', store: ls, now, sample });
  a.log('ready'); a.end('left');
  assert.equal(wasCut(createBlackbox({ year: '1904', store: ls, now, sample }).previous, clock), false,
    'a clean exit says nothing');

  const ls2 = store();
  const b = createBlackbox({ year: '1904', store: ls2, now, sample });
  clock += 1000; b.log('ready'); clock += 3000; b.tick(); clock += 500; b.log('tap', { to: 'point' });
  clock += 40; b.log('pick', { meshes: 2, batches: 6 });
  // …and the page dies here, mid-pick: no end, no pagehide.
  const prev = createBlackbox({ year: '1904', store: ls2, now, sample }).previous;
  assert.equal(wasCut(prev, clock), true, 'a page that stopped mid-step is shown');
  const line = summary(prev);
  assert.match(line, /^Page stopped/);
  assert.match(line, /pick meshes=2 batches=6 \(0 ms before\)/);
  assert.match(line, /tap to=point \(40 ms before\)/);
  assert.match(line, /236 draws, 908k triangles, 61 textures, 410 geometries, 390×844 at 1×/);
  assert.equal(JSON.parse(report(prev)).entries.length, prev.entries.length, 'Copy carries the whole record');

  const ls3 = store();
  const c = createBlackbox({ year: '1904', store: ls3, now, sample });
  c.log('ready'); clock += 200; c.log('nav', { level: 1, app: 'home' }); clock += 900; c.log('lost'); c.end('left');
  const lostPrev = createBlackbox({ year: '1904', store: ls3, now, sample }).previous;
  assert.equal(wasCut(lostPrev, clock), true, 'a lost context is shown even though the page then reloaded cleanly');
  assert.match(summary(lostPrev), /^Display reset .*nav app=home level=1 \(900 ms before\)/);

  assert.equal(wasCut(lostPrev, clock + STALE_MS + 60_000), false, 'an old record is not shown');
}

// A page put in the background and discarded later was not cut off doing anything.
{
  const ls = store();
  const box = createBlackbox({ year: '1904', store: ls, now, sample });
  box.log('ready'); box.log('hidden');
  assert.equal(wasCut(createBlackbox({ year: '1904', store: ls, now, sample }).previous, clock), false);
}

// A store that refuses writes never throws into the page.
{
  const refusing = { getItem: () => { throw new Error('denied'); }, setItem: () => { throw new Error('full'); } };
  const box = createBlackbox({ year: '1904', store: refusing, now, sample });
  box.log('tap'); box.tick(); box.end();
  assert.equal(box.previous, null);
}

console.log('ok  the black box keeps the page\'s last steps, shows a cut-off page\'s, and never throws (T-2826)');

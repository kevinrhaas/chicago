#!/usr/bin/env node
// People met, places found (T-3673): the browser-local store and the two rules, without a
// browser. docs/CLASSROOM-FEATURES.md item 14: opening a card must never be reported as
// entering a building or physically meeting someone. So, held here:
//   1. the store is per year and per kind, an id and its first day only, bounded, never evicts;
//   2. a stored copy that cannot be read is left unchanged and said so; a browser that cannot
//      save keeps this visit's list in memory and says that; Clear <year> forgets one year;
//   3. MET is a talk (greet, story, question) from the town, with someone standing in it,
//      within 8 m, not flying: a card opened anywhere else, or a far figure, never counts;
//   4. FOUND is standing inside a named place or within 3 m of it, on foot: flying, riding,
//      aboard, Inspect and the arrival screen never count, nor an unnamed shed or privy;
//   5. the watch records each place once and allocates nothing per check.
//
//   node tools/test_met_found.mjs
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {
  METFOUND_KEY, LIMITS, TALK_M, FOUND_M, createMetFound, parseMetFound, meetingCounts, onFoot, personIdOf,
  placeTitle, placeIndex, placesAt, nearRing, createMetFoundWatch, localDay,
} from '../renderers/web/js/met-found.js';
import { dayWords, metFoundRow } from '../renderers/web/js/met-found-view.js';

const memStorage = () => { const m = new Map(); return { m, getItem: (k) => m.get(k) ?? null, setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k) }; };
const day = () => '2026-11-19';

// 1. Per year, per kind, first day only.
{
  const s = memStorage();
  const mf = createMetFound({ storage: s, today: day });
  assert.deepEqual(mf.record('1904', 'met', 'glessner_john'), { ok: true, added: true, error: null });
  assert.deepEqual(mf.record('1904', 'met', 'glessner_john'), { ok: true, added: false, error: null }, 'met twice is met once');
  assert.equal(mf.record('1835', 'met', 'glessner_john').added, true, 'another year is another list');
  assert.equal(mf.record('1904', 'found', 'glessner_house').added, true);
  const y = mf.year('1904');
  assert.deepEqual(y, { met: { glessner_john: '2026-11-19' }, found: { glessner_house: '2026-11-19' }, error: null });
  assert.deepEqual(Object.keys(mf.year('1835').found), [], '1835 found nothing');
  assert.equal(mf.has('1904', 'met', 'glessner_john'), true);
  assert.equal(mf.has('1812', 'met', 'glessner_john'), false);
  const stored = JSON.parse(s.m.get(METFOUND_KEY));
  assert.deepEqual(Object.keys(stored), ['version', 'years'], 'no totals, times, streaks or scores are stored');
  assert.deepEqual(Object.keys(stored.years['1904']).sort(), ['found', 'met']);
  assert.equal(mf.record('19o4', 'met', 'x').ok, false, 'a year is four digits');
  assert.equal(mf.record('1904', 'visited', 'x').ok, false, 'two kinds only');
  assert.equal(mf.record('1904', 'met', 'x'.repeat(LIMITS.idChars + 1)).ok, false, 'an id is bounded');
  assert.match(localDay(new Date(2026, 0, 5)), /^2026-01-05$/);
  assert.equal(dayWords('2026-11-19'), '19 November 2026');
  assert.equal(dayWords('nonsense'), '');
  // Writes are heard (the People and Map screens repaint on them).
  let heard = 0;
  const off = mf.subscribe(() => heard++);
  mf.record('1904', 'met', 'another');
  off();
  mf.record('1904', 'met', 'third');
  assert.equal(heard, 1);
}

// Bounded, never evicting.
{
  const s = memStorage();
  const mf = createMetFound({ storage: s, today: day });
  for (let i = 0; i < LIMITS.perKind; i++) assert.equal(mf.record('1835', 'met', `p${i}`).added, true);
  const full = mf.record('1835', 'met', 'one_more');
  assert.equal(full.ok, false); assert.equal(full.reason, 'full', 'a full list says so');
  assert.equal(Object.keys(mf.year('1835').met).length, LIMITS.perKind, 'nobody was evicted to make room');
  assert.equal(mf.record('1835', 'found', 'a_place').added, true, 'the other kind has its own room');
  const many = createMetFound({ storage: memStorage(), today: day });
  for (let i = 0; i < LIMITS.years; i++) many.record(String(1800 + i), 'met', 'x');
  assert.equal(many.record('1999', 'met', 'x').reason, 'full', 'and the number of years is bounded');
}

// 2. A damaged copy is left as it was; reported, never silently wiped.
for (const raw of ['{not json', JSON.stringify({ version: 2, years: {} }), JSON.stringify({ version: 1, years: { 1904: { met: { a: 'yesterday' } } } }),
  JSON.stringify({ version: 1, years: { 1904: { met: {}, score: {} } } }), JSON.stringify({ version: 1, years: [] })]) {
  assert.equal(parseMetFound(raw), null, `refused: ${raw.slice(0, 40)}`);
  const s = memStorage();
  s.m.set(METFOUND_KEY, raw);
  const mf = createMetFound({ storage: s, today: day });
  assert.equal(mf.year('1904').error, 'damaged');
  const r = mf.record('1904', 'met', 'someone');
  assert.equal(r.ok, true); assert.equal(r.error, 'damaged', 'this visit still counts, and says the saved copy is damaged');
  assert.equal(mf.has('1904', 'met', 'someone'), true);
  mf.clearYear('1904');
  assert.equal(s.m.get(METFOUND_KEY), raw, 'the stored copy is left unchanged by a record or a clear');
  assert.equal(mf.reset().ok, true, 'Start a new list replaces it, on the visitor\'s ask');
  assert.deepEqual(JSON.parse(s.m.get(METFOUND_KEY)), { version: 1, years: {} });
  assert.equal(mf.error, null);
}
{
  const s = memStorage();
  s.m.set(METFOUND_KEY, 'x'.repeat(LIMITS.chars + 1));
  assert.equal(createMetFound({ storage: s }).error, 'damaged', 'an oversized copy is not parsed');
}
// Unavailable storage: no storage, a throwing getter, a throwing write (quota).
for (const storage of [null, () => { throw new Error('denied'); }, { getItem() { throw new Error('denied'); }, setItem() {} },
  { getItem: () => null, setItem() { throw new Error('quota'); } }]) {
  const mf = createMetFound({ storage, today: day });
  const r = mf.record('1812', 'found', 'fort_dearborn');
  assert.equal(r.ok, true); assert.equal(r.added, true);
  assert.equal(r.error, 'storage', 'a browser that cannot save says so');
  assert.equal(mf.year('1812').error, 'storage');
  assert.equal(mf.has('1812', 'found', 'fort_dearborn'), true, 'and keeps the visit\'s list in memory');
}
// Clear one year only.
{
  const s = memStorage();
  const mf = createMetFound({ storage: s, today: day });
  mf.record('1904', 'met', 'a'); mf.record('1904', 'found', 'b'); mf.record('1835', 'met', 'c');
  assert.equal(mf.clearYear('1904').ok, true);
  assert.deepEqual(mf.year('1904'), { met: {}, found: {}, error: null });
  assert.deepEqual(Object.keys(mf.year('1835').met), ['c'], 'other years are kept');
}

// 3. The met rule.
{
  const person = (at, extra = {}) => ({ kind: 'person', personId: 'glessner_frances', at, ...extra });
  const me = { e: 0, n: 0, flying: false };
  assert.equal(TALK_M, 8);
  assert.equal(meetingCounts({ thing: person([2, 1]), actionId: 'greet', walker: me }), true, 'greeted at arm\'s length');
  assert.equal(meetingCounts({ thing: person([5, 6]), actionId: 'tale', walker: me }), true, 'a story heard within 8 m');
  assert.equal(meetingCounts({ thing: person([0, 7.9]), actionId: 'ask', walker: me }), true);
  assert.equal(meetingCounts({ thing: person([0, 8.1]), actionId: 'greet', walker: me }), false, 'a figure picked from across the street is not met');
  assert.equal(meetingCounts({ thing: person([40, 0]), actionId: 'greet', walker: me }), false);
  for (const via of ['card', 'directory', 'search', 'inspect', 'jaunt', 'link'])
    assert.equal(meetingCounts({ thing: person([1, 0]), actionId: 'greet', walker: me, via }), false, `a card opened from ${via} is not meeting them`);
  assert.equal(meetingCounts({ thing: person(null), actionId: 'greet', walker: me }), false, 'someone indoors or not in town is not met');
  assert.equal(meetingCounts({ thing: person([1, 0]), actionId: 'go_home', walker: me }), false, 'sending someone home is not talking with them');
  assert.equal(meetingCounts({ thing: person([1, 0]), actionId: 'greet', walker: { ...me, flying: true } }), false, 'not from the air');
  assert.equal(meetingCounts({ thing: { kind: 'door', at: [1, 0] }, actionId: 'greet', walker: me }), false);
  assert.equal(meetingCounts({ thing: person([1, 0]), actionId: 'greet', walker: null }), false);
  assert.equal(personIdOf({ kind: 'person', actor: { personId: 'x' } }), 'x');
}

// 4. The found rule and what counts as a place.
{
  const sq = (e, n, s, id) => Object.assign([[e - s, n - s], [e + s, n - s], [e + s, n + s], [e - s, n + s]], { id });
  const names = { house: 'The Glessner house', shed: 'A shed', privy: 'Privy', lot: 'lot_7_block_16', generic: 'A building', store: 'Dole’s store' };
  const outlines = [sq(0, 0, 10, 'house'), sq(30, 0, 2, 'shed'), sq(40, 0, 2, 'privy'), sq(60, 0, 5, 'lot'), sq(80, 0, 5, 'generic'),
    sq(100, 0, 5, 'store'), sq(100, 30, 5, 'store')];
  const index = placeIndex(outlines, (id) => names[id]);
  assert.deepEqual(index.ids, ['house', 'store'], 'named places only: no shed, privy, id or "A building"');
  assert.equal(index.count, 2, 'a place of two footprints is one place');
  assert.equal(placeTitle('The Pratt house'), 'The Pratt house');
  assert.equal(placeTitle('Woodshed'), null);
  const on = (e, n, extra = {}) => ({ e, n, flying: false, ...extra });
  assert.deepEqual([...placesAt(index, on(0, 0))], ['house'], 'inside');
  assert.deepEqual([...placesAt(index, on(12.5, 0))], ['house'], `on the doorstep, within ${FOUND_M} m of the wall`);
  assert.deepEqual([...placesAt(index, on(13.5, 0))], [], 'past it is not there');
  assert.deepEqual([...placesAt(index, on(100, 30))], ['store'], 'either footprint of a place');
  assert.deepEqual([...placesAt(index, on(30, 0))], [], 'a shed is not a place');
  for (const [why, extra] of [['flying', { flying: true }], ['riding', { riding: true }], ['aboard', { aboard: true }],
    ['at a helm', { piloting: true }], ['in Inspect', { inspecting: true }], ['on the arrival screen', { gate: true }]])
    assert.deepEqual([...placesAt(index, on(0, 0, extra))], [], `never ${why}`);
  assert.equal(onFoot({ e: NaN, n: 0 }), false);
  assert.equal(nearRing(sq(0, 0, 1, 'x'), 0, 3.9, 3), true);

  // 5. The watch: once per place, nothing for a card, and Inspect does not move you.
  const s = memStorage();
  const store = createMetFound({ storage: s, today: day });
  let pose = on(500, 500);
  const watch = createMetFoundWatch({ store, year: '1904', walker: () => pose, places: () => index });
  assert.equal(watch.tick(), 0, 'nowhere');
  pose = on(0, 0, { inspecting: true });
  assert.equal(watch.tick(), 0, 'Inspect over a house is not standing in it');
  pose = on(0, 0, { flying: true });
  assert.equal(watch.tick(), 0, 'nor flying over it');
  pose = on(0, 0);
  assert.equal(watch.tick(), 1, 'standing in it finds it');
  assert.equal(watch.tick(), 0, 'once');
  assert.deepEqual(Object.keys(store.year('1904').found), ['house']);
  // Two places at once (a house and the store next to it): both, in one check.
  const pair = placeIndex([sq(0, 0, 10, 'house'), sq(22, 0, 10, 'store')], (id) => names[id]);
  const s2 = createMetFound({ storage: memStorage(), today: day });
  let both = on(11, 0);
  const w3 = createMetFoundWatch({ store: s2, year: '1835', walker: () => both, places: () => pair });
  assert.equal(w3.tick(), 2, 'two places in reach are both found in one check');
  assert.deepEqual(Object.keys(s2.year('1835').found).sort(), ['house', 'store']);
  assert.equal(w3.tick(), 0);
  both = on(0, 0);
  assert.equal(w3.tick(), 0);
  w3.dispose();
  // Nothing allocated per check: the same output array, and no store read once known.
  let reads = 0;
  const counting = { ...store, year: (y) => { reads++; return store.year(y); }, subscribe: store.subscribe, record: store.record };
  const w2 = createMetFoundWatch({ store: counting, year: '1904', walker: () => pose, places: () => index });
  w2.tick(); w2.tick(); w2.tick();
  assert.equal(reads, 1, 'the found list is read once, then kept');
  store.clearYear('1904');
  pose = on(0, 0);
  assert.equal(watch.tick(), 1, 'after Clear 1904 the house can be found again');
  // Talk: the engine's finished action, from the town.
  pose = on(0, 0);
  assert.equal(watch.talked({ kind: 'person', personId: 'p1', at: [2, 0] }, 'greet')?.added, true);
  assert.equal(watch.talked({ kind: 'person', personId: 'p2', at: [20, 0] }, 'greet'), null, 'too far to have talked');
  assert.deepEqual(Object.keys(store.year('1904').met), ['p1']);
  watch.dispose();
}

// The row People and the Map show: count, Clear <year> with Clear / Keep, a visible status.
{
  const mk = (tag) => {
    const on = {};
    const el = { tagName: tag, children: [], hidden: false, textContent: '', className: '', title: '', attrs: {}, focused: 0,
      append(...c) { el.children.push(...c); }, setAttribute(k, v) { el.attrs[k] = String(v); },
      addEventListener(t, fn) { on[t] = fn; }, fire(t, e = {}) { on[t]?.({ preventDefault() {}, stopPropagation() {}, ...e }); }, focus() { el.focused++; } };
    return el;
  };
  const doc = { createElement: mk };
  const s = memStorage();
  const store = createMetFound({ storage: s, today: day });
  store.record('1904', 'met', 'a'); store.record('1835', 'met', 'b');
  let pressed = false;
  const row = metFoundRow(doc, { year: '1904', cls: 'x', toggleCls: 'y', store, title: 't',
    text: () => `Met ${Object.keys(store.year('1904').met).length} of 3`, pressed: () => pressed, onToggle: () => { pressed = !pressed; } });
  assert.equal(row.toggle.textContent, 'Met 1 of 3');
  assert.equal(row.toggle.attrs['aria-pressed'], 'false');
  row.toggle.fire('click');
  assert.equal(row.toggle.attrs['aria-pressed'], 'true', 'the filter is a pressed toggle');
  assert.equal(row.clear.textContent, 'Clear 1904');
  assert.match(row.status.textContent, /this browser only/);
  row.clear.fire('click');
  assert.equal(row.ask.hidden, false); assert.equal(row.clear.hidden, true);
  assert.equal(row.no.focused, 1, 'the confirm opens on Keep');
  row.no.fire('click');
  assert.equal(Object.keys(store.year('1904').met).length, 1, 'Keep keeps');
  row.clear.fire('click');
  row.ask.fire('keydown', { key: 'Escape' });
  assert.equal(row.ask.hidden, true, 'Escape closes the confirm');
  row.clear.fire('click'); row.yes.fire('click');
  assert.equal(Object.keys(store.year('1904').met).length, 0, 'Clear clears this year');
  assert.equal(Object.keys(store.year('1835').met).length, 1, '…and only this year');
  assert.equal(row.status.textContent, 'Cleared for 1904.');
  row.paint(); row.quiet(); row.paint();
  assert.equal(row.toggle.textContent, 'Met 0 of 3');
  // A damaged copy: said, and Clear becomes Start a new list.
  const bad = memStorage(); bad.m.set(METFOUND_KEY, '{');
  const badStore = createMetFound({ storage: bad, today: day });
  const r2 = metFoundRow(doc, { year: '1812', cls: 'x', toggleCls: 'y', store: badStore, title: 't', text: () => '', pressed: () => false, onToggle() {} });
  assert.match(r2.status.textContent, /could not be read/);
  assert.match(r2.status.className, /is-problem/);
  assert.equal(r2.clear.textContent, 'Start a new list');
  r2.clear.fire('click'); r2.yes.fire('click');
  assert.equal(bad.m.get(METFOUND_KEY), JSON.stringify({ version: 1, years: {} }), 'replaced only on the visitor\'s ask');
  // Unavailable storage is said.
  const r3 = metFoundRow(doc, { year: '1812', cls: 'x', toggleCls: 'y', store: createMetFound({ storage: null }), title: 't', text: () => '', pressed: () => false, onToggle() {} });
  assert.match(r3.status.textContent, /not saving/);
}

// The views read only the store; the person cards add nothing (no record() outside the town).
{
  const web = new URL('../renderers/web/js/', import.meta.url);
  for (const f of ['apps/people-view.js', 'people.js', 'apps/map-view.js', 'met-found-view.js', 'person-card.js'])
    assert.doesNotMatch(fs.readFileSync(new URL(f, web), 'utf8'), /\.record\(/, `${f} never records a meeting or a place`);
  const main = fs.readFileSync(new URL('main.js', web), 'utf8');
  assert.match(main, /interactions\.on\(\(thing, event\) => \{ if \(event === 'done'\) try \{ api\.metFound\.talked\(thing, thing\.last\?\.id\); \}/,
    'main.js tells the watch only of finished Interact actions');
  assert.match(main, /if \(\(metFoundAt \+= elapsed\) >= 1\) \{ metFoundAt = 0; try \{ api\.metFound\?\.tick\(\); \}/, 'and checks places about once a second');
  for (const f of ['met-found.js', 'met-found-view.js'])
    assert.doesNotMatch(fs.readFileSync(new URL(f, web), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '').replace(/\/\/.*$/gm, ''),
      /fetch\(|XMLHttpRequest|sendBeacon|WebSocket|streak|leaderboard|score/i, `${f}: no network, streaks or scores`);
}

console.log(`Met and found (T-3673): ok — per-year bounded store, damaged/unavailable storage visible, Clear <year>; met within ${TALK_M} m from the town only, found within ${FOUND_M} m on foot only`);

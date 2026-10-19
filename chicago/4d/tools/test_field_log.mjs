#!/usr/bin/env node
// T-2660 (NAV-S02; DESIGN §14 "Measure fun"): the field log. Landings, the first inspect
// after a landing (with the seconds it took), Inspect tabs, Show me, Jaunts started and
// finished, Tour steps and Confidence view presets are counted in localStorage only, shown
// in Settings › About with Clear, and NEVER SENT. This proves the last part three ways:
//   1. the module's source holds no import and no network door at all;
//   2. every event, Clear and a read run with every network door trapped, and none is used;
//   3. each hook is one countField(...) call, so no hook can carry the log anywhere either.
// The smoke (part 13) watches the page's own requests while the events fire.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WEB = path.join(ROOT, 'renderers', 'web');
const read = (p) => fs.readFileSync(path.join(WEB, p), 'utf8');
const code = (src) => src.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`])\/\/.*$/gm, '$1');

// ---- 1. the source: nothing imported, no network door named.
const DOORS = /\b(fetch|XMLHttpRequest|sendBeacon|WebSocket|EventSource|RTCPeerConnection|importScripts|postMessage|BroadcastChannel|serviceWorker|navigator|location|document|Image|Worker|open)\b|\bimport\s*\(|\.src\b|\bhttps?:/;
{
  const src = code(read('js/field-log.js'));
  assert.ok(!/^\s*import\b/m.test(src), 'field-log.js imports nothing');
  assert.ok(!/\bexport\s+\*?\s*\{?[^;]*\bfrom\b/.test(src), 'and re-exports nothing');
  const door = src.match(DOORS);
  assert.equal(door, null, `field-log.js names no network door (found ${door?.[0]})`);
  assert.ok(/localStorage/.test(src), 'its one store is localStorage');
}
{
  // The About view builds DOM nodes and imports only the string table and the log.
  const src = code(read('js/field-log-view.js'));
  const imports = [...src.matchAll(/^\s*import\b[^;]*?['"]([^'"]+)['"]/gm)].map((m) => m[1]).sort();
  assert.deepEqual(imports, ['./field-log.js', './strings/field-log.js', './strings/index.js'], 'the view imports only the table and the log');
  const door = src.replace(/\bdoc(ument)?\b/g, '').match(/\b(fetch|XMLHttpRequest|sendBeacon|WebSocket|EventSource|postMessage|location|Image)\b|\bimport\s*\(|\.src\b|\bhttps?:/);
  assert.equal(door, null, `field-log-view.js names no network door (found ${door?.[0]})`);
}

// ---- 2. every event with each network door trapped.
const used = [];
const trap = (name) => function trapped() { used.push(name); throw new Error(`${name} must never be called by the field log`); };
const define = (obj, key, value) => Object.defineProperty(obj, key, { value, configurable: true, writable: true });
const mem = () => { const m = new Map(); return { getItem: (k) => (m.has(k) ? m.get(k) : null), setItem: (k, v) => m.set(k, String(v)), removeItem: (k) => m.delete(k), m }; };
const page = mem();
define(globalThis, 'localStorage', page);
define(globalThis, 'fetch', trap('fetch'));
define(globalThis, 'XMLHttpRequest', trap('XMLHttpRequest'));
define(globalThis, 'WebSocket', trap('WebSocket'));
define(globalThis, 'EventSource', trap('EventSource'));
define(globalThis, 'Image', trap('Image'));
define(globalThis, 'navigator', { sendBeacon: trap('sendBeacon'), userAgent: 'test' });

const { fieldLog, count, createFieldLog, emptyLog, normalLog, EVENTS, COUNTS, FIELD_LOG_KEY, QUICK_INSPECT_S } =
  await import('../renderers/web/js/field-log.js');

assert.equal(FIELD_LOG_KEY, 'chicago4d.fieldLog');
assert.equal(QUICK_INSPECT_S, 90, 'the design\'s target: a first inspect within 90 s');
assert.deepEqual(COUNTS, ['landed', 'firstInspect', 'tab', 'showMe', 'jauntStarted', 'jauntFinished', 'tourStep', 'confidencePreset']);
for (const e of EVENTS) count(e);
count('inspect');
fieldLog.read();
fieldLog.clear();
for (const e of EVENTS) count(e);
assert.deepEqual(used, [], `no network door was touched (used: ${used.join(', ')})`);
assert.ok(page.m.has(FIELD_LOG_KEY), 'the page\'s one field log keeps itself in localStorage');
const kept = JSON.parse(page.m.get(FIELD_LOG_KEY));
assert.deepEqual(Object.keys(kept).sort(), ['counts', 'lastFirstInspectS', 'quick'], 'and keeps only counts — no id, path, name or time of day');
assert.ok(COUNTS.every((k) => kept.counts[k] === 1), JSON.stringify(kept.counts));

// ---- the counts themselves, over a fake store and clock.
{
  const s = mem();
  let t = 1000;
  const log = createFieldLog({ storage: s, now: () => t });
  assert.deepEqual(log.read(), emptyLog(), 'a new device starts empty');
  assert.equal(log.count('landed'), 1);
  t += 41_000;
  assert.equal(log.count('inspect'), 1, 'the first inspect after landing counts');
  assert.equal(log.count('inspect'), null, 'and only the first');
  let r = log.read();
  assert.equal(r.counts.firstInspect, 1);
  assert.equal(r.lastFirstInspectS, 41, 'with the seconds since landing');
  assert.equal(r.quick, 1, 'within 90 s');
  for (const e of ['tab', 'tab', 'showMe', 'jauntStarted', 'jauntFinished', 'tourStep', 'tourStep', 'tourStep', 'confidencePreset']) log.count(e);
  r = log.read();
  assert.deepEqual(r.counts, { landed: 1, firstInspect: 1, tab: 2, showMe: 1, jauntStarted: 1, jauntFinished: 1, tourStep: 3, confidencePreset: 1 });
  assert.equal(log.count('firstInspect'), null, 'firstInspect is decided by inspect, never said by a hook');
  assert.equal(log.count('purchase'), null, 'an event this does not keep is refused');
  assert.equal(log.read().counts.firstInspect, 1);
  // A second visit from this device: the log is read back, and a slow inspect is not quick.
  const again = createFieldLog({ storage: s, now: () => t });
  assert.deepEqual(again.read(), log.read(), 'the next visit reads the same log back');
  again.count('landed');
  t += 125_000;
  again.count('inspect');
  r = again.read();
  assert.equal(r.counts.landed, 2);
  assert.equal(r.counts.firstInspect, 2);
  assert.equal(r.lastFirstInspectS, 125);
  assert.equal(r.quick, 1, 'two minutes is not within 90 s');
  // Subscribers hear every change; Clear empties it here and in storage.
  const heard = [];
  const off = again.subscribe((l) => heard.push(l.counts.showMe));
  again.count('showMe');
  assert.deepEqual(heard, [2]);
  assert.deepEqual(again.clear(), emptyLog(), 'Clear empties the log');
  assert.equal(s.getItem(FIELD_LOG_KEY), null, 'and takes it out of storage');
  assert.deepEqual(heard, [2, 0], 'and says so');
  off();
  again.count('showMe');
  assert.deepEqual(heard, [2, 0], 'unsubscribed is unsubscribed');
  assert.equal(createFieldLog({ storage: s }).read().counts.showMe, 1, 'counting goes on after a Clear');
}
// An inspect with no landing on this page counts, with no time.
{
  const log = createFieldLog({ storage: mem() });
  log.count('inspect');
  assert.equal(log.read().counts.firstInspect, 1);
  assert.equal(log.read().lastFirstInspectS, null);
}
// Storage refused (a private window, blocked site data): kept for the page, never a throw.
{
  const refusing = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); }, removeItem() { throw new Error('denied'); } };
  for (const storage of [refusing, null, () => { throw new Error('SecurityError'); }]) {
    const log = createFieldLog({ storage });
    for (const e of EVENTS) assert.doesNotThrow(() => log.count(e), `count(${e}) with storage refused`);
    assert.equal(log.read().counts.tab, 1, 'the page still counts');
    assert.doesNotThrow(() => log.clear());
    assert.equal(log.read().counts.tab, 0);
  }
  // A full store (setItem refused, getItem fine) keeps counting in the page.
  const full = { getItem: () => null, setItem() { throw new Error('QuotaExceededError'); }, removeItem() {} };
  const log = createFieldLog({ storage: full });
  log.count('showMe'); log.count('showMe');
  assert.equal(log.read().counts.showMe, 2);
}
// Garbage in storage is read as an empty log, and odd values as whole counts.
{
  const s = mem();
  s.setItem(FIELD_LOG_KEY, '{not json');
  assert.deepEqual(createFieldLog({ storage: s }).read(), emptyLog());
  assert.deepEqual(normalLog({ counts: { landed: '3', tab: -2, showMe: 2.7, extra: 9 }, quick: 'x', lastFirstInspectS: 12.4, url: 'https://x' }),
    { counts: { ...emptyLog().counts, landed: 3, showMe: 2 }, lastFirstInspectS: 12, quick: 0 });
}

// ---- Settings › About: the rows in plain words, and Clear.
{
  const { fieldLogRows, paintFieldLog, wireFieldLogView, duration } = await import('../renderers/web/js/field-log-view.js');
  assert.equal(duration(41), '41 s');
  assert.equal(duration(125), '2 min 5 s');
  const rows = fieldLogRows({ ...emptyLog(), counts: { ...emptyLog().counts, landed: 3, firstInspect: 2, tab: 4 }, lastFirstInspectS: 41, quick: 2 });
  assert.deepEqual(rows.map((r) => r.label), ['Landings', 'Landings with a building inspected', 'Time to first inspect',
    'Inspect tabs opened', 'Show me used', 'Jaunts started', 'Jaunts finished', 'Tour steps reached', 'Confidence view presets chosen']);
  assert.equal(rows[2].value, '41 s last time, 2 of 3 within 90 s');
  assert.equal(rows[3].value, '4');
  assert.equal(fieldLogRows(emptyLog())[2].value, 'Not yet');
  for (const r of rows) assert.ok(!/[a-z][A-Z]|_/.test(r.label + r.value), `no event name or snake_case reaches a visitor: ${r.label}`);

  const nodes = new Map();
  const el = (tag) => {
    const fns = {};
    return { tag, textContent: '', dataset: {}, children: [], replaceChildren(...c) { this.children = c; },
      addEventListener: (t, fn) => { (fns[t] ??= []).push(fn); }, click: () => (fns.click ?? []).forEach((f) => f()) };
  };
  for (const id of ['s-field-log-rows', 's-field-log-clear', 's-field-log-status']) nodes.set(id, el('x'));
  const doc = { getElementById: (id) => nodes.get(id) ?? null, createElement: (tag) => el(tag) };
  const log = createFieldLog({ storage: mem() });
  wireFieldLogView({ doc, log });
  const list = nodes.get('s-field-log-rows');
  const cell = (key) => list.children.find((c) => c.dataset.fieldLog === key)?.textContent;
  assert.equal(list.children.length, 18, 'nine rows, each a label and its count');
  assert.equal(cell('showMe'), '0');
  log.count('showMe');
  assert.equal(cell('showMe'), '1', 'About repaints as the log changes');
  nodes.get('s-field-log-clear').click();
  assert.equal(cell('showMe'), '0', 'Clear empties it');
  assert.equal(nodes.get('s-field-log-status').textContent, 'Cleared. Nothing was kept anywhere else.');
  log.count('tab');
  assert.equal(nodes.get('s-field-log-status').textContent, '', 'and the note goes at the next count');
  assert.equal(paintFieldLog({ doc: { getElementById: () => null } }), null, 'no section, no paint');
}

// ---- the Tour's steps: reached ones count, a reload resuming one does not.
{
  const { createTour } = await import('../renderers/web/js/tour.js');
  fieldLog.clear();
  const tour = createTour({ storage: mem() });
  tour.start();
  tour.press();
  assert.equal(fieldLog.read().counts.tourStep, 2, 'steps 01 and 02 reached');
  const s = mem();
  createTour({ storage: s }).start();
  const before = fieldLog.read().counts.tourStep;
  assert.equal(createTour({ storage: s }).resume(), true);
  assert.equal(fieldLog.read().counts.tourStep, before, 'a reload resuming a step is not a step reached');
}

// ---- 3. the hooks: one countField call each, at the place the ticket names.
{
  const HOOKS = [
    ['js/main.js', /journey\.on\(\(\{ to \}\) => \{ if \(to === 'landed'\) countField\('landed'\); \}\)/, 'landed: the journey reaching landed'],
    ['js/main.js', /onShow: \(record\) => \{[\s\S]{0,200}countField\('inspect'\)/, 'inspect: a building card drawn'],
    ['js/main.js', /function showMeFor\([\s\S]{0,3000}countField\('showMe'\);[^\n]*\n\s*return showMe\.show\(target\)/, 'showMe: Show me'],
    ['js/apps/inspect-view.js', /function render\([\s\S]{0,500}countField\('inspect'\)/, 'inspect: Inspect drawing a building'],
    ['js/apps/inspect-view.js', /function selectTab\([\s\S]{0,400}countField\('tab'\)/, 'tab: an Inspect tab'],
    ['js/jaunts.js', /dispatch\(\{ type: 'ARRIVE', session: generation, leg: state\.leg \}\);\s*\n\s*countField\('jauntStarted'\)/, 'jauntStarted'],
    ['js/jaunts.js', /state\.phase === 'outcome' && old\.phase !== 'outcome'\) \{\s*\n\s*countField\('jauntFinished'\)/, 'jauntFinished'],
    ['js/tour.js', /if \(!resumed\) countField\('tourStep'\)/, 'tourStep'],
    ['js/apps/confidence-view.js', /applyPreset\(p\.id, d\); countField\('confidencePreset'\)/, 'confidencePreset: a preset picked in the app'],
  ];
  for (const [file, re, what] of HOOKS) assert.ok(re.test(read(file)), `${file} hooks ${what}`);
  const said = new Set();
  for (const file of ['js/main.js', 'js/apps/inspect-view.js', 'js/jaunts.js', 'js/tour.js', 'js/apps/confidence-view.js']) {
    const src = read(file);
    for (const m of src.matchAll(/countField\(([^)]*)\)/g)) {
      assert.match(m[1], /^'[a-zA-Z]+'$/, `${file}: a hook passes only an event name, never data (${m[0]})`);
      said.add(m[1].slice(1, -1));
    }
    assert.ok(!/fieldLog\.read\b/.test(src), `${file} never reads the log back`);
  }
  assert.deepEqual([...said].sort(), [...EVENTS].sort(), 'every event the log keeps has its hook, and no hook says another');
  // The section is in Settings › About, with the ids the smoke reads.
  const html = read('index.html');
  const about = html.slice(html.indexOf('id="s-about"'), html.indexOf('data-panel="controls"'));
  for (const id of ['s-field-log', 's-field-log-rows', 's-field-log-clear', 's-field-log-status']) assert.ok(about.includes(`id="${id}"`), `#${id} is in Settings › About`);
}

console.log('field log: counted on the device only, shown in About with Clear, never sent — OK');

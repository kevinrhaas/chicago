// T-2612 — the arrival telemetry (js/arrival-telemetry.js): YEARS TO GO, the four named
// lamps on the real boot phases, and the log lines from each destination's deck.
//
//   node tools/test_arrival_telemetry.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createTelemetry, groupState, yearsToGo, LAMP_GROUPS, MACHINE_LINES } from '../renderers/web/js/arrival-telemetry.js';
import { createBoot, PHASES } from '../renderers/web/js/boot-phases.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const deck = year => JSON.parse(readFileSync(path.join(here, `../data/timestream/${year}.json`), 'utf8'));

// The groups cover every phase the old six lamps showed, plus people; census has no lamp.
const grouped = LAMP_GROUPS.flatMap(([, , ids]) => ids);
assert.deepEqual([...grouped].sort(), PHASES.map(([id]) => id).filter(id => id !== 'census').sort(),
  'the four lamps stand on every boot phase but census, once each');
assert.deepEqual(LAMP_GROUPS.map(([g]) => g), ['streets', 'buildings', 'trees', 'people']);

assert.equal(yearsToGo(2026, 1904), 122);
assert.equal(yearsToGo(1904, 1904), 0);
assert.equal(yearsToGo(1900, 1904), 0, 'never negative');

const P = (id, o = {}) => ({ id, essential: id !== 'people' && id !== 'census', startedAt: null, endedAt: null, error: null, ...o });
assert.equal(groupState([P('scene'), P('terrain'), P('ground')], ['scene', 'terrain', 'ground']), null);
assert.equal(groupState([P('scene', { startedAt: 1 }), P('terrain'), P('ground')], ['scene', 'terrain', 'ground']), 'active');
assert.equal(groupState([P('scene', { startedAt: 1, endedAt: 2 }), P('terrain', { startedAt: 2, endedAt: 3 }), P('ground')],
  ['scene', 'terrain', 'ground']), 'partial', 'STREETS glows dim, waiting for the ground');
assert.equal(groupState([P('scene', { startedAt: 1, endedAt: 2 }), P('terrain', { startedAt: 2 }), P('ground')],
  ['scene', 'terrain', 'ground']), 'active', 'STREETS blinks while the terrain runs');
assert.equal(groupState([P('people', { startedAt: 1, endedAt: 2, error: 'x' }), P('interaction', { startedAt: 1, endedAt: 3 })],
  ['people', 'interaction']), 'done', 'an optional failure does not hold PEOPLE dark');
assert.equal(groupState([P('flora', { startedAt: 1, endedAt: 2, error: 'x' })], ['flora']), 'fault');

/** The page's lamps, log rows and years cell as plain objects. */
function page() {
  const lamps = Object.fromEntries(LAMP_GROUPS.map(([g]) => [g, { dataset: {} }]));
  const lampsEl = { querySelector: sel => lamps[/data-group="(\w+)"/.exec(sel)?.[1]] ?? null };
  const rows = [0, 1, 2].map(() => ({ textContent: '', className: '', dataset: {} }));
  return { lamps, lampsEl, rows, logEl: { children: rows }, yearsEl: { textContent: '—' } };
}

for (const year of [1812, 1835, 1904]) {
  const d = deck(year);
  let t = 0;
  const boot = createBoot({ now: () => t });
  const p = page();
  const tel = createTelemetry({ boot, targetYear: year, currentYear: 2026, lampsEl: p.lampsEl, logEl: p.logEl, yearsEl: p.yearsEl });
  assert.equal(p.yearsEl.textContent, String(2026 - year), `${year}: YEARS TO GO starts at the present`);
  assert.ok(Object.values(p.lamps).every(l => l.dataset.state === undefined), `${year}: a lamp lit before its phase`);

  boot.start('scene');
  assert.equal(p.lamps.streets.dataset.state, 'active');
  assert.equal(p.rows[2].textContent, MACHINE_LINES.scene, `${year}: the first line shows before the deck arrives`);
  assert.equal(p.rows[2].className, 'run fresh');
  tel.setDeck(d);
  assert.equal(p.rows[2].textContent, d.log.scene, `${year}: a row already up takes the deck's wording`);
  t = 10; boot.end('scene');
  assert.equal(p.rows[2].className, 'ok');
  for (const [id, at] of [['terrain', 20], ['buildings', 30], ['ground', 40], ['flora', 50]]) {
    boot.start(id); t = at; boot.end(id);
  }
  assert.equal(p.lamps.streets.dataset.state, 'done', `${year}: STREETS lights when scene, terrain and ground finish`);
  assert.equal(p.lamps.buildings.dataset.state, 'done');
  assert.equal(p.lamps.trees.dataset.state, 'done');
  assert.equal(p.lamps.people.dataset.state, undefined);
  assert.deepEqual(p.rows.map(r => r.textContent), [d.log.buildings, d.log.ground, d.log.flora],
    `${year}: the log scrolls the deck's lines, newest last`);
  boot.start('interaction');
  assert.equal(p.lamps.people.dataset.state, 'active');
  boot.start('people');
  if (year === 1812) boot.fail('people', 'no directory'); else boot.end('people');
  assert.equal(p.rows.find(r => r.textContent === d.log.people).className, year === 1812 ? 'skip' : 'ok');
  assert.equal(p.lamps.people.dataset.state, 'active', `${year}: PEOPLE waits for interaction too`);
  boot.end('interaction');
  assert.equal(p.lamps.people.dataset.state, 'done', `${year}: PEOPLE lights when people and interaction finish`);
  assert.ok(Object.values(p.lamps).every(l => l.dataset.state === 'done'), `${year}: all four lamps lit at the end`);

  for (const y of [2000, 1990, 2010, year + 1, year]) tel.year(y);
  assert.equal(p.yearsEl.textContent, '0', `${year}: YEARS TO GO lands on 0 and never climbs back`);
  assert.ok(p.rows.every(r => !/[a-z0-9]+_[a-z0-9]+/i.test(r.textContent)), `${year}: an id in the log`);
}

// An essential failure faults its lamp and its log line.
{
  const boot = createBoot({ now: () => 0 });
  const p = page();
  createTelemetry({ boot, targetYear: 1835, lampsEl: p.lampsEl, logEl: p.logEl, yearsEl: p.yearsEl });
  boot.start('scene'); boot.end('scene'); boot.start('terrain'); boot.fail('terrain', 'tiles 404');
  assert.equal(p.lamps.streets.dataset.state, 'fault');
  assert.equal(p.rows[2].className, 'fault');
}

// The page: four lamps, named, on their phases; YEARS TO GO beside Payload, Link and ETA.
{
  const index = readFileSync(path.join(here, '../renderers/web/index.html'), 'utf8');
  const lamps = index.match(/<ul id="arrival-lamps"[\s\S]*?<\/ul>/)?.[0] ?? '';
  for (const [group, label, ids] of LAMP_GROUPS) {
    assert.match(lamps, new RegExp(`data-group="${group}" data-phases="${ids.join(' ')}"><i></i>${label}<`),
      `the ${label} lamp is on the page, on its phases`);
  }
  assert.doesNotMatch(lamps, /Struct|Sync|Flora/, 'the old lamp names are gone');
  assert.match(index, /id="arrival-readout"[\s\S]*data-read="bytes"[\s\S]*data-read="rate"[\s\S]*data-read="eta"[\s\S]*Years to go<\/dt><dd data-telemetry="years">/,
    'YEARS TO GO sits after Payload, Link and ETA');
  const css = readFileSync(path.join(here, '../renderers/web/css/walk.css'), 'utf8');
  assert.match(css, /prefers-reduced-motion: reduce\)[\s\S]*?\.arrival-log li\.fresh \{ animation: none; \}|prefers-reduced-motion: reduce\)[\s\S]*?\.arrival-log li\.fresh[^{]*\{ animation: none; \}/,
    'reduced motion stops the log line animation');
}

console.log('ARRIVAL TELEMETRY PASS — four named lamps on real phases, YEARS TO GO to 0, deck log lines, faults and skips');

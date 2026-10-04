import assert from 'node:assert/strict';
import fs from 'node:fs';
import { yearForProgress, createArrival } from '../renderers/web/js/arrival.js';
import { createBoot } from '../renderers/web/js/boot-phases.js';
import { scenePresentation, arrivalTitles } from '../renderers/web/js/scene-presentation.js';
for (const year of [1812, 1835, 1904, 1920]) {
  let prior = 2026;
  for (let i = 0; i <= 100; i++) {
    const value = yearForProgress(i / 100, 2026, false, year);
    assert(value <= prior && value >= year + 1); prior = value;
  }
  assert.equal(yearForProgress(1, 2026, true, year), year);
  const boot = createBoot({ now: () => 0 });
  const arrival = createArrival({ boot, targetYear: year, reducedMotion: true, requestFrame: null });
  for (const p of boot.phases.filter(p => p.essential)) { boot.start(p.id); boot.end(p.id); }
  boot.frameRendered(); boot.finish();
  assert.equal(arrival.state.year, year);
  assert(scenePresentation(year).welcomeTitle.includes(String(year)));
}
const prairie = scenePresentation('1904', '1904-07-01');
assert(prairie.intro.includes('1 July 1904'));
assert(prairie.entries.every(e => !/1835|Thompson|Hathaway|prairie$/i.test(e.text)));
for (const e of prairie.entries) for (const source of e.source_ids || []) {
  assert(fs.existsSync(new URL(`../data/sources/${source}.json`, import.meta.url)));
  assert(e.locator);
}
// T-0472: the 1812 welcome names its fort, and every quote on its cards resolves.
const fort = scenePresentation('1812', '1812-08-01');
assert.equal(fort.eyebrow, 'The first Fort Dearborn');
assert(fort.intro.includes('1 August 1812'));
const scene1812 = JSON.parse(fs.readFileSync(new URL('../data/scenes/1812.json', import.meta.url)));
assert(scene1812.cards.length && !scene1812.released);
for (const card of scene1812.cards) for (const q of card.quotes || []) {
  assert(fs.existsSync(new URL(`../data/sources/${q.source_id}.json`, import.meta.url)));
  assert(q.cite && q.locator);
}
assert.equal(arrivalTitles(1904).length, 8);
assert(arrivalTitles(1904).includes('Approaching Chicago, 1904'));
for (const year of ['1835', '1904']) {
  const catalog = JSON.parse(fs.readFileSync(new URL(`../data/sidecars/${year}/jaunts/catalog.json`, import.meta.url)));
  assert.equal(catalog.scene, year); assert(catalog.jaunts.length);
  for (const row of catalog.jaunts) {
    const content = JSON.parse(fs.readFileSync(new URL(`../data/sidecars/${year}/jaunts/${row.id}.json`, import.meta.url)));
    assert.equal(content.scene, year);
  }
}
console.log('SELECTED YEAR PASS — rollback, actual readiness, dated copy, source references and isolated catalogs');
for (const reducedMotion of [false, true]) {
  let clock = 0, callback;
  const titleEl = { textContent: '' }, phaseEl = { hidden: true, setAttribute() {} };
  const boot = createBoot({ now: () => clock });
  const arrival = createArrival({ boot, targetYear: 1904, titleEl, phaseEl, reducedMotion,
    now: () => clock, requestFrame: fn => { callback = fn; return 1; }, cancelFrame() {} });
  clock = 3001; callback();
  assert.equal(titleEl.textContent, reducedMotion ? 'Preparing your arrival' : 'Setting temporal coordinates');
  arrival.fail(new Error('test failure'));
  const title = titleEl.textContent; clock = 7000; callback();
  assert.equal(titleEl.textContent, title); assert.equal(phaseEl.hidden, false);
}
console.log('TITLE PASS — paced rotation, reduced-motion stability and error stop');

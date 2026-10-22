#!/usr/bin/env node
// Independent measured pins, including actual confidence transitions; no WebGL.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { renderBudget } from '../renderers/web/js/render-budget.js';
const vendor = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
const confidenceSource = fs.readFileSync(new URL('../renderers/web/js/confidence.js', import.meta.url), 'utf8')
  .replace("from 'three'", `from '${vendor}'`);
const { createConfidenceView } = await import('data:text/javascript;base64,' + Buffer.from(confidenceSource).toString('base64'));
const full = Object.freeze({ drawCalls: 7800, triangles: 3470000 });
const expectedGhost = { drawCalls: 8900, triangles: 3675000 };
let checks = 0;
function check(name, fn) { fn(); checks++; console.log('PASS ' + name); }
check('Full active Ghost uses independently measured draw and triangle pins', () => {
  assert.equal(Math.ceil(8469 * 1.05 / 100) * 100, 8900);
  assert.equal(Math.ceil((3656436 + 18059) / 5000) * 5000, 3675000);
  assert.deepEqual(renderBudget(full, 'full', true), expectedGhost);
});
check('the resolver does not mutate or drop other base policy fields', () => {
  const base = Object.freeze({ ...full, marker: 'preserve' });
  const selected = renderBudget(base, 'full', true);
  assert.deepEqual(base, { ...full, marker: 'preserve' });
  assert.deepEqual(selected, { ...expectedGhost, marker: 'preserve' });
  selected.drawCalls = 1;
  assert.equal(base.drawCalls, 7800);
});
check('Normal, Tint and inactive Ghost keep the original base object and limits', () => {
  for (const active of [false, undefined, null, 0, 'true']) assert.equal(renderBudget(full, 'full', active), full);
});
check('Balanced and Light preserve their exact ceilings with Ghost enabled', () => {
  for (const [detail, triangles] of [['balanced', 2625000], ['light', 1190000]]) {
    const base = Object.freeze({ drawCalls: 7800, triangles });
    assert.equal(renderBudget(base, detail, true), base);
    assert.deepEqual(base, { drawCalls: 7800, triangles });
  }
  const floor = Object.freeze({ drawCalls: 5900, triangles: 1190000 });
  assert.equal(renderBudget(floor, 'light', true), floor, 'an existing lower floor cannot be raised');
});
check('a higher inspection allowance is preserved in either dimension', () => {
  const inspection = Object.freeze({ drawCalls: 7800, triangles: 4600000 });
  assert.deepEqual(renderBudget(inspection, 'full', true), { drawCalls: 8900, triangles: 4600000 });
  const higher = Object.freeze({ drawCalls: 12000, triangles: 4600000 });
  assert.deepEqual(renderBudget(higher, 'full', true), higher);
  assert.equal(renderBudget(inspection, 'full', false), inspection);
});
check('actual confidence view enables the allowance only while Ghost is active', () => {
  const c = createConfidenceView();
  const selected = detail => renderBudget(full, detail, c.ghosting);
  assert.equal(selected('full'), full);
  c.setGrade('reconstructed', { mode: 'ghost', opacity: .4 });
  assert.equal(c.ghosting, false, 'a stored Ghost look with view off is inactive');
  assert.equal(selected('full'), full);
  c.set(true);
  assert.equal(c.ghosting, true); assert.deepEqual(selected('full'), expectedGhost);
  c.setHidden('reconstructed', true);
  assert.equal(c.ghosting, false); assert.equal(selected('full'), full);
  c.setHidden('reconstructed', false);
  assert.deepEqual(selected('full'), expectedGhost);
  c.set(false);
  assert.equal(selected('full'), full);
  c.set(true); c.setGrade('reconstructed', { mode: 'tint' });
  assert.equal(selected('full'), full);
});
check('multiple Ghost grades restore only when the last visible Ghost ends', () => {
  const c = createConfidenceView(); c.set(true);
  c.setGrade('inferred', { mode: 'ghost' }); c.setGrade('reconstructed', { mode: 'ghost' });
  assert.deepEqual(renderBudget(full, 'full', c.ghosting), expectedGhost);
  c.setHidden('inferred', true);
  assert.deepEqual(renderBudget(full, 'full', c.ghosting), expectedGhost);
  c.setHidden('reconstructed', true);
  assert.equal(renderBudget(full, 'full', c.ghosting), full);
  c.showAll(); assert.deepEqual(renderBudget(full, 'full', c.ghosting), expectedGhost);
  c.resetGrades(); assert.equal(renderBudget(full, 'full', c.ghosting), full);
});
check('detail transitions return to the original lower-tier and ordinary policies', () => {
  const c = createConfidenceView(); c.set(true); c.setGrade('inferred', { mode: 'ghost' });
  const balanced = Object.freeze({ drawCalls: 7800, triangles: 2625000 });
  assert.deepEqual(renderBudget(full, 'full', c.ghosting), expectedGhost);
  assert.equal(renderBudget(balanced, 'balanced', c.ghosting), balanced);
  assert.deepEqual(renderBudget(full, 'full', c.ghosting), expectedGhost);
  c.set(false); assert.equal(renderBudget(full, 'full', c.ghosting), full);
});
console.log(`render-budget: ${checks} policy/transition checks passed`);

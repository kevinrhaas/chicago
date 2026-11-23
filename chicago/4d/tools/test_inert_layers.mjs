#!/usr/bin/env node
/**
 * test_inert_layers.mjs — a layer the scene does not list is never downloaded (T-3732).
 *
 *     node tools/test_inert_layers.mjs
 *
 * main.js used to import nine layer modules statically that the 1835 first visit only ever
 * asked for an empty layer (docs/SITE-BUDGET.md § 4s): the 1904 street grid, parkway elms,
 * gas lamps, back and front yards, railway and context city, the crossings, and Glessner's
 * coach house. It now imports each only where the scene lists the layer (or, for the coach
 * house, where Glessner's record stands), and stands in the empty layer from inert-layers.js
 * elsewhere. This holds the three things that keeps true:
 *
 *   1. each factory, handed no data base, returns its inert-layers.js builder's object
 *      field for field (same keys, same values, a function where it had a function, an
 *      empty three Group of the same name), so the stand-in is the layer it replaces;
 *   2. main.js imports none of the nine statically, and its on-demand loader names each
 *      under the scene layer its call site asks `layerBase` for;
 *   3. the coach house's gate is its factory's own first test: no Glessner record, no house.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s, c, next) {
  if (s === 'three') return { url: '${vendor}three.module.js', shortCircuit: true };
  if (s.startsWith('three/addons/')) return { url: '${vendor}addons/' + s.slice(13), shortCircuit: true };
  return next(s, c);
}`)}`, import.meta.url);
const THREE = await import('three');
const JS = new URL('../renderers/web/js/', import.meta.url);
const inert = await import(new URL('inert-layers.js', JS).href);

/** A layer's shape: every own field, functions as 'fn', a Group as its type and name and children. */
function shape(value, path = '') {
  if (typeof value === 'function') return 'fn';
  if (value instanceof THREE.Group) return { group: value.name, children: value.children.length };
  if (Array.isArray(value)) return value.map((v, i) => shape(v, `${path}[${i}]`));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.keys(value).sort().map((k) => [k, shape(value[k], `${path}.${k}`)]));
  }
  return value;
}

// [module, factory, builder, the options main.js hands it with no data base, the scene layer]
const LAYERS = [
  ['street-grid.js', 'createStreetGrid', 'inertStreetGrid', {}, 'street_grid'],
  ['street-trees.js', 'createStreetTrees', 'inertStreetTrees', { mode: 'autumn', detail: 'light' }, 'street_trees'],
  ['street-furniture.js', 'createStreetFurniture', 'inertStreetFurniture', { detail: 'balanced' }, 'street_furniture'],
  ['back-yards.js', 'createBackYards', 'inertBackYards', { detail: 'light', season: 'winter' }, 'back_yards'],
  ['front-yards.js', 'createFrontYards', 'inertFrontYards', { detail: 'full', mode: 'spring' }, 'front_yards'],
  ['railway.js', 'createRailway', 'inertRailway', {}, 'railway'],
  ['context.js', 'createContext', 'inertContext', {}, 'context'],
  ['crossings.js', 'createCrossings', 'inertCrossings', {}, 'crossings'],
];

// 1. The stand-in is the layer it replaces, with defaults and with options alike.
const terrain = { heightAt: () => 0, inBounds: () => true, isWater: () => false };
for (const [file, factory, builder, opts] of LAYERS) {
  const mod = await import(new URL(file, JS).href);
  for (const given of [{}, opts]) {
    const real = await mod[factory]({ dataBase: null, terrain, sceneId: '1835', problems: [], ...given });
    const stand = inert[builder](given);
    assert.deepEqual(shape(stand), shape(real), `${builder}(${JSON.stringify(given)}) is ${file}'s empty layer`);
    assert.notEqual(stand.group, real.group, `${builder} builds a fresh group each call`);
  }
}
console.log(`ok - ${LAYERS.length} empty layers equal their factories' own, field for field`);

// 2. main.js imports none of them, or the coach house, until it needs them.
const main = fs.readFileSync(new URL('main.js', JS), 'utf8');
for (const [file] of [...LAYERS, ['coach-house.js']]) {
  const name = file.replace(/[.]/g, '\\.');
  assert.ok(!new RegExp(`^import [^;]*from '\\./${name}';`, 'm').test(main), `main.js imports ${file} statically`);
}
const loader = main.match(/const LAYER_MODULES = Object\.freeze\(\{([\s\S]*?)\}\);/);
assert.ok(loader, 'main.js has its LAYER_MODULES loader');
const entries = [...loader[1].matchAll(/(\w+): \(\) => import\('\.\/([\w-]+\.js)'\)/g)].map((m) => [m[1], m[2]]);
assert.deepEqual(entries.map(([, f]) => f).sort(), LAYERS.map(([f]) => f).sort(), 'LAYER_MODULES loads exactly these eight layers');
for (const [file, factory, , , layer] of LAYERS) {
  assert.ok(entries.some(([l, f]) => l === layer && f === file), `LAYER_MODULES loads ${file} for '${layer}'`);
  // Every call site asks layerBase for the same scene layer the loader is keyed by.
  const calls = [...main.matchAll(new RegExp(`await ${factory}\\(\\{\\s*dataBase: layerBase\\('(\\w+)'\\)`, 'g'))].map((m) => m[1]);
  assert.ok(calls.length >= 1, `main.js calls ${factory} with a layerBase`);
  assert.ok(calls.every((c) => c === layer), `${factory} is called for '${layer}', not ${calls.join(', ')}`);
}
console.log(`ok - main.js imports the ${LAYERS.length} layers and the coach house only on demand, each under its own layer`);

// 3. No Glessner record, no coach house: the gate main.js asks first is the factory's own.
const { createCoachHouse } = await import(new URL('coach-house.js', JS).href);
const empty = new Map();
assert.equal(createCoachHouse({ registry: empty }), null, 'createCoachHouse without glessner_house is null');
assert.equal(createCoachHouse({ registry: new Map([['glessner_house', { id: 'glessner_house' }]]) }), null,
  'createCoachHouse without a sidecar is null');
assert.ok(/if \(loaded\.registry\?\.get\?\.\('glessner_house'\)\?\.sidecar\) try \{\s*const \{ createCoachHouse \} = await import\('\.\/coach-house\.js'\);/.test(main),
  "main.js imports coach-house.js only where glessner_house has a sidecar");
console.log('ok - the coach house loads only where Glessner\'s record stands');

#!/usr/bin/env node
/**
 * T-2446, T-2469 — Glessner's granite is retinted to grey-greige, and nothing else is.
 *
 * The owner chose grey-greige from T-2446's comparison. The bake cannot carry it (the glTF
 * exporter clamps a colour factor to 1), so the renderer multiplies it in at load. This
 * holds that to its terms: the baked tint it divides by is the one the generator writes
 * (GRANITE_TINT), only glessner_house's five granite slots are touched, each once (a clone
 * of a retinted slot is not retinted again), and each lands on grey-greige times its own
 * variant offset.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(threeURL);
const source = await readFile(path.join(web, 'js/glessner-stone.js'), 'utf8');
const { tintGlessnerGranite, GLESSNER_STONE, GLESSNER_STONE_BAKED } = await import(
  `data:text/javascript;base64,${Buffer.from(source.replace("from 'three'", `from '${threeURL}'`)).toString('base64')}`);

const checks = [];
function check(name, run) { run(); checks.push(name); }
const glessner = { id: 'glessner_house' };
const slot = (name, rgb) => new THREE.MeshStandardMaterial({ name, color: new THREE.Color(...rgb) });
const near = (a, b) => Math.abs(a - b) < 1e-6;

{
  const py = await readFile(path.join(root, 'generators/archetypes/masonry_house_v4_materials.py'), 'utf8');
  const m = py.match(/^GRANITE_TINT = \(([^)]*)\)/m);
  assert.ok(m, 'GRANITE_TINT not found in masonry_house_v4_materials.py');
  assert.deepEqual(m[1].split(',').map(Number), [...GLESSNER_STONE_BAKED],
    'GRANITE_TINT changed: set GLESSNER_STONE_BAKED to the new bake and re-check grey-greige');
  checks.push("the baked tint is the generator's GRANITE_TINT");
}
check('the main slot lands on grey-greige', () => {
  const m = slot('granite', GLESSNER_STONE_BAKED);
  tintGlessnerGranite(m, glessner);
  assert.ok(near(m.color.r, GLESSNER_STONE[0]) && near(m.color.g, GLESSNER_STONE[1]) && near(m.color.b, GLESSNER_STONE[2]));
});
check("each granite slot is retinted once, by grey-greige / baked", () => {
  const lift = GLESSNER_STONE.map((v, i) => v / GLESSNER_STONE_BAKED[i]);
  for (const name of ['granite', 'granite_1', 'granite_2', 'granite_3', 'granite_4']) {
    const m = slot(name, [0.8, 0.8, 0.8]);
    tintGlessnerGranite(m, glessner);
    const want = lift.map((k) => 0.8 * k);
    assert.ok(near(m.color.r, want[0]) && near(m.color.g, want[1]) && near(m.color.b, want[2]), name);
    tintGlessnerGranite(m, glessner);
    const copy = m.clone();
    tintGlessnerGranite(copy, glessner);
    assert.ok(near(m.color.r, want[0]) && near(copy.color.r, want[0]), `${name} was retinted twice`);
  }
});
check('nothing else is retinted', () => {
  for (const [name, record] of [['limestone_trim', glessner], ['rough_stone_trim', glessner], ['granite_5', glessner],
    ['brick', glessner], ['granite', { id: 'kimball_house' }], ['granite', null]]) {
    const m = slot(name, [0.8, 0.8, 0.8]);
    tintGlessnerGranite(m, record);
    assert.equal(m.color.r, 0.8, `${name} on ${record?.id} was retinted`);
  }
});
console.log(`glessner stone PASS: ${checks.length} checks — ${checks.join('; ')}`);

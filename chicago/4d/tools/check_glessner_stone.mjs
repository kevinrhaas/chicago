#!/usr/bin/env node
/**
 * T-2446 — `?stone=` retints Glessner's granite, and only Glessner's granite.
 *
 * The owner asked to compare a few stone colours before a default is baked. This holds the
 * option to its terms: the baked tint it divides by is the one the generator writes
 * (GRANITE_TINT), a known name or a linear `r,g,b` is read and anything else falls back to
 * the default, only glessner_house's five granite slots are touched, each once, and
 * `?stone=baked` leaves the package's colour exactly as it is.
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
const { readGlessnerStone, tintGlessnerGranite, GLESSNER_STONES, GLESSNER_STONE_BAKED, GLESSNER_STONE_DEFAULT } = await import(
  `data:text/javascript;base64,${Buffer.from(source.replace("from 'three'", `from '${threeURL}'`)).toString('base64')}`);

const checks = [];
function check(name, run) { run(); checks.push(name); }
const glessner = { id: 'glessner_house' };
const slot = (name, rgb) => new THREE.MeshStandardMaterial({ name, color: new THREE.Color(...rgb) });

{
  const py = await readFile(path.join(root, 'generators/archetypes/masonry_house_v4_materials.py'), 'utf8');
  const m = py.match(/^GRANITE_TINT = \(([^)]*)\)/m);
  assert.ok(m, 'GRANITE_TINT not found in masonry_house_v4_materials.py');
  assert.deepEqual(m[1].split(',').map(Number), [...GLESSNER_STONE_BAKED],
    'GRANITE_TINT changed: set GLESSNER_STONE_BAKED (and the presets) to the new bake');
  checks.push("the baked tint is the generator's GRANITE_TINT");
}
check('a known name is read, an unknown one falls back to the default', () => {
  assert.ok(Object.hasOwn(GLESSNER_STONES, GLESSNER_STONE_DEFAULT));
  assert.equal(GLESSNER_STONES.baked, GLESSNER_STONE_BAKED);
  for (const name of Object.keys(GLESSNER_STONES)) {
    assert.deepEqual(readGlessnerStone(`?stone=${name}`), { name, tint: GLESSNER_STONES[name] });
  }
  assert.equal(readGlessnerStone('?stone=Greige').name, 'greige');
  for (const q of ['', '?stone=', '?stone=pink', '?stone=1,2', '?stone=0,1,1', '?stone=a,b,c', '?stone=2,1,1', '?stone=toString']) {
    assert.equal(readGlessnerStone(q).name, GLESSNER_STONE_DEFAULT, q);
  }
  assert.deepEqual([...readGlessnerStone('?stone=0.9,0.97,1').tint], [0.9, 0.97, 1]);
});
check('only glessner_house\'s granite slots are retinted, each by preset / baked, once', () => {
  const stone = readGlessnerStone('?stone=0.5,0.97,0.94');
  for (const name of ['granite', 'granite_1', 'granite_2', 'granite_3', 'granite_4']) {
    const m = slot(name, [0.8, 0.8, 0.8]);
    tintGlessnerGranite(m, glessner, stone);
    assert.ok(Math.abs(m.color.r - 0.4) < 1e-6 && Math.abs(m.color.g - 0.8) < 1e-6 && Math.abs(m.color.b - 0.8) < 1e-6, name);
    tintGlessnerGranite(m, glessner, stone);
    assert.ok(Math.abs(m.color.r - 0.4) < 1e-6, `${name} was retinted twice`);
    assert.ok(Math.abs(m.clone().color.r - 0.4) < 1e-6 && m.clone().userData.glessnerStone === stone.name);
  }
  for (const [name, record] of [['limestone_trim', glessner], ['rough_stone_trim', glessner], ['granite_5', glessner],
    ['brick', glessner], ['granite', { id: 'kimball_house' }], ['granite', null]]) {
    const m = slot(name, [0.8, 0.8, 0.8]);
    tintGlessnerGranite(m, record, stone);
    assert.equal(m.color.r, 0.8, `${name} on ${record?.id} was retinted`);
  }
});
check('?stone=baked leaves the package colour exactly', () => {
  const m = slot('granite', GLESSNER_STONE_BAKED);
  const before = m.color.getHex();
  tintGlessnerGranite(m, glessner, readGlessnerStone('?stone=baked'));
  assert.equal(m.color.getHex(), before);
});
console.log(`glessner stone PASS: ${checks.length} checks — ${checks.join('; ')}`);

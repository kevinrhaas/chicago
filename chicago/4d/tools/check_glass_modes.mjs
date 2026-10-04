#!/usr/bin/env node
/**
 * T-2109 — the cheaper glass replaces exactly what it should, and nothing else.
 *
 * 1904's Glessner glass carries KHR_materials_transmission, which makes three
 * draw every opaque object a second time; glass.js swaps it at load for a
 * `clear` or `dark` pane when `?glass=` asks. This holds the swap to its terms:
 * only a transmissive material is touched, the default keeps the GLB's own
 * glass, the input is never mutated, and the replacement carries no
 * transmission (so three's transmission pass cannot run for it).
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(threeURL);
const source = await readFile(path.join(web, 'js/glass.js'), 'utf8');
const { cheapenGlass, readGlassMode, GLASS_MODES, DEFAULT_GLASS } = await import(
  `data:text/javascript;base64,${Buffer.from(source.replace("from 'three'", `from '${threeURL}'`)).toString('base64')}`);

const checks = [];
function check(name, run) { run(); checks.push(name); }
// The Glessner GLB's own glass, as GLTFLoader builds it.
const gltfGlass = () => new THREE.MeshPhysicalMaterial({ name: 'glass', color: new THREE.Color(0.945, 0.97, 0.953),
  roughness: 0.065, metalness: 0, transmission: 1, ior: 1.52, side: THREE.DoubleSide });

check('the default keeps the GLB glass, untouched', () => {
  assert.equal(DEFAULT_GLASS, 'transmission');
  const g = gltfGlass();
  assert.equal(cheapenGlass(g), g);
  assert.equal(cheapenGlass(g, 'transmission'), g);
});
check('?glass= reads only a known mode', () => {
  assert.deepEqual([...GLASS_MODES], ['transmission', 'clear', 'dark']);
  for (const m of GLASS_MODES) assert.equal(readGlassMode(new URLSearchParams(`glass=${m}`)), m);
  for (const q of ['', 'glass=', 'glass=CLEAR', 'glass=frosted']) assert.equal(readGlassMode(new URLSearchParams(q)), DEFAULT_GLASS);
  assert.equal(readGlassMode(null), DEFAULT_GLASS);
});
check('an opaque or untransmissive material is never swapped', () => {
  for (const m of ['clear', 'dark']) {
    const stone = new THREE.MeshStandardMaterial({ color: 0x887766 });
    assert.equal(cheapenGlass(stone, m), stone);
    const phys = new THREE.MeshPhysicalMaterial({ transmission: 0 });
    assert.equal(cheapenGlass(phys, m), phys);
  }
});
for (const mode of ['clear', 'dark']) {
  check(`${mode}: a fresh standard material with no transmission, input untouched`, () => {
    const g = gltfGlass();
    const before = JSON.stringify(g.toJSON());
    const c = cheapenGlass(g, mode);
    assert.notEqual(c, g);
    assert.equal(JSON.stringify(g.toJSON()), before, 'the source material was mutated');
    assert.equal(c.type, 'MeshStandardMaterial');
    assert.ok(!(c.transmission > 0), 'the replacement still transmits');
    assert.equal(c.side, g.side);
    assert.equal(c.roughness, g.roughness);
    assert.equal(c.name, g.name);
    assert.equal(c.userData.glassMode, mode);
    assert.equal(c.transparent, mode === 'clear');
    assert.ok(c.color.r < g.color.r, 'the pane is no brighter than the GLB tint');
    if (mode === 'clear') { assert.ok(c.opacity > 0 && c.opacity < 1); assert.equal(c.depthWrite, false); }
    else assert.equal(c.opacity, 1);
  });
}
console.log(`glass modes PASS: ${checks.length} checks — ${checks.join('; ')}`);

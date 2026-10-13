#!/usr/bin/env node
/**
 * T-2109 — the cheaper glass replaces exactly what it should, and nothing else.
 *
 * 1904's Glessner glass carries KHR_materials_transmission, which makes three
 * draw every opaque object a second time; glass.js swaps it at load for a
 * `clear` or `dark` pane. This holds the swap to its terms: only a
 * transmissive material is touched, a caller naming no mode keeps the GLB's
 * own glass, the input is never mutated, and the replacement carries no
 * transmission (so three's transmission pass cannot run for it). And it holds
 * the owner's updated pick (T-2183): dark at full, balanced and light, with
 * `?glass=` overriding the choice at every setting.
 *
 * T-2213: the dark pane reads its panes and windows (`paneLayout`) so no two
 * panes catch the same reflection and each window carries its own blind. This
 * holds the layout to a built window: a double-hung pair is one window whose
 * blind can stop at its meeting rail, a door's grid of small lights and a cellar
 * light carry none, every pane has its own seed, and the same pane gets the same
 * seed wherever it is read.
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
const { cheapenGlass, readGlassRequest, glassForDetail, GLASS_MODES, GLASS_BY_DETAIL, DEFAULT_GLASS,
  paneLayout, writePaneAttributes, BLIND_DROPS, PANE_PATCH } = await import(
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
  for (const m of GLASS_MODES) assert.equal(readGlassRequest(new URLSearchParams(`glass=${m}`)), m);
  for (const q of ['', 'glass=', 'glass=CLEAR', 'glass=frosted']) assert.equal(readGlassRequest(new URLSearchParams(q)), null);
  assert.equal(readGlassRequest(null), null);
});
check("the owner's pick: dark at every scene detail setting", () => {
  assert.deepEqual({ ...GLASS_BY_DETAIL }, { full: 'dark', balanced: 'dark', light: 'dark' });
  assert.equal(glassForDetail('full'), 'dark');
  assert.equal(glassForDetail('balanced'), 'dark');
  assert.equal(glassForDetail('light'), 'dark');
  // An unknown setting keeps the GLB's glass rather than guessing.
  for (const d of [undefined, null, '', 'ultra', 'toString']) assert.equal(glassForDetail(d), DEFAULT_GLASS);
});
check('?glass= overrides the pick at every setting', () => {
  for (const d of ['full', 'balanced', 'light']) {
    for (const m of GLASS_MODES) assert.equal(glassForDetail(d, m), m);
    assert.equal(glassForDetail(d, 'frosted'), GLASS_BY_DETAIL[d]);
  }
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
check('only the dark pane is pane-patched, under its own batch key and program', () => {
  const dark = cheapenGlass(gltfGlass(), 'dark');
  assert.equal(dark.userData.glassPanes, PANE_PATCH);
  assert.equal(dark.customProgramCacheKey(), PANE_PATCH);
  const shader = { vertexShader: '#include <begin_vertex>', fragmentShader: '#include <color_fragment>\n#include <normal_fragment_maps>' };
  dark.onBeforeCompile(shader);
  assert.match(shader.vertexShader, /attribute vec4 _pane;[\s\S]*vChiPaneWin = _paneWin;/);
  assert.ok(shader.fragmentShader.indexOf('chiLift') < shader.fragmentShader.indexOf('#include <color_fragment>'),
    'the pane albedo must land before <color_fragment>, so tone and confidence still apply over it');
  assert.ok(shader.fragmentShader.indexOf('roughnessFactor =') > shader.fragmentShader.indexOf('#include <normal_fragment_maps>'));
  assert.equal(cheapenGlass(gltfGlass(), 'clear').userData.glassPanes, undefined);
});

// A pane as the GLB builds one: a 12-triangle slab, 2 cm thick, in the x-y plane.
function slab(x0, y0, w, h, z = 0, t = 0.02) {
  const c = [];
  for (const [x, y, zz] of [[0,0,0],[w,0,0],[w,h,0],[0,h,0],[0,0,t],[w,0,t],[w,h,t],[0,h,t]]) c.push(x0 + x, y0 + y, z + zz);
  const f = [0,1,2, 0,2,3, 4,6,5, 4,7,6, 0,4,5, 0,5,1, 1,5,6, 1,6,2, 2,6,7, 2,7,3, 3,7,4, 3,4,0];
  return { c, f };
}
function mesh(slabs) {
  const pos = [], idx = [];
  for (const s of slabs) { const base = pos.length / 3; pos.push(...s.c); idx.push(...s.f.map((i) => i + base)); }
  return { pos: Float32Array.from(pos), idx: Uint32Array.from(idx) };
}
// Eight double-hung windows (lower light 1.2 m, rail 6 cm, upper 1.2 m), a door's
// three-by-two grid of 0.15 m lights, and one cellar light.
const sashes = [];
for (let k = 0; k < 8; k += 1) sashes.push(slab(k * 1.6, 1, 0.9, 1.2), slab(k * 1.6, 2.26, 0.9, 1.2));
const door = [];
for (let i = 0; i < 3; i += 1) for (let j = 0; j < 2; j += 1) door.push(slab(14 + i * 0.2, 1.5 + j * 0.2, 0.15, 0.15));
const cellar = [slab(16, 0.1, 0.9, 0.4)];
const town = mesh([...sashes, ...door, ...cellar]);
const layout = paneLayout(town.pos, town.idx);
check('a double-hung pair is one window; door lights and a cellar light carry no blind', () => {
  assert.equal(layout.panes.length, 16 + 6 + 1);
  const sashWindows = layout.windows.filter((w) => w.panes[0].width > 0.5 && w.height > 1);
  assert.equal(sashWindows.length, 8);
  for (const w of sashWindows) {
    assert.ok(Math.abs(w.height - 2.46) < 1e-4, `window height ${w.height}`);
    assert.ok(w.blind >= 0 && w.blind < 0.9);
  }
  // The door's lights are columns of narrow panes, the cellar light is short.
  for (const w of layout.windows.filter((w) => !sashWindows.includes(w))) assert.equal(w.blind, 0);
  // A blind dealt to the meeting rail stops on it: its edge hides behind the rail.
  for (const w of sashWindows.filter((w) => w.blind > 0.45 && w.blind < 0.55)) {
    assert.ok(Math.abs(w.blind - ((3.46 - 2.2) / 2.46 + 0.01)) < 1e-4, `rail drop ${w.blind}`);
  }
});
check('every pane its own seed, the same pane the same seed, and u/v spanning each pane', () => {
  const seeds = new Set(layout.panes.map((p) => p.seed.toFixed(6)));
  assert.equal(seeds.size, layout.panes.length, 'two panes share a seed, so they would draw alike');
  const again = paneLayout(mesh([...cellar, ...door, ...sashes]).pos, mesh([...cellar, ...door, ...sashes]).idx);
  const bySeat = (l) => new Map(l.panes.map((p) => [`${p.cx.toFixed(3)},${p.yMin.toFixed(3)}`, p.seed]));
  assert.deepEqual(bySeat(again), bySeat(layout), 'a pane read in another order drew a different seed');
  for (let i = 0; i < layout.pane.length; i += 4) {
    assert.ok(layout.pane[i] >= -1e-6 && layout.pane[i] <= 1 + 1e-6 && layout.pane[i + 1] >= -1e-6 && layout.pane[i + 1] <= 1 + 1e-6);
  }
  assert.ok(new Set(BLIND_DROPS.filter((d) => d !== 0)).size >= 3, 'blinds need several drops, not one');
  assert.ok(BLIND_DROPS.filter((d) => d === 0).length >= 2, 'some blinds are up');
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(town.pos, 3));
  geo.setIndex(new THREE.BufferAttribute(town.idx, 1));
  writePaneAttributes(geo, THREE);
  assert.equal(geo.getAttribute('_pane').itemSize, 4);
  assert.equal(geo.getAttribute('_paneWin').count, town.pos.length / 3);
  assert.ok([...geo.getAttribute('_paneWin').array].every(Number.isFinite));
});
console.log(`glass modes PASS: ${checks.length} checks — ${checks.join('; ')}`);

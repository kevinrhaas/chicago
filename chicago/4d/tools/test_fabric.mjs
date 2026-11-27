// SPDX-License-Identifier: GPL-3.0-or-later
// T-2804: the cloth patch for portable humans' plain garments (renderers/web/js/fabric.js).
// It must: clothe exactly the garments of the real driver exports (never skin, hair,
// eyes or shoes); add no texture; splice into three's own standard shader at
// every anchor it names; chain beneath and above another hook (confidence.js)
// with a program key that names the chain; and share one program across cloths.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
const THREE = await import(threeURL);
const data = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const source = (await fs.readFile(new URL('renderers/web/js/fabric.js', here), 'utf8')).replace("from 'three'", `from '${threeURL}'`);
const { clothFor, patchFabric, clothHuman, CLOTHS, HATS, hatBand, HAT_BAND } = await import(data(source));

const materialNames = async asset => {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.glb`, here));
  const n = bytes.readUInt32LE(12);
  return JSON.parse(bytes.subarray(20, 20 + n)).materials.map(m => m.name);
};

for (const asset of ['anonymous_working_driver_1904.lod0', 'anonymous_working_driver_1904.lod3', 'bardwell_otis_1835.lod0']) {
  const names = await materialNames(asset);
  const root = new THREE.Group();
  for (const name of names) root.add(new THREE.Mesh(new THREE.BufferGeometry(), Object.assign(new THREE.MeshStandardMaterial(), { name })));
  const clothed = clothHuman(root).sort();
  assert.deepEqual(clothed, names.filter(n => n.startsWith('garment_') || (n.startsWith('headwear__') && clothFor({ name: n }))).sort(), `${asset}: exactly the garments and hats are clothed`);
  assert(clothed.length >= 3, `${asset}: shirt, waistcoat and trousers`);
  root.traverse(o => { if (o.isMesh) assert.equal(o.material.map ?? null, null, 'no texture added'); });
  console.log(`${asset}: clothed ${clothed.join(', ')}`);
}
assert.equal(clothFor({ name: 'garment_outer__waistcoat_wool' }), CLOTHS.wool);
assert.equal(clothFor({ name: 'garment_upper__shirt_linen' }), CLOTHS.linen);
assert.equal(clothFor({ name: 'garment_lower__highwaist_pantaloons' }), CLOTHS.cotton_twill);
for (const name of ['skin', 'hair__makehuman_short04', 'footwear__closed_leather_shoes', 'eyes__iris', '', 'headwear__plume_white_1812', 'accessory__picture_hat_trim_t3553']) assert.equal(clothFor({ name }), null, name);
// T-3553 round 8: hats have their own surfaces (felt, silk plush, straw, a grosgrain band; caps of linen, a knitted tuque of wool).
for (const [name, cloth] of [['headwear__derby_felt', HATS.felt], ['headwear__lady_hat_black', HATS.felt], ['headwear__round_hat_t3522', HATS.felt],
  ['headwear__silk_top_hat_1904', HATS.plush], ['headwear__top_hat_black', HATS.plush], ['headwear__toque_hat_t3522', HATS.plush],
  ['headwear__errand_boater_straw', HATS.straw], ['headwear__sailor_hat_t3522', HATS.straw], ['headwear__errand_boater_ribbon', HATS.ribbon],
  ['headwear__round_hat_band_t3522', HATS.ribbon], ['headwear__maid_cap_white', CLOTHS.linen], ['headwear__tuque_red_1812', CLOTHS.wool]]) assert.equal(clothFor({ name }), cloth, name);
assert.equal(clothFor({ name: 'headwear__picture_hat_t3522', userData: { chiHat: 'straw' } }), HATS.straw, 'a summer picture hat is straw');
assert(HATS.felt.weave === 0 && HATS.felt.rough >= 0.8, 'felt has no weave and no gloss');
{ const felt = Object.assign(new THREE.MeshStandardMaterial({ roughness: 0.7 }), { name: 'headwear__derby_felt' });
  assert.equal(patchFabric(felt), HATS.felt); assert(felt.roughness >= HATS.felt.rough, 'a felt hat is drawn matte'); }
// A derby modelled without a band gets one round the foot of its crown: a lathe of brim and crown.
{ const prof = [[0.16, 0.012], [0.14, 0.004], [0.1, 0.0], [0.092, 0.02], [0.092, 0.06], [0.088, 0.1], [0.06, 0.118], [0.0, 0.122]].map(([r, y]) => new THREE.Vector2(r, y));
  const g = new THREE.LatheGeometry(prof, 24); g.computeVertexNormals();
  const root = new THREE.Group(), hat = new THREE.Mesh(g, Object.assign(new THREE.MeshStandardMaterial(), { name: 'headwear__derby_felt' })); root.add(hat); root.updateMatrixWorld(true);
  const band = hatBand(hat);
  assert(band && band.foot > 0 && band.foot < 0.025 && Math.abs(band.half * 2 - HAT_BAND.width) < 1e-9, `the band at the crown's foot (${JSON.stringify(band)})`);
  assert.equal(hat.material.userData.chiFinery.bands[0][2], 1, 'drawn as a ribbon');
  const own = new THREE.Mesh(g.clone(), Object.assign(new THREE.MeshStandardMaterial(), { name: 'headwear__round_hat_t3522' })), ribbon = new THREE.Mesh(g.clone(), Object.assign(new THREE.MeshStandardMaterial(), { name: 'headwear__round_hat_band_t3522' }));
  const r2 = new THREE.Group(); r2.add(own, ribbon); r2.updateMatrixWorld(true);
  assert.equal(hatBand(own), null, 'a hat with its own band gets none');
  assert.equal(hatBand(Object.assign(new THREE.Mesh(g.clone(), Object.assign(new THREE.MeshStandardMaterial(), { name: 'headwear__maid_cap_white' })))), null, 'a cap gets none'); }
assert.equal(patchFabric(Object.assign(new THREE.MeshBasicMaterial(), { name: 'garment_upper__shirt_linen' })), null, 'an unlit material is left alone');

// Splices into three's own standard shader, after a prior hook, and is idempotent.
const compile = material => {
  const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader, fragmentShader: THREE.ShaderLib.standard.fragmentShader };
  material.onBeforeCompile(shader, null);
  return shader;
};
const wool = Object.assign(new THREE.MeshStandardMaterial(), { name: 'garment_outer__waistcoat_wool' });
let priorRan = 0;
wool.onBeforeCompile = shader => { priorRan++; shader.fragmentShader = '// prior\n' + shader.fragmentShader; };
wool.customProgramCacheKey = () => 'chicago4d-confidence';
assert.equal(patchFabric(wool), CLOTHS.wool);
assert.equal(patchFabric(wool), CLOTHS.wool, 'a second patch is a no-op');
const shader = compile(wool);
assert.equal(priorRan, 1, 'the prior hook runs once, first');
assert(shader.fragmentShader.includes('// prior'));
for (const marker of ['chiFabricPerturb( - vViewPosition', 'roughnessFactor = clamp( roughnessFactor - chiFabricGloss', 'chiFin.w ) - chiFinGloss',
  'reflectedLight.indirectDiffuse += ( diffuseColor.rgb * 2.0 + 0.035 ) * chiShe', 'float chiFabricH = 0.0', 'float chiFinGloss = 0.0']) {
  assert.equal(shader.fragmentShader.split(marker).length, 2, `spliced once: ${marker}`);
}
assert(shader.vertexShader.includes('vChiFabricP = position;'));
assert.deepEqual(Object.keys(shader.uniforms).sort(), ['chiFabric', 'chiFabricWear', 'chiFin', 'chiFinBand', 'chiFinBandRgb', 'chiFinPat', 'chiFinPatRgb']);
// T-3553: a plain cloth's finery is all zeros (drawn exactly as before).
assert(shader.uniforms.chiFin.value.toArray().every(v => v === 0) && shader.uniforms.chiFinPat.value.x === 0, 'no finery by default');
assert.equal(wool.customProgramCacheKey(), 'chicago4d-confidence|chicago-fabric-v2', 'the key names the chain');

// A hook chained above (as confidence.js chains) still sees the anchors it needs.
for (const anchor of ['#include <begin_vertex>']) assert(shader.vertexShader.includes(anchor));
for (const anchor of ['#include <color_fragment>', '#include <clipping_planes_fragment>', '#include <opaque_fragment>']) assert(shader.fragmentShader.includes(anchor), anchor);

// Cloths differ by uniforms, never code: one program for all three.
const texts = Object.keys(CLOTHS).map(k => {
  const m = Object.assign(new THREE.MeshStandardMaterial(), { name: { wool: 'garment_outer__waistcoat_wool', cotton_twill: 'garment_lower__trousers', linen: 'garment_upper__shirt_linen' }[k] });
  patchFabric(m); const s = compile(m); return [s.vertexShader + s.fragmentShader, m.customProgramCacheKey(), s.uniforms.chiFabric.value.toArray().join()];
});
assert.equal(new Set(texts.map(t => t[0])).size, 1, 'one program text');
assert.equal(new Set(texts.map(t => t[1])).size, 1, 'one program key');
assert.equal(new Set(texts.map(t => t[2])).size, 3, 'three cloths by uniform');
{ const felt = Object.assign(new THREE.MeshStandardMaterial(), { name: 'headwear__derby_felt' }); patchFabric(felt); const s = compile(felt);
  assert.equal(s.vertexShader + s.fragmentShader, texts[0][0], 'a hat in the same program'); }
console.log('fabric: garments and hats only, no texture, spliced at every anchor, chained key, one program for all cloths: PASS');

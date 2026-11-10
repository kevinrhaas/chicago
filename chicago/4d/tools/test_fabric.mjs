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
const { clothFor, patchFabric, clothHuman, CLOTHS } = await import(data(source));

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
  assert.deepEqual(clothed, names.filter(n => n.startsWith('garment_')).sort(), `${asset}: exactly the garments are clothed`);
  assert(clothed.length >= 3, `${asset}: shirt, waistcoat and trousers`);
  root.traverse(o => { if (o.isMesh) assert.equal(o.material.map ?? null, null, 'no texture added'); });
  console.log(`${asset}: clothed ${clothed.join(', ')}`);
}
assert.equal(clothFor({ name: 'garment_outer__waistcoat_wool' }), CLOTHS.wool);
assert.equal(clothFor({ name: 'garment_upper__shirt_linen' }), CLOTHS.linen);
assert.equal(clothFor({ name: 'garment_lower__highwaist_pantaloons' }), CLOTHS.cotton_twill);
for (const name of ['skin', 'hair__makehuman_short04', 'footwear__closed_leather_shoes', 'eyes__iris', '']) assert.equal(clothFor({ name }), null, name);
assert.equal(patchFabric(Object.assign(new THREE.MeshBasicMaterial(), { name: 'garment_upper__shirt_linen' })), null, 'an unlit material is left alone');


// Portable near material extras survive real Three material cloning. Their PBR
// normal/roughness owns the weave; no additive shader relief is installed.
const portable = Object.assign(new THREE.MeshStandardMaterial(), { name: 'garment_outer__round_jacket__woven_near',
  normalMap: new THREE.Texture(), roughnessMap: new THREE.Texture() });
portable.userData.chicago4d_cloth_microtexture = { version: 1, runtime_weave: 'portable_maps_replace_common_fabric' };
const clonedPortable = portable.clone(), portablePrior = clonedPortable.onBeforeCompile;
assert.equal(patchFabric(clonedPortable), null, 'marked portable maps avoid double fabric weave');
assert.equal(clonedPortable.onBeforeCompile, portablePrior, 'portable shader hook unchanged');
assert.equal(clonedPortable.normalMap, portable.normalMap, 'normal texture remains shared through clone');
const missingNormal = portable.clone(); missingNormal.normalMap = null;
assert.equal(patchFabric(missingNormal), CLOTHS.wool, 'incomplete map binding cannot claim portable relief');
const unmarkedMaps = portable.clone(); unmarkedMaps.userData = {};
assert.equal(patchFabric(unmarkedMaps), CLOTHS.wool, 'unmarked old material keeps common cloth shader');
portable.normalMap.dispose(); portable.roughnessMap.dispose();
portable.dispose(); clonedPortable.dispose(); missingNormal.dispose(); unmarkedMaps.dispose();

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
for (const marker of ['chiFabricPerturb( - vViewPosition', 'roughnessFactor = clamp( roughnessFactor - chiFabricGloss',
  'reflectedLight.indirectDiffuse += diffuseColor.rgb * chiFabricWear.x', 'float chiFabricH = 0.0']) {
  assert.equal(shader.fragmentShader.split(marker).length, 2, `spliced once: ${marker}`);
}
assert(shader.vertexShader.includes('vChiFabricP = position;'));
assert.deepEqual(Object.keys(shader.uniforms).sort(), ['chiFabric', 'chiFabricWear']);
assert.equal(wool.customProgramCacheKey(), 'chicago4d-confidence|chicago-fabric-v1', 'the key names the chain');

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
console.log('fabric: garments only, no texture, spliced at every anchor, chained key, one program for all cloths: PASS');

// SPDX-License-Identifier: GPL-3.0-or-later
// T-3400: skin, hair and eyes for every portable human (renderers/web/js/human-skin.js).
// It must: dress exactly the skin, hair and eyes of every real export (never a garment
// or a shoe); add no texture; splice into three's own standard shader at every anchor it
// names, light wrapper included; chain beneath another hook (confidence.js) with a program
// key that names the chain; share one skin and one hair program across bodies; read each
// body's bind pose in metres however it was quantised; and be wired into humans.js's build.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
// human-skin.js imports its sibling human-hair-styles.js (T-3493), so it is loaded from its own
// file with 'three' resolved to the vendored copy, not from a data: URL.
registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const { surfaceFor, dressSkin, restMatrix, SKIN, EYES, AGE, restingLid } = await import(new URL('renderers/web/js/human-skin.js', here));

const materialNames = async asset => {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.glb`, here));
  const n = bytes.readUInt32LE(12);
  return JSON.parse(bytes.subarray(20, 20 + n)).materials.map(m => m.name);
};
const exports = (await fs.readdir(new URL('assets/humans/web/', here))).filter(f => f.endsWith('.glb')).map(f => f.slice(0, -4));
assert(exports.some(a => a.startsWith('anonymous_working_driver_1904')) && exports.some(a => a.startsWith('bardwell_otis_1835')), 'Hans and Otis are exported');
for (const asset of exports) {
  const names = await materialNames(asset);
  const root = new THREE.Group();
  for (const name of names) root.add(new THREE.Mesh(new THREE.BufferGeometry(), Object.assign(new THREE.MeshStandardMaterial(), { name })));
  const dressed = dressSkin(root);
  const want = names.filter(n => /^(skin|hair|eyes)($|__)/.test(n)).sort();   // the pupil too, under its cornea (T-3414)
  assert.deepEqual(Object.keys(dressed).sort(), want, `${asset}: exactly its skin, hair and eyes`);
  assert(Object.values(dressed).includes('skin'), `${asset}: has skin`);
  root.traverse(o => { if (o.isMesh && !/^(skin|hair|eyes)/.test(o.material.name)) assert.equal(o.material.onBeforeCompile, THREE.Material.prototype.onBeforeCompile, `${o.material.name} untouched`); });
  console.log(`${asset}: ${Object.entries(dressed).map(([k, v]) => `${k}=${v}`).join(', ')}`);
}
for (const [name, surface] of [['skin', 'skin'], ['skin__dark', 'skin'], ['hair__makehuman_short04', 'hair'], ['eyes', 'eyes'], ['eyes__sclera', 'eyes'], ['eyes__iris', 'eyes'],
  ['eyes__pupil', 'eyes'], ['eyes__lash', null], ['garment_upper__shirt_linen', null], ['footwear__closed_leather_shoes', null], ['skinny_tie', null], ['', null]]) assert.equal(surfaceFor({ name }), surface, name);
assert.deepEqual(dressSkin(new THREE.Mesh(new THREE.BufferGeometry(), Object.assign(new THREE.MeshBasicMaterial(), { name: 'skin' }))), {}, 'an unlit material is left alone');

// Eyes: wet, the sclera less paper-white, once however often a body is dressed.
const sclera = Object.assign(new THREE.MeshStandardMaterial({ color: 0xd0c8b8, roughness: .38 }), { name: 'eyes__sclera' });
const eyeRoot = new THREE.Mesh(new THREE.BufferGeometry(), sclera);
const before = sclera.color.r;
dressSkin(eyeRoot); dressSkin(eyeRoot);
assert.equal(sclera.roughness, EYES.roughness);
assert.equal(sclera.customProgramCacheKey(), '|chicago-sclera-v1', 'the white is shaded toward its corners');
assert(Math.abs(sclera.color.r - before * EYES.sclera_value) < 1e-9, 'the sclera is toned once');

// The bind pose in metres: a quantised export folds its scale into the inverse bind matrices.
{
  const bone = new THREE.Bone(); bone.position.set(0, .9, 0);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute([0, -1, 0, 0, 1, 0, .1, 1, 0], 3));
  geo.setAttribute('skinIndex', new THREE.Uint16BufferAttribute([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 4));
  geo.setAttribute('skinWeight', new THREE.Float32BufferAttribute([1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0], 4));
  const mesh = new THREE.SkinnedMesh(geo, new THREE.MeshStandardMaterial());
  const root = new THREE.Group(); root.add(bone, mesh); root.position.set(40, 2, -7); root.updateMatrixWorld(true);
  // Positions span ±1 for a 1.7 m body: the inverse bind matrix carries the .85 m unit.
  // (three skins a vertex to bone.matrixWorld · inverse · bindMatrix · position).
  const inverse = new THREE.Matrix4().copy(bone.matrixWorld).invert().multiply(root.matrixWorld)
    .multiply(new THREE.Matrix4().makeScale(.85, .85, .85)).multiply(new THREE.Matrix4().makeTranslation(0, 1, 0))
    .multiply(new THREE.Matrix4().copy(mesh.matrixWorld).invert());
  mesh.bind(new THREE.Skeleton([bone], [inverse]), mesh.matrixWorld);
  const m = restMatrix(mesh, root);
  const foot = new THREE.Vector3(0, -1, 0).applyMatrix4(m), top = new THREE.Vector3(0, 1, 0).applyMatrix4(m);
  assert(Math.abs(foot.y) < 1e-6 && Math.abs(top.y - 1.7) < 1e-6, `rest pose in metres from the root: ${foot.y} → ${top.y}`);
}

// Splices into three's own standard shader, after a prior hook, and is idempotent.
const compile = material => {
  const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader, fragmentShader: THREE.ShaderLib.standard.fragmentShader };
  material.onBeforeCompile(shader, null);
  return shader;
};
const dressOne = (name, hook) => {
  const m = Object.assign(new THREE.MeshStandardMaterial(), { name });
  if (hook) { m.onBeforeCompile = hook; m.customProgramCacheKey = () => 'chicago4d-confidence'; }
  const root = new THREE.Mesh(new THREE.BufferGeometry(), m);
  root.geometry.setAttribute('position', new THREE.Float32BufferAttribute([0, 1.6, 0, .1, 1.8, 0, -.1, 1.7, .1], 3));
  dressSkin(root); dressSkin(root);
  return m;
};
let priorRan = 0;
const skin = dressOne('skin', shader => { priorRan++; shader.fragmentShader = '// prior\n' + shader.fragmentShader; });
const s = compile(skin);
assert.equal(priorRan, 1, 'the prior hook runs once, first');
assert(s.fragmentShader.includes('// prior'));
assert(THREE.ShaderChunk.lights_physical_pars_fragment.includes('void RE_Direct_Physical( const in IncidentLight directLight'), "three's direct-light signature is the one wrapped");
for (const marker of ['chiSkinH = - chiSkin.x * pore', 'roughnessFactor = clamp( min( roughnessFactor, chiSkinSheen.z ) - chiSkinSheen.x', 'chiSkinN0 = normal;',
  'void chiSkinDirect(', '#define RE_Direct chiSkinDirect', 'reflectedLight.indirectDiffuse += diffuseColor.rgb * chiSkinSheen.y']) {
  assert.equal(s.fragmentShader.split(marker).length, 2, `skin spliced once: ${marker}`);
}
// The wrapper must follow three's own definition, and the normal step the begin step.
assert(s.fragmentShader.indexOf('#include <lights_physical_pars_fragment>') < s.fragmentShader.indexOf('void chiSkinDirect('));
assert(s.vertexShader.includes('vChiSkinP = ( chiSkinRest * vec4( position, 1.0 ) ).xyz;'));
assert.deepEqual(Object.keys(s.uniforms).sort(), ['chiBrowTint', 'chiFace', 'chiFaceLook', 'chiFaceMarks', 'chiSkin', 'chiSkinLipTone', 'chiSkinRest', 'chiSkinSheen']);
// T-3553 (Kevin, 2026-11-12: "when the sun is behind people their lips have a pink line too much"):
// lips found in the map's own colour (the complexion divided out) and turned partway to the skin's
// hue; the parting shaded in the light step. Every skin, every period: one program.
assert(SKIN.lip_tone > 0 && SKIN.lip_tone < 1, 'a lip keeps some of its own colour');
assert.equal(s.uniforms.chiSkinLipTone.value, SKIN.lip_tone);
for (const marker of ['vec3 tex = c / max( diffuse, vec3( 1e-3 ) );', 'chiSkinLip = smoothstep(', 'chiSkinLip * chiSkinLipTone',
  'chiSkinCrease = chiSkinLip * face', 'reflectedLight.indirectDiffuse *= shade;'])
  assert.equal(s.fragmentShader.split(marker).length, 2, `lips spliced once: ${marker}`);
assert(s.fragmentShader.indexOf('chiSkinLip = smoothstep(') < s.fragmentShader.indexOf('chiSkinCrease = chiSkinLip'), 'the lip is found before its parting is shaded');
// T-3493: a face's look is uniforms; a body with no face frame draws no age and no brow shade.
assert.deepEqual(s.uniforms.chiFaceLook.value.toArray(), [0, 0, 0, 0]);
for (const marker of ['float ageH = 0.0;', 'c = mix( c, c * chiBrowTint,', 'chiSkinH = - chiSkin.x * pore * 0.000035 - chiSkin.y * lines * 0.00002 + grain * 0.00007 + ageH;'])
  assert.equal(s.fragmentShader.split(marker).length, 2, `face look spliced once: ${marker}`);
assert.equal(restingLid(null), 0);
assert.equal(restingLid(AGE.lid_from), 0, 'no resting lid before its age');
assert(Math.abs(restingLid(AGE.lid_full) - AGE.lid_most) < 1e-9 && restingLid(99) === AGE.lid_most, 'full by its age, no further');
assert.deepEqual(s.uniforms.chiSkin.value.toArray(), [SKIN.pores, SKIN.lines, SKIN.mottle, SKIN.scatter]);
assert.equal(skin.customProgramCacheKey(), 'chicago4d-confidence|chicago-skin-v1', 'the key names the chain');
assert.equal(skin.map ?? null, null, 'no texture added');

const hair = dressOne('hair__makehuman_short04');
const h = compile(hair);
for (const marker of ['void chiHairDirect(', '#define RE_Direct chiHairDirect', 'roughnessFactor = max( roughnessFactor, chiHair.w );', 'chiHairTv = dot( t, t )']) {
  assert.equal(h.fragmentShader.split(marker).length, 2, `hair spliced once: ${marker}`);
}
// The strand runs with the skinned body: it is turned by skinMatrix, which three declares before begin_vertex.
assert(h.vertexShader.indexOf('#include <skinnormal_vertex>') < h.vertexShader.indexOf('tObj = ( skinMatrix * vec4( tObj, 0.0 ) ).xyz;'));
assert.deepEqual(Object.keys(h.uniforms).sort(), ['chiHair', 'chiHairCrown', 'chiSkinRest', 'chiSkinRestInv']);
assert.equal(hair.customProgramCacheKey(), '|chicago-hair-v1');

// Bodies differ by uniforms, never code: one skin program for two bodies.
const a = compile(dressOne('skin')), b = compile(dressOne('skin__other'));
assert.equal(a.vertexShader + a.fragmentShader, b.vertexShader + b.fragmentShader, 'one skin program text');

// Every person, not only drivers: humans.js dresses each body it builds.
const humans = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
assert(/import \{ dressSkin(, restingLid)? \} from '\.\/human-skin\.js';/.test(humans), 'humans.js imports dressSkin');
// T-3412 put per-person variation between the clone and the dressing, so the window
// allows build()'s whole preamble, not just the lines that were there first.
assert(/const scene = cloneSkinned\(gltf\.scene\);[\s\S]{0,1700}dressSkin\(scene[,)]/.test(humans), 'build() dresses the clone');
// T-3493: the person's age reaches the skin, and the face's cards join the face's morphs.
assert(/dressSkin\(scene, \{ age: this\.variation\?\.age/.test(humans), 'build() passes the person\'s age');
assert(/faces\.push\(hair\.face\)/.test(humans), 'brows and lashes move with the face');
console.log('human-skin: skin, hair and eyes only, no texture, spliced at every anchor, chained key, rest pose in metres, every body: PASS');

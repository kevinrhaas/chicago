/**
 * T-0053: a patched plain lit material cannot be handed another patched
 * material's compiled program.
 *
 *   node tools/test_program_cache_key.mjs
 *
 * three caches a compiled program under a key ending in
 * `material.customProgramCacheKey()`, whose default is the SOURCE TEXT of
 * `onBeforeCompile`. Before T-0053 every material `confidence.patch()` touched
 * reported the text of the same arrow function, so a plain patched
 * MeshStandardMaterial and a mapless building material — whose roughness hook
 * sits beneath the confidence hook — asked for one program, and whichever
 * compiled first drew both (T-0050's black fence).
 *
 * This imports the real `confidence.js` and asks the question three asks. It
 * also asks it of the same file with the T-0053 key removed, and requires the
 * collision to come back there: an assertion that cannot fail on the old code
 * proves nothing. It does not compile GLSL; the key is the whole of what three
 * consults to decide whether two materials share a program, and the contract
 * at the end pins that three still consults it.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const vendor = path.join(web, 'vendor/three-0.185.1');
const threeURL = pathToFileURL(path.join(vendor, 'three.module.js')).href;
const THREE = await import(threeURL);
const moduleURL = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;

const source = await readFile(path.join(web, 'js/confidence.js'), 'utf8');
const load = async (text) => (await import(moduleURL(text.replace("from 'three'", `from '${threeURL}'`))));

// The roughness hook buildings.js installs beneath the confidence patch, in the
// shape it has there (chained prior-first). Its body is not what is under test;
// that it is a different hook from confidence's is.
function perVertexRoughness(material) {
  const prior = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    shader.fragmentShader = shader.fragmentShader.replace(
      '#include <roughnessmap_fragment>', 'float roughnessFactor = vChiRough;');
  };
  return material;
}

const plain = () => new THREE.MeshStandardMaterial({ color: 0x8a6a4a, roughness: 0.9 });
const building = () => perVertexRoughness(new THREE.MeshStandardMaterial({ vertexColors: true }));
const key = (m) => m.customProgramCacheKey();

let failures = 0;
function check(label, fn) {
  try { fn(); console.log(`  ok   ${label}`); } catch (err) {
    failures++;
    console.log(`  FAIL ${label}\n       ${err.message.split('\n')[0]}`);
  }
}

// The T-0053 collision itself: the one assertion that fails on the old code.
const collision = (view) => () => {
  assert.notEqual(key(view.patch(plain())), key(view.patch(building())));
};

console.log('T-0053 — confidence.patch() keys a program by the hooks that write it');
const view = (await load(source)).createConfidenceView();

check('a plain patched material and a building material ask for different programs', collision(view));
// Neither of the next two collided before T-0053; they keep the cure from
// becoming a fixed key that would make them collide.
check('…and so does a patched material wrapped by a second hook after patching', () => {
  const wrapped = perVertexRoughness(view.patch(plain()));
  assert.notEqual(key(wrapped), key(view.patch(plain())));
  assert.notEqual(key(wrapped), key(view.patch(building())));
});
check('…and so does a material that carried a key of its own before patching', () => {
  const own = plain();
  own.onBeforeCompile = () => {};
  own.customProgramCacheKey = () => 'a-layer-of-its-own';
  assert.notEqual(key(view.patch(own)), key(view.patch(plain())));
});

check('two plain patched materials still share one program', () => {
  assert.equal(key(view.patch(plain())), key(view.patch(plain())));
});
check('two building materials still share one program (not one per material)', () => {
  assert.equal(key(view.patch(building())), key(view.patch(building())));
});
check('a patched depth material reports the confidence hook alone', () => {
  assert.equal(key(view.patch(new THREE.MeshDepthMaterial())), 'chicago4d-confidence');
});
check('a key carried before patching is part of the key, not lost', () => {
  const own = plain();
  own.customProgramCacheKey = () => 'a-layer-of-its-own';
  assert.match(key(view.patch(own)), /a-layer-of-its-own/);
});
check('a key a layer assigns after patching still wins (enclosures.js and kin)', () => {
  const m = view.patch(plain());
  m.customProgramCacheKey = () => 'chicago4d-enclosure-timber';
  assert.equal(key(m), 'chicago4d-enclosure-timber');
});
check('patching twice changes nothing', () => {
  const m = view.patch(building());
  const once = key(m);
  view.patch(m);
  assert.equal(key(m), once);
});
check('the patched hook still runs the hook beneath it', () => {
  const m = view.patch(building());
  const shader = {
    uniforms: {},
    vertexShader: '#include <begin_vertex>',
    fragmentShader: '#include <clipping_planes_fragment>\n#include <color_fragment>\n#include <roughnessmap_fragment>',
  };
  m.onBeforeCompile(shader, null);
  assert.match(shader.fragmentShader, /roughnessFactor = vChiRough/);
  assert.ok('uConfMode' in shader.uniforms);
});

// Teeth: the same file with the T-0053 key taken out must collide again.
const KEY_BLOCK = /\n {4}material\.customProgramCacheKey = function customProgramCacheKey\(\) \{[\s\S]*?\n {4}\};\n/;
check('self-test: the key assignment is where this test expects it', () => {
  assert.match(source, KEY_BLOCK);
});
const unkeyed = (await load(source.replace(KEY_BLOCK, '\n'))).createConfidenceView();
check('self-test: without the key, the plain and building materials collide again', () => {
  assert.throws(collision(unkeyed), assert.AssertionError);
});

// Contracts: the key is what three consults, and buildings.js chains in the
// order the building material above was built in.
const threeSource = await readFile(path.join(vendor, 'three.module.js'), 'utf8');
check('three builds its program key from material.customProgramCacheKey()', () => {
  assert.match(threeSource, /customProgramCacheKey: material\.customProgramCacheKey\(\)/);
  assert.match(threeSource, /array\.push\( parameters\.customProgramCacheKey \)/);
});
const buildings = await readFile(path.join(web, 'js/buildings.js'), 'utf8');
check('buildings.js installs its roughness hook beneath the confidence patch', () => {
  assert.match(buildings, /perVertexRoughness\(material\);\s*\n\s*confidence\.patch\(material\);/);
});

if (failures) {
  console.log(`\n${failures} check(s) failed`);
  process.exit(1);
}
console.log('\nall checks passed');

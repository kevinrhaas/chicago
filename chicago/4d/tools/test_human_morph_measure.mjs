// SPDX-License-Identifier: GPL-3.0-or-later
// Exercise the installed reader and acceptance block with real CPU-skinned geometry.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import * as THREE from '../renderers/web/vendor/three-0.185.1/three.module.js';

const read = (name) => fs.readFileSync(new URL(name, import.meta.url), 'utf8');
const source = read('./human_fixture.html');
const acceptance = read('./human_fixture.mjs');
const contract = JSON.parse(read('../data/humans/contract.json'));
const names = contract.morphs.required;
assert.equal(names.length, 3);
function between(text, start, end) {
  const a = text.indexOf(start), b = text.indexOf(end, a);
  assert.ok(a >= 0 && b > a, `Source boundary missing: ${start}`);
  return text.slice(a, b);
}
const sampling = between(source, 'function positions(body)', 'function boxOf(p)')
  + between(source, 'function maxMove(a, b)', 'const angle =');
const measurement = between(source, '  r.morphs =', '  // Clips:');
const requiredGuard = between(acceptance,
  '  if (contract.morphs.required_lods.includes(lod))',
  "  check('the required material slots load'");
const oldFirstMesh = measurement.replace(/^  r\.morphs = .*$/m,
  '  r.morphs = Object.keys(mesh.morphTargetDictionary || {});');
assert.notEqual(oldFirstMesh, measurement, 'The original reader control must differ');

function mesh(name, morphs, defaults = [0, 0, 0], zero = false) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(
    [0, 0, 0, .1, 1, 0, 0, 1.5, 0], 3));
  geometry.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Array(12).fill(0), 4));
  geometry.setAttribute('skinWeight', new THREE.Float32BufferAttribute(
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0], 4));
  if (morphs) {
    geometry.morphTargetsRelative = true;
    geometry.morphAttributes.position = names.map((target, i) => {
      const attribute = new THREE.Float32BufferAttribute(
        [0, 0, 0, 0, 0, 0, 0, zero ? 0 : .005 + i * .001, 0], 3);
      attribute.name = target;
      return attribute;
    });
  }
  const result = new THREE.SkinnedMesh(geometry, new THREE.MeshBasicMaterial());
  result.name = name;
  const bone = new THREE.Bone();
  result.add(bone);
  result.bind(new THREE.Skeleton([bone]));
  if (morphs) result.morphTargetInfluences.splice(0, names.length, ...defaults);
  return result;
}

function run(block, {order = ['hair', 'body'], defaults = [0, 0, 0],
  second = false, zero = false, inject = false} = {}) {
  const scene = new THREE.Scene();
  const meshes = {hair: mesh('hair', false), body: mesh('body', true, defaults, zero),
    body2: mesh('body2', true, [.6, .1, .25], zero)};
  for (const name of order) scene.add(meshes[name]);
  if (second) scene.add(meshes.body2);
  scene.updateMatrixWorld(true);
  const skinned = [];
  scene.traverse((object) => {
    if (object.isSkinnedMesh) { skinned.push(object); object.skeleton.update(); }
  });
  const snapshot = () => skinned.map((object) => object.morphTargetInfluences?.slice() ?? null);
  const before = snapshot();
  const context = vm.createContext({THREE, skinned, mesh: skinned[0], r: {}});
  vm.runInContext(sampling + 'const rest = positions(skinned);', context);
  if (inject) vm.runInContext('positions = () => { throw new Error("sampling failure"); };', context);
  let error = null;
  try { vm.runInContext(block, context); } catch (caught) { error = caught.message; }
  const result = {r: JSON.parse(JSON.stringify(context.r)), before, after: snapshot(), error};
  for (const object of Object.values(meshes)) {
    object.geometry.dispose(); object.material.dispose(); object.skeleton.dispose();
  }
  return result;
}

function accepted(result) {
  const findings = [];
  vm.runInNewContext(requiredGuard, {contract, REQ_MORPHS: names, lod: 0, r: result.r,
    check: (label, passed) => { if (!passed) findings.push(label); }});
  return findings.length === 0;
}

assert.equal(accepted(run(oldFirstMesh)), false, 'Original hair-first reader must fail');
for (const options of [{}, {order: ['body', 'hair']}, {defaults: [.2, .3, .4], second: true}]) {
  const result = run(measurement, options);
  assert.equal(result.error, null);
  assert.equal(accepted(result), true);
  assert.deepEqual(result.after, result.before, 'Restore each mesh\'s own defaults');
}
for (const options of [{order: ['hair']}, {zero: true}]) {
  assert.equal(accepted(run(measurement, options)), false, 'Missing/no-op targets must fail');
}
const failure = run(measurement, {defaults: [.2, .3, .4], second: true, inject: true});
assert.equal(failure.error, 'sampling failure');
assert.deepEqual(failure.after, failure.before, 'Restore defaults when sampling throws');
console.log('PASS human morph reader: both mesh orders, missing/no-op controls, exact defaults and failure restoration');

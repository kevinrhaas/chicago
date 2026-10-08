#!/usr/bin/env node
/**
 * THE WELCOME DRAWS THE TOWN ONLY WHEN THE TOWN CHANGED (T-2113).
 *
 * `renderers/web/js/gate-frame.js` decides, while the gate is up, whether a
 * tick draws. Its failure modes are opposite and both real: a change it cannot
 * see leaves a stale town under the menu, and a signature that moves every tick
 * holds nothing. So this builds a scene from the real three.js, asks once that
 * an untouched scene is held tick after tick, and then makes every kind of change
 * the loop makes under the gate, one at a time, and asks that each is drawn
 * exactly once. No browser: the signature reads objects, not pixels.
 */
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const THREE = await import(pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href);
const { createGateFrame, frameSignature } = await import(pathToFileURL(path.join(web, 'js/gate-frame.js')).href);

// The parts of a WebGLRenderer the signature reads, without a GL context.
const renderer = {
  domElement: { width: 1280, height: 800 }, toneMappingExposure: 1, shadowMap: { enabled: true, type: 1 },
};
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xcccccc, 10, 900);
const camera = new THREE.PerspectiveCamera(62, 1.6, 0.1, 3000);
camera.position.set(0, 2, 10);
camera.updateMatrixWorld();

const texture = new THREE.DataTexture(new Uint8Array(4), 1, 1);
const lit = new THREE.MeshStandardMaterial({ color: 0x8a6a4a, map: texture });
const box = new THREE.Mesh(new THREE.BoxGeometry(1, 1, 1), lit);
const shader = new THREE.ShaderMaterial({ uniforms: { aid: { value: 0 }, tint: { value: new THREE.Color(1, 1, 1) } } });
const strip = new THREE.Mesh(new THREE.PlaneGeometry(4, 4), shader);
const trees = new THREE.InstancedMesh(new THREE.ConeGeometry(1, 3), lit, 64);
trees.count = 10;
const sun = new THREE.DirectionalLight(0xffffff, 2);
scene.add(box, strip, trees, sun);

const gate = createGateFrame({ renderer, scene, camera });
assert.equal(gate.due(), true, 'the first frame under the gate is drawn');
for (let i = 0; i < 50; i++) assert.equal(gate.due(), false, `an untouched town is held (tick ${i})`);
assert.equal(gate.held, 50);

const changes = {
  'the camera moves (a jaunt preview, a spawn)': () => { camera.position.x += 0.001; camera.updateMatrixWorld(); },
  'the projection changes (fov, resize)': () => { camera.fov = 70; camera.updateProjectionMatrix(); },
  'the drawing buffer is resized (sharpness, rotation)': () => { renderer.domElement.width = 1170; },
  'the exposure moves (brightness)': () => { renderer.toneMappingExposure = 1.1; },
  'shadows are switched off': () => { renderer.shadowMap.enabled = false; },
  'the haze changes colour': () => { scene.fog.color.setHex(0xbbccdd); },
  'a layer streams in': () => { scene.add(new THREE.Mesh(new THREE.BoxGeometry(), lit)); },
  'a layer is hidden (detail, a confidence level)': () => { strip.visible = false; },
  'a hidden layer is shown again': () => { strip.visible = true; },
  'a buffer is rewritten in place (the flora rebuild)': () => { box.geometry.attributes.position.needsUpdate = true; },
  'an index is rewritten': () => { box.geometry.index.needsUpdate = true; },
  'a draw range is cut': () => { box.geometry.setDrawRange(0, 12); },
  'more instances are drawn': () => { trees.count = 20; },
  'an instance moves': () => { trees.instanceMatrix.needsUpdate = true; },
  'an object moves': () => { box.position.y = 0.5; },
  'an object turns': () => { box.rotation.y = 0.25; },
  'a texture lands (a sign atlas)': () => { texture.needsUpdate = true; },
  'a material is recompiled': () => { lit.needsUpdate = true; },
  'a material colour is written': () => { lit.color.setHex(0x112233); },
  'a uniform number is written (the road aid)': () => { shader.uniforms.aid.value = 1; },
  'a uniform colour is written': () => { shader.uniforms.tint.value.setRGB(0.5, 1, 1); },
  'a light dims': () => { sun.intensity = 1.5; },
  'the gate is told outright (a setting)': () => gate.invalidate(),
  'the gate reopens (pause)': () => gate.reset(),
};
for (const [what, change] of Object.entries(changes)) {
  change();
  assert.equal(gate.due(), true, `drawn when ${what}`);
  assert.equal(gate.due(), false, `held again after ${what} was drawn`);
}

// Equal scenes sign equal; the signature is a pure read and leaves no mark.
const before = Object.keys(box).sort().join();
const a = frameSignature(renderer, scene, camera);
assert.equal(frameSignature(renderer, scene, camera), a);
assert.equal(Object.keys(box).sort().join(), before, 'the signature writes nothing onto the objects it reads');

console.log(`gate frame: an untouched town held 50 of 50 ticks; ${Object.keys(changes).length} kinds of change each drawn once and then held`);

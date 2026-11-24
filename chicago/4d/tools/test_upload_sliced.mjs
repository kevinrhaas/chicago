#!/usr/bin/env node
/**
 * T-3728: a weak computer's boot upload, worked in slices (upload-release.js
 * `uploadLayerSliced`), uploads exactly what the one-pass upload does.
 *
 *  1. every bound worked out in slices is three's own figure — a big geometry's box
 *     and sphere, and every geometry of a batch;
 *  2. the pieces together draw every object the one pass draws, each exactly once,
 *     and nothing the pass would not (hidden, held back, off the camera's layers);
 *  3. a yield falls between pieces, and every piece puts back what it touched: the
 *     visibility, culling, layer bits and the camera's mask, before the yield;
 *  4. the lights take each piece's layer bit, so the programs are the real frame's.
 */
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const { register } = await import('node:module');
register('data:text/javascript,' + encodeURIComponent(`
  import { readFile } from 'node:fs/promises';
  export async function resolve(s,c,n) {
    if(s==='three') return {url:${JSON.stringify(threeURL)},shortCircuit:true};
    return n(s,c);
  }
  export async function load(u,c,n) {
    if(u.startsWith('file:')&&u.endsWith('.js'))
      return {format:'module',source:await readFile(new URL(u),'utf8'),shortCircuit:true};
    return n(u,c);
  }
`), import.meta.url);
const THREE = await import(threeURL);
const { uploadLayerNow, uploadLayerSliced } = await import(pathToFileURL(path.join(web, 'js/upload-release.js')));

let seed = 7;
const rand = () => ((seed = (seed * 16807) % 2147483647) / 2147483647) * 200 - 100;
const lights = () => [new THREE.DirectionalLight(), new THREE.AmbientLight()];

function soup(n, normalized = false) {
  const g = new THREE.BufferGeometry();
  if (normalized) {
    const a = new Int16Array(n * 3);
    for (let i = 0; i < a.length; i += 1) a[i] = Math.round(rand() * 300);
    g.setAttribute('position', new THREE.BufferAttribute(a, 3, true));
  } else {
    const a = new Float32Array(n * 3);
    for (let i = 0; i < a.length; i += 1) a[i] = rand();
    g.setAttribute('position', new THREE.BufferAttribute(a, 3));
  }
  return g;
}

function town() {
  seed = 7;
  const scene = new THREE.Scene();
  for (const l of lights()) scene.add(l);
  const other = new THREE.Group(); other.name = 'streets'; scene.add(other);
  other.add(new THREE.Mesh(soup(30), new THREE.MeshBasicMaterial()));
  const layer = new THREE.Group(); layer.name = 'trees'; scene.add(layer);
  const mat = new THREE.MeshStandardMaterial();
  const big = new THREE.Mesh(soup(100_003), mat); big.name = 'big';
  const bigN = new THREE.Mesh(soup(70_001, true), mat); bigN.name = 'big-normalized';
  layer.add(big, bigN);
  const sub = new THREE.Group(); layer.add(sub);
  for (let i = 0; i < 40; i += 1) {
    const m = new THREE.Mesh(soup(200 + i * 50), mat); m.name = `small-${i}`; sub.add(m);
  }
  const hidden = new THREE.Mesh(soup(40), mat); hidden.name = 'hidden'; hidden.visible = false; layer.add(hidden);
  const held = new THREE.Mesh(soup(40), mat); held.name = 'held'; held.userData.heldBack = true; layer.add(held);
  const offLayer = new THREE.Mesh(soup(40), mat); offLayer.name = 'off-layer'; offLayer.layers.set(5); layer.add(offLayer);
  const batch = new THREE.BatchedMesh(8, 20_000, 40_000, mat); batch.name = 'batch';
  for (let i = 0; i < 150; i += 1) {
    const g = soup(30 + (i % 7) * 10);
    g.setIndex([...Array(g.attributes.position.count).keys()]);
    const id = batch.addGeometry(g);
    if (i < 8) batch.addInstance(id);
  }
  layer.add(batch);
  return { scene, layer, big, bigN, batch };
}

/** A renderer that uploads nothing: it records what three would project and draw. */
function stubRenderer(scene, log) {
  let scissorTest = false;
  const scissor = new THREE.Vector4(0, 0, 640, 480);
  return {
    shadowMap: { autoUpdate: true, needsUpdate: false },
    getScissorTest: () => scissorTest,
    setScissorTest: (v) => { scissorTest = v; },
    getScissor: (t) => t.copy(scissor),
    setScissor: (x, y, w, h) => { if (x.isVector4) scissor.copy(x); else scissor.set(x, y, w, h); },
    getContext: () => ({ getExtension: () => null }),
    render(s, camera) {
      const drawn = [], lit = [];
      const project = (o) => {
        if (!o.visible) return;
        if (o.layers.test(camera.layers)) {
          if (o.isLight) lit.push(o);
          else if (o.isMesh || o.isLine || o.isPoints) drawn.push(o);
        }
        for (const c of o.children) project(c);
      };
      project(s);
      assert.equal(this.shadowMap.autoUpdate, false, 'the sun is held for the pass');
      log.push({ drawn, lit, culled: drawn.filter((o) => o.frustumCulled).length });
    },
  };
}

const hide = (o) => !!o.userData.heldBack;
const camera = new THREE.PerspectiveCamera();
let checks = 0;

// One pass: the reference.
const one = town();
const oneLog = [];
uploadLayerNow(stubRenderer(one.scene, oneLog), one.scene, camera, one.layer, { hide });
assert.equal(oneLog.length, 1);
const reference = oneLog[0].drawn.map((o) => o.name).sort();
assert.ok(reference.includes('big') && reference.includes('batch'));
assert.ok(!reference.includes('hidden') && !reference.includes('held') && !reference.includes('off-layer'));
checks += 3;

// Sliced.
const two = town();
const log = [];
let yields = 0;
const masks = new Map();
two.scene.traverse((o) => masks.set(o, o.layers.mask));
const visible = new Map();
two.scene.traverse((o) => visible.set(o, [o.visible, o.frustumCulled]));
const pause = () => {
  yields += 1;
  // At every yield the scene is as it was: nothing tagged, nothing hidden, the camera's own mask.
  for (const [o, mask] of masks) assert.equal(o.layers.mask, mask, `layers of ${o.name || o.type} put back`);
  for (const [o, [v, f]] of visible) { assert.equal(o.visible, v); assert.equal(o.frustumCulled, f); }
  assert.equal(camera.layers.mask, 1);
  return Promise.resolve();
};
await uploadLayerSliced(stubRenderer(two.scene, log), two.scene, camera, two.layer, { hide, pause, pieceBytes: 256 << 10, pieceMs: 0 });
assert.ok(log.length > 3, `the layer went up in pieces (${log.length})`); checks += 1;
assert.ok(yields >= log.length - 1, 'a yield between pieces'); checks += 1;
const names = log.flatMap((p) => p.drawn.map((o) => o.name)).sort();
assert.deepEqual(names, reference, 'every object the one pass draws, each exactly once'); checks += 1;
for (const p of log) {
  assert.equal(p.lit.length, 2, 'both lights are in every piece'); checks += 1;
  assert.equal(p.culled, 0, 'no frustum cull in the pass'); checks += 1;
}
pause(); checks += 1;

// The bounds are three's own.
for (const [a, b] of [[one.big, two.big], [one.bigN, two.bigN]]) {
  const ref = a.geometry.clone();
  ref.boundingBox = null; ref.boundingSphere = null;
  ref.computeBoundingBox(); ref.computeBoundingSphere();
  assert.deepEqual(b.geometry.boundingBox.min.toArray(), ref.boundingBox.min.toArray());
  assert.deepEqual(b.geometry.boundingBox.max.toArray(), ref.boundingBox.max.toArray());
  assert.deepEqual(b.geometry.boundingSphere.center.toArray(), ref.boundingSphere.center.toArray());
  assert.equal(b.geometry.boundingSphere.radius, ref.boundingSphere.radius);
  checks += 4;
}
const box = new THREE.Box3(), sphere = new THREE.Sphere(), box2 = new THREE.Box3(), sphere2 = new THREE.Sphere();
for (let id = 0; id < 150; id += 1) {
  one.batch.getBoundingBoxAt(id, box); two.batch.getBoundingBoxAt(id, box2);
  one.batch.getBoundingSphereAt(id, sphere); two.batch.getBoundingSphereAt(id, sphere2);
  assert.ok(box2.containsBox(box) && sphere2.radius >= sphere.radius, `batch geometry ${id} bounds`);
  checks += 1;
}
assert.deepEqual(two.batch.geometry.boundingSphere.center.toArray(), one.batch.geometry.boundingSphere.center.toArray());
assert.equal(two.batch.geometry.boundingSphere.radius, one.batch.geometry.boundingSphere.radius);
checks += 2;

// A layer hidden meanwhile is left alone.
const three = town();
three.layer.visible = false;
const log3 = [];
await uploadLayerSliced(stubRenderer(three.scene, log3), three.scene, camera, three.layer, { hide });
assert.equal(log3.length, 0); checks += 1;

console.log(`test_upload_sliced: ${checks} checks PASS (${log.length} pieces, ${yields} yields)`);

#!/usr/bin/env node
// T-2827: a pick draws only the batches its ray can meet, and a phone's probe
// answers from the parts' boxes without drawing (gpu-pick.js). No browser: three
// in Node, and a renderer that counts what it is asked to draw.
import fs from 'node:fs';
import assert from 'node:assert/strict';
const js = new URL('../renderers/web/js/', import.meta.url);
const threeURL = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
const THREE = await import(threeURL);
const source = fs.readFileSync(new URL('gpu-pick.js', js), 'utf8')
  .replace("from 'three'", `from '${threeURL}'`)
  .replace("from './compact-streams.js'", `from '${new URL('compact-streams.js', js).href}'`);
const { gpuPick, boxPick, setPickRenderer } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));

// Two batches of unit boxes down the -z axis: A at 10 m and 30 m, B at 20 m and off to the side.
function batch(name, spots) {
  const b = new THREE.BatchedMesh(spots.length, 24 * spots.length, 36 * spots.length, new THREE.MeshBasicMaterial());
  b.name = name;
  const geo = b.addGeometry(new THREE.BoxGeometry(2, 2, 2));
  for (const [x, z] of spots) b.setMatrixAt(b.addInstance(geo), new THREE.Matrix4().makeTranslation(x, 0, z));
  b.updateMatrixWorld(true);
  return b;
}
const A = batch('A', [[0, -10], [0, -30]]);
const B = batch('B', [[0, -20], [40, -20]]);
const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 1000);
camera.updateMatrixWorld(true);
const centre = { x: 0, y: 0 };

// The box answer: nearest shown part, within reach, hidden parts passed over.
{
  const hit = boxPick([A, B], centre, camera, 400);
  assert.equal(hit.object, A); assert.equal(hit.batchId, 0);
  assert.ok(Math.abs(hit.distance - 9) < 0.05, `box face at 9 m, read ${hit.distance}`);
  assert.equal(boxPick([A, B], centre, camera, 5), null, 'nothing within 5 m');
  A.setVisibleAt(0, false);
  assert.equal(boxPick([A, B], centre, camera, 400).object, B, 'a hidden part is not answered');
  A.setVisibleAt(0, true);
  assert.equal(boxPick([A, B], { x: 0.9, y: 0.9 }, camera, 400), null, 'a ray past every box');
  // A part moved after its boxes were kept is read where it now stands.
  B.setMatrixAt(0, new THREE.Matrix4().makeTranslation(0, 0, -5));
  assert.equal(boxPick([A, B], centre, camera, 400).object, B);
  B.setMatrixAt(0, new THREE.Matrix4().makeTranslation(0, 0, -20));
  // A ray that starts inside a part meets it at once.
  const inside = camera.clone(); inside.position.set(0, 0, -10); inside.updateMatrixWorld(true);
  assert.equal(boxPick([A, B], centre, inside, 400).distance, 0);
}

// The drawn pick: only met batches go to the GPU, and a pick no box answers draws nothing.
{
  const drawn = [];
  const fake = {
    autoClear: true, shadowMap: { autoUpdate: true }, info: { autoReset: true, render: {} },
    getDrawingBufferSize: (v) => v.set(100, 100), getRenderTarget: () => null, getClearAlpha: () => 1,
    getClearColor: (c) => c, setClearColor() {}, setRenderTarget() {},
    render: (object) => { if (object.isBatchedMesh) drawn.push(object.name); },
    readRenderTargetPixels: (_t, _x, _y, _w, _h, buffer) => buffer.fill(0),
  };
  setPickRenderer(fake);
  assert.equal(gpuPick([A, B], { x: 0.9, y: 0.9 }, camera, 400), null);
  assert.deepEqual(drawn, [], 'a ray no box meets draws nothing');
  const C = batch('C', [[40, -40]]);
  gpuPick([A, B, C], centre, camera, 400);
  assert.deepEqual(drawn, ['A', 'B'], 'only the batches the ray meets are drawn');
  drawn.length = 0;
  gpuPick([A, B, C], centre, camera, 15);
  assert.deepEqual(drawn, ['A'], 'nor one met only beyond reach');
  setPickRenderer(null);
}

console.log('ok  a pick draws only the batches its ray meets; the box answer draws nothing (T-2827)');

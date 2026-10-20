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
const { gpuPick, gpuPickAsync, boxPick, setPickRenderer } = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));

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

// T-2723: the gaze target's read waits on a fence, not on the GPU, and answers what a tap answers.
{
  // The pixel every pick here draws: slot 1 (A), instance 1, 29 m down the ray.
  const words = Uint32Array.of(1, 1, new Uint32Array(Float32Array.of(29).buffer)[0]);
  const pixel = new Uint8Array(words.buffer);
  const fake = (gl) => ({
    autoClear: true, shadowMap: { autoUpdate: true }, info: { autoReset: true, render: {} },
    getDrawingBufferSize: (v) => v.set(100, 100), getRenderTarget: () => null, getClearAlpha: () => 1,
    getClearColor: (c) => c, setClearColor() {}, setRenderTarget() {}, render() {}, getContext: () => gl,
    readRenderTargetPixels: (_t, _x, _y, _w, _h, buffer, _f, k) => buffer.set(pixel.subarray(k * 4, k * 4 + 4)),
  });
  let packed = null, attachment = 0, waits = 0, signalAfter = 2;
  const stores = new Map();
  const gl = {
    PIXEL_PACK_BUFFER: 1, STREAM_READ: 2, COLOR_ATTACHMENT0: 10, RGBA: 3, UNSIGNED_BYTE: 4,
    SYNC_GPU_COMMANDS_COMPLETE: 5, TIMEOUT_EXPIRED: 6, ALREADY_SIGNALED: 7, CONDITION_SATISFIED: 8, WAIT_FAILED: 9,
    createBuffer: () => ({}), deleteBuffer: (b) => stores.delete(b), bindBuffer: (_t, b) => { packed = b; },
    bufferData: (_t, n) => stores.set(packed, new Uint8Array(n)), readBuffer: (a) => { attachment = a - 10; },
    readPixels: (_x, _y, _w, _h, _f, _t, offset) => {
      assert.ok(packed, 'the async read goes into a pack buffer');
      stores.get(packed).set(pixel.subarray(attachment * 4, attachment * 4 + 4), offset);
    },
    fenceSync: () => ({}), deleteSync() {}, flush() {},
    clientWaitSync: () => (++waits > signalAfter ? 7 : 6),
    getBufferSubData: (_t, _o, out) => out.set(stores.get(packed)),
  };
  setPickRenderer(fake(gl));
  const now = gpuPick([A, B], centre, camera, 400);
  const asked = gpuPickAsync([A, B], centre, camera, 400);
  assert.equal(packed, null, 'the pack buffer is unbound before the frame goes on, so a tap can still read');
  const later = await asked;
  assert.ok(waits > signalAfter, 'the answer waited for its fence');
  assert.equal(later.object, now.object); assert.equal(later.batchId, now.batchId);
  assert.equal(later.distance, now.distance); assert.ok(later.point.equals(now.point), 'the same answer as the tap\'s read');
  assert.equal(stores.size, 0, 'the pack buffer is let go');
  // A chunk rebuilt while its answer was on the way answers nothing.
  const D = new THREE.Mesh(new THREE.BoxGeometry(2, 2, 2).toNonIndexed());
  D.updateMatrixWorld(true);
  const rebuilt = gpuPickAsync([D], centre, camera, 400);
  D.geometry = new THREE.BufferGeometry();
  assert.equal(await rebuilt, null);
  // A read the context lost answers nothing, and the buffer is still let go.
  gl.clientWaitSync = () => 9;
  assert.equal(await gpuPickAsync([A, B], centre, camera, 400), null);
  assert.equal(stores.size, 0);
  // No fence to wait on: the tap's read, at once.
  setPickRenderer(fake(null));
  const fallback = await gpuPickAsync([A, B], centre, camera, 400);
  assert.equal(fallback.object, A); assert.equal(fallback.distance, 29);
  setPickRenderer(null);
}

console.log('ok  a pick draws only the batches its ray meets; the box answer draws nothing (T-2827); the gaze read waits on a fence, not the GPU (T-2723)');

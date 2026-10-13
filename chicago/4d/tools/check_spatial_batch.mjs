/** Exact ground batching contracts, including Three's real per-instance cull.
 * CPU geometry/state checks; published pixels and frame costs stay smoke gates.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(threeURL);
const source = await readFile(path.join(web, 'js/spatial-batch.js'), 'utf8');
const { spatialBatch, spatialPieces } = await import('data:text/javascript;base64,' + Buffer.from(
  source.replace("from 'three'", `from '${threeURL}'`)).toString('base64'));

function triangles(geometry) {
  const attrs = Object.entries(geometry.attributes).sort(([a], [b]) => a.localeCompare(b));
  const index = geometry.getIndex();
  const count = index?.count ?? geometry.getAttribute('position').count;
  const out = [];
  for (let i = 0; i < count; i += 3) {
    out.push(JSON.stringify([0, 1, 2].map((j) => {
      const k = index ? index.getX(i + j) : i + j;
      return attrs.map(([name, a]) => [name, a.itemSize, a.normalized,
        [...a.array.slice(k * a.itemSize, (k + 1) * a.itemSize)]]);
    })));
  }
  return out.sort();
}

for (const indexed of [false, true]) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute([
    -2, 0, -20, 2, 0, -20, 0, 1, -20,
    -2, 0, 100, 2, 0, 100, 0, 1, 100,
    38, 0, -20, 42, 0, -20, 40, 1, -20,
  ], 3));
  geometry.setAttribute('_confidence', new THREE.Float32BufferAttribute([0, .5, 1, 1, .5, 0, .5, 1, 0], 1));
  geometry.setAttribute('uv', new THREE.Float32BufferAttribute([0, 0, 1, 0, 0, 1, 1, 1, 2, 1, 1, 2, 2, 2, 3, 2, 2, 3], 2));
  geometry.setAttribute('color', new THREE.Uint8BufferAttribute(
    Array.from({ length: 36 }, (_, i) => i * 7), 4, true));
  if (indexed) geometry.setIndex([0, 1, 2, 3, 4, 5, 6, 7, 8, 0, 2, 1]);
  geometry.computeVertexNormals();
  const material = new THREE.MeshStandardMaterial({ transparent: true, depthWrite: false });
  const batch = spatialBatch(geometry, material);
  assert.deepEqual(triangles(batch.geometry), triangles(geometry), 'every triangle, winding and attribute byte survives');
  assert.equal(batch.material, material, 'the material is shared unchanged');
  assert.equal(batch.material.depthWrite, false, 'a ground decal keeps its depth policy');
  assert.equal(batch.perObjectFrustumCulled, true);
  assert.equal(batch.userData.spatialBatch.pieces, 3);
  const identity = new THREE.Matrix4();
  for (let i = 0; i < 3; i++) {
    assert.deepEqual(batch.getMatrixAt(i, new THREE.Matrix4()).elements, identity.elements);
  }
  // A triangle straddling the fixed-grid edge keeps its corners in its bounds.
  const edge = batch.getBoundingBoxAt(2, new THREE.Box3());
  assert.equal(edge.min.x, 38); assert.equal(edge.max.x, 42);
  const camera = new THREE.OrthographicCamera(-60, 60, 60, -60, 1, 200);
  camera.updateMatrixWorld(); batch.updateMatrixWorld();
  batch.onBeforeRender(null, null, camera, batch.geometry, material);
  assert.equal(batch._multiDrawCount, 2, 'the piece behind the visitor is not submitted');
  batch.setVisibleAt(0, false);
  batch.onBeforeRender(null, null, camera, batch.geometry, material);
  assert.equal(batch._multiDrawCount, 1, 'the reach can hold one piece without hiding its tile');
  batch.setVisibleAt(0, true);
  batch.onBeforeRender(null, null, camera, batch.geometry, material);
  assert.equal(batch._multiDrawCount, 2, 'restoring the reach restores the exact pieces');
  camera.lookAt(0, 0, 100); camera.updateMatrixWorld();
  batch.onBeforeRender(null, null, camera, batch.geometry, material);
  assert.equal(batch._multiDrawCount, 1, 'turning round restores the ground behind the old view');
  const ray = new THREE.Raycaster(new THREE.Vector3(0, .3, 0), new THREE.Vector3(0, 0, -1));
  const original = new THREE.Mesh(geometry, material);
  original.updateMatrixWorld();
  const hits = (mesh) => ray.intersectObject(mesh).map((h) => [h.distance, ...h.point.toArray()]);
  assert.ok(hits(original).length, 'the pick probe intersects the ground fixture');
  assert.deepEqual(hits(batch), hits(original), 'batched ground answers the same pick points and distances');
  batch.dispose(); geometry.dispose(); material.dispose();
}
console.log('PASS spatial ground batch: indexed/nonindexed triangles, attributes, bounds, material, identity transforms, frustum and reversible reach');

// A building's upper storey shares x/z with its basement; vertical cells must
// separate them without changing any surface or losing a corner at a boundary.
for (const indexed of [false, true]) {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute([
    7, 0, 0, 9, 0, 0, 7, 1, 0,
    7, 8, 0, 9, 8, 0, 7, 9, 0,
  ], 3));
  for (const name of ['uv', 'uv1', '_confidence', '_roughness', '_grain', '_pane']) {
    g.setAttribute(name, new THREE.Float32BufferAttribute([0, .25, .5, .75, 1, 0], 1));
  }
  g.setAttribute('color', new THREE.Uint8BufferAttribute([1, 2, 3, 4, 5, 6], 1, true));
  if (indexed) g.setIndex([0, 1, 2, 3, 4, 5]);
  g.computeVertexNormals();
  const pieces = spatialPieces(g, { cellM: 8, heightM: 4 });
  assert.equal(pieces.length, 2);
  assert.deepEqual(pieces.flatMap(triangles).sort(), triangles(g));
  for (const p of pieces) {
    p.computeBoundingBox();
    assert.equal(p.boundingBox.min.x, 7);
    assert.equal(p.boundingBox.max.x, 9);
    assert.equal(p.boundingBox.max.y - p.boundingBox.min.y, 1);
    p.dispose();
  }
  assert.throws(() => spatialPieces(g, { cellM: 0 }));
  assert.throws(() => spatialPieces(g, { heightM: NaN }));
  g.dispose();
}
console.log('PASS building cells: vertical separation, exact triangles and all attributes, boundary corners');

// A Float32/end-line nudge can cross the cell whose plane generated a cut.
// Exercise the shipped clipping/drape functions on a continuous, folded grid.
const streets = await readFile(path.join(web, 'js/streets.js'), 'utf8');
function body(name) {
  const start = streets.indexOf(`function ${name}(`);
  assert.ok(start >= 0, `missing shipped ${name}`);
  const open = streets.indexOf('{', start + streets.slice(start).indexOf(')') + 1);
  let depth = 1, end = open + 1;
  for (; depth && end < streets.length; end++) {
    if (streets[end] === '{') depth++;
    if (streets[end] === '}') depth--;
  }
  return streets.slice(start, end);
}
const drape = Function('const LIFT_M=.022,WET_NUDGE_M=.02,WET_NUDGE_STEPS=12;\n'
  + ['cellAt','ridgeOf','ridgeHeight','clipConvex','halfPlane','ridgeDrape'].map(body).join('\n')
  + '\nreturn {ridgeDrape,ridgeHeight};')();
const field = {
  grid: {originE:0,originN:0,cellM:2.5},
  surfaceHeight: (e) => Math.abs(e-200)*.9,
  inBounds: () => true, isWater: () => false,
};
const laid = drape.ridgeDrape(field, [[199.9,0],[200.1,0],[200.1,2],[199.9,2]],
  () => [0,0], (e,n) => [e+.00003,n]);
assert.ok(laid?.tris.length, 'cut panels were emitted');
for (const [e,n,y] of laid.verts) {
  assert.equal(e,Math.fround(e),'the final end-line position is Float32');
  const drawnY=Math.fround(y)-.022;
  assert.ok(Math.abs(drawnY-field.surfaceHeight(e,n))<1e-5,
    `end-line rounding left the drawn road off its actual cell: ${drawnY-field.surfaceHeight(e,n)}`);
}
console.log('PASS ridge drape: final Float32/end-line positions stand on their actual cell');

#!/usr/bin/env node
/**
 * check_batch_map_key.mjs — T-3411. The merged town batches a mapped material by the
 * picture it samples and how, not by its Texture's uuid (`buildings.js` `mapKey`).
 *
 * T-3387 laid seven 1835 brick buildings in one K03 panel, each GLB with its own clone
 * of the one shared (KTX2, so `CompressedTexture`) source, and the uuid key split them
 * into seven batches. This holds both halves of the fix: clones of one source share a
 * key, whether decoded images or compressed blocks; a different source, any sampler
 * or transform setting, or a texture class that is not a still picture does not.
 * Sliced out of buildings.js, which cannot be imported outside a page.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const THREE = await import(pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href);
const src = await readFile(path.join(web, 'js/buildings.js'), 'utf8');
const start = src.indexOf('const mapIds = new WeakMap();');
const end = src.indexOf('\n}\n', src.indexOf('export function mapKey(t) {'));
assert.ok(start > 0 && end > start, 'buildings.js no longer defines mapKey where this check reads it');
const mapKey = new Function('THREE', `${src.slice(start, end + 2).replace('export function', 'function')}\nreturn mapKey;`)(THREE);

let n = 0;
const check = (fn) => { fn(); n++; };
const image = { width: 4, height: 4, data: new Uint8Array(64) };
for (const make of [() => new THREE.Texture(image),
  () => new THREE.CompressedTexture([{ data: new Uint8Array(16), width: 4, height: 4 }], 4, 4, THREE.RGBA_ASTC_4x4_Format)]) {
  const t = make();
  const clone = t.clone();
  clone.mipmaps = (t.mipmaps ?? []).map((level) => ({ ...level })); // ktx2.js isolates descriptors
  check(() => assert.notEqual(t.uuid, clone.uuid));
  check(() => assert.equal(mapKey(t), mapKey(clone), `${t.constructor.name}: clones of one source share a batch`));
  check(() => assert.notEqual(mapKey(t), mapKey(make()), `${t.constructor.name}: another source does not`));
  for (const [field, value] of Object.entries({ channel: 1, wrapS: THREE.MirroredRepeatWrapping,
    wrapT: THREE.RepeatWrapping, magFilter: THREE.NearestFilter, minFilter: THREE.NearestFilter,
    anisotropy: 4, colorSpace: THREE.SRGBColorSpace, flipY: !t.flipY, rotation: 0.2,
    generateMipmaps: !t.generateMipmaps, premultiplyAlpha: true })) {
    const d = t.clone(); d[field] = value;
    check(() => assert.notEqual(mapKey(t), mapKey(d), `${t.constructor.name}: ${field} separates`));
  }
  for (const field of ['offset', 'repeat', 'center']) {
    const d = t.clone(); d[field].x += 0.25;
    check(() => assert.notEqual(mapKey(t), mapKey(d), `${t.constructor.name}: ${field} separates`));
  }
}
const canvasLike = new THREE.DataTexture(new Uint8Array(64), 4, 4);
check(() => assert.notEqual(mapKey(canvasLike), mapKey(canvasLike.clone()), 'other texture classes keep identity'));
const live = new THREE.Texture(image); live.onUpdate = () => {};
check(() => assert.notEqual(mapKey(live), mapKey(live.clone()), 'a self-updating texture keeps identity'));
check(() => assert.equal(mapKey(null), '-'));
console.log(`PASS batch map key (T-3411): ${n} checks — clones of one picture share a batch, nothing else does`);

// SPDX-License-Identifier: GPL-3.0-or-later
// Resource ownership and byte binding, not native model/appearance acceptance.
import assert from 'node:assert/strict';
import { register } from 'node:module';
import { createHash } from 'node:crypto';
const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export async function resolve(s,c,n){
if(s==='three')return{url:${JSON.stringify(vendor+'three.module.js')},shortCircuit:true};
if(s.startsWith('three/addons/'))return{url:${JSON.stringify(vendor)}+'addons/'+s.slice(13),shortCircuit:true};return n(s,c);}`)}`);
const THREE = await import('three');
const { acquireDraftHorse } = await import('../renderers/web/js/draft-horse-assets.js');
const bytes = new Uint8Array([1, 2, 3, 4]);
const hash = createHash('sha256').update(bytes).digest('hex');
const previous = globalThis.fetch;
let reads = 0, parses = 0, geometries = 0, materials = 0, failParse = false;
globalThis.fetch = async () => { reads++; return { ok: true, arrayBuffer: async () => bytes.buffer }; };
const loader = { async parseAsync() {
  parses++; if (failParse) throw Error('original parse failure');
  const scene = new THREE.Group(), geometry = new THREE.BoxGeometry(), material = new THREE.MeshStandardMaterial();
  geometry.addEventListener('dispose', () => geometries++); material.addEventListener('dispose', () => materials++);
  scene.add(new THREE.Mesh(geometry, material)); return { scene };
} };
const spec = { url: 'https://controlled.invalid/horse.glb', sha256: hash, materialVariant: 'organic_dielectric_v1', loader };
try {
  const [moving, parked] = await Promise.all([acquireDraftHorse(spec), acquireDraftHorse(spec)]);
  assert.equal(reads, 1); assert.equal(parses, 1); assert.equal(moving.asset, parked.asset);
  moving.release(); moving.release();
  assert.equal(geometries, 0); assert.equal(materials, 0, 'a still-used team keeps its source materials');
  parked.release(); assert.equal(geometries, 1); assert.equal(materials, 1);
  const again = await acquireDraftHorse(spec);
  assert.equal(reads, 2); assert.notEqual(again.asset, moving.asset);
  const native = await acquireDraftHorse({ ...spec, materialVariant: 'source_native' });
  assert.equal(reads, 3); assert.notEqual(native.asset, again.asset, 'different material variants never mutate one shared template');
  native.release(); again.release(); assert.equal(geometries, 3); assert.equal(materials, 3);
  const before = parses;
  await assert.rejects(acquireDraftHorse({ ...spec, sha256: '0'.repeat(64) }), /model binding/);
  assert.equal(parses, before, 'changed bytes are refused before model parsing');
  failParse = true; await assert.rejects(acquireDraftHorse(spec), /original parse failure/);
  failParse = false; const recovered = await acquireDraftHorse(spec); recovered.release();
  assert.equal(geometries, 4); assert.equal(materials, 4, 'a failed acquisition does not poison or retain a cache entry');
  await assert.rejects(acquireDraftHorse({ ...spec, materialVariant: 'invented' }), /explicit bound asset/);
  console.log('Draft horse leases PASS — moving/parked share one checked template; final release owns disposal; variants, failures and retries stay separate');
} finally { globalThis.fetch = previous; }

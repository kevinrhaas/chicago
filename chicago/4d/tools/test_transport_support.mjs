// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import { fitHorseSupport } from '../renderers/web/js/transport-support.js';
const support = options => fitHorseSupport({ e: 10, n: 20, yaw: .7, heightAt: () => 5, ...options });
assert.equal(support().height_m, 5); assert.equal(support().sampled_maximum_clearance_m, 0);
const plane = support({ heightAt: (e, n) => 5 + .01 * (e - 10) + .005 * (n - 20) });
assert(Math.abs(plane.height_m - 5) < 1e-12);
assert(plane.tilt_rad > 0 && plane.tilt_rad < Math.PI / 180);
assert(plane.sampled_maximum_clearance_m < 1e-12);
assert(Math.abs(Math.hypot(...plane.normal_local_xyz) - 1) < 1e-12);
assert.throws(() => support({ heightAt: (e, n) => e > 10 ? .002 : 0 }), /1mm/);
assert.throws(() => support({ heightAt: e => .1 * e }), /2-degree/);
assert.throws(() => support({ heightAt: () => null }), /no rendered ground/);
const slight = support({ heightAt: e => e > 10 ? .0005 : 0 });
assert(slight.sampled_minimum_clearance_m >= 0 && slight.sampled_maximum_clearance_m <= .001);
console.log('horse support: flat/tilted plane, original2degree+1mm bounds, rough/missing ground refusals PASS');

// Model-specific dimensions are admitted by the actual source GLB and complete
// finite native proof, and leave the original generic rectangle failures intact.
const { readFileSync } = await import('node:fs');
const { sha256, verifyCompleteClassifier, verifyMeasurements } = await import('./measure_horse_support_domain.mjs');
const { certifiedHorseSupportDomain, teamSupportAt } = await import('../renderers/web/js/transport-support.js');
const root = new URL('../', import.meta.url), read = path => readFileSync(new URL(path, root));
const config = JSON.parse(read('data/transport/driven/loops.json'));
const spec = config.horse_models.current26_inplace_full, certificateBytes = read('data/' + spec.support_domain.certificate_file);
assert.equal(sha256(certificateBytes), spec.support_domain.certificate_sha256);
const certificate = JSON.parse(certificateBytes), fixtureBytes = read(certificate.native_measurement_fixture);
assert.equal(sha256(fixtureBytes), certificate.native_measurement_fixture_sha256);
const fixture = JSON.parse(fixtureBytes), raw = read(certificate.asset_file);
assert.equal(sha256(raw), spec.sha256); assert.equal(certificate.asset_sha256, spec.sha256);
assert.equal(certificate.accepted_native_proof_sha256, 'b0024dc6ed116251b41a046e0bfd02c1e66a37d56385a09b430975783dc0f2d4');
assert.equal(certificate.accepted_native_domain_bridge_sha256, 'b063265f5d00721089cb92f518227e459d2b7a551a838eba55a37a8f35433484');
const reference = fixture.classifier.originalReference, ancestry = fixture.classifier.physicalAncestry;
assert.equal(sha256(read(reference.path)), reference.sha256); assert.equal(sha256(read(ancestry.path)), ancestry.sha256);
verifyCompleteClassifier(raw, JSON.parse(read(reference.path)), JSON.parse(read(ancestry.path)), fixture.classifier);
const measured = verifyMeasurements(certificate, fixture);
assert.equal(measured.halfX, .34852683866067585); assert.equal(measured.halfZ, .5937919879345586);
const domain = certifiedHorseSupportDomain(spec, certificate);
assert.deepEqual(domain, { half_width_m: .35, half_length_m: .595 }); assert(Object.isFrozen(domain));
for (const bad of [
  { ...spec, sha256: '0'.repeat(64) },
  { ...spec, support_domain: { ...spec.support_domain, model_sha256: '0'.repeat(64) } },
  { ...spec, support_domain: { ...spec.support_domain, half_length_m: .59 } },
  { ...spec, support_domain: { ...spec.support_domain, half_width_m: NaN } },
]) assert.throws(() => certifiedHorseSupportDomain(bad, certificate), /invalid or stale/);
assert.throws(() => certifiedHorseSupportDomain(spec, { ...certificate, maximum_support_tilt_deg: 3 }), /invalid or stale/);
assert.throws(() => verifyMeasurements({ ...certificate, half_length_m: .59 }, fixture), /Rounded domain/);
const missingPhase = structuredClone(fixture); missingPhase.frames.pop();
assert.throws(() => verifyMeasurements(certificate, missingPhase), /Expected values/);
const missingFace = structuredClone(fixture.classifier); missingFace.classified.fore_l.meshes[0].sourceFaceIds.pop();
assert.throws(() => verifyCompleteClassifier(raw, JSON.parse(read(reference.path)), JSON.parse(read(ancestry.path)), missingFace), /Complete actual/, 'Removed boundary face rejected by actual GLB classifier');
const missingVertex = structuredClone(fixture.classifier); missingVertex.classified.hind_r.meshes[0].sourceVertexIds.pop();
assert.throws(() => verifyCompleteClassifier(raw, JSON.parse(read(reference.path)), JSON.parse(read(ancestry.path)), missingVertex), /Complete actual/, 'Removed complete surface vertex rejected');
// Same dimensions reach route preflight; the generic call still reads +-1m.
const row = { horse_offset_m: [0, 0, 3], team_half_spacing_m: .65 }, pose = { e: 0, n: 0, yaw: 0, curvature: 0, rootAhead: 1 };
const seen = []; teamSupportAt(row, pose, (e, n) => { seen.push([e, n]); return 0; }, domain);
assert.equal(seen.length, 18); assert(Math.max(...seen.map(p => Math.abs(p[1] + 3))) < .596);
const generic = []; teamSupportAt(row, pose, (e, n) => { generic.push([e, n]); return 0; });
assert.equal(Math.max(...generic.map(p => Math.abs(p[1] + 3))), 1);
console.log('model-bound complete1196vertex/2048face native1154 domain, original rounding, stale/missing/wrong model controls PASS');

// Actual roadway triangle heights survive the existing phone upload release.
// This exercises transformed/indexed geometry and an independent native raycast,
// rather than checking a copy of the barycentric implementation.
{
  const { register } = await import('node:module');
  const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
  register('data:text/javascript,' + encodeURIComponent(`export async function resolve(s,c,n){const v=${JSON.stringify(vendor)};if(s==='three')return{url:v+'three.module.js',shortCircuit:true};if(s.startsWith('three/addons/'))return{url:v+'addons/'+s.slice(13),shortCircuit:true};return n(s,c);}`), import.meta.url);
  const THREE = await import('three');
  const { createRoadTriangleHeight } = await import('../renderers/web/js/road-triangle-height.js');
  const { RELEASE_KEEP, releaseAfterUpload } = await import('../renderers/web/js/upload-release.js');
  assert.deepEqual(RELEASE_KEEP['street-grid'], ['position', 'index']);
  const group = new THREE.Group(); group.name = 'street-grid';
  const make = height => {
    const material = new THREE.MeshBasicMaterial({ polygonOffset: true, polygonOffsetFactor: 0, polygonOffsetUnits: -2 });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(12, 12), material);
    mesh.position.set(1300, height, 3200); mesh.rotation.set(-Math.PI / 2, .17, .003);
    group.add(mesh); return mesh;
  };
  const lower = make(4), upper = make(4.002); group.updateMatrixWorld(true);
  const provider = createRoadTriangleHeight([lower, upper]);
  const ray = new THREE.Raycaster();
  for (const [e, n] of [[1300, -3200], [1304, -3200], [1296, -3200], [1300, -3204], [1300, -3196]]) {
    ray.set(new THREE.Vector3(e, 100, -n), new THREE.Vector3(0, -1, 0));
    const hit = ray.intersectObjects([lower, upper], false)[0];
    assert(hit); assert.equal(hit.object, upper);
    assert(Math.abs(provider.heightAt(e, n) - hit.point.y) < 1e-10);
  }
  assert.equal(provider.heightAt(0, 0), null);
  assert.equal(provider.heightAt(NaN, -3200), null);
  assert.equal(provider.reading().duplicated_xyz_bytes, 0);
  assert(provider.reading().owned_buffer_bytes > 0);
  const positionArray = upper.geometry.getAttribute('position').array, indexArray = upper.geometry.index.array;
  releaseAfterUpload(group);
  for (const mesh of [lower, upper]) {
    for (const attribute of Object.values(mesh.geometry.attributes)) attribute.onUploadCallback();
    mesh.geometry.index.onUploadCallback();
  }
  assert.equal(upper.geometry.getAttribute('position').array, positionArray);
  assert.equal(upper.geometry.index.array, indexArray);
  assert(Number.isFinite(provider.heightAt(1300, -3200)));
  const depthOkay = material => material.polygonOffset && material.polygonOffsetFactor === 0 && material.polygonOffsetUnits < 0;
  assert(depthOkay(upper.material)); upper.material.polygonOffsetFactor = -8;
  assert(!depthOkay(upper.material), 'Historical grazing-wall slope bias rejected structurally; GPU pixel regression remains separate');
  upper.material.polygonOffsetFactor = 0;
  provider.dispose(); assert.equal(provider.heightAt(1300, -3200), null);
  assert.equal(provider.reading().owned_buffer_bytes, 0);
  for (const mesh of [lower, upper]) { mesh.geometry.dispose(); mesh.material.dispose(); }
  console.log('actual transformed/indexed road triangles, overlap maximum, cell boundaries, upload-release aliases, disposal and wrong-slope refusal PASS');
}

// Cold road indexes allocate no buffers until a real finite query; same actual
// transformed Float32 meshes and native raycaster remain the reference.
{
  const THREE = await import('three');
  const { createRoadTriangleHeight, createLazyRoadTriangleHeight } = await import('../renderers/web/js/road-triangle-height.js');
  const mesh = new THREE.Mesh(new THREE.PlaneGeometry(8, 8), new THREE.MeshBasicMaterial());
  mesh.position.set(1300, 4, 3200); mesh.rotation.x = -Math.PI / 2;
  let meshReads = 0;
  const lazy = createLazyRoadTriangleHeight(() => { meshReads++; return [mesh]; });
  assert.equal(meshReads, 0); assert.equal(lazy.reading().owned_buffer_bytes, 0);
  assert.equal(lazy.heightAt(NaN, 0), null); assert.equal(lazy.heightAt(0, Infinity), null);
  assert.equal(meshReads, 0); assert.equal(lazy.reading().owned_buffer_bytes, 0);
  const eager = createRoadTriangleHeight([mesh]);
  for (const [e, n] of [[1300, -3200], [1304, -3200], [1296, -3200], [0, 0]])
    assert.equal(lazy.heightAt(e, n), eager.heightAt(e, n));
  assert.equal(meshReads, 1); assert(lazy.reading().owned_buffer_bytes > 0);
  lazy.dispose(); assert.equal(lazy.heightAt(1300, -3200), null); assert.equal(meshReads, 1);
  const cold = createLazyRoadTriangleHeight(() => { throw Error('disposed cold index resurrected'); });
  cold.dispose(); assert.equal(cold.heightAt(1300, -3200), null); assert.equal(cold.reading().owned_buffer_bytes, 0);
  eager.dispose(); mesh.geometry.dispose(); mesh.material.dispose();
  console.log('lazy exact road index: zero cold/invalid allocation, first finite query native equality, one cache and no post-dispose resurrection PASS');
}

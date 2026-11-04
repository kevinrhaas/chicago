// SPDX-License-Identifier: GPL-3.0-or-later
// Source classifier + optional bounded native hoof-only re-read of the original1154 proof.
// No image decoding, terrain qualification, body-motion changes or new gate registration.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
export const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
export function sourceClassifier(raw, reference, ancestry) {
  const n = raw.readUInt32LE(12), doc = JSON.parse(raw.subarray(20, 20 + n)), bin = raw.subarray(28 + n);
  const read = index => {
    const a = doc.accessors[index], v = doc.bufferViews[a.bufferView];
    assert(!a.sparse, 'Sparse input requires an explicit new classifier reader');
    const width = { SCALAR: 1, VEC3: 3, VEC4: 4 }[a.type];
    const [size, method] = { 5121: [1, 'readUInt8'], 5123: [2, 'readUInt16LE'], 5125: [4, 'readUInt32LE'], 5126: [4, 'readFloatLE'] }[a.componentType];
    assert(width && size);
    return Array.from({ length: a.count }, (_, i) => Array.from({ length: width }, (_, k) => bin[method]((v.byteOffset ?? 0) + (a.byteOffset ?? 0) + i * (v.byteStride ?? width * size) + k * size)));
  };
  const meshes = doc.meshes.map((m, mesh) => {
    assert.equal(m.primitives.length, 1); const p = m.primitives[0];
    const indices = read(p.indices).flat(); assert.equal(indices.length % 3, 0);
    return { mesh, vertexCount: doc.accessors[p.attributes.POSITION].count, joints: read(p.attributes.JOINTS_0), weights: read(p.attributes.WEIGHTS_0), triangles: Array.from({ length: indices.length / 3 }, (_, i) => indices.slice(3 * i, 3 * i + 3)) };
  });
  const classified = {};
  for (const [limb, joint] of Object.entries({ fore_l: 10, fore_r: 15, hind_l: 20, hind_r: 25 })) {
    const contactFaces = new Set(reference.contacts[limb].source_triangle_ids.flatMap(f => ancestry.source_boundary.hoof_refinement.source_face_to_children[f]));
    classified[limb] = [];
    for (const m of meshes) {
      const seeds = new Set(m.joints.flatMap((j, i) => j.some((v, k) => v === joint && m.weights[i][k] > 0) ? [i] : []));
      const faces = m.triangles.flatMap((t, i) => t.some(v => seeds.has(v)) || (m.mesh === 1 && contactFaces.has(i)) ? [i] : []);
      const vertices = [...new Set(faces.flatMap(i => m.triangles[i]))].sort((a, b) => a - b);
      if (vertices.length) classified[limb].push({ mesh: m.mesh, vertexCount: m.vertexCount, sourceVertexIds: vertices, sourceFaceIds: faces });
    }
  }
  return { doc, classified };
}
export function verifyCompleteClassifier(raw, reference, ancestry, expected) {
  const actual = sourceClassifier(raw, reference, ancestry); let vertices = 0, faces = 0;
  for (const [limb, sections] of Object.entries(actual.classified)) {
    assert.deepEqual(sections, expected.classified[limb].meshes.map(({ mesh, vertexCount, sourceVertexIds, sourceFaceIds }) => ({ mesh, vertexCount, sourceVertexIds, sourceFaceIds })), 'Complete actual positive-influence/source-contact classifier');
    for (const s of sections) { vertices += s.sourceVertexIds.length; faces += s.sourceFaceIds.length; }
  }
  assert.equal(vertices, 1196); assert.equal(faces, 2048); return actual;
}
export function verifyMeasurements(certificate, fixture) {
  assert.equal(fixture.asset_sha256, certificate.asset_sha256);
  assert.equal(fixture.accepted_native_proof_sha256, certificate.accepted_native_proof_sha256);
  assert.equal(fixture.accepted_native_domain_bridge_sha256, certificate.accepted_native_domain_bridge_sha256);
  for (const [mode, count] of [['walk', 1025], ['quiet', 129]]) assert.deepEqual(fixture.frames.filter(f => f.mode === mode).map(f => f.index), Array.from({ length: count }, (_, i) => i));
  let halfX = 0, halfZ = 0;
  for (const f of fixture.frames) {
    assert(f.min_xyz_m.every(Number.isFinite) && f.max_xyz_m.every(Number.isFinite));
    const x = Math.max(...[f.min_xyz_m[0], f.max_xyz_m[0]].map(Math.abs)), z = Math.max(...[f.min_xyz_m[2], f.max_xyz_m[2]].map(Math.abs));
    const y = Math.max(Math.abs(f.min_xyz_m[1]), Math.abs(f.max_xyz_m[1])), theta = 2 * Math.PI / 180;
    const pad = y * Math.sin(theta) + Math.hypot(x, z) * (1 - Math.cos(theta)) + 1e-5;
    assert(Math.abs(pad - f.tilt_and_numerical_pad_m) < 1e-15);
    halfX = Math.max(halfX, x + pad); halfZ = Math.max(halfZ, z + pad);
  }
  assert.equal(halfX, certificate.measured_required_centered_half_width_m);
  assert.equal(halfZ, certificate.measured_required_centered_half_length_m);
  assert(certificate.half_width_m >= halfX && certificate.half_length_m >= halfZ, 'Rounded domain must contain every original finite native/F32 pose and tilt margin');
  return { halfX, halfZ };
}

async function nativeChunk() {
  const { register } = await import('node:module');
  register(new URL('./horse_support_vendor_loader.mjs', import.meta.url), import.meta.url);
  const T = await import('three'), { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
  const { clone } = await import('three/addons/utils/SkeletonUtils.js');
  const { MeshoptDecoder } = await import('three/addons/libs/meshopt_decoder.module.js'); await MeshoptDecoder.ready;
  const root = new URL('../', import.meta.url), readJSON = path => JSON.parse(readFileSync(new URL(path, root)));
  const cert = readJSON('data/transport/driven/current26-hoof-support-domain.json'), fixtureBytes = readFileSync(new URL(cert.native_measurement_fixture, root));
  assert.equal(sha256(fixtureBytes), cert.native_measurement_fixture_sha256); const fixture = JSON.parse(fixtureBytes); verifyMeasurements(cert, fixture);
  const raw = readFileSync(new URL(cert.asset_file, root)); assert.equal(sha256(raw), cert.asset_sha256);
  const ref = fixture.classifier.originalReference, anc = fixture.classifier.physicalAncestry;
  const refBytes = readFileSync(new URL(ref.path, root)), ancBytes = readFileSync(new URL(anc.path, root));
  assert.equal(sha256(refBytes), ref.sha256); assert.equal(sha256(ancBytes), anc.sha256);
  verifyCompleteClassifier(raw, JSON.parse(refBytes), JSON.parse(ancBytes), fixture.classifier);
  const doc = JSON.parse(raw.subarray(20, 20 + raw.readUInt32LE(12)));
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  loader.register(() => ({ name: 'CPU_POSE_ONLY_MATERIAL_ADAPTER', loadMaterial: async i => new T.MeshBasicMaterial({ side: doc.materials[i].doubleSided ? T.DoubleSide : T.FrontSide }) }));
  const parsed = await loader.parseAsync(raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength), ''); const scene = clone(parsed.scene);
  scene.updateMatrixWorld(true); assert.equal(scene.position.length(), 0); assert.deepEqual(scene.scale.toArray(), [1, 1, 1]); assert.deepEqual(scene.quaternion.toArray(), [0, 0, 0, 1]);
  const originals = [], clones = []; parsed.scene.traverse(o => originals.push(o)); scene.traverse(o => clones.push(o));
  const meshes = doc.meshes.map((_, mi) => clones[originals.findIndex(o => o.isSkinnedMesh && parsed.parser.associations.get(o)?.meshes === mi)]);
  const args = process.argv.slice(2), start = Number(args[args.indexOf('--start') + 1]), count = Number(args[args.indexOf('--count') + 1]);
  assert(args.includes('--start') && args.includes('--count') && Number.isInteger(start) && start >= 0 && Number.isInteger(count) && count > 0 && count <= 32);
  const frames = fixture.frames.slice(start, start + count); assert.equal(frames.length, count); let mixer, action, mode;
  for (const f of frames) {
    if (mode !== f.mode) {
      mixer?.stopAllAction(); mode = f.mode;
      const clipName = mode === 'walk' ? 'reconstructed_bare_current26_inplace_careful_walk_cubic129_v1' : fixture.quiet_clip;
      const clip = parsed.animations.find(a => a.name === clipName); assert(clip, 'Actual named original clip');
      mixer = new T.AnimationMixer(scene); action = mixer.clipAction(clip).setLoop(T.LoopOnce, 1); action.clampWhenFinished = true;
    }
    action.reset().play(); mixer.setTime(f.time_s); scene.updateMatrixWorld(true); for (const mesh of meshes) mesh.skeleton.update();
    const min = [Infinity, Infinity, Infinity], max = [-Infinity, -Infinity, -Infinity]; let rows = 0;
    for (const limb of Object.values(fixture.classifier.classified)) for (const section of limb.meshes) for (const i of section.sourceVertexIds) {
      const m = meshes[section.mesh], P = m.geometry.attributes.position, J = m.geometry.attributes.skinIndex, W = m.geometry.attributes.skinWeight;
      const p = new T.Vector3().fromBufferAttribute(P, i).applyMatrix4(m.bindMatrix), q = new T.Vector3(), B = m.skeleton.boneMatrices;
      for (let k = 0; k < 4; k++) { const j = J.array[i * 4 + k] * 16, w = W.array[i * 4 + k]; q.x += w * (B[j] * p.x + B[j + 4] * p.y + B[j + 8] * p.z + B[j + 12]); q.y += w * (B[j + 1] * p.x + B[j + 5] * p.y + B[j + 9] * p.z + B[j + 13]); q.z += w * (B[j + 2] * p.x + B[j + 6] * p.y + B[j + 10] * p.z + B[j + 14]); }
      const native = m.getVertexPosition(i, new T.Vector3()).applyMatrix4(m.matrixWorld);
      q.applyMatrix4(m.bindMatrixInverse).applyMatrix4(m.matrixWorld);
      for (const v of [native, q]) for (let k = 0; k < 3; k++) { const value = v.getComponent(k); assert(Number.isFinite(value)); min[k] = Math.min(min[k], value); max[k] = Math.max(max[k], value); }
      rows++;
    }
    assert.equal(rows, 1196);
    for (let k = 0; k < 3; k++) { assert(Math.abs(min[k] - f.min_xyz_m[k]) < 1e-12, 'Native/F32 finite minimum matches original measured proof'); assert(Math.abs(max[k] - f.max_xyz_m[k]) < 1e-12, 'Native/F32 finite maximum matches original measured proof'); }
  }
  console.log(`Actual native hoof-only re-read PASS rows ${start}..${start + count - 1}; image/terrain/world acceptance UNRUN`);
}
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  assert(process.argv.includes('--native'), 'Use --native --start N --count 1..32 under the qualified owner lane'); await nativeChunk();
}

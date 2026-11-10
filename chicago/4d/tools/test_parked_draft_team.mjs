// SPDX-License-Identifier: GPL-3.0-or-later
// Actual portable meshes/skin/quiet clip and Three Mixer. Texture connections
// alone are stripped for Node image decoding; no WebGL/image/world acceptance.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';
import { createHash } from 'node:crypto';
const root = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', root).href;
register(`data:text/javascript,${encodeURIComponent(`export async function resolve(s,c,n){
if(s==='three')return{url:${JSON.stringify(vendor+'three.module.js')},shortCircuit:true};
if(s.startsWith('three/addons/'))return{url:${JSON.stringify(vendor)}+'addons/'+s.slice(13),shortCircuit:true};return n(s,c);}`)}`);
const THREE = await import('three');
const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
const { MeshoptDecoder } = await import('three/addons/libs/meshopt_decoder.module.js');
const { createParkedDraftTeam } = await import('../renderers/web/js/parked-draft-team.js');
const { createParkedTransport } = await import('../renderers/web/js/parked-transport.js');
const { verifyCompleteClassifier } = await import('./measure_horse_support_domain.mjs');
await MeshoptDecoder.ready;
const read = p => fs.readFileSync(new URL(p, root));
const json = p => JSON.parse(read(p));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const config = json('data/transport/parked/placements.json');
const row = config.scenes['1904'].find(r => r.id === 'prairie_parked_studebaker_brougham');
const spec = row.stationary_team;
const output = process.argv.includes('--output') ? process.argv[process.argv.indexOf('--output') + 1] : null;
if (output) assert(!fs.existsSync(output), 'Preserve earlier receipts; choose a fresh output');
const report = { scope: 'Actual hash-bound geometry/rig/Three Mixer on a flat synthetic support plane; texture links removed only for Node decoding. No image, actual-street, full surface-intersection, boarding or photographic acceptance.',
  source_inputs: {}, samples: [], passed: false };
const nativeParse = GLTFLoader.prototype.parseAsync, previousFetch = globalThis.fetch;
const nativeVertex = THREE.SkinnedMesh.prototype.getVertexPosition;
let skinVertexReads = 0;
THREE.SkinnedMesh.prototype.getVertexPosition = function(index, target) {
  skinVertexReads++; return nativeVertex.call(this, index, target);
};
const parsed = [];
function geometryOnly(arrayBuffer) {
  const bytes = Buffer.from(arrayBuffer), n = bytes.readUInt32LE(12);
  const doc = JSON.parse(bytes.subarray(20, 20 + n));
  const strip = object => { for (const key of Object.keys(object)) {
    if (/Texture$/.test(key)) delete object[key];
    else if (object[key] && typeof object[key] === 'object') strip(object[key]);
  } };
  for (const material of doc.materials ?? []) strip(material);
  delete doc.images; delete doc.textures;
  const plain = Buffer.from(JSON.stringify(doc)), encoded = Buffer.concat([plain, Buffer.alloc(-plain.length & 3, 32)]);
  const bin = bytes.subarray(28 + n), out = Buffer.alloc(28 + encoded.length + bin.length);
  out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
  out.writeUInt32LE(encoded.length, 12); out.writeUInt32LE(0x4e4f534a, 16); encoded.copy(out, 20);
  out.writeUInt32LE(bin.length, 20 + encoded.length); out.writeUInt32LE(0x004e4942, 24 + encoded.length); bin.copy(out, 28 + encoded.length);
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
}
GLTFLoader.prototype.parseAsync = async function(bytes, base) {
  const asset = await nativeParse.call(this, geometryOnly(bytes), base);
  parsed.push(asset); return asset;
};
globalThis.fetch = async url => {
  const bytes = fs.readFileSync(new URL(String(url)));
  return { ok: true, status: 200, json: async () => JSON.parse(bytes),
    arrayBuffer: async () => bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.length) };
};
let team = null;
try {
  for (const [kind, binding] of Object.entries(spec.vehicles)) {
    const bytes = read('renderers/web/' + binding.file); assert.equal(sha(bytes), binding.sha256);
    report.source_inputs[kind] = { file: binding.file, sha256: binding.sha256 };
  }
  const horseRaw = read('renderers/web/' + spec.horse.file);
  assert.equal(sha(horseRaw), spec.horse.sha256);
  const certificate = json('data/' + spec.horse.support_domain.certificate_file);
  const fixtureBytes = read(certificate.native_measurement_fixture);
  assert.equal(sha(fixtureBytes), certificate.native_measurement_fixture_sha256);
  const fixture = JSON.parse(fixtureBytes), refs = fixture.classifier;
  const contactsBytes = read('data/' + spec.horse.contact_file);
  assert.equal(sha(contactsBytes), spec.horse.contact_sha256);
  const contacts = JSON.parse(contactsBytes);
  assert.deepEqual(contacts.feet, Object.fromEntries(Object.entries(refs.classified).map(([limb, data]) => [limb, data.meshes[0].sourceVertexIds])),
    'Every original classifier vertex is retained in the runtime fitting contract');
  assert.equal(contacts.source_classifier.sha256, certificate.native_measurement_fixture_sha256);
  const reference = read(refs.originalReference.path), ancestry = read(refs.physicalAncestry.path);
  assert.equal(sha(reference), refs.originalReference.sha256); assert.equal(sha(ancestry), refs.physicalAncestry.sha256);
  verifyCompleteClassifier(horseRaw, JSON.parse(reference), JSON.parse(ancestry), refs);
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const near = await loader.parseAsync(read('renderers/web/' + spec.vehicles.near.file), '');
  const mid = await loader.parseAsync(read('renderers/web/' + spec.vehicles.mid.file), '');
  const frame = new THREE.Group(); frame.position.set(row.at_local_enu_m[0], 5, -row.at_local_enu_m[1]);
  frame.rotation.y = Math.PI - row.bearing_deg * Math.PI / 180;
  frame.add(near.scene, mid.scene); frame.updateWorldMatrix(true, true);
  const originalNearParent = near.scene.getObjectByName(spec.pole_node).parent;
  const originalMidParent = mid.scene.getObjectByName(spec.pole_node).parent;
  const initialReads = skinVertexReads;
  team = await createParkedDraftTeam({ row, frame, vehicle: near.scene, midVehicle: mid.scene,
    dataBase: new URL('data/', root), moduleBase: new URL('renderers/web/', root), heightAt: () => 5 });
  report.initial_runtime_skin_vertex_reads = skinVertexReads - initialReads;
  assert.equal(team.horses.length, 2);
  const template = parsed.find(a => a.parser.json.skins?.[0]?.joints?.length === 26 && a.animations.length > 0);
  assert(template, 'Actual current26 source was parsed');
  const sourceMeshes = [];
  template.scene.traverse(mesh => {
    const association = template.parser.associations.get(mesh);
    if (mesh.isSkinnedMesh && Number.isInteger(association?.meshes)) sourceMeshes[association.meshes] = mesh;
  });
  const quiet = fixture.frames.filter(f => f.mode === 'quiet');
  const quietClip = template.animations.find(clip => clip.name === spec.horse.idle_clip);
  assert.equal(quiet.length, 129); assert(quietClip);
  assert.equal(quiet[0].time_s, 0); assert.equal(quiet.at(-1).time_s, quietClip.duration);
  report.quiet_duration_s = quietClip.duration;
  report.independent_phase_fractions = spec.idle_phase_fractions;
  const binding = json('data/' + spec.hitch.bindings_file).vehicle_bindings[spec.hitch.vehicle_binding];
  for (const sample of quiet) {
    const horseTimes = team.horses.map((h, i) => {
      const time = sample.time_s + spec.idle_phase_fractions[i] * quietClip.duration;
      h.mixer.setTime(time); return time;
    });
    const beforeReads = skinVertexReads;
    const snapshot = team.update(0);
    const runtimeReads = skinVertexReads - beforeReads;
    const nearTip = near.scene.getObjectByName(binding.tip_node).getWorldPosition(new THREE.Vector3());
    const midTip = mid.scene.getObjectByName(binding.tip_node).getWorldPosition(new THREE.Vector3());
    const lodTipGap = nearTip.distanceTo(midTip);
    assert(lodTipGap <= 1e-6, `Genuine near/mid pole endpoints agree within one micrometre: ${lodTipGap}`);
    assert(snapshot.valid); assert(snapshot.pole_to_yoke_connection_m <= .12);
    assert.equal(snapshot.actual_palm_surface_endpoints, false);
    assert.equal(snapshot.instance_counts.unit_rein, 0); assert.equal(snapshot.driver_present, false);
    const feet = [];
    report.samples.push({ time_s: sample.time_s, independent_horse_times_s: horseTimes,
      runtime_skin_vertex_reads: runtimeReads, near_mid_pole_tip_gap_m: lodTipGap, snapshot, minimum_gap_by_hoof: feet });
    for (const h of team.horses) {
      const cloneMeshes = [];
      h.root.traverse(mesh => { if (mesh.isSkinnedMesh) cloneMeshes.push(mesh); });
      const minimum = {};
      feet.push(minimum);
      for (const [limb, contact] of Object.entries(refs.classified)) {
        let value = Infinity;
        for (const section of contact.meshes) {
          const mesh = cloneMeshes.find(m => m.geometry === sourceMeshes[section.mesh]?.geometry);
          assert(mesh, 'The source complete-hoof classifier resolves on the actual shared geometry');
          for (const id of section.sourceVertexIds) value = Math.min(value,
            mesh.getVertexPosition(id, new THREE.Vector3()).applyMatrix4(mesh.matrixWorld).y - 5);
        }
        minimum[limb] = value;
        assert(value >= contacts.limits.minimum_clearance_m, `Actual classified ${limb} foot does not penetrate the synthetic ground: ${value}`);
        assert(value <= contacts.limits.maximum_per_hoof_minimum_gap_m,
          `Actual ${limb} foot reaches the original standing contact bound: ${value}`);
      }
    }
  }
  const before = team.horses[0].mixer.time;
  team.update(.05, { paused: true }); assert.equal(team.horses[0].mixer.time, before);
  team.update(.05, { reducedMotion: true }); assert.equal(team.horses[0].mixer.time, before);
  team.dispose(); team.dispose();
  assert.equal(near.scene.getObjectByName(spec.pole_node).parent, originalNearParent);
  assert.equal(mid.scene.getObjectByName(spec.pole_node).parent, originalMidParent);
  assert(!frame.getObjectByName(`${row.id}:stationary-team`));
  // The actual parked adapter adopts the same row, keeps body LOD batching,
  // releases animal leases on Light/hidden and reacquires without duplicates.
  const problems = [], camera = new THREE.PerspectiveCamera(55, 1.6, .1, 5000);
  camera.position.set(row.at_local_enu_m[0], 7, -row.at_local_enu_m[1] + 8);
  const layer = await createParkedTransport({ dataBase: new URL('data/', root), sceneId: '1904',
    terrain: { surfaceHeight: () => 5 }, groundHeight: () => 5, detail: 'balanced',
    stationaryTeams: true, getDrawingBufferHeight: () => 800, problems });
  try {
    assert.equal(layer.instances.length, 1);
    const instance = layer.instances[0];
    layer.update(camera); await layer.ready(); layer.update(camera);
    assert(instance.team, problems.join('\n')); assert.equal(layer.pending, 0);
    assert.match(instance.card.sidecar.attributes.parked.value, /pair of horses/);
    assert.equal(instance.draw_batches, 10, 'Eight preserved body batches and the two independent original pole primitives');
    assert.deepEqual(instance.group.position.toArray(), [1397.9, 5, 3240]);
    assert.equal(instance.row.belongs_to, null, 'No household ownership is silently assigned');
    await layer.setTier('light'); assert.equal(instance.team, null);
    layer.update(camera); assert.equal(instance.group.visible, false);
    await layer.setTier('full'); layer.update(camera); await layer.ready();
    assert(instance.team, problems.join('\n')); assert.equal(instance.team.horses.length, 2);
    layer.setShown(false); assert.equal(instance.team, null);
    layer.setShown(true); await layer.ready(); layer.update(camera);
    assert(instance.team, problems.join('\n')); assert.equal(layer.instances.length, 1);
    assert.equal(problems.length, 0, problems.join('\n'));
    report.adapter = { actual_row: instance.row.id, draw_batches: instance.draw_batches,
      stationary_team: instance.team.snapshot(), Light_and_hidden_release: true, rows: layer.instances.length };
  } finally { layer.dispose(); layer.dispose(); }
  // A visible revision can be replaced while its real horse fetch is still
  // pending. ready() must drain the replacement, not only its stale predecessor.
  const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };
  const started = [deferred(), deferred()], releases = [deferred(), deferred()];
  const fileFetch = globalThis.fetch; let horseFetches = 0, racing = null;
  globalThis.fetch = async url => {
    if (String(url) === new URL('renderers/web/' + spec.horse.file, root).href) {
      const request = horseFetches++;
      assert(request < 2, 'Exactly one replacement horse acquisition is scheduled');
      started[request].resolve(); await releases[request].promise;
    }
    return fileFetch(url);
  };
  try {
    const raceProblems = [];
    racing = await createParkedTransport({ dataBase: new URL('data/', root), sceneId: '1904',
      terrain: { surfaceHeight: () => 5 }, groundHeight: () => 5, detail: 'balanced',
      stationaryTeams: true, getDrawingBufferHeight: () => 800, problems: raceProblems });
    racing.update(camera); await started[0].promise;
    assert.equal(racing.pending, 1); racing.setShown(false); racing.setShown(true);
    let readySettled = false;
    const drained = racing.ready().then(() => { readySettled = true; });
    releases[0].resolve(); await started[1].promise;
    await new Promise(resolve => setImmediate(resolve));
    assert.equal(readySettled, false, 'ready() waits for the replacement created after a stale revision retires');
    assert.equal(racing.pending, 1); assert.equal(racing.instances[0].team, null);
    releases[1].resolve(); await drained;
    assert.equal(racing.pending, 0); assert(racing.instances[0].team, raceProblems.join('\n'));
    assert.equal(horseFetches, 2); assert.equal(racing.instances.length, 1);
    assert.deepEqual(raceProblems, []);
    report.deferred_hide_show = { horse_fetches: horseFetches, pending_after_ready: racing.pending,
      replacement_ready_waited: true, rows: racing.instances.length };
  } finally {
    for (const release of releases) release.resolve();
    racing?.dispose(); await racing?.ready(); globalThis.fetch = fileFetch;
  }
  report.passed = true;
  console.log('Parked draft team PASS — actual current delivery near/mid, existing horse/tack, all 129 quiet sample times with independent phases, original complete-hoof classifier and unoccupied/restore lifecycle; rendered appearance and street placement UNRUN');
} catch (error) { report.error = error.message; throw error; }
finally {
  team?.dispose(); GLTFLoader.prototype.parseAsync = nativeParse;
  THREE.SkinnedMesh.prototype.getVertexPosition = nativeVertex; globalThis.fetch = previousFetch;
  if (output) fs.writeFileSync(output, JSON.stringify(report, null, 2) + '\n');
}

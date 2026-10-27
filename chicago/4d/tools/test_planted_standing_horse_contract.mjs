// Contract/lifecycle unit only; not loaded skin, contact, bounds or visual proof.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { register } from 'node:module';
import { standingHorseCard } from '../renderers/web/js/standing-horse-card.js';
import { validatePlantedStandingHeader, createPlantedStandingHorseIdle, PLANTED_SHA, PLANTED_CLIP }
  from '../renderers/web/js/standing-horse-planted-idle.js';
const spec = JSON.parse(readFileSync(new URL('../data/transport/parked/horse-sevket-sidecar.json', import.meta.url)));
const buffer = readFileSync(new URL('../renderers/web/' + spec.runtime_asset.file, import.meta.url));
assert.equal(createHash('sha256').update(buffer).digest('hex'), PLANTED_SHA);
const bytes = buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
const header = validatePlantedStandingHeader(bytes, spec);
assert.throws(() => validatePlantedStandingHeader(bytes, { ...spec, runtime_scale_m_per_unit: .36440688373115426 }), /unit scale/);
assert.throws(() => validatePlantedStandingHeader(bytes, { ...spec, runtime_origin_m: [.001, 0, 0] }), /unit scale/);
assert.throws(() => validatePlantedStandingHeader(bytes.slice(0, -4), spec), /byte budget/);
function altered(change) {
  const json = structuredClone(header); change(json);
  const encoded = new TextEncoder().encode(JSON.stringify(json)), copy = new ArrayBuffer(bytes.byteLength), view = new DataView(copy);
  view.setUint32(0, 0x46546c67, true); view.setUint32(4, 2, true); view.setUint32(8, copy.byteLength, true);
  view.setUint32(12, encoded.length, true); view.setUint32(16, 0x4e4f534a, true);
  new Uint8Array(copy, 20, encoded.length).set(encoded);
  return copy; // Synthetic metadata guard control; never passed off as actual GLB.
}
assert.throws(() => validatePlantedStandingHeader(altered(j => j.skins[0].joints.pop()), spec), /rig/);
assert.throws(() => validatePlantedStandingHeader(altered(j => j.animations.push(structuredClone(j.animations[0]))), spec), /only planted/);
assert.throws(() => validatePlantedStandingHeader(altered(j => { j.animations[0].channels[0].target.node = 0; }), spec), /unapproved/);
assert.throws(() => validatePlantedStandingHeader(altered(j => { j.animations[0].channels[1].target.node = 3; }), spec), /unapproved/);
assert.throws(() => validatePlantedStandingHeader(altered(j => { j.animations[0].samplers[0].interpolation = 'STEP'; }), spec), /key\/time/);
assert.throws(() => validatePlantedStandingHeader(altered(j => { j.buffers[0].uri = 'unreviewed.bin'; }), spec), /embedded/);
assert.throws(() => validatePlantedStandingHeader(altered(j => { delete j.asset.extras.chicago4d_anatomy_master_v2; }), spec), /anatomy parent/);

// Exact target identities with a deliberately tiny mixer mock test host-clock
// ownership, hold and disposal; physical pose qualification uses real THREE.
const bones = header.skins[0].joints.map(i => ({ name: header.nodes[i].name }));
const byName = new Map(bones.map(b => [b.name, b]));
const meshes = Array.from({ length: 3 }, () => ({ isMesh: true, isSkinnedMesh: true, skeleton: { bones } }));
const root = { userData: {}, traverse: fn => meshes.forEach(fn) };
const times = Float32Array.from({ length: 65 }, (_, i) => i * 12 / 64);
const clip = { name: PLANTED_CLIP, duration: 12, tracks: header.animations[0].channels.map(c => ({
  name: `${header.nodes[c.target.node].name}.${c.target.path === 'translation' ? 'position' : 'quaternion'}`, times,
})) };
let mixer;
class Mixer {
  constructor() { mixer = this; this.advanced = 0; this.stops = 0; this.uncaches = 0; }
  clipAction() { return { setLoop() {}, play() {} }; }
  setTime(t) { assert.equal(t, 0); }
  update(dt) { this.advanced += dt; }
  stopAllAction() { this.stops++; }
  uncacheRoot(r) { assert.equal(r, root); this.uncaches++; }
}
const T = { AnimationMixer: Mixer, LoopRepeat: 2201, PropertyBinding: {
  parseTrackName(name) { const [nodeName, propertyName] = name.split('.'); return { nodeName, propertyName }; },
  findNode(r, name) { assert.equal(r, root); return byName.get(name); },
} };
const args = { T, root, clips: [clip], verifiedDerivedSha256: PLANTED_SHA, instanceId: 'western_hotel_yard_standing_horse_01' };
const player = createPlantedStandingHorseIdle(args);
assert.throws(() => createPlantedStandingHorseIdle(args), /already has/);
player.update(3); const advanced = mixer.advanced; assert(advanced > 0);
for (const hold of [{ paused: true }, { reducedMotion: true }, { visible: false }]) {
  player.update(1, hold); assert.equal(mixer.advanced, advanced);
}
assert.throws(() => player.update(-1), /host delta/);
assert.equal(player.status.weight_shift, true); assert.equal(player.status.head_tail_composed, false);
assert.equal(player.status.walk, false); assert.equal(player.status.trot, false);
player.dispose(); player.dispose(); player.update(1);
assert.equal(mixer.advanced, advanced); assert.equal(mixer.stops, 1); assert.equal(mixer.uncaches, 1);
assert.equal(player.status.mixer_count, 0);

// Modern asset credit never becomes an historically attested animal attribute.
const row = JSON.parse(readFileSync(new URL('../data/transport/parked/standing-horses.json', import.meta.url))).scenes['1835'][0];
const card = standingHorseCard(row, spec).sidecar;
assert(card.change_note.includes('reconstructed, unidentified horse'));
assert(card.change_note.includes(spec.source.credit));
assert(card.citations.some(c => c.source_id === spec.source.id && c.url === spec.source.original_url));
assert(card.citations.every(c => c.citation && c.url));
const missingCredit = structuredClone(spec); delete missingCredit.citation_records[spec.source.id];
assert.throws(() => standingHorseCard(row, missingCredit), /citation does not resolve/);
for (const value of Object.values(card.attributes)) assert(!(value.sources ?? []).includes(spec.source.id));

// Existing bounded yard snapshot helper: actual Two-triangle BatchedMesh,
// then simulated normal GPU upload-release. No renderer/context is created.
const vendor = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s,c,next){if(s==='three')return{url:'${vendor}',shortCircuit:true};return next(s,c);}`)}`, import.meta.url);
const RealT = await import('three');
const { retainYardStaticSupport } = await import('../renderers/web/js/yard-static-support.js');
const geometry = new RealT.BufferGeometry();
geometry.setAttribute('position', new RealT.Float32BufferAttribute([0,1,0,1,1.1,0,1,1.3,-1,0,1.2,-1],3));
geometry.setIndex([0,1,2,0,2,3]);
const yardMesh = new RealT.BatchedMesh(1,4,6,new RealT.MeshBasicMaterial({side:RealT.DoubleSide}));
yardMesh.addInstance(yardMesh.addGeometry(geometry)); yardMesh.name='yard-worn_earth';
const yardGroup = new RealT.Group(); yardGroup.add(yardMesh); yardGroup.updateMatrixWorld(true);
const region={id:'test',record_id:'yard',bounds_enu_m:[[-.05,-.05],[1.05,1.05]]};
const problems=[], cache=retainYardStaticSupport(yardGroup,[region],problems);
assert.equal(problems.length,0); assert.equal(cache.census.triangles,2); assert.equal(cache.census.bytes,144);
const ray = new RealT.Raycaster(); ray.set(new RealT.Vector3(.5,5,-.5),new RealT.Vector3(0,-1,0));
const actualY = ray.intersectObject(yardMesh,false)[0].point.y;
assert(Math.abs(cache.heightAt(.5,.5,'yard','test')-actualY)<1e-12);
yardMesh.geometry.getAttribute('position').array=null;
yardMesh.geometry.index.array=new yardMesh.geometry.index.array.constructor(0);
assert(Math.abs(cache.heightAt(.5,.5,'yard','test')-actualY)<1e-12);
assert.equal(cache.heightAt(.5,.5,'other','test'),null); assert.equal(cache.heightAt(2,2,'yard','test'),null);
cache.dispose(); assert.equal(cache.census.bytes,0); assert.equal(cache.heightAt(.5,.5,'yard','test'),null);
const capProblems=[]; const capped=retainYardStaticSupport(yardGroup,[region,{...region,id:'second'}],capProblems);
assert.equal(capProblems.length,1); assert.equal(capped.census.bytes,0);
const lateProblems=[]; const late=retainYardStaticSupport(yardGroup,[region],lateProblems);
assert.equal(lateProblems.length,1); assert.equal(late.census.bytes,0);
yardMesh.dispose(); geometry.dispose(); yardMesh.material.dispose();
console.log('STANDING INTEGRATION UNIT PASS — modern-credit separation and bounded144B actual-yard fixture snapshot survives upload release; late/cap refusals and disposal. No actual town/render/photo proof.');

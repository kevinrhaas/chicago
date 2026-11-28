#!/usr/bin/env node
// T-3747: season/detail preparation can overlap. A new forest must not consume
// another forest's templates or overwrite its live instance records.
import assert from 'node:assert/strict';
import {register} from 'node:module';
const vendor=new URL('../renderers/web/vendor/three-0.185.1/',import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s,c,next) {
  if(s==='three')return {url:'${vendor}three.module.js',shortCircuit:true};
  if(s.startsWith('three/addons/'))return {url:'${vendor}addons/'+s.slice(13),shortCircuit:true};
  return next(s,c);
}`)}`,import.meta.url);
const THREE=await import('three');
const {TreeInstances}=await import('../renderers/web/js/tree-instances.js');
const builder=new TreeInstances({level:'full',variants:()=>2});
for(const [i,id] of ['ulmus_americana','quercus_alba'].entries()) {
  for(let j=0;j<3;j++)builder.add({speciesId:id,arch:id,form:'open',h:[6,6]},i*12+j*3,0,0);
}
const woodMat=new THREE.MeshStandardMaterial(),leafMat=woodMat.clone();
const checkpoint=()=>new Promise(resolve=>setImmediate(resolve));
const options={woodMat,leafMat,checkpoint};
const rigs=[];
try {
  const [summer,winter]=await Promise.all([
    builder.build({...options,season:{leafCover:1}}),
    builder.build({...options,season:{leafCover:0}}),
  ]);
  rigs.push(summer,winter);
  const eye=new THREE.Vector3(5,1.7,4);
  for(const rig of rigs){rig.update(eye);rig.settle();assert.equal(rig.stats.stems,6);}
  const support=rig=>{
    let area=0;const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
    for(const batch of Object.values(rig.batches)) {
      const g=batch.leaves.geometry,p=g.attributes.position,ix=g.index;
      for(let i=0;i<ix.count;i+=3){
        a.fromBufferAttribute(p,ix.getX(i));b.fromBufferAttribute(p,ix.getX(i+1));c.fromBufferAttribute(p,ix.getX(i+2));
        area+=b.sub(a).cross(c.sub(a)).length()/2;
      }
    }
    return area;
  };
  assert(support(summer)>0,'summer retains its leaves');
  assert.equal(support(winter),0,'winter has no leaf support, including empty batch slots');
  const before=summer.stats.triangles;
  winter.dispose();rigs.splice(rigs.indexOf(winter),1);
  const spring=await builder.build({...options,season:{leafCover:.55,leafScale:.45}});rigs.push(spring);
  summer.update(eye);summer.settle();
  assert.equal(summer.stats.triangles,before,'rebuilding and retiring another forest cannot change the live one');
  assert(support(summer)>0);
  // Exercise the actual upload-release callbacks and cached per-LOD bounds.
  // A later LOD/instance update must not need the discarded vertex arrays.
  for(const batch of Object.values(summer.batches))for(const part of Object.values(batch)) {
    const g=part.geometry;
    assert(g.userData.uploadReleased,'Full woodland uses the established release path');
    for(const attr of [...Object.values(g.attributes),g.index])attr.onUploadCallback();
    assert.equal(g.attributes.position.array,null);
    assert.equal(g.index.array.length,0);
    for(let id=0;id<part._geometryCount;id++) {
      part.getBoundingBoxAt(id,new THREE.Box3());
      part.getBoundingSphereAt(id,new THREE.Sphere());
    }
  }
  summer.update(new THREE.Vector3(400,1.7,0));summer.settle();
  summer.update(eye);summer.settle();
  assert.equal(summer.stats.triangles,before,'released arrays are not needed for returning to the close LOD');
  // The upstream Great Fire API must mutate this snapshot's live slots,
  // including after geometry release and another seasonal forest was built.
  const visible = (role, test) => {
    const found = new Set(), m = new THREE.Matrix4();
    for (const set of Object.values(summer.batches)) {
      const batch = set[role];
      for (const [i, slot] of batch._instanceInfo.entries()) {
        if (!slot.active || !batch.getVisibleAt(i)) continue;
        batch.getMatrixAt(i, m);
        if (test(m.elements[12], -m.elements[14])) found.add(m.elements[12]);
      }
    }
    return found.size;
  };
  const burnt = e => e < 10;
  assert.equal(summer.setBare(burnt), 3, 'the fire marks this live forest, not the reused planner');
  summer.update(new THREE.Vector3(400,1.7,0)); summer.settle();
  summer.update(eye); summer.settle();
  assert.equal(visible('wood', burnt), 3, 'scorched wood survives LOD changes after CPU release');
  assert.equal(visible('leaves', burnt), 0, 'scorched stems cannot regain leaves during LOD changes');
  assert.equal(spring.stats.bare ?? 0, 0, 'another live seasonal forest stays independent');
  assert.equal(summer.setBare(null), 3);
  assert.equal(visible('leaves', burnt), 3, 'leaving the fire restores the live summer leaves');
  console.log('PASS integrated fire/tree ownership: scorched wood and hidden leaves survive released arrays and LOD, with independent forests and exact restore');
  console.log('PASS overlapping tree rebuilds: independent summer/winter templates, stable live instances after another rebuild/disposal');
  console.log('PASS Full woodland upload release: cached LOD bounds and instance updates survive discarded CPU triangles');
} finally {
  for(const rig of rigs)rig.dispose();woodMat.dispose();leafMat.dispose();
}

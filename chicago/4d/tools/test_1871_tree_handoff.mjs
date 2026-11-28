#!/usr/bin/env node
// T-3760: current-data preservation and the context-to-grown
// renderer contract. Only image decoding is stubbed; all tree geometry is real.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';
const vendor=new URL('../renderers/web/vendor/three-0.185.1/',import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s,c,next) {
  if(s==='three')return {url:'${vendor}three.module.js',shortCircuit:true};
  if(s.startsWith('three/addons/'))return {url:'${vendor}addons/'+s.slice(13),shortCircuit:true};
  return next(s,c);
}`)}`,import.meta.url);
const THREE=await import('three');
const {TreeInstances}=await import('../renderers/web/js/tree-instances.js');
const {createStreetTrees}=await import('../renderers/web/js/street-trees.js');
const {createConfidenceView}=await import('../renderers/web/js/confidence.js');
const {cityContextCard}=await import('../renderers/web/js/city-context.js');
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
const doc=read('data/context/1871.json');
const streetDoc=read('data/street_trees/1871.json');
assert.equal(doc.trees.length,3543,'the current context planting is preserved');
assert.equal(streetDoc.trees.length,6693,'the current street planting is preserved');
assert.equal(streetDoc.withdrawn?.length ?? 0,0,'superseded prototype deletions are absent');
for (const [id,e,n] of [['tree.01161',301.1,811.53],['tree.01162',292.07,811.43]])
  assert(streetDoc.trees.some(t=>t.id===id&&t.e===e&&t.n===n),'reassigned valid tree IDs must not be withdrawn');
assert(!doc.trees.some(t=>t.id==='tree1871_8387'),'the old pumping-works tree is not reintroduced');
const row=doc.trees.find(r=>r.id==='tree1871_9715');assert(row,'the current generic context probe remains in data');
const r={id:row.id,e:row.e,n:row.n,h:row.height_m,isTree:true};
const id=`context:1871:${r.id}`;
const card=()=>cityContextCard(r,doc,{vegetation_note:'Fixture uses the unchanged city planting record.'});
const stem={id,e:r.e,n:r.n,y:2,h:r.h,crownW:row.crown_m*2,card};
const originals={fetch:globalThis.fetch,window:globalThis.window,bitmap:globalThis.createImageBitmap,add:TreeInstances.prototype.add};
const additions=[];
let trees;
let holdBuild=false;
const heldBuilds=[];
const checkpoint=()=>holdBuild?new Promise(resolve=>heldBuilds.push(resolve)):null;
try {
  globalThis.window={location:new URL('https://fixture.invalid/1871/')};
  globalThis.createImageBitmap=async()=>({width:4,height:4,close(){}});
  globalThis.fetch=async url=>String(url).endsWith('/street_trees/1871.json')
    ? new Response(JSON.stringify({scene:'1871',trees:[],placement:{variants:1}}),{headers:{'content-type':'application/json'}})
    : new Response(new Uint8Array([1]));
  TreeInstances.prototype.add=function(spec,x,y,z,scale,opts) {
    const h=originals.add.call(this,spec,x,y,z,scale,opts);
    additions.push({spec,x,y,z,h,opts});return h;
  };
  const confidence=createConfidenceView(),problems=[];
  trees=await createStreetTrees({dataBase:new URL('https://fixture.invalid/'),sceneId:'1871',
    terrain:{surfaceHeight:()=>0},confidence,problems,detail:'full',lowSpec:false,
    contextTrees:()=>[stem],levelAt:()=>-.1,checkpoint});
  assert.deepEqual(problems,[]);
  assert.equal(trees.stats.context,1);assert.equal(trees.stats.grown.stems,1,'context-only planting still draws');
  assert.equal(additions.length,1);const grown=additions[0];
  assert.deepEqual([grown.x,grown.y,grown.z],[r.e,1.9,-r.n]);
  assert(Math.abs(grown.h-r.h)<1e-10,'the context keeps its nominal record height');
  assert.equal(grown.opts.crownW,stem.crownW);assert.equal(grown.spec.speciesId,'context_deciduous');
  assert.equal(trees.cardFor(id).sidecar.name,'Reconstructed deciduous tree');
  assert(trees.cardFor(id).libertyIds.includes('L-1871-grown-context-3760'),'the proxy is declared on its own card');
  const camera=new THREE.PerspectiveCamera(60,1,.1,1000);
  camera.position.set(r.e,3,-r.n+6);camera.lookAt(r.e,3,-r.n);camera.updateMatrixWorld();
  assert.equal(trees.pickAt(null,camera)?.id,id,'the real bole opens its own generic card');
  confidence.setHidden('reconstructed',true);assert.equal(trees.pickAt(null,camera),null);
  confidence.setHidden('reconstructed',false);
  const relief = trees.materials.leafMat.bumpMap;
  assert(relief, 'capable Full starts with the existing atlas as leaf relief');
  await trees.setDetail('light');
  assert.equal(trees.materials.leafMat.bumpMap, null, 'switching to Light removes the extra relief sampling');
  await trees.setDetail('full');
  assert.equal(trees.materials.leafMat.bumpMap, relief, 'returning to Full reuses the same atlas');
  const visibleSlots = role => {
    let count=0;
    trees.group.traverse(o=>{
      if(!o.isBatchedMesh||!o.name.endsWith('-'+role))return;
      for(const [i,slot] of o._instanceInfo.entries())if(slot.active&&o.getVisibleAt(i))count++;
    });
    return count;
  };
  const settle=()=>{trees.update(0,camera);trees.settle();};
  assert.equal(trees.setBurnt(()=>true),1);settle();
  assert.equal(visibleSlots('leaves'),0);assert(visibleSlots('wood')>0);
  await trees.setMode('spring');settle();
  assert.equal(visibleSlots('leaves'),0,'burnt context trees stay bare through a season rebuild');
  holdBuild=true;
  const clearing=trees.setMode('summer');
  await Promise.resolve();await Promise.resolve();
  assert(heldBuilds.length>0,'the replacement is actually pending');
  trees.setBurnt(null);settle();
  assert(visibleSlots('leaves')>0,'clearing the fire updates the retained live forest');
  holdBuild=false;for(const resolve of heldBuilds.splice(0))resolve();
  await clearing;settle();
  assert(visibleSlots('leaves')>0,'the candidate uses the latest cleared fire state');
  assert.equal(trees.stats.burnt,0);
  holdBuild=true;
  const charring=trees.setDetail('light');
  await Promise.resolve();await Promise.resolve();assert(heldBuilds.length>0);
  trees.setBurnt(()=>true);settle();
  assert.equal(visibleSlots('leaves'),0,'fire updates the live forest during a detail rebuild');
  holdBuild=false;for(const resolve of heldBuilds.splice(0))resolve();
  await charring;settle();
  assert.equal(visibleSlots('leaves'),0,'the mounted candidate receives the latest burnt state');
  assert.equal(trees.stats.burnt,1);assert(visibleSlots('wood')>0);
  trees.setBurnt(null);await trees.setDetail('full');settle();
  assert(visibleSlots('leaves')>0);
  for (const mode of ['spring','fall','winter']) {
    await trees.setMode(mode);trees.update(0,camera);trees.settle();
    assert.equal(trees.stats.grown.stems,1);assert.equal(trees.stats.context,1);
    assert.equal(trees.cardFor(id).id,id,'season rebuild retains inspection identity');
    if (mode==='winter') {
      let leafArea=0;
      trees.group.traverse(o=>{
        if(o.isBatchedMesh&&o.material.name==='timber-leaves') {
          // A bare template carries one degenerate triangle for the batch.
          // Measure support area, rather than mistaking that slot for a leaf.
          const p=o.geometry.attributes.position,ix=o.geometry.index;
          const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
          for (let i=0;i<ix.count;i+=3) {
            a.fromBufferAttribute(p,ix.getX(i));b.fromBufferAttribute(p,ix.getX(i+1));c.fromBufferAttribute(p,ix.getX(i+2));
            leafArea+=b.sub(a).cross(c.sub(a)).length()/2;
          }
        }
      });
      assert.equal(leafArea,0,'winter handoff draws wood, with no solid portable crown or leaf area');
    }
  }
  const prior=trees.group.children[0];
  holdBuild=true;
  const rebuilding=trees.setMode('summer');
  await Promise.resolve();
  assert.equal(trees.group.children[0],prior,'the live forest stays mounted while its replacement grows');
  let duplicateDone=false;
  const duplicate=trees.setMode('summer').then(()=>{duplicateDone=true;});
  await Promise.resolve();await Promise.resolve();
  assert.equal(duplicateDone,false,'a repeated choice joins the pending rebuild');
  holdBuild=false;for(const resolve of heldBuilds.splice(0))resolve();
  await Promise.all([rebuilding,duplicate]);
  assert.notEqual(trees.group.children[0],prior);
  assert.equal(trees.group.children.length,1);
  await Promise.all([trees.setMode('summer'),trees.setMode('winter')]);
  assert.equal(trees.group.children.length,1,'only the latest concurrent seasonal forest is attached');
  assert.equal(trees.stats.mode,'winter');
  await trees.setMode('hidden');assert.equal(trees.group.visible,false);
  assert.equal(trees.pickAt(null,camera),null);assert.equal(trees.cardFor(id).id,id,'Hide retains card metadata');
  trees.setBurnt(()=>true);
  await trees.setMode('summer');settle();
  assert.equal(visibleSlots('leaves'),0,'a fire choice made while hidden applies on show');
  assert(visibleSlots('wood')>0);assert.equal(trees.stats.burnt,1);
  trees.setBurnt(null);settle();assert(visibleSlots('leaves')>0);
  await trees.setMode('hidden');
  let released=0;trees.materials.leafMat.addEventListener('dispose',()=>released++);
  const late=trees.setMode('summer');trees.dispose();await late;trees.dispose();
  assert.equal(released,1,'owned materials are released once');
  assert.equal(trees.group.children.length,0,'a late rebuild cannot remount disposed trees');
  trees=null;
} finally {
  trees?.dispose();TreeInstances.prototype.add=originals.add;
  globalThis.fetch=originals.fetch;globalThis.window=originals.window;globalThis.createImageBitmap=originals.bitmap;
}
console.log('PASS 1871 current planting, real generic growth/picking/confidence, winter wood, pending/latest fire and detail state, disposal and hidden cards');

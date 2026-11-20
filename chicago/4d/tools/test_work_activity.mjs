// SPDX-License-Identifier: GPL-3.0-or-later
// Actual portable 1812 rig + generated work kit; CPU tests, no browser/network.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const three = new URL('three.core.js', vendor).href;
const THREE = await import(three);
const data = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const utils = {};
for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) {
  utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${three}'`));
}
const gltfURL = new URL('addons/loaders/GLTFLoader.js', vendor);
const loaderSource = (await fs.readFile(gltfURL, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => {
  const name = Object.keys(utils).find(k => spec.endsWith(`/${k}.js`));
  return `from '${spec === 'three' ? three : name ? utils[name] : new URL(spec, gltfURL).href}'`;
});
const { GLTFLoader } = await import(data(loaderSource));
const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
const js = async (name) => (await fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8')).replace("from 'three'", `from '${three}'`);
const driverLife = data(await js('driver-life.js'));
const { createHumanLife } = await import(data((await js('human-life.js')).replace("from './driver-life.js'", `from '${driverLife}'`)));
const { createHumanActions } = await import(data((await js('human-actions.js')).replace("from './driver-life.js'", `from '${driverLife}'`)));

function geometryOnly(bytes) {
  const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20 + n));
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    if (m.pbrMetallicRoughness) { delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; }
  }
  const json0 = Buffer.from(JSON.stringify(doc)), json = Buffer.concat([json0, Buffer.alloc(-json0.length & 3, 32)]);
  const bin = bytes.subarray(28 + n), out = Buffer.alloc(28 + json.length + bin.length);
  out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
  out.writeUInt32LE(json.length, 12); out.writeUInt32LE(0x4e4f534a, 16); json.copy(out, 20);
  out.writeUInt32LE(bin.length, 20 + json.length); out.writeUInt32LE(0x004e4942, 24 + json.length); bin.copy(out, 28 + json.length);
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
}



const workSource=(await js('work-activity.js')).replace("from 'three/addons/loaders/GLTFLoader.js'",`from '${data(loaderSource)}'`);
const {createWorkActivity,workTaskAt,advanceWorkPhase}=await import(data(workSource));
const config=JSON.parse(await fs.readFile(new URL('data/humans/work_1812.json',here),'utf8'));
const bodyBytes=await fs.readFile(new URL('assets/humans/web/engage_1812.lod2.glb',here));
const kitBytes=await fs.readFile(new URL('assets/props/work_1812.glb',here));
// Re-run the real generator CLI outside the checkout. A changed data recipe must
// fail against a stale committed kit; never repair that kit while gates share it.
const kitTemp=await fs.mkdtemp(path.join(tmpdir(),'chicago4d-work-kit-'));
try {
  const regeneratedPath=path.join(kitTemp,'work_1812.glb');
  execFileSync('python3',[fileURLToPath(new URL('tools/generate_work_1812.py',here)),
    '--output',regeneratedPath],{cwd:kitTemp,encoding:'utf8'});
  const regenerated=await fs.readFile(regeneratedPath);
  assert(regenerated.equals(kitBytes),'work_1812.glb is stale: regenerate from data/humans/work_1812.json');
} finally {
  await fs.rm(kitTemp,{recursive:true,force:true});
}
console.log('Work kit: real generator CLI matches committed bytes; temporary output cleaned.');
const body=await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bodyBytes),'');
const sceneRoot=new THREE.Scene(),root=new THREE.Group();root.position.set(1082,.2,-165);root.rotation.y=-Math.PI/2;
sceneRoot.add(root);root.add(body.scene);
const variations=JSON.parse(await fs.readFile(new URL('assets/humans/web/hm08_variation_persons.json',here),'utf8'));
body.scene.scale.setScalar(variations.persons.chicago_militia_unnamed_4.looks.height_scale);root.updateMatrixWorld(true);
const meshes=[];body.scene.traverse(o=>{if(o.isMesh)meshes.push(o);});
const mixer=new THREE.AnimationMixer(body.scene);mixer.clipAction(body.animations.find(c=>c.name==='idle')).play();mixer.update(0);
const actions=createHumanActions({id:config.tasks[1].actor_id,scene:body.scene});assert(actions?.bound);
const actor={id:config.tasks[1].actor_id,e:1082,n:165,heading:270,root,inRange:true,state:'working',body:{scene:body.scene,meshes,oneShot:null},actions,counters:{animated:0}};
const humans={shown:true,get:id=>id===actor.id?actor:null,isHeld:()=>false};
const confidence={hidden:{reconstructed:false}};let now=0,loads=0;
const days={workSource:()=>({actorId:actor.id,epoch:1,active:true,originalAt:{e:1082,n:165},at:{e:1082,n:165},heading:270})};
const work=createWorkActivity({humans,days,config,assetBase:here,sceneRoot,confidence,now:()=>now,
 loader:{loadAsync:async()=>{loads++;return new GLTFLoader().parseAsync(geometryOnly(kitBytes),'');}}});sceneRoot.add(work.group);
const step=(opts={})=>{now+=1000/30;mixer.update(1/30);actions.apply(1/30,{state:actor.state,root});actor.counters.animated++;
 work.update(1/30,{scene:'1812',date:'1812-08-14',hour:15,paused:false,...opts});};
assert.equal(workTaskAt(config,{scene:'1812',date:'1812-08-14',hour:15}).id,'militia-packing-chest');
assert.equal(workTaskAt(config,{scene:'1812',date:'1812-04-15',hour:10}).id,'militia-piazza-repair');
assert.equal(workTaskAt(config,{scene:'1812',date:'1812-02-15',hour:15}),null);
assert.equal(workTaskAt(config,{scene:'1812',date:'1812-08-14',hour:2}),null);
assert.equal(workTaskAt(config,{scene:'1835',date:'1835-07-01',hour:15}),null);
step();await new Promise(r=>setImmediate(r));assert.equal(loads,1);assert(work.state.ready);
let contacts=0,maxError=0;
for(let i=0;i<300;i++){
 step();if(work.state.handError!==null)maxError=Math.max(maxError,work.state.handError);
 if(work.state.contacts>contacts){contacts=work.state.contacts;
  const strike=work.group.getObjectByName('hammer_strike').getWorldPosition(new THREE.Vector3());
  const target=work.group.getObjectByName('work_contact').getWorldPosition(new THREE.Vector3());
  assert(strike.distanceTo(target)<=config.action.max_contact_error_m,'actual hammer touches actual visible lid');
  assert(work.audioSources.length===1);assert.equal(work.audioSources[0].contactSerial,contacts);
 }
}
assert(contacts>=2,`actual rig produced ${contacts} contacts; state=${JSON.stringify(work.state)}`);
assert(maxError<.018,`measured real hand grip error ${maxError}`);
const before=contacts;actor.state='walking';step();assert.equal(work.audioSources.length,0);assert.equal(work.group.visible,false);
actor.state='working';for(let i=0;i<25;i++)step();assert.equal(work.state.contacts,before,'new action starts quietly');
confidence.hidden.reconstructed=true;step();assert.equal(work.audioSources.length,0);assert.equal(work.group.visible,false);
confidence.hidden.reconstructed=false;for(let i=0;i<25;i++)step();
const materials=[...new Set(meshes.flatMap(m=>Array.isArray(m.material)?m.material:[m.material]))];
materials.forEach(m=>m.visible=false);step();assert.equal(work.audioSources.length,0);assert.equal(work.group.visible,false);materials.forEach(m=>m.visible=true);
for(let i=0;i<25;i++)step();
actor.body.oneShot={};step();assert.equal(work.audioSources.length,0);actor.body.oneShot=null;
humans.shown=false;step();assert.equal(work.group.visible,false);humans.shown=true;
for(let i=0;i<25;i++)step();step({paused:true});assert.equal(work.audioSources.length,0);
for(let i=0;i<25;i++)step();now+=300;assert.equal(work.audioSources.length,0,'old pose snapshot expires');
step({date:'1812-02-15'});assert.equal(work.group.visible,false,'absent winter task is not still hammering');
assert.equal(advanceWorkPhase(.62,.25,config.action).phase,.63,'slow live frame shows exact contact');
assert.equal(advanceWorkPhase(.62,3,config.action).contact,false,'stale time never catches up impacts');
work.dispose();step();assert.equal(work.audioSources.length,0);assert.equal(work.group.children.length,0);
console.log(`Work activity: actual engage LOD2, ${contacts} contact frames, max grip error ${maxError.toFixed(6)}m; dates/hide/walk/one-shot/pause/stale/dispose pass`);

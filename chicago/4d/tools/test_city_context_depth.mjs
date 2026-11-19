#!/usr/bin/env node
/** T-3654: the actual context casters share the colour pass's confidence controls.
 * Tiny loader fixtures exercise createCityContext itself without a browser or GPU.
 * Shader hooks and live uniforms are checked here; native GLSL/shadow rendering
 * remains a separate published-browser reading. */
import assert from 'node:assert/strict';
import { register } from 'node:module';

const vendor = new URL('../renderers/web/vendor/three-0.185.1/', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s,c,next) {
  if(s==='three')return {url:'${vendor}three.module.js',shortCircuit:true};
  if(s.startsWith('three/addons/'))return {url:'${vendor}addons/'+s.slice(13),shortCircuit:true};
  return next(s,c);
}`)}`, import.meta.url);
const THREE = await import('three');
const { GLTFLoader } = await import('three/addons/loaders/GLTFLoader.js');
const { createConfidenceView } = await import('../renderers/web/js/confidence.js');
const { createCityContext } = await import('../renderers/web/js/city-context.js');

const texture = () => new THREE.DataTexture(new Uint8Array([255,255,255,255]),1,1);
const mapped = new THREE.MeshStandardMaterial({name:'mapped',map:texture(),alphaMap:texture(),alphaTest:.3,
  displacementMap:texture(),displacementScale:.2,displacementBias:.1,side:THREE.DoubleSide});
mapped.shadowSide=THREE.FrontSide; mapped.clipShadows=true;
mapped.clippingPlanes=[new THREE.Plane(new THREE.Vector3(0,1,0),0)]; mapped.clipIntersection=true;
mapped.wireframeLinewidth=2;
const plain = new THREE.MeshStandardMaterial({name:'plain'}); plain.visible=false;
const leaf = new THREE.MeshStandardMaterial({name:'leaf',map:texture(),alphaTest:.1,alphaToCoverage:true});
const road = new THREE.MeshStandardMaterial({name:'road'});
const box = () => {
  const g=new THREE.BoxGeometry(1,1,1);
  g.setAttribute('_confidence',new THREE.BufferAttribute(new Float32Array(g.attributes.position.count).fill(1),1));
  return g;
};
const kit = new THREE.Group(), infrastructure = new THREE.Group();
const template = (id,material,vegetation=false) => {
  const nodes={near:`${id}_near`,far:`${id}_far`};
  for(const name of Object.values(nodes)) {
    const mesh=new THREE.Mesh(box(),material); mesh.name=name; kit.add(mesh);
  }
  return {id,name:id,nodes,width_m:1,depth_m:1,eave_m:1,triangles:{near:12,far:12},vegetation};
};
const definition={templates:[template('house',mapped),template('house_alt',mapped),template('plain',plain)],
  vegetation:[template('tree',leaf,true)],asset_bytes:0};
for(const [material,layer] of [[mapped,'bridges'],[mapped,'bridges'],[road,'streets']]) {
  const mesh=new THREE.Mesh(box(),material);mesh.userData.layer=layer;infrastructure.add(mesh);
}
const building=(id,kit,e)=>({id,kit,e,n:20,width_m:10,depth_m:8,eave_m:9,district:'fixture',base_m:0});
const doc={kit_definition:'kit.json',kit_glb:'kit.glb',infrastructure_glbs:['infrastructure.glb'],tile_m:500,
  buildings:[building('a','house',20),building('b','house',520),building('c','house_alt',40),building('d','plain',70)],
  trees:[{id:'tree',e:90,n:20,height_m:6,crown_m:2,base_m:0}]};
const confidence=createConfidenceView();
const originalFetch=globalThis.fetch, originalLoad=GLTFLoader.prototype.loadAsync;
let city;
try {
  globalThis.fetch=async url=>{
    assert.equal(new URL(url).pathname,'/kit.json');
    return new Response(JSON.stringify(definition),{headers:{'content-type':'application/json'}});
  };
  GLTFLoader.prototype.loadAsync=async url=>{
    const file=new URL(url).pathname;
    assert(['/kit.glb','/infrastructure.glb'].includes(file));
    return {scene:file==='/kit.glb'?kit:infrastructure};
  };
  city=await createCityContext({doc,dataBase:new URL('https://fixture.invalid/'),
    terrain:{surfaceHeight:()=>0},confidence,detail:'full'});
} finally {
  globalThis.fetch=originalFetch; GLTFLoader.prototype.loadAsync=originalLoad;
}
const camera=new THREE.PerspectiveCamera(62,1,.1,28000);
camera.position.set(300,20,0);camera.lookAt(300,0,-100);city.update(0,camera);
const near=[],bridges=[],far=[],streets=[];
city.group.traverse(o=>{
  if(!o.isMesh)return;
  if(o.userData.contextTier==='near')near.push(o);
  else if(o.userData.contextTier==='far')far.push(o);
  else if(o.userData.layers?.includes('bridges'))bridges.push(o);
  else streets.push(o);
});
assert.equal(near.length,5,'all building and tree instance batches are tested');
assert.equal(bridges.length,1,'the two portable bridge primitives form one material batch');
assert(near.some(o=>o.userData.treeCount>0),'the fixture includes a near tree caster');
const casters=[...near,...bridges], depths=new Set(), owners=new Map();
const compileHook = (material,lib) => {
  const shader={uniforms:THREE.UniformsUtils.clone(lib.uniforms),vertexShader:lib.vertexShader,fragmentShader:lib.fragmentShader};
  material.onBeforeCompile(shader,{}); return shader;
};
const shaders=[];
for(const mesh of casters) {
  assert(mesh.castShadow,`${mesh.name} is a real Full-detail caster`);
  const material=mesh.material,depth=mesh.customDepthMaterial;
  assert(depth?.isMeshDepthMaterial,`${mesh.name} needs its confidence-patched shadow material`);
  assert.equal(depth.depthPacking,THREE.RGBADepthPacking);
  assert.equal(depth.visible,material.visible,'shadow visibility follows the colour owner');
  assert.equal(depth.side,material.shadowSide??material.side);
  for(const key of ['map','alphaMap','displacementMap','displacementScale','displacementBias','wireframe',
    'wireframeLinewidth','clipShadows','clippingPlanes','clipIntersection']) assert.equal(depth[key],material[key],key);
  assert.equal(depth.alphaTest,material.alphaToCoverage ? .5 : material.alphaTest);
  if(owners.has(material))assert.equal(depth,owners.get(material),'one colour owner reuses its depth across batches');
  owners.set(material,depth);depths.add(depth);
  const grade=mesh.geometry.getAttribute('_confidence');
  assert(grade && grade.count>0);for(let i=0;i<grade.count;i++)assert.equal(grade.getX(i),1);
  const shadow=compileHook(depth,THREE.ShaderLib.depth),colour=compileHook(material,THREE.ShaderLib.standard);
  assert.match(shadow.vertexShader,/attribute float _confidence;/);
  assert.match(shadow.vertexShader,/vConfidence =/);
  assert.match(shadow.fragmentShader,/if \(hide > 0\.0\) discard;/);
  assert.match(shadow.fragmentShader,/chicago_bayer4/);
  for(const key of ['uHideLevel','uConfMode','uGradeMode','uGradeOpacity'])assert.equal(shadow.uniforms[key],colour.uniforms[key],key);
  shaders.push(shadow);
}
assert.equal(depths.size,owners.size,'different colour owners never share cached depth maps');
assert.equal(owners.size,3);
assert.equal(owners.get(plain).map,null,'the unmapped owner cannot inherit another caster’s atlas');
for(const mesh of [...far,...streets]) {
  assert.equal(mesh.castShadow,false);assert.equal(mesh.customDepthMaterial,undefined,'noncasters need no depth owner');
}
confidence.set(false);confidence.setHidden('reconstructed',true);
for(const shader of shaders) {
  assert.equal(shader.uniforms.uConfMode.value,0);
  assert.equal(shader.uniforms.uHideLevel.value.z,1,'Hide reaches the depth pass even with the colour view off');
}
assert.equal(city.pickAt(null,camera),null,'hidden context still cannot intercept inspection');
confidence.setHidden('reconstructed',false);confidence.set(true);
confidence.setGrade('reconstructed',{mode:'dither',opacity:.34});
for(const shader of shaders) {
  assert.equal(shader.uniforms.uHideLevel.value.z,0);
  assert.equal(shader.uniforms.uConfMode.value,1);
  assert.equal(shader.uniforms.uGradeMode.value.z,2);
  assert.equal(shader.uniforms.uGradeOpacity.value.z,.34);
}
city.setDetail('light');city.update(0,camera);
assert(near.every(o=>!o.castShadow),'Light keeps its existing near-shadow policy');
assert(bridges.every(o=>o.castShadow),'bridge casting remains unchanged');
city.setDetail('full');city.update(0,camera);assert(near.every(o=>o.castShadow));
const disposed=new Map([...depths].map(d=>[d,0]));
for(const depth of depths)depth.addEventListener('dispose',()=>disposed.set(depth,disposed.get(depth)+1));
city.dispose();city.dispose();
assert([...disposed.values()].every(n=>n===1),'every owned depth is disposed exactly once');
console.log('PASS 1871 context shadows: actual near building/tree and bridge casters, per-colour depth ownership, confidence attributes/live hide-dither uniforms, map isolation, unchanged tier policy and idempotent disposal');

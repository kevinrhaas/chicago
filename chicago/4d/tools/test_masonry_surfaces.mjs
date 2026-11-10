/** T-3341: fabric decisions, actual mixed-stack conservation and shader composition. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL, fileURLToPath } from 'node:url';
import * as THREE from '../renderers/web/vendor/three-0.185.1/three.module.js';
import { parseGlb, readAccessor } from './k01_contract.mjs';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = (p) => fs.readFileSync(path.join(APP, p), 'utf8');
const three = pathToFileURL(path.join(APP, 'renderers/web/vendor/three-0.185.1/three.module.js')).href;
const plain = (src) => src.replace(/^import .*$/mg, '');
const uri = (src) => `data:text/javascript,${encodeURIComponent(src)}`;
const hooks = 'const captureHooks = () => null, registerPatch = () => {}, programKeyOf = () => "prior";\n';
const bondUri = uri(`const {ShaderChunk} = await import(${JSON.stringify(three)});\n${hooks}`
  + plain(read('renderers/web/js/brick-bond.js')));
const b = await import(bondUri);
const fixture = `
const {BufferAttribute,BufferGeometry,Mesh,ShaderChunk,Vector3} = await import(${JSON.stringify(three)});
const {bondUniformsFor,brickBondShader,SPREAD} = await import(${JSON.stringify(bondUri)});
${hooks}
const SCALARS_GLSL = {declare:(s)=>s, roughness:'0.85'};
const structureFrameGLSL = (name) => 'vec3 '+name+' = transformed;';
const resolveBases = () => ({assetBase:'https://example.test/data/'});
let calls=0;
const loadSubstrate = async(base,dir) => {
  calls++;
  return {id:dir,normal:{kind:'normal'},orl:{kind:'orl'},tileM:dir.endsWith('chimney')?2.04:4.2,meanRough:.9,px:512,ktx2:true};
};
export const loadCalls = () => calls;
`;
const m = await import(uri(fixture + plain(read('renderers/web/js/masonry-surfaces.js'))));
const early = (archetype, attributes = {}, scene = '1835') => ({ scene, archetype, attributes });
const attr = (value) => ({ value, confidence: 'reconstructed' });
let passed = 0;
const check = async (name, fn) => { await fn(); passed++; console.log(`PASS ${name}`); };

await check('material roles use early brick and keep exterior log stacks clay', () => {
  for (const role of ['brick', 'draft_brick', 'k13_brick', 'chimney']) {
    assert.equal(m.masonrySubstrate(role, early('frame_dwelling')), 'brick');
  }
  assert.equal(m.masonrySubstrate('chimney', early('log_dwelling')), 'clay');
  assert.equal(m.masonrySubstrate('wall', early('fort_structure', {construction: attr('brick')})), 'brick');
  assert.equal(m.masonrySubstrate('wall', early('fort_structure', {construction: attr('frame')})), null);
  assert.equal(m.masonrySubstrate('log', early('log_dwelling')), null);
});
await check('recorded log ridge stacks take masonry instead of blanket log=clay', () => {
  assert.equal(m.masonrySubstrate('chimney', early('log_dwelling', {chimney_ridge_at: attr([.2,.8])})), 'brick');
  assert.equal(m.masonrySubstrate('chimney', early('log_dwelling', {chimney_ridge_at: attr([])})), 'clay');
});
await check('1904 and mapped period surfaces are excluded for every matching role', () => {
  for (const role of ['brick','chimney','draft_brick','k13_brick','wall']) {
    assert.equal(m.masonrySubstrate(role, early('log_dwelling', {}, '1904')), null);
    assert.equal(m.masonrySubstrate(role, early('log_dwelling'), true), null);
  }
});
await check('early library module is its actual20 by48 running bond, with48 whole-face choices', () => {
  const sheet = JSON.parse(read('assets/textures/chicago_1835_pbr/masonry/chicago_clay_brick_lime_mortar/material.json'));
  assert.equal(sheet.span_m, 4.2);
  assert.deepEqual([m.EARLY_BRICK.modules,m.EARLY_BRICK.courses],[20,48]);
  const u = b.bondUniformsFor(m.EARLY_BRICK,{maxCourses:48});
  assert.deepEqual(u.panel,[20,48,.055,.14]);
  assert.equal(u.course.length,48); assert.equal(u.list.flat().length,48);
  for(let i=0;i<48;i++) assert.deepEqual(u.course[i],[i%2/2,1,0,48]);
  assert.deepEqual(u.list.flat(),Array.from({length:48},(_,i)=>i));
});
await check('existing1904 panels retain their original twelve-course uniforms and shader', () => {
  for(const id of Object.keys(b.PANELS)) {
    const u=b.bondUniforms(id);assert.equal(u.course.length,12);assert.equal(u.list.length,3);
  }
  const s=b.brickBondShader(); assert(s.pars.includes('chiBondCourse[ 12 ]'));
  assert(s.pars.includes('chiBondList[ 3 ]'));assert(s.resolve.includes('vMapUv'));
});
await check('unwanted scenes do not fetch a single early sheet or mutate their materials', async () => {
  const n=m.loadCalls();const out=await m.loadMasonrySurfaces({wanted:false});
  const mat={name:'brick'};assert.equal(out.apply(mat,early('frame_dwelling',{},'1904')),null);
  assert.deepEqual(mat,{name:'brick'});assert.equal(m.loadCalls(),n);
});
await check('bound normals,roughness andAO shuffle together with stable derivatives', async () => {
  const out=await m.loadMasonrySurfaces({wanted:true});const mat=new THREE.MeshStandardMaterial();mat.name='chimney';
  assert.equal(out.apply(mat,early('frame_dwelling')),'brick');
  const shader={uniforms:{},vertexShader:THREE.ShaderLib.standard.vertexShader,fragmentShader:THREE.ShaderLib.standard.fragmentShader};
  mat.onBeforeCompile(shader,{});
  assert.equal(shader.uniforms.chiBondCourse.value.length,48*4);
  assert(shader.vertexShader.includes('vNormalMapUv = uv;'));
  for(const name of ['normalMap','roughnessMap','aoMap']) {
    assert(new RegExp(`${name}, v(?:Normal|Roughness|Ao)MapUv \\+ chiBondShift`).test(shader.fragmentShader));
  }
  assert(shader.fragmentShader.includes('dFdx( vNormalMapUv )'));
  assert.equal(mat.customProgramCacheKey(),'early-masonry-v1|over:prior');
});

/** Actual native accessor streams; the shared reader already handles normalized data. */
const sidecar=JSON.parse(read('data/sidecars/1835/miller_house.json'));
const glb=parseGlb(fs.readFileSync(path.join(APP,'assets',sidecar.asset)));
const ctx={...glb,views:new Map()};
const meshes=[];
function visit(ni,parent) {
  const n=glb.json.nodes[ni];
  const local=n.matrix ? new THREE.Matrix4().fromArray(n.matrix) : new THREE.Matrix4().compose(
    new THREE.Vector3(...(n.translation??[0,0,0])),new THREE.Quaternion(...(n.rotation??[0,0,0,1])),
    new THREE.Vector3(...(n.scale??[1,1,1])));
  const matrix=parent.clone().multiply(local);
  for(const p of glb.json.meshes?.[n.mesh]?.primitives??[]) {
    const material=glb.json.materials[p.material];if(material.name!=='chimney')continue;
    const g=new THREE.BufferGeometry();
    for(const [name,ai] of Object.entries(p.attributes)) {
      const a=glb.json.accessors[ai],width={SCALAR:1,VEC2:2,VEC3:3,VEC4:4}[a.type];
      g.setAttribute(name.toLowerCase(),new THREE.BufferAttribute(new Float32Array(readAccessor(ctx,ai)),width));
    }
    if(p.indices!==undefined)g.setIndex(new THREE.BufferAttribute(new Uint32Array(readAccessor(ctx,p.indices)),1));
    const mat=new THREE.MeshStandardMaterial();mat.name='chimney';
    meshes.push({mesh:new THREE.Mesh(g,mat),matrix});
  }
  for(const c of n.children??[])visit(c,matrix);
}
for(const n of glb.json.scenes[glb.json.scene??0].nodes)visit(n,new THREE.Matrix4());
await check('actual Miller mixed primitive separates ground-foot clay and roof-foot brick without lost triangles', () => {
  assert.equal(meshes.length,1);const original=meshes[0].mesh.geometry;
  const parts=m.masonryMeshes(meshes,sidecar);assert.equal(parts.length,2);
  assert.deepEqual(parts.map((p)=>p.mesh.material.userData.chiMasonryFabric),['clay','brick']);
  assert.equal(parts.reduce((n,p)=>n+p.mesh.geometry.getIndex().count,0),original.getIndex().count);
  function triangles(rows) {
    const out=[];
    for(const {mesh,matrix} of rows) {
      const g=mesh.geometry,p=g.getAttribute('position'),c=g.getAttribute('_confidence'),idx=g.getIndex();
      for(let i=0;i<idx.count;i+=3) {
        const tri=[];for(let j=0;j<3;j++) {
          const k=idx.getX(i+j),v=new THREE.Vector3().fromBufferAttribute(p,k).applyMatrix4(matrix);
          tri.push([...v.toArray(),c?.getX(k)??null]);
        }
        out.push(JSON.stringify(tri));
      }
    }
    return out.sort();
  }
  assert.deepEqual(triangles(parts),triangles(meshes));
});
await check('ambiguous mixed geometry is rejected rather than assigning a guessed fabric', () => {
  assert.throws(()=>m.chimneyComponents([[0,2,0],[1,2,0],[0,3,0]],[0,1,2]),/declared mixed chimney/);
});
console.log(`MASONRY SURFACES PASS — ${passed} meaningful checks`);

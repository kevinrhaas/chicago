#!/usr/bin/env node
/** CPU regression controls for Full directional shadow culling.
 * Native Three light/shadow matrices and BatchedMesh callbacks; the renderer
 * descriptor is a prototype-only fixture, not an initialized WebGL renderer.
 * A null descriptor preserves the old native/AABB path for comparisons.
 * No browser, external fixtures, production mutations or artifact files are required.
 */
import fs from 'node:fs';
import assert from 'node:assert/strict';
const vendor = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
const T = await import(vendor);
const helper = new URL('../renderers/web/js/batch-frustum-box.js', import.meta.url);
const text = fs.readFileSync(helper, 'utf8');
// Same real helper, resolving its browser import map in Node. Expose the two
// private pure kernels only in this test module; production exports stay exact.
const source = text.replace("from 'three'", 'from ' + JSON.stringify(vendor))
  + '\nexport { shadowViewFrame, shadowCannotReachView };';
const M = await import('data:text/javascript;base64,' + Buffer.from(source).toString('base64'));
const checks=[];const test=(name,fn)=>{fn();checks.push(name);console.log('PASS '+name);};
function context(){
 const light=new T.DirectionalLight();light.castShadow=true;light.position.set(-320,320,-10);light.target.position.set(0,0,-10);light.updateMatrixWorld(true);light.target.updateMatrixWorld(true);
 const c=light.shadow.camera;c.left=c.bottom=-240;c.right=c.top=240;c.near=1;c.far=900;c.updateProjectionMatrix();light.shadow.updateMatrices(light);light.shadow.bias=-.0004;light.shadow.normalBias=.045;light.shadow.mapSize.set(4096,4096);
 const map=light.shadow.map=new T.WebGLRenderTarget(4096,4096);map.depthTexture=new T.DepthTexture(4096,4096,T.UnsignedIntType);Object.assign(map.depthTexture,{format:T.DepthFormat,minFilter:T.LinearFilter,magFilter:T.LinearFilter,compareFunction:T.LessEqualCompare,wrapS:T.ClampToEdgeWrapping,wrapT:T.ClampToEdgeWrapping});
 const renderer=Object.create(T.WebGLRenderer.prototype);renderer.shadowMap={enabled:true,autoUpdate:true,type:T.PCFShadowMap};const camera=new T.PerspectiveCamera(60,1,.1,100);camera.updateMatrixWorld(true);
 const batch={matrixWorld:new T.Matrix4()},descriptor={light:()=>light,fresh:()=>true};const out={identity:new T.Matrix4(),clip:new T.Matrix4(),expected:new T.Matrix4(),frustum:new T.Frustum(),ray:new T.Vector3()};
 return{light,camera,renderer,batch,descriptor,out};
}
const frame=o=>M.shadowViewFrame(o.out,o.renderer,o.camera,o.light.shadow.camera,o.descriptor,o.batch);
test('native directional matrices/map/filter frame accepted with unreduced physical margin',()=>{const o=context(),f=frame(o);assert(f);assert(Math.abs(f.ray.dot(new T.Vector3(1,-1,0).normalize())-1)<1e-12);assert(f.margin>=2*Math.SQRT2*480/4096+.045+.0004*899);});
for(const[name,change]of[
 ['missing descriptor',o=>o.descriptor=null],['nonfresh cadence',o=>o.descriptor.fresh=()=>false],['cached renderer shadows',o=>o.renderer.shadowMap.autoUpdate=false],['unknown shadow filter',o=>o.renderer.shadowMap.type=T.VSMShadowMap],['unconverted PCFSoft',o=>o.renderer.shadowMap.type=T.PCFSoftShadowMap],['unknown light',o=>o.descriptor.light=()=>new T.PointLight()],['unknown renderer',o=>o.renderer={}],['mismatched actual camera',o=>o.light.shadow.camera=new T.OrthographicCamera()],['shadow radius changed',o=>o.light.shadow.radius=2],['nonfinite bias',o=>o.light.shadow.bias=NaN],['depth nearest sampler',o=>o.light.shadow.map.depthTexture.magFilter=T.NearestFilter],['depth compare changed',o=>o.light.shadow.map.depthTexture.compareFunction=T.GreaterCompare],['map size mismatch',o=>o.light.shadow.map.width=2048],['nonunit camera',o=>o.light.shadow.camera.matrixWorld.scale(new T.Vector3(2,1,1))],['unknown shadow projection',o=>o.light.shadow.camera.projectionMatrix.elements[0]*=2],['stale shadow matrix',o=>o.light.shadow.matrix.elements[12]+=.1],['inconsistent shadow inverse',o=>o.light.shadow.camera.matrixWorldInverse.elements[12]+=.1],['depth image dimensions mismatch',o=>o.light.shadow.map.depthTexture.image.width=2048],['nonidentity batch frame',o=>o.batch.matrixWorld.makeTranslation(1,0,0)],['reversed main depth',o=>o.camera._reversedDepth=true],['shadow subview',o=>o.light.shadow.camera.view={}],['MSAA shadow target',o=>o.light.shadow.map.samples=4]
])test(name+' skips supplemental phase',()=>{const o=context();change(o);assert.equal(frame(o),null);});
test('modified global stock receiver shadow chunk skips phase',()=>{const prior=T.ShaderChunk.shadowmap_vertex;try{const o=context();T.ShaderChunk.shadowmap_vertex+='\nunknown';assert.equal(frame(o),null);}finally{T.ShaderChunk.shadowmap_vertex=prior;}});
test('away ray rejects, toward/tangent rays and filter-nearby caster stay',()=>{const f={frustum:{planes:[new T.Plane(new T.Vector3(1,0,0),0)]},ray:new T.Vector3(-1,0,0),margin:.5},box=new T.Box3(new T.Vector3(-2,-1,-1),new T.Vector3(-1,1,1));assert(M.shadowCannotReachView(f,box));f.ray.x=1;assert(!M.shadowCannotReachView(f,box));f.ray.set(0,-1,0);assert(!M.shadowCannotReachView(f,box));f.ray.x=-1;const near=new T.Box3(new T.Vector3(-.2,-1,-1),new T.Vector3(-.1,1,1));assert(!M.shadowCannotReachView(f,near));assert(M.shadowCannotReachView({...f,margin:0},near),'omitting filter expansion is detectably wrong');});
function build(module,descriptor){const geometry=new T.PlaneGeometry(.2,40,1,500),m=new T.MeshStandardMaterial(),b=new T.BatchedMesh(2,geometry.attributes.position.count*2,geometry.index.count*2,m);for(const x of[0,8]){const id=b.addInstance(b.addGeometry(geometry));b.setMatrixAt(id,new T.Matrix4().makeTranslation(x,0,-10));}b.updateMatrixWorld(true);const depth=new T.MeshDepthMaterial(),stats={};const c=module.installFrustumBoxCull(b,true,depth,null,stats,descriptor);c.seal();return{b,m,depth,stats};}
const ids=b=>Array.from({length:b._multiDrawCount},(_,k)=>b._indirectTexture.image.data[k]);
test('actual native shadow wrapper removes away caster only; colour list exact',()=>{const o=context(),a=build(M,null),b=build(M,o.descriptor);for(const x of[a,b])x.b.onBeforeRender(o.renderer,null,o.camera,x.b.geometry,x.m);assert.deepEqual(ids(a.b),ids(b.b));for(const x of[a,b])x.b.onBeforeShadow(o.renderer,x.b,o.camera,o.light.shadow.camera,x.b.geometry,x.depth);assert.deepEqual([...ids(a.b)].sort(),[0,1]);assert.deepEqual(ids(b.b),ids(a.b).filter(id=>id!==1));assert.equal(b.stats.shadowViewRejected,1);b.b.onBeforeRender(o.renderer,null,o.camera,b.b.geometry,b.m);assert.deepEqual(ids(b.b),[0],'shadow context cleared before colour');});
test('toward-view sun keeps offscreen caster',()=>{const o=context();o.light.position.set(320,320,-10);o.light.updateMatrixWorld(true);o.light.shadow.updateMatrices(o.light);const a=build(M,null),b=build(M,o.descriptor);for(const x of[a,b])x.b.onBeforeShadow(o.renderer,x.b,o.camera,o.light.shadow.camera,x.b.geometry,x.depth);assert.deepEqual(ids(b.b),ids(a.b));assert.deepEqual([...ids(b.b)].sort(),[0,1]);});
let seed=82735;const rand=()=>((seed=(Math.imul(seed,1664525)+1013904223)>>>0)/2**32);
test('1000 separating-plane rays remain outside for arbitrary positive travel and bounded offsets',()=>{for(let i=0;i<1000;i++){const n=new T.Vector3(rand()-.5,rand()-.5,rand()-.5).normalize(),ray=n.clone().negate(),margin=.1+rand(),f={frustum:{planes:[new T.Plane(n,0)]},ray,margin};const center=n.clone().multiplyScalar(-10),box=new T.Box3().setFromCenterAndSize(center,new T.Vector3(1,1,1));assert(M.shadowCannotReachView(f,box));for(const t of[0,.1,1,100,1e6])for(const x of[box.min.x,box.max.x])for(const y of[box.min.y,box.max.y])for(const z of[box.min.z,box.max.z]){const p=new T.Vector3(x,y,z).addScaledVector(ray,t).add(new T.Vector3((rand()-.5)*2*margin,(rand()-.5)*2*margin,(rand()-.5)*2*margin));assert(n.dot(p)<0);}}});
console.log('PASS '+checks.length+' batch shadow cull controls; CPU only, no browser/GPU acceptance');

import fs from 'node:fs/promises';
import {pathToFileURL,fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';
const root=process.cwd(),proof=fileURLToPath(new URL('.',import.meta.url)).replace(/\/$/,'');
const threeURL=pathToFileURL(root+'/renderers/web/vendor/three-0.185.1/three.module.js').href;
const T=await import(threeURL);
const load=async p=>import('data:text/javascript;base64,'+Buffer.from((await fs.readFile(p,'utf8')).replace("from 'three'",`from '${threeURL}'`)).toString('base64'));
const before=await load(proof+'/view-occlusion-before-cpu-opt.txt');
const after=await load(root+'/renderers/web/js/view-occlusion.js');
const stands=JSON.parse(await fs.readFile(proof+'/mobile/browser-validation-mobile.json','utf8')).results[0].stands;
let seed=2227;const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296;};
const fixtures=[];let hidden=0,visible=0;
for(const stand of stands){
 const camera=new T.PerspectiveCamera();camera.position.fromArray(stand.cameraPosition);
 camera.quaternion.fromArray(stand.cameraQuaternion);camera.projectionMatrix.fromArray(stand.projection);
 camera.updateMatrixWorld();
 const world=(x,y,z)=>new T.Vector3(x,y,z).applyMatrix4(camera.matrixWorld);
 const triangles=[];
 for(let i=0;i<50;i++){
  const d=2+rand()*35,span=3+rand()*30,x=(rand()-.5)*d,y=(rand()-.5)*d;
  const points=[world(x-span,y-span,-d),world(x+span,y-span,-d-rand()*4),world(x,y+span,-d-rand()*4)];
  triangles.push({points,normal:new T.Vector3().subVectors(points[1],points[0]).cross(new T.Vector3().subVectors(points[2],points[0])),side:T.DoubleSide});
 }
 const vp=new T.Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse);
 const polygons=after.projectOccluders(triangles,camera,390,780);
 for(let i=0;i<500;i++){
  const d=(rand()-.05)*100,center=world((rand()-.5)*d,(rand()-.5)*d,-d),size=.005+rand()*2;
  const box=new T.Box3(center.clone().addScalar(-size),center.clone().addScalar(size));
  const expected=before.boxOccluded(box,vp,polygons,390,780);
  assert.equal(after.boxOccluded(box,vp,polygons,390,780),expected,stand.name+' box '+i);
  expected?hidden++:visible++;fixtures.push([box,vp,polygons]);
 }
}
assert.ok(hidden>100 && visible>100,'Exercise both conservative outcomes');
const time=fn=>{const start=performance.now();for(const args of fixtures)fn(...args,390,780);return performance.now()-start;};
// Warm both paths, then alternate so neither consistently gets the first run.
time(before.boxOccluded);time(after.boxOccluded);
const runs=[];
for(let i=0;i<5;i++){
 const row={};for(const [name,fn]of i%2?[['after',after.boxOccluded],['before',before.boxOccluded]]:[['before',before.boxOccluded],['after',after.boxOccluded]])row[name]=time(fn);
 runs.push(row);
}
const result={method:'7,500 deterministic synthetic world boxes, slanting opaque triangles and the fifteen measured camera matrices; exact Boolean equality to the preserved pre-optimization function. CPU microbenchmark only, not browser frame time.',cases:fixtures.length,hidden,visible,allDecisionsExact:true,runs};
await fs.writeFile(process.env.QA_EQUIVALENCE_OUT||'/tmp/glessner-box-equivalence.json',JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));

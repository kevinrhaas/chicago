/** T-2037: protect emitted crossings from the coarse far-ground mesh.
 * node tools/check_plank_ground.mjs [--json] [--baseline]
 * --baseline deliberately exits 1 after reporting the original burial witness.
 * Imports actual terrain/frontage builders; no copied plank-height assumptions.
 * The 25 mm refinement trigger is not a geometric-error guarantee: acceptance
 * uses exact planar intersections of the Float32 geometry that the GPU draws.
 */
import {readFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
import path from 'node:path';
import {pathToFileURL, fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const sourceRoot=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const checks=[];
function check(name,fn){fn();checks.push(name);}
const threeURL=pathToFileURL(path.join(sourceRoot,'renderers/web/vendor/three-0.185.1/three.module.js')).href;
const THREE=await import(threeURL);
const modURL=s=>'data:text/javascript;base64,'+Buffer.from(s).toString('base64');
const terrainSource=await readFile(path.join(sourceRoot,'renderers/web/js/terrain.js'),'utf8');
const baseStride=Number(terrainSource.match(/const GROUND_BASE_STEP = (\d+)/)[1]);
const baseOffset=Number(terrainSource.match(/groundBase\.position\.y = (-?[\d.]+)/)[1]);
const at=terrainSource.indexOf('function gridGeometry(');
const end=terrainSource.indexOf('/* -------------------------------------------------------------------------- */',at);
const {adaptiveGroundGrid}=await import(pathToFileURL(path.join(sourceRoot,'renderers/web/js/terrain-base.js')).href);
const gridGeometry=new Function('THREE','SHORE_Y','adaptiveGroundGrid',terrainSource.slice(at,end)+'\nreturn gridGeometry;')(THREE,0.015,adaptiveGroundGrid);
const dir=path.join(sourceRoot,'data/terrain/epochs/e1834_harbor_cut');
const meta=JSON.parse(await readFile(path.join(dir,'heightfield.json')));
const bin=await readFile(path.join(dir,meta.bin));
const raw=new Int16Array(bin.buffer,bin.byteOffset,bin.length/2);
const hf={loaded:true,cols:meta.cols,rows:meta.rows,cellM:meta.cell_m,originE:meta.origin_e,originN:meta.origin_n,
 data:Float32Array.from(raw,v=>v*meta.scale+meta.offset)};
hf.sample=(e,n)=>{let x=(e-hf.originE)/hf.cellM,y=(n-hf.originN)/hf.cellM;
 x=Math.max(0,Math.min(hf.cols-1.001,x));y=Math.max(0,Math.min(hf.rows-1.001,y));
 const c=Math.floor(x),r=Math.floor(y),u=x-c,v=y-r,h=(c,r)=>hf.data[r*hf.cols+c];
 return (h(c,r)*(1-u)+h(c+1,r)*u)*(1-v)+(h(c,r+1)*(1-u)+h(c+1,r+1)*u)*v;};
const dataBase=pathToFileURL(path.join(sourceRoot,'data/'));
const frontageSource=await readFile(path.join(sourceRoot,'renderers/web/js/frontage.js'),'utf8');
const frontage=await import(modURL(frontageSource.replace("from 'three'",`from '${threeURL}'`)
 .replace("import { resolveBases } from './scene-loader.js';","const resolveBases=()=>({assetBase:new URL('file:///tmp/t2037-no-assets/')});")
 .replace("from './gates.js'",`from '${pathToFileURL(path.join(sourceRoot,'renderers/web/js/gates.js')).href}'`)
 +'\nexport {timberBuf,buildWalk,buildCrossing};'));
globalThis.fetch=async(url)=>{const file=fileURLToPath(url);if(!file.startsWith(path.join(sourceRoot,'data/')))return {ok:false,status:404};
 return {ok:true,json:async()=>JSON.parse(await readFile(file,'utf8'))};};
globalThis.document={createElement:()=>({getContext:()=>null})};
let footprints=[];
const terrain={surfaceHeight:(e,n)=>hf.sample(e,n),isWater:(e,n)=>hf.sample(e,n)<0.015,
 protectGroundUnder:pts=>{footprints=pts;}};
let layer=await frontage.createFrontage({dataBase,terrain});
const allWalks=layer.walks;
layer.dispose();layer=null;
const originalGeometry=gridGeometry(hf,baseStride);
const original={position:originalGeometry.attributes.position.array,index:originalGeometry.index.array,
 stats:{triangles:originalGeometry.index.count/3}};
const adaptiveGeometry=gridGeometry(hf,baseStride,footprints);
const adaptive={position:adaptiveGeometry.attributes.position.array,index:adaptiveGeometry.index.array,stats:adaptiveGeometry.userData.adaptiveGround};
const allPts=allWalks.flatMap(w=>w.centreline_local_enu_m??[]);
const bounds={minE:Math.min(...allPts.map(p=>p[0]))-5,maxE:Math.max(...allPts.map(p=>p[0]))+5,
 minN:Math.min(...allPts.map(p=>p[1]))-5,maxN:Math.max(...allPts.map(p=>p[1]))+5};
// Exact planar overlap audit: maximum of two affine surfaces occurs
// at a vertex of their clipped intersection, including vertices between our
// regular top-face samples. This is geometric coverage, not GPU visibility.
function exactSurface(mesh){const p=mesh.position,idx=mesh.index,cell=15,buckets=new Map();
 for(let k=0;k<idx.length;k+=3){const tri=[0,1,2].map(j=>{const v=idx[k+j]*3;return[p[v],-p[v+2],p[v+1]+baseOffset];});
  const es=tri.map(p=>p[0]),ns=tri.map(p=>p[1]);
  const loE=Math.min(...es),hiE=Math.max(...es),loN=Math.min(...ns),hiN=Math.max(...ns);
  if(hiE<bounds.minE||loE>bounds.maxE||hiN<bounds.minN||loN>bounds.maxN)continue;
  for(let e=Math.floor(loE/cell);e<=Math.floor(hiE/cell);e++)for(let n=Math.floor(loN/cell);n<=Math.floor(hiN/cell);n++){
   const key=e+','+n;if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push({k,tri});}}
 return top=>{const seen=new Set();let max=-Infinity,point=null;
  const es=top.map(p=>p[0]),ns=top.map(p=>p[1]);
  for(let e=Math.floor(Math.min(...es)/cell);e<=Math.floor(Math.max(...es)/cell);e++)
  for(let n=Math.floor(Math.min(...ns)/cell);n<=Math.floor(Math.max(...ns)/cell);n++)
  for(const{k,tri}of buckets.get(e+','+n)??[]){if(seen.has(k))continue;seen.add(k);let poly=top;
   for(let i=0;i<3&&poly.length;i++){const a=tri[i],b=tri[(i+1)%3],side=p=>(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]);
    const next=[];for(let j=0;j<poly.length;j++){const x=poly[j],y=poly[(j+1)%poly.length],sx=side(x),sy=side(y),ix=sx>=-1e-10,iy=sy>=-1e-10;
     if(ix)next.push(x);if(ix!==iy){const t=sx/(sx-sy);next.push(x.map((v,h)=>v+(y[h]-v)*t));}}poly=next;}
   if(!poly.length)continue;
   const[a,b,c]=tri,den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);
   for(const p of poly){const u=((b[1]-c[1])*(p[0]-c[0])+(c[0]-b[0])*(p[1]-c[1]))/den;
    const v=((c[1]-a[1])*(p[0]-c[0])+(a[0]-c[0])*(p[1]-c[1]))/den;
    const ground=u*a[2]+v*b[2]+(1-u-v)*c[2],excess=ground-p[2];
    if(excess>max){max=excess;point={e:p[0],n:p[1],deck:p[2],ground};}}
  }return{max,point};};}
const exact={before:exactSurface(original),after:exactSurface(adaptive)};
function edgeAudit(mesh,field=hf){const edges=new Map(),p=mesh.position,idx=mesh.index;
 for(let i=0;i<idx.length;i+=3)for(const [a,b]of [[idx[i],idx[i+1]],[idx[i+1],idx[i+2]],[idx[i+2],idx[i]]]){
 const key=Math.min(a,b)+','+Math.max(a,b);edges.set(key,(edges.get(key)??0)+1);}
 let internalOpen=0,nonmanifold=0,boundary=0,down=0,degenerate=0;
 for(let i=0;i<idx.length;i+=3){const[a,b,c]=[idx[i]*3,idx[i+1]*3,idx[i+2]*3];
 const cross=(p[b]-p[a])*(-p[c+2]+p[a+2])-(-p[b+2]+p[a+2])*(p[c]-p[a]);
 if(cross<0)down++;if(cross===0)degenerate++;}
 const eMax=field.originE+(field.cols-1)*field.cellM,nMax=field.originN+(field.rows-1)*field.cellM;
 for(const[key,count]of edges){if(count>2)nonmanifold++;if(count!==1)continue;
 const[a,b]=key.split(',').map(Number),ae=p[a*3],an=-p[a*3+2],be=p[b*3],bn=-p[b*3+2];
 if((ae===be&&(ae===field.originE||ae===eMax))||(an===bn&&(an===field.originN||an===nMax)))boundary++;else internalOpen++;}
 return {internalOpen,nonmanifold,boundary,down,degenerate};}
const rows=[];
for(const walk of allWalks){
 const buf=frontage.timberBuf(),problems=[];
 (walk.kind==='board_crossing'?frontage.buildCrossing:frontage.buildWalk)(buf,walk,terrain,1,problems);
 assert.deepEqual(problems,[]);
 // The draw uploads Float32 positions. Test those, not higher-precision JS arrays.
 const positions=Float32Array.from(buf.pos);
 const row={id:walk.id,kind:walk.kind,topTriangles:0,beforeBuried:0,afterBuried:0,
  beforeMax:-Infinity,afterMax:-Infinity,beforeMissing:0,afterMissing:0};
 for(let i=0;i<positions.length;i+=9){if(buf.nrm[i+1]<.99)continue;
  row.topTriangles++;
  const top=[0,1,2].map(j=>[positions[i+j*3],-positions[i+j*3+2],positions[i+j*3+1]]);
  for(const name of ['before','after']){
   const result=exact[name](top);
   if(!Number.isFinite(result.max)){row[name+'Missing']++;continue;}
   if(result.max>1e-6)row[name+'Buried']++;
   if(result.max>row[name+'Max']){row[name+'Max']=result.max;row[name+'Worst']=result.point;}
  }
 }
 rows.push(row);
}
const subset=predicate=>{
 const group=rows.filter(predicate);
 return {walks:group.length,topTriangles:group.reduce((a,r)=>a+r.topTriangles,0),
  beforeBuried:group.reduce((a,r)=>a+r.beforeBuried,0),afterBuried:group.reduce((a,r)=>a+r.afterBuried,0),
  beforeMissing:group.reduce((a,r)=>a+r.beforeMissing,0),afterMissing:group.reduce((a,r)=>a+r.afterMissing,0),
  beforeMax:Math.max(...group.map(r=>r.beforeMax)),afterMax:Math.max(...group.map(r=>r.afterMax))};
};
const edges={before:edgeAudit(original),after:edgeAudit(adaptive)};
const all=subset(()=>true);
check('only emitted crossings request terrain protection',()=>{
 assert.deepEqual(footprints.map(f=>f.id).sort(),allWalks.filter(w=>w.kind==='board_crossing').map(w=>w.id).sort());
 assert.ok(footprints.length>0);
});
check('baseline reproduces buried crossing top faces',()=>{
 assert.ok(all.beforeBuried>0,'the unprotected witness must expose the original defect');
 assert.ok(all.beforeMax>.1,'the measured defect exceeds 100 mm');
 assert.equal(rows.filter(r=>r.kind!=='board_crossing').reduce((a,r)=>a+r.beforeBuried,0),0);
});
check('all actual emitted top faces clear protected terrain',()=>{
 assert.equal(all.afterBuried,0);assert.equal(all.beforeMissing,0);assert.equal(all.afterMissing,0);
 assert.ok(all.afterMax<-.04,'retain at least 40 mm of geometric clearance');
});
check('adaptive transitions share every internal edge with upward winding',()=>{
 for(const mesh of Object.values(edges)){
  assert.equal(mesh.internalOpen,0);assert.equal(mesh.nonmanifold,0);
  assert.equal(mesh.down,0);assert.equal(mesh.degenerate,0);
 }
 assert.equal(edges.after.boundary,edges.before.boundary);
});
check('crossing refinement stays local and below its measured 9000-triangle allocation',()=>{
 assert.ok(adaptive.stats.refinedCells>0);
 assert.ok(adaptive.stats.protectedCells<200);
 assert.ok(adaptive.stats.triangles-original.stats.triangles<=9000);
});
check('partial edge cells keep their shared transitions closed',()=>{
 const field={loaded:true,cols:10,rows:9,cellM:1,originE:0,originN:0,data:new Float32Array(90).fill(1)};
 field.data[2*10+2]=.5;
 field.sample=(e,n)=>{const c=Math.min(8,Math.floor(e)),r=Math.min(7,Math.floor(n)),u=e-c,v=n-r;
  const at=(c,r)=>field.data[r*10+c];return(at(c,r)*(1-u)+at(c+1,r)*u)*(1-v)+(at(c,r+1)*(1-u)+at(c+1,r+1)*u)*v;};
 const mesh=adaptiveGroundGrid(field,6,.025,[{pts:[[1,1],[3,1],[3,3],[1,3]]}]);
 assert.equal(mesh.stats.refinedCells,1);
 const audit=edgeAudit(mesh,field);
 assert.equal(audit.internalOpen,0);assert.equal(audit.nonmanifold,0);
 assert.equal(audit.down,0);assert.equal(audit.degenerate,0);
});
check('repeated terrain replacement disposes each geometry once',()=>{
 const geometries=[];
 const make=()=>{const geometry={disposed:0,userData:{adaptiveGround:{}},dispose(){this.disposed++;}};geometries.push(geometry);return geometry;};
 const groundBase={geometry:make()},disposables=[groundBase.geometry];
 const body=terrainSource.match(/protectGroundUnder\(footprints\) \{([\s\S]*?)\n    \},/)?.[1];
 assert.ok(body,'the terrain API exists');
 const run=new Function('groundBase','heightfield','gridGeometry','GROUND_BASE_STEP','disposables',
  `return function(footprints){${body}}`)(groundBase,{loaded:true},make,baseStride,disposables);
 run([]);run([]);
 assert.equal(disposables.length,1);assert.equal(disposables[0],groundBase.geometry);
 for(const d of disposables)d.dispose();
 assert.ok(geometries.every(g=>g.disposed===1));
});
// Exercise the actual frontage publication path with one accepted default-width
// crossing, one too-short rejected crossing, and an ordinary longitudinal walk.
let fixtureProtection;
const savedFetch=globalThis.fetch;
globalThis.fetch=async url=>{
 const file=fileURLToPath(url);
 if(file.endsWith('/frontage/index.json'))return{ok:true,json:async()=>({frontage:[{id:'fixture',file:'fixture.json'}]})};
 if(file.endsWith('/frontage/fixture.json'))return{ok:true,json:async()=>({id:'fixture',walks:[
  {id:'accepted',kind:'board_crossing',centreline_local_enu_m:[[0,0],[6,0]]},
  {id:'rejected',kind:'board_crossing',centreline_local_enu_m:[[0,2],[.1,2]]},
  {id:'walk',kind:'plank_walk',centreline_local_enu_m:[[0,4],[6,4]]},
 ]})};
 return{ok:false,status:404};
};
const fixtureLayer=await frontage.createFrontage({dataBase,terrain:{surfaceHeight:()=>1,isWater:()=>false,
 protectGroundUnder:value=>{fixtureProtection=value;}}});
globalThis.fetch=savedFetch;
check('publication protects accepted crossings at their actual default width',()=>{
 assert.deepEqual(fixtureProtection.map(f=>f.id),['accepted']);
 const north=fixtureProtection[0].pts.map(p=>p[1]);
 assert.equal(Math.max(...north)-Math.min(...north),1.22);
 assert.equal(fixtureLayer.census.crossings,1);
});
fixtureLayer.dispose();
const report={checks,scope:'CPU geometry: all Float32 emitted walk, crossing and kerb top faces. Each planar overlap is clipped against actual rendered base triangles; no browser, GPU, reach, shader or visual claim.',
 baseStride,baseOffset,cellM:hf.cellM,origin:[hf.originE,hf.originN],footprints:footprints.length,
 fingerprints:{terrain:createHash('sha256').update(terrainSource).digest('hex'),
  terrainBase:createHash('sha256').update(await readFile(path.join(sourceRoot,'renderers/web/js/terrain-base.js'))).digest('hex'),
  frontage:createHash('sha256').update(frontageSource).digest('hex'),heightfield:createHash('sha256').update(bin).digest('hex')},
 before:original.stats,after:adaptive.stats,additionalTriangles:adaptive.stats.triangles-original.stats.triangles,edges,
 subsets:{all,southWater:subset(r=>/south_water/.test(r.id)),southWaterLongitudinal:subset(r=>/south_water/.test(r.id)&&r.kind==='plank_walk')},
 worstBefore:rows.reduce((a,r)=>r.beforeMax>a.beforeMax?r:a),worstAfter:rows.reduce((a,r)=>r.afterMax>a.afterMax?r:a)};
originalGeometry.dispose();adaptiveGeometry.dispose();
if(process.argv.includes('--json')) console.log(JSON.stringify(report,null,2));
else {
 for(const name of checks)console.log('PASS '+name);
 console.log(`PASS plank ground: ${checks.length} checks; ${all.topTriangles} top triangles, ${all.beforeBuried} buried before / ${all.afterBuried} after; ${(all.afterMax*-1000).toFixed(2)} mm minimum clearance; +${report.additionalTriangles} triangles`);
}
if(process.argv.includes('--baseline')){
 console.error(`FAIL baseline: ${all.beforeBuried} top triangles intersect unprotected terrain by up to ${(all.beforeMax*1000).toFixed(2)} mm`);
 process.exitCode=1;
}

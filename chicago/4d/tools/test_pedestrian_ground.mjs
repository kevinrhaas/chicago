/** Pure mask/Float32 support controls. No world, GPU, feet-contact or phone acceptance claim. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { performance } from 'node:perf_hooks';
import { definitelyCutByRedMask, isPedestrianSurface, createMaskedPedestrianHeight } from '../renderers/web/js/pedestrian-ground.js';
import { deckGroundHeight, figureGroundHeight } from '../renderers/web/js/deck-surface.js';
import { createLazyRoadTriangleHeight } from '../renderers/web/js/road-triangle-height.js';

if (process.argv.slice(2).some(arg => arg !== '--check')) throw new Error('Only --check is supported');
let checks = 0;
const check = (condition, why) => { assert(condition, why); checks++; };
const near = (a, b, why, eps = 1e-9) => check(Math.abs(a - b) <= eps, `${why}: ${a} versus ${b}`);
const mask = { image: { data: new Uint8Array([255,255,255,255]), width: 2, height: 2 }, flipY: false };
const box = { x: 0, y: 0, z: 1, w: 1 };
check(definitelyCutByRedMask(mask, box, .5, -.5), 'four actual red texels prove the shader discards');
mask.image.data[0] = 128;
check(definitelyCutByRedMask(mask, box, .5, -.5), 'unsigned128 remains strictly above shader0.5');
mask.image.data[0] = 127;
check(!definitelyCutByRedMask(mask, box, .5, -.5), 'mixed blend edge conservatively retains original floor');
mask.image.data.fill(255);
for (const [e,n] of [[0,-.5],[1,-.5],[.5,0],[.5,-1],[2,-2],[NaN,0]])
  check(!definitelyCutByRedMask(mask, box, e, n), 'strict shader-box boundary/outside/nonfinite stays unchanged');
mask.flipY = true; check(!definitelyCutByRedMask(mask, box, .5, -.5), 'unqualified flipped texture rejected'); mask.flipY = false;
check(!definitelyCutByRedMask({ image: { ...mask.image, data: new Uint8Array(16) } }, box, .5, -.5), 'RGBA data cannot masquerade as red texture');

// Execute the exact active-material admission method, with interface-only
// material/constant doubles. No duplicate implementation of that method.
const terrainSource = fs.readFileSync(new URL('../renderers/web/js/terrain.js', import.meta.url), 'utf8');
const at = terrainSource.indexOf('pedestrianGroundCutAt(e, n, expectedMask) {');
const end = terrainSource.indexOf('\n    },', at);
assert(at > 0 && end > at);
const THREE = { RedFormat: 1, UnsignedByteType: 2, LinearFilter: 3, ClampToEdgeWrapping: 4 };
Object.assign(mask, { format:1, type:2, minFilter:3, magFilter:3, wrapS:4, wrapT:4, generateMipmaps:false });
const vector = () => ({ ...box, equals(other) { return ['x','y','z','w'].every(key => this[key] === other[key]); } });
const cut = () => ({ on:{value:1},tex:{value:mask},box:{value:vector()} });
const groundMat = { userData:{cut:cut()} }, groundBase = { material:{userData:{cut:cut()}} };
const method = Function('groundMat','groundBase','THREE','definitelyCutByRedMask',
  `return {${terrainSource.slice(at,end+6)}}.pedestrianGroundCutAt;`)(groundMat,groundBase,THREE,definitelyCutByRedMask);
check(method(.5,-.5,mask), 'both actual material-cut interfaces admit the same mask');
for (const owner of [groundMat.userData.cut,groundBase.material.userData.cut]) {
  owner.on.value = 0; check(!method(.5,-.5,mask), 'either disabled material retains raw terrain'); owner.on.value = 1;
  owner.on.value = NaN; check(!method(.5,-.5,mask), 'invalid material toggle cannot admit support'); owner.on.value = 1;
  owner.tex.value = {}; check(!method(.5,-.5,mask), 'either changed texture retains raw terrain'); owner.tex.value = mask;
}
groundBase.material.userData.cut.box.value.x = .1;
check(!method(.5,-.5,mask), 'near/base uniform-box disagreement rejects replacement');
groundBase.material.userData.cut.box.value.x = 0;
for (const [key,value] of [['format',8],['type',8],['minFilter',8],['magFilter',8],['wrapS',8],['wrapT',8],['generateMipmaps',true]]) {
  const old = mask[key]; mask[key] = value; check(!method(.5,-.5,mask), 'unqualified sampler state rejected'); mask[key] = old;
}

function mesh(cls, points, { marked = true, indexed = false, translation = [0,0,0] } = {}) {
  const array = new Float32Array(points.flatMap(([e,n,y]) => [e,y,-n]));
  const position = { array, count:array.length/3, itemSize:3,
    getX:i=>array[i*3],getY:i=>array[i*3+1],getZ:i=>array[i*3+2] };
  const indices = indexed ? new Uint16Array([0,1,2,0,2,3]) : null;
  const index = indices && {array:indices,count:indices.length,getX:i=>indices[i]};
  const elements = new Float64Array([1,0,0,0,0,1,0,0,0,0,1,0,...translation,1]);
  return { userData:{cls,pedestrianSurface:marked},matrixWorld:{elements},updateWorldMatrix(){},
    geometry:{index,getAttribute:name=>name==='position'?position:null} };
}
const plane = mesh('parkway', [[0,0,3],[4,0,3.08],[4,4,3.04],[0,4,2.96]], { indexed:true,translation:[1393.2,1.3,3247.955] });
const prop = mesh('curb', [[0,0,30],[4,0,30],[4,4,30]], {marked:false,translation:[1393.2,0,3247.955]});
const road = mesh('carriageway', [[0,0,20],[4,0,20],[4,4,20]], {translation:[1393.2,0,3247.955]});
const vertical = mesh('curb', [[2,0,10],[2,4,10],[2,4,20]], {translation:[1393.2,0,3247.955]});
check(isPedestrianSurface(plane) && !isPedestrianSurface(prop) && !isPedestrianSurface(road), 'explicit top-surface marker excludes props and roadways');
const original = Buffer.from(plane.geometry.getAttribute('position').array.buffer).toString('hex');
let admitted = false;
const support = createMaskedPedestrianHeight(()=>[plane,prop,road,vertical],()=>admitted);
check(support.heightAt(1395.2,-3245.955) === null && !support.reading().initialized, 'no mask admission never builds an index');
admitted = true;
const first = performance.now(), mid = support.heightAt(1395.2,-3245.955), buildMs = performance.now()-first;
near(mid,4.32,'transformed actual Float32 top plane',3e-7);
near(support.heightAt(1395.2,-3243.955),4.3,'vertical face cannot become a floor',3e-7);
check(support.heightAt(1300,-3200) === null, 'mask without actual support keeps fallback');
// Independent plane equation on the represented Float32 vertices, rather than
// a copy of the production bucket/barycentric reader.
function planeAt(points,e,n) {
  const [a,b,c] = points;
  const u=b.map((x,i)=>x-a[i]),v=c.map((x,i)=>x-a[i]);
  const normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];
  return a[1]-(normal[0]*(e-a[0])+normal[2]*(-n-a[2]))/normal[1];
}
const p=plane.geometry.getAttribute('position'),m=plane.matrixWorld.elements;
const world=i=>[p.getX(i)+m[12],p.getY(i)+m[13],p.getZ(i)+m[14]];
let maxResidual=0;const hot=performance.now();
for(let i=0;i<10000;i++){
  const x=.01+3.98*((i*137%997)/996),n=.01+3.98*((i*269%991)/990);
  const e=1393.2+x,north=-3247.955+n;
  const expected=planeAt((n<=x?[0,1,2]:[0,2,3]).map(world),e,north);
  maxResidual=Math.max(maxResidual,Math.abs(support.heightAt(e,north)-expected));
}
const queryMs=performance.now()-hot;
check(maxResidual<1e-10,'independent represented-triangle plane agrees over10000 points');
check(support.reading().duplicated_xyz_bytes===0 && support.reading().owned_buffer_bytes>0,'index aliases retained attributes without XYZ duplication');
check(Buffer.from(p.array.buffer).toString('hex')===original,'no geometry or vertex buffer mutation');
const roadReader=createLazyRoadTriangleHeight(()=>[road]);near(roadReader.heightAt(1395.2,-3245.955),20,'original roadway reader untouched');roadReader.dispose();
admitted=false;check(support.heightAt(1395.2,-3245.955)===null,'cleared mask immediately returns old floor');
const reading=support.reading();support.dispose();admitted=true;
check(support.heightAt(1395.2,-3245.955)===null && support.reading().owned_buffer_bytes===0,'disposed support cannot resurrect');

const terrain={surfaceHeight:()=>6,isWater:()=>false};
const deck={y:6.4,pts:[[-2,-2],[2,-2],[2,2],[-2,2]]};
near(figureGroundHeight(terrain,[],0,0,0,null),6,'no admitted street keeps raw terrain');
near(figureGroundHeight(terrain,[],0,0,0,5.97),5.97,'zero yard lift cannot reinstate hidden terrain');
near(figureGroundHeight(terrain,[deck],0,0,0,5.97),6.4,'higher scalar deck remains authoritative');
near(figureGroundHeight(terrain,[],0,0,.02,5.97),6.02,'positive laid yard surface remains authoritative');
near(deckGroundHeight(terrain,[],0,0),6,'old deck helper signature unchanged');
const water={surfaceHeight:()=>-2,isWater:()=>true};
near(figureGroundHeight(water,[deck],0,0,0,5.97),6.4,'water and deck precedence unchanged');
near(figureGroundHeight(water,[],0,0,0,5.97),-2,'human ground never substitutes the navigation water barrier');
const profile={y:6.1,pts:[[-2,-2],[2,-2],[2,2],[-2,2]],profile:{version:1,axis:'local_x',stations_m:[[0,6.1],[2,6.8],[4,6.1]]},profileFrame:{e0:-2,n0:0,cos:1,sin:0}};
near(figureGroundHeight(terrain,[profile],0,0,0,5.97),6.8,'declared profiled deck still wins');
const main=fs.readFileSync(new URL('../renderers/web/js/main.js',import.meta.url),'utf8');
check(/String\(YEAR\) === '1904' \? streetGrid\.pedestrianHeight/.test(main),'integration is scoped to1904');
check(/const figureGround = [^;]*yards\.groundLiftAt/s.test(main),'existing actual yard lift callback retained');
console.log(JSON.stringify({status:'PASS',checks,fixtureBuildMs:buildMs,fixture10000QueryMs:queryMs,maxIndependentPlaneResidual:maxResidual,
  fixtureIndex:reading,qualification:'Synthetic Float32/mask/composition controls only; actual district cost and post-change feet remain unmeasured'}));

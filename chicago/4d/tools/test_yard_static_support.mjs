// CPU-only regression: real Three BatchedMesh, then simulated actual upload release.
import assert from 'node:assert/strict';
import { register } from 'node:module';
const vendor = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s,c,next){if(s==='three')return{url:'${vendor}',shortCircuit:true};return next(s,c);}`)}`, import.meta.url);
const T = await import('three');
const { retainYardStaticSupport } = await import('../renderers/web/js/yard-static-support.js');
const geometry = new T.BufferGeometry();
geometry.setAttribute('position', new T.Float32BufferAttribute([0,1,0, 1,1.1,0, 1,1.3,-1, 0,1.2,-1],3));
geometry.setIndex([0,1,2,0,2,3]);
const mesh = new T.BatchedMesh(1,4,6,new T.MeshBasicMaterial({side:T.DoubleSide}));
mesh.addInstance(mesh.addGeometry(geometry)); mesh.name='yard-worn_earth';
const group = new T.Group();group.add(mesh);group.updateMatrixWorld(true);
const region={id:'test',record_id:'yard',bounds_enu_m:[[-.05,-.05],[1.05,1.05]]};
const problems=[],cache=retainYardStaticSupport(group,[region],problems);
assert.equal(problems.length,0);assert.equal(cache.census.triangles,2);assert.equal(cache.census.bytes,144);
const ray = new T.Raycaster(), rows=[];
for(const e of [.1,.5,.9])for(const n of [.1,.5,.9]){
 ray.set(new T.Vector3(e,5,-n),new T.Vector3(0,-1,0));
 const actual=ray.intersectObject(mesh,false)[0]?.point.y;
 const retained=cache.heightAt(e,n,'yard','test');
 assert(Number.isFinite(actual));assert(Math.abs(actual-retained)<1e-12);
 rows.push({e,n,actual_triangle_y:actual,retained_y:retained});
}
// Same observable release operations used by normal upload-release.js, no
// keep-geometry switch and no change to RELEASE_KEEP.
mesh.geometry.getAttribute('position').array=null;
mesh.geometry.index.array=new mesh.geometry.index.array.constructor(0);
for(const row of rows)assert(Math.abs(cache.heightAt(row.e,row.n,'yard','test')-row.actual_triangle_y)<1e-12);
assert.equal(cache.heightAt(2,2,'yard','test'),null);assert.equal(cache.heightAt(.5,.5,'other','test'),null);
assert.equal(cache.heightAt(.5,.5,'yard','missing'),null);
assert.equal(mesh.geometry.attributes.position.array,null);assert.equal(mesh.geometry.index.array.length,0);
const retainedBytes=cache.census.bytes;cache.dispose();assert.equal(cache.heightAt(.5,.5,'yard','test'),null);assert.equal(cache.census.bytes,0);
const tooManyProblems=[];const tooMany=retainYardStaticSupport(group,[region,{...region,id:'second'}],tooManyProblems);
assert(tooManyProblems.length===1&&tooMany.census.bytes===0);
const releasedProblems=[];const unavailable=retainYardStaticSupport(group,[region],releasedProblems);
assert(releasedProblems.length===1&&unavailable.census.bytes===0);assert.equal(unavailable.heightAt(.5,.5,'yard','test'),null);
const result={status:'PASS finite CPU real-BatchedMesh support regression; no browser/GPU/horse build/app writes',actual_triangle_comparisons:rows,retained_typed_array_bytes_before_disposal:retainedBytes,source_arrays_released:true,cache_works_after_release:true,disposal_releases_cache:true,wrong_region_record_outside_return_null:true,region_cap_fail_closed:true,late_snapshot_fail_closed:true,scope_limits:'Synthetic two-triangle reference fixture only. Actual published yard snapshot count/bytes/grounding and normal mobile upload-release require separately released app/browser readback.'};
console.log('YARD STATIC SUPPORT PASS —9 actual-triangle raycast comparisons,144B retained, source-array release/refusal/caps/disposal; actual yard/mobile remains separate');

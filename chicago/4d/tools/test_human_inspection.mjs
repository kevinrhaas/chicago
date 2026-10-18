// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
// Uses the pinned application vendor directly: no npm dependency or WebGL.
import * as T from '../renderers/web/vendor/three-0.185.1/three.module.js';
const source=await readFile(new URL('./human_frame_compare.js',import.meta.url),'utf8');
const pure=source.slice(source.indexOf('export function maximumPointDisplacement'),source.indexOf('export async function compareFrameRepair')).replace('export function','function');
const ctx=vm.createContext({T,console});vm.runInContext(pure,ctx);
function model(defaultWeight=.4,scale=1){
 const geo=new T.BufferGeometry();
 geo.setAttribute('position',new T.Float32BufferAttribute([0,0,0,.1,1.7,0,-.1,1.7,0],3));
 geo.setAttribute('skinIndex',new T.Uint16BufferAttribute(new Array(12).fill(0),4));
 geo.setAttribute('skinWeight',new T.Float32BufferAttribute([1,0,0,0,1,0,0,0,1,0,0,0],4));
 geo.morphTargetsRelative=true;
 geo.morphAttributes.position=[new T.Float32BufferAttribute([0,.01,0,0,.01,0,0,.01,0],3)];
 const mesh=new T.SkinnedMesh(geo,new T.MeshBasicMaterial());mesh.name='adult';
 const bone=new T.Bone();bone.name='root';mesh.add(bone);mesh.bind(new T.Skeleton([bone]));
 mesh.morphTargetInfluences[0]=defaultWeight;
 const scene=new T.Scene();scene.add(mesh);scene.scale.setScalar(scale);scene.updateMatrixWorld(true);
 return{scene,meshes:[mesh],bind:[],animations:[new T.AnimationClip('expression',1,[new T.NumberKeyframeTrack('adult.morphTargetInfluences[0]',[0,1],[.2,.8])])]};
}
const a=model(.4),b=model(.8);ctx.bind(a);ctx.bind(b);a.meshes[0].morphTargetInfluences[0]=.9;ctx.pose(a,null,0);ctx.pose(b,null,0);
assert.equal(a.meshes[0].morphTargetInfluences[0],.4);
assert.equal(b.meshes[0].morphTargetInfluences[0],.8);
assert.ok(Math.abs(ctx.maximumPointDisplacement(ctx.surface(a),ctx.surface(b))-.004)<1e-8,'default morph difference survives actual CPU skinning');
ctx.pose(a,'expression',1);assert.ok(Math.abs(a.meshes[0].morphTargetInfluences[0]-.8)<1e-6,'terminal clamped sample reaches final value');
ctx.pose(a,'expression',.5);assert.ok(Math.abs(a.meshes[0].morphTargetInfluences[0]-.5)<1e-6,'next sample resets action time');
ctx.pose(a,null,0);assert.equal(a.meshes[0].morphTargetInfluences[0],.4,'post-animation default restored');
assert.throws(()=>ctx.maximumPointDisplacement([],[]),/layout/);
const tiny=model(.4,.001);ctx.bind(tiny);ctx.pose(tiny,null,0);assert.throws(()=>ctx.metricSpan(ctx.surface(tiny)),/metric/);
assert.ok(ctx.metricSpan(ctx.surface(a)).maximum_axis_span_m>1.6);
const duplicate=model();duplicate.animations.push(duplicate.animations[0]);assert.throws(()=>ctx.clipFacts(duplicate),/ambiguous/);
// Dormant target: neither defaults nor the bone-only walk activates it.
const dormantRaw=model(0),dormantClean=model(0);
const boneWalk=()=>new T.AnimationClip('walk',1,[new T.QuaternionKeyframeTrack('root.quaternion',[0,1],[0,0,0,1,0,Math.sin(.1),0,Math.cos(.1)])]);
for(const m of [dormantRaw,dormantClean])m.animations=[boneWalk()];
dormantClean.meshes[0].geometry.morphAttributes.position[0].array.fill(0);
for(let i=1;i<9;i+=3)dormantClean.meshes[0].geometry.morphAttributes.position[0].array[i]=.02;
ctx.bind(dormantRaw);ctx.bind(dormantClean);
ctx.pose(dormantRaw,null,0);ctx.pose(dormantClean,null,0);assert.equal(ctx.maximumPointDisplacement(ctx.surface(dormantRaw),ctx.surface(dormantClean)),0);
const dormant=ctx.sampleNamedMorphs(dormantRaw,dormantClean);
assert.equal(dormant.receipts.length,2);assert.equal(dormant.nonrest_clip,'walk');
assert.ok(dormant.receipts.every(r=>Math.abs(r.maximum_vertex_delta_m-.01)<1e-7));
assert.equal(dormantRaw.meshes[0].morphTargetInfluences[0],0);assert.equal(dormantClean.meshes[0].morphTargetInfluences[0],0);
const defaultRaw=model(.4),defaultClean=model(.4);ctx.bind(defaultRaw);ctx.bind(defaultClean);
const retained=ctx.sampleNamedMorphs(defaultRaw,defaultClean);assert.equal(retained.maximum_vertex_delta_m,0);
assert.equal(defaultRaw.meshes[0].morphTargetInfluences[0],.4);assert.equal(defaultClean.meshes[0].morphTargetInfluences[0],.4);
const multiRaw=model(.4),multiClean=model(.4);let contextChecks=0;
for(const m of [multiRaw,multiClean]){
 const mesh=m.meshes[0];mesh.geometry.morphAttributes.position.push(new T.Float32BufferAttribute([0,0,.005,0,0,.005,0,0,.005],3));
 mesh.morphTargetDictionary={face:0,otherShape:1};mesh.morphTargetInfluences=[.4,.35];
 const original=mesh.getVertexPosition;
 mesh.getVertexPosition=function(i,v){if(this.morphTargetInfluences[0]===1){assert.equal(this.morphTargetInfluences[1],.35);contextChecks++;}if(this.morphTargetInfluences[1]===1){assert.equal(this.morphTargetInfluences[0],.4);contextChecks++;}return original.call(this,i,v);};
 ctx.bind(m);
}
const multi=ctx.sampleNamedMorphs(multiRaw,multiClean);assert.equal(multi.maximum_vertex_delta_m,0);assert.ok(contextChecks>0);
assert.deepEqual(multiRaw.meshes[0].morphTargetInfluences,[.4,.35]);assert.deepEqual(multiClean.meshes[0].morphTargetInfluences,[.4,.35]);

console.log('PASS: actual vendored Three.js CPU skin/morph regression: defaults, sampled surface difference, terminal clamp/reset, empty surface, metric scale and duplicate clips; plus dormant named-morph delta detection at rest/walk midpoint and default restoration; no resident/WebGL acceptance');

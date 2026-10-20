// SPDX-License-Identifier: GPL-3.0-or-later
import assert from 'node:assert/strict';
import test from 'node:test';
import * as T from '../renderers/web/vendor/three-0.185.1/three.module.js';
import {sampleSoleContact} from './human_sole_contact.mjs';
function fixture({collar=false,soleOnCalf=false}={}){
  const scene=new T.Group(),root=new T.Bone(),left=new T.Bone(),right=new T.Bone(),calfL=new T.Bone(),calfR=new T.Bone();root.name='pelvis';left.name='foot_l';right.name='foot_r';calfL.name='calf_l';calfR.name='calf_r';root.add(left,right,calfL,calfR);scene.add(root);
  const positions=[],indices=[],weights=[];
  for(const x of [.15,-.15])for(const [dx,z]of [[-.05,-.1],[.05,-.1],[0,.15]]){positions.push(x+dx,0,z);indices.push(x>0?1:2,0,0,0);weights.push(1,0,0,0);}
  // A low shoe's collar: above the sole, blended between its own calf and foot.
  if(collar)for(const x of [.15,-.15])for(const [dx,z]of [[-.05,0],[.05,0],[0,.05]]){positions.push(x+dx,.1,z);indices.push(x>0?3:4,x>0?1:2,0,0);weights.push(.6,.4,0,0);}
  // A sole vertex bound mostly to the calf: still the left leg's, but not its foot's.
  if(soleOnCalf){indices.splice(0,4,3,1,0,0);weights.splice(0,4,.95,.05,0,0);}
  const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(positions,3));g.setAttribute('skinIndex',new T.Uint16BufferAttribute(indices,4));g.setAttribute('skinWeight',new T.Float32BufferAttribute(weights,4));
  const mesh=new T.SkinnedMesh(g,new T.MeshBasicMaterial());mesh.name='synthetic_two_shoes';mesh.material.name='footwear__test';scene.add(mesh);scene.updateMatrixWorld(true);mesh.bind(new T.Skeleton([root,left,right,calfL,calfR]));
  const times=[],values=[[],[]];
  for(let k=0;k<=36;k++){const phase=k/36;times.push(phase*1.2);for(let s=0;s<2;s++){const q=(phase+s*.5)%1,duty=.62;let z,y=0;if(q<duty)z=.2232-.72*q;else{const u=(q-duty)/(1-duty),smooth=u**3*(10-15*u+6*u*u),m=-.72*(1-duty);z=-.2232+m*u+(.4464-m)*smooth;y=.065*Math.sin(Math.PI*u)**2;}values[s].push(0,y,z);}}
  const tracks=['foot_l','foot_r'].map((n,i)=>new T.VectorKeyframeTrack(n+'.position',times,values[i],T.InterpolateLinear));
  const clip=new T.AnimationClip('walk',1.2,tracks);clip.userData={speed_m_s:.6,stance_fraction:.62,cycle_duration_s:1.2};
  return {scene,animations:[clip],mesh,left,right};
}
test('actual Three CPU skinned synthetic planted soles; not exported-resident evidence',()=>{const f=fixture();const r=sampleSoleContact(T,f,{raw:true});assert.equal(r.passed,true);assert.equal(r.selection.left.length,3);assert.equal(r.raw_samples.length,1001);assert.ok(r.metrics.maximum_stance_horizontal_drift_m<.001);assert.ok(r.metrics.local_loop_closure_m<1e-6);assert.equal(f.left.position.z,0);});
test('limb identity follows named skin weights through actor yaw',()=>{const f=fixture();f.scene.rotation.y=Math.PI;const r=sampleSoleContact(T,f,{forward_world:[0,0,-1],raw:false});assert.equal(r.passed,true);assert.ok(r.selection.left.every(v=>v.rest_world[0]<0));});
test('stationary sliding animation fails compensated stance drift',()=>{const f=fixture();for(const tr of f.animations[0].tracks)tr.values.fill(0);const r=sampleSoleContact(T,f);assert.equal(r.passed,false);assert.ok(r.metrics.maximum_stance_horizontal_drift_m>.4);});
test('encoded root translation is not cancelled away',()=>{const f=fixture();f.animations[0].tracks.push(new T.VectorKeyframeTrack('pelvis.position',[0,1.2],[0,0,0,0,0,.72]));const r=sampleSoleContact(T,f);assert.equal(r.passed,false);assert.ok(r.metrics.local_loop_closure_m>.7);});
test('ambiguous limb identity refuses',()=>{const f=fixture();f.left.name='unknown';assert.throws(()=>sampleSoleContact(T,f),/ambiguous/);});
test('missing footwear and duplicate walk refuse',()=>{const f=fixture();f.mesh.material.name='skin';assert.throws(()=>sampleSoleContact(T,f),/missing named/);const g=fixture();g.animations.push(g.animations[0]);assert.throws(()=>sampleSoleContact(T,g),/unique walk/);});
test('bad speed and duration refuse',()=>{assert.throws(()=>sampleSoleContact(T,fixture(),{speed_m_s:NaN}),/nonfinite/);assert.throws(()=>sampleSoleContact(T,fixture(),{expected_duration_s:2}),/duration/);});

test('actual loaded metadata comparisons are recorded',()=>{const r=sampleSoleContact(T,fixture());for(const entry of Object.values(r.metadata_comparisons))assert.equal(entry.matched,true);assert.equal(r.metadata_comparisons.speed_m_s.declared,.6);});
test('missing, nonfinite, string or different speed/duty/cycle metadata refuse',()=>{for(const key of ['speed_m_s','stance_fraction','cycle_duration_s'])for(const value of [undefined,NaN,Infinity,'0.6',.1]){const f=fixture();f.animations[0].userData[key]=value;assert.throws(()=>sampleSoleContact(T,f),new RegExp('walk metadata '+key));}const f=fixture();delete f.animations[0].userData;assert.throws(()=>sampleSoleContact(T,f),/walk metadata/);});
test('nonfinite loaded duration refuses explicitly',()=>{const f=fixture();f.animations[0].duration=NaN;assert.throws(()=>sampleSoleContact(T,f),/duration/);});

test('single material ignores geometry groups exactly as Three renderer does',()=>{const f=fixture();f.mesh.geometry.addGroup(3,3,9);const r=sampleSoleContact(T,f);assert.equal(r.passed,true);assert.equal(r.selection.right.length,3);});
test('material arrays honor geometry groups',()=>{const f=fixture(),other=new T.MeshBasicMaterial();other.name='skin';f.mesh.material=[f.mesh.material,other];f.mesh.geometry.addGroup(0,3,1);f.mesh.geometry.addGroup(3,3,0);assert.throws(()=>sampleSoleContact(T,f),/missing named left/);});

test('a shoe collar blended with its own calf is that leg, and the walk still passes (T-1789)',()=>{const r=sampleSoleContact(T,fixture({collar:true}));assert.equal(r.passed,true);assert.equal(r.selection.left.length,3);assert.ok(r.selection.left.every(v=>v.rest_world[1]===0));});
test('a sole vertex bound to the calf rather than the foot refuses',()=>{assert.throws(()=>sampleSoleContact(T,fixture({soleOnCalf:true})),/sole vertex not bound to its left foot/);});
test('a collar split between the two legs is still ambiguous',()=>{const f=fixture({collar:true});const w=f.mesh.geometry.attributes.skinIndex;w.setXYZW(6,3,2,0,0);w.needsUpdate=true;assert.throws(()=>sampleSoleContact(T,f),/ambiguous/);});

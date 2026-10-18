// SPDX-License-Identifier: GPL-3.0-or-later
// Optional CPU-only loaded-skin comparison. No renderer/placement or Blender work.
import * as T from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { loadMeshoptDecoder } from '/runtime/renderers/web/js/scene-loader.js';

export function maximumPointDisplacement(a,b){
  if(!a.length||a.length!==b.length||a.length%3)throw Error('surface sample layout differs');
  let max=0;for(let i=0;i<a.length;i+=3){const d=Math.hypot(a[i]-b[i],a[i+1]-b[i+1],a[i+2]-b[i+2]);if(!Number.isFinite(d))throw Error('nonfinite surface sample');max=Math.max(max,d);}return max;
}
function release(scene){const geometries=new Set(),materials=new Set(),textures=new Set();scene.traverse(o=>{if(o.isMesh){geometries.add(o.geometry);for(const m of[].concat(o.material)){materials.add(m);for(const value of Object.values(m))if(value?.isTexture)textures.add(value);}}});for(const g of geometries)g.dispose();for(const t of textures){t.image?.close?.();t.dispose();}for(const m of materials)m.dispose();}
async function load(url){
  const res=await fetch(url);if(!res.ok)throw Error(`frame pair fetch failed ${res.status}: ${url}`);const buffer=await res.arrayBuffer(),view=new DataView(buffer);if(view.getUint32(0,true)!==0x46546c67)throw Error('frame pair requires GLB');const header=JSON.parse(new TextDecoder().decode(new Uint8Array(buffer,20,view.getUint32(12,true))));const loader=new GLTFLoader();if(header.extensionsRequired?.includes('EXT_meshopt_compression'))loader.setMeshoptDecoder(await loadMeshoptDecoder());const asset=await loader.parseAsync(buffer,new URL('.',new URL(url,location.href)).href);const meshes=[];asset.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);});if(!meshes.length)throw Error('frame pair has no loaded skin');return{...asset,meshes,bind:[]};
}
function bind(model){model.defaultMorphs=[];model.scene.traverse(o=>{model.bind.push([o,o.position.clone(),o.quaternion.clone(),o.scale.clone()]);if(o.morphTargetInfluences)model.defaultMorphs.push([o,o.morphTargetInfluences.slice()]);});model.mixer=new T.AnimationMixer(model.scene);}
function pose(model,name,phase){model.mixer.stopAllAction();for(const[o,p,q,s]of model.bind){o.position.copy(p);o.quaternion.copy(q);o.scale.copy(s);}for(const[o,weights]of model.defaultMorphs)o.morphTargetInfluences.splice(0,o.morphTargetInfluences.length,...weights);if(name!==null){const clip=model.animations.find(c=>c.name===name);if(!clip)throw Error('missing frame pair clip '+name);const action=model.mixer.clipAction(clip);action.setLoop(T.LoopOnce,1);action.clampWhenFinished=true;action.play();model.mixer.setTime(phase*clip.duration);}model.scene.updateMatrixWorld(true);for(const o of model.meshes)o.skeleton.update();}
function surface(model){const result=[],v=new T.Vector3();for(const o of model.meshes)for(let i=0;i<o.geometry.attributes.position.count;i++){o.getVertexPosition(i,v).applyMatrix4(o.matrixWorld);result.push(v.x,v.y,v.z);}return result;}
function layout(model){return model.meshes.map(m=>({name:m.name,vertices:m.geometry.attributes.position.count,index:Array.from(m.geometry.index?.array??[]),groups:m.geometry.groups.map(g=>({...g})),drawRange:{...m.geometry.drawRange},morphs:Object.entries(m.morphTargetDictionary??{}).sort(([a],[b])=>a.localeCompare(b)),morphPositionCounts:(m.geometry.morphAttributes.position??[]).map(a=>a.count),materials:[].concat(m.material).map(v=>v.name)}));}
function clipFacts(model){const names=new Set();return model.animations.map(a=>{if(names.has(a.name)||!Number.isFinite(a.duration)||a.duration<0)throw Error('ambiguous clip name or invalid duration');names.add(a.name);return{name:a.name,duration_s:a.duration};}).sort((a,b)=>a.name.localeCompare(b.name));}
function metricSpan(points){const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(let i=0;i<points.length;i++) {if(!Number.isFinite(points[i]))throw Error('nonfinite default-rest surface');const k=i%3;lo[k]=Math.min(lo[k],points[i]);hi[k]=Math.max(hi[k],points[i]);}const span=Math.max(...hi.map((v,k)=>v-lo[k]));if(!Number.isFinite(span)||span<.45||span>2.3)throw Error('default-rest human world extent is not plausibly metric');return{min:lo,max:hi,maximum_axis_span_m:span};}
function restoreMorphDefaults(model){for(const[o,weights]of model.defaultMorphs)o.morphTargetInfluences.splice(0,o.morphTargetInfluences.length,...weights);}
function sampleNamedMorphs(raw,cleaned){
  const clips=clipFacts(raw),nonrest=clips.find(c=>c.name==='walk'&&c.duration_s>0)??clips.find(c=>c.duration_s>0);
  const poses=[{name:'rest',clip:null,phase:0},...(nonrest?[{name:'clip_midpoint',clip:nonrest.name,phase:.5}]:[])];
  const receipts=[];let maximum=0;
  try{
    for(let meshIndex=0;meshIndex<raw.meshes.length;meshIndex++){
      const a=raw.meshes[meshIndex],b=cleaned.meshes[meshIndex];
      const targets=Object.entries(a.morphTargetDictionary??{}).sort(([x],[y])=>x.localeCompare(y));
      for(const[target,index]of targets){
        if(b.morphTargetDictionary?.[target]!==index)throw Error('morph pair correspondence differs');
        for(const at of poses){
          pose(raw,at.clip,at.phase);pose(cleaned,at.clip,at.phase);
          // Isolate this named target at the sampled skeletal pose. Every other
          // target keeps its actual loaded default, including nonzero defaults.
          restoreMorphDefaults(raw);restoreMorphDefaults(cleaned);
          a.morphTargetInfluences[index]=1;b.morphTargetInfluences[index]=1;
          raw.scene.updateMatrixWorld(true);cleaned.scene.updateMatrixWorld(true);
          for(const m of [...raw.meshes,...cleaned.meshes])m.skeleton.update();
          const delta=maximumPointDisplacement(surface(raw),surface(cleaned));
          maximum=Math.max(maximum,delta);
          receipts.push({mesh_index:meshIndex,mesh_name:a.name,target,index,weight:1,pose:at.name,clip:at.clip,phase:at.phase,other_morphs:'actual loaded defaults',maximum_vertex_delta_m:delta});
          // A sample cannot leak its weight or action into the next sample.
          pose(raw,null,0);pose(cleaned,null,0);
        }
      }
    }
    return{scope:'each matching named morph at weight1 independently, actual defaults for other targets; rest and one available clip midpoint skeletal pose only',nonrest_clip:nonrest?.name??null,receipts,maximum_vertex_delta_m:maximum};
  }finally{pose(raw,null,0);pose(cleaned,null,0);}
}
export async function compareFrameRepair(rawUrl,cleanedUrl,{samples=21,tolerance_m=.0001}={}){
  if(!Number.isInteger(samples)||samples<2||samples>101||!Number.isFinite(tolerance_m)||tolerance_m<=0||tolerance_m>.001)throw Error('bounded frame-pair settings required (2..101 samples, tolerance <=1mm)');
  let raw,cleaned;
  try{
    raw=await load(rawUrl);cleaned=await load(cleanedUrl);bind(raw);bind(cleaned);
    if(JSON.stringify(layout(raw))!==JSON.stringify(layout(cleaned)))throw Error('raw/cleaned mesh/index/material layout differs; pointwise comparison is not applicable');
    if(JSON.stringify(clipFacts(raw))!==JSON.stringify(clipFacts(cleaned)))throw Error('raw/cleaned clip names or durations differ');
    pose(raw,null,0);pose(cleaned,null,0);const rawRest=surface(raw),cleanedRest=surface(cleaned),rawMetric=metricSpan(rawRest),cleanedMetric=metricSpan(cleanedRest);const rest=maximumPointDisplacement(rawRest,cleanedRest),clips=[];let maximum=rest;
    for(const clip of clipFacts(raw)){const phases=[];for(let i=0;i<samples;i++){const phase=i/(samples-1);pose(raw,clip.name,phase);pose(cleaned,clip.name,phase);const delta=maximumPointDisplacement(surface(raw),surface(cleaned));maximum=Math.max(maximum,delta);phases.push({phase,maximum_vertex_delta_m:delta});}clips.push({name:clip.name,duration_s:clip.duration,phases,maximum_vertex_delta_m:Math.max(...phases.map(p=>p.maximum_vertex_delta_m))});}
    const morph_samples=sampleNamedMorphs(raw,cleaned);maximum=Math.max(maximum,morph_samples.maximum_vertex_delta_m);
    return{scope:'actual decoded CPU-skinned world vertices, raw export versus frame-cleaned/source-skin-consolidated export only; not Meshopt parity, photographic quality or a continuous-time proof',raw_url:rawUrl,cleaned_url:cleanedUrl,mesh_count:raw.meshes.length,samples_per_clip:samples,default_rest_metric_bounds:{raw:rawMetric,cleaned:cleanedMetric},default_morph_weights:{raw:raw.defaultMorphs.map(([o,w])=>({mesh:o.name,weights:w})),cleaned:cleaned.defaultMorphs.map(([o,w])=>({mesh:o.name,weights:w}))},rest_maximum_vertex_delta_m:rest,maximum_vertex_delta_m:maximum,tolerance_m,clips,morph_samples,passed:maximum<=tolerance_m};
  }finally{for(const m of [raw,cleaned])if(m){m.mixer?.stopAllAction();m.mixer?.uncacheRoot(m.scene);release(m.scene);}}
}

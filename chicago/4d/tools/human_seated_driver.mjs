// SPDX-License-Identifier: GPL-3.0-or-later
// Technical canonical-export preview using the existing portable HumanActor, never mounted in town.
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {HumanActor,createHumanAssets} from '../renderers/web/js/humans.js';
import {disposeLoadedAsset} from '../renderers/web/js/scene-loader.js';
import {parseVerifiedSeatedWagon,cleanupSeatedStudy} from './human_seated_runtime.mjs';
import {resolveHumanIdentity} from '../renderers/web/js/human-identity.js';
const q=new URLSearchParams(location.search),asset=q.get('asset')??'bardwell_otis_1835',sceneId=q.get('scene')??'1835';
const require=(condition,message)=>{if(!condition)throw Error(message);};
const json=async href=>{const r=await fetch(href);require(r.ok,`Missing required study input: ${href} (${r.status})`);return r.json();};
const report=window.seatedDriver={ready:false,passed:false,scope:'Actual named canonical export preview only; garment/contact and photographic acceptance separate'};
const resources={actor:null,assets:null,renderer:null,wagon:null,inspectionLease:false,asset,disposeLoadedAsset};
const cleanup=()=>{report.cleanup=cleanupSeatedStudy(resources);actor=null;assets=null;renderer=null;wagon=null;window.seatedDriverView=null;document.querySelectorAll('[data-view]').forEach(b=>b.onclick=null);return report.cleanup;};
window.addEventListener('beforeunload',cleanup);
let actor,assets,renderer,wagon;const scene=new T.Scene();scene.background=new T.Color('#d8dcd5');
try {
 require(sceneId==='1835','This named wardrobe/pose is eligible only for scene1835');
 const recipe=await json('../data/humans/recipes/worker_1835.json');
 const variant=recipe.proof_variants.find(v=>v.id===asset);require(variant&&variant.person_reference_scene==='1835','Unknown named1835 study asset');
 const people=(await json('../data/sidecars/1835/people.json')).people;
 const instance={id:`study_seated_${asset}`,person_id:variant.person_reference_id,scene:'1835',placement:{local_e:0,local_n:0,heading_deg:180},behaviour:{state:'seated'},animation:{clip:'sit_drive',loop:true,phase:0},appearance:{asset_id:asset},lod:{policy:'fixed',fixed:0},interaction:{opens:'resident_card'},provenance:{grade:'reconstructed'},review_required:true};
 const identity=resolveHumanIdentity(instance,{sceneId,people});
 require(identity.person.present==='present'&&identity.person.grade==='reconstructed','Named record changed; review study binding');
 assets=createHumanAssets({assetBase:new URL('../assets/',location.href)});resources.assets=assets;
 resources.inspectionLease=true;const loaded=await assets.acquire(asset,0);let metadata,driverStudy;
 {
   const exportScene=loaded.parser.json.scenes?.[0]?.extras;metadata=exportScene?.chicago4d_human;
   driverStudy=JSON.parse(exportScene?.driver_study_json??'null');
   require(driverStudy?.person_reference_id===identity.personId&&driverStudy.scene==='1835','Actual exported seated study must bind this named1835 reference');
   require(metadata?.person_reference_id===identity.personId&&metadata.person_reference_scene==='1835','Actual exported named identity/date differs');
   require(loaded.animations.some(a=>a.name==='sit_drive'),'Canonical sit_drive export required; no idle/fixture fallback');
 }
 actor=new HumanActor({instance,person:identity.person,identity,assets,heightAt:()=>0,tier:'full'});resources.actor=actor;await actor.setLod(0);assets.release(asset,0);resources.inspectionLease=false;scene.add(actor.root);
 const vehicleResponse=await fetch('../renderers/web/transport/wagon-driver/wagon-w01.json');require(vehicleResponse.ok,'Actual driver vehicle sidecar missing');
 const vehicleBytes=await vehicleResponse.arrayBuffer(),vehicleHash=[...new Uint8Array(await crypto.subtle.digest('SHA-256',vehicleBytes))].map(x=>x.toString(16).padStart(2,'0')).join('');
 require(driverStudy.vehicle_sidecar_sha256===vehicleHash,'Actual seated clip was authored for another vehicle sidecar');
 const furniture=JSON.parse(new TextDecoder().decode(vehicleBytes));
 require(furniture.asset_id==='wagon_w01_driver_bench_study'&&furniture.driver_furniture?.seat_surface_m?.join(',')==='0,1.58,0.65','Actual supported W01 physical seat required');
 const control=q.get('vehicle-control');require(!control||control==='baseline','Unknown vehicle control');
 const wagonURL=control==='baseline'?'../renderers/web/transport/wagon/wagon-w01.glb':'../renderers/web/transport/wagon-driver/wagon-w01.glb';
 const wagonResponse=await fetch(wagonURL);require(wagonResponse.ok,'Actual wagon GLB missing');const wagonBytes=await wagonResponse.arrayBuffer();
 const verified=await parseVerifiedSeatedWagon(wagonBytes,(bytes,base)=>new GLTFLoader().parseAsync(bytes,base),new URL('.',new URL(wagonURL,location.href)).href);
 wagon=verified.gltf;resources.wagon=wagon;scene.add(wagon.scene);
 const update=()=>{scene.updateMatrixWorld(true);actor.body.meshes.forEach(m=>m.skeleton.update());};
 const points=(root)=>{update();const p=[],v=new T.Vector3();root.traverse(o=>{if(!o.isMesh||!o.visible)return;const a=o.geometry.attributes.position,indices=o.geometry.index?new Set(o.geometry.index.array):Array.from({length:a.count},(_,i)=>i);for(const i of indices){if(o.isSkinnedMesh)o.getVertexPosition(i,v);else v.fromBufferAttribute(a,i);v.applyMatrix4(o.matrixWorld);p.push(...v.toArray());}});return p;};
 require(actor.play('idle',{fade:0,time:0}),'Original idle clip required');const idle=points(actor.root);
 require(actor.play('sit_drive',{fade:0,time:.5}),'Actual seated clip did not play');const seated=points(actor.root);require(idle.length===seated.length&&idle.length>0,'Actual skinned surface missing');
 let displacement=0;for(let i=0;i<idle.length;i+=3)displacement=Math.max(displacement,Math.hypot(seated[i]-idle[i],seated[i+1]-idle[i+1],seated[i+2]-idle[i+2]));require(displacement>.1,'Actual exported seated deformation is absent');
 renderer=new T.WebGLRenderer({antialias:true});resources.renderer=renderer;renderer.setPixelRatio(1);renderer.setSize(innerWidth,innerHeight);renderer.outputColorSpace=T.SRGBColorSpace;document.body.append(renderer.domElement);
 scene.add(new T.HemisphereLight(0xf0f5ff,0x77684b,2.2));const light=new T.DirectionalLight(0xffefdf,3);light.position.set(3,5,4);scene.add(light);const camera=new T.PerspectiveCamera(32,innerWidth/innerHeight,.03,100);
 document.getElementById('name').textContent=`${identity.person.name} — reconstructed1835 reference`;
 document.getElementById('state').textContent='Actual sit_drive clip on portable HumanActor; physical support is the W01 seat, not a pelvis socket.';
 const selected=[...points(actor.root),...points(wagon.scene)];
 window.seatedDriverView=(name='threequarter')=>{const theta={front:0,side:Math.PI/2,threequarter:Math.PI/4}[name];require(Number.isFinite(theta),'Unknown view');let framing=fitInspectionCamera(camera,selected,{width:innerWidth,height:innerHeight,headerBottom:document.querySelector('aside').getBoundingClientRect().bottom,theta});actor.update(0,camera.position);framing=fitInspectionCamera(camera,[...points(actor.root),...points(wagon.scene)],{width:innerWidth,height:innerHeight,headerBottom:document.querySelector('aside').getBoundingClientRect().bottom,theta});renderer.render(scene,camera);return{view:name,framing,actor_costs:actor.costsNow,gl_error:renderer.getContext().getError(),draws:renderer.info.render.calls,triangles:renderer.info.render.triangles};};
 document.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>window.seatedDriverView(b.dataset.view));
 Object.assign(report,{ready:true,passed:true,asset,person_id:identity.personId,name:identity.person.name,person_grade:identity.person.grade,scene:sceneId,driver_study:driverStudy,vehicle_sidecar_sha256:vehicleHash,vehicle_glb_sha256:verified.sha256,clip:actor.clipName,actual_surface_displacement_from_idle_m:displacement,skinned_meshes:actor.body.meshes.length,furniture,view:window.seatedDriverView()});

}catch(error){cleanup();report.ready=false;report.passed=false;report.error=String(error.stack||error);document.getElementById('state').textContent=report.error;throw error;}

// Existing project actual-vertex perspective/header fit, unchanged.
function fitInspectionCamera(camera,points,{width,height,headerBottom,theta=0,margin=.02,minHeightFraction=0}={}){
 if(!points.length||points.length%3||!points.every(Number.isFinite)||![width,height,headerBottom,theta].every(Number.isFinite)||width<=0||height<=0)throw Error('finite nonempty camera-fit input required');
 const rect={left:margin,right:1-margin,top:Math.max(margin,headerBottom/height+margin),bottom:1-margin};
 if(rect.top>=rect.bottom)throw Error('header leaves no inspection viewport');
 camera.aspect=width/height;camera.updateProjectionMatrix();
 const outward=new T.Vector3(Math.sin(theta),0,Math.cos(theta)),up=new T.Vector3(0,1,0),right=new T.Vector3().crossVectors(up,outward),center=new T.Vector3(),box=new T.Box3(),v=new T.Vector3();
 for(let i=0;i<points.length;i+=3)box.expandByPoint(v.fromArray(points,i));box.getCenter(center);
 const tanY=Math.tan(T.MathUtils.degToRad(camera.fov)/2)/camera.zoom,tanX=tanY*camera.aspect,cx=rect.left+rect.right-1,cy=1-rect.top-rect.bottom;
 // Centre the target in the unobscured rectangle with a camera-plane translation.
 function place(distance){const aim=center.clone().addScaledVector(right,-cx*distance*tanX).addScaledVector(up,-cy*distance*tanY);camera.position.copy(aim).addScaledVector(outward,distance);camera.up.copy(up);camera.lookAt(aim);camera.updateMatrixWorld(true);}
 function receipt(distance){place(distance);let left=Infinity,rightEdge=-Infinity,top=Infinity,bottom=-Infinity,valid=true;for(let i=0;i<points.length;i+=3){v.fromArray(points,i);const depth=-v.clone().applyMatrix4(camera.matrixWorldInverse).z;v.project(camera);const x=(v.x+1)/2,y=(1-v.y)/2;valid&&=Number.isFinite(x)&&Number.isFinite(y)&&depth>camera.near&&depth<camera.far;left=Math.min(left,x);rightEdge=Math.max(rightEdge,x);top=Math.min(top,y);bottom=Math.max(bottom,y);}return{distance_m:distance,bounds:{left,right:rightEdge,top,bottom},height_fraction:bottom-top,inside:valid&&left>=rect.left&&rightEdge<=rect.right&&top>=rect.top&&bottom<=rect.bottom};}
 let low=camera.near,high=Math.max(box.getSize(v).length(),camera.near*2),r;for(let i=0;i<40;i++){r=receipt(high);if(r.inside)break;high*=1.5;if(high>=camera.far)throw Error('no camera fit within clipping range');}if(!r.inside)throw Error('camera fit did not converge');
 for(let i=0;i<55;i++){const mid=(low+high)/2;if(receipt(mid).inside)high=mid;else low=mid;}
 // A tiny inward safety margin avoids floating-point equality at the strict boundary.
 r=receipt(high*1.00001);if(!r.inside||r.height_fraction<minHeightFraction)throw Error(`inspection geometry cannot meet framing/detail criteria: ${JSON.stringify(r)}`);
 return{...r,available_rectangle:rect,method:'perspective fit of actual selected world vertices below measured header; camera motion only'};
}

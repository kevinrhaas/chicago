// SPDX-License-Identifier: GPL-3.0-or-later
import * as THREE from 'three';
import {GLTFLoader} from '../../vendor/three-0.185.1/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from '../../vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js';

const canvas=document.querySelector('#view');
const renderer=new THREE.WebGLRenderer({canvas,antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1;
renderer.shadowMap.enabled=true;
renderer.shadowMap.type=THREE.PCFSoftShadowMap;
const scene=new THREE.Scene();scene.background=new THREE.Color('#e8e5de');
scene.add(new THREE.HemisphereLight(0xe8f0ff,0x8e8172,2.2));
const sun=new THREE.DirectionalLight(0xfff6e7,3.0);sun.position.set(4,8,6);sun.castShadow=true;
sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-6,right:6,top:6,bottom:-6,near:.1,far:25});sun.shadow.bias=-.0001;scene.add(sun);
const floor=new THREE.Mesh(new THREE.PlaneGeometry(40,40),new THREE.MeshStandardMaterial({color:0xc9c7be,roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-.004;floor.receiveShadow=true;scene.add(floor);
const metreGrid=new THREE.GridHelper(10,10,0xa4a69b,0xb7b8ae);metreGrid.position.y=-.002;scene.add(metreGrid);
const camera=new THREE.PerspectiveCamera(38,1,.03,500),target=new THREE.Vector3(0,.8,.95);
let theta=.95,phi=1.08,distance=9.3,model,metadata,playing=false,previous=performance.now(),drag,request=0,canonicalBox;
let frameSamples=[],loadedDetail=null;
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
const steer=document.querySelector('#steer'),travel=document.querySelector('#travel'),raised=document.querySelector('#raised');
function fitView(){
  if(!model)return;
  model.updateMatrixWorld(true);
  const bounds=canonicalBox.clone().applyMatrix4(model.matrixWorld);bounds.getCenter(target);
  const direction=new THREE.Vector3(Math.sin(phi)*Math.sin(theta),Math.cos(phi),Math.sin(phi)*Math.cos(theta));
  const right=new THREE.Vector3(Math.cos(theta),0,-Math.sin(theta)),up=new THREE.Vector3().crossVectors(direction,right);
  const vertical=Math.tan(camera.fov*Math.PI/360),horizontal=vertical*canvas.clientWidth/canvas.clientHeight;
  let fit=0;
  for(const x of [bounds.min.x,bounds.max.x])for(const y of [bounds.min.y,bounds.max.y])for(const z of [bounds.min.z,bounds.max.z]){
    const corner=new THREE.Vector3(x,y,z).sub(target),depth=corner.dot(direction);
    fit=Math.max(fit,depth+Math.abs(corner.dot(right))/(horizontal*.8),depth+Math.abs(corner.dot(up))/(vertical*.8));
  }
  const detail=document.querySelector('#detail').value,threshold=detail==='far'?24:detail==='mid'?96:Infinity;
  const focalPixels=canvas.clientHeight/(2*vertical),lodDistance=2*metadata.parameters.wheel_radius_m.rear*focalPixels/threshold;
  distance=Math.max(fit,lodDistance);
}
function update(){
  if(!model)return;
  const p=metadata.parameters,delta=Number(steer.value)*Math.PI/180,s=Number(travel.value);
  const wheelbase=p.axle_stations_z_m.front-p.axle_stations_z_m.rear,k=Math.tan(delta)/wheelbase,a=s*k;
  model.rotation.y=a;
  model.position.set(Math.abs(k)>1e-7?(1-Math.cos(a))/k-p.axle_stations_z_m.rear*Math.sin(a):0,0,
    Math.abs(k)>1e-7?Math.sin(a)/k-p.axle_stations_z_m.rear*(Math.cos(a)-1):s);
  model.getObjectByName('vehicle_steer_front').rotation.y=delta;
  for(const end of ['rear','front'])for(const side of ['left','right']){
    const x=(side==='left'?1:-1)*p.wheel_center_track_m/2;
    const factor=end==='rear'?1-k*x:1/Math.cos(delta)-k*x;
    model.getObjectByName(`vehicle_wheel_${end}_${side}`).rotation.x=s*factor/p.wheel_radius_m[end];
  }
  model.getObjectByName('vehicle_tongue').rotation.x=raised.checked?0:Math.asin((p.wheel_radius_m.front-.03)/p.tongue_length_m);
  document.querySelector('#steerValue').textContent=`${Number(steer.value).toFixed(1)}°`;
  document.querySelector('#travelValue').textContent=`${s.toFixed(2)} m`;
  window.farmBoxState={loaded:true,steer:Number(steer.value),travel:s,raised:raised.checked,
    wheelAngles:['rear_left','rear_right','front_left','front_right'].map(n=>model.getObjectByName('vehicle_wheel_'+n).rotation.x),
    detail:loadedDetail,sourceSHA:metadata.source.original_sha256,photographicAcceptance:false};
}
function dispose(tree){
  const geometries=new Set(),materials=new Set(),textures=new Set();
  tree.traverse(n=>{if(n.isMesh){geometries.add(n.geometry);for(const m of Array.isArray(n.material)?n.material:[n.material]){materials.add(m);for(const v of Object.values(m))if(v?.isTexture)textures.add(v);}}});
  for(const geometry of geometries)geometry.dispose();for(const texture of textures)texture.dispose();for(const material of materials)material.dispose();
}
function finish(){
  if(!model)return;
  const warm=document.querySelector('#finish').value==='warm';
  const materials=new Set();model.traverse(n=>{if(n.isMesh)for(const m of Array.isArray(n.material)?n.material:[n.material])materials.add(m);});
  for(const material of materials){
    if(!material.userData.originalColor)material.userData.originalColor=material.color.clone();
    material.color.copy(material.userData.originalColor);
    if(warm)material.color.multiply(new THREE.Color().setRGB(.93,.84,.72));
  }
}
function loadDetail(){
  const token=++request,detail=document.querySelector('#detail').value;
  document.querySelector('#status').textContent='Loading wagon…';
  loader.load(`./farm-box-${detail}.glb`,g=>{
    if(token!==request){dispose(g.scene);return;}
    if(model){scene.remove(model);dispose(model);}
    metadata=g.parser.json.extras;model=g.scene.getObjectByName('vehicle_root');scene.add(model);loadedDetail=detail;
    let triangles=0,batches=0;
    model.traverse(n=>{if(n.isMesh){n.castShadow=true;n.receiveShadow=true;triangles+=(n.geometry.index?.count??n.geometry.attributes.position.count)/3;batches++;}});
    document.querySelector('#status').textContent='Wagon ready';
    document.querySelector('#technical-status').textContent=`${triangles.toLocaleString()} triangles · ${batches} material batches`;
    update();finish();frameSamples=[];if(!canonicalBox)canonicalBox=new THREE.Box3().setFromObject(model);
    if(!document.querySelector('#hold-view').checked)fitView();
  },undefined,error=>{document.querySelector('#status').textContent='Wagon could not be loaded';console.error(error);});
}
document.querySelector('#detail').addEventListener('change',loadDetail);loadDetail();
document.querySelector('#finish').addEventListener('change',finish);
for(const input of [steer,travel,raised])input.addEventListener('input',update);
document.querySelector('#play').addEventListener('click',()=>{playing=!playing;document.querySelector('#play').textContent=playing?'Pause':'Roll';});
document.querySelector('#reset').addEventListener('click',()=>{playing=false;steer.value=0;travel.value=0;raised.checked=true;document.querySelector('#play').textContent='Roll';update();});
for(const button of document.querySelectorAll('[data-view]'))button.addEventListener('click',()=>{
  theta={quarter:.95,side:Math.PI/2,front:0,rear:Math.PI}[button.dataset.view];phi=button.dataset.view==='quarter'?1.08:1.38;
  fitView();
});
canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});
canvas.addEventListener('pointermove',e=>{if(drag){theta-=(e.clientX-drag[0])*.008;phi=Math.max(.25,Math.min(1.5,phi+(e.clientY-drag[1])*.006));drag=[e.clientX,e.clientY];}});
canvas.addEventListener('pointerup',()=>{drag=null;});
canvas.addEventListener('wheel',e=>{e.preventDefault();distance=Math.max(4,Math.min(300,distance+e.deltaY*.008));},{passive:false});
function render(now){
  const elapsed=now-previous,dt=Math.min(.04,elapsed/1000);previous=now;
  if(playing){const s=Number(travel.value)+dt*.35;if(s>2){playing=false;document.querySelector('#play').textContent='Roll';}else{travel.value=s;update();}}
  const w=canvas.clientWidth,h=canvas.clientHeight;renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();
  camera.position.set(target.x+distance*Math.sin(phi)*Math.sin(theta),target.y+distance*Math.cos(phi),target.z+distance*Math.sin(phi)*Math.cos(theta));camera.lookAt(target);
  const submitted=performance.now();renderer.render(scene,camera);
  if(model){frameSamples.push({interval_ms:elapsed,cpu_submission_ms:performance.now()-submitted});if(frameSamples.length>120)frameSamples.shift();}
  // These are measurements in the current browser/viewport, not physical-phone
  // or GPU timer certification. Keep technical counters out of visitor prose.
  window.farmBoxRenderReceipt={width:w,height:h,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,cameraDistance:distance,rearWheelPixels:metadata?2*metadata.parameters.wheel_radius_m.rear*h/(2*Math.tan(camera.fov*Math.PI/360)*distance):null,
    textures:renderer.info.memory.textures,geometries:renderer.info.memory.geometries,frameSamples:[...frameSamples],detail:loadedDetail,finish:document.querySelector('#finish').value};
  requestAnimationFrame(render);
}
requestAnimationFrame(render);

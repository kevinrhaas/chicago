// SPDX-License-Identifier: GPL-3.0-or-later
// One original generated woodworking kit, on a real dated person's existing work span.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const finite = Number.isFinite;
const smooth = x => { x=Math.max(0,Math.min(1,x)); return x*x*(3-2*x); };
export function shownWorkObject(object, sceneRoot) {
  const seen=new Set();
  for(let n=object;n;n=n.parent){if(seen.has(n)||n.visible===false)return false;if(n===sceneRoot)return true;seen.add(n);}
  return false;
}
export function workTaskAt(config, {scene,date,hour}={}) {
  if(scene!==config?.scene || !/^\d{4}-\d{2}-\d{2}$/.test(date??'') || !finite(hour))return null;
  return config.tasks?.find(t=>date>=t.dates.from&&date<=t.dates.to&&t.hours.some(([a,b])=>hour>=a&&hour<b))??null;
}
/** At least one displayed frame lands exactly on contact, including a slow frame.
 * It never fabricates multiple catch-up contacts after a pause. */
export function advanceWorkPhase(phase, dt, {cycle_seconds,contact_phase}) {
  if(!finite(dt)||dt<=0||dt>.25)return{phase,contact:false};
  const next=phase+dt/cycle_seconds;
  if(phase<contact_phase&&next>=contact_phase)return{phase:contact_phase,contact:true};
  return{phase:next>=1?next%1:next,contact:false};
}
export function workLift(phase,contact=.63) {
  if(phase<.2)return .12;
  if(phase<.45)return .12+.88*smooth((phase-.2)/.25);
  if(phase<=contact)return 1-smooth((phase-.45)/(contact-.45));
  return .12*smooth((phase-contact)/.12);
}

/** Main calls this AFTER humans, days and spacing; no audio or geometry is synthesized.
 * Only original GLB props are drawn; hand motion uses the person's contract rig. */
export function createWorkActivity({humans,days,config,assetBase,sceneRoot,confidence=null,
  loader=new GLTFLoader(),now=()=>performance.now(),onError=()=>{}}={}) {
  const group=new THREE.Group();group.name='work-activities';
  let disposed=false,loading=null,asset=null,chest=null,hammer=null,strike=null,contact=null;
  let current=null,active=false,session=0,serial=0,phase=0,warm=0,updatedAt=-Infinity;
  let lastFrame=0,contactFrame=0,contactAt=-Infinity,lastDate=null,lastHour=null,handError=null;
  let contacts=0,failed=false;
  const errors=[];
  const anchor=new THREE.Vector3(),grip=new THREE.Vector3(),left=new THREE.Vector3();
  const fingers=new THREE.Vector3(),palm=new THREE.Vector3(),actualStrike=new THREE.Vector3();
  const markerLocal=new THREE.Vector3(...(config?.geometry?.contact_local??[0,0,0]));
  const leftLocal=new THREE.Vector3(...(config?.geometry?.left_wrist_local??[0,0,0]));
  function releaseAsset(scene){const geometries=new Set(),materials=new Set();scene?.traverse(o=>{
    if(o.geometry)geometries.add(o.geometry);for(const m of Array.isArray(o.material)?o.material:[o.material])if(m)materials.add(m);
  });geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());}
  function reset({hide=true}={}) {
    if(current||active)session++;
    current=null;active=false;serial=0;phase=0;warm=0;contactAt=-Infinity;contactFrame=0;handError=null;
    if(hide)group.visible=false;
  }
  function load() {
    if(disposed||loading||asset||failed)return;
    loading=loader.loadAsync(new URL(config.asset,assetBase).href).then(g=>{
      if(disposed){releaseAsset(g.scene);return;}
      const h=g.scene.getObjectByName('work_hammer'),c=g.scene.getObjectByName('work_chest');
      const s=h?.getObjectByName('hammer_strike'),p=c?.getObjectByName('work_contact');
      if(!h||!c||!s||!p){releaseAsset(g.scene);throw Error('generated work kit lacks contact markers');}
      asset=g.scene;hammer=h;chest=c;strike=s;contact=p;group.add(asset);
      asset.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;}});
      reset();
    }).catch(e=>{if(!disposed){failed=true;errors.push(e.message);onError(`Work kit: ${e.message}`);}})
      .finally(()=>{loading=null;});
  }
  const gradeShown=()=>!confidence?.hidden?.[config?.provenance?.grade??'reconstructed'];
  function materialVisible(m) {
    if(Array.isArray(m))return m.some(materialVisible);
    if(!m||m.visible===false||(m.transparent===true&&finite(m.opacity)&&m.opacity<=0))return false;
    const look=confidence?.grade?.(config?.provenance?.grade??'reconstructed');
    // Ordinary portable humans need not be confidence-shader patched. Only a
    // patched transparent/dither grade uses that shader's zero-opacity rule.
    return !(m.userData?.confidencePatched&&confidence?.enabled
      &&['ghost','dither'].includes(look?.mode)&&look.opacity<=0);
  }
  function visibleActor(a) {
    return !!a&&!a.disposed&&!a.indoors&&a.inRange&&humans.shown!==false&&!humans.isHeld?.(a)
      &&a.root?.visible!==false&&a.body?.scene&&a.actions?.bound&&!a.body.oneShot&&gradeShown()
      &&shownWorkObject(a.body.scene,sceneRoot)
      &&a.body.meshes?.some(m=>m.visible!==false&&materialVisible(m.material)&&m.geometry?.getAttribute('position')?.count>0);
  }
  function eligible(a,task,work) {
    const heading=Math.abs(((a?.heading-work?.heading+540)%360)-180);
    return work?.active===true&&work.actorId===task.actor_id
      &&Math.hypot(work.originalAt.e-task.at.e,work.originalAt.n-task.at.n)<.01
      &&visibleActor(a)&&a.state==='working'&&!a.path&&!a.route&&!a.tow
      &&Math.hypot(a.e-work.at.e,a.n-work.at.n)<.42&&heading<12;
  }
  const api={
    group,
    update(dt,{paused=false,scene,date,hour}={}) {
      if(disposed)return;
      lastFrame++;updatedAt=now();lastDate=date;lastHour=hour;
      const task=workTaskAt(config,{scene,date,hour}),actor=task?humans.get(task.actor_id):null;
      const work=task?days?.workSource?.(task.actor_id):null;
      if(!task||!eligible(actor,task,work)){reset();return;}
      if(paused||!finite(dt)||dt<=0||dt>.25){reset({hide:!visibleActor(actor)});return;}
      if(!asset){reset();load();return;}
      if(current?.actor!==actor||current?.body!==actor.body||current?.task!==task||current?.date!==date||current?.work.epoch!==work.epoch){
        reset();current={actor,body:actor.body,task,date,work,animated:actor.counters?.animated};
        // The first shown action frame is a baseline, not an impact.
        group.visible=false;return;
      }
      if(actor.counters?.animated===current.animated){reset({hide:false});return;}
      current.animated=actor.counters?.animated;
      warm+=dt;
      if(warm<.4){group.visible=false;return;} // let a newly arrived walk crossfade settle
      group.position.set(work.at.e,actor.root.position.y,-work.at.n);
      group.rotation.set(0,actor.root.rotation.y,0);group.updateMatrixWorld(true);
      const next=advanceWorkPhase(phase,dt,config.action);phase=next.phase;
      const lift=workLift(phase,config.action.contact_phase),length=config.geometry.hammer.strike_local[1];
      grip.copy(markerLocal);grip.y+=length+config.action.lift_m*lift;
      group.localToWorld(grip);left.copy(leftLocal);group.localToWorld(left);
      fingers.set(0,0,1).transformDirection(group.matrixWorld);palm.set(1,0,0).transformDirection(group.matrixWorld);
      const solved=actor.actions.poseWorkHands({rightGrip:grip,leftWrist:left,fingers,palm});
      if(!solved){reset();return;}
      handError=solved.rightGrip.distanceTo(grip);
      if(handError>.08){reset();return;}
      // The visible hammer follows the measured hand grip; it is not positioned
      // at the sound source independently of the person holding it.
      hammer.position.copy(solved.rightGrip);group.worldToLocal(hammer.position);
      hammer.rotation.set(Math.PI+config.action.lift_radians*lift,0,0);
      group.visible=true;group.updateMatrixWorld(true);actor.root.updateMatrixWorld(true);
      contact.getWorldPosition(anchor);strike.getWorldPosition(actualStrike);
      active=true;
      if(next.contact&&actualStrike.distanceTo(anchor)<=config.action.max_contact_error_m){
        serial++;contacts++;contactFrame=lastFrame;contactAt=updatedAt;
      }
    },
    get audioSources() {
      if(disposed||!active||!current||!eligible(current.actor,current.task,current.work)
        ||current.body!==current.actor.body||now()-updatedAt>250||!shownWorkObject(group,sceneRoot))return[];
      return[{id:current.task.id,actorId:current.actor.id,actionId:config.action.id,scene:config.scene,date:lastDate,hour:lastHour,
        session,contactSerial:serial,contactFrame,contactAt,updatedAt,
        anchor:{x:anchor.x,y:anchor.y,z:anchor.z},visible:true,working:true}];
    },
    reset,
    get state(){return{ready:!!asset,loading:!!loading,failed,active,taskId:current?.task.id??null,actorId:current?.actor.id??null,
      session,contactSerial:serial,contactFrame,contacts,phase,handError,anchor:active?{x:anchor.x,y:anchor.y,z:anchor.z}:null,errors:[...errors]};},
    dispose(){if(disposed)return;disposed=true;reset();releaseAsset(asset);group.clear();asset=null;},
  };
  group.visible=false;return api;
}

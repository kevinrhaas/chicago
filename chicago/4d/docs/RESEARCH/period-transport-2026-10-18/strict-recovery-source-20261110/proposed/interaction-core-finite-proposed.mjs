// SPDX-License-Identifier: GPL-3.0-or-later
// Engine-neutral, passenger-first interaction study. No rendering/people directory.
export function createSeatRegistry(){const seats=new Map();return {reserve(key,owner){if(seats.has(key))return null;const token=Object.freeze({key,owner});seats.set(key,token);return token;},release(token){if(token&&seats.get(token.key)===token)seats.delete(token.key);},get size(){return seats.size;},owner(key){return seats.get(key)?.owner??null;}};}
const REQUIRED=['captureVisitor','restoreVisitor','captureCamera','restoreCamera','planApproach','moveVisitor','attachVisitor','detachVisitor','vehicleStatus','stopVehicle','startVehicle','resolveExit','updateSeatedCamera'];
const canceled=()=>Object.assign(new Error('Canceled'),{name:'AbortError'});
export class BoardingController{
 constructor({vehicleId,scene,seats,adapter,registry=createSeatRegistry(),mode='camera-study',person=null,gates={},role='passenger',reducedMotion=false,requireSettledRollback=false}){
  if(!vehicleId||!scene||!Array.isArray(seats)||!seats.length)throw Error('Explicit vehicle, scene and passenger seats required');
  if(!['passenger','rider'].includes(role))throw Error('Unsupported attachment role');
  if(seats.some(s=>!s.id||s.role!==role||!s.socket||!s.boardingSocket||!s.eligibleScenes?.includes(scene)))throw Error('Eligible explicit passenger sockets required');
  if(new Set(seats.map(s=>s.id)).size!==seats.length)throw Error('Duplicate seats');
  if(!['camera-study','occupied-production'].includes(mode))throw Error('Unknown interaction mode');
  if(person&&(!person.id||person.identityKind!=='person'||!person.record||person.scene!==scene))throw Error('Existing scene-eligible person record required; no anonymous fallback');
  if(mode==='occupied-production'&&(!person||!(role==='rider'?['sceneRoute','ridingTack','riderFit','gaitContact','cameraCollision']:['sceneRoute','hitch','seatedHumanFit','cameraCollision']).every(k=>gates[k]===true)))throw Error('Occupied production dependencies not accepted');
  for(const key of REQUIRED)if(typeof adapter[key]!=='function')throw Error(`Missing adapter ${key}`);
  if(requireSettledRollback&&(adapter.strictRecoveryContract!=='outside-app/strict-recovery-v1'||typeof adapter.recoverStrict!=='function'))throw Error('Unsupported strict recovery ports');
  Object.assign(this,{vehicleId,scene,seats,adapter,registry,mode,person,reducedMotion,role,requireSettledRollback});this.state='idle';this.listeners=new Set();this.generation=0;this.busy=false;this.disposed=false;this.reservation=null;this.saved=null;this.seat=null;this.error=null;this.motionPermitted=false;
 }
 snapshot(){return {state:this.state,mode:this.mode,seatId:this.seat?.id??null,personId:this.person?.id??null,error:this.error,busy:this.busy,disposed:this.disposed,motionPermitted:this.motionPermitted,acceptance:this.mode==='camera-study'?'Unoccupied seat-camera scaffolding; no physical occupant/driver/hitch acceptance':'Supplied accepted production gates'};}
 subscribe(fn){this.listeners.add(fn);fn(this.snapshot());return()=>this.listeners.delete(fn);}
 emit(state=this.state,error=null){this.state=state;this.error=error;for(const fn of this.listeners)fn(this.snapshot());}
 async task(fn){if(this.disposed||this.disposing||this.busy)return false;const id=++this.generation,abort=new AbortController();this.abort=abort;this.busy=true;const current=()=>{if(id!==this.generation||abort.signal.aborted||this.disposed)throw canceled();};try{return await fn({signal:abort.signal,current});}catch(e){if(id!==this.generation||e.name==='AbortError')return false;try{await this.rollback();if(!this.requireSettledRollback||id===this.generation)this.emit('idle',e.message);}catch(recovery){if(!this.requireSettledRollback||id===this.generation)this.emit('recovery-blocked',recovery.message);}return false;}finally{if(id===this.generation){this.busy=false;this.abort=null;this.emit(this.state,this.error);}}}
 async approach(seatId){if(this.state!=='idle')return false;const seat=this.seats.find(s=>s.id===seatId);if(!seat)return false;return this.task(async op=>{
  const token=this.registry.reserve(`${this.vehicleId}:${seat.id}`,this.person?.id??'local-visitor');if(!token){this.emit('idle','This seat is reserved.');return false;}
  this.reservation=token;this.seat=seat;this.saved={visitor:this.adapter.captureVisitor(),camera:this.adapter.captureCamera()};this.emit('approaching');
  const path=await this.adapter.planApproach(seat,{signal:op.signal,scene:this.scene});op.current();if(path?.clear!==true)throw Error(path?.reason??'Approach is obstructed.');
  await this.adapter.moveVisitor(path,{signal:op.signal,reducedMotion:this.reducedMotion});op.current();this.emit('ready');return true;
 });}
 async board(){if(this.state!=='ready')return false;return this.task(async op=>{if(Math.abs(this.adapter.vehicleStatus().speed_m_s)>1e-5)throw Error('Vehicle must stop before boarding.');this.emit('boarding');await this.adapter.attachVisitor(this.seat,{signal:op.signal,reducedMotion:this.reducedMotion,mode:this.mode,person:this.person});op.current();this.motionPermitted=false;this.emit('seated');return true;});}
 async ride(){if(this.state!=='seated')return false;return this.task(async op=>{const started=await this.adapter.startVehicle({signal:op.signal,kinematicStudy:this.mode==='camera-study'});op.current();if(started?.started===false){this.emit('seated',started.reason??'The route is stopped.');return false;}this.motionPermitted=true;this.emit('riding');return true;});}
 async stop(){if(!['riding','seated','blocked-exit'].includes(this.state))return false;return this.task(async op=>{this.emit('stopping');this.motionPermitted=false;await this.adapter.stopVehicle({signal:op.signal});op.current();if(Math.abs(this.adapter.vehicleStatus().speed_m_s)>1e-5)throw Error('Vehicle did not stop.');this.emit('seated');return true;});}
 async leave(){if(this.requireSettledRollback)return this.strictLeave();if(!['riding','seated','blocked-exit'].includes(this.state))return false;return this.task(async op=>{
  this.motionPermitted=false;this.emit('stopping');await this.adapter.stopVehicle({signal:op.signal});op.current();if(Math.abs(this.adapter.vehicleStatus().speed_m_s)>1e-5)throw Error('Vehicle did not stop.');
  const exit=await this.adapter.resolveExit(this.seat,{signal:op.signal,scene:this.scene});op.current();if(exit?.clear!==true){this.emit('blocked-exit',exit?.reason??'Exit is obstructed. Remain seated or try another exit.');return false;}
  this.emit('leaving');await this.adapter.detachVisitor(exit,{signal:op.signal,reducedMotion:this.reducedMotion});op.current();this.adapter.restoreCamera(this.saved.camera,{preserveVisitorPosition:true});this.release();this.emit('idle');return true;
 });}
 tick(dt){if(this.disposed)return;if(!Number.isFinite(dt)||dt<0)throw Error('Finite nonnegative dt required');if(['seated','riding','stopping','blocked-exit'].includes(this.state)||(this.requireSettledRollback&&this.reservation&&this.state==='recovery-blocked'&&this.strictCameraHeld))this.adapter.updateSeatedCamera(this.seat,{dt:Math.min(dt,.1),reducedMotion:this.reducedMotion});}
 release(){this.registry.release(this.reservation);this.reservation=null;this.saved=null;this.seat=null;this.motionPermitted=false;}
 async rollback(){if(this.requireSettledRollback)return this.strictRollback();this.motionPermitted=false;const failures=[];const attempt=async fn=>{try{await fn();}catch(e){failures.push(e.message);}};await attempt(()=>this.adapter.stopVehicle({immediate:true}));if(this.requireSettledRollback&&(failures.length||Math.abs(this.adapter.vehicleStatus().speed_m_s)>1e-5))throw Error(failures[0]??'Recovery has not stopped; remain attached.');if(this.saved){const saved=this.saved;await attempt(()=>this.adapter.detachVisitor(null,{immediate:true}));await attempt(()=>this.adapter.restoreVisitor(saved.visitor));await attempt(()=>this.adapter.restoreCamera(saved.camera));}this.release();return failures;}
 async cancel(reason='Interaction canceled.'){if(this.requireSettledRollback)return this.strictCancel(reason);if(this.disposed)return false;if(this.resetPromise)return this.resetPromise;++this.generation;this.abort?.abort();this.abort=null;this.busy=true;this.resetPromise=(async()=>{const failures=await this.rollback();this.emit('idle',[reason,...failures].join(' '));return true;})().catch(e=>{this.emit('recovery-blocked',e.message);return false;}).finally(()=>{this.busy=false;this.resetPromise=null;this.emit(this.state,this.error);});return this.resetPromise;}
 async strictRollback(options={}){
  this.motionPermitted=false;
  if(!this.reservation&&!this.saved)return [];
  const token=this.reservation,saved=this.saved,seat=this.seat;
  if(this.strictRecovery){if(this.strictRecovery.token!==token)throw canceled();if(!options.exit&&this.strictRecovery.exit){this.strictRecovery.exit=null;this.strictRecovery.intent++;}return this.strictRecovery.promise;}
  const current=()=>!this.disposed&&this.reservation===token&&this.saved===saved&&this.seat===seat;
  const record={token,promise:null,exit:options.exit??null,intent:0};this.strictRecovery=record;
  const ctx={token,saved,seat,get exit(){return record.exit;},intentRevision:()=>record.intent,retry:this.state==='recovery-blocked',isCurrent:current,retained:on=>{if(current())this.strictCameraHeld=on;}};
  record.promise=Promise.resolve().then(()=>this.adapter.recoverStrict(ctx)).then(receipt=>{
   if(!current())throw canceled();
   if(receipt?.committed!==true||receipt?.verified!==true||receipt.token!==token)throw Error('Strict recovery commit unverified');
   this.release();this.strictCameraHeld=false;return [];
  }).finally(()=>{if(this.strictRecovery===record)this.strictRecovery=null;});
  return record.promise;
 }
 async strictLeave(){
  if(!['riding','seated','blocked-exit'].includes(this.state))return false;
  return this.task(async op=>{this.motionPermitted=false;this.emit('stopping');await this.adapter.stopVehicle({signal:op.signal});op.current();
   const speed=this.adapter.vehicleStatus()?.speed_m_s;if(!Number.isFinite(speed)||Math.abs(speed)>1e-5)throw Error('Vehicle did not stop.');
   const exit=await this.adapter.resolveExit(this.seat,{signal:op.signal,scene:this.scene});op.current();
   if(exit?.clear!==true){this.emit('blocked-exit',exit?.reason??'Exit is obstructed. Remain seated.');return false;}
   this.emit('leaving');await this.strictRollback({exit});op.current();this.emit('idle');return true;
  });
 }
 async strictCancel(reason){
  if(this.disposed)return false;if(this.resetPromise)return this.resetPromise;
  const id=++this.generation;this.abort?.abort();this.abort=null;this.busy=true;
  const promise=this.rollback().then(()=>{if(id!==this.generation)return false;this.emit('idle',reason);return true;})
   .catch(e=>{if(id===this.generation&&e.name!=='AbortError')this.emit('recovery-blocked',e.message);return false;})
   .finally(()=>{if(this.resetPromise!==promise)return;this.resetPromise=null;if(id===this.generation){this.busy=false;this.emit(this.state,this.error);}});
  this.resetPromise=promise;return promise;
 }
 async contextChanged(reason='Destination or scene changed.'){return this.cancel(reason);}
 async dispose(){if(this.disposed)return;this.disposing=true;const settled=await this.cancel('Interaction disposed.');if(this.requireSettledRollback&&!settled){this.disposing=false;throw Error('Recovery incomplete; disposal retained live attachment.');}this.disposed=true;this.listeners.clear();}
}

/** Structural gate only; no second HumanActor implementation or inferred fit. */
export function validatePortableAttachment(actor,{scene,fit,role='passenger'}){
 if(!actor||actor.disposed||actor.identity?.kind!=='person'||!actor.personId||!actor.person||typeof actor.setState!=='function')throw Error('Existing live named/person-bound HumanActor required');
 if(fit?.personId!==actor.personId||fit?.scene!==scene||fit?.accepted!==true||fit?.role!==role||!fit.clip)throw Error('Scene/person-specific accepted passenger fit required');
 if(!actor.clips?.includes(fit.clip))throw Error('Authored passenger clip unavailable; idle fallback is not seating proof');
 return {id:actor.personId,record:actor.person,scene,identityKind:'person',clip:fit.clip};
}

export function validatePortablePassenger(actor,options){return validatePortableAttachment(actor,{...options,role:'passenger'}); }

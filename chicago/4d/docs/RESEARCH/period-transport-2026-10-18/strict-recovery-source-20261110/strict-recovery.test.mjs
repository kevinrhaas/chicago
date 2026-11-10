// SPDX-License-Identifier: GPL-3.0-or-later
/** Pure outside-app contract controls. No real model, camera, NPC or scene binding. */
import assert from 'node:assert/strict';
import { createStrictRecoveryAdapter } from './proposed/strict-recovery-adapter.mjs';
const which = process.argv[2];
if (!['baseline','proposed'].includes(which)) throw Error('Choose baseline or proposed');
const { BoardingController, createSeatRegistry } = await import(`./${which}/interaction-core-finite-proposed.mjs`);
const clone = value => structuredClone(value), same = (a,b) => JSON.stringify(a) === JSON.stringify(b);
const seat = { id:'p1',role:'passenger',socket:'seat',boardingSocket:'board',eligibleScenes:['1904'] };
const defer = () => { let resolve,reject;const promise=new Promise((yes,no)=>{resolve=yes;reject=no;});return{promise,resolve,reject}; };
const turn = () => new Promise(resolve => setImmediate(resolve));
function fixture() {
  const s={visitor:{e:4,n:2},camera:{x:3,fov:52},attached:false,speed:0,stops:0,follow:0,releases:0,
    commits:0,compensations:0,flags:{},leases:Object.fromEntries(['visitor','camera','person','model'].map(k=>[k,{kind:k}]))};
  let controller;
  const base={captureVisitor:()=>clone(s.visitor),captureCamera:()=>clone(s.camera),
    restoreVisitor(v){if(s.flags.restoreVisitor==='before')throw Error('visitor-before');s.visitor=clone(v);if(s.flags.restoreVisitor==='after')throw Error('visitor-after');},
    restoreCamera(v){if(s.flags.restoreCamera==='before')throw Error('camera-before');s.camera=clone(v);if(s.flags.restoreCamera==='after')throw Error('camera-after');},
    async planApproach(){return{clear:true,point:{e:1,n:1}};},async moveVisitor(path){s.visitor=clone(path.point);},
    async attachVisitor(){s.attached=true;s.camera={x:8,fov:40};},
    detachVisitor(exit){if(s.flags.detach==='before')throw Error('detach-before');s.attached=false;if(exit)s.visitor=clone(exit.point);if(s.flags.detach==='after')throw Error('detach-after');},
    vehicleStatus:()=>({speed_m_s:s.flags.unknownSpeed?undefined:s.speed}),
    async stopVehicle(){s.stops++;if(s.flags.stopReject)throw Error('stop-rejected');if(s.flags.stopDeferred)await s.flags.stopDeferred.promise;
      if(!s.flags.nonzero)s.speed=0;return{completed:true,finalNeutral:true};},
    async startVehicle(){s.speed=1;return{started:true};},
    async resolveExit(){return s.flags.blocked?{clear:false,reason:'occupied'}:{clear:true,point:{e:9,n:9}};},
    updateSeatedCamera(){s.follow++;s.camera.x++;},
  };
  const ports={commitKind:'synchronous-compensated-v1',isStopped:()=>s.speed===0,
    captureLeases(ctx){return{ownerToken:ctx.token,...s.leases,attached:s.attached};},
    verifyHeld(lease){return ['visitor','camera','person','model'].every(k=>s.leases[k]===lease[k])&&s.attached===lease.attached;},
    async prepare(ctx){if(s.flags.prepareDeferred)await s.flags.prepareDeferred.promise;
      if(s.flags.providerRetired)return{prepared:false};
      return{prepared:true,compensationReady:true,ownerToken:ctx.token,exit:ctx.exit,held:{visitor:clone(s.visitor),camera:clone(s.camera),attached:s.attached}};},
    commit(plan,ctx){s.commits++;base.detachVisitor(plan.exit);if(!plan.exit)base.restoreVisitor(ctx.saved.visitor);base.restoreCamera(ctx.saved.camera);
      if(s.flags.commitReceipt)return{committed:false};return{committed:true,ownerToken:ctx.token};},
    verifyRecovered(receipt,plan,ctx){return!s.flags.verifyRecovered&&s.attached===false&&same(s.visitor,plan.exit?.point??ctx.saved.visitor)&&same(s.camera,ctx.saved.camera)
      &&['visitor','camera','person','model'].every(k=>s.leases[k]===ctx.lease[k]);},
    releaseLeases(receipt,plan,ctx){for(const k of ['visitor','camera','person','model']){assert.equal(s.leases[k],ctx.lease[k]);s.leases[k]=null;}
      if(s.flags.releaseAfter)throw Error('release-after');s.releases++;return{released:true,ownerToken:ctx.token};},
    verifyReleased:()=>Object.values(s.leases).every(x=>x===null),
    compensate(plan,ctx){s.compensations++;s.visitor=clone(plan.held.visitor);s.camera=clone(plan.held.camera);s.attached=plan.held.attached;
      for(const k of ['visitor','camera','person','model'])s.leases[k]=ctx.lease[k];
      return{compensated:!s.flags.compensationFalse,ownerToken:ctx.token};},
  };
  const adapter=createStrictRecoveryAdapter({base,ports,getOwner:()=>controller?.reservation});
  const registry=createSeatRegistry();
  controller=new BoardingController({vehicleId:'PARKED-BROUGHAM-CONTRACT-ONLY',scene:'1904',seats:[seat],adapter,registry,requireSettledRollback:true});
  return{s,base,ports,adapter,registry,c:controller};
}
async function seated(f,ride=false){assert.equal(await f.c.approach('p1'),true);assert.equal(await f.c.board(),true);if(ride)assert.equal(await f.c.ride(),true);}
function retained(f,token,saved,leases){assert.equal(f.c.reservation,token);assert.equal(f.c.saved,saved);assert.equal(f.registry.size,1);assert.equal(f.s.attached,true);
  for(const k of ['visitor','camera','person','model'])assert.equal(f.s.leases[k],leases[k]);assert.equal(f.s.releases,0);}
const tests=[];const test=(name,fn)=>tests.push({name,fn});
test('unsupported real ports refuse before any strict reservation',()=>{
  const f=fixture();assert.throws(()=>new BoardingController({vehicleId:'unsupported',scene:'1904',seats:[seat],adapter:f.base,requireSettledRollback:true}),/Unsupported strict recovery/);
});
test('asynchronous commit ports refuse rather than assert atomicity',()=>{
  const f=fixture();assert.throws(()=>createStrictRecoveryAdapter({base:f.base,getOwner:()=>null,ports:{...f.ports,commit:async()=>({committed:true})}}),/asynchronous/);
});
for(const phase of ['detach','restoreVisitor','restoreCamera'])for(const when of ['before','after'])
  test(`${phase} ${when} failure compensates and retains all owners`,async()=>{
    const f=fixture();await seated(f,true);const token=f.c.reservation,saved=f.c.saved,leases={...f.s.leases};f.s.flags[phase]=when;
    assert.equal(await f.c.cancel(),false);assert.equal(f.c.state,'recovery-blocked');retained(f,token,saved,leases);
    const follow=f.s.follow;f.c.tick(.02);assert.equal(f.s.follow,follow+1,'blocked recovery retains moving attachment updates');
    delete f.s.flags[phase];assert.equal(await f.c.cancel(),true);assert.equal(f.c.state,'idle');assert.equal(f.registry.size,0);assert.equal(f.s.releases,1);assert.equal(f.s.attached,false);
    assert(same(f.s.visitor,saved.visitor)&&same(f.s.camera,saved.camera));await f.c.dispose();assert.equal(f.s.releases,1);
  });
test('failed stop never detaches; blocked ticks and explicit retry remain owned',async()=>{
  const f=fixture();await seated(f,true);const token=f.c.reservation,saved=f.c.saved,leases={...f.s.leases};f.s.flags.stopReject=true;
  assert.equal(await f.c.leave(),false);assert.equal(f.c.state,'recovery-blocked');retained(f,token,saved,leases);assert.equal(f.s.commits,0);
  const before=f.s.follow;f.c.tick(.03);assert.equal(f.s.follow,before+1);
  delete f.s.flags.stopReject;assert.equal(await f.c.cancel(),true);assert.equal(f.s.releases,1);assert.equal(f.s.stops,2);
});
test('nonzero or unknown speed is never neutral success',async()=>{
  for(const flag of ['nonzero','unknownSpeed']){const f=fixture();await seated(f,true);f.s.flags[flag]=true;
    const token=f.c.reservation,saved=f.c.saved,leases={...f.s.leases};assert.equal(await f.c.cancel(),false);retained(f,token,saved,leases);assert.equal(f.s.commits,0);}
});
test('canceled waiter retains single owned stop through complete recovery',async()=>{
  const f=fixture();await seated(f,true);const pending=defer();f.s.flags.stopDeferred=pending;
  const leave=f.c.leave();await turn();assert.equal(f.s.stops,1);const cancel=f.c.cancel();await turn();
  assert.equal(f.registry.size,1);assert.equal(f.s.attached,true);assert.equal(f.s.stops,1);
  pending.resolve();assert.equal(await leave,false);assert.equal(await cancel,true);assert.equal(f.s.stops,1);assert.equal(f.s.releases,1);assert.equal(f.registry.size,0);
});
test('repeated cancel joins one pending recovery and releases once',async()=>{
  const f=fixture();await seated(f,true);const pending=defer();f.s.flags.prepareDeferred=pending;
  const a=f.c.cancel(),b=f.c.cancel();await turn();assert.equal(f.s.commits,0);assert.equal(f.registry.size,1);pending.resolve();
  assert.deepEqual(await Promise.all([a,b]),[true,true]);assert.equal(f.s.commits,1);assert.equal(f.s.releases,1);await f.c.dispose();assert.equal(f.s.releases,1);
});
test('failed independent verification compensates exact held state',async()=>{
  const f=fixture();await seated(f,true);const token=f.c.reservation,saved=f.c.saved,leases={...f.s.leases};f.s.flags.verifyRecovered=true;
  assert.equal(await f.c.cancel(),false);retained(f,token,saved,leases);assert.equal(f.s.compensations,1);
});
test('lease release mutate-then-throw is compensated before seat release',async()=>{
  const f=fixture();await seated(f,true);const token=f.c.reservation,saved=f.c.saved,leases={...f.s.leases};f.s.flags.releaseAfter=true;
  assert.equal(await f.c.cancel(),false);retained(f,token,saved,leases);assert.equal(f.s.compensations,1);
  delete f.s.flags.releaseAfter;assert.equal(await f.c.cancel(),true);assert.equal(f.s.releases,1);
});
test('false compensation acknowledgment never declares successful recovery',async()=>{
  const f=fixture();await seated(f,true);f.s.flags.restoreCamera='after';f.s.flags.compensationFalse=true;
  assert.equal(await f.c.cancel(),false);assert.equal(f.c.state,'recovery-blocked');assert.equal(f.registry.size,1);assert.equal(f.s.releases,0);assert.equal(f.c.disposed,false);
});
test('superseded owner/generation cannot release or overwrite newer state',async()=>{
  const f=fixture();await seated(f,true);const pending=defer();f.s.flags.stopDeferred=pending;
  const cancel=f.c.cancel();await turn();const old=f.c.reservation;f.registry.release(old);
  const token=f.registry.reserve('PARKED-BROUGHAM-CONTRACT-ONLY:p1','new-generation'),saved={visitor:{e:99},camera:{fov:99}};
  f.c.reservation=token;f.c.saved=saved;f.c.seat=seat;f.c.generation++;f.c.state='seated';pending.resolve();
  assert.equal(await cancel,false);assert.equal(f.c.reservation,token);assert.equal(f.c.saved,saved);assert.equal(f.c.state,'seated');assert.equal(f.registry.size,1);assert.equal(f.s.releases,0);
});
test('provider retirement request blocks disposal and retains attachment',async()=>{
  const f=fixture();await seated(f,true);const token=f.c.reservation,saved=f.c.saved,leases={...f.s.leases};f.s.flags.providerRetired=true;
  await assert.rejects(f.c.dispose(),/Recovery incomplete/);assert.equal(f.c.disposed,false);retained(f,token,saved,leases);
  delete f.s.flags.providerRetired;await f.c.dispose();assert.equal(f.c.disposed,true);assert.equal(f.s.releases,1);
});
test('blocked exit stays seated and preserves ownership before retry',async()=>{
  const f=fixture();await seated(f,true);f.s.flags.blocked=true;const token=f.c.reservation,saved=f.c.saved,leases={...f.s.leases};
  assert.equal(await f.c.leave(),false);assert.equal(f.c.state,'blocked-exit');retained(f,token,saved,leases);const n=f.s.follow;f.c.tick(.02);assert.equal(f.s.follow,n+1);
  f.s.flags.blocked=false;assert.equal(await f.c.leave(),true);assert.equal(f.s.releases,1);assert.equal(f.registry.size,0);
  assert.deepEqual(f.s.visitor,{e:9,n:9});
});
test('strict leave restore failure compensates before releasing any ownership',async()=>{
  const f=fixture();await seated(f,true);const token=f.c.reservation,saved=f.c.saved,leases={...f.s.leases};f.s.flags.restoreCamera='after';
  assert.equal(await f.c.leave(),false);retained(f,token,saved,leases);assert.equal(f.c.state,'recovery-blocked');
});
test('context cancellation supersedes prepared exit before recovery commits',async()=>{
  const f=fixture();await seated(f,true);const pending=defer();f.s.flags.prepareDeferred=pending;
  const leave=f.c.leave();await turn();assert.equal(f.s.commits,0);const saved=f.c.saved;
  const cancel=f.c.contextChanged('Destination changed');await turn();assert.equal(f.registry.size,1);pending.resolve();
  assert.equal(await leave,false);assert.equal(await cancel,true);assert.equal(f.s.releases,1);assert(same(f.s.visitor,saved.visitor));
});
let failed=0;const results=[];
for(const {name,fn}of tests){try{await fn();results.push({name,status:'PASS'});}catch(e){failed++;results.push({name,status:'FAIL',reason:String(e.message).slice(0,500)});}}
console.log(JSON.stringify({core:which,status:failed?'FAIL':'PASS',tests:tests.length,failed,results,
  qualification:'Synthetic contract controls only; no physical boarding/motion/scene/UI/current-app acceptance.'}));
process.exitCode=failed?1:0;

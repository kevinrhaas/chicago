// SPDX-License-Identifier: GPL-3.0-or-later
// Real six-person militia days: work source follows separated spots, not authored overlap.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import {createHumanDays} from '../renderers/web/js/human-days.js';
const here=new URL('../',import.meta.url);
const records=await Promise.all(Array.from({length:6},(_,i)=>fs.readFile(new URL(`data/humans/instances/1812/hi_town_chicago_militia_unnamed_${i+1}_1812.json`,here),'utf8').then(JSON.parse)));
function actorOf(instance){const p=instance.placement;const a={id:instance.id,personId:instance.person_id,instance,
 e:p.local_e,n:p.local_n,heading:p.heading_deg,state:'standing',indoors:false,inRange:true,path:null,
 root:{visible:true,getWorldPosition(v){v.x=a.e;v.y=0;v.z=-a.n;return v;}},actions:{setTalk(){},hold(){}},
 place(){},setState(s){a.state=s;},setIndoors(on){a.indoors=on;},turnTo(h){a.heading=h;},
 walkPath(points,{endHeading,onArrive}={}){a.pending={point:points.at(-1),heading:endHeading,onArrive};a.state='walking';return true;}};return a;}
const actors=records.map(actorOf);
const humans={actors,shown:true,isHeld:()=>false};let date='1812-08-14',hour=15;
const doors=JSON.parse(await fs.readFile(new URL('data/humans/doors_1812.json',here),'utf8'));
const days=createHumanDays({humans,date:()=>date,hour:()=>hour,doors});
const id=records[3].id;
function step(){for(const a of actors){if(a.pending){const p=a.pending;a.pending=null;a.e=p.point.e;a.n=p.point.n;a.heading=p.heading??a.heading;p.onArrive?.();}}days.update(.1);}
let found=null;
for(let i=0;i<100&&!found;i++){step();found=days.workSource(id);}
assert(found,'default August 14 packing produces a real primary work source');
assert.deepEqual(found.originalAt,{e:1082,n:165});
assert(Math.hypot(actors[3].e-found.at.e,actors[3].n-found.at.n)<.01);
assert.equal(found.doing,'packing for the march; the agency house emptied');
const packing={...found.at};
hour=2;step();assert.equal(days.workSource(id),null,'indoors at night');
date='1812-02-15';hour=15;step();assert.equal(days.workSource(id),null,'this militia actor is not present in winter');
date='1812-04-15';hour=10;found=null;
for(let i=0;i<100&&!found;i++){step();found=days.workSource(id);}
assert(found);assert.deepEqual(found.originalAt,{e:1072.5,n:177});assert.match(found.doing,/mending the planking/);
console.log(`Work day source: actual default packing at ${JSON.stringify(packing)}, spring repair at ${JSON.stringify(found.at)}; winter/night absent`);

// Explicit overlap regression: authored work places may be separated by the day engine.
const shared=structuredClone(records[3]);shared.id='hi_shared_test';shared.person_id='shared_test';
const pair=[actorOf(records[3]),actorOf(shared)];
const overlap=createHumanDays({humans:{actors:pair,shown:true,isHeld:()=>false},date:()=> '1812-08-14',hour:()=>15,doors});
let separated=null;
for(let i=0;i<100&&!separated;i++){
 for(const a of pair)if(a.pending){const p=a.pending;a.pending=null;a.e=p.point.e;a.n=p.point.n;a.heading=p.heading??a.heading;p.onArrive?.();}
 overlap.update(.1);separated=overlap.workSource(id);
}
assert(separated);assert.deepEqual(separated.originalAt,{e:1082,n:165});
assert(Math.hypot(separated.at.e-1082,separated.at.n-165)>.1,'overlap fixture returns real separated spot');
console.log('Work source overlap regression: original and rendered work locations remain distinct.');

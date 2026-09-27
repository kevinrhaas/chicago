import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createBags, createLoadingContent, CONTENT_PHASE, dwellMs} from '../renderers/web/js/loading-content.js';
const entries = JSON.parse(fs.readFileSync(new URL('../data/loading/statuses.json', import.meta.url))).entries;
const sequence = seed => { const bag=createBags(entries,seed); return Array.from({length:25},()=>bag.next('prepare').id); };
assert.deepEqual(sequence('repeat'),sequence('repeat'));
assert.notDeepEqual(sequence('repeat'),sequence('different'));
for (const phase of Object.values(CONTENT_PHASE)) {
 const bag=createBags(entries, 'phase-'+phase), size=entries.filter(e=>e.phase===phase&&e.kind!=='humor').length;
 const first=Array.from({length:size},()=>bag.next(phase));
 assert.equal(new Set(first.map(e=>e.id)).size,size);
 assert.ok(first.every(e=>e.phase===phase));
 assert.notEqual(bag.next(phase).id,first.at(-1).id);
}
let humor=0;
for(let seed=0;seed<10000;seed++){
 const bag=createBags(entries,seed);let jokes=0;
 for(let i=0;i<84;i++) if(bag.next('prepare').kind==='humor') jokes++;
 assert.ok(jokes<=1); if(jokes) humor++;
 assert.equal(bag.next('land'),null);
}
assert.ok(humor<=100); console.log(`Humor: ${humor}/10000 seeded sessions (at most one per session)`);
assert.equal(dwellMs({min_dwell_ms:2400},20),4000);
assert.equal(dwellMs({min_dwell_ms:2000},.1),2000);
function fixture(options={}){
 let at=0, id=0;const timers=new Map(),listeners=new Map();
 const boot={expected:{scene:.2,flora:5},phases:[],on:(k,fn)=>{if(!listeners.has(k))listeners.set(k,[]);listeners.get(k).push(fn);}};
 const emit=(type,phase)=>{for(const fn of listeners.get(type)||[])fn({phase});};
 const card={textContent:'',dataset:{}};
 const content=createLoadingContent({boot,cardEl:card,seed:42,entries,now:()=>at,
  schedule:(fn,ms)=>{timers.set(++id,{fn,due:at+ms});return id;},cancel:i=>timers.delete(i),...options});
 const advance=ms=>{at+=ms;for(const [i,t]of [...timers])if(t.due<=at){timers.delete(i);t.fn();}};
 return {content,emit,card,timers,advance,boot};
}
let f=fixture();assert.equal(f.card.dataset.loadingKind,'source');
f.emit('phasestart',{id:'flora',essential:true});f.advance(4000);assert.equal(f.card.dataset.loadingPhase,'prepare');assert.equal(f.card.dataset.loadingKind,'build');
f.emit('phasestart',{id:'scene',essential:true});f.advance(4000);assert.equal(f.card.dataset.loadingPhase,'assess');
f.emit('ready');const before=f.card.textContent;f.advance(5000);assert.equal(f.card.textContent,before);assert.equal(f.timers.size,0);
f.content.land();f.content.land();assert.equal(f.card.dataset.loadingPhase,'land');assert.equal(f.content.state.count,4);
f=fixture();f.emit('error',{essential:false});assert.equal(f.content.state.stopped,false);f.emit('error',{essential:true});assert.equal(f.card.dataset.loadingKind,'error');assert.equal(f.timers.size,0);f.content.land();assert.equal(f.card.dataset.loadingKind,'error');
f=fixture();f.emit('phasestart',{id:'flora',essential:true});
const floraKinds=[];for(let i=0;i<10;i++){f.advance(4000);floraKinds.push(f.card.dataset.loadingKind);}
assert.equal(floraKinds[0],'build');assert.ok(floraKinds.includes('fact'),'long flora phase must not starve facts');
f=fixture({warm:true});f.advance(30000);f.emit('phasestart',{id:'flora',essential:true});f.advance(10000);f.content.land();assert.equal(f.content.state.count,2);
f=fixture();f.advance(100);f.emit('ready');f.content.land();assert.equal(f.content.state.count,2);
f=fixture();f.emit('ready');f.content.land();const end=f.card.textContent;
await f.content.load('/statuses',async()=>({ok:true,json:async()=>({schema_version:1,entries})}));assert.equal(f.card.textContent,end);
await f.content.load('/statuses',async()=>{throw Error('offline');});assert.equal(f.card.textContent,end);
const early=entries.filter(e=>e.phase==='collect').slice(0,3), b=createBags(early,12);
const old=b.next('collect');b.replace(entries);assert.notEqual(b.next('collect').id,old.id);
console.log('LOADING RUNTIME PASS — seed, shuffle, phase, dwell, warm/fast, stop, optional fetch and hydration');

#!/usr/bin/env node
// Actual native parameters and actual walking consumer share two reconstructed seats.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {register} from 'node:module';
const vendor=new URL('../renderers/web/vendor/three-0.185.1/',import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s,c,next){if(s==='three')return {url:'${vendor}three.module.js',shortCircuit:true};if(s.startsWith('three/addons/'))return {url:'${vendor}addons/'+s.slice(13),shortCircuit:true};return next(s,c);}`)}`,import.meta.url);
const THREE=await import('three');
const {stockadePlan,createFortGates,FORT_GATES,SWING_S}=await import('../renderers/web/js/fort-gates.js');
const {footprintsFrom,createWalker}=await import('../renderers/web/js/walker.js');
const {createInteractions}=await import('../renderers/web/js/interact.js');
const {createIntent}=await import('../renderers/web/js/controls/intent.js');
const root=new URL('../',import.meta.url);
const record=JSON.parse(fs.readFileSync(new URL('data/structures/fort_dearborn_palisade.json',root)));
const phase=record.phases[0];
// Native sidecar compilation copies these consumed form values unchanged. A zero
// bearing on a flat plane isolates gate behavior from unrelated datum/terrain.
const sidecar={id:record.id,archetype:record.archetype,footprint:phase.footprint,
 placement:{local_e:0,local_n:0,rotation_deg:0},attributes:phase.form};
const registry=new Map([[record.id,{id:record.id,sidecar}]]);
const plan=stockadePlan(sidecar);
assert.equal(plan.gates.length,4);
for(const side of ['n','s']){const g=plan.gates.find(x=>x.side===side);assert.equal(g.kind,'gateway');assert.equal(g.half,1.8);}
for(const [side,y] of [['e',41],['w',11.5]]){
 const g=plan.gates.find(x=>x.side===side);assert.equal(g.kind,'wicket');assert.deepEqual(g.centre,[side==='e'?53:0,y]);
 assert.equal(g.confidence,1);assert(FORT_GATES[record.id][side]);
}
const footprints=footprintsFrom(registry),ix=createInteractions(),problems=[];
const layer=createFortGates({registry,buildings:{matrixOf:()=>new THREE.Matrix4()},footprints,problems,interactions:ix});
assert.deepEqual(problems,[]);
assert.equal(layer.gates.length,4,'each hole has an actual leaf and interaction');
for(const gate of layer.gates)ix.add(gate);
// The actual consumer's closed/open barrier contract; a walker approaches the
// east and west posterns from their outside, then crosses after the leaf swings.
const terrain={walkHeight:()=>0,surfaceHeight:()=>0,isWater:()=>false};
for(const side of ['e','w']){
 const gate=layer.gates.find(x=>x.id.endsWith(':'+side));
 assert(gate,'named actual runtime postern '+side);
 assert.equal(gate.state,'closed');
 const shut=footprints.find(x=>x.id===record.id);
 assert(shut.walls.length>plan.walls.length,'closed postern adds a barrier');
 const centre=plan.gates.find(x=>x.side===side).centre;
 const outside=side==='e'?centre[0]+2:centre[0]-2;
 function walk(){
  const walker=createWalker({camera:new THREE.PerspectiveCamera(),terrain,footprints,
   spawn:{local_e:outside,local_n:centre[1],yaw_deg:side==='e'?270:90}});
  const intent=createIntent();intent.forward=1;
  for(let i=0;i<180;i++)walker.update(1/60,intent);
  return walker.state.e;
 }
 const closedEnd=walk();assert(side==='e'?closedEnd>53:closedEnd<0,'closed postern stops actual walker');
 const result=ix.act(gate,'open');assert(result.ok);
 ix.update(SWING_S+0.1);assert.equal(gate.state,'open');
 const openEnd=walk();assert(side==='e'?openEnd<52.5:openEnd>.5,'opened postern passes actual walker');
}
console.log('PASS second-fort posterns: four real runtime leaves; existing3.6m main gates retained; reconstructed side seats, closed barriers and actual open interactions');

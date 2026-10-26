// SPDX-License-Identifier: GPL-3.0-or-later
// Independent expected pins applied to the ACTUAL main.js declaration/selector.
// The native gate fixes the measured Full policy; it accepts no override.
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
if(process.argv.length!==2)throw Error('This policy gate accepts no overrides');
const mainPath=new URL('../../../renderers/web/js/main.js',import.meta.url),expectedFull=4700000;
const source=fs.readFileSync(mainPath,'utf8'),sha=x=>crypto.createHash('sha256').update(x).digest('hex');
function section(s,start,end){const a=s.indexOf(start);assert(a>=0,start);const b=s.indexOf(end,a);assert(b>a,end);return s.slice(a,b+end.length)}
async function load(s){
 const table=section(s,'const DETAIL_DECLARED = {','\n};'),order=section(s,'const DETAIL_ORDER = [','];'),seal=section(s,'const sealLadder = (declared, order) => {','\n};');
 const full=section(s,'const GLESSNER_V4_FULL_TRIANGLES =',';'),light=section(s,'const GLESSNER_V4_LIGHT_TRIANGLES =',';');
 const select=section(s,'const detailLevels = inspectionLod ? {','} : DETAIL;'),budget=section(s,'const BUDGET = {',';');
 const module=`const FURNITURE_REACH_BALANCED_M=null,FURNITURE_REACH_LIGHT_M=null,GROUND_DETAIL_REACH_LIGHT_M=null;\n${table}\n${order}\n${seal}\nconst DETAIL=sealLadder(DETAIL_DECLARED,DETAIL_ORDER);\n${full}\n${light}\n${budget}\nexport const driverBudget=BUDGET;\nexport const ordinary=DETAIL;\nexport function select(inspectionLod){${select}\nreturn detailLevels}`;
 return import('data:text/javascript;base64,'+Buffer.from(module).toString('base64'));
}
function check(m){
 const base=m.ordinary,off=m.select(false),on=m.select(true);
 assert.equal(m.driverBudget.drawCalls,7800,'General driver draw-call ceiling unchanged');
 assert.equal(m.driverBudget.triangles,3470000,'Ordinary driver triangle ceiling unchanged');
 assert.equal(off,base,'No inspection uses exact original table');
 assert.equal(base.full.triangles,3470000,'Ordinary Full unchanged');assert.equal(base.balanced.triangles,2625000,'Balanced unchanged');assert.equal(base.light.triangles,1190000,'Ordinary Light unchanged');
 assert.equal(on.full.triangles,expectedFull,'Only measured selected Full allowance');assert.equal(on.full.declared,expectedFull,'Declaration matches runtime Full');
 assert.equal(on.light.triangles,1270000,'Selected Light floor unchanged');assert.equal(on.light.declared,1270000,'Selected Light declaration unchanged');
 assert.equal(on.balanced,base.balanced,'Inspection cannot replace Balanced policy');
 for(const level of['full','light']){
  assert.deepEqual(Object.keys(on[level]).sort(),Object.keys(base[level]).sort());
  for(const key of Object.keys(base[level]))if(!['triangles','declared','measured'].includes(key))assert.deepEqual(on[level][key],base[level][key],`${level} original ${key} unchanged`);
 }
 const snapshot=JSON.stringify(base);on.full.triangles=1;on.light.triangles=1;assert.equal(JSON.stringify(base),snapshot,'Selected copies cannot mutate original table');
 assert.equal(m.select(false),base,'Turning inspection off restores original policy object');
 const restored=m.select(true);assert.equal(restored.full.triangles,expectedFull);assert.equal(restored.light.triangles,1270000);
 return{ordinary:{full:base.full.triangles,balanced:base.balanced.triangles,light:base.light.triangles},inspection:{full:restored.full.triangles,balanced:restored.balanced.triangles,light:restored.light.triangles}};
}
const policy=check(await load(source)),controls=[];
for(const[name,mutate]of[
 ['Inspection Full unauthorized extra triangle',s=>s.replace(/const GLESSNER_V4_FULL_TRIANGLES = \d+;/,`const GLESSNER_V4_FULL_TRIANGLES = ${expectedFull+1};`)],
 ['Inspection Light increase',s=>s.replace('const GLESSNER_V4_LIGHT_TRIANGLES = 1270000;','const GLESSNER_V4_LIGHT_TRIANGLES = 1270001;')],
 ['Ordinary Light increase',s=>s.replace('light:    { triangles: 1190000,','light:    { triangles: 1190001,')],
 ['Balanced increase',s=>s.replace('balanced: { triangles: 2625000,','balanced: { triangles: 2625001,')],
 ['Ordinary Full increase',s=>s.replace('full:     { triangles: 3470000,','full:     { triangles: 3470001,')],
 ['Selected Full shadow reach',s=>s.replace('full: { ...DETAIL.full, triangles:', 'full: { ...DETAIL.full, shadowReachM: 241, triangles:')],
 ['Selected Light shadow reach',s=>s.replace('light: { ...DETAIL.light, triangles:', 'light: { ...DETAIL.light, shadowReachM: 121, triangles:')],
 ['Selected Full furniture shadows',s=>s.replace('full: { ...DETAIL.full, triangles:', 'full: { ...DETAIL.full, furnitureCastsShadow: false, triangles:')],
 ['General draw-call increase',s=>s.replace('const BUDGET = { drawCalls: 7800,','const BUDGET = { drawCalls: 7801,')],
]){
 const bad=mutate(source);assert.notEqual(bad,source,`Control actually changes source: ${name}`);let rejected=null;
 try{check(await load(bad))}catch(e){rejected=e.message}assert(rejected,`Negative control escaped: ${name}`);controls.push({name,correctly_rejected:rejected});
}
const result={scope:'Actual main declaration/selector policy isolation only; no renderer/world/FPS claim',main_sha256:sha(source),policy,controls,pass:true};
console.log(JSON.stringify(result,null,2));

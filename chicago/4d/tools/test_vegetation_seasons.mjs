#!/usr/bin/env node
// T-3748: seasonal dates and evergreen coverage from real species geometry.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { register } from 'node:module';
const vendor=new URL('../renderers/web/vendor/three-0.185.1/',import.meta.url).href;
register(`data:text/javascript,${encodeURIComponent(`export function resolve(s,c,next) {
  if(s==='three')return {url:'${vendor}three.module.js',shortCircuit:true};
  if(s.startsWith('three/addons/'))return {url:'${vendor}addons/'+s.slice(13),shortCircuit:true};
  return next(s,c);
}`)}`,import.meta.url);
const {seasonDate,seasonForDate,applySeasonLook,seasonUniforms}=await import('../renderers/web/js/season.js');
const {buildTreeTemplate,EVERGREEN_BELOW_V}=await import('../renderers/web/js/tree-model.js');
const read=p=>JSON.parse(fs.readFileSync(new URL('../'+p,import.meta.url),'utf8'));
for (const year of ['1812','1835','1871','1904']) {
  const target=read(`data/scenes/${year}.json`).target_date;
  const own=seasonForDate(target);
  assert.equal(seasonDate(own,target),target,`${year} keeps its own dated reconstruction`);
  for (const [s,day] of Object.entries({spring:'04-15',summer:'07-15',fall:'10-15',winter:'02-15'})) {
    assert.equal(seasonDate(s,target),s===own?target:`${year}-${day}`);
  }
}
assert.equal(seasonForDate('1871-10-08'),'fall');
assert.equal(seasonDate('fall','1871-10-08'),'1871-10-08');
assert.equal(seasonDate('summer','1871-10-08'),'1871-07-15');
assert.equal(seasonForDate(null),null);assert.equal(seasonForDate('1871-13-01'),null);
assert.equal(seasonDate('unknown','1871-10-08'),'1871-10-08');
for (const id of ['juniperus_virginiana','pinus_banksiana']) {
  const t=buildTreeTemplate({speciesId:id,arch:id,form:'open',h:[12,12],evergreen:true},3748,'near');
  const uv=t.leaves.getAttribute('uv');assert(uv.count>0);
  for (let i=0;i<uv.count;i++) assert(uv.getY(i)<EVERGREEN_BELOW_V+1e-7,
    `${id}: its whole scale/needle tile keeps evergreen colour`);
  t.wood.dispose();t.leaves.dispose();
}
for (const [s,fresh] of [['spring',1],['summer',0],['fall',0],['winter',0]]) {
  applySeasonLook(s);assert.equal(seasonUniforms.uChiFresh.value,fresh);
}
applySeasonLook('summer');

console.log('PASS all-year seasonal dates, representative summer for1871, complete scale/needle evergreen atlas coverage and spring uniform');

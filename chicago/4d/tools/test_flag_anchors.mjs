#!/usr/bin/env node
/** Pure CPU contract tests; no canvas, browser, Three or shipped GLB needed. */
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const { flownFlags, flagMount } = await import(path.join(root, 'renderers/web/js/flag-anchors.js'));
const defaults = { fly: 12*.3048, hoistToFly: 1/1.85, truckGap: .18 };
const levels = { attested: 0, inferred: .5, reconstructed: 1 };
const attr = (value, confidence='attested') => ({ value, confidence });
const box = { min: [-2.32, 0, -11.46], max: [17.56, 15.061870575, 2.32] };
const record = JSON.parse(fs.readFileSync(path.join(root, 'data/structures/tremont_house_1.json')));
const phase = record.phases.find(p => p.id === 'frame_1833');
const registry = new Map([[record.id, {id: record.id, sidecar: { phase: phase.id,
  target_date: '1835-07-01', attributes: phase.form } }]]);
let tests = 0;
const ok = (name, fn) => { fn(); tests++; console.log('  ok '+name); };
ok('unanchored fort mount exactly retains legacy bounding-box computation', () => {
  const b = {min: [-.2, 0, -.3], max: [.2, 15, .3]};
  assert.deepEqual(flagMount({id: 'fort'}, b, defaults), {
    axis: [0, 15, 0], foot: [0, 0, 0], radius: .4/2*.6,
    fly: defaults.fly, hoist: defaults.fly*defaults.hoistToFly,
  });
  const old = flownFlags(new Map([['fort', {id:'fort',sidecar:{attributes:{flag:attr('us_flag_24_star'),flag_flying:attr(true,'inferred')}}}]]),levels);
  assert.deepEqual(old, [{id:'fort',pattern:'us_flag_24_star',confidence:.5}]);
});
ok('phase-selected roof data maps east/north/up to local glTF without hotel centre', () => {
  const flags = flownFlags(registry, levels); assert.equal(flags.length, 1);
  const mount = flagMount(flags[0], box, defaults), a = phase.form.flag_anchor.value;
  assert.deepEqual(mount.axis, [a.head[0], a.head[2], -a.head[1]]);
  assert.deepEqual(mount.foot, [a.foot[0], a.foot[2], -a.foot[1]]);
  assert.notEqual(mount.axis[0], (box.min[0]+box.max[0])/2);
  assert.equal(mount.radius, .035); assert.equal(mount.fly, 1.85); assert.equal(mount.hoist, 1.3);
  // Both horizontal components map independently; a north-axis staff isn't
  // mistaken for east, and a placement rotation/translation happens only later.
  const altered = {...flags[0],anchor:{...a,head:[2,6,14],foot:[2,6,10]}};
  assert.deepEqual(flagMount(altered,box,defaults).axis,[2,14,-6]);
});
ok('record anchor stays on reconstructed generator spar and source bounds', () => {
  const a=phase.form.flag_anchor.value, f=phase.form;
  const w=Math.max(...phase.footprint.polygon.map(p=>p[0]));
  const d=Math.max(...phase.footprint.polygon.map(p=>p[1]));
  const ridge=f.wall_height_m.value+(d/2+.25)*Math.tan(f.roof_pitch_deg.value*Math.PI/180);
  assert.deepEqual(a.head.slice(0,2),[w*.37,d/2]);
  assert.ok(Math.abs(a.head[2]-(ridge+f.flagstaff_height_m.value))<1e-9);
  assert.ok(Math.abs(a.foot[2]-(ridge-.15))<1e-9);
  assert.ok(a.fly_m/f.flagstaff_height_m.value>=.35 && a.fly_m/f.flagstaff_height_m.value<=.50);
  assert.ok(a.hoist_m/f.flagstaff_height_m.value>=.25 && a.hoist_m/f.flagstaff_height_m.value<=.40);
  assert.equal(f.flag.value,'us_flag_24_star');
});
ok('anchor grade participates in cloth confidence and absence keeps it off', () => {
  const r={id:'roof',sidecar:{phase:'p',target_date:'1835-07-01',attributes:{
    flag:attr('us_flag_24_star'),flag_flying:attr(true),flag_anchor:attr({},'reconstructed')}}};
  assert.equal(flownFlags(new Map([['roof',r]]),levels)[0].confidence,1);
  r.sidecar.attributes.flag_anchor.confidence='inferred';
  assert.equal(flownFlags(new Map([['roof',r]]),levels)[0].confidence,.5);
  r.sidecar.attributes.flag_flying.value=false;
  assert.deepEqual(flownFlags(new Map([['roof',r]]),levels),[]);
});
ok('unsupported dates/phase/frames and malformed/stale anchors refuse without fallback', () => {
  const flag=flownFlags(registry,levels)[0], a=flag.anchor;
  const cases=[{anchor:null},{phase:'other'},{targetDate:'1836-07-04'},{targetDate:'1835-02-30'},
    {anchor:{...a,phase:''}},{anchor:{...a,frame:'blender'}},
    {anchor:{...a,head:[NaN,0,10]}},{anchor:{...a,head:[true,4,10]}},
    {anchor:{...a,head:[a.head[0]+1,a.head[1],a.head[2]]}},
    {anchor:{...a,head:[1,1,1],foot:[1,1,2]}},
    {anchor:{...a,radius_m:0}},{anchor:{...a,fly_m:Infinity}},
    {anchor:{...a,hoist_m:20}},{anchor:{...a,head:[a.head[0],a.head[1],30]}},
    {anchor:{...a,valid_from:'1837-01-01',valid_to:'1836-01-01'}}];
  for (const change of cases) assert.throws(()=>flagMount({...flag,...change},box,defaults),Error);
  for (const targetDate of ['1833-01-01','1836-07-03'])
    assert.doesNotThrow(()=>flagMount({...flag,targetDate},box,defaults));
});
console.log(`Flag anchor contract: ${tests} checks passed; no browser or accepted image match.`);

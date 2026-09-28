import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createDestinations } from '../renderers/web/js/destinations.js';
import { createRouter } from '../renderers/web/js/route.js';

const terrain = { surfaceHeight: () => 2, isWater: () => false };
const footprints = [{ id: 'peck_store', pts: [[-3,-3],[3,-3],[3,3],[-3,3]] }];
const router = createRouter({ terrain, footprints });
const record = (name, fn, e, n, confidence = 'attested') => ({ sidecar: {
  name, attributes: { function: { value: fn } }, documented_range: { confidence },
  ...(e === undefined ? {} : { placement: { local_e: e, local_n: n, position_confidence: confidence } }),
} });
const registry = new Map([
  ['peck_store', record("Peck's Store", 'store', 0, 0)],
  ['sauganash_hotel', record('Sauganash Hotel', 'tavern_inn', 70, 60)],
  ['workshop', record('A workshop', 'cooper_shop', 80, 70, 'reconstructed')],
  ['missing', record('Unplaced store', 'store')],
]);
const scene = { anchors: [{ id: 'sauganash', label: 'Sauganash viewpoint', local_e: 30, local_n: 30, yaw_deg: 270 }] };
const index = { intersections: [{ id: 'kinzie_canal', label: 'Kinzie & Canal', local_e: 40, local_n: 40 }] };
const people = { people: [
  { id: 'peck', name: 'Philip Peck', lives_at: { value: 'peck_store' } },
  { id: 'unknown', name: 'Émile Unknown', lives_at: 'absent' },
  { id: 'worker', name: 'A worker', works_at: 'sauganash_hotel' },
] };
const args = { scene, index, registry, people, router, terrain };
const d = createDestinations(args);
assert.deepEqual(d.search('peck').map(t => t.kind).sort(), ['business','person','structure']);
assert.equal(d.byId('business','peck_store').derived_from, 'structure');
assert.equal(d.byId('business','missing').limit, 'No known address');
assert.equal(d.search('kinzie & canal')[0].id, 'kinzie_canal');
assert.deepEqual(d.search('sauganash').map(t => t.kind).sort(), ['anchor','business','person','structure']);
assert.match(d.search('emile')[0].sub, /No known address/);
for (const t of [d.byId('person','unknown'), d.byId('structure','missing'), {kind:'structure',id:'absent'}, null]) assert.equal(d.resolve(t), null);
assert.equal(d.search('workshop').length, 0);
assert.equal(d.search('workshop', {includeReconstructed:true}).length, 2);
assert.ok(d.search('', {kind:'taverns'}).every(t => t.kind === 'structure'));
assert.ok(router.blockedAt(0,0), 'fixture really blocks the building centre');
for (const [kind,id] of [['structure','peck_store'],['intersection','kinzie_canal'],['anchor','sauganash'],['person','peck'],['business','peck_store']]) {
  const target = d.byId(kind,id), r = d.resolve(target);
  assert.ok(r); assert.equal(router.blockedAt(r.standOff.e,r.standOff.n),false);
  assert.equal(r.standOff.y,terrain.surfaceHeight(r.standOff.e,r.standOff.n));
  assert.deepEqual(d.resolve(target),r);
}
const businesses = { businesses: [
  {id:'firm',name:'Peck & Company',people:[{name:'Philip Peck'}],present_at_scene_date:true,where:{kind:'premises',structure_id:'peck_store',from:'1833'}},
  {id:'unlocated',name:'Street firm',where:{kind:'street_only',street:'Lake Street',limit_reason:'Only street known'}},
  {id:'nearby',name:'Opposite firm',where:{kind:'anchored',structure_id:'peck_store',limit_reason:'Opposite, not premises'}},
  {id:'later',name:'Later firm',present_at_scene_date:false,where:{kind:'premises',structure_id:'peck_store'}},
] };
const authored = createDestinations({...args,businesses});
assert.equal(authored.search('',{kind:'business'}).length,4);
assert.ok(authored.search('Philip Peck').some(t => t.id === 'firm'));
assert.equal(authored.resolve(authored.byId('business','firm')).structureId,'peck_store');
for (const id of ['unlocated','nearby','later']) { assert.equal(authored.resolve(authored.byId('business',id)),null); assert.ok(authored.byId('business',id).limit); }
assert.equal(createDestinations({...args,businesses:{businesses:[]}}).search('',{kind:'business'}).length,0);
const blocked = createDestinations({...args,standFor:()=>({e:0,n:0})});
assert.equal(blocked.resolve(blocked.byId('structure','peck_store')),null);
const goto = fs.readFileSync(new URL('../renderers/web/js/goto.js',import.meta.url),'utf8');
assert.ok(!goto.includes('targets.push')); assert.ok(goto.includes('destinations.search'));
console.log('PASS shared destinations: fallback/authored search, unknown addresses, real-router safe ground, one inventory');

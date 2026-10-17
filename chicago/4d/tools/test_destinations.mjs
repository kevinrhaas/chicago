import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createDestinations, sortRows, addressOf, ownerKey, SORTS } from '../renderers/web/js/destinations.js';
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
// T-2740: Go to's orders. Address is street then number, numerically; a row with nothing to
// sort on goes last in every order; the owner is whose house the record says it is.
assert.deepEqual(SORTS.map(s => s.id), ['near', 'far', 'address', 'name', 'owner']);
assert.deepEqual(addressOf('1616-1620 S. Prairie Avenue — the alley building'), { number: 1616, street: 'prairie avenue', text: '1616-1620 S. Prairie Avenue' });
assert.equal(addressOf('Sauganash Hotel'), null);
assert.equal(ownerKey('John J. Glessner'), 'glessner john j. glessner');
assert.equal(ownerKey('Armour/Corwith'), 'armour armour/corwith');
const prairie = new Map([
  ['sherman_house_2100_prairie', record('2100 Prairie Avenue — Sherman Victorian Gothic', 'residence', 0, 200)],
  ['sherman_house_2100_prairie_coach_house', record('2100 S. Prairie Avenue — the alley building of the house at 2100', 'coach house', 10, 200)],
  ['stone_house_2035_prairie', record('2035 Prairie Avenue — Corner of limestone row', 'residence', 0, 50)],
  ['house_1600_prairie', record('1600 Prairie Avenue — brick corner house', 'residence', 0, 20)],
  ['glessner_house', record('John J. Glessner House', 'residence', 0, 100)],
  ['house_2001_indiana', record('2001 Indiana Avenue — brick house', 'residence', 0, 1000)],
]);
prairie.get('glessner_house').sidecar.aka = ['1800 S. Prairie Avenue'];
const pd = createDestinations({ scene: { anchors: [{ id: 'corner', label: 'Prairie at Eighteenth', local_e: 0, local_n: 99 }] }, registry: prairie,
  people: { people: [{ id: 'fmg', name: 'Frances M. Glessner', relationship: 'wife', lives_at: 'glessner_house' },
    { id: 'jjg', name: 'John J. Glessner', relationship: 'head', lives_at: 'glessner_house' }] } });
const ids = (sort, v = { e: 0, n: 0 }) => pd.search('', { kind: 'structure', includeReconstructed: true, sort, visitor: v }).map(t => t.id);
assert.deepEqual(ids('near'), ['house_1600_prairie', 'stone_house_2035_prairie', 'glessner_house', 'sherman_house_2100_prairie', 'sherman_house_2100_prairie_coach_house', 'house_2001_indiana']);
assert.deepEqual(ids('far'), [...ids('near')].reverse());
assert.deepEqual(ids('address'), ['house_2001_indiana', 'house_1600_prairie', 'glessner_house', 'stone_house_2035_prairie',
  'sherman_house_2100_prairie', 'sherman_house_2100_prairie_coach_house']);
// Named buildings A to Z, then the ones whose title only describes them, in title order.
assert.deepEqual(ids('name'), ['stone_house_2035_prairie', 'glessner_house', 'sherman_house_2100_prairie',
  'house_1600_prairie', 'house_2001_indiana', 'sherman_house_2100_prairie_coach_house']);
assert.deepEqual(ids('owner').slice(0, 3), ['glessner_house', 'sherman_house_2100_prairie', 'sherman_house_2100_prairie_coach_house']);
assert.equal(pd.byId('structure', 'glessner_house').owner, 'John J. Glessner');
assert.equal(pd.byId('structure', 'stone_house_2035_prairie').owner, null, 'limestone is not a family');
assert.equal(pd.byId('structure', 'sherman_house_2100_prairie_coach_house').owner, 'Sherman');
assert.equal(pd.byId('person', 'jjg').address.number, 1800);
const all = pd.search('', { includeReconstructed: true, sort: 'address', visitor: { e: 0, n: 0 } });
assert.equal(all.at(-1).kind, 'anchor', 'a viewpoint has no address, so it sorts last');
assert.equal(pd.search('', { includeReconstructed: true, sort: 'near' }).length, all.length, 'no position: every row still listed');
assert.deepEqual(pd.sorts.map(s => s.id), ['near', 'far', 'address', 'name', 'owner']);
assert.deepEqual(d.sorts.map(s => s.id), ['near', 'far', 'name', 'owner'], 'no house numbers, no Address order');
assert.equal(d.search('', { includeReconstructed: true, sort: 'name' }).at(-1).limit, 'No known address', 'a row with nowhere to stand goes last');
const goto = fs.readFileSync(new URL('../renderers/web/js/goto.js',import.meta.url),'utf8');
assert.ok(!goto.includes('targets.push')); assert.ok(goto.includes('destinations.search'));
console.log('PASS shared destinations: fallback/authored search, unknown addresses, real-router safe ground, one inventory, five orders');

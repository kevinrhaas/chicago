import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { HUNT_PHOTOS, HUNT_STORAGE_KEY, validHuntDay, huntDay, huntOrder, huntLink, parseHuntLink,
  huntRounds, huntResult, huntSpotSafe, createHuntSession } from '../renderers/web/js/photo-hunt.js';
import { createDestinations } from '../renderers/web/js/destinations.js';
import { spotTarget } from '../renderers/web/js/photos-tab.js';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const doc = JSON.parse(execFileSync('python3', ['-c',
  'import sys,json;sys.path.insert(0,"tools");import compile_pictures as p;print(json.dumps(p.add_place_names(p.derive(*p.read_tree()),p.load_json(p.PLACE_NAMES))["1904"]))'], { cwd: root, maxBuffer: 4 * 1024 * 1024 }));
const registry = new Map();
for (const id of Object.keys(doc.by_structure)) {
  const file = path.join(root, 'data/sidecars/1904', `${id}.json`);
  if (fs.existsSync(file)) registry.set(id, { sidecar: JSON.parse(fs.readFileSync(file)) });
}
const destinations = createDestinations({ scene: {}, registry }); destinations.addPhotos(doc);
const day = '2026-11-18';
const rounds = huntRounds(doc, destinations, day);
assert.equal(rounds.length, 5, 'all five real photographs meet the evidence requirements');
assert.equal(new Set(rounds.map(r => r.structure)).size, 4, 'five photographs represent four places');
for (const round of rounds) {
  assert.equal(round.structure, HUNT_PHOTOS[round.id], 'duplicate catalogue attachments use the canonical owner');
  const p = doc.by_structure[round.structure].find(p => p.id === round.id);
  const expected = spotTarget(p, registry.get(round.structure).sidecar.placement);
  assert.deepEqual(round.target, expected, 'the existing rotated camera spot is preserved');
  assert.equal(round.date, p.date, 'preserve the source date qualifier separately from its range');
  assert.match(round.image, /-thumb\.jpg$/);
  assert(round.target.e > 1100 && round.target.e < 1800 && round.target.n > -3800 && round.target.n < -2900);
}
const ne = rounds.find(r => r.id === 'a18-rba-taylor-2135-glessner-ne');
assert(Math.abs(ne.target.e - 1425.61595) < .001 && Math.abs(ne.target.n + 3199.31225) < .001,
  'shared Glessner photograph uses the Glessner camera, not the neighboring Keith camera');
for (const [day, valid] of [['2026-11-18', true], ['2024-02-29', true], ['2026-02-29', false],
  ['2026-13-01', false], ['2026-11-18Z', false], ['2026-1-18', false], ['../1904', false], ['1904-01-01', false]])
  assert.equal(validHuntDay(day), valid);
assert.equal(huntDay(new Date('2026-11-19T00:30:00Z')), '2026-11-19');
assert.deepEqual(huntOrder(day), huntOrder(day));
assert.notDeepEqual(huntOrder(day), huntOrder('2026-11-19'));
for (let i = 1; i <= 30; i++) assert.deepEqual([...huntOrder(`2026-11-${String(i).padStart(2, '0')}`)].sort(), Object.keys(HUNT_PHOTOS).sort());
const url = new URL(huntLink(day, 'https://example.test/4d/dev/1904/?token=private&data=remote&moment=1#private'));
assert.equal(url.pathname, '/4d/dev/1904/'); assert.equal(url.hash, '');
assert.deepEqual([...url.searchParams.keys()], ['year', 'nav', 'hunt', 'huntDay']);
assert.deepEqual(parseHuntLink(url.search), { day, version: 1 });
for (const q of ['?hunt=2&huntDay=2026-11-18&year=1904', '?hunt=1&huntDay=2026-02-29&year=1904',
  '?hunt=1&huntDay=2026-11-18&year=1835', '?hunt=1&hunt=1&huntDay=2026-11-18&year=1904']) assert.equal(parseHuntLink(q), null);
assert.equal(huntLink(day, 'javascript:alert(1)'), null);
assert.equal(huntLink('bad', url.href), null);
const row = destinations.byId('photo', ne.id);
const safe = { inBounds: () => true, isWater: () => false, blockedAt: () => false, barrierAt: () => false };
assert(huntSpotSafe(row, safe));
for (const key of ['isWater', 'blockedAt', 'barrierAt']) assert(!huntSpotSafe(row, { ...safe, [key]: () => true }));
assert(!huntSpotSafe(row, { ...safe, inBounds: () => false })); assert(!huntSpotSafe(null, safe));
const badRow = { ...row, picture: { ...row.picture, rights: 'check_required' } };
assert.deepEqual(huntRounds(doc, { byId: (_, id) => id === ne.id ? badRow : destinations.byId('photo', id) }, day), []);
badRow.picture = { ...row.picture, kind: 'ENGRAVING' };
assert.deepEqual(huntRounds(doc, { byId: (_, id) => id === ne.id ? badRow : destinations.byId('photo', id) }, day), []);
badRow.picture = { ...row.picture, years: [1900, 1905] };
assert.deepEqual(huntRounds(doc, { byId: (_, id) => id === ne.id ? badRow : destinations.byId('photo', id) }, day), []);
assert.equal(huntResult(ne, { e: ne.target.e + 3, n: ne.target.n + 4 }).score, 1000);
assert(huntResult(ne, { e: ne.target.e + 100, n: ne.target.n }).score < 200);
assert.equal(huntResult(ne, { e: Infinity, n: 0 }), null);

let raw = null;
const storage = { getItem: () => raw, setItem: (key, value) => { assert.equal(key, HUNT_STORAGE_KEY); raw = value; } };
let session = createHuntSession({ day, rounds, storage });
assert.equal(session.next(), false); assert.equal(session.guess(null), false);
assert(session.guess(rounds[0].target)); assert.equal(session.guess(rounds[0].target), false, 'one guess per photo');
session = createHuntSession({ day, rounds, storage });
assert.equal(session.state.cursor, 0); assert.equal(session.state.score, 1000, 'reloading preserves the reveal and score');
assert(session.next()); assert(session.skip()); assert(session.next());
for (let i = 2; i < 5; i++) { assert(session.guess(rounds[i].target)); assert(session.next()); }
assert(session.state.complete); assert.equal(session.state.score, 4000); assert.equal(session.guess(rounds[0].target), false);
assert(raw.length < 4096); session.reset(); assert.equal(session.state.answers.length, 0);
const blocked = createHuntSession({ day, rounds, storage: { getItem: () => null, setItem: () => { throw new Error('quota'); } } });
assert(blocked.guess(rounds[0].target)); assert.equal(blocked.state.issue, 'unsaved'); assert.equal(blocked.state.score, 1000);
raw = '{broken'; session = createHuntSession({ day, rounds, storage });
assert.equal(session.state.issue, 'unreadable'); session.guess(rounds[0].target);
assert.equal(raw, '{broken', 'corrupt saved data is not silently overwritten');
session.reset(); assert.equal(session.state.issue, null); assert.equal(JSON.parse(raw).answers.length, 0);
console.log('PHOTO HUNT PASS — canonical licensed photos and camera positions, dates, daily links, visit guards, distance scores, bounded progress and storage failures');

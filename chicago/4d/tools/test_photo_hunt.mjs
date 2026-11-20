import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { HUNT_PHOTOS, HUNT_STORAGE_KEY, HUNT_SETS, HUNT_MAX_EYE_M, huntSet, huntCount, validHuntDay, huntDay, huntOrder, huntLink, parseHuntLink,
  huntRounds, huntResult, huntSpotSafe, createHuntSession } from '../renderers/web/js/photo-hunt.js';
import { createDestinations } from '../renderers/web/js/destinations.js';
import { spotTarget } from '../renderers/web/js/photos-tab.js';

const root = path.resolve(new URL('..', import.meta.url).pathname);
const docs = JSON.parse(execFileSync('python3', ['-c',
  'import sys,json;sys.path.insert(0,"tools");import compile_pictures as p;print(json.dumps(p.add_place_names(p.derive(*p.read_tree()),p.load_json(p.PLACE_NAMES))))'], { cwd: root, maxBuffer: 64 * 1024 * 1024 }));
function catalogue(year) {
  const doc = docs[year], registry = new Map();
  for (const id of Object.keys(doc.by_structure)) {
    const file = path.join(root, 'data/sidecars', year, `${id}.json`);
    if (fs.existsSync(file)) registry.set(id, { sidecar: JSON.parse(fs.readFileSync(file)) });
  }
  const destinations = createDestinations({ scene: {}, registry }); destinations.addPhotos(doc);
  return { doc, registry, destinations };
}
const { doc, registry, destinations } = catalogue('1904');
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
assert.deepEqual(parseHuntLink(url.search), { day, version: 1, year: '1904' });
// T-3677: the link's year names its set; a year with no set, or two years, is refused.
for (const q of ['?hunt=2&huntDay=2026-11-18&year=1904', '?hunt=1&huntDay=2026-02-29&year=1904',
  '?hunt=1&huntDay=2026-11-18&year=1871', '?hunt=1&huntDay=2026-11-18', '?hunt=1&huntDay=2026-11-18&year=1904&year=1835',
  '?hunt=1&huntDay=2026-11-18&year=constructor', '?hunt=1&hunt=1&huntDay=2026-11-18&year=1904']) assert.equal(parseHuntLink(q), null);
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
assert.equal(session.state.persisted, false, 'an empty first visit must not claim a successful save');
assert.equal(session.next(), false); assert.equal(session.guess(null), false);
assert(session.guess(rounds[0].target)); assert.equal(session.guess(rounds[0].target), false, 'one guess per photo');
session = createHuntSession({ day, rounds, storage });
assert.equal(session.state.cursor, 0); assert.equal(session.state.score, 1000, 'reloading preserves the reveal and score');
assert.equal(session.state.persisted, true);
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
const yesterday = '2026-11-17', oldRounds = huntRounds(doc, destinations, yesterday);
const oldSession = createHuntSession({ day: yesterday, rounds: oldRounds, storage });
oldSession.guess(oldRounds[0].target);
const oldRaw = raw;
session = createHuntSession({ day, rounds, storage });
assert.equal(session.state.answers.length, 0, 'a new day does not reuse another challenge’s guesses');
assert.equal(raw, oldRaw, 'opening a different challenge does not erase saved progress');
const oldLink = huntLink(yesterday, url.href);
assert.equal(parseHuntLink(new URL(oldLink).search).day, yesterday, 'a shared day remains fixed after midnight');
assert.deepEqual(huntOrder(parseHuntLink(new URL(oldLink).search).day), oldRounds.map(r => r.id));
raw = JSON.stringify({ version: 1, day, cursor: 4, answers: [] });
assert.equal(createHuntSession({ day, rounds, storage }).state.issue, 'unreadable');
raw = 'x'.repeat(4097);
assert.equal(createHuntSession({ day, rounds, storage }).state.issue, 'unreadable');
raw = JSON.stringify({ version: 1, year: '1812', day, cursor: 0, answers: [] });
assert.equal(createHuntSession({ day, rounds, storage }).state.issue, 'unreadable', 'another year’s record is not 1904 progress');
const before = JSON.stringify({ version: 1, day, cursor: 1, answers: [{ id: huntOrder(day)[0], skipped: true }] });
raw = before; session = createHuntSession({ day, rounds, storage });
assert.equal(session.state.cursor, 1, 'progress saved before T-3677 still opens');
assert(session.skip()); assert.equal(JSON.parse(raw).year, undefined, '1904 keeps its record format');

// T-3677: the earlier years' sets of prints and drawings, each from its own catalogue.
assert.deepEqual(Object.keys(HUNT_SETS).sort(), ['1835', '1904']);
assert.equal(huntSet('1812'), null, '1812 has two pictures with a spot on safe ground, fewer than a set needs');
assert.equal(huntSet('1871'), null, '1871 has no picture with a camera spot, so no set');
assert.equal(huntSet('__proto__'), null);
const keys = new Set(Object.values(HUNT_SETS).map(s => s.storageKey));
assert.equal(keys.size, 2, 'each year keeps its own saved record');
for (const [year, count, places] of [['1835', 3, 1]]) {
  const cat = catalogue(year), set = huntSet(year);
  assert.equal(huntCount(year), count);
  const yr = huntRounds(cat.doc, cat.destinations, day, year);
  assert.equal(yr.length, count, `${year}: every picture meets the evidence requirements`);
  assert.deepEqual(yr.map(r => r.id), huntOrder(day, year));
  assert.equal(new Set(yr.map(r => r.structure)).size, places);
  assert.deepEqual(huntRounds(cat.doc, cat.destinations, day, '1904'), [], 'a set never reads another year’s catalogue');
  for (const round of yr) {
    const p = cat.doc.by_structure[round.structure].find(p => p.id === round.id);
    assert.equal(round.structure, set.pictures[round.id]);
    assert.deepEqual(round.target, spotTarget(p, cat.registry.get(round.structure).sidecar.placement));
    assert.notEqual(round.kind, 'PHOTO', `${round.id}: a print or drawing, never called a photograph`);
    assert.match(round.kind, /^(ENGRAVING|LITHO|ILLUSTRATION)$/);
    assert(round.later && round.made > Number(year), `${round.id}: made after ${year}, and the reveal says so`);
    assert(p.spot.h <= HUNT_MAX_EYE_M, `${round.id}: a spot on the ground`);
    assert.match(p.rights, /^public domain/);
    assert.equal(new URL(round.image).origin, new URL(cat.doc.image_store.base_url).origin);
    assert.match(round.image, new RegExp(`/${round.id}-thumb\\.jpg$`));
  }
  assert.deepEqual(huntOrder(day, year), huntOrder(day, year));
  for (let i = 1; i <= 30; i++) assert.deepEqual([...huntOrder(`2026-11-${String(i).padStart(2, '0')}`, year)].sort(), Object.keys(set.pictures).sort());
  assert(Array.from({ length: 30 }, (_, i) => huntOrder(`2026-12-${String(i + 1).padStart(2, '0')}`, year).join()).some(o => o !== huntOrder(day, year).join()),
    `${year}: the daily order changes`);
  const link = new URL(huntLink(day, 'https://example.test/4d/1904/?year=1904&token=x', year));
  assert.equal(link.searchParams.get('year'), year);
  assert.deepEqual(parseHuntLink(link.search), { day, version: 1, year });
  link.searchParams.set('year', '1812');
  assert.equal(parseHuntLink(link.search), null, 'a link names one year’s set only');
  const bad = { ...cat.destinations.byId('photo', yr[0].id) };
  const swap = (picture) => ({ byId: (_, id) => id === yr[0].id ? { ...bad, picture } : cat.destinations.byId('photo', id) });
  for (const change of [{ rights: 'unknown — link only' }, { kind: 'POSTCARD' }, { years: [1931, 1931] },
    { spot: { ...bad.picture.spot, h: 20.5 } }])
    assert.deepEqual(huntRounds(cat.doc, swap({ ...bad.picture, ...change }), day, year), [], `${year}: refuses ${JSON.stringify(change)}`);
  let saved = null;
  const box = { getItem: (k) => (k === set.storageKey ? saved : null), setItem: (k, v) => { assert.equal(k, set.storageKey); saved = v; } };
  const s = createHuntSession({ day, rounds: yr, storage: box, year });
  assert.equal(s.state.total, count);
  assert.throws(() => createHuntSession({ day, rounds: yr.slice(1), storage: box, year }));
  assert.throws(() => createHuntSession({ day, rounds: yr, storage: box, year: '1871' }));
  for (let i = 0; i < count; i++) { assert(s.guess(yr[i].target)); assert(s.next()); }
  assert(s.state.complete); assert.equal(s.state.score, count * 1000); assert.equal(s.guess(yr[0].target), false);
  assert.equal(JSON.parse(saved).year, year);
  assert.equal(createHuntSession({ day, rounds: yr, storage: box, year }).state.score, count * 1000, `${year}: progress reloads`);
  assert.equal(createHuntSession({ day, rounds, storage: box }).state.answers.length, 0, `${year}'s record is not read as 1904's`);
  saved = JSON.stringify({ ...JSON.parse(saved), year: '1904' });
  assert.equal(createHuntSession({ day, rounds: yr, storage: box, year }).state.issue, 'unreadable');
}
console.log('PHOTO HUNT PASS — 1904 and 1835 sets: canonical licensed pictures and camera positions, dates, daily links, visit guards, distance scores, bounded progress and storage failures');

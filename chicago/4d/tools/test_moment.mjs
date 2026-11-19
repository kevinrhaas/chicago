import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { normalMoment, parseMoment, momentLink, momentFits, photoSize, stampMoment, jumpHref, nearestOpen } from '../renderers/web/js/moment.js';
const raw = { year: '1904', e: -156.576, n: -3520, bearing: 270, pitch: -5, altitude: null,
  season: 'winter', hour: '16:35', date: '1904-12-15', person: 'glessner_frances', structure: 'glessner_house' };
const expected = { ...raw, e: -156.58 };
assert.deepEqual(normalMoment(raw), expected);
assert.equal(normalMoment({ ...raw, altitude: 900 }).altitude, 900);
assert.equal(normalMoment({ ...raw, altitude: 901 }).altitude, null, 'reject altitudes above the walker ceiling');
const url = momentLink(raw, 'https://chicago.polecat.live/4d/dev/1904/?debug=1&data=https://bad.test/&token=private#private');
const parsed = new URL(url);
assert.equal(parsed.pathname, '/4d/dev/1904/');
assert.equal(parsed.searchParams.has('debug'), false);
assert.equal(parsed.searchParams.has('data'), false);
assert.equal(parsed.searchParams.has('token'), false);
assert.equal(parsed.hash, '');
assert.deepEqual(parseMoment(parsed.search), expected);
for (const year of ['1812', '1835', '1904']) assert.equal(parseMoment(new URL(momentLink({ ...raw, year }, 'https://example.test/renderers/web/')).search).year, year);
for (const e of [null, '', undefined, NaN, Infinity, -100001, '<script>']) assert.equal(normalMoment({ ...raw, e }), null);
for (const year of ['2026', '../1904', '', null]) assert.equal(normalMoment({ ...raw, year }), null);
assert.equal(parseMoment('?year=1904&e=1&n=2'), null);
assert.equal(parseMoment('?moment=2&year=1904&e=1&n=2'), null);
const dropped = normalMoment({ ...raw, person: '../bad', structure: '<script>', season: 'snow', hour: '24:60', date: '1904-02-30' });
for (const key of ['person','structure','season','hour','date']) assert.equal(dropped[key], null);
assert.equal(momentLink(raw, 'javascript:alert(1)'), null);
const checks = { year: '1904', inBounds: (e, n) => e > -1000 && n > -4000, blockedAt: () => false };
assert.equal(momentFits(expected, checks), true);
assert.equal(momentFits(expected, { ...checks, year: '1835' }), false);
assert.equal(momentFits(expected, { ...checks, inBounds: () => false }), false);
assert.equal(momentFits(expected, { ...checks, blockedAt: () => true }), false);
assert.equal(momentFits({ ...expected, altitude: 30 }, { ...checks, blockedAt: () => true }), true);
assert.deepEqual(photoSize(4096, 2048), { width: 1280, height: 640 });
assert.deepEqual(photoSize(400, 800), { width: 400, height: 800 });
assert.throws(() => photoSize(0, 0));
const lines = [], drawing = [], out = { width: 0, height: 0,
  getContext: () => ({ drawImage: (...args) => drawing.push(args), fillRect() {},
    measureText: text => ({ width: text.length * 5 }), fillText: text => lines.push(text) }),
  toBlob(callback, type) { assert.equal(type, 'image/png'); assert.ok(this.height <= 1280 && this.width <= 1280); callback(new Blob(['image'], { type })); } };
const photo = await stampMoment({ width: 4096, height: 4096 }, { ...expected, place: 'Prairie Avenue', sources: [] },
  { doc: { createElement: () => out } });
assert.equal(photo.blob.type, 'image/png');
assert.equal(drawing.length, 1);
assert.ok(lines.some(s => s.includes('not a historical photograph')));
assert.ok(lines.some(s => s.includes('1904-12-15')));
assert.equal(out.width, 1, 'temporary raster released after encoding');
assert.equal(out.height, 1);
// Exercise the real source-rich caption, not a short hand-written stand-in.
const dataRoot = process.env.C4D_TEST_ROOT || path.resolve(new URL('..', import.meta.url).pathname);
const glessner = JSON.parse(fs.readFileSync(path.join(dataRoot, 'data/sidecars/1904/glessner_house.json')));
const sources = glessner.citations.filter(c => c.source_id && c.citation)
  .map(c => Object.freeze({ id: c.source_id, title: c.citation, url: c.url || c.archived_url || '' }));
Object.freeze(sources);
const caption = `Sources for ${glessner.name}: ${sources.map(s => s.title).join('; ')}`;
assert(caption.length >= 9000, 'fixture must retain a genuinely long real citation caption');
let measures = 0;
const fitted = [], fittedCalls = [], widths = [];
const boundedOut = { width: 0, height: 0,
  getContext: () => ({ drawImage() {}, fillRect() {},
    measureText(value) { measures++; return { width: Array.from(value).length * 6 }; },
    fillText(value) { fitted.push(value); fittedCalls.push(measures); widths.push(boundedOut.width - 24); measures = 0; } }),
  toBlob(callback) { callback(new Blob(['image'])); } };
const stamped = await stampMoment({ width: 390, height: 780 }, { ...expected, place: glessner.name, sourceSubject: glessner.name, sources },
  { doc: { createElement: () => boundedOut } });
assert.equal(stamped.sources, sources, 'fitting the image caption preserves every full source in metadata');
assert(fitted[2].startsWith(`Sources for ${glessner.name}:`));
assert(fitted[2].endsWith('…'));
assert(fitted.every((line, i) => Array.from(line).length * 6 <= widths[i]), 'all caption lines fit the raster');
assert(fittedCalls[2] <= Math.ceil(Math.log2(caption.length)) + 3,
  `long source caption took ${fittedCalls[2]} text measurements`);
const captionMeasurements = fittedCalls[2];
assert.equal(boundedOut.width, 1); assert.equal(boundedOut.height, 1);
// Very narrow views must not draw an ellipsis outside the available caption.
fitted.length = fittedCalls.length = widths.length = 0;
await stampMoment({ width: 25, height: 50 }, { year: '1904', place: '🪶 Chicago', sources: [] },
  { doc: { createElement: () => boundedOut } });
assert(fitted.every(line => line === ''));

// T-3669, same spot another year: Jump carries only the ground, facing, season and hour.
{
  const pose = { e: 1410.123, n: -3218, bearing: 90, pitch: -3, altitude: null, season: 'summer', hour: '15:20',
    date: '1904-07-01', person: 'glessner_frances', structure: 'glessner_house' };
  const href = jumpHref('../1812/', pose, { year: 1812, from: '1904' });
  assert(href.startsWith('../1812/?moment=1&'), href);
  const m = parseMoment(href.slice(href.indexOf('?')));
  assert.deepEqual(m, { date: null, year: '1812', e: 1410.12, n: -3218, bearing: 90, pitch: -3, altitude: null,
    season: 'summer', person: null, structure: null, hour: '15:20', via: 'jump', from: '1904' },
    'a date, a person and a building stay with the year that holds them');
  assert.equal(jumpHref('../1835/?x=1#y', null, { year: 1835, from: 1904 }), '../1835/?x=1#y', 'no pose, the plain page');
  assert.equal(jumpHref('../1835/', { e: 'x', n: 1 }, { year: 1835, from: 1904 }), '../1835/', 'a malformed pose, the plain page');
  assert.equal(parseMoment('?moment=1&year=1835&e=1&n=2&via=jump&from=1835').from, null, 'a year is never its own origin');
  assert.equal(parseMoment('?moment=1&year=1835&e=1&n=2&via=elsewhere').via, undefined, 'only a Jump says it is one');
  assert(!momentLink({ ...raw }, 'https://x.test/1904/').includes('via='), 'a shared link never claims to be a Jump');
  // Nearest open ground: the closest free ring point, inside coverage; null when none.
  const inBounds = (e, n) => Math.abs(e) <= 100 && Math.abs(n) <= 100;
  assert.deepEqual(nearestOpen(5, 5, { inBounds, blockedAt: () => false }), { e: 5, n: 5, moved: 0 });
  const house = (e, n) => Math.hypot(e, n) < 7;
  const near = nearestOpen(0, 0, { inBounds, blockedAt: house });
  assert(near && near.moved === 8 && !house(near.e, near.n), JSON.stringify(near));
  assert.equal(nearestOpen(500, 500, { inBounds, blockedAt: () => false }), null, 'outside the town is not moved into it');
  assert.equal(nearestOpen(0, 0, { inBounds, blockedAt: () => true }), null, 'no open ground within reach');
  const edge = nearestOpen(99, 0, { inBounds, blockedAt: (e) => e > 90 });
  assert(edge && inBounds(edge.e, edge.n) && edge.e <= 90);
}
console.log(`MOMENT PASS — private query omitted; Jump keeps only ground, facing, season and hour, nearest open ground in coverage; bounded scene state round-trips; bounds/collision enforced; ${caption.length}-character real source caption fitted in ${captionMeasurements} measurements with intact metadata; stamped PNG released after encoding`);

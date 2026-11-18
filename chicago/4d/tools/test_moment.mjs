import assert from 'node:assert/strict';
import { normalMoment, parseMoment, momentLink, momentFits, photoSize, stampMoment } from '../renderers/web/js/moment.js';
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
console.log('MOMENT PASS — private query omitted; bounded scene state round-trips; bounds/collision enforced; stamped PNG released after encoding');

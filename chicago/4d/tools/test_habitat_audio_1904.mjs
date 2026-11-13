// T-3585. 1904 nature sounds from the parkway elms; no browser, network or decode.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { habitatCandidates, createHabitatAudio } from '../renderers/web/js/habitat-audio.js';
import { TOWN_HABITAT, townHabitatPlacement, townSeasonOfDate } from '../renderers/web/js/habitat-town.js';
// season.js SEASON_DAY (it imports three, so the dates are read from its source).
const SEASON_DAY = Object.fromEntries([...fs.readFileSync(new URL('../renderers/web/js/season.js', import.meta.url), 'utf8')
  .match(/SEASON_DAY = Object\.freeze\(\{([^}]*)\}/)[1].matchAll(/(\w+): '(\d\d-\d\d)'/g)].map(m => [m[1], m[2]]));
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), 'utf8'));
const catalog = read('renderers/web/audio/catalog.json');
const ids = cs => cs.map(c => c.asset.id).sort();
const DATES = { summer: '1904-07-01', ...Object.fromEntries(Object.entries(SEASON_DAY).map(([s, d]) => [s, `1904-${d}`])) };
// Camera at the origin looking along -Z (north): +Z is behind. A tree at n = -50 stands 50 m behind.
const behind = (d = 50, id = 'b') => ({ id, e: 0, n: -d, kind: 'mature' });
const ahead = (d = 50, id = 'a') => ({ id, e: 0, n: d, kind: 'mature' });
function env({ season = 'summer', period = 'day', date = DATES[season], trees = [behind(), behind(20, 'close')], y = 1.7 } = {}) {
  const [hhmm, sunElevation] = { dawn: ['05:00', 0], morning: ['10:00', 40], day: ['15:00', 50], dusk: ['20:00', -3], night: ['23:00', -20] }[period];
  return { season, time: { date, hhmm }, sunElevation, streetTrees: trees,
    camera: { position: { x: 0, y, z: 0 }, quaternion: { x: 0, y: 0, z: 0, w: 1 } },
    flora: { zoneAt: () => null }, terrain: { loaded: true, isWater: () => false, surfaceHeight: () => 0.5,
      height: () => { throw Error('navigation height is not audible ground'); }, heightfield: { contains: () => true } } };
}
const at = (e, opts) => habitatCandidates(catalog, e, '1904', opts);

test('1904 placements are their own, sourced and on assets already verified for 1812/1835', () => {
  const scoped = catalog.assets.filter(a => a.town_placements);
  assert.deepEqual(scoped.map(a => a.id).sort(), ['late-summer-katydid', 'robin-calls', 'summer-cicada-proxy', 'summer-crickets']);
  const receipt = read('tools/audio-host-verification.json');
  const verified = new Set(JSON.stringify(receipt).match(/[0-9a-f]{64}/g));
  for (const a of scoped) {
    assert(a.approved_eras.includes('1904')); assert.equal(a.license, 'CC0-1.0');
    assert(verified.has(a.delivery.sha256), `${a.id}: no new upload is needed, its delivery is already hosted`);
    for (const p of a.town_placements) {
      assert.equal(townHabitatPlacement(a, env({ season: p.season, date: p.from_month_day ? `1904-${p.from_month_day}` : DATES[p.season] }), '1904')?.id, p.id);
      for (const id of p.source_ids) assert(fs.existsSync(path.join(root, 'data/sources', id + '.json')), id);
      for (const r of p.basis_records ?? []) assert(fs.existsSync(path.join(root, r)), r);
    }
  }
  const intake = read('assets/audio/intake.json');
  for (const a of scoped) assert.deepEqual(intake.assets.find(x => x.id === a.id).town_placements, a.town_placements, 'catalogue mirrors intake');
  assert(read('data/liberties.json').liberties?.some?.(l => l.id === 'L-1904-nature-sounds-3585')
    ?? JSON.stringify(read('data/liberties.json')).includes('L-1904-nature-sounds-3585'));
});

test('summer: robins by day from a real elm behind; cicadas only after noon; crickets at dusk', () => {
  const day = at(env());
  assert.deepEqual(ids(day), ['robin-calls', 'summer-cicada-proxy']);
  const robin = day.find(c => c.asset.id === 'robin-calls');
  assert.equal(robin.tree, 'b', 'the 20 m tree is too close for an unseen bird');
  assert.deepEqual(robin.anchor, { x: 0, y: 0.5 + TOWN_HABITAT.crownHeight, z: 50 });
  assert(robin.gain > 0.05 && robin.gain <= 0.2, `robin is clearly audible: ${robin.gain}`);
  assert.deepEqual(ids(at(env({ period: 'morning' }))), ['robin-calls'], 'no cicada before noon');
  assert.deepEqual(ids(at(env({ period: 'dawn' }))), ['robin-calls']);
  assert.deepEqual(ids(at(env({ period: 'dusk' }))), ['robin-calls', 'summer-cicada-proxy', 'summer-crickets']);
  assert.deepEqual(ids(at(env({ period: 'night' }))), ['summer-crickets'], 'the July 1 night has no katydid');
  assert.deepEqual(ids(at(env({ period: 'night', date: '1904-08-10' }))), ['late-summer-katydid', 'summer-crickets']);
});

test('other seasons: spring and fall robins only, winter silent', () => {
  assert.deepEqual(ids(at(env({ season: 'spring' }))), ['robin-calls']);
  assert.deepEqual(ids(at(env({ season: 'fall' }))), ['robin-calls']);
  assert.deepEqual(ids(at(env({ season: 'fall', period: 'dusk' }))), [], 'fall robins are sparse: dawn and day only');
  for (const period of ['dawn', 'day', 'dusk', 'night']) assert.deepEqual(at(env({ season: 'winter', period })), []);
  const spring = catalog.assets.find(a => a.id === 'robin-calls').town_placements;
  const gap = s => spring.find(p => p.season === s).gap_seconds[0];
  assert(gap('summer') < gap('spring') && gap('spring') < gap('fall'), 'most song in summer, least in fall');
});

test('habitat: the parkway trees, with no invented elsewhere', () => {
  assert.deepEqual(at(env({ trees: [] })), [], 'no parkway trees, no nature');
  assert.deepEqual(at(env({ trees: [ahead()] })).filter(c => c.mode === 'distant-bird'), [], 'a phrase never begins in view');
  assert.deepEqual(ids(at(env({ trees: [behind(80)] }))), ['robin-calls'], '80 m from any elm: a robin, no insect bed');
  assert.deepEqual(at(env({ trees: [behind(130)] })), [], 'beyond 110 m nothing');
  assert.deepEqual(at(env({ trees: [{ ...behind(), kind: 'young' }] })), [], 'a sapling is no song post');
  assert.deepEqual(ids(at(env({ y: 40 }))), ['robin-calls'], 'flying at 40 m: a robin below, no insect bed');
  assert.deepEqual(at(env({ y: 130 })), [], 'flying high leaves both the crowns and the grass');
  assert.deepEqual(at(env({ date: '1904-07-01', season: 'winter' })), [], 'a date and season that disagree stay quiet');
  assert.deepEqual(at(env({ date: '1835-07-01' })), [], 'the 1835 date is not 1904');
  assert.deepEqual(habitatCandidates(catalog, env(), '1835'), [], '1835 never borrows the 1904 street');
  assert.deepEqual(habitatCandidates(catalog, env(), '1812'), []);
  assert.equal(townSeasonOfDate('1904-08-10'), 'summer');
});

test('one phrase at a time, anchored in its crown, kept when the visitor turns toward the tree', async () => {
  const sources = [], panners = [];
  const param = () => ({ value: 0, setTargetAtTime(v) { this.value = v; }, setValueAtTime(v) { this.value = v; }, linearRampToValueAtTime(v) { this.value = v; } });
  const node = () => ({ connect(n) { this.target = n; }, disconnect() {} });
  const ctx = { currentTime: 0,
    createGain() { return { ...node(), gain: param() }; },
    createPanner() { const n = { ...node(), positionX: param(), positionY: param(), positionZ: param() }; panners.push(n); return n; },
    createBufferSource() { const n = { ...node(), start() { this.started = true; }, stop(t) { this.stopAt = t; } }; sources.push(n); return n; } };
  const e = env({ period: 'morning' }); let time = 0;
  const engine = createHabitatAudio({ ctx, output: {}, catalog: () => catalog, environment: () => e, now: () => time, random: () => 0,
    fetcher: async () => ({ ok: true, arrayBuffer: async () => new ArrayBuffer(8) }),
    decodeAudio: async () => ({ duration: 24, sampleRate: 48000, length: 24 * 48000, numberOfChannels: 1 }) });
  const flush = async () => { for (let i = 0; i < 20; i++) await Promise.resolve(); };
  engine.sync({ enabled: true, year: '1904' }); await flush();
  time = 13000; engine.sync({ enabled: true, year: '1904' }); await flush();
  assert.deepEqual(engine.state.voices, ['robin-calls'], 'a robin within its 6-12 s opening gap');
  assert.deepEqual(engine.state.anchor, { x: 0, y: 9.5, z: 50 });
  assert.equal(panners.at(-1).positionZ.value, 50);
  e.camera.quaternion = { x: 0, y: 1, z: 0, w: 0 }; // turned round to face the tree
  time = 14000; engine.sync({ enabled: true, year: '1904' }); await flush();
  assert.deepEqual(engine.state.voices, ['robin-calls'], 'the crown hides it; the phrase goes on');
  e.camera.position = { x: 0, y: 1.7, z: 200 }; // walked well past it
  time = 15000; engine.sync({ enabled: true, year: '1904' }); await flush();
  assert(sources.at(-1).stopAt != null, 'out of range, the phrase fades');
  engine.dispose();
});

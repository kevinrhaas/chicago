// The page asks only for the prebuilt layers publish wrote (js/prebuilt-index.js):
// a scene with no prebuild makes no request for one, so /1904/ and /1812/ boot with no
// 404 for data/prebuilt/<year>/ground.json, base.json, streets.json or yards.json (dev's mobile smoke was red on it).
//
//   node tools/test_prebuilt_index.mjs
import assert from 'node:assert/strict';
import { prebuiltAbsent, prebuiltListing, resetPrebuiltListing } from '../renderers/web/js/prebuilt-index.js';
import { listing } from './prebuild_layers.mjs';

const dataBase = 'https://example.test/4d/data/';
const requests = [];
let served = { format: 1, build: 'b123', layers: { 1835: ['frontage', 'ground', 'base'] } };
globalThis.fetch = async (url) => {
  requests.push(String(url));
  if (String(url).endsWith('prebuilt/index.json') && served) return { ok: true, status: 200, json: async () => served };
  return { ok: false, status: 404, json: async () => ({}) };
};

// 1904 and 1812: nothing is asked for beyond the one list, and the reason says so.
for (const year of ['1904', '1812']) {
  for (const layer of ['ground', 'base', 'frontage']) {
    const why = await prebuiltAbsent({ dataBase, year, build: 'b123', layer });
    assert.equal(why, `publish prebuilt no ${layer} for ${year}`);
  }
}
assert.deepEqual(requests, [`${dataBase}prebuilt/index.json`], 'one list fetched, once, and no 404 for a year with no prebuild');

// 1835 with this build: listed, so the page may go on to fetch it.
assert.equal(await prebuiltAbsent({ dataBase, year: '1835', build: 'b123', layer: 'ground' }), null);
assert.equal(await prebuiltAbsent({ dataBase, year: '1835', build: 'other', layer: 'ground' }),
  'prebuilt by build b123, this page is build other');

// No list at all (an older mirror): nothing is asked for, honestly.
resetPrebuiltListing(); served = null; requests.length = 0;
const why = await prebuiltAbsent({ dataBase, year: '1835', build: 'b123', layer: 'ground' });
assert.equal(why, 'no list of what publish prebuilt (404)');
assert.deepEqual(requests, [`${dataBase}prebuilt/index.json`]);
assert.equal((await prebuiltListing(dataBase)).why, why);

// What publish writes: every year and layer the build produced, once each.
assert.deepEqual(listing([
  { year: '1835', layer: 'ground' }, { year: '1835', layer: 'base' }, { year: '1835', layer: 'frontage' },
  { year: '1835', layer: 'ground' },
], 'b9'), { format: 1, build: 'b9', layers: { 1835: ['ground', 'base', 'frontage'] } });
assert.deepEqual(listing([], null), { format: 1, build: null, layers: {} });

// The streets (T-2710) ask the same list: /1904/ draws streets and publish prebuilds none.
// streets.js imports 'three' bare, as the page's import map resolves it, and yards.js's
// terrain.js 'three/addons/' too; map both to the vendored copy.
const { register } = await import('node:module');
const THREE_URL = new URL('../renderers/web/vendor/three-0.185.1/three.module.js', import.meta.url).href;
const ADDONS_URL = new URL('../renderers/web/vendor/three-0.185.1/addons/', import.meta.url).href;
register('data:text/javascript,' + encodeURIComponent(
  `export async function resolve(spec, ctx, next) { if (spec === 'three') return { url: ${JSON.stringify(THREE_URL)}, shortCircuit: true }; `
  + `if (spec.startsWith('three/addons/')) return { url: ${JSON.stringify(ADDONS_URL)} + spec.slice(13), shortCircuit: true }; return next(spec, ctx); }`));
const { fetchPrebuiltStreets } = await import('../renderers/web/js/streets.js');
resetPrebuiltListing(); served = { format: 1, build: 'b123', layers: { 1835: ['streets'] } }; requests.length = 0;
const streets1904 = await fetchPrebuiltStreets({ dataBase, year: '1904', build: 'b123' });
assert.equal(streets1904.why, 'publish prebuilt no streets for 1904, so the page lays its own streets');
assert.deepEqual(requests, [`${dataBase}prebuilt/index.json`], 'the streets ask for no 1904 file');
await fetchPrebuiltStreets({ dataBase, year: '1835', build: 'b123' });
assert.ok(requests.includes(`${dataBase}prebuilt/1835/streets.json`), 'a listed year still fetches its streets');

// And the yards (T-2711): /1904/ draws enclosures and publish prebuilds no yards for it.
const { fetchPrebuiltYards } = await import('../renderers/web/js/yards.js');
resetPrebuiltListing(); served = { format: 1, build: 'b123', layers: { 1835: ['yards'] } }; requests.length = 0;
const yards1904 = await fetchPrebuiltYards({ dataBase, year: '1904', build: 'b123' });
assert.equal(yards1904.why, 'publish prebuilt no yards for 1904, so the page lays its own yards');
assert.deepEqual(requests, [`${dataBase}prebuilt/index.json`], 'the yards ask for no 1904 file');
await fetchPrebuiltYards({ dataBase, year: '1835', build: 'b123' });
assert.ok(requests.includes(`${dataBase}prebuilt/1835/yards.json`), 'a listed year still fetches its yards');

console.log('PREBUILT INDEX PASS — only listed layers are fetched; a year with no prebuild makes no 404 request');

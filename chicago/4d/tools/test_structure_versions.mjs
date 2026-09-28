#!/usr/bin/env node
/**
 * The address-bar half of structure versions (T-1727), without a browser.
 *
 *   node tools/test_structure_versions.mjs [--self-test]   (the flag is accepted; every run is one)
 *
 * `renderers/web/js/structure-versions.js` decides what `?structure=<id>&version=<label>`
 * swaps. The ticket's rules for it are all decidable without WebGL, so they are held
 * here, on the committed versions index, in well under a second:
 *
 *   - no request, no fetch: a plain boot never reads the versions index (the boot
 *     payload must not grow);
 *   - a committed label swaps exactly that entry, and the row carries its sidecar path;
 *   - every miss — no ?structure=, an unknown id, an unknown label, a malformed label,
 *     an unreadable index — falls back to the default WITH a notice, never silently;
 *   - version=default is the canonical record, named as such in the HUD chip.
 *
 * The browser half (the swap in a booted scene, nothing else moving, both viewports) is
 * the release smoke's, in tools/smoke_renderer.mjs part 3.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const mod = await import(pathToFileURL(path.join(ROOT, 'renderers/web/js/structure-versions.js')));
const { readVersionRequest, resolveStructureVersion, versionBadge } = mod;

const failures = [];
const check = (name, cond, detail = '') => {
  console.log(`   self-test | ${cond ? 'ok  ' : 'FAIL'} ${name}${cond || !detail ? '' : ` — ${detail}`}`);
  if (!cond) failures.push(name);
};

const dataBase = pathToFileURL(path.join(ROOT, 'data') + '/');
const sceneIndex = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars/1835/index.json'), 'utf8'));
const entries = sceneIndex.structures.map((r) => (typeof r === 'string' ? { id: r } : r));
let fetched = [];
const getJSON = async (url) => {
  fetched.push(String(url));
  return JSON.parse(fs.readFileSync(fileURLToPath(url), 'utf8'));
};
const resolve = async (search, ctx = {}) => {
  fetched = [];
  return resolveStructureVersion(readVersionRequest(search), {
    year: '1835', dataBase, entries, getJSON, ...ctx,
  });
};

// the committed index is what the smoke's fixture lives in
const vindex = JSON.parse(fs.readFileSync(path.join(ROOT, 'data/sidecars/1835/versions/index.json'), 'utf8'));
const fixture = vindex.structures?.bates_auction_room?.find((r) => r.label === 'fixture');
check('the committed versions index lists the smoke fixture, marked as a test fixture',
  fixture?.test_fixture === true && /versions\/bates_auction_room\/fixture\.json$/.test(fixture.sidecar),
  JSON.stringify(fixture));

let s = await resolve('?year=1835&anchor=fort');
check('no ?version= asks for nothing and fetches nothing', s.requested === null && s.active === null
  && fetched.length === 0 && versionBadge(s) === null, JSON.stringify({ s, fetched }));
s = await resolve('?structure=bates_auction_room');
check('?structure= alone asks for nothing yet (reserved for opening a structure)',
  s.requested === null && fetched.length === 0);

s = await resolve('?structure=bates_auction_room&version=fixture');
check('a committed label swaps exactly that structure, and names its sidecar',
  s.active?.id === 'bates_auction_room' && s.active?.label === 'fixture'
  && s.active?.sidecar === fixture?.sidecar && s.notice === null, JSON.stringify(s));
check('…fetching only the versions index, once', fetched.length === 1
  && /sidecars\/1835\/versions\/index\.json$/.test(fetched[0]), fetched.join(', '));
let b = versionBadge(s);
check('…and the HUD chip names the version and says it is a test fixture',
  b?.tone === 'active' && b.text === 'version fixture' && /test fixture/.test(b.title)
  && /Auction Room/.test(b.title), JSON.stringify(b));

s = await resolve('?structure=bates_auction_room&version=default');
b = versionBadge(s);
check('version=default shows the canonical record and the chip says so, with no fetch',
  s.active === null && s.explicitDefault && s.notice === null && fetched.length === 0
  && b?.tone === 'default' && b.text === 'version default', JSON.stringify({ s, b }));

const misses = [
  ['?version=fixture', /needs \?structure=/],
  ['?structure=no_such_house&version=v1', /No structure “no_such_house” in the 1835 scene/],
  ['?structure=Bad-Id!&version=v1', /No structure/],
  ['?structure=bates_auction_room&version=zzz', /No version “zzz” of .* — showing the default\. Versions: fixture\./],
  ['?structure=bates_auction_room&version=Hall_Plan', /is not a version label/],
  ['?structure=sauganash_hotel&version=v2', /has no committed versions — showing the default/],
];
for (const [search, re] of misses) {
  s = await resolve(search);
  b = versionBadge(s);
  check(`${search} falls back to the default and SAYS so`, s.active === null && re.test(s.notice ?? '')
    && b?.tone === 'notice' && b.text === 'default shown' && b.title === s.notice,
  JSON.stringify({ notice: s.notice, b }));
}
s = await resolve('?structure=bates_auction_room&version=fixture', {
  getJSON: async () => { throw new Error('404 Not Found'); },
});
check('an unreadable versions index falls back to the default and says why',
  s.active === null && /could not be read \(404 Not Found\)/.test(s.notice ?? ''), s.notice);

console.log(`   self-test | ${failures.length} failure(s)`);
process.exit(failures.length ? 1 : 0);

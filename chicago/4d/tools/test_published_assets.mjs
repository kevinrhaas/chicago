import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import http from 'node:http';
import vm from 'node:vm';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { validateAssetAliases, assetAliasIdInput, fetchPublishedAssetBytes, publishedAssetAddress,
  verifiedPackAliases, publishedAssetCatalogue, completeTextureBuffer } from '../renderers/web/js/published-assets.js';
import { writeYearPacks, checkYearPacks, publicationAliases, glbOwners, yearFiles } from './write_year_packs.mjs';

if (process.argv.slice(2).some((arg) => arg !== '--check')) throw new Error('Only --check is supported');
const sha = (bytes) => createHash('sha256').update(bytes).digest('hex');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'published-assets-'));
const site = path.join(temporary, 'site/4d'), dev = path.join(site, 'dev');
let checks = 0;
const check = (condition, message) => { assert(condition, message); checks++; };
const put = (file, bytes) => { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, bytes); };
const glb = (json) => {
  let j = Buffer.from(JSON.stringify({ asset: { version: '2.0' }, ...json }));
  j = Buffer.concat([j, Buffer.alloc((4 - j.length % 4) % 4, 32)]);
  const header = Buffer.alloc(20); header.writeUInt32LE(0x46546c67); header.writeUInt32LE(2, 4);
  header.writeUInt32LE(20 + j.length, 8); header.writeUInt32LE(j.length, 12); header.writeUInt32LE(0x4e4f534a, 16);
  return Buffer.concat([header, j]);
};
const payloads = {
  'data/gltf/house.glb': glb({}),
  'data/gltf/sheets/0123456789abcdef.ktx2': Buffer.from('fixture sheet; byte integrity only, no texture decode claim'),
  'data/prebuilt/1835/ground.bin.gz': Buffer.from('fixture prebuilt; no geometry claim'),
};
const aliases = Object.fromEntries(Object.entries(payloads).map(([rel, bytes]) => [rel,
  { source: `/4d/${rel}`, sha256: sha(bytes), bytes: bytes.length }]));
const catalogue = { schema: 1, scope: '/4d/dev/', productionScope: '/4d/', id: sha(assetAliasIdInput(aliases)), aliases };
const filename = `asset-aliases.${catalogue.id}.json`;
const meta = `<meta name="c4d-asset-aliases" content="/4d/dev/${filename}" data-sha256="${catalogue.id}">`;
const root = 'https://fixture.test/4d/dev/';
let server;
try {
  check(validateAssetAliases(catalogue, root).aliases['data/gltf/house.glb'].bytes === payloads['data/gltf/house.glb'].length, 'exact scoped catalogue');
  for (const mutate of [
    (c) => { c.scope = '/4d/'; },
    (c) => { c.aliases['../data/gltf/bad.glb'] = c.aliases['data/gltf/house.glb']; },
    (c) => { c.aliases['data/gltf/house.glb'].source = 'https://other.test/4d/data/gltf/house.glb'; },
    (c) => { c.aliases['data/gltf/house.glb'].source += '?other=1'; },
    (c) => { c.aliases['data/gltf/house.glb'].sha256 = '0'; },
    (c) => { c.aliases['data/gltf/house.glb'].bytes = -1; },
  ]) {
    const broken = structuredClone(catalogue); mutate(broken);
    assert.throws(() => validateAssetAliases(broken, root)); checks++;
  }
  const textureJSON = { buffers: [{ byteLength: 60 }, { uri: 'sheets/0123456789abcdef.ktx2', byteLength: 32 }],
    bufferViews: [{ buffer: 0, byteLength: 60 }, { buffer: 1, byteOffset: 0, byteLength: 32 }],
    images: [{ bufferView: 1, mimeType: 'image/ktx2' }], accessors: [{ bufferView: 0 }] };
  check(completeTextureBuffer(textureJSON, 1), 'actual native complete KTX2 external buffer image layout accepted');
  for (const mutate of [
    c => { c.accessors.push({ bufferView: 1 }); },
    c => { c.accessors.push({ sparse: { indices: { bufferView: 1 } } }); },
    c => { c.bufferViews[0].extensions = { EXT_meshopt_compression: { buffer: 1 } }; },
    c => { c.bufferViews[1].byteOffset = 1; },
    c => { c.bufferViews[1].byteLength = 31; },
    c => { c.images[0].mimeType = 'image/png'; },
    c => { c.bufferViews[1].target = 34962; },
    c => { c.bufferViews[1].byteStride = 4; },
  ]) { const broken = structuredClone(textureJSON); mutate(broken); check(!completeTextureBuffer(broken, 1), 'geometry/partial/nonKTX texture buffer rejected'); }
  let missingRequests = 0;
  const identity = await publishedAssetAddress(`${root}data/gltf/house.glb`, {
    document: null, fetchImpl: async () => { missingRequests++; throw new Error('must not ask for a catalogue'); },
  });
  check(identity.source.href === identity.logical.href && missingRequests === 0, 'non-DOM/missing pointer stays identity without a request');
  const retryCatalogue = structuredClone(catalogue);
  retryCatalogue.aliases['data/gltf/retry.glb'] = { ...retryCatalogue.aliases['data/gltf/house.glb'], source: '/4d/data/gltf/retry.glb' };
  retryCatalogue.id = sha(assetAliasIdInput(retryCatalogue.aliases));
  const retryDocument = { baseURI: 'https://retry.test/4d/dev/walk/', querySelector: () => ({ getAttribute: (name) =>
    name === 'content' ? `/4d/dev/asset-aliases.${retryCatalogue.id}.json` : retryCatalogue.id }) };
  let attempts = 0;
  const retryEnvironment = { document: retryDocument, fetchImpl: async () => ++attempts === 1
    ? new Response('temporary', { status: 500 }) : new Response(JSON.stringify(retryCatalogue)) };
  await assert.rejects(publishedAssetCatalogue(retryEnvironment)); checks++;
  check((await publishedAssetCatalogue(retryEnvironment)).catalogue.id === retryCatalogue.id && attempts === 2,
    'failed catalogue request evicted and real retry recovers');
  const native = fs.readFileSync(new URL('../renderers/web/js/scene-loader.js', import.meta.url), 'utf8');
  const functions = native.slice(native.indexOf('export function hasInspectionLod'), native.indexOf('/** A serial'))
    .replaceAll('export function ', 'function ');
  const scope = vm.createContext({ URL });
  vm.runInContext(functions, scope);
  const record = { id: 'glessner_house', sidecar: { asset: 'gltf/glessner_house__as_built_1887.glb', asset_lods: { light: 'gltf/light.glb' } } };
  check(scope.hasInspectionLod(record) && scope.detailAssetPath(record, 'light') === 'gltf/light.glb', 'unchanged default Glessner Light recognition');
  check(scope.detailAssetPath(record, 'full') === record.sidecar.asset && scope.detailAssetUrl(record, 'light', { assetBase: new URL(root + 'data/') }).href === root + 'data/gltf/light.glb', 'logical LOD identity and URI');
  for (const [rel, bytes] of Object.entries(payloads)) put(path.join(site, rel), bytes);
  put(path.join(dev, filename), JSON.stringify(catalogue));
  put(path.join(dev, 'walk/index.html'), `<!doctype html><base href="/4d/dev/walk/">${meta}`);
  put(path.join(dev, 'walk/js/fixture.js'), '/* fixture entry */');
  put(path.join(dev, 'build.json'), '{}');
  for (const year of ['1812', '1835', '1904']) {
    put(path.join(dev, `${year}/index.html`), `${meta}<p>${year}</p>`);
    put(path.join(dev, `data/scenes/${year}.json`), '{}');
  }
  put(path.join(dev, 'data/sidecars/1904/house.json'), '{"asset":"gltf/house.glb"}');
  const summary = writeYearPacks(dev);
  check(Object.keys(summary).length === 3, 'all native year doors rebuilt');
  check(checkYearPacks(dev).length === 0, 'native pack check validates canonical sources');
  const pack = JSON.parse(fs.readFileSync(path.join(dev, 'packs/1904.json')));
  check(pack.files.some(([rel]) => rel === 'data/gltf/house.glb') && !fs.existsSync(path.join(dev, 'data/gltf/house.glb')), 'removed GLB retains logical pack membership');
  check(pack.files.some(([rel]) => rel === filename), 'offline pack retains immutable catalogue');
  await verifiedPackAliases(pack, root); checks++;
  const wrong = structuredClone(pack); wrong.files.find(([rel]) => rel === 'data/gltf/house.glb')[1] = '0000000000000000';
  await assert.rejects(verifiedPackAliases(wrong, root)); checks++;
  const wrongID = structuredClone(pack); wrongID.assetAliases.id = '0'.repeat(64);
  await assert.rejects(verifiedPackAliases(wrongID, root)); checks++;
  const bytes = payloads['data/gltf/house.glb']; put(path.join(site, 'data/gltf/house.glb'), Buffer.from('changed'));
  assert.throws(() => checkYearPacks(dev), /Publication source changed/); checks++;
  put(path.join(site, 'data/gltf/house.glb'), bytes);
  const absent = path.join(site, 'data/gltf/house.glb'); fs.unlinkSync(absent);
  assert.throws(() => publicationAliases(dev)); checks++;
  put(absent, bytes);
  const owners = glbOwners(['data/sidecars/1904/house.json', 'data/gltf/house.glb'], () => '{"asset":"gltf/house.glb"}');
  check(!yearFiles(['data/gltf/house.glb'], '1835', owners).length && yearFiles(['data/gltf/house.glb'], '1904', owners).length === 1, 'year ownership preserved');
  let mode = 'full'; const requests = [];
  server = http.createServer((request, response) => {
    const u = new URL(request.url, 'http://localhost'); requests.push(u.pathname);
    if (u.pathname === `/4d/dev/${filename}`) { response.setHeader('Content-Type', 'application/json'); response.end(JSON.stringify(catalogue)); return; }
    const rel = u.pathname.slice('/4d/'.length), data = payloads[rel];
    if (!data) { response.writeHead(404); response.end(); return; }
    if (mode === 'partial') { response.writeHead(206, { 'Content-Range': `bytes 0-0/${data.length}` }); response.end(data.subarray(0, 1)); return; }
    response.end(mode === 'corrupt' ? Buffer.alloc(data.length) : data);
  });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const origin = `http://127.0.0.1:${server.address().port}`;
  const document = { baseURI: `${origin}/4d/dev/walk/`, querySelector: () => ({ getAttribute: (name) => name === 'content' ? `/4d/dev/${filename}` : catalogue.id }) };
  const environment = { document };
  const logical = `${origin}/4d/dev/data/gltf/house.glb`;
  const address = await publishedAssetAddress(logical, environment);
  check(address.source.pathname === '/4d/data/gltf/house.glb' && address.source.searchParams.get('c4d-asset-alias') === aliases['data/gltf/house.glb'].sha256
    && address.source.searchParams.get('c4d-pack') === aliases['data/gltf/house.glb'].sha256, 'HTTP source uses exact full-hash offline allowlist key');
  const got = await fetchPublishedAssetBytes(logical, {}, environment);
  check(Buffer.from(got).equals(bytes), 'actual HTTP source returns exact original buffer');
  check(!requests.includes('/4d/dev/data/gltf/house.glb'), 'removed logical file never requested from network');
  mode = 'corrupt'; await assert.rejects(fetchPublishedAssetBytes(logical, {}, environment), /differs/); checks++;
  mode = 'partial'; await assert.rejects(fetchPublishedAssetBytes(logical, {}, environment), /complete response/); checks++;
  mode = 'full';
  const unchanged = await publishedAssetAddress(`${origin}/4d/dev/data/gltf/unlisted.glb`, environment);
  check(!unchanged.alias && unchanged.source.href === unchanged.logical.href, 'unknown asset keeps its logical network URL');
  const capability = JSON.parse(execFileSync(process.execPath, [new URL('./write_year_packs.mjs', import.meta.url).pathname, '--asset-alias-capability']));
  check(capability.logicalPackSources && capability.ktx2Aliases && capability.logicalGltfResources && capability.textureBufferAliases, 'actual native capability handshake');
  console.log(JSON.stringify({ status: 'PASS', checks, realHTTP: true, browserOffline: 'separate required fixture', threeYears: Object.keys(summary), requestCount: requests.length }));
} finally {
  if (server) await new Promise((resolve) => server.close(resolve));
  fs.rmSync(temporary, { recursive: true, force: true });
}

import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { createAudioReplay } from './audio_smoke_replay.mjs';
import { publishAudio } from './audio_hosting.mjs';

const root = fs.mkdtempSync(path.join(os.tmpdir(), 'audio-smoke-replay-'));
const site = path.join(root, 'site');
const put = (rel, value) => {
  const file = path.join(root, rel); fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, typeof value === 'string' ? value : JSON.stringify(value));
};
try {
  const body = Buffer.from('verified river recording');
  const delivery = { sha256: createHash('sha256').update(body).digest('hex'), bytes: body.length };
  const base = 'https://test.r2.dev/', key = `media/${delivery.sha256}.mp3`, url = base + key;
  const policy = { version: 1, scope: 'development', public_base: base, origin: 'https://chicago.polecat.live' };
  const receipt = { complete: true, errors: [], public_base: base, origin: policy.origin,
    verified: [{ key, bytes: body.length }] };
  const localCatalog = { assets: [{ id: 'river', kind: 'environment', url: 'river.mp3', delivery }] };
  const catalog = { assets: [{ ...localCatalog.assets[0], url }],
    hosting: { scope: 'development', public_base: base, offline_audio: false } };
  put('tools/audio-hosting.json', policy); put('tools/audio-host-verification.json', receipt);
  put('site/walk/audio/catalog.json', catalog);
  let fetches = 0;
  const fetcher = async (asked, options) => {
    fetches++; assert.equal(asked, url); assert.equal(options.redirect, 'error');
    assert.equal(options.credentials, 'omit'); assert.equal(options.headers.Origin, policy.origin);
    return new Response(body);
  };
  // Deliberately no renderers/ tree: this is the bake's sparse artifact layout.
  const sparse = createAudioReplay({ root, site, fetcher });
  assert.equal(fetches, 0, 'constructing any smoke stage fetches no audio');
  assert.equal(sparse.size, 1); assert(sparse.has(url));
  assert.equal(sparse.has(base + 'unknown.mp3'), false);
  await assert.rejects(sparse.get('https://unlisted.example/file.mp3'), /unlisted/);
  assert.equal(fetches, 0);
  const [first, shared] = await Promise.all([sparse.get(url), sparse.get(url)]);
  assert.equal(fetches, 1, 'one lazy fetch shared by concurrent media requests');
  assert.equal(first, shared); assert.deepEqual(first.body, body); assert.equal(first.contentType, 'audio/mpeg');
  for (const [bad, message] of [
    [Buffer.from('x'.repeat(body.length)), /differ from verified/],
    [body.subarray(0, -1), /differ from verified/],
    [Buffer.concat([body, Buffer.from('extra')]), /exceeds verified size/],
  ]) {
    const replay = createAudioReplay({ root, site, fetcher: async () => new Response(bad) });
    await assert.rejects(replay.get(url), message);
  }
  const unavailable = createAudioReplay({ root, site, fetcher: async () => new Response(null, { status: 404 }) });
  await assert.rejects(unavailable.get(url), /HTTP 404/);
  for (const escaped of ['https://other.example/' + key, url + '?extra=1', base + 'media/../' + key]) {
    put('site/walk/audio/catalog.json', { ...catalog, assets: [{ ...catalog.assets[0], url: escaped }] });
    assert.throws(() => createAudioReplay({ root, site, fetcher }), /not verified/);
  }
  put('site/walk/audio/catalog.json', catalog);
  put('tools/audio-host-verification.json', { ...receipt, verified: [] });
  assert.throws(() => createAudioReplay({ root, site, fetcher }), /not verified/);
  put('tools/audio-host-verification.json', receipt);
  // A full source checkout still validates and replays local bytes, never fetching.
  put('renderers/web/audio/catalog.json', localCatalog); put('renderers/web/audio/river.mp3', body.toString());
  publishAudio(site, { root });
  const local = createAudioReplay({ root, site, fetcher: () => { throw Error('Local replay must not fetch'); } });
  assert.match(local.mode, /local/); assert.deepEqual((await local.get(url)).body, body);
  put('renderers/web/audio/river.mp3', 'changed');
  assert.throws(() => createAudioReplay({ root, site, fetcher }), /delivery changed/);
  console.log('AUDIO SMOKE REPLAY PASS: sparse artifact boot without source media; lazy immutable receipt-bound fetch; URL, size, hash and HTTP refusal; shared requests; full checkout uses verified local bytes');
} finally { fs.rmSync(root, { recursive: true, force: true }); }

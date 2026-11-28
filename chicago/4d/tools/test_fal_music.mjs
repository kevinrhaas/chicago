#!/usr/bin/env node
// T-3710: trial music through fal's queue. Offline: a fake fal answers. The plan prices every
// clip from the model's own price block; the key goes only to the queue origin and never into
// output; queue URLs off fal's origin are refused; and a submit whose answer is unclear is never
// sent again.
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { loadTrials, planWork, priceFor, secondsFor, inputFor, runsOn, readKey, onQueueOrigin, makeClip, QUEUE } from './fal_music.mjs';

const trials = loadTrials();
const KEY = 'test-key-000:never-printed';

// ---- the plan ---------------------------------------------------------------------------
{
  const work = planWork(trials);
  const expected = trials.cues.reduce((n, c) => n + trials.trial_models.filter(m => runsOn(m, trials.models[m], c)).length, 0);
  assert.equal(work.length, expected, 'every cue on every trial model it can run on');
  const mm = trials.models.minimax;
  assert.ok(work.filter(x => x.model === 'minimax').every(x => x.input.lyrics_prompt?.length >= 10), 'MiniMax always gets words');
  assert.ok(!runsOn('minimax', mm, { prompt: 'p' }), 'a singing model skips a cue with no words');
  assert.ok(!runsOn('lyria', trials.models.lyria, { prompt: 'p', lyrics: 'x', models: ['minimax'] }), 'a cue keeps to the models it names');
  assert.throws(() => inputFor(mm, { id: 'long', prompt: 'x'.repeat(301), lyrics: 'words here' }), /takes 300/);
  for (const c of trials.cues) if (c.lyrics) assert.ok(c.lyrics_source, `${c.id} says where its words come from`);
  for (const w of work) assert.ok(w.usd >= 0 && w.usd < 1, `${w.cue}/${w.model} priced`);
  const el = trials.models.elevenlabs, lyria = trials.models.lyria, cassette = trials.models.cassette;
  assert.equal(priceFor(el, 45), 0.6, 'ElevenLabs bills a started minute');
  assert.equal(priceFor(el, 61), 1.2);
  assert.equal(priceFor(lyria, secondsFor(lyria, { seconds: 90 })), 0.1, 'Lyria makes 30 s whatever is asked');
  assert.ok(Math.abs(priceFor(cassette, 45) - 0.015) < 1e-9, 'Cassette bills by the second');
  assert.equal(secondsFor(cassette, { seconds: 2 }), 10, 'a duration is clamped into the model range');
  assert.deepEqual(inputFor(el, { prompt: 'p', seconds: 45 }), { prompt: 'p', force_instrumental: true, music_length_ms: 45000 });
  assert.equal(inputFor(lyria, { prompt: 'p', seconds: 45 }).music_length_ms, undefined, 'no duration sent to a fixed-length model');
  const planned = { id: 'p', plan: { positive_global_styles: ['orchestral'], negative_global_styles: ['vocals'], sections: [{ section_name: 'Hook', duration_ms: 6000 }, { section_name: 'Bed', duration_ms: 54000 }] } };
  assert.equal(secondsFor(el, planned), 60, 'a plan lasts as long as its sections');
  assert.equal(priceFor(el, secondsFor(el, planned)), 0.6);
  const pin = inputFor(el, planned);
  assert.equal(pin.prompt, undefined, 'a plan stands instead of the prompt');
  assert.equal(pin.force_instrumental, undefined, 'force_instrumental only goes with a prompt');
  assert.deepEqual(pin.composition_plan.sections[0], { lines: [], positive_local_styles: [], negative_local_styles: [], section_name: 'Hook', duration_ms: 6000 }, 'a section with no words');
  assert.ok(!runsOn('lyria', lyria, planned), 'a planned cue skips a model that takes no plan');
  assert.equal(planWork(trials, { cue: trials.cues[0].id, model: 'lyria' }).length, 1);
  assert.throws(() => planWork(trials, { cue: trials.cues[0].id, model: 'minimax' }), /nothing to make/);
  assert.throws(() => planWork(trials, { model: 'nope' }), /no model/);
  // T-3811: a run names a set of cues, comma-separated; an unknown one is refused whole.
  const two = trials.cues.slice(0, 2).map(c => c.id);
  assert.deepEqual([...new Set(planWork(trials, { cue: two.join(',') }).map(w => w.cue))], two);
  assert.throws(() => planWork(trials, { cue: `${two[0]},nope` }), /no cue nope/);
  assert.throws(() => planWork(trials, { cue: 'nope' }), /no cue/);
}

// ---- the key ----------------------------------------------------------------------------
{
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'fal-'));
  const f = path.join(dir, 'env');
  fs.writeFileSync(f, `OTHER=1\nFAL_KEY='${KEY}'\n`);
  assert.equal(readKey({}, f), KEY, 'read from the env file the connect flow writes');
  assert.equal(readKey({ FAL_KEY: 'from-env' }, f), 'from-env', 'the environment wins');
  assert.equal(readKey({}, null), null);
  assert.equal(readKey({}, path.join(dir, 'missing')), null);
  fs.rmSync(dir, { recursive: true });
  assert.ok(onQueueOrigin(`${QUEUE}/fal-ai/lyria2/requests/x/status`));
  for (const u of ['https://evil.test/requests/x', 'http://queue.fal.run/x', 'https://queue.fal.run.evil.test/x', 'nonsense', undefined]) assert.ok(!onQueueOrigin(u), `refused ${u}`);
}

// ---- a clip through a fake queue ---------------------------------------------------------
const w = planWork(trials, { cue: trials.cues[0].id, model: 'elevenlabs' })[0];
function fakeFal({ submit = null, polls = 2, statusUrl = `${QUEUE}/fal-ai/elevenlabs/requests/r1/status`, error = null } = {}) {
  const calls = [];
  let n = 0;
  const fetcher = async (url, opts = {}) => {
    calls.push({ url, auth: opts.headers?.Authorization ?? null, method: opts.method || 'GET', body: opts.body ?? null });
    if (opts.method === 'POST') return submit ? submit() : Response.json({ request_id: 'r1', status_url: statusUrl, response_url: `${QUEUE}/fal-ai/elevenlabs/requests/r1` });
    if (url.endsWith('/status')) return Response.json(++n < polls ? { status: 'IN_PROGRESS' } : { status: 'COMPLETED', metrics: { inference_time: 3.1 }, ...(error ? { error, error_type: 'x' } : {}) });
    if (url.startsWith(QUEUE)) return Response.json({ audio: { url: 'https://v3.fal.media/files/a/out.mp3', content_type: 'audio/mpeg' }, seed: 7 });
    if (url === 'https://v3.fal.media/files/a/out.mp3') return new Response(new Uint8Array([1, 2, 3]));
    return new Response('', { status: 404 });
  };
  return { fetcher, calls };
}
const fast = { sleep: async () => {}, pollMs: 0 };
{
  const { fetcher, calls } = fakeFal();
  const c = await makeClip(KEY, w, { fetcher, ...fast });
  assert.equal(c.request_id, 'r1'); assert.equal(c.seed, 7); assert.equal(c.ext, 'mp3'); assert.equal(c.bytes.length, 3);
  assert.equal(calls.filter(x => x.method === 'POST').length, 1, 'one submit');
  assert.equal(calls[0].url, `${QUEUE}/fal-ai/elevenlabs/music`);
  assert.deepEqual(JSON.parse(calls[0].body), w.input, 'the model input as planned');
  for (const x of calls) {
    if (x.url.startsWith(`${QUEUE}/`)) assert.equal(x.auth, `Key ${KEY}`, 'the queue gets the key');
    else assert.equal(x.auth, null, `the key never goes to ${x.url}`);
    assert.ok(!x.url.includes(KEY), 'never in a URL');
  }
}
{
  const { fetcher, calls } = fakeFal({ statusUrl: 'https://evil.test/requests/r1/status' });
  await assert.rejects(makeClip(KEY, w, { fetcher, ...fast }), e => e.billed && e.request_id === 'r1', 'an off-origin status URL is refused');
  assert.ok(!calls.some(x => x.url.startsWith('https://evil.test')), 'and never fetched');
}
{
  const { fetcher, calls } = fakeFal({ submit: () => { throw Error('socket hang up'); } });
  await assert.rejects(makeClip(KEY, w, { fetcher, ...fast }), e => e.billed && /not resubmitting/.test(e.message));
  assert.equal(calls.filter(x => x.method === 'POST').length, 1, 'an unclear submit is not sent again');
}
{
  const { fetcher } = fakeFal({ submit: () => new Response('{"detail":"Exhausted balance"}', { status: 403 }) });
  await assert.rejects(makeClip(KEY, w, { fetcher, ...fast }), e => e.refused && /Exhausted balance/.test(e.message), 'a 403 says why');
}
{
  // fal can accept a job and then refuse its result when the balance runs out mid-run.
  const { fetcher: inner } = fakeFal();
  const fetcher = async (url, o) => url === `${QUEUE}/fal-ai/elevenlabs/requests/r1` ? new Response('{"detail":"User is locked. Reason: Exhausted balance."}', { status: 403 }) : inner(url, o);
  await assert.rejects(makeClip(KEY, w, { fetcher, ...fast }), e => e.refused && e.request_id === 'r1' && /Exhausted balance/.test(e.message), 'a refused result says why');
}
{
  const { fetcher } = fakeFal({ error: 'bad prompt' });
  await assert.rejects(makeClip(KEY, w, { fetcher, ...fast }), e => e.billed && /bad prompt/.test(e.message), 'a failed request reports its error');
}
{
  const { fetcher } = fakeFal({ polls: 1e9 });
  let t = 0; const clock = Date.now;
  Date.now = () => (t += 60_000);
  try { await assert.rejects(makeClip(KEY, w, { fetcher, ...fast, timeoutMs: 120_000 }), /still not complete/); } finally { Date.now = clock; }
}

console.log('FAL MUSIC PASS — every trial clip priced from its model\'s list price; the key goes only to fal\'s queue, never a URL or the output; off-origin queue URLs refused; an unclear submit is never resent');

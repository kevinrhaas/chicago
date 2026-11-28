#!/usr/bin/env node
/**
 * T-3710 — trial pieces of generated period music through fal's queue API.
 *
 *   node tools/fal_music.mjs --plan                       what a run would make, and its list price
 *   node tools/fal_music.mjs --make --out DIR             make every cue on every trial model into DIR
 *
 *   --cues PATH       the cue file (default data/music/fal_trials.json; the score is data/music/score.json)
 *   --cue ID[,ID…]    only these cues (the cue file's `cues`)
 *   --model NAME      only this model (a key of `models`: minimax, cassette, stable-audio, lyria, elevenlabs)
 *   --max-usd N       refuse a run whose list price is over N dollars (default 5)
 *   --env-file PATH   read FAL_KEY from this file when the environment has none
 *
 * Nothing here reaches the app: the clips land in DIR with a receipt.json (endpoint, prompt,
 * request id, seed, bytes, SHA-256) for the owner to listen to. A cue that sounds right goes
 * through the ordinary music intake (assets/audio/originals, LICENSES.md, prepare_audio.py)
 * like any other recording, with a liberty saying the music is generated.
 *
 * FAL_KEY comes from the environment (or --env-file) and is only ever sent to the fal queue
 * origin in an Authorization header. It is never printed, written or put in a URL. A submit
 * is a billable job, so a submit whose answer is unclear is NEVER sent again: the run stops
 * and prints the request id it has, if any.
 */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const QUEUE = 'https://queue.fal.run';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');

export const DEFAULT_CUES = 'data/music/fal_trials.json';
export function loadTrials(root = ROOT, file = DEFAULT_CUES) {
  const t = JSON.parse(fs.readFileSync(path.resolve(root, file), 'utf8'));
  if (t.version !== 1 || typeof t.models !== 'object' || !Array.isArray(t.cues) || !Array.isArray(t.trial_models)) throw Error('fal_trials.json: unknown shape');
  for (const name of t.trial_models) if (!t.models[name]) throw Error(`fal_trials.json: trial model ${name} is not in models`);
  const ids = new Set();
  for (const c of t.cues) {
    if (!c.id || ids.has(c.id)) throw Error(`fal_trials.json: cue id ${c.id} missing or repeated`);
    ids.add(c.id);
    if (c.plan) {
      if (!Array.isArray(c.plan.sections) || !c.plan.sections.length) throw Error(`cue ${c.id}: a plan needs sections`);
      for (const sec of c.plan.sections) if (!(sec.duration_ms >= 3000 && sec.duration_ms <= 120000)) throw Error(`cue ${c.id}: section ${sec.section_name} must be 3-120 s`);
    } else {
      if (typeof c.prompt !== 'string' || !c.prompt.trim()) throw Error(`fal_trials.json: cue ${c.id} has no prompt`);
      if (!(c.seconds > 0)) throw Error(`fal_trials.json: cue ${c.id} has no seconds`);
    }
  }
  return t;
}

/** The seconds a model will actually make for a cue (clamped to its range, or its fixed length). */
export function secondsFor(model, cue) {
  if (cue.plan) return cue.plan.sections.reduce((t, sec) => t + sec.duration_ms, 0) / 1000;
  if (model.fixed_seconds) return model.fixed_seconds;
  const [lo, hi] = model.duration_range || [1, Infinity];
  return Math.min(hi, Math.max(lo, cue.seconds));
}

/** fal's list price for one clip, from the price block read off the model's page. */
export function priceFor(model, seconds) {
  const { usd, per, rounded_up } = model.price;
  if (per === 'clip') return usd;
  if (per === '30s') return usd * Math.ceil(seconds / 30);
  if (per === 'minute') return usd * (rounded_up ? Math.ceil(seconds / 60) : seconds / 60);
  throw Error(`unknown price unit ${per}`);
}

export function inputFor(model, cue) {
  if (cue.plan) {
    if (!model.plans) throw Error(`cue ${cue.id}: ${model.endpoint} takes no composition plan`);
    // A plan stands instead of the prompt: the model reads its sections and styles, not words.
    const { force_instrumental, ...rest } = model.extra;
    return { composition_plan: { positive_global_styles: cue.plan.positive_global_styles || [], negative_global_styles: cue.plan.negative_global_styles || [], sections: cue.plan.sections.map(sec => ({ lines: [], positive_local_styles: [], negative_local_styles: [], ...sec })) }, respect_sections_durations: cue.plan.respect_durations ?? true, ...rest };
  }
  if (model.prompt_max && cue.prompt.length > model.prompt_max) throw Error(`cue ${cue.id}: prompt is ${cue.prompt.length} characters, ${model.endpoint} takes ${model.prompt_max}`);
  const input = { prompt: cue.prompt, ...model.extra };
  if (model.duration_param) input[model.duration_param] = secondsFor(model, cue) * (model.duration_scale || 1);
  if (model.lyrics_param) input[model.lyrics_param] = cue.lyrics;
  return input;
}

/** A cue runs on a model unless it names other models, or the model sings and the cue has no words. */
export function runsOn(name, model, cue) {
  if (Array.isArray(cue.models) && !cue.models.includes(name)) return false;
  if (model.lyrics_param && !cue.lyrics) return false;
  if (cue.plan && !model.plans) return false;
  return true;
}

export function planWork(trials, { cue = null, model = null } = {}) {
  const models = model ? [model] : trials.trial_models;
  for (const m of models) if (!trials.models[m]) throw Error(`no model ${m} in fal_trials.json`);
  // `cue` is one id or several, comma-separated (T-3811: a run makes a set of cues).
  const ids = cue ? String(cue).split(',').map(s => s.trim()).filter(Boolean) : null;
  for (const id of ids ?? []) if (!trials.cues.some(c => c.id === id)) throw Error(`no cue ${id} in fal_trials.json`);
  const cues = trials.cues.filter(c => !ids || ids.includes(c.id));
  if (!cues.length) throw Error(`no cue ${cue} in fal_trials.json`);
  const work = [];
  for (const c of cues) for (const name of models) {
    const m = trials.models[name];
    if (!runsOn(name, m, c)) continue;
    const seconds = secondsFor(m, c);
    work.push({ cue: c.id, era: c.era, lyrics_source: c.lyrics_source ?? null, model: name, endpoint: m.endpoint, seconds, usd: priceFor(m, seconds), input: inputFor(m, c), output: m.output });
  }
  if (!work.length) throw Error('nothing to make: no cue runs on that model');
  return work;
}

/** FAL_KEY from the environment, else from an env file's `FAL_KEY=` line. Never echoed. */
export function readKey(env = process.env, envFile = null) {
  if (env.FAL_KEY) return env.FAL_KEY;
  if (!envFile || !fs.existsSync(envFile)) return null;
  for (const line of fs.readFileSync(envFile, 'utf8').split(/\r?\n/)) {
    const m = /^\s*(?:export\s+)?FAL_KEY\s*=\s*(.*)\s*$/.exec(line);
    if (m) return m[1].replace(/^(['"])(.*)\1$/, '$2') || null;
  }
  return null;
}

/** A URL the queue hands back is followed (with the key) only if it is on the queue's own origin. */
export function onQueueOrigin(url) {
  try { return new URL(url).origin === QUEUE; } catch { return false; }
}

const wait = ms => new Promise(r => setTimeout(r, ms));

/**
 * One clip: submit, poll, fetch the result, download the audio. Throws with `billed: true` once a
 * submit may have been accepted, so the caller stops instead of submitting again.
 */
export async function makeClip(key, w, { fetcher = fetch, sleep = wait, pollMs = 2000, timeoutMs = 10 * 60_000 } = {}) {
  const auth = { Authorization: `Key ${key}` };
  let submit;
  try {
    const r = await fetcher(`${QUEUE}/${w.endpoint}`, { method: 'POST', headers: { ...auth, 'Content-Type': 'application/json' }, body: JSON.stringify(w.input) });
    const text = await r.text();
    if (r.status === 403) throw Object.assign(Error(`fal refused the submit (403): ${text.slice(0, 300)}`), { billed: false, refused: true });
    if (!r.ok) throw Object.assign(Error(`fal submit HTTP ${r.status}: ${text.slice(0, 300)}`), { billed: r.status >= 500 });
    submit = JSON.parse(text);
  } catch (e) {
    if (e.billed !== undefined) throw e;
    throw Object.assign(Error(`fal submit answer unclear (${e.message}); not resubmitting`), { billed: true });
  }
  const id = submit.request_id;
  if (!id || !onQueueOrigin(submit.status_url) || !onQueueOrigin(submit.response_url)) {
    throw Object.assign(Error(`fal submit answer not usable (request ${id || 'unknown'}): status/result URLs missing or off ${QUEUE}`), { billed: true, request_id: id || null });
  }
  const started = Date.now();
  let status;
  for (;;) {
    const r = await fetcher(submit.status_url, { headers: auth });
    if (r.ok) {
      status = await r.json();
      if (status.status === 'COMPLETED') break;
    } else if (r.status !== 429 && r.status < 500) {
      throw Object.assign(Error(`fal status HTTP ${r.status} for request ${id}`), { billed: true, request_id: id });
    }
    if (Date.now() - started > timeoutMs) throw Object.assign(Error(`request ${id} still not complete after ${timeoutMs / 1000}s`), { billed: true, request_id: id });
    await sleep(pollMs);
  }
  if (status.error) throw Object.assign(Error(`request ${id} failed: ${status.error_type || ''} ${status.error}`.trim()), { billed: true, request_id: id });
  const res = await fetcher(submit.response_url, { headers: auth });
  if (res.status === 403) throw Object.assign(Error(`fal refused the result (403) for request ${id}: ${(await res.text()).slice(0, 300)}`), { billed: true, refused: true, request_id: id });
  if (!res.ok) throw Object.assign(Error(`fal result HTTP ${res.status} for request ${id}`), { billed: true, request_id: id });
  const result = await res.json();
  const file = result[w.output];
  if (!file?.url || !/^https:\/\//.test(file.url)) throw Object.assign(Error(`request ${id}: no ${w.output}.url in the result`), { billed: true, request_id: id });
  // The audio is on fal's media store, not the queue: fetched WITHOUT the key.
  const a = await fetcher(file.url);
  if (!a.ok) throw Object.assign(Error(`request ${id}: audio download HTTP ${a.status}`), { billed: true, request_id: id });
  const bytes = Buffer.from(await a.arrayBuffer());
  const ext = (file.content_type || '').includes('wav') || /\.wav(\?|$)/.test(file.url) ? 'wav' : 'mp3';
  return { request_id: id, seed: result.seed ?? null, content_type: file.content_type || null, ext, bytes, inference_s: status.metrics?.inference_time ?? null };
}

const usd = n => `$${n.toFixed(2)}`;

async function main(argv) {
  const has = f => argv.includes(f);
  const val = f => { const i = argv.indexOf(f); return i >= 0 && argv[i + 1] && !argv[i + 1].startsWith('--') ? argv[i + 1] : null; };
  const trials = loadTrials(ROOT, val('--cues') || DEFAULT_CUES);
  const work = planWork(trials, { cue: val('--cue'), model: val('--model') });
  const total = work.reduce((s, w) => s + w.usd, 0);
  for (const w of work) console.log(`${w.cue.padEnd(22)} ${w.model.padEnd(13)} ${String(w.seconds).padStart(4)}s  ${usd(w.usd)}  ${w.endpoint}`);
  console.log(`${work.length} clip(s), list price ${usd(total)}`);
  if (has('--plan') || !has('--make')) return 0;

  const maxUsd = Number(val('--max-usd') ?? 5);
  if (total > maxUsd) { console.error(`refused: ${usd(total)} is over --max-usd ${usd(maxUsd)}`); return 1; }
  const out = val('--out');
  if (!out) { console.error('--make needs --out DIR'); return 1; }
  const key = readKey(process.env, val('--env-file'));
  if (!key) { console.error('FAL_KEY: absent (set it in the environment, or pass --env-file). See docs/AUDIO.md § Generated music trials.'); return 1; }

  fs.mkdirSync(out, { recursive: true });
  const receiptPath = path.join(out, 'receipt.json');
  const receipt = fs.existsSync(receiptPath) ? JSON.parse(fs.readFileSync(receiptPath, 'utf8')) : { clips: [] };
  const save = () => fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + '\n');
  for (const w of work) {
    process.stdout.write(`making ${w.cue} on ${w.model} … `);
    try {
      const c = await makeClip(key, w);
      const name = `${w.cue}--${w.model}.${c.ext}`;
      fs.writeFileSync(path.join(out, name), c.bytes);
      receipt.clips.push({ file: name, cue: w.cue, era: w.era, lyrics_source: w.lyrics_source, model: w.model, endpoint: w.endpoint, input: w.input, list_usd: w.usd, request_id: c.request_id, seed: c.seed, content_type: c.content_type, bytes: c.bytes.length, sha256: sha(c.bytes), inference_s: c.inference_s, made: new Date().toISOString() });
      save();
      console.log(`${name} (${(c.bytes.length / 1024).toFixed(0)} KiB, request ${c.request_id})`);
    } catch (e) {
      console.log('FAILED');
      console.error(`  ${e.message}`);
      receipt.clips.push({ cue: w.cue, model: w.model, endpoint: w.endpoint, error: e.message, request_id: e.request_id ?? null, made: new Date().toISOString() });
      save();
      if (e.refused) { console.error('  a 403 is the account (credits or a lock), not the clip: stopping. Credits: https://fal.ai/dashboard/usage-billing/credits'); return 1; }
      if (e.billed) { console.error('  stopping without resubmitting; check the request on https://fal.ai/dashboard'); return 1; }
    }
  }
  return 0;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).then(code => process.exit(code), e => { console.error(e.message); process.exit(1); });
}

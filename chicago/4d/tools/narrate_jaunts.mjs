#!/usr/bin/env node
/**
 * T-3578 — voice jaunt scripts with ElevenLabs, only where the words or the voice changed.
 *
 *   node tools/narrate_jaunts.mjs --plan                 what would be voiced, and its characters
 *   node tools/narrate_jaunts.mjs --list-voices          the owner's ElevenLabs voices and their ids
 *   node tools/narrate_jaunts.mjs --voice --out DIR      voice what changed into DIR/narration/
 *   node tools/narrate_jaunts.mjs --verify DIR           check DIR's upload on the public media host
 *
 *   --jaunt ID        only this jaunt (it must be listed in data/narration/voices.json)
 *   --max-chars N     refuse a run that would spend more characters (default: the config's)
 *   --index PATH|URL  the current narration index (default: the media host's)
 *
 * Reads the COMPILED jaunts (data/sidecars/<scene>/jaunts/<id>.json), the files the app shows,
 * through renderers/web/js/narration.js's own narrationScripts/textKey, so the clip the tool
 * makes is the one the app finds. A clip is up to date when the index holds one for these
 * words (by SHA-256) made with the same voice, model, format and settings; nothing else is
 * sent, so an unchanged jaunt costs nothing. The index only ever gains entries: an older
 * build (production, before a promote) still finds the clip for the words it shows.
 *
 * ELEVENLABS_API_KEY comes from the environment (a repository secret in CI) and is never
 * written anywhere. The tool never uploads: .github/workflows/chicago-4d-narration.yml does
 * that with the R2 keys, media first and the index last, then runs --verify.
 */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { narrationScripts, textKey, INDEX_PATH } from '../renderers/web/js/narration.js';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const API = 'https://api.elevenlabs.io';
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const looksLikeId = v => /^[A-Za-z0-9]{20}$/.test(v);

export function loadConfig(root = ROOT) {
  const config = read(path.join(root, 'data/narration/voices.json'));
  if (config.version !== 1 || !Array.isArray(config.jaunts) || typeof config.voices !== 'object') throw Error('voices.json: unknown shape');
  return config;
}
export function publicBase(root = ROOT) {
  return new URL(read(path.join(root, 'tools/audio-hosting.json')).public_base).href;
}

/** Every script of the configured jaunts, with its words' key. */
export async function scriptsFor(config, { root = ROOT, only = null } = {}) {
  const out = [];
  for (const id of config.jaunts) {
    if (only && id !== only) continue;
    const source = read(path.join(root, 'data/jaunts', `${id}.json`));
    const jaunt = read(path.join(root, 'data/sidecars', source.scene, 'jaunts', `${id}.json`));
    for (const script of narrationScripts(jaunt)) out.push({ ...script, jaunt: id, scene: source.scene, text_sha256: await textKey(script.text) });
  }
  if (only && !out.length) throw Error(`${only}: not a jaunt listed in data/narration/voices.json`);
  return out;
}

/** A speaker's voice and settings, resolved to an id; `names` maps the owner's voice names to ids. */
export function voiceFor(config, speaker, names = null) {
  const raw = config.voices[speaker] ?? null;
  const entry = typeof raw === 'string' ? { voice: raw } : raw;
  if (!entry?.voice) return { missing: 'no voice chosen' };
  let id = entry.voice;
  if (!looksLikeId(id)) {
    if (!names) return { missing: `voice "${id}" is a name; resolving it needs ELEVENLABS_API_KEY` };
    const hit = names.get(id.toLowerCase());
    if (!hit) return { missing: `no voice named "${id}" in this ElevenLabs account` };
    id = hit;
  }
  const params = { voice_id: id, model_id: config.model_id, output_format: config.output_format,
    voice_settings: { ...config.voice_settings, ...(entry.voice_settings ?? {}) } };
  return { params, settings_sha256: sha(JSON.stringify(params)), voice_name: entry.voice };
}

/** What to voice: scripts whose words have no clip, or a clip made with other settings. */
export function plan(scripts, config, index, names = null) {
  const todo = [], current = [], skipped = [];
  for (const s of scripts) {
    const v = voiceFor(config, s.speaker, names);
    if (v.missing) { skipped.push({ ...s, reason: v.missing }); continue; }
    const have = index?.clips?.[s.text_sha256];
    (have?.settings_sha256 === v.settings_sha256 ? current : todo).push({ ...s, voice: v });
  }
  return { todo, current, skipped, chars: todo.reduce((n, s) => n + s.text.length, 0) };
}

async function readIndex(where, fetcher = fetch) {
  if (where && !/^https?:/.test(where)) return fs.existsSync(where) ? read(where) : { version: 1, clips: {} };
  const url = where ?? new URL(INDEX_PATH, publicBase()).href;
  const r = await fetcher(url, { cache: 'no-store' });
  if (r.status === 404 || r.status === 403) return { version: 1, clips: {} };   // nothing voiced yet
  if (!r.ok) throw Error(`narration index: HTTP ${r.status} from ${url}`);
  const index = await r.json();
  if (index?.version !== 1 || typeof index.clips !== 'object') throw Error('narration index: unknown shape');
  return index;
}

export async function listVoices(key, fetcher = fetch) {
  const r = await fetcher(`${API}/v1/voices`, { headers: { 'xi-api-key': key } });
  if (!r.ok) throw Error(`ElevenLabs voices: HTTP ${r.status} ${await r.text().catch(() => '')}`.trim());
  return (await r.json()).voices.map(v => ({ name: v.name, id: v.voice_id, category: v.category }));
}

export async function synthesize(key, script, fetcher = fetch, { tries = 4, wait = ms => new Promise(r => setTimeout(r, ms)) } = {}) {
  const { voice_id, output_format, ...body } = script.voice.params;
  for (let attempt = 1; ; attempt++) {
    const r = await fetcher(`${API}/v1/text-to-speech/${encodeURIComponent(voice_id)}?output_format=${encodeURIComponent(output_format)}`, {
      method: 'POST', headers: { 'xi-api-key': key, 'content-type': 'application/json', accept: 'audio/mpeg' },
      body: JSON.stringify({ text: script.text, ...body }) });
    if (r.ok) {
      const bytes = Buffer.from(await r.arrayBuffer());
      if (bytes.length < 1000) throw Error(`${script.jaunt}/${script.id}: ElevenLabs returned ${bytes.length} bytes`);
      return bytes;
    }
    const detail = await r.text().catch(() => '');
    if ((r.status === 429 || r.status >= 500) && attempt < tries) { await wait(2000 * 2 ** attempt); continue; }
    throw Error(`${script.jaunt}/${script.id}: ElevenLabs HTTP ${r.status} ${detail.slice(0, 300)}`.trim());
  }
}

/** Voice the plan into out/narration/, and write the index the upload ends with. */
export async function voice(work, index, out, key, { fetcher = fetch, now = () => new Date().toISOString() } = {}) {
  const dir = path.join(out, 'narration');
  fs.mkdirSync(dir, { recursive: true });
  const next = { version: 1, updated: now(), clips: { ...index.clips } }, made = [];
  for (const s of work) {
    const bytes = await synthesize(key, s, fetcher);
    const digest = sha(bytes), file = `narration/${digest}.mp3`;
    fs.writeFileSync(path.join(out, file), bytes);
    next.clips[s.text_sha256] = { text_sha256: s.text_sha256, file, bytes: bytes.length, sha256: digest,
      jaunt: s.jaunt, scene: s.scene, part: s.part, part_id: s.id, speaker: s.speaker, chars: s.text.length,
      voice_id: s.voice.params.voice_id, voice: s.voice.voice_name, model_id: s.voice.params.model_id,
      output_format: s.voice.params.output_format, settings_sha256: s.voice.settings_sha256,
      provider: 'ElevenLabs text to speech', generated: now() };
    made.push(file);
    console.log(`voiced ${s.jaunt}/${s.part}:${s.id} (${s.speaker}, ${s.text.length} chars) → ${file} ${bytes.length} bytes`);
  }
  fs.writeFileSync(path.join(out, INDEX_PATH), JSON.stringify(next, null, 1) + '\n');
  fs.writeFileSync(path.join(out, 'made.json'), JSON.stringify(made) + '\n');
  return { index: next, made };
}

/** After upload: every made clip and the index are served, whole, from the public host. */
export async function verify(out, base = publicBase(), fetcher = fetch) {
  const made = read(path.join(out, 'made.json')), local = read(path.join(out, INDEX_PATH)), errors = [];
  for (const file of made) {
    const r = await fetcher(new URL(file, base), { cache: 'no-store' });
    const bytes = r.ok ? Buffer.from(await r.arrayBuffer()) : null;
    if (!bytes) errors.push(`${file}: HTTP ${r.status}`);
    else if (sha(bytes) !== path.basename(file, '.mp3')) errors.push(`${file}: served bytes differ`);
  }
  const served = await readIndex(new URL(INDEX_PATH, base).href, fetcher);
  for (const k of Object.keys(local.clips)) if (served.clips[k]?.file !== local.clips[k].file) errors.push(`index: ${k} not served`);
  return errors;
}

function report(p, scripts, config) {
  const name = s => config.speaker_names?.[s] ?? s;
  const lines = [`Narration plan: ${scripts.length} scripts in ${new Set(scripts.map(s => s.jaunt)).size} jaunt(s);`
    + ` ${p.current.length} already voiced, ${p.todo.length} to voice (${p.chars} characters), ${p.skipped.length} skipped.`];
  for (const s of p.todo) lines.push(`  voice   ${s.jaunt}/${s.part}:${s.id}  ${name(s.speaker)}  ${s.text.length} chars`);
  for (const s of p.skipped) lines.push(`  skip    ${s.jaunt}/${s.part}:${s.id}  ${name(s.speaker)}: ${s.reason}`);
  return lines.join('\n');
}

async function main(argv) {
  const has = f => argv.includes(f), arg = f => { const i = argv.indexOf(f); return i >= 0 ? argv[i + 1] : null; };
  const key = process.env.ELEVENLABS_API_KEY || null, summary = process.env.GITHUB_STEP_SUMMARY;
  const note = text => { console.log(text); if (summary) fs.appendFileSync(summary, '```\n' + text + '\n```\n'); };
  if (has('--list-voices')) {
    if (!key) throw Error('--list-voices needs ELEVENLABS_API_KEY');
    const voices = await listVoices(key);
    note(['Your ElevenLabs voices (name · id · kind):', ...voices.map(v => `  ${v.name} · ${v.id} · ${v.category}`)].join('\n'));
    return;
  }
  if (has('--verify')) {
    const errors = await verify(arg('--verify'));
    if (errors.length) throw Error(`NARRATION VERIFY FAIL\n${errors.join('\n')}`);
    note('NARRATION VERIFY PASS — every new clip and the index are served from the media host');
    return;
  }
  const config = loadConfig();
  const scripts = await scriptsFor(config, { only: arg('--jaunt') });
  const index = await readIndex(arg('--index'));
  const names = key && Object.values(config.voices).some(v => (typeof v === 'string' ? v : v?.voice) && !looksLikeId(typeof v === 'string' ? v : v.voice))
    ? new Map((await listVoices(key)).map(v => [v.name.toLowerCase(), v.id])) : null;
  const p = plan(scripts, config, index, names);
  note(report(p, scripts, config));
  const max = Number(arg('--max-chars') ?? config.max_chars_per_run);
  if (has('--voice')) {
    const out = arg('--out'); if (!out) throw Error('--voice needs --out DIR');
    if (!p.todo.length) { fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(path.join(out, 'made.json'), '[]\n'); note('Nothing to voice.'); return; }
    if (!key) throw Error('--voice needs ELEVENLABS_API_KEY');
    if (p.chars > max) throw Error(`this run would spend ${p.chars} characters, over the ${max} cap; raise --max-chars (or max_chars_per_run) to allow it`);
    const { made } = await voice(p.todo, index, out, key);
    note(`Voiced ${made.length} clip(s), ${p.chars} characters.`);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch(e => { console.error(e.message); process.exit(1); });
}

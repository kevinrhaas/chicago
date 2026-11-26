#!/usr/bin/env node
/**
 * T-3578 — voice jaunt scripts with ElevenLabs, only where the words or the voice changed.
 *
 *   node tools/narrate_jaunts.mjs --plan                 what would be voiced, and its characters
 *   node tools/narrate_jaunts.mjs --list-voices          the owner's ElevenLabs voices and their ids
 *   node tools/narrate_jaunts.mjs --voice --out DIR      voice what changed into DIR/narration/
 *   node tools/narrate_jaunts.mjs --verify DIR           check DIR's upload on the public media host
 *   node tools/narrate_jaunts.mjs --quota                the account's ElevenLabs credits used, limit, reset
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
import { narrationScripts, textKey, clipKey, INDEX_PATH, NARRATOR, NARRATORS, DEFAULT_NARRATOR } from '../renderers/web/js/narration.js';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const API = 'https://api.elevenlabs.io';
const read = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const looksLikeId = v => /^[A-Za-z0-9]{20}$/.test(v);

export function loadConfig(root = ROOT) {
  const config = read(path.join(root, 'data/narration/voices.json'));
  if (config.version !== 1 || !Array.isArray(config.jaunts) || typeof config.voices !== 'object' || typeof config.narrators !== 'object') throw Error('voices.json: unknown shape');
  const ids = Object.keys(config.narrators).join(), app = NARRATORS.map(n => n.id).join();
  if (ids !== app) throw Error(`voices.json narrators (${ids}) differ from the app's choices in narration.js (${app})`);
  for (const j of jauntEntries(config)) {
    if (!j.id) throw Error('voices.json: a jaunts entry has no id');
    for (const n of j.narrators) if (!config.narrators[n]) throw Error(`voices.json: ${j.id} names narrator "${n}", which is not in narrators`);
  }
  return config;
}
/** The voiced jaunts and the narrators each is voiced in. An entry is a jaunt id (every narrator)
 *  or { id, narrators: [...] }. The owner, 2026-11-19 (T-3696): new jaunts are voiced in the
 *  Cultivated Essayist only, the Storyteller later, to keep inside the ElevenLabs budget; the app
 *  plays the default narrator's clip when the chosen one has none (narration.js clipFor). */
export function jauntEntries(config) {
  return config.jaunts.map(j => (typeof j === 'string' ? { id: j, narrators: Object.keys(config.narrators) }
    : { id: j.id, narrators: j.narrators ?? Object.keys(config.narrators) }));
}
export const jauntIds = config => jauntEntries(config).map(j => j.id);
/** The words of a text, and nothing else: what a performance copy must keep unchanged. Tags in
 *  square brackets are directions; case, punctuation and spacing are the performance's. */
export function spokenWords(text) {
  return String(text).replace(/\[[^\]]*\]/g, ' ').toLowerCase().match(/[\p{L}\p{N}]+/gu) ?? [];
}
export const sameWords = (a, b) => spokenWords(a).join(' ') === spokenWords(b).join(' ');

/** A jaunt's direction (data/narration/direction/<jaunt>.json): for a part, the words as they are
 *  performed: the same words as the panel shows, with ElevenLabs v3 audio tags ([laughs],
 *  [whispers], [short pause] ...) and punctuation for pauses. Keyed `<part>:<id>`. */
export function loadDirection(id, root = ROOT) {
  const file = path.join(root, 'data/narration/direction', `${id}.json`);
  return fs.existsSync(file) ? read(file).scripts ?? {} : {};
}

/** A direction that no longer matches its script is set aside (the plain words are voiced) and
 *  reported: tools/test_narration.mjs fails on one, so the gate catches an edit to a script
 *  whose direction was not brought along. */
export function directionProblems(scripts, directions) {
  const problems = [], seen = new Set();
  for (const s of scripts) {
    const k = `${s.part}:${s.id}`, d = directions[s.jaunt]?.[k];
    seen.add(`${s.jaunt}/${k}`);
    if (d != null && !sameWords(d, s.text)) problems.push(`${s.jaunt}/${k}: the direction's words differ from the script's`);
  }
  for (const [jaunt, map] of Object.entries(directions))
    for (const k of Object.keys(map)) if (!seen.has(`${jaunt}/${k}`)) problems.push(`${jaunt}/${k}: direction for a part the jaunt does not have`);
  return [...new Set(problems)];
}

/** The smooth style (owner, 2026-11-19, T-3696: "not a lot of transition between topics and also
 *  pauses between subjects"; "the parts where they whisper and laugh could be toned down"; "that
 *  smoother narration rule applies for all the jaunts"). A direction file marked
 *  `"style": "smooth"` is held to it: no whispering, at most one laugh in a script, and a pause
 *  ([short pause], [long pause] or an ellipsis) at least every SMOOTH.words_per_pause words, so
 *  a speaker breathes between subjects. docs/AUDIO.md § Narration style. Every new or re-made
 *  direction is written in it; older files say nothing, and are brought to it when next voiced. */
export const SMOOTH = { words_per_pause: 50, laughs: 1 };
const LAUGH = /\[(?:laughs?|laughing|chuckles?|chuckling|giggles?|giggling|snickers?)[^\]]*\]/gi;
const WHISPER = /\[(?:whispers?|whispering)[^\]]*\]/gi;
const PAUSE = /\[(?:short |long )?pause\]|\.\.\.|…/gi;
export function styleProblems(id, file) {
  if (file?.style !== 'smooth') return [];
  const out = [];
  for (const [k, text] of Object.entries(file.scripts ?? {})) {
    const words = spokenWords(text).length, pauses = (text.match(PAUSE) ?? []).length;
    if ((text.match(WHISPER) ?? []).length) out.push(`${id}/${k}: whispers (the smooth style has none)`);
    const laughs = (text.match(LAUGH) ?? []).length;
    if (laughs > SMOOTH.laughs) out.push(`${id}/${k}: ${laughs} laughs (the smooth style allows ${SMOOTH.laughs})`);
    const need = Math.floor(words / SMOOTH.words_per_pause);
    if (pauses < need) out.push(`${id}/${k}: ${pauses} pause(s) in ${words} words (the smooth style wants ${need})`);
  }
  return out;
}
export function loadDirectionFile(id, root = ROOT) {
  const file = path.join(root, 'data/narration/direction', `${id}.json`);
  return fs.existsSync(file) ? read(file) : null;
}

export function publicBase(root = ROOT) {
  return new URL(read(path.join(root, 'tools/audio-hosting.json')).public_base).href;
}

/** Every script of the configured jaunts, with its words' key and its clip's index key. A
 *  narrator script is listed once for each narrator (`narrator` names which). */
export async function scriptsFor(config, { root = ROOT, only = null } = {}) {
  const out = [];
  for (const { id, narrators } of jauntEntries(config)) {
    if (only && id !== only) continue;
    const source = read(path.join(root, 'data/jaunts', `${id}.json`));
    const jaunt = read(path.join(root, 'data/sidecars', source.scene, 'jaunts', `${id}.json`));
    const direction = loadDirection(id, root);
    for (const script of narrationScripts(jaunt)) {
      const text_sha256 = await textKey(script.text);
      const directed = direction[`${script.part}:${script.id}`];
      const spoken = directed != null && sameWords(directed, script.text) ? directed : script.text;
      const spoken_sha256 = sha(spoken);
      for (const narrator of script.speaker === NARRATOR ? narrators : [null]) {
        out.push({ ...script, jaunt: id, scene: source.scene, text_sha256, spoken, spoken_sha256, directed: spoken !== script.text, narrator,
          key: clipKey(text_sha256, script.speaker, narrator ?? DEFAULT_NARRATOR) });
      }
    }
  }
  if (only && !out.length) throw Error(`${only}: not a jaunt listed in data/narration/voices.json`);
  return out;
}

/** A speaker's voice and settings, resolved to an id; `names` maps the owner's voice names to ids.
 *  The narrator's voice is the named narrator's. */
export function voiceFor(config, speaker, names = null, narrator = DEFAULT_NARRATOR) {
  const raw = speaker === NARRATOR ? config.narrators[narrator] ?? null : config.voices[speaker] ?? null;
  const entry = typeof raw === 'string' ? { voice: raw } : raw;
  if (!entry?.voice) return { missing: 'no voice chosen' };
  let id = entry.voice;
  if (!looksLikeId(id)) {
    if (!names) return { missing: `voice "${id}" is a name; resolving it needs ELEVENLABS_API_KEY` };
    const hit = names.get(id.replace(/\s+/g, ' ').trim().toLowerCase());
    if (!hit) return { missing: `no voice named "${id}" in this ElevenLabs account` };
    id = hit;
  }
  const params = { voice_id: id, model_id: config.model_id, output_format: config.output_format,
    voice_settings: { ...config.voice_settings, ...(entry.voice_settings ?? {}) } };
  return { params, settings_sha256: sha(JSON.stringify(params)), voice_name: entry.voice };
}

/** What to voice: scripts whose words have no clip, or a clip made with other settings or another
 *  performance of them (a clip from before direction was performed from the plain words). */
export function plan(scripts, config, index, names = null) {
  const todo = [], current = [], skipped = [], seen = new Set();
  for (const s of scripts) {
    // T-3755: one clip for one set of words (a stop's closing line is shared by many jaunts):
    // voiced once in a run, not once per jaunt that says it.
    if (seen.has(s.key)) continue;
    seen.add(s.key);
    const v = voiceFor(config, s.speaker, names, s.narrator ?? DEFAULT_NARRATOR);
    if (v.missing) { skipped.push({ ...s, reason: v.missing }); continue; }
    const have = index?.clips?.[s.key];
    const performed = have ? have.spoken_sha256 ?? sha(s.text) : null;
    (have?.settings_sha256 === v.settings_sha256 && performed === (s.spoken_sha256 ?? sha(s.text)) ? current : todo).push({ ...s, voice: v });
  }
  return { todo, current, skipped, chars: todo.reduce((n, s) => n + (s.spoken ?? s.text).length, 0) };
}

/** The longest start of the plan (in its order) that fits `budget` characters; a clip is never
 *  split, and one that does not fit ends the batch so the order is kept. */
export function takeWithin(todo, budget) {
  let chars = 0, i = 0;
  for (; i < todo.length; i++) {
    const n = (todo[i].spoken ?? todo[i].text).length;
    if (chars + n > budget) break;
    chars += n;
  }
  return { batch: todo.slice(0, i), rest: todo.slice(i), chars };
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

/** The account's ElevenLabs quota (T-3696): credits used this billing period, its limit and when it
 *  resets. A key without the user_read permission gets null, and the run says so; it never fails a
 *  run, which still voices. Asked before and after voicing, the difference is what the run spent. */
export async function quota(key, fetcher = fetch) {
  try {
    const r = await fetcher(`${API}/v1/user/subscription`, { headers: { 'xi-api-key': key } });
    if (!r.ok) return { error: `HTTP ${r.status}` };
    const q = await r.json();
    if (!Number.isFinite(q.character_count) || !Number.isFinite(q.character_limit)) return { error: 'unknown shape' };
    return { tier: q.tier ?? null, used: q.character_count, limit: q.character_limit,
      resets: Number.isFinite(q.next_character_count_reset_unix) ? new Date(q.next_character_count_reset_unix * 1000).toISOString() : null };
  } catch (e) { return { error: e.message }; }
}
export const quotaLine = (q, when) => (q.error ? `ElevenLabs quota ${when}: not readable (${q.error}; the key needs the user_read permission)`
  : `ElevenLabs quota ${when}: ${q.used} of ${q.limit} credits used this period (${q.limit - q.used} left${q.tier ? `, plan ${q.tier}` : ''}${q.resets ? `, resets ${q.resets}` : ''})`);

export async function synthesize(key, script, fetcher = fetch, { tries = 4, wait = ms => new Promise(r => setTimeout(r, ms)) } = {}) {
  const { voice_id, output_format, ...body } = script.voice.params;
  for (let attempt = 1; ; attempt++) {
    const r = await fetcher(`${API}/v1/text-to-speech/${encodeURIComponent(voice_id)}?output_format=${encodeURIComponent(output_format)}`, {
      method: 'POST', headers: { 'xi-api-key': key, 'content-type': 'application/json', accept: 'audio/mpeg' },
      body: JSON.stringify({ text: script.spoken ?? script.text, ...body }) });
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
export async function voice(work, index, out, key, { fetcher = fetch, now = () => new Date().toISOString(), narrators = null } = {}) {
  const dir = path.join(out, 'narration');
  fs.mkdirSync(dir, { recursive: true });
  const next = { version: 1, updated: now(), clips: { ...index.clips } }, made = [];
  if (narrators) next.narrators = narrators;
  let stopped = null;
  for (const s of work) {
    // T-3696: a clip ElevenLabs refuses (out of credits, most likely) ends the run, but what was
    // already voiced is paid for: it is kept, indexed and uploaded, and the rest waits.
    let bytes;
    try { bytes = await synthesize(key, s, fetcher); } catch (e) { stopped = { at: `${s.jaunt}/${s.part}:${s.id}`, error: e.message }; break; }
    const digest = sha(bytes), file = `narration/${digest}.mp3`;
    fs.writeFileSync(path.join(out, file), bytes);
    next.clips[s.key] = { text_sha256: s.text_sha256, file, bytes: bytes.length, sha256: digest,
      jaunt: s.jaunt, scene: s.scene, part: s.part, part_id: s.id, speaker: s.speaker, ...(s.narrator ? { narrator: s.narrator } : {}), chars: (s.spoken ?? s.text).length,
      spoken_sha256: s.spoken_sha256 ?? sha(s.text), directed: !!s.directed,
      voice_id: s.voice.params.voice_id, voice: s.voice.voice_name, model_id: s.voice.params.model_id,
      output_format: s.voice.params.output_format, settings_sha256: s.voice.settings_sha256,
      provider: 'ElevenLabs text to speech', generated: now() };
    made.push(file);
    console.log(`voiced ${s.jaunt}/${s.part}:${s.id} (${s.narrator ? `narrator ${s.narrator}` : s.speaker}, ${(s.spoken ?? s.text).length} chars${s.directed ? ', directed' : ''}) → ${file} ${bytes.length} bytes`);
  }
  fs.writeFileSync(path.join(out, INDEX_PATH), JSON.stringify(next, null, 1) + '\n');
  fs.writeFileSync(path.join(out, 'made.json'), JSON.stringify(made) + '\n');
  return { index: next, made, stopped };
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
  const name = s => (s.narrator ? `Narrator (${config.narrators[s.narrator]?.label ?? s.narrator})` : config.speaker_names?.[s.speaker] ?? s.speaker);
  const voiceOf = s => (s.voice ? ` · voice "${s.voice.voice_name}"` : '');
  const lines = [`Narration plan: ${scripts.length} scripts in ${new Set(scripts.map(s => s.jaunt)).size} jaunt(s);`
    + ` ${p.current.length} already voiced, ${p.todo.length} to voice (${p.chars} characters), ${p.skipped.length} skipped.`];
  for (const s of p.todo) lines.push(`  voice   ${s.jaunt}/${s.part}:${s.id}  ${name(s)}${voiceOf(s)}  ${(s.spoken ?? s.text).length} chars${s.directed ? ' (directed)' : ''}`);
  for (const s of p.current) lines.push(`  have    ${s.jaunt}/${s.part}:${s.id}  ${name(s)}${voiceOf(s)}`);
  for (const s of p.skipped) lines.push(`  skip    ${s.jaunt}/${s.part}:${s.id}  ${name(s)}: ${s.reason}`);
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
  if (has('--quota')) {
    if (!key) throw Error('--quota needs ELEVENLABS_API_KEY');
    note(quotaLine(await quota(key), 'now'));
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
  const stale = directionProblems(scripts, Object.fromEntries(jauntIds(config).map(id => [id, loadDirection(id)])));
  if (stale.length) note(['Direction set aside (the plain words are voiced instead):', ...stale.map(x => `  ${x}`)].join('\n'));
  const index = await readIndex(arg('--index'));
  const names = key && [...Object.values(config.voices), ...Object.values(config.narrators)].some(v => (typeof v === 'string' ? v : v?.voice) && !looksLikeId(typeof v === 'string' ? v : v.voice))
    ? new Map((await listVoices(key)).map(v => [v.name.replace(/\s+/g, ' ').trim().toLowerCase(), v.id])) : null;
  const p = plan(scripts, config, index, names);
  note(report(p, scripts, config));
  const before = key ? await quota(key) : null;
  if (before) note(quotaLine(before, 'before this run'));
  const max = Number(arg('--max-chars') ?? config.max_chars_per_run);
  if (has('--voice')) {
    const out = arg('--out'); if (!out) throw Error('--voice needs --out DIR');
    if (!p.todo.length) { fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(path.join(out, 'made.json'), '[]\n'); note('Nothing to voice.'); return; }
    if (!key) throw Error('--voice needs ELEVENLABS_API_KEY');
    // T-3696 (the owner, 2026-11-19: "work towards the full budget"): a run voices the plan in
    // order (voices.json's jaunt order, which is the budget plan's) up to the per-run cap and what
    // the quota has left above its reserve; the rest waits for the next run, which takes up
    // where this one stopped. A run never fails for want of credits.
    const left = before && !before.error ? before.limit - before.used - (config.quota_reserve ?? 0) : Infinity;
    const { batch, rest, chars } = takeWithin(p.todo, Math.min(max, left));
    if (rest.length) note(`Over ${Math.min(max, left) === max ? `the ${max}-character cap per run` : `what the quota has left (${Math.max(0, left)} above the ${config.quota_reserve ?? 0} reserve)`}: `
      + `${rest.length} clip(s), ${rest.reduce((n, s) => n + (s.spoken ?? s.text).length, 0)} characters, wait for the next run:\n`
      + [...new Set(rest.map(s => s.jaunt))].map(j => `  ${j}`).join('\n'));
    if (!batch.length) { fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(path.join(out, 'made.json'), '[]\n'); note('Nothing voiced this run.'); return; }
    const { made, stopped } = await voice(batch, index, out, key, { narrators: { default: DEFAULT_NARRATOR,
      choices: Object.fromEntries(Object.entries(config.narrators).map(([id, n]) => [id, n.label ?? id])) } });
    const spent = batch.slice(0, made.length).reduce((n, s) => n + (s.spoken ?? s.text).length, 0);
    note(`Voiced ${made.length} clip(s), ${spent} characters.`);
    if (stopped) {
      note(`Stopped at ${stopped.at}: ${stopped.error}. The ${made.length} clip(s) voiced before it are kept and uploaded; the other ${batch.length - made.length} wait for the next run.`);
      if (!made.length) throw Error(`nothing voiced: ${stopped.error}`);
      console.log(`::warning::narration stopped early at ${stopped.at} (${stopped.error.slice(0, 160)})`);
    }
    const after = await quota(key);
    note(quotaLine(after, 'after this run'));
    if (!before.error && !after.error) note(`This run used ${after.used - before.used} ElevenLabs credits (${spent} characters sent).`);
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main(process.argv.slice(2)).catch(e => { console.error(e.message); process.exit(1); });
}

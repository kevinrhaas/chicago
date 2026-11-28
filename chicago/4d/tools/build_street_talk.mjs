#!/usr/bin/env node
// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * T-3812 — the street talk: short lines a scene's people say aloud as you pass or greet them.
 * The owner, 2026-11-27: "Let's do great fire plus street talk". Lines are written in
 * docs/RESEARCH/street-talk-3812/<scene>.txt (its header says the format); this writes
 * data/narration/street/<scene>.json for the voicer (tools/narrate_jaunts.mjs, which voices
 * each line once in its kind's stock voice) and the app (renderers/web/js/street-talk.js).
 *
 *   node tools/build_street_talk.mjs            write every scene
 *   node tools/build_street_talk.mjs --check    refuse a stale file (tools/test_narration.mjs runs it)
 *
 * Who says what: the people of the scene, by the roles, sex, age and origin the tales library
 * already holds for them (data/tales/<scene>.json `tellers`, tools/build_tales.py), sorted into
 * one of seven voices by VOICES (first rule that fits). Children are not voiced. Someone with a
 * voice of their own (data/narration/voices.json `voices`, the Glessner household) is left out:
 * their own voice is the one they speak in.
 */
import fs from 'node:fs';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const SCENES = ['1904'];
export const KINDS = ['greet', 'remark'];
export const TIMES = ['morning', 'afternoon', 'evening'];
export const SEASONS = ['spring', 'summer', 'fall', 'winter'];
export const MAX_CHARS = 140;
/** First fit wins. `roles`: any of the teller's roles; `min_age`: at least that old. */
export const VOICES = [
  { voice: 'cook', sex: 'f', roles: ['cook', 'housekeeper', 'governess', 'companion'] },
  { voice: 'cook', sex: 'f', roles: ['maid', 'laundress', 'nurse', 'nursemaid', 'ladies_maid'], min_age: 45 },
  { voice: 'maid', sex: 'f', roles: ['maid', 'laundress', 'nurse', 'nursemaid', 'ladies_maid'] },
  { voice: 'manservant', sex: 'm', roles: ['coachman', 'groom', 'manservant', 'butler', 'footman', 'valet', 'steward', 'houseman'] },
  { voice: 'young_lady', sex: 'f', roles: ['young_lady'] },
  { voice: 'young_man', sex: 'm', roles: ['young_man'] },
  { voice: 'lady', sex: 'f', roles: ['lady', 'wife', 'widow'] },
  { voice: 'gent', sex: 'm', roles: ['gentleman'] },
];
export const VOICE_IDS = [...new Set(VOICES.map((v) => v.voice))];
const CHILD = ['child', 'toddler'];
const read = (p) => JSON.parse(fs.readFileSync(p, 'utf8'));

/** 'role,role/sex[/c][/a<age>][/o<origin>]' (tales.js readTeller). */
export function readTeller(row) {
  const [roles = '', sex = '', ...rest] = String(row).split('/');
  const age = Number(rest.find((x) => /^a\d+$/.test(x))?.slice(1));
  return { roles: roles.split(',').filter(Boolean), sex, age: Number.isFinite(age) ? age : null,
    origin: rest.find((x) => /^o\w+$/.test(x))?.slice(1) ?? null };
}

/** The voice a teller speaks street talk in, or null (a child, or nobody's kind). */
export function voiceOf(teller) {
  if (!teller || teller.roles.some((r) => CHILD.includes(r)) || (teller.age != null && teller.age < 16)) return null;
  for (const v of VOICES) {
    if (v.sex !== teller.sex || !teller.roles.some((r) => v.roles.includes(r))) continue;
    if (v.min_age && !(teller.age >= v.min_age)) continue;
    return v.voice;
  }
  return null;
}

export function parseLines(text, file = 'lines') {
  const lines = [], problems = [], seen = new Set();
  text.split(/\r?\n/).forEach((raw, i) => {
    const line = raw.trim();
    if (!line || line.startsWith('#')) return;
    const m = /^(\w+)\s+(\w+)(?:@(\w+))?((?:\s+[\w:]+)*)\s*\|\s*(.+)$/.exec(line);
    const where = `${file}:${i + 1}`;
    if (!m) { problems.push(`${where}: not "<voice> <kind>[@time] [season] [o:origin] | words"`); return; }
    const [, voice, kind, time, tags, words] = m;
    const row = { voice, kind };
    if (time) row.time = time;
    for (const tag of tags.trim().split(/\s+/).filter(Boolean)) {
      if (SEASONS.includes(tag)) row.season = tag;
      else if (/^o:\w+$/.test(tag)) row.origin = tag.slice(2);
      else problems.push(`${where}: unknown tag ${tag}`);
    }
    if (!VOICE_IDS.includes(voice)) problems.push(`${where}: no voice ${voice}`);
    if (!KINDS.includes(kind)) problems.push(`${where}: no kind ${kind}`);
    if (time && !TIMES.includes(time)) problems.push(`${where}: no time ${time}`);
    const text = words.trim();
    if (text.length > MAX_CHARS) problems.push(`${where}: ${text.length} characters, over ${MAX_CHARS}`);
    if (/\b(19(0[5-9]|[1-9]\d)|20\d\d)\b/.test(text)) problems.push(`${where}: a year after 1904`);
    // A street clip is keyed by its words and its voice (street-talk.js streetKey): each voice says them once.
    if (seen.has(`${voice}|${text}`)) problems.push(`${where}: the same words as another ${voice} line`);
    seen.add(`${voice}|${text}`);
    row.id = `${voice}-${kind}-${createHash('sha1').update(text).digest('hex').slice(0, 6)}`;
    row.text = text;
    lines.push(row);
  });
  return { lines, problems };
}

export function build(scene, root = ROOT) {
  const src = path.join(root, 'docs/RESEARCH/street-talk-3812', `${scene}.txt`);
  const { lines, problems } = parseLines(fs.readFileSync(src, 'utf8'), path.relative(root, src));
  const own = new Set(Object.keys(read(path.join(root, 'data/narration/voices.json')).voices ?? {}));
  const tellers = read(path.join(root, 'data/tales', `${scene}.json`)).tellers ?? {};
  const people = {};
  for (const [id, row] of Object.entries(tellers).sort(([a], [b]) => a.localeCompare(b))) {
    if (own.has(id)) continue;
    const t = readTeller(row), voice = voiceOf(t);
    if (voice) people[id] = t.origin ? `${voice}/${t.origin}` : voice;
  }
  for (const v of VOICE_IDS) for (const kind of KINDS)
    if (!lines.some((l) => l.voice === v && l.kind === kind)) problems.push(`${scene}: no ${kind} line for ${v}`);
  return { problems, doc: { version: 1, scene,
    about: `T-3812: street talk, written by tools/build_street_talk.mjs from docs/RESEARCH/street-talk-3812/${scene}.txt. ` +
      'Each line is voiced once in its voice (data/narration/voices.json `street:<voice>`); `people` says which voice ' +
      '(and origin) each person speaks in. Reconstructed speech, not quotation (L-street-talk-3812).',
    liberty: 'L-street-talk-3812', voices: VOICE_IDS, lines, people } };
}

export const outPath = (scene, root = ROOT) => path.join(root, 'data/narration/street', `${scene}.json`);
export const body = (doc) => JSON.stringify(doc, null, 2) + '\n';

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const check = process.argv.includes('--check');
  let bad = 0;
  for (const scene of SCENES) {
    const { problems, doc } = build(scene);
    if (problems.length) { console.error(problems.join('\n')); bad = 1; continue; }
    const file = outPath(scene), text = body(doc);
    if (check) {
      if (!fs.existsSync(file) || fs.readFileSync(file, 'utf8') !== text) { console.error(`${path.relative(ROOT, file)} is stale: run node tools/build_street_talk.mjs`); bad = 1; }
      continue;
    }
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, text);
    console.log(`street talk ${scene}: ${doc.lines.length} lines (${doc.lines.reduce((n, l) => n + l.text.length, 0)} characters), ${Object.keys(doc.people).length} people`);
  }
  process.exit(bad);
}

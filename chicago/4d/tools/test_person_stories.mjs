#!/usr/bin/env node
// T-3521 (the owner, 2026-11-08: "the story text style deviates from the style we had before,
// this is really technical and not interesting, do a sweep of everyone so that we have good
// correct stories for each"). Every person of the 1812 and 1904 scenes has a story written for
// a visitor: a written story in data/residents_<scene>/stories.json, or (with none written) a
// reconstructed history or a census servant's lead, which the card says from the record. A
// written story is prose, not research notes: none of the record's working words (source
// lines, sheets and leaves, OCR, ticket or liberty numbers, the grade names) belong in it.
import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const ENUMERATED = /^Enumerated on 1 June 1900 /;
const TECHNICAL = /\b(OCR|ED \d+|sheet \d|leaf n?\d|line \d+|L\d{3}|T-\d{3,4}|attested|inferred|reconstructed|grade|the card|this card)\b/i;
const fail = [];
let told = 0, other = 0;

for (const scene of ['1812', '1904']) {
  const dir = join(root, 'data', `residents_${scene}`);
  const doc = JSON.parse(readFileSync(join(dir, 'stories.json'), 'utf8'));
  const stories = doc.stories ?? {};
  const people = new Map();
  for (const f of readdirSync(join(dir, 'households')).filter((n) => n.endsWith('.json'))) {
    const hh = JSON.parse(readFileSync(join(dir, 'households', f), 'utf8'));
    for (const p of hh.persons ?? []) people.set(p.id, p);
  }
  for (const id of Object.keys(stories)) if (!people.has(id)) fail.push(`${scene}: story for ${id}, who is in no household`);
  for (const [id, p] of people) {
    const paras = stories[id];
    if (paras) {
      told++;
      if (!Array.isArray(paras) || !paras.length || paras.some((s) => typeof s !== 'string' || s.trim().length < 20)) fail.push(`${scene}: ${id} story is not a list of paragraphs`);
      for (const s of paras ?? []) {
        const m = String(s).match(TECHNICAL);
        if (m) fail.push(`${scene}: ${id} story carries "${m[0]}": ${String(s).slice(0, 90)}`);
      }
      continue;
    }
    const note = String(p.notes ?? p.note ?? '');
    const hist = Array.isArray(p.history?.paragraphs) && p.history.paragraphs.length;
    if (hist || ENUMERATED.test(note)) { other++; continue; }
    fail.push(`${scene}: ${id} (${p.name}) has no story`);
  }
}

if (fail.length) {
  console.error(`FAIL person stories: ${fail.length}\n  ${fail.slice(0, 40).join('\n  ')}`);
  process.exit(1);
}
console.log(`ok person stories: ${told} written, ${other} said from a history or census line`);

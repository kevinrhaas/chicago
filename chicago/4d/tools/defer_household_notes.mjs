#!/usr/bin/env node
/**
 * The household notes leave the boot path (T-2151).
 *
 * WHY. Every first visit loads the 1835 sidecars, and since T-1971 seated the town's
 * households under its roofs those sidecars carry each household's `residents[]` in
 * full: every person's grading note, the household's `why` and its `research_note`.
 * Measured on dev @ 08cf2391 that was **1.07 MB of the 13.652 MB** a first visit
 * downloads — the boot payload was 0.65 MB over its 13 MB budget, and SITE-BUDGET §4b
 * had already named the question to ask first: do the household seats belong in the
 * boot sidecars at all? A card reads them; the scene draws nothing from them.
 *
 * The answer is "the seat does, the paragraphs do not". The display name and the
 * Go-to search read a household's `name` and `relation` (display-name.js), and the
 * card's "Who was here" section draws its people, roles, grades and basis the moment it
 * opens. Only the reasoning behind a `why` toggle is read on demand, and only on a card.
 * So `tools/publish.sh` runs this after it copies the sidecars, and the mirror ships:
 *
 *   data/sidecars/<scene>/<id>.json              the record, its households SLIM:
 *                                                no `why`, no `research_note`, no
 *                                                person's `note` (0.197 MB of 1.07)
 *   data/sidecars/<scene>/households/<id>.json   { id, residents } — the households
 *                                                exactly as the source carries them
 *
 * and the card (main.js `ensureHouseholdNotes`, through `createPopup`'s `onShow`)
 * fetches the second file when a card with households opens, swaps it in and redraws.
 * The source tree is untouched: two dozen Python tools read `data/sidecars/` and keep
 * reading it whole.
 *
 * A household with no `why` key is how the card knows its notes are deferred:
 * `compile_scene.py` writes `why` on every household it seats, so its absence is this
 * transform and nothing else. `--check` holds that too.
 *
 *   node tools/defer_household_notes.mjs [--site DIR]   transform the mirror in place
 *   node tools/defer_household_notes.mjs --check        the shipped form against source
 *   node tools/defer_household_notes.mjs --self-test    the transform on a fixture
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync, mkdirSync, rmSync } from 'node:fs';
import { isDeepStrictEqual } from 'node:util';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');                         // chicago/4d
const SRC = path.join(ROOT, 'data', 'sidecars');
const SITE = path.resolve(ROOT, '..', '..', 'site', '4d', 'data', 'sidecars');

/** The fields a card reads only when its reasoning is asked for. */
const HOUSEHOLD_DEFERRED = ['why', 'research_note'];
const PERSON_DEFERRED = ['note'];

const omit = (o, keys) => Object.fromEntries(Object.entries(o).filter(([k]) => !keys.includes(k)));

/** The household as the boot sidecar carries it. */
export function slimHousehold(h) {
  const out = omit(h, HOUSEHOLD_DEFERRED);
  if (Array.isArray(h.persons)) out.persons = h.persons.map((p) => omit(p, PERSON_DEFERRED));
  return out;
}

/** A record that seats anybody, or null — the only records this touches. */
const seated = (rec) => (rec && typeof rec === 'object' && !Array.isArray(rec)
  && Array.isArray(rec.residents) && rec.residents.length ? rec : null);

/** The two shipped files for one source record: [slim record, households file]. */
export function split(rec) {
  return [
    { ...rec, residents: rec.residents.map(slimHousehold) },
    { id: rec.id, residents: rec.residents },
  ];
}

/** `<scene>/<id>.json` for every top-level sidecar under `dir`. */
function records(dir) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const scene of readdirSync(dir).sort()) {
    const sdir = path.join(dir, scene);
    if (!statSync(sdir).isDirectory()) continue;
    for (const f of readdirSync(sdir).sort()) {
      if (f.endsWith('.json') && statSync(path.join(sdir, f)).isFile()) out.push(`${scene}/${f}`);
    }
  }
  return out;
}

const read = (p) => JSON.parse(readFileSync(p, 'utf8'));
const householdsPath = (dir, rel) => path.join(dir, path.dirname(rel), 'households', path.basename(rel));

function write(site) {
  let n = 0;
  let households = 0;
  for (const rel of records(site)) {
    const rec = seated(read(path.join(site, rel)));
    if (!rec) continue;
    const [slim, full] = split(rec);
    const out = householdsPath(site, rel);
    mkdirSync(path.dirname(out), { recursive: true });
    writeFileSync(out, JSON.stringify(full));
    writeFileSync(path.join(site, rel), JSON.stringify(slim));
    n += 1;
    households += rec.residents.length;
  }
  console.log(`household notes deferred: ${households} household(s) on ${n} record(s) → `
    + `sidecars/<scene>/households/<id>.json`);
}

function check(src, site) {
  const problems = [];
  let n = 0;
  const expected = new Set();
  for (const rel of records(src)) {
    const rec = seated(read(path.join(src, rel)));
    if (!rec) continue;
    n += 1;
    const [slim, full] = split(rec);
    const hrel = path.join(path.dirname(rel), 'households', path.basename(rel));
    expected.add(hrel);
    if (rec.residents.some((h) => !Object.hasOwn(h, 'why'))) {
      problems.push(`${rel}: a seated household has no \`why\` in the SOURCE, so the card would read it as deferred`);
    }
    const shipped = path.join(site, rel);
    if (!existsSync(shipped)) { problems.push(`${rel}: not in the mirror`); continue; }
    if (!isDeepStrictEqual(read(shipped), slim)) problems.push(`${rel}: the shipped record is not its source with the household notes taken out`);
    const hfile = path.join(site, hrel);
    if (!existsSync(hfile)) { problems.push(`${hrel}: missing — this record's notes ship nowhere`); continue; }
    if (!isDeepStrictEqual(read(hfile), full)) problems.push(`${hrel}: not the source's households, value for value`);
  }
  for (const scene of existsSync(site) ? readdirSync(site) : []) {
    const hdir = path.join(site, scene, 'households');
    if (!existsSync(hdir)) continue;
    for (const f of readdirSync(hdir)) {
      const hrel = path.join(scene, 'households', f);
      if (!expected.has(hrel)) problems.push(`${hrel}: shipped, but no source record seats a household`);
    }
  }
  if (problems.length) {
    console.error(`DEFERRED HOUSEHOLD NOTES: ${problems.length} problem(s)`);
    for (const p of problems.slice(0, 12)) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`deferred household notes: ${n} record(s) ship slim, and their households ship whole beside them`);
}

function selfTest() {
  const rec = {
    id: 'x', name: 'X',
    residents: [{ name: 'The X household', relation: 'lived here', why: 'w', research_note: 'r', basis: 'b',
      sources: ['s'], persons: [{ name: 'A', relationship: 'head', grade: 'attested', note: 'n' }] }],
  };
  const [slim, full] = split(rec);
  const h = slim.residents[0];
  const fails = [];
  if (Object.hasOwn(h, 'why') || Object.hasOwn(h, 'research_note') || Object.hasOwn(h.persons[0], 'note')) fails.push('a deferred field stayed on the boot record');
  if (h.basis !== 'b' || h.name !== 'The X household' || h.persons[0].grade !== 'attested') fails.push('a field the card draws at once was taken off');
  if (!isDeepStrictEqual(full.residents, rec.residents)) fails.push('the households file is not the source');
  if (rec.residents[0].why !== 'w' || rec.residents[0].persons[0].note !== 'n') fails.push('the transform mutated its input');
  if (seated({ id: 'y', residents: [] }) || seated([])) fails.push('a record seating nobody would be split');
  if (fails.length) { for (const f of fails) console.error(`self-test | FAIL ${f}`); process.exit(1); }
  console.log('self-test | ok: notes leave the boot record, the card\'s fields stay, the households file is the source');
}

const argv = process.argv.slice(2);
if (argv.includes('--self-test')) selfTest();
else if (argv.includes('--check')) check(SRC, SITE);
else {
  const i = argv.indexOf('--site');
  const site = i >= 0 ? path.resolve(argv[i + 1]) : SITE;
  for (const scene of existsSync(site) ? readdirSync(site) : []) {
    const hdir = path.join(site, scene, 'households');
    if (existsSync(hdir)) rmSync(hdir, { recursive: true });
  }
  write(site);
}

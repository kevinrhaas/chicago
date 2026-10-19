#!/usr/bin/env node
/**
 * The reader's overlay, applied by the page exactly as the gate applies it (T-2825).
 *
 *   node tools/test_reader_text.mjs          the smaller families, compiled to a scratch folder
 *   node tools/test_reader_text.mjs --all    every family, and then the cards themselves: every
 *                                            household card, every building card in every scene
 *                                            and the plants and wildlife topics, rendered by the
 *                                            page's own functions and read as a person reads them
 *                                            (check.sh runs this; about forty seconds)
 *   node tools/test_reader_text.mjs DIR      an overlay already compiled into DIR (publish's)
 *
 * tools/compile_reader_text.py writes data/reader/<family>.json, and tools/check_visitor_ui.py
 * lints each family's records read through it by readable_text.reader_copy. What a visitor
 * sees is js/reader-text.js applying the same overlay in a browser, so this holds the two to
 * one another on the committed data, not on fixtures:
 *
 *   1. every entry of every overlay is found by the page: some string in that family's files
 *      hashes, in JavaScript, to the entry's key (the CRC, the UTF-8 length and the prose
 *      rule agree across the two languages);
 *   2. every string the page rewrites comes out free of a link, a file path, an id, a ticket
 *      number and the words "tier", "ticket" and "order book" (fallback-summary.js's lint,
 *      the twin of compile_summaries.lint_string);
 *   3. the newspaper rule `nameOf` holds agrees with the names the compiler wrote;
 *   4. a record is never changed by being said: `readerCopy` returns a copy;
 *   5. (with --all) what the cards RENDER carries none of them either, in its text and its
 *      tooltips — the bare ids a renderer prints itself (a source id on a grade summary, a
 *      record id on a research row, a stage code), which no data lint can see.
 */
import { readFileSync, readdirSync, mkdtempSync, rmSync, existsSync } from 'node:fs';
import os from 'node:os';
import { execFileSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { readerKey, readerCopy, nameOf } from '../renderers/web/js/reader-text.js';
import { visitorTextProblems } from '../renderers/web/js/fallback-summary.js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const COMPILER = path.join(ROOT, 'tools/compile_reader_text.py');
// The households and the 1835 cards are the two big families; the default run leaves them to
// --all (and to the gate's lint, which reads every family's records through the same rewrite).
const SMALL = ['flora', 'fauna', 'residents_index', 'businesses', 'structures_1812', 'structures_1904',
  'jaunts_1812', 'jaunts_1835', 'jaunts_1904'];
const args = process.argv.slice(2);
const given = args.find((a) => !a.startsWith('--'));
let families = JSON.parse(execFileSync('python3', [COMPILER, '--list'],
  { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 << 20 }));
if (!args.includes('--all') && !given) {
  families = Object.fromEntries(Object.entries(families).filter(([k]) => SMALL.includes(k)));
}
let dir = given ? path.resolve(given) : null;
let scratch = null;
if (!dir) {
  scratch = mkdtempSync(path.join(os.tmpdir(), 'reader-text-'));
  dir = scratch;
  execFileSync('python3', [COMPILER, '--out', dir, ...Object.keys(families).flatMap((f) => ['--family', f])],
    { cwd: ROOT, encoding: 'utf8', stdio: ['ignore', 'ignore', 'inherit'] });
}
process.on('exit', () => { if (scratch && existsSync(scratch)) rmSync(scratch, { recursive: true, force: true }); });
const WORDS = /\btiers?\b|\btickets?\b|\border[\s-]+books?\b/i;

let fails = 0;
const expect = (ok, what) => { console.log(`   ${ok ? 'ok  ' : 'FAIL'} ${what}`); if (!ok) fails++; };

// Every string with the key it sits under: a one-token id under `claim_id` is the data's even
// where the same token under `locator` is a sentence the overlay says (reader-text.js).
function strings(v, out, key = null) {
  if (typeof v === 'string') out.push([v, key]);
  else if (Array.isArray(v)) v.forEach((x) => strings(x, out, key));
  else if (v && typeof v === 'object') Object.entries(v).forEach(([k, x]) => strings(x, out, k));
  return out;
}
const PROSE_KEYS = new Set(['note', 'locator']);
const isProse = ([s, key]) => /\S\s+\S/.test(s) || (PROSE_KEYS.has(key) && s.trim() !== '');

for (const [family, files] of Object.entries(families)) {
  const overlay = JSON.parse(readFileSync(path.join(dir, `${family}.json`), 'utf8'));
  const keys = new Set(Object.keys(overlay.edits || {}));
  const found = new Set();
  const left = [];
  let rewritten = 0;
  let unchanged = true;
  for (const rel of files) {
    const doc = JSON.parse(readFileSync(path.join(ROOT, rel), 'utf8'));
    const before = JSON.stringify(doc);
    const raw = strings(doc, []);
    const said = strings(readerCopy(doc, overlay), []);
    if (JSON.stringify(doc) !== before) unchanged = false;
    raw.forEach((pair, i) => {
      const k = readerKey(pair[0]);
      if (!keys.has(k) || !isProse(pair)) return;
      found.add(k);
      rewritten++;
      const out = said[i][0];
      const p = visitorTextProblems(out);
      if (p.length || WORDS.test(out)) left.push(`${rel}: ${p[0] ?? out.match(WORDS)[0]} — ${out.slice(0, 100)}`);
    });
  }
  const missing = [...keys].filter((k) => !found.has(k));
  expect(missing.length === 0, `${family}: the page finds all ${keys.size} of the overlay's entries in its records`
    + (missing.length ? ` (${missing.length} not found, e.g. ${missing[0]})` : ''));
  expect(left.length === 0, `${family}: the ${rewritten} strings the page rewrites carry no ticket, id or path`
    + (left.length ? ` — ${left[0]}` : ''));
  expect(unchanged, `${family}: saying a record for a reader leaves the record itself as it was`);
  for (const [tok, name] of Object.entries(overlay.names || {})) {
    // Where the compiler fell back on the newspaper rule (no source record names the issue),
    // the page's own fallback must say it the same way.
    if (/^[a-z]+(?:_[a-z]+)*_1[78]\d\d_\d\d_\d\d(?:#c\d+)?$/.test(tok) && /^the .+ of \d{4}-\d\d-\d\d$/.test(name)
      && nameOf(tok) !== name) {
      expect(false, `${family}: nameOf(${tok}) is "${nameOf(tok)}", the compiler wrote "${name}"`);
      break;
    }
  }
}
expect(nameOf('chicago_democrat_1834_07_02#c048') === 'the Chicago Democrat of 1834-07-02',
  'a newspaper notice is its paper and its date');

// ---- 5. the cards, rendered ------------------------------------------------------------
if (args.includes('--all') || given) {
  const R = (p) => JSON.parse(readFileSync(path.join(ROOT, p), 'utf8'));
  const ov = (f) => JSON.parse(readFileSync(path.join(dir, `${f}.json`), 'utf8'));
  const js = (m) => import(path.join(ROOT, 'renderers/web/js', m));
  const decode = (t) => t.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'");
  const read = (html) => [html.replace(/<[^>]+>/g, ' '),
    ...[...html.matchAll(/\s(?:title|aria-label)="([^"]*)"/g)].map((m) => m[1])].map(decode);
  const leaksIn = (html) => read(html).flatMap((t) => [...visitorTextProblems(t),
    ...[...t.matchAll(new RegExp(WORDS.source, 'gi'))].map((m) => `the word "${m[0]}"`)]);
  const tally = (what, n) => {
    const r = { what, cards: 0, leaks: [] };
    return { r, add(html) { r.cards++; const l = leaksIn(html); if (l.length) r.leaks.push(...l.slice(0, 2)); },
      done() { expect(r.cards >= n && !r.leaks.length, `${what}: ${r.cards} rendered, no ticket, id or path in what they show`
        + (r.leaks.length ? ` — ${r.leaks.length}, e.g. ${r.leaks[0]}` : '')); } };
  };

  // A person's card and the household browser: householdHtml, with the joins said.
  const res = await js('residents.js');
  const roverlay = ov('residents');
  const cites = new Map(Object.entries(R('data/sidecars/1835/residents_sources.json').citations || {}));
  const byPerson = (rows) => new Map((rows || []).map((r) => [r.person_id, r]));
  const withheld = new Map();
  for (const row of R('data/residents/person_facts_withheld.json').rows || []) {
    if (!withheld.has(row.person_id)) withheld.set(row.person_id, []);
    withheld.get(row.person_id).push(row);
  }
  const dirs = R('data/residents/directories.json');
  const cov = R('data/residents/employment_coverage.json');
  const said = res.sayJoins({
    citationsById: cites, researchByPerson: byPerson(R('data/residents/research_pilot.json').reviews),
    directoryByPerson: new Map((dirs.people || []).map((r) => [r.person_id, { ...r, standard: dirs.standard }])),
    withheldByPerson: withheld, seatingByPerson: byPerson(R('data/residents/reconstructed_seating.json').rows),
    coverage: { byPerson: byPerson(cov.rows), words: cov.vocabulary?.reasons || {}, placed: new Set(), counts: {}, model: {} },
  }, roverlay);
  const ladder = readerCopy(R('data/residents/index.json'), ov('residents_index')).vocabulary?.ladder_rules || [];
  const people = tally('household cards', 1000);
  for (const f of readdirSync(path.join(ROOT, 'data/residents/households')).filter((x) => x.endsWith('.json'))) {
    people.add(res.householdHtml(readerCopy(R(`data/residents/households/${f}`), roverlay), said.citationsById,
      said.researchByPerson, said.directoryByPerson, ladder, null, said.withheldByPerson, said.seatingByPerson, said.coverage));
  }
  people.done();

  // A building's card, every tab of it, in every scene, and the title it leads with.
  const doc = globalThis.document;
  globalThis.document = { documentElement: { classList: { add() {}, remove() {} } } };
  const { createPopup } = await js('popup.js');
  const { displayName } = await js('display-name.js');
  for (const scene of ['1812', '1835', '1904']) {
    const root = { innerHTML: '', addEventListener() {}, setAttribute() {}, removeAttribute() {}, dispatchEvent() {} };
    const popup = createPopup(root, {});
    popup.setReader(ov(`structures_${scene}`));
    const cards = tally(`building cards, ${scene}`, 40);
    const titles = tally(`building titles, ${scene}`, 40);
    for (const f of readdirSync(path.join(ROOT, 'data/sidecars', scene)).filter((x) => x.endsWith('.json'))) {
      const sc = R(`data/sidecars/${scene}/${f}`);
      if (!sc?.attributes || !sc.phase) continue;
      popup.show({ id: sc.id, sidecar: sc });
      cards.add(root.innerHTML);
      const title = displayName(sc, sc.id).title;
      titles.add(`<h2>${title}</h2>`);
      if (/\bK\d\d\b|map-led|district draft|refined by|frontage assembly/i.test(title)) titles.r.leaks.push(`the production step in "${title}"`);
    }
    cards.done();
    titles.done();
  }
  globalThis.document = doc;

  // The plants and the wildlife topics, mounted from the committed records.
  const fetched = globalThis.fetch;
  globalThis.fetch = async (url) => {
    const rel = new URL(url).pathname.replace(/^\/data\//, '');
    const full = rel.startsWith('reader/') ? path.join(dir, rel.slice(7)) : path.join(ROOT, 'data', rel);
    if (!existsSync(full)) return { ok: false, status: 404, statusText: 'Not Found', json: async () => ({}) };
    return { ok: true, status: 200, json: async () => JSON.parse(readFileSync(full, 'utf8')) };
  };
  for (const [what, mod, fn] of [['the plants topic', 'plants.js', 'mountPlants'], ['the wildlife topic', 'fauna.js', 'mountFauna']]) {
    const mount = { innerHTML: '', removeAttribute() {} };
    const problems = [];
    await (await js(mod))[fn]({ mount, sceneId: '1835', dataBase: new URL('http://reader.test/data/'), problems });
    const t = tally(what, 1);
    t.add(mount.innerHTML);
    if (!/<details/.test(mount.innerHTML) || problems.length) t.r.leaks.push(`it did not render (${problems[0] ?? 'empty'})`);
    t.done();
  }
  globalThis.fetch = fetched;
}
console.log(fails ? `\nREADER TEXT FAIL — ${fails}` : '\nREADER TEXT PASS — the page says every record the way the gate reads it');
process.exit(fails ? 1 : 0);

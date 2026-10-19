#!/usr/bin/env node
/**
 * The reader's overlay, applied by the page exactly as the gate applies it (T-2825).
 *
 *   node tools/test_reader_text.mjs          the six smaller families, compiled to a scratch folder
 *   node tools/test_reader_text.mjs --all    every family (the households and the 1835 cards
 *                                            too: half a minute more, and the same mechanism)
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
 *   4. a record is never changed by being said: `readerCopy` returns a copy.
 */
import { readFileSync, mkdtempSync, rmSync, existsSync } from 'node:fs';
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

function strings(v, out) {
  if (typeof v === 'string') out.push(v);
  else if (Array.isArray(v)) v.forEach((x) => strings(x, out));
  else if (v && typeof v === 'object') Object.values(v).forEach((x) => strings(x, out));
  return out;
}

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
    raw.forEach((s, i) => {
      const k = readerKey(s);
      if (!keys.has(k)) return;
      found.add(k);
      rewritten++;
      const p = visitorTextProblems(said[i]);
      if (p.length || WORDS.test(said[i])) left.push(`${rel}: ${p[0] ?? said[i].match(WORDS)[0]} — ${said[i].slice(0, 100)}`);
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
console.log(fails ? `\nREADER TEXT FAIL — ${fails}` : '\nREADER TEXT PASS — the page says every record the way the gate reads it');
process.exit(fails ? 1 : 0);

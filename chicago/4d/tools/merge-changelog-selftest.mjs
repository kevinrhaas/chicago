#!/usr/bin/env node
/**
 * The changelog merge driver's assertions, and proof they still fire when broken.
 *
 * The cases are the ones this repo has actually paid for: the everyday both-sides-
 * prepend (three hand repairs on 2026-09-04), the entry-swallowing shape union
 * produced five times on 2026-08-15, and the two entries on `dev` that close on
 * the same line as their last item.
 */
import { execFileSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const DRIVER = path.join(HERE, 'merge-changelog.mjs');

let pass = 0; let fail = 0;
const ok = (c, w) => { if (c) { pass++; console.log(`  ok    ${w}`); } else { fail++; console.log(`  FAIL  ${w}`); } };

function run(base, ours, theirs) {
  const dir = mkdtempSync(path.join(tmpdir(), 'mc-'));
  const O = path.join(dir, 'base'); const A = path.join(dir, 'ours'); const B = path.join(dir, 'theirs');
  writeFileSync(O, base); writeFileSync(A, ours); writeFileSync(B, theirs);
  let code = 0;
  try { execFileSync('node', [DRIVER, O, A, B, 'changelog.js'], { stdio: ['ignore', 'ignore', 'ignore'] }); }
  catch (e) { code = e.status ?? 1; }
  const text = readFileSync(A, 'utf8');
  rmSync(dir, { recursive: true, force: true });
  return { code, text };
}

const HEAD = 'export const CHANGELOG = [ // newest first\n';
const TAIL = '];\n\nexport const LATEST_VERSION = CHANGELOG[0].v;\n';
const entry = (v, title, close = '\n    ] },') =>
  `  { v: ${v}, title: '${title}', kind: 'fix', ts: '2026-01-0${v % 9}T00:00:00.000Z', date: 'Jan ${v}, 2026',\n`
  + `    items: [\n      'item for ${title}.',${close}`;
const file = (...es) => HEAD + es.join('\n') + '\n' + TAIL;
const titles = (t) => [...t.matchAll(/title:\s*'((?:[^'\\]|\\.)*)'/g)].map((m) => m[1]);
const vs = (t) => [...t.matchAll(/^  \{ v: ([^,]+),/gm)].map((m) => m[1]);

console.log('\n\x1b[1m== the changelog merge driver\x1b[0m');

// 1. THE EVERYDAY CASE: both sides prepend. This is the one that conflicts on
//    every branch and that union silently corrupted.
{
  const base = file(entry(10, 'older'));
  const ours = file(entry(11, 'ours new'), entry(10, 'older'));
  const theirs = file(entry(11, 'theirs new'), entry(10, 'older'));
  const r = run(base, ours, theirs);
  ok(r.code === 0, 'both sides prepend an entry — resolved, not conflicted');
  ok(titles(r.text).join('|') === 'ours new|theirs new|older', '...ours on top, theirs kept, base beneath');
  ok(vs(r.text)[0] === 'null', "...ours is UNSTAMPED so the stamper numbers it");
  ok(vs(r.text)[1] === '11', "...theirs keeps the number it already shipped with");
  ok(!/ts: '2026-01-02T/.test(r.text.split('\n')[1]), '...and ours loses its guessed timestamp');
}

// 2. The shape that broke union: no entry may be spliced into another. Every
//    entry in the result must still carry its own items block.
{
  const base = file(entry(10, 'older'));
  const ours = file(entry(11, 'ours new'), entry(10, 'older'));
  const theirs = file(entry(11, 'theirs new'), entry(10, 'older'));
  const r = run(base, ours, theirs);
  const opens = (r.text.match(/items: \[/g) || []).length;
  const closes = (r.text.match(/\] \},/g) || []).length;
  ok(opens === 3 && closes === 3, 'every entry keeps its own items block — none is swallowed');
}

// 3. An entry that closes on the same line as its last item — two on dev do.
{
  const odd = `  { v: 12, title: 'odd close', kind: 'fix', ts: '2026-01-04T00:00:00.000Z', date: 'Jan 12, 2026',\n    items: [\n      'only item.',    ] },`;
  const base = file(odd);
  const ours = file(entry(13, 'ours new'), odd);
  const theirs = file(entry(13, 'theirs new'), odd);
  const r = run(base, ours, theirs);
  ok(r.code === 0, 'an entry closing on its last item line is handled');
  ok(titles(r.text).includes('odd close'), '...and survives the merge');
  ok(titles(r.text).length === 3, '...with nothing lost or doubled');
}

// 4. Only one side shipped an entry — the trivial merge.
{
  const base = file(entry(10, 'older'));
  const ours = file(entry(10, 'older'));
  const theirs = file(entry(11, 'theirs new'), entry(10, 'older'));
  const r = run(base, ours, theirs);
  ok(r.code === 0 && titles(r.text).join('|') === 'theirs new|older', 'only theirs shipped — take theirs whole');
  ok(vs(r.text)[0] === '11', '...and nothing is needlessly unstamped');
}

// 5. The same entry on both sides (a cherry-pick, or the same run twice).
{
  const base = file(entry(10, 'older'));
  const both = entry(11, 'same entry');
  const r = run(base, file(both, entry(10, 'older')), file(both, entry(10, 'older')));
  ok(r.code === 0, 'the same new entry on both sides is not an error');
  ok(titles(r.text).filter((t) => t === 'same entry').length === 1, '...it appears exactly once');
}

console.log('\n\x1b[1m== …and the refusals still fire\x1b[0m');

// 6. Both sides edited ONE EXISTING entry differently — union's silent case.
{
  const base = file(entry(10, 'older'));
  const ours = file(entry(10, 'older').replace('item for older.', 'OURS rewrote this.'));
  const theirs = file(entry(10, 'older').replace('item for older.', 'THEIRS rewrote this.'));
  const r = run(base, ours, theirs);
  ok(r.code !== 0, 'both sides editing one shipped entry differently is REFUSED');
}

// 7. Garbage in is refused, not written through.
{
  const r = run('not a changelog', 'nor is this', 'nor this');
  ok(r.code !== 0, 'an unparseable file is REFUSED rather than merged');
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);

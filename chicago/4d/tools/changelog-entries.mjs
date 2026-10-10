#!/usr/bin/env node
/**
 * changelog-entries.mjs — a pull request's What's-New entry, written as a file of its
 * own, and folded into renderers/web/js/changelog.js after it lands on `dev`.
 *
 * WHY THIS EXISTS (owner, 2026-10-10, on "PRs seem to be building"). Every pull
 * request used to prepend its entry to the top of changelog.js. Two open PRs therefore
 * always edited the same line, so the moment one landed every other open PR read
 * `dirty` on GitHub. GitHub never runs the repo's merge drivers (T-0833), so the
 * driver that resolves this locally never helped there. Each PR then needed a lap and
 * a fresh ~12-minute gate, and with ten steward lanes a sibling landed inside that
 * window more often than not. Measured that night: #607, #608, #610 and #613 were
 * finished and gated green, some three times over, and lost every merge to that one
 * line. The queue grew while dev took 32 merges in twelve hours.
 *
 * So a PR no longer writes changelog.js at all. It adds ONE new file:
 *
 *     chicago/4d/changelog.d/<ticket or topic>.json
 *     { "title": "…", "kind": "fix", "items": ["…", "…"] }
 *
 * A new file never conflicts with a sibling's new file. After the merge,
 * `.github/workflows/chicago-4d-changelog-fold.yml` runs this tool with `--fold` on
 * `dev`: each pending file becomes an entry at the top of changelog.js, in the order
 * the files landed, with `v: null, ts: '', date: ''`. The repo's own stamper then
 * numbers and stamps them, exactly as it always has, and the files are deleted. The
 * published file, its shape, its URL and its numbering rules do not change.
 *
 *   node tools/changelog-entries.mjs --check       every pending file is well formed
 *                                                  and inside the What's-New budget
 *   node tools/changelog-entries.mjs --fold        fold them into changelog.js, stamp,
 *                                                  delete the files (dev only)
 *   node tools/changelog-entries.mjs --self-test   the fold, in a sandbox
 *
 * A PR that still edits changelog.js the old way keeps working; it just keeps the old
 * conflict too.
 */
import { readFileSync, writeFileSync, readdirSync, existsSync, rmSync, mkdtempSync,
  mkdirSync, cpSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');                       // chicago/4d

/** Where pending entries live, relative to chicago/4d. */
export const ENTRY_DIR = 'changelog.d';

/**
 * The What's-New budget, shared with check-changelog.mjs so the two cannot drift.
 * Measured 2026-08-15 (see check-changelog.mjs § LENGTH). Warn at the budget, fail
 * at the ceiling.
 */
export const LIMITS = { titleWords: 12, items: 6, words: 450 };
export const CEILING = 1.5;

/** Every kind the published history carries; the first four are the ones to use. */
export const KINDS = ['feature', 'fix', 'change', 'chore',
  'add', 'feat', 'improvement', 'improve', 'polish'];

const words = (s) => String(s ?? '').trim().split(/\s+/).filter(Boolean).length;

/**
 * Hold one entry to the What's-New budget. Returns { problems, notes }.
 * `at` names the entry in the messages.
 */
export function budget(entry, at) {
  const problems = [];
  const notes = [];
  const iw = (entry.items || []).reduce((n, i) => n + words(i), 0);
  const one = (name, got, limit) => {
    if (got > Math.ceil(limit * CEILING)) {
      problems.push(`${at}: ${name} is ${got}, over the hard ceiling of `
        + `${Math.ceil(limit * CEILING)} (budget ${limit}). What's-New is for a visitor asking `
        + 'what changed in the town; the reasoning belongs in the PR body and STATUS.md, which '
        + 'have no limit. Cut the entry, do not raise this number.');
    } else if (got > limit) {
      notes.push(`${at}: ${name} is ${got}, over the budget of ${limit} — allowed, but `
        + 'the last 20 entries already drifted 78 % longer than the first 20. Trim if you can.');
    }
  };
  one('title length in words', words(entry.title), LIMITS.titleWords);
  one('item count', (entry.items || []).length, LIMITS.items);
  one('total words', iw, LIMITS.words);
  return { problems, notes };
}

/** The shape of one pending file. Returns a list of problems. */
export function validate(entry, at) {
  const problems = [];
  if (entry === null || typeof entry !== 'object' || Array.isArray(entry)) {
    return [`${at}: must be a JSON object { "title", "kind", "items" }`];
  }
  const allowed = new Set(['title', 'kind', 'items']);
  for (const k of Object.keys(entry)) {
    if (!allowed.has(k)) {
      problems.push(`${at}: unexpected key "${k}" — v, ts and date are assigned when the `
        + 'entry is folded on dev, never written by hand');
    }
  }
  if (typeof entry.title !== 'string' || !entry.title.trim()) problems.push(`${at}: no title`);
  if (!KINDS.includes(entry.kind)) {
    problems.push(`${at}: kind must be one of ${KINDS.slice(0, 4).join(', ')} (got ${JSON.stringify(entry.kind)})`);
  }
  if (!Array.isArray(entry.items) || !entry.items.length) {
    problems.push(`${at}: no items`);
  } else {
    for (const it of entry.items) {
      if (typeof it !== 'string' || !it.trim()) problems.push(`${at}: an item is not a non-empty string`);
      // A `//` inside item text breaks naive comment-stripping in some parsers.
      else if (it.includes('//')) problems.push(`${at}: an item contains "//"`);
    }
  }
  for (const s of [entry.title, ...(Array.isArray(entry.items) ? entry.items : [])]) {
    if (typeof s === 'string' && /[\r\n]/.test(s)) problems.push(`${at}: a line break inside the text`);
  }
  return problems;
}

/** One JS string literal in the changelog's own style: single-quoted. */
export function lit(s) {
  return `'${String(s)
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/\u2028/g, '\\u2028')
    .replace(/\u2029/g, '\\u2029')}'`;
}

/** An entry as the text the changelog literal carries, unnumbered and unstamped. */
export function entryText(entry) {
  return `  { v: null, ts: '', date: '', title: ${lit(entry.title)}, kind: ${lit(entry.kind)},\n`
    + '    items: [\n'
    + entry.items.map((i) => `      ${lit(i)},\n`).join('')
    + '    ] },\n';
}

/**
 * The pending files under `root`/changelog.d, oldest landing first. "Landing" is the
 * commit time of the commit that added the file on the checked-out history; a file
 * git does not know yet sorts last (it is the newest). Ties break by name.
 */
export function pending(root = ROOT) {
  const dir = path.join(root, ENTRY_DIR);
  if (!existsSync(dir)) return [];
  const names = readdirSync(dir).filter((n) => n.endsWith('.json')).sort();
  const landed = (name) => {
    const r = spawnSync('git', ['log', '--diff-filter=A', '--format=%ct', '-1', '--',
      path.join(ENTRY_DIR, name)], { cwd: root, encoding: 'utf8' });
    const t = Number((r.stdout || '').trim());
    return Number.isFinite(t) && t > 0 ? t : Infinity;
  };
  return names
    .map((name) => ({ name, file: path.join(dir, name), at: landed(name) }))
    .sort((a, b) => (a.at - b.at) || a.name.localeCompare(b.name));
}

/** Read and validate every pending file. Returns { entries, problems, notes }. */
export function readPending(root = ROOT, published = []) {
  const entries = [];
  const problems = [];
  const notes = [];
  const titles = new Map(published.map((e) => [String(e.title ?? ''), e.v]));
  for (const p of pending(root)) {
    const at = `${ENTRY_DIR}/${p.name}`;
    let entry;
    try {
      entry = JSON.parse(readFileSync(p.file, 'utf8'));
    } catch (err) {
      problems.push(`${at}: not valid JSON — ${err.message}`);
      continue;
    }
    const shape = validate(entry, at);
    problems.push(...shape);
    if (shape.length) continue;
    const b = budget(entry, at);
    problems.push(...b.problems);
    notes.push(...b.notes);
    const t = entry.title;
    if (titles.has(t)) {
      problems.push(`${at}: repeats the title of ${titles.get(t) === null ? 'another pending entry'
        : `v${titles.get(t)}`} ("${t.slice(0, 60)}") — the merge driver and the contract check `
        + 'identify an entry by its title, so give this one its own');
    } else titles.set(t, null);
    entries.push({ ...p, entry });
  }
  return { entries, problems, notes };
}

/**
 * Fold the pending files under `root` into its changelog.js: prepend them (newest on
 * top), run the stamper, delete the files. Returns { folded, out }.
 */
export function fold(root = ROOT, { stamp = true } = {}) {
  const file = path.join(root, 'renderers', 'web', 'js', 'changelog.js');
  const { entries, problems } = readPending(root);
  if (problems.length) {
    const err = new Error(`refusing to fold — ${problems.length} problem(s):\n  - ${problems.join('\n  - ')}`);
    err.problems = problems;
    throw err;
  }
  if (!entries.length) return { folded: [], out: '' };
  const src = readFileSync(file, 'utf8');
  const head = src.match(/^export const CHANGELOG = \[[^\n]*\n/);
  if (!head) throw new Error('changelog.js does not open with `export const CHANGELOG = [` on its first line');
  // Oldest landing first in `entries`; the file is newest-first, so the last to land
  // goes on top.
  const block = [...entries].reverse().map((e) => entryText(e.entry)).join('');
  writeFileSync(file, head[0] + block + src.slice(head[0].length));
  let out = '';
  if (stamp) {
    const r = spawnSync('node', [path.join(root, 'tools', 'stamp-changelog.mjs')],
      { cwd: root, encoding: 'utf8' });
    out = `${r.stdout ?? ''}${r.stderr ?? ''}`;
    if (r.status !== 0) {
      writeFileSync(file, src);                   // leave the tree as it was
      throw new Error(`the stamper refused the folded file:\n${out}`);
    }
  }
  for (const e of entries) rmSync(e.file);
  return { folded: entries.map((e) => ({ name: e.name, title: e.entry.title })), out };
}

/* ------------------------------------------------------------------------------- */

async function publishedEntries() {
  try {
    const { CHANGELOG } = await import(pathToFileURL(path.join(ROOT, 'renderers', 'web', 'js', 'changelog.js')).href);
    return Array.isArray(CHANGELOG) ? CHANGELOG : [];
  } catch {
    return [];                                     // check-changelog.mjs reports a broken file
  }
}

async function cliCheck() {
  const { entries, problems, notes } = readPending(ROOT, await publishedEntries());
  for (const n of notes) console.warn(`  note  ${n}`);
  if (problems.length) {
    console.error('changelog entries FAILED:');
    for (const p of problems) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(entries.length
    ? `changelog entries OK — ${entries.length} pending in ${ENTRY_DIR}/, folded into changelog.js on dev after merge`
    : `changelog entries OK — none pending in ${ENTRY_DIR}/`);
}

function cliFold() {
  let r;
  try {
    r = fold(ROOT);
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
  if (!r.folded.length) {
    console.log(`changelog fold: nothing pending in ${ENTRY_DIR}/`);
    return;
  }
  if (r.out.trim()) console.log(r.out.trim());
  for (const f of r.folded) console.log(`folded ${ENTRY_DIR}/${f.name} — "${f.title}"`);
}

function selfTest() {
  let failures = 0;
  const check = (what, ok, detail) => {
    console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
    if (!ok) failures += 1;
  };
  const env = { ...process.env, GIT_AUTHOR_NAME: 't', GIT_AUTHOR_EMAIL: 't@t',
    GIT_COMMITTER_NAME: 't', GIT_COMMITTER_EMAIL: 't@t' };
  const box = mkdtempSync(path.join(tmpdir(), 'clfold-'));
  try {
    mkdirSync(path.join(box, 'tools'), { recursive: true });
    mkdirSync(path.join(box, 'renderers', 'web', 'js'), { recursive: true });
    mkdirSync(path.join(box, ENTRY_DIR), { recursive: true });
    for (const t of ['stamp-changelog.mjs', 'changelog_shim.mjs']) {
      cpSync(path.join(HERE, t), path.join(box, 'tools', t));
    }
    const cl = path.join(box, 'renderers', 'web', 'js', 'changelog.js');
    writeFileSync(cl, "export const CHANGELOG = [ // newest first\n"
      + "  { v: 7, ts: '2026-10-01T00:00:00.000Z', date: 'Sep 30, 2026, 7:00 PM CT', title: 'Old', kind: 'fix',\n"
      + "    items: [\n      'An old item.',\n    ] },\n];\n"
      + 'export const LATEST_VERSION = CHANGELOG[0].v;\n');
    const g = (...a) => spawnSync('git', a, { cwd: box, env, encoding: 'utf8' });
    g('init', '-q', '-b', 'dev');
    g('add', '-A');
    g('commit', '-q', '-m', 'base', '--date', '2026-10-01T00:00:00Z');
    const put = (name, entry, when) => {
      writeFileSync(path.join(box, ENTRY_DIR, name), JSON.stringify(entry, null, 2));
      g('add', '-A');
      spawnSync('git', ['commit', '-q', '-m', `land ${name}`],
        { cwd: box, encoding: 'utf8', env: { ...env, GIT_COMMITTER_DATE: when, GIT_AUTHOR_DATE: when } });
    };
    // Landed in the order b, a: name order must NOT decide.
    put('T-0002-b.json', { title: 'Landed first', kind: 'fix', items: ["Bob's lot, with a \\ and an apostrophe."] },
      '2026-10-02T00:00:00Z');
    put('T-0001-a.json', { title: 'Landed second', kind: 'change', items: ['One.', 'Two.'] },
      '2026-10-03T00:00:00Z');

    const r = readPending(box);
    check('two well-formed files read clean', !r.problems.length, r.problems.join('; '));
    check('…oldest landing first, not name order',
      r.entries.map((e) => e.name).join(',') === 'T-0002-b.json,T-0001-a.json');

    const f = fold(box);
    check('the fold folds both', f.folded.length === 2);
    check('…and deletes the files it folded', readdirSync(path.join(box, ENTRY_DIR)).length === 0);
    const src = readFileSync(cl, 'utf8');
    const vs = [...src.matchAll(/v: (\d+)/g)].map((m) => Number(m[1]));
    check('the stamper numbers them above the shipped top, newest first', vs.join(',') === '9,8,7', vs.join(','));
    check('…the last to land is on top', src.indexOf('Landed second') < src.indexOf('Landed first'));
    check('…every new entry has a ts and a date', !/ts: ''/.test(src) && !/date: ''/.test(src));
    check('…a shipped entry is untouched', src.includes("{ v: 7, ts: '2026-10-01T00:00:00.000Z'"));
    check('quotes and backslashes survive as a loadable literal',
      spawnSync('node', ['--input-type=module', '-e',
        `import(${JSON.stringify(pathToFileURL(cl).href)}).then(m => { if (m.CHANGELOG[1].items[0] !== "Bob's lot, with a \\\\ and an apostrophe.") process.exit(1); })`],
      { encoding: 'utf8' }).status === 0);
    check('a second fold with nothing pending changes nothing',
      fold(box).folded.length === 0 && readFileSync(cl, 'utf8') === src);

    // Refusals.
    const bad = (entry) => validate(entry, 'x').length > 0;
    check('a hand-written v is refused', bad({ v: 10, title: 'T', kind: 'fix', items: ['a'] }));
    check('a missing title is refused', bad({ kind: 'fix', items: ['a'] }));
    check('an unknown kind is refused', bad({ title: 'T', kind: 'misc', items: ['a'] }));
    check('no items is refused', bad({ title: 'T', kind: 'fix', items: [] }));
    check('a "//" in an item is refused', bad({ title: 'T', kind: 'fix', items: ['see https://x'] }));
    check('a line break in an item is refused', bad({ title: 'T', kind: 'fix', items: ['a\nb'] }));
    check('a title over the hard ceiling is refused',
      budget({ title: Array(19).fill('w').join(' '), items: ['a'] }, 'x').problems.length === 1);
    check('…and one merely over the budget only notes it',
      budget({ title: Array(13).fill('w').join(' '), items: ['a'] }, 'x').notes.length === 1);
    writeFileSync(path.join(box, ENTRY_DIR, 'dup.json'), JSON.stringify({ title: 'Old', kind: 'fix', items: ['x'] }));
    check('a title the published file already carries is refused',
      readPending(box, [{ v: 7, title: 'Old' }]).problems.length === 1);
    let refused = false;
    writeFileSync(path.join(box, ENTRY_DIR, 'broken.json'), '{ not json');
    try { fold(box); } catch { refused = true; }
    check('the fold refuses a broken file and folds nothing', refused
      && existsSync(path.join(box, ENTRY_DIR, 'broken.json')) && readFileSync(cl, 'utf8') === src);
  } finally {
    rmSync(box, { recursive: true, force: true });
  }
  console.log(failures ? `\n${failures} FAILED` : '\nchangelog entries self-test: all passed');
  process.exit(failures ? 1 : 0);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  const arg = process.argv[2];
  if (arg === '--check') await cliCheck();
  else if (arg === '--fold') cliFold();
  else if (arg === '--self-test') selfTest();
  else {
    console.error('usage: changelog-entries.mjs --check | --fold | --self-test');
    process.exit(2);
  }
}

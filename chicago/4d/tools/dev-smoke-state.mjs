#!/usr/bin/env node
/**
 * T-0216 — dev's STANDING smoke record, so a branch never re-derives dev's reds.
 *
 *   node tools/dev-smoke-state.mjs                 # ask: what does the record say?
 *   node tools/dev-smoke-state.mjs ask --viewport desktop --stage 3
 *   node tools/dev-smoke-state.mjs record run.log  # fold a local smoke log in
 *   node tools/dev-smoke-state.mjs ci 32689397335  # fold a chicago-4d-smoke.yml run in
 *   node tools/dev-smoke-state.mjs ci              # list that workflow's runs on dev
 *   node tools/dev-smoke-state.mjs hash            # the smoke-relevant tree hash
 *
 * WHY THIS EXISTS. `chicago-4d-check.yml` runs `check.sh` and nothing else, and
 * `chicago-4d-smoke.yml` is dispatch-plus-one-path, so the smoke state of `dev`
 * has been whatever the last agent happened to run in a worktree. The question
 * every branch asks — *"is this red mine, or did I inherit it?"* — was therefore
 * answered by cutting a clean `origin/dev` worktree and paying for the stage
 * again. On 2026-08-27 THREE separate agents each paid that price on the same
 * red, and the red was neither branch's nor dev's: it was the machine (T-0215).
 * A fourth was re-deriving the desktop triangle-ceiling red the same way.
 *
 * THE ANSWER IS A COMMITTED RECORD, NOT A NEW GATE. `.github/workflows/` is
 * outside a steward run's scope (AGENTS.md § How work ships), which is why
 * T-0215 could not build this in its own PR — so the record is fed by the two
 * routes a run already has: the log of a smoke it ran anyway, and the log of a
 * `chicago-4d-smoke.yml` run that already happened. Both go through ONE parser.
 * If the owner later schedules that workflow on `dev`, `ci <id>` is what folds
 * its result in, and nothing here has to change.
 *
 * THE TRAP THE TICKET NAMES, AND HOW EVERY READING ANSWERS IT. *"A result taken
 * on a quiet CI runner does not predict a steward run on a box carrying a dozen
 * agents"* — T-0215's readings differ by a factor of twenty on the same tree. So
 * a reading here is never just pass/fail: it carries the host it was taken on,
 * the CPU count, the load average, its wall clock, and any animation-frame cost
 * the smoke reported. A CI pass does not license ignoring a steward-runner red;
 * it dates it.
 *
 * AND WHAT MAKES A READING *YOURS*. Every reading records `treeHash`, a digest
 * of everything the smoke actually exercises — `renderers/`, `data/`, `assets/`,
 * `tools/smoke_renderer.mjs` and the published mirror `site/chicago/4d/`. If
 * your tree hashes the same as a reading, that reading is a reading OF YOUR
 * TREE: a red in it is inherited, full stop, with no re-run needed. If it does
 * not, the record says so instead of pretending. That is the whole of the
 * ticket's acceptance — answer it from the record, WITHOUT running anything.
 *
 * A RECORD, NEVER A BAR. Nothing here can fail a gate, refuse a merge or excuse
 * a red. It is evidence with its conditions attached, in the shape T-0016's road
 * bands are kept in, and it is read by a human or an agent deciding where to
 * spend the next ten minutes.
 */

import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const APP = path.resolve(HERE, '..');                 // chicago/4d
const REPO = path.resolve(APP, '..', '..');           // the monorepo root
const STATE = path.join(HERE, 'dev-smoke-state.json');

/** Parts of the smoke body. Mirrors `PARTS` in tools/smoke_renderer.mjs. */
const PARTS = 13;

const NOTE =
  'T-0216 — dev\'s standing smoke result, so a branch can answer "is this red mine, or did I '
  + 'inherit it?" from the record instead of re-running the stage on a clean worktree (three '
  + 'agents paid that price on one red on 2026-08-27; T-0215). Written by '
  + 'tools/dev-smoke-state.mjs, which parses a smoke log — local or from a chicago-4d-smoke.yml '
  + 'run. Every reading carries the CONDITIONS it was taken under, because a quiet CI runner '
  + 'does not predict a loaded steward box: T-0215 measured a factor of twenty on one tree. '
  + 'loadavg is sampled when the reading is filed, so it includes the smoke\'s own load. '
  + '`treeHash` digests exactly what the smoke exercises (renderers, data, assets, '
  + 'smoke_renderer.mjs, the published mirror), so a reading whose hash matches yours is a '
  + 'reading OF YOUR TREE. A RECORD, NOT A BAR: nothing here gates anything. THE PART '
  + 'NUMBERS CHANGED ON 2026-08-30 (T-0346): part 4 was cut into 4, 5 and 6 and the old '
  + 'parts 5-9 became 7-11; then T-0173 halved part 7 (8-11 -> 9-12) and T-0170 halved '
  + 'part 10 (11-12 -> 12-13). A reading filed before any of those is labelled in the OLD '
  + 'numbering of its day. Each of those also carries a treeHash that cannot match a tree containing '
  + 'the cut, so `ask` already reports them as not taken on your tree — but read the stage '
  + 'number as dated rather than current.';

// ---------------------------------------------------------------------------
// the smoke-relevant tree hash
// ---------------------------------------------------------------------------

/**
 * Paths, relative to the repo root, whose content can change what the smoke
 * reads. Deliberately WIDER than "what I edited": the point of the hash is that
 * an equal hash licenses skipping a run, so anything it misses is a wrong
 * answer. It is narrower than the whole repo only because `kevinrhaas/custom`
 * is a monorepo of unrelated projects (AGENTS.md § How work ships) and a CAD
 * file landing would otherwise retire every reading here.
 */
const SMOKE_INPUTS = [
  'chicago/4d/renderers',
  'chicago/4d/data',
  'chicago/4d/assets',
  'chicago/4d/tools/smoke_renderer.mjs',
  'site/chicago/4d',
  // THE EXCLUSIONS BELOW ARE LOAD-BEARING, and getting them wrong is how this
  // whole idea fails silently rather than loudly. Each of these files changes on
  // EVERY branch BY CONSTRUCTION, so a hash that included them would differ from
  // dev's before a line of real work was written — and a hash that never matches
  // answers "is this red mine?" with "cannot tell", every time. They are
  // excluded for three DIFFERENT reasons and the difference is the point:
  //
  //  - NOT AN INPUT AT ALL. `ticket.mjs claim` mirrors tickets.json into the
  //    published tree in the first commit of every run (T-0154). Neither
  //    smoke_renderer.mjs nor renderers/web reads it — the walkthrough has no
  //    ticket surface — so dropping it loses nothing.
  //  - AN INPUT, HASHED APART. AGENTS.md requires a changelog entry in every PR,
  //    and the release notes ARE read by the smoke — by PART 8 alone (the
  //    What's-new panel: the unread dot, the entry count, the is-new flagging).
  //    So they get their own hash and are reported against part 8.
  //  - A PUBLISH STAMP, NORMALISED AWAY. `publish.sh` stamps a fresh build id
  //    and clock into build.json and into the gate's build line every time it
  //    runs, which is once per PR minimum. build.json is stamp and nothing else;
  //    the gate page is real smoke input carrying a stamp, so it is hashed with
  //    the stamp normalised out rather than dropped.
  ':(exclude)site/chicago/4d/tickets.json',
  ':(exclude)chicago/4d/renderers/web/js/changelog.js',
  ':(exclude)site/chicago/4d/js/changelog.js',
  ':(exclude)site/chicago/4d/walk/js/changelog.js',
  ':(exclude)site/chicago/4d/build.json',
  ':(exclude)site/chicago/4d/walk/index.html',
];

/** The release notes, hashed on their own — see the note above. */
const CHANGELOG_INPUTS = [
  'chicago/4d/renderers/web/js/changelog.js',
  'site/chicago/4d/js/changelog.js',
  'site/chicago/4d/walk/js/changelog.js',
];

/** The parts whose checks actually read the release notes. Part 8 until T-0346
 * renumbered the tail of the body, then part 10 until T-0173 halved part 7, then
 * part 11 until T-0170 halved part 10; What's-new is part 12 now. */
const CHANGELOG_PARTS = [12];

/**
 * Smoke inputs carrying a publish stamp: hashed by CONTENT with the stamp
 * normalised out, so two publishes of the same tree hash the same.
 */
const STAMPED_INPUTS = ['site/chicago/4d/walk/index.html'];
const STAMP_PATTERN = /build\s+[0-9a-f]{6,}\s+·[^<\n]*/g;

const git = (args, cwd = REPO) =>
  execFileSync('git', args, { cwd, encoding: 'utf8', maxBuffer: 1 << 28 });

/**
 * A digest of the smoke's inputs, from the index (so `git add`-ed work counts),
 * plus an honest `dirty` flag for anything modified and not staged — a hash
 * that silently ignored a working-tree edit would license exactly the wrong
 * skip.
 */
/**
 * Blob shas from the INDEX, not the commit: `git add`-ed work counts, which is
 * what a run that has staged its change but not committed it needs. Anything
 * modified and not staged is reported as `dirty` rather than silently ignored —
 * a hash that quietly missed a working-tree edit would license exactly the wrong
 * skip, which is the one failure this tool must not have.
 */
function digest(paths, extra = []) {
  const listing = git(['ls-files', '-s', '--', ...paths]);
  const dirty = git(['status', '--porcelain', '--', ...paths, ...extra]).trim();
  const h = crypto.createHash('sha256');
  h.update(listing);
  for (const rel of extra) {
    const file = path.join(REPO, rel);
    const body = fs.existsSync(file)
      ? fs.readFileSync(file, 'utf8').replace(STAMP_PATTERN, 'build <stamp>')
      : '';
    h.update(`\n${rel}\n${body}`);
  }
  return { hash: `sha256:${h.digest('hex').slice(0, 16)}`, dirty: dirty.length > 0 };
}

function treeHash() {
  try {
    const tree = digest(SMOKE_INPUTS, STAMPED_INPUTS);
    const notes = digest(CHANGELOG_INPUTS);
    return { hash: tree.hash, dirty: tree.dirty, changelogHash: notes.hash };
  } catch {
    return { hash: null, dirty: null, changelogHash: null };
  }
}

function headInfo() {
  const out = {};
  try {
    out.commit = git(['rev-parse', 'HEAD']).trim().slice(0, 12);
    out.ref = git(['rev-parse', '--abbrev-ref', 'HEAD']).trim();
  } catch { /* not a checkout; the reading still stands on its tree hash */ }
  try {
    // Is HEAD's tree the same as dev's, for the paths that matter? That is a
    // stronger statement than "I am on dev" and it is the one a reader wants.
    const devSha = git(['rev-parse', 'origin/dev']).trim().slice(0, 12);
    out.devCommit = devSha;
  } catch { /* origin/dev not fetched here */ }
  return out;
}

// ---------------------------------------------------------------------------
// the parser — ONE code path for a local log and a CI log
// ---------------------------------------------------------------------------

/**
 * `gh run view --log` prefixes every line with `job\tstep\t<ISO timestamp> `.
 * Strip both, keeping the timestamp: it is the only trustworthy clock a CI log
 * carries, and it is what dates a folded-in reading.
 */
function stripLogPrefix(raw) {
  let line = raw;
  let when = null;
  const tab = line.lastIndexOf('\t');
  if (tab !== -1) line = line.slice(tab + 1);
  const iso = line.match(/^(\d{4}-\d\d-\d\dT[\d:.]+Z)\s(.*)$/);
  if (iso) { when = iso[1]; line = iso[2]; }
  return { line, when };
}

/** Expand a SMOKE_STAGE spec — `3`, `3-4`, `1,5-6`, or '' for all — into parts. */
function partsOf(spec) {
  if (!spec || spec === 'all') return Array.from({ length: PARTS }, (_, i) => i + 1);
  const out = new Set();
  for (const piece of String(spec).split(',')) {
    const m = piece.trim().match(/^(\d+)(?:-(\d+))?$/);
    if (!m) continue;
    const lo = Number(m[1]);
    const hi = m[2] === undefined ? lo : Number(m[2]);
    for (let n = lo; n <= hi && n <= PARTS; n++) if (n >= 1) out.add(n);
  }
  return [...out].sort((a, b) => a - b);
}

const VIEWPORTS = { 'mobile 390x780': 'mobile', 'desktop 1280x800': 'desktop' };

/**
 * Read a smoke log into one reading PER VIEWPORT. Per viewport, because the two
 * halves boot separate browser processes and fail independently — a mobile pass
 * says nothing about desktop, and a record that merged them would answer the
 * ticket's question wrongly half the time.
 */
function parseSmokeLog(text) {
  const readings = [];
  let stageSpec = '';        // '' means unfiltered — every part
  let viewportFilter = '';
  let target = 'source';
  let current = null;        // the viewport section being read
  let lastTime = null;
  let wallSeconds = null;
  let sawSummary = false;
  const frameCosts = [];

  const finish = () => { if (current) readings.push(current); current = null; };

  for (const raw of text.split('\n')) {
    const { line, when } = stripLogPrefix(raw);
    if (when) lastTime = when;

    let m;
    if ((m = line.match(/^serving .* — (PUBLISHED mirror|source tree)/))) {
      target = m[1].startsWith('PUBLISHED') ? 'published' : 'source';
      continue;
    }
    if ((m = line.match(/^NOT THE FULL GATE — viewports filtered to "([^"]+)"/))) {
      viewportFilter = m[1];
      continue;
    }
    if ((m = line.match(/^NOT THE FULL GATE — stages filtered to "([^"]+)"/))) {
      stageSpec = m[1];
      continue;
    }
    if ((m = line.match(/^(mobile 390x780|desktop 1280x800):\s*$/))) {
      finish();
      current = {
        viewport: VIEWPORTS[m[1]], label: m[1], stage: stageSpec || 'all',
        parts: partsOf(stageSpec), target, passed: 0, failed: 0,
        failures: [], verdict: 'killed',
      };
      continue;
    }
    if ((m = line.match(/^\s{2}(pass|FAIL)\s+(?:\[\d+:\d\d\]\s+)?(.*)$/))) {
      if (!current) continue;                 // the vendor block, after both viewports
      if (m[1] === 'pass') current.passed += 1;
      else { current.failed += 1; current.failures.push(m[2].trim()); }
      // `zero page errors` is the LAST check of a viewport body and the whole
      // reason T-0060 cut the stages: a run killed before it merged without
      // ever having been told whether the page threw. Reaching it is what
      // turns `killed` into a real verdict.
      if (/: zero page errors\b/.test(m[2])) current.verdict = current.failed ? 'fail' : 'pass';
      else if (current.failed && current.verdict === 'killed') current.reachedAFailure = true;
      continue;
    }
    if ((m = line.match(/one animation frame costs ([\d.\s/]+) ms here/))) {
      frameCosts.push(...m[1].split('/').map((s) => Number(s.trim())).filter(Number.isFinite));
      continue;
    }
    if ((m = line.match(/^(\d+) m (\d+) s (?:for stage \S+|unfiltered)/))) {
      wallSeconds = Number(m[1]) * 60 + Number(m[2]);
      continue;
    }
    if (/^\d+ passed, \d+ failed$/.test(line)) { finish(); sawSummary = true; continue; }
  }
  finish();

  // A viewport section that never reached its page-error check was killed —
  // timed out, or the process died. Say `killed`, never `fail`: they are
  // different facts and only one of them is about the tree.
  for (const r of readings) {
    if (r.verdict === 'killed' && sawSummary && !r.failed) r.verdict = 'pass';
    if (r.verdict === 'killed' && sawSummary && r.failed) r.verdict = 'fail';
    delete r.reachedAFailure;
    if (wallSeconds !== null && readings.length === 1) r.wallSeconds = wallSeconds;
  }
  if (viewportFilter && readings.length > 1) {
    // Cannot happen from the smoke, but a hand-concatenated log could.
    return readings.filter((r) => r.label.includes(viewportFilter));
  }
  void lastTime;
  return readings;
}

// ---------------------------------------------------------------------------
// the state file
// ---------------------------------------------------------------------------

function load() {
  if (!fs.existsSync(STATE)) return { note: NOTE, readings: [] };
  const j = JSON.parse(fs.readFileSync(STATE, 'utf8'));
  return { note: NOTE, readings: j.readings ?? [] };
}

/**
 * Keep the record small without losing the two things `ask` needs for every
 * (viewport, part): the NEWEST reading and the newest PASSING one. Everything
 * else is history and is trimmed newest-first.
 */
function prune(readings, cap = 60) {
  const sorted = [...readings].sort((a, b) => String(b.takenAt).localeCompare(String(a.takenAt)));
  const keep = new Set();
  for (const viewport of ['mobile', 'desktop']) {
    for (let part = 1; part <= PARTS; part++) {
      const rows = sorted.filter((r) => r.viewport === viewport && r.parts.includes(part));
      const newest = rows[0];
      const newestPass = rows.find((r) => r.verdict === 'pass');
      if (newest) keep.add(newest);
      if (newestPass) keep.add(newestPass);
    }
  }
  for (const r of sorted) { if (keep.size >= cap) break; keep.add(r); }
  return [...keep].sort((a, b) => String(b.takenAt).localeCompare(String(a.takenAt)));
}

function save(readings) {
  fs.writeFileSync(STATE, `${JSON.stringify({ note: NOTE, readings: prune(readings) }, null, 2)}\n`);
}

/** The conditions half of a reading — the thing T-0215 says a verdict is worthless without. */
function localConditions() {
  return {
    kind: process.env.GITHUB_ACTIONS ? 'steward-runner' : 'local',
    cpus: os.cpus().length,
    memGB: Math.round((os.totalmem() / 1024 ** 3) * 10) / 10,
    // Sampled when the reading is FILED, so it includes the smoke's own load —
    // which is the honest figure. The question a reader asks is "how contended
    // was the box while this ran", and a load taken before the browsers started
    // would answer a different one.
    loadavg: os.loadavg().map((n) => Math.round(n * 10) / 10),
  };
}

function addReadings(parsed, { host, source, when }) {
  const th = treeHash();
  const head = headInfo();
  const takenAt = when ?? new Date().toISOString();
  const rows = parsed.map((r) => ({
    viewport: r.viewport,
    stage: r.stage,
    parts: r.parts,
    verdict: r.verdict,
    target: r.target,
    passed: r.passed,
    failed: r.failed,
    failures: r.failures.slice(0, 6),
    wallSeconds: r.wallSeconds ?? null,
    takenAt,
    ref: head.ref ?? null,
    commit: head.commit ?? null,
    devCommit: head.devCommit ?? null,
    treeHash: th.hash,
    treeDirty: th.dirty,
    changelogHash: th.changelogHash,
    host,
    source,
  }));
  const state = load();
  save([...rows, ...state.readings]);
  return rows;
}

// ---------------------------------------------------------------------------
// ask — the whole point: an answer with nothing run
// ---------------------------------------------------------------------------

const fmtWall = (s) => (s === null || s === undefined ? '—'
  : `${Math.floor(s / 60)}m ${String(s % 60).padStart(2, '0')}s`);

function describeHost(h) {
  if (!h) return 'unknown host';
  const bits = [h.kind];
  if (h.cpus) bits.push(`${h.cpus} cpu`);
  if (h.loadavg) bits.push(`load ${h.loadavg[0]}`);
  if (h.frameCostMs?.length) bits.push(`frame ${h.frameCostMs.join('/')} ms`);
  return bits.join(', ');
}

function ask(argv) {
  const state = load();
  const wantViewport = flag(argv, '--viewport');
  const wantStage = flag(argv, '--stage');
  const wantParts = wantStage ? partsOf(wantStage) : partsOf('');
  const th = treeHash();

  console.log('dev\'s standing smoke record — tools/dev-smoke-state.json');
  console.log(`your smoke-relevant tree: ${th.hash}${th.dirty ? ' (WORKING TREE DIRTY — '
    + 'stage your changes for an exact comparison)' : ''}`);
  console.log(`your release notes:       ${th.changelogHash}  (hashed apart: every branch `
    + `appends one entry, and only part ${CHANGELOG_PARTS.join('/')} reads them)`);
  if (!state.readings.length) {
    console.log('\nno readings yet. Fold one in with:\n'
      + '  node tools/dev-smoke-state.mjs record <smoke.log>\n'
      + '  node tools/dev-smoke-state.mjs ci <chicago-4d-smoke.yml run id>');
    return;
  }
  console.log('');

  for (const viewport of ['mobile', 'desktop']) {
    if (wantViewport && viewport !== wantViewport) continue;
    for (let part = 1; part <= PARTS; part++) {
      if (!wantParts.includes(part)) continue;
      const rows = state.readings
        .filter((r) => r.viewport === viewport && r.parts.includes(part))
        .sort((a, b) => String(b.takenAt).localeCompare(String(a.takenAt)));
      const latest = rows[0];
      const lastPass = rows.find((r) => r.verdict === 'pass');
      const head = `${viewport}, part ${part}`;
      if (!latest) { console.log(`${head}\n  no reading — nobody has recorded this one.`); continue; }
      console.log(head);
      console.log(`  latest ..... ${latest.verdict.toUpperCase().padEnd(6)} ${latest.takenAt}`
        + `  ${latest.stage === 'all' ? 'unfiltered' : `stage ${latest.stage}`}`
        + `  ${latest.target}  ${fmtWall(latest.wallSeconds)}  [${describeHost(latest.host)}]`);
      for (const f of latest.failures) console.log(`               - ${f}`);
      if (lastPass && lastPass !== latest) {
        console.log(`  last pass .. ${lastPass.takenAt}  `
          + `${lastPass.stage === 'all' ? 'unfiltered' : `stage ${lastPass.stage}`}`
          + `  ${lastPass.target}  ${fmtWall(lastPass.wallSeconds)}  [${describeHost(lastPass.host)}]`);
      } else if (!lastPass) {
        console.log('  last pass .. never recorded here.');
      }
      // The sentence the ticket actually asked for.
      if (latest.verdict !== 'pass') {
        const sameTree = latest.treeHash && latest.treeHash === th.hash;
        const notesDiffer = CHANGELOG_PARTS.includes(part)
          && latest.changelogHash && latest.changelogHash !== th.changelogHash;
        // `killed` and `fail` are DIFFERENT FACTS and only one of them is about
        // the tree — which is the whole of T-0215. A matching hash proves an
        // ordinary red is inherited; it proves nothing at all about a kill,
        // because a kill is a statement about the box the browser was starved
        // on. Saying "inherited" over both would rebuild the wrong answer three
        // runs already gave.
        console.log(`  → ${!sameTree
          ? 'taken on a different tree from yours, so it dates this but does not attribute it.'
          : latest.verdict === 'killed'
            ? 'taken on YOUR EXACT tree — but a KILL is a fact about the machine, not the '
              + 'tree.\n     The hash says the tree was the same; it does not say the stage '
              + 'would fail on a quiet box.\n     Read the load and the frame cost above '
              + 'before spending ten minutes re-running it (T-0215).'
            : 'this reading was taken on YOUR EXACT tree — the red is INHERITED, not yours. '
              + 'Do not re-derive it.'
        }`);
        if (sameTree && notesDiffer) {
          console.log('     (part 8 reads the release notes, and your changelog entry is not '
            + 'the one\n      that reading was taken with — everything else about the tree is '
            + 'identical.)');
        }
      }
      console.log('');
    }
  }
  console.log('Conditions are part of the reading, not decoration: T-0215 measured the same tree\n'
    + 'twenty times slower on a loaded box than a quiet one, and a `killed` verdict there is a\n'
    + 'fact about the machine. A CI pass dates a steward-runner red; it does not overrule it.');
}

// ---------------------------------------------------------------------------
// entry points
// ---------------------------------------------------------------------------

function flag(argv, name) {
  const i = argv.indexOf(name);
  return i === -1 ? null : argv[i + 1];
}

function record(argv) {
  const files = [];
  for (let i = 0; i < argv.length; i++) {
    if (argv[i].startsWith('--')) { i += 1; continue; }   // a flag and its value
    files.push(argv[i]);
  }
  const text = files.length
    ? files.map((f) => fs.readFileSync(f, 'utf8')).join('\n')
    : fs.readFileSync(0, 'utf8');
  const parsed = parseSmokeLog(text);
  if (!parsed.length) { console.error('no viewport section found in that log'); process.exit(2); }
  const host = { ...localConditions(), ...(flag(argv, '--host') ? { kind: flag(argv, '--host') } : {}) };
  const frames = text.match(/one animation frame costs ([\d.\s/]+) ms here/g);
  if (frames) {
    host.frameCostMs = frames.flatMap((f) => f.match(/[\d.]+/g).map(Number)).slice(0, 6);
  }
  const rows = addReadings(parsed, { host, source: files.join(' ') || 'stdin', when: flag(argv, '--at') });
  for (const r of rows) {
    console.log(`recorded ${r.viewport} stage ${r.stage}: ${r.verdict} `
      + `(${r.passed} passed, ${r.failed} failed) on ${r.treeHash}`);
  }
}

/**
 * `gh`, with the two failures this tool must not turn into a stack trace. It
 * exists to be CHEAPER than re-running a stage; a run that has to read a Node
 * traceback to learn "GitHub is rate-limiting you" has already lost that
 * argument. Both known modes — no `gh`/no auth, and the secondary rate limit a
 * busy fleet hits constantly — get one sentence and exit 3, which is distinct
 * from the exit 2 a malformed log gets.
 */
function gh(args, { json = true } = {}) {
  try {
    const out = execFileSync('gh', args, { cwd: REPO, encoding: 'utf8', maxBuffer: 1 << 29 });
    return json ? JSON.parse(out) : out;
  } catch (e) {
    const why = String(e.stderr ?? e.message ?? '');
    if (/rate limit|abuse detection|secondary rate/i.test(why)) {
      console.error('GitHub is rate-limiting this account, so the CI half of the record cannot be '
        + 'read right now.\nThe committed readings below are unaffected — run `ask`. Re-run '
        + '`ci` when it is quieter.');
    } else if (/not found|command not found|ENOENT/i.test(why)) {
      console.error('`gh` is unavailable or unauthenticated here; `ci` needs it. `ask` and '
        + '`record` do not.');
    } else {
      console.error(`gh failed: ${why.trim().split('\n')[0]}`);
    }
    process.exit(3);
  }
}

const ghJson = (args) => gh(args);

function ci(argv) {
  const id = argv.find((a) => /^\d+$/.test(a));
  if (!id) {
    const runs = ghJson(['run', 'list', '--workflow=chicago-4d-smoke.yml', '--branch', 'dev',
      '--limit', '15', '--json', 'databaseId,conclusion,createdAt,event,headSha']);
    if (!runs.length) { console.log('chicago-4d-smoke.yml has never run on dev.'); return; }
    console.log('chicago-4d-smoke.yml on dev — fold one in with `ci <id>`:\n');
    for (const r of runs) {
      console.log(`  ${r.databaseId}  ${r.conclusion ?? 'running'}  ${r.createdAt}  `
        + `${r.event}  ${String(r.headSha).slice(0, 12)}`);
    }
    return;
  }
  const meta = ghJson(['run', 'view', id, '--json', 'conclusion,createdAt,headSha,headBranch,url']);
  const log = gh(['run', 'view', id, '--log'], { json: false });
  const parsed = parseSmokeLog(log);
  if (!parsed.length) { console.error(`run ${id} has no viewport section in its log`); process.exit(2); }
  // A CI runner cannot report its load average to us after the fact, and saying
  // so is better than inventing one. The wall clock IS the comparable figure —
  // it is what differs by a factor of twenty (T-0215).
  const host = { kind: 'ci', cpus: null, loadavg: null, note: 'GitHub-hosted ubuntu-latest, load not recoverable from the log' };
  const rows = addReadings(parsed, { host, source: `gh-run:${id} ${meta.url}`, when: meta.createdAt });
  console.log(`folded in ${meta.headBranch}@${String(meta.headSha).slice(0, 12)} `
    + `(${meta.conclusion}) from ${meta.url}`);
  for (const r of rows) {
    console.log(`  ${r.viewport} stage ${r.stage}: ${r.verdict} (${r.passed} passed, ${r.failed} failed)`);
  }
  console.log('NOTE: the tree hash on a folded-in CI reading is THIS checkout\'s, not that run\'s '
    + '—\n  a log does not carry one. Fold runs in promptly, or read the reading by its date.');
}

const [cmd, ...rest] = process.argv.slice(2);
switch (cmd) {
  case 'record': record(rest); break;
  case 'ci': ci(rest); break;
  case 'hash': {
    const th = treeHash();
    console.log(`${th.hash}${th.dirty ? '  (working tree dirty)' : ''}`);
    break;
  }
  case 'ask': case undefined: ask(rest); break;
  default:
    console.error('usage: dev-smoke-state.mjs [ask|record|ci|hash] …  (see the file header)');
    process.exit(2);
}

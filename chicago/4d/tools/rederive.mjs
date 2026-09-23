#!/usr/bin/env node
/**
 * rederive.mjs — run the derived research layer's rebuild sequence, and answer
 * whether a given conflict may be cleared by doing so.
 *
 * WHY THIS EXISTS (owner, 2026-09-10). With PR #1058 the PR lap could merge for
 * the first time, and every open PR promptly came back LEFT ALONE for a REAL
 * CONFLICT. Every conflicting file was a tool output that two runs had each
 * re-derived — seven directory crosswalks on one PR, the land-sale crosswalk and
 * spend and identity_master on another, the scene sidecar and the audit workbook
 * on a third. Not one of them was a disagreement about the town.
 *
 * `.github/steward/pr-lap.sh` already draws exactly the right line for this:
 *
 *   "A conflict here is never resolved by hand: the merge takes either side to
 *    clear the marker and the tool then rewrites the file from source."
 *
 * It just drew it around five bookkeeping files. This widens it to the derived
 * research layer, and the widening is a LIST rather than a pattern, so what is
 * in scope can be read off `tools/derived_manifest.json` by anyone.
 *
 * THE SAFETY PROPERTY, and it is worth being exact about, because this is a tool
 * that resolves merges in research data:
 *
 *   1. A path not named in the manifest is refused, exactly as before.
 *   2. A path whose file declares `hand_authored: true` is refused even if named
 *      — `--check` fails if the manifest ever lists one.
 *   3. Resolving is only ever "take either side, then rebuild from the inputs".
 *      Nothing here merges two versions of anything.
 *   4. `tools/check.sh` is the proof, and it runs AFTER this. check.sh is what
 *      asserts each of these files re-derives; a wrong entry here makes the gate
 *      red, and the lap does not push a red tree. The worst case is a PR that
 *      stays open — the state it was already in — never a bad merge onto dev.
 *
 * THE ORDER IS LOAD-BEARING, and was learned on PR #1055: crosswalks before the
 * spends that read them, consolidate after all of them, and mint_civic_residents
 * AFTER consolidate, because consolidate moves the inputs mint reads. Built in
 * the wrong order mint still differed on two cards and only converged when re-run.
 *
 *   node tools/rederive.mjs --check                 the manifest is well-formed
 *   node tools/rederive.mjs --resolvable <paths…>   may these conflicts be cleared?
 *   node tools/rederive.mjs --run                   run the sequence, in order
 *   node tools/rederive.mjs --prove                 does every step write what it claims?
 *   node tools/rederive.mjs --self-test
 */
import { readFileSync, existsSync, statSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const APP = path.resolve(HERE, '..');
const REPO = path.resolve(APP, '..', '..');
const MANIFEST = path.join(HERE, 'derived_manifest.json');

const argv = process.argv.slice(2);
const has = (n) => argv.includes(`--${n}`);
const rest = () => argv.filter((a) => !a.startsWith('--'));

const load = (file = MANIFEST) => JSON.parse(readFileSync(file, 'utf8'));

/**
 * Repo-relative, whatever the caller passed.
 *
 * REPO-RELATIVE IS TRIED FIRST, and that is not arbitrary: `git diff
 * --diff-filter=U` prints repo-relative paths and pr-lap.sh hands them straight
 * here, but the manifest's commands run with cwd = chicago/4d, so a bare
 * cwd-relative resolve turned `chicago/4d/data/…` into
 * `chicago/4d/chicago/4d/data/…` and every path fell through as "not in the
 * manifest". Refusing everything is the SAFE direction, which is exactly why it
 * would have gone unnoticed: the lap would have kept leaving PRs alone and this
 * file would have looked like it simply never matched.
 */
function normalise(p) {
  if (!p.startsWith('/') && existsSync(path.join(REPO, p))) {
    return path.relative(REPO, path.join(REPO, p)).split(path.sep).join('/');
  }
  const abs = path.resolve(p.startsWith('/') ? p : path.join(process.cwd(), p));
  return path.relative(REPO, abs).split(path.sep).join('/');
}

/** Does this file declare itself hand-authored? A judgement is not a derivation. */
function handAuthored(rel) {
  const abs = path.join(REPO, rel);
  if (!existsSync(abs) || !rel.endsWith('.json')) return false;
  try { return load(abs).hand_authored === true; } catch { return false; }
}

const allResolved = (m) => m.steps.flatMap((s) => s.resolves ?? []);

/* ------------------------------------------------------------------- check */

function check(m = load()) {
  const problems = [];
  const seen = new Map();
  // THE INVARIANT THAT MAKES THE BACKSTOP REAL (see the manifest's own
  // `_only_gated_tools`). check.sh is what proves a rebuild was right; a tool
  // check.sh never asks `--check` of has no such proof, so re-running it can
  // destroy a committed file and leave the gate green.
  const gate = existsSync(path.join(APP, 'tools', 'check.sh'))
    ? readFileSync(path.join(APP, 'tools', 'check.sh'), 'utf8') : '';

  m.steps.forEach((s, i) => {
    const at = `step ${i + 1} (${(s.command ?? []).join(' ')})`;
    if (!Array.isArray(s.command) || s.command.length < 2) {
      problems.push(`${at}: command must be an argv array`);
      return;
    }
    const script = path.join(APP, s.command[1]);
    if (!existsSync(script)) problems.push(`${at}: ${s.command[1]} does not exist`);
    else if (gate && !new RegExp(`${s.command[1].replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}[^\\n]*--check`).test(gate)) {
      problems.push(`${at}: tools/check.sh never runs ${s.command[1]} with --check, so nothing `
        + 'asserts its output re-derives. An ungated derivation may not resolve a conflict — '
        + 'gate the tool first, or leave the conflict for the run that owns the ticket.');
    }
    if (!Array.isArray(s.resolves)) problems.push(`${at}: resolves must be an array (use [] for a rebuild-only step)`);

    for (const rel of s.resolves ?? []) {
      if (rel !== normalise(path.join(REPO, rel))) problems.push(`${at}: ${rel} is not a clean repo-relative path`);
      // A path claimed by two steps means the later one silently wins, and which
      // one that is depends on the order — exactly the ambiguity this file exists
      // to remove.
      if (seen.has(rel)) problems.push(`${at}: ${rel} is also resolved by ${seen.get(rel)} — one owner per file`);
      seen.set(rel, at);
      if (!existsSync(path.join(REPO, rel))) problems.push(`${at}: ${rel} is listed but does not exist in the tree`);
      if (handAuthored(rel)) {
        problems.push(`${at}: ${rel} declares hand_authored — a judgement is not a derivation `
          + 'and a tool may not rewrite it. Remove it from the manifest.');
      }
    }
  });

  if (problems.length) {
    console.error('derived manifest FAILED:');
    for (const p of problems) console.error(`  - ${p}`);
    return 1;
  }
  console.log(`derived manifest OK — ${m.steps.length} step(s), ${allResolved(m).length} `
    + 'resolvable file(s), none hand-authored');
  return 0;
}

/* ------------------------------------------------------- resolvable? */

/**
 * The question pr-lap.sh asks. EVERY path must be covered, or the answer is no:
 * clearing some conflicts and leaving others would leave the merge half-done and
 * the markers in the tree.
 */
function resolvable(paths, m = load()) {
  const covered = new Set(allResolved(m));
  const unknown = [];
  const refused = [];
  for (const raw of paths) {
    const rel = normalise(raw);
    if (handAuthored(rel)) refused.push(`${rel} (declares hand_authored)`);
    else if (!covered.has(rel)) unknown.push(rel);
  }
  if (unknown.length === 0 && refused.length === 0) {
    console.log(`all ${paths.length} conflicting file(s) are rebuilt from source by the manifest`);
    return 0;
  }
  console.error('these conflicts are NOT the manifest\'s to clear:');
  for (const u of refused) console.error(`  - ${u}`);
  for (const u of unknown) console.error(`  - ${u} (not in tools/derived_manifest.json)`);
  console.error('\nThey want the run that owns the ticket. Add a file here only when a tool');
  console.error('rewrites it from its inputs and check.sh asserts that it does.');
  return 1;
}

/* -------------------------------------------------------------------- run */

function run(m = load()) {
  for (const [i, s] of m.steps.entries()) {
    const label = s.command.join(' ');
    process.stdout.write(`  [${i + 1}/${m.steps.length}] ${label}\n`);
    try {
      execFileSync(s.command[0], s.command.slice(1), { cwd: APP, stdio: ['ignore', 'pipe', 'pipe'] });
    } catch (e) {
      console.error(`  FAILED: ${label}`);
      console.error(`${e.stdout ?? ''}${e.stderr ?? ''}`.split('\n').slice(-8).map((l) => `    ${l}`).join('\n'));
      return 1;
    }
  }
  console.log(`derived layer rebuilt — ${m.steps.length} step(s), in dependency order`);
  return 0;
}

/* ------------------------------------------------------------------ prove */

/**
 * DOES EACH STEP ACTUALLY WRITE WHAT IT CLAIMS? The one thing `--check` cannot
 * see by reading the manifest, and the one that bit.
 *
 * read_newberry_index.py was listed here as the rebuild for leads.json. Invoked
 * bare it PRINTS ITS USAGE AND EXITS 0 — it writes nothing at all, because
 * rebuilding that file needs `--parse` over OCR shards kept outside the repo.
 * The entry passed `--check` (the tool is gated), passed an idempotency test
 * (nothing changed, because nothing ran) and passed a full-sequence run. It
 * failed only when a real merge needed it, hours later, as `leads.json does not
 * re-derive from its inputs`.
 *
 * The idempotency test that missed it ran the tool under `timeout 400` with its
 * output suppressed, so a tool killed at 400 seconds and a tool that did nothing
 * looked exactly alike. This asks the question that separates them: run the
 * command, and require every file it claims to resolve to have been WRITTEN.
 * mtime rather than content, because a correct rebuild of an unchanged tree
 * produces identical bytes — "the file did not change" is the expected result
 * and proves nothing either way.
 */
function prove(m = load()) {
  const stamp = (rel) => { try { return statSync(path.join(REPO, rel)).mtimeMs; } catch { return null; } };
  let bad = 0;
  for (const [i, s] of m.steps.entries()) {
    const label = s.command.join(' ');
    const before = new Map((s.resolves ?? []).map((r) => [r, stamp(r)]));
    try {
      execFileSync(s.command[0], s.command.slice(1), { cwd: APP, stdio: ['ignore', 'pipe', 'pipe'] });
    } catch (e) {
      console.error(`  [${i + 1}] FAILED to run: ${label}`);
      bad += 1;
      continue;
    }
    const untouched = [...before.keys()].filter((r) => stamp(r) === before.get(r));
    if (untouched.length) {
      console.error(`  [${i + 1}] ${label}`);
      console.error('        claims to rebuild file(s) it did not write:');
      for (const u of untouched) console.error(`          ${u}`);
      bad += 1;
    } else if ((s.resolves ?? []).length) {
      console.log(`  [${i + 1}] ok — ${label} wrote all ${s.resolves.length} of its file(s)`);
    } else {
      console.log(`  [${i + 1}] ok — ${label} (rebuild only, resolves nothing)`);
    }
  }
  if (bad) {
    console.error(`\nderived manifest: ${bad} step(s) do not write what they claim.`);
    console.error('A command that writes nothing leaves the lap taking `--ours` on a file it');
    console.error('then cannot rebuild, and the gate goes red where a plain refusal would');
    console.error('have been clearer. Remove the step, or give it the arguments that write.');
    return 1;
  }
  console.log(`\nderived manifest: all ${m.steps.length} step(s) write what they claim`);
  return 0;
}

/* -------------------------------------------------------------- self-test */

async function selfTest() {
  const { mkdtempSync, writeFileSync, rmSync, mkdirSync } = await import('node:fs');
  const { tmpdir } = await import('node:os');
  let failures = 0;
  const check_ = (what, ok, detail) => {
    console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
    if (!ok) failures += 1;
  };

  const real = load();

  console.log('\n  the manifest that ships');
  check_('is well-formed, and check() passes it', check(real) === 0);
  check_('every step rebuilds at least one thing or says it rebuilds nothing',
    real.steps.every((s) => Array.isArray(s.resolves)));
  check_('the hand-authored file is NOT resolvable',
    resolvable(['chicago/4d/data/research/land_sales/resident_rulings.json'], real) === 1);
  check_('a file nobody derives is NOT resolvable',
    resolvable(['chicago/4d/data/residents/households/hh_taylor_c.json'], real) === 1);
  check_('a file the manifest owns IS resolvable',
    resolvable(['chicago/4d/data/research/land_sales/resident_crosswalk.json'], real) === 0);
  check_('a MIXED set is refused as a whole — half a merge is not a merge',
    resolvable([
      'chicago/4d/data/research/land_sales/resident_crosswalk.json',
      'chicago/4d/data/residents/households/hh_taylor_c.json',
    ], real) === 1);
  check_('mint_civic_residents resolves nothing, because its outputs are resident cards',
    real.steps.find((s) => s.command.join(' ').includes('mint_civic_residents'))?.resolves.length === 0);
  check_('the spends come after the crosswalks they read',
    real.steps.findIndex((s) => s.command.join(' ').includes('spend_land_sales'))
      > real.steps.findIndex((s) => s.command.join(' ').includes('read_land_sales')));
  check_('mint comes after consolidate, which moves the inputs it reads (PR #1055)',
    real.steps.findIndex((s) => s.command.join(' ').includes('mint_civic_residents'))
      > real.steps.findIndex((s) => s.command.join(' ').includes('consolidate_resident_evidence')));

  console.log('\n  check() refuses a manifest that would be unsafe');
  const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-rederive-'));
  try {
    const bad = (steps) => {
      const f = path.join(tmp, 'm.json');
      writeFileSync(f, JSON.stringify({ schema: 1, steps }));
      return check(load(f));
    };
    check_('a step naming a script that does not exist',
      bad([{ command: ['python3', 'tools/no_such_tool.py'], resolves: [] }]) === 1);
    check_('the SAME file resolved by two steps — one owner per file',
      bad([
        { command: ['python3', 'tools/compile_scene.py'], resolves: ['chicago/4d/data/town_census.json'] },
        { command: ['python3', 'tools/town_census.py'], resolves: ['chicago/4d/data/town_census.json'] },
      ]) === 1);
    check_('a hand-authored file listed as resolvable',
      bad([{
        command: ['python3', 'tools/read_land_sales.py', '--build'],
        resolves: ['chicago/4d/data/research/land_sales/resident_rulings.json'],
      }]) === 1);
    check_('a listed path that is not in the tree',
      bad([{ command: ['python3', 'tools/compile_scene.py'], resolves: ['chicago/4d/data/nope.json'] }]) === 1);
  } finally { rmSync(tmp, { recursive: true, force: true }); }

  console.log(`\n${failures === 0 ? 'rederive self-test: all pass' : `rederive self-test: ${failures} FAILURE(S)`}`);
  return failures === 0 ? 0 : 1;
}

/* ------------------------------------------------------------------- main */

if (has('self-test')) process.exit(await selfTest());
else if (has('resolvable')) process.exit(resolvable(rest()));
else if (has('prove')) process.exit(prove());
else if (has('run')) process.exit(run());
else process.exit(check());

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
 * AND ORDER ALONE IS NOT ENOUGH, which is T-1363. The derived layer has a CYCLE in
 * it: `reconstruct_residents_1835.py --stage attribute_fill_arrival` draws from the
 * town model, and model_town_1835.py rebuilds the town model from a profile of the
 * cards that stage writes. No linear order settles that — put the stage first and
 * its draws end the run one model behind; put it last and the model ends the run
 * one population behind. A second `--run` does not help either, because the second
 * pass moves the model again. So the manifest declares a SECOND PASS: a short list
 * of steps re-run after the sequence, walking the cycle once more from a settled
 * model. `--run` runs it; `--check` holds its shape (see `_the_second_pass`); and
 * tools/check.sh is the proof that it settles, because it asserts the model, the
 * profile, the tier table and the resident cards all still re-derive afterwards.
 *
 * AND THE PASS IS NOT THE END OF IT, which is T-1602. The model is a lagging reader
 * too — it reads the scene's people.json and the town census, both rebuilt far below
 * it — so it leads the pass. And the pass rewrites cards that compile_scene.py and
 * everything below it read, so `--run` ends with the manifest's `after_the_pass`
 * tail, repeated until a lap changes nothing: the scene and its generators read
 * each other, and one lap leaves the sidecars a lap behind the structures. Before
 * this, `--run` alone left the gate red on any branch that moved the population,
 * and only pr-lap.sh's own late `--tail` (plus a hand step) turned it green.
 *
 *   node tools/rederive.mjs --check                 the manifest is well-formed
 *   node tools/rederive.mjs --resolvable <paths…>   may these conflicts be cleared?
 *   node tools/rederive.mjs --run                   the sequence, the second pass, then the settled tail
 *   node tools/rederive.mjs --tail <tools/x.py>     that step and every step below it (T-1661),
 *                                                   repeated until a lap moves nothing (T-1602)
 *   node tools/rederive.mjs --resolve               mid-merge: clear derived conflicts by rebuilding
 *   node tools/rederive.mjs --callers <script…>     no caller re-runs a step bare (T-1661)
 *   node tools/rederive.mjs --prove                 does every step write what it claims?
 *   node tools/rederive.mjs --self-test
 */
import { readFileSync, existsSync, statSync, copyFileSync, rmSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
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

  // A READER SITS BELOW WHAT IT READS (T-2080). On a clean tree a reader placed above
  // its writer passes, because every committed file already agrees with its inputs;
  // the lag shows only on a merged tree, as a refusal that reads like a data fault or
  // as a stale file written without complaint. So the edge is declared on the reader
  // (`reads`) and held here: rebuilt by a step ABOVE it, and named in the reader's own
  // source, so the declaration cannot be cargo. A cycle is `second_pass`, not this.
  m.steps.forEach((s, i) => {
    if (s.reads === undefined) return;
    const at = `step ${i + 1} (${(s.command ?? []).join(' ')})`;
    if (!Array.isArray(s.reads) || s.reads.length === 0) {
      problems.push(`${at}: reads must be a non-empty array of paths`);
      return;
    }
    const script = path.join(APP, String(s.command?.[1] ?? ''));
    const source = existsSync(script) ? readFileSync(script, 'utf8') : '';
    for (const rel of s.reads) {
      const owner = m.steps.findIndex((st) => (st.resolves ?? []).includes(rel));
      if (owner < 0) {
        problems.push(`${at}: declares it reads ${rel}, which no step rebuilds — there is no `
          + 'edge to hold. Declare only files the sequence itself rewrites.');
      } else if (owner === i) {
        problems.push(`${at}: declares it reads ${rel}, which it rebuilds itself. A step is `
          + 'not downstream of its own output.');
      } else if (owner > i) {
        problems.push(`${at}: reads ${rel}, which step ${owner + 1} (${m.steps[owner].command.join(' ')}) `
          + 'rebuilds BELOW it. On a merged tree this step reads the pre-merge file — T-2080 '
          + 'measured location_spend.py refusing a business whose seat had moved, and '
          + 'report_convergence_coverage.py writing a stale join without a word. Move the '
          + `writer above step ${i + 1}; if they read each other, it is a cycle and belongs `
          + 'in second_pass with reads_rebuilt.');
      }
      if (source && !source.includes(path.basename(rel))) {
        problems.push(`${at}: declares it reads ${rel}, and ${s.command[1]} never names `
          + `${path.basename(rel)}. A read the tool does not make is an edge that holds nothing.`);
      }
    }
  });

  // THE SECOND PASS (T-1363). Its safety rests entirely on every entry naming a
  // step from the list above: re-running a command the sequence already runs adds
  // no tool that `_only_gated_tools` has not gated and `--prove` has not proved.
  // An entry that named a command of its own would slip past both.
  const key = (c) => (Array.isArray(c) ? c : []).join('\u0000');
  const stepAt = new Map(m.steps.map((s, i) => [key(s.command), i]));
  const secondPass = m.second_pass ?? [];
  if (!Array.isArray(secondPass)) problems.push('second_pass must be an array');
  else {
    const seenPass = new Set();
    let lagSeen = false;
    secondPass.forEach((e, i) => {
      const at = `second_pass ${i + 1} (${(e.command ?? []).join(' ')})`;
      if (!Array.isArray(e.command) || e.command.length < 2) {
        problems.push(`${at}: command must be an argv array`);
        return;
      }
      const k = key(e.command);
      if (!stepAt.has(k)) {
        problems.push(`${at}: names no step in the sequence. The second pass may only re-run `
          + 'the sequence\'s own commands — a command listed only here is a derivation '
          + 'nothing gated, proved, or wrote down as part of the layer.');
      }
      if (seenPass.has(k)) problems.push(`${at}: is listed twice — a pass, not a loop`);
      seenPass.add(k);
      if (!e.why || !String(e.why).trim()) {
        problems.push(`${at}: needs a why. A step re-run for an unstated reason is one `
          + 'nobody can ever remove.');
      }
      // THE LAG MUST BE REAL. An entry claiming it reads a file the sequence rebuilds
      // has to point at a step BELOW it that actually resolves that file — otherwise
      // there is no lag and the re-run is cargo.
      if (e.reads_rebuilt !== undefined) {
        if (!Array.isArray(e.reads_rebuilt) || e.reads_rebuilt.length === 0) {
          problems.push(`${at}: reads_rebuilt must be a non-empty array of paths`);
        } else {
          for (const rel of e.reads_rebuilt) {
            const owner = m.steps.findIndex((st) => (st.resolves ?? []).includes(rel));
            if (owner < 0) {
              problems.push(`${at}: claims to read ${rel}, which no step rebuilds — so there `
                + 'is no lag here and nothing to re-run for. Name the file the sequence '
                + 'actually rewrites under it.');
            } else if (owner === stepAt.get(k)) {
              problems.push(`${at}: claims to lag on ${rel}, which it rebuilds itself at step `
                + `${owner + 1}. A step cannot be behind its own output.`);
            } else if (owner < stepAt.get(k)) {
              problems.push(`${at}: claims to read ${rel}, but step ${owner + 1} rebuilds it `
                + `BEFORE step ${stepAt.get(k) + 1} runs — the sequence already settles this `
                + 'one, and a second pass over it is cargo.');
            }
          }
        }
        lagSeen = true;
      } else if (!lagSeen) {
        problems.push(`${at}: is the first entry and states no reads_rebuilt. The pass exists `
          + 'because something reads a file the sequence rebuilds after it; an entry that '
          + 'follows no such reader is repairing nothing. Lead with the lagging reader.');
      }
    });
  }

  // THE SETTLED TAIL AFTER THE PASS (T-1602). It must start at one real step, and
  // that step must sit BELOW every second-pass step — a tail that began above the
  // pass would re-run the cycle the pass just closed and move the population back.
  const after = m.after_the_pass;
  if (after !== undefined) {
    const at = 'after_the_pass';
    const hits = m.steps.map((s, i) => [i, s])
      .filter(([, s]) => s.command.join(' ').includes(String(after.tail_from ?? '').trim() || '\u0000'));
    if (hits.length !== 1) {
      problems.push(`${at}: tail_from must name exactly one step of the sequence; `
        + `${JSON.stringify(after.tail_from)} matches ${hits.length}`);
    } else {
      const passAt = secondPass.map((e) => stepAt.get(key(e.command))).filter((i) => i !== undefined);
      const above = passAt.filter((i) => i >= hits[0][0]);
      if (above.length) {
        problems.push(`${at}: tail_from (step ${hits[0][0] + 1}) is at or above second-pass `
          + `step(s) ${above.map((i) => i + 1).join(', ')}. The tail would re-run the cycle the `
          + 'pass just closed; start it below the pass.');
      }
      const lo = passAt.length ? Math.min(...passAt) : hits[0][0];
      problems.push(...between(m, m.steps.map((_, i) => i)
        .filter((i) => i > lo && i < hits[0][0] && !passAt.includes(i)), passAt));
    }
    if (!Number.isInteger(after.max_laps) || after.max_laps < 2 || after.max_laps > 5) {
      problems.push(`${at}: max_laps must be an integer from 2 to 5 — one lap cannot show `
        + 'that the tree has stopped moving, and more than five is a loop that is not settling');
    }
    if (!after.why || !String(after.why).trim()) problems.push(`${at}: needs a why`);
  }

  if (problems.length) {
    console.error('derived manifest FAILED:');
    for (const p of problems) console.error(`  - ${p}`);
    return 1;
  }
  console.log(`derived manifest OK — ${m.steps.length} step(s), ${allResolved(m).length} `
    + `resolvable file(s), none hand-authored; second pass of ${secondPass.length} step(s)`
    + (after ? `, then the tail from ${after.tail_from} until it settles` : ''));
  return 0;
}

/**
 * THE STEPS BETWEEN THE PASS AND THE TAIL (T-2082, T-1671's step 3). `window` is every
 * step below the pass's first step and above `tail_from` that is not itself in the pass.
 * Nothing re-runs these after the pass moves the population, so each one is safe there
 * only if it reads nothing the pass moves, and that is a measurement, not a property of
 * the code: a source scan says nearly all of them read the resident cards. So the answer
 * is written down, as `after_the_pass.between`, with the date and the perturbation that
 * took it, and held here. A step inserted into the window, or a pass entry that widens
 * it, fails until somebody measures the step the same way and lists it. A step found
 * sensitive does not get listed: it joins the pass or goes below the tail, which is what
 * happened to seat_trade_roofs_1835.py when this was first measured.
 */
function between(m, window, passAt) {
  const problems = [];
  const at = 'after_the_pass.between';
  const b = m.after_the_pass?.between;
  const cmd = (i) => m.steps[i].command.join(' ');
  if (b === undefined) {
    if (window.length) {
      problems.push(`${at}: steps ${window.map((i) => i + 1).join(', ')} sit between the second `
        + 'pass and the tail, where nothing re-runs them after the pass moves the population, '
        + 'and no measured answer says they are safe there. Perturb what the pass writes, '
        + '--check each of them, and record what you found here.');
    }
    return problems;
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(String(b?.measured ?? ''))) {
    problems.push(`${at}: measured must be the date the answer was taken (YYYY-MM-DD)`);
  }
  if (!String(b?.how ?? '').trim()) {
    problems.push(`${at}: needs how: the perturbation that took the answer, so the next step `
      + 'inserted here can be measured the same way');
  }
  const listed = b?.insensitive;
  if (!Array.isArray(listed)) {
    problems.push(`${at}: insensitive must be the array of commands measured safe there`);
    return problems;
  }
  const here = new Set(window.map(cmd));
  for (const i of window) {
    if (!listed.includes(cmd(i))) {
      problems.push(`${at}: step ${i + 1} (${cmd(i)}) sits between the pass and the tail and was `
        + 'never measured there. If it reads what the pass moves, a --run ends with it stale '
        + 'and nothing says so. Measure it the way `how` says and list it, or, if it moves, put '
        + 'it in second_pass or below tail_from.');
    }
  }
  listed.forEach((c, j) => {
    if (listed.indexOf(c) !== j) problems.push(`${at}: lists ${c} twice`);
    else if (!here.has(c)) {
      problems.push(`${at}: lists ${c}, which does not sit between the pass and the tail. The `
        + 'answer is a reading of the steps actually there; take it off.');
    }
  });
  // A DECLARED read of a file a pass step rewrites is the one edge the answer must name.
  // It is the case most likely to move, so it gets its own measured why.
  const rewrites = new Map();
  for (const i of passAt) for (const rel of m.steps[i].resolves ?? []) rewrites.set(rel, i);
  const readers = b.declared_readers ?? {};
  if (typeof readers !== 'object' || Array.isArray(readers)) {
    problems.push(`${at}: declared_readers must map a command to its measured why`);
    return problems;
  }
  const owed = new Set();
  for (const i of window) {
    const hit = (m.steps[i].reads ?? []).filter((rel) => rewrites.has(rel));
    if (!hit.length) continue;
    owed.add(cmd(i));
    if (!String(readers[cmd(i)] ?? '').trim()) {
      problems.push(`${at}: step ${i + 1} (${cmd(i)}) declares it reads ${hit.map((rel) => `${rel} `
        + `(rewritten by pass step ${rewrites.get(rel) + 1})`).join(', ')}. Say in `
        + 'declared_readers why that rewrite does not move it, measured, or put it in the pass.');
    }
  }
  for (const c of Object.keys(readers)) {
    if (!owed.has(c)) {
      problems.push(`${at}: declared_readers names ${c}, which declares no read of a file the `
        + 'pass rewrites, or is not between the pass and the tail. A why for an edge that is '
        + 'not there is cargo.');
    }
  }
  return problems;
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
  const exec = (command, label) => {
    try {
      execFileSync(command[0], command.slice(1), { cwd: APP, stdio: ['ignore', 'pipe', 'pipe'] });
      return true;
    } catch (e) {
      console.error(`  FAILED: ${label}`);
      console.error(`${e.stdout ?? ''}${e.stderr ?? ''}`.split('\n').slice(-8).map((l) => `    ${l}`).join('\n'));
      return false;
    }
  };

  for (const [i, s] of m.steps.entries()) {
    const label = s.command.join(' ');
    process.stdout.write(`  [${i + 1}/${m.steps.length}] ${label}\n`);
    if (!exec(s.command, label)) return 1;
  }

  // AND THEN THE CYCLE, ONCE MORE, FROM A SETTLED MODEL (T-1363). Without this the
  // run ends with the arrival draws standing on the model as it was before the run
  // moved the population, and the gate goes red on ~1,400 cards. See
  // `_the_second_pass` in the manifest for the measurement.
  const secondPass = m.second_pass ?? [];
  for (const [i, e] of secondPass.entries()) {
    const label = e.command.join(' ');
    process.stdout.write(`  [second pass ${i + 1}/${secondPass.length}] ${label}\n`);
    if (!exec(e.command, label)) return 1;
  }

  console.log(`derived layer rebuilt — ${m.steps.length} step(s) in dependency order, then a `
    + `second pass of ${secondPass.length} over the steps that read what the sequence rebuilds`);

  // AND EVERYTHING THAT READS THE CARDS THE PASS JUST MOVED, UNTIL IT STOPS MOVING
  // (T-1602). Without this a `--run` on a branch that moved the population ended with
  // the scene, its generators and their sidecars standing on the pre-pass cards, and
  // only the lap's own late `--tail` — or a person — knew to fix it.
  if (!m.after_the_pass) return 0;
  const first = tailFrom(m.after_the_pass.tail_from, m);
  if (first < 0) return 1;
  return runFrom(first, m);
}

/**
 * WHAT THE TREE UNDER chicago/4d HOLDS RIGHT NOW, AS ONE GIT TREE ID (T-1602).
 *
 * Written into a throwaway copy of the index, so the real one — mid-merge, during
 * `--resolve` — is never touched. Copying the index keeps its stat cache, so only the
 * files a lap actually rewrote are hashed again. Returns null outside a git checkout,
 * and the caller then runs one lap and does not claim to know whether it settled.
 */
function treeState() {
  const tmp = path.join(tmpdir(), `c4d-rederive-index-${process.pid}`);
  try {
    const index = path.resolve(REPO, execFileSync('git', ['rev-parse', '--git-path', 'index'],
      { cwd: REPO, encoding: 'utf8' }).trim());
    if (existsSync(index)) copyFileSync(index, tmp);
    const env = { ...process.env, GIT_INDEX_FILE: tmp };
    execFileSync('git', ['add', '-A', '--', path.relative(REPO, APP)], { cwd: REPO, env, stdio: 'ignore' });
    return execFileSync('git', ['write-tree'], { cwd: REPO, env, encoding: 'utf8' }).trim();
  } catch {
    return null;
  } finally {
    rmSync(tmp, { force: true });
  }
}

/* --------------------------------------------------------------------- tail */

/**
 * THE STEPS FROM ONE NAMED STEP TO THE END, IN MANIFEST ORDER (T-1661).
 *
 * `--run` is the whole sequence and settles everything. This is for the caller
 * that has to re-run ONE step late — pr-lap.sh does, because the second pass
 * rewrites the resident cards `compile_scene.py` reads, so the scene the
 * sequence built is stale by the time the sequence ends. Re-running that step
 * BARE is what T-1661 measured: `compile_source_use.py` is the very next step of
 * the manifest and it exports "current-scene membership" out of
 * data/sidecars/1835/index.json and people.json — the two files compile_scene
 * writes — so the lap pushed a tree whose source-use had been derived against
 * the PRE-merge scene. On PR #105 that silently dropped 38 of
 * owner_chicago_1835_reconstruction_spec_2026's claims (3582 written where a
 * correct derivation gives 3620) and took three steps of check.sh red on a
 * branch GitHub reported as merged and up to date.
 *
 * So a late re-run is never one step: it is that step and everything the
 * manifest places below it. Naming the step and letting the manifest supply the
 * rest is the point — insert a step after compile_scene.py tomorrow and the lap
 * picks it up with no edit, which a hand-written pair of commands would not.
 *
 * NO SECOND PASS. The pass walks the residents/model cycle once more (see
 * `_the_second_pass`), and its own steps sit ABOVE this tail — `--check` holds that
 * for `after_the_pass` — so running it again here would move the population under
 * the very steps this tail just settled. The caller has already had it from `--run`.
 */
function tailFrom(from, m = load()) {
  const name = (from ?? '').trim();
  if (!name) {
    console.error('--tail needs the step to start from, e.g. --tail tools/compile_scene.py');
    return -1;
  }
  const hits = m.steps
    .map((s, i) => [i, s])
    .filter(([, s]) => s.command.join(' ').includes(name));
  if (hits.length !== 1) {
    console.error(hits.length === 0
      ? `--tail ${name}: no step of the manifest runs that`
      : `--tail ${name}: ${hits.length} steps run that — name one`);
    hits.forEach(([i, s]) => console.error(`    [${i + 1}] ${s.command.join(' ')}`));
    return -1;
  }
  return hits[0][0];
}

function tail(from, m = load()) {
  const first = tailFrom(from, m);
  if (first < 0) return 1;
  return runFrom(first, m);
}

/**
 * A TAIL, REPEATED UNTIL A LAP CHANGES NOTHING (T-1602). The scene and its generators
 * read each other — compile_scene.py reads the structure records the infill
 * generators write, and they read the sidecars it writes — so one lap can leave the
 * sidecars a lap behind. A settled tree costs exactly one lap: the one that shows
 * nothing moved. Still moving after `max_laps` is reported, not hidden, and check.sh
 * stays the proof either way.
 */
function runFrom(first, m = load()) {
  const run_ = m.steps.slice(first);
  const maxLaps = m.after_the_pass?.max_laps ?? 1;
  for (let lap = 1; lap <= maxLaps; lap += 1) {
    const before = maxLaps > 1 ? treeState() : null;
    if (lap > 1) process.stdout.write(`  — lap ${lap} of at most ${maxLaps}: the last one moved the tree —\n`);
    for (const [i, s] of run_.entries()) {
      const label = s.command.join(' ');
      process.stdout.write(`  [${first + i + 1}/${m.steps.length}] ${label}\n`);
      try {
        execFileSync(s.command[0], s.command.slice(1), { cwd: APP, stdio: ['ignore', 'pipe', 'pipe'] });
      } catch (e) {
        console.error(`  FAILED: ${label}`);
        console.error(`${e.stdout ?? ''}${e.stderr ?? ''}`.split('\n').slice(-8).map((l) => `    ${l}`).join('\n'));
        return 1;
      }
    }
    const after = before ? treeState() : null;
    if (!before || !after || before === after) {
      console.log(`derived layer rebuilt from step ${first + 1} — ${run_.length} step(s) in manifest `
        + `order, ${lap} lap(s)${before && after ? ', and the last one moved nothing' : ''}; `
        + 'no second pass (it sits above this tail)');
      return 0;
    }
  }
  console.error(`WARNING: the tail from step ${first + 1} was still moving the tree after `
    + `${maxLaps} laps. Something below it is not converging — ./tools/check.sh will say which.`);
  return 0;
}

/* ------------------------------------------------------------------ resolve */

/**
 * THE LAP'S RESOLUTION, FOR A MERGE IN A CLONE (2026-09-28).
 *
 * pr-lap.sh clears a conflict in the derived layer on the server side: take either
 * side, rebuild from source. A merge made by hand in a clone had no such step.
 * Measured on PR #137 on 2026-09-27: its merge of `dev` conflicted TWICE in
 * data/sidecars/1835/sources/ (index.json, andreas_1884_v1.json,
 * chicago_democrat_1833_1835.json), and each time it was cleared by hand with the
 * same two moves the lap makes. #130 hit the same files. They conflict on any two branches that both touch a
 * citation, because the backlink files are one derivation of every citation.
 *
 * A merge driver cannot do this. git runs a driver on ONE FILE while the merge is
 * still going, before the inputs that file is derived from have been merged, so
 * the most a driver can do is keep one side. The rebuild has to come after the
 * merge. So this is a step, not a driver:
 *
 *   git merge origin/dev           conflicts in derived files are left standing
 *   node tools/rederive.mjs --resolve
 *   ./tools/check.sh               the proof, as it is for the lap
 *   git commit
 *
 * It clears ONLY paths the manifest lists (and never one that declares
 * hand_authored). If anything else is still unmerged it refuses and touches
 * nothing, because the rebuild reads its inputs and an input with markers in it is
 * not an input. Resolve those by hand first, then run it again.
 *
 * NARROWEST CORRECT REBUILD. It runs `--tail` from the earliest step that owns a
 * conflicted file, so a conflict only in the source backlinks costs the last
 * handful of steps, not all 160. But if that step sits at or above a
 * second-pass step, `--tail` cannot settle the residents/model cycle (see `tail`),
 * so the whole `--run` is taken instead.
 */
function resolvePlan(unmerged, m = load(), handAuthoredOurs = () => false) {
  const owner = new Map();
  m.steps.forEach((s, i) => (s.resolves ?? []).forEach((r) => { if (!owner.has(r)) owner.set(r, i); }));
  const paths = unmerged.map(normalise);
  const refused = paths.filter((p) => owner.has(p) && handAuthoredOurs(p));
  const derived = paths.filter((p) => owner.has(p) && !handAuthoredOurs(p));
  const other = paths.filter((p) => !owner.has(p)).concat(refused);
  if (derived.length === 0 || other.length) return { derived, other, first: -1, full: false };
  const first = Math.min(...derived.map((p) => owner.get(p)));
  const passKeys = new Set((m.second_pass ?? []).map((e) => e.command.join(' ')));
  const passAt = m.steps.map((s, i) => [i, s]).filter(([, s]) => passKeys.has(s.command.join(' ')))
    .map(([i]) => i);
  const full = passAt.some((i) => i >= first);
  return { derived, other, first, full };
}

function resolveMerge(m = load()) {
  const git = (...a) => execFileSync('git', a, { cwd: REPO, encoding: 'utf8' });
  let unmerged;
  try {
    unmerged = git('diff', '--name-only', '--diff-filter=U').split('\n').filter(Boolean);
  } catch (e) {
    console.error(`--resolve: could not list unmerged paths — ${String(e.message).split('\n')[0]}`);
    return 1;
  }
  if (unmerged.length === 0) {
    console.log('--resolve: nothing is unmerged — no conflict to clear');
    return 0;
  }
  // hand_authored is read from OUR side of the index (stage 2): the working copy
  // has conflict markers in it and would not parse, which would read as "no".
  const oursDeclares = (rel) => {
    if (!rel.endsWith('.json')) return false;
    try { return JSON.parse(git('show', `:2:${rel}`)).hand_authored === true; } catch { return false; }
  };
  const plan = resolvePlan(unmerged, m, oursDeclares);
  if (plan.other.length) {
    console.error(`--resolve: ${plan.other.length} unmerged path(s) are not the manifest's to clear:`);
    plan.other.forEach((p) => console.error(`  - ${p}`));
    console.error(`\nNothing was touched. Resolve ${plan.other.length === 1 ? 'it' : 'those'} by hand `
      + '(they are inputs or authored), `git add` them, and run --resolve again');
    if (plan.derived.length) {
      console.error(`for the ${plan.derived.length} derived file(s) still conflicting, which it `
        + 'will rebuild from the merged inputs.');
    }
    return 1;
  }

  console.log(`--resolve: ${plan.derived.length} conflicting file(s), all rebuilt from source by the manifest`);
  git('checkout', '--ours', '--', ...plan.derived);

  // The manifest's LAST step reads the published mirror and refuses without it
  // (see pr-lap.sh `lap_publish_mirror`, T-1521), and every tail reaches that step.
  try {
    execFileSync('bash', ['tools/publish.sh'], { cwd: APP, stdio: ['ignore', 'pipe', 'pipe'] });
  } catch (e) {
    console.error('--resolve: the publish the rebuild reads failed:');
    console.error(`${e.stdout ?? ''}${e.stderr ?? ''}`.split('\n').slice(-6).map((l) => `    ${l}`).join('\n'));
    return 1;
  }

  const status = plan.full ? run(m) : runFrom(plan.first, m);
  if (status !== 0) {
    console.error('--resolve: the rebuild failed. The conflicted files hold OUR side and are NOT added.');
    return status;
  }

  // Stage every manifest-owned file the rebuild moved, not just the conflicted
  // ones: a rebuild that rewrote a file the merge left clean has to ride the same
  // commit, or that commit ships a tree that does not re-derive.
  const owned = new Set(allResolved(m));
  const moved = git('diff', '--name-only').split('\n').filter((p) => p && owned.has(p));
  const stage = [...new Set([...plan.derived, ...moved])];
  git('add', '--', ...stage);
  console.log(`--resolve: ${stage.length} file(s) staged (${plan.derived.length} were conflicting).`);
  console.log('Next: ./tools/check.sh — the proof, as it is for the lap — then `git commit`.');
  return 0;
}

/* ------------------------------------------------------------------ callers */

/**
 * NO CALLER RE-RUNS A MANIFEST STEP BARE (T-1661).
 *
 * The hole `tail` fills can be reopened by one line in a shell script, silently,
 * and the tree it produces is wrong in a way only the gate can see. So the gate
 * reads the scripts: any `python3 tools/<x>.py` a caller runs that the manifest
 * also runs must either BE the manifest's last step or go through `--tail`.
 * Comment lines are not calls — pr-lap.sh explains itself at length and names
 * these tools while doing it.
 */
function callers(scripts, m = load()) {
  if (scripts.length === 0) {
    console.error('--callers needs the script(s) to read');
    return 1;
  }
  const problems = [];
  let calls = 0;
  for (const script of scripts) {
    const abs = path.isAbsolute(script) ? script : path.join(REPO, script);
    if (!existsSync(abs)) { problems.push(`${script}: no such file`); continue; }
    const lines = readFileSync(abs, 'utf8').split('\n')
      .filter((l) => !/^\s*#/.test(l));
    m.steps.forEach((s, i) => {
      const tool = s.command.find((a) => /^tools\/.+\.py$/.test(a));
      if (!tool) return;
      const bare = new RegExp(`python3?\\s+${tool.replace(/[.]/g, '\\.')}(\\s|$)`);
      const hit = lines.findIndex((l) => bare.test(l));
      if (hit < 0) return;
      calls += 1;
      if (i < m.steps.length - 1) {
        problems.push(`${script}: runs \`python3 ${tool}\` bare, and the manifest places `
          + `${m.steps.length - 1 - i} step(s) after it (it is step ${i + 1} of ${m.steps.length}) `
          + `— re-run it with \`node tools/rederive.mjs --tail ${tool}\``);
      }
    });
  }
  if (problems.length) {
    problems.forEach((p) => console.error(`  ${p}`));
    console.error(`callers of the derived manifest: ${problems.length} out-of-sequence re-run(s)`);
    return 1;
  }
  console.log(`callers of the derived manifest OK — ${scripts.length} script(s) read, `
    + `${calls} manifest step(s) re-run bare, none with a step below it`);
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
  const gz = 'chicago/4d/data/research/location_reconciliation.json.gz';
  const stepOf = (t) => real.steps.findIndex((s) => s.command[1] === t);
  check_('both readers of the location reconciliation declare it and sit below it (T-2080)',
    ['tools/location_spend.py', 'tools/report_convergence_coverage.py'].every((t) =>
      (real.steps[stepOf(t)]?.reads ?? []).includes(gz)
        && stepOf(t) > stepOf('tools/location_reconciliation.py')));

  console.log('\n  the second pass that closes the cycle (T-1363)');
  const pass = real.second_pass ?? [];
  const k = (c) => c.join('\u0000');
  check_('the shipped manifest declares one', pass.length > 0, `${pass.length} step(s)`);
  check_('every entry re-runs a command the sequence already runs — no new tool sneaks in',
    pass.every((e) => real.steps.some((s) => k(s.command) === k(e.command))));
  check_('the model leads it, lagging on the scene and the census rebuilt below it (T-1602)',
    (pass[0]?.command ?? []).join(' ').includes('model_town_1835.py')
      && ['chicago/4d/data/sidecars/1835/people.json', 'chicago/4d/data/town_census.json']
        .every((rel) => (pass[0]?.reads_rebuilt ?? []).includes(rel)));
  check_('and the arrival stage, which draws from the model, follows it',
    (pass[1]?.command ?? []).join(' ').includes('attribute_fill_arrival')
      && Array.isArray(pass[1]?.reads_rebuilt));
  check_('every file an entry lags on IS rebuilt by a later step — the lag is real, not cargo',
    pass.filter((e) => e.reads_rebuilt).every((e) => e.reads_rebuilt.every((rel) => {
      const owner = real.steps.findIndex((s) => (s.resolves ?? []).includes(rel));
      const mine = real.steps.findIndex((s) => k(s.command) === k(e.command));
      return owner > mine && mine >= 0;
    })));
  check_('every entry says why it is re-run', pass.every((e) => String(e.why ?? '').trim().length > 0));

  console.log('\n  and after the pass, the tail that reads what it moved, until it settles (T-1602)');
  const after = real.after_the_pass ?? {};
  check_('the shipped manifest declares it, from compile_scene.py — the lap\'s own late step',
    after.tail_from === 'tools/compile_scene.py' && tailFrom(after.tail_from, real) >= 0);
  check_('it may take more than one lap, because the scene and its generators read each other',
    Number.isInteger(after.max_laps) && after.max_laps >= 2, `max_laps ${after.max_laps}`);

  console.log('\n  a late re-run is that step and everything below it (T-1661)');
  const scene = 'tools/compile_scene.py';
  check_('the step a caller re-runs late is found, and it is not the last one',
    tailFrom(scene, real) >= 0 && tailFrom(scene, real) < real.steps.length - 1,
    `step ${tailFrom(scene, real) + 1} of ${real.steps.length}`);
  check_('the scene tail rebuilds jaunts before source-use consumes their claims (T-1253)',
    (real.steps[tailFrom(scene, real) + 1]?.command ?? []).join(' ').includes('compile_jaunts.py')
    && (real.steps[tailFrom(scene, real) + 2]?.command ?? []).join(' ').includes('compile_source_use.py'));
  check_('a name no step runs is refused, not silently skipped', tailFrom('tools/no_such.py', real) === -1);
  check_('a name MANY steps run is refused — the tail has one start', tailFrom('tools/generate_', real) === -1);
  check_('no argument at all is refused', tailFrom('', real) === -1);
  check_('the second pass sits ABOVE the tail, so the tail must not re-run it',
    (real.second_pass ?? []).every((e) => real.steps
      .findIndex((st) => k(st.command) === k(e.command)) < tailFrom(scene, real)));

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

    // …and the declared reads (T-2080): the order that shipped until then is the
    // first case, and it must be refused.
    const recon = { command: ['python3', 'tools/location_reconciliation.py', '--build'], resolves: [gz] };
    const spend = { command: ['python3', 'tools/location_spend.py', '--build'], resolves: [], reads: [gz] };
    check_('a reader ABOVE the step that rebuilds what it reads — the order before T-2080',
      bad([spend, recon]) === 1);
    check_('the same reader BELOW it is accepted', bad([recon, spend]) === 0);
    check_('a declared read of a file no step rebuilds — no edge to hold',
      bad([recon, { ...spend, reads: ['chicago/4d/data/town_census.json'] }]) === 1);
    check_('a declared read the tool\'s own source never names — cargo',
      bad([recon, { command: ['python3', 'tools/compile_scene.py'], resolves: [], reads: [gz] }]) === 1);
    check_('an empty reads list', bad([recon, { ...spend, reads: [] }]) === 1);

    // …and the second pass's own assertions. Each is a way the pass could quietly
    // stop meaning anything: a tool nothing gated, a claimed lag that is not one,
    // a repair with nothing above it to repair, a loop written as a pass.
    const withPass = (second_pass) => {
      const f = path.join(tmp, 'p.json');
      writeFileSync(f, JSON.stringify({
        schema: 1,
        steps: [
          { command: ['python3', 'tools/compile_scene.py'], resolves: [] },
          { command: ['python3', 'tools/model_town_1835.py', '--build'],
            resolves: ['chicago/4d/data/reconstruction/1835_town_model.json'] },
        ],
        second_pass,
      }));
      return check(load(f));
    };
    const reader = {
      command: ['python3', 'tools/compile_scene.py'],
      reads_rebuilt: ['chicago/4d/data/reconstruction/1835_town_model.json'],
      why: 'reads the model the step below rebuilds',
    };
    check_('a well-formed pass is accepted', withPass([reader]) === 0);
    check_('an entry naming no step in the sequence — an ungated, unproved derivation',
      withPass([{ command: ['python3', 'tools/no_such_tool.py'], why: 'x' }]) === 1);
    check_('an entry with no why — a re-run nobody can ever remove',
      withPass([{ ...reader, why: '  ' }]) === 1);
    check_('the same entry twice — a pass, not a loop',
      withPass([reader, reader]) === 1);
    check_('a claimed lag on a file NO step rebuilds',
      withPass([{ ...reader, reads_rebuilt: ['chicago/4d/data/town_census.json'] }]) === 1);
    check_('a claimed lag on a file rebuilt BEFORE the entry runs — the sequence settles it',
      withPass([{
        command: ['python3', 'tools/model_town_1835.py', '--build'],
        reads_rebuilt: ['chicago/4d/data/reconstruction/1835_town_model.json'],
        why: 'reads what it rebuilds itself',
      }]) === 1);
    check_('a repair with no lagging reader above it — it is repairing nothing',
      withPass([{ command: ['python3', 'tools/compile_scene.py'], why: 'downstream of nothing' }]) === 1);

    const withAfter = (after_the_pass) => {
      const f = path.join(tmp, 'a.json');
      writeFileSync(f, JSON.stringify({
        schema: 1,
        steps: [
          { command: ['python3', 'tools/compile_scene.py'], resolves: [] },
          { command: ['python3', 'tools/model_town_1835.py', '--build'],
            resolves: ['chicago/4d/data/reconstruction/1835_town_model.json'] },
          { command: ['python3', 'tools/town_census.py'], resolves: [] },
        ],
        second_pass: [reader],
        after_the_pass,
      }));
      return check(load(f));
    };
    // compile_scene.py is the pass, town_census.py the tail; model_town_1835.py sits between.
    const answered = { measured: '2026-10-04', how: 'perturb what the pass writes, --check each',
      insensitive: ['python3 tools/model_town_1835.py --build'] };
    const settle = { tail_from: 'tools/town_census.py', max_laps: 3, why: 'reads what the pass moved',
      between: answered };
    check_('a settled tail below the pass is accepted', withAfter(settle) === 0);
    check_('a settled tail starting AT a pass step — it would re-open the cycle',
      withAfter({ ...settle, tail_from: 'tools/compile_scene.py' }) === 1);
    check_('a settled tail naming no step', withAfter({ ...settle, tail_from: 'tools/no_such.py' }) === 1);
    check_('a settled tail of one lap — one lap cannot show the tree stopped moving',
      withAfter({ ...settle, max_laps: 1 }) === 1);
    check_('a settled tail with no why', withAfter({ ...settle, why: '' }) === 1);

    console.log('\n  and the steps between the pass and the tail are a measured answer, held (T-2082)');
    const real_between = real.after_the_pass?.between ?? {};
    check_('the shipped answer lists steps, and says when and how it was taken',
      (real_between.insensitive ?? []).length > 0 && /^\d{4}-\d{2}-\d{2}$/.test(real_between.measured ?? '')
      && String(real_between.how ?? '').length > 0, `${(real_between.insensitive ?? []).length} step(s)`);
    check_('seat_trade_roofs_1835.py, measured to move with the deals, is in the pass and not the answer',
      (real.second_pass ?? []).some((e) => k(e.command).includes('seat_trade_roofs_1835.py'))
      && !(real_between.insensitive ?? []).some((c) => c.includes('seat_trade_roofs_1835.py')));
    check_('a window with no answer at all — the hole T-1671 found',
      withAfter({ ...settle, between: undefined }) === 1);
    check_('a step INSERTED into the window that nobody measured',
      withAfter({ ...settle, between: { ...answered, insensitive: [] } }) === 1);
    check_('a listed step that is not between the pass and the tail',
      withAfter({ ...settle, between: { ...answered,
        insensitive: [...answered.insensitive, 'python3 tools/town_census.py'] } }) === 1);
    check_('a step listed twice',
      withAfter({ ...settle, between: { ...answered,
        insensitive: [...answered.insensitive, ...answered.insensitive] } }) === 1);
    check_('an answer with no date', withAfter({ ...settle, between: { ...answered, measured: 'today' } }) === 1);
    check_('an answer that does not say how it was taken',
      withAfter({ ...settle, between: { ...answered, how: ' ' } }) === 1);
    const withReader = (between_) => {
      const f = path.join(tmp, 'r.json');
      const model = ['python3', 'tools/model_town_1835.py', '--build'];
      writeFileSync(f, JSON.stringify({
        schema: 1,
        steps: [
          { command: model, resolves: ['chicago/4d/data/reconstruction/1835_town_model.json'] },
          { command: ['python3', 'tools/town_census.py'], resolves: [],
            reads: ['chicago/4d/data/reconstruction/1835_town_model.json'] },
          { command: ['python3', 'tools/compile_scene.py'], resolves: ['chicago/4d/data/sidecars/1835/people.json'] },
        ],
        second_pass: [{ command: model, reads_rebuilt: ['chicago/4d/data/sidecars/1835/people.json'], why: 'lags' }],
        after_the_pass: { tail_from: 'tools/compile_scene.py', max_laps: 3, why: 'x', between: between_ },
      }));
      return check(load(f));
    };
    const census = { measured: '2026-10-04', how: 'x', insensitive: ['python3 tools/town_census.py'] };
    const readerWhy = { 'python3 tools/town_census.py': 'measured still when the model moved' };
    check_('a step declaring it reads what the pass rewrites, with its measured why, is accepted',
      withReader({ ...census, declared_readers: readerWhy }) === 0);
    check_('the same declared read with no why — the edge most likely to move',
      withReader(census) === 1);
    check_('a why for a read the step does not declare is cargo',
      withReader({ ...census, declared_readers: { ...readerWhy, 'python3 tools/compile_scene.py': 'x' } }) === 1);

    console.log('\n  and a merge in a clone resolves the way the lap does (--resolve)');
    const src = (id) => `chicago/4d/data/sidecars/1835/sources/${id}.json`;
    const srcAt = real.steps.findIndex((st) => st.command.join(' ').includes('compile_source_use'));
    const p137 = resolvePlan([src('index'), src('andreas_1884_v1'), src('chicago_democrat_1833_1835')], real);
    check_('#137\'s three source backlinks are all the manifest\'s to clear',
      p137.derived.length === 3 && p137.other.length === 0, JSON.stringify(p137.other));
    check_('and they cost a tail from compile_source_use, not the whole sequence',
      p137.first === srcAt && p137.full === false, `first ${p137.first}, full ${p137.full}`);
    const pMixed = resolvePlan([src('index'), 'chicago/4d/data/residents/households/hh_taylor_c.json'], real);
    check_('an authored input still unmerged refuses the set — the rebuild would read its markers',
      pMixed.other.length === 1 && pMixed.first === -1);
    const pHand = resolvePlan(['chicago/4d/data/research/land_sales/resident_crosswalk.json'], real,
      () => true);
    check_('a listed file whose ours declares hand_authored is refused',
      pHand.other.length === 1 && pHand.first === -1);
    const pEarly = resolvePlan(['chicago/4d/data/research/land_sales/resident_crosswalk.json'], real);
    check_('a conflict above the second pass takes the whole --run — a tail cannot settle the cycle',
      pEarly.full === true);

    console.log('\n  and no caller re-runs a manifest step bare (T-1661)');
    const script = (body) => {
      const f = path.join(tmp, 'caller.sh');
      writeFileSync(f, body);
      return callers([f], real);
    };
    const last = real.steps[real.steps.length - 1].command.find((a) => /^tools\/.+\.py$/.test(a));
    check_('the lap that ships is in sequence', callers(['.github/steward/pr-lap.sh'], real) === 0);
    check_('a bare re-run of the scene is refused — this is T-1661 itself',
      script('set -e\ncd chicago/4d\npython3 tools/compile_scene.py --all\n') === 1);
    check_('the same call through --tail is accepted',
      script('set -e\ncd chicago/4d\nnode tools/rederive.mjs --tail tools/compile_scene.py\n') === 0);
    check_('a COMMENT naming the tool is not a call — pr-lap.sh explains itself at length',
      script('set -e\n# python3 tools/compile_scene.py --all is what this used to do\n') === 0);
    check_('the manifest LAST step re-run bare is accepted — nothing is below it',
      script(`set -e\npython3 ${last} --build\n`) === 0);
    check_('a script that is not there is refused, not read as clean',
      callers([path.join(tmp, 'no-such-script.sh')], real) === 1);
    check_('no script at all is refused', callers([], real) === 1);
  } finally { rmSync(tmp, { recursive: true, force: true }); }

  console.log(`\n${failures === 0 ? 'rederive self-test: all pass' : `rederive self-test: ${failures} FAILURE(S)`}`);
  return failures === 0 ? 0 : 1;
}

/* ------------------------------------------------------------------- main */

if (has('self-test')) process.exit(await selfTest());
else if (has('resolvable')) process.exit(resolvable(rest()));
else if (has('prove')) process.exit(prove());
else if (has('run')) process.exit(run());
else if (has('tail')) process.exit(tail(rest()[0]));
else if (has('resolve')) process.exit(resolveMerge());
else if (has('callers')) process.exit(callers(rest()));
else process.exit(check());

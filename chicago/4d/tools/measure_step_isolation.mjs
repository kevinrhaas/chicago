#!/usr/bin/env node
/**
 * measure_step_isolation.mjs — what every gate step WRITES, measured rather than assumed.
 *
 *   node tools/measure_step_isolation.mjs --build     run the gate instrumented, write the file
 *   node tools/measure_step_isolation.mjs --self-test prove the reader's own assertions fire
 *
 * WHY THIS EXISTS (T-1339, out of T-1336). check.sh runs its steps in a job pool over ONE
 * working tree. A step that mutates that tree — even for the fraction of a second a
 * self-test needs to prove a check fires on a drift — is read by whatever runs beside it,
 * and the gate reports red on a tree that is green. Four PRs went red that way in one
 * afternoon before the cause was found, and each looked like a defect.
 *
 * T-1336 fixed the six offenders it found and put a retry behind them: a step that fails
 * in the pool is re-run once the pool has drained, and named if it then passes. That makes
 * the VERDICT correct. It does not stop the seventh being written — and two of the six
 * carried comments claiming they already worked on a copy, so a convention is not enough.
 *
 * SO THE ANSWER IS A MEASUREMENT, exactly as T-1302 answered "which tools write?" with
 * tools/writer_inventory.json rather than a pattern over the source. Behaviour is the only
 * thing that can answer this, behaviour is too slow for a per-commit gate, so the slow part
 * is run here and the gate reads the file (tools/audit_step_isolation.mjs).
 *
 * HOW. One instrumented gate run, not a second sweep. PYTHONPATH reaches every python
 * subprocess through `sitecustomize`, NODE_OPTIONS=--require reaches every node one, and
 * each records the files it opened for writing that resolve INSIDE the repo. A tool writing
 * its own tempdir is doing the right thing and is not recorded — that distinction is the
 * whole measurement, and getting it wrong once already produced a false finding
 * (resolve_id_collisions.mjs copies two tools OUT to a fixture; an early probe read the
 * SOURCE argument of copyFileSync and reported it as a writer).
 */
import { execFileSync, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const APP = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const ROOT = execFileSync('git', ['rev-parse', '--show-toplevel'], { cwd: APP, encoding: 'utf8' }).trim();
const OUT = path.join(APP, 'tools', 'step_isolation.json');
const PROBE = path.join(APP, 'tools', 'isolation_probe');

/** A gate step's command, as check.sh declares it — the key both files agree on. */
export function declaredSteps(checkSh) {
  const lines = checkSh.split('\n');
  const out = [];
  for (let i = 0; i < lines.length; i++) {
    const m = /^\s*(step|selftest)\s/.exec(lines[i]);
    if (!m) continue;
    // A declaration is `step "label" \` with the command on the lines below, or a
    // single line calling a shell function. Join continuations before splitting.
    let joined = lines[i];
    while (/\\\s*$/.test(joined) && i + 1 < lines.length) joined = joined.replace(/\\\s*$/, '') + ' ' + lines[++i].trim();
    // strip `step`/`selftest` and the quoted label that follows it
    const rest = joined.replace(/^\s*(step|selftest)\s+/, '');
    const lab = /^"((?:[^"\\]|\\.)*)"\s*/.exec(rest);
    const cmd = (lab ? rest.slice(lab[0].length) : rest).trim();
    if (cmd) out.push({ kind: m[1], command: cmd.replace(/\s+/g, ' ') });
  }
  return out;
}

/** The tool a command runs, or null when it is a shell function or a shell wrapper. */
export function toolOf(command) {
  // The leading boundary allows a QUOTE as well as whitespace: check.sh really does
  // carry `sh -c 'python3 tools/select_resident_research_pilot.py --self-test …'`, and a
  // \s-only boundary silently skipped it — caught by this tool's own self-test.
  const m = /(?:^|[\s'"])(?:python3|node)\s+(tools\/[A-Za-z0-9_.\-]+\.(?:py|mjs))(?:[\s'"]|$)/.exec(command);
  return m ? m[1] : null;
}

function build() {
  const jsonl = fs.mkdtempSync('/tmp/c4d-iso-') + '/probe.jsonl';
  fs.writeFileSync(jsonl, '');
  const env = {
    ...process.env,
    ISOLATION_ROOT: ROOT,
    ISOLATION_OUT: jsonl,
    PYTHONPATH: PROBE + (process.env.PYTHONPATH ? ':' + process.env.PYTHONPATH : ''),
    NODE_OPTIONS: `--require ${path.join(PROBE, 'node_probe.js')}` + (process.env.NODE_OPTIONS ? ' ' + process.env.NODE_OPTIONS : ''),
    CHECK_JOBS: '1',   // serial, so no step can be blamed for a neighbour's writes
  };
  console.log('running the gate instrumented (serial, so a write is attributable)…');
  const r = spawnSync('bash', ['tools/check.sh'], { cwd: APP, env, encoding: 'utf8', maxBuffer: 1 << 28 });
  const verdict = /^CHECK (PASS|FAIL)/m.exec((r.stdout || '').replace(/\x1b\[[0-9;]*m/g, ''));

  // Aggregated by tool, but the INVOCATION that wrote is kept beside the paths. A tool
  // like ticket.mjs is spawned by eight fixture harnesses as well as by the gate itself,
  // and "tools/ticket.mjs writes BOARD.md" is not actionable without knowing which of the
  // nine did it — the row has to say enough to find the step.
  const byTool = new Map();
  for (const line of fs.readFileSync(jsonl, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    let d; try { d = JSON.parse(line); } catch { continue; }
    const argv0 = (d.argv || [])[0] || '';
    const tool = argv0.includes('tools/') ? 'tools/' + argv0.split('tools/').pop() : argv0;
    const prev = byTool.get(tool) || { wrote: new Set(), by: new Set() };
    for (const w of d.wrote || []) prev.wrote.add(w);
    if ((d.wrote || []).length) prev.by.add((d.argv || []).join(' ').trim());
    byTool.set(tool, prev);
  }

  const steps = declaredSteps(fs.readFileSync(path.join(APP, 'tools', 'check.sh'), 'utf8'));
  const tools = {};
  for (const t of [...byTool.keys()].sort()) {
    const v = byTool.get(t);
    tools[t] = { wrote: [...v.wrote].sort() };
    if (v.by.size) tools[t].wrote_by = [...v.by].sort();
  }

  // EXEMPTIONS SURVIVE A REGENERATION. They are written by a person with a reason and the
  // measurement must not silently drop them on the next --build; a rebuild that quietly
  // reopened a decided question would be worse than no file.
  let exempt = {};
  try { exempt = JSON.parse(fs.readFileSync(OUT, 'utf8')).exempt || {}; } catch {}

  const doc = {
    schema: 1,
    _doc: 'MEASURED by tools/measure_step_isolation.mjs --build (T-1339). One row per tool the '
      + 'gate ran, listing every file it opened for writing INSIDE the repo. A row with an empty '
      + '`wrote` was measured and wrote nothing here; a tool absent from this file was never '
      + 'measured, which is what the coverage half of tools/audit_step_isolation.mjs refuses. '
      + 'Writes to a tempdir are not recorded and are not findings — that is the distinction the '
      + 'measurement turns on. Regenerate when a tool changes; this is too slow for a per-commit '
      + 'gate and does not belong in one, the same call T-1302 made for writer_inventory.json. '
      + 'WHAT THIS DOES NOT PROVE: it is one tree state, so a CONDITIONAL writer is invisible to '
      + 'it — ticket.mjs check writes nothing on a consistent tree and REPAIRS tickets.json on a '
      + 'stale one, and measures clean here purely because the mirror was current when this ran '
      + '(T-1341). So this file says no tool wrote on the tree it was measured on, which is '
      + 'weaker than saying no tool writes, and the difference is the conditional case.',
    measured: new Date().toISOString().slice(0, 10),
    gate_verdict: verdict ? verdict[0] : 'UNKNOWN',
    declared_steps: steps.length,
    exempt,
    tools,
  };
  fs.writeFileSync(OUT, JSON.stringify(doc, null, 2) + '\n');
  const ex = Object.keys(exempt);
  const live = (w) => !ex.some((p) => w.startsWith(p));
  const dirty = Object.entries(tools).filter(([, v]) => v.wrote.some(live));
  console.log(`\nwrote ${path.relative(ROOT, OUT)} — ${Object.keys(tools).length} tool(s) measured, `
    + `${steps.length} step(s) declared, gate ${doc.gate_verdict}`);
  for (const [t, v] of dirty) console.log(`  WRITES LIVE  ${t}  →  ${v.wrote.filter(live).slice(0, 3).join(', ')}`);
  if (!dirty.length) console.log('  none of them wrote the live tree');
  return 0;
}

/**
 * Measure ONE tool, by running exactly the commands check.sh declares for it.
 *
 * WHY THIS EXISTS. `--build` is one instrumented gate run — right for a full sweep and
 * far too heavy for the common case, which is a PR that adds a single gated tool. The
 * coverage half of the audit refuses such a PR until the tool has a row, so without this
 * every tool-adding PR paid a ~10 minute rebuild of a measurement already correct for the
 * other 337 tools. Three paid it in one evening (#1476, #1480, #1488) before it was worth
 * fixing.
 *
 * It measures the SAME WAY `--build` does — the tool's own declared step and self-test
 * commands, under the same probes — so a row minted here is not a weaker row. What it
 * gives up is stated: it sees only this tool, so it cannot notice that some OTHER tool
 * started writing. That is what the full sweep is for, and why --build stays.
 */
function buildOne(tool) {
  const sh = fs.readFileSync(path.join(APP, 'tools', 'check.sh'), 'utf8');
  const cmds = declaredSteps(sh).filter((s) => toolOf(s.command) === tool);
  if (!cmds.length) {
    console.error(`no gate step runs ${tool} — check.sh declares none, so there is `
      + 'nothing to measure and no row to mint');
    return 1;
  }
  const jsonl = fs.mkdtempSync('/tmp/c4d-iso1-') + '/probe.jsonl';
  fs.writeFileSync(jsonl, '');
  const env = {
    ...process.env,
    ISOLATION_ROOT: ROOT,
    ISOLATION_OUT: jsonl,
    PYTHONPATH: PROBE + (process.env.PYTHONPATH ? ':' + process.env.PYTHONPATH : ''),
    NODE_OPTIONS: `--require ${path.join(PROBE, 'node_probe.js')}`
      + (process.env.NODE_OPTIONS ? ' ' + process.env.NODE_OPTIONS : ''),
  };
  for (const c of cmds) {
    console.log(`  ${c.kind.padEnd(8)} ${c.command}`);
    spawnSync('bash', ['-c', c.command], { cwd: APP, env, encoding: 'utf8', maxBuffer: 1 << 28 });
  }

  const wrote = new Set(); const by = new Set();
  for (const line of fs.readFileSync(jsonl, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    let d; try { d = JSON.parse(line); } catch { continue; }
    const a0 = (d.argv || [])[0] || '';
    const key = a0.includes('tools/') ? 'tools/' + a0.split('tools/').pop()
      : (path.isAbsolute(a0) && a0.startsWith(ROOT + path.sep) ? path.relative(ROOT, a0) : a0);
    if (key !== tool) continue;               // a helper it spawned is not this row
    for (const w of d.wrote || []) wrote.add(w);
    if ((d.wrote || []).length) by.add((d.argv || []).join(' ').trim());
  }

  let doc;
  try { doc = JSON.parse(fs.readFileSync(OUT, 'utf8')); } catch {
    console.error(`${path.relative(ROOT, OUT)} is missing — run --build once before `
      + 'measuring a single tool into it');
    return 1;
  }
  doc.tools[tool] = { wrote: [...wrote].sort() };
  if (by.size) doc.tools[tool].wrote_by = [...by].sort();
  doc.tools = Object.fromEntries(Object.keys(doc.tools).sort().map((k) => [k, doc.tools[k]]));
  doc.measured = new Date().toISOString().slice(0, 10);
  fs.writeFileSync(OUT, JSON.stringify(doc, null, 2) + '\n');

  const live = [...wrote].filter((w) => !Object.keys(doc.exempt || {}).some((p) => w.startsWith(p)));
  console.log(`\n${tool}: ${cmds.length} declared command(s) measured — `
    + (live.length ? `WRITES THE LIVE TREE: ${live.slice(0, 3).join(', ')}` : 'wrote nothing in-tree'));
  return 0;
}

function selfTest() {
  let bad = 0;
  const ok = (c, m) => { console.log(`   ${c ? 'ok  ' : 'FAIL'}  ${m}`); if (!c) bad++; };
  const S = (s) => declaredSteps(s);

  ok(S('step "a label" \\\n  python3 tools/x.py --check\n')[0].command === 'python3 tools/x.py --check',
     'a continuation line is joined onto its declaration');
  ok(S('selftest "…and it fires" \\\n  python3 tools/x.py --self-test\n')[0].kind === 'selftest',
     'a selftest is told from a step');
  ok(S('step "renderer modules parse" check_js\n')[0].command === 'check_js',
     'a single-line declaration calling a shell function is read');
  ok(S('step "a label with \\"quotes\\" in it" \\\n  python3 tools/x.py\n')[0].command === 'python3 tools/x.py',
     'an escaped quote inside the label does not end the label');
  ok(S('# step "a commented-out step" \\\n#  python3 tools/x.py\n').length === 0,
     'a commented-out declaration is not a step');
  ok(S('step "one" \\\n  python3 tools/a.py\n\nstep "two" \\\n  node tools/b.mjs\n').length === 2,
     'two declarations are two steps');

  ok(toolOf('python3 tools/read_census_1830.py --check') === 'tools/read_census_1830.py',
     'the tool is taken out of a python command');
  ok(toolOf('node tools/rederive.mjs --self-test') === 'tools/rederive.mjs',
     'the tool is taken out of a node command');
  ok(toolOf('check_js') === null, 'a shell function names no tool');
  ok(toolOf('bash tools/publish.sh') === null, 'a bash step names no python or node tool');
  ok(toolOf("sh -c 'python3 tools/x.py --self-test'") === 'tools/x.py',
     'a tool wrapped in sh -c is still found');

  // --tool selects the SAME commands --build would have measured for that tool, which is
  // the whole basis for a row minted incrementally being as good as one from a full sweep.
  const SH2 = 'step "reads" \\\n  python3 tools/a.py --check\n'
    + 'selftest "…and it fires" \\\n  python3 tools/a.py --self-test\n'
    + 'step "another tool" \\\n  python3 tools/b.py --check\n';
  const forA = declaredSteps(SH2).filter((x) => toolOf(x.command) === 'tools/a.py');
  ok(forA.length === 2, '--tool picks up both the step and the self-test of its tool');
  ok(forA.some((x) => x.kind === 'selftest'),
     'and the self-test among them — the half that breaks things on purpose');
  ok(declaredSteps(SH2).filter((x) => toolOf(x.command) === 'tools/b.py').length === 1,
     'and does not sweep in another tool\'s commands');
  ok(declaredSteps(SH2).filter((x) => toolOf(x.command) === 'tools/nope.py').length === 0,
     'a tool no gate step runs selects nothing, so --tool refuses rather than minting an empty row');

  console.log(bad ? `  self-test: ${bad} FAILURE(S)` : '  self-test: every assertion fires');
  return bad ? 1 : 0;
}

// ONLY RUN THE CLI WHEN THIS FILE IS THE ENTRY POINT. audit_step_isolation.mjs imports
// the two readers below, and without this guard that import executed this file's argument
// parsing and exited — the audit's own self-test printed this file's instead.
const isEntry = process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname);
const arg = isEntry ? process.argv[2] : null;
if (isEntry) {
if (arg === '--build') process.exit(build());
else if (arg === '--tool') {
  const t = process.argv[3];
  if (!t) { console.error('usage: measure_step_isolation.mjs --tool tools/x.py'); process.exit(2); }
  process.exit(buildOne(t));
} else if (arg === '--self-test') process.exit(selfTest());
else { console.error('usage: measure_step_isolation.mjs --build | --tool <tools/x> | --self-test'); process.exit(2); }
}

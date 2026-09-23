#!/usr/bin/env node
/**
 * audit_step_isolation.mjs — the per-commit half of T-1339.
 *
 *   node tools/audit_step_isolation.mjs --check      refuse an unmeasured or mutating step
 *   node tools/audit_step_isolation.mjs --self-test  prove each refusal fires when broken
 *
 * tools/step_isolation.json is the measurement (measure_step_isolation.mjs --build, one
 * instrumented gate run). This reads it and asks two questions that cost milliseconds:
 *
 *   1. DOES ANY MEASURED TOOL WRITE THE LIVE TREE? That is the T-1336 race at its source.
 *      check.sh runs its steps in a job pool over one working tree, so a tool that mutates
 *      it — even to prove its own check fires on a drift, and even putting it straight back
 *      — is read by whatever runs beside it.
 *
 *   2. IS EVERY GATE STEP MEASURED? Question 1 alone is satisfied by an empty file. A new
 *      step added without a measurement is exactly how the seventh offender arrives, so a
 *      declared python or node step with no row is a failure here and not a footnote.
 *
 * WHAT IT DELIBERATELY DOES NOT ASK. A step that is a shell function or a bash script names
 * no python or node tool and cannot be keyed to one; those are listed, not counted as holes,
 * because pretending to have measured them would be worse than saying which ones are open.
 */
import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { declaredSteps, toolOf } from './measure_step_isolation.mjs';

const APP = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const FILE = path.join(APP, 'tools', 'step_isolation.json');
const CHECK = path.join(APP, 'tools', 'check.sh');

/** The whole judgement, over data rather than over the filesystem, so a self-test can drive it. */
export function faults(measurement, checkSh) {
  const bad = [];
  if (!measurement || typeof measurement !== 'object' || !measurement.tools) {
    return ['tools/step_isolation.json is missing or carries no `tools` — run '
      + '`node tools/measure_step_isolation.mjs --build`'];
  }
  const tools = measurement.tools;

  // AN EXEMPTION IS A PATH PREFIX WITH A WRITTEN REASON, and one without a reason is
  // refused here. The gate's own first step regenerates site/ wholesale and check.sh's
  // single barrier sits between it and everything else, so those writes are decided
  // rather than accidental — but "decided" has to be stated by someone, in the file,
  // or an exemption becomes the place findings go to be forgotten.
  const exempt = measurement.exempt && typeof measurement.exempt === 'object' ? measurement.exempt : {};
  for (const [prefix, e] of Object.entries(exempt)) {
    const why = e && typeof e === 'object' ? String(e.reason || '').trim() : '';
    if (!why) bad.push(`exempt "${prefix}" carries no reason — an exemption without one is a finding in hiding`);
  }
  const exemptPrefixes = Object.entries(exempt)
    .filter(([, e]) => e && String(e.reason || '').trim())
    .map(([p]) => p);
  const live = (w) => !exemptPrefixes.some((p) => w.startsWith(p));

  for (const [tool, row] of Object.entries(tools)) {
    if (!row || !Array.isArray(row.wrote)) { bad.push(`${tool}: no measured \`wrote\` list`); continue; }
    const wrote = row.wrote.filter(live);
    if (wrote.length) {
      bad.push(`${tool} WRITES THE LIVE TREE — ${wrote.slice(0, 3).join(', ')}`
        + `${wrote.length > 3 ? ` and ${wrote.length - 3} more` : ''}`
        + `${row.wrote_by ? ` (via ${row.wrote_by[0]})` : ''}. A step that mutates the `
        + `working tree is read by whatever the pool runs beside it (T-1336). Break a COPY: `
        + `rebind the tool's module-level path and check that, the way read_census_1830.py and `
        + `compile_businesses.py do.`);
    }
  }

  const steps = declaredSteps(checkSh);
  const missing = [];
  for (const s of steps) {
    const t = toolOf(s.command);
    if (t && !(t in tools)) missing.push(`${t}  (${s.kind})`);
  }
  for (const m of [...new Set(missing)]) {
    bad.push(`${m} is a gate step and has NO measured row — run `
      + `\`node tools/measure_step_isolation.mjs --build\` in the commit that adds it`);
  }
  return bad;
}

function check(quiet) {
  let doc = null;
  try { doc = JSON.parse(fs.readFileSync(FILE, 'utf8')); } catch {}
  const sh = fs.readFileSync(CHECK, 'utf8');
  const bad = faults(doc, sh);
  if (bad.length) {
    console.log('step isolation: FAILED');
    for (const b of bad) console.log(`  - ${b}`);
    return 1;
  }
  const n = Object.keys(doc.tools).length;
  const steps = declaredSteps(sh);
  const unkeyed = steps.filter((s) => !toolOf(s.command)).length;
  if (!quiet) {
    console.log(`step isolation: OK — ${n} tool(s) measured, none writes the live tree; `
      + `every one of ${steps.length - unkeyed} keyed gate step(s) has a row`);
    console.log(`  ${unkeyed} step(s) are shell functions or bash and name no python/node tool; `
      + `they are named rather than counted as measured (measured ${doc.measured})`);
  }
  return 0;
}

function selfTest() {
  let bad = 0;
  const ok = (c, m) => { console.log(`   ${c ? 'ok  ' : 'FAIL'}  ${m}`); if (!c) bad++; };
  const SH = 'step "reads a thing" \\\n  python3 tools/a.py --check\n';
  const clean = { tools: { 'tools/a.py': { wrote: [] } } };

  ok(faults(clean, SH).length === 0, 'a measured step that writes nothing passes');
  ok(faults({ tools: { 'tools/a.py': { wrote: ['chicago/4d/data/x.json'] } } }, SH)
       .some((b) => /WRITES THE LIVE TREE/.test(b)),
     'a tool that wrote in-tree is refused');
  ok(faults({ tools: {} }, SH).some((b) => /NO measured row/.test(b)),
     'a gate step with no row is refused — an empty file must not read as proof');
  ok(faults(null, SH).some((b) => /missing/.test(b)), 'a missing measurement file is refused');
  ok(faults({ tools: { 'tools/a.py': {} } }, SH).some((b) => /no measured `wrote` list/.test(b)),
     'a row with no measured list is refused');
  ok(faults(clean, 'step "a shell function" check_js\n').length === 0,
     'a step naming no python or node tool is not a hole');
  ok(faults({ tools: { 'tools/a.py': { wrote: [] }, 'tools/b.py': { wrote: [] } } }, SH).length === 0,
     'a row for a tool no longer gated is not a failure — it is stale, not wrong');
  ok(faults(clean, SH + 'selftest "…and it fires" \\\n  python3 tools/b.py --self-test\n')
       .some((b) => /tools\/b\.py/.test(b)),
     'a NEW self-test added without a measurement is refused, which is the point of this gate');

  const wrote = (paths, exempt) => ({ exempt, tools: { 'tools/a.py': { wrote: paths } } });
  ok(faults(wrote(['site/chicago/4d/js/changelog.js'],
                  { 'site/': { reason: 'the generated mirror, regenerated by the gate itself' } }), SH).length === 0,
     'a write under an exempted prefix, with a reason, passes');
  ok(faults(wrote(['site/chicago/4d/js/changelog.js'], { 'site/': { reason: '' } }), SH)
       .some((b) => /carries no reason/.test(b)),
     'an exemption with an EMPTY reason is refused — not a way to silence a finding');
  ok(faults(wrote(['site/chicago/4d/js/changelog.js'], { 'site/': {} }), SH)
       .some((b) => /carries no reason/.test(b)),
     'an exemption with no reason field at all is refused');
  ok(faults(wrote(['chicago/4d/data/x.json'],
                  { 'site/': { reason: 'the generated mirror' } }), SH)
       .some((b) => /WRITES THE LIVE TREE/.test(b)),
     'an exemption for one prefix does not excuse a write to another');
  ok(faults({ exempt: { 'site/': { reason: 'r' } },
              tools: { 'tools/a.py': { wrote: ['chicago/4d/d.json'], wrote_by: ['tools/a.py --build'] } } }, SH)
       .some((b) => /via tools\/a\.py --build/.test(b)),
     'the finding names the invocation that wrote, not just the tool');

  console.log(bad ? `  self-test: ${bad} FAILURE(S)` : '  self-test: every assertion fires when broken');
  return bad ? 1 : 0;
}

// ONLY RUN THE CLI WHEN THIS FILE IS THE ENTRY POINT. audit_step_isolation.mjs imports
// the two readers below, and without this guard that import executed this file's argument
// parsing and exited — the audit's own self-test printed this file's instead.
const isEntry = process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname);
const arg = isEntry ? process.argv[2] : null;
if (isEntry) {
if (arg === '--check') process.exit(check(process.argv.includes('--quiet')));
else if (arg === '--self-test') process.exit(selfTest());
else { console.error('usage: audit_step_isolation.mjs --check [--quiet] | --self-test'); process.exit(2); }
}

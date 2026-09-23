#!/usr/bin/env node
// check_gh_rest.mjs — T-0234: refuse a GraphQL draw re-entering the steward surfaces.
//
//   node tools/check_gh_rest.mjs            scan the repo's workflows + steward scripts
//   node tools/check_gh_rest.mjs --self-test  prove the scanner fires (fixture trees)
//
// GitHub meters GraphQL and REST as two separate hourly buckets (steward run
// 1140, 2026-08-27: graphql 0/5000 while core sat 4969/5000). `gh pr create/
// list/view/merge/comment` and `gh issue/search` draw on GraphQL; the same
// operations through `gh api repos/…/pulls` draw on core. The fleet already
// moved its lap and merge-ready scripts to REST — measured in
// test_pr_lap_list.mjs — and the comment there says the shape of the relapse:
// "one reintroduced `gh pr …` blinds the lap again on a busy afternoon."
// This is the tripwire for that relapse, run by tools/check.sh on every gate.
//
// THE NAMED EXCEPTION (T-0234 acceptance): arming auto-merge has no REST
// equivalent — enablePullRequestAutoMerge is GraphQL-only — so
// `gh pr merge N --auto` is allowlisted EXACTLY WHERE IT IS, with its cost in
// the surrounding comment. Any other `gh pr/issue/search` call in a workflow
// or steward script is a violation: it names file and line, and exits 1.

import { readFileSync, readdirSync, mkdtempSync, writeFileSync, mkdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = resolve(HERE, '..', '..', '..');
const SURFACES = ['.github/workflows', '.github/steward'];
// `gh pr merge --auto` — the ONLY GraphQL call with no REST equivalent, armed
// on bake PRs by chicago-4d-bake.yml. Anything else matches GRAPHQL_DRAW below.
const NAMED_EXCEPTION = /gh\s+pr\s+merge\b[^\n]*--auto/;
const GRAPHQL_DRAW = /\bgh\s+(pr\s+(create|list|view|merge|comment|status|checks|diff|review)|issue\b|search\b)/;

export function scan(root) {
  const violations = [];
  const named = [];
  for (const surface of SURFACES) {
    let files;
    try {
      files = readdirSync(join(root, surface), { withFileTypes: true })
        .filter((e) => e.isFile() && /\.(yml|yaml|sh)$/.test(e.name))
        .map((e) => join(surface, e.name));
    } catch {
      continue; // a fixture may carry only one surface
    }
    for (const rel of files) {
      const text = readFileSync(join(root, rel), 'utf8');
      text.split('\n').forEach((line, i) => {
        if (/^\s*#/.test(line)) return; // comment lines may quote a command
        if (!GRAPHQL_DRAW.test(line)) return;
        if (NAMED_EXCEPTION.test(line)) {
          named.push(`${rel}:${i + 1} — named exception (auto-merge, GraphQL-only, cost in comment)`);
        } else {
          violations.push(`${rel}:${i + 1} — ${line.trim()}\n    draws GraphQL; use .github/steward/pr-rest.sh or gh api repos/… (T-0234)`);
        }
      });
    }
  }
  return { violations, named };
}

function main() {
  const selfTest = process.argv.includes('--self-test');
  if (selfTest) {
    const mk = (base, rel, content) => {
      mkdirSync(join(base, dirname(rel)), { recursive: true });
      writeFileSync(join(base, rel), content);
    };
    // (a) a clean surface passes
    const t1 = mkdtempSync(join(tmpdir(), 'gh-rest-clean-'));
    try {
      mk(t1, '.github/workflows/clean.yml', 'run: gh api repos/x/pulls\n');
      const a = scan(t1);
      const cleanOk = a.violations.length === 0;
      // (b) a reintroduced GraphQL draw is caught, and (c) the named exception
      // is allowed exactly where it is
      mk(t1, '.github/steward/lap.sh', 'PRS=$(gh pr list --limit 50)\n');
      mk(t1, '.github/workflows/bake.yml', 'run: gh pr merge "$N" --auto --squash # named\n');
      const b = scan(t1);
      const catches = b.violations.length === 1 && b.violations[0].includes('lap.sh:1');
      const excepts = b.named.length === 1 && b.named[0].includes('bake.yml');
      console.log(`self-test: clean-scan ${cleanOk ? 'ok' : 'FAIL'}, violation caught ${catches ? 'ok' : 'FAIL'}, named exception allowed ${excepts ? 'ok' : 'FAIL'}`);
      if (!(cleanOk && catches && excepts)) process.exit(1);
    } finally {
      rmSync(t1, { recursive: true, force: true });
    }
    return;
  }

  const { violations, named } = scan(DEFAULT_ROOT);
  for (const n of named) console.log(`named exception  ${n}`);
  if (violations.length) {
    console.error(`T-0234: ${violations.length} GraphQL draw(s) in the steward surfaces:`);
    for (const v of violations) console.error(`  ${v}`);
    console.error('GitHub meters GraphQL separately from REST; the fleet exhausted GraphQL while REST sat at 4969/5000 (run 1140). Move the call to .github/steward/pr-rest.sh or gh api repos/…');
    process.exit(1);
  }
  console.log(`T-0234: steward surfaces are REST-clean (${named.length} named exception(s) allowed).`);
}

main();

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
//
// AND THE SECOND QUESTION ABOUT THE SAME SURFACES (T-1655): a call has to land on
// the right REPOSITORY, not merely on the right meter. `.github/steward/pr-rest.sh`
// read its repository out of `$GITHUB_REPOSITORY`, and the environment belongs to
// whoever started the process rather than to the checkout the script is in — a
// steward improve run drives this file from a chicago clone inside a
// polecat-platform job. Measured 2026-09-27 (T-1652, chicago#104): `create` failed
// loudly with a 422, and `resume` SUCCEEDED, commenting the handoff reason on and
// applying `resume` to polecat-platform#104, an unrelated PR. Both repositories had
// a #104 open that day, which is the whole point — a number collision across repos
// is not rare, so the failure mode is labelling a stranger's PR, the one thing
// T-1577 exists to stop happening without the owner knowing why.
//
// So pr-rest.sh must NAME the repository it acts on: it takes `--repo owner/name`
// and otherwise reads this checkout's own origin remote. This is the tripwire for
// the relapse, and it is deliberately about a READ of the variable and not a mention
// of it — the refusal message names `$GITHUB_REPOSITORY` in order to say it is not
// consulted, and an escaped `\$` in a shell string is prose, not a read.

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
// T-1655, widened to all four by T-1656. The scripts whose verbs each act on a named
// repository, and the two halves of that: no READ of the ambient repo name (an
// unescaped expansion — a `\$` is a mention, which the refusal message itself needs),
// and a `--repo` option to name it with.
//
// The other three joined the list because the reason they were left out of it was
// only that today's callers happen to be right: they are run by this repository's OWN
// workflows, where the ambient name is the ambient name you want. That is a property
// of the CALLER, and pr-rest.sh had the same property until a steward run drove it
// from a clone inside a polecat-platform job (T-1652). Two of the three WRITE —
// merge-ready.sh merges, pr-stuck.sh labels and comments — so the silent
// wrong-repository write T-1655 measured was available to them the same way.
const REPO_NAMED = [
  '.github/steward/pr-rest.sh',
  '.github/steward/pr-lap.sh',
  '.github/steward/merge-ready.sh',
  '.github/steward/pr-stuck.sh',
];
const AMBIENT_REPO = /(^|[^\\])\$\{?GITHUB_REPOSITORY\b/;
const REPO_OPTION = /--repo\b/;

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
  return { violations, named, ambient: scanRepoNamed(root) };
}

/** T-1655: does every verb of a repo-naming script say which repository it acts on? */
export function scanRepoNamed(root) {
  const ambient = [];
  for (const rel of REPO_NAMED) {
    let text;
    try {
      text = readFileSync(join(root, rel), 'utf8');
    } catch {
      continue; // a fixture may not carry this surface
    }
    text.split('\n').forEach((line, i) => {
      if (/^\s*#/.test(line)) return; // a comment may name the variable to disown it
      if (AMBIENT_REPO.test(line)) {
        ambient.push(`${rel}:${i + 1} — ${line.trim()}\n    reads the repository from the environment; the environment belongs to the JOB, not to this checkout — take --repo, default to this checkout's origin remote (T-1655)`);
      }
    });
    if (!REPO_OPTION.test(text)) {
      ambient.push(`${rel} — no --repo option, so a caller cannot name the repository it means (T-1655)`);
    }
  }
  return ambient;
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
      // (d) T-1655: a script that reads the repo out of the environment is caught,
      // (e) one that takes --repo and only MENTIONS the variable (escaped, in the
      // refusal that disowns it) is clean, and (f) one with no --repo at all is
      // caught even though it never reads the environment — naming the repository is
      // the requirement, and a script nobody can point at a repository fails it.
      mk(t1, '.github/steward/pr-rest.sh', 'repo="${GITHUB_REPOSITORY:?unset}"\n# --repo\n');
      const ambientCaught = scanRepoNamed(t1).some((a) => /pr-rest\.sh:1/.test(a));
      mk(t1, '.github/steward/pr-rest.sh',
         '# NEVER \\$GITHUB_REPOSITORY (T-1655)\n'
         + 'case "$1" in --repo) repo=$2 ;; esac\n'
         + 'echo "pass --repo owner/name; never \\$GITHUB_REPOSITORY" >&2\n');
      const ambientClean = scanRepoNamed(t1).length === 0;
      mk(t1, '.github/steward/pr-rest.sh', 'repo=kevinrhaas/chicago\n');
      const optionRequired = scanRepoNamed(t1).some((a) => /no --repo option/.test(a));
      // (g) T-1656: EVERY entry in REPO_NAMED is really covered, one at a time. The
      // list is the whole of what makes the tripwire reach a script, and a list is
      // exactly the kind of thing that grows a name without gaining a check — this
      // one carried pr-rest.sh alone while pr-lap.sh, merge-ready.sh and pr-stuck.sh
      // sat outside it with the same fault in them. So each name is put back in a
      // fixture that reads the environment, with the other three clean, and the scan
      // has to name THAT file and no other.
      const CLEAN = '# never \\$GITHUB_REPOSITORY (T-1655)\ncase "$1" in --repo) repo=$2 ;; esac\n';
      const coverage = REPO_NAMED.map((rel) => {
        for (const other of REPO_NAMED) mk(t1, other, CLEAN);
        mk(t1, rel, `${CLEAN}REPO="\${GITHUB_REPOSITORY:-kevinrhaas/chicago}"\n`);
        const found = scanRepoNamed(t1);
        return found.length === 1 && found[0].startsWith(`${rel}:3`);
      });
      const allCovered = coverage.length === 4 && coverage.every(Boolean);
      console.log(`self-test: clean-scan ${cleanOk ? 'ok' : 'FAIL'}, violation caught ${catches ? 'ok' : 'FAIL'}, named exception allowed ${excepts ? 'ok' : 'FAIL'}`);
      console.log(`self-test: T-1655 ambient repo caught ${ambientCaught ? 'ok' : 'FAIL'}, an escaped mention allowed ${ambientClean ? 'ok' : 'FAIL'}, --repo required ${optionRequired ? 'ok' : 'FAIL'}`);
      console.log(`self-test: T-1656 each of the ${REPO_NAMED.length} named scripts covered on its own — ${REPO_NAMED.map((r, i) => `${r.replace(/^.*\//, '')} ${coverage[i] ? 'ok' : 'FAIL'}`).join(', ')}`);
      if (!(cleanOk && catches && excepts && ambientCaught && ambientClean && optionRequired && allCovered)) process.exit(1);
    } finally {
      rmSync(t1, { recursive: true, force: true });
    }
    return;
  }

  const { violations, named, ambient } = scan(DEFAULT_ROOT);
  for (const n of named) console.log(`named exception  ${n}`);
  if (ambient.length) {
    console.error(`T-1655: ${ambient.length} unnamed-repository fault(s) in the steward surfaces:`);
    for (const a of ambient) console.error(`  ${a}`);
    console.error('A steward run drives these scripts from a chicago checkout inside a polecat-platform job, so $GITHUB_REPOSITORY is the wrong repository: chicago#104\'s handoff was commented on and labelled onto polecat-platform#104, an unrelated PR.');
    process.exit(1);
  }
  if (violations.length) {
    console.error(`T-0234: ${violations.length} GraphQL draw(s) in the steward surfaces:`);
    for (const v of violations) console.error(`  ${v}`);
    console.error('GitHub meters GraphQL separately from REST; the fleet exhausted GraphQL while REST sat at 4969/5000 (run 1140). Move the call to .github/steward/pr-rest.sh or gh api repos/…');
    process.exit(1);
  }
  console.log(`T-0234: steward surfaces are REST-clean (${named.length} named exception(s) allowed).`);
  console.log(`T-1655: ${REPO_NAMED.length} repo-naming script(s) name the repository they act on.`);
}

main();

#!/usr/bin/env node
/**
 * A DRAIN LAP, AS A TOOL — merge a batch of open PRs onto one branch, let this
 * repository's own merge drivers do the work they were written for, and REFUSE,
 * loudly and with the markers left in place, on any conflict they do not cover.
 *
 * T-0833, the second piece of T-0813. The first piece built the drivers; this is
 * the lap that uses them. #880 did the whole procedure by hand and wrote it into
 * its commit message; #891 did it again; the steps have not changed since, which
 * is the definition of something that should be a command.
 *
 * ── WHY A LAP IS NEEDED AT ALL, MEASURED ON THIS REPO ─────────────────────────
 *
 * GITHUB DOES NOT RUN THIS REPOSITORY'S MERGE DRIVERS. Git deliberately keeps a
 * driver's command out of tracked content, so `.gitattributes` can say
 * `merge=queue` but only a local clone that has run `tools/setup-merge-drivers.sh`
 * knows what `queue` is. The server therefore sees conflicts a clone does not —
 * measured on PR #940 (zero conflicts locally, "merge conflict" in the UI) and
 * recorded in /.gitattributes. Auto-merge can never fire on those PRs, and the
 * janitor's own `git merge` runs in a clone that has not registered them either,
 * so it skips them in silence (T-0809). They sit. They rot. The next slice reads
 * their ticket as `open` and builds the work a second time.
 *
 * The pile measured on 2026-09-13, six PRs open against `dev`, every one of them
 * reported conflicting by `git merge-tree` — which, like GitHub, loads no driver:
 *
 *   chicago/4d/renderers/web/js/changelog.js   6 of 6   merge=changelog
 *   chicago/4d/tickets/QUEUE.md                6 of 6   merge=queue
 *   chicago/4d/tools/dev-smoke-state.json      5 of 6   merge=smokestate
 *   chicago/4d/assets/manifest.json            1 of 6   NO DRIVER — a real one
 *
 * Three of the four already have an answer committed to this repo. The lap's job
 * is to be the clone that can apply them, and to hand back the fourth untouched.
 *
 * ── WHAT IT RESOLVES, AND WHY THE SET IS EXACTLY THIS ─────────────────────────
 *
 * T-0813 wrote the rule as "refuses on any conflict outside the BUILD PRODUCTS",
 * because when it was filed the six conflicting files were generated artifacts.
 * They are not any more: T-0937 and T-0938 took `tickets/BOARD.md`,
 * `tickets/tickets.json` and the whole `site/chicago/4d/**` mirror OUT of the
 * tree — untracked and .gitignored — on the reasoning that a file that is not
 * tracked cannot conflict, in a clone or on a server. `merge=generated` names no
 * path today. So the set that remains is the DRIVER-COVERED set, and the rule is
 * written against what the repository actually declares rather than against a
 * list this file would have to keep in step by hand:
 *
 *   the lap resolves what `.gitattributes` has already decided how to resolve,
 *   and nothing else.
 *
 * That is stricter than it sounds, and deliberately. A driver may itself REFUSE —
 * merge-changelog.mjs does, when both sides edited one shipped entry, and
 * merge-smoke-state.mjs does, when either side is not the shape it knows. A path
 * still carrying markers after its own driver has run is a semantic conflict that
 * the driver looked at and declined, which is the last thing a batching tool
 * should overrule. So the test is not "was this path driver-covered" but "is this
 * path still unresolved", and any unresolved path at all ends the lap. The
 * driver-coverage lookup survives only to tell you WHICH kind of refusal you are
 * reading, because "the driver declined this" and "nothing here knows this file"
 * want different next moves from a person.
 *
 * REFUSING LEAVES THE MERGE OPEN. Not `--abort`: the ticket asks for "ordinary
 * conflict markers", and they are more useful than a clean tree — you are one
 * `git status` from the files and one `git merge --abort` from the old state.
 *
 * ── WHAT IT DOES AFTER A MERGE, AND WHY THAT IS PART OF THE LAP ───────────────
 *
 * A driver that resolves a file can leave it needing a tool run, and both of this
 * repo's do. merge-changelog.mjs keeps our entries UNSTAMPED on purpose and says
 * so on stderr; an unstamped entry fails `check-changelog.mjs`, which is a gate
 * step. Two branches that each filed a ticket can collide on an id, which
 * `ticket.mjs restamp` settles while keeping every queue place. Doing those by
 * hand is how #880's lap was six steps instead of one, and forgetting one is how
 * a drained batch fails the gate for a reason that has nothing to do with the
 * work in it. So the lap runs them, and it runs them only where they exist —
 * which is what lets the self-test drive the real code path in a scratch repo
 * that has neither.
 *
 * ── USAGE ────────────────────────────────────────────────────────────────────
 *
 *   node tools/drain.mjs 1234 1235 1239      # PR numbers, resolved through REST
 *   node tools/drain.mjs some/branch ...     # or refs, resolved as given
 *   node tools/drain.mjs --self-test         # the assertions, in scratch repos
 *
 *   --base <ref>     what the batch is cut from        (default origin/dev)
 *   --branch <name>  the batch branch                  (default drain/<stamp>)
 *   --repo <dir>     the repository to work in         (default: this checkout)
 *   --no-gate        skip tools/check.sh at the end
 *
 * It never pushes and never merges into `dev`. It leaves a branch and a report;
 * landing it is a PR like any other, and on this repo that is the owner's
 * pipeline (chicago/4d/docs/PIPELINE.md).
 */
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const APP_REL = 'chicago/4d';                         // the app, from the repo root
const CHECKOUT = path.resolve(HERE, '..', '..', '..'); // the repository this file lives in

// EVERY PATH BELOW IS RELATIVE TO THE REPOSITORY BEING DRAINED, not to this file.
// A lap over a repository runs THAT repository's tools, which is what lets the
// self-test drive this same code in a scratch repo that has none of them: the
// `existsSync` guard is then answering a real question rather than a fixed yes.
const SETUP_REL = `${APP_REL}/tools/setup-merge-drivers.sh`;
const CHECK_REL = `${APP_REL}/tools/check.sh`;

/** Follow-ups a driver's own output demands. Each runs only where it exists. */
const AFTER_MERGE = [
  { rel: `${APP_REL}/tools/stamp-changelog.mjs`, argv: ['node', `${APP_REL}/tools/stamp-changelog.mjs`],
    why: 'merge-changelog.mjs keeps our entries unstamped; check-changelog.mjs fails on one' },
  { rel: `${APP_REL}/tools/ticket.mjs`, argv: ['node', `${APP_REL}/tools/ticket.mjs`, 'board'],
    why: 'the board and its mirror are written before they are read' },
];

/**
 * The id collisions a batch creates, settled one at a time.
 *
 * `ticket.mjs restamp` takes a FILE and not an id, and the reason is the whole
 * problem: with two tickets carrying one id, an id cannot say which of them
 * moves. `ticket.mjs check` already names the pair and names the younger file,
 * so the lap does exactly what its message tells a person to do, and re-asks
 * after each one rather than trusting a single pass — restamping one collision
 * can be all there is, or the first of several.
 *
 * It restamps ONLY on a DUPLICATE finding. `check` fails for other reasons (a
 * stale board, a bad state, a ticket the queue has lost), and none of those is a
 * thing a merge tool may quietly rewrite.
 */
function restampCollisions(repo, run, log, limit = 20) {
  const ticket = ['node', `${APP_REL}/tools/ticket.mjs`];
  const done = [];
  for (let i = 0; i < limit; i++) {
    const r = run([...ticket, 'check']);
    if ((r.status ?? 1) === 0) return { ok: true, done };
    const out = `${r.stdout ?? ''}${r.stderr ?? ''}`;
    const dup = out.split('\n').map((l) => l.match(/^\s*(\S+): DUPLICATE id (T-\d{4})/)).find(Boolean);
    if (!dup) {
      log('drain: ticket.mjs check is red for something that is not an id collision,');
      log('       which is not a merge tool\'s to rewrite:');
      log(out.trim().split('\n').map((l) => `    ${l}`).join('\n'));
      return { ok: false, done };
    }
    const [, file, id] = dup;
    const s = run([...ticket, 'restamp', file]);
    if ((s.status ?? 1) !== 0) {
      log(`drain: could not restamp ${file} (${id}): ${((s.stderr || s.stdout) ?? '').trim()}`);
      return { ok: false, done };
    }
    log(`  restamped ${id} — two branches had both assigned it (${file}); its queue place is kept.`);
    done.push(id);
  }
  log('drain: still finding id collisions after 20 restamps — stopping rather than looping.');
  return { ok: false, done };
}

export function parseArgs(argv) {
  const opts = { targets: [], base: 'origin/dev', branch: null, repo: null, gate: true, selfTest: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--self-test') opts.selfTest = true;
    else if (a === '--no-gate') opts.gate = false;
    else if (a === '--base') opts.base = argv[++i];
    else if (a === '--branch') opts.branch = argv[++i];
    else if (a === '--repo') opts.repo = argv[++i];
    else if (a.startsWith('-')) throw new Error(`unknown option ${a}`);
    else opts.targets.push(a);
  }
  return opts;
}

const stamp = () => new Date().toISOString().replace(/[-:]/g, '').replace(/\..*/, '');

/** A lap over one repository. Returns { ok, branch, merged, refused, steps }. */
export function drain(opts, log = console.log) {
  const repo = opts.repo ? path.resolve(opts.repo) : CHECKOUT;
  const git = (...a) => spawnSync('git', ['-C', repo, ...a], { encoding: 'utf8' });
  const run = (argv) => spawnSync(argv[0], argv.slice(1), { cwd: repo, encoding: 'utf8' });
  const steps = [];
  const branch = opts.branch || `drain/${stamp()}`;

  // 1. A dirty tree is refused before anything is touched. A lap that stashes
  //    work it did not create is a lap that can lose it.
  const dirty = git('status', '--porcelain').stdout.trim();
  if (dirty) {
    log('drain: the working tree is not clean, and a lap will not start on one:');
    log(dirty.split('\n').map((l) => `    ${l}`).join('\n'));
    return { ok: false, branch: null, merged: [], refused: [], steps, reason: 'dirty' };
  }
  if (!opts.targets.length) {
    log('drain: nothing to drain — name the PRs or refs to batch.');
    return { ok: false, branch: null, merged: [], refused: [], steps, reason: 'no targets' };
  }

  // 2. Register the drivers. This is the whole reason the lap is cheap, and it
  //    is the one step GitHub cannot take.
  const setup = path.join(repo, SETUP_REL);
  if (existsSync(setup)) {
    const r = run(['bash', setup]);
    steps.push({ step: 'register merge drivers', code: r.status ?? 1 });
    if (r.status !== 0) {
      log('drain: could not register the merge drivers, and without them a lap is\n'
        + '       just a hand merge with extra steps. Stopping.');
      log((r.stderr || '').trim());
      return { ok: false, branch: null, merged: [], refused: [], steps, reason: 'drivers' };
    }
  }

  // 3. Resolve the targets. A bare number is a PR and is looked up over REST —
  //    never GraphQL, which is the quota this fleet actually exhausts (T-0234).
  const refs = [];
  for (const t of opts.targets) {
    if (!/^\d+$/.test(t)) { refs.push({ label: t, ref: t }); continue; }
    const url = git('remote', 'get-url', 'origin').stdout.trim();
    const slug = (url.match(/github\.com[/:]([^/]+\/[^/.]+)/) || [])[1];
    if (!slug) { log(`drain: cannot read a GitHub slug off origin (${url}) to resolve PR #${t}`); return { ok: false, branch: null, merged: [], refused: [], steps, reason: 'slug' }; }
    const r = spawnSync('gh', ['api', `repos/${slug}/pulls/${t}`, '--jq', '.head.ref'], { encoding: 'utf8' });
    const head = (r.stdout || '').trim();
    if (r.status !== 0 || !head) { log(`drain: could not resolve PR #${t}: ${(r.stderr || '').trim()}`); return { ok: false, branch: null, merged: [], refused: [], steps, reason: 'pr lookup' }; }
    const f = git('fetch', '-q', 'origin', head);
    if (f.status !== 0) { log(`drain: could not fetch ${head} for PR #${t}`); return { ok: false, branch: null, merged: [], refused: [], steps, reason: 'fetch' }; }
    refs.push({ label: `#${t} (${head})`, ref: `origin/${head}` });
  }

  // 4. Cut the batch branch.
  const cut = git('checkout', '-q', '-B', branch, opts.base);
  if (cut.status !== 0) {
    log(`drain: cannot cut ${branch} from ${opts.base}: ${(cut.stderr || '').trim()}`);
    return { ok: false, branch: null, merged: [], refused: [], steps, reason: 'base' };
  }
  log(`drain: ${branch} cut from ${opts.base}; ${refs.length} target(s) to merge.`);

  // 5. Merge them one at a time, and stop on the first thing the drivers do not
  //    settle. Stopping rather than skipping: a lap that carries on past a real
  //    conflict hands back a batch nobody can read.
  const merged = [];
  for (const { label, ref } of refs) {
    const m = git('merge', '--no-ff', '--no-edit', ref);
    const unresolved = git('diff', '--name-only', '--diff-filter=U').stdout.trim();
    if (m.status === 0 && !unresolved) {
      const driven = (m.stdout + m.stderr).match(/^(?:merge-\w[\w-]*):/gm) || [];
      log(`  merged   ${label}${driven.length ? '   (a driver spoke — see its note above)' : ''}`);
      merged.push(label);
      steps.push({ step: `merge ${label}`, code: 0 });
      continue;
    }
    const paths = unresolved ? unresolved.split('\n') : [];
    const covered = paths.filter((p) => driverFor(git, p));
    const bare = paths.filter((p) => !driverFor(git, p));
    log(`  REFUSED  ${label}`);
    for (const p of bare) log(`      no driver knows ${p} — this is a real conflict`);
    for (const p of covered) log(`      ${p} carries merge=${driverFor(git, p)} and its driver DECLINED — read it, do not overrule it`);
    if (!paths.length) log(`      the merge failed without leaving an unresolved path:\n${(m.stderr || m.stdout || '').trim()}`);
    log('  the markers are left in place. Resolve them, or `git merge --abort`.');
    steps.push({ step: `merge ${label}`, code: m.status ?? 1, refused: paths });
    return { ok: false, branch, merged, refused: paths, steps, reason: 'conflict' };
  }

  // 6. The follow-ups a resolved merge leaves behind.
  for (const { rel, argv, why } of AFTER_MERGE) {
    if (!existsSync(path.join(repo, rel))) continue;
    const r = run(argv);
    steps.push({ step: argv.slice(1).join(' '), code: r.status ?? 1 });
    if (r.status !== 0) {
      log(`drain: ${argv.slice(1).join(' ')} failed — ${why}`);
      log((r.stderr || r.stdout || '').trim());
      return { ok: false, branch, merged, refused: [], steps, reason: 'after-merge' };
    }
  }
  if (existsSync(path.join(repo, `${APP_REL}/tools/ticket.mjs`))) {
    const r = restampCollisions(repo, run, log);
    steps.push({ step: 'restamp id collisions', code: r.ok ? 0 : 1, restamped: r.done });
    if (!r.ok) return { ok: false, branch, merged, refused: [], steps, reason: 'tickets' };
    if (r.done.length) run(['node', `${APP_REL}/tools/ticket.mjs`, 'board']);
  }

  const after = git('status', '--porcelain').stdout.trim();
  if (after) {
    git('add', '-A');
    git('commit', '-q', '-m', `drain: the follow-ups the drivers leave behind\n\nStamped, restamped and rebuilt after merging ${merged.join(', ')}.`);
    log('  committed the stamp/restamp/rebuild the drivers leave behind.');
  }

  // 7. The gate. A batch that has not been gated is not drained, it is stacked.
  const check = path.join(repo, CHECK_REL);
  if (opts.gate && existsSync(check)) {
    log('drain: running the gate…');
    const r = spawnSync('bash', [check], { cwd: path.join(repo, APP_REL), encoding: 'utf8', stdio: 'inherit' });
    steps.push({ step: 'check.sh', code: r.status ?? 1 });
    if (r.status !== 0) {
      log(`drain: ${branch} carries ${merged.length} PR(s) and the gate is RED on it.`);
      return { ok: false, branch, merged, refused: [], steps, reason: 'gate' };
    }
  }

  log(`drain: ${branch} carries ${merged.length} PR(s)${opts.gate && existsSync(check) ? ' and the gate is green' : ''}.`);
  log('       Push it and open ONE PR for the batch; this tool does not push.');
  return { ok: true, branch, merged, refused: [], steps };
}

/** The driver `.gitattributes` declares for a path, or null. */
function driverFor(git, rel) {
  const out = git('check-attr', 'merge', '--', rel).stdout.trim();
  const value = out.split(': ').pop();
  return (value && value !== 'unspecified' && value !== 'unset') ? value : null;
}

if (process.argv[1] && process.argv[1].endsWith('drain.mjs')) {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.selfTest) {
    const { selfTest } = await import('./drain-selftest.mjs');
    process.exit(selfTest() ? 0 : 1);
  }
  if (!opts.targets.length) {
    console.log('usage: drain.mjs <pr|ref>... [--base <ref>] [--branch <name>] [--no-gate]');
    console.log('       drain.mjs --self-test');
    process.exit(2);
  }
  process.exit(drain(opts).ok ? 0 : 1);
}

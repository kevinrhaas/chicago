#!/usr/bin/env node
/**
 * test_pr_resume.mjs — `pr-rest.sh resume`, the one call a run makes when it
 * cannot finish, tested on the four things that have to be true of it.
 *
 * WHY THIS EXISTS (T-1573; owner, 2026-09-25, on finding three PRs parked on
 * `hold` whose reasons he had not seen: *"that seems like a bad move because i am
 * not aware of why they are held"*).
 *
 * `hold` was the only label a run had. It is THE OWNER'S PARK SWITCH — every
 * automated pass in this repository skips a held PR on purpose, because a park a
 * robot can overrule is not a park — and the steward prompt nevertheless told a
 * run to apply it whenever it merely COULD NOT FINISH: verification unrun, the
 * turn budget low, `dev` moving faster than it could rebase, `dev`'s own gate red.
 * So work that needed nobody's decision had nothing coming for it either.
 * Measured on the three PRs open at 17:35Z on 2026-09-25:
 *
 *   #39 (T-1563)  "this run's clock ran out" — CI then passed all 620 steps, so
 *                 the reason was already stale, and it drifted into conflict with
 *                 `dev` while held.
 *   #41 (T-1521)  complete; held only because `dev`'s gate was red (T-1567).
 *   #42 (T-1565)  the same.
 *
 * Not one needed a ruling. Each needed a machine to lap it, re-gate it and merge
 * it, and each got a person instead.
 *
 * `resume` is the run's own word for that, and the whole value is in the FIRST
 * LINE it writes — `resume: <reason> · waits on: <T-NNNN|nothing>` — because that
 * is what `pr-stuck.sh` reads back into every sweep's log and what the 4D Board
 * will read. Four things therefore have to hold, and each is a case below:
 *
 *   1. the reason is MANDATORY and stays on ONE line, or every reader below sees
 *      a handoff with no reason — the same silence wearing a new label;
 *   2. `waits on` is a ticket id or the word `nothing`, never prose, because its
 *      reader is a script;
 *   3. the comment is posted BEFORE the label, so a labelled PR never exists
 *      without its reason beside it;
 *   4. `hold` comes OFF, because a run declaring work unfinished is not parking
 *      it, and leaving both on leaves every pass skipping it — the exact state
 *      being fixed.
 *
 * THE SCRIPT IS NOT COPIED HERE. Every case runs the real
 * `.github/steward/pr-rest.sh` with `gh` faked on PATH, recording each call in
 * order, because "in what order did it write, and what exactly did it write"
 * is the only question that matters.
 */
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, rmSync, readFileSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const SH = path.resolve(path.dirname(new URL(import.meta.url).pathname),
                        '..', '..', '..', '.github', 'steward', 'pr-rest.sh');

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

/**
 * Run the real script against a fake `gh`. Every write is appended to a log, one
 * line each, IN THE ORDER IT HAPPENED — which is itself under test (case 3).
 *   holdExists  whether DELETE .../labels/hold succeeds (a PR with no `hold`
 *               answers 404, and that is not a failure)
 */
function run(args, { holdExists = true } = {}) {
  const box = mkdtempSync(path.join(tmpdir(), 'prresume-'));
  const bin = path.join(box, 'bin');
  mkdirSync(bin, { recursive: true });
  const acted = path.join(box, 'acted.txt');

  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
ACTED=${JSON.stringify(acted)}
P=""; M="GET"
prev=""
for a in "$@"; do
  case "$a" in repos/*) P="$a" ;; esac
  case "$prev" in -X) M="$a" ;; esac
  prev="$a"
done
case "$M/$P" in
  POST/*/labels)
    # the vocabulary (repos/O/R/labels) or a PR's labels (repos/O/R/issues/N/labels)
    case "$P" in
      */issues/*/labels)
        for a in "$@"; do case "$a" in labels\\[\\]=*) echo "label \${P} \${a#*=}" >> "$ACTED" ;; esac; done ;;
      *) echo "ensure-label \$(for a in "$@"; do case "$a" in name=*) echo -n "\${a#*=}" ;; esac; done)" >> "$ACTED" ;;
    esac
    exit 0 ;;
  POST/*/comments)
    # the body arrives on stdin as JSON, exactly as \`jq -Rs '{body: .}'\` wrote it
    # COMPACTED, because the log is one write per LINE and \`jq -Rs\` pretty-prints:
    # the raw body spans a dozen lines and the reader below would find only \`{\`.
    body=$(cat | jq -c .)
    printf 'comment %s\\n' "$body" >> "$ACTED"
    exit 0 ;;
  DELETE/*/labels/hold)
    if [ "${holdExists ? 1 : 0}" = "1" ]; then echo "unlabel hold" >> "$ACTED"; exit 0; fi
    echo "Not Found" >&2; exit 1 ;;
esac
exit 0
`);
  chmodSync(path.join(bin, 'gh'), 0o755);

  const r = spawnSync('bash', [SH, 'resume', ...args], {
    cwd: box,
    encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`,
           GH_TOKEN: 'fake', GITHUB_REPOSITORY: 'kevinrhaas/chicago' },
  });
  const did = existsSync(acted) ? readFileSync(acted, 'utf8') : '';
  rmSync(box, { recursive: true, force: true });
  return { code: r.status, out: `${r.stdout || ''}${r.stderr || ''}`, acted: did,
           lines: did.split('\n').filter(Boolean) };
}

/** The body of the comment it posted, unwrapped from the JSON jq -Rs made. */
const bodyOf = (r) => {
  const line = r.lines.find((l) => l.startsWith('comment '));
  if (!line) return null;
  try { return JSON.parse(line.slice('comment '.length)).body; } catch { return null; }
};

console.log('pr-rest.sh resume — a run hands off unfinished work, and says why');

/* 1. THE WHOLE POINT: the machine-readable first line. */
{
  const r = run(['41', '--why', "dev's gate is red on T-1567", '--waits-on', 'T-1567']);
  check('the call succeeds', r.code === 0, `exit ${r.code} ${r.out.trim()}`);
  const body = bodyOf(r);
  check('…and a comment was posted', body !== null, r.acted.trim() || 'nothing written');
  const first = (body || '').split('\n')[0];
  check('…whose FIRST line is the one a script reads',
        first === "resume: dev's gate is red on T-1567 · waits on: T-1567", first);
  check('…and pr-stuck.sh’s own reader gets the reason back out of it',
        /^resume: (.*)$/.exec(first)?.[1] === "dev's gate is red on T-1567 · waits on: T-1567");
  check('…the `resume` label was applied',
        r.lines.some((l) => /^label repos\/kevinrhaas\/chicago\/issues\/41\/labels resume$/.test(l)),
        r.acted.trim());
  check('…the label vocabulary was created first, since adding an absent label is a 422',
        r.lines[0] === 'ensure-label resume', r.lines[0]);
  check('…and the run is told what it did', /waits on: T-1567/.test(r.out), r.out.trim());
}

/* 2. THE ORDER, WHICH IS THE POINT OF THE WHOLE VERB. A labelled PR must never
 *    exist without its reason beside it: if the comment fails, the label is never
 *    applied (the script runs `set -e`) and the run is told loudly. The reverse
 *    order would produce exactly the artefact T-1571 complains about — a parked
 *    PR whose reason nobody can find. */
{
  const r = run(['41', '--why', 'the run ran out of clock']);
  const comment = r.lines.findIndex((l) => l.startsWith('comment '));
  const label = r.lines.findIndex((l) => l.startsWith('label '));
  check('the reason is posted BEFORE the label is applied',
        comment !== -1 && label !== -1 && comment < label,
        `comment@${comment} label@${label}`);
}

/* 3. `waits on` DEFAULTS TO `nothing`, and the body then says nothing about
 *    waiting — a handoff that waits on nothing is ready for the very next run. */
{
  const r = run(['41', '--why', 'the run ran out of clock']);
  const body = bodyOf(r) || '';
  check('a handoff with no --waits-on says `nothing`, not an empty field',
        body.split('\n')[0] === 'resume: the run ran out of clock · waits on: nothing',
        body.split('\n')[0]);
  check('…and the body does not tell a later run to wait for something',
        !/It waits on/.test(body));
}

/* 4. …and one that DOES wait says so in prose too, because the reader who has to
 *    decide whether to spend a run on it is sometimes a person. */
{
  const body = bodyOf(run(['41', '--why', 'x', '--waits-on', 'T-1567'])) || '';
  check('a handoff that waits on a ticket names it in the body as well',
        /It waits on \*\*T-1567\*\*/.test(body));
}

/* 5. A REASON IS MANDATORY. This is the fault the verb exists to end, so it is a
 *    usage error and never a default: "unfinished" with no reason is the silence
 *    that was already there. */
{
  const r = run(['41']);
  check('a handoff with no --why is refused', r.code === 2, `exit ${r.code}`);
  check('…and says why the reason is the point', /--why is required/.test(r.out));
  check('…and wrote NOTHING — no label without a reason, ever', r.acted === '', r.acted.trim());
}

/* 6. ONE LINE, ALWAYS. A newline in the reason would push `waits on` off the first
 *    line, and every reader below — pr-stuck.sh's `sed -n 's/^resume: //p'`, the
 *    Board — would see a handoff with no reason. Folded, not refused: a run in
 *    trouble should not lose its handoff to a stray newline. */
{
  const body = bodyOf(run(['41', '--why', 'the gate went red\non stage 8\tat 1280', '--waits-on', 'nothing'])) || '';
  const first = body.split('\n')[0];
  check('a reason carrying newlines and tabs is folded onto one line',
        first === 'resume: the gate went red on stage 8 at 1280 · waits on: nothing', first);
  check('…so `waits on` is still on the first line where its reader looks',
        /· waits on: nothing$/.test(first));
}

/* 7. `waits on` IS NOT PROSE. Its reader is a script deciding whether to spend a
 *    whole run re-gating this PR; "the smoke, probably" is not an answer it can
 *    act on, and a field that is sometimes prose is a field nobody parses. */
{
  const r = run(['41', '--why', 'x', '--waits-on', 'the smoke, probably']);
  check('a --waits-on that is not a ticket id or `nothing` is refused',
        r.code === 2, `exit ${r.code}`);
  check('…naming both forms it accepts', /T-1567/.test(r.out) && /nothing/.test(r.out));
  check('…and nothing was written', r.acted === '', r.acted.trim());
}

/* 8. `hold` COMES OFF. A run reaching for this verb is declaring the work
 *    unfinished, not parked; leaving both on leaves every pass skipping it, which
 *    is the exact state T-1571 measured. */
{
  const r = run(['41', '--why', 'x']);
  check('`hold` is removed, because a run never leaves the owner’s switch on',
        r.lines.includes('unlabel hold'), r.acted.trim());
  check('…and the run is told', /hold removed/.test(r.out));
}

/* 8b. …and a PR that never had `hold` answers 404, which is not a failure. This
 *     is the common case — most handoffs are of PRs nobody parked. */
{
  const r = run(['41', '--why', 'x'], { holdExists: false });
  check('a PR with no `hold` on it is handed off without error', r.code === 0, `exit ${r.code}`);
  check('…and the label is still applied',
        r.lines.some((l) => /labels resume$/.test(l)), r.acted.trim());
  check('…and it does not claim to have removed a label it did not',
        !/hold removed/.test(r.out));
}

/* 9. DRIFT GUARD: no GraphQL. `gh pr comment`/`gh pr edit` would do all of the
 *    above in fewer lines and on the budget that runs out — measured 2026-08-27,
 *    steward run 1140: `graphql remaining 0 of 5000` while `core remaining 4969
 *    of 5000`, and a finished, gated, pushed unit of work lost its PR to it. This
 *    verb is reached exactly when a run is already in trouble, so it is the last
 *    place that should draw on the empty bucket. */
{
  const src = readFileSync(SH, 'utf8')
    .split('\n').filter((l) => !l.trim().startsWith('#')).join('\n');
  const graphql = /\bgh (pr|issue|search) \w+/.exec(src);
  check('no GraphQL-backed `gh` verb is used anywhere in pr-rest.sh',
        graphql === null, graphql ? graphql[0] : 'every call is `gh api`');
}

/* 10. …and the usage line offers the verb, because a facility nobody can find is
 *     not a facility. AGENTS.md § the two labels points at this exact spelling. */
{
  const src = readFileSync(SH, 'utf8');
  check('the usage line documents `resume`', /pr-rest\.sh resume N --why/.test(src));
  const bad = spawnSync('bash', [SH, 'nonsense'], { encoding: 'utf8',
    env: { ...process.env, GITHUB_REPOSITORY: 'kevinrhaas/chicago' } });
  check('…and so does the error for an unknown command',
        /resume/.test(`${bad.stdout}${bad.stderr}`), `${bad.stdout}${bad.stderr}`.trim());
}

console.log(failures ? `\n${failures} FAILED` : '\nall passed');
process.exit(failures ? 1 : 0);

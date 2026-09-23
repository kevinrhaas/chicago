#!/usr/bin/env node
/**
 * test_pr_stuck.mjs — the reporter that ends the silence around a pull request
 * nothing in this repository can move (T-1368), tested in the four states that
 * look identical from outside and must be told apart.
 *
 * WHY THIS EXISTS. A `dirty` PR has no merge ref, so the `pull_request` gate
 * cannot start, so it carries zero check runs, so `gate` — a required check —
 * never passes, so merge-ready.sh never sees `clean` and the lap correctly
 * refuses a conflict it does not own. Nothing advances. Measured on #1495 and
 * #1497 (2026-09-19) and again on #1587, #1585, #1584 and #1590 (2026-09-20):
 * six pull requests, six pairs of hands, and both of the first two merged
 * THEMSELVES within minutes of a person pushing the merge — the rest of the
 * automation was sound and the only missing piece was anyone being told.
 *
 * AND THE SHAPE ALONE DOES NOT IDENTIFY IT, which is the whole difficulty and
 * every case below:
 *
 *   #1499  dirty, zero checks — and its run was STILL GOING. It rebased onto
 *          `dev` twice, re-derived, pushed and cleared itself with no hands at
 *          all. Acting on it would have collided with a live run for nothing.
 *   #1533  dirty, zero checks — and labelled `hold`, the owner's park switch.
 *   #1576  the same, and mistaken for the deadlock on 2026-09-20 as well.
 *   #1518  `unknown` indefinitely, and merged fine when asked directly.
 *
 * THE SCRIPT IS NOT COPIED HERE. Every case runs the REAL
 * `.github/steward/pr-stuck.sh` with `gh` faked on PATH, so a change that makes
 * it shout at a held or mid-run pull request fails here rather than on `dev`.
 */
import { mkdtempSync, mkdirSync, writeFileSync, chmodSync, rmSync, readFileSync, existsSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const SH = path.resolve(path.dirname(new URL(import.meta.url).pathname),
                        '..', '..', '..', '.github', 'steward', 'pr-stuck.sh');

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

const iso = (minutesAgo) => new Date(Date.now() - minutesAgo * 60_000)
  .toISOString().replace(/\.\d+Z$/, 'Z');

/**
 * Run the real script against a fake `gh`.
 *   prs       [{ n, branch, sha, labels[], state, headAgeMin, checks }]
 *   claims    { "t-1368": { runStatus: 'in_progress'|'completed'|null, ageHours } }
 *   comments  { "<n>": ["existing body", …] }
 * Every write the script attempts — label, unlabel, comment — is appended to a
 * file the caller reads back, because "what did it SAY about this PR" is the
 * only question that matters here.
 */
function run({ prs = [], claims = {}, comments = {}, listExit = 0, only = '', dry = '', soft = '' }) {
  const box = mkdtempSync(path.join(tmpdir(), 'prstuck-'));
  const bin = path.join(box, 'bin');
  mkdirSync(bin, { recursive: true });
  const acted = path.join(box, 'acted.txt');

  const byNum = {};
  for (const p of prs) byNum[String(p.n)] = p;
  const cfg = {
    list: prs.map((p) => `${p.n}\t${p.branch}\t${p.sha}\t${(p.labels || []).join(',')}`).join('\n'),
    prs: byNum, claims, comments,
  };
  writeFileSync(path.join(box, 'cfg.json'), JSON.stringify(cfg));

  // One fake `gh`, driven by cfg.json. Node does the parsing because the real
  // script's calls differ only in their path and --jq expression, and matching
  // those in bash is how a fake stops resembling the API it stands for.
  writeFileSync(path.join(bin, 'gh'), `#!/usr/bin/env bash
exec node ${JSON.stringify(path.join(box, 'gh.mjs'))} "$@"
`);
  chmodSync(path.join(bin, 'gh'), 0o755);

  writeFileSync(path.join(box, 'gh.mjs'), `
import { readFileSync, appendFileSync } from 'node:fs';
const cfg = JSON.parse(readFileSync(${JSON.stringify(path.join(box, 'cfg.json'))}, 'utf8'));
const ACTED = ${JSON.stringify(acted)};
const argv = process.argv.slice(2);
const joined = argov => argov.join(' ');
const all = argv.join(' ');
const pathArg = argv.find(a => a.startsWith('repos/')) || '';
const jq = (() => { const i = argv.indexOf('--jq'); return i < 0 ? '' : argv[i + 1]; })();
const method = (() => { const i = argv.indexOf('-X'); return i < 0 ? 'GET' : argv[i + 1]; })();
const iso = (hoursAgo) => new Date(Date.now() - hoursAgo * 3600000).toISOString().replace(/\\.\\d+Z$/, 'Z');
const isoMin = (minAgo) => new Date(Date.now() - minAgo * 60000).toISOString().replace(/\\.\\d+Z$/, 'Z');
const out = (s) => { process.stdout.write(String(s) + '\\n'); process.exit(0); };

// the label vocabulary — created once, and a 422 in real life
if (method === 'POST' && /^repos\\/[^/]+\\/[^/]+\\/labels$/.test(pathArg)) {
  appendFileSync(ACTED, 'ensure-label\\n'); process.exit(0);
}
// add a label to a PR
let m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/issues\\/(\\d+)\\/labels$/);
if (m && method === 'POST') {
  const l = (argv.find(a => a.startsWith('labels[]=')) || '').split('=')[1] || '?';
  appendFileSync(ACTED, 'label ' + m[1] + ' ' + l + '\\n'); process.exit(0);
}
// remove one
m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/issues\\/(\\d+)\\/labels\\/(.+)$/);
if (m && method === 'DELETE') {
  appendFileSync(ACTED, 'unlabel ' + m[1] + ' ' + m[2] + '\\n'); process.exit(0);
}
// comments: read, then post (the body arrives on stdin)
m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/issues\\/(\\d+)\\/comments$/);
if (m) {
  if (method === 'POST') {
    const body = readFileSync(0, 'utf8');
    appendFileSync(ACTED, 'comment ' + m[1] + ' ' + JSON.stringify(body) + '\\n');
    process.exit(0);
  }
  out((cfg.comments[m[1]] || []).join('\\n'));
}
// the PR list
if (/^repos\\/[^/]+\\/[^/]+\\/pulls\\?/.test(pathArg)) {
  process.stdout.write(cfg.list ? cfg.list + '\\n' : '');
  process.exit(${listExit});
}
// one PR's fields
m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/pulls\\/(\\d+)$/);
if (m) out((cfg.prs[m[1]] || {}).state || 'unknown');
// the claim marker
m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/commits\\/heads\\/claim\\/(t-\\d+)$/);
if (m) {
  const c = cfg.claims[m[1]];
  if (!c) process.exit(1);
  if (jq.includes('committer.date')) out(iso(c.ageHours == null ? 0.1 : c.ageHours));
  out('claim ' + m[1].toUpperCase() + ' — run\\n\\n' +
      (c.runUrl === null ? '' : 'run: https://github.com/kevinrhaas/polecat-platform/actions/runs/999\\n') +
      'nonce: abc');
}
// a head commit
m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/commits\\/([0-9a-f]+)$/);
if (m) {
  const pr = Object.values(cfg.prs).find(p => p.sha === m[1]);
  if (!pr) process.exit(1);
  if (pr.headAgeMin === null) out('');
  out(isoMin(pr.headAgeMin == null ? 600 : pr.headAgeMin));
}
// its check runs — the bare count the deadlock branch asks for...
m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/commits\\/([0-9a-f]+)\\/check-runs$/);
if (m) {
  const pr = Object.values(cfg.prs).find(p => p.sha === m[1]);
  out(pr ? (pr.checks == null ? 0 : pr.checks) : 0);
}
// ...and the newest \`gate\` verdict the red-gate branch asks for (T-1510). A head
// with no gate answers NOTHING, not a null string, because the script decides the
// shape on whether this call produced anything at all.
m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/commits\\/([0-9a-f]+)\\/check-runs\\?/);
if (m) {
  const pr = Object.values(cfg.prs).find(p => p.sha === m[1]);
  const g = pr && pr.gate;
  if (!g) process.exit(0);
  out(g.status + ':' + (g.conclusion == null ? 'none' : g.conclusion) +
      '\\t' + 'https://github.com/kevinrhaas/custom/actions/runs/7/job/' + (g.job == null ? 42 : g.job));
}
// the job behind that check run, for the step names
m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/actions\\/jobs\\/(\\d+)$/);
if (m) {
  const pr = Object.values(cfg.prs).find(p => p.gate && String(p.gate.job == null ? 42 : p.gate.job) === m[1]);
  if (!pr || !pr.gate.steps) process.exit(1);
  out(pr.gate.steps.map(s => '  * ' + s).join('\\n'));
}
// the run that owns a claim
m = pathArg.match(/^repos\\/[^/]+\\/[^/]+\\/actions\\/runs\\/(\\d+)$/);
if (m) {
  const c = Object.values(cfg.claims).find(c => c.runStatus !== undefined);
  if (!c || c.runStatus === null) process.exit(1);
  out(c.runStatus);
}
process.exit(0);
`);

  const r = spawnSync('bash', [SH], {
    cwd: box,
    encoding: 'utf8',
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`,
           GH_TOKEN: 'fake', STUCK_ONLY: only, STUCK_DRY_RUN: dry,
           STUCK_RETRY_SLEEP: '0', STUCK_SOFT_FAIL: soft,
           GITHUB_REPOSITORY: 'kevinrhaas/custom' },
  });
  const did = existsSync(acted) ? readFileSync(acted, 'utf8') : '';
  rmSync(box, { recursive: true, force: true });
  return { code: r.status, out: `${r.stdout || ''}${r.stderr || ''}`, acted: did };
}

const SHA = 'aaaaaaaabbbbbbbbccccccccddddddddeeeeeeee';
const deadlocked = (over = {}) => ({
  n: 1587, branch: 'steward/t-1400-whatever', sha: SHA, labels: [],
  state: 'dirty', headAgeMin: 600, checks: 0, ...over,
});

console.log('pr-stuck.sh — a PR nothing can move is never silent, and nothing else is touched');

/* 1. THE DEADLOCK ITSELF: dirty, zero check runs, and no claim marker, so no run
 *    holds the ticket. This is #1587/#1585/#1584 on 2026-09-20, each of which
 *    needed a person and got one only because somebody happened to look. */
{
  const r = run({ prs: [deadlocked()] });
  check('a dirty PR with zero checks and no live run is reported',
        /#1587 {2}STUCK/.test(r.out), (r.out.match(/^#1587.*$/m) || ['nothing said'])[0]);
  check('…labelled `stuck`', /^label 1587 stuck$/m.test(r.acted), r.acted.trim() || 'no label');
  check('…and told, on the PR itself', /^comment 1587 /m.test(r.acted), 'no comment');
  check('…naming the cycle rather than only the symptom',
        /zero check runs/.test(r.acted) && /required check/.test(r.acted));
  check('…and the hand-resolution path is in the comment, not only in a doc',
        /setup-merge-drivers\.sh/.test(r.acted) && /PR lap/.test(r.acted));
  // Every write it attempted is in `acted`, one per line. The only verbs that
  // may appear are the three this script is allowed: create the label, apply it,
  // say why. A merge or a push would be a new line here.
  check('…and it merges, pushes and resolves nothing',
        r.acted.split('\n').filter(Boolean)
          .every((l) => /^(ensure-label|label \d+ |comment \d+ |unlabel \d+ )/.test(l)),
        r.acted.split('\n').filter((l) => l && !/^(ensure-label|label|comment|unlabel)/.test(l)).join(' | '));
}

/* 2. #1499. A PR mid-run looks EXACTLY like the deadlock and is not it: that one
 *    rebased twice, re-derived, pushed and cleared itself. T-1368 calls touching
 *    such a PR a fault of the ticket, in those words. */
{
  const r = run({ prs: [deadlocked({ n: 1499, branch: 'steward/t-1343-something' })],
                  claims: { 't-1343': { runStatus: 'in_progress', ageHours: 1 } } });
  check('a PR whose owning run is still in_progress is NOT reported',
        !/STUCK/.test(r.out), (r.out.match(/^#1499.*$/m) || [''])[0]);
  check('…and nothing at all was written to it', r.acted.replace(/ensure-label\n/g, '') === '',
        r.acted.trim());
  check('…and the run is named in the log, so the judgement can be checked',
        /claim\/t-1343 names a run that is still in_progress/.test(r.out));
}

/* 3. The same shape once that run has finished IS the deadlock. */
{
  const r = run({ prs: [deadlocked({ n: 1499, branch: 'steward/t-1343-something' })],
                  claims: { 't-1343': { runStatus: 'completed', ageHours: 5 } } });
  check('a finished run leaves its PR reportable', /#1499 {2}STUCK/.test(r.out));
  check('…and it is reported', /^label 1499 stuck$/m.test(r.acted), r.acted.trim());
}

/* 3b. A marker whose run cannot be read at all is treated as ALIVE until it is
 *     older than the three hours ticket.mjs already calls a dead run. Never act
 *     on a maybe-live run: that is rule 4b of the ticket. */
{
  const r = run({ prs: [deadlocked({ n: 1500, branch: 'steward/t-1344-x' })],
                  claims: { 't-1344': { runStatus: null, ageHours: 1 } } });
  check('an unreadable run inside the run window is assumed alive',
        !/STUCK/.test(r.out) && /assuming it is alive/.test(r.out));

  const s = run({ prs: [deadlocked({ n: 1500, branch: 'steward/t-1344-x' })],
                  claims: { 't-1344': { runStatus: null, ageHours: 9 } } });
  check('…and past it, the marker is litter and the PR is reported',
        /#1500 {2}STUCK/.test(s.out), (s.out.match(/^#1500.*$/m) || [''])[0]);
}

/* 4. `hold` — #1533 and #1576, both mistaken for the deadlock on 2026-09-20.
 *    A park a robot can overrule is not a park, and a park it SHOUTS at is not
 *    much better. Labels are read before any state is. */
{
  const r = run({ prs: [deadlocked({ n: 1576, labels: ['hold'] })] });
  check('a `hold` PR is never reported however identical it looks',
        !/STUCK/.test(r.out) && !/^label 1576/m.test(r.acted), r.acted.trim());
  check('…and the log says it was seen and left, not that it was absent',
        /#1576 {2}held/.test(r.out));
}

/* 5. `unknown` IS NOT A DIAGNOSIS. #1518 read `unknown` indefinitely and merged
 *    fine when asked directly. Reporting on it would be a lie with a label on it. */
{
  const r = run({ prs: [deadlocked({ n: 1518, state: 'unknown' })] });
  check('an `unknown` PR is not called stuck', !/STUCK/.test(r.out));
  check('…and nothing was written to it', !/^label 1518/m.test(r.acted));
}

/* 6. A LABEL THAT OUTLIVES ITS REASON IS WORSE THAN NO LABEL. The lap cleared
 *    this one; the reporter takes its own word back. */
{
  const r = run({ prs: [deadlocked({ n: 1587, state: 'blocked', labels: ['stuck'] })] });
  check('a PR that came unstuck loses the label',
        /^unlabel 1587 stuck$/m.test(r.acted), r.acted.trim() || 'nothing');
  check('…and the summary counts it', /unlabelled=1/.test(r.out));
}

/* 7. EVERY PR IS DIRTY FOR A WHILE AFTER A MERGE INTO dev (T-0857) — that is the
 *    normal state of this queue, not a fault, and the lap is what clears it.
 *    Shouting at a PR the lap has not reached yet is how a signal becomes noise. */
{
  const r = run({ prs: [deadlocked({ headAgeMin: 4 })] });
  check('a freshly-pushed dirty PR is left for the lap',
        !/STUCK/.test(r.out) && /too-young=1/.test(r.out),
        (r.out.match(/^#1587.*$/m) || [''])[0]);
}

/* 7b. …and a head whose date cannot be read is not an old one. `to_epoch`
 *     answers 0 when it cannot parse, and 0 reads as decades. */
{
  const r = run({ prs: [deadlocked({ headAgeMin: null })] });
  check('a PR whose age cannot be read is not reported on', !/STUCK/.test(r.out));
  check('…and it says that is why', /age is unknown/.test(r.out));
}

/* 8. #1590: dirty WITH a green gate. It could not merge either, and it cost
 *    hands. Reported, with the sentence that fits it rather than the other one. */
{
  const r = run({ prs: [deadlocked({ n: 1590, checks: 3 })] });
  check('a dirty PR whose gate already passed is still reported',
        /#1590 {2}STUCK/.test(r.out));
  check('…and the comment says `dirty` is not `clean` rather than talking about zero checks',
        /dirty` is not `clean/.test(r.acted) && !/zero check runs/.test(r.acted));
}

/* 9. ONE COMMENT PER STUCK HEAD. Once a sweep would bury the PR; the sweep runs
 *    on every steward push. */
{
  const before = `PR stuck: no automation in this repository can move this pull request (\`${SHA.slice(0, 8)}\`)`;
  const r = run({ prs: [deadlocked()], comments: { 1587: [before] } });
  check('a head already commented on is not commented on twice',
        !/^comment 1587/m.test(r.acted), r.acted.trim());
  check('…and the log says why, rather than going quiet', /already said so on this head/.test(r.out));
}

/* 10. A FAILED LIST FAILS THE RUN. `PRS=$(gh api …)` carries gh's status and the
 *     script has no `set -e`, so a failure leaves the list empty and the loop
 *     runs zero times — printing what a healthy empty queue prints. That is the
 *     shape that made the blind lap look green all morning on 2026-09-14, and a
 *     reporter that cannot see the queue has not reported on it. */
{
  const r = run({ prs: [], listExit: 1 });
  check('a failed PR-list call fails the run', r.code !== 0, `exit ${r.code}`);
  check('…and never reports a quiet queue it never saw', !/deadlocked=0 red-gate=0/.test(r.out));
}

/* 10b. …EXCEPT WHEN THAT FAILURE WOULD LAND ON SOMEBODY ELSE'S PULL REQUEST. A
 *      run started by a push creates a check run on the pushed head sha, and for
 *      a `steward/**` branch that sha is an open PR's head. A failing non-required
 *      check makes the PR `unstable`, and merge-ready.sh merges only on `clean` —
 *      so a rate-limited sweep would leave a FINISHED pull request waiting on
 *      checks for ever. The workflow sets STUCK_SOFT_FAIL on that trigger alone;
 *      the same sweep on a push to `dev` still fails hard, and a rate limit does
 *      not outlast the gap between the two. */
{
  const r = run({ prs: [], listExit: 1, soft: '1' });
  check('a blind sweep on a steward branch does not fail the job', r.code === 0, `exit ${r.code}`);
  check('…and is still loud about it', /::error::/.test(r.out));
  check('…and says why it is not failing, rather than looking healthy',
        /would attach to an open PR's head sha/.test(r.out));
  check('…and still never reports a queue it never saw', !/deadlocked=0 red-gate=0/.test(r.out));
}

/* 11. The honest empty queue still passes — the guard above must not cost that. */
{
  const r = run({ prs: [], listExit: 0 });
  check('a genuinely empty queue is not an error', r.code === 0, `exit ${r.code}`);
  check('…and still prints the summary', /PR stuck: deadlocked=0 red-gate=0/.test(r.out));
}

/* 12. DRY RUN WRITES NOTHING, so the first live sweep could be watched before it
 *     was trusted. */
{
  const r = run({ prs: [deadlocked()], dry: '1' });
  check('a dry run labels and comments on nothing', r.acted === '', r.acted.trim());
  check('…and still says what it found', /#1587 {2}STUCK/.test(r.out));
}

/* ------------------------------------------------------------------ T-1510
 * THE SECOND SHAPE: a RED GATE under a run that has finished. Nothing in this
 * repository owns that state — the lap merges and pushes but does not gate,
 * `merge-ready` merges only `clean`, and the run that would have fixed it is
 * over. Measured 2026-09-21: #1616's steward run completed SUCCESS 28 seconds
 * after its own gate went red, #1618's four minutes before, and both sat until
 * somebody read the logs. The near-misses below are the reason this is four
 * cases and not one: each of them looks the same from outside. */
const redGated = (over = {}) => ({
  n: 1616, branch: 'steward/t-1294-joiner-north-02-ownership', sha: SHA, labels: [],
  state: 'blocked', headAgeMin: 600,
  gate: { status: 'completed', conclusion: 'failure',
          steps: ['Does this change carry a changelog entry?'] },
  ...over,
});

/* 12b. The shape itself. */
{
  const r = run({ prs: [redGated()] });
  check('a blocked PR with a failed gate and a finished run is reported',
        /#1616 {2}STUCK/.test(r.out), (r.out.match(/^#1616.*$/m) || ['nothing said'])[0]);
  check('…labelled `stuck`', /^label 1616 stuck$/m.test(r.acted), r.acted.trim() || 'no label');
  check('…and counted apart from the deadlock, which has a different remedy',
        /red-gate=1/.test(r.out) && /deadlocked=0/.test(r.out));
  check('…NAMING THE FAILING STEP, so the reader is not sent back to the logs',
        /Does this change carry a changelog entry\?/.test(r.acted),
        'the step name is most of what the reporter is for');
  check('…and saying why nothing is coming for it',
        /merges only what GitHub calls `clean`/.test(r.acted) && /does NOT gate/.test(r.acted));
  check('…and it still merges, pushes and resolves nothing',
        r.acted.split('\n').filter(Boolean)
          .every((l) => /^(ensure-label|label \d+ |comment \d+ |unlabel \d+ )/.test(l)),
        r.acted.split('\n').filter((l) => l && !/^(ensure-label|label|comment|unlabel)/.test(l)).join(' | '));
}

/* 12b-ii. …AND WHEN THE FAILING STEP IS ONE `preflight.sh` ALREADY ASKS, it says so.
 *         The changelog-entry question is asked only on the `pull_request` event,
 *         where a base ref exists, and is out of tools/check.sh on purpose — the
 *         bake regenerates data/ and correctly ships no entry (T-0409). So a run
 *         that runs the gate alone CANNOT find it, which is why #1049 sat red for
 *         2h19m and six more PRs did on 2026-09-21. Naming the rehearsal is the
 *         only enforcement a reporter that writes nothing can offer. */
{
  const r = run({ prs: [redGated()] });
  check('a changelog-entry failure names the rehearsal that would have caught it',
        /preflight\.sh/.test(r.acted), 'the run could have found this in seconds');
  check('…and says why running the gate alone could not',
        /out of `check\.sh` on\\npurpose/.test(r.acted) || /bake regenerates/.test(r.acted));
}

/* 12b-iii. …and it does NOT say it for a failure preflight does not ask about.
 *          A rehearsal named for every red is advice that stops being read. */
{
  const r = run({ prs: [redGated({ gate: { status: 'completed', conclusion: 'failure',
                                           steps: ['Run the gate'] } })] });
  check('a failure preflight does not rehearse is not told to run preflight',
        !/preflight\.sh/.test(r.acted), 'advice given for everything is advice for nothing');
  check('…and the step is still named', /Run the gate/.test(r.acted));
}

/* 12c. A GATE STILL RUNNING IS NOT A RED ONE. `blocked` is what a PR reads while
 *      its gate runs, and that is the gate's business — reporting it would shout
 *      at every PR in the queue within a minute of every push. */
{
  const r = run({ prs: [redGated({ gate: { status: 'in_progress', conclusion: null } })] });
  check('a gate still in progress is not a red gate',
        !/STUCK/.test(r.out) && /something can move this/.test(r.out),
        (r.out.match(/^#1616.*$/m) || [''])[0]);
  check('…and nothing was written to it', !/^label 1616/m.test(r.acted), r.acted.trim());
}

/* 12d. A RED GATE UNDER A LIVE RUN IS THE RUN'S TO FIX, and it commonly does —
 *      that is the whole of #1499 reached from the other side. The liveness test
 *      guards both shapes for exactly this reason. */
{
  const r = run({ prs: [redGated({ branch: 'steward/t-1343-something' })],
                  claims: { 't-1343': { runStatus: 'in_progress', ageHours: 1 } } });
  check('a red gate under a run that is still going is left alone',
        !/STUCK/.test(r.out), (r.out.match(/^#1616.*$/m) || [''])[0]);
  check('…and the log names the run, so the judgement can be checked',
        /still in_progress/.test(r.out));
  check('…and says what it saw, not merely that it skipped',
        /blocked with a red gate/.test(r.out));
}

/* 12e. …and a freshly-red head is not one either. A run that pushes a fix within
 *      the minute is the normal way this clears; MIN_AGE is what keeps the
 *      reporter from being the noise it was built to replace. */
{
  const r = run({ prs: [redGated({ headAgeMin: 4 })] });
  check('a freshly-red head is left for the run that owns it',
        !/STUCK/.test(r.out) && /too-young=1/.test(r.out),
        (r.out.match(/^#1616.*$/m) || [''])[0]);
}

/* 12f. AND THE LABEL COMES BACK OFF when the gate goes green, exactly as it does
 *      when a dirty PR comes clean. A label that outlives its reason is worse
 *      than no label, and a red-gate label is the easiest kind to strand. */
{
  const r = run({ prs: [redGated({ labels: ['stuck'],
                                   gate: { status: 'completed', conclusion: 'success' } })] });
  check('a PR whose gate went green loses the label',
        /^unlabel 1616 stuck$/m.test(r.acted), r.acted.trim() || 'nothing');
  check('…and the summary counts it', /unlabelled=1/.test(r.out));
}

/* 12g. A head with NO gate at all is not red. It is a PR the gate has not reached
 *      — or shape A, which the `dirty` branch above has already claimed. */
{
  const r = run({ prs: [redGated({ gate: null })] });
  check('a head carrying no gate is not called red', !/STUCK/.test(r.out));
}

/* 13. DRIFT GUARDS on the lines that carry the judgement. */
{
  const src = readFileSync(SH, 'utf8')
    .split('\n').filter((l) => !l.trim().startsWith('#')).join('\n');
  check('drafts are filtered out of the list',
        /select\(\.draft==false\)/.test(src));
  check('`hold` is NOT filtered out of the list — it has to be SEEN to be left alone',
        !/index\("hold"\) \| not/.test(src));
  // The comment body it writes CONTAINS `git push` and a merge recipe, on
  // purpose — that is the hand-resolution path rule 5 of the ticket keeps
  // available. So the guard is on the calls, not on the prose: no merge endpoint,
  // and no git invoked at all.
  const calls = src.split('\n').filter((l) => /\bgh api\b|^\s*git\b/.test(l)).join('\n');
  check('nothing here merges or pushes',
        !/\/merge\b/.test(calls) && !/\bgit\b/.test(calls), calls.match(/.*(merge|git).*/)?.[0]);
  check('no GraphQL-backed `gh pr|issue` verb is used — the budget that fails',
        /\bgh (pr|issue) (comment|create|merge|view|list|edit|close)\b/.exec(src) === null);
}

/* 14. AND THE TRIGGER, which is the half a script cannot hold. `schedule` fires
 *     only from the default branch (`main`), and this file lives on `dev`; a
 *     reporter hung on a push to `dev` goes quiet exactly when the queue stops,
 *     which is when it is needed. The steward-branch push is the loop's own
 *     heartbeat and is what makes this fire during a jam. */
{
  const wf = path.resolve(path.dirname(new URL(import.meta.url).pathname),
                          '..', '..', '..', '.github', 'workflows', 'chicago-4d-pr-stuck.yml');
  const y = readFileSync(wf, 'utf8');
  check('the sweep runs on a steward-branch push, not only on a push to dev',
        /'steward\/\*\*'/.test(y), 'the trigger that survives a jammed queue');
  check('…and it is not `schedule`, which never fires from a non-default branch',
        !/^\s*schedule:/m.test(y));
  check('…and it can be dispatched at a single PR', /STUCK_ONLY/.test(y));
}

/* 15. T-1288 IS NOT UNDONE. Its measurement — one commit must never get two
 *     `gate` runs, and a PR must never wait on the slower of a pair — is why
 *     chicago-4d-check.yml filters its push trigger to dev and main. The fix for
 *     T-1368 must not reach for that filter, and this is the guard that says so.
 */
{
  const gate = path.resolve(path.dirname(new URL(import.meta.url).pathname),
                            '..', '..', '..', '.github', 'workflows', 'chicago-4d-check.yml');
  const y = readFileSync(gate, 'utf8');
  check('the gate still triggers on pushes to dev and main only (T-1288)',
        /push:\s*\n\s*branches: \[dev, main\]/.test(y),
        'an unfiltered push trigger double-gates every open PR');
}

console.log(failures ? `\n${failures} failure(s)` : '\nall good');
process.exit(failures ? 1 : 0);

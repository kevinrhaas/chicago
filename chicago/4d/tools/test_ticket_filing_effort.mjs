#!/usr/bin/env node
/**
 * test_ticket_filing_effort.mjs — A FILING FAULT IS CAUGHT AT FILING, AND A FAULT THIS
 * DIFF CANNOT FIX IS NOT CHARGED TO IT (T-1593).
 *
 * WHAT HAPPENED. The tickets moved into kevinrhaas/chicago-tickets on 2026-09-23, so
 * `ticket queue` is the one step of the gate whose subject is NOT in the diff under
 * review. On 2026-09-25 that turned into a red nobody could clear:
 *
 *   23:07Z  T-1585 and T-1586 are filed at effort L, which the queue gate refuses —
 *           an L is more than one run, so whoever claims it cannot finish it.
 *   23:44Z  the gate on #51 — a pull request whose whole diff is AGENTS.md, a changelog
 *           entry and three files under tools/ — comes back red on five of 628 steps.
 *           The fifth is `ticket queue`, naming two tickets #51 never touched.
 *
 * #51 merged with GH_REST_MERGE_BLIND=1 and the reason written on it, which is the
 * escape hatch working and not a thing any run should need. Both halves are held here:
 *
 *   1-5   `new` REFUSES an effort-L filing, and an effort the gate cannot read, before
 *         anything is written or an id is minted — at the prompt, where one person fixes
 *         it in one command. `--anyway` is the budget's override and cannot reach this.
 *   6-8   `check` run bare is unchanged and STRICT: the L fails, by name, with the split
 *         command. That is where the rule keeps its teeth.
 *   9-12  `check --inherited-warn` — what `tools/check.sh` passes — reports that same
 *         fault as a WARN naming the filing and the clearing command, and passes.
 *   13-15 …and it softens NOTHING it should not: a fault in this repository's own files
 *         still fails, a tickets clone this run has dirtied still fails, and in embedded
 *         mode (tickets inside the code repo, where they ARE in the diff) it is strict.
 *
 * Every assertion is run against a real clone of a real bare tickets repository, because
 * the whole distinction is about which repository a file lives in — a fixture folder
 * could not tell the two apart.
 */
import { mkdtempSync, mkdirSync, rmSync, writeFileSync, readFileSync, readdirSync, cpSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
let failures = 0;
const check = (label, ok, detail = '') => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${label}${!ok && detail ? `\n        ${detail}` : ''}`);
  if (!ok) failures += 1;
};
const git = (cwd, ...a) => spawnSync('git', a, { cwd, encoding: 'utf8' });

const root = mkdtempSync(path.join(tmpdir(), 'c4d-filing-'));
const bare = path.join(root, 'tickets.git');

/** The publish.sh line `check` pins itself to — present means no code-scope fault. */
const PIN = 'cp -f tickets/tickets.json "$SITE/tickets.json"';

function ticketText(id, title, extra = {}) {
  const fm = { id, title, state: 'open', epic: 'META', requested_by: 'loop', seen: false, effort: 'S',
    legacy_id: null, parent: null, opened: '2026-09-25', closed: null, pr: null, claimed_by: null,
    blocked_on: null, needs_bake: false, closed_at: null, claimed_run: null };
  return `---\n${Object.entries({ ...fm, ...extra }).map(([k, v]) => `${k}: ${v ?? 'null'}`).join('\n')}\n---\n\n${title}.\n\n**Acceptance:** it is done.\n`;
}

// The tickets repository as it stood at 23:07Z: two workable tickets, and one of them
// filed at effort L — the state that turned #51 red.
const SEEDED = [['T-1584', 'a ticket sized for one run', 'S'], ['T-1585', 'a ticket nobody can finish in one run', 'L']];
{
  const seed = path.join(root, 'seed');
  mkdirSync(path.join(seed, 'T-1500-1749'), { recursive: true });
  writeFileSync(path.join(seed, 'QUEUE.md'), `# QUEUE — top is next. THE OWNER ORDERS THIS FILE.\n\n${
    SEEDED.map(([id, title]) => `${id} — ${title}`).join('\n')}\n`);
  writeFileSync(path.join(seed, '.gitignore'), 'BOARD.md\ntickets.json\n');
  for (const [id, title, effort] of SEEDED) {
    writeFileSync(path.join(seed, 'T-1500-1749', `${id}-fixture.md`), ticketText(id, title, { effort }));
  }
  git(seed, 'init', '-q', '-b', 'main');
  git(seed, '-c', 'user.name=t', '-c', 'user.email=t@t', 'add', '-A');
  git(seed, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'T-1585: new — a ticket nobody can finish in one run');
  git(root, 'clone', '-q', '--bare', seed, bare);
}

/** A code-repo-shaped sandbox. `mode: 'repo'` clones the tickets repository into
 *  tickets/ (the real layout); `mode: 'embedded'` puts plain files there instead. */
function sandbox(name, { mode = 'repo', pin = true } = {}) {
  const code = path.join(root, name);
  const app = path.join(code, 'chicago', '4d');
  mkdirSync(path.join(app, 'tools'), { recursive: true });
  cpSync(path.join(HERE, 'ticket.mjs'), path.join(app, 'tools', 'ticket.mjs'));
  writeFileSync(path.join(app, 'tools', 'publish.sh'),
    `#!/usr/bin/env bash\n# a stand-in for the real one\n${pin ? PIN : 'cp -f tickets/tickets.json "$SITE/elsewhere.json"'}\n`);
  git(code, 'init', '-q', '-b', 'dev');
  if (mode === 'repo') {
    git(root, 'clone', '-q', bare, path.join(app, 'tickets'));
    git(path.join(app, 'tickets'), 'config', 'user.name', name);
    git(path.join(app, 'tickets'), 'config', 'user.email', `${name}@t`);
  } else {
    mkdirSync(path.join(app, 'tickets'), { recursive: true });
    cpSync(path.join(root, 'seed', 'QUEUE.md'), path.join(app, 'tickets', 'QUEUE.md'));
    for (const [id, title, effort] of SEEDED) {
      writeFileSync(path.join(app, 'tickets', `${id}-fixture.md`), ticketText(id, title, { effort }));
    }
  }
  git(code, 'add', '-A');
  git(code, '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-q', '-m', 'the code repo');
  return app;
}
const env = { ...process.env, GITHUB_ACTIONS: '', GITHUB_RUN_ID: '' };
delete env.CHICAGO_TICKETS_DIR;
const tool = (app, ...args) => {
  const r = spawnSync('node', [path.join(app, 'tools', 'ticket.mjs'), ...args],
    { cwd: app, encoding: 'utf8', env });
  return { status: r.status, out: `${r.stdout ?? ''}${r.stderr ?? ''}` };
};
const ticketFiles = (app) => {
  const dir = path.join(app, 'tickets');
  const flat = readdirSync(dir).filter((f) => /^T-\d+.*\.md$/.test(f));
  const chunk = readdirSync(dir).filter((f) => /^T-\d+-\d+$/.test(f))
    .flatMap((d) => readdirSync(path.join(dir, d)));
  return [...flat, ...chunk];
};

try {
  /* ----------------------------------------- 1-5. the refusal at the prompt */
  console.log('\n  a run filing a ticket it has sized as more than one run');
  const A = sandbox('a');
  const before = ticketFiles(A).length;
  const L = tool(A, 'new', 'a whole programme of work', '--effort', 'L', '--after', 'T-1584');
  check('1. `new --effort L` is REFUSED', L.status !== 0 && /REFUSED/.test(L.out),
    L.out.trim().split('\n')[0] || `status ${L.status}`);
  check('   …and says to file the pieces, naming the anchor it was given',
    /--effort M --after T-1584/.test(L.out) && /first piece/.test(L.out) && /second piece/.test(L.out),
    L.out.trim());
  check('2. …and names `split` for an L that is already in the queue',
    /ticket\.mjs split T-NNNN/.test(L.out), L.out.trim());
  check('3. …nothing is written and no id is minted — the refusal is before the file',
    ticketFiles(A).length === before
    && !readFileSync(path.join(A, 'tickets', 'QUEUE.md'), 'utf8').includes('whole programme'),
    `${before} ticket file(s) before, ${ticketFiles(A).length} after`);
  const forced = tool(A, 'new', 'a whole programme of work', '--effort', 'L', '--after', 'T-1584',
    '--anyway', '--why', 'the budget lets me file over the ceiling, so try it here too');
  check('4. `--anyway` cannot take it — that override is the BUDGET\'s, and this is not a budget',
    forced.status !== 0 && /REFUSED/.test(forced.out) && ticketFiles(A).length === before,
    forced.out.trim().split('\n')[0] || `status ${forced.status}`);
  const bad = tool(A, 'new', 'filed with an effort nothing can read', '--effort', 'XL', '--after', 'T-1584');
  check('5. an effort the gate cannot read is refused at the prompt too',
    bad.status !== 0 && /REFUSED/.test(bad.out) && ticketFiles(A).length === before,
    bad.out.trim().split('\n')[0] || `status ${bad.status}`);
  const ok = tool(A, 'new', 'one run of work', '--effort', 'S', '--after', 'T-1584');
  check('   …and a ticket sized for one run still files, carrying the effort it was given',
    ok.status === 0 && ticketFiles(A).some((f) => {
      const id = /(T-\d{4})/.exec(ok.out)?.[1];
      return id && f.startsWith(id);
    }), ok.out.trim().split('\n')[0] || `status ${ok.status}`);

  /* -------------------------- 6-8. the state that failed, read strictly */
  console.log('\n  the queue as it stood at 23:07Z on 2026-09-25, with T-1585 filed as an L');
  const B = sandbox('b');
  const strict = tool(B, 'check');
  check('6. `check` run bare still FAILS on it — the rule keeps its teeth',
    strict.status === 1 && /ticket queue FAILED/.test(strict.out), strict.out.trim());
  check('7. …naming the offending ticket and what it is', /T-1585/.test(strict.out)
    && /effort L is in the queue/.test(strict.out), strict.out.trim());
  check('8. …and the one command that cuts it',
    /ticket\.mjs split T-1585/.test(strict.out), strict.out.trim());

  /* ------------------ 9-12. the same state, read by the code repo's gate */
  const warn = tool(B, 'check', '--inherited-warn');
  check('9. THE FIX: `--inherited-warn` PASSES — no code change in this diff can clear it',
    warn.status === 0, `status ${warn.status}: ${warn.out.trim()}`);
  check('10. …and reports it as a WARN, saying whose it is not',
    /WARN: 1 queue fault/.test(warn.out) && /cannot fix/.test(warn.out)
    && /chicago-tickets/.test(warn.out), warn.out.trim());
  check('11. …naming the filing that caused it, off the ticket and the tickets repo\'s history',
    /filed 2026-09-25 by loop/.test(warn.out) && /chicago-tickets [0-9a-f]{7,}/.test(warn.out),
    warn.out.trim());
  check('12. …and still the command that clears it, for every open PR at once',
    /ticket\.mjs split T-1585/.test(warn.out)
    && /inherited fault\(s\) reported above as WARN/.test(warn.out), warn.out.trim());

  /* ------------------------------ 13-15. and it softens nothing else */
  console.log('\n  the three things `--inherited-warn` must NOT let through');
  const C = sandbox('c', { pin: false });
  const code = tool(C, 'check', '--inherited-warn');
  check('13. a fault in THIS repository\'s own files still fails — it is in the diff',
    code.status === 1 && /ticket queue FAILED/.test(code.out) && /publish\.sh/.test(code.out),
    code.out.trim());

  const D = sandbox('d');
  writeFileSync(path.join(D, 'tickets', 'T-1500-1749', 'T-1586-fixture.md'),
    ticketText('T-1586', 'a second L, filed by this very run', { effort: 'L' }));
  const dirty = tool(D, 'check', '--inherited-warn');
  check('14. a tickets clone THIS RUN has dirtied still fails — this run put it there',
    dirty.status === 1 && /ticket queue FAILED/.test(dirty.out) && /T-1586/.test(dirty.out),
    dirty.out.trim());

  const E = sandbox('e', { mode: 'embedded' });
  const embedded = tool(E, 'check', '--inherited-warn');
  check('15. in embedded mode the tickets ARE in the diff, so the flag is strict',
    embedded.status === 1 && /ticket queue FAILED/.test(embedded.out) && /T-1585/.test(embedded.out),
    embedded.out.trim());
} finally {
  rmSync(root, { recursive: true, force: true });
}

console.log(failures
  ? `\n  ${failures} failure(s)\n`
  : '\n  an unsplit L cannot be filed, and a queue fault no code diff carries is reported rather than charged to it\n');
process.exit(failures ? 1 : 0);

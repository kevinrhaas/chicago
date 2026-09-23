#!/usr/bin/env node
/**
 * The drain lap's assertions, and proof they still fire.
 *
 * T-0833. The thing worth testing hardest here is the REFUSAL, not the merge.
 * A batching tool that quietly resolves one conflict it should not have touched
 * looks exactly like a batching tool that works — the batch is green, the branch
 * is one commit, and the thing it picked between is gone. #876 against #888
 * collided in `newberry_index/coverage.json`, two research claims about the same
 * page: a merge tool that picks one of those has destroyed a reading and told
 * nobody. So the cases below spend most of their weight on what the lap declines,
 * and on the two properties that make a refusal usable: a non-zero exit, and the
 * markers still in the tree afterwards.
 *
 * The laps run in scratch repositories rather than against this one, because a
 * lap MERGES and this checkout is where the run's own work lives. What makes them
 * honest rather than a mock is that they drive the real `drain()` through real
 * `git merge`s with the repo's real `merge-smoke-state.mjs` registered: the
 * conflicts are genuine, the driver that settles them is the shipped one, and the
 * classification the lap does is the shipped classification. The follow-ups
 * (stamp-changelog, ticket.mjs) are absent in a scratch repo and are skipped
 * there by the same `existsSync` guard that runs them here — one code path, not
 * two.
 */
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { drain, parseArgs } from './drain.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const SMOKE = path.join(HERE, 'merge-smoke-state.mjs');

let pass = 0; let fail = 0;
const ok = (cond, what) => {
  if (cond) { pass++; console.log(`  ok    ${what}`); }
  else { fail++; console.log(`  FAIL  ${what}`); }
};

const rd = (n) => ({ tree: `t${n}`, viewport: 'desktop', stage: n, result: 'green' });
const led = (...r) => `${JSON.stringify({ readings: r }, null, 1)}\n`;

/**
 * A scratch repository shaped like the real conflict: a driver-covered ledger
 * that both sides append to, and a plain source file beside it.
 *
 *   base ── featureA   (ledger + source A)
 *        └─ featureB   (ledger + source B, optionally colliding)
 */
function fixture({ collide }) {
  const dir = mkdtempSync(path.join(tmpdir(), 'drain-'));
  const git = (...a) => spawnSync('git', ['-C', dir, ...a], { encoding: 'utf8' });
  const write = (rel, body) => writeFileSync(path.join(dir, rel), body);

  git('init', '-q', '-b', 'dev');
  git('config', 'user.email', 't@t'); git('config', 'user.name', 't');
  git('config', 'merge.smokestate.driver', `node ${SMOKE} %O %A %B %P`);
  write('.gitattributes', 'ledger.json merge=smokestate\n');
  write('ledger.json', led(rd(1)));
  write('claim.json', '{"page": 1, "reading": "base"}\n');
  git('add', '-A'); git('commit', '-qm', 'base');

  git('checkout', '-q', '-b', 'featureA');
  write('ledger.json', led(rd(1), rd(2)));
  write('claim.json', '{"page": 1, "reading": "A"}\n');
  git('add', '-A'); git('commit', '-qm', 'A');

  git('checkout', '-q', 'dev');
  git('checkout', '-q', '-b', 'featureB');
  write('ledger.json', led(rd(1), rd(3)));
  if (collide) write('claim.json', '{"page": 1, "reading": "B"}\n');
  else write('other.json', '{"page": 2, "reading": "B"}\n');
  git('add', '-A'); git('commit', '-qm', 'B');

  git('checkout', '-q', 'dev');
  return { dir, git };
}

const lap = (dir, targets, extra = []) =>
  drain(parseArgs([...targets, '--repo', dir, '--base', 'dev', '--branch', 'drain/test', '--no-gate', ...extra]), () => {});

export function selfTest() {
  pass = 0; fail = 0;

  // ── the lap the drivers are for ────────────────────────────────────────────
  console.log('\na batch whose only collision is driver-covered');
  {
    const { dir, git } = fixture({ collide: false });
    const r = lap(dir, ['featureA', 'featureB']);
    ok(r.ok, 'two branches that both appended to the ledger drain in one lap');
    ok(r.merged.length === 2, '…and BOTH are on the batch branch, not the first only');
    ok(git('rev-parse', '--abbrev-ref', 'HEAD').stdout.trim() === 'drain/test',
      '…on the branch the lap was told to cut, never on the base');
    const l = JSON.parse(readFileSync(path.join(dir, 'ledger.json'), 'utf8')).readings;
    ok(l.length === 3, '…and no smoke reading is lost to the batching');
    ok(git('status', '--porcelain').stdout.trim() === '',
      '…and the lap leaves a clean tree behind it');
    rmSync(dir, { recursive: true, force: true });
  }

  // ── the refusal, which is the point ───────────────────────────────────────
  console.log('\na batch carrying a conflict no driver knows');
  {
    const { dir, git } = fixture({ collide: true });
    const r = lap(dir, ['featureA', 'featureB']);
    ok(!r.ok, 'a real conflict REFUSES the lap rather than picking a side');
    ok(r.reason === 'conflict', '…and says that is why');
    ok(r.refused.includes('claim.json'), '…naming the file nothing knows how to merge');
    ok(r.merged.length === 1, '…after landing the targets that were clean, and no further');
    const text = readFileSync(path.join(dir, 'claim.json'), 'utf8');
    ok(/^<{7} /m.test(text) && /^>{7} /m.test(text),
      '…and leaves ORDINARY CONFLICT MARKERS, not an aborted merge');
    ok(git('diff', '--name-only', '--diff-filter=U').stdout.trim() === 'claim.json',
      '…with the merge still open, one `git merge --abort` from the old state');
    const l = JSON.parse(readFileSync(path.join(dir, 'ledger.json'), 'utf8')).readings;
    ok(l.length === 3 && !/^<{7} /m.test(readFileSync(path.join(dir, 'ledger.json'), 'utf8')),
      '…while the driver-covered file beside it was still resolved, not abandoned');
    rmSync(dir, { recursive: true, force: true });
  }

  // ── the two ways a lap must not start ─────────────────────────────────────
  console.log('\nwhat a lap refuses before it touches anything');
  {
    const { dir } = fixture({ collide: false });
    writeFileSync(path.join(dir, 'claim.json'), '{"page": 1, "reading": "uncommitted"}\n');
    const r = lap(dir, ['featureA']);
    ok(!r.ok && r.reason === 'dirty', 'a dirty working tree is refused, never stashed');
    ok(readFileSync(path.join(dir, 'claim.json'), 'utf8').includes('uncommitted'),
      '…and the uncommitted work is exactly where it was');
    rmSync(dir, { recursive: true, force: true });
  }
  {
    const { dir } = fixture({ collide: false });
    const r = lap(dir, []);
    ok(!r.ok && r.reason === 'no targets', 'a lap with nothing to drain does not cut a branch');
    rmSync(dir, { recursive: true, force: true });
  }

  // ── and the assertions themselves still fire ──────────────────────────────
  // A self-test whose cases cannot fail is the failure it was written to catch.
  console.log('\n…and the refusal assertion fires when the refusal stops happening');
  {
    const { dir } = fixture({ collide: true });
    const r = lap(dir, ['featureA', 'featureB']);
    ok(r.refused.length > 0 && !r.ok,
      'the colliding fixture really does collide — the case is not vacuously green');
    rmSync(dir, { recursive: true, force: true });
  }

  console.log(`\n${pass} passed, ${fail} failed`);
  return fail === 0;
}

if (process.argv[1] && process.argv[1].endsWith('drain-selftest.mjs')) {
  process.exit(selfTest() ? 0 : 1);
}

#!/usr/bin/env node
/**
 * The two build-product drivers' assertions, and proof they still fire.
 *
 * T-0831. These exist because both drivers are the kind that could quietly stop
 * doing their job: one succeeds by touching nothing, and the other's whole
 * promise is a negative — that no smoke reading is ever dropped. Neither failure
 * would be visible in a merge that reported success.
 *
 * The dangerous mistake this file is really guarding is the one that nearly
 * shipped: treating tools/dev-smoke-state.json as a build product. It sits in the
 * same conflict set as the five regenerable files, and it is an append-only
 * ledger no gate reads. Keeping ours there would have thrown away the other
 * side's readings silently. So the ledger's cases are the long half below.
 */
import { spawnSync } from 'node:child_process';
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const GENERATED = path.join(HERE, 'merge-generated.mjs');
const SMOKE = path.join(HERE, 'merge-smoke-state.mjs');

let pass = 0; let fail = 0;
const ok = (cond, what) => {
  if (cond) { pass++; console.log(`  ok    ${what}`); }
  else { fail++; console.log(`  FAIL  ${what}`); }
};

/** Run a driver over three versions the way git does; returns { code, text, log }. */
function run(driver, base, ours, theirs, placeholder) {
  const dir = mkdtempSync(path.join(tmpdir(), 'mg-'));
  const O = path.join(dir, 'base'); const A = path.join(dir, 'ours'); const B = path.join(dir, 'theirs');
  writeFileSync(O, base); writeFileSync(A, ours); writeFileSync(B, theirs);
  // spawnSync, not execFileSync: these drivers report on STDERR and exit 0, and
  // execFileSync hands back STDOUT, so a driver that succeeded quietly looked
  // like a crash. Measuring the wrong stream is how a green driver reads red.
  const p = spawnSync('node', [driver, O, A, B, placeholder], { encoding: 'utf8' });
  const code = p.status ?? 1;
  const log = `${p.stderr ?? ''}${p.stdout ?? ''}`;
  const text = readFileSync(A, 'utf8');
  rmSync(dir, { recursive: true, force: true });
  return { code, text, log };
}

// ── merge-generated: keeps ours, says so, and never fails ──────────────────
console.log('\nmerge-generated (the five build products)');
{
  const r = run(GENERATED, 'base\n', 'OURS\n', 'THEIRS\n', 'chicago/4d/tickets/BOARD.md');
  ok(r.code === 0, 'a conflicting build product does not fail the merge');
  ok(r.text === 'OURS\n', '…and OURS is what survives, byte for byte');
}
{
  const r = run(GENERATED, 'b\n', 'o\n', 't\n', 'chicago/4d/tickets/BOARD.md');
  ok(/ticket\.mjs board/.test(r.log),
    'BOARD.md is told to regenerate with ticket.mjs board');
}
{
  const r = run(GENERATED, 'b\n', 'o\n', 't\n', 'site/chicago/4d/build.json');
  ok(/publish\.sh/.test(r.log), 'build.json is told to regenerate with publish.sh');
}
{
  // A path with no advice must still merge — silence about HOW is acceptable,
  // failing the merge is not.
  const r = run(GENERATED, 'b\n', 'o\n', 't\n', 'some/unknown/thing.json');
  ok(r.code === 0 && r.text === 'o\n', 'an unlisted path still keeps ours and exits 0');
}

// ── merge-smoke-state: the ledger, where dropping a row is the whole risk ──
console.log('\nmerge-smoke-state (the append-only smoke ledger)');
const led = (...readings) => `${JSON.stringify({ note: 'ledger', readings }, null, 2)}\n`;
const rd = (n, extra = {}) => ({ viewport: 'mobile', stage: String(n), passed: n, ...extra });
const readingsOf = (text) => JSON.parse(text).readings;

{
  const r = run(SMOKE, led(rd(1)), led(rd(1), rd(2)), led(rd(1), rd(3)),
    'tools/dev-smoke-state.json');
  const got = readingsOf(r.text);
  ok(r.code === 0, 'two sides that each recorded a reading merge cleanly');
  ok(got.length === 3, '…and BOTH new readings survive — the whole point');
  ok(JSON.stringify(got[2]) === JSON.stringify(rd(3)), "…theirs' reading is the one appended");
}
{
  // The failure this driver exists to prevent, stated as its own case.
  const ours = led(rd(1), rd(2));
  const theirs = led(rd(1), rd(3), rd(4));
  const r = run(SMOKE, led(rd(1)), ours, theirs, 'tools/dev-smoke-state.json');
  const got = readingsOf(r.text);
  const kept = (x) => got.some((g) => JSON.stringify(g) === JSON.stringify(x));
  ok(kept(rd(2)) && kept(rd(3)) && kept(rd(4)),
    'NO reading is dropped when both sides appended — keeping ours would lose two');
}
{
  const r = run(SMOKE, led(rd(1)), led(rd(1), rd(2)), led(rd(1), rd(2)),
    'tools/dev-smoke-state.json');
  ok(readingsOf(r.text).length === 2,
    'a reading carried down both sides is held once, not twice');
}
{
  // Why the key is canonical at every depth: these two differ only INSIDE a
  // nested object. A replacer-array key would flatten them together and silently
  // drop one.
  const a = rd(9, { host: { load: 1 } });
  const b = rd(9, { host: { load: 2 } });
  const r = run(SMOKE, led(), led(a), led(b), 'tools/dev-smoke-state.json');
  ok(readingsOf(r.text).length === 2,
    'two readings differing only inside a NESTED object are both kept');
}
{
  const r = run(SMOKE, led(), led(rd(1)), '{ not json', 'tools/dev-smoke-state.json');
  ok(r.code !== 0, 'an unparseable side is REFUSED, not guessed at');
}
{
  const r = run(SMOKE, led(), led(rd(1)), '{"note":"x"}\n', 'tools/dev-smoke-state.json');
  ok(r.code !== 0, 'a side with no readings[] is REFUSED — this driver knows one shape');
}
{
  const r = run(SMOKE, led(), led(rd(1)), '{"readings":{}}\n', 'tools/dev-smoke-state.json');
  ok(r.code !== 0, '…and a readings that is not an array is refused too');
}
{
  const r = run(SMOKE, led(rd(1)), led(rd(1)), led(rd(1)), 'tools/dev-smoke-state.json');
  ok(r.code === 0 && readingsOf(r.text).length === 1,
    'identical sides merge to themselves, so a firing above means something');
}
{
  // The ledger's prose belongs to the branch being merged into, the same way
  // QUEUE.md's ORDER does.
  const ours = `${JSON.stringify({ note: 'OURS NOTE', readings: [rd(1)] }, null, 2)}\n`;
  const theirs = `${JSON.stringify({ note: 'THEIRS NOTE', readings: [rd(2)] }, null, 2)}\n`;
  const r = run(SMOKE, led(), ours, theirs, 'tools/dev-smoke-state.json');
  ok(JSON.parse(r.text).note === 'OURS NOTE', "ours' hand-written note is kept");
  ok(readingsOf(r.text).length === 2, '…without costing theirs a reading');
}

// ── end to end, through git itself ────────────────────────────────────────
//
// Everything above tests the SCRIPTS. This tests the WIRING — .gitattributes
// naming the driver, the driver being registered, and git actually reaching it
// during a real merge. Those are three separate things and only the last one is
// what a branch experiences. A driver that works perfectly and is never invoked
// looks exactly like no driver at all, which is the state this repo was in for
// five merges of PR #906.
console.log('\nend to end, through a real git merge');
{
  const dir = mkdtempSync(path.join(tmpdir(), 'mg-git-'));
  const git = (...a) => spawnSync('git', ['-C', dir, ...a], { encoding: 'utf8' });
  const write = (rel, body) => writeFileSync(path.join(dir, rel), body);

  git('init', '-q', '-b', 'main');
  git('config', 'user.email', 't@t'); git('config', 'user.name', 't');
  git('config', 'merge.generated.driver', `node ${GENERATED} %O %A %B %P`);
  git('config', 'merge.smokestate.driver', `node ${SMOKE} %O %A %B %P`);
  write('.gitattributes', 'board.md merge=generated\nledger.json merge=smokestate\n');
  write('board.md', 'base\n');
  write('ledger.json', led(rd(1)));
  git('add', '-A'); git('commit', '-qm', 'base');

  git('checkout', '-q', '-b', 'feature');
  write('board.md', 'OURS regenerated\n');
  write('ledger.json', led(rd(1), rd(2)));
  git('add', '-A'); git('commit', '-qm', 'feature');

  git('checkout', '-q', 'main');
  write('board.md', 'THEIRS regenerated\n');
  write('ledger.json', led(rd(1), rd(3)));
  git('add', '-A'); git('commit', '-qm', 'main moved');

  git('checkout', '-q', 'feature');
  const m = git('merge', '--no-edit', 'main');
  const conflicted = git('diff', '--name-only', '--diff-filter=U').stdout.trim();

  ok(m.status === 0 && conflicted === '',
    'a real merge where BOTH sides rewrote a build product no longer conflicts');
  ok(readFileSync(path.join(dir, 'board.md'), 'utf8') === 'OURS regenerated\n',
    '…ours survives it, ready to be regenerated');
  const l = JSON.parse(readFileSync(path.join(dir, 'ledger.json'), 'utf8')).readings;
  ok(l.length === 3,
    '…and the ledger beside it keeps BOTH sides’ readings rather than picking one');

  rmSync(dir, { recursive: true, force: true });
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);

#!/usr/bin/env node
/**
 * test_changelog_mirror.mjs — stamping the changelog does not leave either
 * published mirror stale, AND the gate that catches a genuinely stale mirror
 * still catches one.
 *
 * WHY THIS EXISTS (T-0155, the latent sibling T-0154 named on its way out).
 * `renderers/web/js/changelog.js` is published to TWO paths — `js/changelog.js`,
 * the contract URL Manager and the polecat.live launcher parse, and
 * `walk/js/changelog.js` inside the copied renderer tree the What's-new tab
 * imports — and `tools/check_published.mjs` compares both byte for byte.
 * `tools/stamp-changelog.mjs` rewrites the source. So a run that stamps AFTER
 * `tools/publish.sh` gets a red gate for following the documented rules, and the
 * only remedy is a REMEMBERED second publish: the kind of unwritten step that
 * goes wrong at 3am, which is precisely what it did to tickets.json on
 * T-0153/PR #318 before T-0154 closed that half.
 *
 * The fix is that the writer of the file maintains its mirrors. The DANGER in
 * that fix is the one T-0155's acceptance names: a tool that refreshed the
 * mirrors whenever it ran would launder a genuinely stale one, and the fault
 * class check_published exists for (#145, three parcels) would be invisible
 * again. So this file asserts BOTH halves, and the second one is the important
 * one.
 *
 * EVERYTHING RUNS IN A SANDBOX, for the reason test_ticket_mirror.mjs gives: the
 * tools resolve their paths from their own location, so a temporary tree of the
 * shape they expect — `<tmp>/chicago/4d/…` beside `<tmp>/site/chicago/4d/` —
 * gives them a whole world to be wrong in without touching the repository.
 */
import { mkdtempSync, mkdirSync, cpSync, rmSync, readFileSync, writeFileSync,
  existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import path from 'node:path';

import { WALK_SHIM } from './changelog_shim.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const REPO = path.resolve(HERE, '..');

let failures = 0;
const check = (what, ok, detail) => {
  console.log(`  ${ok ? 'ok  ' : 'FAIL'}  ${what}${detail ? ` — ${detail}` : ''}`);
  if (!ok) failures += 1;
};

/* ------------------------------------------------------------------ sandbox */

const tmp = mkdtempSync(path.join(tmpdir(), 'c4d-changelog-mirror-'));
const APP = path.join(tmp, 'chicago', '4d');
const SITE = path.join(tmp, 'site', 'chicago', '4d');
mkdirSync(path.join(APP, 'tools'), { recursive: true });
mkdirSync(path.join(APP, 'renderers', 'web', 'js'), { recursive: true });
mkdirSync(path.join(SITE, 'js'), { recursive: true });
mkdirSync(path.join(SITE, 'walk', 'js'), { recursive: true });
for (const f of ['stamp-changelog.mjs', 'changelog_shim.mjs', 'check_published.mjs', 'publish.sh']) {
  cpSync(path.join(REPO, 'tools', f), path.join(APP, 'tools', f));
}

const SRC = path.join(APP, 'renderers', 'web', 'js', 'changelog.js');
const CONTRACT = path.join(SITE, 'js', 'changelog.js');
const INSIDE_WALK = path.join(SITE, 'walk', 'js', 'changelog.js');

/**
 * A two-entry changelog in the fleet shape, with an unstamped entry on top —
 * exactly what an author writes and what the stamper is for. Small on purpose:
 * this test is about the mirrors, not about the literal.
 */
const fresh = () => `export const CHANGELOG = [ // newest first
  { v: null, title: 'A new thing', kind: 'chore', ts: '', date: '',
    items: [
      'Something happened.',
    ] },
  { v: 1, title: 'The first thing', kind: 'feature', ts: '2026-01-01T00:00:00.000Z', date: 'Dec 31, 2025, 6:00 PM CT',
    items: [
      'It began.',
    ] },
];
`;

const RUN = { cwd: APP, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] };
const said = (e) => `${e.stdout ?? ''}${e.stderr ?? ''}`;
const stamp = () => execFileSync('node', [path.join(APP, 'tools', 'stamp-changelog.mjs')], RUN);
/** The gate, as a boolean plus what it said. */
const published = () => {
  try {
    return { ok: true, out: execFileSync('node',
      [path.join(APP, 'tools', 'check_published.mjs')], RUN) };
  } catch (e) {
    return { ok: false, out: said(e) };
  }
};
/**
 * The sandbox's stand-in for publish.sh, and it installs what publish.sh
 * installs: the file at the fleet path, the SHIM inside walk/ (T-0722). Writing
 * the file to both here would make this test pass on a state publish.sh can no
 * longer produce — the shape of green that is worse than red.
 */
const publish = () => {
  writeFileSync(CONTRACT, readFileSync(SRC));
  writeFileSync(INSIDE_WALK, WALK_SHIM);
};

try {
  console.log(`changelog mirror — sandbox at ${tmp}`);

  // A published tree: the changelog authored, then copied the way publish.sh
  // copies it. This is the state a run is in when it reaches the stamp step.
  writeFileSync(SRC, fresh());
  publish();
  check('a freshly published sandbox passes the mirror gate', published().ok);

  /* --- half one: stamping after publish.sh ends green -------------------- */
  //
  // The order that has no documented remedy: publish, then stamp. No second
  // publish, because a run following the documented steps does not do one.
  const out = stamp();
  const afterStamp = published();
  check('stamping after publish.sh leaves both published mirrors fresh', afterStamp.ok,
    afterStamp.ok ? 'no remembered publish.sh needed'
      : afterStamp.out.trim().split('\n').filter(Boolean).pop());
  check('…and the stamper said which paths it carried', /mirrored to .*T-0155/.test(out),
    out.trim().split('\n').filter((l) => l.includes('mirrored')).join('; ') || 'it said nothing');
  const stampedSrc = readFileSync(SRC, 'utf8');
  check('…and the contract mirror really is the stamped file, not the unstamped one',
    readFileSync(CONTRACT, 'utf8') === stampedSrc
      && /ts: '20\d\d-/.test(stampedSrc) && /v: 2\b/.test(stampedSrc),
    `${stampedSrc.length} bytes, v2 stamped`);

  /* --- T-0722: the walk copy is a re-export, and stays one -------------- */
  //
  // The duplicate this replaced was worth 4.1 % of the site budget and nobody saw
  // it, because both copies were correct and neither was checked against the
  // other. So assert the SHAPE, not just the freshness: the walk copy must be the
  // shim, must be small, and must name the path it re-exports — a shim pointing
  // at nothing is a blank What's-new tab that only the published tree can show.
  const inWalk = readFileSync(INSIDE_WALK, 'utf8');
  check('the walk copy is the shim, not a second copy of the changelog',
    inWalk === WALK_SHIM && inWalk.length < 2048 && inWalk !== stampedSrc,
    `${inWalk.length} bytes against the changelog's ${stampedSrc.length}`);
  check('…and it re-exports the fleet path, with the names What\'s-new imports',
    /from '\.\.\/\.\.\/js\/changelog\.js'/.test(inWalk)
      && /CHANGELOG/.test(inWalk) && /LATEST_VERSION/.test(inWalk),
    inWalk.trim().split('\n').pop());

  /* --- half two: the gate is not weaker ---------------------------------- */
  //
  // This is the half the acceptance clause insists on. A mirror somebody else
  // made stale — a hand edit, a bad merge, a publish that half-ran — must still
  // fail, and running the stamper over it must NOT quietly repair it.
  writeFileSync(CONTRACT, `${readFileSync(CONTRACT, 'utf8')}\n// hand-edited\n`);
  const dirtied = published();
  check('a hand-staled mirror still fails the gate', !dirtied.ok,
    dirtied.out.includes('js/changelog.js DIFFERS') ? 'and it names changelog.js'
      : 'WITHOUT naming it');

  stamp();   // a re-stamp with no empty ts left: dates refreshed, bytes unchanged
  const afterNoop = published();
  check('a no-op re-stamp does NOT launder that stale mirror', !afterNoop.ok,
    afterNoop.ok ? 'the mirror was silently repaired — the gate has been weakened'
      : 'still red');

  publish();
  check('and republishing clears it again', published().ok);

  /* --- an unpublished checkout stays unpublished ------------------------- */
  //
  // The stamper must never CREATE a mirror. A checkout that has not published is
  // a checkout whose site tree publish.sh has not decided the shape of yet, and
  // a stamper that guesses at it would put a file where nothing checks it.
  rmSync(path.join(SITE, 'walk'), { recursive: true, force: true });
  writeFileSync(SRC, fresh());        // an unstamped entry again, so the stamper writes
  stamp();
  check('the stamper does not create a mirror directory that publish.sh has not made',
    !existsSync(path.join(SITE, 'walk')), 'walk/ stayed absent');
  check('…while the mirror that DOES exist was still carried',
    readFileSync(CONTRACT, 'utf8') === readFileSync(SRC, 'utf8'));

  /* --- the pin: two copies of one fact cannot drift ---------------------- */
  //
  // stamp-changelog.mjs hard-codes where publish.sh puts this file, twice. This
  // pins both copy lines so the pair cannot drift into mirroring different paths
  // in silence — the same reconciliation `ticket.mjs check` makes for tickets.json,
  // asserted here because the stamper has no `check` verb of its own to hang it on.
  //
  // The pins are read out of the stamper's SOURCE rather than imported from it:
  // importing an .mjs script runs it, and this one has a job. Parsing the array
  // literal still pins the real constant, which a second hand-kept copy would not.
  const stamperSrc = readFileSync(path.join(REPO, 'tools', 'stamp-changelog.mjs'), 'utf8');
  const block = stamperSrc.match(/export const PUBLISH_PINS = \[([\s\S]*?)\];/);
  check('stamp-changelog.mjs still declares PUBLISH_PINS', Boolean(block));
  const pins = [...(block?.[1] ?? '').matchAll(/'([^']*)'/g)].map((m) => m[1]);
  check('…and it names every published copy and the call that writes the shim',
    pins.length === 3, pins.join(' | '));
  const pubSh = readFileSync(path.join(REPO, 'tools', 'publish.sh'), 'utf8');
  for (const pin of pins) {
    check(`publish.sh still contains ${JSON.stringify(pin)}`, pubSh.includes(pin),
      pubSh.includes(pin) ? 'pinned'
        : 'the copy moved and the stamper still mirrors the old path — reconcile them');
  }
} finally {
  if (existsSync(tmp)) rmSync(tmp, { recursive: true, force: true });
}

console.log(failures ? `changelog mirror FAILED — ${failures} assertion(s)`
  : 'changelog mirror OK');
process.exit(failures ? 1 : 0);

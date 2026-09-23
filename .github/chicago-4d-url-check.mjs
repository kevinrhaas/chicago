// chicago-4d-url-check.mjs — T-0968: a green deploy is not proof the site is reachable.
//
//   node .github/chicago-4d-url-check.mjs --origin <base URL> [--window 240] [--interval 15]
//   node .github/chicago-4d-url-check.mjs --self-test
//
// After actions/deploy-pages succeeds, this requests the LIVE origin for every URL in
// chicago-4d-url-check.json and records what it actually returns. On 2026-09-07
// /chicago/4d/dev/ served a 404 for hours while every deploy reported success — the
// only detector was the owner opening the page. This is the detector.
//
// LOUD, NOT BLOCKING — the shape is the point, and the reasoning is stated where the
// next person will look for a "fix":
//
//   * A hard gate on a deploy step once froze this site for ~21 hours
//     (chicago/4d/CLAUDE.md). #1030 made a 4D publish step fatal; #1031 reverted it.
//     A URL smoke that can freeze the monorepo's deploy is a worse bug than the one it
//     detects. So a failed check emits a `::error::` annotation and THIS PROCESS ALWAYS
//     EXITS 0 in normal mode. deploy.yml wraps the call in `|| echo "::warning::…"` as
//     well, so even a crash of this script cannot take the deploy down.
//   * Pages serves the new artifact some seconds after the API reports success, so a
//     URL that fails right after deploy may be propagation, not a hole. Each URL is
//     retried over a bounded window (default 240 s, every 15 s) before it is reported.
//     A check that cries wolf on every deploy will be ignored, which is worse than none.
//   * Status alone is not proof: a Pages 404 returns 404, but a stale or empty preview
//     can return 200 with nothing in it. Every entry asserts a BODY signal — the gate's
//     build stamp for a tier, the preview's own PREVIEW marking for the dev tier — not
//     just a status code.
//
// The URL list is DATA (chicago-4d-url-check.json): a new tenant is one line, no code.
// The origin comes from steps.deployment.outputs.page_url in deploy.yml, so the CNAME
// never hardcodes in this repo.
//
// --self-test answers the acceptance clause "an unproven detector is not a detector":
// it stands up a fixture origin on 127.0.0.1 with one good page and one URL that is
// known to 404, runs THIS code against it, and fails (exit 1) unless the good page
// passed AND the 404 produced a `::error::` annotation naming the URL and the status.
// It touches no external network, so tools/check.sh runs it on every gate.

import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const LIST = join(HERE, 'chicago-4d-url-check.json');

// GitHub workflow-command escaping: %, \r and \n are metacharacters in annotations.
const esc = (s) => String(s).replace(/%/g, '%25').replace(/\r/g, '%0D').replace(/\n/g, '%0A');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function parseArgs(argv) {
  const a = { origin: '', windowSec: 240, intervalSec: 15, selfTest: false, list: LIST };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--origin') a.origin = argv[++i];
    else if (argv[i] === '--window') a.windowSec = Number(argv[++i]);
    else if (argv[i] === '--interval') a.intervalSec = Number(argv[++i]);
    else if (argv[i] === '--list') a.list = argv[++i];
    else if (argv[i] === '--self-test') a.selfTest = true;
    else { console.error(`unknown argument: ${argv[i]}`); process.exit(2); }
  }
  return a;
}

/** One URL against the live origin: retry inside the bounded propagation window. */
async function checkOne(origin, entry, windowSec, intervalSec) {
  const url = origin.replace(/\/$/, '') + entry.path;
  const deadline = Date.now() + windowSec * 1000;
  let last = { status: 0, bytes: 0, missing: '' };
  let attempts = 0;
  while (true) {
    attempts++;
    try {
      const res = await fetch(url, { redirect: 'follow' });
      const body = await res.text();
      last = { status: res.status, bytes: body.length, missing: '' };
      if (res.status === 200 && body.includes(entry.must_contain)) {
        return { ok: true, attempts, ...last };
      }
      last.missing = entry.must_contain;
    } catch (e) {
      last = { status: 0, bytes: 0, missing: `${entry.must_contain} (fetch: ${e.message})` };
    }
    if (Date.now() >= deadline) return { ok: false, attempts, ...last };
    await sleep(intervalSec * 1000);
  }
}

/** Run the list; return {passed, failed, annotations}. annotations is the loud part. */
async function runChecks(origin, entries, { windowSec, intervalSec }) {
  const annotations = [];
  let passed = 0;
  const results = [];
  for (const entry of entries) {
    const r = await checkOne(origin, entry, windowSec, intervalSec);
    results.push({ path: entry.path, ...r });
    if (r.ok) {
      passed++;
      console.log(`PASS  ${entry.path}  200  ${r.bytes} bytes  (${r.attempts} attempt${r.attempts === 1 ? '' : 's'})`);
    } else {
      const status = r.status === 0 ? 'no response' : `HTTP ${r.status}`;
      const msg = `T-0968 URL check: ${entry.path} returned ${status} after ${r.attempts} attempt(s) over ${windowSec}s — expected 200 and a body containing '${r.missing}'`;
      console.log(`FAIL  ${msg}`);
      annotations.push(`::error::${esc(msg)}`);
    }
  }
  for (const a of annotations) console.log(a);
  return { passed, failed: entries.length - passed, annotations, results };
}

/** The acceptance proof: point the same code at a fixture origin with a known 404. */
async function selfTest() {
  const fixture = [
    { path: '/ok', must_contain: '<title>fixture tenant</title>' },
    { path: '/missing-on-purpose', must_contain: 'a body signal nothing serves' },
  ];
  const server = createServer((req, res) => {
    if (req.url === '/ok') {
      res.writeHead(200, { 'content-type': 'text/html' });
      res.end('<!doctype html><title>fixture tenant</title><p>fixture ok</p>');
    } else {
      res.writeHead(404, { 'content-type': 'text/html' });
      res.end('<h1>404 — fixture says nothing here</h1>');
    }
  });
  await new Promise((r) => server.listen(0, '127.0.0.1', r));
  const origin = `http://127.0.0.1:${server.address().port}`;
  try {
    const { passed, failed, annotations, results } = await runChecks(origin, fixture,
      { windowSec: 3, intervalSec: 1 });
    const good = results.find((r) => r.path === '/ok');
    const bad = results.find((r) => r.path === '/missing-on-purpose');
    const fired = annotations.length === 1
      && annotations[0].includes('/missing-on-purpose')
      && annotations[0].includes('404');
    console.log('--- self-test fired annotation:');
    console.log(annotations[0] || '(none — THE DETECTOR DID NOT FIRE)');
    if (passed === 1 && failed === 1 && good?.ok && !bad?.ok && fired) {
      console.log('SELF-TEST PASS — the check passes a good page and fires ::error:: on a known 404.');
      return 0;
    }
    console.error('SELF-TEST FAIL — the detector did not fire as required (T-0968 acceptance 5).');
    return 1;
  } finally {
    server.close();
  }
}

async function main() {
  const a = parseArgs(process.argv.slice(2));
  if (a.selfTest) process.exit(await selfTest());

  if (!a.origin) {
    console.error('usage: node chicago-4d-url-check.mjs --origin <base URL> [--window s] [--interval s]');
    process.exit(2);
  }
  const list = JSON.parse(await readFile(a.list, 'utf8'));
  const entries = list.urls;
  if (!Array.isArray(entries) || entries.length === 0) {
    console.error(`${a.list}: no urls[] — the list is the detector's contract`);
    process.exit(2);
  }
  console.log(`T-0968 URL smoke against ${a.origin} — ${entries.length} URL(s), ` +
    `${a.windowSec}s propagation window, non-blocking by design.`);
  const { passed, failed } = await runChecks(a.origin, entries,
    { windowSec: a.windowSec, intervalSec: a.intervalSec });
  console.log(`URL smoke: ${passed} passed, ${failed} failed — ` +
    (failed ? 'annotations above; ' : '') +
    'the deploy itself is NOT failed by this step (a hard gate once froze the site ~21h).');
  process.exit(0); // loud, not blocking — always.
}

main().catch((e) => {
  console.error(`chicago-4d-url-check crashed: ${e.message}`);
  process.exit(2); // deploy.yml's `|| echo "::warning::…"` keeps even this from gating.
});

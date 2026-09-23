#!/usr/bin/env node
// test_dev_preview.mjs — exercise the dev-preview assembler end to end.
//
//   node tools/test_dev_preview.mjs
//
// `.github/chicago-4d-dev-preview.mjs` is the only thing standing between the
// integration preview and being mistaken for production: it is what adds the
// noindex, the banner, and the build stamp. It had no test, which is how the
// stamp went for a while saying only `dev@<sha>` — true, but not enough to
// answer "how old is what I am looking at", the question the production gate
// answers with a date.
//
// The fixture is SYNTHETIC, deliberately. Running against the published
// `site/` mirror would couple this test to whatever the walk gate's markup
// happens to be today, and then it would fail for reasons that have nothing to
// do with the assembler. What it asserts is the CONTRACT: given a tree with a
// gate element in it, what comes out the other side.
import { mkdtemp, mkdir, writeFile, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const REPO = resolve(fileURLToPath(new URL('../../..', import.meta.url)));
const SCRIPT = join(REPO, '.github', 'chicago-4d-dev-preview.mjs');
const APP = 'site/chicago/4d';

let failed = 0;
const ok = (label, cond, detail = '') => {
  if (cond) { console.log(`   ok   ${label}`); return; }
  failed = 1;
  console.log(`   FAIL ${label}${detail ? `\n        ${detail}` : ''}`);
};

const GATE = '<p class="gate-build" id="gate-build" hidden><!--BUILD_STAMP--></p>';
const FIXTURE = `<!doctype html><html><head><title>t</title></head>
<body><div class="gate">${GATE}</div></body></html>`;

/** Assemble a preview in a throwaway tree and hand back what it produced. */
async function assemble(...args) {
  const root = await mkdtemp(join(tmpdir(), 'devprev-'));
  await mkdir(join(root, 'src', APP, 'walk'), { recursive: true });
  await mkdir(join(root, 'run', 'site'), { recursive: true });
  await writeFile(join(root, 'src', APP, 'walk', 'index.html'), FIXTURE);
  execFileSync(process.execPath, [SCRIPT, join(root, 'src'), ...args],
    { cwd: join(root, 'run'), stdio: 'pipe' });
  const out = join(root, 'run', APP, 'dev');
  const html = await readFile(join(out, 'walk', 'index.html'), 'utf8');
  const build = JSON.parse(await readFile(join(out, 'build.json'), 'utf8'));
  const robots = await readFile(join(root, 'run', 'site', 'robots.txt'), 'utf8');
  await rm(root, { recursive: true, force: true });
  return { html, build, robots, stamp: html.match(/<p class="gate-build"[^>]*>(.*?)<\/p>/s)?.[1] ?? '' };
}

console.log('== dev preview: a stamped, unindexed, clearly-marked copy');

// A fixed instant so the assertion can name the exact string. 04:59 UTC-05:00
// is Central summer time, which is what the project quotes everything in.
const ISO = '2026-08-14T04:59:12-05:00';
const full = await assemble('0ccf24b', ISO);

ok('the gate says which tier it is', /\bDEV PREVIEW\b/.test(full.stamp), full.stamp);
ok('the gate names the dev commit', full.stamp.includes('dev@0ccf24b'), full.stamp);
ok('the gate dates the build in Central Time',
  full.stamp.includes('Aug 14, 2026, 4:59 AM CT'), full.stamp);

// Production stamps with the shell's `date`, which emits a plain space before
// AM/PM; Intl emits U+202F on current ICU. Two gates side by side in a
// screenshot must not differ by an invisible character.
ok('no narrow or non-breaking spaces in the stamp',
  !/[  ]/.test(full.stamp),
  JSON.stringify(full.stamp));

ok('the preview is kept out of the index',
  /<meta name="robots" content="noindex,nofollow">/.test(full.html));
ok('the preview carries its banner', full.html.includes('id="__dev"'));
ok('robots.txt disallows the preview path',
  full.robots.includes('Disallow: /chicago/4d/dev/'), full.robots.trim());

ok('build.json marks the tier', full.build.tier === 'dev');
ok('build.json carries the commit date, machine-readable',
  full.build.committedAt === ISO, String(full.build.committedAt));
ok('build.json carries the same date the gate shows',
  full.build.committedCT === 'Aug 14, 2026, 4:59 AM CT', String(full.build.committedCT));
// An assembly time would age the stamp on deploys of main that never touched
// dev. If one is ever added, this test should be the thing that argues with it.
ok('build.json does NOT claim an assembly time',
  !('assembledAt' in full.build));

// Degradation: the date is optional, and a missing one must not leave a
// dangling separator on the gate.
const bare = await assemble('0ccf24b');
ok('a missing date degrades to just the tier and sha',
  bare.stamp === 'DEV PREVIEW · dev@0ccf24b', JSON.stringify(bare.stamp));
ok('a missing date nulls out in build.json',
  bare.build.committedAt === null && bare.build.committedCT === null);

// An unparseable date is the same case as no date — never the string "Invalid
// Date" on the gate, which is the failure mode a naive `new Date(x)` gives.
const junk = await assemble('0ccf24b', 'not-a-date');
ok('an unparseable date degrades rather than printing "Invalid Date"',
  junk.stamp === 'DEV PREVIEW · dev@0ccf24b', JSON.stringify(junk.stamp));

console.log(failed ? '   dev preview: FAILED' : '   dev preview: all checks passed');
process.exit(failed);

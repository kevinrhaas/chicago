#!/usr/bin/env node
/**
 * Does the site ship what the repository says it ships?
 *
 * WHY THIS EXISTS. R-BUG3c-b (#145) cost three parcels on one owner report, and
 * the sentence it ended on was: *do not measure the file you built, measure the
 * file you ship*. `generators/terrain_gen.py` refuses to export a ground more
 * than 30 mm from the heightfield and holds its master to 2.5 mm — and the file
 * a browser loaded was 85 mm rms out, because a `gltf-transform optimize` step
 * quantised POSITION to 14 bits AFTERWARDS. Every gate in the project passed,
 * because every gate compared a render to another render, and a quantised
 * ground looks perfectly correct.
 *
 * That fault is fixed. THIS is the generalisation #145 explicitly left open:
 * "Nothing else in this project measures a published artefact against its own
 * source, and nobody has looked for the next instance of it."
 *
 * WHAT IT ASSERTS, and why the assertion is this shape. `tools/publish.sh` is
 * almost entirely `cp` — the mirror is meant to be the repository, rearranged.
 * So the invariant is simple and total: **every published file is byte-identical
 * to its source, unless it is on the declared list below.** A transform that
 * appears where a copy was assumed is exactly the class of fault that hid the
 * terrain quantiser, and it now fails here rather than in a screenshot.
 *
 * The declared list is deliberately awkward to add to. Each entry has to say
 * WHAT transforms the bytes and WHY that is legitimate, and each is a standing
 * invitation to ask whether the gate downstream of it measures the shipped form
 * or the source form. That question is what nobody asked about the terrain.
 */
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const REPO = path.resolve(HERE, '..');
const SITE = path.resolve(REPO, '../../site/chicago/4d');

/**
 * Published path prefix -> where its source lives. Mirrors publish.sh's own
 * `cp` calls; if publish.sh grows a new copy, this needs the matching row and
 * the unmapped-file check below will say so.
 */
const COPIES = [
  ['walk/', 'renderers/web/'],
  ['js/changelog.js', 'renderers/web/js/changelog.js'],
  ['tickets.json', 'tickets/tickets.json'],
  ['data/scenes/', 'data/scenes/'],
  ['data/datum.json', 'data/datum.json'],
  ['data/liberties.json', 'data/liberties.json'],
  ['data/town_census.json', 'data/town_census.json'],
  ['data/reconstruction/1835_hay_limits.json', 'data/reconstruction/1835_hay_limits.json'],
  ['data/reconstruction/1835_agencies.json', 'data/reconstruction/1835_agencies.json'],
  ['data/reconstruction/1835_population_profile.json', 'data/reconstruction/1835_population_profile.json'],
  ['data/terrain/', 'data/terrain/'],
  ['data/sidecars/', 'data/sidecars/'],
  ['data/residents/', 'data/residents/'],
  ['data/enclosures/', 'data/enclosures/'],
  ['data/signage/', 'data/signage/'],
  ['data/yard/', 'data/yard/'],
  ['data/wharves/', 'data/wharves/'],
  ['data/boats/', 'data/boats/'],
  ['data/wells/', 'data/wells/'],
  ['data/frontage/', 'data/frontage/'],
  ['data/flora/', 'data/flora/'],
  ['data/fauna/', 'data/fauna/'],
];

/**
 * The transforms, each with the reason it is allowed to differ. A file matching
 * one of these is REPORTED, never silently skipped: the report is the point,
 * because it is the list of places where what ships is not what was checked.
 */
const TRANSFORMED = [
  { re: /^index\.html$/,
    what: 'publish.sh writes the mirror landing page once, if absent (`[ -f ] ||`), from a heredoc',
    gate: 'none, and it does not need one: it is a redirect stub with no claim in it. Recorded so '
        + 'that if it ever grows a claim, the absence of a gate is visible here.' },
  { re: /^build\.json$/,
    what: 'publish.sh writes it each run from the same BUILD_VERSION and BUILD_CT as the visible stamp',
    gate: 'tools/test_dev_preview.mjs reads it. Until 2026-08-15 it was written ONCE by hand and never '
        + 'again — this gate found it two days stale, claiming a version the mirror beside it did not '
        + 'have. That is the exact fault class this file exists for, found on its first run.' },
  { re: /^walk\/js\/changelog\.js$/,
    what: 'a nine-line re-export of js/changelog.js, written by tools/stamp-changelog.mjs (which '
        + 'owns the shim text) and installed by publish.sh\'s `--write-mirrors` call',
    gate: 'T-0722. Both published paths carried the changelog verbatim until 2026-09-05, so the site '
        + 'shipped the same 1.31 MB twice — 4.1 % of its 32 MB budget on a byte-for-byte copy, growing '
        + 'at double the rate of the record, which is what put dev at 31.999 MB with no room for any '
        + 'PR to add a changelog entry. The shipped form is gated three ways: tools/validate.py refuses '
        + 'any two published files over 64 KB with identical bytes (so the duplicate cannot return the '
        + 'way it arrived); tools/test_changelog_mirror.mjs asserts the shim is what lands here and '
        + 'that it names the file it re-exports; and the smoke\'s What\'s-new leg loads the tab out of '
        + 'the published tree, which is the shim resolving or not.' },
  { re: /^walk\/index\.html$/,
    what: 'publish.sh stamps the build commit and its Central-time date into the gate overlay',
    gate: 'tools/test_dev_preview.mjs asserts the stamp on the PUBLISHED form' },
  { re: /^data\/residents\/.*\.json$/,
    what: 'publish.sh writes the residents layer minified — the same JSON value on one line',
    gate: 'tools/check_published_residents.mjs asserts the SHIPPED file parses to a value '
        + 'deep-equal to its source, file for file, with none missing and none extra. The '
        + 'transform exists because the layer is 1,380 hand-annotated household records whose '
        + 'notes run to paragraphs: at indent=1 it was 8.8 MB of the 32 MB budget, the tree '
        + 'measured 31.999 MB on 2026-09-05, and the next resident pass could not land. '
        + 'Whitespace is the one thing in it a visitor never reads — the renderer fetches '
        + 'these with response.json().' },
  { re: /^data\/gltf\/.*\.glb$/,
    what: 'gltf-transform meshopt derivative built by bake.sh from assets/gltf masters',
    gate: 'R-BUG3c-b: check.sh asserts the committed master against the heightfield and REPORTS the '
        + 'derivative\'s FIT; the renderer conforms the ground to the field at load, so the drawn '
        + 'surface is the sampler by construction. Its POSITION BIT DEPTH is asserted rather than '
        + 'reported (T-0012): tools/measure_terrain_fit.mjs --gate recovers the depth from the shipped '
        + 'rungs and fails if it is coarser than tools/web_derivatives.sh asks for, because the '
        + 'derivative gate next door compares triangles, node identity, materials and a bounding box '
        + 'within four rungs and a bit-depth change moves none of them. This is the entry that cost '
        + 'three parcels — read #145 before adding another.' },
];

const walk = (dir, base = '') => {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const e of readdirSync(dir)) {
    const abs = path.join(dir, e);
    const rel = base ? `${base}/${e}` : e;
    if (statSync(abs).isDirectory()) out.push(...walk(abs, rel));
    else out.push(rel);
  }
  return out;
};
const sha = (p) => createHash('sha1').update(readFileSync(p)).digest('hex');

const problems = [];
const transformed = [];
let identical = 0;
const unmapped = [];

for (const rel of walk(SITE)) {
  const t = TRANSFORMED.find((x) => x.re.test(rel));
  if (t) { transformed.push({ rel, ...t }); continue; }

  const row = COPIES.find(([pfx]) => rel === pfx || rel.startsWith(pfx));
  if (!row) { unmapped.push(rel); continue; }
  const [pfx, srcPfx] = row;
  const src = path.resolve(REPO, rel === pfx ? srcPfx : srcPfx + rel.slice(pfx.length));
  if (!existsSync(src)) {
    problems.push(`${rel} is published but ${path.relative(REPO, src)} does not exist — `
      + 'the mirror carries a file the repository does not');
    continue;
  }
  if (sha(src) === sha(path.join(SITE, rel))) { identical++; continue; }
  problems.push(`${rel} DIFFERS from its source ${path.relative(REPO, src)}. publish.sh copies this `
    + 'path verbatim, so either something transforms it — in which case it belongs in TRANSFORMED '
    + 'with the gate that measures its SHIPPED form named — or the mirror is stale and publish.sh '
    + 'was not re-run. This is the shape of the fault that hid the terrain quantiser for three '
    + 'parcels (#145).');
}

// Grouped by RULE, not per file: 294 identical paragraphs is noise, and noise is
// how a gate stops being read. What matters is the set of transforms and their
// count, so a new one is visible at a glance.
const byRule = new Map();
for (const t of transformed) {
  const k = t.what;
  if (!byRule.has(k)) byRule.set(k, { gate: t.gate, files: [] });
  byRule.get(k).files.push(t.rel);
}
console.log(`published mirror: ${identical} file(s) byte-identical to source, `
  + `${transformed.length} transformed under ${byRule.size} declared rule(s), `
  + `${unmapped.length} unmapped`);
for (const [what, v] of byRule) {
  console.log(`  ${v.files.length}x transformed — ${what}`);
  console.log(`      e.g. ${v.files[0]}`);
  console.log(`      gate: ${v.gate}`);
}
// Unmapped is NOT a pass. A published file this gate cannot trace to a source is
// a file nobody is checking, which is the whole failure mode being closed here.
if (unmapped.length) {
  problems.push(`${unmapped.length} published file(s) trace to no source and no declared transform, `
    + `so nothing checks what ships in them: ${unmapped.slice(0, 8).join(', ')}`
    + `${unmapped.length > 8 ? ` (+${unmapped.length - 8} more)` : ''}. Add the publish.sh copy rule `
    + 'to COPIES, or declare the transform and name the gate that measures its shipped form.');
}
if (problems.length) {
  console.error('published mirror FAILED:');
  for (const p of problems) console.error('  - ' + p);
  process.exit(1);
}

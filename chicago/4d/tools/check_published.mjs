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
const SITE = path.resolve(REPO, '../../site/4d');

/**
 * Published path prefix -> where its source lives. Mirrors publish.sh's own
 * `cp` calls; if publish.sh grows a new copy, this needs the matching row and
 * the unmapped-file check below will say so.
 */
const COPIES = [
  // The owner-requested atlas browser is copied verbatim into the dev preview.
  ['prairie-1904/', '../prairie_1904_v1/'],
  ['pre-fire/', '../pre_fire_v1/'],
  ['walk/', 'renderers/web/'],
  ['js/changelog.js', 'renderers/web/js/changelog.js'],
  ['tickets.json', 'tickets/tickets.json'],
  ['data/scenes/', 'data/scenes/'],
  ['data/datum.json', 'data/datum.json'],
  // T-2741: today's streets, for the compass readout and the maps in every year.
  ['data/modern/', 'data/modern/'],
  ['data/comparisons/glessner/', 'data/comparisons/glessner/'],
  ['data/liberties.json', 'data/liberties.json'],
  // Written into the tree by tools/compile_pictures.py just before the copy (T-2389).
  ['data/pictures/', 'data/pictures/'],
  // Written into the tree by tools/compile_reader_text.py just before the copy (T-2825):
  // the reader's overlay, derived and ignored like data/pictures/, copied byte for byte (T-2924).
  ['data/reader/', 'data/reader/'],
  // Written into the tree by tools/compile_summaries.py just before the copy (T-2635).
  ['data/inspect/', 'data/inspect/'],
  ['data/town_census.json', 'data/town_census.json'],
  ['data/render/town_completion_1835.json', 'data/render/town_completion_1835.json'],
  ['data/reconstruction/1835_hay_limits.json', 'data/reconstruction/1835_hay_limits.json'],
  ['data/reconstruction/1835_agencies.json', 'data/reconstruction/1835_agencies.json'],
  ['data/reconstruction/1835_population_profile.json', 'data/reconstruction/1835_population_profile.json'],
  ['data/reconstruction/1835_reconstruction_order_book.json', 'data/reconstruction/1835_reconstruction_order_book.json'],
  ['data/reconstruction/1835_address_book.json', 'data/reconstruction/1835_address_book.json'],
  ['data/terrain/', 'data/terrain/'],
  ['data/sidecars/', 'data/sidecars/'],
  ['data/loading/statuses.json', 'data/loading/statuses.json'],
  // The arrival's time-stream decks (T-2611); js/time-stream.js fetches them on arrival.
  ['data/timestream/', 'data/timestream/'],
  // The Guide's glossary and questions (T-2662), copied verbatim; tools/check_guide.py gates
  // the source, and the Guide reads faq.json the first time it opens.
  ['data/guide/', 'data/guide/'],
  ['data/residents/', 'data/residents/'],
  ['data/enclosures/', 'data/enclosures/'],
  ['data/signage/', 'data/signage/'],
  ['data/yard/', 'data/yard/'],
  ['data/transport/parked/', 'data/transport/parked/'],
  ['data/wharves/', 'data/wharves/'],
  ['data/boats/', 'data/boats/'],
  ['data/wells/', 'data/wells/'],
  ['data/street_grid/', 'data/street_grid/'],
  ['data/context/', 'data/context/'],
  ['data/street_surfaces/', 'data/street_surfaces/'],
  ['data/street_section/', 'data/street_section/'],
  ['data/street_trees/', 'data/street_trees/'],
  ['data/street_furniture/', 'data/street_furniture/'],
  ['data/railway/', 'data/railway/'],
  ['data/frontage/', 'data/frontage/'],
  ['data/flora/', 'data/flora/'],
  ['data/humans/web/', 'assets/humans/web/'],
  ['data/humans/', 'data/humans/'],
  ['data/fauna/', 'data/fauna/'],
  ['data/businesses/', 'data/businesses/'],
  // The two roof coverings' relief maps (T-1488). The mirror's asset base is
  // data/ where the dev tree's is assets/, which is the whole of the rename;
  // the files themselves are the vendored library's, byte for byte, so this
  // is a verbatim copy under a different prefix and belongs here rather than
  // in TRANSFORMED.
  ['data/textures/', 'assets/textures/'],
];

/**
 * The transforms, each with the reason it is allowed to differ. A file matching
 * one of these is REPORTED, never silently skipped: the report is the point,
 * because it is the list of places where what ships is not what was checked.
 */
/**
 * The sidecars that seat a household, read from the SOURCE so the transform below
 * covers exactly them and every other sidecar is still compared byte for byte.
 */
const SEATED = new Set();
for (const scene of existsSync(path.join(REPO, 'data/sidecars')) ? readdirSync(path.join(REPO, 'data/sidecars')) : []) {
  const dir = path.join(REPO, 'data/sidecars', scene);
  if (!statSync(dir).isDirectory()) continue;
  for (const f of readdirSync(dir)) {
    if (!f.endsWith('.json') || !statSync(path.join(dir, f)).isFile()) continue;
    const rec = JSON.parse(readFileSync(path.join(dir, f), 'utf8'));
    if (Array.isArray(rec?.residents) && rec.residents.length) SEATED.add(`data/sidecars/${scene}/${f}`);
  }
}

const TRANSFORMED = [
  { re: /^(?:\d{4}\/)?index\.html$/,
    what: 'the front doors — /4d/ and /4d/<year>/ on chicago.polecat.live. tools/write_entry_pages.mjs '
        + 'copies the temporal observatory to the root and writes year doors as the stamped renderer plus a base into walk/, so the address '
        + 'bar keeps the short path and every relative URL resolves from walk/',
    gate: 'write_entry_pages.mjs --self-test (check.sh) asserts the <base> is the first child of '
        + '<head>, exact root-template copying, working year doors and the honest 1812 status; the deploy URL smoke '
        + '(.github/chicago-4d-url-check.json) requests /4d/, /4d/1835/ and /4d/dev/1835/ live.' },
  { re: /^(?:prairie-1904|pre-fire)\/viewer\/root-served\.js$/,
    what: 'tools/serve_from_root.py (T-1828) names the asset directories it removed from the mirror because '
        + 'the site root ships them byte for byte, and the viewer reads those from /<app>/ instead',
    gate: 'serve_from_root.py --self-test (check.sh) proves a directory leaves only when every file in it is '
        + 'identical at the root; tools/check_published.mjs still compares every file that does ship' },
  { re: /^(?:sw\.js|packs\/[^/]+\.json|\d{4}\/app\.webmanifest)$/,
    what: 'tools/write_year_packs.mjs (T-2561) writes the per-year packs a visitor can keep on the device, '
        + 'each year\'s home-screen manifest, and sw.js — offline/sw.js, with its KILL line flipped '
        + 'when offline/sw-off exists',
    gate: 'write_year_packs.mjs --check (check.sh) asserts every file a pack lists ships at the hash and size '
        + 'it lists, each pack holds its own door, the index carries each pack\'s id, and sw.js is its source '
        + '(or the killed form exactly when the switch is thrown); --self-test holds which files go in which '
        + 'year\'s pack and the update diff the page downloads by.' },
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
  { re: /^data\/prebuilt\/(?:index\.json|\d{4}\/(?:(?:frontage|ground|base|yards)\.(?:json|bin\.gz)|streets\.(?:json|(?:light|full)\.bin\.gz)))$/,
    what: 'tools/prebuild_layers.mjs (run by publish.sh) writes the frontage layer\'s finished buffers, built '
        + 'in Node by the page\'s own createFrontage, with a hash of every file they were built from and the '
        + 'build id the page is stamped with, the buffer gzipped for the tree budget; the page inflates and '
        + 'uploads them instead of building them (T-2677); and the ground\'s tiles, cut into the page\'s 40 m '
        + 'pieces by terrain.js\'s and spatial-batch.js\'s own functions, uploaded in the ground GLB\'s place (T-2693); '
        + 'and the distant base, laid over frontage\'s crossing footprints and cut the same way, batched in place of '
        + 'the page\'s own grid and cut (T-2709); and the streets\' surfaces laid by streets.js\'s own '
        + 'streetLayoutOf, one buffer per layout, batched in place of laying the road (T-2710); '
        + 'and the yards\' five surfaces, laid by yards.js\'s own createFencedGround and cut the same way, uploaded '
        + 'in place of laying them (T-2711); and index.json, '
        + 'the list of every year and layer it wrote, which the page reads before asking for any of them '
        + '(js/prebuilt-index.js), so a year with no prebuild costs no 404',
    gate: 'this file refuses a prebuild whose inputs no longer hash to its index, or whose buffer is not the '
        + 'one its index hashed (prebuild_layers.mjs stale(), below); prebuild_layers.mjs --self-test '
        + '(check.sh) proves two builds byte-identical and the page\'s replay of one equal to its own build; '
        + '--parity reads the live page\'s buffers against it.' },
  { re: /^walk\/index\.html$/,
    what: 'publish.sh stamps the build commit and its Central-time date into the gate overlay and the '
        + 'release numbers into the c4d-releases meta, then tools/strip_page_comments.mjs takes the '
        + 'source\'s developer comments out (about 13 KB, shipped once per door; placeholders, conditional '
        + 'comments and every <script>/<style>/<textarea>/<pre> body pass through untouched)',
    gate: 'tools/strip_page_comments.mjs --check (check.sh) asserts the PUBLISHED page is the source with '
        + 'exactly those two transforms and nothing else, byte for byte, and that every year door is it plus '
        + 'its <base>; tools/test_dev_preview.mjs asserts the stamp the dev preview rewrites' },
  { re: /^data\/residents\/letter_list\/[^/]+\.json$/,
    what: 'tools/pack_letter_list.py packs the letter-list cohort into a roster of the strings it '
        + 'repeats and a shard per initial, and takes those households\' own files out (T-0438)',
    gate: 'tools/check_published_residents.mjs unpacks every shipped record with the renderer\'s own '
        + 'unpackRecord and asserts it deep-equal to its source, the cohort exactly the index\'s '
        + 'letter_list_only households and none shipped twice; pack_letter_list.py --self-test '
        + '(check.sh) proves the round trip and refuses a record the packing would make ambiguous. '
        + 'The cohort had reached 9.30 MiB as one file per name, most of it the same paragraphs.' },
  { re: /^data\/residents\/.*\.json$/,
    what: 'publish.sh writes the residents layer minified — the same JSON value on one line',
    gate: 'tools/check_published_residents.mjs asserts the SHIPPED file parses to a value '
        + 'deep-equal to its source, file for file, with none missing and none extra. The '
        + 'transform exists because the layer is 1,380 hand-annotated household records whose '
        + 'notes run to paragraphs: at indent=1 it was 8.8 MB of the 32 MB budget, the tree '
        + 'measured 31.999 MB on 2026-09-05, and the next resident pass could not land. '
        + 'Whitespace is the one thing in it a visitor never reads — the renderer fetches '
        + 'these with response.json().' },
  { re: /^data\/sidecars\/[^/]+\/households\/[^/]+\.json$/,
    what: 'tools/defer_household_notes.mjs (run by publish.sh) writes each seated record\'s households, '
        + 'whole, beside it for the card to fetch when it opens (T-2151)',
    gate: 'defer_household_notes.mjs --check (check.sh) asserts each is its source record\'s `residents`, '
        + 'value for value, with none missing and none extra.' },
  { re: { test: (rel) => SEATED.has(rel) },
    what: 'the same tool ships every sidecar that seats a household with its households SLIM — no `why`, '
        + '`research_note` or person `note` — because those paragraphs were 0.87 MB of a first visit '
        + 'that was 0.65 MB over its 13 MB budget, and only an open card reads them (T-2151)',
    gate: 'defer_household_notes.mjs --check (check.sh) asserts each shipped record deep-equals its '
        + 'source with exactly those fields taken out, and that every source household carries the '
        + '`why` whose absence is how the card knows to fetch the rest.' },
  { re: /^data\/sidecars\/[^/]+\/boot\/[^/]+\.json$/,
    what: 'tools/pack_boot_sidecars.mjs (run by publish.sh) writes each scene\'s records packed against '
        + 'each other — every value three or more repeat shipped once in boot/shared.json — because a '
        + 'citation hundreds of records carry was paid for once per record on a first visit 1.51 MB over '
        + 'its 13 MB budget. scene-loader.js reads these and rehydrates; the records at their own URLs '
        + 'are untouched (T-2315)',
    gate: 'pack_boot_sidecars.mjs --check (check.sh) rehydrates every boot copy with the loader\'s own '
        + 'function and asserts it equals the shipped record key for key, with none missing and none extra.' },
  { re: /^data\/sidecars\/[^/]+\/index\.json$/,
    what: 'the same tool adds `boot: { shared, dir }` to each scene\'s sidecar index, which is how the '
        + 'loader knows the packed copies exist without probing for them (T-2315)',
    gate: 'pack_boot_sidecars.mjs --check (check.sh) asserts the shipped index is its source plus exactly '
        + 'that key.' },
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

// T-2793: omit only declared source masters, never a live vehicle or public
// demo. Partial mirror fixtures have no transport manifest; a complete app
// must carry its policy and retain the authoring originals in the source tree.
const transportPolicyFile = path.join(REPO, 'tools/transport-source-only.json');
const transportManifestFiles = [
  'data/transport/parked/placements.json',
  'data/transport/parked/standing-horses.json',
];
if (!existsSync(transportPolicyFile) && transportManifestFiles.some((f) => existsSync(path.join(REPO, f)))) {
  problems.push('The transport source-only publication policy is missing.');
}
if (existsSync(transportPolicyFile)) {
  const policy = JSON.parse(readFileSync(transportPolicyFile, 'utf8'));
  const files = policy.files;
  if (policy.schema !== 1 || !policy.reason || !Array.isArray(files) || new Set(files).size !== files.length) {
    problems.push('The transport source-only publication policy is invalid.');
  } else {
    const strings = (value) => typeof value === 'string' ? [value]
      : Array.isArray(value) ? value.flatMap(strings)
      : value && typeof value === 'object' ? Object.values(value).flatMap(strings) : [];
    const liveModels = transportManifestFiles.filter((f) => existsSync(path.join(REPO, f)))
      .flatMap((f) => strings(JSON.parse(readFileSync(path.join(REPO, f), 'utf8')).models));
    const rendererSource = path.join(REPO, 'renderers/web');
    const scripts = walk(rendererSource).filter((f) => !f.startsWith('vendor/') && /\.(?:html|m?js)$/.test(f))
      .map((f) => [f, readFileSync(path.join(rendererSource, f), 'utf8')]);
    for (const file of files) {
      if (typeof file !== 'string' || !file.startsWith('transport/') || !file.endsWith('.glb')
          || file.split('/').some((part) => part === '..' || part === '.' || !part)) {
        problems.push(`Invalid transport source-only path: ${file}`);
        continue;
      }
      if (!existsSync(path.join(rendererSource, file))) problems.push(`Authoring source is missing: ${file}`);
      if (existsSync(path.join(SITE, 'walk', file))) problems.push(`Source-only master is still published: walk/${file}`);
      if (liveModels.includes(file)) problems.push(`Source-only master is a live transport model: ${file}`);
      for (const [script, text] of scripts) {
        // Demos in wagon/ and wagon-driver/ each have their OWN wagon-w01.glb.
        // Resolve relative literals; an identical basename is not the same URL.
        const relativeReferences = [...text.matchAll(/(['"`])([^'"`\r\n]*\.glb(?:[?#][^'"`\r\n]*)?)\1/g)]
          .map((match) => match[2].split(/[?#]/)[0])
          .filter((value) => !value.includes('${') && !/^(?:[a-z]+:|\/)/i.test(value))
          .map((value) => path.posix.normalize(path.posix.join(path.posix.dirname(script), value)));
        if (text.includes(file) || relativeReferences.includes(file)) {
          problems.push(`Source-only master is referenced by renderer ${script}: ${file}`);
        }
      }
    }
    console.log(`transport publication: ${files.length} declared source masters retained outside the mirror`);
  }
}

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
// T-2677: a prebuilt layer ships only while it is current. Its index lists every
// file it was built from by hash; the copies above prove the published copies equal
// their sources, and this proves those sources are still what the buffers came from.
// A mirror with no data/prebuilt/ is not stale — the page builds its own timber —
// and the sandboxes that publish one file (test_ticket_mirror.mjs) have none.
if (existsSync(path.join(SITE, 'data/prebuilt'))) {
  const { stale, PREBUILT_LAYERS } = await import('./prebuild_layers.mjs');
  for (const why of PREBUILT_LAYERS.flatMap((layer) => stale(path.join(SITE, 'data/prebuilt'), layer))) {
    problems.push(`data/prebuilt is stale — ${why}. publish.sh rebuilds it; a stale prebuild would hand `
      + 'the page timber built from other records or other code.');
  }
  // The page asks only for what index.json lists (js/prebuilt-index.js), so the list
  // must be exactly what is on disk: a layer it omits is never used, and one it names
  // that is missing is the 404 the list exists to prevent.
  const listFile = path.join(SITE, 'data/prebuilt/index.json');
  if (!existsSync(listFile)) {
    problems.push('data/prebuilt has no index.json, so the page cannot tell which years were prebuilt '
      + 'and would ask for, and 404 on, every year\'s layers.');
  } else {
    const list = JSON.parse(readFileSync(listFile, 'utf8'));
    const onDisk = {};
    for (const year of readdirSync(path.join(SITE, 'data/prebuilt'))) {
      if (!/^\d{4}$/.test(year)) continue;
      onDisk[year] = PREBUILT_LAYERS.filter((layer) => existsSync(path.join(SITE, 'data/prebuilt', year, `${layer}.json`))).sort();
    }
    const sorted = (o) => JSON.stringify(Object.fromEntries(Object.entries(o).map(([y, ls]) => [y, [...ls].sort()]).sort()));
    if (sorted(onDisk) !== sorted(list.layers ?? {})) {
      problems.push(`data/prebuilt/index.json lists ${sorted(list.layers ?? {})} and the mirror holds ${sorted(onDisk)}.`);
    }
  }
}
if (problems.length) {
  console.error('published mirror FAILED:');
  for (const p of problems) console.error('  - ' + p);
  process.exit(1);
}

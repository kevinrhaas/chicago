#!/usr/bin/env node
// write_year_packs.mjs — the per-year packs a visitor can keep on the device (T-2561).
//
//   node tools/write_year_packs.mjs <site/4d>      # publish.sh runs it last
//   node tools/write_year_packs.mjs --self-test    # check.sh: the rules, no site needed
//   node tools/write_year_packs.mjs --check <site/4d>   # every listed file is what it says
//
// For every year with a scene it writes:
//
//   packs/<year>.json      the pack: every file the year can ask for, with a
//                          content hash and size. renderers/web/js/year-pack.js
//                          downloads it into Cache Storage and, on a later
//                          publish, fetches only the entries whose hash moved.
//   packs/index.json       one line per year (id, file count, bytes), so the
//                          welcome can quote the size without the whole list.
//   <year>/app.webmanifest the home-screen app for that year's door.
//   sw.js                  offline/sw.js, at the root so its scope is
//                          the whole app (KILL = true when offline/sw-off
//                          exists — the kill switch; see that file's header).
//
// WHAT A YEAR'S PACK HOLDS. Everything under walk/ (the app), the year's door,
// the changelog What's-New reads, build.json, and data/ — except the two things
// that are genuinely split by year: GLBs (a year takes the ones its own sidecars
// name, plus the terrain epochs' grounds, which every year may load) and the other
// years' sidecars. The rest of data/ is shared and goes
// in every pack, because every year's cards and layers read from it and a pack
// that missed one file would fail offline at the moment a visitor opens that card.
// Checked against a recorded 1835 boot: all 687 GLBs it loaded are in 1835's pack.
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync, mkdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import path from 'node:path';
import { planUpdate } from '../renderers/web/js/year-pack.js';
import { sheetsNamedBy } from './share_glb_sheets.mjs';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const ROOT4D = path.resolve(HERE, '..');
export const SW_SOURCE = path.join(ROOT4D, 'offline/sw.js');
export const SW_OFF = path.join(ROOT4D, 'offline/sw-off');
export const HASH_HEX = 16;
// Read from the network first while online; the pack's copy answers offline.
export const NETWORK_FIRST = ['build.json', 'js/changelog.js', 'walk/js/changelog.js'];
const GLB_REF = /gltf\/[A-Za-z0-9_.\/-]+?\.(?:glb|ktx2|bin)/g;

export const hashOf = (bytes) => createHash('sha256').update(bytes).digest('hex').slice(0, HASH_HEX);

/** Years with a scene: the doors a pack can open. */
export function packYears(site) {
  const dir = path.join(site, 'data/scenes');
  return existsSync(dir)
    ? readdirSync(dir).map((f) => (f.match(/^(\d{4})\.json$/) || [])[1]).filter(Boolean).sort() : [];
}

function listFiles(site, rel = '') {
  const out = [];
  for (const e of readdirSync(path.join(site, rel), { withFileTypes: true })) {
    const r = rel ? `${rel}/${e.name}` : e.name;
    if (e.isDirectory()) out.push(...listFiles(site, r));
    else out.push(r);
  }
  return out;
}

/**
 * Which years load each GLB: a GLB named in data/sidecars/<year>/ belongs to that
 * year; one named by data/terrain/ belongs to every year. A name in the app's code
 * or in prose (liberties, comparisons) is not a load: scene-loader.js names the
 * Glessner file to recognise it, and counting that put 59 MB in every year's pack.
 * A GLB nothing names also goes to every year: a pack that holds a file too many
 * costs bytes, a pack that misses one breaks offline.
 *
 * T-3232: a shared texture sheet (data/gltf/sheets/) is named inside the GLBs that use
 * it, not by any record, so `sheetsOf(glb)` reads those names and a sheet belongs to
 * every year its GLBs belong to — to every year, if one of them does.
 */
export function glbOwners(files, read, sheetsOf = () => []) {
  const owners = new Map();
  const add = (glb, owner) => (owners.get(glb) || owners.set(glb, new Set()).get(glb)).add(owner);
  for (const rel of files) {
    if (!/\.(json|js)$/.test(rel)) continue;
    const year = rel.match(/^data\/sidecars\/(\d{4})\//)?.[1];
    const every = rel.startsWith('data/terrain/');
    if (!year && !every) continue;
    for (const m of read(rel).matchAll(GLB_REF)) add(`data/${m[0]}`, year || '*');
  }
  for (const rel of files) {
    if (!/^data\/gltf\/.+\.glb$/.test(rel)) continue;
    const of = owners.get(rel) ?? new Set(['*']);
    for (const sheet of sheetsOf(rel)) for (const o of of) add(sheet, o);
  }
  return owners;
}

export function yearFiles(files, year, owners) {
  return files.filter((rel) => {
    // T-2685: the home page's destination clips are the Observatory's, not a year's app.
    if (rel.startsWith('walk/portal/clips/')) return false;
    if (rel.startsWith('walk/') || rel === `${year}/index.html` || rel === `${year}/app.webmanifest`
      || NETWORK_FIRST.includes(rel)) return true;
    if (!rel.startsWith('data/')) return false;
    const side = rel.match(/^data\/sidecars\/(\d{4})\//)?.[1];
    if (side) return side === year;
    // A year's prebuilt layers (T-2677) are that year's alone, like its sidecars.
    const pre = rel.match(/^data\/prebuilt\/(\d{4})\//)?.[1];
    if (pre) return pre === year;
    if (/^data\/gltf\/.+\.(glb|ktx2|bin)$/.test(rel)) {
      const o = owners.get(rel);
      return !o || o.has('*') || o.has(year);
    }
    return true;
  });
}

// The update rule is the page's own, imported, so the self-test proves the shipped code.
export { planUpdate };

export function appManifest(year) {
  return {
    name: `4D Chicago · ${year}`,
    short_name: `Chicago ${year}`,
    description: `The walkable reconstruction of Chicago in ${year}, kept on this device.`,
    start_url: './',
    scope: './',
    display: 'standalone',
    background_color: '#16150f',
    theme_color: '#16150f',
    icons: [
      { src: '../walk/icons/icon-192.png', sizes: '192x192', type: 'image/png' },
      { src: '../walk/icons/icon-512.png', sizes: '512x512', type: 'image/png' },
      { src: '../walk/icons/icon-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
    ],
  };
}

export function swText(killed = existsSync(SW_OFF)) {
  const src = readFileSync(SW_SOURCE, 'utf8');
  if (!/^const KILL = false;$/m.test(src)) throw new Error('offline/sw.js has no `const KILL = false;` line');
  return killed ? src.replace(/^const KILL = false;$/m, 'const KILL = true;') : src;
}

export function writeYearPacks(site) {
  writeFileSync(path.join(site, 'sw.js'), swText());
  // The kill switch, the page's side: year-pack.js reads build.json on every visit.
  if (existsSync(SW_OFF) && existsSync(path.join(site, 'build.json'))) {
    const stamp = JSON.parse(readFileSync(path.join(site, 'build.json'), 'utf8'));
    writeFileSync(path.join(site, 'build.json'), `${JSON.stringify({ ...stamp, sw_off: true }, null, 2)}\n`);
  }
  const years = packYears(site);
  for (const year of years) {
    if (!existsSync(path.join(site, year))) mkdirSync(path.join(site, year), { recursive: true });
    writeFileSync(path.join(site, year, 'app.webmanifest'), `${JSON.stringify(appManifest(year), null, 1)}\n`);
  }
  const files = listFiles(site).filter((rel) => !rel.startsWith('packs/')).sort();
  const owners = glbOwners(files, (rel) => readFileSync(path.join(site, rel), 'utf8'),
    (rel) => sheetsNamedBy(site, rel));
  const sums = new Map();
  const sum = (rel) => sums.get(rel) || sums.set(rel, (() => {
    const bytes = readFileSync(path.join(site, rel));
    return [hashOf(bytes), bytes.length];
  })()).get(rel);
  mkdirSync(path.join(site, 'packs'), { recursive: true });
  const summary = {};
  for (const year of years) {
    const list = yearFiles(files, year, owners).map((rel) => [rel, ...sum(rel)]);
    const id = hashOf(list.map((f) => f.join(' ')).join('\n'));
    const bytes = list.reduce((s, f) => s + f[2], 0);
    const pack = { year, id, count: list.length, bytes, network_first: NETWORK_FIRST, files: list };
    writeFileSync(path.join(site, 'packs', `${year}.json`), `${JSON.stringify(pack)}\n`);
    summary[year] = { id, count: list.length, bytes };
  }
  writeFileSync(path.join(site, 'packs', 'index.json'), `${JSON.stringify(summary, null, 1)}\n`);
  return summary;
}

/** The shipped packs list what ships: every entry exists, at its hash and size. */
export function checkYearPacks(site) {
  const problems = [];
  const killed = existsSync(SW_OFF);
  if (readFileSync(path.join(site, 'sw.js'), 'utf8') !== swText(killed)) {
    problems.push(`sw.js is not offline/sw.js${killed ? ' with KILL = true' : ''} — publish.sh was not re-run`);
  }
  const summary = JSON.parse(readFileSync(path.join(site, 'packs/index.json'), 'utf8'));
  for (const year of packYears(site)) {
    const pack = JSON.parse(readFileSync(path.join(site, 'packs', `${year}.json`), 'utf8'));
    if (summary[year]?.id !== pack.id) problems.push(`packs/index.json does not carry ${year}'s pack id`);
    for (const [rel, hash, size] of pack.files) {
      const abs = path.join(site, rel);
      if (!existsSync(abs)) { problems.push(`${year}: ${rel} is in the pack and not in the site`); continue; }
      const bytes = readFileSync(abs);
      if (bytes.length !== size || hashOf(bytes) !== hash) problems.push(`${year}: ${rel} is not the file its pack entry describes`);
    }
    if (!pack.files.some(([rel]) => rel === `${year}/index.html`)) problems.push(`${year}: the pack does not hold its own door`);
  }
  return problems;
}

function selfTest() {
  const fail = [];
  const ok = (cond, what) => { if (!cond) fail.push(what); };
  const files = ['walk/index.html', 'walk/js/main.js', '1835/index.html', '1904/index.html', 'build.json',
    'js/changelog.js', 'tickets.json', 'index.html', 'data/scenes/1835.json', 'data/residents/a.json',
    'data/sidecars/1835/a.json', 'data/sidecars/1904/b.json', 'data/terrain/epochs/e1834.json',
    'data/gltf/a__1835.glb', 'data/gltf/b__1904.glb', 'data/gltf/terrain__e1834.glb', 'data/gltf/loose.glb',
    'data/liberties.json', 'prairie-1904/index.html', 'walk/js/scene-loader.js',
    'data/prebuilt/1835/frontage.json', 'data/prebuilt/1835/frontage.bin.gz'];
  const text = {
    'data/sidecars/1835/a.json': '{"asset":"gltf/a__1835.glb"}',
    'data/sidecars/1904/b.json': '{"asset":"gltf/b__1904.glb"}',
    'data/terrain/epochs/e1834.json': '{"glb":"gltf/terrain__e1834.glb"}',
    // A prose mention is not a load: liberties naming a 1904 file must not pull it into 1835.
    'data/liberties.json': '{"note":"see gltf/b__1904.glb"}',
    'walk/js/scene-loader.js': "asset === 'gltf/b__1904.glb'",
  };
  const owners = glbOwners(files, (rel) => text[rel] || '');
  const y1835 = new Set(yearFiles(files, '1835', owners));
  ok(y1835.has('data/gltf/a__1835.glb'), '1835 holds its own GLB');
  ok(!y1835.has('data/gltf/b__1904.glb'), '1835 does not hold a 1904 GLB that a liberty or the code merely names');
  ok(y1835.has('data/gltf/terrain__e1834.glb'), 'a terrain GLB is in every pack');
  ok(y1835.has('data/gltf/loose.glb'), 'a GLB nothing names stays in (missing one breaks offline)');
  ok(!y1835.has('data/sidecars/1904/b.json') && y1835.has('data/sidecars/1835/a.json'), 'sidecars split by year');
  // T-3232: a shared sheet goes where the GLBs that name it go.
  const sheetFiles = [...files, 'data/gltf/sheets/0123456789abcdef.ktx2', 'data/gltf/sheets/fedcba9876543210.ktx2'];
  const named = { 'data/gltf/b__1904.glb': ['data/gltf/sheets/0123456789abcdef.ktx2'],
    'data/gltf/loose.glb': ['data/gltf/sheets/fedcba9876543210.ktx2'] };
  const sheetOwners = glbOwners(sheetFiles, (rel) => text[rel] || '', (rel) => named[rel] ?? []);
  const s1835 = new Set(yearFiles(sheetFiles, '1835', sheetOwners));
  ok(!s1835.has('data/gltf/sheets/0123456789abcdef.ktx2')
    && yearFiles(sheetFiles, '1904', sheetOwners).includes('data/gltf/sheets/0123456789abcdef.ktx2'),
    'a sheet only a 1904 GLB names is in the 1904 pack and not 1835\'s (T-3232)');
  ok(s1835.has('data/gltf/sheets/fedcba9876543210.ktx2'), 'a sheet a GLB of every year names is in every pack (T-3232)');
  ok(y1835.has('data/prebuilt/1835/frontage.bin.gz') && !yearFiles(files, '1904', owners).includes('data/prebuilt/1835/frontage.bin.gz'),
    'a year\'s prebuilt layers are in its own pack and no other (T-2677)');
  ok(y1835.has('1835/index.html') && !y1835.has('1904/index.html'), 'each pack holds its own door only');
  ok(y1835.has('js/changelog.js') && y1835.has('build.json'), 'the network-first files are in the pack for offline');
  ok(!y1835.has('tickets.json') && !y1835.has('prairie-1904/index.html') && !y1835.has('index.html'),
    'files the walk never loads stay out');
  const old = { files: [['a', '1'], ['b', '2'], ['c', '3']] };
  const plan = planUpdate(old, { files: [['a', '1'], ['b', '9'], ['d', '4']] });
  ok(plan.fetch.map((f) => f[0]).join() === 'b,d', 'an update fetches only the changed and the new');
  ok(plan.drop.join() === 'c', 'an update drops what left the pack');
  ok(planUpdate(null, old).fetch.length === 3, 'a first install fetches everything');
  ok(planUpdate(old, old, new Set(['a', 'c'])).fetch.map((f) => f[0]).join() === 'b', 'an evicted file is fetched again');
  ok(/^const KILL = true;$/m.test(swText(true)) && /^const KILL = false;$/m.test(swText(false)), 'the kill switch flips one line');
  for (const f of fail) console.error(`write_year_packs self-test FAIL: ${f}`);
  if (fail.length) process.exit(1);
  console.log('write_year_packs self-test: ok (pack membership, the update diff, the kill switch)');
}

if (process.argv[1] && path.resolve(process.argv[1]) === new URL(import.meta.url).pathname) {
  const args = process.argv.slice(2);
  if (args[0] === '--self-test') selfTest();
  else if (args[0] === '--check') {
    const problems = checkYearPacks(path.resolve(args[1] || path.join(ROOT4D, '../../site/4d')));
    for (const p of problems) console.error(`year packs: ${p}`);
    if (problems.length) process.exit(1);
    console.log('year packs: every listed file is the file it describes');
  } else {
    const site = path.resolve(args[0] || path.join(ROOT4D, '../../site/4d'));
    const summary = writeYearPacks(site);
    for (const [year, s] of Object.entries(summary)) {
      console.log(`   pack ${year}: ${s.count} files, ${(s.bytes / 1e6).toFixed(1)} MB`);
    }
  }
}

#!/usr/bin/env node
/**
 * The boot sidecars ship packed, and the records stay whole at their own URLs (T-2315).
 *
 * WHY. Every first visit loads every 1835 sidecar, one file per structure, and gzip
 * compresses each file on its own — so a value the town repeats is paid for once PER
 * RECORD. It repeats a great deal: 1,505 citations across 689 records are 58 distinct
 * sources (the reconstruction specification alone is on hundreds of them, with its
 * `what_it_supplies` and `what_it_does_not_supply` written out in full each time), and
 * the reconstructed roofs share their attribute reasoning family by family. Measured on
 * dev @ 031535d99: the sidecars were 3.74 MB of a 14.51 MB first visit, 1.51 MB over the
 * 13 MB budget (docs/SITE-BUDGET.md §4). And the 686 records were 686 requests, each
 * its own gzip stream, so even the field names every record shares were compressed afresh
 * 686 times.
 *
 * The answer is not to take anything OFF the boot path. A card draws its citations and
 * its "why" toggles the moment it opens, and the smoke reads them in the same tick, so
 * every byte the scene loads now still arrives before `ready`. What changes is that a
 * repeated value arrives once, and records travel fifty to a file. `tools/publish.sh`
 * runs this after the household notes are deferred, and for every scene with a sidecar
 * index the mirror gains:
 *
 *   data/sidecars/<scene>/boot/shared.json   { values: [...] } — every string or object
 *                                            of 60+ characters that 3+ records carry
 *   data/sidecars/<scene>/boot/part-<n>.json { <id>: record, … } for index rows
 *                                            50n … 50n+49, each record as shipped with
 *                                            every shared value replaced by
 *                                            { "$shared": <its index> }
 *   data/sidecars/<scene>/index.json         + `boot: { shared, dir, per_part }`, which is
 *                                            how the loader knows (it never probes)
 *
 * Measured on the wire (tools/measure_boot_payload.mjs), the 1835 sidecar folder a first
 * visit loads: 3.739 MB in 694 requests as it was; 2.194 MB with the shared values alone,
 * still one file per record; 1.269 MB in 23 requests with the parts as well.
 *
 * `scene-loader.js` fetches shared.json once beside the index, each part once, and puts
 * every value back (`rehydrate`) before anything else sees a record — so the registry
 * holds exactly what `<id>.json` holds, key for key and in
 * the same order, and no consumer can tell. `<id>.json` itself is untouched: the record
 * a person opens at its URL is still the readable one (SITE-BUDGET §6). A structure
 * pointed at a version (T-1727) loads its version file whole, as before.
 *
 *   node tools/pack_boot_sidecars.mjs [--site DIR]   pack the mirror in place
 *   node tools/pack_boot_sidecars.mjs --check        each boot copy against its record
 *   node tools/pack_boot_sidecars.mjs --self-test    pack and rehydrate on a fixture
 */
import { readFileSync, writeFileSync, readdirSync, statSync, existsSync, mkdirSync, mkdtempSync, rmSync } from 'node:fs';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { isDeepStrictEqual } from 'node:util';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');                         // chicago/4d
const SRC = path.join(ROOT, 'data', 'sidecars');
const SITE = path.resolve(ROOT, '..', '..', 'site', '4d', 'data', 'sidecars');

/** A value is worth sharing when it is at least this long as JSON… */
export const MIN_CHARS = 60;
/** …and at least this many records carry it. */
export const MIN_RECORDS = 3;
/** Index rows per boot part: few enough requests, and each part's gzip stream long
 *  enough to see the field names and phrasing its records share. */
export const PER_PART = 50;
const MARK = '$shared';

const isObject = (v) => v !== null && typeof v === 'object';
const candidate = (v) => (typeof v === 'string' || isObject(v)) && JSON.stringify(v).length >= MIN_CHARS;
const isMark = (v) => isObject(v) && !Array.isArray(v)
  && Object.keys(v).length === 1 && Object.hasOwn(v, MARK);

/** Every candidate value under `v` (not `v` itself), as JSON, into `into`. */
function collect(v, into) {
  for (const x of Array.isArray(v) ? v : isObject(v) ? Object.values(v) : []) {
    if (candidate(x)) into.add(JSON.stringify(x));
    collect(x, into);
  }
  if (isMark(v)) throw new Error(`a record already holds a { "${MARK}" } object, which the loader would read as a reference`);
}

/**
 * Pack a set of records against each other.
 * @param {object[]} records  shipped sidecars, in index order
 * @returns {{ values: any[], packed: object[] }}
 */
export function pack(records) {
  const seen = new Map();
  for (const rec of records) {
    const mine = new Set();
    collect(rec, mine);
    for (const k of mine) seen.set(k, (seen.get(k) ?? 0) + 1);
  }
  const keys = [...seen].filter(([, n]) => n >= MIN_RECORDS).map(([k]) => k).sort();
  const index = new Map(keys.map((k, i) => [k, i]));
  const sub = (v) => {
    if (!isObject(v)) return v;
    if (Array.isArray(v)) return v.map((x) => (candidate(x) && index.has(JSON.stringify(x)) ? { [MARK]: index.get(JSON.stringify(x)) } : sub(x)));
    const out = {};
    for (const [k, x] of Object.entries(v)) {
      Object.defineProperty(out, k, { value: candidate(x) && index.has(JSON.stringify(x)) ? { [MARK]: index.get(JSON.stringify(x)) } : sub(x),
        enumerable: true, writable: true, configurable: true });
    }
    return out;
  };
  return { values: keys.map((k) => JSON.parse(k)), packed: records.map(sub) };
}

/**
 * Put every shared value back — the same function scene-loader.js runs, kept here so
 * the gate and the self-test exercise the very shape the loader reads.
 */
export function rehydrate(v, values) {
  if (!isObject(v)) return v;
  if (isMark(v)) {
    const got = values[v[MARK]];
    if (got === undefined) throw new Error(`no shared value ${v[MARK]}`);
    return structuredClone(got);
  }
  for (const k of Object.keys(v)) v[k] = rehydrate(v[k], values);
  return v;
}

const read = (p) => JSON.parse(readFileSync(p, 'utf8'));

/** The scenes under `site` that publish a sidecar index, and their rows. */
function scenes(site) {
  const out = [];
  for (const scene of existsSync(site) ? readdirSync(site).sort() : []) {
    const idx = path.join(site, scene, 'index.json');
    if (!statSync(path.join(site, scene)).isDirectory() || !existsSync(idx)) continue;
    const index = read(idx);
    const rows = (Array.isArray(index.structures) ? index.structures : [])
      .map((row) => (typeof row === 'string' ? { id: row } : row))
      .filter((row) => row && typeof row.id === 'string');
    out.push({ scene, idx, index, rows });
  }
  return out;
}

/** Where a row's record sits in the mirror — the path scene-loader.js reads. */
const recordPath = (site, scene, row) => path.join(path.dirname(site),
  row.sidecar ?? `sidecars/${scene}/${row.id}.json`);
const bootFor = (scene) => ({ shared: `sidecars/${scene}/boot/shared.json`, dir: `sidecars/${scene}/boot/`, per_part: PER_PART });
/** The part an index row's record travels in — the loader computes the same. */
export const partName = (position) => `part-${Math.floor(position / PER_PART)}.json`;

function write(site) {
  for (const { scene, idx, index, rows } of scenes(site)) {
    const dir = path.join(site, scene, 'boot');
    if (existsSync(dir)) rmSync(dir, { recursive: true });
    // A missing indexed record stays out of its part; the checker rejects it and
    // the loader reports it as before. A genuinely empty index still needs its
    // boot descriptor and empty shared table, with no part files (1871 context).
    const present = rows.map((row, at) => ({ row, at })).filter(({ row }) => existsSync(recordPath(site, scene, row)));
    const { values, packed } = pack(present.map(({ row }) => read(recordPath(site, scene, row))));
    const parts = new Map();
    present.forEach(({ row, at }, i) => {
      const name = partName(at);
      if (!parts.has(name)) parts.set(name, {});
      Object.defineProperty(parts.get(name), row.id, { value: packed[i], enumerable: true, writable: true, configurable: true });
    });
    mkdirSync(dir, { recursive: true });
    writeFileSync(path.join(dir, 'shared.json'), JSON.stringify({ values }));
    for (const [name, part] of parts) writeFileSync(path.join(dir, name), JSON.stringify(part));
    writeFileSync(idx, JSON.stringify({ ...index, boot: bootFor(scene) }, null, 2));
    console.log(`boot sidecars packed: ${scene} — ${present.length} record(s) in ${parts.size} part(s), sharing ${values.length} value(s) → sidecars/${scene}/boot/`);
  }
}

function check(src, site) {
  const problems = [];
  let n = 0;
  for (const { scene, index, rows } of scenes(site)) {
    const srcIdx = path.join(src, scene, 'index.json');
    const { boot, ...rest } = index;
    if (!boot) { problems.push(`${scene}/index.json: no \`boot\` — publish.sh did not pack this scene`); continue; }
    if (!isDeepStrictEqual(boot, bootFor(scene))) problems.push(`${scene}/index.json: \`boot\` is ${JSON.stringify(boot)}, not ${JSON.stringify(bootFor(scene))}`);
    if (!existsSync(srcIdx) || !isDeepStrictEqual(rest, read(srcIdx))) problems.push(`${scene}/index.json: not its source plus \`boot\``);
    const sharedFile = path.join(site, scene, 'boot', 'shared.json');
    if (!existsSync(sharedFile)) { problems.push(`${scene}/boot/shared.json: missing`); continue; }
    const { values } = read(sharedFile);
    if (!Array.isArray(values)) { problems.push(`${scene}/boot/shared.json: holds no \`values\` array`); continue; }
    const expected = new Set(['shared.json']);
    const parts = new Map();
    const partFor = (name) => {
      if (!parts.has(name)) {
        const file = path.join(site, scene, 'boot', name);
        parts.set(name, existsSync(file) ? { ids: new Set(Object.keys(read(file))), part: read(file) } : null);
      }
      return parts.get(name);
    };
    for (const [at, row] of rows.entries()) {
      const rec = recordPath(site, scene, row);
      if (!existsSync(rec)) { problems.push(`${scene}/index.json: missing indexed record ${path.relative(path.dirname(site), rec)}`); continue; }
      const name = partName(at);
      expected.add(name);
      const got = partFor(name);
      if (!got || !Object.hasOwn(got.part, row.id)) { problems.push(`${scene}/boot/${name}: does not carry ${row.id} — this record would not load`); continue; }
      got.ids.delete(row.id);
      n += 1;
      let back;
      try { back = rehydrate(got.part[row.id], values); } catch (err) { problems.push(`${scene}/boot/${name} ${row.id}: ${err.message}`); continue; }
      const whole = read(rec);
      if (!isDeepStrictEqual(back, whole) || JSON.stringify(back) !== JSON.stringify(whole)) {
        problems.push(`${scene}/boot/${name} ${row.id}: does not rehydrate to ${path.relative(path.dirname(site), rec)}, key for key`);
      }
    }
    for (const [name, got] of parts) {
      for (const id of got?.ids ?? []) problems.push(`${scene}/boot/${name}: carries ${id}, which its index row does not put there`);
    }
    for (const f of readdirSync(path.join(site, scene, 'boot'))) {
      if (!expected.has(f)) problems.push(`${scene}/boot/${f}: shipped, but no index row loads it`);
    }
  }
  if (problems.length) {
    console.error(`PACKED BOOT SIDECARS: ${problems.length} problem(s)`);
    for (const p of problems.slice(0, 12)) console.error(`  - ${p}`);
    process.exit(1);
  }
  console.log(`packed boot sidecars: ${n} record(s) rehydrate to the record at their own URL, key for key`);
}

/** Exercise the real CLI in an isolated source/publication layout, including its
 * strict failure exits. No committed scene, mirror or fixture is modified. */
function publicationSelfTest() {
  const root = mkdtempSync(path.join(tmpdir(), 'packed-boot-sidecars-'));
  try {
    const tool = path.join(root, 'chicago', '4d', 'tools', 'pack_boot_sidecars.mjs');
    const src = path.join(root, 'chicago', '4d', 'data', 'sidecars');
    const site = path.join(root, 'site', '4d', 'data', 'sidecars');
    mkdirSync(path.dirname(tool), { recursive: true });
    writeFileSync(tool, readFileSync(fileURLToPath(import.meta.url)));
    const put = (p, value) => { mkdirSync(path.dirname(p), { recursive: true }); writeFileSync(p, JSON.stringify(value)); };
    const run = (...args) => {
      const result = spawnSync(process.execPath, [tool, ...args], { encoding: 'utf8', timeout: 10000 });
      assert.ifError(result.error);
      return result;
    };
    const requirePass = (result) => assert.equal(result.status, 0, result.stderr || result.stdout);
    const requireFailure = (message) => {
      const result = run('--check');
      assert.equal(result.status, 1, `checker accepted corruption: ${message}`);
      assert.match(result.stderr, message);
    };
    const seed = (count, missing = []) => {
      rmSync(src, { recursive: true, force: true });
      rmSync(site, { recursive: true, force: true });
      const rows = Array.from({ length: count }, (_, i) => ({ id: `roof_${i}` }));
      const index = { scene: '1871', structures: rows };
      put(path.join(src, '1871', 'index.json'), index);
      put(path.join(site, '1871', 'index.json'), index);
      for (const [at, row] of rows.entries()) {
        if (missing.includes(at)) continue;
        put(path.join(site, '1871', `${row.id}.json`), { id: row.id, own: at,
          note: 'A shared reason long enough for this publication fixture to exercise real packing.' });
      }
      requirePass(run('--site', site));
    };
    const idx = path.join(site, '1871', 'index.json');
    const boot = path.join(site, '1871', 'boot');
    seed(0);
    assert.deepEqual(read(idx).boot, bootFor('1871'));
    assert.deepEqual(read(path.join(boot, 'shared.json')), { values: [] });
    assert.deepEqual(readdirSync(boot), ['shared.json']);
    requirePass(run('--check'));

    seed(PER_PART + 1);
    assert.deepEqual(readdirSync(boot).sort(), ['part-0.json', 'part-1.json', 'shared.json']);
    requirePass(run('--check'));
    const first = [idx, ...readdirSync(boot).sort().map((f) => path.join(boot, f))]
      .map((f) => [f, readFileSync(f, 'utf8')]);
    requirePass(run('--site', site));
    for (const [f, before] of first) assert.equal(readFileSync(f, 'utf8'), before, `repacking changed ${f}`);
    requirePass(run('--check'));

    seed(PER_PART + 1, [1]);
    assert.ok(Object.hasOwn(read(path.join(boot, 'part-1.json')), `roof_${PER_PART}`), 'missing row shifted later parts');
    requireFailure(/missing indexed record sidecars\/1871\/roof_1\.json/);
    seed(2, [0, 1]);
    requireFailure(/missing indexed record/);

    seed(0);
    const { boot: omitted, ...withoutBoot } = read(idx);
    put(idx, withoutBoot);
    requireFailure(/no `boot`/);
    seed(0);
    put(idx, { ...read(idx), boot: { ...bootFor('1871'), per_part: 1 } });
    requireFailure(/`boot` is/);
    seed(0);
    rmSync(path.join(boot, 'shared.json'));
    requireFailure(/shared\.json: missing/);
    seed(0);
    put(path.join(boot, 'shared.json'), { values: {} });
    requireFailure(/holds no `values` array/);
    seed(0);
    put(path.join(boot, 'part-0.json'), {});
    requireFailure(/shipped, but no index row loads it/);

    seed(PER_PART + 1);
    rmSync(path.join(boot, 'part-1.json'));
    requireFailure(/does not carry roof_50/);
    seed(3);
    const part = read(path.join(boot, 'part-0.json'));
    part.roof_0.own = 'corrupted';
    put(path.join(boot, 'part-0.json'), part);
    requireFailure(/does not rehydrate/);

    seed(PER_PART + 1);
    put(path.join(src, '1871', 'index.json'), { scene: '1871', structures: [] });
    put(idx, { ...read(idx), structures: [] });
    requirePass(run('--site', site));
    assert.deepEqual(readdirSync(boot), ['shared.json'], 'empty repack retained obsolete parts');
    assert.deepEqual(read(path.join(boot, 'shared.json')), { values: [] });
    requirePass(run('--check'));
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
}

function selfTest() {
  const long = 'A reason long enough to be worth sharing between the records that carry it.';
  const cite = { source_id: 'spec', citation: 'The reconstruction specification, cited on every roof.' };
  const recs = ['a', 'b', 'c'].map((id, i) => ({ id, attributes: { h: { value: i, note: long } }, citations: [cite], own: `${id} is its own and no other record's.` }));
  recs.push({ id: 'd', citations: [cite, { source_id: 'x', citation: 'Only once, and so never shared at all, however long.' }] });
  const before = structuredClone(recs);
  const { values, packed } = pack(recs);
  const fails = [];
  if (!isDeepStrictEqual(recs, before)) fails.push('packing mutated its input');
  // The note, the citation, and the one-citation list a, b and c carry alike.
  if (values.length !== 3) fails.push(`expected the note, the citation and its list shared, got ${values.length} value(s)`);
  if (!isMark(packed[0].attributes.h.note) || !isMark(packed[3].citations[0])) fails.push('a repeated value was not replaced');
  if (isMark(packed[3].citations[1]) || isMark(packed[0].own)) fails.push('a value fewer than three records carry was shared');
  if (partName(0) !== partName(PER_PART - 1) || partName(PER_PART - 1) === partName(PER_PART)) fails.push('rows are not grouped PER_PART to a part');
  const back = packed.map((p) => rehydrate(structuredClone(p), values));
  if (JSON.stringify(back) !== JSON.stringify(recs)) fails.push('rehydration did not restore the records key for key');
  back[0].citations[0].citation = 'changed';
  if (back[1].citations[0].citation !== cite.citation) fails.push('two rehydrated records share one object, so a change to one would change both');
  try { pack([{ id: 'e', x: { [MARK]: 0 } }]); fails.push('a record holding the marker was packed'); } catch { /* refused, as it must be */ }
  try { publicationSelfTest(); } catch (err) { fails.push(`publication fixtures: ${err.message}`); }
  if (fails.length) { for (const f of fails) console.error(`self-test | FAIL ${f}`); process.exit(1); }
  console.log('self-test | ok: repeated values ship once, every record comes back whole and unaliased');
  console.log('self-test | ok: empty/nonempty publication, stable repacking and part positions, nine corruption refusals, and stale-part cleanup');
}

const argv = process.argv.slice(2);
if (argv.includes('--self-test')) selfTest();
else if (argv.includes('--check')) check(SRC, SITE);
else {
  const i = argv.indexOf('--site');
  write(i >= 0 ? path.resolve(argv[i + 1]) : SITE);
}

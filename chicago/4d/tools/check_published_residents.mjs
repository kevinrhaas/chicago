#!/usr/bin/env node
/**
 * The gate that measures the SHIPPED form of the residents layer.
 *
 * `tools/publish.sh` writes `site/4d/data/residents/**.json` MINIFIED, which is
 * the one path in the mirror that is not byte-identical to its source, so
 * `check_published.mjs` lists it under TRANSFORMED and points here. The reason is the
 * size budget: 1,380 hand-annotated household records whose notes run to paragraphs came
 * to 8.8 MB of the 32 MB a Pages tree is allowed, the tree measured 31.999 MB on
 * 2026-09-05, and the next resident pass of any size could not have landed.
 *
 * Whitespace is the one thing in these files a visitor never reads — the renderer fetches
 * them with `response.json()`. So the invariant this asserts is not weaker than the byte
 * comparison it replaces, it is the same claim one level up: **the shipped file parses to
 * a value deep-equal to its source**, file for file, with no file missing and none extra.
 * A dropped field, a truncated note or a stale mirror fails here exactly as it would have
 * failed there.
 */
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { unpackRecord } from '../renderers/web/js/letter-list-roster.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');                 // chicago/4d
const SRC = path.join(ROOT, 'data', 'residents');
const SITE = path.resolve(ROOT, '..', '..', 'site', '4d', 'data', 'residents');

const walk = (dir, base = '') => {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const e of readdirSync(dir).sort()) {
    const abs = path.join(dir, e);
    const rel = base ? `${base}/${e}` : e;
    if (statSync(abs).isDirectory()) out.push(...walk(abs, rel));
    else if (e.endsWith('.json')) out.push(rel);
  }
  return out;
};

/** Structural equality, order-sensitive for arrays and order-insensitive for objects. */
const same = (a, b) => JSON.stringify(canon(a)) === JSON.stringify(canon(b));
const canon = (v) => {
  if (Array.isArray(v)) return v.map(canon);
  if (v && typeof v === 'object') {
    return Object.fromEntries(Object.keys(v).sort().map((k) => [k, canon(v[k])]));
  }
  return v;
};

if (!existsSync(SITE)) {
  console.log('published residents: nothing published yet — skipped');
  process.exit(0);
}

const srcFiles = new Set(walk(SRC));
const problems = [];
let checked = 0;
let minified = 0;

// T-0438. The letter-list cohort ships PACKED under letter_list/ — a roster of the
// strings it repeats and a shard per initial — and its per-record files are taken out
// of the mirror by tools/pack_letter_list.py. Those records are held to the same claim
// as every other file here: each one, unpacked by the renderer's own `unpackRecord`,
// must parse to its source's value. So the roster's records join the comparison below
// as if they were published at their own paths, and the packed files themselves are
// the one thing in the mirror with no source of their own.
const ROSTER_DIR = 'letter_list';
const packed = new Map();
const rosterPath = path.join(SITE, ROSTER_DIR, 'roster.json');
const rosterFiles = walk(path.join(SITE, ROSTER_DIR)).map((f) => `${ROSTER_DIR}/${f}`);
if (existsSync(rosterPath)) {
  const roster = JSON.parse(readFileSync(rosterPath, 'utf8'));
  const shardBodies = new Map();
  for (const f of rosterFiles) {
    if (f.endsWith('/roster.json')) continue;
    shardBodies.set(path.basename(f, '.json'), JSON.parse(readFileSync(path.join(SITE, f), 'utf8')));
  }
  const listed = new Set();
  for (const [file, shard] of Object.entries(roster.shards || {})) {
    const rec = shardBodies.get(shard)?.records?.[file];
    if (rec === undefined) {
      problems.push(`the letter-list roster puts ${file} in shard ${shard} and that shard does not hold it`);
      continue;
    }
    listed.add(`${shard}|${file}`);
    try {
      packed.set(file, unpackRecord(rec, roster.strings || []));
    } catch (e) {
      problems.push(`${file} does not unpack from shard ${shard}: ${e.message}`);
    }
  }
  for (const [shard, body] of shardBodies) {
    for (const file of Object.keys(body.records || {})) {
      if (!listed.has(`${shard}|${file}`)) {
        problems.push(`letter_list/${shard}.json carries ${file} and the roster does not name it there`);
      }
    }
  }
  // The cohort is exactly the index's letter_list_only households — no more, no fewer.
  const index = JSON.parse(readFileSync(path.join(SRC, 'index.json'), 'utf8'));
  const cohort = new Set((index.households || []).filter((e) => e.letter_list_only).map((e) => e.file));
  for (const f of cohort) {
    if (!packed.has(f)) problems.push(`${f} is in the letter-list cohort and the roster does not carry it`);
  }
  for (const f of packed.keys()) {
    if (!cohort.has(f)) problems.push(`the roster carries ${f}, which the index does not put in the letter-list cohort`);
  }
} else if (rosterFiles.length) {
  problems.push(`letter_list/ is published without its roster.json — its shards cannot be read`);
}
const siteFiles = new Set(walk(SITE).filter((f) => !f.startsWith(`${ROSTER_DIR}/`)));
for (const rel of packed.keys()) {
  if (siteFiles.has(rel)) {
    problems.push(`${rel} is published twice — as its own file and in the letter-list roster`);
  }
}

for (const rel of siteFiles) {
  if (!srcFiles.has(rel)) {
    problems.push(`${rel} is published but data/residents/${rel} does not exist — the mirror `
      + 'carries a file the repository does not');
    continue;
  }
  let a; let b;
  try { a = JSON.parse(readFileSync(path.join(SRC, rel), 'utf8')); } catch (e) {
    problems.push(`data/residents/${rel} does not parse: ${e.message}`); continue;
  }
  try { b = JSON.parse(readFileSync(path.join(SITE, rel), 'utf8')); } catch (e) {
    problems.push(`the published ${rel} does not parse: ${e.message}`); continue;
  }
  if (!same(a, b)) {
    problems.push(`${rel} does NOT carry its source's value. publish.sh minifies this path and `
      + 'nothing else may change in it, so either the mirror is stale and publish.sh was not '
      + 're-run, or something is rewriting the layer on the way out.');
    continue;
  }
  checked++;
  if (!readFileSync(path.join(SITE, rel), 'utf8').includes('\n')) minified++;
}

let unpacked = 0;
for (const [rel, b] of packed) {
  let a;
  try { a = JSON.parse(readFileSync(path.join(SRC, rel), 'utf8')); } catch (e) {
    problems.push(`data/residents/${rel} is in the roster and does not parse at its source: ${e.message}`);
    continue;
  }
  if (!same(a, b)) {
    problems.push(`${rel} does NOT read back from the letter-list roster as its source's value — `
      + 'the roster is stale, or tools/pack_letter_list.py changed a record on the way out');
    continue;
  }
  unpacked++;
}

for (const rel of srcFiles) {
  if (!siteFiles.has(rel) && !packed.has(rel)) {
    problems.push(`data/residents/${rel} is in the repository and NOT in the mirror — the renderer `
      + 'fetches this layer by path and an unpublished file is a 404 on the deployed site');
  }
}

if (problems.length) {
  console.log(`published residents: ${problems.length} problem(s)`);
  for (const p of problems.slice(0, 20)) console.log(`  - ${p}`);
  if (problems.length > 20) console.log(`  … and ${problems.length - 20} more`);
  process.exit(1);
}

console.log(`published residents OK — ${checked} file(s) carry their source's value exactly, `
  + `${minified} of them shipped on one line`
  + (packed.size ? `; ${unpacked} letter-list record(s) read back exactly from the roster (T-0438)` : ''));

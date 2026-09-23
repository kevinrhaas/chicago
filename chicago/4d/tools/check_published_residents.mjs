#!/usr/bin/env node
/**
 * The gate that measures the SHIPPED form of the residents layer.
 *
 * `tools/publish.sh` writes `site/chicago/4d/data/residents/**.json` MINIFIED, which is
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

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');                 // chicago/4d
const SRC = path.join(ROOT, 'data', 'residents');
const SITE = path.resolve(ROOT, '..', '..', 'site', 'chicago', '4d', 'data', 'residents');

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
const siteFiles = new Set(walk(SITE));
const problems = [];
let checked = 0;
let minified = 0;

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

for (const rel of srcFiles) {
  if (!siteFiles.has(rel)) {
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
  + `${minified} of them shipped on one line`);

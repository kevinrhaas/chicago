#!/usr/bin/env node
/**
 * The gate that holds the card's tier and the gate's tier to the same answer (T-1158).
 *
 *   node tools/check_attribute_tiers.mjs             compare, and print the counts
 *   node tools/check_attribute_tiers.mjs --self-test the assertions, broken on purpose
 *
 * The tier of an attribute is DERIVED from the confidence and the value the card already
 * carries, and it is derived TWICE: once in `tools/migrate_attribute_tiers.py`, which
 * publishes the counts and every reconstructed value's basis, and once in
 * `renderers/web/js/attribute-tiers.js`, which has to answer for the one card a visitor
 * has open without fetching a table of ten thousand rows to do it.
 *
 * Two derivations of one rule is exactly the shape that comes apart quietly. The failure
 * would not look like a crash: a card would simply draw the hatched *reconstructed* chip
 * over a field nobody invented, which is the defect this whole ticket exists to remove,
 * and the published table would keep reporting the correct figure while the walkthrough
 * showed the wrong one. So the two are run over the same 1,258 cards and required to
 * agree, attribute for attribute.
 */
import { readFileSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { tierOf, TIERS } from '../renderers/web/js/attribute-tiers.js';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const CARDS = path.join(ROOT, 'data', 'residents', 'households');
const TABLE = path.join(ROOT, 'data', 'research', 'residents', 'attribute_tiers.json');

/** Every claim block in a record, keyed by the attribute path that names it. */
export function* walkBlocks(node, prefix = '') {
  if (Array.isArray(node)) {
    for (const v of node) yield* walkBlocks(v, `${prefix}[]`);
    return;
  }
  if (node && typeof node === 'object') {
    if ('confidence' in node && 'value' in node) { yield [prefix, node]; return; }
    for (const [k, v] of Object.entries(node)) yield* walkBlocks(v, prefix ? `${prefix}.${k}` : k);
  }
}

function countCards() {
  const byAttribute = new Map();
  const byTier = Object.fromEntries(TIERS.map((t) => [t, 0]));
  for (const name of readdirSync(CARDS).sort()) {
    if (!name.endsWith('.json')) continue;
    const doc = JSON.parse(readFileSync(path.join(CARDS, name), 'utf8'));
    for (const [attr, block] of walkBlocks(doc)) {
      const tier = tierOf(block);
      if (!tier) continue;
      byTier[tier] += 1;
      if (!byAttribute.has(attr)) byAttribute.set(attr, Object.fromEntries(TIERS.map((t) => [t, 0])));
      byAttribute.get(attr)[tier] += 1;
    }
  }
  return { byTier, byAttribute };
}

function compare(mine, table) {
  const bad = [];
  const want = table.counts.by_tier;
  for (const t of TIERS) {
    if (mine.byTier[t] !== want[t]) {
      bad.push(`tier ${t}: the card reader counts ${mine.byTier[t]}, the table publishes ${want[t]}`);
    }
  }
  const wantAttr = table.counts.by_attribute;
  for (const attr of new Set([...Object.keys(wantAttr), ...mine.byAttribute.keys()])) {
    const a = mine.byAttribute.get(attr);
    const b = wantAttr[attr];
    if (!a || !b) { bad.push(`${attr}: seen by only one of the two readers`); continue; }
    for (const t of TIERS) {
      if (a[t] !== b[t]) bad.push(`${attr} ${t}: card reader ${a[t]}, table ${b[t]}`);
    }
  }
  return bad;
}

function selfTest() {
  const cases = [
    ['a null value under reconstructed', { value: null, confidence: 'reconstructed' }, 'unknown'],
    ['the trade sentinel', { value: 'none_recorded', confidence: 'reconstructed' }, 'unknown'],
    ['an empty string', { value: '', confidence: 'reconstructed' }, 'unknown'],
    ['a value somebody supplied', { value: '1826', confidence: 'reconstructed' }, 'reconstructed'],
    ['an inferred value', { value: '1834', confidence: 'inferred' }, 'inferred'],
    ['an attested value', { value: '1834', confidence: 'attested' }, 'attested'],
    ['a tier already written on the card wins', { value: null, confidence: 'reconstructed', tier: 'unknown' }, 'unknown'],
    ['a tier that is not one is ignored', { value: '1834', confidence: 'attested', tier: 'probable' }, 'attested'],
    ['something that is not a claim block', { value: '1834' }, null],
    ['nothing at all', null, null],
  ];
  let failed = 0;
  for (const [label, block, want] of cases) {
    const got = tierOf(block);
    const ok = got === want;
    console.log(`${ok ? 'ok   ' : 'FAIL '}${label}${ok ? '' : ` -> ${got}, wanted ${want}`}`);
    if (!ok) failed += 1;
  }
  // The walker must find a block nested inside a list inside an object, which is where
  // every person's occupation lives.
  const found = [...walkBlocks({ persons: [{ occupation: { value: null, confidence: 'reconstructed' } }] })];
  const ok = found.length === 1 && found[0][0] === 'persons[].occupation';
  console.log(`${ok ? 'ok   ' : 'FAIL '}the walker names a block nested in a list`);
  if (!ok) failed += 1;
  console.log(`${failed} failure(s)`);
  return failed ? 1 : 0;
}

if (process.argv.includes('--self-test')) process.exit(selfTest());

const table = JSON.parse(readFileSync(TABLE, 'utf8'));
const mine = countCards();
const bad = compare(mine, table);
if (bad.length) {
  console.error('FAIL the walkthrough and the published table derive different tiers:\n  '
    + bad.slice(0, 8).join('\n  ')
    + '\nOne of renderers/web/js/attribute-tiers.js and tools/migrate_attribute_tiers.py has '
    + 'moved without the other. They implement one rule and there is no version of this '
    + 'project in which they may answer differently.');
  process.exit(1);
}
console.log(`ok  the card reader and the published table agree on all ${
  TIERS.reduce((n, t) => n + mine.byTier[t], 0)} attribute tiers (${
  TIERS.map((t) => `${t} ${mine.byTier[t]}`).join(', ')})`);

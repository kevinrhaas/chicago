#!/usr/bin/env node
/**
 * T-3231 — every 1904 corner ramp's head meets its curb's top.
 *
 * street-grid.js draws a corner crossing's stone slab by asking `offsetAt` how far
 * below the field each vertex lies: inside a ramp, the slope from the curb's top
 * down to the roadway; inside a face's bands, the fall across the sidewalk space;
 * inside a roadway, the road's level. A ramp's head corners lie exactly on the ramp's
 * own edge and on the face bands' outer edge, where a parity test can fall either
 * way. Where both said "outside", the corner took the ROADWAY's level and the slab's
 * head dropped off the curb (the owner saw it at Prairie & 18th and Prairie & 16th):
 * 26 of the 112 head corners did.
 *
 * The fix tests a ramp with `nearPolygon` (inside, or within RAMP_EDGE_M of the edge).
 * This test slices `pointInPolygon`, `nearPolygon` and RAMP_EDGE_M out of the shipped
 * street-grid.js (three will not load headless, and a copy could drift), checks that
 * offsetAt's ramp branch calls nearPolygon, and asserts every ramp corner of every
 * crossing in data/street_section/1904.json is caught by it. The self-test runs the
 * same corners through the bare parity test and must see it miss some, or the gate
 * proves nothing.
 *
 *   node tools/test_ramp_heads.mjs [--self-test]
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const src = readFileSync(join(ROOT, 'renderers/web/js/street-grid.js'), 'utf8');
const section = JSON.parse(readFileSync(join(ROOT, 'data/street_section/1904.json'), 'utf8'));
const selfTest = process.argv.includes('--self-test');

function slice(name) {
  const at = src.indexOf(`function ${name}(`);
  if (at < 0) throw new Error(`street-grid.js has no function ${name} — this test is stale`);
  let depth = 0;
  for (let i = src.indexOf('{', at); i < src.length; i += 1) {
    if (src[i] === '{') depth += 1;
    if (src[i] === '}' && (depth -= 1) === 0) return src.slice(at, i + 1);
  }
  throw new Error(`could not read function ${name}`);
}
const eps = Number((src.match(/const RAMP_EDGE_M = ([0-9.]+);/) ?? [])[1]);
if (!(eps > 0)) throw new Error('street-grid.js has no RAMP_EDGE_M — this test is stale');
if (!/nearPolygon\(e, n, x\.ramp, RAMP_EDGE_M\)/.test(src)) {
  console.log('FAIL offsetAt does not test a ramp with nearPolygon(…, RAMP_EDGE_M)');
  process.exit(1);
}
// eslint-disable-next-line no-new-func
const { pointInPolygon, nearPolygon } = new Function(
  `${slice('pointInPolygon')}\n${slice('nearPolygon')}\nreturn { pointInPolygon, nearPolygon };`)();

const crossings = section.corner_crossings?.crossings ?? [];
if (!crossings.length) { console.log('FAIL no corner crossings in data/street_section/1904.json'); process.exit(1); }
const test = selfTest ? (e, n, poly) => pointInPolygon(e, n, poly) : (e, n, poly) => nearPolygon(e, n, poly, eps);
const missed = [];
let n = 0;
for (const x of crossings) {
  for (const [i, p] of x.ramp.entries()) {
    n += 1;
    if (!test(p[0], p[1], x.ramp)) missed.push(`${x.id} corner ${i} (${i < 2 ? 'head' : 'foot'})`);
  }
}
if (selfTest) {
  if (!missed.length) { console.log('FAIL self-test: the bare parity test caught every ramp corner, so this gate proves nothing'); process.exit(1); }
  console.log(`ok   self-test: the bare parity test misses ${missed.length} of ${n} ramp corners, which nearPolygon catches`);
  process.exit(0);
}
if (missed.length) {
  console.log(`FAIL ${missed.length} of ${n} ramp corners take the roadway's level, not the ramp's:`);
  for (const m of missed.slice(0, 20)) console.log(`  ${m}`);
  process.exit(1);
}
console.log(`ok   all ${n} ramp corners of ${crossings.length} crossings take the ramp's level (head at the curb's top)`);

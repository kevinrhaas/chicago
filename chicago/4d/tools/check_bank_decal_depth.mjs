/** T-2098: the working bank is a ground decal and must never hide the timber on it.
 * node tools/check_bank_decal_depth.mjs
 * Source contract only. Opaque, the bank wrote its slope-scaled polygon-offset depth
 * before the timber drew, and past ~30 m from a walking eye that biased depth stood
 * in front of the river walk's boards. The repair is draw ORDER (frontage.js, T-0625):
 * the bank sits in the transparent list ahead of the street ribbon and the timber and
 * writes no depth, so nothing that stands on it can lose a depth test to it.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const web = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../renderers/web/js');
const bank = await readFile(path.join(web, 'working-bank.js'), 'utf8');
const frontage = await readFile(path.join(web, 'frontage.js'), 'utf8');
const streets = await readFile(path.join(web, 'streets.js'), 'utf8');

assert.match(bank, /\n\s*mat\.transparent = true;/, 'the working bank is drawn in the transparent list');
assert.match(bank, /\n\s*mat\.depthWrite = false;/, 'the working bank writes no depth');
const bankOrder = Number(bank.match(/mesh\.renderOrder = (-?\d+);/)?.[1]);
const ribbonOrder = Number(streets.match(/mesh\.renderOrder = (-?\d+);/)?.[1]);
const timberOrders = [...frontage.matchAll(/mesh\.renderOrder = (-?\d+);/g)].map((m) => Number(m[1]));
assert.ok(Number.isFinite(bankOrder), 'the working bank sets its renderOrder');
assert.ok(bankOrder < ribbonOrder, `bank (${bankOrder}) draws before the street ribbon (${ribbonOrder})`);
assert.ok(timberOrders.length && timberOrders.every((o) => o > bankOrder),
  `bank (${bankOrder}) draws before every timber mesh (${timberOrders.join(', ')})`);
// The timber stays unbiased (T-2037's own acceptance): the bank is what changed.
assert.doesNotMatch(frontage.slice(frontage.indexOf('const mat = new THREE.MeshStandardMaterial({')),
  /^\s*polygonOffset:\s*true/m, 'the timber carries no counter-bias');
console.log(`PASS bank decal depth: bank renderOrder ${bankOrder}, ribbon ${ribbonOrder}, timber ${[...new Set(timberOrders)].join('/')}; no depth write`);

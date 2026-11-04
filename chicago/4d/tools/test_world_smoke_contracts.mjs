import assert from 'node:assert/strict';
import { STRUCTURE_BATCH_KEYS, structureBatchContract, greenTreeYardMode } from './world_smoke_contracts.mjs';
const batches = STRUCTURE_BATCH_KEYS.map((key) => ({ key, owners: ['source-owner'],
  mapped: /^(roof|wall):/.test(key), validMaterial: true }));
assert.ok(structureBatchContract(batches));
for (const invalid of [batches.slice(1), [...batches, batches[0]],
  batches.map((b, i) => i === 0 ? { ...b, key: batches[1].key } : b),
  batches.map((b) => b.mapped ? { ...b, mapped: false } : b),
  batches.map((b, i) => i === 0 ? { ...b, owners: [] } : b),
  batches.map((b, i) => i === 0 ? { ...b, validMaterial: false } : b)]) {
  assert.equal(structureBatchContract(invalid), false);
}
const closed = { enclosed: true, sheds: 0, coveredWagons: 0, ghostSpans: 0,
  refusal: true, shoulderGeometry: true };
const open = { enclosed: false, sheds: 1, coveredWagons: 1, ghostSpans: 0,
  refusal: false, shoulderGeometry: false };
assert.ok(greenTreeYardMode(closed));
assert.ok(greenTreeYardMode(open));
assert.ok(greenTreeYardMode({ ...open, enclosed: null }));
for (const mutation of [{ sheds: 1 }, { coveredWagons: 1 }, { ghostSpans: 1 },
  { refusal: false }, { shoulderGeometry: false }, { enclosed: 'true' }]) {
  assert.equal(greenTreeYardMode({ ...closed, ...mutation }), false);
}
for (const mutation of [{ sheds: 0 }, { coveredWagons: 0 }, { ghostSpans: 1 }, { refusal: true }]) {
  assert.equal(greenTreeYardMode({ ...open, ...mutation }), false);
}
console.log('world smoke contracts: exact batch key set and both yard readings pass/refute');

import assert from 'node:assert/strict';
import { STRUCTURE_BATCH_KEYS, MAPPED_BATCH, structureBatchContract, greenTreeYardMode } from './world_smoke_contracts.mjs';
const batches = STRUCTURE_BATCH_KEYS.map((key) => ({ key, owners: ['source-owner'],
  mapped: MAPPED_BATCH.test(key), validMaterial: true }));
assert.ok(structureBatchContract(batches));
// T-3411: the town's brick is ONE batch. Seven brick batches (one per GLB, as T-3387
// shipped) or a brick group drawn without its relief both refute the contract.
const brick = batches.find((b) => b.key.startsWith('brick:'));
assert.ok(brick && brick.mapped);
assert.equal(structureBatchContract([...batches, ...Array(6).fill(brick)]), false);
assert.equal(structureBatchContract(batches.filter((b) => b !== brick)), false);
// T-3341's two new source-bound reliefs each remain one mapped group, and may
// not hide in the opaque group or substitute for an existing roof/wall panel.
for (const key of ['masonry:brick', 'masonry:clay']) {
  const masonry = batches.find(b => b.key === key);
  assert.ok(masonry?.mapped);
  assert.equal(structureBatchContract(batches.filter(b => b !== masonry)), false);
  assert.equal(structureBatchContract([...batches, masonry]), false);
  assert.equal(structureBatchContract(batches.map(b => b === masonry ? { ...b, key: 'opaque' } : b)), false);
  assert.equal(structureBatchContract(batches.map(b => b === masonry ? { ...b, mapped: false } : b)), false);
}
for (const invalid of [batches.slice(1), [...batches, batches[0]],
  batches.map((b, i) => i === 0 ? { ...b, key: batches[1].key } : b),
  batches.map((b) => b.mapped ? { ...b, mapped: false } : b),
  batches.map((b) => b === brick ? { ...b, mapped: false } : b),
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

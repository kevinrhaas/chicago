import assert from 'node:assert/strict';
import { CENSUS, BREAK_IT } from './drawn_placement_census.mjs';

// Real batch-shaped buffers, with a sparse camp whose declared north-east
// plot corner is empty. The positions retain their local GLB frame; only the
// instance matrix says where the GPU draws them.
function scene({ camp = true, gap = 4, dx = 0, turn = false, missing = false } = {}) {
  const points = [[gap, 0, -1], [42, 0, -1], [42, 2, -7], [gap, 2, -7]];
  const matrices = new Float32Array(turn
    ? [0, 0, 1, 0, 0, 1, 0, 0, -1, 0, 0, 0, 342.5 + dx, 0, -27.5, 1]
    : [-1, 0, 0, 0, 0, 1, 0, 0, 0, 0, -1, 0, 342.5 + dx, 0, -27.5, 1]);
  const batch = {
    geometry: { index: null, getAttribute: () => ({
      getX: i => points[i][0], getY: i => points[i][1], getZ: i => points[i][2],
    }) },
    _matricesTexture: { image: { data: matrices } },
    _instanceInfo: [{ geometryIndex: 0 }],
    _geometryInfo: [{ start: 0, count: points.length }],
    userData: { batchIndex: ['fixture'] },
  };
  globalThis.window = { __chicago4d: {
    buildings: { batches: [batch] },
    registry: new Map([['fixture', { sidecar: {
      archetype: camp ? 'camp' : 'masonry_house',
      placement: missing ? null : { local_e: 342.5, local_n: 27.5, rotation_deg: 180 },
    } }]]),
    streets: { records: [], group: { traverse() {} } },
  } };
}

scene();
let b = CENSUS().buildings;
assert.equal(b.compared, 1);
assert.equal(b.verts, 4);
assert.equal(b.compounds, 1);
assert.ok(b.worst > 4, 'the empty plot corner really is outside the drawn body');
assert.equal(b.outside, 0);
assert.equal(b.misplaced, 0);

scene({ dx: 0.02 });
assert.equal(CENSUS().buildings.misplaced, 1, 'a two-centimetre camp displacement fails');
scene({ turn: true });
assert.equal(CENSUS().buildings.misplaced, 1, 'wrong rotation fails with the correct origin');
scene();
BREAK_IT();
b = CENSUS().buildings;
assert.equal(b.misplaced, 1, 'the original northing mirror fault still fails');
assert.equal(b.mirrorCloser, 1);

scene({ camp: false });
assert.equal(CENSUS().buildings.outside, 1, 'buildings retain the occupied-corner bar');
scene({ camp: false, gap: 0 });
b = CENSUS().buildings;
assert.equal(b.outside, 0);
assert.equal(b.misplaced, 0);
scene({ camp: false, gap: 0, dx: 0.02 });
assert.equal(CENSUS().buildings.misplaced, 1, 'the stronger transform check covers buildings too');
scene({ missing: true });
assert.equal(CENSUS().buildings.unrecorded, 1, 'missing provenance cannot pass');
delete globalThis.window;
console.log('drawn placement: sparse plot passes; displacement, rotation, mirror and missing placement fail');

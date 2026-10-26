import assert from 'node:assert/strict';
import { CENSUS, BREAK_IT } from './drawn_placement_census.mjs';

// Real batch-shaped buffers, with a sparse camp whose declared north-east
// plot corner is empty. The positions retain their local GLB frame; only the
// instance matrix says where the GPU draws them.
function scene({ camp = true, gap = 4, dx = 0, turn = false, missing = false, footprint = null, bearing = 180 } = {}) {
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
      ...(footprint ? { footprint: { polygon: footprint } } : {}),
      placement: missing ? null : { local_e: 342.5, local_n: 27.5, rotation_deg: bearing },
    } }]]),
    streets: { records: [], group: { traverse() {} } },
  } };
}

scene();
let b = CENSUS().buildings;
assert.equal(b.compared, 1);
assert.equal(b.verts, 4);
assert.equal(b.compounds, 1);
assert.ok(b.campWorst > 4, 'the empty plot corner really is outside the drawn body');
assert.equal(b.worst, 0, 'and an exempt camp is never named as the worst stray (T-3174)');
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
// T-3174: a body drawn inside a footprint that is inset from its origin (the
// 1832 lighthouse) is drawn around the anchor its record gives it. The fixture
// turns 180 degrees, so a wrong sign on either footprint axis misses by metres.
scene({ camp: false, footprint: [[4, 1], [42, 1], [42, 7], [4, 7]] });
b = CENSUS().buildings;
assert.equal(b.outside, 0, 'an inset footprint drawn where it is recorded passes');
assert.ok(b.worst < 1e-3);
scene({ camp: false, footprint: [[4, 10], [42, 10], [42, 16], [4, 16]] });
b = CENSUS().buildings;
assert.equal(b.outside, 1, 'a body drawn off its recorded footprint still fails');
assert.equal(b.worstId, 'fixture');
scene({ missing: true });
assert.equal(CENSUS().buildings.unrecorded, 1, 'missing provenance cannot pass');
// The DATA plan has an offset origin, independently of the hand-authored
// GPU positions above. Rotation180 places its centroid at(320.86,23.5).
const offsetPlan = [[1.28, 1], [42, 1], [42, 7], [1.28, 7]];
scene({ camp: false, gap: 1.28, footprint: offsetPlan });
b = CENSUS().buildings;
assert.equal(b.outside, 0, 'an explicit offset footprint is occupied despite its empty origin');
assert.equal(b.misplaced, 0);
scene({ camp: false, gap: 1.28, footprint: offsetPlan, turn: true, bearing: 90 });
b = CENSUS().buildings;
assert.equal(b.outside, 0, 'the independent record reference follows a right-angle bearing');
assert.equal(b.misplaced, 0);
scene({ camp: false, gap: 1.28, footprint: offsetPlan, dx: 0.02 });
assert.equal(CENSUS().buildings.misplaced, 1, 'offset origins do not excuse a two-centimetre translation');
scene({ camp: false, gap: 1.28, footprint: offsetPlan, turn: true });
assert.equal(CENSUS().buildings.misplaced, 1, 'offset origins do not excuse wrong rotation');
scene({ camp: false, gap: 1.28, footprint: offsetPlan });
BREAK_IT();
b = CENSUS().buildings;
assert.equal(b.misplaced, 1, 'offset origins do not excuse mirrored GPU placement');
assert.equal(b.mirrorCloser, 1);
scene({ camp: false, gap: 1.28, footprint: [[100, 1], [110, 1], [110, 7], [100, 7]] });
assert.equal(CENSUS().buildings.outside, 1, 'a wrong DATA footprint cannot use the GPU bounds as its own reference');
delete globalThis.window;
console.log('drawn placement: sparse plot and declared offset plan pass; displacement, rotation, mirror, wrong footprint and missing placement fail');

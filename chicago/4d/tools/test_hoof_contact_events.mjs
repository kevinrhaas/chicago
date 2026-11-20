import test from 'node:test';
import assert from 'node:assert/strict';
import { createHoofContactEvents, WALK_V2_CONTACTS as C } from '../renderers/web/js/hoof-contact-events.js';
const positions = Object.fromEntries(C.contacts.map(c => [c.foot, { x: 0, y: 0, z: 0 }]));
const horse = (distanceM, id = 'left') => ({ id, distanceM, clipSha256: C.clipSha256,
  modelSha256: C.modelSha256, strideM: C.strideM, hooves: positions });
const actor = (distanceM, extra = {}) => ({ id: 'wagon', epoch: 'spawn-1', eligible: true,
  horses: [horse(distanceM)], ...extra });
const tick = (engine, distanceM, nowMs, extra = {}) => engine.sync({ enabled: true,
  scope: '1835|1835-07-01', nowMs, actors: [actor(distanceM)], ...extra });
test('first observation is silent; exact boundary emits once; wrap uses real accumulated distance', () => {
  const e = createHoofContactEvents();
  assert.deepEqual(tick(e, .2, 0), []);
  assert.equal(tick(e, C.contacts[0].phase, 16)[0].foot, 'fore_l');
  assert.deepEqual(tick(e, C.contacts[0].phase, 32), []);
  e.reset(); tick(e, .95, 40);
  assert.equal(tick(e, 1.02, 56)[0].foot, 'hind_l');
  assert.deepEqual(tick(e, 1.03, 72), []);
});
test('every hold, missing/cull and late sample readiness resumes with a baseline only', () => {
  for (const input of [{ enabled: false }, { actors: [] }, { actors: [actor(.3, { eligible: false })] }]) {
    const e = createHoofContactEvents(); tick(e, .2, 0);
    assert.deepEqual(tick(e, .3, 16, input), []);
    assert.deepEqual(tick(e, .47, 32), []);
    assert.deepEqual(tick(e, .49, 48), []);
  }
});
test('scope/era/date changes, epoch replacement, teleport, backwards distance and long gaps never replay', () => {
  const cases = [
    [ .22, 16, { scope: '1904|1904-07-01' } ],
    [ .22, 16, { actors: [actor(.22, { epoch: 'teleport-2' })] } ],
    [ 9.22, 16, {} ], [ .1, 16, {} ], [ .22, 126, {} ], [ .22, -1, {} ],
  ];
  for (const [distance, time, extra] of cases) {
    const e = createHoofContactEvents(); tick(e, .2, 0);
    assert.deepEqual(tick(e, distance, time, extra), []);
  }
});
test('two horses keep their own accepted distances, without a second beat clock', () => {
  const e = createHoofContactEvents();
  tick(e, 0, 0, { actors: [actor(0, { horses: [horse(.2, 'left'), horse(.4, 'right')] })] });
  const rows = tick(e, 0, 16, { actors: [actor(0, { horses: [horse(.22, 'left'), horse(.42, 'right')] })] });
  assert.deepEqual(rows.map(r => [r.horse, r.foot]), [['left', 'fore_l']]);
});
test('old contacts are dropped within an otherwise admitted frame', () => {
  const e = createHoofContactEvents(); tick(e, .214, 0);
  assert.deepEqual(tick(e, .3, 100), []);
  assert.equal(e.state.queuedEvents, 0);
});
test('invalid model/clip/support positions and duplicate identities do not create contacts', () => {
  for (const bad of [{ clipSha256: 'wrong' }, { modelSha256: 'wrong' }, { strideM: .135 },
    { distanceM: NaN }, { hooves: {} }]) {
    const e = createHoofContactEvents(); tick(e, .2, 0);
    assert.deepEqual(tick(e, .22, 16, { actors: [actor(.22, { horses: [{ ...horse(.22), ...bad }] })] }), []);
  }
  const e = createHoofContactEvents(); tick(e, .2, 0);
  assert.equal(tick(e, .22, 16, { actors: [actor(.22, { horses: [horse(.22), horse(.22)] })] }).length, 1);
});
test('four-horse bound and disposal hold under oversized actor input', () => {
  const e = createHoofContactEvents();
  const actors = d => Array.from({ length: 100 }, (_, i) => actor(d, { id: `wagon-${i}`,
    horses: [horse(d, 'left'), horse(d, 'right'), horse(d, 'third')] }));
  tick(e, 0, 0, { actors: actors(.2) });
  assert.equal(tick(e, 0, 16, { actors: actors(.22) }).length, 4);
  assert.equal(e.state.trackedHorses, 4);
  e.dispose(); assert.deepEqual(tick(e, .47, 32), []);
  assert.equal(e.state.trackedHorses, 0);
});

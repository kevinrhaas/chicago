import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {floraReview, FLORA_RENDERER_SOURCES} from './photo_match_flora.mjs';

/** T-1881: a picture's planting binds the lots and parkway trees drawn, their renderers and the anchor. */
export function testFloraReviews() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'photo-flora-test-'));
  const write = (file, content) => {
    const p = path.join(root, file); fs.mkdirSync(path.dirname(p), {recursive: true});
    fs.writeFileSync(p, typeof content === 'string' ? content : JSON.stringify(content));
  };
  const camera = {structure_id: 'anchor', scene: '1904',
    flora: {front_yards: ['prairie_1729'], street_trees_m: 50, season: 'spring'}};
  const anchor = {id: 'anchor', scene: '1904', target_date: '1904-07-01', phase: 'standing',
    placement: {local_e: 100, local_n: 200, rotation_deg: 90}};
  const yards = {lots: [{parcel: 'prairie_1729', shrubs: [[101, 201, 'lilac', 2, 2]], trees: [], beds: [],
    creeper: [[102, 202, 270, 1.4, 5]]}, {parcel: 'prairie_1801', shrubs: [], trees: [], beds: [], creeper: []}]};
  const trees = {trees: [{id: 'near', e: 120, n: 200}, {id: 'far', e: 400, n: 200}]};
  try {
    write('data/scenes/1904.json', {id: '1904', target_date: '1904-07-01'});
    write('data/sidecars/1904/anchor.json', anchor);
    write('data/front_yards/1904.json', yards);
    write('data/street_trees/1904.json', trees);
    for (const file of FLORA_RENDERER_SOURCES) write(file, 'fixture renderer: ' + file);
    assert.equal(floraReview(root, {structure_id: 'anchor'}), null);
    const before = floraReview(root, camera);
    assert.deepEqual(before.docs.front_yards.lots.map(l => l.parcel), ['prairie_1729'], 'only the named lot is drawn');
    assert.deepEqual(before.docs.street_trees.trees.map(t => t.id), ['near'], 'only the parkway trees in reach');
    assert.equal(before.review.flora_sha256, floraReview(root, camera).review.flora_sha256);
    const changed = (why) => assert.notEqual(before.review.flora_sha256, floraReview(root, camera).review.flora_sha256, why);
    yards.lots[0].creeper[0][4] = 6; write('data/front_yards/1904.json', yards);
    changed('regrowing the lot’s ivy invalidates the review');
    yards.lots[0].creeper[0][4] = 5; write('data/front_yards/1904.json', yards);
    trees.trees[0].e = 121; write('data/street_trees/1904.json', trees);
    changed('moving a parkway tree in reach invalidates the review');
    trees.trees[0].e = 120; write('data/street_trees/1904.json', trees);
    trees.trees[1].e = 401; write('data/street_trees/1904.json', trees);
    assert.equal(before.review.flora_sha256, floraReview(root, camera).review.flora_sha256,
      'a tree out of reach does not');
    anchor.placement.local_n++; write('data/sidecars/1904/anchor.json', anchor);
    changed('moving the anchor invalidates plants placed in its frame');
    anchor.placement.local_n--; write('data/sidecars/1904/anchor.json', anchor);
    write(FLORA_RENDERER_SOURCES[2], 'regrown front yards');
    changed('changing a plant renderer invalidates the review');
    assert.throws(() => floraReview(root, {...camera, flora: {...camera.flora, season: 'monsoon'}}), /season is one of/);
    assert.throws(() => floraReview(root, {...camera, flora: {...camera.flora, front_yards: ['prairie_9999']}}), /no such lot/);
    assert.throws(() => floraReview(root, {...camera, flora: {...camera.flora, front_yards: ['a', 'a']}}), /distinct lot/);
    assert.throws(() => floraReview(root, {...camera, flora: {season: 'summer'}}), /names front_yards/);
    assert.throws(() => floraReview(root, {...camera, flora: {...camera.flora, street_trees_m: 900}}), /radius/);
    assert.throws(() => floraReview(root, {...camera, flora: {...camera.flora, extra: 1}}), /flora takes/);
    assert.throws(() => floraReview(root, {...camera, scene: undefined}), /explicit scene/);
    console.log('ok   picture planting review: named lots and reachable parkway trees, renderer/anchor freshness, refusals');
  } finally { fs.rmSync(root, {recursive: true, force: true}); }
}
if (import.meta.url === `file://${process.argv[1]}`) testFloraReviews();

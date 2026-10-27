import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {enclosureReview, ENCLOSURE_RENDERER_SOURCES} from './photo_match_enclosures.mjs';

export function testEnclosureReviews() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'photo-enclosure-test-'));
  const write = (file, content) => {
    const p = path.join(root, file); fs.mkdirSync(path.dirname(p), {recursive: true});
    fs.writeFileSync(p, typeof content === 'string' ? content : JSON.stringify(content));
  };
  const camera = {structure_id: 'anchor', scene: '1835', enclosures: ['palisade']};
  const anchor = {id: 'anchor', scene: '1835', target_date: '1835-07-01', phase: 'standing',
    placement: {local_e: 100, local_n: 200, rotation_deg: 90}};
  const record = {id: 'palisade', scene: '1835', target_date: '1835-07-01', structure_id: 'anchor',
    documented_range: {from: '1833-10-01', to: '1835-12-31'},
    runs: [{id: 'north', path_local_enu_m: [[100, 200], [108, 200]]}],
    form: {fence_type: {value: 'board'}, height_m: {value: 3.05}}};
  try {
    write('data/scenes/1835.json', {id: '1835', target_date: '1835-07-01'});
    write('data/sidecars/1835/anchor.json', anchor);
    write('data/enclosures/index.json', {enclosures: [{id: 'palisade', file: 'palisade.json'}]});
    write('data/enclosures/palisade.json', record);
    for (const file of ENCLOSURE_RENDERER_SOURCES) write(file, 'fixture renderer: ' + file);
    assert.equal(enclosureReview(root, {structure_id: 'anchor'}), null);
    assert.equal(enclosureReview(root, {enclosures: []}), null);
    const before = enclosureReview(root, camera);
    assert.equal(before.records.length, 1); assert.deepEqual(before.anchor, {...anchor.placement,
      scene: '1835', target_date: '1835-07-01', phase: 'standing'});
    assert.equal(before.review.enclosures_sha256, enclosureReview(root, camera).review.enclosures_sha256);
    record.form.height_m.value = 3.2; write('data/enclosures/palisade.json', record);
    assert.notEqual(before.review.enclosures_sha256, enclosureReview(root, camera).review.enclosures_sha256,
      'changing a native fence input invalidates its review');
    record.form.height_m.value = 3.05; write('data/enclosures/palisade.json', record);
    anchor.placement.local_e++; write('data/sidecars/1835/anchor.json', anchor);
    assert.notEqual(before.review.enclosures_sha256, enclosureReview(root, camera).review.enclosures_sha256,
      'moving the anchor invalidates a fence placed in its frame');
    anchor.placement.local_e--; write('data/sidecars/1835/anchor.json', anchor);
    write(ENCLOSURE_RENDERER_SOURCES[0], 'rebuilt native fence geometry');
    assert.notEqual(before.review.enclosures_sha256, enclosureReview(root, camera).review.enclosures_sha256,
      'changing the native renderer invalidates its review');
    for (const ids of [['palisade', 'palisade'], ['../palisade'], 'palisade'])
      assert.throws(() => enclosureReview(root, {...camera, enclosures: ids}), /distinct enclosure ids/);
    assert.throws(() => enclosureReview(root, {...camera, scene: undefined}), /explicit scene/);
    assert.throws(() => enclosureReview(root, {...camera, enclosures: ['absent']}), /absent from the native manifest/);
    record.target_date = '1836-07-01'; write('data/enclosures/palisade.json', record);
    assert.throws(() => enclosureReview(root, camera), /wrong-scene\/date/);
    record.target_date = '1835-07-01'; record.structure_id = 'another_house';
    write('data/enclosures/palisade.json', record);
    assert.throws(() => enclosureReview(root, camera), /does not belong/);
    record.structure_id = 'anchor'; record.runs[0].path_local_enu_m[0][0] = null;
    write('data/enclosures/palisade.json', record);
    assert.throws(() => enclosureReview(root, camera), /finite native run/);
    fs.unlinkSync(path.join(root, 'data/enclosures/palisade.json'));
    assert.throws(() => enclosureReview(root, camera), /ENOENT/);
    console.log('ok   native enclosure review: selected source/anchor/renderer freshness and missing/wrong-date/owner refusals');
  } finally { fs.rmSync(root, {recursive: true, force: true}); }
}
if (import.meta.url === `file://${process.argv[1]}`) testEnclosureReviews();

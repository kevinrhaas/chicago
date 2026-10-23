import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {renderGroup, groupReview} from './photo_match_group.mjs';

export function testRenderGroups() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'photo-group-test-'));
  const write = (file, content) => {
    const dest = path.join(root, file);
    fs.mkdirSync(path.dirname(dest), {recursive: true});
    fs.writeFileSync(dest, typeof content === 'string' ? content : JSON.stringify(content));
  };
  const camera = {structure_id: 'anchor', scene: '1835', also_render: ['barracks']};
  const member = {id: 'barracks', scene: '1835', target_date: '1835-07-01',
    phase: 'standing', asset: 'gltf/barracks.glb',
    placement: {local_e: 110, local_n: 220, rotation_deg: 0}};
  const anchor = {...member, id: 'anchor', asset: 'gltf/anchor.glb',
    placement: {local_e: 100, local_n: 200, rotation_deg: 90}};
  try {
    write('data/scenes/1835.json', {id: '1835', target_date: '1835-07-01'});
    write('data/sidecars/1835/anchor.json', anchor);
    write('data/sidecars/1835/barracks.json', member);
    write('assets/gltf/anchor.glb', 'anchor'); write('assets/gltf/barracks.glb', 'barracks');
    write('assets/manifest.json', {assets: {'anchor.glb': {structure_id: 'anchor'}}});
    const members = renderGroup(root, camera);
    assert.equal(members.length, 2);
    assert(members[0].position.every(v => v === 0));
    // A scene point 10 m east and 20 m north, viewed in a 90-degree anchor frame.
    assert(Math.abs(members[1].position[0] + 20) < 1e-9);
    assert(Math.abs(members[1].position[2] + 10) < 1e-9);
    assert.equal(members[1].rotation_y, Math.PI / 2);
    const original = groupReview(root, members);
    assert.equal(groupReview(root, renderGroup(root, camera)).group_sha256, original.group_sha256);
    write('assets/gltf/barracks.glb', 'rebuilt barracks');
    assert.notEqual(groupReview(root, renderGroup(root, camera)).group_sha256, original.group_sha256);
    write('assets/gltf/barracks.glb', 'barracks');
    member.placement.local_e++;
    write('data/sidecars/1835/barracks.json', member);
    assert.notEqual(groupReview(root, renderGroup(root, camera)).group_sha256, original.group_sha256);
    member.placement.local_e--; write('data/sidecars/1835/barracks.json', member);
    anchor.placement.rotation_deg = 0; write('data/sidecars/1835/anchor.json', anchor);
    const north = renderGroup(root, camera)[1];
    assert.deepEqual(north.position, [10, 0, -20]); assert.equal(north.rotation_y, 0);
    assert.notEqual(groupReview(root, renderGroup(root, camera)).group_sha256, original.group_sha256);
    assert.equal(renderGroup(root, {structure_id: 'anchor'})[0].glb, 'assets/gltf/anchor.glb');
    assert.equal(renderGroup(root, camera, {glb: 'assets/gltf/barracks.glb'})[0].glb,
      'assets/gltf/barracks.glb');
    for (const extra of [['anchor'], ['barracks', 'barracks'], ['../barracks'], 'barracks'])
      assert.throws(() => renderGroup(root, {...camera, also_render: extra}));
    assert.throws(() => renderGroup(root, {...camera, scene: undefined}), /explicit scene/);
    assert.throws(() => renderGroup(root, {...camera, also_render: ['absent']}), /absent from scene/);
    member.target_date = '1812-08-14'; write('data/sidecars/1835/barracks.json', member);
    assert.throws(() => renderGroup(root, camera), /stale or wrong-scene/);
    member.target_date = '1835-07-01'; member.placement.local_e = null;
    write('data/sidecars/1835/barracks.json', member);
    assert.throws(() => renderGroup(root, camera), /finite scene placement/);
    member.placement.local_e = 110; write('data/sidecars/1835/barracks.json', member);
    fs.unlinkSync(path.join(root, 'assets/gltf/barracks.glb'));
    assert.throws(() => renderGroup(root, camera), /missing GLB/);
    console.log('ok   image gate self-test: group bearings, phase selection, dependency hashes and missing-member refusals');
  } finally { fs.rmSync(root, {recursive: true, force: true}); }
}
if (import.meta.url === `file://${process.argv[1]}`) testRenderGroups();

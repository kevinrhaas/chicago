/** T-3226: a coursed wall's mortar floor is drawn behind the stone faces that lie on it.
 * node tools/check_joint_floor.mjs [--self-test]
 * Source contract plus the shipped files. K02's `stone()` lays a `mortar` floor under each
 * stone's whole cell, its fabric's joint recess (1 to 6 mm) behind the face; the 14-bit web
 * derivative rounds that recess onto the face, and past ~50 m a 24-bit depth buffer cannot
 * part it anyway, so the floor and the face fought (1827 and 1801 Prairie, 2026-10-28).
 * buildings.js now gives the floor a depth offset away from the eye. This requires:
 *   - JOINT_FLOOR names `mortar` and pushes AWAY (factor and units both positive),
 *   - seatJointFloor runs in the load loop after the material is chosen and before the
 *     batch key is taken, and the key carries the offset, so a floor never shares a batch
 *     (or a GL state) with an un-offset surface,
 *   - every shipped web GLB that names a `mortar` material is one the K02 writer or
 *     Glessner's own builder made, so the name still means what the contract says.
 * `--self-test` feeds it the pre-T-3226 source and requires the check to refuse it.
 */
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const src = await readFile(path.join(APP, 'renderers/web/js/buildings.js'), 'utf8');

function check(s) {
  const spec = s.match(/export const JOINT_FLOOR = Object\.freeze\(\{ names: Object\.freeze\((\[[^\]]*\])\), factor: ([\d.]+), units: ([\d.]+) \}\);/);
  assert.ok(spec, 'buildings.js states JOINT_FLOOR (names, factor, units)');
  assert.deepEqual(JSON.parse(spec[1].replace(/'/g, '"')), ['mortar'], 'the joint floor is the material named mortar');
  assert.ok(Number(spec[2]) > 0 && Number(spec[3]) > 0, 'the floor is pushed away from the eye, never toward it');
  const seat = s.match(/export function seatJointFloor\(material\) \{([\s\S]*?)\n\}/)?.[1] ?? '';
  for (const k of ['polygonOffset = true', 'polygonOffsetFactor = JOINT_FLOOR.factor', 'polygonOffsetUnits = JOINT_FLOOR.units']) {
    assert.ok(seat.includes(k), `seatJointFloor sets ${k}`);
  }
  const loop = s.slice(s.indexOf('for (const { mesh, matrix } of meshes)'));
  const call = loop.indexOf('seatJointFloor(material);');
  const key = loop.indexOf('const key = preserveMaterials ? inspectionMaterialKey(material) : materialKey(material);');
  const chosen = loop.indexOf('let material = preserveMaterials ? sourceMaterial.clone() : sourceMaterial;');
  assert.ok(call > 0 && key > 0 && chosen > 0, 'the load loop seats the floor, chooses the material and takes the key');
  assert.ok(chosen < call && call < key, 'the floor is seated on the material being batched, before its batch key is taken');
  const mk = s.slice(s.indexOf('function materialKey(m) {'));
  const body = mk.slice(0, mk.indexOf('\n}\n'));
  assert.match(body, /m\.polygonOffset/, 'materialKey separates an offset material from an un-offset one');
}

async function shippedNames() {
  const dir = path.join(APP, 'assets/web');
  const out = [];
  for (const f of (await readdir(dir)).filter((x) => x.endsWith('.glb'))) {
    const b = await readFile(path.join(dir, f));
    const j = JSON.parse(b.subarray(20, 20 + b.readUInt32LE(12)).toString());
    if ((j.materials ?? []).some((m) => m.name === 'mortar')) out.push(f);
  }
  return out;
}

if (process.argv.includes('--self-test')) {
  const before = src.replace(/\n      seatJointFloor\(material\);/, '');
  assert.notEqual(before, src, 'self-test: the call was found to remove');
  assert.throws(() => check(before), /seats the floor/, 'self-test: a loop that never seats the floor is refused');
  const toward = src.replace(/factor: ([\d.]+), units: ([\d.]+) \}/, 'factor: -1, units: -4 }');
  assert.throws(() => check(toward), /states JOINT_FLOOR|pushed away/, 'self-test: a floor pulled toward the eye is refused');
  const unkeyed = src.replace("const offset = m.polygonOffset ? `${m.polygonOffsetFactor}/${m.polygonOffsetUnits}` : '-';", "const offset = '-';");
  assert.notEqual(unkeyed, src, 'self-test: the key line was found');
  assert.throws(() => check(unkeyed), /separates an offset material/, 'self-test: a key blind to the offset is refused');
  console.log('PASS self-test: the joint-floor check refuses a missing seat, a forward offset and a blind batch key');
} else {
  check(src);
  const files = await shippedNames();
  const writers = /^(glessner_house__|.*__as_(mapped_1904|built_18\d\d)(\.light)?\.glb$)/;
  const strays = files.filter((f) => !writers.test(f));
  assert.deepEqual(strays, [], `a mortar material outside the K02 houses and Glessner: ${strays.join(', ')}`);
  console.log(`PASS joint floor: mortar drawn behind its stones (factor ${src.match(/factor: ([\d.]+)/)[1]}, units ${src.match(/units: ([\d.]+)/)[1]}) on ${files.length} shipped houses`);
}

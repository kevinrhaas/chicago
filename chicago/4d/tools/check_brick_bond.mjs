/** T-3295: the renderer's K03 brick bonds are the library's.
 * node tools/check_brick_bond.mjs [--self-test]
 * `renderers/web/js/brick-bond.js` draws each brick of a K03 panel from another brick of its
 * kind, so it has to know where the bricks are: the panel's bond (each course's offset and
 * unit), its repeat and its joint. It restates them, because a renderer does not read the
 * generators' data. This holds the restatement to the library:
 *   - MODULE_M and COURSE_M are profiles.json's module,
 *   - every panel in profiles.json is either shuffled (PANELS) or named in NOT_SHUFFLED with
 *     a reason, and every shuffled panel's bond, modules, courses and joint are its
 *     material.json's; every shuffled bond is profiles.json's, course for course,
 *   - every panel a shipped web GLB wears as a base colour (`<panel>_basecolor`) is shuffled,
 *   - each panel's uniforms swap a brick only with a brick of its own length,
 *   - buildings.js binds it in the load loop before the batch key is taken.
 * `--self-test` feeds it a bond with one course moved and a loop that never binds, and
 * requires both refused.
 */
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const APP = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const LIB = path.join(APP, 'assets/textures/prairie_1904_brick');
const SRC = await readFile(path.join(APP, 'renderers/web/js/brick-bond.js'), 'utf8');
const BUILDINGS = await readFile(path.join(APP, 'renderers/web/js/buildings.js'), 'utf8');
const profiles = JSON.parse(await readFile(path.join(LIB, 'profiles.json'), 'utf8'));

/** The module under node: its three imports stubbed (only its tables are read here). */
async function load(src) {
  const prelude = "const ShaderChunk = { normal_fragment_maps: 'texture2D( normalMap, vNormalMapUv )' };\n"
    + 'const captureHooks = () => null, registerPatch = () => {}, programKeyOf = () => "";\n';
  const body = src.replace(/^import .*$/mg, '');
  return import(`data:text/javascript,${encodeURIComponent(prelude + body)}`);
}

async function shippedPanels() {
  const dir = path.join(APP, 'assets/web');
  const out = new Set();
  for (const f of (await readdir(dir)).filter((x) => x.endsWith('.glb'))) {
    const b = await readFile(path.join(dir, f));
    const j = JSON.parse(b.subarray(20, 20 + b.readUInt32LE(12)).toString());
    for (const img of j.images ?? []) {
      const m = /^(.*)_basecolor$/.exec(img.name ?? '');
      if (m && profiles.panels.some((p) => p.id === m[1])) out.add(m[1]);
    }
  }
  return out;
}

async function check(src, buildings, shipped) {
  const mod = await load(src);
  assert.equal(mod.MODULE_M, profiles.module.length_m, 'MODULE_M is profiles.json\'s module length');
  assert.equal(mod.COURSE_M, profiles.module.course_m, 'COURSE_M is profiles.json\'s course');
  const unit = profiles.unit_modules;
  for (const p of profiles.panels) {
    const shuffled = mod.PANELS[p.id];
    if (!shuffled) {
      assert.ok(mod.NOT_SHUFFLED[p.id], `${p.id}: neither shuffled nor named in NOT_SHUFFLED with a reason`);
      continue;
    }
    const mat = JSON.parse(await readFile(path.join(LIB, 'panel', p.id, 'material.json'), 'utf8'));
    assert.equal(shuffled.bond, mat.bond, `${p.id}: bond is material.json's (${mat.bond})`);
    assert.equal(shuffled.modules, mat.repeat.modules, `${p.id}: modules are material.json's`);
    assert.equal(shuffled.courses, mat.repeat.courses, `${p.id}: courses are material.json's`);
    assert.equal(shuffled.joint_m, mat.joint.width_m, `${p.id}: joint is material.json's`);
    const tile = [mat.tile_m[0] / mat.repeat.modules, mat.tile_m[1] / mat.repeat.courses];
    assert.ok(Math.abs(tile[0] - mod.MODULE_M) < 1e-4 && Math.abs(tile[1] - mod.COURSE_M) < 1e-4,
      `${p.id}: its tile is whole modules and courses of the module brick-bond.js states`);
    const want = profiles.bonds[mat.bond].courses.map((c) => {
      assert.equal(new Set(c.units).size, 1, `${p.id}: a ${mat.bond} course mixes units, which the shuffle cannot read`);
      return [c.offset_modules, unit[c.units[0]]];
    });
    assert.deepEqual(mod.BONDS[mat.bond].map((r) => [...r]), want, `${p.id}: the ${mat.bond} bond is profiles.json's, course for course`);
    const u = mod.bondUniforms(p.id);
    const list = u.list.flat();
    for (let ci = 0; ci < shuffled.courses; ci++) {
      const [, len, start, count] = u.course[ci];
      assert.ok(count > 0, `${p.id}: course ${ci} has somewhere to swap to`);
      for (let i = start; i < start + count; i++) {
        assert.equal(u.course[list[i]][1], len, `${p.id}: course ${ci} swaps only with courses of its own unit length`);
      }
    }
  }
  for (const id of shipped) assert.ok(mod.PANELS[id], `${id}: a shipped GLB wears it and brick-bond.js does not shuffle it`);
  const loop = buildings.slice(buildings.indexOf('for (const { mesh, matrix } of meshes)'));
  const call = loop.indexOf('applyBrickBond(material');
  const key = loop.indexOf('const key = preserveMaterials ? inspectionMaterialKey(material) : materialKey(material);');
  assert.ok(call > 0 && key > call, 'buildings.js binds the shuffle in the load loop before the batch key is taken');
}

const shipped = await shippedPanels();
if (process.argv.includes('--self-test')) {
  const moved = SRC.replace('[0.0, S], [0.5, S], [0.0, S], [0.5, S], [0.0, S], [0.0, H],',
    '[0.0, S], [0.5, S], [0.0, S], [0.5, S], [0.5, S], [0.0, H],');
  assert.notEqual(moved, SRC, 'self-test: the common_6 row was found to move');
  await assert.rejects(check(moved, BUILDINGS, shipped), /course for course/, 'self-test: a moved course is refused');
  const unbound = BUILDINGS.replace(/applyBrickBond\(material/g, 'void (material');
  await assert.rejects(check(SRC, unbound, shipped), /before the batch key/, 'self-test: a loop that never binds is refused');
  console.log('OK self-test: a moved course and an unbound loop are both refused');
} else {
  await check(SRC, BUILDINGS, shipped);
  console.log(`OK: brick-bond.js shuffles ${Object.keys((await load(SRC)).PANELS).length} panels as profiles.json lays them; shipped: ${[...shipped].sort().join(', ')}`);
}

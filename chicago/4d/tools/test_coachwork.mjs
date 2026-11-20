// SPDX-License-Identifier: GPL-3.0-or-later
// Kevin, 2026-11-13: each 1904 carriage its own (renderers/web/js/coachwork.js). On the
// real brougham's node and material names it must: give every mesh its own material, so one
// coach's paint never reaches another's; paint the panels, the body's timber and the running
// gear (wheels, pole) each in the row's colour; leave glass and the inside unmarked; splice
// into three's own standard shader with a program key that names the chain and is the same
// for every coach (uniforms differ, the program is one); place its marks by its own seed;
// and give back the loaded materials on dispose. And every finish loops.json carries is valid.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const threeURL = new URL('renderers/web/vendor/three-0.185.1/three.module.js', here).href;
const THREE = await import(threeURL);
const data = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const source = (await fs.readFile(new URL('renderers/web/js/coachwork.js', here), 'utf8')).replace("from 'three'", `from '${threeURL}'`);
const { applyCoachwork, readFinish, seedOffsets } = await import(data(source));

// The brougham's own node tree and materials, read from the GLB the 1904 rows drive.
const loops = JSON.parse(await fs.readFile(new URL('data/transport/driven/loops.json', here), 'utf8'));
const rows = loops.rows.filter(r => r.scene === '1904');
const glb = await fs.readFile(new URL(`renderers/web/${rows[0].vehicle_file}`, here));
const json = JSON.parse(glb.subarray(20, 20 + glb.readUInt32LE(12)));
function brougham() {
  const materials = json.materials.map(m => Object.assign(new THREE.MeshStandardMaterial({
    color: new THREE.Color().setRGB(...m.pbrMetallicRoughness.baseColorFactor.slice(0, 3), THREE.LinearSRGBColorSpace) }), { name: m.name }));
  const build = index => {
    const n = json.nodes[index], node = new THREE.Group();
    node.name = n.name ?? '';
    if (n.translation) node.position.fromArray(n.translation);
    if (n.rotation) node.quaternion.fromArray(n.rotation);
    if (n.mesh != null) for (const p of json.meshes[n.mesh].primitives) {
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(.1, .1, .1), materials[p.material]); mesh.name = `${node.name}:${p.material}`;
      node.add(mesh);
    }
    for (const c of n.children ?? []) node.add(build(c));
    return node;
  };
  const scene = new THREE.Group();
  for (const i of json.scenes[0].nodes) scene.add(build(i));
  return { scene, materials };
}

// Every finish the rows carry reads, and every brougham material has a role.
for (const row of rows) assert(row.vehicle_finish, `${row.id} has its own finish`), readFinish(row.vehicle_finish);
assert.equal(new Set(rows.map(r => r.vehicle_finish.seed)).size, rows.length, 'every coach its own seed');
assert.throws(() => readFinish({ seed: 'x', panels: [2, 0, 0] }), /linear channels/);
assert.throws(() => readFinish({ seed: 'x', varnish: 1 }), /unknown finish key/);
assert.throws(() => readFinish({ panels: [0, 0, 0] }), /seed/);
assert.deepEqual(seedOffsets('a'), seedOffsets('a'));
assert.notDeepEqual(seedOffsets('pullman-brougham-1904'), seedOffsets('armour-brougham-1904'));

const shader = () => ({ uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader, fragmentShader: THREE.ShaderLib.standard.fragmentShader });
const keys = new Set();
const north = rows.find(r => r.id.includes('north')).vehicle_finish;
for (const row of rows) {
  const { scene, materials } = brougham();
  const meshes = []; scene.traverse(o => { if (o.isMesh) meshes.push(o); });
  const loaded = new Map(meshes.map(m => [m, m.material]));
  const work = applyCoachwork(scene, row.vehicle_finish, { wheelRadius_m: row.wheel_radii_m[0] });
  assert.equal(new Set(meshes.map(m => m.material)).size, meshes.length, `${row.id}: every mesh its own material`);
  assert(meshes.every(m => !materials.includes(m.material)), `${row.id}: the loaded materials are left alone`);
  const f = row.vehicle_finish, colour = rgb => new THREE.Color().setRGB(...rgb, THREE.LinearSRGBColorSpace);
  for (const m of meshes) {
    const role = m.material.userData.chicago4d_coachwork?.role;
    assert(role, `${row.id}: ${m.name} has a role`);
    let gear = false; for (let n = m; n; n = n.parent) if (/^vehicle_(wheel_|steer_front|running_gear|team_pole)|^hubcap$/.test(n.name)) gear = true;
    if (role === 'panels' && f.panels) assert(m.material.color.equals(colour(f.panels)), `${row.id}: ${m.name} panels`);
    if (role === 'timber' && gear && f.gear) assert(m.material.color.equals(colour(f.gear)), `${row.id}: ${m.name} running gear`);
    if (role === 'timber' && !gear && f.timber) assert(m.material.color.equals(colour(f.timber)), `${row.id}: ${m.name} body timber`);
    if (!f.panels && role === 'panels') assert(m.material.color.equals(loaded.get(m).color), `${row.id}: ${m.name} keeps its catalogue colour`);
    const marked = !['glass', 'upholstery'].includes(role);
    assert.equal(Object.prototype.hasOwnProperty.call(m.material, 'customProgramCacheKey'), marked, `${row.id}: ${m.name} ${marked ? 'carries' : 'is spared'} the road`);
    if (!marked) continue;
    const s = shader(); m.material.onBeforeCompile(s);
    assert(s.fragmentShader.includes('chiCoachDust') && s.vertexShader.includes('vChiCoachP = ( chiCoachFrame'), `${row.id}: ${m.name} spliced`);
    assert(['chiCoach', 'chiCoachSeed', 'chiCoachDust', 'chiCoachFrame'].every(k => s.uniforms[k]), `${row.id}: ${m.name} uniforms`);
    let wheel = false; for (let n = m; n; n = n.parent) if (/^vehicle_wheel_/.test(n.name)) wheel = true;
    assert.equal(s.uniforms.chiCoach.value.w, wheel ? 1 : 0, `${row.id}: ${m.name} marked as ${wheel ? 'a wheel' : 'the body'}`);
    keys.add(m.material.customProgramCacheKey());
  }
  // Chained beneath a later hook (confidence.js), the key names both.
  const any = meshes.find(m => m.material.userData.chicago4d_coachwork.role === 'panels').material;
  const before = any.customProgramCacheKey();
  assert(before.endsWith('|chicago-coachwork-v1'));
  work.dispose();
  assert(meshes.every(m => m.material === loaded.get(m)), `${row.id}: dispose gives back the loaded materials`);
  console.log(`${row.id}: ${meshes.length} meshes their own, panels/timber/gear/trim painted, glass and the inside clean, disposed cleanly`);
}
assert.equal(keys.size, 1, 'one program for every coach');
assert(north.gear && north.panels, 'the Pullman coach has its own claret panels and carmine gear');
console.log('coachwork: every coach its own paint, wear and marks on one program, no texture: PASS');

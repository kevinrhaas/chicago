/**
 * T-2700: one draw per mesh, its pieces' boxes decoded in the vertex stage.
 *
 *   node tools/check_position_boxes.mjs [--json]
 *
 * `packPositionBoxes` (compact-streams.js) writes a mesh too wide for one box
 * as Int16 x 4 over each triangle's own piece, the piece named in the padding
 * lane, and leaves every face where it was. This holds it to that, on a
 * synthetic town-long walk and on the 1835 frontage as the page builds it:
 *
 *   - every vertex read back (on the CPU, and as the vertex stage reads it in
 *     float32) is within the millimetre of the float it was;
 *   - faces keep their order and their three vertices one piece; the other
 *     streams are not touched; each piece's box keeps the millimetre;
 *   - bounds are in metres, and the raycast answers what three's own raycast
 *     answered on the float mesh: the same face, its point on that face to the
 *     millimetre (a ray within a millimetre of an edge may fall either side);
 *   - the lane is bound under its own name without being enumerated, so the
 *     readers that walk a geometry's streams see what they saw;
 *   - the material patch decodes right after `<begin_vertex>`, before the
 *     patches beneath it, and its program key carries the table's length;
 *   - frontage's shared mesh is ONE boxed mesh with its matrix the identity.
 *
 * It does not compile GLSL or draw: pixel parity and call counts are the
 * smoke's (stages 1-2 and 5), and a tap through gpu-pick.js is
 * check_upload_release.mjs's.
 */
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const THREE = await import(pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href);
const {
  compactStreams, BOX_TABLE_MAX, BOX_LANE, POSITION_ERROR_M, POSITION_STEPS,
} = await import(pathToFileURL(path.join(web, 'js/compact-streams.js')).href);
const cs = compactStreams(THREE);

const json = process.argv.includes('--json');
const checks = [];
const readings = {};
function check(name, run) {
  try { run(); checks.push({ name, ok: true }); } catch (err) {
    checks.push({ name, ok: false, why: err.message });
  }
}

/** A seeded walk of boxes 700 m long, wandering, at a street's heights. */
function townWalk(seed = 7) {
  let s = seed;
  const rnd = () => { s = (s * 16807) % 2147483647; return s / 2147483647; };
  const pos = [];
  let x = -350, z = 40;
  while (x < 350) {
    const len = 0.3 + rnd() * 3, w = 0.2 + rnd() * 1.6, h = 0.02 + rnd() * 1.2;
    const y = rnd() * 1.4, a = (rnd() - 0.5) * 0.4;
    const geo = new THREE.BoxGeometry(len, h, w).toNonIndexed();
    geo.rotateY(a);
    geo.translate(x, y + h / 2, z + (rnd() - 0.5) * 30);
    pos.push(...geo.getAttribute('position').array);
    x += len * (0.5 + rnd());
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pos), 3));
  g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array((pos.length / 3) * 2).map((_, i) => i), 2));
  g.computeBoundingSphere();
  return g;
}

/** What the vertex stage computes, in float32: `xyz * box.w + box.xyz`. */
function shaderDecode(geo, table, i) {
  const p = geo.getAttribute('position');
  const f = Math.fround;
  const q = Math.trunc(f(f(p.getW(i)) * POSITION_STEPS) + 0.5) - 1;
  const b = table.uniform.value;
  return [0, 1, 2].map((c) => f(f(f([p.getX(i), p.getY(i), p.getZ(i)][c]) * b[q * 4 + 3]) + b[q * 4 + c]));
}

function holdToSource(name, geo, before, table) {
  const src = before.getAttribute('position');
  const pos = geo.getAttribute('position');
  let cpu = 0, gpu = 0, laneSplit = 0;
  const v = new THREE.Vector3();
  for (let i = 0; i < src.count; i += 1) {
    cs.boxedPositionAt(geo, i, v);
    cpu = Math.max(cpu, Math.abs(v.x - src.getX(i)), Math.abs(v.y - src.getY(i)), Math.abs(v.z - src.getZ(i)));
    const s = shaderDecode(geo, table, i);
    gpu = Math.max(gpu, Math.abs(s[0] - src.getX(i)), Math.abs(s[1] - src.getY(i)), Math.abs(s[2] - src.getZ(i)));
    if (i % 3 === 2 && !(pos.getW(i) === pos.getW(i - 1) && pos.getW(i) === pos.getW(i - 2))) laneSplit += 1;
  }
  readings[name] = { vertices: src.count, pieces: geo.userData.positionBoxes.boxes.length / 4,
    worst_cpu_mm: +(cpu * 1000).toFixed(3), worst_vertex_stage_mm: +(gpu * 1000).toFixed(3) };
  assert.ok(cpu <= POSITION_ERROR_M, `${name}: a vertex read back ${cpu} m from its float`);
  // The vertex stage's own float32 sum adds at most an ulp of the box centre.
  assert.ok(gpu <= POSITION_ERROR_M + 1e-4, `${name}: the vertex stage reads a vertex ${gpu} m off`);
  assert.equal(laneSplit, 0, `${name}: ${laneSplit} faces straddle two pieces`);
}

// ---------------------------------------------------------------- synthetic
const walk = townWalk();
const before = walk.clone();
const uvBefore = walk.getAttribute('uv');
const table = cs.createBoxTable();
check('a town-long walk is boxed in place: Int16 x 4, the lane naming its piece', () => {
  assert.ok(cs.packPositionBoxes(walk, table), 'the walk was not boxed');
  const p = walk.getAttribute('position');
  assert.ok(p.array instanceof Int16Array && p.itemSize === 4 && p.normalized);
  assert.equal(p.count, before.getAttribute('position').count, 'vertex count moved');
  assert.ok(table.count > 1, `one box cannot keep a ${before.boundingSphere.radius * 2} m walk`);
  for (let i = 0; i < p.count; i += 1) {
    const q = p.array[i * 4 + 3];
    assert.ok(q >= 1 && q <= table.count, `vertex ${i} names row ${q}`);
  }
  assert.equal(walk.getAttribute('uv'), uvBefore, 'another stream was replaced');
});
check('every vertex reads back within the millimetre, on the CPU and as the vertex stage reads it', () => {
  holdToSource('synthetic', walk, before, table);
});
check('each piece keeps the millimetre in its own box', () => {
  const b = walk.userData.positionBoxes.boxes;
  for (let i = 3; i < b.length; i += 4) {
    assert.ok(b[i] / POSITION_STEPS / 2 <= POSITION_ERROR_M, `piece ${(i - 3) / 4}: half-extent ${b[i]} m`);
  }
});
check('bounds are in metres, and recomputing them reads metres again', () => {
  const s0 = before.boundingSphere;
  before.computeBoundingBox();
  const b0 = before.boundingBox;
  assert.ok(walk.boundingSphere.center.distanceTo(s0.center) < 0.002, 'sphere centre moved');
  assert.ok(Math.abs(walk.boundingSphere.radius - s0.radius) < 0.002, 'sphere radius moved');
  walk.boundingBox = null;
  walk.computeBoundingBox();
  assert.ok(walk.boundingBox.min.distanceTo(b0.min) < 0.002 && walk.boundingBox.max.distanceTo(b0.max) < 0.002,
    'box not in metres');
  const m = cs.positionsInMetres(walk);
  assert.equal(m.count, walk.getAttribute('position').count);
});
check('the lane is bound under its own name, the same attribute, and never enumerated', () => {
  assert.equal(walk.attributes[BOX_LANE], walk.attributes.position);
  assert.deepEqual(Object.keys(walk.attributes).sort(), ['position', 'uv']);
  assert.ok(!JSON.stringify(Object.entries(walk.attributes).map(([k]) => k)).includes(BOX_LANE));
});
check('the raycast answers what three answered on the float walk: the face, its point on the float face to the millimetre', () => {
  const mat = new THREE.MeshBasicMaterial();
  const a = new THREE.Mesh(before, mat);
  const b = new THREE.Mesh(walk, mat);
  b.raycast = cs.raycastBoxed;
  a.updateMatrixWorld(); b.updateMatrixWorld();
  const ray = new THREE.Raycaster();
  let hits = 0, worst = 0, grazing = 0;
  /** How far a hit lies from the nearest edge of the face it hit, in metres. */
  const edgeGap = (_, h) => {
    const t = [0, 1, 2].map((j) => (h.object === a ? new THREE.Vector3().fromBufferAttribute(src, h.faceIndex * 3 + j)
      : cs.boxedPositionAt(walk, h.faceIndex * 3 + j, new THREE.Vector3())));
    return Math.min(...[0, 1, 2].map((j) => new THREE.Line3(t[j], t[(j + 1) % 3])
      .closestPointToPoint(h.point, true, new THREE.Vector3()).distanceTo(h.point)));
  };
  const src = before.getAttribute('position');
  const faces = src.count / 3;
  const c = new THREE.Vector3(), v = new THREE.Vector3();
  for (let k = 0; k < 400; k += 1) {
    // Aimed at a face's centre from above and aside, so most rays land.
    const f = Math.floor((k * faces) / 400);
    c.set(0, 0, 0);
    for (let j = 0; j < 3; j += 1) c.add(v.fromBufferAttribute(src, f * 3 + j));
    c.divideScalar(3);
    const from = c.clone().add(new THREE.Vector3(3 * Math.sin(k), 20, 3 * Math.cos(k)));
    ray.set(from, c.clone().sub(from).normalize());
    const ha = ray.intersectObject(a, false)[0];
    const hb = ray.intersectObject(b, false)[0];
    if (!!ha !== !!hb || (ha && hb.faceIndex !== ha.faceIndex)) {
      // A ray within the grid's millimetre of a face's edge may fall either
      // side of it; that is the tolerance the positions were written to, and
      // only there is a disagreement allowed.
      const h = ha ?? hb;
      assert.ok(edgeGap(null, h) < 0.003,
        `ray ${k}: ${ha ? `face ${ha.faceIndex}` : 'a miss'} on the float walk, ${hb ? `face ${hb.faceIndex}` : 'a miss'} boxed`);
      grazing += 1;
      continue;
    }
    if (!ha) continue;
    hits += 1;
    // How far the boxed hit stands off the float face: a ray at a grazing
    // angle slides along a face a millimetre moved, but never off it.
    const t = [0, 1, 2].map((j) => new THREE.Vector3().fromBufferAttribute(src, ha.faceIndex * 3 + j));
    const off = new THREE.Triangle(...t).closestPointToPoint(hb.point, new THREE.Vector3()).distanceTo(hb.point);
    worst = Math.max(worst, off);
  }
  readings.raycast = { rays: 400, hits, grazing, worst_off_face_mm: +(worst * 1000).toFixed(3) };
  assert.ok(hits > 300, `only ${hits} rays hit the walk alike`);
  assert.ok(worst <= POSITION_ERROR_M * 2, `a boxed hit stands ${worst} m off the float face`);
});
check('a table refuses a mesh past its rows, and leaves the mesh float', () => {
  const full = cs.createBoxTable();
  full.count = BOX_TABLE_MAX;
  const g = townWalk(11);
  assert.equal(cs.packPositionBoxes(g, full), false);
  assert.ok(g.getAttribute('position').array instanceof Float32Array);
});
check('a second mesh takes the rows after the first, and a prebuilt one is adopted at its own rows', () => {
  const g = townWalk(23);
  const first = table.count;
  assert.ok(cs.packPositionBoxes(g, table));
  assert.equal(g.userData.positionBoxes.first, first);
  const copy = new THREE.BufferGeometry();
  copy.setAttribute('position', g.getAttribute('position'));
  copy.userData.positionBoxes = JSON.parse(JSON.stringify(g.userData.positionBoxes));
  const fresh = cs.createBoxTable();
  assert.ok(cs.adoptPositionBoxes(copy, fresh));
  assert.equal(fresh.count, table.count);
  for (let i = first * 4; i < table.count * 4; i += 1) assert.equal(fresh.uniform.value[i], table.uniform.value[i]);
  assert.equal(copy.attributes[BOX_LANE], copy.attributes.position);
});
check('the material decodes right after <begin_vertex>, before the patches beneath it, keyed by its rows', () => {
  const mat = new THREE.MeshStandardMaterial();
  mat.onBeforeCompile = (shader) => {
    shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n// INNER');
  };
  mat.customProgramCacheKey = () => 'inner';
  cs.patchBoxTable(mat, table);
  const shader = { vertexShader: THREE.ShaderLib.standard.vertexShader, uniforms: {} };
  mat.onBeforeCompile(shader, null);
  const vs = shader.vertexShader;
  assert.ok(vs.includes(`attribute vec4 ${BOX_LANE};`) && vs.includes(`uniform vec4 uChiBoxes[${table.count}];`));
  const at = (s) => vs.indexOf(s);
  assert.ok(at('#include <begin_vertex>') < at('transformed = transformed * uChiBoxes') &&
    at('transformed = transformed * uChiBoxes') < at('// INNER'), 'the decode is not first after <begin_vertex>');
  assert.equal(shader.uniforms.uChiBoxes, table.uniform);
  assert.equal(mat.customProgramCacheKey(), `inner|boxes:${table.count}`);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(9), 3));
  mat.onBeforeRender(null, null, null, g, null, null);
  assert.equal(g.attributes[BOX_LANE], g.attributes.position, 'a mesh drawn with it has no lane bound');
  const depth = cs.boxDepthMaterial(table);
  assert.ok(depth.isMeshDepthMaterial && cs.boxDepthMaterial(table) === depth);
});

// ------------------------------------------------------------------ frontage
const sources = new Map();
const setAttribute = THREE.BufferGeometry.prototype.setAttribute;
THREE.BufferGeometry.prototype.setAttribute = function (name, attr) {
  const was = this.attributes?.position;
  if (name === 'position' && was?.array instanceof Float32Array && attr.array instanceof Int16Array) {
    sources.set(this, was);
  }
  return setAttribute.call(this, name, attr);
};
const prebuild = await import(pathToFileURL(path.join(root, 'tools/prebuild_layers.mjs')).href);
const scene = prebuild.frontageScenes().find((s) => /1835/.test(JSON.stringify(s)));
const built = await prebuild.buildFrontage(scene);
THREE.BufferGeometry.prototype.setAttribute = setAttribute;
const group = built.layer.group;
check('1835: frontage\'s shared mesh is ONE boxed mesh, its matrix the identity, every piece in its table', () => {
  const shared = group.children.filter((c) => c.name === 'frontage');
  assert.equal(shared.length, 1, `${shared.length} shared meshes`);
  const [mesh] = shared;
  const pb = mesh.geometry.userData.positionBoxes;
  assert.ok(pb, 'the shared mesh is not boxed');
  assert.ok(mesh.matrix.equals(new THREE.Matrix4()), 'the shared mesh carries a matrix');
  assert.ok(mesh.geometry.getAttribute('position').array instanceof Int16Array);
  assert.notEqual(mesh.raycast, THREE.Mesh.prototype.raycast, 'the shared mesh raycasts the -1..1 grid');
  assert.ok(mesh.customDepthMaterial?.isMeshDepthMaterial, 'the shared mesh casts with three\'s own depth');
  const tbl = mesh.material.userData.boxTable;
  assert.ok(tbl && tbl.count >= pb.first + pb.boxes.length / 4, 'the material\'s table lacks its rows');
  readings.frontage_shared = { pieces: pb.boxes.length / 4 };
});
check('1835: every shared-mesh vertex reads back within the millimetre of the float the layer laid', () => {
  const mesh = group.children.find((c) => c.name === 'frontage');
  const src = sources.get(mesh.geometry);
  assert.ok(src, 'the float positions were never seen');
  const was = new THREE.BufferGeometry();
  was.setAttribute('position', src);
  holdToSource('frontage_1835', mesh.geometry, was, mesh.material.userData.boxTable);
});
check('1835: every other frontage mesh names no box, and draws as it did', () => {
  for (const c of group.children) {
    if (c.name === 'frontage' || !c.isMesh) continue;
    assert.ok(!c.geometry.userData.positionBoxes, `${c.name} is boxed`);
    const p = c.geometry.getAttribute('position');
    if (p.array instanceof Int16Array) {
      for (let i = 3; i < p.array.length; i += 4) assert.equal(p.array[i], 0, `${c.name} carries a lane`);
    }
  }
});

const failed = checks.filter((c) => !c.ok);
if (json) console.log(JSON.stringify({ checks, readings }, null, 2));
else {
  for (const c of checks) console.log(`${c.ok ? 'PASS' : 'FAIL'} ${c.name}${c.ok ? '' : ` — ${c.why}`}`);
  console.log(`${failed.length ? 'FAIL' : 'PASS'} position boxes: ${checks.length - failed.length}/${checks.length}; ${JSON.stringify(readings)}`);
}
process.exit(failed.length ? 1 : 0);

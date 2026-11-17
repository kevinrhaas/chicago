// SPDX-License-Identifier: GPL-3.0-or-later
// Trousers bridge the seat and never trace the cleft (renderers/web/js/human-seat.js, T-3553:
// "no trousers tracing the buttock cleft on any figure in motion"). On the real exports, on
// the CPU, every trouser-like garment of every body at every level: the hollow behind,
// between the cheeks, measured against the cloth's own rear outline (its upper convex hull,
// row by row from the fork up past the top of the cleft), standing and at a stride, before
// and after. It must: find every pair of trousers, breeches, pantaloons and overalls; leave
// the hollow no deeper than DEPTH_M standing and STRIDE_M at the stride on the near level (the
// middle level at least halved, the far ones never deeper than drawn); move only the seat
// (nothing below the fork or above the band, nothing in toward the body, nothing slid more
// than 3.5 cm across it); move nothing more than MAX_M; keep topology, UVs and skin weights; and run once per loaded body.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const three = new URL('three.core.js', vendor).href;
const THREE = await import(three);
const data = text => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const utils = {};
for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) {
  utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${three}'`));
}
const gltfURL = new URL('addons/loaders/GLTFLoader.js', vendor);
const loaderSource = (await fs.readFile(gltfURL, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => {
  const name = Object.keys(utils).find(k => spec.endsWith(`/${k}.js`));
  return `from '${spec === 'three' ? three : name ? utils[name] : new URL(spec, gltfURL).href}'`;
});
const { GLTFLoader } = await import(data(loaderSource));
const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
const js = async (name) => (await fs.readFile(new URL(`renderers/web/js/${name}`, here), 'utf8')).replace("from 'three'", `from '${three}'`);
const { easeSeats, isSeat, MAX_M } = await import(data(await js('human-seat.js')));

function geometryOnly(bytes) {
  const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20 + n));
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    if (m.pbrMetallicRoughness) { delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; }
  }
  const json0 = Buffer.from(JSON.stringify(doc)), json = Buffer.concat([json0, Buffer.alloc(-json0.length & 3, 32)]);
  const bin = bytes.subarray(28 + n), out = Buffer.alloc(28 + json.length + bin.length);
  out.writeUInt32LE(0x46546c67, 0); out.writeUInt32LE(2, 4); out.writeUInt32LE(out.length, 8);
  out.writeUInt32LE(json.length, 12); out.writeUInt32LE(0x4e4f534a, 16); json.copy(out, 20);
  out.writeUInt32LE(bin.length, 20 + json.length); out.writeUInt32LE(0x004e4942, 24 + json.length); bin.copy(out, 28 + json.length);
  return out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength);
}
async function load(asset, lod) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  gltf.scene.updateMatrixWorld(true);
  return gltf;
}

export const DEPTH_M = 0.016, STRIDE_M = 0.025;
const ROW = 0.008, HALF = 0.006, MID = 0.05, COL = 0.005;
const smoothstep = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
function hull(points) {
  points.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const h = [];
  for (const p of points) {
    while (h.length >= 2) { const a = h[h.length - 2], b = h[h.length - 1]; if ((b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0]) < -1e-12) break; h.pop(); }
    h.push(p);
  }
  return h;
}
const at = (h, x) => { if (h.length < 2 || x < h[0][0] || x > h.at(-1)[0]) return null; for (let i = 1; i < h.length; i++) if (x <= h[i][0]) return h[i - 1][1] + (h[i][1] - h[i - 1][1]) * (x - h[i - 1][0]) / ((h[i][0] - h[i - 1][0]) || 1); return h.at(-1)[1]; };

/** The pelvis frame now (posed or not): hips centre, up from the ankles, left, forward. */
function frame(bones) {
  const w = n => bones[n].getWorldPosition(new THREE.Vector3());
  const O = w('thigh_l').add(w('thigh_r')).multiplyScalar(0.5);
  const U = O.clone().sub(w('foot_l').add(w('foot_r')).multiplyScalar(0.5)).normalize();
  // Up from the pelvis's own bind axis, so a raised thigh does not tip the frame.
  const L = w('thigh_l').sub(w('thigh_r')); L.addScaledVector(U, -L.dot(U)).normalize();
  const F = new THREE.Vector3().crossVectors(L, U).normalize();
  return { O, U, L, F };
}
/** The deepest hollow behind between the cheeks, metres, over the seat band. */
function hollow(mesh, fr, band) {
  const pos = mesh.geometry.attributes.position, v = new THREE.Vector3(), P = [];
  for (let i = 0; i < pos.count; i++) {
    mesh.getVertexPosition(i, v); v.applyMatrix4(mesh.matrixWorld).sub(fr.O);
    P.push([v.dot(fr.L), v.dot(fr.U), -v.dot(fr.F)]);
  }
  let worst = 0, where = null;
  for (let y = band.lo; y <= band.hi; y += ROW) {
    // What is seen from behind: the rearmost cloth in each 5 mm column of the row (the fork's
    // underside, facing the ground, is under it and never seen).
    const cols = new Map();
    for (const p of P) {
      if (p[2] <= 0 || Math.abs(p[1] - y) > HALF) continue;
      const c = Math.round(p[0] / COL);
      if (!cols.has(c) || cols.get(c) < p[2]) cols.set(c, p[2]);
    }
    const pts = [...cols].map(([c, r]) => [c * COL, r]);
    if (!pts.some(p => Math.abs(p[0]) < 0.014) || pts.length < 3) continue;
    const h = hull(pts.map(p => [p[0], p[1]]));
    for (const p of pts) { if (Math.abs(p[0]) > MID) continue; const r = at(h, p[0]); if (r !== null && r - p[1] > worst) { worst = r - p[1]; where = [+(p[0] * 100).toFixed(1), +(y * 100).toFixed(1)]; } }
  }
  return { worst, where };
}

function rigOf(gltf) {
  const bones = {};
  gltf.scene.traverse(o => { if (o.isBone) bones[o.name] = o; });
  return bones;
}
/** A stride: left thigh flexed 30 deg, knee 10; right thigh back 15, knee 40. */
function stride(bones, sign = 1) {
  const fr = frame(bones);
  const turn = (b, ang) => {
    b.parent.updateWorldMatrix(true, false);
    const pq = b.parent.getWorldQuaternion(new THREE.Quaternion()), wq = pq.clone().multiply(b.quaternion);
    b.quaternion.copy(pq.invert().multiply(new THREE.Quaternion().setFromAxisAngle(fr.L, ang).multiply(wq)));
  };
  const [lead, back] = sign > 0 ? ['l', 'r'] : ['r', 'l'];
  turn(bones[`thigh_${lead}`], -30 * Math.PI / 180); turn(bones[`calf_${lead}`], 10 * Math.PI / 180);
  turn(bones[`thigh_${back}`], 15 * Math.PI / 180); turn(bones[`calf_${back}`], 40 * Math.PI / 180);
}

const ASSETS = (await fs.readdir(new URL('assets/humans/web/', here))).filter(f => f.endsWith('.lod0.glb') && !f.startsWith('c4d_fixture')).map(f => f.replace('.lod0.glb', '')).sort();
const lines = [];
let seats = 0;
for (const asset of ASSETS) for (const lod of [0, 1, 2, 3]) {
  const before = await load(asset, lod), after = await load(asset, lod);
  const meshes = (g) => { const out = []; g.scene.traverse(o => { if (isSeat(o)) out.push(o); }); return out; };
  const mb = meshes(before), ma = meshes(after);
  if (!mb.length) continue;
  const snap = ma.map(m => ({ pos: m.geometry.attributes.position.array.slice(), uv: m.geometry.attributes.uv?.array.slice(), si: m.geometry.attributes.skinIndex.array.slice(), sw: m.geometry.attributes.skinWeight.array.slice(), idx: m.geometry.index?.array.slice() }));
  const report = easeSeats(after.scene);
  assert.equal(report.length, ma.length, `${asset} LOD${lod}: every seat garment bridged (${report.length} of ${ma.length})`);
  after.scene.updateMatrixWorld(true);
  for (let k = 0; k < ma.length; k++) {
    const m = ma[k], s = snap[k], g = m.geometry;
    assert.deepEqual(g.attributes.skinIndex.array, s.si, `${asset} LOD${lod} ${m.name}: skin indices kept`);
    assert.deepEqual(g.attributes.skinWeight.array, s.sw, `${asset} LOD${lod} ${m.name}: skin weights kept`);
    if (s.uv) assert.deepEqual(g.attributes.uv.array, s.uv, `${asset} LOD${lod} ${m.name}: UVs kept`);
    if (s.idx) assert.deepEqual(g.index.array, s.idx, `${asset} LOD${lod} ${m.name}: topology kept`);
  }
  const bb = rigOf(before), ba = rigOf(after);
  const fb = frame(bb), fa = frame(ba);
  const legM = bb.thigh_l.getWorldPosition(new THREE.Vector3()).distanceTo(bb.foot_l.getWorldPosition(new THREE.Vector3()));
  const band = { lo: -0.175 * legM / 0.85, hi: 0.11 * legM / 0.85 };
  // The cleft a visitor sees: above the fork's fade (between the legs the cloth is two tubes)
  // to below the bridge's top fade.
  const cleft = { lo: -0.07 * legM / 0.85, hi: 0.05 * legM / 0.85 };
  // Only the seat moved, only back, and never more than MAX_M.
  for (let k = 0; k < ma.length; k++) {
    const pa = ma[k].geometry.attributes.position, pb = mb[k].geometry.attributes.position, va = new THREE.Vector3(), vb = new THREE.Vector3();
    let most = 0;
    for (let i = 0; i < pa.count; i++) {
      ma[k].getVertexPosition(i, va); va.applyMatrix4(ma[k].matrixWorld);
      mb[k].getVertexPosition(i, vb); vb.applyMatrix4(mb[k].matrixWorld);
      const d = va.clone().sub(vb), len = d.length();
      if (len < 1e-4) continue;
      most = Math.max(most, len);
      const y = vb.clone().sub(fb.O).dot(fb.U);
      assert(y >= band.lo - 0.01 && y <= band.hi + 0.01, `${asset} LOD${lod} ${ma[k].name}: a vertex ${(y * 100).toFixed(1)} cm from the hips moved`);
      assert(-d.dot(fb.F) > -5e-4, `${asset} LOD${lod} ${ma[k].name}: a vertex moved in, toward the body (${(d.dot(fb.F) * 1000).toFixed(1)} mm)`);
      assert(Math.hypot(d.dot(fb.L), d.dot(fb.U)) < 0.035, `${asset} LOD${lod} ${ma[k].name}: a vertex slid ${(Math.hypot(d.dot(fb.L), d.dot(fb.U)) * 100).toFixed(1)} cm over the seat`);
    }
    assert(most <= MAX_M * legM / 0.85 + 1e-3, `${asset} LOD${lod} ${ma[k].name}: moved ${(most * 100).toFixed(1)} cm`);
  }
  const res = [];
  for (let k = 0; k < ma.length; k++) {
    const h0 = hollow(mb[k], fb, cleft), h1 = hollow(ma[k], fa, cleft);
    stride(bb); stride(ba); before.scene.updateMatrixWorld(true); after.scene.updateMatrixWorld(true);
    const s0 = hollow(mb[k], frame(bb), cleft), s1 = hollow(ma[k], frame(ba), cleft);
    stride(bb, -1); stride(ba, -1); stride(bb, -1); stride(ba, -1); before.scene.updateMatrixWorld(true); after.scene.updateMatrixWorld(true);
    const m0 = hollow(mb[k], frame(bb), cleft), m1 = hollow(ma[k], frame(ba), cleft);
    stride(bb); stride(ba); before.scene.updateMatrixWorld(true); after.scene.updateMatrixWorld(true);
    const name = ma[k].name.replace(`${asset}_`, '').replace(/_lod\d$/, '');
    const st = Math.max(s1.worst, m1.worst);
    if (lod === 0 || process.env.SEAT_REPORT) res.push(`L${lod} ${name} ${(h0.worst * 1000).toFixed(0)}→${(h1.worst * 1000).toFixed(0)} mm standing ${JSON.stringify(h1.where)}, ${(Math.max(s0.worst, m0.worst) * 1000).toFixed(0)}→${(st * 1000).toFixed(0)} mm striding ${JSON.stringify(s1.worst > m1.worst ? s1.where : m1.where)}`);
    if (!process.env.SEAT_REPORT && lod === 1) {
      // The middle level, fewer rows: the hollow at least halved.
      assert(h1.worst <= Math.max(DEPTH_M, 0.55 * h0.worst), `${asset} LOD${lod} ${name}: standing, the seat still sinks ${(h1.worst * 1000).toFixed(1)} mm (drawn ${(h0.worst * 1000).toFixed(1)})`);
      assert(st <= Math.max(STRIDE_M, 0.55 * Math.max(s0.worst, m0.worst)), `${asset} LOD${lod} ${name}: at the stride, the seat sinks ${(st * 1000).toFixed(1)} mm`);
    } else if (!process.env.SEAT_REPORT && lod >= 2) {
      // The far levels draw a seat with a handful of rows: no deeper than the asset drew it.
      assert(h1.worst <= Math.max(DEPTH_M, h0.worst + 0.001), `${asset} LOD${lod} ${name}: standing, the seat sinks ${(h1.worst * 1000).toFixed(1)} mm, deeper than drawn`);
      assert(st <= Math.max(STRIDE_M, Math.max(s0.worst, m0.worst) + 0.001), `${asset} LOD${lod} ${name}: at the stride, the seat sinks ${(st * 1000).toFixed(1)} mm, deeper than drawn`);
    } else if (!process.env.SEAT_REPORT) {
      assert(h1.worst <= DEPTH_M, `${asset} LOD${lod} ${name}: standing, the seat still sinks ${(h1.worst * 1000).toFixed(1)} mm at ${JSON.stringify(h1.where)}`);
      assert(st <= STRIDE_M, `${asset} LOD${lod} ${name}: at the stride, the seat sinks ${(st * 1000).toFixed(1)} mm at ${JSON.stringify(s1.worst > m1.worst ? s1.where : m1.where)}`);
    }
    seats++;
  }
  // Once per loaded body: a second call on the same scene moves nothing.
  const held = ma.map(m => m.geometry.attributes.position.array.slice());
  assert.equal(easeSeats(after.scene), report, `${asset} LOD${lod}: the second call returns the first report`);
  ma.forEach((m, k) => assert.deepEqual(m.geometry.attributes.position.array, held[k], `${asset} LOD${lod} ${m.name}: a second call moved it`));
  if (lod === 0 || process.env.SEAT_REPORT) lines.push(`${asset}: ${res.join('; ')}`);
}
assert(seats >= 40, `seat garments found: ${seats}`);
// Wired into humans.js's parse, before any figure is cloned from it.
{
  const humans = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/import \{ easeSeats \} from '\.\/human-seat\.js';/.test(humans), 'humans.js imports easeSeats');
  assert(/const gltf = await loader\.parseAsync\(.*\);[\s\S]{0,500}easeSeats\(gltf\.scene\);[\s\S]{0,200}return gltf;/.test(humans), 'parse() bridges the seats of the shared source');
}
for (const l of lines) console.log(l);
console.log(`${seats} seat garments over every body and level: bridged, nothing else moved: PASS`);

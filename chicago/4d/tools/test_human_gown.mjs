// SPDX-License-Identifier: GPL-3.0-or-later
// A lady's 1904 walking suit is cut as its pictures show it (renderers/web/js/human-gown.js,
// T-3553; the owner, 2026-11-17, on the catalogue review of Frances Glessner: "yes do
// tailoring fixes"). On the real exports, on the CPU, every level of glessner_frances_m_1904,
// after the parse passes that run before it and with those after it, against the same body
// without it. It must:
//   - cut the skirt close over the hips and flaring from about the knee: the hem's half-width
//     at most HEM_RATIO of the hips' and its depth front to back at most HEM_DEPTH_M, the knee
//     taking at most KNEE_SHARE of the flare (as drawn: 1.91, 0.78 m, 0.31);
//   - move nothing above the hold line (the waist, the hips, the basque over them), and no
//     other mesh of the asset;
//   - keep the cloth off the legs and shoes standing (CLEAR_M on every ray, at every height);
//   - draw gore seams and, at the near levels, folds at the hem (relief the light can catch),
//     its normals turned outward;
//   - keep topology, UVs and skin weights;
//   - trim the collar, the jabot and the front in cream lace, the skirt's hem and the coat's
//     cuffs in braid, and bring the shirtwaist's cloth up to cream;
//   - put a lace frill at each wrist: from inside the sleeve's end out past it, clear of the
//     hand at bind and with the wrist bent, appended to the shirtwaist's collar (its cloth):
//     every level keeps the export's meshes and materials, no more (a draw call each, T-3555);
//   - keep the legs inside the cut skirt on the walk (human-skirt.js on the new shape);
//   - run once (a second call changes nothing), on this body only; and be wired into parse().
// GOWN_OFF=1 runs every measure on the asset as drawn (it must fail).
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const threeURL = new URL('three.core.js', vendor).href;
registerHooks({ resolve: (specifier, context, next) => (specifier === 'three' ? { url: threeURL, shortCircuit: true } : next(specifier, context)) });
const THREE = await import(threeURL);
const data = (text) => `data:text/javascript;base64,${Buffer.from(text).toString('base64')}`;
const utils = {};
for (const name of ['BufferGeometryUtils', 'SkeletonUtils']) {
  utils[name] = data((await fs.readFile(new URL(`addons/utils/${name}.js`, vendor), 'utf8')).replace("from 'three'", `from '${threeURL}'`));
}
const gltfURL = new URL('addons/loaders/GLTFLoader.js', vendor);
const loaderSource = (await fs.readFile(gltfURL, 'utf8')).replace(/from '([^']+)'/g, (_, spec) => {
  const name = Object.keys(utils).find((k) => spec.endsWith(`/${k}.js`));
  return `from '${spec === 'three' ? threeURL : name ? utils[name] : new URL(spec, gltfURL).href}'`;
});
const { GLTFLoader } = await import(data(loaderSource));
const { MeshoptDecoder } = await import(new URL('addons/libs/meshopt_decoder.module.js', vendor));
const SkeletonUtils = await import(utils.SkeletonUtils);
await MeshoptDecoder.ready;
globalThis.self ??= globalThis;
const js = (name) => import(new URL(`renderers/web/js/${name}`, here).href);
const { fitGown: realFit, GOWNS, CUT, SEAM, FRILL, gownFrame } = await js('human-gown.js');
const { createHumanSkirt, skirtMeshes } = await js('human-skirt.js');
const { TRIMS } = await js('human-finery.js');
const BEFORE = [(await js('human-collar.js')).dressCollars, (await js('human-seat.js')).easeSeats, (await js('human-coat.js')).fitCoats, (await js('human-sleeve.js')).fitSleeves];
const AFTER = [(await js('human-waist.js')).fitWaist, (await js('human-silver.js')).engraveSilver];
const OFF = process.env.GOWN_OFF === '1';
const fitGown = OFF ? () => null : realFit;

export const HEM_RATIO = 1.6, HEM_DEPTH_M = 0.7, KNEE_SHARE = 0.2, CLEAR_M = 0.012;
export const SEAM_DIP_M = 0.0015, FOLD_RMS_M = { 0: 0.005, 1: 0.004 }, FRILL_CLEAR_M = 0.002;

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
/** The export's own meshes and materials, as loaded, before any pass. */
async function exportCounts(asset, lod) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  return counts(gltf.scene);
}
function counts(scene) {
  let meshes = 0; const mats = new Set();
  scene.traverse((o) => { if (o.isMesh) { meshes++; for (const m of [o.material].flat()) mats.add(m); } });
  return { meshes, materials: mats.size };
}
/** A vertex range's attributes, component by component (a loaded attribute may be interleaved). */
const attrRows = (attr, n) => { const out = []; for (let i = 0; i < n; i++) for (let c = 0; c < attr.itemSize; c++) out.push(attr.getComponent(i, c)); return out; };
/** A parsed body as humans.js parse() leaves it: the passes before, the gown (or not), the passes after. */
async function load(asset, lod, gown = true) {
  const bytes = await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here));
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(geometryOnly(bytes), '');
  gltf.scene.updateMatrixWorld(true);
  for (const f of BEFORE) f(gltf.scene);
  const t0 = performance.now();
  const report = gown ? fitGown(gltf.scene) : null;
  const ms = performance.now() - t0;
  for (const f of AFTER) f(gltf.scene);
  return { gltf, scene: gltf.scene, report, ms };
}
const meshes = (scene) => { const out = []; scene.traverse((o) => { if (o.isSkinnedMesh) out.push(o); }); return out; };
const piece = (asset, m) => m.name.replace(`${asset}_`, '').replace(/_lod\d*$/, '');
const named = (scene, asset, p) => meshes(scene).find((m) => piece(asset, m) === p);
/** A mesh's vertices in the body frame: x left, y up from the hips, z forward. */
function inFrame(mesh, fr) {
  const pos = mesh.geometry.attributes.position, out = new Float64Array(pos.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix).sub(fr.O);
    out[i * 3] = v.dot(fr.L); out[i * 3 + 1] = v.dot(fr.U); out[i * 3 + 2] = v.dot(fr.F);
  }
  return out;
}
/** Points over a mesh's surface (its triangles sampled every `step` metres), in the frame. */
function surface(mesh, fr, step = 0.01) {
  const P = inFrame(mesh, fr), idx = mesh.geometry.index.array, out = [];
  const a = new THREE.Vector3(), b = new THREE.Vector3(), c = new THREE.Vector3();
  for (let t = 0; t < idx.length; t += 3) {
    a.fromArray(P, idx[t] * 3); b.fromArray(P, idx[t + 1] * 3); c.fromArray(P, idx[t + 2] * 3);
    const k = Math.max(1, Math.ceil(Math.max(a.distanceTo(b), b.distanceTo(c), c.distanceTo(a)) / step));
    for (let i = 0; i <= k; i++) for (let j = 0; j <= k - i; j++) {
      const u = i / k, v = j / k;
      out.push(a.x + (b.x - a.x) * u + (c.x - a.x) * v, a.y + (b.y - a.y) * u + (c.y - a.y) * v, a.z + (b.z - a.z) * u + (c.z - a.z) * v);
    }
  }
  return Float64Array.from(out);
}
const lum = (c) => 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];

/** The skirt's outline: half-widths and depth at the hold line, the knee and the hem. */
function outline(skirt, fr) {
  const P = inFrame(skirt, fr), n = P.length / 3, yA = -CUT.holdM * fr.scale;
  let yHem = Infinity; for (let i = 0; i < n; i++) yHem = Math.min(yHem, P[i * 3 + 1]);
  const half = (lo, hi) => { let m = 0; for (let i = 0; i < n; i++) if (P[i * 3 + 1] >= lo && P[i * 3 + 1] <= hi) m = Math.max(m, Math.abs(P[i * 3])); return m; };
  const depth = (lo, hi) => { let f = -Infinity, b = Infinity; for (let i = 0; i < n; i++) if (P[i * 3 + 1] >= lo && P[i * 3 + 1] <= hi) { f = Math.max(f, P[i * 3 + 2]); b = Math.min(b, P[i * 3 + 2]); } return f - b; };
  const hip = half(yA - 0.03, yA + 0.03), knee = half(fr.knee - 0.04, fr.knee + 0.04), hem = half(yHem - 1e-3, yHem + 0.03);
  return { yA, yHem, hip, knee, hem, ratio: hem / hip, share: (knee - hip) / (hem - hip), depth: depth(yHem - 1e-3, yHem + 0.03) };
}

const ASSET = 'glessner_frances_m_1904';
assert(GOWNS.some((g) => g.asset === ASSET), 'the gown is cut for Frances Glessner\'s body');
const lines = [], meshCounts = [];
for (const lod of [0, 1, 2, 3]) {
  const ref = await load(ASSET, lod, false), cut = await load(ASSET, lod, true);
  const tag = `${ASSET} LOD${lod}`;
  // 0. No mesh, draw call or material added: the export's own, level by level.
  const ex = await exportCounts(ASSET, lod), now = counts(cut.scene);
  assert.equal(now.meshes, ex.meshes, `${tag}: ${now.meshes} meshes, the export has ${ex.meshes}`);
  assert.equal(now.materials, ex.materials, `${tag}: ${now.materials} materials, the export has ${ex.materials}`);
  meshCounts.push(`LOD${lod} ${now.meshes}/${ex.meshes}`);
  const sRef = named(ref.scene, ASSET, 'gored_skirt'), sCut = named(cut.scene, ASSET, 'gored_skirt');
  const fr = gownFrame(sRef);
  // 1. The outline.
  const o0 = outline(sRef, fr), o1 = outline(sCut, fr);
  assert(o1.ratio <= HEM_RATIO, `${tag}: the hem is ${o1.ratio.toFixed(2)} x the hips' half-width (${(o1.hem * 100).toFixed(1)} vs ${(o1.hip * 100).toFixed(1)} cm), at most ${HEM_RATIO}`);
  assert(o1.depth <= HEM_DEPTH_M, `${tag}: the hem is ${(o1.depth * 100).toFixed(1)} cm front to back, at most ${HEM_DEPTH_M * 100}`);
  assert(o1.share <= KNEE_SHARE, `${tag}: the knee takes ${(o1.share * 100).toFixed(0)} % of the flare, at most ${KNEE_SHARE * 100} %`);
  assert(Math.abs(o1.hip - o0.hip) < 0.003, `${tag}: the hips are as drawn (${(o0.hip * 100).toFixed(1)} -> ${(o1.hip * 100).toFixed(1)} cm)`);
  // 2. Nothing above the hold line, and no other mesh, moves.
  const P0 = inFrame(sRef, fr), P1 = inFrame(sCut, fr);
  let above = 0;
  for (let i = 0; i < P0.length / 3; i++) if (P0[i * 3 + 1] > o0.yA + SEAM.fadeM * fr.scale) above = Math.max(above, Math.hypot(P1[i * 3] - P0[i * 3], P1[i * 3 + 1] - P0[i * 3 + 1], P1[i * 3 + 2] - P0[i * 3 + 2]));
  assert(above < 1e-4, `${tag}: the skirt above the hold line moves ${(above * 1000).toFixed(2)} mm`);
  const others = meshes(ref.scene).filter((m) => m !== sRef);
  const frill = cut.report?.frills?.[0] ?? null;
  for (const m of others) {
    const twin = meshes(cut.scene).find((x) => x.name === m.name);
    assert(twin, `${tag}: ${m.name} is still there`);
    const n = m.geometry.attributes.position.count, host = frill && twin.name === frill.mesh;
    assert.equal(twin.geometry.attributes.position.count, host ? n + frill.vertices : n, `${tag}: ${piece(ASSET, m)} keeps its vertices${host ? ', the frill after them' : ''}`);
    // Its own vertices and triangles first, as they were (the host's grow by the frill only).
    for (const k of Object.keys(m.geometry.attributes)) assert.deepEqual(attrRows(twin.geometry.attributes[k], n), attrRows(m.geometry.attributes[k], n), `${tag}: ${piece(ASSET, m)}'s ${k} as it was`);
    assert.deepEqual(Array.from(twin.geometry.index.array.slice(0, m.geometry.index.count)), Array.from(m.geometry.index.array), `${tag}: ${piece(ASSET, m)}'s triangles as they were`);
  }
  // 3. Topology, UVs, skin weights.
  assert.deepEqual(sCut.geometry.index.array, sRef.geometry.index.array, `${tag}: the skirt's topology`);
  for (const k of ['uv', 'skinIndex', 'skinWeight']) assert.deepEqual(sCut.geometry.attributes[k].array, sRef.geometry.attributes[k].array, `${tag}: the skirt's ${k}`);
  // 4. Standing, the legs and shoes inside the skirt on every ray, CLEAR_M off.
  const BINS = 72, ROW = 0.02, rows = Math.ceil((o1.yA - o1.yHem) / ROW);
  const cell = (x, y, z) => { const row = Math.floor((y - o1.yHem) / ROW); if (row < 1 || row >= rows) return -1; return row * BINS + ((Math.floor((Math.atan2(x, z) / (2 * Math.PI) + 0.5) * BINS) % BINS) + BINS) % BINS; };
  const sk = new Float64Array(rows * BINS).fill(-1), lg = new Float64Array(rows * BINS).fill(-1);
  const S = surface(sCut, fr);
  for (let i = 0; i < S.length; i += 3) { const c = cell(S[i], S[i + 1], S[i + 2]); if (c >= 0) sk[c] = Math.max(sk[c], Math.hypot(S[i], S[i + 2])); }
  for (const m of meshes(cut.scene).filter((x) => /^(skin|footwear)/.test(x.material?.name ?? ''))) {
    const L = inFrame(m, fr);
    for (let i = 0; i < L.length; i += 3) { const c = cell(L[i], L[i + 1], L[i + 2]); if (c >= 0) lg[c] = Math.max(lg[c], Math.hypot(L[i], L[i + 2])); }
  }
  let clear = Infinity, gaps = 0;
  for (let c = 0; c < sk.length; c++) { if (lg[c] < 0) continue; if (sk[c] < 0) { gaps++; continue; } clear = Math.min(clear, sk[c] - lg[c]); }
  assert.equal(gaps, 0, `${tag}: a leg stands where no skirt is`);
  assert(clear >= CLEAR_M, `${tag}: standing, the skirt is ${(clear * 100).toFixed(1)} cm off a leg or a shoe, at least ${CLEAR_M * 100}`);
  // 5. Seams and folds (near levels), normals outward.
  const ring = [];
  for (let i = 0; i < P1.length / 3; i++) ring.push([P1[i * 3 + 1], Math.atan2(P1[i * 3], P1[i * 3 + 2]), Math.hypot(P1[i * 3], P1[i * 3 + 2])]);
  const resid = (lo, hi) => {
    const pts = ring.filter((p) => p[0] >= lo && p[0] <= hi);
    return pts.map(([y, th, r]) => {
      let s = 0, k = 0;
      for (const q of pts) { if (Math.abs(q[0] - y) > 0.01) continue; let d = Math.abs(q[1] - th); if (d > Math.PI) d = 2 * Math.PI - d; if (d < 20 * Math.PI / 180) { s += q[2]; k++; } }
      return [th, r - s / k, r];
    });
  };
  const gore = (2 * Math.PI) / 7, seamDist = (th, r) => { let d = Math.abs(((th - gore / 2) % gore + gore) % gore); return Math.min(d, gore - d) * r; };
  let dip = 0, rms = 0;
  if (lod <= 1) {
    const band = resid(fr.knee + 0.04, o1.yA - 0.05);
    const near = band.filter(([th, , r]) => seamDist(th, r) < 0.008), far = band.filter(([th, , r]) => seamDist(th, r) > 0.03);
    dip = far.reduce((a, p) => a + p[1], 0) / far.length - near.reduce((a, p) => a + p[1], 0) / near.length;
    assert(dip >= SEAM_DIP_M, `${tag}: the gore seams lie ${(dip * 1000).toFixed(1)} mm in from the gores, at least ${SEAM_DIP_M * 1000}`);
    const hem = resid(o1.yHem + 0.005, o1.yHem + 0.08);
    rms = Math.sqrt(hem.reduce((a, p) => a + p[1] * p[1], 0) / hem.length);
    assert(rms >= FOLD_RMS_M[lod], `${tag}: the hem's folds are ${(rms * 1000).toFixed(1)} mm (rms), at least ${FOLD_RMS_M[lod] * 1000}`);
  }
  // The asset draws the skirt's shell with its normals in (it is double-sided): the cut keeps
  // whichever side the asset's own normals face, everywhere, as one smooth field.
  const facing = (mesh, P) => {
    const nrm = mesh.geometry.attributes.normal, nv = new THREE.Vector3();
    let out = 0, counted = 0;
    for (let i = 0; i < nrm.count; i++) {
      if (P[i * 3 + 1] > o1.yA || P[i * 3 + 1] < o1.yHem + 0.01) continue;
      nv.fromBufferAttribute(nrm, i).transformDirection(mesh.bindMatrix);
      counted++; if (nv.dot(fr.L) * P[i * 3] + nv.dot(fr.F) * P[i * 3 + 2] > 0) out++;
    }
    return out / counted;
  };
  const f0 = facing(sRef, P0), f1 = facing(sCut, P1);
  assert(Math.min(f1, 1 - f1) <= 0.03 && Math.abs(f1 - f0) <= 0.03, `${tag}: the cut skirt's normals face one way, the asset's (${(f1 * 100).toFixed(1)} % out, as drawn ${(f0 * 100).toFixed(1)} %)`);
  // 6. Trims and the cream.
  const lace = named(cut.scene, ASSET, 'lady_shirtwaist_collar').material;
  assert(lum(lace.color.toArray()) >= 1.25, `${tag}: the shirtwaist's cloth is brought up to cream (${lum(lace.color.toArray()).toFixed(2)})`);
  const bands = (m) => (m.userData?.chiFinery?.bands ?? []).map((b, i) => ({ kind: b[2] % 16, axis: Math.floor(b[2] / 16), rgb: m.userData.chiFinery.bandRgb[i] }));
  assert(bands(lace).some((b) => b.kind === TRIMS.lace && b.axis === 1 && lum(b.rgb) >= 0.8), `${tag}: the collar, jabot and front in cream lace`);
  assert(bands(named(cut.scene, ASSET, 'lace_jabot').material).some((b) => b.kind === TRIMS.lace), `${tag}: the jabot in lace`);
  assert.equal(bands(sCut.material).filter((b) => b.kind === TRIMS.braid && b.axis === 0).length, 2, `${tag}: two rows of braid at the skirt's hem`);
  assert(bands(named(cut.scene, ASSET, 'lady_jacket_body').material).some((b) => b.kind === TRIMS.braid && b.axis === 2), `${tag}: braid at the coat's cuffs`);
  // 7. The wrist frills, drawn with the shirtwaist's collar.
  let frillClear = null;
  const collar = named(cut.scene, ASSET, 'lady_shirtwaist_collar');
  if (lod > FRILL.maxLod) {
    assert.equal(cut.report?.frills?.length ?? 0, 0, `${tag}: no frill past the near levels`);
    assert(!bands(collar.material).some((b) => b.axis === 2), `${tag}: and no cuff lace on the collar`);
  } else {
    assert(frill && frill.mesh === collar.name, `${tag}: a lace frill at the wrists, appended to the shirtwaist's collar`);
    assert.equal(collar.material.name, 'garment_upper__lady_shirtwaist_white', `${tag}: the frill is the shirtwaist's cloth`);
    assert(bands(collar.material).some((b) => b.kind === TRIMS.lace && b.axis === 2), `${tag}: the frill is lace`);
    const coat = named(cut.scene, ASSET, 'lady_jacket_body'), body = meshes(cut.scene).find((m) => /^skin/.test(m.material?.name ?? ''));
    frillClear = wristClear(collar, coat, body, frill.from);
    assert(frillClear.inside > 0 && frillClear.past >= 0.025, `${tag}: the frill runs from inside the sleeve (${frillClear.inside}) to ${(frillClear.past * 100).toFixed(1)} cm past its end`);
    assert(frillClear.bind >= FRILL_CLEAR_M, `${tag}: at bind the frill is ${(frillClear.bind * 1000).toFixed(1)} mm off the wrist`);
    assert(frillClear.bent >= FRILL_CLEAR_M, `${tag}: with the wrist bent the frill is ${(frillClear.bent * 1000).toFixed(1)} mm off the hand`);
  }
  // 8. Once.
  if (!OFF) {
    const again = fitGown(cut.scene), before = Float32Array.from(sCut.geometry.attributes.position.array);
    assert.equal(again, cut.report, `${tag}: a second call returns the first report`);
    assert.deepEqual(Float32Array.from(sCut.geometry.attributes.position.array), before, `${tag}: and moves nothing`);
    assert.equal(collar.geometry.attributes.position.count, named(ref.scene, ASSET, 'lady_shirtwaist_collar').geometry.attributes.position.count + (frill?.vertices ?? 0), `${tag}: and adds no second frill`);
    assert.equal(counts(cut.scene).meshes, ex.meshes, `${tag}: nor a mesh`);
  }
  lines.push(`LOD${lod} hem ${(o0.hem * 100).toFixed(1)} -> ${(o1.hem * 100).toFixed(1)} cm (x${o0.ratio.toFixed(2)} -> x${o1.ratio.toFixed(2)} the hips), depth ${(o0.depth * 100).toFixed(0)} -> ${(o1.depth * 100).toFixed(0)} cm, knee ${(o0.share * 100).toFixed(0)} -> ${(o1.share * 100).toFixed(0)} %, clear ${(clear * 100).toFixed(1)} cm${lod <= 1 ? `, seams ${(dip * 1000).toFixed(1)} mm, folds ${(rms * 1000).toFixed(1)} mm` : ''}, ${frill ? `frill ${frill.vertices} v in the collar ${(frillClear.bent * 1000).toFixed(0)} mm off, ` : 'no frill, '}${cut.ms.toFixed(0)} ms`);
}
console.log(`${ASSET}: ${lines.join('; ')}: PASS`);
console.log(`${ASSET} meshes per level (with the gown / the export): ${meshCounts.join(', ')}; no mesh, draw call or material added: PASS`);

/**
 * The frill against the sleeve and the wrist: how many of its points lie inside the sleeve's
 * end, how far past it it reaches, and its least distance off the hand's and wrist's skin at
 * bind and with the wrist bent 40 degrees four ways (both posed on the CPU).
 */
function wristClear(frill, coat, body, from = 0) {
  const sk = coat.skeleton, index = new Map(sk.bones.map((b, i) => [b.name, i]));
  const bindAt = (n) => new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[index.get(n)].clone().invert());
  let inside = 0, past = 0, bind = Infinity, bent = Infinity;
  const fv = (m) => { const p = m.geometry.attributes.position, out = []; for (let i = 0; i < p.count; i++) out.push(new THREE.Vector3().fromBufferAttribute(p, i).applyMatrix4(m.bindMatrix)); return out; };
  const F = fv(frill), C = fv(coat), B = fv(body);
  for (const s of ['l', 'r']) {
    const e = bindAt(`lowerarm_${s}`), w = bindAt(`hand_${s}`), ax = w.clone().sub(e).normalize();
    const t = (p) => p.clone().sub(e).dot(ax), rad = (p) => p.clone().sub(e).addScaledVector(ax, -t(p)).length();
    const side = (p) => t(p) > 0 && rad(p) < 0.12;
    let tEnd = -Infinity; for (const p of C) if (side(p) && t(p) < 0.4) tEnd = Math.max(tEnd, t(p));
    const mine = F.map((p, i) => [p, i]).filter(([p, i]) => i >= from && side(p));
    for (const [p] of mine) { if (t(p) < tEnd) inside++; past = Math.max(past, t(p) - tEnd); }
    const wrist = B.map((p, i) => [p, i]).filter(([p]) => side(p) && t(p) > tEnd - 0.03 && t(p) < tEnd + 0.08);
    for (const [p] of mine) { if (t(p) < tEnd) continue; for (const [q] of wrist) bind = Math.min(bind, Math.abs(q.distanceTo(p))); }
    // Bound away from the wrist only by the hand's own skin being farther in: a frill point at
    // bind must lie farther from the forearm's axis than the skin beside it.
    for (const [p] of mine) { if (t(p) < tEnd) continue; let skin = 0; for (const [q] of wrist) if (Math.abs(t(q) - t(p)) < 0.006) skin = Math.max(skin, rad(q)); bind = Math.min(bind, rad(p) - skin); }
    // Posed: the wrist bent up, down, in and out 40 degrees.
    const hand = sk.bones[index.get(`hand_${s}`)];
    for (const axis of [[0, 0, 1], [0, 0, -1], [0, 1, 0], [0, -1, 0]]) {
      const q0 = hand.quaternion.clone();
      hand.quaternion.multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(...axis), 40 * Math.PI / 180));
      hand.updateMatrixWorld(true); sk.update(); body.skeleton.update();
      const pose = (m, list) => list.map(([, i]) => { const v = new THREE.Vector3(); m.getVertexPosition(i, v); return v.applyMatrix4(m.matrixWorld); });
      const pf = pose(frill, mine.filter(([p]) => t(p) > tEnd + 0.005)), pb = pose(body, wrist);
      let here = Infinity; for (const p of pf) for (const q of pb) here = Math.min(here, p.distanceTo(q)); bent = Math.min(bent, here);
      hand.quaternion.copy(q0); hand.updateMatrixWorld(true); sk.update(); body.skeleton.update();
    }
  }
  return { inside, past, bind, bent };
}

// 9. The walk on the cut skirt: the legs stay inside it (human-skirt.js reads the new shape).
{
  const { gltf, scene } = await load(ASSET, 0, true);
  const fig = SkeletonUtils.clone(scene), root = new THREE.Group(); root.add(fig);
  const mixer = new THREE.AnimationMixer(fig);
  mixer.clipAction(gltf.animations.find((a) => a.name === 'walk')).play();
  const skirt = createHumanSkirt({ id: 'gown', scene: fig });
  assert(skirt?.bound, 'the skirt driver binds on the cut skirt');
  const S = skirtMeshes(fig).skirt, body = meshes(fig).find((m) => /^skin/.test(m.material?.name ?? ''));
  const bone = (n) => fig.getObjectByName(n);
  let worst = Infinity;
  for (let i = 0; i < 60; i++) {
    mixer.update(1 / 30); skirt.apply(1 / 30, { state: 'walking', root }); root.updateMatrixWorld(true);
    if (i % 3) continue;
    const hips = bone('thigh_l').getWorldPosition(new THREE.Vector3()).add(bone('thigh_r').getWorldPosition(new THREE.Vector3())).multiplyScalar(0.5);
    const BINS = 90, sk = Array.from({ length: BINS }, () => []), v = new THREE.Vector3();
    for (let k = 0; k < S.geometry.attributes.position.count; k++) {
      S.getVertexPosition(k, v); v.applyMatrix4(S.matrixWorld).sub(hips);
      const th = Math.atan2(v.x, v.z); sk[((Math.floor((th / (2 * Math.PI) + 0.5) * BINS) % BINS) + BINS) % BINS].push(v.y, Math.hypot(v.x, v.z));
    }
    const si = body.geometry.attributes.skinIndex, sw = body.geometry.attributes.skinWeight, legs = new Set(body.skeleton.bones.map((b, k) => (/^(thigh|calf)_[lr]$/.test(b.name) ? k : -1)).filter((k) => k >= 0));
    for (let k = 0; k < si.count; k++) {
      let w = 0; for (let c = 0; c < 4; c++) if (legs.has(si.getComponent(k, c))) w += sw.getComponent(k, c);
      if (w < 0.5) continue;
      body.getVertexPosition(k, v); v.applyMatrix4(body.matrixWorld).sub(hips);
      if (v.y > -0.1) continue;
      const th = Math.atan2(v.x, v.z), b = ((Math.floor((th / (2 * Math.PI) + 0.5) * BINS) % BINS) + BINS) % BINS;
      let rs = -Infinity, low = Infinity;
      for (let d = -1; d <= 1; d++) { const list = sk[(b + d + BINS) % BINS]; for (let m = 0; m < list.length; m += 2) { low = Math.min(low, list[m]); if (Math.abs(list[m] - v.y) < 0.03) rs = Math.max(rs, list[m + 1]); } }
      if (v.y < low + 0.03 || rs === -Infinity) continue;
      worst = Math.min(worst, rs - Math.hypot(v.x, v.z));
    }
  }
  assert(worst > 0, `walk on the cut skirt: a leg is ${(-worst * 100).toFixed(1)} cm outside it`);
  console.log(`${ASSET} LOD0 walk clip on the cut skirt: the legs ${(worst * 100).toFixed(1)} cm inside at least (vertex rings): PASS`);
}

// 10. Only this body: every other body is left as it was.
{
  const assets = (await fs.readdir(new URL('assets/humans/web/', here))).filter((f) => f.endsWith('.lod0.glb') && !f.startsWith('c4d_fixture')).map((f) => f.replace('.lod0.glb', '')).sort();
  let n = 0;
  for (const asset of assets) {
    if (GOWNS.some((g) => g.asset === asset)) continue;
    const { scene, report } = await load(asset, 0, true);
    assert.equal(report, null, `${asset}: no gown`);
    const ref = await load(asset, 0, false);
    const a = meshes(scene), b = meshes(ref.scene);
    assert.equal(a.length, b.length, `${asset}: no mesh added`);
    for (let i = 0; i < a.length; i++) assert.deepEqual(a[i].geometry.attributes.position.array, b[i].geometry.attributes.position.array, `${asset}: ${a[i].name} untouched`);
    n++;
  }
  console.log(`${n} other bodies: no gown, nothing moved, nothing added: PASS`);
}

// 11. Wired into parse(), after the sleeves and before the waist, once per loaded body.
{
  const humans = await fs.readFile(process.env.HUMANS_JS ?? new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/import \{ fitGown \} from '\.\/human-gown\.js';/.test(humans), 'humans.js imports fitGown');
  assert(/const gltf = await loader\.parseAsync\(.*\);(?:(?!return gltf)[\s\S]){0,1400}fitSleeves\(gltf\.scene\);(?:(?!return gltf)[\s\S]){0,200}fitGown\(gltf\.scene\);(?:(?!return gltf)[\s\S]){0,200}fitWaist\(gltf\.scene\);/.test(humans), 'parse() cuts the gown of the shared source, after the sleeves and before the waist');
  console.log('humans.js parse(): fitGown after fitSleeves, before fitWaist: PASS');
}
console.log('human gown: PASS');

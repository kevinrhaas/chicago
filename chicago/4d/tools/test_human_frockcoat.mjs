// SPDX-License-Identifier: GPL-3.0-or-later
// T-3553: John J. Glessner's frock coat cut as a 1904 frock coat (renderers/web/js/human-frockcoat.js).
// The catalogue review (data/people_match/subjects/glessner_john_j_1904.match.json) found it
// read as a cassock: skirts below the knee, buttoned to the throat with the lapels and
// waistcoat lost in black, no waist, no vent, a low grey collar; the owner approved the
// tailoring fixes on 2026-11-17. On the real export, every level, on the CPU, with every
// parse pass humans.js runs before it (dressCollars, easeSeats, fitCoats, fitSleeves) and
// after it (fitWaist, engraveSilver), standing (the idle clip) and through a stride (the walk
// clip and human-skirt.js), before and after. It must:
//  - put the hem at the knee: at least HEM_MIN_M above the knee joint at bind and standing,
//    and never a hem under the knee by more than STRIDE_HEM_M on the walk;
//  - show the shirt front in a V inside the waistcoat, inside the lapels, from the front,
//    standing and walking: at least V_MIN_CM2 of shirt below the collar on the near levels
//    (V_FAR_CM2 on the far ones, never less than drawn), no skin of the chest, the lapels
//    still showing;
//  - draw the waist in on the near levels: the coat's girth at the seam at least WAIST_MIN_M under
//    the drawn one (the far levels' never over it),
//    the layers' order kept (nothing under the coat showing through it at the waist from any
//    side, standing or walking, more than drawn);
//  - part the skirts at a centre-back vent on the near levels: an open cut up the middle of
//    the back at least VENT_MIN_M long, apart at the hem by VENT_HEM_M, lapped left over right
//    at its top; from behind, the vent's foot shows open and its top does not;
//  - stand the collar up and draw it white: the collar at the back at least COLLAR_MIN_M over
//    the coat's collar, the shirt's cloth in the recipe's linear colour without the picture;
//  - change nothing else: no other piece of the body moves but the trousers' top in the waist,
//    UVs and skin weights of every drawn vertex kept, the vent's copies equal to their own
//    point in every attribute; other bodies untouched; human-coat.js's closeVents still finds
//    no vent of its own on this coat; once per loaded body; wired in humans.js after fitSleeves
//    and before fitWaist.
// FROCK_OLD=1 runs it on the code before this fix (fitFrockCoat a no-op): it must fail.
import fs from 'node:fs/promises';
import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
const here = new URL('../', import.meta.url);
const vendor = new URL('renderers/web/vendor/three-0.185.1/', here);
const threeURL = new URL('three.module.js', vendor).href;
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
const mod = (f) => import(new URL(`renderers/web/js/${f}`, here));
const { dressCollars } = await mod('human-collar.js');
const { easeSeats } = await mod('human-seat.js');
const { fitCoats } = await mod('human-coat.js');
const { fitSleeves } = await mod('human-sleeve.js');
const { fitWaist } = await mod('human-waist.js');
const { engraveSilver } = await mod('human-silver.js');
const { createHumanSkirt } = await mod('human-skirt.js');
const frock = await mod('human-frockcoat.js');
const OLD = process.env.FROCK_OLD === '1';
const fitFrockCoat = OLD ? () => null : frock.fitFrockCoat;

const ASSET = 'glessner_john_j_1904';
export const HEM_MIN_M = 0.015, STRIDE_HEM_M = 0.03, V_MIN_CM2 = 75, V_FAR_CM2 = 60, WAIST_MIN_M = 0.03;
export const VENT_MIN_M = 0.35, VENT_HEM_M = 0.015, COLLAR_MIN_M = 0.04, POKE_TOL_CM2 = 1;

function geometryOnly(bytes) {
  const n = bytes.readUInt32LE(12), doc = JSON.parse(bytes.subarray(20, 20 + n));
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    // The base colour picture is kept as a flag (the shirt's is the collar's colour); its pixels are not read.
    if (m.pbrMetallicRoughness) { if (m.pbrMetallicRoughness.baseColorTexture) m.extras = { ...(m.extras ?? {}), hadPicture: true }; delete m.pbrMetallicRoughness.baseColorTexture; delete m.pbrMetallicRoughness.metallicRoughnessTexture; }
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
/** Every pass of humans.js's parse, in its order, with this one where it is wired. */
function passes(scene, mine = true) {
  dressCollars(scene); easeSeats(scene); fitCoats(scene); fitSleeves(scene);
  const r = mine ? fitFrockCoat(scene) : null;
  fitWaist(scene); engraveSilver(scene);
  return r;
}
const matName = (o) => (Array.isArray(o.material) ? o.material[0] : o.material)?.name ?? '';
const meshesOf = (scene) => { const out = []; scene.traverse((o) => { if (o.isSkinnedMesh && o.geometry.index) out.push(o); }); return out; };
const piece = (m) => m.name.replace(`${ASSET}_`, '').replace(/_lod\d+$/, '');
const byPiece = (scene) => Object.fromEntries(meshesOf(scene).map((m) => [piece(m), m]));
const readAttr = (a) => { const out = new Float64Array(a.count * a.itemSize); for (let i = 0; i < a.count; i++) for (let c = 0; c < a.itemSize; c++) out[i * a.itemSize + c] = a.getComponent(i, c); return out; };

/** The bind frame: O mid-hips, U up, L left, F forward; the knee's and the neck's heights. */
function bindFrame(mesh) {
  const sk = mesh.skeleton, J = (n) => new THREE.Vector3().setFromMatrixPosition(sk.boneInverses[sk.bones.findIndex((b) => b.name === n)].clone().invert());
  const O = J('thigh_l').add(J('thigh_r')).multiplyScalar(0.5), U = O.clone().sub(J('foot_l').add(J('foot_r')).multiplyScalar(0.5)).normalize();
  const L = J('thigh_l').sub(J('thigh_r')); L.addScaledVector(U, -L.dot(U)).normalize();
  const F = new THREE.Vector3().crossVectors(L, U).normalize();
  return { O, U, L, F, knee: (J('calf_l').sub(O).dot(U) + J('calf_r').sub(O).dot(U)) / 2, neck: J('neck_01').sub(O).dot(U) };
}
function bindPoints(mesh, fr) {
  const pos = mesh.geometry.attributes.position, v = new THREE.Vector3(), P = new Float64Array(pos.count * 3);
  for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i).applyMatrix4(mesh.bindMatrix).sub(fr.O); P[i * 3] = v.dot(fr.L); P[i * 3 + 1] = v.dot(fr.U); P[i * 3 + 2] = v.dot(fr.F); }
  return P;
}
/** Posed points in the world. */
function posed(mesh) {
  mesh.skeleton.update();
  const pos = mesh.geometry.attributes.position, P = new Float64Array(pos.count * 3), v = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) { mesh.getVertexPosition(i, v); v.applyMatrix4(mesh.matrixWorld); P[i * 3] = v.x; P[i * 3 + 1] = v.y; P[i * 3 + 2] = v.z; }
  return P;
}
function frameNow(scene) {
  const w = (n) => scene.getObjectByName(n).getWorldPosition(new THREE.Vector3());
  const O = w('thigh_l').add(w('thigh_r')).multiplyScalar(0.5), U = O.clone().sub(w('foot_l').add(w('foot_r')).multiplyScalar(0.5)).normalize();
  const L = w('thigh_l').sub(w('thigh_r')); L.addScaledVector(U, -L.dot(U)).normalize();
  return { O, U, L, F: new THREE.Vector3().crossVectors(L, U).normalize(), w };
}
/** An orthographic id buffer: each pixel the tag of the nearest layer toward `dir`'s viewer. */
function idBuffer(layers, dir, up, centre, half, px) {
  const F = dir.clone().normalize(), R = new THREE.Vector3().crossVectors(up, F).normalize(), U = new THREE.Vector3().crossVectors(F, R);
  const N = Math.round(2 * half / px), depth = new Float64Array(N * N).fill(-Infinity), tag = new Array(N * N).fill('');
  const pr = (P, i, o) => { const x = P[i * 3] - centre.x, y = P[i * 3 + 1] - centre.y, z = P[i * 3 + 2] - centre.z; o[0] = (x * R.x + y * R.y + z * R.z + half) / px; o[1] = (half - (x * U.x + y * U.y + z * U.z)) / px; o[2] = x * F.x + y * F.y + z * F.z; };
  const a = [0, 0, 0], b = [0, 0, 0], c = [0, 0, 0];
  for (const Ly of layers) for (let t = 0; t < Ly.idx.length / 3; t++) {
    pr(Ly.P, Ly.idx[t * 3], a); pr(Ly.P, Ly.idx[t * 3 + 1], b); pr(Ly.P, Ly.idx[t * 3 + 2], c);
    const x0 = Math.max(0, Math.floor(Math.min(a[0], b[0], c[0]))), x1 = Math.min(N - 1, Math.ceil(Math.max(a[0], b[0], c[0])));
    const y0 = Math.max(0, Math.floor(Math.min(a[1], b[1], c[1]))), y1 = Math.min(N - 1, Math.ceil(Math.max(a[1], b[1], c[1])));
    if (x0 > x1 || y0 > y1) continue;
    const den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1]); if (Math.abs(den) < 1e-12) continue;
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) {
      const X = x + 0.5, Y = y + 0.5;
      const l0 = ((b[1] - c[1]) * (X - c[0]) + (c[0] - b[0]) * (Y - c[1])) / den, l1 = ((c[1] - a[1]) * (X - c[0]) + (a[0] - c[0]) * (Y - c[1])) / den, l2 = 1 - l0 - l1;
      if (l0 < -1e-6 || l1 < -1e-6 || l2 < -1e-6) continue;
      const z = l0 * a[2] + l1 * b[2] + l2 * c[2], k = y * N + x;
      if (z > depth[k]) { depth[k] = z; tag[k] = Ly.tag; }
    }
  }
  return { N, tag, depth, R, U, half, px, centre };
}
const tagOf = (name) => (/frock_coat_lapels/.test(name) ? 'lapel' : /frock_coat/.test(name) ? 'coat' : /shirt/.test(name) ? 'shirt' : /tie/.test(name) ? 'tie'
  : /waistcoat/.test(name) ? 'waistcoat' : /trousers/.test(name) ? 'trousers' : /body/.test(name) ? 'skin' : 'other');
/** Where a pixel is, in the frame (x left, y up from the hips). */
const where = (buf, fr, k) => {
  const p = buf.centre.clone().addScaledVector(buf.R, (k % buf.N + 0.5) * buf.px - buf.half).addScaledVector(buf.U, buf.half - (Math.floor(k / buf.N) + 0.5) * buf.px).sub(fr.O);
  return [p.dot(fr.L), p.dot(fr.U)];
};

/** Measures of one posed frame: hem vs knee, the shirt V and bare chest from the front, things
 * under the coat showing through it at the waist from four sides, and the vent from behind. */
function measurePosed(scene, ms, frs, seamY, vent) {
  const fr = frameNow(scene), layers = ms.filter((m) => m.visible && !/^(eyes|hair|headwear)/.test(matName(m))).map((m) => ({ P: posed(m), idx: m.geometry.index.array, tag: tagOf(m.name), m }));
  const k = (fr.w('calf_l').sub(fr.O).dot(fr.U) + fr.w('calf_r').sub(fr.O).dot(fr.U)) / 2;
  const sk = layers.find((l) => /frock_coat_skirts/.test(l.m.name));
  let hem = Infinity;
  for (let i = 0; i < sk.P.length / 3; i++) hem = Math.min(hem, (sk.P[i * 3] - fr.O.x) * fr.U.x + (sk.P[i * 3 + 1] - fr.O.y) * fr.U.y + (sk.P[i * 3 + 2] - fr.O.z) * fr.U.z);
  const px = 0.003, cm2 = px * px * 1e4;
  // Front, a little from above (the town's eye over a man at three metres).
  const front = idBuffer(layers, fr.F.clone().addScaledVector(fr.U, 0.15), fr.U, fr.O.clone().addScaledVector(fr.U, frs.neck - 0.2), 0.3, px);
  let shirtV = 0, chest = 0, lapel = 0;
  for (let q = 0; q < front.tag.length; q++) {
    const t = front.tag[q]; if (!t) continue;
    const [x, y] = where(front, fr, q);
    if (y > frs.neck - 0.03 || y < frs.neck - 0.32) continue;
    if (t === 'lapel' && Math.abs(x) < 0.2) lapel++;
    if (Math.abs(x) > 0.13) continue;
    if (t === 'shirt' && y < frs.neck - 0.05) shirtV++;
    if (t === 'skin') chest++;
  }
  // The waist from four sides: an inner layer's pixel with the coat both sides of it along its row within 2 cm.
  let poke = 0;
  for (const d of [fr.F, fr.F.clone().negate(), fr.L, fr.L.clone().negate()]) {
    const buf = idBuffer(layers, d, fr.U, fr.O.clone().addScaledVector(fr.U, seamY), 0.3, px), N = buf.N, reach = Math.round(0.02 / px);
    for (let q = 0; q < N * N; q++) {
      const t = buf.tag[q]; if (!t || t === 'coat' || t === 'lapel' || t === 'other') continue;
      const [, y] = where(buf, fr, q); if (Math.abs(y - seamY) > 0.06) continue;
      let l = false, r = false; const x = q % N;
      for (let j = 1; j <= reach; j++) { if (x - j >= 0 && buf.tag[q - j] === 'coat') l = true; if (x + j < N && buf.tag[q + j] === 'coat') r = true; }
      if (l && r) poke++;
    }
  }
  // The vent from behind: below the skirts' top, within 4 cm of the middle, something else between coat.
  let ventFoot = 0, ventTop = 0;
  if (vent) {
    const buf = idBuffer(layers, fr.F.clone().negate(), fr.U, fr.O.clone().addScaledVector(fr.U, -0.15), 0.4, px), N = buf.N, reach = Math.round(0.03 / px);
    // A pixel of the vent: something other than the skirts' outside (the trousers, the air
    // between the legs, or the skirts' own cloth a centimetre further off: their inside through
    // the gap), between the skirts' outside on both sides.
    const D = buf.depth;
    for (let q = 0; q < N * N; q++) {
      const t = buf.tag[q]; if (t === 'other') continue;
      const [x, y] = where(buf, fr, q); if (Math.abs(x) > 0.04 || y > vent.to || y < hem - 0.01) continue;
      // The skirts' outside each side: the nearest of their cloth to the eye within 3 cm along the row.
      let l = -Infinity, r = -Infinity; const c = q % N;
      for (let j = 1; j <= reach; j++) {
        if (c - j >= 0 && buf.tag[q - j] === 'coat') l = Math.max(l, D[q - j]);
        if (c + j < N && buf.tag[q + j] === 'coat') r = Math.max(r, D[q + j]);
      }
      if (l === -Infinity || r === -Infinity) continue;
      if (t === 'coat' && !(D[q] < Math.min(l, r) - 0.01)) continue;
      if (y < vent.from + (vent.to - vent.from) * 0.35) ventFoot++; else if (y > vent.from + (vent.to - vent.from) * 0.6) ventTop++;
    }
  }
  return { hemAboveKnee: hem - k, shirtV: shirtV * cm2, chest: chest * cm2, lapel: lapel * cm2, poke: poke * cm2, ventFoot: ventFoot * cm2, ventTop: ventTop * cm2 };
}
/** Standing (the idle clip, 1 s in) and through the walk (every 6th frame of 2 s). */
function runPoses(gltf, frs, seamY, vent) {
  const scene = SkeletonUtils.clone(gltf.scene), root = new THREE.Group(); root.add(scene);
  root.rotation.y = 0.7; root.position.set(3, 0, -2);
  const ms = meshesOf(scene), out = { stand: null, walk: [] };
  const mixer = new THREE.AnimationMixer(scene);
  const idle = mixer.clipAction(gltf.animations.find((a) => a.name === 'idle')); idle.play(); mixer.update(1.0);
  const sk = createHumanSkirt({ id: 'frock-test', scene });
  for (let f = 0; f < 10; f++) sk?.apply(1 / 30, { state: 'standing', root });
  root.updateMatrixWorld(true);
  out.stand = measurePosed(scene, ms, frs, seamY, vent);
  idle.stop(); mixer.clipAction(gltf.animations.find((a) => a.name === 'walk')).play(); mixer.update(0);
  for (let f = 0; f < 60; f++) {
    mixer.update(1 / 30); sk?.apply(1 / 30, { state: 'walking', root }); root.updateMatrixWorld(true);
    if (f % 6 === 5 && f > 10) out.walk.push(measurePosed(scene, ms, frs, seamY, vent));
  }
  return out;
}
/** The coat's girth at a height: the perimeter of the hull of its section (bind). */
function girth(Ps, y, half = 0.008) {
  const pts = [];
  for (const P of Ps) for (let i = 0; i < P.length / 3; i++) if (Math.abs(P[i * 3 + 1] - y) < half && Math.abs(P[i * 3]) < 0.3) pts.push([P[i * 3], P[i * 3 + 2]]);
  pts.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
  const lower = [], upper = [];
  for (const p of pts) { while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop(); lower.push(p); }
  for (const p of pts.slice().reverse()) { while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop(); upper.push(p); }
  const h = lower.slice(0, -1).concat(upper.slice(0, -1));
  let per = 0; for (let i = 0; i < h.length; i++) { const a = h[i], b = h[(i + 1) % h.length]; per += Math.hypot(a[0] - b[0], a[1] - b[1]); }
  return per;
}
/** The vent in bind: open edges up the middle of the back of the skirts; their length and the
 * two sides' edges apart at the hem (+ apart, - lapped) and at the top (left's x - right's x). */
function ventOf(mesh, fr) {
  const P = bindPoints(mesh, fr), a = mesh.geometry.index.array, n = P.length / 3;
  const key = (i) => `${Math.round(P[i * 3] * 2e4)},${Math.round(P[i * 3 + 1] * 2e4)},${Math.round(P[i * 3 + 2] * 2e4)}`;
  const g = new Int32Array(n), ids = new Map();
  for (let i = 0; i < n; i++) { const k = key(i); let v = ids.get(k); if (v === undefined) ids.set(k, (v = ids.size)); g[i] = v; }
  const edges = new Map(), W = 4194304;
  for (let t = 0; t < a.length; t += 3) for (let k = 0; k < 3; k++) {
    const p = g[a[t + k]], q = g[a[t + (k + 1) % 3]], e = p < q ? p * W + q : q * W + p;
    const c = edges.get(e); edges.set(e, c ? [c[0] + 1, c[1], c[2], c[3]] : [1, a[t + k], a[t + (k + 1) % 3], t]);
  }
  // A vent edge: open, behind, within 3 cm of the middle, running down; its side is the side of its triangle.
  let len = 0, lo = Infinity, hi = -Infinity; const side = { l: [], r: [] };
  for (const [, [c, i, j, t]] of edges) {
    if (c !== 1) continue;
    if (P[i * 3 + 2] > -0.03 || P[j * 3 + 2] > -0.03 || Math.abs(P[i * 3]) > 0.03 || Math.abs(P[j * 3]) > 0.03) continue;
    const dy = Math.abs(P[i * 3 + 1] - P[j * 3 + 1]); if (dy < 0.5 * Math.abs(P[i * 3] - P[j * 3])) continue;
    let cx = 0; for (let k = 0; k < 3; k++) cx += P[a[t + k] * 3]; cx /= 3;
    const s = cx > (P[i * 3] + P[j * 3]) / 2 ? 'l' : 'r';
    side[s].push([P[i * 3 + 1], P[i * 3]], [P[j * 3 + 1], P[j * 3]]);
    if (s === 'l') { len += Math.hypot(P[i * 3] - P[j * 3], dy, P[i * 3 + 2] - P[j * 3 + 2]); lo = Math.min(lo, P[i * 3 + 1], P[j * 3 + 1]); hi = Math.max(hi, P[i * 3 + 1], P[j * 3 + 1]); }
  }
  if (!side.l.length || !side.r.length) return { len: 0, hemGap: 0, topGap: 0, from: 0, to: 0 };
  const at = (list, y) => { let best = null, d = Infinity; for (const [yy, x] of list) if (Math.abs(yy - y) < d) { d = Math.abs(yy - y); best = x; } return best; };
  return { len, from: lo, to: hi, hemGap: at(side.l, lo) - at(side.r, lo), topGap: at(side.l, hi - 0.03) - at(side.r, hi - 0.03) };
}
function bindMeasures(scene) {
  const M = byPiece(scene), fr = bindFrame(M.frock_coat_body);
  const sk = bindPoints(M.frock_coat_skirts, fr), body = bindPoints(M.frock_coat_body, fr), shirt = bindPoints(M.shirt_standing_collar, fr);
  let hem = Infinity, top = -Infinity, bodyLow = Infinity;
  for (let i = 0; i < sk.length / 3; i++) { hem = Math.min(hem, sk[i * 3 + 1]); top = Math.max(top, sk[i * 3 + 1]); }
  for (let i = 0; i < body.length / 3; i++) if (Math.abs(body[i * 3]) < 0.25) bodyLow = Math.min(bodyLow, body[i * 3 + 1]);
  const seam = (bodyLow + top) / 2;
  // The collar at the back: the shirt's top behind the neck over the coat's top there.
  let collar = -Infinity, coatTop = -Infinity;
  for (let i = 0; i < shirt.length / 3; i++) if (Math.abs(shirt[i * 3]) < 0.03 && shirt[i * 3 + 2] < 0) collar = Math.max(collar, shirt[i * 3 + 1]);
  for (let i = 0; i < body.length / 3; i++) if (Math.abs(body[i * 3]) < 0.03 && body[i * 3 + 2] < 0) coatTop = Math.max(coatTop, body[i * 3 + 1]);
  const mat = Array.isArray(M.shirt_standing_collar.material) ? M.shirt_standing_collar.material[0] : M.shirt_standing_collar.material;
  const linear = mat.color.clone(); // three keeps colours linear
  const pictured = !!mat.map || (mat.userData?.hadPicture && !mat.userData?.chicagoFrockCollar);
  // A flat picture at 8-bit 202 (sRGB), as the export draws the shirt, is 0.59 linear under the colour.
  const lum = (0.2126 * linear.r + 0.7152 * linear.g + 0.0722 * linear.b) * (pictured ? 0.59 : 1);
  return { fr, hem, top, seam, hemAboveKnee: hem - fr.knee, girth: girth([body, sk], seam), collarOver: collar - coatTop, collarLum: lum, vent: ventOf(M.frock_coat_skirts, fr) };
}

// ---- every level ---------------------------------------------------------------------------
const failures = [], lines = [];
const check = (ok, msg) => { if (!ok) failures.push(msg); };
const r2 = (x) => Math.round(x * 1000) / 1000, c1 = (x) => Math.round(x * 10) / 10;
for (const lod of [0, 1, 2, 3]) {
  const before = await load(ASSET, lod), after = await load(ASSET, lod);
  passes(before.scene, false);
  const drawn = new Map(meshesOf(after.scene).map((m) => [m, { n: m.geometry.attributes.position.count, pos: readAttr(m.geometry.attributes.position), idx: Array.from(m.geometry.index.array),
    keep: Object.fromEntries(Object.entries(m.geometry.attributes).filter(([k]) => k !== 'position' && k !== 'normal').map(([k, a]) => [k, readAttr(a)])) }]));
  // The passes before this one, then this one, then the rest: what this one changes is measured against what it was given.
  dressCollars(after.scene); easeSeats(after.scene); fitCoats(after.scene); fitSleeves(after.scene);
  const given = new Map(meshesOf(after.scene).map((m) => [m, { pos: readAttr(m.geometry.attributes.position), keep: Object.fromEntries(Object.entries(m.geometry.attributes).filter(([k]) => k !== 'position' && k !== 'normal').map(([k, a]) => [k, readAttr(a)])), idx: Array.from(m.geometry.index.array) }]));
  const t0 = performance.now(), report = fitFrockCoat(after.scene), ms = performance.now() - t0;
  fitWaist(after.scene); engraveSilver(after.scene);
  const B = bindMeasures(before.scene), A = bindMeasures(after.scene);
  const near = lod <= 1;
  // human-coat.js's lap is not this coat's: closeVents found nothing of its own on it.
  check(Array.isArray(after.scene.userData.chicagoVents) && after.scene.userData.chicagoVents.length === 0, `lod${lod}: closeVents lapped a vent of its own on the frock coat`);
  // 1. length
  check(A.hemAboveKnee >= HEM_MIN_M, `lod${lod}: hem ${r2(A.hemAboveKnee)} m from the knee at bind (want >= ${HEM_MIN_M})`);
  check(A.hemAboveKnee <= 0.08, `lod${lod}: hem ${r2(A.hemAboveKnee)} m over the knee: no longer a frock coat's`);
  // 2. waist
  if (near) check(B.girth - A.girth >= WAIST_MIN_M, `lod${lod}: the waist drawn in by ${r2(B.girth - A.girth)} m (want >= ${WAIST_MIN_M})`);
  else check(A.girth <= B.girth + 0.002, `lod${lod}: the waist let out by ${r2(A.girth - B.girth)} m`);
  // 4. collar
  check(A.collarOver >= COLLAR_MIN_M, `lod${lod}: the collar stands ${r2(A.collarOver)} m over the coat's at the back (want >= ${COLLAR_MIN_M})`);
  check(A.collarLum >= 0.75, `lod${lod}: the collar's cloth ${r2(A.collarLum)} linear (want >= 0.75, the recipe's 0.8)`);
  // 5. vent (near levels; the far ones as drawn)
  if (near) {
    check(A.vent.len >= VENT_MIN_M, `lod${lod}: the vent is ${r2(A.vent.len)} m long (want >= ${VENT_MIN_M})`);
    check(A.vent.hemGap >= VENT_HEM_M, `lod${lod}: the vent ${r2(A.vent.hemGap)} m apart at the hem (want >= ${VENT_HEM_M})`);
    check(A.vent.topGap < 0, `lod${lod}: the vent not lapped left over right at its top (${r2(A.vent.topGap)})`);
  }
  // Topology, UVs, skin weights.
  for (const m of meshesOf(after.scene)) {
    const d = drawn.get(m), gv = given.get(m), p = piece(m), pos = readAttr(m.geometry.attributes.position);
    if (p === 'frock_coat_skirts' && !OLD) {
      const n0 = d.n, n1 = m.geometry.attributes.position.count;
      check(n1 >= n0, `lod${lod}: the skirts lost vertices`);
      for (const [k, arr] of Object.entries(gv.keep)) {
        const now = readAttr(m.geometry.attributes[k]), w = m.geometry.attributes[k].itemSize;
        let bad = 0; for (let i = 0; i < n0 * w; i++) if (now[i] !== arr[i]) bad++;
        check(bad === 0, `lod${lod}: the skirts' ${k} changed on ${bad} drawn values`);
      }
      // Each copy: equal in every kept attribute to the point it was cut from (same place before the shift).
      if (n1 > n0) {
        const idx = Array.from(m.geometry.index.array), from = new Map();
        for (let t = 0; t < idx.length; t++) if (idx[t] !== gv.idx[t]) { if (idx[t] < n0) failures.push(`lod${lod}: the vent re-pointed a corner to a drawn vertex`); else from.set(idx[t], gv.idx[t]); }
        check(from.size === n1 - n0, `lod${lod}: ${n1 - n0} copies, ${from.size} used`);
        for (const [j, i] of from) for (const [k, arr] of Object.entries(gv.keep)) {
          const a = m.geometry.attributes[k], w = a.itemSize;
          for (let c = 0; c < w; c++) if (a.getComponent(j, c) !== arr[i * w + c]) { failures.push(`lod${lod}: copy ${j}'s ${k} is not its point's`); break; }
        }
      }
      continue;
    }
    check(m.geometry.attributes.position.count === d.n, `lod${lod}: ${p} vertex count changed`);
    check(gv.idx.every((v, i) => v === m.geometry.index.array[i]), `lod${lod}: ${p} topology changed`);
    for (const [k, arr] of Object.entries(gv.keep)) {
      const now = readAttr(m.geometry.attributes[k]);
      check(now.every((v, i) => v === arr[i]), `lod${lod}: ${p} ${k} changed`);
    }
    if (!/^(frock_coat_body|frock_coat_lapels|waistcoat_high_cut|shirt_standing_collar|straight_trousers)$/.test(p)) {
      let moved = 0; for (let i = 0; i < pos.length; i++) if (pos[i] !== gv.pos[i]) moved++;
      check(moved === 0, `lod${lod}: ${p} moved (${moved} values)`);
    }
  }
  // Posed: standing and through the stride, before and after.
  const PB = runPoses(before, B.fr, B.seam, null), PA = runPoses(after, A.fr, A.seam, near ? A.vent : null);
  const all = (P) => [P.stand, ...P.walk];
  const worst = (P, f, pick = Math.min) => pick(...all(P).map(f));
  check(PA.stand.hemAboveKnee >= HEM_MIN_M, `lod${lod}: standing, the hem ${r2(PA.stand.hemAboveKnee)} m from the knee (want >= ${HEM_MIN_M})`);
  check(worst(PA, (m) => m.hemAboveKnee) >= -STRIDE_HEM_M, `lod${lod}: walking, the hem ${r2(worst(PA, (m) => m.hemAboveKnee))} m from the knee (want >= -${STRIDE_HEM_M})`);
  const vMin = near ? V_MIN_CM2 : V_FAR_CM2;
  check(worst(PA, (m) => m.shirtV) >= Math.max(vMin, worst(PB, (m) => m.shirtV) + 1), `lod${lod}: the shirt front shows ${c1(worst(PA, (m) => m.shirtV))} cm2 in the V at worst (drawn ${c1(worst(PB, (m) => m.shirtV))}; want >= ${vMin})`);
  check(worst(PA, (m) => m.chest, Math.max) <= worst(PB, (m) => m.chest, Math.max) + 0.2, `lod${lod}: bare chest ${c1(worst(PA, (m) => m.chest, Math.max))} cm2 in the V (drawn ${c1(worst(PB, (m) => m.chest, Math.max))})`);
  check(worst(PA, (m) => m.lapel) >= 0.8 * worst(PB, (m) => m.lapel), `lod${lod}: the lapels show ${c1(worst(PA, (m) => m.lapel))} cm2 (drawn ${c1(worst(PB, (m) => m.lapel))})`);
  check(worst(PA, (m) => m.poke, Math.max) <= worst(PB, (m) => m.poke, Math.max) + POKE_TOL_CM2, `lod${lod}: under the coat showing through it at the waist, ${c1(worst(PA, (m) => m.poke, Math.max))} cm2 (drawn ${c1(worst(PB, (m) => m.poke, Math.max))})`);
  if (near) {
    check(PA.stand.ventFoot >= 0.5 && worst(PA, (m) => m.ventFoot) >= 0.5, `lod${lod}: the vent's foot shows ${c1(worst(PA, (m) => m.ventFoot))} cm2 from behind at worst (want >= 0.5)`);
    check(worst(PA, (m) => m.ventTop, Math.max) <= 1, `lod${lod}: the vent's top shows ${c1(worst(PA, (m) => m.ventTop, Math.max))} cm2 through it (want <= 1)`);
  }
  lines.push(`lod${lod}: hem ${r2(B.hemAboveKnee)} -> ${r2(A.hemAboveKnee)} m from the knee (standing ${r2(PB.stand.hemAboveKnee)} -> ${r2(PA.stand.hemAboveKnee)}, walking worst ${r2(worst(PB, (m) => m.hemAboveKnee))} -> ${r2(worst(PA, (m) => m.hemAboveKnee))}); `
    + `waist girth ${r2(B.girth)} -> ${r2(A.girth)} m; shirt V ${c1(worst(PB, (m) => m.shirtV))} -> ${c1(worst(PA, (m) => m.shirtV))} cm2 at worst; lapels ${c1(worst(PA, (m) => m.lapel))} cm2; `
    + `poke ${c1(worst(PB, (m) => m.poke, Math.max))} -> ${c1(worst(PA, (m) => m.poke, Math.max))} cm2; collar ${r2(B.collarOver)} -> ${r2(A.collarOver)} m over the coat, ${r2(B.collarLum)} -> ${r2(A.collarLum)} linear; `
    + (near ? `vent ${r2(A.vent.len)} m, ${r2(A.vent.hemGap)} m apart at the hem, ${r2(A.vent.topGap)} at the top, foot ${c1(worst(PA, (m) => m.ventFoot))} / top ${c1(worst(PA, (m) => m.ventTop, Math.max))} cm2; ` : 'vent as drawn; ')
    + `${Math.round(ms)} ms`);
  // Once per loaded body.
  if (!OLD) {
    const again = fitFrockCoat(after.scene);
    check(again === report && report !== null, `lod${lod}: a second call did not return the first report`);
  }
}
// Other bodies are left as drawn.
for (const other of ['peck_philip_1835', 'trader_1812', 'anonymous_working_driver_1904', 'williamson_mattie_1904_cook_study']) {
  const g = await load(other, 0); passes(g.scene, false);
  const before = meshesOf(g.scene).map((m) => readAttr(m.geometry.attributes.position));
  const r = frock.fitFrockCoat(g.scene);
  const same = meshesOf(g.scene).every((m, i) => readAttr(m.geometry.attributes.position).every((v, j) => v === before[i][j]));
  check(r === null && same, `${other}: changed by the frock coat's fit`);
}
// Wired in humans.js's parse, after fitSleeves and before fitWaist.
const humans = await fs.readFile(process.env.FROCK_HUMANS_JS ?? new URL('renderers/web/js/humans.js', here), 'utf8');
check(/import \{ fitFrockCoat \} from '\.\/human-frockcoat\.js';/.test(humans), 'humans.js does not import fitFrockCoat');
const parseBody = humans.slice(humans.indexOf('async function parse('), humans.indexOf('return gltf;', humans.indexOf('async function parse(')));
const at = (s) => parseBody.indexOf(s);
check(at('fitSleeves(gltf.scene);') >= 0 && at('fitSleeves(gltf.scene);') < at('fitFrockCoat(gltf.scene);') && at('fitFrockCoat(gltf.scene);') < at('fitWaist(gltf.scene);'),
  'humans.js parse(): fitFrockCoat(gltf.scene) not between fitSleeves and fitWaist');

for (const l of lines) console.log(`  ${l}`);
if (failures.length) {
  for (const f of failures) console.log(`FAIL ${f}`);
  console.log(`human-frockcoat${OLD ? ' (old code)' : ''}: ${failures.length} failure(s): FAIL`);
  process.exit(1);
}
assert.ok(true);
console.log('human-frockcoat: knee-length skirts, a waist, the shirt front in the lapels\' V, a white standing collar and a centre-back vent on every level, standing and walking: PASS');

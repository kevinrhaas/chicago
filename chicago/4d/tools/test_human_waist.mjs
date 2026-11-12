// SPDX-License-Identifier: GPL-3.0-or-later
// T-3553: a belted waist sits on the body, and trade silver is engraved (human-waist.js,
// human-silver.js). Kevin, 2026-11-12, in the 1812 camp: "the native belts do not wrap
// tightly, they float as well as their bottom pants float around the waist, and that silver
// band should have detail? dont do that if it will blow things up".
// On every level of the real Potawatomi man it must: draw the belt in to just outside the
// shirt and skirt (a man without his blanket) and still outside the blanket (a man with it);
// close the ledge where the shirt's skirt began wider than the shirt; weight the belt as the
// shirt beneath it (never a thigh); keep the belt on the shirt through the walk and the idle
// where it used to stand off in a hoop; be idempotent and leave other bodies alone. The silver
// must be a shader patch only (no texture, no geometry), one program for bands and brooches,
// and both wired into humans.js's parse, before any clone.
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
const { fitWaist, EASE, HOLD_M, BLEND_M } = await import(new URL('renderers/web/js/human-waist.js', here));
const { engraveSilver, SILVER } = await import(new URL('renderers/web/js/human-silver.js', here));
const { restMatrix } = await import(new URL('renderers/web/js/human-skin.js', here));

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
const parse = async (asset, lod) => new GLTFLoader().setMeshoptDecoder(MeshoptDecoder)
  .parseAsync(geometryOnly(await fs.readFile(new URL(`assets/humans/web/${asset}.lod${lod}.glb`, here))), '');
const mesh = (scene, piece) => { let m = null; scene.traverse((o) => { if (o.isSkinnedMesh && new RegExp(`_${piece}_lod\\d+$`).test(o.name)) m = o; }); return m; };

/** Bind points (metres, the figure's frame) of a mesh. */
function bind(m, root) {
  const R = restMatrix(m, root), p = m.geometry.attributes.position, v = new THREE.Vector3(), out = [];
  for (let i = 0; i < p.count; i++) out.push(v.fromBufferAttribute(p, i).applyMatrix4(R).toArray());
  return out;
}
/** Points across a mesh's triangles (its cloth between the vertices too), bind metres. */
function across(m, pts) {
  const idx = m.geometry.index, out = [];
  for (let f = 0; f < idx.count / 3; f++) {
    const [a, b, c] = [0, 1, 2].map((k) => pts[idx.getX(f * 3 + k)]);
    for (let i = 0; i <= 5; i++) for (let j = 0; j <= 5 - i; j++) { const u = i / 5, v = j / 5, w = 1 - u - v; out.push([0, 1, 2].map((k) => a[k] * u + b[k] * v + c[k] * w)); }
  }
  return out;
}
/** Largest radius from the body's axis in each of n sectors, of points between y0 and y1. */
function sectors(pts, y0, y1, n = 24) {
  const r = new Array(n).fill(0);
  for (const [x, y, z] of pts) if (y >= y0 && y <= y1) { const k = Math.floor(((Math.atan2(x, z) + Math.PI) / (2 * Math.PI)) * n) % n; r[k] = Math.max(r[k], Math.hypot(x, z)); }
  return r;
}
function innerSectors(pts, n = 24) {
  const r = new Array(n).fill(Infinity);
  for (const [x, , z] of pts) { const k = Math.floor(((Math.atan2(x, z) + Math.PI) / (2 * Math.PI)) * n) % n; r[k] = Math.min(r[k], Math.hypot(x, z)); }
  return r;
}
/** Posed: the belt's vertices' distance to the nearest posed shirt or skirt cloth (sampled across its triangles), worst of all. */
function posedStandOff(scene, belt, under, mixer, clip, times) {
  let worst = 0;
  for (const t of times) {
    mixer.setTime(t); scene.updateMatrixWorld(true);
    const pose = (m) => { const p = m.geometry.attributes.position, out = []; for (let i = 0; i < p.count; i++) { const v = new THREE.Vector3().fromBufferAttribute(p, i); m.applyBoneTransform(i, v); out.push(v.applyMatrix4(m.matrixWorld)); } return out; };
    const B = pose(belt), U = under.flatMap((m) => across(m, pose(m).map((v) => v.toArray())).map((q) => new THREE.Vector3(...q)));
    const y0 = Math.min(...B.map((v) => v.y)) - .03, y1 = Math.max(...B.map((v) => v.y)) + .03;
    const near = U.filter((v) => v.y > y0 && v.y < y1);
    for (const b of B) { let d = Infinity; for (const u of near) d = Math.min(d, b.distanceToSquared(u)); worst = Math.max(worst, Math.sqrt(d)); }
  }
  return worst;
}

const ASSET = 'potawatomi_man_1812';
for (const lod of [0, 1, 2, 3]) {
  const before = await parse(ASSET, lod), after = await parse(ASSET, lod);
  before.scene.updateMatrixWorld(true);
  const report = fitWaist(after.scene);
  assert(report && report.asset === ASSET, `lod${lod}: the waist is fitted`);
  assert.deepEqual(fitWaist(after.scene), report, `lod${lod}: a second call changes nothing`);
  const s = after.scene, shirt = mesh(s, 'trade_shirt'), skirt = mesh(s, 'trade_shirt_skirt'), belt = mesh(s, 'leather_belt'), wrap = mesh(s, 'blanket_wrap');
  const B0 = bind(mesh(before.scene, 'leather_belt'), before.scene), B = bind(belt, s);
  const S = bind(shirt, s), K = bind(skirt, s), W = bind(wrap, s), K0 = bind(mesh(before.scene, 'trade_shirt_skirt'), before.scene);
  const by = B.map((p) => p[1]), lo = Math.min(...by), hi = Math.max(...by);
  // The stack under the belt (shirt and skirt), and the belt's inner face, sector by sector.
  const N = 96, stack = sectors([...across(shirt, S), ...across(skirt, K)], lo - .002, hi + .002, N), was = innerSectors(B0, N), now = innerSectors(B, N);
  const off0 = was.map((r, k) => r - stack[k]).filter(Number.isFinite), off = now.map((r, k) => r - stack[k]).filter(Number.isFinite);
  assert(Math.max(...off0) > .02, `lod${lod}: the belt used to stand off the shirt (${Math.max(...off0).toFixed(3)} m)`);
  // Within a centimetre everywhere (the cinch it sits on is the cloth's widest from just below the
  // belt to its top, so over the hollow of the back it spans a little air, as a belt does).
  const lift = EASE.skirt + EASE.wrap + EASE.belt;
  // On a simplified level (seen from further off) the blanket is a few long panels, and the belt
  // stands over the one that runs out furthest under it, so it may stand a little more off there.
  assert(Math.max(...off) < (lod ? .02 : lift + .003), `lod${lod}: the belt is drawn in to the shirt (worst ${Math.max(...off).toFixed(4)} m)`);
  const median = [...off].sort((p, q) => p - q)[Math.floor(off.length / 2)];
  assert(median < lift, `lod${lod}: and most of the way round it is within its own few millimetres (median ${median.toFixed(4)} m)`);
  // Never into it: each belt vertex against the cloth at its own angle and the two beside it.
  const bin = ([x, , z]) => Math.floor(((Math.atan2(x, z) + Math.PI) / (2 * Math.PI)) * N) % N;
  const into = Math.min(...B.map((p) => Math.hypot(p[0], p[2]) - Math.max(stack[bin(p)], stack[(bin(p) + 1) % N], stack[(bin(p) + N - 1) % N])));
  assert(into > -.002, `lod${lod}: and never into it (least ${into.toFixed(4)} m)`);
  // A man who wears his blanket: over the belt's height the blanket's and the skirt's cloth (between
  // their vertices too) are inside the belt; just below it the blanket hangs over the skirt.
  const wrapIn = sectors(across(wrap, W), lo, hi, N), skirtIn = sectors(across(skirt, K), lo, hi, N);
  for (let k = 0; k < N; k++) if (Number.isFinite(now[k])) {
    if (wrapIn[k] > 0) assert(wrapIn[k] < now[k], `lod${lod}: the blanket is under the belt (bin ${k}: ${wrapIn[k].toFixed(4)} < ${now[k].toFixed(4)})`);
    if (skirtIn[k] > 0) assert(skirtIn[k] < now[k], `lod${lod}: the skirt is under the belt (bin ${k}: ${skirtIn[k].toFixed(4)} < ${now[k].toFixed(4)})`);
  }
  const wrapBelow = sectors(across(wrap, W), lo - .03, lo - .004, N), skirtBelow = sectors(across(skirt, K), lo - .03, lo - .004, N);
  let tuck = 0;
  for (let k = 0; k < N; k++) if (wrapBelow[k] > 0 && skirtBelow[k] > 0) tuck = Math.max(tuck, skirtBelow[k] - wrapBelow[k]);
  const W0 = bind(mesh(before.scene, 'blanket_wrap'), before.scene), wB0 = sectors(across(mesh(before.scene, 'blanket_wrap'), W0), lo - .03, lo - .004, N), kB0 = sectors(across(mesh(before.scene, 'trade_shirt_skirt'), K0), lo - .03, lo - .004, N);
  let tuck0 = 0;
  for (let k = 0; k < N; k++) if (wB0[k] > 0 && kB0[k] > 0) tuck0 = Math.max(tuck0, kB0[k] - wB0[k]);
  console.log(`lod${lod}: skirt through the blanket below the belt ${tuck0.toFixed(4)} -> ${tuck.toFixed(4)} m`);
  // The far level (a few hundred triangles, a figure a few pixels tall) is allowed a centimetre.
  assert(tuck < Math.max(lod === 3 ? .012 : .003, tuck0 + .001), `lod${lod}: below the belt the skirt does not come through the blanket (${tuck.toFixed(4)} m, was ${tuck0.toFixed(4)})`);
  // The ledge: the skirt's top edge stood out a couple of centimetres round the shirt, wider than
  // the belt over it at places. Now the edge is under the belt, inside it all round, and tighter.
  const kTop = Math.max(...K.map((p) => p[1]));
  assert(kTop > lo && kTop < hi, `lod${lod}: the skirt's top edge is under the belt`);
  const edge = sectors(K, kTop - .006, kTop + .001, N), edge0 = sectors(K0, kTop - .006, kTop + .001, N);
  for (let k = 0; k < N; k++) if (edge[k] > 0 && Number.isFinite(now[k])) assert(edge[k] < now[k], `lod${lod}: the skirt's top inside the belt (bin ${k}: ${edge[k].toFixed(4)} < ${now[k].toFixed(4)})`);
  const pulled = edge.map((r, k) => edge0[k] - r).filter((x, k) => edge[k] > 0 && edge0[k] > 0);
  assert(Math.max(...pulled) > .01, `lod${lod}: and drawn in where it stood out (${Math.max(...pulled).toFixed(3)} m)`);
  const ledge0 = Math.max(...pulled);
  K.forEach((p, i) => { if (p[1] < kTop - HOLD_M - BLEND_M - .001) assert.deepEqual(p.map((x) => x.toFixed(5)), K0[i].map((x) => x.toFixed(5)), `lod${lod}: the skirt below the waist is as drawn`); });
  // The belt is weighted as the shirt under it (it moves as the shirt does, the thigh's share
  // at the hip included); the walk and the idle below are the proof.
  const si = belt.geometry.attributes.skinIndex, sw = belt.geometry.attributes.skinWeight;
  const legOf = (m) => { const a = m.geometry.attributes.skinIndex, w = m.geometry.attributes.skinWeight; return (i) => { let leg = 0; for (let c = 0; c < 4; c++) if (/thigh|calf/.test(m.skeleton.bones[a.getComponent(i, c)].name)) leg += w.getComponent(i, c); return leg; }; };
  const leg = legOf(belt), leg0 = legOf(mesh(before.scene, 'leather_belt'));
  let most = 0, most0 = 0;
  for (let i = 0; i < si.count; i++) {
    let sum = 0; for (let c = 0; c < 4; c++) sum += sw.getComponent(i, c);
    assert(Math.abs(sum - 1) < .01, `lod${lod}: belt vertex ${i}'s weights sum to one`);
    most = Math.max(most, leg(i)); most0 = Math.max(most0, leg0(i));
  }
  // In motion: on the walk and the idle the belt stays on the shirt where it used to hoop.
  if (lod <= 2) {
    const figure = (g) => { const sc = SkeletonUtils.clone(g.scene); const root = new THREE.Group(); root.add(sc); const mixer = new THREE.AnimationMixer(sc); return { sc, root, mixer }; };
    for (const clip of ['walk', 'idle']) {
      const a = figure(before), b = figure(after);
      const ca = before.animations.find((x) => x.name === clip), cb = after.animations.find((x) => x.name === clip);
      a.mixer.clipAction(ca).play(); b.mixer.clipAction(cb).play();
      const times = [0, .2, .4, .6, .8].map((f) => f * ca.duration);
      const m = (f, piece) => mesh(f.sc, piece);
      const gap0 = posedStandOff(a.root, m(a, 'leather_belt'), [m(a, 'trade_shirt'), m(a, 'trade_shirt_skirt')], a.mixer, ca, times);
      const gap = posedStandOff(b.root, m(b, 'leather_belt'), [m(b, 'trade_shirt'), m(b, 'trade_shirt_skirt')], b.mixer, cb, times);
      assert(gap < .03 && gap < gap0 * (lod < 2 ? .6 : .75), `lod${lod} ${clip}: the belt stays on the shirt (the hollow of the back it spans is in it) (worst ${gap.toFixed(3)} m, was ${gap0.toFixed(3)})`);
      console.log(`lod${lod} ${clip}: belt to the cloth beneath, worst ${gap0.toFixed(3)} -> ${gap.toFixed(3)} m`);
    }
  }
  console.log(`lod${lod}: belt off the shirt ${Math.max(...off0).toFixed(3)} -> ${Math.max(...off).toFixed(4)} m; skirt's top edge drawn in up to ${ledge0.toFixed(3)} m, under the belt`);
}
// Another body is left as drawn.
{
  const g = await parse('settler_1812', 2), p0 = [];
  g.scene.traverse((o) => { if (o.isMesh) p0.push(Array.from(o.geometry.attributes.position.array)); });
  assert.equal(fitWaist(g.scene), null, 'a body without a belted waist is not fitted');
  const p1 = []; g.scene.traverse((o) => { if (o.isMesh) p1.push(Array.from(o.geometry.attributes.position.array)); });
  assert.deepEqual(p1, p0, 'and not moved');
}

// The silver: a shader patch on two materials, no texture, one program text.
{
  const g = await parse(ASSET, 0);
  const done = engraveSilver(g.scene);
  assert.deepEqual([...new Set(done)].sort(), ['arm_bands', 'brooches']);
  const band = mesh(g.scene, 'silver_arm_bands').material, brooch = mesh(g.scene, 'silver_brooches').material;
  assert.notEqual(band, brooch, 'the bands have their own material');
  assert.equal(band.name, brooch.name, 'under the body\'s own material name');
  for (const m of [band, brooch]) {
    assert.equal(m.map ?? null, null, 'no texture'); assert.equal(m.normalMap ?? null, null, 'no normal map');
    assert.equal(m.metalness, SILVER.metalness);
  }
  engraveSilver(g.scene);
  const compile = (material) => { const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader, fragmentShader: THREE.ShaderLib.standard.fragmentShader }; material.onBeforeCompile(shader, null); return shader; };
  const a = compile(band), b = compile(brooch);
  assert.equal(a.vertexShader + a.fragmentShader, b.vertexShader + b.fragmentShader, 'one program for bands and brooches');
  assert.equal(band.customProgramCacheKey(), brooch.customProgramCacheKey());
  assert.equal(a.uniforms.chiSilver.value.x, 0); assert.equal(b.uniforms.chiSilver.value.x, 1);
  for (const marker of ['vChiSilverUv = uv;', 'float chiSilverH = 0.0;', 'chiSilverPerturb( - vViewPosition', 'roughnessFactor = clamp( roughnessFactor + chiSilverCutAt'])
    assert.equal((a.vertexShader + a.fragmentShader).split(marker).length, 2, `silver spliced once: ${marker}`);
  // The cuts fade by their screen rate before they can alias.
  assert(a.fragmentShader.includes('cut *= fade;'));
}
// Both wired into humans.js's parse, before any figure is cloned from it.
{
  const humans = await fs.readFile(new URL('renderers/web/js/humans.js', here), 'utf8');
  assert(/import \{ fitWaist \} from '\.\/human-waist\.js';/.test(humans) && /import \{ engraveSilver \} from '\.\/human-silver\.js';/.test(humans));
  assert(/const gltf = await loader\.parseAsync\(.*\);[\s\S]{0,400}fitWaist\(gltf\.scene\);\s*engraveSilver\(gltf\.scene\);\s*return gltf;/.test(humans), 'parse() fits and engraves the shared source');
}
console.log('human-waist: belts on the body at every level, standing and walking; silver engraved by shader, no texture: PASS');

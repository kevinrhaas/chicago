/**
 * T-2037: source-side contracts for filtering unresolved plank gaps.
 *
 *   node tools/check_plank_gap_filter.mjs [--json]
 *
 * Exercises the real frontage builder on straight, rotated and sloping walks,
 * then measures its top-face intervals. The unresolved limit must close the
 * internal comb without changing deck height, width, run or triangle count.
 * Posts and kerbs must carry zero displacement. A separate perspective witness
 * checks that the pixel transition preserves resolved gaps and honours DPR.
 * Shader composition, ordinary depth occlusion and far-merge attribute copying
 * are checked as source contracts. This does NOT compile GLSL or render pixels;
 * moving-camera browser comparison remains required for visual acceptance.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(threeURL);
const moduleURL = (source) => `data:text/javascript;base64,${Buffer.from(source).toString('base64')}`;

// Import the actual private builders, without booting the scene or loading maps.
// Only the unused scene-loader dependency is stubbed; no geometry is copied.
const source = await readFile(path.join(web, 'js/frontage.js'), 'utf8');
const mod = await import(moduleURL(source
  .replace("from 'three'", `from '${threeURL}'`)
  .replace("import { resolveBases } from './scene-loader.js';",
    "const resolveBases = () => { throw new Error('scene loading outside this check'); };")
  .replace("from './gates.js'", `from '${pathToFileURL(path.join(web, 'js/gates.js')).href}'`)
  + '\nexport { timberBuf, laySegment, pushBox, plankGapAttribute, filterPlankGaps, PLANK_GAP_M };'));
const confidenceSource = await readFile(path.join(web, 'js/confidence.js'), 'utf8');
const { createConfidenceView } = await import(moduleURL(
  confidenceSource.replace("from 'three'", `from '${threeURL}'`)));
const farMergeSource = await readFile(path.join(web, 'js/far-merge.js'), 'utf8');
const { createFarMerge } = await import(moduleURL(
  farMergeSource.replace("from 'three'", `from '${threeURL}'`)));

const checks = [];
const near = (a, b, why, eps = 1e-8) => assert.ok(Math.abs(a - b) <= eps,
  `${why}: ${a} versus ${b}`);
function check(name, run) { run(); checks.push(name); }

const fixtures = [];
for (const [name, angle, slope, bare] of [
  ['level', 0, 0, false],
  ['diagonal', 0.73, 0, false],
  ['graded', 2.31, 0.018, true],
]) {
  const length = 2.6, rx = Math.cos(angle), rn = Math.sin(angle);
  const walk = { width_m: 1.83, rise_m: 0.11, plank_pitch_m: 0.26,
    plank_thickness_m: 0.055, plank_underside: !bare };
  const buf = mod.timberBuf();
  const boards = mod.laySegment(buf, walk, 0, 0, rx * length, rn * length,
    { surfaceHeight: (e, n) => 0.7 + (e * rx + n * rn) * slope }, 1);
  const verticesPerBoard = (bare ? 10 : 12) * 3;
  const stride = verticesPerBoard + 2 * 10 * 3;
  check(`${name}: unchanged triangle cost and complete seam stream`, () => {
    assert.equal(boards, 10);
    assert.equal(buf.pos.length / 3, boards * stride);
    assert.equal(buf.seam.length, buf.pos.length);
  });
  check(`${name}: full closure meets each neighbouring board, preserving deck bounds`, () => {
    let previousEnd = 0;
    for (let board = 0; board < boards; board++) {
      const open = [], closed = [], across = [];
      for (let v = board * stride; v < board * stride + verticesPerBoard; v++) {
        const j = v * 3;
        if (buf.nrm[j + 1] !== 1) continue;
        const e = buf.pos[j], n = -buf.pos[j + 2];
        const de = buf.seam[j], dn = -buf.seam[j + 2];
        near(buf.seam[j + 1], 0, 'no height displacement');
        near(Math.hypot(de, dn), mod.PLANK_GAP_M / 2, 'bounded half-gap');
        near(de * -rn + dn * rx, 0, 'no cross-walk displacement');
        open.push(e * rx + n * rn);
        closed.push((e + de) * rx + (n + dn) * rn);
        across.push((e + de) * -rn + (n + dn) * rx);
        near(buf.pos[j + 1], 0.81 + (board + 0.5) * 0.26 * slope,
          'deck height retained');
      }
      assert.equal(open.length, 6);
      near(Math.min(...open), board * 0.26 + 0.01, 'resolved leading edge');
      near(Math.max(...open), (board + 1) * 0.26 - 0.01, 'resolved trailing edge');
      near(Math.min(...closed), previousEnd, 'neighbour joint has no uncovered interval');
      previousEnd = Math.max(...closed);
      near(Math.min(...across), -(1.83 / 2 - 0.09), 'left deck edge');
      near(Math.max(...across), 1.83 / 2 - 0.09, 'right deck edge');
      for (let v = board * stride + verticesPerBoard; v < (board + 1) * stride; v++) {
        near(Math.hypot(...buf.seam.slice(v * 3, v * 3 + 3)), 0, 'kerb is fixed');
      }
    }
    near(previousEnd, length, 'walk endpoint retained');
  });
  fixtures.push({ name, boards, triangles: buf.pos.length / 9,
    additionalTriangles: 0, seamBytes: mod.plankGapAttribute(buf.seam).array.byteLength });
}

check('standing timber has zero seam displacement', () => {
  const buf = mod.timberBuf();
  mod.pushBox(buf, 0, 1, 0, 1, 0, 0.1, 0.1, 1, 1);
  assert.ok(buf.seam.every((v) => v === 0));
});
check('compact displacement retains XZ direction to sub-micrometre accuracy', () => {
  const input = [0.0073, 0, -0.0061, 0, 0, 0, -0.01, 0, 0.01];
  const attribute = mod.plankGapAttribute(input);
  assert.equal(attribute.normalized, true);
  assert.equal(attribute.itemSize, 2);
  assert.equal(attribute.array.byteLength, 12);
  for (let i = 0; i < 3; i++) {
    near(attribute.getX(i) * 0.01, input[i * 3], 'packed X displacement', 0.00000031);
    near(attribute.getY(i) * 0.01, input[i * 3 + 2], 'packed Z displacement', 0.00000031);
  }
});

const material = new THREE.MeshStandardMaterial({ transparent: true });
mod.filterPlankGaps(material);
createConfidenceView().patch(material);
const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader,
  fragmentShader: THREE.ShaderLib.standard.fragmentShader };
material.onBeforeCompile(shader, {});
check('filter composes with confidence and preserves ordinary depth testing', () => {
  assert.equal(material.depthTest, true);
  assert.equal(material.depthWrite, true);
  assert.equal(material.polygonOffset, false);
  assert.ok(shader.vertexShader.includes('transformed += chiGapDelta * chiGapClose;'));
  assert.ok(shader.vertexShader.includes('vConfidence'));
  assert.ok(shader.fragmentShader.includes('uConfMode'));
  assert.equal(shader.vertexShader.match(/attribute vec2 aChiPlankGap/g)?.length, 1);
});
check('viewport uniform reads physical pixels, including offscreen viewports', () => {
  material.onBeforeRender({ getCurrentViewport: (v) => v.set(0, 0, 585, 1170) });
  assert.deepEqual(shader.uniforms.uChiPlankGapViewport.value.toArray(), [585, 1170]);
  material.onBeforeRender({ getCurrentViewport: (v) => v.set(20, 40, 256, 128) });
  assert.deepEqual(shader.uniforms.uChiPlankGapViewport.value.toArray(), [256, 128]);
});

// Independent perspective witness: a physical seam is projected through the
// camera, then compared against the shader's declared pixel thresholds.
const { closePx, openPx } = material.userData.plankGapFilter;
function gapPixels(distance, dpr) {
  const camera = new THREE.PerspectiveCamera(62, 1280 / 800, 0.1, 3000);
  camera.position.set(0, 1.68, distance);
  camera.lookAt(0, 0.11, 0);
  camera.updateMatrixWorld();
  const a = new THREE.Vector3(0, 0.11, -0.01).project(camera);
  const b = new THREE.Vector3(0, 0.11, 0.01).project(camera);
  return Math.hypot((b.x - a.x) * 640 * dpr, (b.y - a.y) * 400 * dpr);
}
const pixelReadings = [2, 8, 40, 100].map((distance) => ({ distance,
  gapPxDpr1: gapPixels(distance, 1), gapPxDpr2: gapPixels(distance, 2) }));
check('resolved near gaps are unchanged; distant subpixel gaps reach full closure', () => {
  assert.ok(pixelReadings[0].gapPxDpr1 > openPx);
  assert.ok(pixelReadings[2].gapPxDpr2 < closePx);
  for (const r of pixelReadings) near(r.gapPxDpr2, 2 * r.gapPxDpr1, 'DPR scaling');
  assert.ok(closePx > 0 && closePx < openPx && openPx <= 1);
});

check('far merging retains every seam displacement and the shared material', () => {
  const scene = new THREE.Scene(), group = new THREE.Group();
  group.name = 'frontage'; scene.add(group);
  const camera = new THREE.PerspectiveCamera(62, 1.6, 0.1, 3000);
  camera.position.set(0, 10, 0); camera.lookAt(0, 0, -500);
  camera.updateMatrixWorld();
  const banked = [];
  for (let i = 0; i < 4; i++) {
    const buf = mod.timberBuf();
    mod.laySegment(buf, { width_m: 1.83 }, i * 3, 500, i * 3 + 2.6, 500,
      { surfaceHeight: () => 0.7 }, 1);
    const geometry = new THREE.BufferGeometry();
    for (const [key, values, size] of [['position', buf.pos, 3], ['normal', buf.nrm, 3]]) {
      geometry.setAttribute(key, new THREE.Float32BufferAttribute(values, size));
    }
    geometry.setAttribute('aChiPlankGap', mod.plankGapAttribute(buf.seam));
    geometry.computeBoundingSphere();
    const mesh = new THREE.Mesh(geometry, material); mesh.renderOrder = 1;
    group.add(mesh);
    banked.push({ mesh, c: geometry.boundingSphere.center.clone(), r: geometry.boundingSphere.radius });
  }
  const merger = createFarMerge({ scene, camera, layers: ['frontage'] });
  merger.rebuild(banked); merger.update();
  const merged = group.children.find((m) => m.userData.farMerged);
  assert.ok(merged?.visible, 'fixture actually exercises a visible merged batch');
  assert.equal(merged.material, material);
  assert.equal(merged.renderOrder, 1);
  assert.equal(merged.geometry.attributes.aChiPlankGap.normalized, true);
  assert.ok(merged.geometry.attributes.aChiPlankGap.array instanceof Int16Array);
  const expected = banked.flatMap(({ mesh }) => Array.from(mesh.geometry.attributes.aChiPlankGap.array));
  assert.deepEqual(Array.from(merged.geometry.attributes.aChiPlankGap.array), expected);
  assert.equal(merged.geometry.attributes.position.count,
    banked.reduce((n, { mesh }) => n + mesh.geometry.attributes.position.count, 0));
  merger.dispose();
});

const report = { pass: true, checks, fixtures, pixelReadings,
  scope: 'source geometry, material composition, projected seam size and far-merge compatibility',
  pending: 'GLSL compilation and moving-camera pixel/occlusion comparisons in desktop and mobile browsers',
  reachPolicy: 'unchanged; this filter does not retain light-tier chunks beyond their furniture cutoff' };
console.log(process.argv.includes('--json') ? JSON.stringify(report, null, 2)
  : `PASS ${checks.length} plank-gap source checks; zero added triangles. Browser visual validation pending.`);

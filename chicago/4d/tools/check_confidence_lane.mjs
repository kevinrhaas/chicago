/**
 * THE CONFIDENCE LANE AND THE ONE-GRADE CHUNK (T-2689).
 *
 *   node tools/check_confidence_lane.mjs
 *
 * Frontage and the yard goods keep a vertex's confidence in the colour's fourth
 * lane, and an enclosure chunk of one grade keeps none at all
 * (compact-streams.js § CONFIDENCE). This holds the three things that make that
 * a storage change and not a different picture:
 *
 *   - 0, 0.5 and 1 come back EXACT, both as the shader reads them (the lane
 *     rounded to the nearest half, `laneGrade`) and through `confidenceOf`, and
 *     the tones beside them are what `compactColors` writes;
 *   - anything else is never squeezed into the lane: a confidence that is not
 *     all 0, 0.5 and 1 stays a float32 `_confidence` beside a THREE-lane colour
 *     (a four-lane colour would be read as a grade), and a tone past 1 keeps the
 *     lane in float32;
 *   - the patched shaders say what the lane means: the colour lane rounds and
 *     puts the varying alpha back to 1 (the frontage draws in the transparent
 *     pass), the float branch survives for a geometry without the lane, and a
 *     one-grade material reads its grade as a literal, keyed apart per grade.
 */
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const threeURL = pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href;
const THREE = await import(threeURL);
const streams = await import(pathToFileURL(path.join(web, 'js/compact-streams.js')).href);
const confSource = await readFile(path.join(web, 'js/confidence.js'), 'utf8');
const { createConfidenceView } = await import(`data:text/javascript;base64,${Buffer.from(
  confSource.replace("from 'three'", `from '${threeURL}'`)).toString('base64')}`);

const { setColorsAndConfidence, uniformGrade, confidenceOf, compactColors } = streams.compactStreams(THREE);
const checks = [];
const check = (name, run) => { run(); checks.push(name); };

const tones = [0.12, 0.34, 0.56, 0, 1, 0.5, 0.0402, 0.9, 0.333];
const grades = [0, 0.5, 1];

check('0, 0.5 and 1 ride the colour lane and read back exact', () => {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(9), 3));
  setColorsAndConfidence(g, Float32Array.from(tones), Float32Array.from(grades));
  const c = g.getAttribute('color');
  assert.ok(c.array instanceof Uint16Array && c.itemSize === 4 && c.normalized);
  assert.equal(g.getAttribute('_confidence'), undefined, 'no float stream left beside the lane');
  assert.equal(g.userData.confidenceLane, 'color');
  // The tones are byte for byte what compactColors writes.
  const plain = compactColors(Float32Array.from(tones));
  for (let i = 0; i < 3; i += 1) {
    for (let k = 0; k < 3; k += 1) assert.equal(c.array[i * 4 + k], plain.array[i * 4 + k]);
  }
  // As WebGL decodes a normalized Uint16, and as the shader then rounds it.
  assert.deepEqual([0, 1, 2].map((i) => streams.laneGrade(c.array[i * 4 + 3] / 65535)), grades);
  assert.deepEqual(Array.from(confidenceOf(g).array), grades);
});

check('a tone past 1 keeps the lane in float32, still exact', () => {
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(9), 3));
  setColorsAndConfidence(g, Float32Array.from([1.4, 0.2, 0.2, 0, 0, 0, 1, 1, 1]), Float32Array.from(grades));
  const c = g.getAttribute('color');
  assert.ok(c.array instanceof Float32Array && c.itemSize === 4 && !c.normalized);
  assert.equal(c.getX(0), Math.fround(1.4));
  assert.deepEqual(Array.from(confidenceOf(g).array), grades);
});

check('any other confidence keeps its float stream and a three-lane colour', () => {
  for (const odd of [[0, 0.25, 1], [0, NaN, 1], [0, 1.2, 1]]) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(9), 3));
    setColorsAndConfidence(g, Float32Array.from(tones), Float32Array.from(odd));
    assert.equal(g.getAttribute('color').itemSize, 3, 'a four-lane colour would be read as a grade');
    assert.ok(g.getAttribute('_confidence').array instanceof Float32Array);
    assert.equal(g.userData.confidenceLane, undefined);
    assert.equal(confidenceOf(g), g.getAttribute('_confidence'));
  }
});

check('one grade whole drops the stream; mixed or odd keeps it', () => {
  assert.equal(uniformGrade(Float32Array.from([1, 1, 1])), 1);
  assert.equal(uniformGrade(Float32Array.from([0.5, 0.5])), 0.5);
  assert.equal(uniformGrade(Float32Array.from([0, 0, 0])), 0);
  assert.equal(uniformGrade(Float32Array.from([1, 0.5, 1])), null);
  assert.equal(uniformGrade(Float32Array.from([0.3, 0.3])), null);
  assert.equal(uniformGrade(new Float32Array(0)), null);
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(new Float32Array(12), 3));
  g.userData.confidence = 0.5;
  assert.deepEqual(Array.from(confidenceOf(g).array), [0.5, 0.5, 0.5, 0.5]);
  assert.equal(confidenceOf(new THREE.BufferGeometry()), null);
});

// The vertex stage three hands onBeforeCompile, cut to the includes the patch
// anchors on; the fragment likewise.
const fakeShader = () => ({
  uniforms: {},
  vertexShader: 'void main() {\n#include <color_vertex>\n#include <begin_vertex>\n}',
  fragmentShader: 'void main() {\n#include <clipping_planes_fragment>\n#include <color_fragment>\n}',
});
const compiled = (packed) => {
  const view = createConfidenceView();
  const m = new THREE.MeshStandardMaterial({ vertexColors: true });
  view.patch(m, packed ? { packed } : {});
  const shader = fakeShader();
  m.onBeforeCompile(shader, null);
  return { shader, key: m.customProgramCacheKey() };
};

check('the colour-lane shader rounds the lane, restores alpha and keeps the float branch', () => {
  const { shader, key } = compiled(streams.COLOR_LANE_CONFIDENCE);
  const v = shader.vertexShader;
  assert.match(v, /#ifndef USE_COLOR_ALPHA\nattribute float _confidence;\n#endif/);
  assert.match(v, /vConfidence = floor\( color\.a \* 2\.0 \+ 0\.5 \) \* 0\.5;\s*vColor\.a = 1\.0;/);
  assert.match(v, /#else\s*vConfidence = \( _confidence == _confidence \)/);
  assert.ok(v.indexOf('#include <color_vertex>') < v.indexOf('vColor.a = 1.0'),
    'the alpha is put back after three writes the varying colour');
  assert.equal(v.split('attribute float _confidence;').length, 2, 'declared once');
  assert.match(key, /packed:color-lane/);
  assert.notEqual(key, compiled(null).key);
});

check('a one-grade material reads its grade as a literal, keyed apart per grade', () => {
  const one = compiled(streams.constantConfidence(1));
  const half = compiled(streams.constantConfidence(0.5));
  assert.match(one.shader.vertexShader, /vConfidence = 1\.0;/);
  assert.match(half.shader.vertexShader, /vConfidence = 0\.5;/);
  assert.doesNotMatch(one.shader.vertexShader, /attribute float _confidence/);
  assert.notEqual(one.key, half.key);
});

console.log(`check_confidence_lane: ${checks.length}/${checks.length} — ${checks.join('; ')}`);

#!/usr/bin/env node
/**
 * T-2646 — every grade's look (tint, dither or ghost, at an opacity) and the ghost pass.
 *
 *   node tools/test_confidence_looks.mjs
 *
 * The Confidence view used to have one look per grade, written into its shader:
 * Attested and Inferred tinted, Reconstructed tinted and dithered. js/confidence.js
 * now carries a mode and an opacity per grade in two uniforms, and draws a
 * ghosted grade see-through in a second pass (`renderGhost`) with twin materials
 * that are transparent and do not write depth. A browser is the only place the
 * GLSL itself runs (tools/smoke_renderer.mjs part 2 photographs it); this holds
 * what can be held without one:
 *
 *   - the look API: defaults are the old view's, a look is set and read back,
 *     nonsense is refused and changes nothing, reset restores;
 *   - opaqueConfidenceRange: a dithered or ghosted grade is not an occluder while
 *     the view is on, on exactly the band the shader gives it weight;
 *   - the shader the patch writes: the per-grade uniforms, the ghost-pass discard
 *     and alpha, and the old single-grade code gone;
 *   - the two passes against a recording renderer: one plain render unless a
 *     grade is ghosted with the view on; when it is, what holds only ghosted (or
 *     hidden) grades leaves the opaque pass, what holds none leaves the ghost
 *     pass — per object, and per instance in a structures batch — each patched
 *     material is swapped for a twin that inherits it (transparent, depthWrite
 *     off, its own program defines) and is put back, and every visibility,
 *     renderer and camera setting it touched is restored.
 */
import assert from 'node:assert/strict';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const vendorDir = (await readdir(path.join(web, 'vendor'))).find((d) => /^three-/.test(d));
const threeURL = pathToFileURL(path.join(web, 'vendor', vendorDir, 'three.module.js')).href;
const THREE = await import(threeURL);
const source = await readFile(path.join(web, 'js/confidence.js'), 'utf8');
const C = await import(`data:text/javascript;base64,${Buffer.from(source.replace("from 'three'", `from '${threeURL}'`)).toString('base64')}`);

let failures = 0;
function check(label, fn) {
  try { fn(); console.log(`  ok   ${label}`); } catch (err) {
    failures++;
    console.log(`  FAIL ${label}\n       ${String(err.message).split('\n')[0]}`);
  }
}

console.log('T-2646 — per-grade looks and the ghost pass');

check('the default looks are the view that shipped: Attested and Inferred tinted, Reconstructed dithered at 34%', () => {
  const v = C.createConfidenceView();
  assert.deepEqual(v.modes, { attested: 'tint', inferred: 'tint', reconstructed: 'dither' });
  assert.equal(v.grade('reconstructed').opacity.toFixed(2), '0.34');
  assert.equal(v.grade('attested').color, `#${C.GRADE_COLORS.attested.scene.toString(16).padStart(6, '0')}`);
});

check('each grade takes any mode at any opacity, and reads it back', () => {
  const v = C.createConfidenceView();
  for (const level of ['attested', 'inferred', 'reconstructed']) {
    for (const mode of ['tint', 'ghost', 'dither']) {
      for (const opacity of [0, 0.25, 1]) {
        const look = v.setGrade(level, { mode, opacity });
        assert.equal(look.mode, mode);
        assert.ok(Math.abs(look.opacity - opacity) < 1e-6);
      }
    }
  }
  assert.equal(v.setGrade('inferred', { color: '#336699' }).color, '#336699');
  assert.equal(v.uniforms.uGradeMode.value.z, C.GRADE_MODES.dither);
});

check('a grade that is not one, a mode that is not one and a non-number opacity are refused and change nothing', () => {
  const v = C.createConfidenceView();
  const before = JSON.stringify(v.resetGrades());
  assert.equal(v.setGrade('documented', { mode: 'ghost' }), null);
  assert.equal(v.setGrade('attested', { mode: 'xray', opacity: 0.1 }), null);
  assert.equal(v.setGrade('attested', { opacity: 'lots', mode: 'ghost' }), null);
  assert.equal(JSON.stringify(Object.fromEntries(['attested', 'inferred', 'reconstructed'].map((l) => [l, v.grade(l)]))), before);
  assert.equal(v.setGrade('attested', { opacity: 7 }).opacity, 1, 'opacity is clamped to 0..1');
});

check('resetGrades puts every colour, mode and opacity back', () => {
  const v = C.createConfidenceView();
  v.setGrade('reconstructed', { mode: 'ghost', opacity: 0.9, color: 0x00ff00 });
  const r = v.resetGrades();
  assert.equal(r.reconstructed.mode, 'dither');
  assert.equal(r.reconstructed.color, '#8c5a2b');
});

check('ghosting needs the view on and a ghosted grade that is not hidden', () => {
  const v = C.createConfidenceView();
  v.setGrade('inferred', { mode: 'ghost', opacity: 0.5 });
  assert.equal(v.ghosting, false, 'view off');
  v.set(true);
  assert.equal(v.ghosting, true);
  v.setHidden('inferred', true);
  assert.equal(v.ghosting, false, 'the ghosted grade is hidden');
});

check('a dithered or ghosted grade is no occluder while the view is on, on its own band only', () => {
  const view = (modes, enabled = true) => ({ enabled, hidden: {}, modes });
  const tint = { attested: 'tint', inferred: 'tint', reconstructed: 'tint' };
  assert.equal(C.opaqueConfidenceRange([0, 1], view(tint)), true, 'all tinted: opaque everywhere');
  assert.equal(C.opaqueConfidenceRange([0, 0.2], view({ ...tint, attested: 'ghost' })), false);
  assert.equal(C.opaqueConfidenceRange([0.5, 0.5], view({ ...tint, attested: 'ghost' })), true);
  assert.equal(C.opaqueConfidenceRange([0.5, 0.5], view({ ...tint, inferred: 'dither' })), false);
  assert.equal(C.opaqueConfidenceRange([0.75, 0.75], view({ ...tint, reconstructed: 'dither' })), true, 'the band edge carries no weight');
  assert.equal(C.opaqueConfidenceRange([0, 1], view({ ...tint, reconstructed: 'ghost' }, false)), true, 'view off: looks do not apply');
  // A view with no modes reads as the defaults, which is the rule before T-2646.
  assert.equal(C.opaqueConfidenceRange([0, 0.8], { enabled: true, hidden: {} }), false);
  assert.equal(C.opaqueConfidenceRange([0, 0.5], { enabled: true, hidden: {} }), true);
});

// The shader the patch writes, on three's own standard shader.
function compiled(view, material = new THREE.MeshStandardMaterial()) {
  view.patch(material);
  const shader = {
    uniforms: {},
    vertexShader: THREE.ShaderLib.standard.vertexShader,
    fragmentShader: THREE.ShaderLib.standard.fragmentShader,
  };
  material.onBeforeCompile(shader, null);
  return { material, shader };
}

check('the patched shader reads per-grade mode and opacity, and the old single-grade uniforms are gone', () => {
  const v = C.createConfidenceView();
  const { shader } = compiled(v);
  const f = shader.fragmentShader;
  for (const u of ['uGradeMode', 'uGradeOpacity', 'uTintAttested', 'uTintInferred', 'uTintReconstructed']) {
    assert.ok(f.includes(`uniform vec3 ${u};`), `${u} declared`);
    assert.ok(shader.uniforms[u] === v.uniforms[u], `${u} bound to the shared uniform`);
  }
  assert.ok(!/uReconAlpha|uTintStrength/.test(f), 'no stale uniform');
  assert.ok(f.includes('#ifdef CHICAGO_GHOST_PASS'), 'ghost-pass branch');
  assert.ok(f.startsWith('#define CHICAGO_GHOST_ALPHA'), 'the alpha anchor was found');
  assert.ok(/#include <opaque_fragment>[\s\S]*gl_FragColor\.a \*=/.test(f), 'ghost alpha after the fragment is written');
});

check('a shader without three\'s output anchor never claims a ghost alpha', () => {
  const v = C.createConfidenceView();
  const m = new THREE.MeshStandardMaterial();
  v.patch(m);
  const shader = { uniforms: {}, vertexShader: THREE.ShaderLib.standard.vertexShader,
    fragmentShader: THREE.ShaderLib.standard.fragmentShader.replace('#include <opaque_fragment>', 'gl_FragColor = vec4(1.0);') };
  m.onBeforeCompile(shader, null);
  assert.ok(!shader.fragmentShader.includes('#define CHICAGO_GHOST_ALPHA'));
});

// The ghost pass, against a renderer that records what it was asked to draw.
function recordingRenderer() {
  const r = {
    autoClear: true,
    shadowMap: { autoUpdate: true, needsUpdate: true },
    info: { autoReset: true, render: { calls: 0 } },
    seen: [],
    render(scene, camera) {
      const drawn = [];
      const instances = new Map();
      scene.traverse((o) => {
        if (!o.visible) return;
        if ((o.isMesh || o.isLight) && o.layers.test(camera.layers)) drawn.push(o);
        if (o.isBatchedMesh && o.layers.test(camera.layers)) {
          instances.set(o, [0, 1, 2].filter((i) => o.getVisibleAt(i)));
        }
      });
      r.seen.push({
        drawn, instances, mask: camera.layers.mask, background: scene.background, autoClear: r.autoClear,
        shadow: { ...r.shadowMap }, autoReset: r.info.autoReset,
        materials: drawn.filter((o) => o.isMesh).map((o) => o.material),
      });
      if (r.info.autoReset) r.info.render.calls = 0;
      r.info.render.calls += drawn.filter((o) => o.isMesh).length;
    },
  };
  return r;
}
const graded = (value) => {
  const g = new THREE.BoxGeometry();
  const n = g.getAttribute('position').count;
  g.setAttribute('_confidence', new THREE.Float32BufferAttribute(
    Array.from({ length: n }, (_, i) => (Array.isArray(value) ? value[i % value.length] : value)), 1));
  return g;
};
function town(view) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x88aacc);
  const patchedMat = view.patch(new THREE.MeshStandardMaterial({ color: 0x804020 }));
  const glass = view.patch(new THREE.MeshPhysicalMaterial({ transmission: 1 }));
  const recon = new THREE.Mesh(graded(1), patchedMat);              // nothing but Reconstructed
  const mixed = new THREE.Mesh(graded([0, 0.5, 1]), [patchedMat, new THREE.MeshBasicMaterial()]);
  const attested = new THREE.Mesh(graded(0), patchedMat);           // nothing but Attested
  const plain = new THREE.Mesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial());
  const pane = new THREE.Mesh(graded(1), glass);
  const batch = new THREE.BatchedMesh(3, 100, 200, patchedMat);
  const gid = batch.addGeometry(new THREE.BoxGeometry());
  for (let i = 0; i < 3; i++) batch.addInstance(gid);
  batch.userData.confidenceRanges = [[0, 0], [1, 1], [0, 1]];       // attested, reconstructed, mixed
  const group = new THREE.Group();
  group.add(mixed);
  const sun = new THREE.DirectionalLight();
  scene.add(recon, group, attested, plain, pane, batch, sun);
  return { scene, recon, mixed, attested, plain, pane, batch, sun, patchedMat };
}

check('with no ghost, render() is one plain renderer.render and touches nothing', () => {
  const v = C.createConfidenceView();
  const { scene } = town(v);
  const r = recordingRenderer(), cam = new THREE.PerspectiveCamera();
  v.set(true);
  assert.equal(v.render(r, scene, cam), 0);
  v.set(false); v.setGrade('reconstructed', { mode: 'ghost' });
  assert.equal(v.render(r, scene, cam), 0);
  assert.equal(r.seen.length, 2, 'one draw per frame');
  assert.ok(r.seen.every((p) => p.mask === cam.layers.mask && p.autoClear && p.instances.get([...p.instances.keys()][0]).length === 3));
});

check('with Reconstructed ghosted: the opaque pass leaves out what is only Reconstructed, the ghost pass draws only what holds it', () => {
  const v = C.createConfidenceView();
  const t = town(v);
  const r = recordingRenderer(), cam = new THREE.PerspectiveCamera();
  const camMask = cam.layers.mask;
  const bg = t.scene.background;
  v.set(true);
  v.setGrade('reconstructed', { mode: 'ghost', opacity: 0.25 });
  const calls = v.render(r, t.scene, cam);
  assert.equal(r.seen.length, 2);
  const [opaque, ghost] = r.seen;
  // opaque pass
  assert.ok(!opaque.drawn.includes(t.recon), 'a wholly Reconstructed mesh is not in the opaque pass');
  assert.ok(opaque.drawn.includes(t.mixed) && opaque.drawn.includes(t.attested));
  assert.deepEqual(opaque.instances.get(t.batch), [0, 2], 'nor is the wholly Reconstructed instance');
  // ghost pass
  assert.equal(ghost.mask, (1 << C.GHOST_LAYER) >>> 0, 'drawn on the ghost layer only');
  assert.deepEqual(new Set(ghost.drawn), new Set([t.recon, t.mixed, t.batch, t.sun]),
    'what holds Reconstructed, and the light; not the Attested mesh, the plain mesh or the glass');
  assert.deepEqual(ghost.instances.get(t.batch), [1, 2], 'the wholly Attested instance is left out');
  assert.equal(ghost.background, null, 'no background redrawn over the frame');
  assert.equal(ghost.autoClear, false, 'the frame is not cleared');
  assert.deepEqual(ghost.shadow, { autoUpdate: false, needsUpdate: false }, 'no shadow pass');
  assert.equal(ghost.autoReset, false, 'its draws add to the frame\'s');
  assert.equal(calls, 3);
  assert.equal(r.info.render.calls, opaque.drawn.filter((o) => o.isMesh).length + 3, 'renderer.info holds both passes');
  const twin = ghost.materials[ghost.drawn.filter((o) => o.isMesh).indexOf(t.recon)];
  assert.notEqual(twin, t.patchedMat);
  assert.equal(Object.getPrototypeOf(twin), t.patchedMat, 'the twin inherits the material, so nothing is copied');
  assert.equal(twin.transparent, true);
  assert.equal(twin.depthWrite, false);
  assert.ok('CHICAGO_GHOST_PASS' in twin.defines, 'its own program');
  assert.notEqual(twin.id, t.patchedMat.id);
  assert.equal(t.patchedMat.transparent, false, 'the material itself is untouched');
  assert.equal(t.patchedMat.depthWrite, true);
  const arr = ghost.materials[ghost.drawn.filter((o) => o.isMesh).indexOf(t.mixed)];
  assert.ok(Array.isArray(arr) && arr[0] === twin && arr[1] === t.mixed.material[1],
    'a material array swaps only its patched entries');
  // and everything is put back
  assert.equal(t.recon.material, t.patchedMat);
  assert.equal(t.recon.visible, true);
  assert.equal(t.mixed.material[0], t.patchedMat);
  assert.deepEqual([0, 1, 2].map((i) => t.batch.getVisibleAt(i)), [true, true, true]);
  assert.equal(cam.layers.mask, camMask);
  assert.equal(t.scene.background, bg);
  assert.equal(r.autoClear, true);
  assert.deepEqual(r.shadowMap, { autoUpdate: true, needsUpdate: true });
  assert.equal(r.info.autoReset, true);
  assert.equal(t.plain.layers.isEnabled(C.GHOST_LAYER), false);
  assert.equal(t.attested.layers.isEnabled(C.GHOST_LAYER), false);
  assert.equal(t.pane.layers.isEnabled(C.GHOST_LAYER), false);
  // The twin follows its material: one prototype down, the colour IS the material's.
  t.patchedMat.color.set(0x00ff00);
  assert.equal(twin.color, t.patchedMat.color);
  // A second frame reuses the twin.
  v.render(r, t.scene, cam);
  assert.equal(r.seen[3].materials[ghost.drawn.filter((o) => o.isMesh).indexOf(t.recon)], twin);
});

check('an instance something else had hidden stays hidden through both passes', () => {
  const v = C.createConfidenceView();
  const t = town(v);
  const r = recordingRenderer(), cam = new THREE.PerspectiveCamera();
  t.batch.setVisibleAt(1, false);
  v.set(true);
  v.setGrade('reconstructed', { mode: 'ghost' });
  v.render(r, t.scene, cam);
  assert.deepEqual(r.seen[1].instances.get(t.batch), [2]);
  assert.deepEqual([0, 1, 2].map((i) => t.batch.getVisibleAt(i)), [true, false, true]);
});

check('a ghosted grade that is hidden is not ghosted', () => {
  const v = C.createConfidenceView();
  const t = town(v);
  const r = recordingRenderer(), cam = new THREE.PerspectiveCamera();
  v.set(true);
  v.setGrade('attested', { mode: 'ghost' });
  v.setGrade('reconstructed', { mode: 'ghost' });
  v.setHidden('reconstructed', true);
  v.render(r, t.scene, cam);
  const [opaque, ghost] = r.seen;
  // In the opaque pass the hidden grade is discarded by the shader, as it always was.
  assert.ok(opaque.drawn.includes(t.recon));
  assert.ok(!ghost.drawn.includes(t.recon), 'a hidden grade is not ghosted');
  assert.ok(ghost.drawn.includes(t.attested));
});

check('a mesh added later with a patched material is reached when the object list is next rebuilt', () => {
  const v = C.createConfidenceView();
  const t = town(v);
  const r = recordingRenderer(), cam = new THREE.PerspectiveCamera();
  v.set(true);
  v.setGrade('attested', { mode: 'ghost' });
  v.render(r, t.scene, cam);
  const late = new THREE.Mesh(graded(0), t.patchedMat);
  t.scene.add(late);
  for (let i = 0; i < 30; i++) v.render(r, t.scene, cam);
  assert.ok(r.seen.at(-1).drawn.includes(late));
});

check('a geometry whose page arrays were freed is read from the range kept for it, or drawn in both passes', () => {
  const v = C.createConfidenceView();
  const t = town(v);
  const r = recordingRenderer(), cam = new THREE.PerspectiveCamera();
  const freed = (range) => {
    const g = graded(1);
    g.getAttribute('_confidence').array = null;
    if (range) g.userData.confidenceRange = range;
    return new THREE.Mesh(g, t.patchedMat);
  };
  const kept = freed([1, 1]);
  const unknown = freed(null);
  t.scene.add(kept, unknown);
  v.set(true);
  v.setGrade('reconstructed', { mode: 'ghost' });
  v.render(r, t.scene, cam);
  const [opaque, ghost] = r.seen;
  assert.ok(!opaque.drawn.includes(kept) && ghost.drawn.includes(kept), 'kept range: ghost pass only');
  assert.ok(opaque.drawn.includes(unknown) && ghost.drawn.includes(unknown), 'no range: both passes');
});

check('disposing a material disposes its twin', () => {
  const v = C.createConfidenceView();
  const t = town(v);
  const r = recordingRenderer(), cam = new THREE.PerspectiveCamera();
  v.set(true); v.setGrade('reconstructed', { mode: 'ghost' });
  v.render(r, t.scene, cam);
  const twin = r.seen[1].materials[0];
  let twinDisposed = false;
  twin.addEventListener('dispose', () => { twinDisposed = true; });
  t.patchedMat.dispose();
  assert.equal(twinDisposed, true);
});

if (failures) { console.log(`\n${failures} check(s) failed`); process.exit(1); }
console.log('\nall checks passed');

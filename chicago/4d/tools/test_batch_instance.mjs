/**
 * T-3363 — a grown wood's batch draws every copy of one template as ONE instanced
 * entry, and draws exactly the stems, with exactly their instance data, it drew before.
 *
 *   node tools/test_batch_instance.mjs
 *
 * Built on the real three.js BatchedMesh (no WebGL is needed: the multi-draw list is
 * made in `onBeforeRender`, and the extension is a recorder). Every case compares the
 * list three makes alone — one entry per stem — with the regrouped one read through
 * the patched shader's table (`table[table[draw] + instance]`), as the set of
 * (template range, stem, matrix, colour) it draws.
 */
import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const web = path.join(root, 'renderers/web');
const THREE = await import(pathToFileURL(path.join(web, 'vendor/three-0.185.1/three.module.js')).href);
const { instanceDraws, patchInstancedDraws, regroup, extraSlots } = await import(
  pathToFileURL(path.join(web, 'js/batch-instance.js')).href);

/** A recorder standing in for WEBGL_multi_draw and the renderer three hands a hook. */
function fakeRenderer({ instanced = true } = {}) {
  const calls = [];
  const md = {
    multiDrawElementsWEBGL(mode, counts, co, type, offsets, oo, n) {
      calls.push({ kind: 'plain', mode, counts: [...counts.slice(co, co + n)], offsets: [...offsets.slice(oo, oo + n)] });
    },
  };
  if (instanced) {
    md.multiDrawElementsInstancedWEBGL = function (mode, counts, co, type, offsets, oo, inst, io, n) {
      calls.push({ kind: 'instanced', mode, counts: [...counts.slice(co, co + n)], offsets: [...offsets.slice(oo, oo + n)],
        instances: [...inst.slice(io, io + n)] });
    };
  }
  const info = { render: { triangles: 0, calls: 0 } };
  return { md, calls, info, extensions: { has: (n) => n === 'WEBGL_multi_draw', get: () => md } };
}

/** Three templates (a tall, a mid, a far tree), and `n` stems dealt among them. */
function build(n = 40, { slots = true } = {}) {
  const templates = [new THREE.BoxGeometry(1, 3, 1, 2, 2, 2), new THREE.BoxGeometry(1, 2, 1), new THREE.PlaneGeometry(1, 1)];
  const verts = templates.reduce((s, g) => s + g.attributes.position.count, 0);
  const idx = templates.reduce((s, g) => s + g.index.count, 0);
  const mat = patchInstancedDraws(new THREE.MeshStandardMaterial());
  const batch = new THREE.BatchedMesh(n + (slots ? extraSlots(templates.length) : 0), verts, idx, mat);
  batch.sortObjects = false;
  const ids = templates.map((g) => batch.addGeometry(g));
  for (let i = 0; i < n; i += 1) {
    const id = batch.addInstance(ids[(i * 7) % 3]);
    batch.setMatrixAt(id, new THREE.Matrix4().makeTranslation((i % 10) * 3 - 15, 0, -10 - Math.floor(i / 10) * 4));
    batch.setColorAt(id, new THREE.Vector4(1, 1, 1, (i % 5) / 4) );
  }
  batch.updateMatrixWorld(true);
  return batch;
}

const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 1000);
camera.position.set(0, 1, 5);
camera.updateMatrixWorld(true);
camera.updateProjectionMatrix();

function stemData(batch, inst) {
  const m = batch._matricesTexture.image.data;
  const c = batch._colorsTexture.image.data;
  return [...m.slice(inst * 16, inst * 16 + 16), ...c.slice(inst * 4, inst * 4 + 4)].join(',');
}

/** What three's own list draws: one entry a stem. */
function drawnPlain(batch) {
  const out = [];
  const t = batch._indirectTexture.image.data;
  for (let k = 0; k < batch._multiDrawCount; k += 1) {
    out.push(`${batch._multiDrawStarts[k]}+${batch._multiDrawCounts[k]}|${t[k]}|${stemData(batch, t[k])}`);
  }
  return out.sort();
}

/** What the recorded instanced call draws, read as the patched shader reads the table. */
function drawnRegrouped(batch, call) {
  const out = [];
  const t = batch._indirectTexture.image.data;
  for (let d = 0; d < call.counts.length; d += 1) {
    for (let i = 0; i < call.instances[d]; i += 1) {
      const inst = t[t[d] + i];
      out.push(`${call.offsets[d]}+${call.counts[d]}|${inst}|${stemData(batch, inst)}`);
    }
  }
  return out.sort();
}

/** Prepare one pass and draw it the way three does (renderMultiDraw). */
function pass(batch, r, cam = camera) {
  batch.onBeforeRender(r, null, cam, batch.geometry, batch.material);
  if (batch._multiDrawCount === 0) return null;
  r.md.multiDrawElementsWEBGL(4, batch._multiDrawCounts, 0, 5125, batch._multiDrawStarts, 0, batch._multiDrawCount);
  return r.calls.at(-1);
}

let failures = 0;
const check = (label, fn) => {
  try { fn(); console.log(`  ok   ${label}`); } catch (e) { failures += 1; console.log(`  FAIL ${label}\n       ${e.message}`); }
};

check('every stem in view: one instanced draw per template, the same stems', () => {
  const plain = build(); plain.onBeforeRender(null, null, camera, plain.geometry, plain.material);
  const b = build(); instanceDraws(b);
  const r = fakeRenderer();
  const call = pass(b, r);
  assert.equal(call.kind, 'instanced');
  assert.equal(call.counts.length, 3);
  assert.ok(plain._multiDrawCount > 10, `three drew ${plain._multiDrawCount} entries`);
  assert.equal(call.instances.reduce((s, x) => s + x, 0), plain._multiDrawCount);
  assert.deepEqual(drawnRegrouped(b, call), drawnPlain(plain));
});

check('renderer.info is given the triangles of every instance past the first', () => {
  const b = build(); instanceDraws(b);
  const r = fakeRenderer();
  const call = pass(b, r);
  const all = call.counts.reduce((s, c, d) => s + (c / 3) * call.instances[d], 0);
  const one = call.counts.reduce((s, c) => s + c / 3, 0);
  assert.equal(r.info.render.triangles, all - one, 'three adds one instance a draw itself');
});

check('hidden stems and stems the frustum culls stay undrawn', () => {
  const setup = (x) => {
    x.setVisibleAt(3, false); x.setVisibleAt(17, false);
    x.setMatrixAt(5, new THREE.Matrix4().makeTranslation(0, 0, 500));
  };
  const plain = build(); setup(plain); plain.onBeforeRender(null, null, camera, plain.geometry, plain.material);
  const b = build(); setup(b); instanceDraws(b);
  const call = pass(b, fakeRenderer());
  const got = drawnRegrouped(b, call);
  assert.deepEqual(got, drawnPlain(plain));
  for (const gone of [3, 5, 17]) assert.ok(!got.some((x) => x.split('|')[1] === String(gone)), `stem ${gone}`);
});

check('the sun\'s pass (onBeforeShadow) is regrouped too, with its own cull', () => {
  const sun = new THREE.OrthographicCamera(-30, 30, 30, -30, 0.1, 500);
  sun.position.set(0, 100, -20); sun.lookAt(0, 0, -20); sun.updateMatrixWorld(true);
  const depth = patchInstancedDraws(new THREE.MeshDepthMaterial());
  const plain = build(); plain.onBeforeShadow(null, plain, camera, sun, plain.geometry, depth);
  const b = build(); instanceDraws(b);
  const r = fakeRenderer();
  b.onBeforeShadow(r, b, camera, sun, b.geometry, depth);
  r.md.multiDrawElementsWEBGL(4, b._multiDrawCounts, 0, 5125, b._multiDrawStarts, 0, b._multiDrawCount);
  const call = r.calls.at(-1);
  assert.equal(call.kind, 'instanced');
  assert.deepEqual(drawnRegrouped(b, call), drawnPlain(plain));
});

check('an unpatched material (a pick stand-in) is drawn as three draws it', () => {
  const b = build(); instanceDraws(b);
  const r = fakeRenderer();
  const pick = new THREE.MeshBasicMaterial();
  b.onBeforeRender(r, null, camera, b.geometry, pick);
  const n = b._multiDrawCount;
  r.md.multiDrawElementsWEBGL(4, b._multiDrawCounts, 0, 5125, b._multiDrawStarts, 0, n);
  assert.equal(r.calls.at(-1).kind, 'plain');
  const plain = build(); plain.onBeforeRender(null, null, camera, plain.geometry, pick);
  assert.equal(n, plain._multiDrawCount);
});

check('without an instanced multi-draw the batch is left as three draws it', () => {
  const b = build(); instanceDraws(b);
  const r = fakeRenderer({ instanced: false });
  const call = pass(b, r);
  assert.equal(call.kind, 'plain');
  const plain = build(); plain.onBeforeRender(null, null, camera, plain.geometry, plain.material);
  assert.equal(b._multiDrawCount, plain._multiDrawCount);
});

check('another batch\'s multi-draw passes through untouched', () => {
  const b = build(); instanceDraws(b);
  const r = fakeRenderer();
  pass(b, r);
  const other = new Int32Array([6, 6]);
  r.md.multiDrawElementsWEBGL(4, other, 0, 5125, new Int32Array([0, 24]), 0, 2);
  assert.equal(r.calls.at(-1).kind, 'plain');
});

check('a batch without room for its table draws nothing rather than the wrong stems', () => {
  const b = build(40, { slots: false });
  // Fill the table: three sizes it to the square at or above the stems.
  const r = fakeRenderer();
  instanceDraws(b);
  b.onBeforeRender(r, null, camera, b.geometry, b.material);
  const room = b._indirectTexture.image.data.length;
  if (40 + 3 > room) assert.equal(b._multiDrawCount, 0);
  else assert.ok(b._multiDrawCount <= 3);
});

check('the shader reads the table through the run (the patch is written once, after three\'s)', () => {
  const m = patchInstancedDraws(new THREE.MeshStandardMaterial());
  const shader = { vertexShader: '#include <batching_pars_vertex>\nvoid main() {}', fragmentShader: '' };
  m.onBeforeCompile(shader, fakeRenderer());
  assert.match(shader.vertexShader, /#include <batching_pars_vertex>\s+#ifdef USE_BATCHING\s+float chiInstancedIndex/);
  assert.match(shader.vertexShader, /getIndirectIndex\( run \+ gl_InstanceID \)/);
  assert.match(shader.vertexShader, /#define getIndirectIndex\( i \) chiInstancedIndex\( i \)/);
  const bare = { vertexShader: '#include <batching_pars_vertex>\nvoid main() {}', fragmentShader: '' };
  patchInstancedDraws(new THREE.MeshStandardMaterial()).onBeforeCompile(bare, fakeRenderer({ instanced: false }));
  assert.doesNotMatch(bare.vertexShader, /chiInstancedIndex/);
  assert.match(m.customProgramCacheKey(), /instanced-draws/);
});

// What the regroup costs a frame at the size of 1904's parkway (about 1,000 kept
// entries a pass): printed, not asserted.
{
  const n = 4000;
  const b = build(n);
  instanceDraws(b);
  const r = fakeRenderer();
  b.onBeforeRender(r, null, camera, b.geometry, b.material);
  const reps = 200;
  const t0 = performance.now();
  for (let i = 0; i < reps; i += 1) b.onBeforeRender(r, null, camera, b.geometry, b.material);
  const both = (performance.now() - t0) / reps;
  const plain = build(n);
  const t1 = performance.now();
  for (let i = 0; i < reps; i += 1) plain.onBeforeRender(null, null, camera, plain.geometry, plain.material);
  const three = (performance.now() - t1) / reps;
  console.log(`  note ${n} stems: three's own list ${three.toFixed(3)} ms, with the regroup ${both.toFixed(3)} ms, `
    + `${b._multiDrawCount} draws after`);
}

if (failures) {
  console.log(`\nFAIL: ${failures} batch-instance check(s) failed`);
  process.exit(1);
}
console.log('\nOK: every copy of one template draws as one instanced entry, drawing the same stems');

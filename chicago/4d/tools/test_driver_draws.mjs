#!/usr/bin/env node
// T-2970: the driver's draws, counted as three's `info.render.calls` plus each
// multi-draw's entries past the first — without a browser, on a renderer shaped
// as three 0.185's (WebGLInfo's `reset`/`update`, `extensions.has/get`).
import assert from 'node:assert/strict';
import { countDriverDraws } from '../renderers/web/js/driver-draws.js';

const fakeRenderer = ({ multiDraw = true } = {}) => {
  const render = { frame: 0, calls: 0, triangles: 0 };
  const info = { render, autoReset: true, reset() { render.calls = 0; render.triangles = 0; },
    update(count) { render.calls += 1; render.triangles += count / 3; } };
  const sent = [];
  const ext = multiDraw ? {
    multiDrawArraysWEBGL(m, f, fo, c, co, n) { sent.push(['arrays', n]); },
    multiDrawElementsWEBGL(m, c, co, t, o, oo, n) { sent.push(['elements', n]); },
    multiDrawArraysInstancedWEBGL(m, f, fo, c, co, i, io, n) { sent.push(['arraysInstanced', n]); },
    multiDrawElementsInstancedWEBGL(m, c, co, t, o, oo, i, io, n) { sent.push(['elementsInstanced', n]); },
  } : null;
  // The context hands the extension out, and records who asked: three's
  // WebGLExtensions caches what `gl.getExtension` returned, first asked at the first
  // BatchedMesh it draws.
  const asked = [];
  const gl = { getExtension(name) { asked.push(name); return name === 'WEBGL_multi_draw' ? ext : null; } };
  const cache = {};
  const extensions = { get: (name) => (name in cache ? cache[name] : (cache[name] = gl.getExtension(name))) };
  extensions.has = (name) => extensions.get(name) !== null;
  // Three's two ways of drawing a BatchedMesh (three.module.js renderMultiDraw and
  // its per-entry fallback), and a plain mesh: each takes one `info.update` per
  // GL call three makes.
  const batched = (counts) => {
    const md = extensions.get('WEBGL_multi_draw');
    if (md) { md.multiDrawElementsWEBGL(4, counts, 0, 5125, counts, 0, counts.length); info.update(counts.reduce((a, b) => a + b, 0)); }
    else for (const c of counts) info.update(c);
  };
  const mesh = (count) => info.update(count);
  const frame = () => { if (info.autoReset) info.reset(); };
  return { renderer: { info, extensions, getContext: () => gl }, ext, asked, sent, batched, mesh, frame };
};

// It never enables the extension itself: three takes it lazily, at its first
// BatchedMesh, and asking for it at boot put a 52-57 ms flora pass on the first walk
// after a tier change (the moving-frames gate). Counting starts when three asks.
{
  const r = fakeRenderer();
  const d = countDriverDraws(r.renderer);
  assert.deepEqual(r.asked, [], 'counting asked the context for nothing');
  assert.equal(d.native, false, 'nothing to count before three takes the extension');
  r.frame(); r.mesh(3); r.batched([1, 1, 1]);
  assert.deepEqual(r.asked, ['WEBGL_multi_draw'], 'three asked, once');
  assert.equal(d.native, true);
  assert.equal(d.draws, 4, 'the first multi-draw three made was counted');
}

// A multi-draw of n entries is n driver draws where three's counter says one.
{
  const r = fakeRenderer();
  const d = countDriverDraws(r.renderer);
  r.frame(); r.mesh(36); r.batched([30, 12, 6, 6]); r.batched([3]);
  assert.equal(d.native, true);
  assert.equal(r.renderer.info.render.calls, 3, "three's own counter takes a batch as one");
  assert.equal(d.draws, 1 + 4 + 1, 'the driver received one draw per kept entry');
  assert.equal(d.multiDrawExtra, 3);
  assert.deepEqual(r.sent, [['elements', 4], ['elements', 1]], 'the wrapped call still reaches the extension, arguments intact');
  // The next render() resets both, so the figure is one frame's.
  r.frame(); r.batched([3, 3]);
  assert.equal(d.draws, 2, 'the tally resets with renderer.info');
}

// Every entry point is counted at its own drawcount argument.
{
  const r = fakeRenderer();
  const d = countDriverDraws(r.renderer);
  r.frame(); r.renderer.extensions.get('WEBGL_multi_draw');
  r.ext.multiDrawArraysWEBGL(4, [], 0, [], 0, 3);
  r.ext.multiDrawArraysInstancedWEBGL(4, [], 0, [], 0, [], 0, 5);
  r.ext.multiDrawElementsInstancedWEBGL(4, [], 0, 5125, [], 0, [], 0, 7);
  r.ext.multiDrawElementsWEBGL(4, [], 0, 5125, [], 0, 0);
  assert.equal(d.multiDrawExtra, 2 + 4 + 6, 'an empty multi-draw adds nothing');
}

// Held across passes (gpu-pick.js and confidence.js turn autoReset off), the
// tally accumulates exactly as three's does.
{
  const r = fakeRenderer();
  const d = countDriverDraws(r.renderer);
  r.frame(); r.batched([1, 1, 1]);
  r.renderer.info.autoReset = false;
  r.frame(); r.batched([1, 1]);
  assert.equal(d.draws, 5);
}

// Without the extension three draws entry by entry and counts each: nothing to add.
{
  const r = fakeRenderer({ multiDraw: false });
  const d = countDriverDraws(r.renderer);
  assert.equal(d.native, false);
  r.frame(); r.batched([3, 3, 3]); r.mesh(3);
  assert.equal(d.draws, 4);
  assert.equal(d.draws, r.renderer.info.render.calls);
}

// A second caller on the same renderer reads the same tally and does not wrap twice.
{
  const r = fakeRenderer();
  countDriverDraws(r.renderer);
  const d = countDriverDraws(r.renderer);
  r.frame(); r.batched([1, 1, 1, 1]);
  assert.equal(d.draws, 4);
}

console.log('driver-draws: multi-draw entries counted, reset with renderer.info, held passes summed, no double count, the extension left for three to enable');

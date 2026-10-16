/**
 * THE PAGE BOTH SPIKE ENTRIES SHARE (T-2558): renderer setup, the block, the lights,
 * the stands, and `window.__hd`, the handle tools/measure_hd_spike.mjs drives.
 *
 * The page hands in its renderer, a `prepare(mesh)` that puts the confidence view on a
 * mesh's material its own way, and a `setView(on)` that flips it. Everything else is
 * the same code on both pages, so a difference between their readings is the renderer's.
 */

import * as THREE from 'three';
import { loadBlock, addLights, stands, dollyPose, enuToWorld } from './block.js';

const nextFrame = () => new Promise((r) => requestAnimationFrame(r));

export async function runSpike({ renderer, backend, prepare, setView, finish }) {
  const status = document.getElementById('status');
  const say = (text) => { if (status) status.textContent = text; };
  const params = new URLSearchParams(location.search);
  const dataBase = new URL(params.get('data') ?? '../data/', location.href);
  const t0 = performance.now();

  renderer.setPixelRatio(window.devicePixelRatio || 1);
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  document.getElementById('stage').appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.3, 2000);

  say('Loading the Glessner block…');
  const load = await loadBlock({
    renderer, dataBase, onProgress: (i, n) => say(`Loading the Glessner block… ${i} of ${n}`),
  });
  const tLoaded = performance.now();
  load.group.traverse((o) => { if (o.isMesh) prepare(o); });
  scene.add(load.group);
  const c = load.centre;
  addLights(scene, load.sun, enuToWorld(c.local_e, c.local_n, load.heightfield.sample(c.local_e, c.local_n)));

  const standList = stands(load);
  function setStand(id) {
    const s = standList.find((x) => x.id === id) ?? standList[0];
    camera.position.copy(s.eye);
    camera.lookAt(s.look);
    camera.updateMatrixWorld();
    return s.id;
  }
  setStand('spawn');

  if (renderer.compileAsync) await renderer.compileAsync(scene, camera);
  renderer.render(scene, camera);
  await nextFrame();
  renderer.render(scene, camera);
  await nextFrame();
  const tReady = performance.now();

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  /** Draw the current pose `n` times, each on its own frame, so a capture is presented. */
  async function settle(n = 3) {
    for (let i = 0; i < n; i += 1) {
      renderer.render(scene, camera);
      await nextFrame();
    }
  }

  /**
   * The moving reading: `frames` poses along dollyPose, one per animation frame. Returns
   * every frame interval (rAF timestamp to rAF timestamp) and the time the render call
   * itself took on the main thread.
   */
  async function dolly(frames = 120) {
    const intervals = [];
    const renderMs = [];
    let last = await nextFrame();
    for (let i = 0; i < frames; i += 1) {
      const pose = dollyPose(load, i / Math.max(1, frames - 1));
      camera.position.copy(pose.eye);
      camera.lookAt(pose.look);
      const t = performance.now();
      renderer.render(scene, camera);
      renderMs.push(performance.now() - t);
      const now = await nextFrame();
      intervals.push(now - last);
      last = now;
    }
    return { intervals, renderMs };
  }

  /**
   * The same dolly with every frame waited out: render, then `finish()` (the page's way
   * of blocking until the GPU has done the work: onSubmittedWorkDone on WebGPU, a
   * one-pixel readPixels on WebGL). A frame interval only says how often the page was
   * given a frame; this says what each frame cost to finish, on either API.
   */
  async function dollySynced(frames = 120) {
    const costMs = [];
    for (let i = 0; i < frames; i += 1) {
      const pose = dollyPose(load, i / Math.max(1, frames - 1));
      camera.position.copy(pose.eye);
      camera.lookAt(pose.look);
      const t = performance.now();
      renderer.render(scene, camera);
      await finish();
      costMs.push(performance.now() - t);
      await nextFrame();
    }
    return { costMs };
  }

  /**
   * A capture read off the canvas in the same task as its render, so it is the frame
   * this renderer drew, read the same way on both APIs.
   */
  async function capture() {
    await settle(2);
    renderer.render(scene, camera);
    return renderer.domElement.toDataURL('image/png');
  }

  function info() {
    const r = renderer.info?.render ?? {};
    let meshes = 0;
    let triangles = 0;
    load.group.traverse((o) => {
      if (!o.isMesh) return;
      meshes += 1;
      const g = o.geometry;
      triangles += (g.index ? g.index.count : g.attributes.position.count) / 3;
    });
    return {
      backend: typeof backend === 'function' ? backend() : backend,
      calls: r.drawCalls ?? r.calls ?? null,
      renderedTriangles: r.triangles ?? null,
      meshes,
      triangles: Math.round(triangles),
    };
  }

  /**
   * Every block texture onto the GPU now. WebGLRenderer uploads a texture on its first
   * draw; WebGPURenderer's compileAsync had already uploaded all of them at boot. So a
   * reading taken before this compares the whole block on one page with whatever the
   * camera has seen on the other. Both renderers have `initTexture`.
   */
  async function uploadAll() {
    const seen = new Set();
    load.group.traverse((o) => {
      if (!o.isMesh) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        for (const v of Object.values(m)) {
          if (v?.isTexture && !seen.has(v)) { seen.add(v); renderer.initTexture(v); }
        }
      }
    });
    await settle(2);
    return seen.size;
  }

  /** The block's textures as three holds them: what each page was handed to upload. */
  function textures() {
    const seen = new Set();
    const rows = { compressed: { count: 0, texels: 0 }, image: { count: 0, texels: 0 }, other: { count: 0, texels: 0 } };
    load.group.traverse((o) => {
      if (!o.isMesh) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        for (const v of Object.values(m)) {
          if (!v?.isTexture || seen.has(v)) continue;
          seen.add(v);
          const w = v.image?.width ?? v.mipmaps?.[0]?.width ?? 0;
          const h = v.image?.height ?? v.mipmaps?.[0]?.height ?? 0;
          const row = v.isCompressedTexture ? rows.compressed : (v.image ? rows.image : rows.other);
          row.count += 1;
          row.texels += w * h;
          row.formats ??= {};
          row.formats[v.format] = (row.formats[v.format] ?? 0) + 1;
        }
      }
    });
    return rows;
  }

  window.__hd = {
    textures,
    uploadAll,
    ready: true,
    backend: info().backend,
    bootMs: Math.round(tReady - t0),
    loadMs: Math.round(tLoaded - t0),
    loaded: load.loaded,
    problems: load.problems,
    bytes: load.bytes,
    sun: load.sun,
    stands: standList.map((s) => s.id),
    info,
    setStand,
    async setView(on) { setView(!!on); await settle(); return !!on; },
    settle,
    capture,
    dolly,
    dollySynced,
  };
  say(`${info().backend} · ${load.loaded.length} structures · ready in ${Math.round(tReady - t0)} ms`);
  return window.__hd;
}

export function fail(err) {
  const status = document.getElementById('status');
  if (status) status.textContent = `Failed: ${err?.message ?? err}`;
  /**
   * Every block texture onto the GPU now. WebGLRenderer uploads a texture on its first
   * draw; WebGPURenderer's compileAsync had already uploaded all of them at boot. So a
   * reading taken before this compares the whole block on one page with whatever the
   * camera has seen on the other. Both renderers have `initTexture`.
   */
  async function uploadAll() {
    const seen = new Set();
    load.group.traverse((o) => {
      if (!o.isMesh) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        for (const v of Object.values(m)) {
          if (v?.isTexture && !seen.has(v)) { seen.add(v); renderer.initTexture(v); }
        }
      }
    });
    await settle(2);
    return seen.size;
  }

  /** The block's textures as three holds them: what each page was handed to upload. */
  function textures() {
    const seen = new Set();
    const rows = { compressed: { count: 0, texels: 0 }, image: { count: 0, texels: 0 }, other: { count: 0, texels: 0 } };
    load.group.traverse((o) => {
      if (!o.isMesh) return;
      for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        for (const v of Object.values(m)) {
          if (!v?.isTexture || seen.has(v)) continue;
          seen.add(v);
          const w = v.image?.width ?? v.mipmaps?.[0]?.width ?? 0;
          const h = v.image?.height ?? v.mipmaps?.[0]?.height ?? 0;
          const row = v.isCompressedTexture ? rows.compressed : (v.image ? rows.image : rows.other);
          row.count += 1;
          row.texels += w * h;
          row.formats ??= {};
          row.formats[v.format] = (row.formats[v.format] ?? 0) + 1;
        }
      }
    });
    return rows;
  }

  window.__hd = {
    textures,
    uploadAll, ready: false, error: String(err?.stack ?? err) };
  throw err;
}

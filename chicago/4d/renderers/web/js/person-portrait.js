// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * person-portrait.js — a picture of the visitor's own person for the Settings card (T-3644) and
 * the character creator (person-creator.js).
 *
 * The figure is the one the town draws (visitor-person.js visitorActor: the people layer's own
 * body, dress, face, skin and hair), stood in a small lit stage of its own and rendered by the
 * scene's renderer into an sRGB target (three applies the tone curve and the colour-space encode
 * there, as world.js's horizon ring relies on), read back and laid on a 2D canvas. No second
 * WebGL context is made: a phone keeps its one. `frame: 'face'` draws the same figure's face up
 * close (Kevin, 2026-11-19: "the face would be nice in addition to the body to see the face up
 * close"), framed on its eyes.
 *
 * Kept fast (Kevin, 2026-11-27: "optimize the rendering of that"):
 *   - the figure is built once per choice and kept, so a turn or a zoom is one render, no build;
 *   - each canvas size keeps its own target, made once, not one per picture;
 *   - the pixels come back through a pixel-pack buffer behind a fence (as crowd.js reads its
 *     colours), so a turn being dragged never stalls the frame waiting on the GPU; the newest
 *     turn asked for wins, the ones overtaken are never drawn;
 *   - `preview` draws a choice not yet made (the creator's option pictures) on a figure of its
 *     own under a row of its own, and lets it go at once.
 */
import * as THREE from 'three';
import { visitorActor, VISITOR_PERSON_ID } from './visitor-person.js';
import { likenessSheetsReady, photoFacePagesReady, photoFaceTextureStats } from './human-skin.js';

export const PREVIEW_PERSON_ID = `${VISITOR_PERSON_ID}:preview`;

export function createPersonPortrait({ renderer, humans, person, lod = 1 }) {
  const stage = new THREE.Scene();
  stage.add(new THREE.HemisphereLight(0xdfe8f2, 0x5a4a3a, 1.6));
  const key = new THREE.DirectionalLight(0xfff2e0, 2.6); key.position.set(1.6, 2.6, 2.4); stage.add(key);
  const rim = new THREE.DirectionalLight(0xcfe0ff, 1.0); rim.position.set(-2, 1.8, -2); stage.add(rim);
  const camera = new THREE.PerspectiveCamera(22, 2 / 3, 0.1, 50);
  const turnGroup = new THREE.Group(); stage.add(turnGroup);
  let held = null;   // { year, lod, actor }
  const level = lod;
  const targets = new Map();   // `${W}x${H}` -> WebGLRenderTarget, made once
  let chain = Promise.resolve();
  const builds = { count: 0, ms: 0 }, renders = { count: 0, ms: 0 };

  async function build(who, year, { id, personId }) {
    const t0 = performance.now();
    const actor = await visitorActor(humans(), who, year, { id, state: 'standing', lod: level, personId });
    if (!actor) return null;
    await actor.setLod(level);
    if (!actor.body) { actor.dispose(); return null; }
    actor.play?.('idle', { fade: 0, time: 0.6 });
    actor.body.mixer?.update(0);
    for (const m of actor.body.meshes ?? []) m.frustumCulled = false;
    actor.root.position.set(0, 0, 0);
    builds.count++; builds.ms += performance.now() - t0;
    return actor;
  }

  async function figure(year) {
    if (held?.year === year && held.lod === level && held.actor.body) return held.actor;
    forget();
    const actor = await build(person, year, { id: `visitor:portrait:${year}`, personId: VISITOR_PERSON_ID });
    if (!actor) return null;
    turnGroup.add(actor.root);
    held = { year, lod: level, actor };
    return actor;
  }

  function forget() {
    if (!held) return;
    held.actor.root.removeFromParent();
    held.actor.dispose();
    held = null;
  }

  /** Aim the camera at `actor`, turned `turn` degrees: whole, or the face up close. */
  function aim(actor, { turn, frame, aspect }) {
    camera.aspect = aspect;
    camera.updateProjectionMatrix();
    const face = frame === 'face' ? faceAt(actor, turn) : null;
    if (face) {
      // On the eyes, a little under them: the face from brow to chin, the hair and hat over it.
      camera.position.set(face.x, face.y, face.z + FACE_HALF_M / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
      camera.lookAt(face);
    } else {
      turnGroup.rotation.y = THREE.MathUtils.degToRad(20 + turn);   // a little turned, toward the light
      stage.updateMatrixWorld(true);
      const box = new THREE.Box3().setFromObject(actor.root);
      const h = Math.max(1.2, box.max.y - Math.min(0, box.min.y));
      const mid = new THREE.Vector3(0, h * 0.52, 0);
      const dist = (h * 0.62 * Math.max(1, (2 / 3) / aspect)) / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
      camera.position.set(0, mid.y + 0.05, dist);
      camera.lookAt(mid);
    }
    camera.updateMatrixWorld();
  }

  /** Draw the person in `year`, turned `turn` degrees, onto `canvas`: whole, or (`frame: 'face'`)
   * the face up close. False with no people layer. Calls run one after another. */
  function draw(canvas, opts = {}) {
    const run = chain.then(() => drawNow(canvas, opts));
    chain = run.catch(() => {});
    return run;
  }

  async function drawNow(canvas, { year, turn = 0, frame = 'whole' } = {}) {
    if (!humans()?.createActor) return false;
    const actor = await figure(String(year));
    if (!actor) return false;
    aim(actor, { turn, frame, aspect: canvas.width / canvas.height });
    await paint(canvas);
    // T-3553: a photographed face is drawn from its sharp page only once that page has loaded
    // (human-skin.js asks for it as the face is drawn near the camera, and the crowd's small
    // sheet stands in till then), and a face sheet still on its way shows the body's own skin.
    // So when either was still coming, draw again once it has: the face, not its stand-in.
    const tick = new Promise((done) => setTimeout(() => done(true), 0));
    const sheets = await Promise.race([likenessSheetsReady().then(() => false), tick]);
    if (sheets || photoFaceTextureStats().pendingPages > 0) {
      await Promise.all([likenessSheetsReady(), photoFacePagesReady()]);
      if (held?.actor === actor) { aim(actor, { turn, frame, aspect: canvas.width / canvas.height }); await paint(canvas); }
    }
    return true;
  }

  /**
   * A choice not yet made, drawn small (the character creator's option pictures): `who` is
   * { catalog, record(year), asset(year) } for it (visitor-person.js personRecord/personAsset).
   * Built on a figure of its own under PREVIEW_PERSON_ID, so the visitor's own row and figure
   * are never touched, rendered once and let go. Runs in turn with `draw`.
   */
  function preview(canvas, who, opts = {}) {
    const run = chain.then(async () => {
      if (!humans()?.createActor) return false;
      const actor = await build(who, String(opts.year), { id: `visitor:preview:${opts.year}`, personId: PREVIEW_PERSON_ID });
      if (!actor) return false;
      const had = held?.actor.root ?? null;
      had?.removeFromParent();
      turnGroup.add(actor.root);
      try {
        aim(actor, { turn: opts.turn ?? 0, frame: opts.frame ?? 'whole', aspect: canvas.width / canvas.height });
        await paint(canvas);
      } finally {
        actor.root.removeFromParent();
        actor.dispose();
        if (had && held) turnGroup.add(had);
      }
      return true;
    });
    chain = run.catch(() => {});
    return run;
  }

  /** Render the stage into this size's own target and lay its pixels on `canvas`. */
  async function paint(canvas) {
    const W = canvas.width, H = canvas.height, size = `${W}x${H}`;
    let rt = targets.get(size);
    if (!rt) {
      // One target a size: a creator, a tab and the option pictures use three at most.
      if (targets.size >= 4) { for (const t of targets.values()) t.dispose(); targets.clear(); }
      rt = new THREE.WebGLRenderTarget(W, H, { colorSpace: THREE.SRGBColorSpace, samples: 4 });
      targets.set(size, rt);
    }
    const t0 = performance.now();
    const was = renderer.getRenderTarget();
    const clear = renderer.getClearColor(new THREE.Color()), alpha = renderer.getClearAlpha();
    let px = null;
    try {
      renderer.setRenderTarget(rt);
      renderer.setClearColor(0x000000, 0);
      renderer.clear();
      renderer.render(stage, camera);
      px = readLater(renderer, rt, W, H);
    } finally {
      renderer.setRenderTarget(was);
      renderer.setClearColor(clear, alpha);
    }
    const pixels = await px;
    renders.count++; renders.ms += performance.now() - t0;
    if (!pixels) return false;
    await lay(canvas, pixels, W, H);
    return true;
  }

  /** Turns to the figure already built: what a drag asks for. Only the newest turn is drawn. */
  let wanted = null, turning = null;
  function turnTo(canvas, opts) {
    wanted = { canvas, opts };
    if (!turning) {
      turning = (async () => {
        while (wanted) {
          const w = wanted; wanted = null;
          await draw(w.canvas, w.opts).catch(() => false);
        }
      })().finally(() => { turning = null; });
    }
    return turning;
  }

  function faceAt(actor, turn) {
    turnGroup.rotation.y = THREE.MathUtils.degToRad(8 + turn);
    stage.updateMatrixWorld(true);
    const eyes = ['eye_l', 'eye_r'].map((n) => actor.root.getObjectByName(n)).filter(Boolean);
    if (!eyes.length) return null;
    const at = new THREE.Vector3(), p = new THREE.Vector3();
    for (const e of eyes) at.add(e.getWorldPosition(p));
    return at.multiplyScalar(1 / eyes.length).add(new THREE.Vector3(0, -FACE_BELOW_EYES_M, 0));
  }

  function dispose() {
    forget();
    for (const t of targets.values()) t.dispose();
    targets.clear();
  }

  return { draw, turnTo, preview, forget, dispose, stats: () => ({ builds: { ...builds }, renders: { ...renders }, lod: level }) };
}

/**
 * A target's pixels without waiting on the GPU: into a pixel-pack buffer behind a fence, polled
 * (WebGL2), as crowd.js readLater does; the buffer is unbound before this returns. On WebGL1, the
 * plain read. Resolves the rows (bottom-up, as GL gives them) or null.
 */
function readLater(renderer, rt, W, H) {
  const gl = renderer.getContext();
  const px = new Uint8Array(W * H * 4);
  if (typeof WebGL2RenderingContext === 'undefined' || !(gl instanceof WebGL2RenderingContext)) {
    renderer.readRenderTargetPixels(rt, 0, 0, W, H, px);
    return Promise.resolve(px);
  }
  const fb = renderer.properties.get(rt).__webglFramebuffer;
  renderer.state.bindFramebuffer(gl.FRAMEBUFFER, fb);
  const buffer = gl.createBuffer();
  gl.bindBuffer(gl.PIXEL_PACK_BUFFER, buffer);
  gl.bufferData(gl.PIXEL_PACK_BUFFER, px.byteLength, gl.STREAM_READ);
  gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, 0);
  gl.bindBuffer(gl.PIXEL_PACK_BUFFER, null);
  const fence = gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0);
  gl.flush();
  const since = performance.now();
  return new Promise((resolve) => {
    const done = (ok) => { gl.deleteSync(fence); gl.deleteBuffer(buffer); resolve(ok ? px : null); };
    const probe = () => {
      const state = gl.clientWaitSync(fence, 0, 0);
      if (state === gl.TIMEOUT_EXPIRED && performance.now() - since < 30000) { setTimeout(probe, 4); return; }
      if (state !== gl.ALREADY_SIGNALED && state !== gl.CONDITION_SATISFIED) { done(false); return; }
      gl.bindBuffer(gl.PIXEL_PACK_BUFFER, buffer);
      gl.getBufferSubData(gl.PIXEL_PACK_BUFFER, 0, px);
      gl.bindBuffer(gl.PIXEL_PACK_BUFFER, null);
      done(true);
    };
    setTimeout(probe, 0);
  });
}

/** GL's bottom-up rows onto a canvas: flipped by the browser where it can, by hand where not. */
async function lay(canvas, px, W, H) {
  const ctx = canvas.getContext('2d');
  const img = new ImageData(new Uint8ClampedArray(px.buffer, px.byteOffset, px.byteLength), W, H);
  if (typeof createImageBitmap === 'function') {
    try {
      const bmp = await createImageBitmap(img, { imageOrientation: 'flipY', premultiplyAlpha: 'none' });
      ctx.clearRect(0, 0, W, H);
      ctx.drawImage(bmp, 0, 0);
      bmp.close?.();
      return;
    } catch { /* the hand flip below */ }
  }
  const out = new ImageData(W, H);
  for (let y = 0; y < H; y++) out.data.set(px.subarray((H - 1 - y) * W * 4, (H - y) * W * 4), y * W * 4);
  ctx.putImageData(out, 0, 0);
}

/** The close face: half its frame's height, and how far under the eyes its centre sits (m). */
export const FACE_HALF_M = 0.16;
export const FACE_BELOW_EYES_M = 0.025;

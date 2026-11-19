// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * person-portrait.js — a picture of the visitor's own person for the Settings card (T-3644).
 *
 * The figure is the one the town draws (visitor-person.js visitorActor: the people layer's own
 * body, dress, face, skin and hair), stood in a small lit stage of its own and rendered once per
 * change by the scene's renderer into an sRGB target (three applies the tone curve and the
 * colour-space encode there, as world.js's horizon ring relies on), read back and laid on a 2D
 * canvas. Nothing is drawn every frame and no second WebGL context is made: a phone keeps its
 * one. The figure is kept while the person is unchanged so a turn is one render; `forget` lets
 * it go.
 */
import * as THREE from 'three';
import { visitorActor } from './visitor-person.js';

export function createPersonPortrait({ renderer, humans, person, lod = 1 }) {
  const stage = new THREE.Scene();
  stage.add(new THREE.HemisphereLight(0xdfe8f2, 0x5a4a3a, 1.6));
  const key = new THREE.DirectionalLight(0xfff2e0, 2.6); key.position.set(1.6, 2.6, 2.4); stage.add(key);
  const rim = new THREE.DirectionalLight(0xcfe0ff, 1.0); rim.position.set(-2, 1.8, -2); stage.add(rim);
  const camera = new THREE.PerspectiveCamera(22, 2 / 3, 0.1, 50);
  const turnGroup = new THREE.Group(); stage.add(turnGroup);
  let held = null;   // { year, actor }

  async function figure(year) {
    if (held?.year === year && held.actor.body) return held.actor;
    forget();
    const actor = await visitorActor(humans(), person, year, { id: `visitor:portrait:${year}`, state: 'standing', lod });
    if (!actor) return null;
    await actor.setLod(lod);
    if (!actor.body) { actor.dispose(); return null; }
    actor.play?.('idle', { fade: 0, time: 0.6 });
    actor.body.mixer?.update(0);
    for (const m of actor.body.meshes ?? []) m.frustumCulled = false;
    actor.root.position.set(0, 0, 0);
    turnGroup.add(actor.root);
    held = { year, actor };
    return actor;
  }

  function forget() {
    if (!held) return;
    held.actor.root.removeFromParent();
    held.actor.dispose();
    held = null;
  }

  /** Draw the person in `year`, turned `turn` degrees, onto `canvas`. False with no people layer. */
  async function draw(canvas, { year, turn = 0 } = {}) {
    if (!humans()?.createActor) return false;
    const actor = await figure(String(year));
    if (!actor) return false;
    turnGroup.rotation.y = THREE.MathUtils.degToRad(20 + turn);   // a little turned, toward the light
    stage.updateMatrixWorld(true);
    const box = new THREE.Box3().setFromObject(actor.root);
    const h = Math.max(1.2, box.max.y - Math.min(0, box.min.y));
    const mid = new THREE.Vector3(0, h * 0.52, 0);
    const dist = (h * 0.62) / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    camera.position.set(0, mid.y + 0.05, dist);
    camera.lookAt(mid);
    camera.updateMatrixWorld();
    const W = canvas.width, H = canvas.height;
    const rt = new THREE.WebGLRenderTarget(W, H, { colorSpace: THREE.SRGBColorSpace, samples: 4 });
    const was = renderer.getRenderTarget();
    const clear = renderer.getClearColor(new THREE.Color()), alpha = renderer.getClearAlpha();
    const px = new Uint8Array(W * H * 4);
    try {
      renderer.setRenderTarget(rt);
      renderer.setClearColor(0x000000, 0);
      renderer.clear();
      renderer.render(stage, camera);
      renderer.readRenderTargetPixels(rt, 0, 0, W, H, px);
    } finally {
      renderer.setRenderTarget(was);
      renderer.setClearColor(clear, alpha);
      rt.dispose();
    }
    // GL rows run bottom-up; the canvas's top-down.
    const img = new ImageData(W, H);
    for (let y = 0; y < H; y++) img.data.set(px.subarray((H - 1 - y) * W * 4, (H - y) * W * 4), y * W * 4);
    canvas.getContext('2d').putImageData(img, 0, 0);
    return true;
  }

  return { draw, forget, dispose: forget };
}

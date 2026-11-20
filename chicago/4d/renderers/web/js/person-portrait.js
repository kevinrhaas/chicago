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
 * it go. `frame: 'face'` draws the same figure's face up close (Kevin, 2026-11-19: "the face
 * would be nice in addition to the body to see the face up close"), framed on its eyes.
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

  /** Draw the person in `year`, turned `turn` degrees, onto `canvas`: whole, or (`frame: 'face'`)
   * the face up close. False with no people layer. */
  async function draw(canvas, { year, turn = 0, frame = 'whole' } = {}) {
    if (!humans()?.createActor) return false;
    const actor = await figure(String(year));
    if (!actor) return false;
    camera.aspect = canvas.width / canvas.height;
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
      const dist = (h * 0.62) / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
      camera.position.set(0, mid.y + 0.05, dist);
      camera.lookAt(mid);
    }
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

  /** The face's centre (between the eyes, a little under them) with the figure turned `turn`
   * degrees from the front (and a touch toward the key light); null on a body without eyes. */
  function faceAt(actor, turn) {
    turnGroup.rotation.y = THREE.MathUtils.degToRad(8 + turn);
    stage.updateMatrixWorld(true);
    const eyes = ['eye_l', 'eye_r'].map((n) => actor.root.getObjectByName(n)).filter(Boolean);
    if (!eyes.length) return null;
    const at = new THREE.Vector3(), p = new THREE.Vector3();
    for (const e of eyes) at.add(e.getWorldPosition(p));
    return at.multiplyScalar(1 / eyes.length).add(new THREE.Vector3(0, -FACE_BELOW_EYES_M, 0));
  }

  return { draw, forget, dispose: forget };
}

/** The close face: half its frame's height, and how far under the eyes its centre sits (m). */
export const FACE_HALF_M = 0.16;
export const FACE_BELOW_EYES_M = 0.025;

/**
 * CLASSIC — walk/'s engine on the Glessner block (T-2558): three's WebGLRenderer and
 * walk/'s own confidence view, `confidence.js`'s `onBeforeCompile` patch, imported from
 * walk/'s published copy unchanged. This is the baseline the WebGPU page is held to.
 */

import * as THREE from 'three';
import { createConfidenceView } from '../../walk/js/confidence.js';
import { runSpike, fail } from './harness.js';

const PIXEL = new Uint8Array(4);

try {
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  const view = createConfidenceView();
  // buildings.js: "Shadows have to agree with the view" — one patched depth material,
  // so a dithered wall casts a dithered shadow. The same here, on every block mesh.
  const depthMaterial = view.patch(new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking }));
  await runSpike({
    renderer,
    backend: 'webgl-classic',
    prepare(mesh) {
      const mats = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
      for (const m of mats) view.patch(m);
      if (mesh.name !== 'ground') mesh.customDepthMaterial = depthMaterial;
    },
    setView(on) { view.uniforms.uConfMode.value = on ? 1 : 0; },
    finish() {
      const gl = renderer.getContext();
      gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, PIXEL);
    },
  });
} catch (err) {
  fail(err);
}

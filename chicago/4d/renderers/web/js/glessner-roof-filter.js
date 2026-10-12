import * as THREE from 'three';
import { hasInspectionLod } from './scene-loader.js';

/** T-2204. Texture mipmaps cannot filter the individual tile noses. The asset
 * marks ONLY those relief vertices with their exposed course in metres;
 * continuous beds and ridge ornaments have zero. Blend unresolved relief over
 * the existing, identically scaled mipmapped bed. No geometry or UV is moved.
 *
 * The transition spans 6–24 projected course pixels, not a fixed world distance:
 * changing FOV, viewport or render quality retains the same sampling limit.
 * A course can still span several pixels while its 6 mm lap nose is subpixel.
 * The wider 6–24 pixel interval filters those noses before they form broad bands
 * in the middle-distance pullback (2–8 left visible interference there).
 */
export function filterGlessnerRoof(material, record, geometry) {
  if (!hasInspectionLod(record) || !/^roof_plane(?:_[123])?$/.test(material.name)) return;
  for (const texture of new Set([material.map, material.normalMap, material.roughnessMap])) {
    if (!texture) continue;
    texture.minFilter = THREE.LinearMipmapLinearFilter;
    texture.magFilter = THREE.LinearFilter;
    texture.generateMipmaps = true;
    texture.anisotropy = 8; // Three clamps to the device's supported maximum.
    texture.needsUpdate = true;
  }
  if (material.name === 'roof_plane' || !geometry.hasAttribute('_roof_detail')) return;
  material.userData.roofFilter = 'course-pixels-v1';
  material.transparent = true;
  // Crests share the clay batch and remain opaque: retain their self-occlusion.
  // Fully filtered relief is discarded below, leaving the bed's depth intact.
  material.depthWrite = true;
  material.forceSinglePass = true;
  const projectedPixels = { value: 1 };
  const size = new THREE.Vector2();
  const beforeRender = material.onBeforeRender;
  material.onBeforeRender = function(renderer, scene, camera, ...rest) {
    beforeRender?.call(this, renderer, scene, camera, ...rest);
    renderer.getDrawingBufferSize(size);
    projectedPixels.value = size.y * camera.projectionMatrix.elements[5] / 2;
  };
  const prior = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    prior?.(shader, renderer);
    shader.uniforms.chiRoofProjectionPixels = projectedPixels;
    shader.vertexShader = 'attribute float _roof_detail;\nvarying float vChiRoofCourse;\n'
      + shader.vertexShader.replace('#include <begin_vertex>',
        '#include <begin_vertex>\nvChiRoofCourse = _roof_detail;');
    shader.fragmentShader = 'uniform float chiRoofProjectionPixels;\nvarying float vChiRoofCourse;\n'
      + shader.fragmentShader.replace('#include <alphamap_fragment>', `#include <alphamap_fragment>
        if (vChiRoofCourse > 0.0) {
          float coursePixels = vChiRoofCourse * chiRoofProjectionPixels / max(vViewPosition.z, 0.001);
          float coverage = smoothstep(6.0, 24.0, coursePixels);
          if (coverage <= 0.0) discard;
          diffuseColor.a *= coverage;
        }`);
  };
  material.customProgramCacheKey = () => 'glessner-roof-course-pixels-v1';
  material.needsUpdate = true;
}

/**
 * Thin foliage in the existing opaque, alpha-tested pass (T-3747).
 * This is an artistic thin-sheet approximation, not a measured leaf BSDF.
 * Direct transmission uses three's already shadowed incident light; the small
 * sky term follows time-of-day.js. No new texture, light, render target or pass.
 */
import * as THREE from 'three';
import { LEAF_SKY } from './time-of-day.js';

export function patchLeafLight(material, { mask = '1.0', lowSpec = false } = {}) {
  const prior = material.onBeforeCompile;
  const key = material.customProgramCacheKey === THREE.Material.prototype.customProgramCacheKey
    ? String(prior) : material.customProgramCacheKey();
  material.onBeforeCompile = (shader, renderer) => {
    prior(shader, renderer);
    const pars = '#include <lights_physical_pars_fragment>';
    const end = '#include <lights_fragment_end>';
    if (!shader.fragmentShader.includes(pars) || !shader.fragmentShader.includes(end)) {
      throw new Error('leaf lighting: missing standard lighting anchors');
    }
    shader.uniforms.uLeafSky = LEAF_SKY;
    shader.fragmentShader = 'uniform float uLeafSky;\n' + shader.fragmentShader
      .replace(pars, `${pars}
void chiLeafDirect(const in IncidentLight light, const in vec3 position,
    const in vec3 normal, const in vec3 viewDir, const in vec3 clearcoatNormal,
    const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
  RE_Direct_Physical(light, position, normal, viewDir, clearcoatNormal, material, reflectedLight);
  float chiBack = max(-dot(normal, light.direction), 0.0);
  ${lowSpec ? 'float chiTransmit = 0.16;' : `
  float chiForward = max(dot(viewDir, -light.direction), 0.0);
  float chiTransmit = 0.08 + 0.20 * chiForward * chiForward;`}
  // light.color has already received the light's attenuation and shadow test.
  // The record's leaf colour still controls the hue; wood is masked out.
  reflectedLight.directDiffuse += material.diffuseColor * vec3(0.8, 1.0, 0.6)
    * light.color * (RECIPROCAL_PI * chiBack * chiTransmit * (${mask}));
}
#undef RE_Direct
#define RE_Direct chiLeafDirect
`)
      .replace(end, `${end}
float chiLeafFill = 1.0;
#if NUM_DIR_LIGHTS > 0
  float chiLeafBack = max(-dot(normal, directionalLights[0].direction), 0.0);
  chiLeafFill = 0.72 + 0.56 * chiLeafBack;
#endif
reflectedLight.indirectDiffuse += diffuseColor.rgb * (uLeafSky * chiLeafFill * (${mask}));
`);
  };
  material.customProgramCacheKey = () => `${key}|leaf-light-3747-${mask}-${lowSpec}`;
}

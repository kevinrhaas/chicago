/** Light's matte nonmetals keep shaped sky fill without a glossy environment lookup.
 * Full and Balanced compile the original physical lighting unchanged.
 */
import * as THREE from 'three';

const DEFINE = 'CHI_ROUGH_LIGHT_3748';
const DIRECT = /* glsl */`
void chiRoughDirect(const in IncidentLight light, const in vec3 position,
 const in vec3 normal, const in vec3 viewDir, const in vec3 clearcoatNormal,
 const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
  vec3 irradiance = max(dot(normal, light.direction), 0.0) * light.color;
  reflectedLight.directSpecular += irradiance * BRDF_GGX(light.direction, viewDir, normal, material);
  reflectedLight.directDiffuse += irradiance * BRDF_Lambert(material.diffuseContribution);
}
#define RE_Direct_Physical chiRoughDirect
`;
const ENVIRONMENT = /* glsl */`
void chiRoughEnvironment(const in vec3 radiance, const in vec3 irradiance,
 const in vec3 clearcoatRadiance, const in vec3 position, const in vec3 normal,
 const in vec3 viewDir, const in vec3 clearcoatNormal,
 const in PhysicalMaterial material, inout ReflectedLight reflectedLight) {
  // A diffuse convolution of the actual sky and ground, not a flat ambient colour.
  // Constant dielectric reflectance is the deliberate Light approximation.
  reflectedLight.indirectDiffuse += irradiance * RECIPROCAL_PI
    * (material.diffuseContribution * 0.96 + vec3(0.04));
}
#define RE_IndirectSpecular_Physical chiRoughEnvironment
`;

function eligible(material) {
  return material?.isMeshStandardMaterial && !material.isMeshPhysicalMaterial
    && material.metalness === 0 && material.roughness >= 0.65
    && !material.roughnessMap && !material.userData.chiHasVertexRoughness;
}

export function createRoughSurfaceLighting() {
  let light = false;
  const records = new WeakMap();
  const live = new Set();
  function flags(material) {
    const wanted = light && eligible(material);
    if (!!material.defines?.[DEFINE] === wanted) return false;
    material.defines = { ...material.defines };
    if (wanted) material.defines[DEFINE] = 1;
    else delete material.defines[DEFINE];
    material.needsUpdate = true;
    return true;
  }
  function prepare(material) {
    if (!eligible(material) && !records.has(material)) return material;
    let record = records.get(material);
    if (!record) {
      const prior = material.onBeforeCompile;
      const key = material.customProgramCacheKey === THREE.Material.prototype.customProgramCacheKey
        ? String(prior) : material.customProgramCacheKey();
      record = { prior, key };
      records.set(material, record);
      material.onBeforeCompile = function (shader, renderer) {
        prior.call(this, shader, renderer);
        if (!material.defines?.[DEFINE] || !eligible(material)) return;
        const marker = '#include <lights_physical_pars_fragment>';
        if (!shader.fragmentShader.includes(marker)) return;
        // Keep the standard include available to a later leaf/box/grade hook.
        // Aliasing the physical entry points also preserves a leaf's outer wrapper.
        shader.fragmentShader = shader.fragmentShader.replace(marker,
          marker + '\n' + DIRECT + '\n' + ENVIRONMENT);
      };
      material.customProgramCacheKey = () => `${key}|rough-light-3748-v3`;
      material.addEventListener('dispose', () => { live.delete(material); });
    }
    live.add(material);
    flags(material);
    return material;
  }
  return {
    prepare,
    set(on) {
      const next = !!on;
      if (next === light) return false;
      light = next;
      for (const material of live) flags(material);
      return true;
    },
    prepareScene(root) {
      root?.traverse((object) => {
        for (const material of [].concat(object.material ?? [])) prepare(material);
      });
    },
    get light() { return light; },
    get materials() { return live.size; },
  };
}

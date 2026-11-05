// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Cloth for the portable humans' plain-coloured garments (T-2804).
 *
 * Kevin, 2026-11-05, of Hans on his brougham: "his clothing has no texture or
 * anything". The exported garments are flat base colours, and 1904's phone
 * memory is at its ceiling, so this adds NO texture: a shader patch
 * that reads the garment's own bind-pose position and draws, at the surface:
 *
 *  - the weave: a 2/2 twill's diagonal wales on wool and on the trousers'
 *    cloth, a plain over-under on linen; a coarse cloth's pitch, faded out by
 *    its screen-space rate before it can alias, so it shows only up close;
 *    linen's slubs, thick places in its thread, as faint streaks;
 *  - heathering: the uneven take-up of dye in spun yarn, a three-octave
 *    value noise of a few percent of the colour;
 *  - wear: a slightly shinier, slightly greyer cloth where it is rubbed
 *    smooth, and soft rumples at the scale of a hand;
 *  - a cloth's sheen: a little more light at grazing angles.
 *
 * The weave and the rumples tip the shading normal (no geometry changes),
 * so the folds of the seated clip catch light like cloth.
 * Everything is a reconstructed authoring choice; no surviving garment or
 * photograph of these people's clothes is claimed (liberty L-driven-town-circuits-2804).
 *
 * Per-cloth differences are UNIFORMS, never code, so every cloth compiles
 * one program (see wall-relief.js on three's program cache). The cache key
 * names the chain, as confidence.js requires of a hook it chains beneath.
 */
import * as THREE from 'three';

/** Cloth by the garment material's name, as the portable-human exports name them. */
export const CLOTHS = Object.freeze({
  // pitch_m: one repeat of the weave; weave/heather/rumple: strengths; twill: 1 diagonal, 0 plain.
  wool: Object.freeze({ pitch_m: .008, weave: 1, heather: .16, rumple: 1, sheen: .22, twill: 1 }),
  cotton_twill: Object.freeze({ pitch_m: .007, weave: .9, heather: .12, rumple: 1, sheen: .16, twill: 1 }),
  linen: Object.freeze({ pitch_m: .005, weave: .6, heather: .08, rumple: .8, sheen: .1, twill: 0 }),
});
export function clothFor(material) {
  const name = material?.name ?? '';
  if (!/^garment_/.test(name)) return null;
  if (/wool|coat|waistcoat|vest|jacket/.test(name)) return CLOTHS.wool;
  if (/linen|shirt/.test(name)) return CLOTHS.linen;
  return CLOTHS.cotton_twill;
}

const KEY = 'chicago-fabric-v1';
const VERTEX = `
  vChiFabricP = position;
  vChiFabricN = normal;`;
const DECLARE = `
uniform vec4 chiFabric;
uniform vec2 chiFabricWear;
varying vec3 vChiFabricP;
varying vec3 vChiFabricN;
float chiFabricHash( vec3 p ) {
  p = fract( p * 0.3183099 + vec3( 0.71, 0.113, 0.419 ) );
  p *= 17.0;
  return fract( p.x * p.y * p.z * ( p.x + p.y + p.z ) );
}
float chiFabricNoise( vec3 x ) {
  vec3 i = floor( x ), f = fract( x );
  f = f * f * ( 3.0 - 2.0 * f );
  return mix( mix( mix( chiFabricHash( i ), chiFabricHash( i + vec3( 1.0, 0.0, 0.0 ) ), f.x ),
                   mix( chiFabricHash( i + vec3( 0.0, 1.0, 0.0 ) ), chiFabricHash( i + vec3( 1.0, 1.0, 0.0 ) ), f.x ), f.y ),
              mix( mix( chiFabricHash( i + vec3( 0.0, 0.0, 1.0 ) ), chiFabricHash( i + vec3( 1.0, 0.0, 1.0 ) ), f.x ),
                   mix( chiFabricHash( i + vec3( 0.0, 1.0, 1.0 ) ), chiFabricHash( i + vec3( 1.0, 1.0, 1.0 ) ), f.x ), f.y ), f.z );
}
vec3 chiFabricPerturb( vec3 surfPos, vec3 surfNorm, vec2 dHdxy, float faceDir ) {
  vec3 sx = dFdx( surfPos ), sy = dFdy( surfPos );
  vec3 r1 = cross( sy, surfNorm ), r2 = cross( surfNorm, sx );
  float det = dot( sx, r1 ) * faceDir;
  vec3 grad = sign( det ) * ( dHdxy.x * r1 + dHdxy.y * r2 );
  return normalize( abs( det ) * surfNorm - grad );
}
`;
// After the garment's colour is known: weave, heather and wear; the height
// the normal is tipped by is kept for the normal step below.
const COLOR = `
  float chiFabricH = 0.0;
  float chiFabricGloss = 0.0;
  {
    vec3 p = vChiFabricP;
    vec3 an = abs( normalize( vChiFabricN ) );
    // Across the cloth and up it: the bind pose stands upright, so the vertical
    // runs up every garment; across is whichever horizontal axis the face turns from.
    vec2 uv = vec2( an.x > an.z ? p.z : p.x, p.y );
    if ( an.y > 0.75 ) uv = p.xz;
    vec2 t = uv / chiFabric.x * 6.2831853;
    float twill = sin( t.x + t.y ) + 0.35 * sin( 2.0 * ( t.x + t.y ) + 1.3 );
    float plain = sin( t.x ) * sin( t.y );
    float weave = mix( plain, twill * 0.75, chiFabricWear.y );
    // Fade the weave by how fast it changes per pixel, before it can alias.
    float rate = max( fwidth( t.x ), fwidth( t.y ) );
    weave *= clamp( 1.6 - rate * 0.9, 0.0, 1.0 );
    float heather = chiFabricNoise( p * 160.0 ) * 0.45 + chiFabricNoise( p * 41.0 ) * 0.35 + chiFabricNoise( p * 9.0 ) * 0.2;
    float rumple = chiFabricNoise( p * 13.0 + 7.1 ) * 0.65 + chiFabricNoise( p * 31.0 + 3.7 ) * 0.35;
    float worn = smoothstep( 0.62, 0.9, chiFabricNoise( p * 5.5 + 1.9 ) );
    // Linen's slubs: thick places in the thread, streaks across a plain weave.
    float slub = chiFabricNoise( vec3( uv.x * 9.0, uv.y * 260.0, 0.5 ) );
    diffuseColor.rgb *= 1.0 + chiFabric.z * ( heather - 0.5 ) * 2.0 + chiFabric.y * 0.07 * weave
      + ( 1.0 - chiFabricWear.y ) * ( slub - 0.5 ) * 0.14;
    diffuseColor.rgb = mix( diffuseColor.rgb, vec3( dot( diffuseColor.rgb, vec3( 0.3, 0.59, 0.11 ) ) ) * 1.12, worn * 0.18 );
    // The height the shading normal is tipped by, in metres: a fraction of a
    // millimetre of thread relief, a millimetre or two of rumple.
    chiFabricH = weave * chiFabric.y * 0.0004 + ( rumple - 0.5 ) * chiFabric.w * 0.6;
    chiFabricGloss = worn;
  }`;
const ROUGHNESS = `
  roughnessFactor = clamp( roughnessFactor - chiFabricGloss * 0.12, 0.35, 1.0 );`;
const NORMAL = `
  normal = chiFabricPerturb( - vViewPosition, normal, vec2( dFdx( chiFabricH ), dFdy( chiFabricH ) ), faceDirection );`;
// A cloth's sheen: fibres catch light at grazing angles, a little, from the sky.
const SHEEN = `
  {
    float chiRim = pow( 1.0 - clamp( abs( dot( normalize( vViewPosition ), normal ) ), 0.0, 1.0 ), 3.0 );
    reflectedLight.indirectDiffuse += diffuseColor.rgb * chiFabricWear.x * chiRim * 2.0;
    reflectedLight.directDiffuse *= 1.0 + chiFabricWear.x * chiRim;
  }`;
const ANCHORS = ['#include <color_fragment>', '#include <roughnessmap_fragment>',
  '#include <normal_fragment_maps>', '#include <lights_fragment_end>'];

const patched = new WeakSet();
/**
 * Patch one garment material in place. Returns the cloth it was given, or null
 * for a material that is not a plain garment (skin, hair, eyes, shoes) or that
 * is not a lit standard material. Safe to call twice.
 */
export function patchFabric(material) {
  const cloth = clothFor(material);
  if (!cloth || !material.isMeshStandardMaterial) return null;
  if (patched.has(material)) return cloth;
  patched.add(material);
  const prior = material.onBeforeCompile;
  const hadKey = Object.prototype.hasOwnProperty.call(material, 'customProgramCacheKey');
  const priorKey = hadKey ? String(material.customProgramCacheKey())
    : (typeof prior === 'function' && prior !== THREE.Material.prototype.onBeforeCompile ? prior.toString() : '');
  const uniforms = {
    chiFabric: { value: new THREE.Vector4(cloth.pitch_m, cloth.weave, cloth.heather, cloth.rumple * .01) },
    chiFabricWear: { value: new THREE.Vector2(cloth.sheen, cloth.twill) },
  };
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    if (!ANCHORS.every(a => shader.fragmentShader.includes(a)) || !shader.vertexShader.includes('#include <begin_vertex>')) return;
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = 'varying vec3 vChiFabricP;\nvarying vec3 vChiFabricN;\n'
      + shader.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>${VERTEX}`);
    shader.fragmentShader = DECLARE + shader.fragmentShader
      .replace('#include <color_fragment>', `#include <color_fragment>${COLOR}`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>${ROUGHNESS}`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>${NORMAL}`)
      .replace('#include <lights_fragment_end>', `#include <lights_fragment_end>${SHEEN}`);
  };
  material.customProgramCacheKey = () => `${priorKey}|${KEY}`;
  material.needsUpdate = true;
  return cloth;
}

/** Every plain garment under a loaded human. Returns the names of the materials clothed. */
export function clothHuman(root) {
  const names = new Set();
  root?.traverse(node => {
    if (!node.isMesh) return;
    for (const m of Array.isArray(node.material) ? node.material : [node.material]) if (patchFabric(m)) names.add(m.name);
  });
  return [...names];
}

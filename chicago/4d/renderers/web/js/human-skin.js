// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * Skin, hair and eyes for every portable human (T-3400).
 *
 * Kevin, 2026-11-06, of Hans on his brougham: "he looks too smooth and not
 * real ... set us on a path for all humans to look photographic realistic".
 * The exported skin is a MakeHuman colour map on a smooth body, the hair a
 * masked card cap with one round highlight, the eyes a matte white. 1904's
 * phone memory is at its ceiling, so, like fabric.js beside it, this adds NO
 * texture: a shader patch that reads each body's own bind pose, in metres.
 *
 * Skin:
 *  - pores and the fine criss-cross lines of the skin's surface, tipping the
 *    shading normal (no geometry changes); each fades by its screen-space
 *    rate before it can alias, so they show only up close;
 *  - colour that is not one surface: blotches of blood under the skin pushed
 *    toward red, others toward a browner tone, a few percent each;
 *  - an uneven sheen: some places a little oilier, pores matte;
 *  - light that goes INTO skin: the diffuse is lit from a smoothed normal
 *    (red most of all, so pores read in the highlight and not as grit), and a
 *    warm glow wraps a little past the terminator, the cheap form of
 *    subsurface scattering;
 *  - a faint grazing bloom: the fine hair on every face.
 * Hair: a Kajiya-Kay strand highlight in two lobes, a pale one and one tinted
 * by the hair's own colour, both stretched ACROSS the strands, which run from
 * the crown down and out; the cap's own round highlight is rubbed out.
 * Eyes: wet, so they catch the light; the sclera a little less paper-white.
 * T-3414: the iris and pupil take a domed cornea's normals (from each eye's
 * own disc), so the sun and sky make a small sharp highlight on them that
 * turns with the gaze; the white is shaded toward the corners the lids cover.
 *
 * Everything is a reconstructed rendering choice; no likeness of anyone's
 * skin, hair or eyes is claimed (liberty L418, its skin and hair supplement).
 *
 * Per-body differences are UNIFORMS, never code, so every body shares one skin
 * program and one hair program. The cache key names the chain beneath, as
 * confidence.js requires of a hook it chains beneath (and as fabric.js does).
 */
import * as THREE from 'three';

/** Strengths. Pores, lines and mottle are 0..1 multipliers; scatter the glow. */
export const SKIN = Object.freeze({ pores: 1, lines: 1, mottle: 1, scatter: 1, oil: .14, fuzz: .05, roughness: .55 });
export const HAIR = Object.freeze({ primary: .5, secondary: .45, shift: .12, roughness_floor: .82 });
export const EYES = Object.freeze({ roughness: .08, sclera_value: .78, cornea_roughness: .1, cornea_sky: 2.5, cornea_radius_m: .0078, corner_shade: .45 });

/** What a material of a portable human is, by the contract's slot names (HUMAN-ASSET-CONTRACT § 5). */
export function surfaceFor(material) {
  const name = material?.name ?? '';
  if (/^skin($|__)/.test(name)) return 'skin';
  if (/^hair($|__)/.test(name)) return 'hair';
  if (/^eyes($|__(sclera|iris|pupil)$)/.test(name)) return 'eyes';
  return null;
}

const KEY = { skin: 'chicago-skin-v1', hair: 'chicago-hair-v1', sclera: 'chicago-sclera-v1' };

// Shared: the bind pose in metres, and a small value noise.
const VERTEX_DECLARE = `
uniform mat4 chiSkinRest;
varying vec3 vChiSkinP;
varying vec3 vChiSkinN;
`;
const VERTEX = `
  vChiSkinP = ( chiSkinRest * vec4( position, 1.0 ) ).xyz;
  vChiSkinN = normalize( mat3( chiSkinRest ) * normal );`;
// Hair also carries the strand's direction, skinned with the body and into view space.
const HAIR_VERTEX_DECLARE = `
uniform vec3 chiHairCrown;
uniform mat3 chiSkinRestInv;
varying vec3 vChiHairT;
`;
const HAIR_VERTEX = `
  {
    vec3 d = vChiSkinP - chiHairCrown;
    // Out from the crown along the scalp, and falling: the way short hair lies.
    vec3 t = d - vChiSkinN * dot( d, vChiSkinN ) + vec3( 0.0, - 0.35 * length( d ), 0.0 );
    t -= vChiSkinN * dot( t, vChiSkinN );
    vec3 tObj = chiSkinRestInv * ( dot( t, t ) > 1e-10 ? t : vec3( 0.0, - 1.0, 0.0 ) );
    #ifdef USE_SKINNING
      tObj = ( skinMatrix * vec4( tObj, 0.0 ) ).xyz;
    #endif
    vChiHairT = ( modelViewMatrix * vec4( tObj, 0.0 ) ).xyz;
  }`;

const NOISE = `
varying vec3 vChiSkinP;
varying vec3 vChiSkinN;
float chiSkinHash( vec3 p ) {
  p = fract( p * 0.3183099 + vec3( 0.71, 0.113, 0.419 ) );
  p *= 17.0;
  return fract( p.x * p.y * p.z * ( p.x + p.y + p.z ) );
}
float chiSkinNoise( vec3 x ) {
  vec3 i = floor( x ), f = fract( x );
  f = f * f * ( 3.0 - 2.0 * f );
  return mix( mix( mix( chiSkinHash( i ), chiSkinHash( i + vec3( 1.0, 0.0, 0.0 ) ), f.x ),
                   mix( chiSkinHash( i + vec3( 0.0, 1.0, 0.0 ) ), chiSkinHash( i + vec3( 1.0, 1.0, 0.0 ) ), f.x ), f.y ),
              mix( mix( chiSkinHash( i + vec3( 0.0, 0.0, 1.0 ) ), chiSkinHash( i + vec3( 1.0, 0.0, 1.0 ) ), f.x ),
                   mix( chiSkinHash( i + vec3( 0.0, 1.0, 1.0 ) ), chiSkinHash( i + vec3( 1.0, 1.0, 1.0 ) ), f.x ), f.y ), f.z );
}
`;

const SKIN_DECLARE = `
uniform vec4 chiSkin;      // pores, lines, mottle, scatter
uniform vec3 chiSkinSheen; // oil, fuzz, roughness
${NOISE}
vec3 chiSkinN0 = vec3( 0.0, 0.0, 1.0 );
float chiSkinH = 0.0;
float chiSkinMatte = 0.0;
vec3 chiSkinPerturb( vec3 surfPos, vec3 surfNorm, vec2 dHdxy, float faceDir ) {
  vec3 sx = dFdx( surfPos ), sy = dFdy( surfPos );
  vec3 r1 = cross( sy, surfNorm ), r2 = cross( surfNorm, sx );
  float det = dot( sx, r1 ) * faceDir;
  vec3 grad = sign( det ) * ( dHdxy.x * r1 + dHdxy.y * r2 );
  return normalize( abs( det ) * surfNorm - grad );
}
`;
// After the colour map: blood and pigment blotches, and the relief the normal is tipped by.
const SKIN_COLOR = `
  {
    vec3 p = vChiSkinP;
    float pix = length( fwidth( p ) );   // metres per pixel here
    // Blotches a few centimetres to a few millimetres across.
    float blood = chiSkinNoise( p * 9.0 ) * 0.5 + chiSkinNoise( p * 27.0 + 3.1 ) * 0.33 + chiSkinNoise( p * 85.0 + 1.7 ) * 0.17 - 0.5;
    float tone = chiSkinNoise( p * 46.0 + 9.2 ) * 0.6 + chiSkinNoise( p * 140.0 + 4.4 ) * 0.4 - 0.5;
    // Small darker spots, sparse: moles and freckles at a millimetre or two.
    float spot = smoothstep( 0.80, 0.93, chiSkinNoise( p * 420.0 + 7.7 ) ) * clamp( 1.5 - pix * 420.0, 0.0, 1.0 );
    vec3 c = diffuseColor.rgb;
    c *= 1.0 + chiSkin.z * ( vec3( 0.10, -0.03, -0.05 ) * blood + vec3( -0.06, -0.08, -0.11 ) * tone );
    c *= 1.0 - chiSkin.z * spot * vec3( 0.10, 0.14, 0.17 );
    // Pores: pits about half a millimetre across, a fraction of that deep.
    float poreF = 1500.0;
    float poreFade = clamp( 1.4 - pix * poreF * 0.9, 0.0, 1.0 );
    float pore = smoothstep( 0.58, 0.86, chiSkinNoise( p * poreF ) ) * poreFade;
    // The skin's own lines: two families of shallow grooves a millimetre or so
    // apart, crossing, bent by a slow noise so they never read as a grid.
    float lineF = 700.0;
    float lineFade = clamp( 1.4 - pix * lineF * 0.9, 0.0, 1.0 );
    float bend = chiSkinNoise( p * 60.0 ) * 6.0;
    float l1 = 1.0 - abs( sin( dot( p, vec3( 0.80, 0.55, 0.25 ) ) * lineF + bend ) );
    float l2 = 1.0 - abs( sin( dot( p, vec3( -0.45, 0.75, 0.50 ) ) * lineF * 1.17 + bend * 1.3 ) );
    float lines = ( pow( l1, 6.0 ) + pow( l2, 6.0 ) ) * chiSkinNoise( p * 180.0 + 2.3 ) * lineFade;
    // A soft unevenness at a few millimetres that is visible from further away.
    float grain = ( chiSkinNoise( p * 260.0 + 5.5 ) - 0.5 ) * clamp( 1.4 - pix * 260.0 * 0.9, 0.0, 1.0 );
    c *= 1.0 - chiSkin.x * pore * 0.05 - chiSkin.y * lines * 0.03;
    diffuseColor.rgb = c;
    // Height, metres.
    chiSkinH = - chiSkin.x * pore * 0.000035 - chiSkin.y * lines * 0.00002 + grain * 0.00007;
    chiSkinMatte = pore;
  }`;
// Some places a little oilier (lower roughness); pores matte.
const SKIN_ROUGHNESS = `
  {
    float oil = smoothstep( 0.35, 0.8, chiSkinNoise( vChiSkinP * 14.0 + 11.3 ) );
    roughnessFactor = clamp( min( roughnessFactor, chiSkinSheen.z ) - chiSkinSheen.x * oil + chiSkinMatte * 0.1, 0.3, 1.0 );
  }`;
const SKIN_NORMAL = `
  chiSkinN0 = normal;
  normal = chiSkinPerturb( - vViewPosition, normal, vec2( dFdx( chiSkinH ), dFdy( chiSkinH ) ), faceDirection );`;
// Light into skin: per channel, part of the diffuse is lit from the smooth
// normal, and a warm glow wraps past the terminator. Specular keeps the relief.
const SKIN_LIGHT = `
void chiSkinDirect( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
  RE_Direct_Physical( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
  float nB = dot( geometryNormal, directLight.direction );
  float nS = dot( chiSkinN0, directLight.direction );
  vec3 soft = vec3( 0.6, 0.38, 0.25 ) * chiSkin.w;
  vec3 lit = mix( vec3( saturate( nB ) ), vec3( saturate( nS ) ), soft );
  float wrap = 0.35;
  vec3 glow = ( saturate( ( nS + wrap ) / ( 1.0 + wrap ) ) - saturate( nS ) ) * vec3( 0.24, 0.07, 0.035 ) * chiSkin.w;
  reflectedLight.directDiffuse += directLight.color * BRDF_Lambert( material.diffuseContribution ) * ( lit - saturate( nB ) + glow );
}
#undef RE_Direct
#define RE_Direct chiSkinDirect
`;
// The fine hair on a face: a little more light at grazing angles.
const SKIN_FUZZ = `
  {
    float chiRim = pow( 1.0 - clamp( abs( dot( normalize( vViewPosition ), chiSkinN0 ) ), 0.0, 1.0 ), 4.0 );
    reflectedLight.indirectDiffuse += diffuseColor.rgb * chiSkinSheen.y * chiRim * 3.0;
  }`;

const HAIR_DECLARE = `
uniform vec4 chiHair; // primary, secondary, shift, roughness floor
${NOISE}
varying vec3 vChiHairT;
vec3 chiHairTv = vec3( 0.0, 1.0, 0.0 );
vec3 chiHairTint = vec3( 0.0 );
`;
const HAIR_COLOR = `
  {
    // Strand to strand, a little lighter and darker: across the strands, never along them.
    chiHairTint = diffuseColor.rgb;
  }`;
const HAIR_ROUGHNESS = `
  roughnessFactor = max( roughnessFactor, chiHair.w );`;
const HAIR_NORMAL = `
  {
    vec3 t = vChiHairT;
    t -= normal * dot( t, normal );
    chiHairTv = dot( t, t ) > 1e-12 ? normalize( t ) : vec3( 0.0, 1.0, 0.0 );
  }`;
const HAIR_LIGHT = `
float chiHairLobe( vec3 T, vec3 H, float e ) {
  float th = dot( T, H );
  return pow( sqrt( max( 1.0 - th * th, 0.0 ) ), e );
}
void chiHairDirect( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
  RE_Direct_Physical( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
  vec3 H = normalize( directLight.direction + geometryViewDir );
  float nl = dot( geometryNormal, directLight.direction );
  float lit = smoothstep( -0.15, 0.35, nl );
  // The pale lobe sits toward the tip, the tinted one toward the root (Kajiya-Kay, Scheuermann).
  vec3 t1 = normalize( chiHairTv + geometryNormal * chiHair.z );
  vec3 t2 = normalize( chiHairTv - geometryNormal * chiHair.z * 1.5 );
  float jitter = 0.75 + 0.5 * chiSkinNoise( vChiSkinP * vec3( 900.0, 900.0, 900.0 ) );
  vec3 spec = vec3( 0.9, 0.86, 0.8 ) * chiHair.x * chiHairLobe( t1, H, 90.0 )
            + ( chiHairTint * 3.0 + 0.04 ) * chiHair.y * chiHairLobe( t2, H, 22.0 ) * jitter;
  // Dark hair reflects a few percent at its peak, and less toward the silhouette.
  float facing = 0.35 + 0.65 * saturate( abs( dot( geometryNormal, geometryViewDir ) ) );
  reflectedLight.directSpecular += directLight.color * spec * lit * facing * 0.08;
}
#undef RE_Direct
#define RE_Direct chiHairDirect
`;

const PHYSICAL = '#include <lights_physical_pars_fragment>';
const SIGNATURE = 'void RE_Direct_Physical( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight )';
const ANCHORS = ['#include <color_fragment>', '#include <roughnessmap_fragment>', '#include <normal_fragment_maps>', PHYSICAL];

/**
 * The matrix taking a mesh's own position attribute to its bind pose in
 * metres, relative to `root`. A quantised export's positions are not metres:
 * the dequantising scale is folded into the inverse bind matrices.
 */
export function restMatrix(mesh, root) {
  root.updateMatrixWorld(true);
  const toRoot = new THREE.Matrix4().copy(root.matrixWorld).invert();
  const bone = mesh.isSkinnedMesh ? mesh.skeleton?.bones?.[0] : null;
  if (!bone) return toRoot.multiply(mesh.matrixWorld);
  return toRoot.multiply(bone.matrixWorld).multiply(mesh.skeleton.boneInverses[0]).multiply(mesh.bindMatrix);
}

const patched = new WeakMap();

/** The pieces strand cards (human-hair.js) share with the hair cap: noise, the two lobes, the chain. */
export const STRAND_GLSL = Object.freeze({ VERTEX_DECLARE, VERTEX, HAIR_DECLARE, HAIR_COLOR, HAIR_ROUGHNESS, HAIR_NORMAL, HAIR_LIGHT, PHYSICAL });
export function chainPatch(material, key, uniforms, patch) { chain(material, key, uniforms, patch); }

function chain(material, key, uniforms, patch) {
  const prior = material.onBeforeCompile;
  const hadKey = Object.prototype.hasOwnProperty.call(material, 'customProgramCacheKey');
  const priorKey = hadKey ? String(material.customProgramCacheKey())
    : (typeof prior === 'function' && prior !== THREE.Material.prototype.onBeforeCompile ? prior.toString() : '');
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    if (!ANCHORS.every(a => shader.fragmentShader.includes(a)) || !shader.vertexShader.includes('#include <begin_vertex>')) return;
    if (!THREE.ShaderChunk.lights_physical_pars_fragment.includes(SIGNATURE)) return;
    Object.assign(shader.uniforms, uniforms);
    patch(shader);
  };
  material.customProgramCacheKey = () => `${priorKey}|${key}`;
  material.needsUpdate = true;
}

function patchSkin(material, rest) {
  const uniforms = {
    chiSkinRest: { value: rest.clone() },
    chiSkin: { value: new THREE.Vector4(SKIN.pores, SKIN.lines, SKIN.mottle, SKIN.scatter) },
    chiSkinSheen: { value: new THREE.Vector3(SKIN.oil, SKIN.fuzz, SKIN.roughness) },
  };
  chain(material, KEY.skin, uniforms, shader => {
    shader.vertexShader = VERTEX_DECLARE + shader.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>${VERTEX}`);
    shader.fragmentShader = SKIN_DECLARE + shader.fragmentShader
      .replace('#include <color_fragment>', `#include <color_fragment>${SKIN_COLOR}`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>${SKIN_ROUGHNESS}`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>${SKIN_NORMAL}`)
      .replace(PHYSICAL, `${PHYSICAL}${SKIN_LIGHT}`)
      .replace('#include <lights_fragment_end>', `#include <lights_fragment_end>${SKIN_FUZZ}`);
  });
  return uniforms;
}

function patchHair(material, rest, crown) {
  const uniforms = {
    chiSkinRest: { value: rest.clone() },
    chiSkinRestInv: { value: new THREE.Matrix3().setFromMatrix4(rest).invert() },
    chiHairCrown: { value: crown.clone() },
    chiHair: { value: new THREE.Vector4(HAIR.primary, HAIR.secondary, HAIR.shift, HAIR.roughness_floor) },
  };
  chain(material, KEY.hair, uniforms, shader => {
    shader.vertexShader = VERTEX_DECLARE + HAIR_VERTEX_DECLARE + shader.vertexShader
      .replace('#include <begin_vertex>', `#include <begin_vertex>${VERTEX}${HAIR_VERTEX}`);
    shader.fragmentShader = HAIR_DECLARE + shader.fragmentShader
      .replace('#include <color_fragment>', `#include <color_fragment>${HAIR_COLOR}`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>${HAIR_ROUGHNESS}`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>${HAIR_NORMAL}`)
      .replace(PHYSICAL, `${PHYSICAL}${HAIR_LIGHT}`);
  });
  return uniforms;
}

// The white of the eye, shaded where the lids and the corners cover it: by how far
// its bind-pose normal turns from the way the eye looks.
const SCLERA_DECLARE = `
uniform vec4 chiSclera; // forward (bind pose), shade
varying vec3 vChiSkinP;
varying vec3 vChiSkinN;
`;
const SCLERA_COLOR = `
  diffuseColor.rgb *= 1.0 - chiSclera.w * ( 1.0 - smoothstep( 0.2, 0.8, dot( normalize( vChiSkinN ), chiSclera.xyz ) ) );`;

function patchEyes(material, mesh, root) {
  const cornea = /__(iris|pupil)$/.test(material.name);
  material.roughness = Math.min(material.roughness, cornea ? EYES.cornea_roughness : EYES.roughness);
  // A wet cornea mirrors the bright sky over the dark iris: the catchlight of every portrait.
  if (cornea) material.envMapIntensity = EYES.cornea_sky;
  if (!/sclera/.test(material.name)) return null;
  material.color.multiplyScalar(EYES.sclera_value);
  const uniforms = {
    chiSkinRest: { value: restMatrix(mesh, root) },
    chiSclera: { value: new THREE.Vector4(...forwardOf(mesh, root).toArray(), EYES.corner_shade) },
  };
  chain(material, KEY.sclera, uniforms, shader => {
    shader.vertexShader = VERTEX_DECLARE + shader.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>${VERTEX}`);
    shader.fragmentShader = SCLERA_DECLARE + shader.fragmentShader.replace('#include <color_fragment>', `#include <color_fragment>${SCLERA_COLOR}`);
  });
  return uniforms;
}

/** The way a body faces in its bind pose: from its head bone out to its eyes (else +z). */
function forwardOf(mesh, root) {
  const bones = mesh.skeleton?.bones ?? [];
  const at = name => {
    const i = bones.findIndex(b => b.name === name);
    return i < 0 ? null : boneRest(mesh, root, i);
  };
  const head = at('head'), l = at('eye_l'), r = at('eye_r');
  if (!head || !l || !r) return new THREE.Vector3(0, 0, 1);
  const f = l.clone().add(r).multiplyScalar(.5).sub(head).setY(0);
  return f.lengthSq() > 1e-8 ? f.normalize() : new THREE.Vector3(0, 0, 1);
}

/** A bone's bind-pose position in metres, relative to `root`. */
export function boneRest(mesh, root, i) {
  root.updateMatrixWorld(true);
  const s = mesh.skeleton;
  return new THREE.Vector3().applyMatrix4(new THREE.Matrix4().copy(root.matrixWorld).invert()
    .multiply(s.bones[0].matrixWorld).multiply(s.boneInverses[0]).multiply(s.boneInverses[i].clone().invert()));
}

/**
 * A cornea over each eye's iris and pupil: their normals are turned to a dome's, centred
 * behind each eye's own disc, so a light makes one small sharp highlight on it rather than
 * a flat plate's. Once per geometry (a clone shares its export's; a varied face has its own).
 */
const domed = new WeakSet();
export function domeCornea(mesh, root) {
  const g = mesh.geometry, p = g?.attributes?.position, n = g?.attributes?.normal;
  if (!p || !n || domed.has(g)) return false;
  domed.add(g);
  const R = restMatrix(mesh, root), Rn = new THREE.Matrix3().getNormalMatrix(R), back = new THREE.Matrix3().setFromMatrix4(R).transpose();
  const v = new THREE.Vector3(), w = new THREE.Vector3();
  const eyes = [-1, 1].map(() => ({ c: new THREE.Vector3(), a: new THREE.Vector3(), k: 0 }));
  const side = new Uint8Array(p.count);
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).applyMatrix4(R);
    const e = eyes[side[i] = v.x >= 0 ? 1 : 0];
    e.c.add(v); e.a.add(w.fromBufferAttribute(n, i).applyMatrix3(Rn).normalize()); e.k++;
  }
  for (const e of eyes) if (e.k) { e.c.divideScalar(e.k); e.a.normalize(); e.c.addScaledVector(e.a, -EYES.cornea_radius_m); }
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).applyMatrix4(R).sub(eyes[side[i]].c).normalize();
    v.applyMatrix3(back).normalize();
    n.setXYZ(i, v.x, v.y, v.z);
  }
  n.needsUpdate = true;
  return true;
}

/** Where the hair grows from, in the rest pose's metres: the top of the cap, a little behind its middle. */
function crownOf(mesh, rest) {
  const box = new THREE.Box3();
  const p = mesh.geometry?.attributes?.position;
  if (!p) return new THREE.Vector3();
  const v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) box.expandByPoint(v.fromBufferAttribute(p, i).applyMatrix4(rest));
  const size = box.getSize(new THREE.Vector3());
  return new THREE.Vector3((box.min.x + box.max.x) / 2, box.max.y - size.y * .08, (box.min.z + box.max.z) / 2 - size.z * .12);
}

/**
 * Patch one human's skin, hair and eyes in place. Materials are shared by every
 * clone of one export, so each is patched once, by the first body that wears it.
 * Returns { material name: surface } for what this call or an earlier one dressed.
 */
export function dressSkin(root) {
  const dressed = {};
  if (!root) return dressed;
  const meshes = [];
  root.traverse(node => { if (node.isMesh) meshes.push(node); });
  for (const mesh of meshes) {
    for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      const surface = surfaceFor(m);
      if (!surface || !m?.isMeshStandardMaterial) continue;
      if (!patched.has(m)) {
        const rest = restMatrix(mesh, root);
        if (surface === 'skin') patched.set(m, patchSkin(m, rest));
        else if (surface === 'hair') patched.set(m, patchHair(m, rest, crownOf(mesh, rest)));
        else patched.set(m, patchEyes(m, mesh, root));
      }
      if (surface === 'eyes' && /__(iris|pupil)$/.test(m.name)) domeCornea(mesh, root);
      dressed[m.name] = surface;
    }
  }
  return dressed;
}

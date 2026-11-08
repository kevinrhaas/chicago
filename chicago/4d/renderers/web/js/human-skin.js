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
import { hairFor, HAIR_COLOURS } from './human-hair-styles.js';

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
uniform mat4 chiFace;      // rest metres -> the face's frame, centimetres (T-3493)
uniform vec4 chiFaceLook;  // age (0..1), brow shade, -, -
uniform vec4 chiFaceMarks; // subnasale y, mouth y, mouth half-width, nose wing x (cm)
uniform vec3 chiBrowTint;  // what the brow shade multiplies the skin by
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
    // T-3493: a face's age, in its folds and lines, and the shade of its brows, placed in the
    // face's own frame (centimetres from between the eyes; x out either side, y up, z forward).
    float ageH = 0.0;
    {
      vec3 q = ( chiFace * vec4( p, 1.0 ) ).xyz;
      float ax = abs( q.x ), y = q.y, A = chiFaceLook.x;
      float face = step( -1.5, q.z ) * step( abs( y ), 9.0 ) * step( ax, 7.0 );
      float cmPix = pix * 100.0;   // centimetres per pixel
      // The brow's shade: a soft band beneath its hairs, the brow arching to its tail.
      float bt = clamp( ( ax - 1.3 ) / 3.3, 0.0, 1.0 );
      float bMid = 1.72 - 0.55 * bt * bt, bHalf = 0.24 * sqrt( 1.0 - 0.7 * bt * bt );
      float brow = ( 1.0 - smoothstep( 0.45, 1.25, abs( y - bMid ) / bHalf ) ) * smoothstep( 1.05, 1.55, ax ) * ( 1.0 - smoothstep( 4.35, 4.95, ax ) );
      brow *= 0.75 + 0.5 * chiSkinNoise( p * 900.0 );
      c = mix( c, c * chiBrowTint, clamp( brow * chiFaceLook.y * face, 0.0, 1.0 ) );
      if ( A > 0.0 && face > 0.0 ) {
        float ys = chiFaceMarks.x, ym = chiFaceMarks.y, mw = chiFaceMarks.z, nx = chiFaceMarks.w;
        // The fold from the nose's wing round to beyond the mouth's corner, bowed out a little.
        float t = clamp( ( ys + 0.7 - y ) / ( ys + 0.7 - ( ym - 0.5 ) ), 0.0, 1.0 );
        float along = smoothstep( -0.02, 0.12, ( ys + 0.7 - y ) / ( ys + 0.7 - ( ym - 0.5 ) ) ) * ( 1.0 - smoothstep( 0.9, 1.15, ( ys + 0.7 - y ) / ( ys + 0.7 - ( ym - 0.5 ) ) ) );
        float d = ax - ( mix( nx + 0.2, mw + 0.6, t ) + 0.35 * sin( 3.14159 * t ) );
        float fold = exp( - d * d / 0.03 ) * along;
        float cheek = smoothstep( 0.05, 0.45, d ) * ( 1.0 - smoothstep( 0.5, 1.5, d ) ) * along;
        // From the mouth's corner down toward the jaw: the marionette line, fainter.
        float t2 = clamp( ( ym - 0.1 - y ) / 2.2, 0.0, 1.0 );
        float d2 = ax - ( mw + 0.15 + 0.35 * t2 );
        float mar = exp( - d2 * d2 / 0.025 ) * smoothstep( 0.0, 0.15, ( ym - 0.1 - y ) / 2.2 ) * ( 1.0 - smoothstep( 0.75, 1.0, t2 ) ) * smoothstep( 0.35, 0.8, A );
        // Under the eye: a crease below the lower lid, and the hollow above it.
        float ue = -1.2 - 0.3 * pow( ( ax - 3.0 ) / 1.4, 2.0 );
        float ux = smoothstep( 1.7, 2.3, ax ) * ( 1.0 - smoothstep( 3.9, 4.6, ax ) );
        float crease = exp( - pow( y - ue, 2.0 ) / 0.02 ) * ux;
        float hollow = smoothstep( ue - 0.1, ue + 0.25, y ) * ( 1.0 - smoothstep( -0.75, -0.5, y ) ) * ux;
        // Crow's feet: fine lines fanning out from the eye's outer corner.
        vec2 oc = vec2( ax - 4.25, y + 0.05 );
        float r = length( oc ), ang = atan( oc.y, oc.x );
        float fan = step( 0.0, oc.x ) * smoothstep( 0.25, 0.5, r ) * ( 1.0 - smoothstep( 1.0, 1.6, r ) ) * ( 1.0 - smoothstep( 0.7, 1.0, abs( ang ) ) );
        float crow = pow( abs( sin( ang * 7.0 + chiSkinNoise( p * 300.0 ) * 1.5 ) ), 14.0 ) * fan * clamp( 1.6 - cmPix / 0.05, 0.0, 1.0 );
        // The forehead: three long shallow lines, wavering.
        float wav = 0.12 * sin( ax * 1.4 + 1.3 ) + 0.06 * ( chiSkinNoise( p * 60.0 ) - 0.5 );
        float fy = y - 3.3 - wav;
        float fl = 0.0;
        for ( int k = 0; k < 3; k++ ) { float g = fy - float( k ) * 0.75; fl += exp( - g * g / 0.004 ); }
        fl *= smoothstep( 2.8, 3.2, y ) * ( 1.0 - smoothstep( 5.0, 5.6, y ) ) * ( 1.0 - smoothstep( 3.6, 4.6, ax ) ) * clamp( 1.6 - cmPix / 0.06, 0.0, 1.0 );
        // Colour: the folds and the hollow shade; older skin a little sallower and less even.
        // The upper lid's fold sinks under the brow: a shade between the lid and the brow.
        float lidFold = smoothstep( 0.45, 0.75, y ) * ( 1.0 - smoothstep( 1.0, 1.35, y ) ) * smoothstep( 1.7, 2.2, ax ) * ( 1.0 - smoothstep( 4.0, 4.6, ax ) );
        float bag = smoothstep( ue - 0.05, ue + 0.15, y ) * ( 1.0 - smoothstep( ue + 0.2, ue + 0.55, y ) ) * ux;
        c *= 1.0 - A * ( 0.3 * fold + 0.14 * mar + 0.22 * crease + 0.22 * hollow * vec3( 0.85, 1.15, 1.05 ) + 0.15 * lidFold + 0.1 * crow + 0.1 * fl );
        // Older skin: a little sallower, less rosy, less even.
        float lum = dot( c, vec3( 0.3, 0.59, 0.11 ) );
        c = mix( c, vec3( lum ), 0.3 * A );
        c = mix( c, c * vec3( 1.03, 0.97, 0.88 ), 0.6 * A );
        c *= 1.0 + A * 0.6 * ( vec3( 0.06, -0.02, -0.04 ) * blood + vec3( -0.05, -0.07, -0.1 ) * tone );
        // Height, metres: grooves, and the fullness of the cheek above the fold and under the eye.
        ageH = A * ( - 0.0009 * fold - 0.0005 * mar - 0.00045 * crease - 0.0001 * crow - 0.0001 * fl + 0.0015 * cheek + 0.0006 * bag );
      }
    }
    diffuseColor.rgb = c;
    // Height, metres.
    chiSkinH = - chiSkin.x * pore * 0.000035 - chiSkin.y * lines * 0.00002 + grain * 0.00007 + ageH;
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

function patchSkin(material, rest, look = NO_LOOK) {
  const uniforms = {
    chiSkinRest: { value: rest.clone() },
    chiSkin: { value: new THREE.Vector4(SKIN.pores, SKIN.lines, SKIN.mottle, SKIN.scatter) },
    chiSkinSheen: { value: new THREE.Vector3(SKIN.oil, SKIN.fuzz, SKIN.roughness) },
    chiFace: { value: look.face.clone() },
    chiFaceLook: { value: new THREE.Vector4(look.age, look.brow, 0, 0) },
    chiFaceMarks: { value: new THREE.Vector4(...look.marks) },
    chiBrowTint: { value: new THREE.Vector3(...look.tint) },
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

/** The face's frame in metres: origin between the eyes, x to the body's left, y up, z forward. */
export function headFrame(mesh, root) {
  const bones = mesh.skeleton?.bones ?? [];
  const at = name => { const i = bones.findIndex(b => b.name === name); return i < 0 ? null : boneRest(mesh, root, i); };
  const head = at('head'), l = at('eye_l'), r = at('eye_r');
  if (!head || !l || !r) return null;
  const o = l.clone().add(r).multiplyScalar(.5);
  const x = l.clone().sub(r).normalize(), y = new THREE.Vector3(0, 1, 0);
  y.addScaledVector(x, -x.dot(y)).normalize();
  const z = new THREE.Vector3().crossVectors(x, y);
  if (z.dot(o.clone().sub(head)) < 0) z.negate();
  return { o, x, y, z, head };
}

/**
 * The lids' edges (T-3493): the skin's open boundary round each eye, in the face's metric
 * bind pose (`face`: { P, index, count } as human-hair.js's metricSurface gives). Each edge
 * carries its two vertices and their points, its length, which eye (+1 the body's left, -1
 * its right), whether it is the upper lid's, and how far across the opening it lies (0 at the
 * inner corner, 1 at the outer). A seam's duplicate edge is kept once.
 */
export function lidEdges(face, f) {
  const I = face.index, n = face.count, uses = new Map();
  for (let t = 0; t < I.length; t += 3) for (let k = 0; k < 3; k++) {
    const a = I[t + k], b = I[t + (k + 1) % 3], key = a < b ? a * n + b : b * n + a;
    uses.set(key, (uses.get(key) ?? 0) + 1);
  }
  const v = new THREE.Vector3();
  const loc = i => { v.fromArray(face.P, 3 * i).sub(f.o); return [v.dot(f.x) * 100, v.dot(f.y) * 100, v.dot(f.z) * 100]; };
  const near = ([x, y, z]) => Math.abs(x) > .8 && Math.abs(x) < 5.5 && Math.abs(y) < 1.6 && z > -1.5;
  const sides = { 1: [], '-1': [] };
  for (const [key, c] of uses) {
    if (c !== 1) continue;
    const a = Math.floor(key / n), b = key % n, la = loc(a), lb = loc(b);
    if (!near(la) || !near(lb) || Math.sign(la[0]) !== Math.sign(lb[0])) continue;
    sides[Math.sign(la[0])].push({ a, b, la, lb });
  }
  const out = [];
  for (const [side, edges] of Object.entries(sides)) {
    if (edges.length < 6) continue;
    const pts = edges.flatMap(e => [e.la, e.lb]);
    const x0 = Math.min(...pts.map(q => Math.abs(q[0]))), x1 = Math.max(...pts.map(q => Math.abs(q[0])));
    // The line from corner to corner: above it the upper lid, below it the lower.
    const inner = pts.find(q => Math.abs(q[0]) === x0), outer = pts.find(q => Math.abs(q[0]) === x1);
    const chord = ax => inner[1] + (outer[1] - inner[1]) * (ax - x0) / Math.max(1e-6, x1 - x0);
    const seen = [];
    for (const e of edges) {
      const m = [(e.la[0] + e.lb[0]) / 2, (e.la[1] + e.lb[1]) / 2, (e.la[2] + e.lb[2]) / 2];
      if (seen.some(q => Math.hypot(q[0] - m[0], q[1] - m[1], q[2] - m[2]) < .01)) continue;
      seen.push(m);
      const pa = new THREE.Vector3().fromArray(face.P, 3 * e.a), pb = new THREE.Vector3().fromArray(face.P, 3 * e.b);
      out.push({ a: e.a, b: e.b, pa, pb, la: e.la, lb: e.lb, length: pa.distanceTo(pb), side: Number(side),
        upper: m[1] > chord(Math.abs(m[0])), across: (Math.abs(m[0]) - x0) / Math.max(1e-6, x1 - x0) });
    }
  }
  return out;
}

/**
 * How a blink shuts the eye (T-3493). The exported eyeBlink targets squash a box round each
 * eye flat to its centre's height, brow and cheek with it (tools/human_teamster_blend.py); a
 * face that blinked pinched its forehead down into its nose. Here the lids are turned about
 * the eye's own centre, so they slide over the eyeball as a lid does: the upper lid's edge
 * down to `meet` of the way from the lower lid's edge, the lower lid's up to the same line,
 * the skin above the upper edge following less and less to `upper_cm` above it, below the
 * lower to `lower_cm`, and nothing past `corner_cm` beyond either corner.
 */
export const BLINK = Object.freeze({ meet: .3, upper_cm: 1.1, lower_cm: .55, corner_cm: .45 });
const blinked = new WeakSet();
export function shapeBlink(mesh, root) {
  const g = mesh.geometry, dict = mesh.morphTargetDictionary, targets = g?.morphAttributes?.position;
  if (!dict || !targets?.length || !g.morphTargetsRelative || !g.attributes.position) return false;
  const sides = [['eyeBlinkLeft', 1], ['eyeBlinkRight', -1]].filter(([k]) => targets[dict[k]]);
  // Once per target: every clone of an export shares its targets (a varied face too).
  if (!sides.length || sides.every(([k]) => blinked.has(targets[dict[k]]))) return false;
  const f = headFrame(mesh, root);
  if (!f) return false;
  const pos = g.attributes.position, n = pos.count, R = restMatrix(mesh, root);
  const back = new THREE.Matrix3().setFromMatrix4(R).invert();
  // The targets' normal deltas turn with the lid too (the export's squashed every normal in
  // its box, and shaded the band round the eyes dark).
  const normals = g.morphAttributes.normal, nrm = g.attributes.normal;
  const Rn = new THREE.Matrix3().getNormalMatrix(R), backN = Rn.clone().invert(), w3 = new THREE.Vector3(), turn = new THREE.Quaternion();
  const P = new Float32Array(n * 3), L = new Float32Array(n * 3), v = new THREE.Vector3();
  for (let i = 0; i < n; i++) {
    v.fromBufferAttribute(pos, i).applyMatrix4(R); P.set([v.x, v.y, v.z], 3 * i);
    v.sub(f.o); L.set([v.dot(f.x) * 100, v.dot(f.y) * 100, v.dot(f.z) * 100], 3 * i);
  }
  const index = g.index ? g.index.array : Array.from({ length: n }, (_, i) => i);
  const edges = lidEdges({ P, index, count: n }, f);
  const bones = mesh.skeleton.bones, eye = name => {
    const c = boneRest(mesh, root, bones.findIndex(b => b.name === name)).sub(f.o);
    return [c.dot(f.x) * 100, c.dot(f.y) * 100, c.dot(f.z) * 100];
  };
  const smooth = (a, b, x) => { const t = Math.min(1, Math.max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t); };
  let shaped = false;
  for (const [name, side] of sides) {
    const attr = targets[dict[name]], nAttr = normals?.[dict[name]] ?? null;
    if (blinked.has(attr)) continue;
    const mine = edges.filter(e => e.side === side);
    const line = up => mine.filter(e => e.upper === up).flatMap(e => [e.la, e.lb]).map(q => [Math.abs(q[0]), q[1], q[2]]).sort((a, b) => a[0] - b[0]);
    const U = line(true), D = line(false);
    if (U.length < 4 || D.length < 4) continue;   // no opening found: leave the export's target
    const at = (pts, ax) => {
      if (ax <= pts[0][0]) return pts[0];
      for (let k = 1; k < pts.length; k++) if (ax <= pts[k][0]) {
        const t = (ax - pts[k - 1][0]) / Math.max(1e-6, pts[k][0] - pts[k - 1][0]);
        return [ax, pts[k - 1][1] + (pts[k][1] - pts[k - 1][1]) * t, pts[k - 1][2] + (pts[k][2] - pts[k - 1][2]) * t];
      }
      return pts[pts.length - 1];
    };
    const x0 = Math.min(U[0][0], D[0][0]), x1 = Math.max(U[U.length - 1][0], D[D.length - 1][0]);
    const c = eye(side > 0 ? 'eye_l' : 'eye_r');
    // The angle about the eye's centre, in the plane of up and forward.
    const angle = (y, z) => Math.atan2(y - c[1], z - c[2]);
    for (let i = 0; i < n; i++) {
      const x = L[3 * i], y = L[3 * i + 1], z = L[3 * i + 2], ax = Math.abs(x);
      let d = [0, 0, 0], th = 0;
      if (Math.sign(x) === side && ax > x0 - BLINK.corner_cm && ax < x1 + BLINK.corner_cm && z > c[2] - .2 && Math.abs(y - c[1]) < 2.5) {
        const u = at(U, ax), l = at(D, ax), meetY = l[1] + BLINK.meet * (u[1] - l[1]);
        const wc = 1 - smooth(0, BLINK.corner_cm, Math.max(x0 - ax, ax - x1, 0));
        const upper = y >= (u[1] + l[1]) / 2;
        const edge = upper ? u : l, h = upper ? y - u[1] : l[1] - y;
        const w = (1 - smooth(0, upper ? BLINK.upper_cm : BLINK.lower_cm, Math.max(0, h))) * wc;
        if (w > 0) {
          const r = Math.hypot(edge[1] - c[1], edge[2] - c[2]);
          const shut = Math.atan2(meetY - c[1], Math.sqrt(Math.max(0, r * r - (meetY - c[1]) ** 2))) - angle(edge[1], edge[2]);
          // Turned about the eye's centre by the edge's own turn, scaled down away from it.
          th = shut * w;
          const cs = Math.cos(th), sn = Math.sin(th), dy = y - c[1], dz = z - c[2];
          d = [0, dz * sn + dy * cs - dy, dz * cs - dy * sn - dz];
        }
      }
      v.copy(f.y).multiplyScalar(d[1] / 100).addScaledVector(f.z, d[2] / 100).applyMatrix3(back);
      attr.setXYZ(i, v.x, v.y, v.z);
      if (nAttr && nrm) {
        // The normal turned with its point, about the face's x (forward toward up by th).
        if (th) {
          w3.fromBufferAttribute(nrm, i).applyMatrix3(Rn).normalize();
          turn.setFromAxisAngle(f.x, -th);
          v.copy(w3).applyQuaternion(turn).applyMatrix3(backN).sub(w3.applyMatrix3(backN));
          nAttr.setXYZ(i, v.x, v.y, v.z);
        } else nAttr.setXYZ(i, 0, 0, 0);
      }
    }
    attr.needsUpdate = true;
    if (nAttr) nAttr.needsUpdate = true;
    blinked.add(attr);
    shaped = true;
  }
  return shaped;
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
 * A face's look (T-3493): how old it reads and how its brows are shaded. Kevin, 2026-11-07,
 * of Frances Glessner beside her 1892 photograph: "frances looks young to me compared to the
 * photo". The age lines start at 28 and are full at 75 (AGE); a person whose hair row grows
 * fine brows gets a soft shade of their brow colour beneath the hairs (BROW). Reconstructed
 * rendering choices, as every value here (liberty L418).
 */
export const AGE = Object.freeze({ from: 28, full: 75, lid_from: 40, lid_full: 75, lid_most: .3 });

/** How far an older face's upper lids rest shut (T-3493): none before 40, under a third by 75. */
export function restingLid(age) {
  if (!Number.isFinite(age)) return 0;
  return AGE.lid_most * Math.min(1, Math.max(0, (age - AGE.lid_from) / (AGE.lid_full - AGE.lid_from)));
}
export const BROW = Object.freeze({ shade: .8, pieces: Object.freeze(['brows_fine']) });
const NO_LOOK = Object.freeze({ age: 0, brow: 0, face: new THREE.Matrix4(), marks: [-4.5, -6.3, 2.5, 1.8], tint: [1, 1, 1], key: 'none' });

/** The midline's marks, in the face's frame (cm): the subnasale and the mouth's line. */
function midlineMarks(mesh, root, f) {
  const p = mesh.geometry?.attributes?.position;
  if (!p) return null;
  const R = restMatrix(mesh, root), v = new THREE.Vector3(), mid = [];
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).applyMatrix4(R).sub(f.o);
    const x = v.dot(f.x) * 100, y = v.dot(f.y) * 100, z = v.dot(f.z) * 100;
    if (Math.abs(x) < .35 && z > 0 && y < 0 && y > -13) mid.push([y, z]);
  }
  // The front profile in 2 mm steps: the foremost point at each height.
  const prof = [];
  for (let y = -.5; y > -13; y -= .2) { const b = mid.filter(q => q[0] <= y && q[0] > y - .2); if (b.length) prof.push([y - .1, Math.max(...b.map(q => q[1]))]); }
  const band = (lo, hi) => prof.filter(q => q[0] > lo && q[0] < hi);
  const most = (b, s) => b.reduce((a, q) => (a && s * a[1] >= s * q[1] ? a : q), null);
  const tip = most(band(-6, -1.5), 1);
  if (!tip) return null;
  const sub = most(band(tip[0] - 2.2, tip[0] - .4), -1), upper = sub && most(band(sub[0] - 1.6, sub[0] - .2), 1);
  const mouth = upper && most(band(upper[0] - 1.4, upper[0] - .15), -1);
  if (!sub || !mouth) return null;
  return [sub[0], mouth[0]];
}

function lookOf(mesh, root, { age = null, person = null, year = null } = {}) {
  const f = headFrame(mesh, root);
  if (!f) return NO_LOOK;
  const a = Number.isFinite(age) ? Math.min(1, Math.max(0, (age - AGE.from) / (AGE.full - AGE.from))) : 0;
  const style = person || year ? hairFor(person, year) : null;
  const fine = style?.facial?.some(k => BROW.pieces.includes(k));
  const hc = fine ? HAIR_COLOURS[style.brow_colour ?? style.colour] : null;
  // The shade takes the skin toward the brow's colour: a ratio, never darker than half.
  const tint = hc ? [0, 1, 2].map(k => Math.max(.5, Math.min(1, Math.sqrt(hc[k] / .25)))) : [1, 1, 1];
  const S = new THREE.Matrix4().makeScale(100, 100, 100), B = new THREE.Matrix4().makeBasis(f.x, f.y, f.z).transpose();
  const face = S.multiply(B).multiply(new THREE.Matrix4().makeTranslation(-f.o.x, -f.o.y, -f.o.z));
  const mid = midlineMarks(mesh, root, f) ?? NO_LOOK.marks.slice(0, 2);
  const marks = [mid[0], mid[1], 2.5, 1.8];
  const ageStep = Math.round(a * 20) / 20, brow = hc ? BROW.shade : 0;
  return { age: ageStep, brow, face, marks, tint,
    key: `${ageStep}|${brow}|${tint.map(t => t.toFixed(2))}|${f.o.toArray().map(t => Math.round(t * 500)).join(',')}` };
}

function setLook(uniforms, look) {
  uniforms.chiFace.value.copy(look.face);
  uniforms.chiFaceLook.value.set(look.age, look.brow, 0, 0);
  uniforms.chiFaceMarks.value.set(...look.marks);
  uniforms.chiBrowTint.value.set(...look.tint);
}

const pristine = new WeakMap(), looks = new WeakMap(), variants = new WeakMap();

/**
 * Patch one human's skin, hair and eyes in place. Materials are shared by every
 * clone of one export, so each is patched once, by the first body that wears it.
 * Returns { material name: surface } for what this call or an earlier one dressed.
 */
export function dressSkin(root, person = {}) {
  const dressed = {};
  if (!root) return dressed;
  const meshes = [];
  root.traverse(node => { if (node.isMesh) meshes.push(node); });
  for (const mesh of meshes) {
    for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      const surface = surfaceFor(m);
      if (!surface || !m?.isMeshStandardMaterial) continue;
      if (surface === 'skin' && mesh.isSkinnedMesh) {
        // A face's look is its skin material's uniforms (T-3493). Clones of one export share
        // its material: a wearer whose look differs takes a twin patched with its own.
        const look = lookOf(mesh, root, person);
        if (!patched.has(m)) {
          pristine.set(m, m.clone());
          patched.set(m, patchSkin(m, restMatrix(mesh, root), look));
          looks.set(m, look.key);
        } else if (looks.get(m) !== look.key) {
          const own = variants.get(m) ?? new Map();
          variants.set(m, own);
          let twin = own.get(look.key);
          if (!twin) {
            twin = (pristine.get(m) ?? m).clone();
            patched.set(twin, patchSkin(twin, restMatrix(mesh, root), look));
            looks.set(twin, look.key);
            own.set(look.key, twin);
          }
          if (!Array.isArray(mesh.material)) mesh.material = twin;
        }
        shapeBlink(mesh, root);
        dressed[m.name] = surface;
        continue;
      }
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

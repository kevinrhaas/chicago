// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * human-silver.js — the 1812 camp's trade silver, engraved (T-3553).
 *
 * Kevin, 2026-11-12, of a Potawatomi man's arm bands: "that silver band should have detail?
 * dont do that if it will blow things up". The bodies draw each arm band as a plain grey
 * loft and each brooch as a plain disc (tools/human_potawatomi_man_1812.py), which read as
 * white plastic rings. Trade silver of the Great Lakes presents was sheet silver, worked by
 * the silversmiths of Montreal and Detroit: arm bands bordered by engraved lines, with
 * wriggle-work (a zigzag cut by rocking a graver) and rows of punched dots between, and
 * brooches pierced or punched in rings (the annual presents Wau-Bun lists: "silver-works
 * (comprising arm-bands, bracelets, brooches; and ear-bobs)"). No surviving band of these
 * men is drawn; the motifs are the commonest of the type, reconstructed (liberty L418 and
 * the dress's), and no maker's mark, crest or figure is put on them.
 *
 * Like fabric.js and human-skin.js this adds NO texture and no geometry: one shader patch,
 * shared by every band and every brooch of every figure (the pattern per piece is a uniform),
 * drawing the cuts as a few tenths of a millimetre of relief that tips the shading normal,
 * dark tarnish in the grooves, and the polished metal between. Each cut fades by its
 * screen-space rate before it can alias, so at the distance most figures are seen it is
 * plain worn silver, as before. Memory: none beyond one program; it is safe on phones.
 */
import * as THREE from 'three';

/** Sizes in metres of the drawn pieces (the body's TAILORING) and of the cuts. */
export const SILVER = Object.freeze({
  band_width_m: .032, band_around_m: .36, // arm band: across its outer face, and round the arm
  pitch_m: .009,                          // one zig and zag of the wriggle-work
  dot_m: .0045,                           // punched dots, centre to centre
  brooch_radius_m: .011,
  colour: [.62, .62, .6], metalness: .8, roughness: .35,   // worn coin silver (the garrison's is .7/.7/.42)
});

const KEY = 'chicago-silver-v1';
const VERTEX = `
  vChiSilverUv = uv;`;
const DECLARE = `
uniform vec4 chiSilver;   // mode (0 band, 1 brooch), width or radius m, around m, pitch m
uniform float chiSilverDot;
varying vec2 vChiSilverUv;
vec3 chiSilverPerturb( vec3 surfPos, vec3 surfNorm, vec2 dHdxy, float faceDir ) {
  vec3 sx = dFdx( surfPos ), sy = dFdy( surfPos );
  vec3 r1 = cross( sy, surfNorm ), r2 = cross( surfNorm, sx );
  float det = dot( sx, r1 ) * faceDir;
  vec3 grad = sign( det ) * ( dHdxy.x * r1 + dHdxy.y * r2 );
  return normalize( abs( det ) * surfNorm - grad );
}
// A groove of half-width w (same units as d), anti-aliased by the rate r of d per pixel.
float chiSilverCut( float d, float w, float r ) { return 1.0 - smoothstep( w - r, w + r, abs( d ) ); }
`;
// The cuts, in millimetres on the piece's own face; cut = 1 in a groove.
const COLOR = `
  float chiSilverH = 0.0;
  float chiSilverCutAt = 0.0;
  {
    vec2 uv = vChiSilverUv;
    float cut = 0.0, fade = 1.0;
    if ( chiSilver.x < 0.5 ) {
      // The band: the loft's rows run inner edge, outer, outer, inner (v 0, 1/3, 2/3, 1), so
      // the outer face is v in [1/3, 2/3]; u runs once round the arm.
      float s = clamp( ( uv.y - 1.0 / 3.0 ) * 3.0, 0.0, 1.0 );
      vec2 mm = vec2( uv.x * chiSilver.z, s * chiSilver.y ) * 1000.0;
      float rate = max( length( fwidth( mm ) ), 1e-4 );
      fade = clamp( 2.0 - rate / 1.2, 0.0, 1.0 );
      float W = chiSilver.y * 1000.0, P = chiSilver.w * 1000.0;
      // Two engraved lines inside each edge.
      cut = max( chiSilverCut( mm.y - 0.11 * W, 0.35, rate ), chiSilverCut( mm.y - 0.89 * W, 0.35, rate ) );
      cut = max( cut, max( chiSilverCut( mm.y - 0.17 * W, 0.18, rate ), chiSilverCut( mm.y - 0.83 * W, 0.18, rate ) ) );
      // Wriggle-work down the middle: a zigzag, its cut a little wider at each turn.
      float tri = abs( fract( mm.x / P ) - 0.5 ) * 2.0;
      float zig = mm.y - ( 0.5 + 0.17 * ( tri * 2.0 - 1.0 ) ) * W;
      cut = max( cut, chiSilverCut( zig / sqrt( 1.0 + pow( 0.68 * W / P, 2.0 ) ), 0.4 + 0.12 * smoothstep( 0.8, 1.0, abs( tri * 2.0 - 1.0 ) ), rate ) );
      // A row of punched dots between the borders and the wriggle, either side.
      float D = chiSilverDot * 1000.0;
      vec2 c1 = vec2( ( fract( mm.x / D ) - 0.5 ) * D, mm.y - 0.255 * W );
      vec2 c2 = vec2( ( fract( mm.x / D + 0.5 ) - 0.5 ) * D, mm.y - 0.745 * W );
      cut = max( cut, max( chiSilverCut( length( c1 ), 0.55, rate ), chiSilverCut( length( c2 ), 0.55, rate ) ) );
      cut *= step( 1.0 / 3.0 - 0.01, uv.y ) * step( uv.y, 2.0 / 3.0 + 0.01 );
    } else {
      // A brooch: the disc's own uv, centre (0.5, 0.5), edge at radius 0.5.
      vec2 p = ( uv - 0.5 ) * 2.0 * chiSilver.y * 1000.0;
      float rate = max( length( fwidth( p ) ), 1e-4 );
      fade = clamp( 2.0 - rate / 1.2, 0.0, 1.0 );
      float R = chiSilver.y * 1000.0, r = length( p ), a = atan( p.y, p.x );
      cut = chiSilverCut( r - 0.82 * R, 0.22, rate );
      float n = 14.0, k = ( floor( a / 6.2831853 * n ) + 0.5 ) / n * 6.2831853;
      cut = max( cut, chiSilverCut( length( p - 0.6 * R * vec2( cos( k ), sin( k ) ) ), 0.38, rate ) );
      cut = max( cut, chiSilverCut( r - 0.3 * R, 0.2, rate ) );
    }
    cut *= fade;
    chiSilverCutAt = cut;
    // Tarnish lies in the cuts; the faces between are rubbed bright.
    diffuseColor.rgb *= 1.0 - 0.55 * cut;
    chiSilverH = - cut * 0.00025;
  }`;
const ROUGHNESS = `
  roughnessFactor = clamp( roughnessFactor + chiSilverCutAt * 0.35, 0.05, 1.0 );`;
const NORMAL = `
  normal = chiSilverPerturb( - vViewPosition, normal, vec2( dFdx( chiSilverH ), dFdy( chiSilverH ) ), faceDirection );`;
const ANCHORS = ['#include <color_fragment>', '#include <roughnessmap_fragment>', '#include <normal_fragment_maps>'];

const piece = (mesh, name) => new RegExp(`(^|_)${name}(_lod\\d+)?$`).test(mesh.name);

/** Patch one silver material in place for `mode` (0 band, 1 brooch). Safe to call twice. */
export function patchSilver(material, mode) {
  if (!material?.isMeshStandardMaterial || material.userData.chicagoSilver !== undefined) return false;
  material.userData.chicagoSilver = mode;
  material.color.setRGB(...SILVER.colour, THREE.LinearSRGBColorSpace);
  material.metalness = SILVER.metalness;
  material.roughness = SILVER.roughness;
  const prior = material.onBeforeCompile;
  const hadKey = Object.prototype.hasOwnProperty.call(material, 'customProgramCacheKey');
  const priorKey = hadKey ? String(material.customProgramCacheKey())
    : (typeof prior === 'function' && prior !== THREE.Material.prototype.onBeforeCompile ? prior.toString() : '');
  const uniforms = {
    chiSilver: { value: new THREE.Vector4(mode, mode ? SILVER.brooch_radius_m : SILVER.band_width_m, SILVER.band_around_m, SILVER.pitch_m) },
    chiSilverDot: { value: SILVER.dot_m },
  };
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    if (!ANCHORS.every((a) => shader.fragmentShader.includes(a)) || !shader.vertexShader.includes('#include <begin_vertex>')) return;
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = 'varying vec2 vChiSilverUv;\n' + shader.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>${VERTEX}`);
    shader.fragmentShader = DECLARE + shader.fragmentShader
      .replace('#include <color_fragment>', `#include <color_fragment>${COLOR}`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>${ROUGHNESS}`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>${NORMAL}`);
  };
  material.customProgramCacheKey = () => `${priorKey}|${KEY}`;
  material.needsUpdate = true;
  return true;
}

/**
 * Engrave the arm bands and brooches under a parsed body, once, before it is cloned: the
 * bands get their own clone of the shared silver material (the pattern differs by piece),
 * so every figure of the asset shares two materials and one program. Returns the pieces done.
 */
export function engraveSilver(root) {
  const done = [];
  if (!root) return done;
  const silver = [];
  root.traverse((o) => { if (o.isMesh && !Array.isArray(o.material) && /^accessory__silver/.test(o.material?.name ?? '')) silver.push(o); });
  // The bands' own material first, cloned from the shared one before either is patched.
  const bandOf = new Map();
  for (const o of silver) {
    if (!piece(o, 'silver_arm_bands') || o.material.userData.chicagoSilver !== undefined) continue;
    if (!bandOf.has(o.material)) { const m = o.material.clone(); m.name = o.material.name; bandOf.set(o.material, m); }
    o.material = bandOf.get(o.material);
  }
  for (const o of silver) {
    const mode = piece(o, 'silver_arm_bands') ? 0 : 1;
    patchSilver(o.material, mode);
    if (o.material.userData.chicagoSilver === mode) done.push(mode ? 'brooches' : 'arm_bands');
  }
  return done;
}

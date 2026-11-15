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
 * T-3553 (finery): the owner, 2026-11-14, of the Prairie Avenue ladies: *"when i see shows like
 * gilded age they are very fancy and lots of details and you don't have that ... give the women
 * some variation in their clothing appearance"*. A garment may also carry, in the same program:
 *
 *  - a woven or printed PATTERN: stripe, check, dot, sprig (a calico's small flower), damask
 *    (a tonal figure in the weave), plaid or pin stripe, in a second colour, run round the body
 *    so a skirt's stripes fall down its gores; faded to its mean colour before it can alias;
 *  - up to four TRIMS laid round the garment at a height: a ribbon or velvet band, a band of lace
 *    (openwork net and scalloped edge over a shadowed underlayer), soutache braid in scrolls,
 *    pin tucks, jet beading, a gathered flounce, embroidered sprays;
 *  - SILK (a smoother, shinier surface with more sheen) or VELVET (a dark face, a bright rim).
 *
 * The person's numbers are set by human-finery.js on their own material clone (`chiFinery` in
 * its userData) before it is patched. All zeros draw the plain cloth exactly as before.
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
  if (/deerskin|buckskin|leather/.test(name)) return null;   // hide has no weave (T-3466)
  if (/wool|stroud|broadcloth|coat|waistcoat|vest|jacket/.test(name)) return CLOTHS.wool;
  if (/linen|shirt/.test(name)) return CLOTHS.linen;
  return CLOTHS.cotton_twill;
}

const KEY = 'chicago-fabric-v2';
const VERTEX = `
  vChiFabricP = position;
  vChiFabricN = normal;`;
const DECLARE = `
uniform vec4 chiFabric;
uniform vec2 chiFabricWear;
uniform vec4 chiFin;          // garment's own y from, y to (bind units), units a metre, silk
uniform vec4 chiFinPat;       // pattern kind, repeat (bind units), contrast, velvet
uniform vec3 chiFinPatRgb;
uniform vec4 chiFinBand[ 4 ]; // centre y, half width (bind units), kind, a second number
uniform vec3 chiFinBandRgb[ 4 ];
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
// A box-filtered stripe of duty d across x (repeats), its width in repeats fw: 0..1 cover.
float chiFinStripe( float x, float d, float fw ) {
  float a = fract( x );
  float w = max( fw, 1e-4 );
  return clamp( smoothstep( d + w, d - w, a ) * smoothstep( -w, w, a ) + smoothstep( 1.0 - w, 1.0 + w, a ), 0.0, 1.0 );
}
// A small flower in a cell (repeats), at a seeded place and turn: its petals' cover.
float chiFinFlower( vec2 q, float petals, float size ) {
  vec2 c = floor( q ), f = fract( q ) - 0.5;
  float h = chiFabricHash( vec3( c, 3.7 ) ), k = chiFabricHash( vec3( c, 9.1 ) );
  f -= ( vec2( h, k ) - 0.5 ) * 0.35;
  float r = length( f ), a = atan( f.y, f.x ) + h * 6.2831853;
  float edge = size * ( 0.62 + 0.38 * abs( cos( a * petals * 0.5 ) ) );
  float flower = smoothstep( edge + 0.03, edge - 0.03, r );
  float eye = smoothstep( size * 0.3, size * 0.18, r );
  return clamp( flower - eye * 0.6, 0.0, 1.0 );
}
// A tonal figure on a cell: a four-lobed medallion and its ring, mirrored as a damask's is.
float chiFinDamask( vec2 q ) {
  vec2 f = abs( fract( q ) - 0.5 );
  vec2 g = abs( fract( q + 0.5 ) - 0.5 );
  float r = length( f ), a = atan( f.y, f.x );
  float lobe = smoothstep( 0.3, 0.26, r / ( 0.55 + 0.45 * abs( cos( a * 2.0 ) ) ) );
  float ring = smoothstep( 0.03, 0.0, abs( r - 0.4 ) ) * 0.6;
  float leaf = smoothstep( 0.17, 0.13, length( g * vec2( 1.0, 1.9 ) ) );
  return clamp( lobe + ring + leaf, 0.0, 1.0 );
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
  }
  float chiFinGloss = 0.0;
  {
    // T-3553: a pattern and trims, in the garment's own bind-pose units (human-finery.js).
    vec3 p = vChiFabricP;
    vec3 an = abs( normalize( vChiFabricN ) );
    float upm = max( chiFin.z, 1e-3 );
    // Round the body: arc length about its upright axis, so stripes fall down a skirt's gores.
    float rad = max( length( p.xz ), 0.05 * upm );
    vec2 ru = vec2( atan( p.x, p.z ) * rad, p.y );
    if ( an.y > 0.75 ) ru = p.xz;
    vec3 base = diffuseColor.rgb;
    float kind = chiFinPat.x;
    if ( kind > 0.5 ) {
      vec2 q = ru / max( chiFinPat.y, 1e-4 );
      float fw = max( fwidth( q.x ), fwidth( q.y ) );
      float fade = clamp( 1.6 - fw * 3.0, 0.0, 1.0 );
      float cover = 0.0, mean = 0.0;
      if ( kind < 1.5 ) { cover = chiFinStripe( q.x, 0.5, fw ); mean = 0.5; }
      else if ( kind < 2.5 ) { float a = chiFinStripe( q.x, 0.5, fw ), b = chiFinStripe( q.y, 0.5, fw ); cover = ( a + b ) * 0.5; mean = 0.5; }
      else if ( kind < 3.5 ) { cover = smoothstep( 0.22, 0.17, length( fract( q + vec2( 0.5 * floor( q.y ), 0.0 ) ) - 0.5 ) ); mean = 0.13; }
      else if ( kind < 4.5 ) { cover = max( chiFinFlower( q, 5.0, 0.2 ), 0.7 * chiFinFlower( q * 1.0 + 0.5, 3.0, 0.11 ) ); mean = 0.16; }
      else if ( kind < 5.5 ) { cover = chiFinDamask( q ); mean = 0.3; }
      else if ( kind < 6.5 ) {
        float a = chiFinStripe( q.x, 0.34, fw ) + 0.6 * chiFinStripe( q.x * 4.0 + 0.3, 0.2, fw * 4.0 );
        float b = chiFinStripe( q.y, 0.34, fw ) + 0.6 * chiFinStripe( q.y * 4.0 + 0.3, 0.2, fw * 4.0 );
        cover = clamp( ( a + b ) * 0.5, 0.0, 1.0 ); mean = 0.45;
      }
      else { cover = chiFinStripe( q.x, 0.12, fw ); mean = 0.12; }
      cover = mix( mean, cover, fade ) * chiFinPat.z;
      // A damask is the cloth's own colour, figured by its weave: lighter, and glossier.
      if ( kind > 4.5 && kind < 5.5 ) { diffuseColor.rgb = mix( base, chiFinPatRgb, cover ); chiFinGloss += cover * 0.35; }
      else diffuseColor.rgb = mix( base, chiFinPatRgb, cover );
    }
    for ( int i = 0; i < 4; i ++ ) {
      vec4 b = chiFinBand[ i ];
      if ( b.z < 0.5 || b.y <= 0.0 ) continue;
      // The kind, and which way the trim runs (kind + 16 x axis): 0 round the garment at a
      // height; 1 the same but on the body only, not the sleeves (the bind pose holds the arms
      // out, so a yoke at shoulder height would otherwise run down them); 2 round a sleeve at
      // its end, a cuff, by the distance out from the body.
      float axis = floor( b.z / 16.0 );
      float bk = b.z - axis * 16.0;
      float d = ( ( axis > 1.5 ? abs( p.x ) : p.y ) - b.x ) / b.y;   // -1 at its foot, +1 at its head
      if ( axis > 1.5 ) d = -d;                    // a cuff's foot is the sleeve's end
      float across = ( axis > 1.5 ? ( p.y + p.z ) * 2.4 : ru.x ) / max( b.y, 1e-4 );
      float fwB = fwidth( d );
      float fadeB = clamp( 1.4 - fwidth( across ) * 1.2, 0.0, 1.0 );
      // A lace band's and a flounce's foot is scalloped.
      float foot = -1.0;
      if ( ( bk > 1.5 && bk < 2.5 ) || ( bk > 5.5 && bk < 6.5 ) ) foot = -1.0 + 0.28 * abs( sin( across * 1.3 ) ) * fadeB;
      float inside = smoothstep( foot - fwB, foot + fwB, d ) * smoothstep( 1.0 + fwB, 1.0 - fwB, d );
      if ( axis > 0.5 && axis < 1.5 ) { float cut = 0.17 * upm, fx = fwidth( p.x ); inside *= smoothstep( cut + fx, cut - fx, abs( p.x ) ); }
      if ( inside <= 0.0 ) continue;
      vec3 col = chiFinBandRgb[ i ];
      vec3 c = col;
      if ( bk < 1.5 ) {
        // Ribbon or velvet: its colour, a fine darker line at each edge.
        c *= 1.0 - 0.3 * smoothstep( 0.8, 1.0, abs( d ) );
      } else if ( bk < 2.5 ) {
        // Lace: a net of threads with flowers in it, over the shadow of what lies beneath.
        // In metres, so a lace's net is fine and its flowers a few centimetres, at any width.
        vec2 lq = vec2( ( axis > 1.5 ? ( p.y + p.z ) : ru.x ), axis > 1.5 ? abs( p.x ) : p.y ) / upm * 100.0;
        float net = 1.0 - smoothstep( 0.04, 0.11, min( abs( fract( lq.x + lq.y ) - 0.5 ), abs( fract( lq.x - lq.y ) - 0.5 ) ) );
        float motif = max( chiFinFlower( lq * 0.3 + 0.25, 6.0, 0.36 ), chiFinFlower( lq * 0.3 + vec2( 0.75, 0.75 ), 5.0, 0.2 ) );
        float fadeL = clamp( 1.5 - max( fwidth( lq.x ), fwidth( lq.y ) ) * 1.5, 0.0, 1.0 );
        float thread = clamp( max( net * 0.6, motif ), 0.0, 1.0 );
        thread = mix( 0.62, thread, fadeL );
        c = mix( mix( base, col, 0.55 ) * 0.55, col, thread );
        chiFabricH += thread * 0.0004;
      } else if ( bk < 3.5 ) {
        // Soutache braid: a cord in scrolls between two straight cords.
        float wave = d - 0.55 * sin( across * 2.2 ) * cos( across * 0.55 );
        float cord = smoothstep( 0.2, 0.08, abs( wave ) ) + smoothstep( 0.16, 0.06, abs( abs( d ) - 0.88 ) );
        cord = mix( 0.3, clamp( cord, 0.0, 1.0 ), fadeB );
        c = mix( base, col, cord );
        chiFabricH += cord * 0.0006;
        chiFinGloss += cord * 0.25;
      } else if ( bk < 4.5 ) {
        // Pin tucks: folds of the cloth itself, each a bright crest and a shadow under it.
        float t = fract( d * max( b.w, 2.0 ) * 0.5 );
        float crest = smoothstep( 0.35, 0.5, t ) * smoothstep( 0.65, 0.5, t );
        float shade = smoothstep( 0.55, 0.75, t ) * smoothstep( 0.95, 0.75, t );
        float tw = clamp( 1.2 - fwB * max( b.w, 2.0 ) * 2.0, 0.0, 1.0 );
        c = mix( base, col, 0.35 ) * ( 1.0 + ( crest * 0.22 - shade * 0.18 ) * tw );
        chiFabricH += crest * 0.0008 * tw;
      } else if ( bk < 5.5 ) {
        // Jet: rows of small black glass beads, each with its glint.
        vec2 bq = vec2( across * 2.4, d * 2.0 );
        float bead = smoothstep( 0.38, 0.24, length( fract( bq + vec2( 0.5 * floor( bq.y ), 0.0 ) ) - 0.5 ) );
        bead = mix( 0.45, bead, fadeB );
        c = mix( base * 0.6, col, bead );
        chiFinGloss += bead * 0.85;
        chiFabricH += bead * 0.0008;
      } else if ( bk < 6.5 ) {
        // A gathered flounce: the cloth in soft vertical folds, lighter at the crests.
        float g = sin( across * 3.1 + sin( across * 0.7 ) );
        c = col * ( 1.0 + 0.16 * g * fadeB ) * ( 1.0 - 0.15 * smoothstep( 0.7, 1.0, d ) );
        chiFabricH += g * 0.0025 * fadeB;
      } else {
        // Embroidered sprays: flowers worked in the band's colour on the cloth.
        float spray = chiFinFlower( vec2( across * 0.8, d * 0.9 + 0.5 ), 5.0, 0.26 );
        spray = mix( 0.15, spray, fadeB );
        c = mix( base, col, spray );
        chiFabricH += spray * 0.0005;
      }
      diffuseColor.rgb = mix( diffuseColor.rgb, c, inside );
    }
    // Velvet: a dark face and a bright rim (the rim in the sheen below).
    diffuseColor.rgb *= 1.0 - 0.22 * chiFinPat.w;
  }`;
const ROUGHNESS = `
  roughnessFactor = clamp( roughnessFactor - chiFabricGloss * 0.12, 0.35, 1.0 );
  roughnessFactor = clamp( roughnessFactor * ( 1.0 - 0.45 * chiFin.w ) - chiFinGloss * 0.3, 0.16, 1.0 );`;
const NORMAL = `
  normal = chiFabricPerturb( - vViewPosition, normal, vec2( dFdx( chiFabricH ), dFdy( chiFabricH ) ), faceDirection );`;
// A cloth's sheen: fibres catch light at grazing angles, a little, from the sky.
const SHEEN = `
  {
    float chiRim = pow( 1.0 - clamp( abs( dot( normalize( vViewPosition ), normal ) ), 0.0, 1.0 ), 3.0 );
    float chiShe = chiFabricWear.x + chiFin.w * 0.35 + chiFinPat.w * 0.9;
    reflectedLight.indirectDiffuse += diffuseColor.rgb * chiShe * chiRim * 2.0;
    reflectedLight.directDiffuse *= 1.0 + chiShe * chiRim;
  }`;
const ANCHORS = ['#include <color_fragment>', '#include <roughnessmap_fragment>',
  '#include <normal_fragment_maps>', '#include <lights_fragment_end>'];

/**
 * T-3553: the finery uniforms of one material, from the numbers human-finery.js put in its
 * userData (`chiFinery`: fin, pat, patRgb, bands[4], bandRgb[4]); all zeros where it has none.
 */
export function fineryUniforms(f = null) {
  const v4 = (a) => new THREE.Vector4(...(Array.isArray(a) && a.length === 4 ? a : [0, 0, 0, 0]));
  const v3 = (a) => new THREE.Vector3(...(Array.isArray(a) && a.length === 3 ? a : [0, 0, 0]));
  return {
    chiFin: { value: v4(f?.fin) },
    chiFinPat: { value: v4(f?.pat) },
    chiFinPatRgb: { value: v3(f?.patRgb) },
    chiFinBand: { value: [0, 1, 2, 3].map((i) => v4(f?.bands?.[i])) },
    chiFinBandRgb: { value: [0, 1, 2, 3].map((i) => v3(f?.bandRgb?.[i])) },
  };
}

const patched = new WeakSet();
/** A reviewed portable wool map supplies only thread weave and dye heather.
 * Keep the existing common macro wear, rumple and sheen. Ordinary materials,
 * recolors keep their inherited normal map; clearing the color map restores
 * common dye heather, while the inherited portable normal still owns the weave.
 */
export function portableCoatThreads(material) {
  const marker = material?.userData?.chicago4d_cloth_microtexture;
  return material?.name === 'garment_outer__livery_coat_green_1904'
    && marker?.version === 1 && marker.profile === 'wool'
    && marker.source_material === material.name
    && marker.runtime_weave === 'portable_maps_with_common_macro'
    && marker.license === 'CC0-1.0' && marker.historical_texture === false
    && Boolean(material.normalMap && material.roughnessMap);
}
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
    chiFabric: { value: new THREE.Vector4(cloth.pitch_m,
      portableCoatThreads(material) ? 0 : cloth.weave,
      portableCoatThreads(material) && material.map ? 0 : cloth.heather, cloth.rumple * .01) },
    chiFabricWear: { value: new THREE.Vector2(cloth.sheen, cloth.twill) },
    ...fineryUniforms(material.userData?.chiFinery),
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

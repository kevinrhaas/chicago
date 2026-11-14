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
 * T-3553: the one texture this file does read is a person's own skin sheet, where a
 * person has one (two stand-ins, William and Sarah Grey: tools/bake_likeness_skin.py lays
 * the owner's pictures of each stand-in on the face fitted to them). It is fetched when
 * that person is first drawn, never at boot, and is still a uniform: the program is shared.
 * Where that person's hair stands out of the skin, the near levels' skin is drawn in finer
 * triangles (human-fine.js), so a top knot or a curl has vertices of its own.
 *
 * Per-body differences are UNIFORMS, never code, so every body shares one skin
 * program and one hair program. The cache key names the chain beneath, as
 * confidence.js requires of a hook it chains beneath (and as fabric.js does).
 */
import * as THREE from 'three';
import { hairFor, HAIR_COLOURS } from './human-hair-styles.js';
import { setLidRest } from './human-variation.js';
import { fineCells, fineOf } from './human-fine.js';
import { teethStrip, teethOf, createMouth, drawnTeeth, drawnLook, TEETH_DRAWN } from './human-mouth.js';

/** Strengths. Pores, lines and mottle are 0..1 multipliers; scatter the glow. */
export const SKIN = Object.freeze({ pores: 1, lines: 1, mottle: 1, scatter: 1, oil: .14, fuzz: .05, roughness: .55, lip_tone: .6 });
export const HAIR = Object.freeze({ primary: .5, secondary: .45, shift: .12, roughness_floor: .82 });
export const EYES = Object.freeze({ roughness: .08, sclera_value: .78, cornea_roughness: .1, cornea_sky: 2.5, cornea_radius_m: .0078, corner_shade: .45, like_sky: .6 });

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
// T-3553: a person's own skin sheet also says how far their hair (and a beard) stands out from
// the fitted skin. The skin's own vertices are moved out that far, away from the head's upright
// middle line (from the middle between the ears' tops, the record's `axis_m` down: the crown's
// hair rises, the sides' and the back's stands straight out, a beard and the nape's out and
// down; the sheet's mask, red: a share of the record's reach), so the pictures' hair has the
// pictures' outline, as the bake measured it. The bind-pose position the fragment's pores and lines are
// placed by stays the bare skin's. The rest frame's own x and y, as they stand in view, go to
// the fragment: the grown surface's facing is kept on the sheet in that frame.
// The shade inside a mouth that opens (T-3553), everyone's. The inside of the mouth has an
// island of its own on the body's map (hm08: every body shares the layout): the rectangle
// u0..u1 from v0 up, less the corner the left hand's island reaches into (left of `hand_u`
// below `hand_v`: the tip of its middle finger, which lies below 0.881 there and, left of
// 0.751, up to 0.905; the mouth's island begins at u 0.758 and, left of `hand_u`, lies above
// 0.898). It keeps `dark` of its light back (the body's map paints it a lit salmon). A pictured strip of teeth behind the lips lies in the same shade
// while the mouth is shut (the lips of a face at rest do not seal, and a light line showed
// between them) and takes the light as the face moves into its smile, all of it by `lit_by`
// of the smile.
export const MOUTH_SHADE = Object.freeze({ u0: 0.7545, u1: 0.93, v0: 0.86, hand_u: 0.764, hand_v: 0.889, dark: 0.85, lit_by: 0.25 });
// Drawn teeth (T-3553), for everyone with no picture of their own: human-mouth.js stands two
// short rows of points behind a person's lips, and their place on the body's map lies outside
// it and says which row, how far across it and from gum to biting edge, and which set and
// tone (TEETH_DRAWN). They are drawn here from that place alone, with no picture.
//   upper, lower  where one tooth ends and the next begins from the row's middle out, as shares
//                 of half the row (an upper row's two incisors, canine and first premolar; a lower
//                 row's are narrower, and one more shows); a set makes them `size` larger or smaller a step
//   long          how far toward the row's edge each tooth reaches (the side incisors are shorter),
//                 `uneven` more or less by the set, its corners rounded off by `round`
//   gap, gum      the dark line between two teeth (a share of half the row), and where the gum ends
//   ivory, stain  the teeth's colour (linear) and what each tone multiplies it by; `gums` theirs
//   lit           how much light they keep in the mouth: at the row's middle and at its ends
//   under         ...and by the gum, under the lip, against the biting edge
//   gloss, shine  their roughness (wet enamel), and how much of the sky's and the sun's glint they keep in the mouth
//   dark          the mouth's dark past a tooth's edge and between two teeth
export const DRAWN_TEETH = Object.freeze({ upper: Object.freeze([0.33, 0.59, 0.88, 1.16]), lower: Object.freeze([0.2, 0.42, 0.7, 0.98]), size: 0.04,
  long: Object.freeze([1, 0.9, 0.97, 0.88, 0.84]), uneven: 0.05, round: 0.1, gap: 0.02, gum: Object.freeze([0.08, 0.16]),
  ivory: Object.freeze([0.8, 0.72, 0.56]), stain: Object.freeze([0.96, 0.92, 0.84]), gums: Object.freeze([0.42, 0.16, 0.15]),
  lit: Object.freeze([0.55, 0.25]), under: 0.7, gloss: 0.4, shine: 0.25, dark: Object.freeze([0.06, 0.03, 0.027]) });
const glsl = x => (Number.isInteger(x) ? x.toFixed(1) : String(x));   // a number as GLSL writes a float
// T-3553: a person's front picture, shown from the front. Their sheet gives each texel one
// colour, and hair that stands beside a face is seen from the front and from the side: the two
// pictures show different things there (the locks' fronts; the hair swept back over the ear),
// so the sheet, which takes the side pictures', drew the hair beside the face pale and streaked
// to someone in front of it. The front picture is kept as a picture too
// (tools/bake_likeness_skin.py front_layer), with where it is to be shown beside it, and laid
// on the skin by where each place stands. It is all of what the skin shows there for an eye
// within `full` of the line the picture was taken along (cosines), none of it past `from`, and
// only on what faces the picture (by `faces` of the grown surface's facing). `inset`: how far
// in from the picture's edge it is read (a share of it), so its neighbour on the file is not:
// two texels of the small blocks beside the picture, so one on a phone's half-size copy and
// half of one a level of the file further down, and still inside the margin the bake leaves
// round the head (about 0.02).
// It is laid on by where a place stands, not by what the camera saw, so it also says what it
// shows at each place, hair or skin, and is shown only on the same: where the two differ by
// `kind` it starts to give way, and by `other` it is not shown (hair that stands behind an ear
// took the ear's skin, pale scraps in the hair to someone a little to one side).
export const FRONT_VIEW = Object.freeze({ from: 0.72, full: 0.94, faces: 0.3, inset: 0.016, kind: 0.25, other: 0.75 });
// T-3553: hair that stands out is lit as the shape it stands in, and the underside of a beard
// (or of hair that hangs over a collar) faces the ground: lit as a ceiling it stood as a dark
// band under the jaw, which no picture of a beard shows (light goes into hair from its sides,
// and the picture laid on it already carries its shade). Where the grown surface of hair faces
// down by more than `from` (the down part of its facing), it is lit as its side is: the way
// straight out from the head's middle line, tipped down by `down`; all of it by `full`.
export const HAIR_UNDER = Object.freeze({ from: 0.25, full: 0.75, down: 0.2 });
const LIKE_VERTEX_DECLARE = `
uniform sampler2D chiLike;
uniform vec4 chiLikeUv[ 3 ];
uniform vec4 chiLikeMap[ 3 ];
uniform vec4 chiLikeMask;
uniform vec4 chiLikeGrow;
uniform vec4 chiLikeHat;
uniform float chiLikeAxis;
uniform mat3 chiLikeBack;
uniform vec4 chiLikeFrontU;
uniform vec4 chiLikeFrontV;
varying vec3 vChiLikeX;
varying vec3 vChiLikeY;
varying vec2 vChiLikeFront;
varying float vChiSmile;
`;
const LIKE_VERTEX = `
  vChiLikeX = vec3( 1.0, 0.0, 0.0 );
  vChiLikeY = vec3( 0.0, 1.0, 0.0 );
  // How far a face with a smile has moved into it: human-variation.js appends the smile after
  // the body's own shapes, so it is the last. Read only where the face has teeth to show.
  vChiSmile = 0.0;
  #ifdef USE_MORPHTARGETS
    vChiSmile = morphTargetInfluences[ MORPHTARGETS_COUNT - 1 ];
  #endif
  // Where the grown surface stands, bind pose (m): the skin's own place, moved out with the hair.
  vec3 chiGrown = vChiSkinP;
  #ifdef USE_MAP
  if ( chiLikeGrow.w > 0.0 ) {
    vec2 st = vec2( 0.0 );
    float on = 0.0;
    for ( int k = 0; k < 3; k++ ) {
      vec4 r = chiLikeUv[ k ];
      float inside = step( r.x, vMapUv.x ) * step( vMapUv.x, r.z ) * step( r.y, vMapUv.y ) * step( vMapUv.y, r.w );
      st = mix( st, vMapUv * chiLikeMap[ k ].xy + chiLikeMap[ k ].zw, inside );
      on = max( on, inside );
    }
    float stand = on * textureLod( chiLike, chiLikeMask.xy + st * chiLikeMask.z, 0.0 ).r * chiLikeGrow.w;
    // Under a worn hat the hair lies flat: above its band, no further out than the hat allows.
    stand = min( stand, mix( 1.0, chiLikeHat.y, smoothstep( chiLikeHat.x - 0.02, chiLikeHat.x, vChiSkinP.y ) ) );
    vec3 from = chiLikeGrow.xyz;
    from.y = clamp( vChiSkinP.y, from.y - chiLikeAxis, from.y );
    vec3 away = vChiSkinP - from;
    away *= stand / max( length( away ), 1e-5 );
    chiGrown += away;
    transformed += chiLikeBack * away;
    vec3 ax = chiLikeBack * vec3( 1.0, 0.0, 0.0 ), ay = chiLikeBack * vec3( 0.0, 1.0, 0.0 );
    #ifdef USE_SKINNING
      ax = ( skinMatrix * vec4( ax, 0.0 ) ).xyz;
      ay = ( skinMatrix * vec4( ay, 0.0 ) ).xyz;
    #endif
    vChiLikeX = normalize( ( modelViewMatrix * vec4( ax, 0.0 ) ).xyz );
    vChiLikeY = normalize( ( modelViewMatrix * vec4( ay, 0.0 ) ).xyz );
  }
  #endif
  // ...and where that place lies on the person's front picture (FRONT_VIEW): across and down.
  vChiLikeFront = vec2( dot( chiLikeFrontU.xyz, chiGrown ) + chiLikeFrontU.w, dot( chiLikeFrontV.xyz, chiGrown ) + chiLikeFrontV.w );`;
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
uniform sampler2D chiLike;      // a person's own skin sheet (T-3553), or nothing
uniform vec4 chiLikeUv[ 3 ];    // the rects of the body's map the sheet covers (u0, v0, u1, v1)
uniform vec4 chiLikeMap[ 3 ];   // each rect's place on the sheet: uv * xy + zw
uniform vec4 chiLikeMask;       // the coverage mask's corner on the sheet (xy), its scale, and 1 where a sheet is worn
uniform vec4 chiLikeTint;       // what the body's map is multiplied by beside the sheet; the sheet's gain
uniform vec4 chiLikeGrow;       // the middle of the head the hair stands out from (bind pose, m), and the most it stands (m; 0: none)
uniform vec4 chiLikeHat;        // a worn hat's band (bind-pose height, m), the most hair stands under it, the facing block's corner on the sheet
uniform vec4 chiLikeTeeth;      // the teeth's patch on the body's map (u0, v0, u1, v1) where the sheet's wearer has teeth to show (human-mouth.js); empty otherwise
uniform sampler2D chiLikeFront; // the person's front picture, as a picture (FRONT_VIEW), or nothing
uniform vec4 chiLikeFrontAt[ 3 ]; // on it: the picture's own rectangle, the one that says where it is shown, and the one that says where it shows hair (x, y, w, h as shares)
uniform vec4 chiLikeFrontTo;    // toward where the picture was taken from (bind pose), and 1 where the person has one
varying vec2 vChiLikeFront;     // where this place lies on that picture
varying float vChiSmile;        // how far the face has moved into its smile
varying vec3 vChiLikeX;
varying vec3 vChiLikeY;
float chiLikeHair = 0.0;        // where the sheet shows hair and not skin
float chiLikeStand = 0.0;       // how far the hair stands out here, m
vec3 chiLikeN = vec3( 0.0 );    // which way the grown surface faces, bind pose
${NOISE}
vec3 chiSkinN0 = vec3( 0.0, 0.0, 1.0 );
float chiSkinH = 0.0;
float chiSkinMatte = 0.0;
float chiSkinLip = 0.0;
float chiSkinCrease = 0.0;
float chiSkinTooth = 0.0;     // 1 on a drawn tooth (T-3553): wet
float chiSkinIn = 0.0;        // 1 inside the mouth (its own island, and a drawn tooth): no pores, no blood's glow
uniform float chiSkinLipTone; // how far a lip turns to the skin's hue (T-3553)
// A drawn row of teeth (DRAWN_TEETH): the colour this far across the row (0..1) and this far
// along a tooth from its gum (0) to its biting edge (1), of the upper row or the lower, in one
// of the sets and tones. Past a tooth's edge and between two teeth it is the mouth's dark.
vec3 chiDrawnTeeth( float across, float along, float lower, float set, float tone ) {
  float x = abs( across * 2.0 - 1.0 );
  vec4 e = mix( vec4( ${DRAWN_TEETH.upper.map(glsl).join(', ')} ), vec4( ${DRAWN_TEETH.lower.map(glsl).join(', ')} ), lower ) * ( 1.0 + ${glsl(DRAWN_TEETH.size)} * ( mod( set, 4.0 ) - 1.5 ) );
  float i = step( e.x, x ) + step( e.y, x ) + step( e.z, x ) + step( e.w, x );   // which tooth from the middle
  float from = i < 0.5 ? 0.0 : i < 1.5 ? e.x : i < 2.5 ? e.y : i < 3.5 ? e.z : e.w;
  float to = i < 0.5 ? e.x : i < 1.5 ? e.y : i < 2.5 ? e.z : i < 3.5 ? e.w : e.w + 0.3;
  float f = ( x - from ) / ( to - from ), side = min( f, 1.0 - f ) * ( to - from );
  float longs = i < 0.5 ? ${glsl(DRAWN_TEETH.long[0])} : i < 1.5 ? ${glsl(DRAWN_TEETH.long[1])} : i < 2.5 ? ${glsl(DRAWN_TEETH.long[2])} : i < 3.5 ? ${glsl(DRAWN_TEETH.long[3])} : ${glsl(DRAWN_TEETH.long[4])};
  longs += ${glsl(DRAWN_TEETH.uneven)} * ( fract( sin( ( i + 1.0 ) * 12.9898 + set * 78.233 + lower * 37.719 ) * 43758.5453 ) - 0.5 );
  longs -= ${glsl(DRAWN_TEETH.round)} * ( 1.0 - smoothstep( 0.0, 0.3, min( f, 1.0 - f ) ) );
  float tooth = ( 1.0 - smoothstep( longs - 0.03, longs, along ) ) * smoothstep( 0.0, ${glsl(DRAWN_TEETH.gap)}, side );
  vec3 ivory = vec3( ${DRAWN_TEETH.ivory.map(glsl).join(', ')} ) * pow( vec3( ${DRAWN_TEETH.stain.map(glsl).join(', ')} ), vec3( tone ) );
  vec3 c = mix( vec3( ${DRAWN_TEETH.gums.map(glsl).join(', ')} ), ivory, smoothstep( ${glsl(DRAWN_TEETH.gum[0])}, ${glsl(DRAWN_TEETH.gum[1])}, along ) );
  c *= mix( ${glsl(DRAWN_TEETH.lit[0])}, ${glsl(DRAWN_TEETH.lit[1])}, x * x ) * mix( ${glsl(DRAWN_TEETH.under)}, 1.0, along );
  return mix( vec3( ${DRAWN_TEETH.dark.map(glsl).join(', ')} ), c, tooth );
}
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
    // Lips (Kevin, 2026-11-12: "when the sun is behind people their lips have a pink line too
    // much"): the shared MakeHuman maps paint the lips a saturated pink, far redder than the
    // skin round them (green over red 0.17 against the skin's 0.43, linear). Found by that
    // ratio in the map's own colour (the complexion's tint divided out), and turned partway to
    // the skin's own hue at the lip's own value, so a lip stays a little rosier and darker
    // than the face but no longer reads as a painted pink line where it catches the sky.
    {
      vec3 tex = c / max( diffuse, vec3( 1e-3 ) );
      chiSkinLip = smoothstep( 0.30, 0.55, 1.0 - tex.g / max( tex.r, 1e-3 ) / 0.43 );
      vec3 skinHue = vec3( 1.0, 0.435, 0.19 ) * diffuse;
      vec3 lw = vec3( 0.3, 0.59, 0.11 );
      c = mix( c, skinHue * ( dot( c, lw ) / max( dot( skinHue, lw ), 1e-4 ) ), chiSkinLip * chiSkinLipTone );
    }
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
      // Its bounds fade over a couple of centimetres (T-3553: a long chin, Sarah Grey's, met the
      // old hard edge 9 cm below the eyes as a straight line across it, sallow above, rosy below).
      float face = smoothstep( -2.0, -1.0, q.z ) * ( 1.0 - smoothstep( 8.0, 11.0, abs( y ) ) ) * ( 1.0 - smoothstep( 6.5, 8.0, ax ) );
      float cmPix = pix * 100.0;   // centimetres per pixel
      // The lips' parting (T-3553): the top of the lower lip faces the sky, and nothing here
      // knows the upper lip hangs over it, so with the sun behind a person (the face lit by
      // the sky alone) it was the brightest thing on the face, a thin pink line. Lips in a
      // band about the mouth's line whose surface turns up are taken as in the crease's shade.
      vec3 fn = mat3( chiFace ) * cross( dFdx( p ), dFdy( p ) );
      float up = fn.y / max( length( fn ), 1e-12 );
      chiSkinCrease = chiSkinLip * face * ( 1.0 - smoothstep( 0.12, 0.4, abs( y - chiFaceMarks.y ) ) ) * smoothstep( 0.3, 0.75, up );
      // The brow's shade: a soft band beneath its hairs, the brow arching to its tail.
      float bt = clamp( ( ax - 1.3 ) / 3.3, 0.0, 1.0 );
      float bMid = 1.72 - 0.55 * bt * bt, bHalf = 0.24 * sqrt( 1.0 - 0.7 * bt * bt );
      float brow = ( 1.0 - smoothstep( 0.45, 1.25, abs( y - bMid ) / bHalf ) ) * smoothstep( 1.05, 1.55, ax ) * ( 1.0 - smoothstep( 4.35, 4.95, ax ) );
      brow *= 0.75 + 0.5 * chiSkinNoise( p * 900.0 );
      c = mix( c, c * chiBrowTint, clamp( brow * chiFaceLook.y * face, 0.0, 1.0 ) );
      if ( A > 0.0 && face > 0.0 ) {
        vec3 c0 = c;   // the age is laid on as far as the face goes, fading at its bounds
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
        ageH = face * A * ( - 0.0009 * fold - 0.0005 * mar - 0.00045 * crease - 0.0001 * crow - 0.0001 * fl + 0.0015 * cheek + 0.0006 * bag );
        c = mix( c0, c, face );
      }
    }
    // T-3553: a person's own skin, from pictures of them. Where the sheet's mask covers, the
    // pictures are the colour (their own brows, lips, lines and hair roots; this face's drawn
    // age lines and brow shade give way to them); the rest of the body takes the pictures' tone.
    #ifdef USE_MAP
    if ( chiLikeMask.w > 0.5 ) {
      vec2 st = vec2( 0.0 );
      float on = 0.0;
      for ( int k = 0; k < 3; k++ ) {
        vec4 r = chiLikeUv[ k ];
        float inside = step( r.x, vMapUv.x ) * step( vMapUv.x, r.z ) * step( r.y, vMapUv.y ) * step( vMapUv.y, r.w );
        st = mix( st, vMapUv * chiLikeMap[ k ].xy + chiLikeMap[ k ].zw, inside );
        on = max( on, inside );
      }
      vec4 mask = texture2D( chiLike, chiLikeMask.xy + st * chiLikeMask.z );
      float a = on * mask.g;
      vec3 like = texture2D( chiLike, st ).rgb * chiLikeTint.w;
      vec3 facing = texture2D( chiLike, chiLikeHat.zw + st * chiLikeMask.z ).rgb * 2.0 - 1.0;
      // Seen from in front, the front picture itself where the sheet took another picture (the
      // hair beside a face, the ears): FRONT_VIEW. Laid on by where each place stands, on what
      // faces the picture, fading out as the eye leaves the line the picture was taken along.
      if ( chiLikeFrontTo.w > 0.5 ) {
        vec3 gx = normalize( vChiLikeX ), gy = normalize( vChiLikeY );
        vec3 to = gx * chiLikeFrontTo.x + gy * chiLikeFrontTo.y + cross( gx, gy ) * chiLikeFrontTo.z;
        float shown = smoothstep( ${FRONT_VIEW.from}, ${FRONT_VIEW.full}, dot( normalize( vViewPosition ), to ) )
          * smoothstep( 0.0, ${FRONT_VIEW.faces}, dot( facing, chiLikeFrontTo.xyz ) );
        vec2 q = clamp( vChiLikeFront, ${FRONT_VIEW.inset}, 1.0 - ${FRONT_VIEW.inset} );
        shown *= texture2D( chiLikeFront, chiLikeFrontAt[ 1 ].xy + q * chiLikeFrontAt[ 1 ].zw ).g;
        // ...its hair on hair and its skin on skin: hair that stands behind an ear is not the ear.
        shown *= 1.0 - smoothstep( ${FRONT_VIEW.kind}, ${FRONT_VIEW.other}, abs( texture2D( chiLikeFront, chiLikeFrontAt[ 2 ].xy + q * chiLikeFrontAt[ 2 ].zw ).g - mask.b ) );
        like = mix( like, texture2D( chiLikeFront, chiLikeFrontAt[ 0 ].xy + q * chiLikeFrontAt[ 0 ].zw ).rgb * chiLikeTint.w, shown );
      }
      c = mix( c / max( diffuse, vec3( 1e-3 ) ) * chiLikeTint.rgb, like, a );
      // The pictured teeth of a face that has them lie in the lips' shade until the lips part
      // (MOUTH_SHADE; the inner mouth's own shade is everyone's, below).
      float teeth = step( chiLikeTeeth.x, vMapUv.x ) * step( vMapUv.x, chiLikeTeeth.z ) * step( chiLikeTeeth.y, vMapUv.y ) * step( vMapUv.y, chiLikeTeeth.w );
      c *= 1.0 - ${MOUTH_SHADE.dark} * teeth * ( 1.0 - smoothstep( 0.0, ${MOUTH_SHADE.lit_by}, vChiSmile ) );
      ageH *= 1.0 - a;
      // Hair in the pictures is hair: no pores, no oil, no light through it, and where it
      // stands out from the skin it is lit as the shape it stands in.
      chiLikeHair = a * mask.b;
      chiLikeStand = a * mask.r * chiLikeGrow.w;
      chiLikeN = facing;
    }
    // T-3553: everyone's mouth. Its inside, seen between parted lips, lies in their shade
    // (MOUTH_SHADE: its island only); and the drawn teeth of a person with no picture of
    // theirs, whose place on the map lies outside it (TEETH_DRAWN), are drawn from that place.
    {
      float bag = step( ${MOUTH_SHADE.u0}, vMapUv.x ) * step( vMapUv.x, ${MOUTH_SHADE.u1} ) * step( ${MOUTH_SHADE.v0}, vMapUv.y )
        * max( step( ${MOUTH_SHADE.hand_u}, vMapUv.x ), step( ${MOUTH_SHADE.hand_v}, vMapUv.y ) );
      c *= 1.0 - ${MOUTH_SHADE.dark} * bag;
      chiSkinIn = bag;
      pore *= 1.0 - bag; lines *= 1.0 - bag; grain *= 1.0 - bag; ageH *= 1.0 - bag;
      if ( vMapUv.x > ${glsl(TEETH_DRAWN.u0 - 0.5)} ) {
        float su = vMapUv.x - ${glsl(TEETH_DRAWN.u0)}, set = floor( ( su + 1e-4 ) / ${glsl(TEETH_DRAWN.set_u)} );
        float sv = vMapUv.y - ${glsl(TEETH_DRAWN.v0)}, tone = floor( sv / ${glsl(TEETH_DRAWN.tone_v)} ), row = sv - ${glsl(TEETH_DRAWN.tone_v)} * tone, lower = step( ${glsl(TEETH_DRAWN.row_v)}, row );
        c = chiDrawnTeeth( clamp( su - ${glsl(TEETH_DRAWN.set_u)} * set, 0.0, 1.0 ), clamp( ( row - ${glsl(TEETH_DRAWN.row_v)} * lower - ${glsl(TEETH_DRAWN.pad)} ) / ${glsl(1 - 2 * TEETH_DRAWN.pad)}, 0.0, 1.0 ), lower, set, tone );
        chiSkinTooth = 1.0; chiSkinIn = 1.0;
        chiSkinLip = 0.0; chiSkinCrease = 0.0; ageH = 0.0; pore = 0.0; lines = 0.0; grain = 0.0;
      }
    }
    #endif
    diffuseColor.rgb = c;
    // Height, metres.
    chiSkinH = ( - chiSkin.x * pore * 0.000035 - chiSkin.y * lines * 0.00002 + grain * 0.00007 ) * ( 1.0 - chiLikeHair ) + ageH;
    chiSkinMatte = pore * ( 1.0 - chiLikeHair );
  }`;
// Some places a little oilier (lower roughness); pores matte.
const SKIN_ROUGHNESS = `
  {
    float oil = smoothstep( 0.35, 0.8, chiSkinNoise( vChiSkinP * 14.0 + 11.3 ) );
    roughnessFactor = clamp( min( roughnessFactor, chiSkinSheen.z ) - chiSkinSheen.x * oil * ( 1.0 - chiLikeHair ) + chiSkinMatte * 0.1 + chiSkinLip * 0.15, 0.3, 1.0 );
    roughnessFactor = mix( roughnessFactor, max( roughnessFactor, 0.8 ), chiLikeHair );
    roughnessFactor = mix( roughnessFactor, ${glsl(DRAWN_TEETH.gloss)}, chiSkinTooth );
  }`;
const SKIN_NORMAL = `
  chiSkinN0 = normal;
  normal = chiSkinPerturb( - vViewPosition, normal, vec2( dFdx( chiSkinH ), dFdy( chiSkinH ) ), faceDirection );
  if ( chiLikeStand > 0.0 ) {
    vec3 gx = normalize( vChiLikeX ), gy = normalize( vChiLikeY );
    // The underside of hair is lit as its side is: HAIR_UNDER.
    vec2 out2 = vChiSkinP.xz - chiLikeGrow.xz;
    vec3 side = vec3( out2.x, 0.0, out2.y ) / max( length( out2 ), 1e-4 ) + vec3( 0.0, - ${HAIR_UNDER.down}, 0.0 );
    vec3 n = mix( chiLikeN, normalize( side ), chiLikeHair * smoothstep( ${HAIR_UNDER.from}, ${HAIR_UNDER.full}, - chiLikeN.y ) );
    vec3 grown = normalize( gx * n.x + gy * n.y + cross( gx, gy ) * n.z );
    #ifdef DOUBLE_SIDED
      grown *= faceDirection;
    #endif
    float stands = smoothstep( 0.0005, 0.003, chiLikeStand );
    normal = normalize( mix( normal, grown, stands ) );
    chiSkinN0 = normalize( mix( chiSkinN0, grown, stands ) );
  }`;
// Light into skin: per channel, part of the diffuse is lit from the smooth
// normal, and a warm glow wraps past the terminator. Specular keeps the relief.
const SKIN_LIGHT = `
void chiSkinDirect( const in IncidentLight directLight, const in vec3 geometryPosition, const in vec3 geometryNormal, const in vec3 geometryViewDir, const in vec3 geometryClearcoatNormal, const in PhysicalMaterial material, inout ReflectedLight reflectedLight ) {
  RE_Direct_Physical( directLight, geometryPosition, geometryNormal, geometryViewDir, geometryClearcoatNormal, material, reflectedLight );
  float nB = dot( geometryNormal, directLight.direction );
  float nS = dot( chiSkinN0, directLight.direction );
  vec3 soft = vec3( 0.6, 0.38, 0.25 ) * chiSkin.w * ( 1.0 - chiLikeHair ) * ( 1.0 - chiSkinIn );
  vec3 lit = mix( vec3( saturate( nB ) ), vec3( saturate( nS ) ), soft );
  float wrap = 0.35;
  vec3 glow = ( saturate( ( nS + wrap ) / ( 1.0 + wrap ) ) - saturate( nS ) ) * vec3( 0.24, 0.07, 0.035 ) * chiSkin.w * ( 1.0 - chiLikeHair ) * ( 1.0 - chiSkinIn );
  reflectedLight.directDiffuse += directLight.color * BRDF_Lambert( material.diffuseContribution ) * ( lit - saturate( nB ) + glow );
}
#undef RE_Direct
#define RE_Direct chiSkinDirect
`;
// The fine hair on a face: a little more light at grazing angles.
const SKIN_FUZZ = `
  {
    float chiRim = pow( 1.0 - clamp( abs( dot( normalize( vViewPosition ), chiSkinN0 ) ), 0.0, 1.0 ), 4.0 );
    reflectedLight.indirectDiffuse += diffuseColor.rgb * chiSkinSheen.y * chiRim * 3.0 * ( 1.0 - chiSkinIn );
    // The inside of the mouth (T-3553) is in the lips' and the cheeks' shade: no sky is mirrored
    // in it and no sun glints there, but a little on a wet tooth.
    float inMouth = chiSkinIn * ( 1.0 - ${glsl(DRAWN_TEETH.shine)} * chiSkinTooth );
    reflectedLight.indirectSpecular *= 1.0 - inMouth;
    reflectedLight.directSpecular *= 1.0 - inMouth;
    // The lips' parting in the upper lip's shade (T-3553).
    float shade = 1.0 - 0.7 * chiSkinCrease;
    reflectedLight.indirectDiffuse *= shade;
    reflectedLight.indirectSpecular *= shade;
    reflectedLight.directDiffuse *= 1.0 - 0.4 * chiSkinCrease;
    reflectedLight.directSpecular *= 1.0 - 0.6 * chiSkinCrease;
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
    chiSkinLipTone: { value: SKIN.lip_tone },
    chiFace: { value: look.face.clone() },
    chiFaceLook: { value: new THREE.Vector4(look.age, look.brow, 0, 0) },
    chiFaceMarks: { value: new THREE.Vector4(...look.marks) },
    chiBrowTint: { value: new THREE.Vector3(...look.tint) },
    chiLike: { value: null },
    chiLikeUv: { value: [0, 1, 2].map(() => new THREE.Vector4()) },
    chiLikeMap: { value: [0, 1, 2].map(() => new THREE.Vector4()) },
    chiLikeMask: { value: new THREE.Vector4() },
    chiLikeTint: { value: new THREE.Vector4(1, 1, 1, 1) },
    chiLikeGrow: { value: new THREE.Vector4() },
    chiLikeHat: { value: new THREE.Vector4(NO_HAT, LIKENESS.under_hat_m, 0, 0) },
    chiLikeAxis: { value: 0 },
    chiLikeTeeth: { value: new THREE.Vector4(2, 2, -1, -1) },
    chiLikeBack: { value: new THREE.Matrix3().setFromMatrix4(rest).invert() },
    chiLikeFront: { value: null },
    chiLikeFrontU: { value: new THREE.Vector4() },
    chiLikeFrontV: { value: new THREE.Vector4() },
    chiLikeFrontAt: { value: [0, 1, 2].map(() => new THREE.Vector4()) },
    chiLikeFrontTo: { value: new THREE.Vector4() },
  };
  setLikeness(uniforms, look.like);
  chain(material, KEY.skin, uniforms, shader => {
    shader.vertexShader = VERTEX_DECLARE + LIKE_VERTEX_DECLARE + shader.vertexShader.replace('#include <begin_vertex>', `#include <begin_vertex>${VERTEX}${LIKE_VERTEX}`);
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
 * T-3553: a face that wears its own skin sheet rests its lids as its front picture shows them
 * (`lid`, 0..1 of a blink, measured by tools/bake_likeness_skin.py). The owner, 2026-11-13,
 * asked for both Greys "photographic matched"; the fitted faces' eyes stood about 4 mm wider
 * open than their pictures'. So that much of the blink's own shape (shapeBlink, above) goes
 * into the face's rest shape, less what its age already rests them (restingLid), and the
 * face's own blink targets carry only what is left, so a full blink still shuts the eye and
 * no further. Returns the blink targets to add, how much of each, and the morph targets for
 * this face's geometry; null where the body has no blink (a far level) or nothing to rest.
 */
export function restedBlink(mesh, root, lid, age) {
  const g = mesh.geometry, dict = mesh.morphTargetDictionary, targets = g?.morphAttributes?.position;
  if (!(lid > 0) || !dict || !targets?.length || !g.morphTargetsRelative) return null;
  const aged = restingLid(age), rest = Math.min(.9, (lid - aged) / (1 - aged));
  if (!(rest > 0)) return null;
  shapeBlink(mesh, root);
  const ids = ['eyeBlinkLeft', 'eyeBlinkRight'].map(k => dict[k]).filter(i => targets[i]);
  if (!ids.length) return null;
  const less = list => list?.map((t, i) => {
    if (!ids.includes(i) || !t) return t;
    const a = new Float32Array(t.count * t.itemSize);
    for (let j = 0; j < t.count; j++) for (let c = 0; c < t.itemSize; c++) a[j * t.itemSize + c] = t.getComponent(j, c) * (1 - rest);
    const out = Object.assign(new THREE.BufferAttribute(a, t.itemSize), { name: t.name });
    blinked.add(out);   // shaped already: these are the shaped targets, part of the way
    return out;
  });
  return { rest, targets: ids.map(i => targets[i]),
    morphAttributes: { ...g.morphAttributes, position: less(g.morphAttributes.position), ...(g.morphAttributes.normal ? { normal: less(g.morphAttributes.normal) } : {}) } };
}
setLidRest(restedBlink);   // human-variation.js builds each face's rest shape, and asks here for its lids'

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
const NO_LOOK = Object.freeze({ age: 0, brow: 0, face: new THREE.Matrix4(), marks: [-4.5, -6.3, 2.5, 1.8], tint: [1, 1, 1], like: null, key: 'none' });

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
  // T-3553: a person's own skin sheet, where human-variation.js left one on the figure.
  const like = likenessLayout(root.userData?.chiLikenessSkin);
  if (!f) return like ? { ...NO_LOOK, like, key: `none|like:${like.url}` } : NO_LOOK;
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
  // The pictures on a sheet carry the person's own brows: no shade is drawn under them.
  const ageStep = Math.round(a * 20) / 20, brow = hc && !like ? BROW.shade : 0;
  return { age: ageStep, brow, face, marks, tint, like,
    key: `${ageStep}|${brow}|${tint.map(t => t.toFixed(2))}|${f.o.toArray().map(t => Math.round(t * 500)).join(',')}${like ? `|like:${like.url}` : ''}` };
}

function setLook(uniforms, look) {
  uniforms.chiFace.value.copy(look.face);
  uniforms.chiFaceLook.value.set(look.age, look.brow, 0, 0);
  uniforms.chiFaceMarks.value.set(...look.marks);
  uniforms.chiBrowTint.value.set(...look.tint);
}

/**
 * A person's own skin sheet (T-3553). `skin` is their row's `skin` block as
 * tools/human_variation_kit.py writes it and human-variation.js hands it on with its address:
 * { url, size_px, rects: [{ uv, px }], mask: { px, scale }, tint, gain }. Up to three rects.
 * Returns what the shader needs, or null where there is no sheet or it does not parse.
 * `fine_lods`: how many of the nearest levels draw the skin finer under the hair.
 */
export const LIKENESS = Object.freeze({ rects: 3, small_px: 700, under_hat_m: .006, fine_lods: 2 });
/** A phone: it keeps a sheet at half size, and the skin under the hair as the body drew it. */
const smallScreen = () => typeof screen !== 'undefined' && (navigator?.maxTouchPoints ?? 0) > 0 && Math.min(screen.width, screen.height) < LIKENESS.small_px;
const NO_HAT = 1e6;
export function likenessLayout(skin) {
  const [W, H] = skin?.size_px ?? [];
  const rects = skin?.rects;
  if (!skin?.url || !(W > 0) || !(H > 0) || !Array.isArray(rects) || !rects.length || rects.length > LIKENESS.rects) return null;
  const uv = [], map = [];
  for (const r of rects) {
    const [u0, v0, u1, v1] = r.uv ?? [], [x0, y0, x1, y1] = r.px ?? [];
    if (![u0, v0, u1, v1, x0, y0, x1, y1].every(Number.isFinite) || !(u1 > u0) || !(v1 > v0)) return null;
    const sx = (x1 - x0) / (u1 - u0) / W, sy = (y1 - y0) / (v1 - v0) / H;
    uv.push([u0, v0, u1, v1]);
    map.push([sx, sy, x0 / W - u0 * sx, y0 / H - v0 * sy]);
  }
  const m = skin.mask;
  if (!m || !(m.scale > 0) || !Array.isArray(m.px)) return null;
  const tint = Array.isArray(skin.tint) && skin.tint.length === 3 && skin.tint.every(Number.isFinite) ? skin.tint : [1, 1, 1];
  // How far the hair stands out from the skin, where the sheet keeps it (the mask's red).
  const g = skin.grow, grows = g && g.reach_m > 0 && Array.isArray(g.from_m) && g.from_m.length === 3 && g.from_m.every(Number.isFinite)
    && Array.isArray(g.normal_px) && g.normal_px.length === 2 && g.normal_px.every(Number.isFinite);
  // The person's own irises (two squares side by side, the body's left eye first) and the
  // colour of the whites, where the sheet keeps them.
  const e = skin.eyes, eyed = e && e.size > 0 && Array.isArray(e.px) && e.px.length === 2 && e.px.every(Number.isFinite)
    && Array.isArray(e.white_srgb) && e.white_srgb.length === 3 && e.white_srgb.every(Number.isFinite);
  return { url: skin.url, uv, map, mask: [m.px[0] / W, m.px[1] / H, m.scale, 1], tint: [...tint, Number.isFinite(skin.gain) ? skin.gain : 1],
    grow: grows ? [...g.from_m, g.reach_m] : [0, 0, 0, 0], facing: grows ? [g.normal_px[0] / W, g.normal_px[1] / H] : [0, 0],
    // The upright line the hair stands out from (its length down from `grow`), and the cells of the sheet it stands out in.
    axis: grows && g.axis_m > 0 ? g.axis_m : 0, fine: grows ? fineCells(g.fine, skin.size_px) : null,
    eyes: eyed ? { rect: [e.px[0] / W, e.px[1] / H, 2 * e.size / W, e.size / H], white: e.white_srgb.slice() } : null,
    // The teeth behind an open mouth's lips (human-mouth.js): a strip of points and their places on the body's map.
    teeth: teethStrip(skin.teeth),
    // The front picture as a picture (FRONT_VIEW), for a head whose hair stands out.
    front: grows ? frontPicture(skin.front) : null };
}

/**
 * A person's front picture, as their row's `skin.front` gives it (tools/bake_likeness_skin.py
 * front_layer; human-variation.js adds its address): the file's size, the picture's own
 * rectangle on it and the rectangle that says where it is shown (pixels), the picture's across
 * and down from a place in the body's rest frame (`u`, `v`: four numbers each, metres to 0..1),
 * and the line it was taken along (`toward`, a unit vector). Null where there is none or it
 * does not parse.
 */
export function frontPicture(front) {
  const [W, H] = front?.size_px ?? [];
  const four = (a) => Array.isArray(a) && a.length === 4 && a.every(Number.isFinite);
  const t = front?.toward;
  if (!front?.url || !(W > 0) || !(H > 0) || !four(front.u) || !four(front.v) || !four(front.colour_px) || !four(front.shown_px) || !four(front.kind_px)
    || !(Array.isArray(t) && t.length === 3 && t.every(Number.isFinite) && Math.abs(Math.hypot(...t) - 1) < 1e-3)) return null;
  const rect = ([x0, y0, x1, y1]) => (x1 > x0 && y1 > y0 ? [x0 / W, y0 / H, (x1 - x0) / W, (y1 - y0) / H] : null);
  const at = [rect(front.colour_px), rect(front.shown_px), rect(front.kind_px)];
  return at.every(Boolean) ? { url: front.url, u: front.u.slice(), v: front.v.slice(), to: t.slice(), at } : null;
}

// One texture per sheet, shared by every body of that person (each level of detail, each
// rebuild). Fetched on first use; until it arrives the sampler reads nothing and the mask is
// empty, so the body's own map shows in the sheet's tone.
const sheets = new Map(), arriving = new Set();
/** Resolves once every skin sheet asked for so far has arrived or failed: a still waits on it. */
export function likenessSheetsReady() { return Promise.all([...arriving]).then(() => undefined); }
function likenessSheet(url) {
  if (typeof document === 'undefined') return null;   // no page (a unit test): the uniforms alone
  let t = sheets.get(url);
  if (t) return t;
  t = new THREE.Texture();
  t.flipY = false;                      // the sheet's rows are the body map's: v down
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.anisotropy = 4;
  sheets.set(url, t);
  const arrival = new Promise((done) => {
    new THREE.ImageLoader().load(url, (img) => {
      // A phone keeps the sheet at half size (a quarter of the memory): its screen cannot show more.
      if (smallScreen()) {
        const c = document.createElement('canvas');
        c.width = img.width >> 1; c.height = img.height >> 1;
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        t.image = c;
      } else t.image = img;
      t.needsUpdate = true;
      for (const part of parts.get(url)?.values() ?? []) part.needsUpdate = true;
      done();
    }, undefined, () => { sheets.delete(url); done(); });   // a sheet that fails is asked for again by the next body
  });
  arriving.add(arrival);
  arrival.then(() => arriving.delete(arrival));
  return t;
}

/**
 * One rectangle of a sheet (x, y, width, height as shares of it) as a map of its own: the same
 * picture on the card (one source, so it is uploaded once), read through its own transform.
 */
const parts = new Map();
function likenessPart(url, rect) {
  const sheet = likenessSheet(url);
  if (!sheet) return null;
  const own = parts.get(url) ?? new Map();
  parts.set(url, own);
  const key = rect.join(',');
  let t = own.get(key);
  if (!t) {
    t = sheet.clone();
    t.offset.set(rect[0], rect[1]);
    t.repeat.set(rect[2], rect[3]);
    if (sheet.image) t.needsUpdate = true;   // else when the sheet arrives
    own.set(key, t);
  }
  return t;
}

/**
 * T-3553: a person's own eyes. A figure that wears its own skin sheet takes its irises from
 * the sheet too (each drawn from its front picture, tools/bake_likeness_skin.py) and the
 * colour of its whites; the model's flat pupil takes the picture's own, and the cornea
 * mirrors less of the sky, the picture having its own light in it. Clones of one export share
 * their eyes' materials, so the figure takes twins of its own.
 */
function likenessEyes(m, mesh, root, like) {
  const key = `eyes:${like.url}`;
  if (m.userData?.chiLikeEyes === key) return m;
  const own = variants.get(m) ?? new Map();
  variants.set(m, own);
  let twin = own.get(key);
  if (!twin) {
    twin = m.clone();
    twin.userData = { ...twin.userData, chiLikeEyes: key };
    patched.set(twin, patchEyes(twin, mesh, root));
    const gain = like.tint[3];
    if (/__(iris|pupil)$/.test(m.name)) {
      // The iris is a ring and the pupil the disc in it: both read the one picture.
      twin.map = likenessPart(like.url, like.eyes.rect);
      twin.color.setScalar(gain);
      twin.envMapIntensity = EYES.like_sky;
    } else if (/__sclera$/.test(m.name)) twin.color.setRGB(...like.eyes.white, THREE.SRGBColorSpace).multiplyScalar(gain);
    twin.needsUpdate = true;
    own.set(key, twin);
  }
  return twin;
}

function setLikeness(uniforms, like) {
  uniforms.chiLike.value = like ? likenessSheet(like.url) : null;
  for (let k = 0; k < LIKENESS.rects; k++) {
    // An unused rect is empty (its far corner before its near one), so nothing falls inside it.
    uniforms.chiLikeUv.value[k].set(...(like?.uv[k] ?? [2, 2, -1, -1]));
    uniforms.chiLikeMap.value[k].set(...(like?.map[k] ?? [0, 0, 0, 0]));
  }
  uniforms.chiLikeMask.value.set(...(like?.mask ?? [0, 0, 0, 0]));
  uniforms.chiLikeTint.value.set(...(like?.tint ?? [1, 1, 1, 1]));
  uniforms.chiLikeGrow.value.set(...(like?.grow ?? [0, 0, 0, 0]));
  uniforms.chiLikeHat.value.set(NO_HAT, LIKENESS.under_hat_m, ...(like?.facing ?? [0, 0]));
  uniforms.chiLikeAxis.value = like?.axis ?? 0;
  // No teeth: an empty rect (its far corner before its near one), which shades nothing.
  uniforms.chiLikeTeeth.value.set(...(like?.teeth?.rect ?? [2, 2, -1, -1]));
  // No front picture: nothing to read, and the fourth of `to` says so.
  const f = like?.front;
  uniforms.chiLikeFront.value = f ? likenessSheet(f.url) : null;
  uniforms.chiLikeFrontU.value.set(...(f?.u ?? [0, 0, 0, 0]));
  uniforms.chiLikeFrontV.value.set(...(f?.v ?? [0, 0, 0, 0]));
  for (let k = 0; k < 3; k++) uniforms.chiLikeFrontAt.value[k].set(...(f?.at[k] ?? [0, 0, 0, 0]));
  uniforms.chiLikeFrontTo.value.set(...(f ? [...f.to, 1] : [0, 0, 1, 0]));
}

/**
 * T-3553: where a person's hair stands out of their skin, the skin is drawn finer (human-fine.js):
 * at the near levels, never on a phone. The fine geometry is the person's own at that level
 * (one for each of their varied geometries), with the body's vertices first and in order.
 */
function fineSkin(mesh, root, like) {
  const lod = Number(/_lod(\d+)$/.exec(mesh.name)?.[1] ?? NaN);
  if (!like?.fine || !(lod < LIKENESS.fine_lods) || Array.isArray(mesh.material) || smallScreen()) return false;
  const g = fineOf(mesh.geometry, like.url, { metres: restMatrix(mesh, root), layout: like, cells: like.fine });
  if (!g || g === mesh.geometry) return false;
  // Its blink is the shaped one's, a vertex more for each edge split: not to be shaped again.
  for (const t of g.morphAttributes.position ?? []) if (t) blinked.add(t);
  mesh.geometry = g;
  return true;
}

/**
 * T-3553: a person whose mouth is open has teeth behind the lips (human-mouth.js). One with a
 * picture of their teeth has its strip added to the skin's own geometry at every level, carried
 * by the head's bone; everyone else has drawn ones (drawnTeethMesh).
 */
function teethSkin(mesh, root, like, person) {
  if (Array.isArray(mesh.material)) return false;
  if (!like?.teeth) return drawnTeethMesh(mesh, root, person);
  drawnTeethOf(mesh)?.removeFromParent();   // drawn ones an earlier dressing left, before the sheet was the figure's
  const bone = mesh.skeleton?.bones.findIndex(b => b.name === like.teeth.bone) ?? -1;
  const g = teethOf(mesh.geometry, like.url, { metres: restMatrix(mesh, root), strip: like.teeth, bone });
  if (!g || g === mesh.geometry) return false;
  // Its blink is the shaped one's, a row more for each of the strip's points: not to be shaped again.
  for (const t of g.morphAttributes.position ?? []) if (t) blinked.add(t);
  mesh.geometry = g;
  return true;
}

/** The mesh of drawn teeth beside the skin `mesh`, where an earlier dressing left one (on its bones: a copy of a figure has skeletons of its own). */
const drawnTeethOf = mesh => mesh.parent?.children.find(o => o.userData?.chiTeeth === true && o.skeleton?.bones?.[0] === mesh.skeleton?.bones?.[0]) ?? null;

/**
 * T-3553: everyone's teeth. Two short drawn rows behind the person's own lips (human-mouth.js
 * drawnTeeth), as a small mesh of their own beside the skin, in the skin's material and on its
 * skeleton: the upper row is carried by the head, the lower by the jaw. It is made hidden; the
 * mouth's play shows it while the jaw is open to a visitor who stands near (MOUTH.teeth_deg,
 * teeth_m), so nobody with their mouth shut, and nobody further off, costs a draw. The rows are
 * kept once for the person's own geometry at each level and freed with it. A level whose lips'
 * edge is not found has none. It takes the sun's shadows as the skin does, each time it is
 * drawn (the figure's level sets that on the skin by its distance, and does not know of this
 * mesh), or teeth in a shaded face stood in full sun.
 */
function drawnTeethMesh(mesh, root, { age = null, person = null } = {}) {
  const bones = mesh.skeleton?.bones, old = drawnTeethOf(mesh);
  const look = drawnLook({ id: person ?? someone(root), age });
  const g = !mesh.parent || !bones || mesh.geometry?.userData?.chiTeeth ? null : teethOf(mesh.geometry, look.key, () => {
    const metres = restMatrix(mesh, root), strips = drawnTeeth(mesh.geometry, { metres, look });
    return strips && { metres, apart: true, strips: strips.map(s => ({ strip: s.strip, bone: bones.findIndex(b => b.name === s.bone) })) };
  });
  if (!g || g === mesh.geometry) { old?.removeFromParent(); return false; }
  const teeth = old ?? new THREE.SkinnedMesh(g, mesh.material);
  if (teeth.geometry !== g) { teeth.geometry = g; teeth.updateMorphTargets(); }
  teeth.material = mesh.material;
  teeth.onBeforeRender = function () { this.receiveShadow = mesh.receiveShadow; };
  if (!old) {
    teeth.name = 'teeth';
    teeth.userData.chiTeeth = true;
    teeth.position.copy(mesh.position); teeth.quaternion.copy(mesh.quaternion); teeth.scale.copy(mesh.scale);
    teeth.bind(mesh.skeleton, mesh.bindMatrix);
    teeth.frustumCulled = false; teeth.castShadow = false; teeth.receiveShadow = mesh.receiveShadow;
    teeth.visible = false;
    mesh.parent.add(teeth);
  }
  return true;
}

/** Who a figure is, where nobody is named: the key its variation was drawn by (human-variation.js), so two strangers differ. */
const someone = root => (typeof root?.userData?.chiVariationKey === 'string' ? root.userData.chiVariationKey : 'human');

/**
 * The height (the skin's bind pose, metres from the root) of the lowest part of a hat that sits
 * on this head, or NO_HAT. The hat is skinned with its own inverse binds (driver-livery.js), so
 * its vertices are carried into the skin's bind pose through the head bone both share; `mid` is
 * the middle of the head (bind pose), and only what is over the head counts (not a hanging veil).
 */
function hatBand(hat, mesh, root, mid) {
  const hi = hat.skeleton?.bones.findIndex(b => b.name === 'head') ?? -1, bi = mesh.skeleton?.bones.findIndex(b => b.name === 'head') ?? -1;
  const p = hat.geometry?.attributes?.position;
  if (hi < 0 || bi < 0 || !p) return NO_HAT;
  root.updateMatrixWorld(true);
  const s = mesh.skeleton;
  const M = new THREE.Matrix4().copy(root.matrixWorld).invert().multiply(s.bones[0].matrixWorld).multiply(s.boneInverses[0])
    .multiply(s.boneInverses[bi].clone().invert()).multiply(hat.skeleton.boneInverses[hi]).multiply(hat.bindMatrix);
  const v = new THREE.Vector3();
  let low = Infinity;
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).applyMatrix4(M);
    const dx = v.x - mid[0], dz = v.z - mid[2];
    if (dx * dx + dz * dz < .11 * .11 && v.y > mid[1]) low = Math.min(low, v.y);
  }
  return Number.isFinite(low) ? low : NO_HAT;
}

/** A figure whose hair stands out from its skin (a sheet with `grow`) keeps it under a hat it wears. */
function watchHat(mesh, root, look) {
  if (!(look.like?.grow?.[3] > 0) || mesh.userData.chiLikeHatWatch) return;
  mesh.userData.chiLikeHatWatch = true;
  const prior = mesh.onBeforeRender;
  let frame = 0, seen;
  mesh.onBeforeRender = function (...args) {
    prior?.apply(this, args);
    if (frame++ % 30) return;
    // Only a hat that is worn: one left off (a bareheaded still) flattens nothing.
    const hat = mesh.parent?.children.find(o => o.isSkinnedMesh && o.visible && /^headwear/.test(o.material?.name ?? '') && !/band/.test(o.material.name)) ?? null;
    if (hat === seen) return;
    seen = hat;
    const u = patched.get(mesh.material);
    if (u?.chiLikeHat) u.chiLikeHat.value.x = hat ? hatBand(hat, mesh, root, look.like.grow) : NO_HAT;
  };
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
  // T-3553: a figure with its own skin sheet may have its own eyes on it.
  const sheet = likenessLayout(root.userData?.chiLikenessSkin), eyesLike = sheet?.eyes ? sheet : null;
  for (const mesh of meshes) {
    for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      const surface = surfaceFor(m);
      if (!surface || !m?.isMeshStandardMaterial) continue;
      if (mesh.userData?.chiTeeth === true) continue;   // an earlier dressing's drawn teeth, in the skin's material
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
        fineSkin(mesh, root, look.like);
        teethSkin(mesh, root, look.like, person);
        watchHat(mesh, root, look);
        dressed[m.name] = surface;
        continue;
      }
      if (surface === 'eyes' && eyesLike && /__(sclera|iris|pupil)$/.test(m.name) && !Array.isArray(mesh.material)) {
        mesh.material = likenessEyes(m, mesh, root, eyesLike);
        if (/__(iris|pupil)$/.test(m.name)) domeCornea(mesh, root);
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
  // T-3553: every figure with a jaw, or a smile to move into, is given its mouth's play
  // (human-mouth.js); human-actions.js finds it here and tells it when the person greets and talks.
  {
    // (A copy of a dressed figure carries a plain record of the mouth, not the mouth: it is made again.)
    const mouth = typeof root.userData.chiMouth?.bind === 'function' ? root.userData.chiMouth : createMouth({ id: person.person ?? someone(root) });
    if (mouth.bind(root)) root.userData.chiMouth = mouth; else delete root.userData.chiMouth;
  }
  return dressed;
}

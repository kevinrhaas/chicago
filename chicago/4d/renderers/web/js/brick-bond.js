/**
 * brick-bond.js — a K03 brick wall drawn without its tile showing. T-3295.
 *
 * The owner, 2026-11-01, on a brick flank seen from 1825 Prairie on his phone:
 * "this brick pattern appears too regular ... they appear as a pattern and are too
 * consistent and repetitive". Every K03 brick wall in 1904 wears ONE bonded panel
 * (`assets/textures/prairie_1904_brick/panel/<id>/`): 4 modules by 12 courses,
 * 0.86 x 0.80 m. A two-storey flank shows the same 48 bricks about 150 times, and
 * the panel's few burnt and salmon bricks line up into a lattice the eye finds at
 * once.
 *
 * ## Why the renderer, and not a bigger panel
 *
 * A panel large enough not to read as a tile (16 x 48, 3.5 x 3.2 m) is sixteen
 * times the pixels: about 16 MB more GPU memory per map pair at the panel's
 * 600 px/m, in a 1904 scene already at its phone ceiling (T-3173). Halving the
 * resolution to pay for it would blur every joint. So the panel stays as it is
 * and the shader stops repeating it:
 *
 *   1. **Every brick draws its face from another brick of the same kind.** The
 *      panel is bonded data, so the brick a fragment lies on is arithmetic in the
 *      map's own coordinate: the course is `floor(-v * courses)` (glTF's v runs
 *      down the image; the panel's foot is a bed joint at v = 0), and along a
 *      course the units start at `-offset + k * unit` modules (the generator's
 *      `course_layout`). A hash of that brick's place on the wall — and of the
 *      building it is on — picks a target course with the same unit length and a
 *      target unit in it, and the fragment samples there at the SAME offset inside
 *      its unit. So each brick keeps a whole brick's face, grain, arris and chips,
 *      and its own half of every joint round it: the cut between two bricks falls
 *      on a joint's centre line, in mortar on both sides. `textureGrad` with the
 *      unshuffled derivatives keeps the mip level continuous across those cuts.
 *   2. **Each brick takes its own small colour spread**, warm or cool and lighter or
 *      darker, masked off the mortar and faded out once a course is under about two
 *      pixels (where per-brick colour would only sparkle).
 *   3. **A broad mottle** of a few percent over a wall, a couple of metres across —
 *      the uneven weathering a real flank has. Mean-neutral, so a wall's colour as a
 *      whole (and every photo-match verdict read off it) is unchanged.
 *
 * No texture, attribute, draw call or GLB byte is added: the cost is a few ALU
 * operations and a hash per fragment on brick walls only.
 *
 * ## How a material is known to be a K03 panel
 *
 * By the base-colour image's name, `<panel id>_basecolor`, which `k01_frontage.to_glb`
 * writes from the panel's `material.json` and the web derivative keeps
 * (docs/GLB-CONTRACT.md § Brick panels). The bond of each panel is restated below;
 * `tools/check_brick_bond.mjs` holds it equal to `profiles.json` and each panel's
 * `material.json`, so the renderer cannot drift from the library it reads.
 * A Flemish panel mixes stretchers and headers within a course and is not laid
 * by any record; it is left unshuffled, and the check says so.
 *
 * The bricks are not evidence of anything: the panel is a reconstruction
 * (L-k03-brick-library-2290), and so is this spread (L-k03-brick-shuffle-3295).
 */

import { ShaderChunk } from 'three';
import { captureHooks, registerPatch } from './batch-material.js';
import { programKeyOf } from './confidence.js';

/** The library's module and course (profiles.json `module`). */
export const MODULE_M = 0.2159;
export const COURSE_M = 0.066675;

/**
 * profiles.json `bonds`: each course's offset along the course (modules) and its
 * unit length (modules; S = 1, H = 0.5), bottom course first.
 */
const S = 1.0, H = 0.5;
export const BONDS = Object.freeze({
  running: Object.freeze([[0.0, S], [0.5, S]]),
  common_6: Object.freeze([
    [0.0, S], [0.5, S], [0.0, S], [0.5, S], [0.0, S], [0.0, H],
    [0.5, S], [0.0, S], [0.5, S], [0.0, S], [0.5, S], [0.0, H],
  ]),
});

/** Each panel a K03 wall may wear: its bond, its repeat, its joint (material.json). */
export const PANELS = Object.freeze({
  common_buff_common_6: Object.freeze({ bond: 'common_6', modules: 4, courses: 12, joint_m: 0.009 }),
  rough_red_brown_running: Object.freeze({ bond: 'running', modules: 4, courses: 12, joint_m: 0.01 }),
  pressed_red_running: Object.freeze({ bond: 'running', modules: 4, courses: 12, joint_m: 0.004 }),
});

/** The panels the library offers that this module does not shuffle, and why. */
export const NOT_SHUFFLED = Object.freeze({
  pressed_red_flemish_dark_headers: 'Flemish bond mixes stretchers and headers in one course; no record lays it',
});

/**
 * The spread, reconstructed (L-k03-brick-shuffle-3295): ±7 % per brick in
 * lightness, ±3 % warm to cool, and a ±5 % mottle a couple of metres across.
 * Bounded by the panel's own firing variants (tints 0.87-1.04 of the body),
 * so a brick never leaves the range the library already deals.
 */
export const SPREAD = Object.freeze({ lightness: 0.07, warmth: 0.03, mottle: 0.05 });

/** The most courses a panel may have: the uniform array's length. */
const MAX_COURSES = 12;

/**
 * The per-panel uniforms: the course table, the course list grouped by unit
 * length (so a brick only ever swaps with a brick of its own length), and the
 * panel's size and half-joint in its own units.
 */
export function bondUniforms(panelId) {
  const panel = PANELS[panelId];
  if (!panel) return null;
  const bond = BONDS[panel.bond];
  const courses = panel.courses;
  if (courses > MAX_COURSES || courses % bond.length) {
    throw new Error(`${panelId}: ${courses} courses do not hold whole periods of ${panel.bond}`);
  }
  const rows = Array.from({ length: courses }, (_, i) => bond[i % bond.length]);
  const lengths = [...new Set(rows.map(([, u]) => u))].sort((a, b) => b - a);
  const list = [];
  const start = new Map();
  for (const u of lengths) {
    start.set(u, list.length);
    rows.forEach(([, uu], i) => { if (uu === u) list.push(i); });
  }
  const course = rows.map(([offset, unit]) => [offset, unit, start.get(unit),
    rows.filter(([, uu]) => uu === unit).length]);
  while (course.length < MAX_COURSES) course.push([0, S, 0, 1]);
  while (list.length < MAX_COURSES) list.push(0);
  const half = panel.joint_m / 2;
  return {
    panel: [panel.modules, courses, half / MODULE_M, half / COURSE_M],
    course,
    list: [list.slice(0, 4), list.slice(4, 8), list.slice(8, 12)],
  };
}

/** `?bricks=tiled` draws the panel as it was before T-3295, for a before/after. */
export function brickBondFromSearch(search = '') {
  return new URLSearchParams(search).get('bricks') !== 'tiled';
}

/** The panel a material's base colour is, or null. */
export function panelOf(material) {
  const name = material?.map?.name ?? '';
  const m = /^(.*)_basecolor(?:_web)?$/.exec(name);
  return m && PANELS[m[1]] ? m[1] : null;
}

const FRAGMENT_PARS = /* glsl */`
uniform vec4 chiBondPanel;
uniform vec4 chiBondCourse[ ${MAX_COURSES} ];
uniform vec4 chiBondList[ 3 ];
uniform vec3 chiBondSpread;
flat varying vec2 vChiBondSeat;
uint chiBondHash( uvec3 v ) {
  v = v * 1664525u + 1013904223u;
  v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
  v ^= v >> 16u;
  v.x += v.y * v.z; v.y += v.z * v.x; v.z += v.x * v.y;
  return v.x ^ v.y ^ v.z;
}
vec3 chiBondRand( ivec2 cell, uint salt ) {
  uint h = chiBondHash( uvec3( uint( cell.x ), uint( cell.y ),
    salt ^ uint( int( round( vChiBondSeat.x * 4.0 ) ) ) * 2654435761u
         ^ uint( int( round( vChiBondSeat.y * 4.0 ) ) ) * 2246822519u ) );
  return vec3( float( h & 1023u ), float( ( h >> 10u ) & 1023u ), float( ( h >> 20u ) & 1023u ) ) / 1023.0;
}
float chiBondNoise( vec2 p ) {
  vec2 i = floor( p ), f = fract( p );
  f = f * f * ( 3.0 - 2.0 * f );
  ivec2 c = ivec2( i );
  float a = chiBondRand( c, 0x51u ).x, b = chiBondRand( c + ivec2( 1, 0 ), 0x51u ).x;
  float d = chiBondRand( c + ivec2( 0, 1 ), 0x51u ).x, e = chiBondRand( c + ivec2( 1, 1 ), 0x51u ).x;
  return mix( mix( a, b, f.x ), mix( d, e, f.x ), f.y ) * 2.0 - 1.0;
}
`;

/**
 * Resolves the brick under `vMapUv`: `chiBondShift` (added to a map coordinate, it
 * reads the brick this one draws its face from) and `chiBondTint`.
 */
const FRAGMENT_RESOLVE = /* glsl */`
  {
    float M = chiBondPanel.x, C = chiBondPanel.y;
    float gx = vMapUv.x * M;
    float gy = - vMapUv.y * C;
    float course = floor( gy );
    float fy = gy - course;
    int ci = clamp( int( mod( course, C ) ), 0, int( C ) - 1 );
    vec4 cc = chiBondCourse[ ci ];
    float L = cc.y;
    float k = floor( ( gx + cc.x ) / L );
    float dx = gx + cc.x - k * L;
    ivec2 cell = ivec2( int( k ), int( course ) );
    vec3 r = chiBondRand( cell, 0xb7u );
    int pick = int( cc.z ) + min( int( r.x * cc.w ), int( cc.w ) - 1 );
    int tc = int( chiBondList[ pick / 4 ][ pick % 4 ] );
    vec4 tcc = chiBondCourse[ tc ];
    float perCourse = M / L;
    float tk = min( floor( r.y * perCourse ), perCourse - 1.0 );
    vec2 src = vec2( tk * L - tcc.x + dx, float( tc ) + fy );
    chiBondShift = vec2( src.x - gx, - ( src.y - gy ) ) / vec2( M, C );

    vec3 t = chiBondRand( cell, 0x2du );
    float warm = chiBondSpread.y * ( t.y * 2.0 - 1.0 );
    vec3 tint = ( 1.0 + chiBondSpread.x * ( t.x * 2.0 - 1.0 ) ) * vec3( 1.0 + warm, 1.0, 1.0 - warm );
    vec2 fw = max( fwidth( vec2( gx, gy ) ), vec2( 1e-4 ) );
    float ex = min( dx, L - dx ) - chiBondPanel.z;
    float ey = min( fy, 1.0 - fy ) - chiBondPanel.w;
    float onBrick = clamp( ex / fw.x + 0.5, 0.0, 1.0 ) * clamp( ey / fw.y + 0.5, 0.0, 1.0 );
    float near = 1.0 - smoothstep( 0.25, 0.6, fw.y );
    chiBondTint = mix( vec3( 1.0 ), tint, onBrick * near );
    float mottle = 0.65 * chiBondNoise( vec2( gx / 11.0, gy / 33.0 ) )
                 + 0.35 * chiBondNoise( vec2( gx / 4.7, gy / 13.0 ) + 17.0 );
    chiBondTint *= 1.0 + chiBondSpread.z * mottle;
  }
`;

const MAP_FRAGMENT = /* glsl */`
vec2 chiBondShift = vec2( 0.0 );
vec3 chiBondTint = vec3( 1.0 );
#ifdef USE_MAP
${FRAGMENT_RESOLVE}
  vec4 sampledDiffuseColor = textureGrad( map, vMapUv + chiBondShift, dFdx( vMapUv ), dFdy( vMapUv ) );
  diffuseColor *= sampledDiffuseColor;
  diffuseColor.rgb *= chiBondTint;
#endif
`;

const NORMAL_SAMPLE = 'texture2D( normalMap, vNormalMapUv )';
const NORMAL_SHUFFLED = 'textureGrad( normalMap, vNormalMapUv + chiBondShift, dFdx( vNormalMapUv ), dFdy( vNormalMapUv ) )';
/** three's chunk with its two normal-map samples moved with the brick; if a future three
 *  samples differently the relief simply stays where the panel put it (colour still moves). */
const NORMAL_FRAGMENT = ShaderChunk.normal_fragment_maps.includes(NORMAL_SAMPLE)
  ? ShaderChunk.normal_fragment_maps.split(NORMAL_SAMPLE).join(NORMAL_SHUFFLED)
  : null;

/**
 * Bind the shuffle to a material whose base colour is a K03 panel. Called on every
 * structures material before its batch key is read (buildings.js, beside the roof
 * and wall relief), so a bound material is patched once and batches as before.
 * Returns the panel id, or null when the material is not a panel.
 */
export function applyBrickBond(material, { on = true } = {}) {
  const panelId = on ? panelOf(material) : null;
  if (!panelId || material.userData?.chiBrickBond) return null;
  const u = bondUniforms(panelId);
  const batchHooks = captureHooks(material);
  const prior = material.onBeforeCompile;
  const priorKey = programKeyOf(material);
  const uniforms = {
    chiBondPanel: { value: new Float32Array(u.panel) },
    chiBondCourse: { value: new Float32Array(u.course.flat()) },
    chiBondList: { value: new Float32Array(u.list.flat()) },
    chiBondSpread: { value: new Float32Array([SPREAD.lightness, SPREAD.warmth, SPREAD.mottle]) },
  };
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = 'flat varying vec2 vChiBondSeat;\n' + shader.vertexShader.replace(
      '#include <batching_vertex>',
      `#include <batching_vertex>
  #ifdef USE_BATCHING
    vChiBondSeat = batchingMatrix[ 3 ].xz;
  #else
    vChiBondSeat = modelMatrix[ 3 ].xz;
  #endif`,
    );
    let fragment = shader.fragmentShader.replace('#include <map_fragment>', MAP_FRAGMENT);
    if (NORMAL_FRAGMENT) fragment = fragment.replace('#include <normal_fragment_maps>', NORMAL_FRAGMENT);
    shader.fragmentShader = FRAGMENT_PARS + fragment;
  };
  // The panel's bond rides uniforms, so every panel shares one program; the key says
  // what is beneath it, as perVertexScalars' does (T-0053's rule).
  material.customProgramCacheKey = () => `k03-brick-bond-v1${priorKey ? `|over:${priorKey}` : ''}`;
  registerPatch(material, batchHooks, 'k03-brick-bond-v1', { panel: panelId });
  material.userData = { ...(material.userData ?? {}), chiBrickBond: panelId };
  material.needsUpdate = true;
  return panelId;
}

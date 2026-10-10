/**
 * wall-relief.js — the town's walls, bound as relief: T-1769's strategy A on
 * real buildings. T-1963.
 *
 * Until this module every wall in the town was a flat-shaded colour. T-1962 gave
 * the lap lines an irregular lay and the bare stock a household's weathering, and
 * its critic frames showed both were real and both were small, because a flat
 * colour has nothing in it for the eye to read at walking distance. The fabric
 * proof (`docs/RESEARCH/1835_fabric_proof.md`) built the answer on one bay and
 * one pen; this is that answer turned on for every clapboarded and log wall that
 * stands in the town. What it looked like before and after, what it costs, and
 * the critique against Glessner v4, are `docs/RESEARCH/1835_wall_relief.md`.
 *
 * ## Strategy A, as `roof-relief.js` and the proof built it
 *
 *  - **A metric UV, derived in the vertex shader from the face's own frame**:
 *    t = n x up (along the courses), b = t x n (up the wall), uv = (p.t, p.b) /
 *    span. No attribute, no UV, no vertex and no bake; the courses run level on
 *    every wall whatever the building's bearing. Exact per vertex for the reason
 *    roof-relief.js gives: every polygon is flat-shaded, so the projection is
 *    affine over a face.
 *  - **One shared relief pair per substrate**: the library's `normal_gl`, and an
 *    `orl` packed here at load from the library's `orm` and basecolor —
 *    R = AO, G = roughness (the library's own), B = 0.5 * L / mean(L), the
 *    basecolor's linear luminance over its own mean. Metallic is 0 on wood, so B
 *    was free. That is `tools/fabric_proof_1835_maps.py`'s recipe, done in the
 *    page the way `frontage.js` derives its board face, so no derived image is
 *    committed and the library stays the one source.
 *  - **Colour stays on the vertex.** `diffuse *= mix(1, 2 * orl.B, grain)`: the
 *    mean of 2 * orl.B is 1, so the household's finish (T-0002's jitter, T-0007's
 *    dealing, T-1962's wear) is the MEAN and the wood's figure is the variation
 *    around it.
 *  - **Roughness by ratio**: roughness = the vertex's own finish roughness *
 *    orl.G / mean(orl.G). A wall batch therefore keeps every household's gloss —
 *    whitewash 0.90 and white lead 0.60 in the same draw call — which
 *    `perVertexRoughness` could not do for a mapped material.
 *  - **Grain strength by finish**, per vertex, in a `_grain` attribute
 *    `buildings.js` writes for bound walls only: bare stock 1.0, a coat 0.3
 *    (`wall-grain.js`). A coat hides the wood's colour and keeps its relief.
 *
 * Per-material differences are UNIFORMS, never code (the proof's defect 2):
 * three caches a program by `onBeforeCompile`'s source text, so the two
 * substrates share one program and differ only in their tile and mean.
 *
 * ## What is bound, and what is not
 *
 * By `wall-grain.js`'s rule, read off the record: `wall` on the three frame
 * archetypes (clapboard, but not the three storefronts dealt vertical board) and
 * `log` on the archetypes whose logs lie down, and since T-2123 on the
 * stockade's standing pickets with the grain turned up the post (a negative
 * `_grain`, see `wall-grain.js` STANDING_LOG_ARCHETYPES). Trim, casings, sash, chinking,
 * battens and outbuilding boards are NOT bound, because the face frame grains
 * every upright face horizontally and an upright board grained across reads as
 * broken (defect 4). The library maps are bound at 1024 px; a coarse device
 * (`lowSpec`) gets them resampled to 512 px, the Light row of the proof's costs.
 *
 * `?walls=flat` leaves every wall as it was, for the before-and-after captures.
 *
 * It degrades rather than throws, as `roof-relief.js` does: a missing map is a
 * town with flat walls, which is the state this improves on, reported on the
 * same `problems` list every other asset complaint travels on.
 */

import * as THREE from 'three';
import { resolveBases } from './scene-loader.js';
import { wallRelief } from './wall-grain.js';
import { packOrl } from './relief-pack.js';

const LIBRARY = 'textures/chicago_1835_pbr/';

/** `wall-grain.js` substrate -> the library directory that carries its face. */
const SUBSTRATES = {
  clapboard: 'walls/clapboard_board_face',
  hewn_log: 'walls/hewn_log_face',
};

/** The proof's Light row: 512 px maps and anisotropy 4 on a coarse device. */
const LIGHT_PX = 512;

/** `?walls=flat` — the town as it was before T-1963, for a comparison capture. */
export function wallReliefOff(search = globalThis.location?.search ?? '') {
  return new URLSearchParams(search).get('walls') === 'flat';
}

function image(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error(`wall relief map did not load — ${url}`));
    img.src = url;
  });
}

/** An image's RGBA bytes at `px` square (resampled by the canvas when it differs). */
function pixels(img, px) {
  const cv = document.createElement('canvas');
  cv.width = px;
  cv.height = px;
  const ctx = cv.getContext('2d', { willReadFrequently: true });
  ctx.imageSmoothingQuality = 'high';
  ctx.drawImage(img, 0, 0, px, px);
  return { canvas: cv, data: ctx.getImageData(0, 0, px, px).data };
}

/** A tiling, linear (data, never colour) texture. */
function tiled(tex, aniso) {
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.colorSpace = THREE.NoColorSpace;
  tex.anisotropy = aniso;
  tex.needsUpdate = true;
  return tex;
}

/** One substrate's pair: `{ normal, orl, tileM, meanRough }`. */
async function loadSubstrate(base, dir, lowSpec) {
  const here = new URL(`${dir}/`, base);
  const res = await fetch(new URL('material.json', here), { cache: 'no-cache' });
  if (!res.ok) throw new Error(`${res.status} — ${new URL('material.json', here)}`);
  const sheet = await res.json();
  const tileM = Number(sheet.span_m);
  if (!(tileM > 0)) throw new Error(`${dir}: material.json states no span_m`);
  const [nrm, orm, col] = await Promise.all([
    image(new URL(`${sheet.id}_normal_gl.webp`, here).href),
    image(new URL(`${sheet.id}_orm.webp`, here).href),
    image(new URL(`${sheet.id}_basecolor.webp`, here).href)]);
  const px = lowSpec ? Math.min(LIGHT_PX, orm.naturalWidth) : orm.naturalWidth;
  const aniso = lowSpec ? 4 : 8;

  // The albedo ratio: linear luminance over its own mean, halved so a texel
  // can carry up to twice the mean, packed bottom row first so it lies the
  // way the flipY'd normal beside it does (relief-pack.js, T-2300).
  const { data: orl, meanRough } = packOrl(pixels(orm, px).data, pixels(col, px).data, px);
  const orlTex = new THREE.DataTexture(orl, px, px, THREE.RGBAFormat);
  orlTex.generateMipmaps = true;
  orlTex.minFilter = THREE.LinearMipmapLinearFilter;
  orlTex.magFilter = THREE.LinearFilter;
  const normal = px === nrm.naturalWidth
    ? new THREE.Texture(nrm)
    : new THREE.CanvasTexture(pixels(nrm, px).canvas);
  return {
    id: sheet.id,
    normal: tiled(normal, aniso),
    orl: tiled(orlTex, aniso),
    tileM,
    meanRough,
    px,
  };
}

/**
 * The vertex and fragment edits. Written once, as a constant string, so every
 * bound material compiles the same source and shares one program.
 */
function patch(material, set) {
  const prior = material.onBeforeCompile;
  material.onBeforeCompile = (shader, renderer) => {
    if (typeof prior === 'function') prior(shader, renderer);
    shader.uniforms.chiWallTileM = { value: set.tileM };
    shader.uniforms.chiWallMeanRough = { value: set.meanRough };
    shader.vertexShader = 'uniform float chiWallTileM;\n'
      + 'attribute float _roughness;\nattribute float _grain;\n'
      + 'varying float vChiWallRough;\nvarying float vChiWallGrain;\n'
      + shader.vertexShader.replace(
        '#include <project_vertex>',
        `#include <project_vertex>
  {
    vec3 chiWallP = ( modelMatrix * vec4( transformed, 1.0 ) ).xyz;
    vec3 chiWallN = normalize( mat3( modelMatrix ) * objectNormal );
    vec3 chiWallT = cross( chiWallN, vec3( 0.0, 1.0, 0.0 ) );
    float chiWallL = length( chiWallT );
    chiWallT = chiWallL > 1e-4 ? chiWallT / chiWallL : vec3( 1.0, 0.0, 0.0 );
    vec3 chiWallB = cross( chiWallT, chiWallN );
    vec2 chiWallUv = vec2( dot( chiWallP, chiWallT ), dot( chiWallP, chiWallB ) ) / chiWallTileM;
    // A negative grain is a STANDING timber (T-2123): the grain runs up it.
    if ( _grain < 0.0 ) chiWallUv = chiWallUv.yx;
    vNormalMapUv = chiWallUv;
    vRoughnessMapUv = chiWallUv;
    vAoMapUv = chiWallUv;
    vChiWallRough = _roughness;
    vChiWallGrain = abs( _grain );
  }`,
      );
    shader.fragmentShader = 'uniform float chiWallMeanRough;\n'
      + 'varying float vChiWallRough;\nvarying float vChiWallGrain;\n'
      + shader.fragmentShader
        .replace('#include <color_fragment>', `#include <color_fragment>
  diffuseColor.rgb *= mix( 1.0, 2.0 * texture2D( roughnessMap, vRoughnessMapUv ).b, vChiWallGrain );`)
        .replace('#include <roughnessmap_fragment>', `float roughnessFactor = vChiWallRough
    * clamp( texture2D( roughnessMap, vRoughnessMapUv ).g / chiWallMeanRough, 0.0, 1.6 );`);
  };
  material.needsUpdate = true;
}

/** One load per page per tier: the packing is ~0.1 s of canvas work a substrate. */
const cache = new Map();
/**
 * The materials already patched. A set rather than a `userData` flag, because a
 * detail replacement CLONES its source materials and `Material.copy` carries
 * `userData` and the maps across but not `onBeforeCompile` — a flag would tell
 * the clone it was patched when it is not.
 */
const patched = new WeakSet();

/**
 * Load both substrates. Resolves to `{ problem, apply(material, sidecar) }`;
 * `apply` returns the grain to write into `_grain` for this material's vertices,
 * or `null` when the material is not a bound wall.
 */
export async function loadWallRelief({ assetBase = resolveBases().assetBase, lowSpec = false,
  off = wallReliefOff() } = {}) {
  if (off) return { problem: null, off: true, apply: () => null };
  const key = `${assetBase}|${lowSpec ? 'light' : 'full'}`;
  if (!cache.has(key)) {
    const base = new URL(LIBRARY, assetBase);
    cache.set(key, Promise.all(Object.entries(SUBSTRATES).map(async ([name, dir]) => (
      [name, await loadSubstrate(base, dir, lowSpec)]))).then((rows) => new Map(rows)));
  }
  let sets;
  try {
    sets = await cache.get(key);
  } catch (err) {
    cache.delete(key);
    return { problem: `wall relief maps not bound — ${err.message}`, apply: () => null };
  }
  return {
    problem: null,
    off: false,
    /** substrate -> `{ id, px, tileM, meanRough }`, for the record a capture writes. */
    sets: Object.fromEntries([...sets].map(([k, s]) => [k, {
      id: s.id, px: s.px, tileM: s.tileM, meanRough: Number(s.meanRough.toFixed(4)) }])),
    apply(material, sidecar) {
      const name = material?.name;
      if (name !== 'wall' && name !== 'log') return null;
      const rule = wallRelief(sidecar)[name];
      if (!rule) return null;
      const set = sets.get(rule.substrate);
      if (!set) return null;
      if (!patched.has(material)) {
        patched.add(material);
        material.normalMap = set.normal;
        // One packed file in two slots, as the roofs bind theirs: three's AO
        // chunk reads R; the roughness and the albedo ratio are read above.
        material.roughnessMap = set.orl;
        material.aoMap = set.orl;
        patch(material, set);
        material.userData = { ...(material.userData ?? {}), chiWallRelief: rule.substrate };
      }
      // The sign carries the axis, so a standing timber can share a batch,
      // a program and a map with the laid logs (the shader takes abs()).
      return rule.upright ? -rule.grain : rule.grain;
    },
  };
}

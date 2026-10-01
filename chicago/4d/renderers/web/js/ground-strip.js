/**
 * ground-strip.js — T-1797, the compact ground strip: packed street dirt with
 * irregular wear, worn bank soil, grey sand thinning into sparse prairie, drawn
 * through the terrain's own runtime-canvas path and feathered into its prairie.
 *
 * A PROOF, DRAWN ONLY UNDER `?proof=ground`. It is the third piece of T-1769:
 * the fabric map (docs/RESEARCH/1835_photographic_fabric_preparation.md) chose
 * the ground's method on paper, and this is that method standing in the real
 * scene — the real heightfield, sun, haze and sward around it — so T-1770–T-1772
 * can lift it with measured costs instead of a promise. The town a visitor walks
 * without the flag does not import this file.
 *
 * ## The method, and what each part is for
 *
 * - **Colour from the 1835 library, at its metric tile.** `wet_prairie_muck` and
 *   `lake_michigan_dune_sand` (6 m each), basecolor only, sampled by WORLD
 *   position the way `terrain.js` samples the prairie — a UV set would stretch
 *   across the bake's planar dissolves, world XZ cannot. `muddy_rutted_street`
 *   is deliberately NOT bound: its 8 m tile carries ruts that repeat (the map's
 *   own finding) and it is 4.6 MB on the wire. Local mud is the muck under the
 *   wetness mask instead.
 * - **Fine relief from a generated grit tile, NOT the library.** The map gave it
 *   to `packed_black_loam`; measured here, the loam (and the muck, and the sand)
 *   has almost none to give — see `gritTilePixels`. One 256 px runtime canvas at
 *   1.6 m carries height-as-grain and the normal together, one fetch.
 * - **Everything coarser from ONE seeded runtime canvas** (`ground-strip-mask.js`):
 *   traffic wear, wetness, 0.6–2 m clumping and 20–60 m broad tone in the four
 *   channels of one 416 × 128 texture, one fetch.
 * - **The dirt is coloured by a recorded tone**, a dusty one in the worn lanes and
 *   a darker one between them, times the grit's grain over its own mean (the
 *   substrate-zone rule in `terrain.js`), so the street averages the tone. The
 *   library loam is packed BLACK loam — right for a yard, too dark for a dry July
 *   street. The tones are reconstructed proof values; T-1770 owns the town's.
 * - **The prairie is the terrain's**, by import (`PRAIRIE_FRAGMENT`), so the
 *   feather lands on exactly the ground beside it and not on a copy of it.
 * - **Relief is a normal blend in a world tangent frame** (east, north, up), with
 *   mud flattened where water would lie. Normal maps do not stand in for a
 *   cross-section: the strip lies ON the heightfield, and grading it is T-1770's.
 */

import * as THREE from 'three';
import { PRAIRIE_FRAGMENT, WORLD_POS_VERT, prairieTexture } from './terrain.js';
import {
  STRIP, MASK_PX_PER_M, maskSize, stripMaskPixels, stripWeights, maskAt, stripLocal,
  GRIT_TILE_PX, GRIT_TILE_M, gritTilePixels,
} from './ground-strip-mask.js';

export { STRIP };

/**
 * Where to stand to see it. The first is the arrival under `?proof=ground`; all
 * three are added to the scene's anchors for the run, so `&anchor=` reaches them.
 */
export const STRIP_ANCHORS = Object.freeze([
  { id: 'ground_strip', label: 'Ground strip (proof)',
    local_e: STRIP.e0 + 1.5, local_n: STRIP.n0 - 1, yaw_deg: 88, pitch_deg: -9 },
  { id: 'ground_strip_above', label: 'Ground strip from above (proof)',
    local_e: STRIP.e0 + STRIP.lengthM / 2, local_n: STRIP.n0 + 17, yaw_deg: 180,
    altitude_m: 14, pitch_deg: -40 },
  { id: 'ground_strip_close', label: 'Ground strip, the dirt and the bank (proof)',
    local_e: STRIP.e0 + 14, local_n: STRIP.n0 + 5.5, yaw_deg: 150, pitch_deg: -30 },
]);

const LIBRARY = 'textures/chicago_1835_pbr/ground/';
/**
 * The two library substrates the strip binds, colour only. Their `normal_gl`
 * maps are as flat as the loam's (see `gritTilePixels`), so binding them would
 * spend two fetches and 11 MB of GPU memory on nothing.
 */
export const SUBSTRATES = Object.freeze(['wet_prairie_muck', 'lake_michigan_dune_sand']);

/**
 * The reconstructed tones, sRGB 0-255. Dirt is two: the worn traffic lanes,
 * dusty and paler, and the less-travelled ground between them. The bank's dry
 * soil is darker than the street, since a bank is damper. All
 * three sit inside the map's packed-dirt row; none is a source's.
 */
export const TONES = Object.freeze({
  dirtLane: [126, 112, 91],
  dirtRest: [96, 86, 69],
  bankDry: [98, 86, 66],
  // The sand's own hue is already the grey-beige the map asks for; what it
  // lacked was restraint. Its mean, held a little under z09's [168, 158, 124]
  // so an inland drift does not out-shine the lakeshore belt.
  sand: [136, 128, 106],
});

/** Grid spacing of the strip mesh, metres — finer than the heightfield's own. */
const MESH_STEP_M = 0.5;

function linearTone(rgb) {
  return new THREE.Color().setRGB(...rgb.map((v) => v / 255), THREE.SRGBColorSpace);
}

/** Mean linear Rec. 709 luminance of a loaded image, read at 256². */
function meanLinearLuma(image) {
  const S = 256;
  const c = document.createElement('canvas');
  c.width = c.height = S;
  const ctx = c.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(image, 0, 0, S, S);
  const d = ctx.getImageData(0, 0, S, S).data;
  const lin = (u8) => { const v = u8 / 255; return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  let sum = 0;
  for (let i = 0; i < d.length; i += 4) {
    sum += 0.2126 * lin(d[i]) + 0.7152 * lin(d[i + 1]) + 0.0722 * lin(d[i + 2]);
  }
  return sum / (S * S);
}

function loadMap(loader, url, colour) {
  return new Promise((resolve, reject) => {
    loader.load(url, (tex) => {
      tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
      tex.colorSpace = colour ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      // Four, as the prairie tile: the ground is most of the screen, and
      // terrain.js measured eight taps halving the software rasteriser's frame.
      tex.anisotropy = 4;
      resolve(tex);
    }, undefined, () => reject(new Error(`ground strip map did not load — ${url}`)));
  });
}

const FRAGMENT_HEAD = /* glsl */`
varying vec3 vChiWorld;
uniform sampler2D uGround;
uniform float uPrairieLuma;
uniform sampler2D uMask;
uniform vec4 uMaskFrame;
uniform sampler2D uGrit;
uniform float uGritM;
uniform float uGritMean;
uniform sampler2D uMuckC;
uniform sampler2D uSandC;
uniform vec2 uSpan;
uniform vec3 uDirtLane;
uniform vec3 uDirtRest;
uniform vec3 uBankDry;
uniform vec3 uSandTone;
uniform float uSandLuma;
uniform vec4 uBands;
uniform vec3 uStrip;
uniform vec2 uSize;
`;

/**
 * The per-fragment half of `stripWeights()` — keep the two in step; the flora
 * clearance reads the JS one. `(No backticks in here: a JS template literal.)`
 */
const STRIP_FRAGMENT = /* glsl */`
  // ---- T-1797 the ground strip ------------------------------------------- //
  vec2 chiEN = vec2(vChiWorld.x, -vChiWorld.z);
  vec4 chiM = texture2D(uMask, (chiEN - uMaskFrame.xy) * uMaskFrame.zw);
  float chiU = chiEN.x - uStrip.x;
  float chiV = chiEN.y - uStrip.y;
  float chiUj = chiU + (chiM.b - 0.5) * 2.4 + (chiM.a - 0.5) * 1.6;
  float chiDirtW = 1.0 - smoothstep(uBands.x - 1.5, uBands.x + 1.5, chiUj);
  float chiSandW = smoothstep(uBands.y - 1.5, uBands.y + 1.5, chiUj);
  float chiBankW = max(0.0, 1.0 - chiDirtW - chiSandW);
  float chiRamp = smoothstep(uBands.z, uBands.w, chiUj);
  float chiClumped = smoothstep(chiM.b - 0.12, chiM.b + 0.12, chiRamp);
  float chiGrassF = (1.0 - chiM.r) * smoothstep(0.70, 0.86, chiM.b) * smoothstep(4.0, 6.0, abs(chiV));
  float chiMudF = smoothstep(0.60, 0.72, chiM.g) * (0.4 + 0.6 * chiM.r) * (1.0 - chiGrassF);
  float chiF = uStrip.z;
  float chiInside = min(min(chiU + chiF, uSize.x + chiF - chiU), uSize.y * 0.5 + chiF - abs(chiV));
  float chiEdge = smoothstep(0.0, chiF, chiInside - chiF * 0.5 + (chiM.b - 0.5) * 1.2);
  float wDirt = chiEdge * chiDirtW * (1.0 - chiGrassF - chiMudF);
  float wMud = chiEdge * chiDirtW * chiMudF;
  float wBank = chiEdge * chiBankW;
  float wSand = chiEdge * chiSandW * (1.0 - chiClumped);
  float wPrairie = 1.0 - wDirt - wMud - wBank - wSand;

  vec4 chiGrit = texture2D(uGrit, chiEN / uGritM);
  vec3 chiMuck = texture2D(uMuckC, chiEN / uSpan.x).rgb;
  vec3 chiSand = texture2D(uSandC, chiEN / uSpan.y).rgb;
  // The grit's height as grain over its own mean, so the dirt averages the
  // recorded tone. Clods catch light, hollows hold shade: about +/-12 %.
  float chiGrain = chiGrit.r / max(uGritMean, 1e-6);
  float chiBroad = 0.93 + 0.14 * chiM.a;
  float chiDirtGrain = mix(1.0, chiGrain, 0.65);
  vec3 chiDirt = mix(uDirtRest, uDirtLane, chiM.r) * chiDirtGrain * chiBroad;
  vec3 chiMud = chiMuck * 0.9;
  float chiBankWet = smoothstep(0.50, 0.80, chiM.g);
  vec3 chiBank = mix(uBankDry * chiDirtGrain * chiBroad, chiMuck, 0.75 * chiBankWet);
  // The sand at a quarter of its grain: the library tile's ripples repeat every
  // 6 m and read as a printed pattern at full strength from any height.
  float chiSandGrain = dot(chiSand, vec3(0.2126, 0.7152, 0.0722)) / max(uSandLuma, 1e-6);
  vec3 chiSandC = uSandTone * mix(1.0, chiSandGrain, 0.25) * mix(1.0, chiGrain, 0.2)
                * (0.90 + 0.20 * chiM.a);
  diffuseColor.rgb = chiPrairie * wPrairie
                   + chiDirt * wDirt + chiMud * wMud + chiBank * wBank + chiSandC * wSand;
  diffuseColor.rgb = min(diffuseColor.rgb, vec3(1.0));
  float chiRough = 1.0 * wPrairie + (0.97 - 0.06 * chiM.r) * wDirt + 0.42 * wMud
                 + mix(0.95, 0.62, chiBankWet) * wBank + 0.93 * wSand;
`;

const NORMAL_FRAGMENT = /* glsl */`
  // Tangent-space relief, blended by the same weights, in a world frame:
  // east is +u of every tile, north is +v (OpenGL normals, flipY'd PNGs).
  // One relief for all four grounds, the grit's, at the strength each holds:
  // full on the dirt, softened on the bank as it wets, a skim on the mud where
  // water has levelled it, and a little on the sand.
  vec2 chiGN = chiGrit.gb * 2.0 - 1.0;
  vec2 chiXY = chiGN * (wDirt + wBank * (1.0 - 0.6 * chiBankWet) + 0.2 * wMud + 0.35 * wSand);
  vec3 chiTn = normalize(vec3(chiXY, 1.0));
  vec3 chiEastV = normalize((viewMatrix * vec4(1.0, 0.0, 0.0, 0.0)).xyz);
  vec3 chiT = normalize(chiEastV - normal * dot(chiEastV, normal));
  vec3 chiB = cross(normal, chiT);
  normal = normalize(chiT * chiTn.x + chiB * chiTn.y + normal * chiTn.z);
`;

/**
 * Build the strip. Resolves to a handle; never throws — a map that does not
 * arrive is a strip that is not drawn, reported on `problems`, and the walk
 * carries on (the smoke holds every page to zero pageerrors).
 */
export async function createGroundStrip({ terrain, assetBase, problems = [] } = {}) {
  const t0 = performance.now();
  const group = new THREE.Group();
  group.name = 'ground_strip';
  const mask = stripMaskPixels();
  const stats = { drawn: false, triangles: 0, textures: 0, gpuBytes: 0,
    fetchesPerFragment: 0, loadMs: 0, maskPx: [mask.w, mask.h] };
  const handle = { group, stats, mask, blocksGrowth: () => false, dispose: () => {} };

  const loader = new THREE.TextureLoader();
  const base = new URL(LIBRARY, assetBase);
  let lib;
  try {
    lib = await Promise.all(SUBSTRATES.map(async (id) => {
      const here = new URL(`${id}/`, base);
      const sheetUrl = new URL('material.json', here).href;
      const res = await fetch(sheetUrl, { cache: 'no-cache' });
      if (!res.ok) throw new Error(`${res.status} — ${sheetUrl}`);
      const sheet = await res.json();
      if (!(Number(sheet.span_m) > 0)) throw new Error(`${id}: material.json states no span_m`);
      const cUrl = new URL(`${id}_basecolor.png`, here).href;
      const colour = await loadMap(loader, cUrl, true);
      return { id, span: Number(sheet.span_m), colour };
    }));
  } catch (err) {
    problems.push(`ground strip: not drawn — ${err.message}`);
    return handle;
  }
  const [muck, sand] = lib;

  // The mask, as a canvas: the "runtime canvas" half of the method.
  const c = document.createElement('canvas');
  c.width = mask.w; c.height = mask.h;
  c.getContext('2d').putImageData(new ImageData(mask.data, mask.w, mask.h), 0, 0);
  const maskTex = new THREE.CanvasTexture(c);
  maskTex.colorSpace = THREE.NoColorSpace;
  maskTex.wrapS = maskTex.wrapT = THREE.ClampToEdgeWrapping;
  const prairie = prairieTexture();
  // The grit tile, the other runtime canvas: fine relief the library lacks.
  const gritData = gritTilePixels();
  const gc = document.createElement('canvas');
  gc.width = gc.height = GRIT_TILE_PX;
  gc.getContext('2d').putImageData(new ImageData(gritData, GRIT_TILE_PX, GRIT_TILE_PX), 0, 0);
  const gritTex = new THREE.CanvasTexture(gc);
  gritTex.colorSpace = THREE.NoColorSpace;
  gritTex.wrapS = gritTex.wrapT = THREE.RepeatWrapping;
  gritTex.anisotropy = 4;
  let gritSum = 0;
  for (let i = 0; i < gritData.length; i += 4) gritSum += gritData[i];
  const gritMean = gritSum / (gritData.length / 4) / 255;

  const F = STRIP.featherM;
  const spanU = STRIP.lengthM + 2 * F, spanV = STRIP.widthM + 2 * F;
  const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 1, metalness: 0 });
  // Lifted a few centimetres and pulled forward in depth, so the terrain under
  // it never wins a fragment; the feather is what hides the join, not a seam.
  mat.polygonOffset = true;
  mat.polygonOffsetFactor = -2;
  mat.polygonOffsetUnits = -2;
  const sandLuma = meanLinearLuma(sand.colour.image);
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, {
      uGround: { value: prairie },
      uPrairieLuma: { value: prairie.userData.meanLinearLuma },
      uMask: { value: maskTex },
      // West feather edge, south feather edge, 1/span along, 1/span across.
      uMaskFrame: { value: new THREE.Vector4(STRIP.e0 - F, STRIP.n0 - spanV / 2, 1 / spanU, 1 / spanV) },
      uGrit: { value: gritTex }, uGritM: { value: GRIT_TILE_M }, uGritMean: { value: gritMean },
      uMuckC: { value: muck.colour }, uSandC: { value: sand.colour },
      uSpan: { value: new THREE.Vector2(muck.span, sand.span) },
      uDirtLane: { value: linearTone(TONES.dirtLane) },
      uDirtRest: { value: linearTone(TONES.dirtRest) },
      uBankDry: { value: linearTone(TONES.bankDry) },
      uSandTone: { value: linearTone(TONES.sand) },
      uSandLuma: { value: sandLuma },
      uBands: { value: new THREE.Vector4(STRIP.dirtEndM, STRIP.sandStartM, STRIP.prairieFromM, STRIP.prairieToM) },
      uStrip: { value: new THREE.Vector3(STRIP.e0, STRIP.n0, F) },
      uSize: { value: new THREE.Vector2(STRIP.lengthM, STRIP.widthM) },
    });
    shader.vertexShader = 'varying vec3 vChiWorld;\n' + shader.vertexShader.replace(
      '#include <begin_vertex>', '#include <begin_vertex>' + WORLD_POS_VERT,
    );
    shader.fragmentShader = FRAGMENT_HEAD + shader.fragmentShader
      .replace('#include <map_fragment>', PRAIRIE_FRAGMENT + STRIP_FRAGMENT)
      .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = chiRough;')
      .replace('#include <normal_fragment_maps>', NORMAL_FRAGMENT);
  };

  // The mesh: a regular grid over the strip and its feather, every vertex on
  // the heightfield the walker stands on.
  const nu = Math.round(spanU / MESH_STEP_M), nv = Math.round(spanV / MESH_STEP_M);
  const pos = new Float32Array((nu + 1) * (nv + 1) * 3);
  let k = 0;
  for (let j = 0; j <= nv; j++) {
    const n = STRIP.n0 - spanV / 2 + j * MESH_STEP_M;
    for (let i = 0; i <= nu; i++) {
      const e = STRIP.e0 - F + i * MESH_STEP_M;
      pos[k++] = e;
      pos[k++] = terrain.surfaceHeight(e, n) + STRIP.liftM;
      pos[k++] = -n;
    }
  }
  const index = [];
  for (let j = 0; j < nv; j++) {
    for (let i = 0; i < nu; i++) {
      const a = j * (nu + 1) + i, b = a + 1, c2 = a + nu + 1, d = c2 + 1;
      index.push(a, b, d, a, d, c2);
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setIndex(index);
  geo.computeVertexNormals();
  const mesh = new THREE.Mesh(geo, mat);
  mesh.name = 'ground_strip_proof';
  mesh.receiveShadow = true;
  mesh.castShadow = false;
  group.add(mesh);

  // The sward is told to leave bare what the shader draws bare, and to thin
  // where it draws the prairie arriving: a plant stands where a seeded draw
  // falls under the prairie weight there.
  const hash = (e, n) => {
    const s = Math.sin(e * 127.1 + n * 311.7) * 43758.5453;
    return s - Math.floor(s);
  };
  handle.blocksGrowth = (e, n) => {
    const { u, v } = stripLocal(e, n);
    const m = maskAt(mask, u, v);
    if (!m) return false;
    return hash(e, n) > stripWeights(u, v, m).prairie;
  };

  const textures = [maskTex, prairie, gritTex, ...lib.map((l) => l.colour)];
  stats.drawn = true;
  stats.triangles = index.length / 3;
  stats.textures = textures.length;
  // Decoded GPU bytes with a full mip chain — arithmetic, as the map's § 5 is.
  stats.gpuBytes = Math.round(textures.reduce((s, t) => {
    const img = t.image;
    return s + (img?.width ?? 0) * (img?.height ?? 0) * 4 * 4 / 3;
  }, 0));
  stats.fetchesPerFragment = 3 /* mask, prairie, grit */ + 2 /* muck, sand colour */;
  stats.loadMs = Math.round(performance.now() - t0);
  stats.maskPxPerM = MASK_PX_PER_M;
  stats.maskSize = maskSize();
  handle.dispose = () => { geo.dispose(); mat.dispose(); for (const t of textures) t.dispose(); };
  return handle;
}

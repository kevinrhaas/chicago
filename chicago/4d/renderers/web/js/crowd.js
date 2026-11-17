// SPDX-License-Identifier: GPL-3.0-or-later
/**
 * crowd.js — the town at a distance: middle-distance people instanced on one shared body per
 * dress, and far people as impostor cards from one shared atlas (T-3555).
 *
 * The owner, 2026-11-10: every device keeps the living town; people, horses, carriages and
 * wagons are core and are never dropped at lower settings, a phone's included: lower
 * resolution or blur instead. And 2026-11-12, consolidating the crowd and traffic work into
 * T-3555: "a living town at a phone's cost". Until this, a person was either a whole skinned,
 * dressed, haired figure (humans.js), out to DRAW_M, or nothing: a street seen from a block
 * away was empty, and the town's carded thousands (1835's 2,830, 1812's 520, 1904's 397 in
 * data/humans/inside_<scene>.json) were drawn only the handful at a time human-days.js builds
 * near the visitor. So a town of people going about their day was a few figures and a void.
 *
 * THREE TIERS, ONE PERSON. Who is out and where is still the day's (human-days.js; this file
 * only reads it, by `days.outdoors`) and the figure's (humans.js actors, by their logical
 * place). This file draws the people nobody else draws:
 *
 *   near     the whole figure, humans.js: anyone built (a record, a resident out near the
 *            visitor), to DRAW_M. Untouched here.
 *   middle   people out of doors and not built, MID[tier] metres off: each dress (asset) is ONE
 *            shared body, its LOD3 figure merged and clustered (CLUSTER_M), drawn as one
 *            InstancedMesh, animated on the GPU from a vertex-animation texture baked from the
 *            asset's own walk clip (WALK_FRAMES frames) and its idle. Per person: place,
 *            heading, height, skin (their looks' complexion), hair (their looks' colour) and a
 *            small shade of the cloth, so a street is not one man repeated.
 *   far      beyond MID's far edge to FAR[tier]: a card, a quad turned to the eye, its picture
 *            from one atlas baked here from the same shared bodies (CARD_YAWS headings x
 *            idle and two strides), so the card and the middle body are the same picture.
 *            And every built figure past its drawing range (humans.js hides it at DRAW_M) is a
 *            card too, so a figure walking away never vanishes.
 *
 * NO POP. Each tier boundary is a dithered cross-fade, in time (FADE_S, CROSS_S): the middle body dissolves
 * in as the card dissolves out, by complementary screen-door patterns, so at no distance is a
 * person drawn twice or not at all. The near edge of the middle tier is a fade too (a person not
 * built who is very near the visitor goes in through their door, as human-days.js's own far
 * people do; or, if the visitor comes on them, dissolves; the day's residents near the visitor
 * are built in their turn, as before).
 *
 * WHAT IT COSTS (docs/measurements/T-3555-crowd.json is the measured row): per scene one atlas
 * (CARD_CELL[tier] pixels a picture), and per dress a few hundred KB (its clustered body and
 * its animation texture); one draw per dress in use for the middle tier, one draw for every
 * card; no skinning on the CPU, no shadow, no picking. Caps (CAPS[tier]) bound the counts.
 *
 * Reconstructed, all of it, as the people's days are: where a far person stands or walks is
 * their day's; the shade of their cloth is a small seeded variation on their dress's own
 * colours (liberty L-crowd-3555), never a colour the dress does not have.
 */
import * as THREE from 'three';
import { clone as cloneSkinned } from 'three/addons/utils/SkeletonUtils.js';
import { enuToWorld } from './terrain.js';
import { COMPLEXION_TINT } from './human-looks.js';
import { HAIR_COLOURS } from './human-hair-styles.js';

/** Middle tier, metres from the eye: [near edge, far edge], by scene detail. */
export const MID = Object.freeze({ full: Object.freeze([28, 110]), balanced: Object.freeze([28, 90]), light: Object.freeze([28, 70]) });
/** Far tier's far edge (cards), metres. */
export const FAR = Object.freeze({ full: 600, balanced: 450, light: 320 });
/** How many of each are drawn at most; the nearest first. */
export const CAPS = Object.freeze({
  full: Object.freeze({ mid: 160, far: 1400 }),
  balanced: Object.freeze({ mid: 110, far: 900 }),
  light: Object.freeze({ mid: 60, far: 500 }),
});
/**
 * Seconds a person takes to dissolve in or out (`FADE_S`) and to cross from the middle body
 * to the card (`CROSS_S`). A fade is in TIME, not across a band of distance, so nobody stands
 * half-dissolved for as long as the visitor stands still; and HYST_M keeps someone on a
 * boundary from flickering across it.
 */
export const FADE_S = 0.6;
export const CROSS_S = 0.5;
export const HYST_M = 3;
/** The card picture's size, pixels (w x h, one person standing in a 1 m x 2 m frame). */
export const CARD_CELL = Object.freeze({ full: Object.freeze([32, 64]), balanced: Object.freeze([32, 64]), light: Object.freeze([24, 48]) });
/** Headings a card is baked from, and the poses: idle, then two strides of the walk. */
export const CARD_YAWS = 8;
export const CARD_POSES = 3;
/** Frames of the walk clip in the animation texture (the idle is one more). */
export const WALK_FRAMES = 8;
/** The clustering cell a shared body is merged on, metres, by detail. */
export const CLUSTER_M = Object.freeze({ full: 0.07, balanced: 0.08, light: 0.1 });
/** An inner layer's point this near an outer layer's kept point is merged into it (m). */
export const MERGE_M = 0.035;
/** Each layer stands this much further out than the one under it (m, along its normal), so
 *  a body or shirt merged coarsely never shows through the coat over it at a distance. */
export const LAYER_LIFT_M = 0.004;
/** Walking pace of a far person, m/s; their clip is played to it at STRIDE_M a cycle. */
export const PACE_M_S = 1.25;
export const STRIDE_M = 1.45;
/** How often the people out of doors are read again (s), and how far the eye may move first. */
export const READ_S = 2.5;
export const READ_MOVE_M = 25;
/** How often who is in which tier is sorted again (s), and how far the eye may move first (m). */
export const SORT_S = 0.4;
export const SORT_MOVE_M = 4;
/** How far a person may go before their ground is read again (m): a middle body, a card. */
export const GROUND_MID_M = 0.6;
export const GROUND_CARD_M = 3;

const DRAW_ORDER = [/garment_outer/, /headwear/, /garment_upper/, /^accessory/, /garment_lower/, /footwear/, /^hair/, /^skin/];
const priorityOf = (name) => { const i = DRAW_ORDER.findIndex((re) => re.test(name ?? '')); return i < 0 ? 4 : i; };
const regionOf = (name) => (/^skin/.test(name ?? '') ? 1 : /^hair/.test(name ?? '') ? 2 : 0);
const DEFAULT_SKIN = [1, 1, 1];
const DEFAULT_HAIR = HAIR_COLOURS.mid_brown ?? [0.062, 0.036, 0.02];

/** FNV-1a into a 0-1 number: the same shade for the same person on every load. */
export function hash01(key) {
  let h = 2166136261 >>> 0;
  const s = String(key);
  for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  h ^= h >>> 13; h = Math.imul(h, 0x5bd1e995) >>> 0; h ^= h >>> 15;
  return (h >>> 0) / 4294967296;
}

/**
 * Where a person `d` metres off is headed: `v` 1 drawn by this layer at all, 0 not; `t` 0 the
 * middle body, 1 the card. `was` is what they were headed for last time ({v, t}), held across a
 * boundary by HYST_M. `built`: a figure humans.js draws itself out to `drawM`; it is a card only
 * past that. Pure, so tools/test_crowd.mjs walks every boundary.
 */
export function tierTargets(d, tier = 'full', { built = false, drawM = 140, was = null } = {}) {
  const [m0, m1] = MID[tier] ?? MID.full, f1 = FAR[tier] ?? FAR.full;
  if (!(d >= 0)) return { v: 0, t: was?.t ?? 0 };
  if (built) return { v: d > drawM && d < f1 ? 1 : 0, t: 1 };
  const shownNow = was?.v > 0, farNow = was?.t > 0;
  const v = d >= (shownNow ? m0 - HYST_M : m0) && d < (shownNow ? f1 + HYST_M : f1) ? 1 : 0;
  const t = d > (farNow ? m1 - HYST_M : m1 + HYST_M) ? 1 : 0;
  return { v, t };
}

/** The weights the shaders draw at, from the eased `v` and `t`: complementary, never both whole. */
export function tierWeights(v, t) { return { mid: v * (1 - t), far: v * t }; }

/** The 4x4 ordered-dither threshold shared by both tiers' shaders (complementary fades). */
const DITHER_GLSL = /* glsl */`
float crowdDither(vec2 p) {
  ivec2 q = ivec2(mod(p, 4.0));
  int i = q.x + q.y * 4;
  float m[16] = float[16](0.,8.,2.,10.,12.,4.,14.,6.,3.,11.,1.,9.,15.,7.,13.,5.);
  return (m[i] + 0.5) / 16.0;
}`;

/**
 * Average linear colour of each textured material's picture, on the GPU (a compressed picture
 * cannot be read back otherwise): one pixel each, sampled over a grid at a coarse mip, weighted
 * by alpha. Returns Map(texture -> [r, g, b]).
 */
async function measureTextures(renderer, textures) {
  const out = new Map();
  if (!renderer || !textures.size) return out;
  const list = [...textures];
  // One pixel a texture, in one row, read back without waiting on the frame (a fence: three's
  // readRenderTargetPixelsAsync), so a dress joining the crowd never stalls the frame.
  const rt = new THREE.WebGLRenderTarget(list.length, 1, { type: THREE.UnsignedByteType, depthBuffer: false });
  const material = new THREE.ShaderMaterial({
    uniforms: { map: { value: null } },
    vertexShader: 'void main() { gl_Position = vec4(position.xy, 0.0, 1.0); }',
    fragmentShader: /* glsl */`
      uniform sampler2D map;
      void main() {
        vec3 sum = vec3(0.0); float w = 0.0;
        for (int y = 0; y < 16; y++) for (int x = 0; x < 16; x++) {
          vec4 c = textureLod(map, (vec2(x, y) + 0.5) / 16.0, 3.0);
          sum += c.rgb * c.a; w += c.a;
        }
        vec3 avg = w > 0.0 ? sum / w : vec3(0.0);
        gl_FragColor = vec4(sqrt(clamp(avg, 0.0, 1.0)), 1.0);
      }`,
    depthTest: false, depthWrite: false,
  });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), material);
  quad.frustumCulled = false;
  const scene = new THREE.Scene(); scene.add(quad);
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const px = new Uint8Array(4 * list.length);
  try {
    const t0 = performance.now();
    const prev = renderer.getRenderTarget();
    rt.scissorTest = true;
    list.forEach((tex, i) => {
      material.uniforms.map.value = tex;
      rt.viewport.set(i, 0, 1, 1); rt.scissor.set(i, 0, 1, 1);
      renderer.setRenderTarget(rt);
      renderer.render(scene, cam);
    });
    renderer.setRenderTarget(prev);
    out.ms = performance.now() - t0;
    await (renderer.readRenderTargetPixelsAsync
      ? renderer.readRenderTargetPixelsAsync(rt, 0, 0, list.length, 1, px)
      : renderer.readRenderTargetPixels(rt, 0, 0, list.length, 1, px));
    list.forEach((tex, i) => out.set(tex, [0, 1, 2].map((k) => (px[i * 4 + k] / 255) ** 2)));
  } catch { /* unmeasured: the material's colour alone */ }
  rt.dispose(); material.dispose(); quad.geometry.dispose();
  return out;
}

/**
 * ONE SHARED BODY. `gltf` is an asset's LOD3 figure. Its meshes are posed by its own clips, merged
 * into one, and clustered on a CLUSTER_M grid (outer garment first, so the cloth over a body is
 * what a merged point wears); each kept point's place is then read in WALK_FRAMES frames of the
 * walk and one of the idle, into an animation texture (half floats, RGBA). Colour is each source
 * material's colour times its picture's average (`measured`); region marks skin and hair, which
 * a person's own looks tint.
 * Returns { geometry, vat: DataTexture, reps, height, walkSeconds } or null.
 */
export function buildCrowdBody(gltf, { cell = CLUSTER_M.full, measured = new Map() } = {}) {
  if (!gltf?.scene) return null;
  const root = cloneSkinned(gltf.scene);
  root.position.set(0, 0, 0); root.rotation.set(0, 0, 0); root.scale.set(1, 1, 1);
  const clips = gltf.animations ?? [];
  const walk = clips.find((c) => c.name === 'walk') ?? null;
  const idle = clips.find((c) => c.name === 'idle') ?? clips.find((c) => /^idle/.test(c.name)) ?? null;
  const mixer = new THREE.AnimationMixer(root);
  const meshes = [];
  root.traverse((o) => {
    if (!o.isMesh || !o.geometry?.attributes?.position || o.visible === false) return;
    const m = Array.isArray(o.material) ? o.material[0] : o.material;
    if (!m || m.visible === false || /eyes__|_eyes_/.test(`${m.name} ${o.name}`)) return;
    meshes.push({ mesh: o, material: m, priority: priorityOf(m.name), region: regionOf(m.name) });
  });
  if (!meshes.length) return null;
  meshes.sort((a, b) => a.priority - b.priority);
  const v = new THREE.Vector3();
  const pose = (clip, t) => {
    mixer.stopAllAction();
    if (clip) { const a = mixer.clipAction(clip); a.play(); mixer.setTime(t); }
    root.updateMatrixWorld(true);
    for (const { mesh } of meshes) if (mesh.isSkinnedMesh) mesh.skeleton.update();
  };
  const placeOf = (entry, i, target) => entry.mesh.getVertexPosition(i, target).applyMatrix4(entry.mesh.matrixWorld);
  // Cluster at rest (the idle's first frame).
  pose(idle, 0);
  // A point of an inner layer (the body under a coat, a shirt under a waistcoat) within a cell
  // of a point an outer layer already keeps is merged INTO that outer point, so the inner
  // layer's triangles fold away under the outer and never show through it at a cell's edge.
  const cells = new Map();
  const reps = [];          // [{ entry, index }]
  const repPos = [];        // x, y, z of each kept point
  const repOf = meshes.map(({ mesh }) => new Int32Array(mesh.geometry.attributes.position.count).fill(-1));
  const cellKey = (x, y, z) => `${x},${y},${z}`;
  meshes.forEach((entry, k) => {
    const n = entry.mesh.geometry.attributes.position.count;
    for (let i = 0; i < n; i++) {
      placeOf(entry, i, v);
      const cx = Math.floor(v.x / cell), cy = Math.floor(v.y / cell), cz = Math.floor(v.z / cell);
      let best = -1, bestD = MERGE_M * MERGE_M;
      for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++) {
        const r = cells.get(cellKey(cx + dx, cy + dy, cz + dz));
        if (r === undefined || reps[r].entry.priority >= entry.priority) continue;
        const ex = repPos[r * 3] - v.x, ey = repPos[r * 3 + 1] - v.y, ez = repPos[r * 3 + 2] - v.z;
        const dd = ex * ex + ey * ey + ez * ez;
        if (dd < bestD) { bestD = dd; best = r; }
      }
      if (best < 0) {
        const key = cellKey(cx, cy, cz);
        best = cells.get(key) ?? -1;
        if (best < 0) { best = reps.length; reps.push({ entry, index: i }); repPos.push(v.x, v.y, v.z); cells.set(key, best); }
      }
      repOf[k][i] = best;
    }
  });
  const tris = [], seen = new Set();
  meshes.forEach(({ mesh }, k) => {
    const idx = mesh.geometry.index;
    const n = idx ? idx.count : mesh.geometry.attributes.position.count;
    for (let t = 0; t + 2 < n; t += 3) {
      const a = repOf[k][idx ? idx.getX(t) : t], b = repOf[k][idx ? idx.getX(t + 1) : t + 1], c = repOf[k][idx ? idx.getX(t + 2) : t + 2];
      if (a === b || b === c || a === c) continue;
      const key = [a, b, c].sort((x, y) => x - y).join(',');
      if (seen.has(key)) continue;
      seen.add(key); tris.push(a, b, c);
    }
  });
  const count = reps.length;
  const frames = WALK_FRAMES + 1;
  const vatW = Math.min(count * frames, 2048);
  const vatH = Math.ceil((count * frames) / vatW);
  const data = new Uint16Array(vatW * vatH * 4);
  const rest = new Float32Array(count * 3);
  const writeFrame = (f) => {
    for (let r = 0; r < count; r++) {
      placeOf(reps[r].entry, reps[r].index, v);
      const o = (f * count + r) * 4;
      data[o] = THREE.DataUtils.toHalfFloat(v.x); data[o + 1] = THREE.DataUtils.toHalfFloat(v.y);
      data[o + 2] = THREE.DataUtils.toHalfFloat(v.z); data[o + 3] = THREE.DataUtils.toHalfFloat(1);
      if (f === WALK_FRAMES) { rest[r * 3] = v.x; rest[r * 3 + 1] = v.y; rest[r * 3 + 2] = v.z; }
    }
  };
  const walkSeconds = walk?.duration > 0 ? walk.duration : 1;
  for (let f = 0; f < WALK_FRAMES; f++) { pose(walk ?? idle, (walkSeconds * f) / WALK_FRAMES); writeFrame(f); }
  pose(idle, 0); writeFrame(WALK_FRAMES);
  mixer.stopAllAction(); mixer.uncacheRoot(root);
  let height = 0;
  for (let r = 0; r < count; r++) height = Math.max(height, rest[r * 3 + 1]);
  const colour = new Float32Array(count * 3), region = new Float32Array(count), lift = new Float32Array(count);
  const c = new THREE.Color();
  reps.forEach(({ entry }, r) => {
    const m = entry.material;
    c.copy(m.color ?? c.setRGB(1, 1, 1));
    const avg = m.map ? measured.get(m.map) : null;
    if (avg) c.multiply(new THREE.Color().setRGB(avg[0], avg[1], avg[2], THREE.LinearSRGBColorSpace));
    colour[r * 3] = c.r; colour[r * 3 + 1] = c.g; colour[r * 3 + 2] = c.b;
    region[r] = entry.region;
    lift[r] = (DRAW_ORDER.length - entry.priority) * LAYER_LIFT_M;
  });
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.BufferAttribute(rest, 3));
  geometry.setAttribute('color', new THREE.BufferAttribute(colour, 3));
  geometry.setAttribute('aRegion', new THREE.BufferAttribute(region, 1));
  geometry.setAttribute('aLift', new THREE.BufferAttribute(lift, 1));
  geometry.setIndex(count > 65535 ? new THREE.Uint32BufferAttribute(tris, 1) : new THREE.Uint16BufferAttribute(tris, 1));
  geometry.computeVertexNormals();
  geometry.computeBoundingSphere();
  const vat = new THREE.DataTexture(data, vatW, vatH, THREE.RGBAFormat, THREE.HalfFloatType);
  vat.minFilter = vat.magFilter = THREE.NearestFilter;
  vat.generateMipmaps = false;
  vat.needsUpdate = true;
  return { geometry, vat, reps: count, triangles: tris.length / 3, height, walkSeconds, vatBytes: data.byteLength };
}

/** The vertex half of the animation texture, for any lit or unlit material. */
function vatVertex(shader, body, { instanced = true } = {}) {
  shader.uniforms.uVat = { value: body.vat };
  shader.uniforms.uVatW = { value: body.vat.image.width };
  shader.uniforms.uReps = { value: body.reps };
  shader.uniforms.uFrame = shader.uniforms.uFrame ?? { value: WALK_FRAMES };
  shader.vertexShader = shader.vertexShader
    .replace('#include <common>', `#include <common>
uniform highp sampler2D uVat; uniform float uVatW; uniform float uReps; uniform float uFrame;
attribute float aRegion; attribute float aLift;
${instanced ? 'attribute vec4 iA; attribute vec3 iSkin; attribute vec3 iHair; attribute float iCloth;' : ''}
varying float vCrowdFade;
vec3 crowdVat(float f) {
  float k = f * uReps + float(gl_VertexID);
  return texelFetch(uVat, ivec2(int(mod(k, uVatW)), int(floor(k / uVatW))), 0).xyz;
}`)
    .replace('#include <begin_vertex>', instanced
      ? 'vec3 transformed = mix(crowdVat(iA.x), crowdVat(iA.y), iA.z) + normal * aLift; vCrowdFade = iA.w;'
      : 'vec3 transformed = crowdVat(uFrame) + normal * aLift; vCrowdFade = 1.0;')
    .replace('#include <color_vertex>', `#include <color_vertex>
${instanced ? 'vColor.rgb = aRegion > 1.5 ? iHair : (aRegion > 0.5 ? vColor.rgb * iSkin : vColor.rgb * iCloth);'
    : 'if (aRegion > 1.5) vColor.rgb = vec3(' + DEFAULT_HAIR.map((x) => x.toFixed(4)).join(', ') + ');'}`);
}

function crowdFragment(shader, mode) {
  // mode 'mid': keep where the dither is below the fade; 'card': where it is at or above 1 - fade.
  shader.fragmentShader = shader.fragmentShader
    .replace('#include <common>', `#include <common>\nvarying float vCrowdFade;\n${DITHER_GLSL}`)
    .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
${mode === 'card' ? 'if (crowdDither(gl_FragCoord.xy) < 1.0 - vCrowdFade) discard;' : 'if (crowdDither(gl_FragCoord.xy) >= vCrowdFade) discard;'}`);
}

/** The middle tier's material for one shared body. */
function midMaterial(body) {
  const m = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.85, metalness: 0, side: THREE.DoubleSide });
  m.name = 'crowd_mid';
  m.onBeforeCompile = (shader) => { vatVertex(shader, body); crowdFragment(shader, 'mid'); };
  m.customProgramCacheKey = () => 'crowd-mid-v1';
  return m;
}

/** The bake's unlit material: the body as its colours, posed at uFrame. */
function bakeMaterial(body) {
  const uFrame = { value: WALK_FRAMES };
  const m = new THREE.MeshBasicMaterial({ vertexColors: true, side: THREE.DoubleSide });
  m.onBeforeCompile = (shader) => { shader.uniforms.uFrame = uFrame; vatVertex(shader, body, { instanced: false }); };
  m.customProgramCacheKey = () => 'crowd-bake-v1';
  m.userData.uFrame = uFrame;
  return m;
}

/**
 * The far tier's card material: a billboard turned about the vertical, its picture the one of
 * `yaws` baked headings the eye sees it from. Instanced by `iPos` (x, y, z, yaw) and `iCell`
 * (scale, first cell, fade, shade). Shared with the distant teams (traffic-cards.js).
 */
export function cardMaterial(atlas, cols, rows, yaws = CARD_YAWS) {
  const m = new THREE.MeshLambertMaterial({ map: atlas, alphaTest: 0.45, side: THREE.DoubleSide });
  m.name = 'crowd_card';
  m.onBeforeCompile = (shader) => {
    shader.uniforms.uGrid = { value: new THREE.Vector2(cols, rows) };
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
uniform vec2 uGrid;
attribute vec4 iPos; attribute vec4 iCell;
varying float vCrowdFade; varying float vCrowdShade;
vec2 crowdToCam() { vec3 t = cameraPosition - iPos.xyz; return normalize(t.xz + vec2(1e-4, 0.0)); }`)
      .replace('#include <uv_vertex>', `#include <uv_vertex>
{
  vec2 tc = crowdToCam();
  float cy = cos(iPos.w), sy = sin(iPos.w);
  float lx = tc.x * cy - tc.y * sy, lz = tc.x * sy + tc.y * cy;
  float k = mod(floor(atan(lx, lz) / (6.2831853 / ${yaws}.0) + 0.5) + ${yaws}.0, ${yaws}.0);
  float cell = iCell.y + k;
  vec2 cr = vec2(mod(cell, uGrid.x), floor(cell / uGrid.x));
  vMapUv = (cr + uv) / uGrid;
  vCrowdFade = iCell.z; vCrowdShade = iCell.w;
}`)
      .replace('#include <defaultnormal_vertex>', `#include <defaultnormal_vertex>
{ vec2 tn = crowdToCam(); transformedNormal = normalize(mat3(viewMatrix) * normalize(vec3(tn.x, 0.8, tn.y))); }`)
      .replace('#include <project_vertex>', `
vec2 tq = crowdToCam();
vec3 right = vec3(tq.y, 0.0, -tq.x);
vec3 crowdWorld = iPos.xyz + right * position.x * iCell.x + vec3(0.0, position.y * iCell.x, 0.0);
vec4 mvPosition = viewMatrix * vec4(crowdWorld, 1.0);
gl_Position = projectionMatrix * mvPosition;`)
      .replace('#include <worldpos_vertex>', 'vec4 worldPosition = vec4(crowdWorld, 1.0);');
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>\nvarying float vCrowdFade; varying float vCrowdShade;\n${DITHER_GLSL}`)
      .replace('#include <alphatest_fragment>', `#include <alphatest_fragment>
if (crowdDither(gl_FragCoord.xy) < 1.0 - vCrowdFade) discard;
diffuseColor.rgb *= vCrowdShade;`);
  };
  m.customProgramCacheKey = () => `crowd-card-v1-${yaws}`;
  return m;
}

/**
 * THE LAYER. `humans` is humans.js's layer (its built figures, its asset store, Show › People
 * and a jaunt's hold); `days` is human-days.js's (`outdoors`, the people out and not built).
 * `renderer` bakes the bodies' pictures into the atlas; without one (a test), nothing is baked
 * and the far tier stays empty, the middle drawn all the same.
 */
export function createCrowd({ humans, days = null, renderer = null, tier = 'full', heightAt = () => 0,
  drawM = 140, problems = [], assetIds = [] } = {}) {
  const group = new THREE.Group();
  group.name = 'crowd';
  const store = humans?.assets ?? null;
  const bodies = new Map();         // assetId -> { status, body, mesh, attrs, row }
  const rows = new Map();           // assetId -> atlas row
  for (const id of assetIds) if (id && !rows.has(id)) rows.set(id, rows.size);
  let shown = true, disposed = false;
  let kit = null;
  void store?.variation?.().then((v) => { kit = v; }, () => {});
  const stats = { mid: 0, far: 0, outdoors: 0, built: 0, bodies: 0, baked: 0, midTriangles: 0, bytes: 0, reads: 0, ms: 0, readMs: 0, bakeMs: 0, buildMs: 0, groundMs: 0 };
  const people = new Map();         // key -> presence
  let readAt = 0, readFrom = null, clock = 0;

  // ── the atlas: one row per dress, CARD_YAWS x CARD_POSES pictures a row ─────────────────
  let atlas = null, cardMesh = null, cardAttrs = null, atlasCell = null, atlasRows = 0;
  const cardCols = CARD_YAWS * CARD_POSES;
  function ensureAtlas() {
    const want = CARD_CELL[tier] ?? CARD_CELL.full;
    const need = Math.max(1, rows.size);
    if (atlas && atlasCell[0] === want[0] && atlasRows >= need) return true;
    if (!renderer) return false;
    disposeAtlas();
    atlasCell = want; atlasRows = need;
    atlas = new THREE.WebGLRenderTarget(cardCols * want[0], need * want[1], {
      type: THREE.UnsignedByteType, generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter,
    });
    atlas.texture.colorSpace = THREE.SRGBColorSpace;
    atlas.texture.name = 'crowd_atlas';
    const cap = (CAPS[tier] ?? CAPS.full).far;
    const quad = new THREE.PlaneGeometry(1, 2).translate(0, 1, 0);
    const geometry = new THREE.InstancedBufferGeometry();
    geometry.index = quad.index;
    geometry.setAttribute('position', quad.attributes.position);
    geometry.setAttribute('normal', quad.attributes.normal);
    geometry.setAttribute('uv', quad.attributes.uv);
    cardAttrs = { pos: new THREE.InstancedBufferAttribute(new Float32Array(cap * 4), 4), cell: new THREE.InstancedBufferAttribute(new Float32Array(cap * 4), 4), cap };
    cardAttrs.pos.setUsage(THREE.DynamicDrawUsage); cardAttrs.cell.setUsage(THREE.DynamicDrawUsage);
    geometry.setAttribute('iPos', cardAttrs.pos);
    geometry.setAttribute('iCell', cardAttrs.cell);
    geometry.instanceCount = 0;
    cardMesh = new THREE.Mesh(geometry, cardMaterial(atlas.texture, cardCols, need));
    cardMesh.name = 'crowd_cards';
    cardMesh.frustumCulled = false;
    // Never picked: a far figure or team is a picture, not a thing to aim at or walk into.
    cardMesh.raycast = () => {};
    cardMesh.castShadow = false; cardMesh.receiveShadow = false;
    group.add(cardMesh);
    for (const b of bodies.values()) b.baked = false;
    return true;
  }
  function disposeAtlas() {
    if (cardMesh) { group.remove(cardMesh); cardMesh.geometry.dispose(); cardMesh.material.dispose(); cardMesh = null; }
    atlas?.dispose(); atlas = null; cardAttrs = null;
  }

  /** Bake one dress's pictures into its atlas row: unlit, its own colours. */
  function bake(id, body) {
    if (!ensureAtlas()) return false;
    const row = rows.get(id);
    if (row == null || row >= atlasRows) return false;
    const material = bakeMaterial(body);
    const mesh = new THREE.Mesh(body.geometry, material);
    mesh.frustumCulled = false;
    const scene = new THREE.Scene(); scene.add(mesh);
    const cam = new THREE.OrthographicCamera(-0.5, 0.5, 1, -1, 0.1, 20);
    const prevTarget = renderer.getRenderTarget();
    const prevClear = renderer.getClearColor(new THREE.Color()), prevAlpha = renderer.getClearAlpha();
    const prevAuto = renderer.autoClear;
    const [cw, ch] = atlasCell;
    const strides = [WALK_FRAMES, 1, 1 + WALK_FRAMES / 2];
    try {
      renderer.setClearColor(0x000000, 0);
      renderer.autoClear = true;
      for (let p = 0; p < CARD_POSES; p++) {
        material.userData.uFrame.value = strides[p];
        for (let k = 0; k < CARD_YAWS; k++) {
          const a = (k * Math.PI * 2) / CARD_YAWS;
          cam.position.set(Math.sin(a) * 6, 1, Math.cos(a) * 6);
          cam.lookAt(0, 1, 0);
          cam.updateMatrixWorld();
          const x = (p * CARD_YAWS + k) * cw, y = row * ch;
          atlas.viewport.set(x, y, cw, ch);
          atlas.scissor.set(x, y, cw, ch);
          atlas.scissorTest = true;
          renderer.setRenderTarget(atlas);
          renderer.render(scene, cam);
        }
      }
    } catch (err) { problems.push(`crowd: ${id} could not be baked (${err?.message ?? err})`); }
    atlas.scissorTest = false;
    atlas.viewport.set(0, 0, atlas.width, atlas.height);
    atlas.scissor.set(0, 0, atlas.width, atlas.height);
    renderer.setRenderTarget(prevTarget);
    renderer.setClearColor(prevClear, prevAlpha);
    renderer.autoClear = prevAuto;
    material.dispose();
    stats.baked++;
    return true;
  }

  /** Load, merge and animate one dress's shared body, once; then its InstancedMesh. */
  function bodyFor(id) {
    let b = bodies.get(id);
    if (b) return b;
    if (!rows.has(id)) rows.set(id, rows.size);
    b = { status: 'loading', body: null, mesh: null, attrs: null, baked: false };
    bodies.set(id, b);
    if (!store) { b.status = 'failed'; return b; }
    store.acquire(id, 3).then(async (gltf) => {
      if (disposed || bodies.get(id) !== b) return;
      const textures = new Set();
      gltf.scene.traverse((o) => { const m = o.material; for (const x of Array.isArray(m) ? m : [m]) if (x?.map) textures.add(x.map); });
      const measured = await measureTextures(renderer, textures);
      stats.measureMs = measured.ms ?? 0;
      // Dropped while it loaded (the detail changed): the new detail's own body takes its place.
      if (disposed || bodies.get(id) !== b) return;
      const k0 = performance.now();
      try {
        const body = buildCrowdBody(gltf, { cell: CLUSTER_M[tier] ?? CLUSTER_M.full, measured });
        if (!body) throw Error('no body');
        b.body = body;
        b.status = 'ready';
        mountMid(b);
        stats.bodies++;
        stats.buildMs = performance.now() - k0;
      } catch (err) { b.status = 'failed'; problems.push(`crowd: ${id} could not be merged (${err?.message ?? err})`); }
    }, (err) => { b.status = 'failed'; problems.push(`crowd: ${id} did not load (${err?.message ?? err})`); })
      .finally(() => store.release(id, 3));
    return b;
  }

  function mountMid(b) {
    const cap = (CAPS[tier] ?? CAPS.full).mid;
    const geometry = new THREE.InstancedBufferGeometry();
    for (const [k, a] of Object.entries(b.body.geometry.attributes)) geometry.setAttribute(k, a);
    geometry.index = b.body.geometry.index;
    const mk = (n) => { const a = new THREE.InstancedBufferAttribute(new Float32Array(cap * n), n); a.setUsage(THREE.DynamicDrawUsage); return a; };
    b.attrs = { a: mk(4), skin: mk(3), hair: mk(3), cloth: mk(1), m: mk(16), cap };
    geometry.setAttribute('iA', b.attrs.a);
    geometry.setAttribute('iSkin', b.attrs.skin);
    geometry.setAttribute('iHair', b.attrs.hair);
    geometry.setAttribute('iCloth', b.attrs.cloth);
    geometry.instanceCount = 0;
    const mesh = new THREE.InstancedMesh(geometry, midMaterial(b.body), cap);
    mesh.count = 0;
    mesh.visible = false;
    mesh.name = 'crowd_mid';
    mesh.frustumCulled = false;
    // Never picked: a far figure or team is a picture, not a thing to aim at or walk into.
    mesh.raycast = () => {};
    mesh.castShadow = false; mesh.receiveShadow = false;
    b.mesh = mesh;
    group.add(mesh);
  }

  /** A person's own tints: skin by their complexion, hair by its colour, a shade of cloth. */
  function looksOf(key) {
    const looks = kit?.persons?.[key]?.looks ?? null;
    const skin = COMPLEXION_TINT[looks?.complexion?.drawn] ?? DEFAULT_SKIN;
    const hair = HAIR_COLOURS[looks?.hair?.drawn] ?? DEFAULT_HAIR;
    const scale = Number.isFinite(looks?.height_scale) ? Math.min(1.08, Math.max(0.92, looks.height_scale)) : 0.97 + hash01(`h:${key}`) * 0.06;
    return { skin, hair, cloth: 0.86 + hash01(`c:${key}`) * 0.26, scale, looked: !!kit };
  }

  /** Read who is out: the day's people not built, and built figures past their range. */
  function read(v) {
    readAt = clock; readFrom = { e: v.e, n: v.n }; stats.reads++;
    const far = FAR[tier] ?? FAR.full;
    const seen = new Set();
    const keep = (key, make) => {
      seen.add(key);
      let p = people.get(key);
      if (!p) { p = make(); people.set(key, p); }
      return p;
    };
    let outdoors = [];
    try { outdoors = days?.outdoors?.(v, far, (CAPS[tier] ?? CAPS.full).far + (CAPS[tier] ?? CAPS.full).mid) ?? []; } catch (err) { problems.push(`crowd: ${err?.message ?? err}`); }
    stats.outdoors = outdoors.length;
    // A household out at its door together shares one point (their day's `front`): stood in a
    // ring about it, turned in, as human-days.js stands a talk's company (ringAbout), not in
    // one another.
    const atPoint = new Map();
    for (const o of outdoors) {
      const k = `${Math.round(o.at.e * 4)},${Math.round(o.at.n * 4)}`;
      let list = atPoint.get(k);
      if (!list) atPoint.set(k, list = []);
      list.push(o);
    }
    for (const list of atPoint.values()) {
      const k = list.length;
      const r = k < 2 ? 0 : Math.max(0.6, 0.75 / (2 * Math.sin(Math.PI / k)));
      const base = k < 2 ? 0 : hash01(`ring:${list[0].person}`) * Math.PI * 2;
      list.forEach((o, i) => {
        const b = base + (Math.PI * 2 * i) / Math.max(1, k);
        const de = r * Math.sin(b), dn = r * Math.cos(b);
        const from = { e: o.at.e + de, n: o.at.n + dn };
        const heading = k < 2 ? o.at.heading_deg : ((b * 180) / Math.PI + 180) % 360;
        const p = keep(`d:${o.person}`, () => ({ key: o.person, assetId: o.asset_id, built: false, e: from.e, n: from.n,
          heading, y: null, phase: hash01(`p:${o.person}`), walk: 0 }));
        p.assetId = o.asset_id;
        // A new place (the hour moved them): there at once; they are far off.
        if (!p.from || p.from.e !== from.e || p.from.n !== from.n) {
          p.from = from; p.e = from.e; p.n = from.n; p.heading = heading; p.rest = heading; p.y = null; p.len = null;
        }
        const to = o.activity === 'walk' && o.to ? { e: o.to.e + de, n: o.to.n + dn } : null;
        if ((to?.e ?? null) !== (p.to?.e ?? null) || (to?.n ?? null) !== (p.to?.n ?? null)) {
          p.to = to; p.len = null;
          if (!to) { p.e = p.from.e; p.n = p.from.n; p.heading = p.rest; }
        }
      });
    }
    let built = 0;
    for (const a of humans?.actors ?? []) {
      if (!a || a.disposed || a.indoors || a.inRange || humans.isHeld?.(a) || !a.instance?.appearance?.asset_id) continue;
      if (Math.hypot(a.e - v.e, a.n - v.n) > far) continue;
      built++;
      const p = keep(`a:${a.id}`, () => ({ key: a.personId ?? a.id, assetId: a.instance.appearance.asset_id, built: true, actor: a,
        phase: hash01(`p:${a.id}`), y: null, yAt: null }));
      p.actor = a;
    }
    stats.built = built;
    for (const k of [...people.keys()]) if (!seen.has(k)) people.delete(k);
  }

  /**
   * Where a far walker is at `t` (s): PACE_M_S along from -> to and back, a pause at each end,
   * a function of the clock and their own phase, so only those drawn are ever placed.
   */
  function placeWalker(p, t) {
    if (!p.to || !p.from) { p.walk = 0; if (p.rest != null) p.heading = p.rest; return; }
    const len = p.len ?? (p.len = Math.hypot(p.to.e - p.from.e, p.to.n - p.from.n));
    if (len < 0.5) { p.walk = 0; return; }
    const go = len / PACE_M_S, rest = 3 + p.phase * 5, period = 2 * (go + rest);
    let x = (t + p.phase * period) % period;
    let a = p.from, b = p.to;
    if (x >= go + rest) { x -= go + rest; a = p.to; b = p.from; }
    if (x >= go) { p.e = b.e; p.n = b.n; p.walk = 0; return; }
    const k = x / go;
    p.e = a.e + (b.e - a.e) * k; p.n = a.n + (b.n - a.n) * k;
    p.heading = ((Math.atan2(b.e - a.e, b.n - a.n) * 180) / Math.PI + 360) % 360;
    p.walk = 1;
  }

  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), s3 = new THREE.Vector3(), w3 = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  const eye = new THREE.Vector3(), sortEye = new THREE.Vector3();
  const order = [];
  let sortAt = -Infinity;
  // What the instance buffers were last written for: a held frame (no time passing, the eye
  // where it was, nothing new loaded or baked, nobody read or sorted) writes nothing, so a
  // paused scene is still (the smoke's capture waits for one).
  let wroteFor = '';

  const layer = {
    group,
    stats,
    get tier() { return tier; },
    get shown() { return shown; },
    setShown(on) { shown = on !== false; group.visible = shown; return shown; },
    setTier(next) {
      if (!CAPS[next] || next === tier) return false;
      tier = next;
      // Bodies are clustered per detail: made again at the new one's cell.
      for (const b of bodies.values()) dropBody(b);
      bodies.clear();
      for (const p of people.values()) p.body = null;
      disposeAtlas();
      readAt = -Infinity;
      return true;
    },
    /** Whether person `id` (a carded person not built) is drawn by this layer now. */
    draws(id) { const p = people.get(`d:${id}`); return !!p && p.v > 0; },
    /** What the crowd holds now, for the smoke and the measurements. */
    census() {
      let tris = 0, bytes = 0;
      for (const b of bodies.values()) if (b.body) { tris += b.body.triangles * (b.mesh?.count ?? 0); bytes += b.body.vatBytes + b.body.reps * 40 + b.body.triangles * 6; }
      if (atlas) bytes += Math.round(atlas.width * atlas.height * 4 * 4 / 3);
      return { ...stats, midTriangles: tris, bytes, bodiesReady: [...bodies.values()].filter((b) => b.status === 'ready').length,
        atlas: atlas ? [atlas.width, atlas.height] : null, tier };
    },
    update(dt, camera, visitor = null) {
      if (disposed) return;
      const t0 = performance.now();
      clock += Math.max(0, dt || 0);
      const showPeople = shown && humans?.shown !== false;
      group.visible = showPeople;
      if (!showPeople || !camera) return;
      camera.getWorldPosition ? camera.getWorldPosition(eye) : eye.copy(camera.position);
      const v = visitor && Number.isFinite(visitor.e) ? { e: visitor.e, n: visitor.n } : { e: eye.x, n: -eye.z };
      if (clock - readAt > READ_S || !readFrom || Math.hypot(v.e - readFrom.e, v.n - readFrom.n) > READ_MOVE_M) {
        const r0 = performance.now();
        read(v); sortAt = -Infinity;
        stats.readMs = performance.now() - r0;
      }
      const f0 = performance.now();
      const caps = CAPS[tier] ?? CAPS.full;
      const held = !(dt > 0);
      // Who is in a tier, nearest first, read again every SORT_S (or once the eye has moved
      // SORT_MOVE_M); the fades themselves run every frame, in time.
      if (clock - sortAt > SORT_S || Math.abs(eye.x - sortEye.x) + Math.abs(eye.z - sortEye.z) > SORT_MOVE_M) {
        sortAt = clock; sortEye.copy(eye);
        order.length = 0;
        for (const p of people.values()) {
          if (p.built) {
            const a = p.actor;
            if (!a || a.disposed || a.indoors || a.inRange || humans.isHeld?.(a)) { p.tv = 0; p.v = 0; continue; }
            p.e = a.e; p.n = a.n;
          }
          const d = Math.hypot(p.e - eye.x, p.n + eye.z);
          p.d = d;
          const goal = tierTargets(d, tier, { built: p.built, drawM, was: { v: p.tv ?? 0, t: p.tt ?? 0 } });
          // Someone new to the layer is already where they belong: no cross-fade from the middle.
          if (p.v == null) { p.v = 0; p.t = goal.t; }
          p.tv = goal.v; p.tt = goal.t;
          if (p.tv > 0 || p.v > 0) order.push(p);
        }
        order.sort((a, b) => a.d - b.d);
        wroteFor = '';
      }
      const key = `${eye.x},${eye.y},${eye.z}|${stats.bodies}|${stats.baked}|${stats.reads}|${tier}`;
      if (held && key === wroteFor) return;
      wroteFor = key;
      for (const b of bodies.values()) if (b.mesh) b.mesh.count = 0;
      let nMid = 0, nFar = 0;
      const haveAtlas = ensureAtlas();
      let baked = 0, bakeMs = 0, groundMs = 0;
      const step = Math.max(0, dt || 0);
      for (const p of order) {
        if (p.built) {
          const a = p.actor;
          if (!a || a.disposed || a.indoors || a.inRange) continue;
          p.e = a.e; p.n = a.n; p.heading = a.heading; p.walk = a.state === 'walking' || a.path || a.route ? 1 : 0;
        } else placeWalker(p, clock);
        // The fades, in time: in or out over FADE_S, the middle to the card over CROSS_S.
        p.v = p.tv > p.v ? Math.min(p.tv, p.v + step / FADE_S) : Math.max(p.tv, p.v - step / FADE_S);
        p.t = p.tt > p.t ? Math.min(p.tt, p.t + step / CROSS_S) : Math.max(p.tt, p.t - step / CROSS_S);
        p.wm = p.v * (1 - p.t); p.wf = p.v * p.t;
        if (p.wm <= 0 && p.wf <= 0) continue;
        const b = p.body ?? bodyFor(p.assetId);
        if (b.status !== 'ready') { p.body = b.status === 'loading' ? null : b; continue; }
        p.body = b;
        // At most one dress's pictures baked a frame (24 small draws).
        if (haveAtlas && !b.baked && baked < 1) {
          const k0 = performance.now();
          b.baked = bake(p.assetId, b.body); baked++;
          bakeMs += performance.now() - k0;
        }
        // Height on the ground: read again only once they have moved a little (a card's
        // further: GROUND_CARD_M is under a pixel of it at the middle tier's far edge).
        if (p.y == null || Math.abs(p.ye - p.e) + Math.abs(p.yn - p.n) > (p.t > 0.5 ? GROUND_CARD_M : GROUND_MID_M)) {
          const g0 = performance.now();
          const h = heightAt(p.e, p.n);
          groundMs += performance.now() - g0;
          p.y = Number.isFinite(h) ? h : 0; p.ye = p.e; p.yn = p.n;
        }
        if (!p.look || (!p.look.looked && kit)) p.look = looksOf(p.key);
        const yaw = Math.PI - ((p.heading ?? 0) * Math.PI) / 180;
        // The walk's frame: the stride's phase by the ground covered.
        p.cycle = ((p.cycle ?? p.phase) + (p.walk ? (PACE_M_S * step) / STRIDE_M : 0)) % 1;
        if (p.wm > 0 && nMid < caps.mid && b.mesh && b.mesh.count < b.attrs.cap) {
          const i = b.mesh.count++;
          w3.set(p.e, p.y, -p.n);
          q.setFromAxisAngle(up, yaw); s3.setScalar(p.look.scale);
          m4.compose(w3, q, s3);
          b.mesh.setMatrixAt(i, m4);
          let fa = WALK_FRAMES, fb = WALK_FRAMES, ft = 0;
          if (p.walk) { const f = p.cycle * WALK_FRAMES; fa = Math.floor(f) % WALK_FRAMES; fb = (fa + 1) % WALK_FRAMES; ft = f - Math.floor(f); }
          b.attrs.a.setXYZW(i, fa, fb, ft, p.wm);
          const sk = p.look.skin, hr = p.look.hair;
          b.attrs.skin.setXYZ(i, sk[0], sk[1], sk[2]);
          b.attrs.hair.setXYZ(i, hr[0], hr[1], hr[2]);
          b.attrs.cloth.setX(i, p.look.cloth);
          nMid++;
        }
        if (p.wf > 0 && haveAtlas && b.baked && cardAttrs && nFar < Math.min(caps.far, cardAttrs.cap)) {
          const i = nFar++;
          cardAttrs.pos.setXYZW(i, p.e, p.y, -p.n, yaw);
          const pose = p.walk ? (p.cycle < 0.5 ? 1 : 2) : 0;
          cardAttrs.cell.setXYZW(i, p.look.scale, rows.get(p.assetId) * cardCols + pose * CARD_YAWS, p.wf, 0.92 + (p.look.cloth - 0.86) * 0.3);
        }
      }
      let tris = 0;
      for (const b of bodies.values()) if (b.mesh) {
        b.mesh.instanceMatrix.needsUpdate = true;
        b.mesh.instanceMatrix.clearUpdateRanges?.(); b.mesh.instanceMatrix.addUpdateRange?.(0, b.mesh.count * 16);
        for (const a of [b.attrs.a, b.attrs.skin, b.attrs.hair, b.attrs.cloth]) { a.needsUpdate = true; a.clearUpdateRanges?.(); a.addUpdateRange?.(0, b.mesh.count * a.itemSize); }
        b.mesh.visible = b.mesh.count > 0;
        tris += b.body.triangles * b.mesh.count;
      }
      if (cardMesh) {
        cardMesh.geometry.instanceCount = nFar;
        cardMesh.visible = nFar > 0;
        for (const a of [cardAttrs.pos, cardAttrs.cell]) { a.needsUpdate = true; a.clearUpdateRanges?.(); a.addUpdateRange?.(0, nFar * 4); }
      }
      stats.mid = nMid; stats.far = nFar; stats.midTriangles = tris;
      // The frame's own cost; a dress's one-off bake is kept apart (`bakeMs`, the last one).
      stats.ms = stats.ms * 0.9 + (performance.now() - f0 - bakeMs) * 0.1;
      if (bakeMs) stats.bakeMs = bakeMs;
      stats.groundMs = stats.groundMs * 0.9 + groundMs * 0.1;
      void t0;
    },
    dispose() {
      disposed = true;
      for (const b of bodies.values()) dropBody(b);
      bodies.clear();
      disposeAtlas();
      group.removeFromParent();
    },
  };
  function dropBody(b) {
    if (b.mesh) { group.remove(b.mesh); b.mesh.geometry.dispose(); b.mesh.material.dispose(); b.mesh.dispose?.(); }
    if (b.body) { b.body.geometry.dispose(); b.body.vat.dispose(); }
    b.mesh = null; b.body = null; b.status = 'dropped';
  }
  return layer;
}
